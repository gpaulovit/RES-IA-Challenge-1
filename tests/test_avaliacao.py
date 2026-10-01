"""Testes automatizados para o módulo de avaliação de benchmark (MLOps)."""

import json
from pathlib import Path

import pytest

from checagens.avaliacao import (
    avaliar_benchmark,
    carregar_benchmark,
    formatar_tabela_resumo,
)
from checagens.embeddings import BaselineHashing, criar_gerador
from checagens.retrieval import carregar_indice


def test_carregar_benchmark_real():
    caminho = Path("data/testes_benchmark.json")
    benchmark = carregar_benchmark(caminho)
    assert isinstance(benchmark, list)
    assert len(benchmark) == 62

    # Confere que os 62 casos contêm os campos obrigatórios
    for item in benchmark:
        assert "id_teste" in item
        assert "tipo" in item
        assert "texto_testado" in item
        assert "resultado_esperado" in item


def test_carregar_benchmark_rejeita_invalido(tmp_path):
    caminho_vazio = tmp_path / "vazio.json"
    caminho_vazio.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="lista não vazia"):
        carregar_benchmark(caminho_vazio)

    caminho_id_duplicado = tmp_path / "duplicado.json"
    caminho_id_duplicado.write_text(
        json.dumps([
            {"id_teste": 1, "tipo": "giria", "texto_testado": "abc", "resultado_esperado": "sem_match"},
            {"id_teste": 1, "tipo": "giria", "texto_testado": "def", "resultado_esperado": "sem_match"},
        ]),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="repetido"):
        carregar_benchmark(caminho_id_duplicado)

    caminho_esperado_invalido = tmp_path / "esperado_invalido.json"
    caminho_esperado_invalido.write_text(
        json.dumps([
            {"id_teste": 1, "tipo": "giria", "texto_testado": "abc", "resultado_esperado": "invalido"},
        ]),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="resultado_esperado"):
        carregar_benchmark(caminho_esperado_invalido)


def test_avaliar_benchmark_com_amostra(tmp_path):
    # Cria uma base pequena e um benchmark fictício para teste controlado
    gerador = BaselineHashing()
    textos = [
        "A prefeitura anunciou transporte gratuito aos domingos",
        "Vacina contra gripe está disponível nos postos de saúde",
    ]
    vetores = gerador.gerar(textos)
    metadados = [
        {"id": "doc1", "linha_vetor": 0, "texto_indexado": textos[0]},
        {"id": "doc2", "linha_vetor": 1, "texto_indexado": textos[1]},
    ]
    manifesto = {
        "modelo": gerador.nome,
        "dimensoes": 256,
        "quantidade_vetores": 2,
        "arquivos": {"vetores.npy": "hash1", "metadados.json": "hash2"},
    }

    benchmark = [
        {
            "id_teste": 101,
            "tipo": "identica",
            "texto_testado": "A prefeitura anunciou transporte gratuito aos domingos",
            "alegacao_ref_original": textos[0],
            "resultado_esperado": "match_confirmado",
        },
        {
            "id_teste": 102,
            "tipo": "controle",
            "texto_testado": "Telescópio descobre nova galáxia distante",
            "alegacao_ref_original": None,
            "resultado_esperado": "sem_match",
        },
    ]

    resultado = avaliar_benchmark(
        benchmark=benchmark,
        vetores=vetores,
        metadados=metadados,
        gerador=gerador,
        manifesto=manifesto,
        top_k=2,
        benchmark_hash="hash_teste",
    )

    assert resultado["resumo_geral"]["total_casos_testados"] == 2
    assert resultado["resumo_geral"]["casos_com_referencia"] == 1
    assert resultado["resumo_geral"]["casos_controle_negativo"] == 1
    assert resultado["resumo_geral"]["recall_1"] == 1.0
    assert resultado["resumo_geral"]["mrr"] == 1.0

    assert "identica" in resultado["metricas_por_tipo"]
    assert "controle" in resultado["metricas_por_tipo"]
    assert resultado["metricas_por_tipo"]["identica"]["recall_1"] == 1.0

    tabela = formatar_tabela_resumo(resultado)
    assert "RELATÓRIO DE AVALIAÇÃO DE MLOPS" in tabela
    assert "identica" in tabela
