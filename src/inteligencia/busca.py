"""Camada 1 do bot: busca as checagens de agências mais parecidas com a mensagem (RF-06, RN-05, RN-06).

Contrato com o bot: `buscar(texto, k=3)` devolve uma lista com os campos da base de checagens
mais `semelhanca` (0 a 1) e `faixa` (`ja_checado` / `relacionada` / `baixa`).

Busca = k-NN exato por cosseno: os vetores são normalizados, então cosseno = produto escalar.
Busca híbrida: o MiniLM quase ignora palavras e nomes que não conhece, e o vetor fica dominado
pelos nomes famosos ("Flávio Bolsonaro e o tesouraço" ficava igual a qualquer checagem sobre
Flávio Bolsonaro). Por isso, além do cosseno:
- nomes raros (palavras com maiúscula pouco comuns na base, como "Vorcaro"): só aparece checagem
  que tenha um deles;
- assunto (as palavras que não são nomes): a checagem precisa cobrir parte dele, pesado pela
  raridade ("tesouraço" pesa muito; "vai" e "diz", quase nada). A cobertura também entra na nota
  usada para ordenar e para a faixa "relacionada". `semelhanca` continua sendo o cosseno.
Reranker (ligado no bot): as candidatas da busca acima (as 20 melhores pelo cosseno e as 20 pela
nota híbrida) são relidas por um cross-encoder multilíngue, que lê a mensagem e a checagem juntas
e dá uma nota de "falam da mesma coisa". A ordem e as faixas passam a vir dessa nota; a negação
(RN-06) continua impedindo "já checado".
O índice guarda o hash SHA-256 de cada arquivo e é conferido ao carregar, para nunca buscar num
índice que não corresponde à base ou ao modelo.

Uso (a partir da raiz do repositório, com o ambiente ativado):
    python -m inteligencia.busca --construir
    python -m inteligencia.busca "texto da mensagem"
"""
import argparse
import hashlib
import json
import re
from datetime import date
from functools import cache
from pathlib import Path

import numpy as np

from inteligencia.normalizacao import normalizar_consulta
from inteligencia.texto import normalizar, tirar_acento

RAIZ = Path(__file__).resolve().parents[2]
BASE_PADRAO = RAIZ / "data" / "processados" / "checagens" / "checagens.json"
INDICE_PADRAO = RAIZ / "data" / "indices" / "camada1"

# Mesmo modelo e revisão de experiments/modelos.py (MINILM), escolhido no notebook 06
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
REVISAO = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
# Reranker: cross-encoder multilíngue treinado no mMARCO (MS MARCO traduzido; Apache-2.0), ~470 MB
RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
REVISAO_RERANKER = "1427fd652930e4ba29e8149678df786c240d8825"
CANDIDATAS = 20            # quantas candidatas de cada ordem (cosseno e híbrida) vão ao reranker
# Notas do reranker, calibradas por grade no benchmark de 62 mensagens + 25 perguntas soltas:
# controles mostrados 1/32, nenhum "já checado" errado; 3 a 5 dão o mesmo resultado.
NOTA_RELACIONADA = 4.0
NOTA_JA_CHECADO = 9.0      # além do cosseno ≥ limite_alta e da mesma negação
PARAMS_PADRAO = RAIZ / "params.yaml"

CAMPOS = ("id", "alegacao", "veredito_original", "veredito_normalizado", "agencia", "data", "link",
          "fonte_dataset")
VEREDITOS = {"falso", "enganoso", "verdadeiro", "outro"}   # RN-02

# RN-06: palavras que invertem o sentido. Aplicada depois de tirar caixa e acento.
NEGACAO = re.compile(r"\b(nao|nunca|jamais|nem|nenhum|nenhuma|falso que|mentira que)\b")

