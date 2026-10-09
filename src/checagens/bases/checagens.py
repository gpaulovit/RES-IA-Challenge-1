#Junta as 4 fontes, descarta sem link, data ou veredito, deduplica, valida o contrato e grava checagens.json, a amostra de 30 e o relatório.

"""Base de checagens da camada 1: FactPolCheckBr + FACTCK.BR + FactChecks.br + Google Fact Check Tools.

    python -m checagens.bases.checagens

Gera data/processados/checagens/checagens.json, a amostra de 30 checagens recentes e o relatório
data/relatorios/checagens.json (descartes, duplicatas, mapeamento de vereditos, contagens).
"""

import csv
import io
import json
from pathlib import Path
import sys
import zipfile

import pandas as pd

from checagens.bases.fontes import BRUTOS, PROCESSADOS, RELATORIOS
from checagens.bases.texto import (chave_link, chave_texto, eh_multi_alegacao, ler_data,
                                   ler_data_factpolcheckbr, limpar_titulo, link_valido)
from checagens.bases.vereditos import NORMALIZADOS, carimbo_do_titulo, nome_agencia, normalizar

SAIDA = PROCESSADOS / "checagens"
CAMPOS = ["id", "alegacao", "veredito_original", "veredito_normalizado", "agencia", "data", "link",
          "fonte_dataset"]
TAMANHO_AMOSTRA = 30
MAXIMO_POR_AGENCIA = 4
# Em duplicata, fica o registro da base com o rótulo mais rico (rótulo da agência em coluna própria).
PRIORIDADE = ["FACTCK.BR", "FactPolCheckBr", "FactChecks.br/Central de Fatos", "FactChecks.br/FakeRecogna",
              "Google Fact Check Tools"]
# Checagens recentes baixadas por scripts/atualizar_checagens_factcheck.py (versionadas no git).
GOOGLE_FACTCHECK = Path("data/externos/google_factcheck.json")


def _base(fonte: str, ids, titulos, vereditos, agencias, datas, links) -> pd.DataFrame:
    d = pd.DataFrame({"id": ids, "titulo": titulos, "veredito_original": vereditos, "agencia": agencias,
                      "data": datas, "link": links})
    d["fonte_dataset"] = fonte
    d["titulo"] = d["titulo"].fillna("").astype(str).str.strip()
    d["alegacao"] = d["titulo"].map(limpar_titulo)
    d["veredito_normalizado"] = d["veredito_original"].map(lambda v: normalizar(v) if isinstance(v, str) else None)
    d["motivo"] = None
    return d


def _descartar(d: pd.DataFrame, mascara: pd.Series, motivo: str) -> None:
    """Marca o motivo só nos registros ainda sem motivo: cada descarte conta uma vez, no 1º motivo."""
    d.loc[mascara & d["motivo"].isna(), "motivo"] = motivo


def _filtros_comuns(d: pd.DataFrame) -> pd.DataFrame:
    _descartar(d, ~d["link"].map(link_valido), "sem_link")
    _descartar(d, d["data"].isna(), "sem_data")
    _descartar(d, d["veredito_original"].isna(), "sem_veredito")
    _descartar(d, d["titulo"].map(eh_multi_alegacao), "multi_alegacao")
    _descartar(d, d["alegacao"].str.split().str.len().fillna(0) < 3, "alegacao_vazia_ou_curta")
    _descartar(d, d["agencia"].isna(), "agencia_desconhecida")
    return d


def carregar_factpolcheckbr() -> pd.DataFrame:
    b = pd.read_csv(BRUTOS / "factpolcheckbr" / "com_texto.csv")
    datas = b["Data da checagem"].map(ler_data_factpolcheckbr)
    d = _base("FactPolCheckBr", [f"factpolcheckbr-{i:04d}" for i in range(len(b))], b["Título da checagem"],
              b["Natureza da notícia"], b["Agência"], datas.str[0], b["Link"])
    d["regra_data"] = datas.str[1]
    return _filtros_comuns(d)


