"""Compara dois baselines lexicais em cenários fictícios e auditáveis."""

import argparse
import json
from pathlib import Path
from statistics import mean
from time import perf_counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from checagens.embeddings import BaselineHashing

AMOSTRA = Path("data/amostras/avaliacao-arquitetura.json")


def carregar_amostra(caminho: Path) -> dict:
    try:
        amostra = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as erro:
        raise ValueError("Não foi possível ler a amostra JSON em UTF-8.") from erro
    if not isinstance(amostra, dict) or not isinstance(amostra.get("alegacoes"), list) or not isinstance(amostra.get("consultas"), list):
        raise ValueError("A amostra precisa conter listas de alegacoes e consultas.")
    if not amostra["alegacoes"] or not amostra["consultas"]:
        raise ValueError("A amostra precisa conter alegações e consultas.")
    ids = [item.get("id") for item in amostra["alegacoes"] if isinstance(item, dict)]
    if len(ids) != len(amostra["alegacoes"]) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("As alegações precisam ter ids únicos e não vazios.")
    for item in amostra["alegacoes"]:
        if not isinstance(item.get("texto"), str) or not item["texto"].strip():
            raise ValueError("Toda alegação precisa de texto.")
    for item in amostra["consultas"]:
        if not isinstance(item, dict) or not isinstance(item.get("texto"), str) or not item["texto"].strip() or not isinstance(item.get("tipo"), str):
            raise ValueError("Toda consulta precisa de tipo e texto.")
        if item.get("id_referencia") is not None and item["id_referencia"] not in ids:
            raise ValueError("Uma consulta aponta para um id inexistente.")
    if not any(item["id_referencia"] is not None for item in amostra["consultas"]):
        raise ValueError("A amostra precisa de ao menos uma consulta com referência.")
    return amostra


def avaliar(amostra: dict) -> dict:
    ids = [item["id"] for item in amostra["alegacoes"]]
    textos = [item["texto"] for item in amostra["alegacoes"]]
    consultas = amostra["consultas"]
    saida = {"aviso": amostra.get("aviso", "Amostra de demonstração."), "quantidade_alegacoes": len(ids), "quantidade_consultas": len(consultas), "metodos": {}}
    for nome, preparar in (
        ("tfidf", TfidfVectorizer(lowercase=True, strip_accents="unicode")),
        ("hashing_lexical", BaselineHashing()),
    ):
        inicio = perf_counter()
        if nome == "tfidf":
            vetores = preparar.fit_transform(textos)
            transformar = preparar.transform
            bytes_vetores = int(vetores.data.nbytes + vetores.indices.nbytes + vetores.indptr.nbytes)
        else:
            vetores = preparar.gerar(textos)
            transformar = preparar.gerar
            bytes_vetores = int(vetores.nbytes)
        tempo_preparo_ms = (perf_counter() - inicio) * 1000
        resultados = []
        tempos_ms = []
        for caso in consultas:
            inicio = perf_counter()
            pontos = cosine_similarity(transformar([caso["texto"]]), vetores)[0]
            ordem = sorted(range(len(ids)), key=lambda pos: (-float(pontos[pos]), ids[pos]))
            tempos_ms.append((perf_counter() - inicio) * 1000)
            referencia = caso.get("id_referencia")
            posicao = next((rank for rank, indice in enumerate(ordem, 1) if ids[indice] == referencia and pontos[indice] > 0), None) if referencia else None
            resultados.append({"tipo": caso["tipo"], "consulta": caso["texto"], "id_referencia": referencia, "primeiro_id": ids[ordem[0]], "primeira_pontuacao": round(float(pontos[ordem[0]]), 4), "posicao_referencia": posicao})
        positivos = [item for item in resultados if item["id_referencia"] is not None]
        saida["metodos"][nome] = {
            "recall_1": round(mean(item["posicao_referencia"] == 1 for item in positivos), 3),
            "recall_3": round(mean(item["posicao_referencia"] is not None and item["posicao_referencia"] <= 3 for item in positivos), 3),
            "mrr": round(mean(1 / item["posicao_referencia"] if item["posicao_referencia"] else 0 for item in positivos), 3),
            "tempo_preparo_ms": round(tempo_preparo_ms, 3),
            "tempo_medio_consulta_ms": round(mean(tempos_ms), 3),
            "bytes_vetores": bytes_vetores,
            "resultados": resultados,
        }
    return saida


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--amostra", type=Path, default=AMOSTRA)
    args = parser.parse_args()
    try:
        print(json.dumps(avaliar(carregar_amostra(args.amostra)), ensure_ascii=False, indent=2))
    except ValueError as erro:
        parser.exit(1, f"Não foi possível avaliar: {erro}\n")


if __name__ == "__main__":
    main()
