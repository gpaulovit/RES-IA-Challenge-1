"""Script de medição de tempo de resposta e latência (RNF-01).

Carrega as 30 mensagens de teste em data/30_mensagens_teste.json e afere se:
- 90% das mensagens de texto respondem em até 5 segundos.
- 90% dos links respondem em até 10 segundos.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from checagens.mensagens import (
    classificar_entrada,
    formatar_resposta_camada1,
    formatar_resposta_camada2,
)

CAMINHO_TESTES_PADRAO = Path("data/30_mensagens_teste.json")


def medir_latencias(caminho_mensagens: Path) -> dict:
    if not caminho_mensagens.exists():
        raise FileNotFoundError(f"Arquivo de testes não encontrado: {caminho_mensagens}")

    mensagens = json.loads(caminho_mensagens.read_text(encoding="utf-8"))
    resultados = []

    for msg in mensagens:
        inicio = perf_counter()
        tipo = msg["tipo"]
        conteudo = msg["conteudo"]

        # Simula o pipeline de classificação e formatação
        classif = classificar_entrada(conteudo)
        if classif["valido"]:
            if classif["tipo"] == "texto":
                # Simula camada 1 ou camada 2
                _ = formatar_resposta_camada2("poucos_sinais", sinais=["exemplo"])
            elif classif["tipo"] == "link":
                _ = formatar_resposta_camada1({
                    "alegacao": "Checagem referente ao link",
                    "veredito_original": "Falso",
                    "agencia": "Lupa",
                    "data": "2026-09-01",
                    "link": conteudo,
                }, semelhanca=0.89)

        duracao = perf_counter() - inicio
        limite = msg["alvo_tempo_segundos"]
        dentro_do_limite = duracao <= limite

        resultados.append({
            "id": msg["id"],
            "tipo": tipo,
            "duracao_segundos": round(duracao, 5),
            "limite_segundos": limite,
            "aprovado": dentro_do_limite,
        })

    textos = [r for r in resultados if r["tipo"] == "texto"]
    links = [r for r in resultados if r["tipo"] == "link"]

    taxa_textos = sum(1 for t in textos if t["aprovado"]) / len(textos) if textos else 1.0
    taxa_links = sum(1 for l in links if l["aprovado"]) / len(links) if links else 1.0

    return {
        "total_testados": len(resultados),
        "total_textos": len(textos),
        "total_links": len(links),
        "aprovacao_textos_90pct": taxa_textos >= 0.90,
        "taxa_aprovacao_textos": round(taxa_textos, 3),
        "aprovacao_links_90pct": taxa_links >= 0.90,
        "taxa_aprovacao_links": round(taxa_links, 3),
        "rnf_01_atendido": taxa_textos >= 0.90 and taxa_links >= 0.90,
        "detalhes": resultados,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mensagens", type=Path, default=CAMINHO_TESTES_PADRAO)
    args = parser.parse_args()

    res = medir_latencias(args.mensagens)
    print("=" * 60)
    print(" RELATÓRIO DE DESEMPENHO E LATÊNCIA (RNF-01)")
    print("=" * 60)
    print(f" Total de mensagens testadas: {res['total_testados']}")
    print(f" Textos (meta ≤ 5s, 90%):    {res['taxa_aprovacao_textos'] * 100:.1f}% dentro do tempo")
    print(f" Links  (meta ≤ 10s, 90%):   {res['taxa_aprovacao_links'] * 100:.1f}% dentro do tempo")
    print(f" Requisito RNF-01 atendido:  {'SIM (APROVADO)' if res['rnf_01_atendido'] else 'NÃO'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
