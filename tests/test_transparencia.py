"""Testes automatizados de transparência (RNF-07 e RF-09).

Garante que 100% das respostas emitidas pelo sistema contêm links oficiais,
atribuição da fonte (Camada 1) ou aviso explícito de limitação (Camada 2).
"""

from checagens.mensagens import (
    TEXTO_START_AJUDA,
    formatar_resposta_camada1,
    formatar_resposta_camada2,
    formatar_resposta_link_quebrado,
    formatar_resposta_sem_camada2,
    validar_transparencia_resposta,
)


def test_transparencia_camada1_alta():
    checagem = {
        "alegacao": "Urnas eletrônicas foram impressas sem auditoria pelo TSE",
        "veredito_original": "Falso",
        "agencia": "Agência Lupa",
        "data": "2026-09-15",
        "link": "https://lupa.uol.com.br/checagem/urnas-auditoria-2026",
    }
    resposta = formatar_resposta_camada1(checagem, semelhanca=0.91)

    assert validar_transparencia_resposta(resposta, camada=1) is True
    assert "https://lupa.uol.com.br/checagem/urnas-auditoria-2026" in resposta
    assert "Agência Lupa" in resposta
    assert "tse.jus.br" in resposta
    assert "Aviso de Limitação" in resposta


def test_transparencia_camada1_media():
    checagem = {
        "alegacao": "Tribunal Eleitoral divulgou novo calendário de votação",
        "veredito_original": "Verdadeiro",
        "agencia": "Aos Fatos",
        "data": "2026-08-10",
        "link": "https://www.aosfatos.org/noticias/calendario-tse-2026",
    }
    resposta = formatar_resposta_camada1(checagem, semelhanca=0.74)

    assert validar_transparencia_resposta(resposta, camada=1) is True
    assert "checagem relacionada" in resposta.lower()
    assert "Aos Fatos" in resposta
    assert "Aviso de Limitação" in resposta


def test_transparencia_camada2_todas_faixas():
    for faixa in ["muitos_sinais", "incerto", "poucos_sinais"]:
        resposta = formatar_resposta_camada2(faixa, sinais=["urgente", "bomba", "repassar"])

        assert validar_transparencia_resposta(resposta, camada=2) is True
        assert "tse.jus.br" in resposta
        assert "Aviso de Limitação" in resposta
        assert "NÃO a veracidade" in resposta or "não dá veredito" in resposta


def test_transparencia_start_ajuda_e_fallback():
    assert "Aviso de Limitação" in TEXTO_START_AJUDA
    assert "tse.jus.br" in TEXTO_START_AJUDA

    fallback_no_go = formatar_resposta_sem_camada2()
    assert "Aviso de Limitação" in fallback_no_go
    assert "tse.jus.br" in fallback_no_go

    link_quebrado = formatar_resposta_link_quebrado()
    assert "Aviso de Limitação" in link_quebrado
