"""Testes do bot do Telegram (src/checagens/bot.py).

Testamos só as partes que não precisam de internet, de token do Telegram nem de celular:
- como a mensagem é classificada (link, texto curto ou texto normal);
- como a resposta é montada no modo de teste (MODO_TESTE=1);
- como o arquivo .env é lido;
- como o texto de uma página é extraído (a página é simulada).
"""

import os
from email.message import Message

import pytest

from checagens import bot
from checagens.bot import (
    AVISO_E_LINKS,
    MAX_ALEGACAO,
    buscar_falso,
    carregar_env,
    classificar_falso,
    extrair_texto_do_link,
    ligado,
    montar_resposta,
    tipo_de_texto,
)


# ---------------------------------------------------------------------------
# Entrada: o bot decide se recebeu link, texto curto ou texto normal
# ---------------------------------------------------------------------------

def test_mensagem_so_com_link_e_reconhecida_como_link():
    assert tipo_de_texto("https://www.exemplo.com.br/noticia") == "link"


def test_mensagem_com_menos_de_cinco_palavras_e_curta():
    assert tipo_de_texto("Oi, tudo bem?") == "curto"


def test_mensagem_com_cinco_palavras_ou_mais_e_texto():
    assert tipo_de_texto("O governo anunciou uma nova medida hoje") == "texto"


def test_link_no_meio_da_mensagem_ainda_nao_e_tratado_como_link():
    # Comportamento atual, registrado de propósito: só vira "link" quando a
    # mensagem inteira é o link. Link no meio do texto ainda é "texto".
    assert tipo_de_texto("Olha isso https://exemplo.com.br/noticia") == "texto"


# ---------------------------------------------------------------------------
# Resposta no modo de teste (MODO_TESTE=1): usa o modelo de mentira do bot
# ---------------------------------------------------------------------------

def _responder(texto):
    mensagem, _ = montar_resposta(texto, buscar_falso, classificar_falso, "falso")
    return mensagem


def test_checagem_igual_aparece_como_ja_conferida():
    # Fala de "banqueiros" e "pix", sem negação: é a checagem falso-001.
    resposta = _responder("Dizem que banqueiros querem revogar o Pix para apoiar Lula")

    assert "Essa notícia já foi conferida" in resposta
    assert "Boatos.org" in resposta
    assert "em 01/08/2022" in resposta
    assert "Resultado: <b>Falso</b>" in resposta


def test_negacao_rebaixa_checagem_igual_para_relacionada():
    # Mesmo assunto, mas com "não": o bot não pode afirmar que é a mesma notícia (RN-06).
    resposta = _responder("Banqueiros não querem revogar o Pix para apoiar Lula")

    assert "Achei uma notícia parecida" in resposta
    assert "Essa notícia já foi conferida" not in resposta


def test_assunto_parecido_aparece_como_relacionada_com_sinal_curto():
    resposta = _responder("Anitta comentou sobre a eleição nas redes sociais")

    assert "Achei uma notícia parecida" in resposta
    assert "Sobre a sua mensagem" in resposta


def test_sem_checagem_e_com_alertas_mostra_muitos_sinais():
    resposta = _responder("URGENTE compartilhe isso antes que apaguem essa verdade")

    assert "muitos sinais de fake news" in resposta
    assert "urgente" in resposta


def test_pergunta_sem_checagem_mostra_nao_da_para_saber():
    resposta = _responder("A vacina de cachorro muda o clima do planeta inteiro?")

    assert "Não dá para saber só pelo texto." in resposta


def test_texto_comum_sem_checagem_mostra_poucos_sinais():
    resposta = _responder("O tempo em Curitiba ficou nublado durante toda a tarde de quarta")

    assert "Poucos sinais de fake news." in resposta


@pytest.mark.parametrize("texto", [
    "Dizem que banqueiros querem revogar o Pix para apoiar Lula",
    "URGENTE compartilhe isso antes que apaguem essa verdade",
    "O tempo em Curitiba ficou nublado durante toda a tarde de quarta",
])
def test_toda_resposta_traz_aviso_de_robo_e_links_oficiais(texto):
    resposta = _responder(texto)

    assert "Sou um robô e posso errar" in resposta
    assert AVISO_E_LINKS in resposta


def test_busca_devolve_no_maximo_tres_resultados_em_ordem_de_semelhanca():
    resultados = buscar_falso("Banqueiros, Pix, Anitta e Renner juntos na mesma frase")

    assert len(resultados) <= 3
    semelhancas = [r["semelhanca"] for r in resultados]
    assert semelhancas == sorted(semelhancas, reverse=True)


def test_busca_com_texto_vazio_levanta_erro():
    with pytest.raises(ValueError):
        buscar_falso("   ")


