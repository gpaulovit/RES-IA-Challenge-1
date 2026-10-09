#Junta Fake.br e WhatsApp, remove os carimbos, deduplica, divide por data (--corte), gera teste_curtos com o FakeTweet, verifica que não há vazamento e grava os CSVs e o relatório.


"""Base de treino e teste da camada 2: Fake.br-Corpus + FakeWhatsApp.Br (e FakeTweet.Br à parte).

    python -m checagens.bases.treino [--corte AAAA-MM-DD]

Treino: Fake.br inteiro (textos de tamanho igualado) + FakeWhatsApp.Br até a data de corte.
Teste: FakeWhatsApp.Br depois do corte (RN-04: época diferente da do treino).
Teste extra de textos curtos: FakeTweet.Br.

Gera data/processados/treino/{treino,teste,teste_curtos}.csv (texto, rotulo, fonte, data) e o
relatório data/relatorios/treino.json (carimbos removidos, vazamentos, descartes, contagens).
"""

import argparse
from datetime import date
import json
import re
import zipfile

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from checagens.bases.fontes import BRUTOS, PROCESSADOS, RELATORIOS
from checagens.bases.texto import ROTULO, chave_texto, ler_data, ler_data_br

SAIDA = PROCESSADOS / "treino"
COLUNAS = ["texto", "rotulo", "fonte", "data"]
ROTULOS = ("falso", "verdadeiro")
CORTE = date(2018, 9, 15)       # último dia do FakeWhatsApp.Br que entra no treino
MINIMO_PALAVRAS = 5             # o bot pede mais contexto abaixo disso (RF-11)
LIMIAR_QUASE_DUPLICATA = 0.9    # cosseno TF-IDF entre um texto do teste e o mais parecido do treino
SEMENTE = 42

# Carimbos que entregam o rótulo. Removidos de todos os textos, de qualquer classe.
CARIMBOS = {
    # Link de agência de checagem: o endereço carrega o veredito (boatos.org/…, …/e-fake-que-…).
    "link_de_agencia": re.compile(
        r"https?://\s?(?:www\.\s?)?\s?\S*(?:boatos\.org|e-farsas|aosfatos|lupa|fato-ou-fake|checamos\.afp|"
        r"projetocomprova|uol\.com\.br/confere|estadao-verifica)\S*", re.IGNORECASE),
    # Pedaço de link quebrado por espaço ("n oticia/2019/05/03/e-fake-que-…"), comum no FakeTweet.Br.
    "trecho_de_link_com_rotulo": re.compile(r"\S*[/-]\S*(?:fake|fals[oa]|boato|verificamos|checamos)\S*",
                                            re.IGNORECASE),
    # Antes da hashtag, para "É #FAKE que" sair inteiro.
    "e_fake_e_falso": re.compile(
        r"(?<!\w)(é|e|eh)\s+#?(fake(\s?news)?|fals[oa]|boato|mentira)(?!\w)[!.]*(\s+que(?!\w))?", re.IGNORECASE),
    "hashtag_de_rotulo": re.compile(
        r"#\s?(fake\s?news|fakenews|fake|boatos?|fals[oa]|mentira|fato|verdade|verificamos|checamos|"
        r"fatooufake|caiunarede)(?!\w)", re.IGNORECASE),
    "palavra_em_maiusculas": re.compile(r"(?<!\w)(FAKE\s?NEWS|FAKE|FALS[OA]|BOATO|MENTIRA)(?!\w)[!.]*"),
    "prefixo_boato": re.compile(r"^\s*boato\s*[–—:-]\s*", re.IGNORECASE),
    "rotulo_de_secao": ROTULO,
}
# Busca exploratória de outros vazamentos: só contados e reportados, não removidos.
VAZAMENTOS = {
    "palavra_fake_falso_boato_mentira": r"\b(?:fake|fals[oa]s?|boatos?|mentiras?)\b",
    "verificamos_checamos": r"\b(?:verificamos|checamos|checagem|checador)",
    "agencia_de_checagem": r"lupa|aos fatos|boatos\.org|e-farsas|comprova|fato ou fake|afp|uol confere|estadão verifica",
    "estadao_conteudo": r"estadão conteúdo|agência estado",
    "agencia_brasil": r"agência brasil",
    "folha_folhapress": r"folhapress|folha de s\.? ?paulo",
    "reuters_ap_efe": r"\breuters\b|\befe\b|associated press",
    "g1_o_globo": r"\bg1\b|o globo",
    "veja_istoe_revista": r"\bveja\b|istoé|\bépoca\b",
    "leia_mais_veja_tambem": r"leia (?:mais|também)|veja também|saiba mais",
    "link": r"https?://|www\.",
    "compartilhe_repasse": r"compartilh|repass|divulgu",
    "urgente": r"\burgente\b",
    "credito_foto": r"\(foto|foto:|crédito",
}


