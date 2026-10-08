"""Modelos de embeddings candidatos e geração de embeddings com cache em disco.

Um lugar só para nome, revisão e prefixo de cada modelo: os notebooks e o gate importam daqui.
"""
import hashlib
import time
from functools import cache
from pathlib import Path

import numpy as np

CACHE = Path(__file__).parent / "data" / "emb"

# família (exigida pela issue #8), id, revisão fixada, prefixo (só o E5 usa; tarefa simétrica: "query: " nos dois lados)
MODELOS = [
    ("multilíngue", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "e8f8c211226b894fcb81acc59f3b34ba3efd5f42", ""),
    ("multilíngue", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2", "4328cf26390c98c5e3c738b4460a05b95f4911f5", ""),
    ("multilíngue", "intfloat/multilingual-e5-base", "d128750597153bb5987e10b1c3493a34e5a4502a", "query: "),
    ("multilíngue", "BAAI/bge-m3", "5617a9f61b028005a4858fdac845db406aefb181", ""),
    ("BERTimbau", "neuralmind/bert-base-portuguese-cased", "94d69c95f98f7d5b2a8700c420230ae10def0baa", ""),
    ("BERTimbau", "rufimelo/bert-large-portuguese-cased-sts", "e5c615d0dd46078764b7f58835b95af95f153e95", ""),
]
MINILM = MODELOS[0]   # o modelo dos gates anteriores e da 1ª rodada do gate temporal


@cache
def carregar(nome: str, revisao: str):
    from sentence_transformers import SentenceTransformer
    modelo = SentenceTransformer(nome, revision=revisao)
    modelo.max_seq_length = 128   # alegações são curtas; corta custo dos modelos grandes
    return modelo


def embeddings(textos, nome: str, revisao: str, prefixo: str = "", usar_cache: bool = True) -> tuple[np.ndarray, float]:
    """Embeddings normalizados (cosseno = produto escalar) e segundos por mil textos (NaN se veio do cache).

    O cache vale só para exatamente estes textos, neste modelo e revisão: a chave inclui o hash dos textos.
    """
    textos = [prefixo + t for t in textos]
    assinatura = hashlib.sha256("\n".join(textos).encode()).hexdigest()[:12]
    arquivo = CACHE / f"{nome.replace('/', '__')}__{revisao[:8]}__{assinatura}.npy"
    if usar_cache and arquivo.exists():
        return np.load(arquivo), float("nan")
    t0 = time.perf_counter()
    E = carregar(nome, revisao).encode(textos, normalize_embeddings=True, batch_size=32, show_progress_bar=len(textos) > 1000)
    seg_por_mil = (time.perf_counter() - t0) / max(len(textos), 1) * 1000
    if usar_cache:
        CACHE.mkdir(parents=True, exist_ok=True)
        np.save(arquivo, E)
    return E, seg_por_mil