# Busca híbrida (ver o topo do arquivo)
PALAVRA_RARA = 0.01       # nome raro = aparece em até 1% das checagens da base
PESO_PALAVRAS = 0.30      # quanto os nomes raros em comum pesam na ordem, além do cosseno
# Calibrados por grade no benchmark de 62 mensagens (RNF-05: controles mostrados ≤ 8, "já checado"
# ≤ 2, negação nunca "já checado"). A região escolhida é estável: os vizinhos dão o mesmo resultado.
PESO_ASSUNTO = 0.20        # nota = cosseno + PESO_ASSUNTO × cobertura do assunto (0 a 1)
ASSUNTO_MINIMO = 0.20      # cobertura mínima para a checagem ser mostrada
ASSUNTO_JA_CHECADO = 0.30  # cobertura mínima para "já checado"
VAZIAS = {"que", "para", "por", "com", "sem", "uma", "uns", "umas", "dos", "das", "nos", "nas", "aos",
          "pelo", "pela", "pelos", "pelas", "como", "mais", "mas", "foi", "ser", "sao", "esta", "este",
          "essa", "esse", "isso", "isto", "ele", "ela", "eles", "elas", "seu", "sua", "seus", "suas",
          "tem", "ter", "sobre", "entre", "ate", "quem", "qual", "onde", "quando", "porque", "verdade"}


def palavras(texto: str) -> set[str]:
    """Palavras que contam na busca por palavras: sem caixa, acento, pontuação e palavras vazias."""
    return {p for p in normalizar(texto).split() if (len(p) >= 3 or p.isdigit()) and p not in VAZIAS}


def nomes(texto: str) -> set[str]:
    """Palavras escritas com maiúscula (nomes, siglas, lugares), já no formato de `palavras()`.
    Mensagem quase toda em maiúsculas ("URGENTE!!! COMPARTILHEM") não diz o que é nome: devolve vazio."""
    tokens = re.findall(r"\w+|[.!?:\n]", texto)
    # a 1ª palavra de cada frase leva maiúscula por regra, não por ser nome: não conta
    maiusculas = [w for anterior, w in zip([".", *tokens], tokens)
                  if w[0].isupper() and anterior not in ".!?:\n"]
    tokens = [w for w in tokens if w not in ".!?:\n"]
    if not tokens or sum(w[0].isupper() for w in tokens) > len(tokens) / 2:
        return set()
    return palavras(" ".join(maiusculas))


# base de checagens

def _validar_registro(registro, posicao: int) -> dict:
    """Único lugar que conhece o esquema da base: se a frente de Dados mudar o formato, muda só aqui."""
    if not isinstance(registro, dict):
        raise ValueError(f"Registro {posicao} não é um objeto JSON.")
    faltando = [c for c in CAMPOS if c not in registro]
    if faltando:
        raise ValueError(f"Registro {posicao} sem os campos {faltando}.")
    if not isinstance(registro["alegacao"], str) or not registro["alegacao"].strip():
        raise ValueError(f"Registro {posicao} tem alegação vazia.")
    if registro["veredito_normalizado"] not in VEREDITOS:
        raise ValueError(f"Registro {posicao} tem veredito_normalizado fora de {sorted(VEREDITOS)}.")
    try:
        date.fromisoformat(registro["data"])
    except (TypeError, ValueError) as erro:
        raise ValueError(f"Registro {posicao} tem data fora do formato AAAA-MM-DD.") from erro
    return {c: registro[c] for c in CAMPOS}


def carregar_base(caminho: Path = BASE_PADRAO) -> list[dict]:
    try:
        bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except OSError as erro:
        raise ValueError(f"Não foi possível ler a base de checagens: {caminho}") from erro
    if isinstance(bruto, dict):           # aceita {"registros": [...]} além da lista pura
        bruto = bruto.get("registros")
    if not isinstance(bruto, list) or not bruto:
        raise ValueError("A base de checagens deve ser uma lista não vazia de registros.")
    registros = [_validar_registro(r, i) for i, r in enumerate(bruto, 1)]
    ids = [r["id"] for r in registros]
    if len(set(ids)) != len(ids):
        raise ValueError("A base de checagens tem ids repetidos.")
    return registros


# índice

@cache
def _modelo():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as erro:
        raise ValueError("Instale as dependências da busca: pip install -e '.[busca]'") from erro
    modelo = SentenceTransformer(MODELO, revision=REVISAO)
    modelo.max_seq_length = 128   # igual a experiments/modelos.py: mesmos vetores do índice
    return modelo


