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

## 2. Instalação e Dependências de Nuvem

Para habilitar a integração com os serviços em nuvem da Microsoft Azure e bibliotecas de busca vetorial:

```bash
pip install -e '.[azure,busca]'
```

O conjunto de dependências adicionais inclui:
- `azure-ai-ml` e `azure-identity`: Interação com a API do Azure Machine Learning e autenticação via RBAC/Service Principal.
- `mlflow` e `azureml-mlflow`: Rastreamento de parâmetros, métricas e integração com o Model Registry na nuvem.
- `dvc` e `dvc-azure`: Sincronização de artefatos com o Azure Blob Storage.
- `sentence-transformers`: Codificação vetorial densa de alegações na Camada 1.

---

## 3. Recursos Provisionados na Microsoft Azure

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
| **Key Vault** | `mlwresiakeyvault21216155` | Vault | Gerenciamento seguro de chaves e segredos |
| **Log Analytics** | `workspace-rgresiaIuVF` | Log Analytics | Agregação centralizada de logs |
| **Service Principal** | `sp-github-res-ia` | App ID: `4ecd68f8-...` | Credenciais RBAC para autenticação da esteira GitHub Actions |

---

## 4. Data Version Control (DVC)

O versionamento de bases pesadas e binários foi desacoplado do Git via DVC integrado ao Azure Blob Storage.

### 4.1. Artefatos Rastreados
* **Índice Vetorial da Camada 1** (`data/indices/camada1/`):
  * `vetores.npy` (18.8 MB): Matriz densa com 12.245 vetores de 384 dimensões gerados via `sentence-transformers`.
  * `checagens.json` (4.9 MB): Base indexada com metadados (alegação, agência, veredito, link, data).
  * `manifesto.json`: Validação estrita de integridade via hashes SHA-256 no momento da carga.
* **Bases de Treino e Teste**: `treino.csv` (9.934 linhas), `teste.csv` (3.295 linhas), `teste_curtos.csv` (297 linhas) e bases brutas.
* **Classificador Serializado**: `models/classificador.joblib` (14 MB).

### 4.2. Configuração de Credenciais e Autenticação (Sem vazar no Git)
O remote oficial está declarado em `.dvc/config`:
```ini
[core]
    remote = azure
['remote "azure"']
    url = azure://dvc/res-ia-challenge-1
```

As credenciais de acesso **nunca** vão para o repositório git. Podem ser definidas de duas formas:
1. **Via Variável de Ambiente (Recomendado para CI/CD e sessões de desenvolvimento local)**:
   ```bash
   export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=stresiachallenge1;AccountKey=...;EndpointSuffix=core.windows.net"
   ```
2. **Via Configuração Local do DVC (`.dvc/config.local` - ignorado pelo `.gitignore`)**:
   ```bash
   dvc config --local remote.azure.connection_string "sua_connection_string"
   # Ou utilizando SAS token:
   dvc config --local remote.azure.sas_token "seu_sas_token"
   ```

### 4.3. Comandos Operacionais do DVC
```bash
# Restaurar todos os artefatos rastreados
dvc pull

# Restaurar especificamente o índice da Camada 1
dvc pull data/indices/camada1

# Enviar novos artefatos para a nuvem
dvc push

# Conferir status de sincronização com o Blob Storage
dvc status -c

# Reproduzir a etapa de treino via pipeline DVC
dvc repro -f treinar
```

---

## 5. Governança e Rastreamento com MLflow (Azure ML)

O treinamento da Camada 2 integra rastreabilidade nativa com o Azure ML Studio via MLflow.

### 5.1. Rastreamento e Modo Offline
A função `registrar_mlflow()` em `src/inteligencia/treino.py`:
* **Modo Offline Automático**: Se `MLFLOW_TRACKING_URI` não estiver definida, o treino executa 100% offline, garantindo testes sem dependência de rede (RNF-10).
* **Tracking na Azure**: Para habilitar o registro remoto no workspace `mlw-res-ia`:
  ```bash
  export MLFLOW_TRACKING_URI=$(az ml workspace show --resource-group rg-res-ia --name mlw-res-ia --query mlflow_tracking_uri -o tsv)
  python -m inteligencia.treino
  ```
  Registra automaticamente:
  * Parâmetros do `params.yaml` (TF-IDF: `max_features`, `ngram_range`; Regressão Logística: `C`, `penalty`, `class_weight`).
  * Métricas de validação: `f1_macro`, taxa de `falso_alarme` e flag de homologação numérica `go_no_go`.
  * Tags de auditoria e reprodutibilidade: `git_commit`, `hash_base` e `decisao`.
  * Artefatos JSON gerados: `metricas_camada2.json` e `params_camada2.json`.
  * Modelo serializado registrado como `checagens-camada2` encapsulado na classe customizada `ClassificadorPyFunc` com total paridade contratual com `classificar()`.

