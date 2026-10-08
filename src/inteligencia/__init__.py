"""Inteligência do bot: busca de checagens (camada 1) e sinais de alerta (camada 2).

Contrato com o bot (mudou? avise a Engenharia):
    from inteligencia import buscar, classificar
    buscar(texto: str, k: int = 3) -> list[dict]     # RF-06, RN-05, RN-06
    classificar(texto: str) -> dict                  # RF-08; só exibir com go (RN-04)
"""
from inteligencia.busca import buscar
from inteligencia.classificador import classificar

__all__ = ["buscar", "classificar"]