@cache
def _reranker():
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as erro:
        raise ValueError("Instale as dependências da busca: pip install -e '.[busca]'") from erro
    return CrossEncoder(RERANKER, revision=REVISAO_RERANKER)


def reranquear(pares: list[tuple[str, str]]) -> np.ndarray:
    """Nota do cross-encoder para cada par (mensagem, alegação): quanto maior, mais falam da mesma coisa."""
    return np.asarray(_reranker().predict(pares, batch_size=64, show_progress_bar=False), dtype="float32")


def vetorizar(textos: list[str]) -> np.ndarray:
    """Embeddings normalizados do MiniLM multilíngue, na revisão fixada."""
    E = _modelo().encode(list(textos), normalize_embeddings=True, batch_size=32,
                         show_progress_bar=len(textos) > 1000)
    return np.asarray(E, dtype="float32")


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def construir_indice(base: Path = BASE_PADRAO, saida: Path = INDICE_PADRAO, vetorizar=vetorizar) -> dict:
    registros = carregar_base(base)
    E = vetorizar([r["alegacao"] for r in registros])
    if E.shape[0] != len(registros) or not np.isfinite(E).all():
        raise ValueError("O modelo devolveu vetores inválidos para a base.")
    saida.mkdir(parents=True, exist_ok=True)
    np.save(saida / "vetores.npy", E, allow_pickle=False)
    (saida / "checagens.json").write_text(json.dumps(registros, ensure_ascii=False, indent=1) + "\n",
                                          encoding="utf-8")
    manifesto = {
        "modelo": MODELO, "revisao": REVISAO, "quantidade": len(registros), "dimensoes": int(E.shape[1]),
        "sha256_base": _sha256(Path(base)),
        "arquivos": {n: _sha256(saida / n) for n in ("vetores.npy", "checagens.json")},
    }
    (saida / "manifesto.json").write_text(json.dumps(manifesto, indent=1) + "\n", encoding="utf-8")
    return manifesto


def carregar_indice(pasta: Path = INDICE_PADRAO) -> tuple[np.ndarray, list[dict]]:
    """Carrega o índice só depois de conferir hashes, modelo e alinhamento entre vetores e checagens."""
    try:
        manifesto = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
    except OSError as erro:
        raise ValueError(f"Índice não encontrado em {pasta}. Rode com --construir.") from erro
    if (manifesto.get("modelo"), manifesto.get("revisao")) != (MODELO, REVISAO):
        raise ValueError("O índice foi gerado com outro modelo ou revisão. Reconstrua o índice.")
    for arquivo, esperado in manifesto["arquivos"].items():
        if _sha256(pasta / arquivo) != esperado:
            raise ValueError(f"{arquivo} foi alterado depois de gerado o índice. Reconstrua o índice.")
    E = np.load(pasta / "vetores.npy", allow_pickle=False)
    registros = json.loads((pasta / "checagens.json").read_text(encoding="utf-8"))
    if E.shape[0] != len(registros) or E.shape[0] != manifesto["quantidade"]:
        raise ValueError("Vetores e checagens do índice estão desalinhados.")
    return E, registros


# ---------------------------------------------------------------- faixas e negação

def ler_limites(params: Path = PARAMS_PADRAO) -> tuple[float, float]:
    import yaml   # só aqui: os testes passam os limites direto e não precisam do pyyaml
    c1 = yaml.safe_load(Path(params).read_text(encoding="utf-8"))["camada1"]
    return float(c1["limite_alta"]), float(c1["limite_media"])


def tem_negacao(texto: str) -> bool:
    return bool(NEGACAO.search(tirar_acento(texto).lower()))


def faixa(semelhanca: float, consulta: str, alegacao: str, alta: float, media: float,
          casa_rara: bool | None = None, assunto: float | None = None) -> str:
    """RN-05 com o rebaixamento da RN-06: divergência de negação nunca passa de "relacionada".

    `casa_rara`: None = sem filtro de palavras (regra original). False = a checagem não passou no
    filtro da busca híbrida (não tem o nome raro ou cobre pouco o assunto da mensagem).
    `assunto`: cobertura do assunto (0 a 1) na busca híbrida; None = regra original, só cosseno.
    """
    if casa_rara is False:
        return "baixa"
    if assunto is not None:
        if semelhanca >= alta and assunto >= ASSUNTO_JA_CHECADO:
            return "relacionada" if tem_negacao(consulta) != tem_negacao(alegacao) else "ja_checado"
        return "relacionada" if semelhanca + PESO_ASSUNTO * assunto >= media else "baixa"
    if semelhanca >= alta:
        return "relacionada" if tem_negacao(consulta) != tem_negacao(alegacao) else "ja_checado"
    return "relacionada" if semelhanca >= media else "baixa"


