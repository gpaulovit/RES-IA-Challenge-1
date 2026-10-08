"""Módulo de regras de negócio de mensagens, formatação e transparência do Bot.

Atende:
- RF-02: Textos de /start e /ajuda.
- RF-04: Tratamento de link que falha extração.
- RF-07: Resposta da Camada 1 (já checado ou relacionado).
- RF-08: Resposta da Camada 2 (faixas de alerta e sinais).
- RF-09: Rodapé com avisos de limitação e links oficiais (TSE e agências).
- RF-10: Tratamento de mídias não suportadas (áudio, foto, vídeo, sticker).
- RF-11: Tratamento de mensagens com menos de 5 palavras.
- RN-01: O bot nunca afirma verdadeiro ou falso.
- RN-05: Faixas de semelhança da Camada 1.
- RN-07: Formato fixo de resposta.
- RNF-07: Transparência (100% com fonte ou aviso de limitação).
- RNF-09: Robustez diante de entradas vazias, longas, emojis ou quebradas.
"""

from __future__ import annotations

import re
from typing import Any

LIMIAR_ALTO = 0.85
LIMIAR_MEDIO = 0.60
LIMITE_MAX_CARACTERES = 5000

RODAPE_TRANSPARENCIA_PADRAO = (
    "\n\n---\n"
    "ℹ️ *Aviso de Limitação:* O bot não dá veredito próprio de verdadeiro ou falso.\n"
    "Consulte sempre as agências de checagem e os canais oficiais:\n"
    "• TSE Fato ou Boato: https://www.tse.jus.br/fato-ou-boato\n"
    "• Agência Lupa: https://lupa.uol.com.br\n"
    "• Aos Fatos: https://www.aosfatos.org"
)

TEXTO_START_AJUDA = (
    "Olá! Sou o bot de verificação eleitoral do RES-IA (Eleições 2026).\n\n"
    "📌 *Como usar:*\n"
    "Encaminhe uma mensagem de texto ou link de notícia sobre as eleições que você recebeu.\n\n"
    "🔍 *O que eu faço:*\n"
    "1. Procuro se agências de checagem confiáveis (Lupa, Aos Fatos etc.) já checaram algo parecido.\n"
    "2. Se não houver checagem, avalio se o texto possui padrões e sinais de alerta típicos de desinformação.\n\n"
    "⚠️ *O que eu NÃO faço:*\n"
    "O bot nunca dá veredito próprio de 'verdade' ou 'mentira'. Quem atesta são as agências jornalísticas.\n"
    "Aceito apenas texto e links (não analiso fotos, áudios ou vídeos)."
    f"{RODAPE_TRANSPARENCIA_PADRAO}"
)


def classificar_entrada(
    texto: str | None,
    tipo_mensagem: str = "texto",
) -> dict[str, Any]:
    """Analisa e higieniza a entrada recebida pelo bot, garantindo a robustez (RNF-09).

    Returns:
        dict contendo:
            'valido': bool
            'tipo': 'texto', 'link', 'midia_invalida', 'entrada_vazia', 'curto', 'apenas_emojis'
            'texto_sanitizado': str | None
            'resposta_imediata': str | None (se a entrada for inválida)
    """
    tipo_msg = str(tipo_mensagem).lower().strip()
    if tipo_msg in {"photo", "audio", "voice", "video", "sticker", "document", "imagem", "figurinha"}:
        return {
            "valido": False,
            "tipo": "midia_invalida",
            "texto_sanitizado": None,
            "resposta_imediata": (
                "⚠️ No momento só consigo analisar mensagens de *texto* ou *links* de notícias. "
                "Envie o texto copiado ou o link para checagem."
                f"{RODAPE_TRANSPARENCIA_PADRAO}"
            ),
        }

    if texto is None:
        return {
            "valido": False,
            "tipo": "entrada_vazia",
            "texto_sanitizado": None,
            "resposta_imediata": (
                "⚠️ Mensagem vazia recebida. Por favor, envie um texto ou link para verificação."
                f"{RODAPE_TRANSPARENCIA_PADRAO}"
            ),
        }

    texto_limpo = texto.strip()
    if not texto_limpo:
        return {
            "valido": False,
            "tipo": "entrada_vazia",
            "texto_sanitizado": None,
            "resposta_imediata": (
                "⚠️ Mensagem vazia recebida. Por favor, envie um texto ou link para verificação."
                f"{RODAPE_TRANSPARENCIA_PADRAO}"
            ),
        }

    # Verifica se é um link HTTP/HTTPS
    if re.match(r"^https?://[^\s]+$", texto_limpo):
        return {
            "valido": True,
            "tipo": "link",
            "texto_sanitizado": texto_limpo,
            "resposta_imediata": None,
        }

    # Remove caracteres puramente não-alfanuméricos para ver se sobraram palavras reais
    caracteres_palavra = re.findall(r"\w+", texto_limpo, re.UNICODE)
    if not caracteres_palavra:
        return {
            "valido": False,
            "tipo": "apenas_emojis",
            "texto_sanitizado": None,
            "resposta_imediata": (
                "⚠️ A mensagem enviada não contém palavras identificáveis. "
                "Por favor, envie o texto da notícia ou alegação eleitoral."
                f"{RODAPE_TRANSPARENCIA_PADRAO}"
            ),
        }

    # RF-11: Textos com menos de 5 palavras recebem pedido de mais contexto
    palavras = texto_limpo.split()
    if len(palavras) < 5:
        return {
            "valido": False,
            "tipo": "curto",
            "texto_sanitizado": None,
            "resposta_imediata": (
                "⚠️ Texto muito curto para conferência (menos de 5 palavras). "
                "Por favor, envie a mensagem completa ou com mais contexto sobre a alegação."
                f"{RODAPE_TRANSPARENCIA_PADRAO}"
            ),
        }

    # RNF-09: Entrada muito longa não derruba o bot (trunca graciosamente)
    if len(texto_limpo) > LIMITE_MAX_CARACTERES:
        texto_limpo = texto_limpo[:LIMITE_MAX_CARACTERES]

    return {
        "valido": True,
        "tipo": "texto",
        "texto_sanitizado": texto_limpo,
        "resposta_imediata": None,
    }


