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
            "models:/checagens-camada2/1",
        ]:
            try:
                print(f"Tentando baixar artefato via URI '{uri_modelo}'...")
                caminho_artefato = download_artifacts(artifact_uri=uri_modelo)
                sucesso = True
                break
            except Exception as e:
                print(f"Aviso: falha ao buscar '{uri_modelo}': {e}")

        if sucesso and caminho_artefato:
            destino = RAIZ / "models"
            destino.mkdir(parents=True, exist_ok=True)

            art_dir = Path(caminho_artefato) / "artifacts"
            if (art_dir / "classificador.joblib").exists():
                shutil.copy2(art_dir / "classificador.joblib", destino / "classificador.joblib")
                print(f"Modelo classificador.joblib extraído para {destino / 'classificador.joblib'}")
            elif (art_dir / "modelo_joblib").exists():
                shutil.copy2(art_dir / "modelo_joblib", destino / "classificador.joblib")
                print(f"Modelo classificador.joblib extraído para {destino / 'classificador.joblib'}")
            elif (Path(caminho_artefato) / "classificador.joblib").exists():
                shutil.copy2(Path(caminho_artefato) / "classificador.joblib", destino / "classificador.joblib")
                print(f"Modelo classificador.joblib copiado para {destino / 'classificador.joblib'}")
            else:
                print(f"Artefatos baixados em {caminho_artefato}")
        else:
            print("Aviso: Falha ao baixar via MLflow. Tentando fallback DVC...", file=sys.stderr)

    if not (RAIZ / "models" / "classificador.joblib").exists():
        print("3. Baixando modelo da camada 2 via DVC (models/classificador.joblib)...")
        subprocess.run(["python", "-m", "dvc", "pull", "models/classificador.joblib"], cwd=str(RAIZ))


if __name__ == "__main__":
    baixar_artefatos()
