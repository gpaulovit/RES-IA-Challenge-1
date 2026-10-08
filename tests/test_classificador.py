"""Camada 2 com dados sintéticos: contrato, faixas, sinais, divisão, critério e reprodutibilidade (roda no CI)."""
import numpy as np
import pytest

from inteligencia import classificador as c2
from inteligencia import treino

PARAMS = {"semente": 42, "camada2": {"ano_corte": 2020, "ngram_range": [1, 2], "min_df": 1, "C": 1.0,
                                     "max_iter": 1000, "folds": 3, "margem_faixas": 0.10}}

FALSAS = ["urgente compartilhe antes que apaguem a verdade escondida", "bomba exclusivo a mídia esconde fraude",
          "urgente divulguem fraude nas urnas escondida", "compartilhe bomba que a mídia não mostra"]
VERDADEIRAS = ["tribunal publica resultado oficial da eleição", "ministério divulga dados oficiais do censo",
               "câmara aprova projeto em votação no plenário", "governo anuncia calendário oficial de vacinação"]


def base(anos=(2019, 2020, 2021), repeticoes=4):
    itens = []
    for ano in anos:
        for r in range(repeticoes):
            itens += [{"texto": f"{t} {ano} caso {r}", "rotulo": True, "ano": ano, "fonte": "a"} for t in FALSAS]
            itens += [{"texto": f"{t} {ano} caso {r}", "rotulo": False, "ano": ano, "fonte": "b"} for t in VERDADEIRAS]
    return itens


@pytest.fixture(scope="module")
def treinado():
    return treino.treinar(base(), PARAMS)


def test_contrato_faixa_e_sinais_sem_probabilidade(treinado):
    clf = treinado[0]
    r = clf.classificar("urgente compartilhe a fraude escondida")
    assert set(r) == {"faixa", "sinais"}
    assert r["faixa"] in c2.FAIXAS
    assert 2 <= len(r["sinais"]) <= 3
    assert all(s in "urgente compartilhe a fraude escondida" for s in r["sinais"])


def test_texto_claramente_falso_tem_muitos_sinais_e_oficial_tem_poucos(treinado):
    clf = treinado[0]
    assert clf.classificar("urgente compartilhe bomba fraude escondida")["faixa"] == "muitos_sinais"
    assert clf.classificar("tribunal publica dados oficiais da votação")["faixa"] == "poucos_sinais"


def test_sinais_saem_como_o_usuario_escreveu(treinado):
    texto = "URGENTE: Mídia esconde a FRAUDE nas urnas"
    sinais = treinado[0].classificar(texto)["sinais"]
    assert sinais and all(s in texto for s in sinais)   # "Mídia", não "midia"


def test_sinais_nao_mostram_palavras_vazias(treinado):
    sinais = treinado[0].classificar("a mídia esconde a fraude nas urnas e no voto")["sinais"]
    assert not any(s.lower() in c2.PALAVRAS_VAZIAS for s in sinais)


def test_texto_vazio(treinado):
    with pytest.raises(ValueError):
        treinado[0].classificar("  ")


def test_divisao_por_epoca_remove_repetidos_do_teste():
    itens = [{"texto": "A notícia", "rotulo": True, "ano": 2020, "fonte": "a"},
             {"texto": "a  NOTÍCIA!", "rotulo": True, "ano": 2021, "fonte": "a"},
             {"texto": "outra", "rotulo": False, "ano": 2021, "fonte": "b"}]
    tr, te, repetidos = treino.dividir(itens, 2020)
    assert [i["ano"] for i in tr] == [2020]
    assert [i["texto"] for i in te] == ["outra"] and repetidos == 1


def test_cortes_respeitam_a_margem():
    p = np.linspace(0, 1, 101)
    y = (p > 0.5).astype(int)
    alto, baixo = c2.escolher_cortes(p, y, margem=0.10)
    assert (p[y == 0] >= alto).mean() <= 0.10
    assert (p[y == 1] <= baixo).mean() <= 0.10


@pytest.mark.parametrize("f1, fa, nf, nv, esperado", [
    (0.75, 0.15, 100, 100, "go"),       # exatamente nos limites
    (0.749, 0.10, 500, 500, "no-go"),   # RNF-02
    (0.90, 0.151, 500, 500, "no-go"),   # RNF-03
    (0.90, 0.05, 500, 99, "no-go"),     # inconclusivo
])
def test_criterio_go_no_go_nas_fronteiras(f1, fa, nf, nv, esperado):
    assert treino.decidir(f1, fa, nf, nv)[0] == esperado


def test_mesma_semente_mesmas_metricas(treinado):
    outro = treino.treinar(base(), PARAMS)
    m1 = treino.avaliar(treinado[0], treinado[1], treinado[2], 42)
    m2 = treino.avaliar(outro[0], outro[1], outro[2], 42)
    assert m1 == m2


def test_base_valida_esquema(tmp_path):
    caminho = tmp_path / "treino.json"
    for ruim in ('[{"texto": "x", "rotulo": 1, "ano": 2020, "fonte": "a"}]',
                 '[{"texto": "x", "rotulo": true, "ano": "2020", "fonte": "a"}]',
                 '[{"texto": "", "rotulo": true, "ano": 2020, "fonte": "a"}]',
                 '[{"texto": "x", "ano": 2020, "fonte": "a"}]'):
        caminho.write_text(ruim, encoding="utf-8")
        with pytest.raises(ValueError):
            treino.carregar_base(caminho)
