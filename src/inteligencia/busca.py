"""Camada 1 do bot: busca as checagens de agências mais parecidas com a mensagem (RF-06, RN-05, RN-06).

Contrato com o bot: `buscar(texto, k=3)` devolve uma lista com os campos da base de checagens
mais `semelhanca` (0 a 1) e `faixa` (`ja_checado` / `relacionada` / `baixa`).

Busca = k-NN exato por cosseno: os vetores são normalizados, então cosseno = produto escalar.
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
from inteligencia.texto import tirar_acento

RAIZ = Path(__file__).resolve().parents[2]
BASE_PADRAO = RAIZ / "data" / "processados" / "checagens" / "checagens.json"
INDICE_PADRAO = RAIZ / "data" / "indices" / "camada1"

# Mesmo modelo e revisão de experiments/modelos.py (MINILM). Comparação preliminar no notebook 06: com a
# consulta normalizada, empata com os outros 5 candidatos (MRR 0,917 contra 0,909–0,929) e é o mais rápido
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
REVISAO = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
PARAMS_PADRAO = RAIZ / "params.yaml"

CAMPOS = ("id", "alegacao", "veredito_original", "veredito_normalizado", "agencia", "data", "link",
          "fonte_dataset")
VEREDITOS = {"falso", "enganoso", "verdadeiro", "outro"}   # RN-02

# RN-06: palavras que invertem o sentido. Aplicada depois de tirar caixa e acento.
NEGACAO = re.compile(r"\b(nao|nunca|jamais|nem|nenhum|nenhuma|falso que|mentira que)\b")


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


def faixa(semelhanca: float, consulta: str, alegacao: str, alta: float, media: float) -> str:
    """RN-05 com o rebaixamento da RN-06: divergência de negação nunca passa de "relacionada"."""
    if semelhanca >= alta:
        return "relacionada" if tem_negacao(consulta) != tem_negacao(alegacao) else "ja_checado"
    return "relacionada" if semelhanca >= media else "baixa"


# busca

class Buscador:
    def __init__(self, vetores: np.ndarray, registros: list[dict], alta: float, media: float,
                 vetorizar=vetorizar, normalizar=normalizar_consulta):
        """`normalizar=None` desliga a normalização da consulta (só para comparar na calibração)."""
        if not 0 <= media <= alta <= 1:
            raise ValueError("Os limites devem respeitar 0 ≤ média ≤ alta ≤ 1.")
        self.vetores, self.registros = vetores, registros
        self.alta, self.media = alta, media
        self._vetorizar = vetorizar
        self._normalizar = normalizar or (lambda t: t)

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
        ordem = np.argsort(-s, kind="stable")[:k]
        return [{**self.registros[i], "semelhanca": round(float(s[i]), 4),
                 "faixa": faixa(float(s[i]), texto, self.registros[i]["alegacao"], self.alta, self.media)}
                for i in ordem]


@cache
def _buscador_padrao() -> Buscador:
    """Carrega índice, modelo e limites uma vez só por processo (latência, RNF-01)."""
    vetores, registros = carregar_indice()
    return Buscador(vetores, registros, *ler_limites())


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
        b = Buscador(vetores, registros, *ler_limites())
        print(json.dumps(b.buscar(a.texto, a.k), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
