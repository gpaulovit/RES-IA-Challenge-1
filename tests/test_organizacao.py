import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from checagens import organizacao
from checagens.inspecao import COLUNAS


def csv_ficticio(linhas):
    arquivo = io.StringIO(newline="")
    escritor = csv.writer(arquivo)
    escritor.writerow(COLUNAS)
    escritor.writerows(linhas)
    return arquivo.getvalue().encode("utf-8")


def preparar(monkeypatch, conteudo):
    sha = hashlib.sha256(conteudo).hexdigest()
    monkeypatch.setattr(organizacao, "SHA256", sha)
    monkeypatch.setattr(organizacao, "VERSAO", "versao-teste")
    monkeypatch.setattr(organizacao, "FONTE", "https://example.org/fonte")
    monkeypatch.setattr(organizacao, "URL", "https://example.org/fonte.csv")
    return {"fonte": "https://example.org/fonte", "url_download": "https://example.org/fonte.csv",
            "sha256": sha, "versao": "versao-teste", "tamanho_bytes": len(conteudo),
            "licenca": "CC BY-NC-SA 4.0"}


def test_preserva_original_e_sinaliza_lacunas_datas_e_duplicacoes(monkeypatch):
    ambiguo = [" https://example.org ", " Título ", "02/03/2022", " ",
               " Pessoa ", " Agência ", ""]
    fora_formato = ["link", "Outro", "30/10/2022", "Falso", "Pessoa", "Agência", "Texto"]
    conteudo = csv_ficticio([ambiguo, ambiguo, fora_formato])
    corpus, relatorio = organizacao.organizar(conteudo, preparar(monkeypatch, conteudo))

    assert len(corpus["registros"]) == 3
    primeiro = corpus["registros"][0]
    assert primeiro["original"]["Link"] == " https://example.org "
    assert primeiro["organizado"]["link"] == "https://example.org"
    assert primeiro["organizado"]["veredito_original"] is None
    assert primeiro["organizado"]["data"]["status"] == "ambigua"
    assert primeiro["organizado"]["data"]["padronizada"] is None
    assert primeiro["qualidade"]["grupo_duplicado"] == [1, 2]
    assert corpus["registros"][2]["organizado"]["data"]["status"] == "fora_formato_fonte"
    assert relatorio["campos_organizados_ausentes"] == {
        "texto_verificacao": {"quantidade": 2, "registros": [1, 2]},
        "veredito_original": {"quantidade": 2, "registros": [1, 2]},
    }
    assert relatorio["grupos_duplicados"] == [[1, 2]]
    assert relatorio["campos_originais_ausentes"]["Data da checagem"]["quantidade"] == 0
    assert relatorio["campos_originais_ausentes"]["Agência"]["quantidade"] == 0


def test_data_unica_no_formato_da_fonte_e_padronizada(monkeypatch):
    linha = ["link", "Título", "10/30/2022", "Falso", "Pessoa", "Agência", "Texto"]
    conteudo = csv_ficticio([linha])
    corpus, _ = organizacao.organizar(conteudo, preparar(monkeypatch, conteudo))
    assert corpus["registros"][0]["organizado"]["data"] == {
        "original": "10/30/2022", "padronizada": "2022-10-30",
        "status": "padronizada", "possibilidades": [{"formato": "mes_dia_ano", "data": "2022-10-30"}],
    }


@pytest.mark.parametrize(
    ("valor", "status", "padronizada"),
    [
        ("", "ausente", None),
        ("31/02/2022", "invalida", None),
        ("30/10/2022", "fora_formato_fonte", None),
        ("02/03/2022", "ambigua", None),
        ("03/03/2022", "padronizada", "2022-03-03"),
    ],
)
def test_estados_de_data(valor, status, padronizada):
    resultado = organizacao._data(valor)
    assert resultado["status"] == status
    assert resultado["padronizada"] == padronizada


def test_rejeita_original_ou_metadados_incompativeis(monkeypatch):
    conteudo = csv_ficticio([["l", "t", "10/30/2022", "v", "c", "a", "x"]])
    origem = preparar(monkeypatch, conteudo)
    with pytest.raises(ValueError, match="original foi alterado"):
        organizacao.organizar(conteudo + b"alterado", origem)
    with pytest.raises(ValueError, match="metadados de origem"):
        organizacao.organizar(conteudo, {**origem, "versao": "outra"})


def test_execucao_repetida_produz_arquivos_identicos(tmp_path, monkeypatch):
    conteudo = csv_ficticio([["l", "t", "10/30/2022", "v", "c", "a", "x"]])
    origem = preparar(monkeypatch, conteudo)
    monkeypatch.chdir(tmp_path)
    original = Path("data/originais/factpolcheckbr/com_texto.csv")
    original.parent.mkdir(parents=True)
    original.write_bytes(conteudo)
    original.with_name("origem.json").write_text(json.dumps(origem), encoding="utf-8")
    organizacao.main()
    primeira = (organizacao.CORPUS.read_bytes(), organizacao.RELATORIO.read_bytes())
    organizacao.main()
    assert (organizacao.CORPUS.read_bytes(), organizacao.RELATORIO.read_bytes()) == primeira
