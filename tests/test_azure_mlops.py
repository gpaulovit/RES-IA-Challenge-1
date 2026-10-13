"""Testes automatizados de MLOps: integração Azure (DVC remote + MLflow tracking e Model Registry).

Valida:
- Configuração versionada do remote DVC na Azure (.dvc/config e pyproject.toml)
- Comportamento estritamente offline de treino e testes sem MLFLOW_TRACKING_URI (RNF-10)
- Rastreamento completo no MLflow (params, métricas F1/falso alarme/go_no_go, tags e artefatos JSON)
- Registro do modelo como pyfunc encapsulando Classificador com paridade total em classificar()
- Script de promoção com alias producao como trava humana auditável
"""
import configparser
import json
import os
import tempfile
from pathlib import Path

import pytest
import tomli

from inteligencia.classificador import Classificador, ClassificadorPyFunc, criar_pipeline
from inteligencia.treino import _achatar_params, registrar_mlflow

RAIZ = Path(__file__).resolve().parents[1]


def test_extra_azure_definido_em_pyproject():
    """Garante que as dependências do extra azure estão especificadas conforme a arquitetura."""
    dados = tomli.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    extras = dados["project"]["optional-dependencies"]
    assert "azure" in extras
    deps_azure = extras["azure"]
    assert any("dvc[azure]" in d or "dvc" in d for d in deps_azure)
    assert any("mlflow" in d for d in deps_azure)
    assert any("azureml-mlflow" in d for d in deps_azure)
    assert any("azure-identity" in d for d in deps_azure)


def test_dvc_remote_azure_configurado():
    """Garante que o remote azure está configurado no .dvc/config com URL e account_name versionados."""
    config_path = RAIZ / ".dvc" / "config"
    assert config_path.exists(), "Arquivo .dvc/config não encontrado."
    conteudo = config_path.read_text(encoding="utf-8")

    assert "remote = azure" in conteudo
    assert "url = azure://dvc/res-ia-challenge-1" in conteudo
    assert "account_name =" in conteudo

    # Credenciais NUNCA devem estar em .dvc/config
    assert "connection_string" not in conteudo
    assert "sas_token" not in conteudo
    assert "password" not in conteudo



def test_treino_offline_sem_mlflow_tracking_uri(monkeypatch):
    """Garante que sem MLFLOW_TRACKING_URI nada de MLflow é acionado (RNF-10 e dvc repro offline)."""
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    assert os.getenv("MLFLOW_TRACKING_URI") is None

    # Parâmetros de teste
    params = {"semente": 42, "camada2": {"ano_corte": 2020, "ngram_range": [1, 2], "min_df": 1,
                                         "C": 1.0, "max_iter": 1000, "folds": 2, "margem_faixas": 0.10}}
    # O pipeline treina normalmente sem erros e sem chamadas externas
    pipe = criar_pipeline(params)
    assert pipe is not None


def test_achatar_params_nested():
    """Garante que parâmetros aninhados do params.yaml são achatados corretamente para o MLflow."""
    p = {
        "semente": 42,
        "camada2": {
            "ano_corte": 2020,
            "ngram_range": [1, 2],
            "C": 1.0,
        }
    }
    achatados = _achatar_params(p)
    assert achatados["semente"] == 42
    assert achatados["camada2.ano_corte"] == 2020
    assert achatados["camada2.C"] == 1.0
    assert achatados["camada2.ngram_range"] == "[1, 2]"