### 5.2. Trava Humana de Promoção para Produção
Nenhum modelo é promovido automaticamente para produção. O script `scripts/promover_modelo.py` atua como gate humano auditável:
```bash
python scripts/promover_modelo.py --versao 1
```
O script audita se a versão registrada atingiu os critérios pré-fixados (`f1_macro >= 0.70` e `falso_alarme <= 0.05`) e efetua a transição oficial para o estágio `Production` e alias/tag `producao`.

---

## 6. Conteinerização e Deploy no Azure Container Apps

### 6.1. Construção da Imagem Docker Autocontida
No `Dockerfile`:
* O script `scripts/baixar_artefatos_deploy.py` baixa o índice da Camada 1 via DVC e o modelo homologado (`@producao`) via MLflow durante a fase de build.
* A imagem empacota o código-fonte, dependências, [params.yaml](../params.yaml), `models/` e `data/indices/`.
* A imagem gerada é autocontida e opera em runtime sem depender de chaves da nuvem para inferência.

### 6.2. Modo Polling e Réplica Única (Zero Conflitos)
* O bot opera via **Long-Polling** com `app.run_polling()` da biblioteca `python-telegram-bot`.
* **Segurança**: Sem portas de entrada (ingress) abertas na internet pública.
* **Escala**: Configurado estritamente com `--min-replicas 1 --max-replicas 1` para garantir escuta contínua de mensagens sem incorrer em conflitos de concorrência com a API do Telegram (`Conflict: terminated by other getUpdates request`).

### 6.3. Comandos de Gerenciamento do Container App (Azure CLI)
```bash
# Atualizar a imagem do Container App para uma nova versão
az containerapp update \
  --name aca-res-ia-bot \
  --resource-group rg-res-ia \
  --image crresiachallenge1.azurecr.io/res-ia-bot:latest

# Acompanhar logs de execução em tempo real
az containerapp logs show \
  --name aca-res-ia-bot \
  --resource-group rg-res-ia \
  --follow
```

---

## 7. Esteira de Integração e Deploy Contínuo (CI/CD)

Configurada em `.github/workflows/ci.yml`:

### 7.1. Fluxo dos Jobs
1. **Testes Paralelos**:
   * Execução da suíte completa de **115 testes** via `pytest` em matriz paralela (**Python 3.11** e **Python 3.12**).
   * Valida testes de Azure MLOps (`tests/test_azure_mlops.py`), busca, robustez (RNF-09), transparência (RNF-07), reprodutibilidade (RNF-10) e conformidade LGPD.
2. **Deploy Automatizado (Push na branch main)**:
   * Autenticação na Azure via Service Principal `sp-github-res-ia`.
   * Execução de `scripts/baixar_artefatos_deploy.py` com fallback DVC/MLflow.
   * Compilação da imagem Docker autocontida.
   * Login e push no Azure Container Registry (`crresiachallenge1.azurecr.io/res-ia-bot:latest`).
   * Atualização/criação transparente e idempotente no Azure Container Apps (`aca-res-ia-bot`).

### 7.2. Segredos Configurados no GitHub Actions
Para a esteira operar de forma autônoma e segura, 3 secrets foram configuradas no repositório (**Settings > Secrets and variables > Actions**):

| Secret no GitHub | Descrição e Finalidade |
|---|---|
| `AZURE_CREDENTIALS` | JSON com `clientId`, `clientSecret`, `subscriptionId` e `tenantId` do Service Principal `sp-github-res-ia` para autenticação RBAC |
| `AZURE_STORAGE_CONNECTION_STRING` | Connection string da conta `stresiachallenge1` para o `dvc pull` restaurar os índices da Camada 1 |
| `TELEGRAM_TOKEN` | Token de autenticação fornecido pelo `@BotFather` para conexão à API do Telegram |

