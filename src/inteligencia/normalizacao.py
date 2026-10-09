"""Normalização da consulta antes da busca (RF-05): desfaz apelidos e internetês por dicionário.

Só a consulta é normalizada; as alegações da base já vêm em português padrão.
- Apelidos: "Xandão" → "Alexandre de Moraes". Só as linhas com `no_normalizador = sim` (as outras
  são ambíguas: "Barba", "Coiso").
- Internetês: "vc" → "você", "ñ"/"naum" → "não". Isso também ajuda a RN-06, que procura "não".

Os dicionários vêm de experiments/dicionarios/ (01/10/2026) e são usados como estão. Não
acrescente entradas olhando data/testes_benchmark.json: a calibração passaria a medir o
dicionário, e não a busca.

Sem Enelvo: no notebook 05 ele piorou consultas que já chegavam limpas (Recall@1 na negação caiu
de 72% para 65%), e a instalação dele não funciona no Python 3.14.
"""
import csv
import re
from functools import cache
from pathlib import Path

from inteligencia.texto import tirar_acento

DICIONARIOS = Path(__file__).resolve().parent / "dicionarios"
# abreviações que também são palavras comuns: trocar estragaria frases normais ("tão bom" ≠ "estão bom")
AMBIGUAS = {"tão"}


def _ler(nome: str) -> list[dict]:
    with (DICIONARIOS / nome).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _padrao(termos) -> str:
    """Casa o termo inteiro (não pedaço de palavra), com e sem acento."""
    variantes = sorted({v for t in termos for v in (t, tirar_acento(t))}, key=len, reverse=True)
    return rf"(?<!\w)(?:{'|'.join(re.escape(v) for v in variantes)})(?!\w)"


@cache
def _substituicoes() -> list[tuple[re.Pattern, str]]:
    trocas = []
    vistos = set()
    for linha in sorted(_ler("apelidos.csv"), key=lambda l: -len(l["apelido"])):   # "Nove Dedos" antes de "Dedos"
        if linha["no_normalizador"] == "sim" and linha["apelido"] not in vistos:
            vistos.add(linha["apelido"])
            trocas.append((re.compile(_padrao([linha["apelido"]]), re.IGNORECASE), linha["entidade"]))
    por_padrao: dict[str, list[str]] = {}
    for linha in _ler("internetes.csv"):
        if linha["internetes"] not in AMBIGUAS:
            por_padrao.setdefault(linha["padrao"], []).append(linha["internetes"])
    vistos = set()
    for padrao, abreviacoes in por_padrao.items():
        livres = [a for a in abreviacoes if a.lower() not in vistos]   # "pq" vale para "porque", a 1ª linha
        vistos |= {a.lower() for a in livres}
        if livres:
            trocas.append((re.compile(_padrao(livres), re.IGNORECASE), padrao))
    return trocas


def normalizar_consulta(texto: str) -> str:
    for padrao, substituto in _substituicoes():
        texto = padrao.sub(substituto, texto)
    return " ".join(texto.split())