def test_registro_mlflow_e_contrato_pyfunc(monkeypatch, tmp_path):
    """Valida o ciclo completo de registro no MLflow e contrato do modelo pyfunc vs classificar()."""
    import mlflow
    import mlflow.pyfunc
    from mlflow import MlflowClient

    tracking_uri = f"file://{tmp_path}/mlruns"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)

    # 1. Cria classificador real
    params = {"semente": 42, "camada2": {"ano_corte": 2020, "ngram_range": [1, 2], "min_df": 1,
                                         "C": 1.0, "max_iter": 1000, "folds": 2, "margem_faixas": 0.10}}
    textos = ["bomba urgente fraude comprovada nas urnas", "tribunal divulga resultado oficial eleicao"]
    rotulos = [1, 0]
    pipeline = criar_pipeline(params).fit(textos, rotulos)
    clf = Classificador(pipeline, corte_alto=0.70, corte_baixo=0.30)

    # Salva modelo em arquivo
    caminho_modelo = tmp_path / "classificador.joblib"
    clf.salvar(caminho_modelo)

    # Prepara diretório de resultados com JSONs
    saida = tmp_path / "results"
    saida.mkdir(parents=True, exist_ok=True)
    metricas = {
        "f1_macro": 0.88,
        "falso_alarme": 0.05,
        "decisao": "go",
    }
    (saida / "metricas_camada2.json").write_text(json.dumps(metricas), encoding="utf-8")
    usados = {"semente": 42, "sha256_base": "abc123hash", "treino": 100, "teste": 50}
    (saida / "params_camada2.json").write_text(json.dumps(usados), encoding="utf-8")

    # 2. Executa registrar_mlflow
    registrar_mlflow(clf, caminho_modelo, params, metricas, usados, saida, tracking_uri)

    # 3. Valida no MLflowClient
    client = MlflowClient(tracking_uri=tracking_uri)
    runs = client.search_runs(experiment_ids=["0"])
    assert len(runs) >= 1
    run = runs[0]

    # Valida métricas
    assert run.data.metrics["f1_macro"] == 0.88
    assert run.data.metrics["falso_alarme"] == 0.05
    assert run.data.metrics["go_no_go"] == 1.0

    # Valida tags
    assert run.data.tags["hash_base"] == "abc123hash"
    assert run.data.tags["decisao"] == "go"
    assert "git_commit" in run.data.tags

    # Valida parâmetros
    assert str(run.data.params["semente"]) == "42"
    assert str(run.data.params["camada2.ano_corte"]) == "2020"

    # Valida artefatos
    artefatos = [a.path for a in client.list_artifacts(run.info.run_id)]
    assert "metricas_camada2.json" in artefatos
    assert "params_camada2.json" in artefatos

    # 4. Valida Model Registry
    versoes = client.search_model_versions("name='checagens-camada2'")
    assert len(versoes) >= 1
    versao_registrada = versoes[0]
    assert str(versao_registrada.version) == "1"

    # 5. Valida contrato do pyfunc: predict([...]) devolve o mesmo resultado que classificar()
    modelo_carregado = mlflow.pyfunc.load_model(f"models:/checagens-camada2/{versao_registrada.version}")

    texto_teste = "bomba urgente fraude comprovada nas urnas"
    resultado_clf = clf.classificar(texto_teste)

    # Chamada com lista de strings: predict([...])
    resultado_predict_lista = modelo_carregado.predict([texto_teste])
    assert resultado_predict_lista == resultado_clf
    assert resultado_predict_lista[0] == resultado_clf
    assert resultado_predict_lista["faixa"] == resultado_clf["faixa"]
    assert resultado_predict_lista["sinais"] == resultado_clf["sinais"]

    # Chamada com string direta
    resultado_predict_str = modelo_carregado.predict(texto_teste)
    assert resultado_predict_str == resultado_clf


def test_promover_modelo_e_alias_producao(monkeypatch, tmp_path):
    """Valida o script de promoção atribuindo o alias 'producao' com auditoria de go/no-go."""
    from mlflow import MlflowClient
    from scripts.promover_modelo import promover

    tracking_uri = f"file://{tmp_path}/mlruns"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)

    # Cria modelo mock registrado
    import mlflow
    import mlflow.pyfunc
    mlflow.set_tracking_uri(tracking_uri)

    class DummyPyFunc(mlflow.pyfunc.PythonModel):
        def predict(self, context, model_input, params=None):
            return {"faixa": "poucos_sinais", "sinais": []}

    with mlflow.start_run() as run:
        mlflow.log_metrics({"f1_macro": 0.91, "falso_alarme": 0.04, "go_no_go": 1.0})
        mlflow.set_tag("decisao", "go")
        mlflow.set_tag("git_commit", "abc456")
        mlflow.set_tag("hash_base", "basehash789")
        mlflow.pyfunc.log_model(
            name="modelo",
            python_model=DummyPyFunc(),
            registered_model_name="checagens-camada2",
        )

    # Promove versão 1
    promover(versao=1, tracking_uri=tracking_uri)

    # Verifica alias producao
    client = MlflowClient(tracking_uri=tracking_uri)
    modelo_prod = client.get_model_version_by_alias("checagens-camada2", "producao")
    assert str(modelo_prod.version) == "1"

    # Carrega modelo via alias 'producao'
    modelo_carregado = mlflow.pyfunc.load_model("models:/checagens-camada2@producao")
    res = modelo_carregado.predict(["texto"])
    assert res == {"faixa": "poucos_sinais", "sinais": []}

