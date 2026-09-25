"""Busca k-NN exata em um índice gerado pelo pipeline de embeddings."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from checagens.embeddings import GeradorEmbeddings, criar_gerador

INDICE_PADRAO = Path("data/indices/experimental")


def _ler_json(caminho: Path, descricao: str):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except OSError as erro:
        raise ValueError(f"Não foi possível ler {descricao}: {caminho}") from erro
    except (json.JSONDecodeError, UnicodeError) as erro:
        raise ValueError(f"{descricao.capitalize()} deve ser JSON válido em UTF-8.") from erro


def carregar_indice(pasta: Path, nome_modelo: str) -> tuple[np.ndarray, list[dict], dict]:
    """Carrega o índice somente após conferir arquivos, hashes e alinhamento."""
    manifesto = _ler_json(pasta / "manifesto.json", "o manifesto")
    metadados = _ler_json(pasta / "metadados.json", "os metadados")
    caminho_vetores = pasta / "vetores.npy"
    if manifesto.get("modelo") != nome_modelo:
        raise ValueError(
            f"O índice usa '{manifesto.get('modelo')}', mas a consulta usa '{nome_modelo}'."
        )
    arquivos = manifesto.get("arquivos")
    if not isinstance(arquivos, dict):
        raise ValueError("O manifesto não contém os hashes dos arquivos.")
    for nome in ("vetores.npy", "metadados.json"):
        caminho = pasta / nome
        try:
            hash_atual = hashlib.sha256(caminho.read_bytes()).hexdigest()
        except OSError as erro:
            raise ValueError(f"Não foi possível ler o arquivo do índice: {caminho}") from erro
        if arquivos.get(nome) != hash_atual:
            raise ValueError(f"O arquivo {nome} foi alterado ou pertence a outra execução.")
    try:
        vetores = np.load(caminho_vetores, allow_pickle=False)
    except (OSError, ValueError) as erro:
        raise ValueError("O arquivo de vetores é inválido.") from erro
    if not isinstance(metadados, list) or vetores.ndim != 2:
        raise ValueError("Vetores ou metadados têm formato inválido.")
    if not len(metadados) == vetores.shape[0] == manifesto.get("quantidade_vetores"):
        raise ValueError("Quantidade de vetores e metadados não corresponde ao manifesto.")
    if vetores.shape[1] != manifesto.get("dimensoes"):
        raise ValueError("Dimensão dos vetores não corresponde ao manifesto.")
    ids = set()
    for linha, item in enumerate(metadados):
        if not isinstance(item, dict) or item.get("linha_vetor") != linha:
            raise ValueError(f"Metadado da linha {linha} está desalinhado.")
        if not item.get("id") or item["id"] in ids:
            raise ValueError(f"Metadado da linha {linha} tem id ausente ou repetido.")
        ids.add(item["id"])
    return np.asarray(vetores, dtype="float32"), metadados, manifesto


def buscar(texto: str, top_k: int, vetores: np.ndarray, metadados: list[dict],
           gerador: GeradorEmbeddings) -> list[dict]:
    """Compara a consulta com todos os vetores e devolve os k mais próximos."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("Informe um texto com conteúdo para buscar.")
    if type(top_k) is not int or not 1 <= top_k <= len(metadados):
        raise ValueError(f"top_k deve ser um inteiro de 1 a {len(metadados)}.")
    consulta = np.asarray(gerador.gerar([texto.strip()]), dtype="float32")
    if consulta.shape != (1, vetores.shape[1]) or not np.isfinite(consulta).all():
        raise ValueError("O vetor da consulta é inválido ou incompatível com o índice.")
    pontuacoes = cosine_similarity(consulta, vetores)[0]
    ordem = sorted(range(len(metadados)), key=lambda i: (-float(pontuacoes[i]), metadados[i]["id"]))
    return [
        {**metadados[indice], "pontuacao": min(max(float(pontuacoes[indice]), -1.0), 1.0)}
        for indice in ordem[:top_k]
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indice", type=Path, default=INDICE_PADRAO)
    parser.add_argument("--modelo", default="baseline-hashing")
    parser.add_argument("--texto", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    argumentos = parser.parse_args()
    try:
        gerador = criar_gerador(argumentos.modelo)
        vetores, metadados, manifesto = carregar_indice(argumentos.indice, gerador.nome)
        candidatos = buscar(argumentos.texto, argumentos.top_k, vetores, metadados, gerador)
        resposta = {
            "modo": manifesto.get("uso"),
            "modelo": manifesto["modelo"],
            "aviso": manifesto.get("aviso"),
            "top_k": argumentos.top_k,
            "candidatos": candidatos,
        }
        print(json.dumps(resposta, ensure_ascii=False, indent=2))
    except ValueError as erro:
        parser.exit(1, f"Não foi possível buscar: {erro}\n")


if __name__ == "__main__":
    main()
