"""Treino da camada 2 com um comando (RF-14): gera modelo, métricas e parâmetros juntos.

Segue o protocolo pré-registrado em docs/relatorio-camada2.md. Nada aqui é ajustado olhando o teste:
hiperparâmetros vêm de params.yaml, e os cortes das faixas saem só do treino (validação cruzada).

A divisão treino/teste vem pronta da frente de Dados (docs/dados.md, `--corte` no dvc.yaml):
treino.csv até 15/09/2018, teste.csv com o WhatsApp de 16/09 a 28/10/2018. O teste_curtos.csv
(tweets) entra só no relato complementar.

Saídas:
- models/classificador.joblib: pipeline + cortes das faixas;
- experiments/results/metricas_camada2.json: critério, decisão go/no-go e relato complementar;
- experiments/results/params_camada2.json: parâmetros usados, hash da base e tamanho dos conjuntos.

Os arquivos não têm data nem hora: rodar duas vezes com os mesmos dados deve dar o mesmo resultado (RNF-10).

Uso (a partir da raiz, com o ambiente ativado):  python -m inteligencia.treino    (ou: dvc repro treinar)
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.preprocessing import OneHotEncoder

from inteligencia.classificador import FAIXAS, MODELO_PADRAO, RAIZ, Classificador, criar_pipeline, \
    escolher_cortes, faixa, probabilidades_fora_da_amostra
from inteligencia.texto import normalizar

BASES = RAIZ / "data" / "processados" / "treino"   # treino.csv, teste.csv, teste_curtos.csv
ROTULOS = {"falso": True, "verdadeiro": False}     # classe positiva: notícia falsa
PARAMS_PADRAO = RAIZ / "params.yaml"
RESULTADOS = RAIZ / "experiments" / "results"

F1_MINIMO = 0.75          # RNF-02
FALSO_ALARME_MAXIMO = 0.15  # RNF-03
MINIMO_POR_CLASSE = 100
MINIMO_POR_CLASSE_FONTE = 30   # relato complementar: F1 dentro de cada fonte


# dados

def _validar_item(item, posicao: int) -> dict:
    """Único lugar que conhece o esquema da base de treino: se a frente de Dados mudar, muda só aqui.

    Colunas: texto, rotulo ("falso"/"verdadeiro"), fonte, data (AAAA-MM-DD ou vazia).
    """
    try:
        texto, rotulo, fonte, data = item["texto"], item["rotulo"], item["fonte"], item["data"]
    except (KeyError, TypeError) as erro:
        raise ValueError(f"Linha {posicao} sem texto, rotulo, fonte ou data.") from erro
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError(f"Linha {posicao} tem texto vazio.")
    if rotulo not in ROTULOS:
        raise ValueError(f"Linha {posicao}: rotulo deve ser 'falso' ou 'verdadeiro', veio {rotulo!r}.")
    return {"texto": texto.strip(), "rotulo": ROTULOS[rotulo], "fonte": fonte, "data": data}


def carregar_csv(caminho: Path) -> list[dict]:
    try:
        with Path(caminho).open(encoding="utf-8", newline="") as f:
            linhas = list(csv.DictReader(f))
    except OSError as erro:
        raise ValueError(f"Não foi possível ler {caminho}. Rode: dvc repro treino") from erro
    if not linhas:
        raise ValueError(f"{caminho} está vazio.")
    return [_validar_item(linha, i) for i, linha in enumerate(linhas, 2)]   # linha 1 é o cabeçalho


def remover_repetidos(treino: list[dict], teste: list[dict]) -> tuple[list[dict], int]:
    """Tira do teste os textos que já estão no treino (normalizados). A frente de Dados já deduplica;
    esta conferência é a do protocolo e deve dar zero."""
    vistos = {normalizar(i["texto"]) for i in treino}
    limpo = [i for i in teste if normalizar(i["texto"]) not in vistos]
    return limpo, len(teste) - len(limpo)


#  métricas

def _r(x: float) -> float:
    return round(float(x), 6)


def decidir(f1: float, falso_alarme: float, n_falsas: int, n_verdadeiras: int) -> tuple[str, list[str]]:
    """Critério pré-registrado. Qualquer condição não atendida → no-go, com o motivo."""
    motivos = []
    if min(n_falsas, n_verdadeiras) < MINIMO_POR_CLASSE:
        motivos.append(f"inconclusivo: teste com {n_falsas} falsas e {n_verdadeiras} verdadeiras "
                       f"(mínimo {MINIMO_POR_CLASSE} de cada)")
    if f1 < F1_MINIMO:
        motivos.append(f"F1 macro {f1:.3f} < {F1_MINIMO} (RNF-02)")
    if falso_alarme > FALSO_ALARME_MAXIMO:
        motivos.append(f"falso alarme {falso_alarme:.1%} > {FALSO_ALARME_MAXIMO:.0%} (RNF-03)")
    return ("go" if not motivos else "no-go"), motivos


def avaliar(clf: Classificador, treino: list[dict], teste: list[dict], semente: int) -> dict:
    X, y = [i["texto"] for i in teste], np.array([i["rotulo"] for i in teste], dtype=int)
    p = clf.probabilidade(X)
    previsto = (p >= 0.5).astype(int)
    faixas = np.array([faixa(v, clf.corte_alto, clf.corte_baixo) for v in p])
    n_f, n_v = int(y.sum()), int((y == 0).sum())
    f1 = f1_score(y, previsto, average="macro") if n_f and n_v else 0.0
    falso_alarme = float((faixas[y == 0] == "muitos_sinais").mean()) if n_v else 1.0
    decisao, motivos = decidir(f1, falso_alarme, n_f, n_v)

    # Relato complementar: não entra na decisão, explica o resultado
    fontes_teste = np.array([i["fonte"] for i in teste])
    por_fonte = {}
    for fonte in sorted(set(fontes_teste)):
        m = fontes_teste == fonte
        nf, nv = int(y[m].sum()), int((y[m] == 0).sum())
        por_fonte[fonte] = {"falsas": nf, "verdadeiras": nv,
                            "f1_macro": _r(f1_score(y[m], previsto[m], average="macro"))
                            if min(nf, nv) >= MINIMO_POR_CLASSE_FONTE else None}
    y_treino = np.array([i["rotulo"] for i in treino], dtype=int)
    majoritaria = DummyClassifier(strategy="most_frequent").fit(np.zeros((len(y_treino), 1)), y_treino)
    so_fonte = LogisticRegression(class_weight="balanced", random_state=semente).fit(
        (enc := OneHotEncoder(handle_unknown="ignore")).fit_transform([[i["fonte"]] for i in treino]), y_treino)
    return {
        "criterio": {"f1_macro_minimo": F1_MINIMO, "falso_alarme_maximo": FALSO_ALARME_MAXIMO,
                     "minimo_por_classe": MINIMO_POR_CLASSE},
        "decisao": decisao,
        "motivos_no_go": motivos,
        "teste": {"falsas": n_f, "verdadeiras": n_v},
        "f1_macro": _r(f1),
        "falso_alarme": _r(falso_alarme),
        "matriz_confusao": {"linhas_real_colunas_previsto": ["verdadeira", "falsa"],
                            "valores": confusion_matrix(y, previsto, labels=[0, 1]).tolist()},
        "cortes": {"alto": _r(clf.corte_alto), "baixo": _r(clf.corte_baixo)},
        "faixas_por_classe": {nome: {f: int((faixas[y == classe] == f).sum()) for f in FAIXAS}
                              for nome, classe in (("verdadeiras", 0), ("falsas", 1))},
        "complementar": {
            "por_fonte": por_fonte,
            "linha_de_base_majoritaria_f1": _r(f1_score(y, majoritaria.predict(np.zeros((len(y), 1))),
                                                        average="macro")),
            "linha_de_base_so_fonte_f1": _r(f1_score(y, so_fonte.predict(enc.transform([[f] for f in fontes_teste])),
                                                     average="macro")),
        },
    }


# comando

def treinar(treino: list[dict], params: dict) -> Classificador:
    """Cortes das faixas pela validação cruzada no treino; depois, o modelo final com o treino inteiro."""
    X, y = [i["texto"] for i in treino], np.array([i["rotulo"] for i in treino], dtype=int)
    p_oof = probabilidades_fora_da_amostra(X, y, params)
    alto, baixo = escolher_cortes(p_oof, y, params["camada2"]["margem_faixas"])
    pipeline = criar_pipeline(params).fit(X, y)
    return Classificador(pipeline, alto, baixo)


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def main() -> None:
    import yaml
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bases", type=Path, default=BASES)
    parser.add_argument("--modelo", type=Path, default=MODELO_PADRAO)
    parser.add_argument("--saida", type=Path, default=RESULTADOS)
    a = parser.parse_args()

    params = yaml.safe_load(PARAMS_PADRAO.read_text(encoding="utf-8"))
    arquivos = {n: a.bases / f"{n}.csv" for n in ("treino", "teste", "teste_curtos")}
    treino = carregar_csv(arquivos["treino"])
    teste, repetidos = remover_repetidos(treino, carregar_csv(arquivos["teste"]))
    curtos, repetidos_curtos = remover_repetidos(treino, carregar_csv(arquivos["teste_curtos"]))

    clf = treinar(treino, params)
    clf.salvar(a.modelo)
    metricas = avaliar(clf, treino, teste, params["semente"])
    # teste extra (tweets curtos, outra fonte e época): só relato, não entra na decisão
    extra = avaliar(clf, treino, curtos, params["semente"])
    metricas["complementar"]["teste_curtos"] = {k: extra[k] for k in ("teste", "f1_macro", "falso_alarme",
                                                                       "matriz_confusao", "faixas_por_classe")}
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "metricas_camada2.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=1) + "\n",
                                                   encoding="utf-8")
    usados = {"semente": params["semente"], "camada2": params["camada2"],
              "sha256": {n: _sha256(c) for n, c in arquivos.items()},
              "linhas": {"treino": len(treino), "teste": len(teste), "teste_curtos": len(curtos)},
              "removidos_por_repeticao": {"teste": repetidos, "teste_curtos": repetidos_curtos}}
    (a.saida / "params_camada2.json").write_text(json.dumps(usados, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8")
    print(f"Treino {len(treino)} | teste {len(teste)} | teste_curtos {len(curtos)} "
          f"({repetidos} + {repetidos_curtos} repetidos removidos)")
    print(f"F1 macro {metricas['f1_macro']:.3f} | falso alarme {metricas['falso_alarme']:.1%} "
          f"→ {metricas['decisao'].upper()}")
    for motivo in metricas["motivos_no_go"]:
        print(f"  - {motivo}")


if __name__ == "__main__":
    main()
