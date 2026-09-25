import hashlib
import json

import numpy as np
import pytest

from checagens.embeddings import (
    BaselineHashing,
    construir_indice,
    preparar_itens,
    salvar_indice,
)


def corpus_ficticio():
    return {
        "metadados": {"versao_fonte": "v1", "sha256_fonte": "abc"},
        "registros": [
            {
                "id": "v1:0001",
                "organizado": {
                    "titulo_checagem": " Título um ", "veredito_original": "Falso",
                    "agencia": "Agência A",
                    "data": {"original": "10/30/2022", "padronizada": "2022-10-30",
                             "status": "padronizada"},
                },
            },
            {
                "id": "v1:0002",
                "organizado": {
                    "titulo_checagem": "Título dois", "veredito_original": None,
                    "agencia": "Agência B",
                    "data": {"original": "02/03/2022", "padronizada": None,
                             "status": "ambigua"},
                },
            },
        ],
    }


class GeradorFalso:
    nome = "modelo-falso"

    def gerar(self, textos):
        return np.array([[len(texto), indice] for indice, texto in enumerate(textos)], dtype="float32")


def test_pipeline_alinha_vetores_e_metadados():
    vetores, metadados, manifesto = construir_indice(corpus_ficticio(), GeradorFalso())
    assert vetores.shape == (2, 2)
    assert metadados[0] == {
        "id": "v1:0001", "linha_vetor": 0, "campo_texto": "titulo_checagem",
        "texto_indexado": "Título um", "veredito_original": "Falso",
        "agencia": "Agência A", "data_original": "10/30/2022",
        "data_padronizada": "2022-10-30", "status_data": "padronizada",
    }
    assert metadados[1]["linha_vetor"] == 1
    assert manifesto["modelo"] == "modelo-falso"
    assert manifesto["apto_produto"] is False


def test_baseline_e_reproduzivel():
    corpus = corpus_ficticio()
    primeira, _, _ = construir_indice(corpus, BaselineHashing())
    segunda, _, _ = construir_indice(corpus, BaselineHashing())
    np.testing.assert_array_equal(primeira, segunda)
    assert primeira.shape == (2, 256)


def test_salva_arquivos_com_hash_e_permite_recarregar(tmp_path):
    vetores, metadados, manifesto = construir_indice(corpus_ficticio(), GeradorFalso())
    final = salvar_indice(tmp_path, vetores, metadados, manifesto)
    recarregados = np.load(tmp_path / "vetores.npy", allow_pickle=False)
    np.testing.assert_array_equal(recarregados, vetores)
    assert json.loads((tmp_path / "metadados.json").read_text(encoding="utf-8")) == metadados
    for nome, hash_esperado in final["arquivos"].items():
        assert hashlib.sha256((tmp_path / nome).read_bytes()).hexdigest() == hash_esperado


@pytest.mark.parametrize("alteracao", ["id_repetido", "titulo_vazio", "formato_invalido"])
def test_rejeita_corpus_que_quebraria_alinhamento(alteracao):
    corpus = corpus_ficticio()
    if alteracao == "id_repetido":
        corpus["registros"][1]["id"] = "v1:0001"
    elif alteracao == "titulo_vazio":
        corpus["registros"][1]["organizado"]["titulo_checagem"] = " "
    else:
        del corpus["registros"][1]["organizado"]
    with pytest.raises(ValueError):
        preparar_itens(corpus)


@pytest.mark.parametrize(
    "retorno",
    [np.array([1, 2]), np.array([[1], [np.nan]]), np.array([[1]])],
)
def test_rejeita_saida_invalida_do_modelo(retorno):
    class GeradorInvalido:
        nome = "invalido"

        def gerar(self, textos):
            return retorno

    with pytest.raises(ValueError, match="modelo"):
        construir_indice(corpus_ficticio(), GeradorInvalido())
