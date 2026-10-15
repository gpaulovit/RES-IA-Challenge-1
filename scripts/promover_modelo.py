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

    # Auditoria de go/no-go na run conforme protocolo pré-registrado (docs/relatorio-camada2.md)
    run = client.get_run(run_id)
    metricas = run.data.metrics
    tags = run.data.tags
    decisao = tags.get("decisao")
    go_no_go = metricas.get("go_no_go")
    f1_macro = metricas.get("f1_macro")
    falso_alarme = metricas.get("falso_alarme")

    print(f"Auditoria da Versão {versao} (Run ID: {run_id}):")
    print(f"  - F1 Macro: {f1_macro if f1_macro is not None else 'N/D'} (Meta RNF-02: >= 0.75)")
    print(f"  - Falso Alarme: {falso_alarme if falso_alarme is not None else 'N/D'} (Teto RNF-03: <= 15.0%)")
    print(f"  - Decisão: {decisao or 'N/D'} (métrica go_no_go: {go_no_go})")
    print(f"  - Git Commit: {tags.get('git_commit', 'N/D')}")
    print(f"  - Hash Base: {tags.get('hash_base', 'N/D')}")

    motivos_rejeicao = []
    if decisao == "no-go":
        motivos_rejeicao.append("Decisão formal registrada como 'no-go'")
    if f1_macro is not None and f1_macro < 0.75:
        motivos_rejeicao.append(f"F1 macro ({f1_macro:.3f}) < 0.75 (RNF-02)")
    if falso_alarme is not None and falso_alarme > 0.15:
        motivos_rejeicao.append(f"Falso alarme ({falso_alarme:.1%}) > 15.0% (RNF-03)")

    if not force and motivos_rejeicao:
        print(f"ERRO: Modelo versão {versao} reprovado no protocolo de Go/No-Go pela RN-04:", file=sys.stderr)
        for motivo in motivos_rejeicao:
            print(f"  - {motivo}", file=sys.stderr)
        print("Promoção para @producao abortada. O bot operará apenas com a Camada 1 factual.", file=sys.stderr)
        sys.exit(1)

    alias_ok = False
    try:
        client.set_registered_model_alias(MODELO_NOME, ALIAS_PRODUCAO, str(versao))
        alias_ok = True
    except Exception as e:
        print(f"Aviso: Servidor MLflow não suporta alias ({e}). Configurando estágio 'Production' e tags.")

    try:
        client.transition_model_version_stage(
            name=MODELO_NOME,
            version=str(versao),
            stage="Production",
            archive_existing_versions=True,
        )
    except Exception as e:
        print(f"Aviso: Transição de estágio para Production: {e}")

    try:
        client.set_model_version_tag(MODELO_NOME, str(versao), "alias", ALIAS_PRODUCAO)
        client.set_model_version_tag(MODELO_NOME, str(versao), "stage", "Production")
    except Exception:
        pass

    print(f"Sucesso: Modelo '{MODELO_NOME}' versão {versao} promovido para produção (alias: {alias_ok}, stage: Production).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--versao", type=str, default=None, help="Número da versão a ser promovida (padrão: última)")
    parser.add_argument("--tracking-uri", type=str, default=None, help="URI do MLflow Tracking (Azure ML)")
    parser.add_argument("--force", action="store_true", help="Permite promover mesmo com status no-go")
    args = parser.parse_args()
    promover(args.versao, args.tracking_uri, args.force)
