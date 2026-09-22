import csv
import io
import hashlib
import json
import sys
from pathlib import Path

import pytest

from checagens.inspecao import COLUNAS, inspecionar
from checagens import inspecao


def csv_ficticio(linhas):
    arquivo = io.StringIO(newline="")
    escritor = csv.writer(arquivo)
    escritor.writerow(COLUNAS)
    escritor.writerows(linhas)
    return arquivo.getvalue().encode("utf-8")


def test_campos_multilinha_e_repeticoes():
    linha = ["https://example.org", "Título fictício", "10/30/2022", "Falso",
             "Ninguém", "Agência fictícia", "Texto com vírgula,\ne outra linha"]
    resultado = inspecionar(csv_ficticio([linha, linha]))
    assert resultado["total_registros"] == 2
    assert resultado["duplicacoes_exatas"]["registro_completo"]["grupos"] == [[1, 2]]
    assert resultado["campos_vazios"]["texto"]["quantidade"] == 0


def test_vazios_e_datas_mistas_sem_corrigir():
    linhas = [["", "Título", data, " ", "Ninguém", "Agência", ""]
              for data in ["30/10/2022", "02/03/2022", "31/02/2022"]]
    resultado = inspecionar(csv_ficticio(linhas))
    assert resultado["campos_vazios"]["Natureza da notícia"]["registros"] == [1, 2, 3]
    assert resultado["duplicacoes_exatas"]["Link"]["grupos"] == []
    assert resultado["datas"]["ambiguas_entre_formatos"] == [2]
    assert resultado["datas"]["invalidas_nos_dois_formatos"] == [3]
    assert resultado["datas"]["fora_do_formato_informado"][0]["valor"] == "30/10/2022"


def test_linha_incompleta_nao_desaparece():
    with pytest.raises(ValueError, match="quantidade incorreta"):
        inspecionar(csv_ficticio([["somente um campo"]]))


def test_cabecalho_inesperado():
    with pytest.raises(ValueError, match="Colunas diferentes"):
        inspecionar(b"coluna\nvalor\n")


def test_base_vazia():
    with pytest.raises(ValueError, match="não contém registros"):
        inspecionar(csv_ficticio([]))


def test_download_e_reexecucao_preservam_original(tmp_path, monkeypatch):
    conteudo = csv_ficticio([["https://example.org", "Título", "10/30/2022",
                             "Falso", "Ninguém", "Agência", "Texto"]])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(inspecao, "SHA256", hashlib.sha256(conteudo).hexdigest())
    monkeypatch.setattr(sys, "argv", ["inspecao", "--baixar"])
    chamadas = []

    def download_simulado(comando, check):
        chamadas.append(comando)
        Path(comando[-1]).write_bytes(conteudo)

    monkeypatch.setattr(inspecao.subprocess, "run", download_simulado)
    inspecao.main()
    original = inspecao.ORIGINAL.read_bytes()
    manifesto = inspecao.ORIGINAL.with_name("origem.json").read_bytes()
    resultado = Path("data/relatorios/inspecao-factpolcheckbr.json").read_bytes()
    inspecao.main()
    assert len(chamadas) == 1
    assert inspecao.ORIGINAL.read_bytes() == original == conteudo
    assert inspecao.ORIGINAL.with_name("origem.json").read_bytes() == manifesto
    assert Path("data/relatorios/inspecao-factpolcheckbr.json").read_bytes() == resultado
    assert json.loads(manifesto)["sha256"] == hashlib.sha256(conteudo).hexdigest()


def test_original_modificado_nao_e_sobrescrito(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["inspecao", "--baixar"])
    inspecao.ORIGINAL.parent.mkdir(parents=True)
    inspecao.ORIGINAL.write_bytes(b"modificado")
    with pytest.raises(SystemExit) as erro:
        inspecao.main()
    assert erro.value.code == 1
    assert inspecao.ORIGINAL.read_bytes() == b"modificado"
    assert not Path("data/relatorios/inspecao-factpolcheckbr.json").exists()
