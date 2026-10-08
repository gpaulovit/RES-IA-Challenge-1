"""Compara a consulta com a base e organiza os candidatos."""

from sklearn.metrics.pairwise import cosine_similarity

from checagens.dados import Checagem
from checagens.representacao import Representacao


class Candidato(Checagem):
    pontuacao: float


class Buscador:
    def __init__(self, exemplos: list[Checagem], representacao: Representacao):
        if not exemplos:
            raise ValueError("A busca precisa de pelo menos uma checagem fictícia.")
        self.exemplos = tuple(exemplos)
        self.representacao = representacao
        self.vetores = representacao.preparar([item.alegacao for item in exemplos])

    @property
    def metodo(self) -> str:
        return self.representacao.metodo

    def buscar(self, texto: str, top_k: int = 3) -> list[Candidato]:
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError("Informe um texto com conteúdo para buscar.")
        if type(top_k) is not int or not 1 <= top_k <= 10:
            raise ValueError("top_k deve ser um número inteiro de 1 a 10.")
        consulta = self.representacao.transformar([texto.strip()])
        pontuacoes = cosine_similarity(consulta, self.vetores)[0]
        candidatos = [
            Candidato(**exemplo.model_dump(), pontuacao=min(float(pontuacao), 1.0))
            for exemplo, pontuacao in zip(self.exemplos, pontuacoes, strict=True)
            if pontuacao > 0
        ]
        candidatos.sort(key=lambda item: (-item.pontuacao, item.id))
        return candidatos[:top_k]
