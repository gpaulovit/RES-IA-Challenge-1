#!/usr/bin/env python3
"""
Simulador Interativo do Bot no Telegram (ChecaAI).
Permite testar exatamente as entradas e saídas que o usuário veria no aplicativo Telegram,
sem depender de rede, token do Telegram ou chip de celular.
"""

import sys
import os
from pathlib import Path

# Adiciona src ao PYTHONPATH
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from checagens.bot import (
    tipo_de_texto,
    extrair_texto_do_link,
    montar_resposta,
    ERRO_CURTO,
    ERRO_LINK,
    ERRO_MIDIA,
    carregar_camadas,
    carregar_env,
)


def simular_consulta(texto: str, buscar=None, classificar=None, modo="falso"):
    print("=" * 70)
    print(f"📩 ENTRADA ENVIADA PELO USUÁRIO:\n{texto}")
    print("=" * 70)

    tipo = tipo_de_texto(texto)
    print(f"⚙️  Tipo detectado: '{tipo}'")

    if tipo == "curto":
        print(f"\n🤖 RESPOSTA DO BOT (ChecaAI):\n{ERRO_CURTO}")
        return

    if tipo == "link":
        print("🌐 Extraindo conteúdo da URL...")
        extraido = extrair_texto_do_link(texto.strip())
        if extraido is None:
            print(f"\n🤖 RESPOSTA DO BOT (ChecaAI):\n{ERRO_LINK}")
            return
        print(f"📄 Texto extraído ({len(extraido)} caracteres): {extraido[:120]}...")
        texto = extraido

    resposta, dados = montar_resposta(texto, buscar, classificar, modo)

    print(f"\n🤖 RESPOSTA DO BOT (ChecaAI):\n{resposta}")
    print("-" * 70)
    print(f"🔘 Botões Inline: [ 👍 Útil ]   [ 👎 Não útil ]")
    print(f"📊 Metadados de Auditoria: {dados}")
    print("=" * 70 + "\n")


def main():
    carregar_env()
    buscar, classificar, modo = carregar_camadas()
    print(f"🚀 Simulador ChecaAI Inicializado | Modo: {modo.upper()} | Camada 1: {'ON' if buscar else 'OFF'} | Camada 2: {'ON' if classificar else 'OFF'}\n")

    testes = [
        # 1. Boato com mais de 5 palavras
        "Alexandre de Moraes recebeu 60 milhões para fraudar as urnas eletrônicas",
        # 2. Entidade que antes dava falso positivo
        "Flávio Bolsonaro e o tesouraço no orçamento do governo federal",
        # 3. Mensagem curta (RF-11)
        "Urna fraudada?",
        # 4. Mensagem com muitos sinais
        "URGENTE COMPARTILHEM ANTES QUE APAGUE FRAUDE CONFIRMADA NAS ELEIÇÕES 2026",
        # 5. Link de teste
        "https://www.tse.jus.br",
    ]

    for t in testes:
        simular_consulta(t, buscar, classificar, modo)


if __name__ == "__main__":
    main()
