"""API local. Execute a partir da raiz do repositório."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from checagens.busca import Buscador, Candidato
from checagens.dados import carregar_exemplos
from checagens.representacao import Representacao, RepresentacaoTfidf

AVISO = (
    "Demonstração com checagens fictícias. A pontuação mede semelhança entre textos, "
    "não a verdade da consulta. O veredito pertence somente ao exemplo de origem."
)


class Consulta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str = Field(description="Texto que você quer comparar com os exemplos fictícios.")
    top_k: Annotated[int, Field(strict=True, ge=1, le=10)] = Field(
        default=3, description="Quantidade máxima de resultados, de 1 a 10."
    )

    @field_validator("texto")
    @classmethod
    def conferir_texto(cls, texto: str) -> str:
        if not texto.strip():
            raise ValueError("Informe um texto com conteúdo para buscar.")
        return texto.strip()


class RespostaBusca(BaseModel):
    modo: Literal["demonstracao"] = "demonstracao"
    metodo: str
    status: Literal["candidatos_encontrados", "nao_encontrada"]
    aviso: str = AVISO
    candidatos: list[Candidato]


class Saude(BaseModel):
    status: Literal["ok"] = "ok"
    modo: Literal["demonstracao"] = "demonstracao"


def criar_app(
    caminho_dados: Path = Path("data/exemplos.json"),
    representacao: Representacao | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def preparar(app: FastAPI):
        app.state.buscador = Buscador(
            carregar_exemplos(caminho_dados),
            representacao if representacao is not None else RepresentacaoTfidf(),
        )
        yield

    app = FastAPI(
        title="Busca em checagens fictícias",
        description=AVISO,
        version="0.1.0",
        lifespan=preparar,
    )

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(request: Request, erro: RequestValidationError):
        detalhes = []
        for item in erro.errors():
            campo = str(item["loc"][-1])
            if campo == "texto":
                mensagem = "Informe texto como uma frase não vazia."
            elif campo == "top_k":
                mensagem = "top_k deve ser um número inteiro de 1 a 10."
            elif item["type"] == "extra_forbidden":
                mensagem = "Campo não reconhecido. Use apenas texto e top_k."
            else:
                mensagem = "Envie um objeto JSON válido com texto e, opcionalmente, top_k."
            detalhes.append({"campo": campo, "mensagem": mensagem})
        return JSONResponse(status_code=422, content={"detail": detalhes})

    @app.get("/health", response_model=Saude, summary="Conferir se o programa está pronto")
    def saude() -> Saude:
        return Saude()

    @app.post("/buscar", response_model=RespostaBusca, summary="Buscar exemplos parecidos")
    def buscar(consulta: Consulta, request: Request) -> RespostaBusca:
        buscador = request.app.state.buscador
        candidatos = buscador.buscar(consulta.texto, consulta.top_k)
        return RespostaBusca(
            metodo=buscador.metodo,
            status="candidatos_encontrados" if candidatos else "nao_encontrada",
            candidatos=candidatos,
        )

    return app


app = criar_app()