def remover_carimbos(texto: str) -> tuple[str, list[str]]:
    """Texto sem carimbos de rótulo e a lista dos tipos de carimbo encontrados."""
    achados = []
    for nome, padrao in CARIMBOS.items():
        texto, n = padrao.subn(" ", texto)
        achados += [nome] * n
    texto = re.sub(r"(?<!\S)[*_~!.:-]+(?!\S)", " ", texto)   # formatação que sobrou sozinha ("* *")
    return re.sub(r"\s+", " ", texto).strip(), achados


def carregar_fakebr() -> pd.DataFrame:
    linhas = []
    with zipfile.ZipFile(BRUTOS / "fakebr" / "Fake.br-Corpus.zip") as z:
        nomes = set(z.namelist())
        raiz = z.namelist()[0].split("/")[0]
        for classe, rotulo in [("fake", "falso"), ("true", "verdadeiro")]:
            pasta = f"{raiz}/size_normalized_texts/{classe}/"
            for nome in sorted(n for n in z.namelist() if n.startswith(pasta) and n.endswith(".txt")):
                numero = nome.rsplit("/", 1)[1].removesuffix(".txt")
                # 1468 e 697 não têm metadados no repositório (e 586 e 1607 têm metadados sem texto):
                # ficam sem data, sem adivinhar a correspondência.
                caminho_meta = f"{raiz}/full_texts/{classe}-meta-information/{numero}-meta.txt"
                meta = z.read(caminho_meta).decode("utf-8").splitlines() if caminho_meta in nomes else []
                linhas.append({"texto": z.read(nome).decode("utf-8"), "rotulo": rotulo, "fonte": "Fake.br-Corpus",
                               "data": ler_data_br(meta[3]) if len(meta) > 3 else None})
    return pd.DataFrame(linhas)


def carregar_fakewhatsapp() -> tuple[pd.DataFrame, dict]:
    b = pd.read_csv(BRUTOS / "fakewhatsappbr" / "fakeWhatsApp.BR_2018.csv", low_memory=False,
                    usecols=["date", "midia", "text", "misinformation"])
    info = {"mensagens": int(len(b)), "rotuladas": int((b["misinformation"] != -1).sum())}
    b = b[(b["misinformation"] != -1) & (b["midia"] == 0) & b["text"].notna()]
    d = pd.DataFrame({"texto": b["text"], "rotulo": b["misinformation"].map({1: "falso", 0: "verdadeiro"}),
                      "fonte": "FakeWhatsApp.Br",
                      "data": pd.to_datetime(b["date"], format="%d/%m/%y").dt.strftime("%Y-%m-%d")})
    return d, info


def carregar_faketweet() -> pd.DataFrame:
    b = pd.concat([pd.read_csv(BRUTOS / "faketweetbr" / f) for f in ["FakeTweetBr.csv", "FakeTweetBr-Test.csv"]])
    return pd.DataFrame({"texto": b["text"], "rotulo": b["classificacao"].str.lower().map({"fake": "falso", "true": "verdadeiro"}),
                         "fonte": "FakeTweet.Br", "data": b["date"].map(lambda x: ler_data(str(x)))})


