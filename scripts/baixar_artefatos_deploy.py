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
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if tracking_uri:
        import mlflow
        from mlflow.artifacts import download_artifacts

        mlflow.set_tracking_uri(tracking_uri)
        try:
            caminho_artefato = download_artifacts(artifact_uri="models:/checagens-camada2@producao")
            destino = RAIZ / "models"
            destino.mkdir(parents=True, exist_ok=True)

            origem_joblib = Path(caminho_artefato) / "artifacts" / "modelo_joblib"
            if origem_joblib.exists():
                shutil.copy2(origem_joblib, destino / "classificador.joblib")
                print(f"Modelo classificador.joblib extraído para {destino / 'classificador.joblib'}")
            elif (Path(caminho_artefato) / "classificador.joblib").exists():
                shutil.copy2(Path(caminho_artefato) / "classificador.joblib", destino / "classificador.joblib")
                print(f"Modelo classificador.joblib copiado para {destino / 'classificador.joblib'}")
            else:
                print(f"Artefatos baixados em {caminho_artefato}")
        except Exception as e:
            print(f"Erro ao baixar modelo via MLflow: {e}", file=sys.stderr)
    else:
        print("Aviso: MLFLOW_TRACKING_URI não definida. Pulando download do MLflow.", file=sys.stderr)


if __name__ == "__main__":
    baixar_artefatos()
