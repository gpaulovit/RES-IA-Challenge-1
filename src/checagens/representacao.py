"""Transforma palavras em números, mantendo a técnica substituível."""

from typing import Protocol

from numpy import ndarray
from scipy.sparse import spmatrix
from sklearn.feature_extraction.text import TfidfVectorizer

Matriz = ndarray | spmatrix


class Representacao(Protocol):
    metodo: str

    def preparar(self, textos: list[str]) -> Matriz:
        """Aprende o vocabulário da base e devolve seus vetores."""
        ...

    def transformar(self, textos: list[str]) -> Matriz:
        """Representa consultas usando a mesma preparação da base."""
        ...


class RepresentacaoTfidf:
    metodo = "tfidf_cosseno"

    def __init__(self) -> None:
        self.vetorizador = TfidfVectorizer(lowercase=True, strip_accents="unicode")

    def preparar(self, textos: list[str]) -> Matriz:
        try:
            return self.vetorizador.fit_transform(textos)
        except ValueError as erro:
            raise ValueError(
                "Não foi possível preparar a base: as alegações precisam conter "
                "palavras com pelo menos dois caracteres."
            ) from erro

    def transformar(self, textos: list[str]) -> Matriz:
        return self.vetorizador.transform(textos)