def preparar(d: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Remove carimbos, normaliza espaços e calcula a chave de deduplicação."""
    antes = d["texto"].astype(str)
    limpos = antes.map(remover_carimbos)
    d = d.assign(texto=limpos.str[0], carimbos=limpos.str[1], chave=limpos.str[0].map(lambda t: chave_texto(t, True)))
    exemplos = [{"tipo": tipos[0], "fonte": f, "rotulo": r, "antes": a[:300], "depois": t[:300]}
                for a, t, tipos, f, r in zip(antes, d["texto"], d["carimbos"], d["fonte"], d["rotulo"]) if tipos]
    return d, exemplos


def deduplicar(d: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Uma linha por texto normalizado; a mais antiga fica. Texto com rótulos conflitantes sai todo."""
    conflito = d.groupby("chave")["rotulo"].transform("nunique") > 1
    sem_conflito = d[~conflito].sort_values(["data", "fonte"], na_position="last", kind="stable")
    unicos = sem_conflito.drop_duplicates("chave")
    return unicos, {"rotulo_conflitante": int(conflito.sum()),
                    "texto_repetido": int(len(sem_conflito) - len(unicos))}


def quase_duplicatas(treino: pd.DataFrame, outro: pd.DataFrame, limiar: float = LIMIAR_QUASE_DUPLICATA) -> np.ndarray:
    """Máscara dos textos de `outro` com cosseno TF-IDF ≥ limiar com algum texto do treino."""
    if outro.empty:
        return np.zeros(0, dtype=bool)
    tfidf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(pd.concat([treino["chave"], outro["chave"]]))
    a, b = tfidf.transform(treino["chave"]), tfidf.transform(outro["chave"])
    maximo = np.concatenate([(b[i:i + 500] @ a.T).max(axis=1).toarray().ravel() for i in range(0, b.shape[0], 500)])
    return maximo >= limiar


def verificar(treino: pd.DataFrame, teste: pd.DataFrame, curtos: pd.DataFrame, corte: date) -> dict:
    """Checagens do contrato e de vazamento; levanta AssertionError se alguma falhar."""
    for nome, d in [("treino", treino), ("teste", teste), ("teste_curtos", curtos)]:
        assert list(d.columns) == COLUNAS, nome
        assert d["rotulo"].isin(ROTULOS).all(), nome
        assert not d["texto"].map(chave_texto).duplicated().any(), f"texto duplicado em {nome}"
        assert not any(p.search(t) for t in d["texto"] for p in CARIMBOS.values()), f"carimbo em {nome}"
        assert (d["texto"].str.split().str.len() >= MINIMO_PALAVRAS).all(), nome
    chaves = {n: set(d["texto"].map(lambda t: chave_texto(t, True))) for n, d in
              [("treino", treino), ("teste", teste), ("teste_curtos", curtos)]}
    assert not chaves["treino"] & chaves["teste"], "texto do teste no treino"
    assert not chaves["treino"] & chaves["teste_curtos"] and not chaves["teste"] & chaves["teste_curtos"]
    wpp = treino[treino["fonte"] == "FakeWhatsApp.Br"]
    assert (wpp["data"] <= corte.isoformat()).all() and (teste["data"] > corte.isoformat()).all()
    assert set(teste["fonte"]) == {"FakeWhatsApp.Br"}
    return {"textos_em_comum_treino_teste": 0, "textos_em_comum_com_teste_curtos": 0,
            "teste_todo_depois_do_corte": True, "treino_whatsapp_todo_ate_o_corte": True,
            "carimbos_restantes": 0, "duplicatas_internas": 0}


def _resumo(d: pd.DataFrame) -> dict:
    return {"linhas": int(len(d)),
            "por_rotulo": {k: int(v) for k, v in d["rotulo"].value_counts().sort_index().items()},
            "proporcao_falso": round(float((d["rotulo"] == "falso").mean()), 4) if len(d) else None,
            "por_fonte": {f: {"linhas": int(len(g)),
                              "por_rotulo": {k: int(v) for k, v in g["rotulo"].value_counts().sort_index().items()},
                              "periodo": [g["data"].dropna().min(), g["data"].dropna().max()],
                              "sem_data": int(g["data"].isna().sum())}
                          for f, g in d.groupby("fonte")}}


def _vazamentos(d: pd.DataFrame) -> dict:
    """% de textos com cada padrão, por fonte e rótulo (depois da remoção de carimbos)."""
    saida = {}
    for nome, padrao in VAZAMENTOS.items():
        tem = d["texto"].str.contains(padrao, case=False, regex=True)
        saida[nome] = {f"{f} / {r}": {"textos": int(g.sum()), "pct": round(100 * float(g.mean()), 1)}
                       for (f, r), g in tem.groupby([d["fonte"], d["rotulo"]])}
    return saida


def _contar_carimbos(d: pd.DataFrame) -> dict:
    e = d.explode("carimbos").dropna(subset=["carimbos"])
    return {f"{f} / {r}": {k: int(v) for k, v in g["carimbos"].value_counts().items()}
            for (f, r), g in e.groupby(["fonte", "rotulo"])}


def main(corte: date = CORTE) -> None:
    fakebr = carregar_fakebr()
    wpp, info_wpp = carregar_fakewhatsapp()
    tweets = carregar_faketweet()
    base, exemplos = preparar(pd.concat([fakebr, wpp], ignore_index=True))
    curtos_preparados, exemplos_curtos = preparar(tweets)

    descartes = {}
    curto = base["texto"].str.split().str.len() < MINIMO_PALAVRAS
    descartes["menos_de_5_palavras"] = {k: int(v) for k, v in base[curto]["fonte"].value_counts().items()}
    unicos, dedup = deduplicar(base[~curto])
    descartes.update(dedup)

    eh_treino = (unicos["fonte"] == "Fake.br-Corpus") | (unicos["data"] <= corte.isoformat())
    treino, teste = unicos[eh_treino], unicos[~eh_treino]
    quase = quase_duplicatas(treino, teste)
    exemplos_quase = teste[quase]["texto"].str[:200].head(5).tolist()
    teste = teste[~quase]

    curtos = curtos_preparados[curtos_preparados["texto"].str.split().str.len() >= MINIMO_PALAVRAS]
    descartes_curtos = {"lidos": int(len(curtos_preparados)),
                        "menos_de_5_palavras": int(len(curtos_preparados) - len(curtos))}
    curtos, dedup_curtos = deduplicar(curtos)
    descartes_curtos.update(dedup_curtos)
    ja_na_base = curtos["chave"].isin(set(unicos["chave"]))
    descartes_curtos["texto_igual_ao_de_treino_ou_teste"] = int(ja_na_base.sum())
    curtos = curtos[~ja_na_base]
    quase_curtos = quase_duplicatas(treino, curtos)
    descartes_curtos["quase_duplicata_do_treino"] = int(quase_curtos.sum())
    curtos = curtos[~quase_curtos]

    saidas = {}
    for nome, d in [("treino", treino), ("teste", teste), ("teste_curtos", curtos)]:
        saidas[nome] = d[COLUNAS].sample(frac=1, random_state=SEMENTE).reset_index(drop=True)
    verificacoes = verificar(saidas["treino"], saidas["teste"], saidas["teste_curtos"], corte)

    SAIDA.mkdir(parents=True, exist_ok=True)
    for nome, d in saidas.items():
        d.to_csv(SAIDA / f"{nome}.csv", index=False)

    rng = np.random.default_rng(SEMENTE)
    def amostra(lista, n=3):
        return [lista[i] for i in sorted(rng.choice(len(lista), size=min(n, len(lista)), replace=False))]
    por_tipo = {}
    for e in exemplos:
        por_tipo.setdefault(f"{e['tipo']} | {e['fonte']} / {e['rotulo']}", []).append(e)
    relatorio = {
        "corte": corte.isoformat(),
        "estrategia": "treino = Fake.br-Corpus (size_normalized_texts) + FakeWhatsApp.Br até o corte; "
                      "teste = FakeWhatsApp.Br depois do corte; teste_curtos = FakeTweet.Br",
        "entrada": {"Fake.br-Corpus": int(len(fakebr)), "FakeWhatsApp.Br": {**info_wpp, "rotuladas_texto": int(len(wpp))},
                    "FakeTweet.Br": int(len(tweets))},
        "carimbos_removidos": _contar_carimbos(base),
        "carimbos_removidos_teste_curtos": _contar_carimbos(curtos_preparados),
        "exemplos_carimbos": {k: amostra(v) for k, v in sorted(por_tipo.items())},
        "exemplos_carimbos_teste_curtos": amostra(exemplos_curtos),
        "descartes": descartes,
        "quase_duplicatas_removidas_do_teste": {"limiar_cosseno": LIMIAR_QUASE_DUPLICATA, "total": int(quase.sum()),
                                                 "exemplos": exemplos_quase},
        "teste_curtos_descartes": descartes_curtos,
        "vazamentos_exploratorios_treino_e_teste": _vazamentos(pd.concat([treino, teste])),
        "arquivos": {n: _resumo(d) for n, d in saidas.items()},
        "verificacoes": verificacoes,
    }
    RELATORIOS.mkdir(parents=True, exist_ok=True)
    (RELATORIOS / "treino.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({n: len(d) for n, d in saidas.items()})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corte", type=date.fromisoformat, default=CORTE,
                        help="último dia do FakeWhatsApp.Br no treino (AAAA-MM-DD)")
    main(parser.parse_args().corte)
