import numpy as np
import pytest
from fastapi.testclient import TestClient

from checagens.api import criar_app
from checagens.busca import Buscador
from checagens.representacao import RepresentacaoTfidf
from conftest import CAMINHO_DADOS


def test_texto_identico_em_primeiro(buscador, exemplos):
    for exemplo in exemplos:
        resultado = buscador.buscar(exemplo.alegacao)
        assert resultado[0].id == exemplo.id
        assert resultado[0].pontuacao == pytest.approx(1.0)


def test_consulta_relacionada(buscador):
    resultados = buscador.buscar("transporte gratuito domingos")
    assert [item.id for item in resultados] == ["demo-002"]


def test_consulta_sem_vocabulario(buscador):
    assert buscador.buscar("abacaxi telescópio submarino") == []
    assert buscador.buscar("!!!") == []


def test_limite_e_ordenacao(buscador):
    texto = "eleição transporte orçamento escolas"
    todos = buscador.buscar(texto, 10)
    assert len(todos) == 3
    assert [item.pontuacao for item in todos] == sorted(
        [item.pontuacao for item in todos], reverse=True
    )
    assert buscador.buscar(texto, 1) == todos[:1]
    assert all(0 < item.pontuacao <= 1 for item in todos)


class RepresentacaoControlada:
    """Vetores conhecidos para conferir troca de técnica e desempate."""

    metodo = "vetores_de_teste"

    def preparar(self, textos):
        return np.array([[1.0, 0.0]] * len(textos))

    def transformar(self, textos):
        return np.array([[1.0, 0.0]] * len(textos))


def test_desempate_por_id_independe_da_ordem_da_base(exemplos):
    buscador = Buscador(list(reversed(exemplos)), RepresentacaoControlada())
    assert [item.id for item in buscador.buscar("consulta")] == sorted(
        item.id for item in exemplos
    )


def test_troca_representacao_sem_mudar_api():
    with TestClient(criar_app(CAMINHO_DADOS, RepresentacaoControlada())) as cliente:
        resposta = cliente.post("/buscar", json={"texto": "qualquer consulta", "top_k": 1})
        assert resposta.status_code == 200
        dados = resposta.json()
        assert dados["metodo"] == "vetores_de_teste"
        assert dados["modo"] == "demonstracao"
        assert dados["candidatos"][0]["id"] == "demo-001"
        assert len(dados["candidatos"]) == 1


@pytest.mark.parametrize("texto,top_k", [(" ", 3), ("texto", 0), ("texto", True)])
def test_funcao_reutilizavel_rejeita_entrada_invalida(buscador, texto, top_k):
    with pytest.raises(ValueError):
        buscador.buscar(texto, top_k)


def test_base_sem_palavras_utilizaveis(exemplos):
    exemplo = exemplos[0].model_copy(update={"alegacao": "!!!"})
    with pytest.raises(ValueError, match="pelo menos dois caracteres"):
        Buscador([exemplo], RepresentacaoTfidf())
