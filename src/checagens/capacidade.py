"""Mede apenas a comparação exata de vetores sintéticos, sem dados reais."""

import argparse
import json
from statistics import median
from time import perf_counter

import numpy as np


def medir(quantidade: int = 1882, dimensoes: int = 256, consultas: int = 100) -> dict:
    if min(quantidade, dimensoes, consultas) < 1:
        raise ValueError("Quantidade, dimensões e consultas devem ser positivas.")
    rng = np.random.default_rng(42)
    vetores = rng.normal(size=(quantidade, dimensoes)).astype("float32")
    vetores /= np.linalg.norm(vetores, axis=1, keepdims=True)
    consulta = rng.normal(size=dimensoes).astype("float32")
    consulta /= np.linalg.norm(consulta)
    tempos = []
    for _ in range(consultas):
        inicio = perf_counter()
        scores = vetores @ consulta
        int(np.argmax(scores))
        tempos.append((perf_counter() - inicio) * 1000)
    ordenados = sorted(tempos)
    return {
        "tipo": "vetores_sinteticos_busca_exata",
        "aviso": "Mede só a comparação em memória neste computador; não mede modelo, disco, rede ou qualidade de busca.",
        "quantidade_vetores": quantidade,
        "dimensoes": dimensoes,
        "consultas": consultas,
        "bytes_vetores": int(vetores.nbytes),
        "mediana_ms": round(median(tempos), 4),
        "p95_ms": round(ordenados[min(len(ordenados) - 1, int(0.95 * len(ordenados)))], 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quantidade", type=int, default=1882)
    parser.add_argument("--dimensoes", type=int, default=256)
    parser.add_argument("--consultas", type=int, default=100)
    args = parser.parse_args()
    try:
        print(json.dumps(medir(args.quantidade, args.dimensoes, args.consultas), ensure_ascii=False, indent=2))
    except ValueError as erro:
        parser.exit(1, f"Não foi possível medir: {erro}\n")


if __name__ == "__main__":
    main()