---

## 8. Observabilidade, Telemetria e Monitoramento

A observabilidade em produção é centralizada no Azure Application Insights (`mlwresiainsightsd3c0939f`):
* **Variável de Ambiente**: Injetada no contêiner via `APPLICATIONINSIGHTS_CONNECTION_STRING`.
* **Métricas Monitoradas**:
  * Latência de ponta a ponta por consulta (garantindo RNF-01: resposta em menos de 3 segundos).
  * Volume de mensagens recebidas e distribuição por camada ativada (Camada 1 vs. Camada 2).
  * Taxa de exceções, falhas de parsing ou timeout na API do Telegram.
* **Log Analytics**: O workspace `workspace-rgresiaIuVF` agrega os logs estruturados emitidos pelo `python-telegram-bot` e pelas rotinas de classificação.

---

## 9. Conformidade e Privacidade (LGPD)

O módulo `src/checagens/registros.py`:
* Registra consultas e votos dos usuários com identificadores pseudo-anônimos (UUID gerado por evento).
* Por desenho de código, impede a captura de qualquer dado identificável do Telegram (`user_id`, `username`, telefone, IP).
* As respostas respeitam a transparência (RNF-07), fornecendo links para agências oficiais e canal do TSE sem emitir juízo próprio de verdade ou mentira.

---

## 10. Resumo de Funções e Componentes da Arquitetura

| Componente / Módulo | Função / Comando Principal | Descrição e Papel na Arquitetura |
|---|---|---|
| **Camada 1 (Busca)** | `inteligencia.busca.buscar()` | Busca híbrida (similaridade semântica + filtro de negação) em 12.245 checagens com vetores pré-computados |
| **Camada 2 (Alerta)** | `inteligencia.classificador.classificar()` | Classificação de estilo e detecção de sinais linguísticos suspeitos com termos-gatilho |
| **Bot Telegram** | `python -m checagens.bot` | Serviço contínuo via long-polling integrado à API do Telegram para atendimento direto em `@checaai_bot` |
| **DVC Remote** | `dvc pull` / `dvc push` | Versionamento de dados brutos/processados e índices pesados no Azure Blob Storage (`stresiachallenge1`) |
| **MLflow Tracking** | `python -m inteligencia.treino` | Registro de experimentos, hiperparâmetros e métricas Go/No-Go no Azure ML Workspace (`mlw-res-ia`) |
| **Model Registry** | `scripts/promover_modelo.py` | Governança com trava humana para validação e promoção do modelo ao estágio `Production` / alias `producao` |
| **Deploy Pipeline** | `scripts/baixar_artefatos_deploy.py` | Script de esteira para baixar artefatos aprovados e preparar o build Docker autocontido |
| **Container Registry** | `az acr login` / `docker push` | Armazenamento de imagens Docker no Azure Container Registry (`crresiachallenge1.azurecr.io`) |
| **Container Apps** | `aca-res-ia-bot` (`env-res-ia`) | Execução serverless com 0.5 vCPU e 1.0 GiB de RAM mantendo réplica única ativa 24/7 |
| **Observabilidade** | Azure Application Insights | Monitoramento contínuo de latência (RNF-01), volume de mensagens e diagnóstico de erros |

---

## 11. Links Oficiais e Acessos Diretos

* **Bot no Telegram**: [https://t.me/checaai_bot](https://t.me/checaai_bot) (`@checaai_bot`)
* **Documentação Online (GitHub Pages / Astro Starlight)**: [https://gpaulovit.github.io/RES-IA-Challenge-1/](https://gpaulovit.github.io/RES-IA-Challenge-1/)
* **Azure Portal (Resource Group `rg-res-ia`)**: [https://portal.azure.com/.../rg-res-ia](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/overview)
* **Azure ML Studio (Workspace `mlw-res-ia`)**: [https://ml.azure.com/.../mlw-res-ia](https://ml.azure.com/?wsid=/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourcegroups/rg-res-ia/workspaces/mlw-res-ia)
* **Azure Container Apps (`aca-res-ia-bot`)**: [https://portal.azure.com/.../aca-res-ia-bot](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/providers/Microsoft.App/containerApps/aca-res-ia-bot)
