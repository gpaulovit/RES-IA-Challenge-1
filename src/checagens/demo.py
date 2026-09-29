"""Mostra uma consulta fictícia sem precisar iniciar o servidor."""

import json
from pathlib import Path

from checagens.busca import Buscador
from checagens.dados import carregar_exemplos
from checagens.representacao import RepresentacaoTfidf


def main() -> None:
    buscador = Buscador(carregar_exemplos(Path("data/exemplos.json")), RepresentacaoTfidf())
    candidatos = buscador.buscar("transporte gratuito domingos", 1)
    print(json.dumps({"modo": "demonstracao", "metodo": buscador.metodo, "consulta": "transporte gratuito domingos", "candidatos": [item.model_dump() for item in candidatos]}, ensure_ascii=False, indent=2))
    print("Pontuação é semelhança de texto; não verifica a verdade da consulta.")


if __name__ == "__main__":
    main()
