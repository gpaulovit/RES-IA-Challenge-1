"""Gate de generalização temporal, 1ª rodada (tasks 2.3, 3.1, 3.3, 3.4, 4.1 e 7.1).

O padrão aprendido num período separa notícias falsas de verdadeiras num período posterior?
Desenho, limites e regras: design.md da change `add-fake-news-pattern-scoring`, Decisões 3–5.
Os limites abaixo são cópia da tabela da Decisão 4; mudar um deles exige mudar o design.md antes.

Uso (a partir de experiments/):  ../.venv/bin/python gate.py
Saídas: results/gate_conjuntos.csv, results/gate_temporal.csv, results/gate_criterios.csv
"""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from corpora import carregar_central_rotulada, carregar_fakebr, carregar_fakerecogna
from modelos import MINILM, embeddings
from reescrita import carregar_apelidos, carregar_internetes, erro_digitacao, internetes, trocar_apelido

RESULTS = Path(__file__).parent / "results"
SEMENTE_GIRIA, POR_CLASSE_GIRIA = 50, 200
CATEGORIAS_GIRIA = ["apelido", "girias", "apelido+girias", "digitacao"]   # de teste_reescrita.csv, sem negacao

# Decisão 3: (origem, anos) de cada lado
TESTES = {
    "A": {"treino": [("fakerecogna", range(2020, 2021))],
          "avaliacao": [("fakerecogna", range(2021, 2022))]},
    "B": {"treino": [("fakebr", range(2016, 2019)), ("central_de_fatos", range(2000, 2019))],
          "avaliacao": [("fakerecogna", range(2020, 2022)), ("central_de_fatos", range(2020, 2022))]},
}

# Decisão 4: (limite GO, limite inconclusivo); maior é melhor
LIMITES_AUC = {"A": (0.85, 0.75), "B": (0.80, 0.75)}
LIMITE_GANHO_LEXICO = (0.05, 0.02)
LIMITE_ATALHO = (0.10, 0.05)


# ---------- conjuntos (2.3) ----------

def _chave(claims: pd.Series) -> pd.Series:
    return claims.str.strip().str.lower()


