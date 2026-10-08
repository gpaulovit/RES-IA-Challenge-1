from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from checagens.api import criar_app
from checagens.busca import Buscador
from checagens.dados import carregar_exemplos
from checagens.representacao import RepresentacaoTfidf

CAMINHO_DADOS = Path(__file__).resolve().parents[1] / "data" / "exemplos.json"


@pytest.fixture
def exemplos():
    return carregar_exemplos(CAMINHO_DADOS)


@pytest.fixture
def buscador(exemplos):
    return Buscador(exemplos, RepresentacaoTfidf())


@pytest.fixture
def cliente():
    with TestClient(criar_app(CAMINHO_DADOS)) as cliente:
        yield cliente
