#!/usr/bin/env python3
"""Promoção de versão do modelo checagens-camada2 para alias 'producao' no MLflow (Azure ML).

Atua como trava humana auditável após conferir o critério de go/no-go pré-registrado.

Uso:
    python scripts/promover_modelo.py [--versao 1] [--tracking-uri ...] [--force]
"""
import argparse
import os
import sys

from mlflow import MlflowClient

MODELO_NOME = "checagens-camada2"
ALIAS_PRODUCAO = "producao"


def promover(versao: int | str | None = None, tracking_uri: str | None = None, force: bool = False) -> None:
    uri = tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
    if not uri:
        print("Erro: MLFLOW_TRACKING_URI não definida. Forneça via ambiente ou --tracking-uri.", file=sys.stderr)
        sys.exit(1)

    import mlflow
    mlflow.set_tracking_uri(uri)
    client = MlflowClient(tracking_uri=uri)

    # Se a versão não foi passada, busca a última versão registrada
    if versao is None:
        versoes = client.search_model_versions(f"name='{MODELO_NOME}'")
        if not versoes:
            print(f"Erro: Nenhuma versão encontrada para o modelo '{MODELO_NOME}'.", file=sys.stderr)
            sys.exit(1)
        # Ordena pela versão mais recente
        versao_obj = max(versoes, key=lambda v: int(v.version))
        versao = versao_obj.version
        run_id = versao_obj.run_id
    else:
        versao = str(versao)
        versao_obj = client.get_model_version(MODELO_NOME, versao)
        run_id = versao_obj.run_id

    # Auditoria de go/no-go na run
    run = client.get_run(run_id)
    metricas = run.data.metrics
    tags = run.data.tags
    decisao = tags.get("decisao")
    go_no_go = metricas.get("go_no_go")

    print(f"Auditoria da Versão {versao} (Run ID: {run_id}):")
    print(f"  - F1 Macro: {metricas.get('f1_macro', 'N/D')}")
    print(f"  - Falso Alarme: {metricas.get('falso_alarme', 'N/D')}")
    print(f"  - Decisão: {decisao or 'N/D'} (métrica go_no_go: {go_no_go})")
    print(f"  - Git Commit: {tags.get('git_commit', 'N/D')}")
    print(f"  - Hash Base: {tags.get('hash_base', 'N/D')}")

    if not force and decisao == "no-go":
        print("ERRO: Modelo com status 'no-go'. Não é permitido promover para produção sem --force.", file=sys.stderr)
        sys.exit(1)

    client.set_registered_model_alias(MODELO_NOME, ALIAS_PRODUCAO, str(versao))
    print(f"Sucesso: Modelo '{MODELO_NOME}' versão {versao} promovido com alias '{ALIAS_PRODUCAO}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--versao", type=str, default=None, help="Número da versão a ser promovida (padrão: última)")
    parser.add_argument("--tracking-uri", type=str, default=None, help="URI do MLflow Tracking (Azure ML)")
    parser.add_argument("--force", action="store_true", help="Permite promover mesmo com status no-go")
    args = parser.parse_args()
    promover(args.versao, args.tracking_uri, args.force)
