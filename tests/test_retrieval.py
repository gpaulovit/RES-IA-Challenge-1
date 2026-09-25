import json

import numpy as np
import pytest

from checagens.embeddings import BaselineHashing, construir_indice, salvar_indice
from checagens.retrieval import buscar, carregar_indice


def corpus_ficticio():
    titulos = [
        "A praça fecha aos domingos",
        "O ônibus é gratuito aos domingos",
        "A imagem foi alterada digitalmente",
    ]
    return {
        "metadados": {"versao_fonte": "teste", "sha256_fonte": "abc"},
        "registros": [
            {
                "id": f"teste:{numero:04d}",
                "organizado": {
                    "titulo_checagem": titulo, "veredito_original": "Falso",
                    "agencia": "Agência fictícia",
                    "data": {"original": "10/30/2022", "padronizada": "2022-10-30",
                             "status": "padronizada"},
                },
            }
            for numero, titulo in enumerate(titulos, 1)
        ],
    }


def indice_ficticio(tmp_path):
    gerador = BaselineHashing()
    vetores, metadados, manifesto = construir_indice(corpus_ficticio(), gerador)
    salvar_indice(tmp_path, vetores, metadados, manifesto)
    return gerador


def test_carrega_indice_e_recupera_registro_identico(tmp_path):
    gerador = indice_ficticio(tmp_path)
    vetores, metadados, manifesto = carregar_indice(tmp_path, gerador.nome)
    resultado = buscar("O ônibus é gratuito aos domingos", 2, vetores, metadados, gerador)
    assert manifesto["modelo"] == gerador.nome
    assert resultado[0]["id"] == "teste:0002"
    assert resultado[0]["pontuacao"] == pytest.approx(1.0)
    assert resultado[0]["agencia"] == "Agência fictícia"


def test_busca_e_exata_e_desempata_por_id():
    class GeradorFixo:
        nome = "fixo"

        def gerar(self, textos):
            return np.array([[1.0, 0.0]], dtype="float32")

    vetores = np.array([[1.0, 0.0], [1.0, 0.0]], dtype="float32")
    metadados = [{"id": "b"}, {"id": "a"}]
    resultado = buscar("consulta", 2, vetores, metadados, GeradorFixo())
    assert [item["id"] for item in resultado] == ["a", "b"]


def test_rejeita_indice_alterado(tmp_path):
    gerador = indice_ficticio(tmp_path)
    (tmp_path / "metadados.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="foi alterado"):
        carregar_indice(tmp_path, gerador.nome)


def test_rejeita_modelo_diferente_do_indice(tmp_path):
    indice_ficticio(tmp_path)
    with pytest.raises(ValueError, match="índice usa"):
        carregar_indice(tmp_path, "outro-modelo")


@pytest.mark.parametrize(("texto", "top_k"), [("", 1), ("texto", 0), ("texto", 4)])
def test_rejeita_consulta_invalida(tmp_path, texto, top_k):
    gerador = indice_ficticio(tmp_path)
    vetores, metadados, _ = carregar_indice(tmp_path, gerador.nome)
    with pytest.raises(ValueError):
        buscar(texto, top_k, vetores, metadados, gerador)


def test_manifesto_e_json_legivel(tmp_path):
    indice_ficticio(tmp_path)
    manifesto = json.loads((tmp_path / "manifesto.json").read_text(encoding="utf-8"))
    assert manifesto["uso"] == "experimental_gate"
    assert manifesto["apto_produto"] is False
