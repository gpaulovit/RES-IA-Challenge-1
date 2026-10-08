#Funções de apoio: limpa o título para virar alegação, detecta checagens de várias alegações, cria as chaves de deduplicação de texto e link e lê os formatos de data.

"""Normalização de texto, link e data usada pelas duas bases (chaves de deduplicação e RF-07)."""

from datetime import date
import re
import unicodedata
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

# --- Limpeza de título: regex copiadas de experiments/limpeza.py (não importadas para o pacote
# não depender de experiments/). Mantê-las iguais às de lá.
PREFIX = re.compile(
    r"^\s*(é\s+(fals[oa]|enganos[oa]|verdadeir[oa]|verdade|exagerad[oa]|impreci[sz][oa]|montagem|mentira|#fake|#fato)"
    r"(?!\w)(\s+que)?|"
    r"não\s+é\s+verdade\s+que|falso:|enganoso:|verdadeiro:|"
    r"(vídeo|mulher|posts?|foto|imagem)\s+(engana|desinforma)\s+ao\s+(afirmar|repetir|dizer)?\s*(que)?)\s*",
    flags=re.IGNORECASE)
SUFFIX = re.compile(r"\s*#boato\s*$", flags=re.IGNORECASE)
CARIMBO = re.compile(r"^\s*boato\s*[–—:-]\s*|\s*#boato(?!\w)|(?<!é )#(fake|fato)(?!\w)", flags=re.IGNORECASE)
ROTULO = re.compile(r"^\s*(#(checamos|verificamos|caiunarede):?|(checamos|verificamos|caiunarede):)\s*",
                    flags=re.IGNORECASE)
MULTI = re.compile(r"veja o que|\d+\s+boatos|o\s+melhor|(checamos|verificamos)\s", flags=re.IGNORECASE)
# --- fim da cópia

# No FACTCK.BR a Lupa perdeu o "É" na coleta ("#Verificamos:  falso que …").
PREFIXO_SEM_E = re.compile(r"^\s*(fals[oa]|verdadeir[oa]|exagerad[oa])\s+que\s+", flags=re.IGNORECASE)
# Nome do site no título do FACTCK.BR ("… | Aos Fatos", "… - Agência Pública", "Agência Lupa - …").
SUFIXO_SITE = re.compile(r"\s*[|–-]\s*(aos fatos|agência pública|agência lupa)\s*$|^\s*(aos fatos|agência pública|agência lupa)\s*[|–-]\s*",
                         flags=re.IGNORECASE)

PARAMETROS_RASTREIO = re.compile(r"^(utm_\w+|fbclid|gclid|igshid|mc_cid|mc_eid|amp)$", flags=re.IGNORECASE)


def limpar_titulo(titulo: str) -> str:
    """Título da checagem → alegação: sem carimbo, rótulo de seção nem prefixo de veredito."""
    t = SUFIXO_SITE.sub("", titulo or "")
    t = CARIMBO.sub("", t)
    t = ROTULO.sub("", t)
    t = PREFIX.sub("", t)
    t = PREFIXO_SEM_E.sub("", t)
    t = SUFFIX.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:1].upper() + t[1:]


def eh_multi_alegacao(titulo: str) -> bool:
    """Checagem de várias alegações ("Veja o que é #FATO ou #FAKE…"): não é um boato único."""
    return bool(MULTI.match(titulo or ""))


def chave_texto(texto: str, sem_acento: bool = False) -> str:
    """Chave de deduplicação: caixa, espaços e pontuação normalizados."""
    t = unicodedata.normalize("NFKC", texto or "").casefold()
    if sem_acento:
        t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s]|_", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def link_valido(link) -> bool:
    return isinstance(link, str) and re.match(r"^https?://[^\s/]+\.[^\s/]+", link.strip()) is not None


def chave_link(link: str) -> str:
    """Link comparável: https, sem www, sem parâmetros de rastreio, fragmento nem barra final."""
    partes = urlsplit(link.strip())
    host = partes.netloc.lower().removeprefix("www.")
    caminho = unquote(partes.path).rstrip("/")
    consulta = urlencode(sorted((k, v) for k, v in parse_qsl(partes.query) if not PARAMETROS_RASTREIO.match(k)))
    return urlunsplit(("https", host, caminho, consulta, ""))


def data_iso(ano: int, mes: int, dia: int, hoje: date | None = None) -> str | None:
    """AAAA-MM-DD se a data existe e está entre 2000 e hoje; senão None."""
    try:
        d = date(ano, mes, dia)
    except ValueError:
        return None
    if not date(2000, 1, 1) <= d <= (hoje or date.today()):
        return None
    return d.isoformat()


def ler_data(texto) -> str | None:
    """Datas sem ambiguidade de ordem: AAAA-MM-DD, AAAA/MM/DD ou DD/MM/AAAA (com ou sem hora)."""
    if not isinstance(texto, str):
        return None
    t = texto.strip()
    if m := re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?:[ T].*)?$", t):
        return data_iso(int(m[1]), int(m[2]), int(m[3]))
    if m := re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", t):
        return data_iso(int(m[3]), int(m[2]), int(m[1]))
    return None


def ler_data_factpolcheckbr(texto) -> tuple[str | None, str]:
    """FactPolCheckBr publica M/D/AAAA; quando o 1º número passa de 12, só vale D/M/AAAA.

    Regra da análise de cobertura de 2022: as datas ambíguas são mês/dia (256 confirmadas pela data
    no link, nenhuma contra). Devolve (data, regra aplicada).
    """
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", str(texto).strip())
    if not m:
        return None, "fora_do_formato"
    a, b, ano = int(m[1]), int(m[2]), int(m[3])
    if a > 12:
        return data_iso(ano, b, a), "dia_mes"
    if b > 12 or a == b:   # dia igual ao mês (ex.: 9/9/2022) dá a mesma data nas duas leituras
        return data_iso(ano, a, b), "mes_dia"
    return data_iso(ano, a, b), "ambigua_lida_mes_dia"


MESES = {m: i for i, m in enumerate(["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
                                     "setembro", "outubro", "novembro", "dezembro"], start=1)}


def ler_data_br(texto) -> str | None:
    """Datas de sites brasileiros: DD/MM/AAAA (com hora opcional), DD/MM/AA, "3 de março de 2015" ou ISO."""
    if not isinstance(texto, str):
        return None
    t = texto.strip().lower()
    if m := re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})(?:\s.*)?$", t):
        ano = int(m[3]) + (2000 if len(m[3]) == 2 else 0)
        return data_iso(ano, int(m[2]), int(m[1]))
    if m := re.match(r"^(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})$", t):
        return data_iso(int(m[3]), MESES[m[2]], int(m[1])) if m[2] in MESES else None
    return ler_data(t)
