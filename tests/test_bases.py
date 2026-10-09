"""Testes das regras das bases de dados (não precisam dos dados brutos)."""

import pandas as pd
import pytest

from checagens.bases.checagens import CAMPOS, amostra_recente, deduplicar, validar
from checagens.bases.texto import (chave_link, chave_texto, eh_multi_alegacao, ler_data, ler_data_br,
                                   ler_data_factpolcheckbr, limpar_titulo, link_valido)
from checagens.bases.treino import CARIMBOS, remover_carimbos
from checagens.bases.vereditos import carimbo_do_titulo, nome_agencia, normalizar


@pytest.mark.parametrize("original, esperado", [
    ("Falsa", "falso"), ("falso", "falso"), ("#boato", "falso"), ("É #FAKE", "falso"), ("É falso", "falso"),
    ("Parcialmente verdadeira", "enganoso"), ("Distorcido", "enganoso"), ("Sem contexto", "enganoso"),
    ("exagerado", "enganoso"), ("impreciso", "enganoso"), ("Subestimado", "enganoso"),
    ("Verdadeiro", "verdadeiro"), ("Verdadeiro, mas", "verdadeiro"), ("É #FATO", "verdadeiro"),
    ("Impossível provar", "outro"), ("Ainda é cedo para dizer", "outro"), ("insustentável", "outro"),
    ("De olho", "outro"), ("rótulo desconhecido", "outro"),
])
def test_taxonomia_rn02(original, esperado):
    assert normalizar(original) == esperado


@pytest.mark.parametrize("titulo, carimbo", [
    ("É #FAKE que Bolsonaro publicou decreto", "É #FAKE"),
    ("Marina Silva é dona de madeira apreendida #boato", "#boato"),
    ("#Verificamos: É falso que STF aprovou auxílio", "É falso"),
    ("Enganoso: post sobre vacina", "Enganoso"),
    ("Bolsonaro não propôs anexar Sergipe à Bahia", None),        # sem carimbo: sem veredito
    ("Post engana ao dizer que ponte é obra do governo", None),   # verbo não é carimbo
    ("É montagem foto de Doria pichando muro", None),             # descrição não é carimbo
    ("É verdade que Kid Bengala virou evangélico?", None),        # pergunta
    ("Veja o que é #FATO ou #FAKE nas declarações", None),        # dois sentidos
])
def test_carimbo_so_do_que_a_agencia_escreveu(titulo, carimbo):
    assert carimbo_do_titulo(titulo) == carimbo


@pytest.mark.parametrize("link, dominio, nome", [
    ("https://piaui.folha.uol.com.br/lupa/2019/07/22/x/", "uol.com.br", "Agência Lupa"),
    ("https://noticias.uol.com.br/confere/ultimas-noticias/x.htm", "uol.com.br", "UOL Confere"),
    ("https://noticias.uol.com.br/comprova/x.htm", "uol.com.br", "Projeto Comprova"),
    ("https://noticias.uol.com.br/videos/?id=x", "uol.com.br", "UOL"),
    ("https://g1.globo.com/fato-ou-fake/noticia/x.ghtml", "globo.com", "Fato ou Fake"),
    ("https://www.e-farsas.com/x.html", "r7.com", "E-farsas"),
    ("https://exemplo.com/x", "", None),
])
def test_nome_agencia_pelo_link(link, dominio, nome):
    assert nome_agencia(link, dominio) == nome


def test_chave_link_ignora_rastreio_www_barra_e_codificacao():
    a = "http://www.projetocomprova.com.br/publica%C3%A7%C3%B5es/x/?utm_source=zap&fbclid=1#topo"
    b = "https://projetocomprova.com.br/publicações/x"
    assert chave_link(a) == chave_link(b)
    assert chave_link("https://a.com/x?id=1") != chave_link("https://a.com/x?id=2")


def test_chave_texto_ignora_caixa_espaco_e_pontuacao():
    assert chave_texto("Lula  anunciou a Guarda Nacional!") == chave_texto("lula anunciou a guarda nacional")


def test_link_valido():
    assert link_valido("https://aosfatos.org/x")
    assert not link_valido(None) and not link_valido("") and not link_valido("aosfatos.org/x")


def test_datas():
    assert ler_data_factpolcheckbr("8/2/2022") == ("2022-08-02", "ambigua_lida_mes_dia")
    assert ler_data_factpolcheckbr("10/30/2022") == ("2022-10-30", "mes_dia")
    assert ler_data_factpolcheckbr("9/9/2022") == ("2022-09-09", "mes_dia")   # dia = mês: sem ambiguidade
    assert ler_data_factpolcheckbr("30/10/2022") == ("2022-10-30", "dia_mes")
    assert ler_data("2019-07-22 13:00:20") == "2019-07-22"
    assert ler_data("11/01/2021") == "2021-01-11"
    assert ler_data("5/04/20195") is None and ler_data("") is None and ler_data(None) is None
    assert ler_data_br("31/10/2017 10h17") == "2017-10-31"
    assert ler_data_br("03 de março de 2015") == "2015-03-03"
    assert ler_data_br("28/2/18") == "2018-02-28"


