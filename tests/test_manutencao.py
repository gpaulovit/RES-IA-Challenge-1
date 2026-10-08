"""Testes automatizados de manutenção do índice sem retreino (RNF-11).

Comprova que uma nova checagem entra na base apenas reindexando os vetores,
sem exigir retreino do classificador de texto.
"""

from pathlib import Path
import numpy as np

from checagens.embeddings import BaselineHashing
from checagens.retrieval import buscar


def test_nova_checagem_entra_apenas_reindexando(tmp_path: Path):
    gerador = BaselineHashing()

    # 1. Base inicial com 2 checagens
    textos_iniciais = [
        "Vacina da gripe está liberada para toda a população",
        "Transporte público será gratuito no próximo domingo",
    ]
    vetores_iniciais = gerador.gerar(textos_iniciais)
    metadados_iniciais = [
        {"id": "c1", "linha_vetor": 0, "texto_indexado": textos_iniciais[0]},
        {"id": "c2", "linha_vetor": 1, "texto_indexado": textos_iniciais[1]},
    ]

    # Consulta sobre uma nova notícia não cadastrada ainda
    nova_noticia = "TSE anuncia abertura de inscrições para mesários voluntários"
    candidatos_antes = buscar(
        texto=nova_noticia,
        top_k=1,
        vetores=vetores_iniciais,
        metadados=metadados_iniciais,
        gerador=gerador,
    )
    # Antes, a checagem não existia
    assert candidatos_antes[0]["id"] in {"c1", "c2"}

    # 2. Reindexação com a nova checagem adicionada (sem retreinar nenhum modelo)
    textos_atualizados = textos_iniciais + [nova_noticia]
    vetores_atualizados = gerador.gerar(textos_atualizados)
    metadados_atualizados = metadados_iniciais + [
        {"id": "c3_nova", "linha_vetor": 2, "texto_indexado": nova_noticia}
    ]

    candidatos_depois = buscar(
        texto="Inscrições para mesários voluntários no TSE",
        top_k=1,
        vetores=vetores_atualizados,
        metadados=metadados_atualizados,
        gerador=gerador,
    )

    # A nova checagem é recuperada com sucesso após a reindexação
    assert candidatos_depois[0]["id"] == "c3_nova"
    assert candidatos_depois[0]["pontuacao"] > 0.0
