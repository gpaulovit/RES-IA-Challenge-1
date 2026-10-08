"""Organiza o corpus inspecionado sem corrigir ou excluir registros."""

import csv
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path

from checagens.inspecao import COLUNAS, FONTE, ORIGINAL, SHA256, URL, VERSAO

CORPUS = Path("data/processados/factpolcheckbr/corpus.json")
RELATORIO = Path("data/relatorios/organizacao-factpolcheckbr.json")
VERSAO_REGRAS = "1"


def _texto(valor: str) -> str | None:
    valor = valor.strip()
    return valor or None


def _data(valor: str) -> dict:
    bruto = valor.strip()
    if not bruto:
        return {"original": None, "padronizada": None, "status": "ausente", "possibilidades": []}

    possibilidades = []
    for formato, nome in (("%m/%d/%Y", "mes_dia_ano"), ("%d/%m/%Y", "dia_mes_ano")):
        try:
            interpretada = datetime.strptime(bruto, formato).date().isoformat()
        except ValueError:
            continue
        if interpretada not in [item["data"] for item in possibilidades]:
            possibilidades.append({"formato": nome, "data": interpretada})

    mdy = next((item["data"] for item in possibilidades if item["formato"] == "mes_dia_ano"), None)
    if not possibilidades:
        status, padronizada = "invalida", None
    elif len(possibilidades) > 1:
        status, padronizada = "ambigua", None
    elif mdy:
        status, padronizada = "padronizada", mdy
    else:
        status, padronizada = "fora_formato_fonte", None
    return {"original": bruto, "padronizada": padronizada,
            "status": status, "possibilidades": possibilidades}


