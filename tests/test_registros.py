"""Testes automatizados para o módulo de registros anônimos e privacidade (LGPD)."""

import json
from pathlib import Path

import pytest

from checagens.registros import (
    carregar_registros,
    obter_metricas_monitoramento,
    registrar_consulta,
    registrar_voto,
)


def test_registrar_consulta_valida(tmp_path: Path):
    arquivo = tmp_path / "consultas.jsonl"
    reg = registrar_consulta(
        tipo_entrada="texto",
        camada=1,
        semelhanca=0.92,
        caminho_arquivo=arquivo,
    )

    assert reg["tipo_entrada"] == "texto"
    assert reg["camada"] == 1
    assert reg["semelhanca"] == 0.92
    assert reg["voto"] is None
    assert "id_consulta" in reg
    assert "data_hora_utc" in reg

    # Verifica persistência física
    assert arquivo.exists()
    registros = carregar_registros(arquivo)
    assert len(registros) == 1
    assert registros[0]["id_consulta"] == reg["id_consulta"]


def test_registrar_e_atualizar_voto(tmp_path: Path):
    arquivo = tmp_path / "consultas.jsonl"
    reg1 = registrar_consulta(
        tipo_entrada="link",
        camada=2,
        faixa="muitos_sinais",
        caminho_arquivo=arquivo,
    )
    reg2 = registrar_consulta(
        tipo_entrada="texto",
        camada=1,
        semelhanca=0.88,
        caminho_arquivo=arquivo,
    )

    # Vota 👍 no primeiro
    sucesso = registrar_voto(reg1["id_consulta"], "👍", caminho_arquivo=arquivo)
    assert sucesso is True

    # Vota 👎 no segundo
    sucesso2 = registrar_voto(reg2["id_consulta"], "negativo", caminho_arquivo=arquivo)
    assert sucesso2 is True

    salvos = carregar_registros(arquivo)
    assert len(salvos) == 2
    assert salvos[0]["voto"] == "positivo"
    assert salvos[0]["data_hora_voto_utc"] is not None
    assert salvos[1]["voto"] == "negativo"


def test_rejeicao_estrita_lgpd_campos_pessoais(tmp_path: Path):
    arquivo = tmp_path / "consultas.jsonl"

    for campo_proibido in ["user_id", "chat_id", "username", "telefone", "nome"]:
        with pytest.raises(ValueError, match="Violação de privacidade"):
            registrar_consulta(
                tipo_entrada="texto",
                camada=1,
                metadados_adicionais={campo_proibido: "dados_sensíveis_123"},
                caminho_arquivo=arquivo,
            )

    # Garante que nenhum dado pessoal foi escrito
    assert not arquivo.exists() or len(carregar_registros(arquivo)) == 0


def test_validacao_tipos_invalidos(tmp_path: Path):
    arquivo = tmp_path / "consultas.jsonl"

    with pytest.raises(ValueError, match="Tipo de entrada inválido"):
        registrar_consulta(tipo_entrada="audio", camada=1, caminho_arquivo=arquivo)

    with pytest.raises(ValueError, match="Camada inválida"):
        registrar_consulta(tipo_entrada="texto", camada=3, caminho_arquivo=arquivo)

    with pytest.raises(ValueError, match="Voto inválido"):
        registrar_voto("id_inexistente", "talvez", caminho_arquivo=arquivo)


def test_metricas_monitoramento_c9(tmp_path: Path):
    arquivo = tmp_path / "consultas.jsonl"
    r1 = registrar_consulta("texto", 1, semelhanca=0.90, caminho_arquivo=arquivo)
    r2 = registrar_consulta("link", 2, faixa="poucos_sinais", caminho_arquivo=arquivo)
    r3 = registrar_consulta("texto", 2, faixa="muitos_sinais", caminho_arquivo=arquivo)

    registrar_voto(r1["id_consulta"], "👍", caminho_arquivo=arquivo)
    registrar_voto(r3["id_consulta"], "👎", caminho_arquivo=arquivo)

    metricas = obter_metricas_monitoramento(arquivo)
    assert metricas["total_consultas"] == 3
    assert metricas["camada_1_total"] == 1
    assert metricas["camada_2_total"] == 2
    assert metricas["votos_positivos"] == 1
    assert metricas["votos_negativos"] == 1
    assert metricas["taxa_satisfacao"] == 0.5
    assert metricas["distribuicao_faixas"]["poucos_sinais"] == 1
    assert metricas["distribuicao_faixas"]["muitos_sinais"] == 1