def formatar_resposta_link_quebrado() -> str:
    """Mensagem de erro amigável quando a extração de link falha (RF-04)."""
    return (
        "⚠️ Não foi possível abrir ou extrair o texto principal do link enviado.\n"
        "Por favor, copie o texto da notícia e cole diretamente aqui na conversa."
        f"{RODAPE_TRANSPARENCIA_PADRAO}"
    )


def formatar_resposta_camada1(
    checagem: dict[str, Any],
    semelhanca: float,
) -> str:
    """Monta a resposta quando uma checagem factual é encontrada (RF-06, RF-07, RN-05, RN-07)."""
    alegacao = checagem.get("alegacao") or checagem.get("texto_indexado", "Informação sob checagem")
    veredito_original = checagem.get("veredito_original") or checagem.get("veredito", "Checado")
    agencia = checagem.get("agencia", "Agência de Checagem")
    data = checagem.get("data", "Data não informada")
    link = checagem.get("link", "Link não disponível")

    if semelhanca >= LIMIAR_ALTO:
        status = "🔍 *Essa informação já foi checada por uma agência:*"
    else:
        status = "⚠️ *Encontrei uma checagem relacionada (semelhança média):*"

    resposta = (
        f"{status}\n\n"
        f"📌 *Alegação checada:* {alegacao}\n"
        f"🏷️ *Veredito da agência:* {veredito_original} (segundo {agencia})\n"
        f"📅 *Data:* {data}\n"
        f"🔗 *Leia a checagem completa:* {link}"
        f"{RODAPE_TRANSPARENCIA_PADRAO}"
    )
    return resposta


def formatar_resposta_camada2(
    faixa: str,
    sinais: list[str] | None = None,
) -> str:
    """Monta a resposta do classificador quando não há checagem prévia (RF-08, RF-09)."""
    sinais_str = ""
    if sinais:
        termos = ", ".join(f"`{s}`" for s in sinais[:3])
        sinais_str = f"\n🔎 *Termos que mais pesaram no texto:* {termos}"

    faixa_norm = faixa.strip().lower()
    if faixa_norm == "muitos_sinais":
        alerta = "🚨 *Atenção: Muitos sinais de alerta de desinformação identificados*"
        explicacao = (
            "Não encontramos checagens prévias para este texto, mas ele apresenta fortes "
            "características estilísticas comuns em conteúdos enganosos ou alarmistas."
        )
    elif faixa_norm == "poucos_sinais":
        alerta = "✅ *Poucos sinais de alerta identificados*"
        explicacao = (
            "Não encontramos checagens prévias de agências, e o texto apresenta poucos "
            "traços formais típicos de boatos conhecidos."
        )
    else:  # 'incerto'
        alerta = "⚖️ *Sinais incertos / inconclusivos*"
        explicacao = (
            "Não encontramos checagens prévias e a análise do texto resultou em sinais mistos. "
            "Recomendamos cautela redobrada antes de repassar."
        )

    resposta = (
        f"{alerta}\n\n"
        f"{explicacao}"
        f"{sinais_str}\n\n"
        "💡 *Lembre-se:* O bot avalia apenas o estilo e padrões do texto, NÃO a veracidade dos fatos."
        f"{RODAPE_TRANSPARENCIA_PADRAO}"
    )
    return resposta


def formatar_resposta_sem_camada2() -> str:
    """Resposta de fallback quando a Camada 2 está desativada por no-go (RN-04)."""
    return (
        "🔍 Não encontramos nenhuma checagem prévia para esta mensagem na base das agências parceiras.\n\n"
        "Como a alegação ainda não foi verificada por jornalistas, recomendamos cautela antes de compartilhar."
        f"{RODAPE_TRANSPARENCIA_PADRAO}"
    )


def validar_transparencia_resposta(resposta: str, camada: int) -> bool:
    """Verifica se uma resposta respeita rigorosamente o requisito RNF-07.

    - Camada 1: deve conter link da checagem e nome de agência/fonte.
    - Camada 2: deve conter aviso de limitação e links oficiais.
    """
    if not resposta or not resposta.strip():
        return False

    tem_aviso = "Aviso de Limitação" in resposta or "tse.jus.br" in resposta
    if not tem_aviso:
        return False

    if camada == 1:
        # Camada 1 precisa ter link e indicação de agência
        tem_link = "http://" in resposta or "https://" in resposta
        tem_agencia = "agência" in resposta.lower() or "segundo" in resposta.lower()
        return tem_link and tem_agencia

    if camada == 2:
        # Camada 2 precisa ter limitação expressa
        tem_ressalva = "não dá veredito" in resposta.lower() or "não a veracidade" in resposta.lower()
        return tem_ressalva

    return True
