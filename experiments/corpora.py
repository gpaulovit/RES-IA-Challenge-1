"""Carrega os corpora prontos para indexar: uma linha por alegação, com origem e ano.

- 2022: FactPolCheckBr (`data/com_texto_limpo.csv`, saída do 00), sem multi-alegação.
- Central de Fatos 2013–2021: FactChecks.br v0.1 (`data/factchecksbr/central_de_fatos.tsv`), lida com
  `csv.reader` (o `pd.read_csv` desloca as colunas neste arquivo) e limpa com a mesma `limpar_titulo()`.
"""
import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from limpeza import eh_multi_alegacao, limpar_titulo

DATA = Path(__file__).parent / "data"


def carregar_2022() -> pd.DataFrame:
    d = pd.read_csv(DATA / "com_texto_limpo.csv")
    d["idx"] = np.arange(len(d))   # linha no com_texto_limpo.csv (o idx dos pares rotulados)
    d = d[~d["multi_claim"]].reset_index(drop=True)
    return pd.DataFrame({"claim": d["claim"], "origem": "2022", "agencia": d["Agência"],
                         "ano": pd.to_datetime(d["Data da checagem"]).dt.year, "idx": d["idx"]})


def carregar_central() -> pd.DataFrame:
    csv.field_size_limit(sys.maxsize)
    with open(DATA / "factchecksbr" / "central_de_fatos.tsv", encoding="utf-8") as f:
        leitor = csv.reader(f, delimiter="\t")
        colunas = next(leitor)
        c = pd.DataFrame([dict(zip(colunas, linha)) for linha in leitor])
    titulo = c["review_text"].str.split("\n").str[0].str.strip()
    c = c.assign(titulo=titulo, claim=limpar_titulo(titulo), multi=eh_multi_alegacao(titulo))
    c = c[~c["multi"] & (c["claim"] != "")].reset_index(drop=True)
    return pd.DataFrame({"claim": c["claim"], "origem": "central_de_fatos", "agencia": c["review_domain"],
                         "ano": pd.to_datetime(c["review_date"]).dt.year, "idx": np.arange(len(c))})


def carregar_indice(qual: str) -> pd.DataFrame:
    """`qual` = "2022" (preliminar) ou "ambos" (a avaliação definitiva)."""
    if qual == "2022":
        return carregar_2022()
    if qual == "ambos":
        return pd.concat([carregar_2022(), carregar_central()], ignore_index=True)
    raise ValueError(qual)
