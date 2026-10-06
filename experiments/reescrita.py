"""Reescritas adversariais de alegações para o conjunto de teste (tarefa 3.1).

Cada função recebe uma alegação do corpus e devolve uma versão reescrita, imitando como o
boato chega ao usuário. O alvo da busca é sempre a alegação original, que continua no índice.
Toda aleatoriedade passa por um `rng` (numpy Generator) para o conjunto ser reproduzível.
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

DICIONARIOS = Path(__file__).parent / "dicionarios"

OUTRA_PESSOA = {"Bolsonaro": ["Eduardo", "Flávio", "Carlos", "Michelle", "Jair Renan"]}


def carregar_apelidos() -> pd.DataFrame:
    return pd.read_csv(DICIONARIOS / "apelidos.csv")


def carregar_internetes() -> pd.DataFrame:
    return pd.read_csv(DICIONARIOS / "internetes.csv")


def tirar_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def padrao_palavra(termo: str) -> re.Pattern:
    """Casa o termo como palavra inteira (sem pegar 'Lula' dentro de 'Lulalivre'), sem diferenciar caixa."""
    return re.compile(rf"(?<!\w){re.escape(termo)}(?!\w)", re.IGNORECASE)


def _padrao_entidade(entidade: str) -> re.Pattern:
    excluir = "".join(rf"(?<!{re.escape(nome)} )" for nome in OUTRA_PESSOA.get(entidade, []))
    return re.compile(rf"(?<!\w){excluir}{re.escape(entidade)}(?!\w)", re.IGNORECASE)


def trocar_apelido(texto: str, apelidos: pd.DataFrame, rng):
    """Troca a 1ª menção de uma entidade por um apelido sorteado.

    Entidades mais longas são testadas antes ("Alexandre de Moraes" antes de "Moraes").
    Devolve (texto_novo, entidade, apelido), ou None se o texto não menciona nenhuma entidade.
    """
    for entidade in sorted(apelidos["entidade"].unique(), key=len, reverse=True):
        padrao = _padrao_entidade(entidade)
        if padrao.search(texto):
            opcoes = apelidos.loc[apelidos["entidade"] == entidade, "apelido"].tolist()
            apelido = opcoes[rng.integers(len(opcoes))]
            return padrao.sub(apelido, texto, count=1), entidade, apelido
    return None


# o desmentido costuma explicar depois daqui: pontuação, travessão, "pois/porque/mas"
FIM_DA_ORACAO = re.compile(r"\s*(?:[,;:]|\s[—–-]\s|\.\s)|\s(?:pois|porque|mas)\s", re.IGNORECASE)
# "X é de 2018 e não tem relação com Y" / "mostra A e não B": correção, não negação do boato
NAO_CORRETIVO = re.compile(r"(?<!\w)e\s+não(?!\w)", re.IGNORECASE)
NAO = re.compile(r"(?<!\w)não\s+", re.IGNORECASE)
# títulos que falam de quem espalhou o boato ("Bolsonaro mente ao dizer que..."): o "não" está dentro da citação
ENQUADRAMENTO = re.compile(r"(?<!\w)(ment(e|em|iu)|engan(a|am|ou)|distorce|desinforma|omite|erra|exagera)(?!\w)",
                           re.IGNORECASE)


def tirar_negacao(titulo: str, alegacao: str):
    """Reconstrói o boato a partir do título de desmentido: "Lula não disse que X; vídeo é editado" → "Lula disse que X".

    É o caso mais realista de negação: o usuário manda o boato, e o catálogo guarda o desmentido.
    Devolve None quando a regra não se aplica com segurança:
    - o título original tinha enquadramento de veredito ("É falso que…", "#boato"): aí a alegação
      JÁ é o boato, e o "não" faz parte dele;
    - o título fala de quem espalhou ("X mente ao dizer que…");
    - a 1ª oração não tem exatamente um "não", ele abre a frase ("Não há registros…") ou é
      corretivo ("é de 2018 e não tem relação com…");
    - sobram menos de 4 palavras.
    """
    if titulo.strip() != alegacao.strip() or ENQUADRAMENTO.search(alegacao):
        return None
    oracao = FIM_DA_ORACAO.split(alegacao, maxsplit=1)[0].strip()
    if (len(NAO.findall(oracao)) != 1 or re.match(r"não(?!\w)", oracao, re.IGNORECASE)
            or NAO_CORRETIVO.search(oracao)):
        return None
    boato = NAO.sub("", oracao, count=1)
    return boato if len(boato.split()) >= 4 else None


VIZINHAS = dict(zip("qwertyuiopasdfghjklzxcvbnm", [
    "wa", "qes", "wrd", "etf", "ryg", "tuh", "yij", "uok", "ipl", "o", "qsz", "awdx", "sefc", "drgv", "fthb",
    "gyjn", "hukm", "jil", "kop", "asx", "zdc", "xfv", "cgb", "vhn", "bjm", "nk"]))


def erro_digitacao(texto: str, rng, p_palavra: float = 0.3):
    """Erros de quem digita rápido no celular, em palavras de 4+ letras: troca de letras vizinhas,
    letra apagada, letra duplicada ou tecla ao lado. Devolve (texto_novo, nº de erros)."""
    erros = 0
    palavras = texto.split()
    for k, p in enumerate(palavras):
        if len(p) < 4 or not p.isalpha() or rng.random() >= p_palavra:
            continue
        i = int(rng.integers(1, len(p) - 1))          # nunca a 1ª letra: quase ninguém erra a inicial
        tipo = rng.integers(4)
        if tipo == 0:
            p = p[:i] + p[i + 1] + p[i] + p[i + 2:]
        elif tipo == 1:
            p = p[:i] + p[i + 1:]
        elif tipo == 2:
            p = p[:i] + p[i] + p[i:]
        else:
            vizinhas = VIZINHAS.get(p[i].lower())
            if not vizinhas:
                continue
            p = p[:i] + vizinhas[rng.integers(len(vizinhas))] + p[i + 1:]
        palavras[k] = p
        erros += 1
    return " ".join(palavras), erros


def internetes(texto: str, tabela: pd.DataFrame, rng, p_troca: float = 0.8, p_sem_acento: float = 0.5):
    """Escreve como em mensagem de WhatsApp: abreviações ('vc', 'q', 'naum'), tudo minúsculo,
    parte das palavras sem acento. Devolve (texto_novo, nº de abreviações aplicadas)."""
    trocas = 0
    # padrões mais longos primeiro: "por que" antes de "que"
    for padrao, grupo in sorted(tabela.groupby("padrao"), key=lambda g: len(g[0]), reverse=True):
        formas = grupo["internetes"].tolist()

        def trocar(m):
            nonlocal trocas
            if rng.random() < p_troca:
                trocas += 1
                return formas[rng.integers(len(formas))]
            return m.group(0)

        texto = padrao_palavra(padrao).sub(trocar, texto)
    palavras = [tirar_acento(p) if rng.random() < p_sem_acento else p for p in texto.lower().split()]
    return " ".join(palavras), trocas