def carregar_factckbr() -> pd.DataFrame:
    b = pd.read_csv(BRUTOS / "factckbr" / "FACTCKBR.tsv", sep="\t")
    d = _base("FACTCK.BR", [f"factckbr-{i:04d}" for i in range(len(b))], b["title"], b["alternativeName"],
              [nome_agencia(u) for u in b["URL"]], b["datePublished"].map(ler_data), b["URL"])
    d = _filtros_comuns(d)
    # Artigo com várias alegações: uma linha por alegação, mesmo link e rótulos diferentes. O título
    # não diz a qual alegação o rótulo se refere, então nenhuma delas entra.
    _descartar(d, b["URL"].duplicated(keep=False), "varias_alegacoes_no_mesmo_link")
    return d


def _ler_factchecksbr(membro: str) -> pd.DataFrame:
    # pd.read_csv desloca as colunas nesses TSVs (ver experiments/corpora.py); csv.reader não.
    csv.field_size_limit(sys.maxsize)
    with zipfile.ZipFile(BRUTOS / "factchecksbr" / "FactChecksbr.zip") as z, z.open(f"data/{membro}") as f:
        leitor = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
        colunas = next(leitor)
        return pd.DataFrame([dict(zip(colunas, linha)) for linha in leitor])


def _carregar_factchecksbr(membro: str, fonte: str, prefixo: str, so_fake: bool) -> pd.DataFrame:
    b = _ler_factchecksbr(membro)
    titulos = b["review_text"].str.split("\n").str[0]
    carimbos = titulos.map(carimbo_do_titulo)
    d = _base(fonte, [f"{prefixo}{i:05d}" for i in range(len(b))], titulos, carimbos,
              [nome_agencia(u, dom) for u, dom in zip(b["review_url"], b["review_domain"])],
              b["review_date"].map(ler_data), b["review_url"])
    d["is_fake"] = b["is_fake"]
    if so_fake:
        _descartar(d, d["is_fake"] != "1", "is_fake_diferente_de_1")
    # Sem carimbo da agência no título não há veredito_original: o is_fake nunca vira rótulo.
    _descartar(d, d["veredito_original"].isna(), "sem_carimbo_da_agencia")
    conflito = (d["veredito_normalizado"].isin(["falso", "enganoso"]) & (d["is_fake"] == "-1")) | \
               ((d["veredito_normalizado"] == "verdadeiro") & (d["is_fake"] == "1"))
    _descartar(d, conflito, "carimbo_contradiz_is_fake")
    return _filtros_comuns(d)


def carregar_central_de_fatos() -> pd.DataFrame:
    return _carregar_factchecksbr("central_de_fatos.tsv", "FactChecks.br/Central de Fatos", "centraldefatos-", False)


def carregar_fakerecogna() -> pd.DataFrame:
    return _carregar_factchecksbr("FakeRecogna.tsv", "FactChecks.br/FakeRecogna", "fakerecogna-", True)


def carregar_google_factcheck() -> pd.DataFrame:
    """Checagens recentes (Google Fact Check Tools). Sem o arquivo, a fonte entra vazia."""
    if not GOOGLE_FACTCHECK.exists():
        return _base("Google Fact Check Tools", [], [], [], [], [], [])
    b = pd.DataFrame(json.loads(GOOGLE_FACTCHECK.read_text(encoding="utf-8")))
    d = _base("Google Fact Check Tools", [f"googlefc-{i:05d}" for i in range(len(b))], b["alegacao"],
              b["veredito_original"], [nome_agencia(u) for u in b["link"]], b["data"].map(ler_data), b["link"])
    return _filtros_comuns(d)


