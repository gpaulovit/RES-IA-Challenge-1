# DevOps e MLOps: Infraestrutura, Versionamento e Deploy

> Responsável: Ingrid Soares (`papel: devops-mlops`). Atualizado em 13/10/2026.

Este documento consolida a arquitetura de infraestrutura em nuvem, esteira de CI/CD, versionamento de dados com DVC, governança de modelos com MLflow e deploy contínuo no Azure Container Apps para o projeto ChecaAÍ (RES-IA Challenge 1).

---

## 1. Visão Geral da Arquitetura

O ecossistema em nuvem foi desenhado para garantir **custo computacional zero em repouso** (arquitetura serverless e storage sob demanda), alta disponibilidade, reprodutibilidade determinística (RNF-10) e conformidade estrita com a LGPD.

```text
+---------------------------------------------------------------------------------+
| Microsoft Azure (rg-res-ia / East US)                                           |
|                                                                                 |
|  +------------------------+      +-------------------------------------------+  |
|  | Storage Account        |      | Azure ML Workspace (mlw-res-ia)           |  |
|  | stresiachallenge1      |      | - MLflow Tracking Server                  |  |
|  | Container Blob: dvc    |      | - Model Registry (checagens-camada2)      |  |
|  +-----------+------------+      +---------------------+---------------------+  |
|              ^                                         ^                        |
|              | dvc push / pull                         | log_params/metrics     |
|              v                                         v                        |
|  +-----------+------------+      +---------------------+---------------------+  |
|  | DVC Remote             |      | MLflow Client (inteligencia.treino)       |  |
|  | azure://dvc/...        |      | Trava Humana (promover_modelo.py)         |  |
|  +-----------+------------+      +---------------------+---------------------+  |
|              |                                         |                        |
|              +--------------------+--------------------+                        |
|                                   | baixar_artefatos_deploy.py                  |
|                                   v                                             |
|                     +-------------+-------------+                               |
|                     | Imagem Docker Autocontida |                               |
|                     +-------------+-------------+                               |
|                                   | docker push                                 |
|                                   v                                             |
|  +--------------------------------+------------------------------------------+  |
|  | Azure Container Registry (crresiachallenge1.azurecr.io)                   |  |
|  +--------------------------------+------------------------------------------+  |
|                                   | deploy (az containerapp)                    |
|                                   v                                             |
|  +--------------------------------+------------------------------------------+  |
|  | Azure Container Apps (aca-res-ia-bot / env-res-ia)                        |  |
|  | - 0.5 vCPU / 1.0 GiB RAM (Consumption)                                   |  |
|  | - Replicas: min 1 / max 1 (Polling continuo no Telegram)                 |  |
|  | - Telemetria: Application Insights (mlwresiainsightsd3c0939f)            |  |
|  +---------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------+
```

---

## 2. Recursos Provisionados na Microsoft Azure

| Recurso Azure | Identificador | SKU / Configuração | Papel no Projeto |
|---|---|---|---|
| **Resource Group** | `rg-res-ia` | East US | Agrupamento dos recursos e isolamento de segurança |
| **Storage Account** | `stresiachallenge1` | Standard_LRS | Armazenamento de dados e artefatos DVC |
| **Blob Container** | `dvc` | Container Blob | Remote oficial do DVC (`azure://dvc/res-ia-challenge-1`) |
| **Azure ML Workspace** | `mlw-res-ia` | Serverless (sem clusters dedicados) | Servidor de tracking MLflow e Model Registry oficial |
| **Azure Container Registry** | `crresiachallenge1` | Basic (Admin Enabled) | Repositório privado de imagens de contêiner |
| **Container Apps Environment** | `env-res-ia` | Perfil Consumption | Ambiente gerenciado serverless para hospedar o bot |
| **Container App** | `aca-res-ia-bot` | 0.5 vCPU, 1.0 GiB RAM | Worker do bot Telegram com 1 réplica ativa 24/7 |
| **Application Insights** | `mlwresiainsightsd3c0939f` | Standard Telemetry | Coleta de telemetria, latência (RNF-01) e erros |
| **Service Principal** | `sp-github-res-ia` | App ID: `4ecd68f8-...` | Credenciais RBAC para autenticação da esteira GitHub Actions |

---

## 3. Data Version Control (DVC)

O versionamento de bases pesadas e binários foi desacoplado do Git via DVC integrado ao Azure Blob Storage.

### 3.1. Artefatos Rastreados
* **Índice Vetorial da Camada 1** (`data/indices/camada1/`):
  * `vetores.npy` (18.8 MB): Matriz densa com 12.245 vetores de 384 dimensões gerados via `sentence-transformers`.
  * `checagens.json` (4.9 MB): Base indexada com metadados (alegação, agência, veredito, link, data).
  * `manifesto.json`: Validação estrita de integridade via hashes SHA-256 no momento da carga.
