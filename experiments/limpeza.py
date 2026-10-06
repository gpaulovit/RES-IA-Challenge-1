
import re

import pandas as pd

PREFIX = re.compile(
    r"^\s*(é\s+(fals[oa]|enganos[oa]|verdadeir[oa]|verdade|exagerad[oa]|impreci[sz][oa]|montagem|mentira|#fake|#fato)"
    r"(?!\w)(\s+que)?|"
    r"não\s+é\s+verdade\s+que|falso:|enganoso:|verdadeiro:|"
    r"(vídeo|mulher|posts?|foto|imagem)\s+(engana|desinforma)\s+ao\s+(afirmar|repetir|dizer)?\s*(que)?)\s*",
    flags=re.IGNORECASE)

SUFFIX = re.compile(r"\s*#boato\s*$", flags=re.IGNORECASE)

# Carimbo da agência em qualquer posição ("Boato – …", "… #boato …"): sem isso o modelo aprende a agência
# ("É #FAKE que…" fica para o PREFIX, que tira também o "que")
CARIMBO = re.compile(r"^\s*boato\s*[–—:-]\s*|\s*#boato(?!\w)|(?<!é )#(fake|fato)(?!\w)", flags=re.IGNORECASE)

# Rótulo de seção da agência: exige "#" antes ou ":" depois, para não pegar o verbo ("Checamos as alegações de…")
ROTULO = re.compile(r"^\s*(#(checamos|verificamos|caiunarede):?|(checamos|verificamos|caiunarede):)\s*",
                    flags=re.IGNORECASE)

# "Checamos/Verificamos …" sem # nem ":" abre uma checagem de várias alegações
MULTI = re.compile(r"veja o que|\d+\s+boatos|o\s+melhor|(checamos|verificamos)\s", flags=re.IGNORECASE)


def limpar_titulo(titulos: pd.Series) -> pd.Series:
    return (titulos
            .str.replace(CARIMBO, "", regex=True)
            .str.replace(ROTULO, "", regex=True)
            .str.replace(PREFIX, "", regex=True)
            .str.replace(SUFFIX, "", regex=True)
            .str.strip()
            .str.replace(r"^(\w)", lambda m: m.group(1).upper(), regex=True))


def eh_multi_alegacao(titulos: pd.Series) -> pd.Series:
    """True para checagens que cobrem várias alegações e não servem como alvo de busca."""
    return titulos.str.match(MULTI)
