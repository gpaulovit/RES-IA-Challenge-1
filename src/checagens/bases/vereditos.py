#Taxonomia que leva o rótulo da agência a falso/enganoso/verdadeiro/outro. Extrai o carimbo da agência do título no FactChecks.br e resolve o nome legível da agência.

"""Taxonomia de vereditos (RN-02), carimbos de agência no título e nomes legíveis das agências."""

import re
from urllib.parse import urlsplit

from checagens.bases.texto import chave_texto

NORMALIZADOS = ("falso", "enganoso", "verdadeiro", "outro")

# Rótulo original (chave_texto, sem acento) → normalizado. Vem da TAXONOMIA do antigo
# src/checagens/cobertura.py (FactPolCheckBr), estendida aos rótulos do FACTCK.BR e aos carimbos.
# Rótulo que não estiver aqui vira "outro" e aparece no relatório.
TAXONOMIA = {
    # falso
    "falsa": "falso", "falso": "falso", "fake": "falso", "boato": "falso",
    # enganoso
    "parcialmente verdadeira": "enganoso", "distorcido": "enganoso", "distorcida": "enganoso",
    "exagerado": "enganoso", "exagerada": "enganoso", "sem contexto": "enganoso",
    "impreciso": "enganoso", "imprecisa": "enganoso", "subestimado": "enganoso", "subestimada": "enganoso",
    "enganoso": "enganoso", "enganosa": "enganoso",
    # verdadeiro
    "verdadeira": "verdadeiro", "verdadeiro": "verdadeiro", "verdadeiro mas": "verdadeiro",
    "verdade": "verdadeiro", "fato": "verdadeiro",
    # outro (explícitos; o que não estiver no dicionário também vira outro)
    "impossivel provar": "outro", "ainda e cedo para dizer": "outro", "discutivel": "outro",
    "insustentavel": "outro", "de olho": "outro", "outros": "outro",
}


def normalizar(rotulo_original: str) -> str:
    """Rótulo da agência → falso / enganoso / verdadeiro / outro."""
    chave = chave_texto(rotulo_original, sem_acento=True)
    chave = re.sub(r"^e ", "", chave)  # "É falso", "É #FAKE"
    return TAXONOMIA.get(chave, "outro")


# Carimbos que a própria agência escreve no título. Só eles valem como veredito_original quando a
# base não tem coluna de rótulo (FactChecks.br): o is_fake binário nunca vira rótulo de agência.
# Frases com verbo ("Post engana ao…") e descrições ("É montagem", "É antiga") ficam de fora.
_ROTULOS_E = r"fals[oa]|verdadeir[oa]|verdade|enganos[oa]|exagerad[oa]|distorcid[oa]|impreci[sz][oa]|subestimad[oa]|insustentável"
CARIMBOS = [
    # Fato ou Fake (G1): "É #FAKE que…", "É #FATO que…", "#NÃO É BEM ASSIM"
    re.compile(r"(?P<c>\bé\s+#(?:fake|fato))\b", re.IGNORECASE),
    re.compile(r"(?P<c>#\s?n[ãa]o\s+[ée]\s+bem\s+assim)", re.IGNORECASE),
    # Boatos.org: "… #boato", "Boato: …", "Boato – …"
    re.compile(r"(?P<c>#boato)\b", re.IGNORECASE),
    re.compile(r"^\s*(?P<c>boato)(?=\s*[:–—-])", re.IGNORECASE),
    # "É falso que…", "#Verificamos: É falso que…", "É enganoso…" (só no início do título)
    re.compile(rf"^\s*(?:#\w+:?\s*)?(?P<c>é\s+(?:{_ROTULOS_E}))(?!\w)", re.IGNORECASE),
    # "Falso: …", "Enganoso: …"
    re.compile(rf"^\s*(?:#\w+:?\s*)?(?P<c>(?:{_ROTULOS_E}))(?=\s*:)", re.IGNORECASE),
]


def carimbo_do_titulo(titulo: str) -> str | None:
    """Carimbo de veredito da agência no título, como ela escreveu; None se não houver um só.

    Título com carimbos de sentido diferente (ex.: #FATO e #FAKE) ou em forma de pergunta
    ("É verdade que…?") não tem veredito único e devolve None.
    """
    titulo = (titulo or "").strip()
    if titulo.endswith("?") or re.search(r"#fato\b.*#fake\b|#fake\b.*#fato\b", titulo, re.IGNORECASE):
        return None
    achados = [re.sub(r"\s+", " ", m.group("c")) for padrao in CARIMBOS for m in padrao.finditer(titulo)]
    if not achados or len({normalizar(a) for a in achados}) > 1:
        return None
    return achados[0]


# Domínio do FactChecks.br → nome legível, com os mesmos nomes usados no FactPolCheckBr.
# Domínios que hospedam mais de uma agência são resolvidos pelo host e pelo 1º trecho do caminho.
AGENCIAS_POR_HOST = [
    # (host sem www, prefixo do caminho ou "", nome)
    ("piaui.folha.uol.com.br", "/lupa", "Agência Lupa"),
    ("noticias.uol.com.br", "/confere", "UOL Confere"),
    ("noticias.uol.com.br", "/comprova", "Projeto Comprova"),
    ("noticias.uol.com.br", "", "UOL"),
    ("g1.globo.com", "/fato-ou-fake", "Fato ou Fake"),
    ("g1.globo.com", "", "G1"),
    ("politica.estadao.com.br", "/blogs/estadao-verifica", "Estadão Verifica"),
    ("checamos.afp.com", "", "AFP Checamos"),
    ("boatos.org", "", "Boatos.org"),
    ("aosfatos.org", "", "Aos Fatos"),
    ("projetocomprova.com.br", "", "Projeto Comprova"),
    ("e-farsas.com", "", "E-farsas"),
    ("apublica.org", "", "Agência Pública"),
]
# Último recurso: nome do site pelo domínio informado na base.
SITES_POR_DOMINIO = {
    "uol.com.br": "UOL", "globo.com": "Globo", "estadao.com.br": "Estadão", "afp.com": "AFP",
    "boatos.org": "Boatos.org", "aosfatos.org": "Aos Fatos", "projetocomprova.com.br": "Projeto Comprova",
    "r7.com": "R7", "gov.br": "Governo Federal", "apublica.org": "Agência Pública",
}


def nome_agencia(link: str, dominio: str = "") -> str | None:
    """Nome legível da agência pelo link; se não der, pelo nome do site do domínio."""
    partes = urlsplit(link or "")
    host = partes.netloc.lower().removeprefix("www.")
    for h, prefixo, nome in AGENCIAS_POR_HOST:
        if host == h and partes.path.startswith(prefixo):
            return nome
    return SITES_POR_DOMINIO.get((dominio or "").lower())