* **Bases de Treino e Teste**: `treino.csv` (9.934 linhas), `teste.csv` (3.295 linhas), `teste_curtos.csv` (297 linhas) e bases brutas.
* **Classificador Serializado**: `models/classificador.joblib` (14 MB).

### 3.2. Comandos Operacionais
```bash
# Restaurar todos os artefatos rastreados
dvc pull

# Restaurar especificamente o índice da Camada 1
dvc pull data/indices/camada1

# Enviar novos artefatos para a nuvem
dvc push

# Conferir status de sincronização com o Blob Storage
dvc status -c
```

---

## 4. Governança e Rastreamento com MLflow (Azure ML)

O treinamento da Camada 2 integra rastreabilidade nativa com o Azure ML Studio via MLflow.

### 4.1. Rastreamento e Modo Offline
A função `registrar_mlflow()` em `src/inteligencia/treino.py`:
* **Modo Offline Automático**: Se `MLFLOW_TRACKING_URI` não estiver definida, o treino executa 100% offline, garantindo testes sem rede (RNF-10).
* **Tracking na Azure**: Quando apontada para `mlw-res-ia`, registra:
  * Parâmetros do `params.yaml` (TF-IDF, penalidade, regularização C).
  * Métricas: `f1_macro`, taxa de `falso_alarme` e flag de homologação numérica `go_no_go`.
  * Tags de auditoria: `git_commit`, `hash_base` e `decisao`.
  * Modelo registrado como `checagens-camada2` encapsulado na classe customizada `ClassificadorPyFunc` com total paridade contratual com `classificar()`.

### 4.2. Trava Humana de Promoção para Produção
Nenhum modelo é promovido automaticamente. O script `scripts/promover_modelo.py` atua como gate humano auditável:
```bash
python scripts/promover_modelo.py --versao 1
```
O script audita se a versão atingiu os critérios pré-fixados (`f1_macro >= 0.70` e `falso_alarme <= 0.05`) e efetua a transição para `stage: Production` e tag/alias `producao`.

---

## 5. Conteinerização e Deploy no Azure Container Apps

### 5.1. Construção da Imagem Docker Autocontida
No `Dockerfile`:
* O script `scripts/baixar_artefatos_deploy.py` baixa o índice da Camada 1 via DVC e o modelo homologado via MLflow durante a fase de build.
* A imagem empacota o código-fonte, dependências, [params.yaml](../params.yaml), `models/` e `data/indices/`.
* A imagem gerada é autocontida e opera em runtime sem depender de chaves da nuvem para inferência.

### 5.2. Modo Polling e Réplica Única
* O bot opera via **Long-Polling** com `app.run_polling()` da biblioteca `python-telegram-bot`.
* **Segurança**: Sem portas de entrada (ingress) abertas na internet.
* **Escala**: Configurado estritamente com `--min-replicas 1 --max-replicas 1` para garantir escuta contínua de mensagens sem incorrer em conflitos de concorrência com a API do Telegram (`Conflict: terminated by other getUpdates request`).

---

## 6. Esteira de Integração e Deploy Contínuo (CI/CD)

Configurada em `.github/workflows/ci.yml`:

1. **Testes Paralelos**:
   * Execução da suíte completa de **115 testes** via `pytest` em matriz paralela (**Python 3.11** e **Python 3.12**).
   * Valida testes de Azure MLOps (`tests/test_azure_mlops.py`), busca, robustez (RNF-09), transparência (RNF-07), reprodutibilidade (RNF-10) e conformidade LGPD.
2. **Deploy Automatizado (Push na branch main)**:
   * Autenticação na Azure via Service Principal.
   * Execução de `scripts/baixar_artefatos_deploy.py` com fallback DVC/MLflow.
   * Compilação da imagem Docker.
   * Login e push no Azure Container Registry (`crresiachallenge1.azurecr.io/res-ia-bot:latest`).
   * Atualização/criação transparente e idempotente no Azure Container Apps (`aca-res-ia-bot`).

---

## 7. Conformidade e Privacidade (LGPD)

O módulo `src/checagens/registros.py`:
* Registra consultas e votos dos usuários com identificadores pseudo-anônimos (UUID gerado por evento).
* Por desenho de código, impede a captura de qualquer dado identificável do Telegram (`user_id`, `username`, telefone, IP).
* As respostas respeitam a transparência (RNF-07), fornecendo links para agências oficiais e canal do TSE sem emitir juízo próprio de verdade ou mentira.