def deduplicar(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove duplicatas por link normalizado e, depois, por alegação normalizada.

    Antes, tira todos os registros de um link que aparece com vereditos normalizados diferentes.

    Devolve (mantidos, removidos); em `removidos`, a coluna `mantido` diz qual id ficou no lugar.
    """
    d = d.assign(_prio=d["fonte_dataset"].map(PRIORIDADE.index), _ordem=range(len(d)))
    d = d.sort_values(["_prio", "_ordem"]).assign(chave_link=lambda x: x["link"].map(chave_link),
                                                  chave_alegacao=lambda x: x["alegacao"].map(chave_texto))
    # Mesmo link com vereditos diferentes entre as bases: não dá para saber qual vale, saem todos.
    conflito = d.groupby("chave_link")["veredito_normalizado"].transform("nunique") > 1
    removidos = [d[conflito].assign(criterio="veredito_conflitante_no_mesmo_link", mantido=None)]
    d = d[~conflito]
    for criterio, chave in [("mesmo_link", "chave_link"), ("mesma_alegacao", "chave_alegacao")]:
        primeiro = d.groupby(chave)["id"].transform("first")
        dup = d["id"] != primeiro
        removidos.append(d[dup].assign(criterio=criterio, mantido=primeiro[dup]))
        d = d[~dup]
    return d.drop(columns=["_prio", "_ordem"]), pd.concat(removidos).drop(columns=["_prio", "_ordem"])


def amostra_recente(d: pd.DataFrame, n: int = TAMANHO_AMOSTRA, maximo_por_agencia: int = MAXIMO_POR_AGENCIA) -> pd.DataFrame:
    """As n checagens mais recentes, com no máximo `maximo_por_agencia` de cada agência."""
    d = d.sort_values(["data", "id"], ascending=[False, True])
    return d[d.groupby("agencia").cumcount() < maximo_por_agencia].head(n)


def validar(registros: list[dict]) -> None:
    """Contrato do checagens.json (combinado com Engenharia e Modelos de IA)."""
    links, alegacoes, ids = set(), set(), set()
    for r in registros:
        assert list(r) == CAMPOS, r
        assert all(isinstance(r[c], str) and r[c].strip() for c in CAMPOS), r
        assert r["veredito_normalizado"] in NORMALIZADOS, r
        assert ler_data(r["data"]) == r["data"], r
        assert link_valido(r["link"]), r
        for conjunto, valor in [(ids, r["id"]), (links, chave_link(r["link"])), (alegacoes, chave_texto(r["alegacao"]))]:
            assert valor not in conjunto, f"duplicata: {valor}"
            conjunto.add(valor)


def _contagem(serie: pd.Series) -> dict:
    return {str(k): int(v) for k, v in serie.value_counts().sort_index().items()}


def relatorio(todos: pd.DataFrame, mantidos: pd.DataFrame, removidos: pd.DataFrame, amostra: pd.DataFrame) -> dict:
    validos = todos[todos["motivo"].isna()]
    fonte_por_id = dict(zip(todos["id"], todos["fonte_dataset"]))
    fk = todos[todos["fonte_dataset"] == "FACTCK.BR"]
    por_link = fk.groupby("link")["veredito_original"].agg(["size", "nunique"])
    por_link = por_link[por_link["size"] > 1]
    factckbr_multi = {"links": int(len(por_link)), "linhas": int(por_link["size"].sum()),
                      "links_com_rotulos_diferentes": int((por_link["nunique"] > 1).sum())}
    fc = todos[todos["fonte_dataset"].str.startswith("FactChecks.br")]
    fc = fc[fc["motivo"] != "is_fake_diferente_de_1"]
    carimbo_por_agencia = (fc.assign(agencia=fc["agencia"].fillna("(desconhecida)"),
                                     com_carimbo=fc["veredito_original"].notna())
                           .groupby(["fonte_dataset", "agencia"])["com_carimbo"].agg(["size", "sum"]))
    return {
        "lidos_por_fonte": _contagem(todos["fonte_dataset"]),
        "descartes_por_fonte_e_motivo": {
            f: _contagem(g["motivo"].dropna()) for f, g in todos.groupby("fonte_dataset")},
        "validos_por_fonte": _contagem(validos["fonte_dataset"]),
        "duplicatas_removidas": {
            "criterio": "primeiro saem todos os registros de um link com vereditos normalizados diferentes; "
                        "depois, duplicatas por link normalizado (https, sem www, sem utm_*/fbclid/gclid/igshid/amp, "
                        "sem fragmento nem barra final, caminho decodificado) e por alegação normalizada (NFKC, "
                        "caixa, pontuação e espaços); fica o registro da fonte mais prioritária: " + " > ".join(PRIORIDADE),
            "total": int(len(removidos)),
            "por_criterio": _contagem(removidos["criterio"]),
            "por_fonte_removida": _contagem(removidos["fonte_dataset"]),
            "por_par_removida_mantida": _contagem(
                removidos["fonte_dataset"] + " -> " + removidos["mantido"].map(fonte_por_id).fillna("(nenhuma)")),
        },
        "factckbr_links_com_varias_alegacoes": factckbr_multi,
        "final": {
            "total": int(len(mantidos)),
            "por_fonte": _contagem(mantidos["fonte_dataset"]),
            "por_agencia": _contagem(mantidos["agencia"]),
            "por_veredito_normalizado": _contagem(mantidos["veredito_normalizado"]),
            "periodo_por_fonte": {f: [g["data"].min(), g["data"].max()] for f, g in mantidos.groupby("fonte_dataset")},
            "periodo": [mantidos["data"].min(), mantidos["data"].max()],
            "por_ano": _contagem(mantidos["data"].str[:4]),
        },
        "por_fonte_e_veredito": {f: _contagem(g["veredito_normalizado"]) for f, g in mantidos.groupby("fonte_dataset")},
        "cobertura_2022": {
            "por_mes": _contagem(mantidos.loc[mantidos["data"].str[:4] == "2022", "data"].str[:7]),
            "por_agencia": _contagem(mantidos.loc[mantidos["data"].str[:4] == "2022", "agencia"]),
        },
        "mapeamento_vereditos": [
            {"fonte_dataset": f, "veredito_original": o, "veredito_normalizado": n, "registros": int(c)}
            for (f, o, n), c in mantidos.groupby(["fonte_dataset", "veredito_original", "veredito_normalizado"]).size().items()],
        "factchecksbr_carimbo_por_agencia": [
            {"fonte_dataset": f, "agencia": a, "registros": int(r["size"]), "com_carimbo": int(r["sum"]),
             "sem_carimbo": int(r["size"] - r["sum"])} for (f, a), r in carimbo_por_agencia.iterrows()],
        "factpolcheckbr_regra_data": _contagem(todos.loc[todos["fonte_dataset"] == "FactPolCheckBr", "regra_data"]),
        "amostra_teste_30": {"por_agencia": _contagem(amostra["agencia"]),
                             "periodo": [amostra["data"].min(), amostra["data"].max()]},
    }


def _gravar_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    todos = pd.concat([carregar_factpolcheckbr(), carregar_factckbr(), carregar_central_de_fatos(),
                       carregar_fakerecogna(), carregar_google_factcheck()], ignore_index=True)
    mantidos, removidos = deduplicar(todos[todos["motivo"].isna()])
    mantidos = mantidos.sort_values(["data", "id"], ascending=[False, True])
    amostra = amostra_recente(mantidos)
    registros = mantidos[CAMPOS].to_dict("records")
    validar(registros)
    _gravar_json(SAIDA / "checagens.json", registros)
    _gravar_json(SAIDA / "amostra_teste_30.json", amostra[CAMPOS].to_dict("records"))
    _gravar_json(RELATORIOS / "checagens.json", relatorio(todos, mantidos, removidos, amostra))
    print(f"{len(registros)} checagens; {len(removidos)} duplicatas removidas; "
          f"{int(todos['motivo'].notna().sum())} descartes")


if __name__ == "__main__":
    main()