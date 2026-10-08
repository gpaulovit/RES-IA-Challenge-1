"""Testes automatizados de robustez (RNF-09 e RF-10/RF-11/RF-04).

Garante que nenhuma entrada inválida, quebrada ou anômala derruba o bot.
"""

import pytest

from checagens.mensagens import (
    classificar_entrada,
    formatar_resposta_link_quebrado,
)


def test_robustez_entrada_vazia():
    for caso in [None, "", "   ", "\n\t  "]:
        res = classificar_entrada(caso)
        assert res["valido"] is False
        assert res["tipo"] == "entrada_vazia"
        assert res["resposta_imediata"] is not None
        assert "vazia" in res["resposta_imediata"].lower()


def test_robustez_apenas_emojis():
    for caso in ["🇧🇷🗳️", "🚩🚩🚩", "⚠️⚠️⚠️‼️", "🎉✨", "👍"]:
        res = classificar_entrada(caso)
        assert res["valido"] is False
        assert res["tipo"] in {"apenas_emojis", "curto"}
        assert res["resposta_imediata"] is not None


def test_robustez_texto_muito_curto_rf11():
    for caso in [
        "Lula ganhou",
        "Urna foi fraudada",
        "Bolsonaro fez discurso ontem",
        "Apenas quatro palavras aqui",
    ]:
        res = classificar_entrada(caso)
        assert res["valido"] is False
        assert res["tipo"] == "curto"
        assert "menos de 5 palavras" in res["resposta_imediata"]


def test_robustez_midias_nao_suportadas_rf10():
    for midia in ["photo", "audio", "voice", "video", "sticker", "figurinha", "imagem"]:
        res = classificar_entrada("qualquer texto", tipo_mensagem=midia)
        assert res["valido"] is False
        assert res["tipo"] == "midia_invalida"
        assert "só consigo analisar mensagens de *texto* ou *links*" in res["resposta_imediata"]


def test_robustez_texto_muito_longo():
    texto_gigante = "Palavra repetida " * 1000  # > 15.000 caracteres
    res = classificar_entrada(texto_gigante)
    assert res["valido"] is True
    assert res["tipo"] == "texto"
    assert len(res["texto_sanitizado"]) <= 5000


def test_robustez_link_valido():
    res = classificar_entrada("https://g1.globo.com/fato-ou-fake/noticia/2026/eleicoes.ghtml")
    assert res["valido"] is True
    assert res["tipo"] == "link"


def test_robustez_link_quebrado_rf04():
    resposta = formatar_resposta_link_quebrado()
    assert "Não foi possível abrir ou extrair" in resposta
    assert "copie o texto da notícia e cole" in resposta
