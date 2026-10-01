"""Métricas de busca (Recall@k e MRR), usadas pelo conjunto de teste e pela comparação de modelos.

Busca = k-NN exato por cosseno (embeddings normalizados → produto escalar), como no design.md.

Acertos e exclusões são definidos pelo TEXTO da alegação, não pela linha: o mesmo conjunto de
teste vale para qualquer índice (só 2022, ou 2022 + Central de Fatos).
"""
import numpy as np
import pandas as pd


def linhas_com_texto(claims: pd.Series, textos) -> list[np.ndarray]:
    """Para cada texto, as linhas do índice com essa mesma alegação (sem diferenciar caixa).

    A mesma checagem publicada por agências diferentes aparece várias vezes no corpus. Achar
    qualquer cópia é acerto; sem isso, a cópia de outra agência em 1º lugar contaria como erro.
    """
    chave = claims.str.strip().str.lower().to_numpy()
    grupos = {k: g.to_numpy() for k, g in pd.Series(np.arange(len(chave))).groupby(chave)}
    return [grupos.get(str(t).strip().lower(), np.array([], dtype=int)) for t in textos]


def posicoes(Q: np.ndarray, E: np.ndarray, relevantes: list[np.ndarray], excluir=None) -> np.ndarray:
    """Posição (1 = primeiro) da 1ª alegação relevante no ranking de cada consulta.

    `excluir[q]`: linhas do índice a tirar do ranking da consulta q. Use quando a consulta é ela
    mesma uma alegação do índice (pares reais): sem isso, ela e as cópias dela se acham em 1º
    lugar com cosseno 1,0, e o teste não mede nada.
    """
    assert all(len(r) for r in relevantes), "alguma alegação-alvo não está no índice"
    S = Q @ E.T
    if excluir is not None:
        for q, linhas in enumerate(excluir):
            if linhas is not None and len(linhas):
                S[q, np.atleast_1d(linhas)] = -np.inf
    resultado = np.empty(len(relevantes), dtype=int)
    for q, rel in enumerate(relevantes):
        melhor_relevante = S[q, rel].max()
        resultado[q] = int((S[q] > melhor_relevante).sum()) + 1
    return resultado


def metricas(pos: np.ndarray, ks=(1, 5, 10)) -> dict[str, float]:
    m = {f"recall@{k}": float((pos <= k).mean()) for k in ks}
    m["mrr"] = float((1.0 / pos).mean())
    m["n"] = int(len(pos))
    return m
