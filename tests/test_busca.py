"""Camada 1 (inteligencia.busca) com vetores falsos: testa contrato, faixas e negação sem baixar modelo (roda no CI)."""
import json

import numpy as np
import pandas as pd
import pytest

from inteligencia import busca
from inteligencia.calibracao import MAX_CONTROLES_MOSTRADOS, avaliar, chave, escolher, grade, preparar


def checagem(numero, alegacao, **extra):
    return {"id": f"t:{numero}", "alegacao": alegacao, "veredito_original": "Falso",
            "veredito_normalizado": "falso", "agencia": "Agência X", "data": "2022-10-01",
            "link": f"https://exemplo.org/{numero}", "fonte_dataset": "teste", **extra}


BASE = [checagem(1, "Anitta retira apoio à candidatura de Lula"),
        checagem(2, "Urna eletrônica foi fraudada no Japão"),
        checagem(3, "Vídeo mostra fila de votação em 2018")]


def vetorizar_falso(textos):
    """Bolsa de palavras normalizada: textos com as mesmas palavras ficam parecidos."""
    vocab = sorted({p for t in [b["alegacao"] for b in BASE] for p in busca.tirar_acento(t).lower().split()})
    E = np.array([[busca.tirar_acento(t).lower().split().count(p) for p in vocab] for t in textos], dtype="float32")
    normas = np.linalg.norm(E, axis=1, keepdims=True)
    return E / np.where(normas == 0, 1, normas)


@pytest.fixture
def buscador():
    return busca.Buscador(vetorizar_falso([b["alegacao"] for b in BASE]), BASE, alta=0.85, media=0.60,
                            vetorizar=vetorizar_falso)


def test_contrato_k_padrao_campos_e_ordem(buscador):
    r = buscador.buscar("Anitta retira apoio à candidatura de Lula")
    assert len(r) == 3
    assert set(r[0]) == set(busca.CAMPOS) | {"semelhanca", "faixa"}
    assert [x["semelhanca"] for x in r] == sorted((x["semelhanca"] for x in r), reverse=True)
    assert all(0 <= x["semelhanca"] <= 1 for x in r)
    assert r[0]["id"] == "t:1" and r[0]["faixa"] == "ja_checado"


def test_texto_vazio_e_k_invalido(buscador):
    with pytest.raises(ValueError):
        buscador.buscar("   ")
    with pytest.raises(ValueError):
        buscador.buscar("Anitta", k=0)


@pytest.mark.parametrize("s, esperado", [(0.85, "ja_checado"), (0.84, "relacionada"),
                                         (0.60, "relacionada"), (0.59, "baixa")])
def test_faixas_nos_limites(s, esperado):
    assert busca.faixa(s, "a b", "a b", alta=0.85, media=0.60) == esperado


def test_negacao_rebaixa_ja_checado_para_relacionada():
    assert busca.faixa(0.95, "Anitta NÃO retirou o apoio", "Anitta retira apoio", 0.85, 0.60) == "relacionada"
    assert busca.faixa(0.95, "Anitta nao retirou", "Anitta não retirou", 0.85, 0.60) == "ja_checado"
    assert busca.faixa(0.50, "Anitta NÃO retirou", "Anitta retira", 0.85, 0.60) == "baixa"


def test_negacao_ignora_acento_e_caixa_e_nao_pega_pedaco_de_palavra():
    assert busca.tem_negacao("NÃO é verdade") and busca.tem_negacao("é mentira que choveu")
    assert not busca.tem_negacao("Nação e nenhures")   # "nao" dentro de "nacao" não conta


def test_base_valida_esquema(tmp_path):
    caminho = tmp_path / "checagens.json"
    caminho.write_text(json.dumps(BASE), encoding="utf-8")
    assert len(busca.carregar_base(caminho)) == 3
    for ruim in ([{**BASE[0], "data": "01/10/2022"}], [{**BASE[0], "veredito_normalizado": "fake"}],
                 [BASE[0], BASE[0]], [{k: v for k, v in BASE[0].items() if k != "link"}]):
        caminho.write_text(json.dumps(ruim), encoding="utf-8")
        with pytest.raises(ValueError):
            busca.carregar_base(caminho)


def test_indice_ida_e_volta_e_deteccao_de_alteracao(tmp_path):
    base = tmp_path / "checagens.json"
    base.write_text(json.dumps(BASE), encoding="utf-8")
    busca.construir_indice(base, tmp_path / "indice", vetorizar=vetorizar_falso)
    E, registros = busca.carregar_indice(tmp_path / "indice")
    assert E.shape[0] == len(registros) == 3
    np.save(tmp_path / "indice" / "vetores.npy", E * 2)
    with pytest.raises(ValueError, match="alterado"):
        busca.carregar_indice(tmp_path / "indice")


def test_calibracao_respeita_rnf05_e_acha_alvo_por_texto_normalizado(buscador):
    casos = [
        {"id_teste": 1, "tipo": "controle_falso_positivo", "texto_testado": "Fila de votação longa hoje",
         "alegacao_ref_original": None, "resultado_esperado": "sem_match"},
        {"id_teste": 2, "tipo": "giria", "texto_testado": "anitta retira apoio a candidatura de lula",
         "alegacao_ref_original": "Anitta retira apoio à candidatura de Lula #boato",
         "resultado_esperado": "match_confirmado"},
        {"id_teste": 3, "tipo": "negacao", "texto_testado": "Anitta não retira apoio à candidatura de Lula",
         "alegacao_ref_original": "Anitta retira apoio à candidatura de Lula #boato", "resultado_esperado": "sem_match"},
    ]
    assert chave("Anitta retira apoio à candidatura de Lula #boato") == chave("anitta retira apoio a candidatura de lula")
    d = preparar(buscador, casos)
    assert d.loc[1, "posicao_certa"] == 1 and not d["alvo_ausente"].any()
    g = grade(d)
    par = escolher(g)
    assert par["controles_ja_checado"] <= 2 and par["reescritas_mostradas"] == 1.0
    assert avaliar(d, 0.85, 0.60)["negacao_ja_checado"] == 0


def test_teto_conta_todo_controle_que_recebe_checagem():
    g = pd.DataFrame([
        {"limite_alta": 0.80, "limite_media": 0.50, "controles_ja_checado": 0, "controles_mostrados": 26,
         "reescritas_mostradas": 0.71, "confirmados_ja_checado": 6},
        {"limite_alta": 0.75, "limite_media": 0.66, "controles_ja_checado": 2, "controles_mostrados": 10,
         "reescritas_mostradas": 0.40, "confirmados_ja_checado": 6},   # empurrar para 'ja_checado' não engana o teto
        {"limite_alta": 0.80, "limite_media": 0.70, "controles_ja_checado": 0,
         "controles_mostrados": MAX_CONTROLES_MOSTRADOS, "reescritas_mostradas": 0.25, "confirmados_ja_checado": 6},
    ])
    assert escolher(g)["limite_media"] == 0.70                       # com o teto (regra 1b)
    assert escolher(g, max_mostrados=None)["limite_media"] == 0.50   # sem o teto, só para comparação


def test_negacao_em_internetes_e_reconhecida_depois_da_normalizacao(buscador):
    # "ñ" só vira "não" na normalização: sem ela, o filtro da RN-06 não veria a negação
    r = buscador.buscar("Anitta ñ retira apoio à candidatura de Lula")
    assert r[0]["id"] == "t:1" and r[0]["faixa"] != "ja_checado"
