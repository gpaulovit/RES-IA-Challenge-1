import json

import pytest
from fastapi.testclient import TestClient

from checagens.api import criar_app
from checagens.dados import carregar_exemplos


def test_tres_exemplos_ficticios(exemplos):
    assert len(exemplos) == 3
    assert all("fictícia" in item.agencia for item in exemplos)


@pytest.mark.parametrize(
    "conteudo,mensagem",
    [
        ("", "JSON válido"),
        ("{", "JSON válido"),
        ("[]", "pelo menos uma"),
        ("{}", "lista"),
        ('[{"id": "incompleto"}]', "Exemplo 1 inválido"),
        ('[null]', "Exemplo 1 inválido"),
    ],
)
def test_arquivo_invalido_impede_iniciar(tmp_path, conteudo, mensagem):
    caminho = tmp_path / "dados.json"
    caminho.write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError, match=mensagem):
        with TestClient(criar_app(caminho)):
            pass


def test_arquivo_ausente_impede_iniciar(tmp_path):
    with pytest.raises(ValueError, match="Não foi possível ler"):
        with TestClient(criar_app(tmp_path / "ausente.json")):
            pass


def test_identificadores_repetidos(tmp_path, exemplos):
    caminho = tmp_path / "dados.json"
    registro = exemplos[0].model_dump()
    caminho.write_text(json.dumps([registro, registro]), encoding="utf-8")
    with pytest.raises(ValueError, match="Identificador repetido"):
        carregar_exemplos(caminho)


@pytest.mark.parametrize("valor", [" ", 123, None])
def test_campos_precisam_de_texto(tmp_path, exemplos, valor):
    caminho = tmp_path / "dados.json"
    registro = exemplos[0].model_dump()
    registro["agencia"] = valor
    caminho.write_text(json.dumps([registro]), encoding="utf-8")
    with pytest.raises(ValueError, match="agencia"):
        carregar_exemplos(caminho)


def test_codificacao_invalida(tmp_path):
    caminho = tmp_path / "dados.json"
    caminho.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="UTF-8"):
        carregar_exemplos(caminho)