def organizar(conteudo: bytes, origem: dict) -> tuple[dict, dict]:
    """Converte o CSV validado em corpus e relatório determinísticos."""
    sha = hashlib.sha256(conteudo).hexdigest()
    if sha != SHA256:
        raise ValueError("O original foi alterado ou pertence a outra versão.")
    origem_esperada = {"fonte": FONTE, "versao": VERSAO, "url_download": URL,
                       "sha256": SHA256, "tamanho_bytes": len(conteudo),
                       "licenca": "CC BY-NC-SA 4.0"}
    divergencias = [campo for campo, esperado in origem_esperada.items()
                    if origem.get(campo) != esperado]
    if divergencias:
        raise ValueError("Os metadados de origem não correspondem ao CSV esperado.")

    leitor = csv.reader(io.StringIO(conteudo.decode("utf-8-sig"), newline=""), strict=True)
    cabecalho = next(leitor, [])
    if cabecalho != COLUNAS:
        raise ValueError(f"Colunas diferentes das esperadas: {cabecalho}")
    linhas = list(leitor)
    if not linhas:
        raise ValueError("O CSV não contém registros.")
    irregulares = [numero for numero, linha in enumerate(linhas, 1) if len(linha) != len(COLUNAS)]
    if irregulares:
        raise ValueError(f"Registros com quantidade incorreta de campos: {irregulares}")

    grupos = defaultdict(list)
    for numero, linha in enumerate(linhas, 1):
        grupos[tuple(linha)].append(numero)
    duplicados = {numero: grupo for grupo in grupos.values() if len(grupo) > 1 for numero in grupo}

    registros = []
    campos_ausentes = defaultdict(list)
    originais_ausentes = {campo: [] for campo in COLUNAS}
    datas = Counter()
    pendentes = []
    for numero, valores in enumerate(linhas, 1):
        original = dict(zip(COLUNAS, valores, strict=True))
        for campo, valor in original.items():
            if not valor.strip():
                originais_ausentes[campo].append(numero)
        data = _data(original["Data da checagem"])
        organizado = {
            "titulo_checagem": _texto(original["Título da checagem"]),
            "texto_verificacao": _texto(original["texto"]),
            "veredito_original": _texto(original["Natureza da notícia"]),
            "data": data,
            "agencia": _texto(original["Agência"]),
            "link": _texto(original["Link"]),
            "candidatos_favorecidos": _texto(original["Candidato(s) favorecidos(s) pela notícia falsa"]),
        }
        ausentes = [campo for campo, valor in organizado.items()
                    if campo != "data" and valor is None]
        for campo in ausentes:
            campos_ausentes[campo].append(numero)
        datas[data["status"]] += 1
        razoes = [f"campo_ausente:{campo}" for campo in ausentes]
        if data["status"] != "padronizada":
            razoes.append(f"data:{data['status']}")
        if numero in duplicados:
            razoes.append("duplicacao_exata")
        if razoes:
            pendentes.append({"registro": numero, "razoes": razoes})
        registros.append({
            "id": f"{VERSAO}:{numero:04d}",
            "numero_origem": numero,
            "original": original,
            "organizado": organizado,
            "qualidade": {"pendente": bool(razoes), "razoes": razoes,
                          "grupo_duplicado": duplicados.get(numero)},
        })

    metadados = {
        "fonte": FONTE, "arquivo_fonte": "dados/com_texto.csv",
        "versao_fonte": VERSAO, "sha256_fonte": SHA256,
        "licenca": origem.get("licenca"), "versao_regras": VERSAO_REGRAS,
        "aviso": "Título da checagem não foi tratado como alegação original.",
    }
    corpus = {"metadados": metadados, "registros": registros}
    relatorio = {
        "metadados": metadados,
        "total_registros": len(registros),
        "contagem_esperada": 1882,
        "contagem_confere": len(registros) == 1882,
        "campos_originais_ausentes": {
            campo: {"quantidade": len(numeros), "registros": numeros}
            for campo, numeros in originais_ausentes.items()
        },
        "campos_organizados_ausentes": {
            campo: {"quantidade": len(numeros), "registros": numeros}
            for campo, numeros in sorted(campos_ausentes.items())
        },
        "status_datas": dict(sorted(datas.items())),
        "registros_com_pendencias": len(pendentes),
        "pendencias": pendentes,
        "grupos_duplicados": [grupo for grupo in grupos.values() if len(grupo) > 1],
        "agencias": dict(sorted(Counter(
            registro["organizado"]["agencia"] for registro in registros
            if registro["organizado"]["agencia"] is not None
        ).items())),
        "prontidao_analise": {
            "status": "pendente_validacao_dados" if pendentes else "pronto",
            "motivo": "Título, datas pendentes e campos ausentes precisam de validação da frente de Dados."
                      if pendentes else None,
        },
    }
    return corpus, relatorio


def main() -> None:
    try:
        conteudo = ORIGINAL.read_bytes()
        origem_path = ORIGINAL.with_name("origem.json")
        origem = json.loads(origem_path.read_text(encoding="utf-8"))
        corpus, relatorio = organizar(conteudo, origem)
        CORPUS.parent.mkdir(parents=True, exist_ok=True)
        RELATORIO.parent.mkdir(parents=True, exist_ok=True)
        opcoes = {"ensure_ascii": False, "indent": 2, "sort_keys": True}
        corpus_temporario = CORPUS.with_suffix(".json.tmp")
        relatorio_temporario = RELATORIO.with_suffix(".json.tmp")
        corpus_temporario.write_text(json.dumps(corpus, **opcoes) + "\n", encoding="utf-8")
        relatorio_temporario.write_text(json.dumps(relatorio, **opcoes) + "\n", encoding="utf-8")
        corpus_temporario.replace(CORPUS)
        relatorio_temporario.replace(RELATORIO)
        print(f"Organização concluída: {relatorio['total_registros']} registros preservados.")
        print(f"Corpus: {CORPUS}\nRelatório: {RELATORIO}")
        print(f"Registros com pendências: {relatorio['registros_com_pendencias']}")
    except (OSError, ValueError, csv.Error, json.JSONDecodeError) as erro:
        raise SystemExit(f"Não foi possível organizar o corpus: {erro}") from erro


if __name__ == "__main__":
    main()
