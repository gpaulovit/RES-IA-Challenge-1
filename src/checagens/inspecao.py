"""Inspeciona a base original sem corrigir, excluir ou indexar registros."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess

VERSAO = "e4b4feafce9b83789a517f649abb39ad4645f1b3"
FONTE = "https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr"
URL = f"https://raw.githubusercontent.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr/{VERSAO}/dados/com_texto.csv"
SHA256 = "7f0c9443dcf2d7fb15ef3320eb1bfeb8b0d67f4689a13757b33809f200e84681"
COLUNAS = ["Link", "Título da checagem", "Data da checagem", "Natureza da notícia",
           "Candidato(s) favorecidos(s) pela notícia falsa", "Agência", "texto"]
ORIGINAL = Path("data/originais/factpolcheckbr/com_texto.csv")


def grupos_repetidos(valores):
    grupos = defaultdict(list)
    for numero, valor in enumerate(valores, 1):
        if isinstance(valor, str) and not valor.strip():
            continue
        grupos[valor].append(numero)
    return [numeros for numeros in grupos.values() if len(numeros) > 1]


def interpretar_data(valor, formato):
    try:
        return datetime.strptime(valor.strip(), formato).date()
    except ValueError:
        return None


def inspecionar(conteudo: bytes) -> dict:
    leitor = csv.reader(io.StringIO(conteudo.decode("utf-8-sig"), newline=""), strict=True)
    cabecalho = next(leitor, [])
    if cabecalho != COLUNAS:
        raise ValueError(f"Colunas diferentes das esperadas: {cabecalho}")
    registros = list(leitor)
    if not registros:
        raise ValueError("O CSV não contém registros.")
    irregulares = [i for i, linha in enumerate(registros, 1) if len(linha) != len(COLUNAS)]
    if irregulares:
        raise ValueError(f"Registros com quantidade incorreta de campos: {irregulares}")
    linhas = [dict(zip(COLUNAS, linha, strict=True)) for linha in registros]
    vazios = {campo: [i for i, linha in enumerate(linhas, 1) if not linha[campo].strip()]
              for campo in COLUNAS}
    repetidos = {campo: grupos_repetidos([linha[campo] for linha in linhas])
                 for campo in ["Link", "Título da checagem", "texto"]}
    repetidos["registro_completo"] = grupos_repetidos([tuple(linha) for linha in registros])
    fora_padrao, ambiguas, invalidas, datas = [], [], [], []
    for numero, linha in enumerate(linhas, 1):
        valor = linha["Data da checagem"]
        mdy = interpretar_data(valor, "%m/%d/%Y")
        dmy = interpretar_data(valor, "%d/%m/%Y")
        if not mdy:
            fora_padrao.append({"registro": numero, "valor": valor,
                                "valida_com_dia_primeiro": dmy is not None})
        if not mdy and not dmy:
            invalidas.append(numero)
        if mdy and dmy and mdy != dmy:
            ambiguas.append(numero)
        if mdy:
            datas.append(mdy.isoformat())
    return {
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "total_registros": len(linhas), "total_informado_fonte": 1882,
        "diferenca_contagem": len(linhas) - 1882, "colunas": cabecalho,
        "numeracao": "Registros a partir de 1, sem cabeçalho; não são linhas físicas do arquivo.",
        "campos_vazios": {campo: {"quantidade": len(ids), "registros": ids}
                          for campo, ids in vazios.items()},
        "agencias": dict(sorted(Counter(linha["Agência"] for linha in linhas).items())),
        "duplicacoes_exatas": {
            campo: {"grupos": grupos, "quantidade_grupos": len(grupos),
                    "ocorrencias_excedentes": sum(len(g) - 1 for g in grupos)}
            for campo, grupos in repetidos.items()
        },
        "datas": {
            "formato_informado_fonte": "mês/dia/ano",
            "fora_do_formato_informado": fora_padrao,
            "invalidas_nos_dois_formatos": invalidas,
            "ambiguas_entre_formatos": ambiguas,
            "intervalo_sob_formato_informado": [min(datas), max(datas)] if datas else [],
            "aviso": "Intervalo provisório: não resolve formatos mistos nem confirma cobertura temporal.",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baixar", action="store_true", help="Baixar a versão fixa oficial, se ausente.")
    argumentos = parser.parse_args()
    try:
        if argumentos.baixar and not ORIGINAL.exists():
            ORIGINAL.parent.mkdir(parents=True, exist_ok=True)
            temporario = ORIGINAL.with_suffix(".download")
            try:
                subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error",
                                "--max-time", "120", URL, "-o", str(temporario)], check=True)
                if hashlib.sha256(temporario.read_bytes()).hexdigest() != SHA256:
                    raise ValueError("O arquivo baixado não corresponde à versão esperada.")
                temporario.replace(ORIGINAL)
            finally:
                temporario.unlink(missing_ok=True)
        conteudo = ORIGINAL.read_bytes()
        if hashlib.sha256(conteudo).hexdigest() != SHA256:
            raise ValueError("O original foi alterado ou pertence a outra versão. Nenhum arquivo foi sobrescrito.")
        relatorio = inspecionar(conteudo)
        manifesto = ORIGINAL.with_name("origem.json")
        if not manifesto.exists():
            origem = {
                "fonte": FONTE, "versao": VERSAO, "url_download": URL,
                "sha256": SHA256, "tamanho_bytes": len(conteudo),
                "obtido_em_utc": datetime.fromtimestamp(ORIGINAL.stat().st_mtime, timezone.utc).isoformat(),
                "criterio_data": "Data de gravação da cópia local no download; não é a data das checagens.",
                "atribuicao": "Interfaces — Núcleo de Estudos Sociopolíticos dos Algoritmos e da Inteligência Artificial",
                "licenca": "CC BY-NC-SA 4.0",
                "licenca_fonte": f"{FONTE}/blob/{VERSAO}/LICENSE.md",
            }
            manifesto.write_text(json.dumps(origem, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        destino = Path("data/relatorios/inspecao-factpolcheckbr.json")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Inspeção concluída: {relatorio['total_registros']} registros. Original preservado.")
        print(f"Origem: {manifesto}\nRelatório detalhado: {destino}")
        for campo, item in relatorio["campos_vazios"].items():
            print(f"  {campo}: {item['quantidade']} vazios")
        print("A inspeção não corrige dados nem conclui a tarefa 1.1.")
    except (OSError, ValueError, csv.Error, subprocess.CalledProcessError) as erro:
        parser.exit(1, f"Não foi possível inspecionar: {erro}\n")


if __name__ == "__main__":
    main()
