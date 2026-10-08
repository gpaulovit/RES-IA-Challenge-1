"""Leitura e conferência dos exemplos antes de iniciar a busca."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class Checagem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    alegacao: str
    checagem: str
    agencia: str
    veredito_original: str

    @field_validator("id", "alegacao", "checagem", "agencia", "veredito_original")
    @classmethod
    def conferir_texto(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("O campo deve conter texto.")
        return valor.strip()


def carregar_exemplos(caminho: Path) -> list[Checagem]:
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    except OSError as erro:
        raise ValueError(f"Não foi possível ler o arquivo de exemplos: {caminho}") from erro
    except (json.JSONDecodeError, UnicodeError) as erro:
        raise ValueError("O arquivo de exemplos deve ser um JSON válido em UTF-8.") from erro

    if not isinstance(conteudo, list) or not conteudo:
        raise ValueError("A base deve ser uma lista com pelo menos uma checagem fictícia.")

    exemplos = []
    ids = set()
    for posicao, registro in enumerate(conteudo, start=1):
        try:
            exemplo = Checagem.model_validate(registro)
        except ValidationError as erro:
            campos = ", ".join(".".join(map(str, item["loc"])) or "registro" for item in erro.errors())
            raise ValueError(
                f"Exemplo {posicao} inválido. Confira os campos: {campos}. "
                "Use apenas os cinco campos previstos, todos com texto não vazio."
            ) from erro
        if exemplo.id in ids:
            raise ValueError(f"Identificador repetido na base: {exemplo.id}")
        ids.add(exemplo.id)
        exemplos.append(exemplo)
    return exemplos
