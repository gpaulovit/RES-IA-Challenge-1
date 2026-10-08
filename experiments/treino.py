"""Treino da camada 2 com um comando (RF-14): gera modelo, métricas e parâmetros juntos.

Segue o protocolo pré-registrado em docs/relatorio-camada2.md. Nada aqui é ajustado olhando o teste:
hiperparâmetros vêm de params.yaml, e os cortes das faixas saem só do treino (validação cruzada).

Saídas:
- models/classificador.joblib: pipeline + cortes das faixas;
- experiments/results/metricas_camada2.json: critério, decisão go/no-go e relato complementar;
- experiments/results/params_camada2.json: parâmetros usados, hash da base e tamanho dos conjuntos.

Os arquivos não têm data nem hora: rodar duas vezes com os mesmos dados deve dar o mesmo resultado (RNF-10).

Uso (a partir da raiz):  .venv/bin/python experiments/treino.py    (ou: dvc repro treinar)
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.preprocessing import OneHotEncoder

from classificador import FAIXAS, MODELO_PADRAO, RAIZ, Classificador, criar_pipeline, escolher_cortes, \
    faixa, probabilidades_fora_da_amostra
from reescrita import tirar_acento

BASE_PADRAO = RAIZ / "data" / "processados" / "treino" / "treino.json"
PARAMS_PADRAO = RAIZ / "params.yaml"
RESULTADOS = Path(__file__).resolve().parent / "results"

# Critério pré-registrado (docs/relatorio-camada2.md, "Critério de decisão"). Não mudar depois do teste.
F1_MINIMO = 0.75          # RNF-02
FALSO_ALARME_MAXIMO = 0.15  # RNF-03
MINIMO_POR_CLASSE = 100
MINIMO_POR_CLASSE_FONTE = 30   # relato complementar: F1 dentro de cada fonte


# ---------------------------------------------------------------- dados

def _validar_item(item, posicao: int) -> dict:
    """Único lugar que conhece o esquema da base de treino: se a frente de Dados mudar, muda só aqui."""
    try:
        texto, rotulo, ano, fonte = item["texto"], item["rotulo"], item["ano"], item["fonte"]
    except (KeyError, TypeError) as erro:
        raise ValueError(f"Item {posicao} sem texto, rotulo, ano ou fonte.") from erro
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError(f"Item {posicao} tem texto vazio.")
    if not isinstance(rotulo, bool):
        raise ValueError(f"Item {posicao}: rotulo deve ser true (falsa) ou false (verdadeira).")
    if type(ano) is not int:
        raise ValueError(f"Item {posicao}: ano deve ser inteiro.")
    return {"texto": texto.strip(), "rotulo": rotulo, "ano": ano, "fonte": str(fonte)}


def carregar_base(caminho: Path) -> list[dict]:
    bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if not isinstance(bruto, list) or not bruto:
        raise ValueError("A base de treino deve ser uma lista não vazia.")
    return [_validar_item(item, i) for i, item in enumerate(bruto, 1)]


def normalizar(texto: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", tirar_acento(texto).lower()).split())


def dividir(itens: list[dict], ano_corte: int) -> tuple[list[dict], list[dict], int]:
    """Treino: ano ≤ corte. Teste: ano > corte, sem textos que já estão no treino (normalizados)."""
    treino = [i for i in itens if i["ano"] <= ano_corte]
    vistos = {normalizar(i["texto"]) for i in treino}
    teste_bruto = [i for i in itens if i["ano"] > ano_corte]
    teste = [i for i in teste_bruto if normalizar(i["texto"]) not in vistos]
    return treino, teste, len(teste_bruto) - len(teste)


# ---------------------------------------------------------------- métricas

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


# ---------------------------------------------------------------- comando

def treinar(itens: list[dict], params: dict) -> tuple[Classificador, list[dict], list[dict], int]:
    treino, teste, repetidos = dividir(itens, params["camada2"]["ano_corte"])
    X, y = [i["texto"] for i in treino], np.array([i["rotulo"] for i in treino], dtype=int)
    p_oof = probabilidades_fora_da_amostra(X, y, params)
    alto, baixo = escolher_cortes(p_oof, y, params["camada2"]["margem_faixas"])
    pipeline = criar_pipeline(params).fit(X, y)
    return Classificador(pipeline, alto, baixo), treino, teste, repetidos


def main() -> None:
    import yaml
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", type=Path, default=BASE_PADRAO)
    parser.add_argument("--modelo", type=Path, default=MODELO_PADRAO)
    parser.add_argument("--saida", type=Path, default=RESULTADOS)
    a = parser.parse_args()

    params = yaml.safe_load(PARAMS_PADRAO.read_text(encoding="utf-8"))
    itens = carregar_base(a.base)
    clf, treino, teste, repetidos = treinar(itens, params)
    clf.salvar(a.modelo)
    metricas = avaliar(clf, treino, teste, params["semente"])
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "metricas_camada2.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=1) + "\n",
                                                   encoding="utf-8")
    usados = {"semente": params["semente"], "camada2": params["camada2"],
              "sha256_base": hashlib.sha256(Path(a.base).read_bytes()).hexdigest(),
              "treino": len(treino), "teste": len(teste), "teste_removidos_por_repeticao": repetidos}
    (a.saida / "params_camada2.json").write_text(json.dumps(usados, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8")
    print(f"Treino {len(treino)} | teste {len(teste)} ({repetidos} repetidos removidos)")
    print(f"F1 macro {metricas['f1_macro']:.3f} | falso alarme {metricas['falso_alarme']:.1%} "
          f"→ {metricas['decisao'].upper()}")
    for motivo in metricas["motivos_no_go"]:
        print(f"  - {motivo}")


if __name__ == "__main__":
    main()
