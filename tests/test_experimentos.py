import numpy as np
import pandas as pd
import pytest

from gate import classificar, ece, montar, veredito
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


def test_ece_zero_quando_calibrado_e_alto_quando_nao():
    y = np.array([1] * 7 + [0] * 3)
    assert ece(y, np.full(10, 0.7)) == pytest.approx(0.0)
    assert ece(y, np.full(10, 0.1)) == pytest.approx(0.6)


def _modelos(auc, ece_=0.03, bss=0.2, auc_lex=0.70, auc_ctrl=0.60):
    return {"auc": auc, "ece": ece_, "brier_skill": bss}, {"auc": auc_lex}, {"auc": auc_ctrl}


GIRIA_OK = {"media": 0.05, "frac_acima_025": 0.01}


def test_criterios_e_agregacao():
    tudo_go = classificar("A", *_modelos(0.90), GIRIA_OK)
    assert set(tudo_go.values()) == {"GO"}
    assert veredito(tudo_go.values()) == "GO"
    # a mesma AUC é GO em B (limite 0,80) e inconclusiva em A (limite 0,85)
    assert classificar("A", *_modelos(0.82, auc_lex=0.6), GIRIA_OK)["auc"] == "INCONCLUSIVO"
    assert classificar("B", *_modelos(0.82, auc_lex=0.6), GIRIA_OK)["auc"] == "GO"
    # controle de fonte/ano perto do modelo → atalho → NO-GO decide tudo
    atalho = classificar("A", *_modelos(0.90, auc_ctrl=0.88), GIRIA_OK)
    assert atalho["distancia_ao_atalho"] == "NO-GO"
    assert veredito(atalho.values()) == "NO-GO"
    assert classificar("A", *_modelos(0.90), {"media": 0.12, "frac_acima_025": 0.04})["giria_apelido"] == "INCONCLUSIVO"
    assert veredito(["GO", "INCONCLUSIVO"]) == "INCONCLUSIVO"


def test_montar_separa_periodos_e_tira_texto_repetido():
    fonte = pd.DataFrame({"claim": ["a", "b", "B ", "c"], "is_fake": [True, False, True, False],
                          "ano": [2020, 2020, 2021, 2021], "fonte": "x", "categoria": "política", "origem": "f"})
    treino, avaliacao = montar({"f": fonte}, {"treino": [("f", range(2020, 2021))],
                                              "avaliacao": [("f", range(2021, 2022))]})
    assert treino["claim"].tolist() == ["a", "b"]
    assert avaliacao["claim"].tolist() == ["c"]   # "B " repete "b" do treino
