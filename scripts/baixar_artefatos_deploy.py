#!/usr/bin/env python3
"""Baixa os artefatos de deploy (índice da camada 1 via DVC e modelo da camada 2 via MLflow @producao).

Garante que o container Docker saia autocontido, sem necessidade de credenciais em runtime.

Uso:
    python scripts/baixar_artefatos_deploy.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def baixar_artefatos() -> None:
    print("1. Baixando índice da camada 1 via DVC (data/indices/camada1)...")
    res_dvc = subprocess.run(["python", "-m", "dvc", "pull", "data/indices/camada1"], cwd=str(RAIZ))
    if res_dvc.returncode != 0:
        print("Aviso: 'dvc pull data/indices/camada1' retornou código diferente de zero. Verifique credenciais ou cache.", file=sys.stderr)

    manifesto = RAIZ / "data" / "indices" / "camada1" / "manifesto.json"
    if not manifesto.exists():
        print("Aviso: índice ausente após dvc pull. Tentando reproduzir com DVC (dvc repro indice)...")
        res_repro = subprocess.run(["python", "-m", "dvc", "repro", "indice"], cwd=str(RAIZ))
        if res_repro.returncode == 0 and os.getenv("AZURE_STORAGE_CONNECTION_STRING"):
            print("Índice reconstruído com sucesso! Enviando para o remote DVC na Azure (dvc push)...")
            subprocess.run(["python", "-m", "dvc", "push", "data/indices/camada1"], cwd=str(RAIZ))

    if not manifesto.exists():
        raise RuntimeError("ERRO CRÍTICO DE DEPLOY: O índice da Camada 1 não foi encontrado nem pôde ser construído. Abortando deploy para evitar container vazio.")

    print("2. Baixando modelo da camada 2 via MLflow (models:/checagens-camada2@producao)...")
    tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        "azureml://eastus.api.azureml.ms/mlflow/v1.0/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/providers/Microsoft.MachineLearningServices/workspaces/mlw-res-ia",
    )
    if tracking_uri:
        import mlflow
        from mlflow.artifacts import download_artifacts

        mlflow.set_tracking_uri(tracking_uri)
        caminho_artefato = None
        sucesso = False
        for uri_modelo in [
            "models:/checagens-camada2@producao",
            "models:/checagens-camada2/Production",
        ]:
            try:
                print(f"Tentando baixar artefato homologado via URI '{uri_modelo}'...")
                caminho_artefato = download_artifacts(artifact_uri=uri_modelo)
                sucesso = True
                break
            except Exception as e:
                print(f"Aviso: modelo homologado não encontrado em '{uri_modelo}': {e}")

        if sucesso and caminho_artefato:
            destino = RAIZ / "models"
            destino.mkdir(parents=True, exist_ok=True)

            art_dir = Path(caminho_artefato) / "artifacts"
            if (art_dir / "classificador.joblib").exists():
                shutil.copy2(art_dir / "classificador.joblib", destino / "classificador.joblib")
                print(f"Modelo homologado classificador.joblib extraído para {destino / 'classificador.joblib'}")
            elif (art_dir / "modelo_joblib").exists():
                shutil.copy2(art_dir / "modelo_joblib", destino / "classificador.joblib")
                print(f"Modelo homologado classificador.joblib extraído para {destino / 'classificador.joblib'}")
            elif (Path(caminho_artefato) / "classificador.joblib").exists():
                shutil.copy2(Path(caminho_artefato) / "classificador.joblib", destino / "classificador.joblib")
                print(f"Modelo homologado classificador.joblib copiado para {destino / 'classificador.joblib'}")
            else:
                print(f"Artefatos baixados em {caminho_artefato}")
        else:
            print("Informação: Nenhum modelo da Camada 2 com alias '@producao' foi encontrado no MLflow.")
            print("Conforme a RN-04, com a decisão de NO-GO a Camada 2 não é promovida e não deve ser empacotada.")
            print("O bot operará exclusivamente com a Camada 1 factual em produção (CAMADA2_LIGADA=0).")


if __name__ == "__main__":
    baixar_artefatos()
