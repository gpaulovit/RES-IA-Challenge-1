"""Relatório de cobertura e taxonomia de vereditos do corpus organizado (Domínio de dados)."""

from collections import Counter, defaultdict
from datetime import date
import json
from pathlib import Path
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from checagens.organizacao import CORPUS

RELATORIO = Path("data/relatorios/cobertura-factpolcheckbr.json")

# A fonte já publica vereditos consolidados; o mapeamento só explicita a taxonomia do projeto.
TAXONOMIA = {
    "Falsa": "falso",
    "Parcialmente verdadeira": "parcialmente_verdadeiro",
    "Verdadeira": "verdadeiro",
    None: "sem_veredito",
}

# Marcadores que as agências escrevem no título; indicam o rótulo original, não o substituem.
MARCADORES = {
    "falso": r"\bfals[oa]s?\b",
    "fake": r"#?\bfake\b",
    "boato": r"#?\bboato\b",
    "enganoso": r"\benganos[oa]s?\b|\bengana\b",
    "montagem_ou_editado": r"\bmontage[mn]|\beditad[oa]",
    "fora_de_contexto": r"fora de contexto|tirad[oa] de contexto",
    "distorcido": r"\bdistorc",
}

# Temas exploratórios por palavra-chave: heurística para o relatório, não clusterização.
TEMAS = {
    "urnas_sistema_eleitoral": r"urna|tse|\bvot|eleitor|apura|fraude|seção|mesári|código-fonte|biometria",
    "midia_pesquisas": r"pesquisa|ipec|datafolha|\bglobo\b|\bg1\b|bonner|jornal|reportagem",
    "seguranca_crime": r"crime|pres[oa]\b|prisão|polícia|facção|\bpcc\b|tráfic|\barma|bandid|assassin|atentado",
    "forcas_armadas_instituicoes": r"forças armadas|exército|militar|intervenção|artigo 142|golpe|\bstf\b|moraes",
    "economia_beneficios": r"\bpix\b|auxílio|imposto|salário|inflação|combustível|preço|banc|aposentad|\binss\b|picanha",
    "religiao": r"igreja|evang|católic|cristã|\bdeus\b|pastor|padre|relig|satan|maçon",
    "saude": r"covid|vacina|saúde|\bsus\b|hospital|ivermectina|cloroquina|pandemia",
    "costumes": r"aborto|\bgay|lgbt|gênero|banheiro|ideologia|drog|maconha",
    "meio_ambiente": r"desmat|amazôn|ambient|indígen",
}

LIMIAR_SIMILARIDADE = 0.6
DIAS_RECORRENCIA = 30


def _data_url(link: str | None) -> date | None:
    encontrada = re.search(r"/(20\d\d)/(\d{1,2})/(\d{1,2})/", link or "")
    if not encontrada:
        return None
    try:
        return date(*(int(parte) for parte in encontrada.groups()))
    except ValueError:
        return None


def _data_provavel(data: dict) -> str | None:
    """Data padronizada ou, se ambígua, a leitura mês/dia/ano sustentada pelas URLs."""
    if data["padronizada"]:
        return data["padronizada"]
    formatos = {item["formato"]: item["data"] for item in data["possibilidades"]}
    if data["status"] == "fora_formato_fonte":
        return formatos.get("dia_mes_ano")
    return formatos.get("mes_dia_ano")


def _confirmacao_datas(registros: list[dict]) -> dict:
    resultado = Counter()
    divergentes = []
    for registro in registros:
        data = registro["organizado"]["data"]
        if data["status"] != "ambigua":
            continue
        da_url = _data_url(registro["organizado"]["link"])
        if da_url is None:
            resultado["sem_data_no_link"] += 1
            continue
        formatos = {item["data"]: item["formato"] for item in data["possibilidades"]}
        formato = formatos.get(da_url.isoformat(), "nenhum")
        resultado[formato] += 1
        if formato == "nenhum":
            divergentes.append(registro["numero_origem"])
    return {"contagem": dict(sorted(resultado.items())), "registros_sem_correspondencia": divergentes}


def _sobreposicao(registros: list[dict]) -> dict:
    chave_intervalo = f"pares_com_intervalo_minimo_{DIAS_RECORRENCIA}_dias"
    titulos = [registro["organizado"]["titulo_checagem"] or "" for registro in registros]
    if len(titulos) < 2:
        return {"limiar": LIMIAR_SIMILARIDADE, "registros_com_par": 0,
                "registros_com_par_outra_agencia": 0, chave_intervalo: 0}
    matriz = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit_transform(
        [titulo.lower() for titulo in titulos])
    similaridade = cosine_similarity(matriz)
    datas = [_data_provavel(registro["organizado"]["data"]) for registro in registros]
    agencias = [registro["organizado"]["agencia"] for registro in registros]
    com_par, outra_agencia, pares_distantes = set(), set(), 0
    for i in range(len(registros)):
        for j in range(i + 1, len(registros)):
            if similaridade[i, j] < LIMIAR_SIMILARIDADE:
                continue
            com_par.update((i, j))
            if agencias[i] != agencias[j]:
                outra_agencia.update((i, j))
            if datas[i] and datas[j]:
                intervalo = abs((date.fromisoformat(datas[i]) - date.fromisoformat(datas[j])).days)
                pares_distantes += intervalo >= DIAS_RECORRENCIA
    return {"limiar": LIMIAR_SIMILARIDADE, "registros_com_par": len(com_par),
            "registros_com_par_outra_agencia": len(outra_agencia),
            chave_intervalo: pares_distantes}


