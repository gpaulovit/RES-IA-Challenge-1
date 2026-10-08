"""Testes de validação do arquivo de 30 mensagens eleitorais de teste (RNF-01)."""

import json
from pathlib import Path


def test_arquivo_30_mensagens_valido():
    caminho = Path("data/30_mensagens_teste.json")
    assert caminho.exists(), "Arquivo data/30_mensagens_teste.json deve existir"

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert isinstance(dados, list)
    assert len(dados) == 30, "Devem existir exatamente 30 mensagens para teste"

    textos = [m for m in dados if m["tipo"] == "texto"]
    links = [m for m in dados if m["tipo"] == "link"]

    assert len(textos) == 18
    assert len(links) == 12

    for msg in dados:
        assert "id" in msg
        assert "tipo" in msg
        assert "conteudo" in msg
        assert "categoria" in msg
        assert "alvo_tempo_segundos" in msg
        assert msg["alvo_tempo_segundos"] in (5.0, 10.0)