# busca

class Buscador:
    def __init__(self, vetores: np.ndarray, registros: list[dict], alta: float, media: float,
                 vetorizar=vetorizar, normalizar=normalizar_consulta, hibrida: bool = True,
                 reranquear=None):
        """`normalizar=None` desliga a normalização da consulta (só para comparar na calibração).
        `hibrida=False` desliga a busca por palavras raras (volta à busca só por cosseno).
        `reranquear`: função pares → notas (ver `reranquear()`); None = sem reranker."""
        if not 0 <= media <= alta <= 1:
            raise ValueError("Os limites devem respeitar 0 ≤ média ≤ alta ≤ 1.")
        self.vetores, self.registros = vetores, registros
        self.alta, self.media = alta, media
        self._vetorizar = vetorizar
        self._normalizar = normalizar or (lambda t: t)
        self.hibrida = hibrida
        self._reranquear = reranquear
        posicoes: dict[str, list[int]] = {}
        for i, r in enumerate(registros):
            for p in palavras(r["alegacao"]):
                posicoes.setdefault(p, []).append(i)
        self._checagens_com = {p: np.array(ix) for p, ix in posicoes.items()}

    def palavras_raras(self, consulta: str) -> list[str]:
        """Nomes da mensagem que estão na base, mas em poucas checagens ("Vorcaro" sim, "Bolsonaro" não)."""
        limite = PALAVRA_RARA * len(self.registros)
        return sorted(p for p in nomes(consulta) if 0 < len(self._checagens_com.get(p, ())) <= limite)

    def cobertura_rara(self, raras: list[str]) -> np.ndarray:
        """Para cada checagem, a fração do peso das palavras raras da mensagem que ela contém (0 a 1).
        Peso = log(n / checagens com a palavra): quanto mais rara, mais pesa."""
        c = np.zeros(len(self.registros), dtype="float32")
        if not raras:
            return c
        n = len(self.registros)
        pesos = {p: float(np.log(n / len(self._checagens_com[p]))) for p in raras}
        total = sum(pesos.values())
        for p, peso in pesos.items():
            c[self._checagens_com[p]] += peso / total
        return c

    def cobertura_assunto(self, consulta: str) -> np.ndarray:
        """Para cada checagem, a fração das palavras de assunto da mensagem (as que não são nomes) que
        ela tem, pesada pela raridade: log(n / checagens com a palavra). Palavra que não está em
        nenhuma checagem ("tesouraço") pesa o máximo e nunca é coberta. Mensagem sem assunto (só
        nomes, ou toda em maiúsculas) não exige nada: devolve 1 para todas."""
        # assunto = palavras em minúscula; a 1ª de cada frase também fica fora, porque pode ser nome
        # ("Flávio Bolsonaro e o tesouraço": o assunto é só "tesouraço")
        minusculas = " ".join(w for w in re.findall(r"\w+", consulta) if not w[0].isupper())
        assunto = palavras(minusculas) if not consulta.isupper() else set()
        n = len(self.registros)
        if not assunto:
            return np.ones(n, dtype="float32")
        pesos = {p: float(np.log((n + 1) / (len(self._checagens_com.get(p, ())) + 1))) for p in assunto}
        total = sum(pesos.values()) or 1.0
        cob = np.zeros(n, dtype="float32")
        for p, peso in pesos.items():
            if p in self._checagens_com:
                cob[self._checagens_com[p]] += peso / total
        return cob

    def preparar_consulta(self, texto: str) -> str:
        """Apelidos e internetês desfeitos (RF-05). A negação (RN-06) é conferida neste texto."""
        return self._normalizar(texto.strip())

    def semelhancas(self, textos: list[str]) -> np.ndarray:
        """Matriz consultas × checagens, cortada em [0, 1] (cosseno negativo = nada parecido)."""
        Q = self._vetorizar([self.preparar_consulta(t) for t in textos])
        return np.clip(Q @ self.vetores.T, 0.0, 1.0)

    def buscar(self, texto: str, k: int = 3) -> list[dict]:
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("Informe um texto com conteúdo para buscar.")
        if type(k) is not int or not 1 <= k <= len(self.registros):
            raise ValueError(f"k deve ser um inteiro de 1 a {len(self.registros)}.")
        s = self.semelhancas([texto])[0]
        texto = self.preparar_consulta(texto)
        if self._reranquear is not None:
            return self._buscar_reranqueado(texto, s, k)
        if self.hibrida:
            raras = self.palavras_raras(texto)
            c = self.cobertura_rara(raras)
            a = self.cobertura_assunto(texto)
            casa = (a >= ASSUNTO_MINIMO) & ((c > 0) if raras else True)
            # primeiro as candidatas a "já checado", depois as que passam no filtro, depois o resto
            grupo = np.where(casa & (s >= self.alta) & (a >= ASSUNTO_JA_CHECADO), 2, np.where(casa, 1, 0))
            ordem = np.lexsort((-(s + PESO_ASSUNTO * a + PESO_PALAVRAS * c), -grupo))[:k]
        else:
            casa = a = None
            ordem = np.argsort(-s, kind="stable")[:k]
        return [{**self.registros[i], "semelhanca": round(float(s[i]), 4),
                 "faixa": faixa(float(s[i]), texto, self.registros[i]["alegacao"], self.alta, self.media,
                                None if casa is None else bool(casa[i]),
                                None if a is None else float(a[i]))}
                for i in ordem]


    def _buscar_reranqueado(self, consulta: str, s: np.ndarray, k: int) -> list[dict]:
        a = self.cobertura_assunto(consulta)
        n = min(CANDIDATAS, len(self.registros))
        candidatas = np.unique(np.concatenate([np.argsort(-s, kind="stable")[:n],
                                               np.argsort(-(s + PESO_ASSUNTO * a), kind="stable")[:n]]))
        notas = self._reranquear([(consulta, self.registros[i]["alegacao"]) for i in candidatas])
        ordem = np.argsort(-notas, kind="stable")[:k]
        negacao = tem_negacao(consulta)
        saida = []
        for j in ordem:
            i, nota = candidatas[j], float(notas[j])
            alegacao = self.registros[i]["alegacao"]
            if nota >= NOTA_JA_CHECADO and s[i] >= self.alta and negacao == tem_negacao(alegacao):
                f = "ja_checado"
            elif nota >= NOTA_RELACIONADA:
                f = "relacionada"
            else:
                f = "baixa"
            saida.append({**self.registros[i], "semelhanca": round(float(s[i]), 4), "faixa": f})
        return saida


@cache
def _buscador_padrao() -> Buscador:
    """Carrega índice, modelo e limites uma vez só por processo (latência, RNF-01)."""
    vetores, registros = carregar_indice()
    return Buscador(vetores, registros, *ler_limites(), reranquear=reranquear)


def buscar(texto: str, k: int = 3) -> list[dict]:
    """Contrato com o bot (RF-06). Mudou a assinatura? Avise a Engenharia."""
    return _buscador_padrao().buscar(texto, k)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("texto", nargs="?")
    parser.add_argument("--construir", action="store_true", help="gera o índice a partir da base")
    parser.add_argument("--base", type=Path, default=BASE_PADRAO)
    parser.add_argument("--indice", type=Path, default=INDICE_PADRAO)
    parser.add_argument("-k", type=int, default=3)
    a = parser.parse_args()
    if a.construir:
        m = construir_indice(a.base, a.indice)
        print(f"Índice com {m['quantidade']} checagens ({m['dimensoes']} dimensões) em {a.indice}")
    if a.texto:
        vetores, registros = carregar_indice(a.indice)
        b = Buscador(vetores, registros, *ler_limites(), reranquear=reranquear)
        print(json.dumps(b.buscar(a.texto, a.k), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