def montar(fontes: dict[str, pd.DataFrame], desenho: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Treino e avaliação de um teste. Textos que já estão no treino saem da avaliação."""
    lado = {nome: pd.concat([fontes[o][fontes[o]["ano"].isin(anos)] for o, anos in partes], ignore_index=True)
            for nome, partes in desenho.items()}
    treino, avaliacao = lado["treino"], lado["avaliacao"]
    avaliacao = avaliacao[~_chave(avaliacao["claim"]).isin(set(_chave(treino["claim"])))].reset_index(drop=True)
    assert not set(treino["ano"]) & set(avaliacao["ano"]), "ano do período de avaliação no treino"
    assert not set(_chave(treino["claim"])) & set(_chave(avaliacao["claim"])), "texto da avaliação no treino"
    return treino, avaliacao


def assinatura(d: pd.DataFrame) -> str:
    linhas = sorted(f"{c}\t{int(f)}\t{a}\t{o}" for c, f, a, o in zip(d["claim"], d["is_fake"], d["ano"], d["origem"]))
    return hashlib.sha256("\n".join(linhas).encode()).hexdigest()


# ---------- métricas e critérios (4.1) ----------

def ece(y: np.ndarray, p: np.ndarray, faixas: int = 10) -> float:
    """Expected calibration error com faixas de largura igual em [0, 1]."""
    y, p = np.asarray(y, dtype=float), np.asarray(p, dtype=float)
    faixa = np.minimum((p * faixas).astype(int), faixas - 1)
    return float(sum(abs(y[faixa == b].mean() - p[faixa == b].mean()) * (faixa == b).mean()
                     for b in range(faixas) if (faixa == b).any()))


def metricas(y, p, proporcao_treino: float) -> dict:
    brier = brier_score_loss(y, p)
    referencia = brier_score_loss(y, np.full(len(y), proporcao_treino))   # prever a proporção de falsas do treino
    return {"auc": roc_auc_score(y, p), "ece": ece(y, p), "brier": brier, "brier_skill": 1 - brier / referencia,
            "n": len(y), "n_falsas": int(np.sum(y))}


def _maior_melhor(valor: float, limites: tuple[float, float]) -> str:
    go, inconclusivo = limites
    return "GO" if valor >= go else "INCONCLUSIVO" if valor >= inconclusivo else "NO-GO"


def classificar(teste: str, principal: dict, lexica: dict, controle: dict, giria: dict) -> dict[str, str]:
    """Cada critério da Decisão 4 → GO, INCONCLUSIVO ou NO-GO."""
    if giria["media"] <= 0.10 and giria["frac_acima_025"] <= 0.05:
        nivel_giria = "GO"
    elif giria["media"] <= 0.15 and giria["frac_acima_025"] <= 0.10:
        nivel_giria = "INCONCLUSIVO"
    else:
        nivel_giria = "NO-GO"
    return {
        "auc": _maior_melhor(principal["auc"], LIMITES_AUC[teste]),
        "ece": "GO" if principal["ece"] <= 0.05 else "INCONCLUSIVO" if principal["ece"] <= 0.10 else "NO-GO",
        "brier_skill": "GO" if principal["brier_skill"] > 0 else "NO-GO",
        "ganho_sobre_lexica": _maior_melhor(principal["auc"] - lexica["auc"], LIMITE_GANHO_LEXICO),
        "distancia_ao_atalho": _maior_melhor(principal["auc"] - controle["auc"], LIMITE_ATALHO),
        "giria_apelido": nivel_giria,
    }


def veredito(niveis) -> str:
    """Regra de agregação: GO só se tudo for GO; qualquer NO-GO → NO-GO; o resto é inconclusivo."""
    niveis = list(niveis)
    if "NO-GO" in niveis:
        return "NO-GO"
    return "GO" if all(n == "GO" for n in niveis) else "INCONCLUSIVO"


# ---------- modelos (3.1, 3.3, 3.4) ----------

def _emb(textos) -> np.ndarray:
    _, nome, revisao, prefixo = MINILM
    return embeddings(list(textos), nome, revisao, prefixo)[0]


def treinar(treino: pd.DataFrame) -> dict:
    """As três linhas de base, sem ajuste de hiperparâmetros (o gate testa o sinal, não o ajuste fino)."""
    y = treino["is_fake"].to_numpy()
    principal = LogisticRegression(max_iter=2000).fit(_emb(treino["claim"]), y)
    lexica = make_pipeline(TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                           LogisticRegression(max_iter=2000)).fit(treino["claim"], y)
    controle = make_pipeline(
        ColumnTransformer([("fonte", OneHotEncoder(handle_unknown="ignore"), ["fonte"]),
                           ("ano", StandardScaler(), ["ano"])]),
        LogisticRegression(max_iter=2000)).fit(treino[["fonte", "ano"]], y)
    return {"principal": lambda d: principal.predict_proba(_emb(d["claim"]))[:, 1],
            "lexica": lambda d: lexica.predict_proba(d["claim"])[:, 1],
            "controle": lambda d: controle.predict_proba(d[["fonte", "ano"]])[:, 1]}


# ---------- gíria e apelido (7.1) ----------

def pares_giria(avaliacao: pd.DataFrame) -> pd.DataFrame:
    """Pares (original, reescrita) de falsas e verdadeiras do período de avaliação + os do teste_reescrita.csv."""
    rng = np.random.default_rng(SEMENTE_GIRIA)
    apelidos, tabela = carregar_apelidos(), carregar_internetes()
    pares = []
    for is_fake, g in avaliacao.groupby("is_fake"):
        for texto in g["claim"].sample(min(POR_CLASSE_GIRIA, len(g)), random_state=SEMENTE_GIRIA):
            trocado = trocar_apelido(texto, apelidos, rng)
            reescritas = {"apelido": trocado[0] if trocado else None,
                          "girias": internetes(texto, tabela, rng)[0],
                          "digitacao": erro_digitacao(texto, rng)[0]}
            pares += [{"original": texto, "reescrita": r, "categoria": c, "is_fake": bool(is_fake), "origem": "avaliacao"}
                      for c, r in reescritas.items() if r and r != texto]
    reescrita_2022 = pd.read_csv(RESULTS / "teste_reescrita.csv")
    reescrita_2022 = reescrita_2022[reescrita_2022["categoria"].isin(CATEGORIAS_GIRIA)]
    pares += [{"original": o, "reescrita": r, "categoria": c, "is_fake": True, "origem": "teste_reescrita_2022"}
              for o, r, c in zip(reescrita_2022["alvo"], reescrita_2022["consulta"], reescrita_2022["categoria"])]
    return pd.DataFrame(pares)


def variacao_giria(prever, pares: pd.DataFrame) -> dict:
    """Critério medido por classe; vale a pior das duas (falso alarme criado e boato escondido pesam igual)."""
    delta = np.abs(prever(pd.DataFrame({"claim": pares["original"]})) - prever(pd.DataFrame({"claim": pares["reescrita"]})))
    por_classe = {f: {"media": float(delta[m].mean()), "frac_acima_025": float((delta[m] > 0.25).mean()), "n": int(m.sum())}
                  for f, m in [("falsas", pares["is_fake"].to_numpy()), ("verdadeiras", ~pares["is_fake"].to_numpy())]}
    return {"media": max(v["media"] for v in por_classe.values()),
            "frac_acima_025": max(v["frac_acima_025"] for v in por_classe.values()),
            "por_classe": por_classe}


# ---------- execução ----------

def main() -> None:
    fontes = {"fakebr": carregar_fakebr(), "fakerecogna": carregar_fakerecogna(),
              "central_de_fatos": carregar_central_rotulada()}
    for origem, d in fontes.items():
        print(f"{origem}: {len(d)} itens políticos; descartes {d.attrs['descartes']}")

    contagens, resultados, criterios = [], [], []
    for teste, desenho in TESTES.items():
        treino, avaliacao = montar(fontes, desenho)
        for lado, d in [("treino", treino), ("avaliacao", avaliacao)]:
            c = d.groupby(["origem", "ano", "is_fake"]).size().rename("n").reset_index()
            contagens.append(c.assign(teste=teste, lado=lado, sha256=assinatura(d)))
        print(f"\n=== Teste {teste}: treino {len(treino)} ({treino['is_fake'].mean():.0%} falsas) | "
              f"avaliação {len(avaliacao)} ({avaliacao['is_fake'].mean():.0%} falsas)")

        prever = treinar(treino)
        y, proporcao = avaliacao["is_fake"].to_numpy(), float(treino["is_fake"].mean())
        m = {nome: metricas(y, f(avaliacao), proporcao) for nome, f in prever.items()}
        for nome, valores in m.items():
            resultados.append({"teste": teste, "modelo": nome, "recorte": "tudo", **valores})
            for origem, g in avaliacao.groupby("origem"):   # Decisão 4: no geral e por fonte
                if g["is_fake"].nunique() == 2:
                    resultados.append({"teste": teste, "modelo": nome, "recorte": origem,
                                       **metricas(g["is_fake"].to_numpy(), prever[nome](g), proporcao)})

        giria = variacao_giria(prever["principal"], pares_giria(avaliacao))
        for classe, v in giria["por_classe"].items():
            resultados.append({"teste": teste, "modelo": "principal", "recorte": f"giria_{classe}",
                               "giria_media": v["media"], "giria_frac_acima_025": v["frac_acima_025"], "n": v["n"]})

        niveis = classificar(teste, m["principal"], m["lexica"], m["controle"], giria)
        valores = {"auc": m["principal"]["auc"], "ece": m["principal"]["ece"], "brier_skill": m["principal"]["brier_skill"],
                   "ganho_sobre_lexica": m["principal"]["auc"] - m["lexica"]["auc"],
                   "distancia_ao_atalho": m["principal"]["auc"] - m["controle"]["auc"],
                   "giria_apelido": f"média {giria['media']:.3f}; >0,25: {giria['frac_acima_025']:.1%}"}
        for criterio, nivel in niveis.items():
            criterios.append({"teste": teste, "criterio": criterio, "valor": valores[criterio], "nivel": nivel})
        print(pd.DataFrame(m).T[["auc", "ece", "brier_skill", "n", "n_falsas"]].round(3).to_string())
        print(pd.DataFrame(criterios)[lambda d: d["teste"] == teste].to_string(index=False))

    final = veredito(c["nivel"] for c in criterios)
    criterios.append({"teste": "A+B", "criterio": "veredito", "valor": "", "nivel": final})
    pd.concat(contagens).to_csv(RESULTS / "gate_conjuntos.csv", index=False)
    pd.DataFrame(resultados).to_csv(RESULTS / "gate_temporal.csv", index=False, float_format="%.4f")
    pd.DataFrame(criterios).to_csv(RESULTS / "gate_criterios.csv", index=False, float_format="%.4f")
    print(f"\nVEREDITO DO GATE (regra de agregação da Decisão 4): {final}")


if __name__ == "__main__":
    main()
