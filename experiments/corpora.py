"""Carrega os corpora: uma linha por alegação, todas as fontes no mesmo esquema.

- 2022: FactPolCheckBr (`data/com_texto_limpo.csv`, saída do 00), sem multi-alegação.
- Central de Fatos 2013–2021, Fake.br e FakeRecogna: FactChecks.br v0.1
  (`data/factchecksbr/FactChecksbr.zip`), lidos com `csv.reader` (o `pd.read_csv` desloca as
  colunas nesses arquivos) e limpos com a mesma `limpar_titulo()`.

Regras de ano, texto, recorte político, rótulo e fonte: design.md da change
`add-fake-news-pattern-scoring`, Decisão 5, "1ª rodada do gate".
"""
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from limpeza import eh_multi_alegacao, limpar_titulo

DATA = Path(__file__).parent / "data"
ZIP = DATA / "factchecksbr" / "FactChecksbr.zip"

POLITICA = {
    "fakebr": {"politica"},
    "fakerecogna": {"política"},
    "central_de_fatos": {"política", "eleições", "eleições 2018", "eleições 2020", "políticas públicas"},
}
ROTULOS = {"1": True, "-1": False}   # is_fake; "0" (sem veredito binário) fica fora
COLUNAS = ["claim", "is_fake", "ano", "fonte", "categoria", "origem"]


def _ler_tsv(membro: str) -> pd.DataFrame:
    csv.field_size_limit(sys.maxsize)
    with zipfile.ZipFile(ZIP) as z, z.open(f"data/{membro}") as f:
        leitor = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
        colunas = next(leitor)
        return pd.DataFrame([dict(zip(colunas, linha)) for linha in leitor])


def _ano(datas: pd.Series) -> pd.Series:
    """As datas misturam formatos (dd/mm/aaaa, aaaa-mm-dd, "2 de março de 2017"): vale o 1º 20xx."""
    return pd.to_numeric(datas.str.extract(r"(20[0-2]\d)")[0])


def _dominio(urls: pd.Series) -> pd.Series:
    """Domínio do veículo sem subdomínio: politica.estadao.com.br → estadao.com.br."""
    host = urls.str.extract(r"https?://([^/]+)")[0].fillna("")
    partes = host.str.split(".")
    return partes.map(lambda p: ".".join(p[-3:] if p[-1:] == ["br"] and len(p) > 2 else p[-2:]))


def _primeira_frase(textos: pd.Series) -> pd.Series:
    """Fake.br não tem título separado: o trecho antes da 1ª quebra/tab/'..' e, nele, a 1ª frase."""
    trecho = textos.str.split(r"\n|\t|\.\.\s", regex=True).str[0]
    return trecho.str.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý\"“'])", regex=True).str[0].str.strip()


def _padronizar(origem: str, titulo: pd.Series, rotulo: pd.Series, datas: pd.Series,
                fonte: pd.Series, categoria: pd.Series, so_politica: bool) -> pd.DataFrame:
    d = pd.DataFrame({"titulo": titulo.str.strip(), "is_fake": rotulo.map(ROTULOS), "ano": _ano(datas),
                      "fonte": fonte, "categoria": categoria, "origem": origem})
    d["claim"] = limpar_titulo(d["titulo"]).str.rstrip(" .")   # só o Fake.br termina em ponto: seria pista de fonte
    filtros = {
        "fora_de_politica": ~d["categoria"].isin(POLITICA[origem]) if so_politica else pd.Series(False, d.index),
        "rotulo_sem_mapeamento": d["is_fake"].isna(),
        "sem_ano": d["ano"].isna(),
        "multi_alegacao": eh_multi_alegacao(d["titulo"]),
        "texto_vazio": d["claim"] == "",
    }
    fora = pd.Series(False, d.index)
    descartes = {}
    for motivo, m in filtros.items():
        descartes[motivo] = int((m & ~fora).sum())   # cada item conta só no 1º motivo
        fora |= m
    d = d[~fora].reset_index(drop=True)
    d["is_fake"] = d["is_fake"].astype(bool)
    d["ano"] = d["ano"].astype(int)
    d = d[COLUNAS]
    d.attrs["descartes"] = descartes
    return d


def carregar_fakebr(so_politica: bool = True) -> pd.DataFrame:
    c = _ler_tsv("fakebr.tsv")
    return _padronizar("fakebr", _primeira_frase(c["claim_text"]), c["is_fake"], c["claim_date"],
                       _dominio(c["claim_url"]), c["category"], so_politica)


def carregar_fakerecogna(so_politica: bool = True) -> pd.DataFrame:
    c = _ler_tsv("FakeRecogna.tsv")
    return _padronizar("fakerecogna", c["review_text"].str.split("\n").str[0], c["is_fake"],
                       c["review_date"], c["review_domain"], c["category"], so_politica)


def carregar_central_rotulada(so_politica: bool = True) -> pd.DataFrame:
    c = _ler_tsv("central_de_fatos.tsv")
    return _padronizar("central_de_fatos", c["review_text"].str.split("\n").str[0], c["is_fake"],
                       c["review_date"], c["review_domain"], c["category"], so_politica)


def carregar_2022() -> pd.DataFrame:
    d = pd.read_csv(DATA / "com_texto_limpo.csv")
    d["idx"] = np.arange(len(d))   # linha no com_texto_limpo.csv (o idx dos pares rotulados)
    d = d[~d["multi_claim"]].reset_index(drop=True)
    return pd.DataFrame({"claim": d["claim"], "origem": "2022", "agencia": d["Agência"],
                         "ano": pd.to_datetime(d["Data da checagem"]).dt.year, "idx": d["idx"]})


def carregar_central() -> pd.DataFrame:
    """Central de Fatos inteira (todas as categorias e rótulos), no formato do índice de busca do 06."""
    c = _ler_tsv("central_de_fatos.tsv")
    titulo = c["review_text"].str.split("\n").str[0].str.strip()
    c = c.assign(claim=limpar_titulo(titulo), multi=eh_multi_alegacao(titulo))
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