def test_sem_camadas_reais_responde_que_nao_encontrou_e_avisa_o_teste():
    # Sem busca e sem classificador (None, None): o bot não inventa resultado.
    mensagem, _ = montar_resposta("texto qualquer com palavras suficientes", None, None, "real")

    assert bot.AVISO_TESTE in mensagem
    assert "Nenhum site de checagem conferiu essa notícia ainda" in mensagem


# ---------------------------------------------------------------------------
# Configuração: MODO_TESTE, CAMADA2_LIGADA e o arquivo .env
# ---------------------------------------------------------------------------

def test_modo_teste_liga_o_modelo_de_mentira(monkeypatch):
    monkeypatch.setenv("MODO_TESTE", "1")

    _, _, modo = bot.carregar_camadas()

    assert modo == "falso"


@pytest.mark.parametrize("valor, esperado", [
    ("1", True),
    ("sim", True),
    ("TRUE", True),
    ("0", False),
    ("nao", False),
])
def test_ligado_aceita_so_valores_de_sim(monkeypatch, valor, esperado):
    monkeypatch.setenv("CHAVE_TESTE_LIGADO", valor)

    assert ligado("CHAVE_TESTE_LIGADO") is esperado


def test_ligado_sem_variavel_e_desligado(monkeypatch):
    monkeypatch.delenv("CHAVE_TESTE_LIGADO", raising=False)

    assert ligado("CHAVE_TESTE_LIGADO") is False


def test_carregar_env_le_chave_valor_e_nao_sobrescreve(monkeypatch, tmp_path):
    # Para cada chave: setenv + delenv. O monkeypatch lembra que a chave não existia e
    # a remove no fim do teste, então os valores lidos do arquivo não vazam para outros testes.
    for chave in ["CHAVE_NOVA_TESTE_BOT", "OUTRA_CHAVE_TESTE_BOT"]:
        monkeypatch.setenv(chave, "")
        monkeypatch.delenv(chave)
    monkeypatch.setenv("CHAVE_JA_DEFINIDA_TESTE_BOT", "do_sistema")
    arquivo = tmp_path / ".env"
    arquivo.write_text(
        "# comentário ignorado\n"
        "CHAVE_NOVA_TESTE_BOT=valor_do_arquivo\n"
        "export OUTRA_CHAVE_TESTE_BOT='com aspas'\n"
        "CHAVE_JA_DEFINIDA_TESTE_BOT=outro_valor\n",
        encoding="utf-8",
    )

    carregar_env(arquivo)

    assert os.environ["CHAVE_NOVA_TESTE_BOT"] == "valor_do_arquivo"
    assert os.environ["OUTRA_CHAVE_TESTE_BOT"] == "com aspas"
    assert os.environ["CHAVE_JA_DEFINIDA_TESTE_BOT"] == "do_sistema"


# ---------------------------------------------------------------------------
# Texto de link: a página é simulada, sem internet
# ---------------------------------------------------------------------------

PAGINA = (
    "<html><head><title>Título da página</title>"
    '<meta property="og:description" content="Resumo curto da notícia"></head>'
    "<body><p>Este é um parágrafo longo o suficiente para entrar na leitura do texto.</p>"
    "</body></html>"
)


class RespostaFalsa:
    """Imita o que urlopen devolve: status, cabeçalhos e corpo."""

    def __init__(self, corpo, status=200, tipo="text/html; charset=utf-8"):
        self._corpo = corpo.encode("utf-8")
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = tipo

    def read(self, _tamanho=-1):
        return self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def test_extrai_titulo_descricao_e_paragrafo_da_pagina(monkeypatch):
    monkeypatch.setattr(bot.urllib.request, "urlopen", lambda *_a, **_k: RespostaFalsa(PAGINA))

    texto = extrair_texto_do_link("https://exemplo.com.br/noticia")

    assert "Título da página" in texto
    assert "Resumo curto da notícia" in texto
    assert "parágrafo longo" in texto


def test_pagina_com_erro_http_devolve_none(monkeypatch):
    monkeypatch.setattr(
        bot.urllib.request, "urlopen", lambda *_a, **_k: RespostaFalsa(PAGINA, status=404)
    )

    assert extrair_texto_do_link("https://exemplo.com.br/sumiu") is None


def test_sem_internet_devolve_none(monkeypatch):
    def sem_rede(*_a, **_k):
        raise OSError("sem internet")

    monkeypatch.setattr(bot.urllib.request, "urlopen", sem_rede)

    assert extrair_texto_do_link("https://exemplo.com.br/noticia") is None


# ---------------------------------------------------------------------------
# Pequenas funções de formatação
# ---------------------------------------------------------------------------

def test_alegacao_muito_longa_e_cortada_com_reticencias():
    cortado = bot._cortar("palavra " * 100)

    assert len(cortado) <= MAX_ALEGACAO
    assert cortado.endswith("…")


def test_data_aaaa_mm_dd_vira_formato_brasileiro():
    assert bot._data_br("2022-08-01") == " em 01/08/2022"
    assert bot._data_br(None) == ""
