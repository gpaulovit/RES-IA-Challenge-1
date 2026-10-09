import pandas as pd

from limpeza import limpar_titulo


def test_limpeza_tira_carimbos_de_agencia():
    titulos = pd.Series(["É #FAKE que Lula disse X", "Boato: é falso que urnas no Japão falharam",
                         "Papa foi preso #boato", "É verdadeiro que zona eleitoral foi transferida",
                         "É falsa foto de ministro do TSE"])
    assert limpar_titulo(titulos).tolist() == ["Lula disse X", "Urnas no Japão falharam", "Papa foi preso",
                                               "Zona eleitoral foi transferida", "Foto de ministro do TSE"]


def test_limpeza_nao_mexe_em_titulo_sem_carimbo():
    titulos = pd.Series(["Senado aprova reforma", "Bolsonaro diz que vai vetar fundão"])
    assert limpar_titulo(titulos).tolist() == titulos.tolist()
