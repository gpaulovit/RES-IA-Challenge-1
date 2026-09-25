"""Gera vetores e metadados rastreáveis a partir do corpus organizado."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
from typing import Protocol

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

CORPUS_PADRAO = Path("data/processados/factpolcheckbr/corpus.json")
SAIDA_PADRAO = Path("data/indices/experimental")
VERSAO_PIPELINE = "1"


class GeradorEmbeddings(Protocol):
    """Contrato mínimo que qualquer modelo candidato precisa cumprir."""

    @property
    def nome(self) -> str: ...

    def gerar(self, textos: list[str]) -> np.ndarray: ...


class BaselineHashing:
    """Modelo lexical pequeno usado apenas para conferir o encanamento."""

    nome = "baseline-hashing-256"

    def __init__(self) -> None:
        self._vetorizador = HashingVectorizer(
            n_features=256, alternate_sign=False, norm="l2", lowercase=True
        )

    def gerar(self, textos: list[str]) -> np.ndarray:
        return self._vetorizador.transform(textos).toarray().astype("float32")


class SentenceTransformers:
    """Adaptador opcional para modelos compatíveis com sentence-transformers."""

    def __init__(self, identificador: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as erro:
            raise ValueError(
                "Instale as dependências opcionais com: pip install -e '.[embeddings]'"
            ) from erro
        self._identificador = identificador
        self._modelo = SentenceTransformer(identificador)

    @property
    def nome(self) -> str:
        return f"sentence-transformers:{self._identificador}"

    def gerar(self, textos: list[str]) -> np.ndarray:
        vetores = self._modelo.encode(
            textos, convert_to_numpy=True, normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vetores, dtype="float32")


def carregar_corpus(caminho: Path) -> dict:
    try:
        corpus = json.loads(caminho.read_text(encoding="utf-8"))
    except OSError as erro:
        raise ValueError(f"Não foi possível ler o corpus: {caminho}") from erro
    except (json.JSONDecodeError, UnicodeError) as erro:
        raise ValueError("O corpus deve ser um JSON válido em UTF-8.") from erro
    if not isinstance(corpus, dict) or not isinstance(corpus.get("registros"), list):
        raise ValueError("O corpus deve conter uma lista chamada 'registros'.")
    if not corpus["registros"]:
        raise ValueError("O corpus não contém registros.")
    return corpus


def preparar_itens(corpus: dict, limite: int | None = None) -> tuple[list[str], list[dict]]:
    """Separa o texto experimental e os metadados que acompanham cada vetor."""
    registros = corpus["registros"][:limite] if limite else corpus["registros"]
    textos, metadados = [], []
    ids = set()
    for posicao, registro in enumerate(registros, 1):
        try:
            identificador = registro["id"]
            organizado = registro["organizado"]
            titulo = organizado["titulo_checagem"]
        except (KeyError, TypeError) as erro:
            raise ValueError(f"Registro {posicao} não segue o formato organizado.") from erro
        if not isinstance(identificador, str) or not identificador or identificador in ids:
            raise ValueError(f"Registro {posicao} tem id ausente ou repetido.")
        if not isinstance(titulo, str) or not titulo.strip():
            raise ValueError(f"Registro {posicao} não tem título para o teste experimental.")
        ids.add(identificador)
        textos.append(titulo.strip())
        data = organizado.get("data") or {}
        metadados.append({
            "id": identificador,
            "linha_vetor": len(metadados),
            "campo_texto": "titulo_checagem",
            "texto_indexado": titulo.strip(),
            "veredito_original": organizado.get("veredito_original"),
            "agencia": organizado.get("agencia"),
            "data_original": data.get("original"),
            "data_padronizada": data.get("padronizada"),
            "status_data": data.get("status"),
        })
    return textos, metadados


def construir_indice(corpus: dict, gerador: GeradorEmbeddings,
                     limite: int | None = None) -> tuple[np.ndarray, list[dict], dict]:
    textos, metadados = preparar_itens(corpus, limite)
    vetores = np.asarray(gerador.gerar(textos), dtype="float32")
    if vetores.ndim != 2 or vetores.shape[0] != len(metadados) or vetores.shape[1] < 1:
        raise ValueError("O modelo deve devolver uma matriz 2D com um vetor por registro.")
    if not np.isfinite(vetores).all():
        raise ValueError("O modelo devolveu vetores com valores inválidos.")
    manifesto = {
        "versao_pipeline": VERSAO_PIPELINE,
        "modelo": gerador.nome,
        "quantidade_vetores": int(vetores.shape[0]),
        "dimensoes": int(vetores.shape[1]),
        "tipo_numerico": str(vetores.dtype),
        "campo_texto": "titulo_checagem",
        "uso": "experimental_gate",
        "apto_produto": False,
        "aviso": "O título é usado somente para validar o pipeline; a frente de Dados ainda deve confirmar a alegação.",
        "versao_fonte": corpus.get("metadados", {}).get("versao_fonte"),
        "sha256_fonte": corpus.get("metadados", {}).get("sha256_fonte"),
        "python": platform.python_version(),
    }
    return vetores, metadados, manifesto


def salvar_indice(saida: Path, vetores: np.ndarray, metadados: list[dict],
                  manifesto: dict) -> dict:
    """Salva três arquivos alinhados e inclui hashes para futura conferência."""
    saida.mkdir(parents=True, exist_ok=True)
    vetores_tmp = saida / "vetores.npy.tmp"
    metadados_tmp = saida / "metadados.json.tmp"
    manifesto_tmp = saida / "manifesto.json.tmp"
    with vetores_tmp.open("wb") as arquivo:
        np.save(arquivo, vetores, allow_pickle=False)
    metadados_tmp.write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    hashes = {
        "vetores.npy": hashlib.sha256(vetores_tmp.read_bytes()).hexdigest(),
        "metadados.json": hashlib.sha256(metadados_tmp.read_bytes()).hexdigest(),
    }
    manifesto_final = {**manifesto, "arquivos": hashes}
    manifesto_tmp.write_text(
        json.dumps(manifesto_final, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    vetores_tmp.replace(saida / "vetores.npy")
    metadados_tmp.replace(saida / "metadados.json")
    manifesto_tmp.replace(saida / "manifesto.json")
    return manifesto_final


def criar_gerador(nome: str) -> GeradorEmbeddings:
    if nome == "baseline-hashing":
        return BaselineHashing()
    prefixo = "sentence-transformers:"
    if nome.startswith(prefixo) and nome[len(prefixo):]:
        return SentenceTransformers(nome[len(prefixo):])
    raise ValueError(
        "Modelo desconhecido. Use 'baseline-hashing' ou "
        "'sentence-transformers:NOME_DO_MODELO'."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--modelo", default="baseline-hashing")
    parser.add_argument("--limite", type=int)
    argumentos = parser.parse_args()
    try:
        if argumentos.limite is not None and argumentos.limite < 1:
            raise ValueError("O limite deve ser um inteiro maior que zero.")
        corpus = carregar_corpus(argumentos.corpus)
        gerador = criar_gerador(argumentos.modelo)
        vetores, metadados, manifesto = construir_indice(corpus, gerador, argumentos.limite)
        manifesto = salvar_indice(argumentos.saida, vetores, metadados, manifesto)
        print(f"Pipeline concluído: {manifesto['quantidade_vetores']} vetores de "
              f"{manifesto['dimensoes']} dimensões.")
        print(f"Modelo: {manifesto['modelo']}\nSaída: {argumentos.saida}")
        print("Uso experimental: ainda depende da validação de Dados e do gate de Modelos de IA.")
    except ValueError as erro:
        parser.exit(1, f"Não foi possível gerar os embeddings: {erro}\n")


if __name__ == "__main__":
    main()
