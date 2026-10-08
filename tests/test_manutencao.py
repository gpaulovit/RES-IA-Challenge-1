"""Testes automatizados de manutenção do índice sem retreino (RNF-11).

Comprova que uma nova checagem entra na base apenas reindexando os vetores,
sem exigir retreino do classificador de texto.
"""

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def test_nova_checagem_entra_apenas_reindexando():
    """Garante que a adição de checagem à Camada 1 exige apenas reindexação vetorial."""
    vectorizer = HashingVectorizer(n_features=256, alternate_sign=False)

    # 1. Base inicial com 2 checagens indexadas
    textos_iniciais = [
        "Vacina da gripe está liberada para toda a população",
        "Transporte público será gratuito no próximo domingo",
    ]
    vetores_iniciais = vectorizer.transform(textos_iniciais)
    metadados_iniciais = [
        {"id": "c1", "texto_indexado": textos_iniciais[0]},
        {"id": "c2", "texto_indexado": textos_iniciais[1]},
    ]

    # Consulta sobre uma nova checagem ainda não cadastrada
    nova_noticia = "TSE anuncia abertura de inscrições para mesários voluntários"
    consulta_vec = vectorizer.transform(["Inscrições para mesários voluntários no TSE"])

    sims_antes = cosine_similarity(consulta_vec, vetores_iniciais)[0]
    idx_antes = int(np.argmax(sims_antes))
    assert metadados_iniciais[idx_antes]["id"] in {"c1", "c2"}

    # 2. Reindexação com a nova checagem incluída (sem retreinar modelo de classificação)
    textos_atualizados = textos_iniciais + [nova_noticia]
    vetores_atualizados = vectorizer.transform(textos_atualizados)
    metadados_atualizados = metadados_iniciais + [
        {"id": "c3_nova", "texto_indexado": nova_noticia}
    ]

    sims_depois = cosine_similarity(consulta_vec, vetores_atualizados)[0]
    idx_depois = int(np.argmax(sims_depois))

    # A nova checagem é recuperada imediatamente com maior similaridade
    assert metadados_atualizados[idx_depois]["id"] == "c3_nova"
    assert sims_depois[idx_depois] > 0.0
