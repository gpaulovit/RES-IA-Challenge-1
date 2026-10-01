"""Normalização da consulta antes da busca: desfaz apelidos (dicionário próprio) e internetês (Enelvo).

Ordem importa: os apelidos saem ANTES do Enelvo. Sozinho, o Enelvo "corrige" apelidos e nomes
que não conhece para palavras parecidas do léxico dele ("xandao" → "danton", "pix" → "pia").

Enelvo (NILC/USP, MIT) instalado com `--no-deps`: o `gensim` não compila no Python 3.14 e só é
usado num modo opcional de geração de candidatos por embeddings, que não usamos aqui.
"""
import re
from pathlib import Path

import pandas as pd
from enelvo import normaliser

from reescrita import tirar_acento


def criar_enelvo(protegidos: set[str], caminho_lista: Path) -> normaliser.Normaliser:
    caminho_lista.write_text("\n".join(sorted(protegidos)) + "\n", encoding="utf-8")
    return normaliser.Normaliser(tokenizer="readable", ig_list=str(caminho_lista), capitalize_pns=True)


def vocabulario_protegido(textos: pd.Series, internetes: pd.DataFrame) -> set[str]:
    vocab = {p for t in textos for p in re.findall(r"\w+", t.lower()) if len(p) >= 2}
    abreviacoes = {f.lower() for f in internetes["internetes"]}
    return vocab - abreviacoes


def desfazer_apelidos(texto: str, apelidos: pd.DataFrame) -> str:
    usados = apelidos[apelidos["no_normalizador"] == "sim"].drop_duplicates("apelido")
    for apelido, entidade in sorted(zip(usados["apelido"], usados["entidade"]), key=lambda x: -len(x[0])):
        variantes = "|".join(re.escape(v) for v in {apelido, tirar_acento(apelido)})
        texto = re.sub(rf"(?<!\w)(?:{variantes})(?!\w)", entidade, texto, flags=re.IGNORECASE)
    return texto


def normalizar(texto: str, enelvo: normaliser.Normaliser, apelidos: pd.DataFrame | None = None) -> str:
    if apelidos is not None:
        texto = desfazer_apelidos(texto, apelidos)
    return enelvo.normalise(texto)


def tem_internetes(texto: str, internetes: pd.DataFrame) -> bool:
    """A consulta tem cara de mensagem informal? (alguma abreviação do dicionário, ou tudo minúsculo e sem acento)

    Na consulta que já chega limpa, o Enelvo só atrapalha (põe nomes em minúscula, troca palavras):
    na negação, o Recall@1 caiu de 72% para 65% com ele. Daí a normalização condicional.
    """
    palavras = set(re.findall(r"\S+", texto.lower()))
    if palavras & {f.lower() for f in internetes["internetes"]}:
        return True
    return texto == texto.lower() and texto == tirar_acento(texto) and len(texto.split()) >= 4


def normalizar_se_preciso(texto: str, enelvo: normaliser.Normaliser, apelidos: pd.DataFrame,
                          internetes: pd.DataFrame) -> str:
    """Apelidos sempre (o dicionário é exato); Enelvo só se a consulta tiver cara de internetês."""
    texto = desfazer_apelidos(texto, apelidos)
    return enelvo.normalise(texto) if tem_internetes(texto, internetes) else texto