def test_limpar_titulo_e_multi_alegacao():
    assert limpar_titulo("#Verificamos: É falso que STF aprovou auxílio") == "STF aprovou auxílio"
    assert limpar_titulo("É #FAKE que vídeo mostra X") == "Vídeo mostra X"
    assert limpar_titulo("Governo não suspendeu insulina | Aos Fatos") == "Governo não suspendeu insulina"
    assert limpar_titulo("Agência Lupa - #Verificamos: Fulano não matou ninguém") == "Fulano não matou ninguém"
    assert eh_multi_alegacao("Veja o que é #FATO ou #FAKE nas declarações")


def _registro(i, alegacao, link, fonte="FactPolCheckBr", data="2022-10-01", agencia="Aos Fatos"):
    return {"id": f"x-{i}", "alegacao": alegacao, "veredito_original": "Falsa", "veredito_normalizado": "falso",
            "agencia": agencia, "data": data, "link": link, "fonte_dataset": fonte}


def test_deduplicar_por_link_e_por_alegacao_com_prioridade():
    d = pd.DataFrame([
        _registro(1, "Alegação um aqui", "https://a.com/1?utm_source=x", fonte="FactChecks.br/Central de Fatos"),
        _registro(2, "Outra alegação aqui", "https://www.a.com/1/", fonte="FACTCK.BR"),
        _registro(3, "alegação UM aqui!", "https://a.com/3"),
        _registro(4, "Terceira alegação aqui", "https://a.com/4"),
    ])
    mantidos, removidos = deduplicar(d)
    assert sorted(mantidos["id"]) == ["x-2", "x-3", "x-4"]
    assert dict(zip(removidos["id"], removidos["criterio"])) == {"x-1": "mesmo_link"}
    d.loc[0, "link"] = "https://a.com/9"
    mantidos, removidos = deduplicar(d)
    assert dict(zip(removidos["id"], removidos["mantido"])) == {"x-1": "x-3"}


def test_deduplicar_tira_link_com_vereditos_conflitantes():
    d = pd.DataFrame([_registro(1, "Alegação um aqui", "https://a.com/1"),
                      {**_registro(2, "Alegação um aqui", "https://www.a.com/1", fonte="FACTCK.BR"),
                       "veredito_normalizado": "verdadeiro"},
                      _registro(3, "Outra alegação", "https://a.com/3")])
    mantidos, removidos = deduplicar(d)
    assert list(mantidos["id"]) == ["x-3"]
    assert set(removidos["criterio"]) == {"veredito_conflitante_no_mesmo_link"}


def test_validar_recusa_contrato_quebrado():
    bom = _registro(1, "Alegação um aqui", "https://a.com/1")
    validar([bom])
    with pytest.raises(AssertionError):
        validar([{**bom, "veredito_normalizado": "parcialmente_verdadeiro"}])
    with pytest.raises(AssertionError):
        validar([{**bom, "data": "10/01/2022"}])
    with pytest.raises(AssertionError):
        validar([bom, {**bom, "id": "x-2", "link": "https://www.a.com/1/"}])
    assert list(bom) == CAMPOS


def test_amostra_recente_limita_por_agencia():
    d = pd.DataFrame([_registro(i, f"alegação {i}", f"https://a.com/{i}", data=f"2022-10-{i:02d}",
                                agencia="A" if i > 10 else "B") for i in range(1, 21)])
    a = amostra_recente(d, n=6, maximo_por_agencia=3)
    assert list(a["agencia"].value_counts().sort_index()) == [3, 3]
    assert a["data"].max() == "2022-10-20"


@pytest.mark.parametrize("antes, depois", [
    ("É #FAKE que Lula aparece na lista da Forbes", "Lula aparece na lista da Forbes"),
    ("Urnas programadas para o horário de verão #boato https://www.boatos.org/politica/urnas.html",
     "Urnas programadas para o horário de verão"),
    ("Isso aqui é FALSO!!! não repassem", "Isso aqui não repassem"),
    ("MENTIRA DESLAVADA! Janot não é candidato", "DESLAVADA! Janot não é candidato"),
    ("Boato – Polícia usa radar móvel", "Polícia usa radar móvel"),
])
def test_remover_carimbos(antes, depois):
    texto, achados = remover_carimbos(antes)
    assert texto == depois and achados
    assert not any(p.search(texto) for p in CARIMBOS.values())


def test_remover_carimbos_preserva_texto_sem_carimbo():
    texto = "Notícia sobre a eleição: candidato visita feira em São Paulo"
    assert remover_carimbos(texto) == (texto, [])