def analisar(corpus: dict) -> dict:
    """Mede volume, cobertura temporal/temática e vereditos; não altera o corpus."""
    registros = corpus["registros"]
    organizados = [registro["organizado"] for registro in registros]

    vereditos = Counter(item["veredito_original"] for item in organizados)
    desconhecidos = sorted(rotulo for rotulo in vereditos if rotulo not in TAXONOMIA)
    if desconhecidos:
        raise ValueError(f"Vereditos sem mapeamento na taxonomia: {desconhecidos}")
    por_agencia = defaultdict(Counter)
    marcadores = defaultdict(Counter)
    temas, sem_tema = Counter(), 0
    meses, semanas = Counter(), Counter()
    for item in organizados:
        agencia = item["agencia"] or "(sem agência)"
        por_agencia[agencia][TAXONOMIA[item["veredito_original"]]] += 1
        titulo = (item["titulo_checagem"] or "").lower()
        encontrados = [nome for nome, padrao in MARCADORES.items() if re.search(padrao, titulo)]
        for nome in encontrados or ["sem_marcador"]:
            marcadores[agencia][nome] += 1
        assuntos = [nome for nome, padrao in TEMAS.items() if re.search(padrao, titulo)]
        temas.update(assuntos)
        sem_tema += not assuntos
        provavel = _data_provavel(item["data"])
        if provavel:
            dia = date.fromisoformat(provavel)
            meses[provavel[:7]] += 1
            semanas[f"{dia.isocalendar().year}-S{dia.isocalendar().week:02d}"] += 1

    datas = sorted(meses)
    return {
        "metadados": {**corpus["metadados"], "versao_taxonomia": "1"},
        "total_registros": len(registros),
        "agencias": {agencia: sum(contagem.values()) for agencia, contagem in sorted(por_agencia.items())},
        "taxonomia": {rotulo or "(vazio)": normalizado for rotulo, normalizado in TAXONOMIA.items()},
        "vereditos_normalizados": dict(sorted(Counter(
            TAXONOMIA[rotulo] for rotulo in (item["veredito_original"] for item in organizados)).items())),
        "vereditos_por_agencia": {agencia: dict(sorted(c.items())) for agencia, c in sorted(por_agencia.items())},
        "registros_nao_falsos": [
            {"registro": registro["numero_origem"], "agencia": registro["organizado"]["agencia"],
             "veredito": TAXONOMIA[registro["organizado"]["veredito_original"]],
             "titulo": registro["organizado"]["titulo_checagem"]}
            for registro in registros if registro["organizado"]["veredito_original"] != "Falsa"
        ],
        "marcadores_no_titulo": {agencia: dict(sorted(c.items())) for agencia, c in sorted(marcadores.items())},
        "candidatos_favorecidos": dict(Counter(item["candidatos_favorecidos"] for item in organizados).most_common()),
        "cobertura_temporal": {
            "leitura": "datas padronizadas + ambíguas lidas como mês/dia/ano + fora do formato como dia/mês/ano",
            "inicio": datas[0] if datas else None, "fim": datas[-1] if datas else None,
            "por_mes": dict(sorted(meses.items())), "por_semana": dict(sorted(semanas.items())),
            "confirmacao_ambiguas_pelo_link": _confirmacao_datas(registros),
        },
        "temas_exploratorios": {"contagem": dict(temas.most_common()), "sem_tema": sem_tema,
                                "aviso": "Palavras-chave no título; temas se sobrepõem e não somam o total."},
        "sobreposicao_lexical_titulos": _sobreposicao(registros),
    }


def main() -> None:
    try:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        relatorio = analisar(corpus)
        RELATORIO.parent.mkdir(parents=True, exist_ok=True)
        RELATORIO.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporal = relatorio["cobertura_temporal"]
        print(f"Cobertura: {relatorio['total_registros']} registros, "
              f"{len(relatorio['agencias'])} agências, {temporal['inicio']} a {temporal['fim']}.")
        print(f"Vereditos: {relatorio['vereditos_normalizados']}")
        print(f"Relatório: {RELATORIO}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as erro:
        raise SystemExit(f"Não foi possível gerar a cobertura: {erro}. "
                         "Execute antes python -m checagens.organizacao.") from erro


if __name__ == "__main__":
    main()
