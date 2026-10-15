"""Camada 2 com dados sintéticos: contrato, faixas, sinais, divisão, critério e reprodutibilidade (roda no CI)."""
import numpy as np
import pytest

from inteligencia import classificador as c2
from inteligencia import treino

PARAMS = {"semente": 42, "camada2": {"ngram_range": [1, 2], "min_df": 1, "C": 1.0,
                                     "max_iter": 1000, "folds": 3, "margem_faixas": 0.10}}

FALSAS = ["urgente compartilhe antes que apaguem a verdade escondida", "bomba exclusivo a mídia esconde fraude",
          "urgente divulguem fraude nas urnas escondida", "compartilhe bomba que a mídia não mostra"]
VERDADEIRAS = ["tribunal publica resultado oficial da eleição", "ministério divulga dados oficiais do censo",
               "câmara aprova projeto em votação no plenário", "governo anuncia calendário oficial de vacinação"]


def base(prefixo, repeticoes=4):
    itens = []
    for r in range(repeticoes):
        itens += [{"texto": f"{t} {prefixo} caso {r}", "rotulo": True, "fonte": "a", "data": ""} for t in FALSAS]
        itens += [{"texto": f"{t} {prefixo} caso {r}", "rotulo": False, "fonte": "b", "data": ""} for t in VERDADEIRAS]
    return itens


@pytest.fixture(scope="module")
def treinado():
    tr, te = base("treino", 8), base("teste", 4)
    return treino.treinar(tr, PARAMS), tr, te


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


def test_teste_perde_textos_repetidos_do_treino():
    tr = [{"texto": "A notícia", "rotulo": True, "fonte": "a", "data": ""}]
    te = [{"texto": "a  NOTÍCIA!", "rotulo": True, "fonte": "a", "data": ""},
          {"texto": "outra", "rotulo": False, "fonte": "b", "data": ""}]
    limpo, repetidos = treino.remover_repetidos(tr, te)
    assert [i["texto"] for i in limpo] == ["outra"] and repetidos == 1


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
    clf, tr, te = treinado
    outro = treino.treinar(tr, PARAMS)
    assert treino.avaliar(clf, tr, te, 42) == treino.avaliar(outro, tr, te, 42)


def test_csv_valida_esquema_e_converte_rotulo(tmp_path):
    caminho = tmp_path / "treino.csv"
    caminho.write_text("texto,rotulo,fonte,data\nurna fraudada,falso,X,2018-09-01\ncenso oficial,verdadeiro,X,\n",
                       encoding="utf-8")
    assert [i["rotulo"] for i in treino.carregar_csv(caminho)] == [True, False]
    for ruim in ("texto,rotulo,fonte,data\nx,fake,X,\n", "texto,rotulo,fonte\nx,falso,X\n",
                 "texto,rotulo,fonte,data\n ,falso,X,\n", "texto,rotulo,fonte,data\n"):
        caminho.write_text(ruim, encoding="utf-8")
        with pytest.raises(ValueError):
            treino.carregar_csv(caminho)
