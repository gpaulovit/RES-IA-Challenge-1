"""Normalização de texto compartilhada pelas duas camadas."""
import re
import unicodedata


def tirar_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Minúsculo, sem acento, sem pontuação e com espaços simples: "a  NOTÍCIA!" → "a noticia"."""
    return " ".join(re.sub(r"[^\w\s]", " ", tirar_acento(texto).lower()).split())
