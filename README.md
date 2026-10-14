# RES-IA-Challenge-1

Bot no Telegram para quem recebeu uma mensagem ou link sobre as eleições de 2026 e quer saber,
antes de repassar, se aquilo já foi desmentido. O bot nunca dá veredito próprio de "verdade" ou
"mentira". O desenho completo está em [Requisitos](docs/requisitos.md).

🤖 **Bot Oficial no Telegram**: [@checaai_bot](https://t.me/checaai_bot)  
📄 **Página do Projeto (Docsify)**: [gpaulovit.github.io/RES-IA-Challenge-1](https://gpaulovit.github.io/RES-IA-Challenge-1/)  
☁️ **Infraestrutura Azure**: [Resource Group `rg-res-ia`](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/overview) · [Azure ML Studio (Model Registry)](https://ml.azure.com/?wsid=/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourcegroups/rg-res-ia/workspaces/mlw-res-ia) · [Container App `aca-res-ia-bot`](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/providers/Microsoft.App/containerApps/aca-res-ia-bot)


## Por onde começar: `experiments/`

A pasta [experiments/](experiments/) é a entrada principal. Os notebooks são numerados na ordem
em que devem ser lidos e guardam código e resultado lado a lado, para auditar célula a célula:

| Notebook | O que responde |
| --- | --- |
| `00_load_corpus.ipynb` | Carga do corpus de checagens (formato e colunas) |
| `01_embeddings.ipynb` | Embeddings das duas versões dos dados |
| `02_clusters.ipynb` | Agrupamento das alegações |
| `05_avaliacao.ipynb` | Conjunto de teste de reescrita e normalização da consulta |
| `06_modelos.ipynb` | Comparação de modelos de embeddings (Recall@k e MRR) |

Os módulos `.py` da pasta guardam a lógica que os notebooks importam; o
[README de experiments](experiments/README.md) descreve cada um. Produtos descartados e o
registro dos gates deles estão em [archive/](archive/README.md) e não devem ser usados como
referência.

```sh
python3 -m venv .venv
.venv/bin/pip install -r experiments/requirements.txt
.venv/bin/dvc pull                     # dados de experiments/data
cd experiments && ../.venv/bin/jupyter lab
```

## Código do bot: `src/`

[src/inteligencia/](src/inteligencia/README.md) tem as duas camadas que o bot chama:
`buscar()` (checagens parecidas) e `classificar()` (sinais de alerta). O contrato está no README
dele.

[src/checagens/](src/checagens/) guarda as regras que o bot aplica:

- `mensagens.py`: formatação, robustez e transparência das respostas.
- `registros.py`: registro anônimo de consultas e votos (LGPD).

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q        # testes do bot e dos experimentos
make latency               # tempo de resposta nas 30 mensagens de teste (RNF-01)
```

## Estrutura

- [experiments/](experiments/): notebooks, módulos e resultados dos modelos.
- [src/inteligencia/](src/inteligencia/README.md): camadas 1 e 2 (busca e sinais de alerta).
- [src/checagens/](src/checagens/): regras de mensagens e registros do bot.
- [tests/](tests/): verificações automáticas (rodam no CI).
- [scripts/](scripts/): medição de latência.
- [data/](data/): mensagens de teste e benchmark.
- [docs/](docs/): documentação publicada via GitHub Pages (docsify).
- [openspec/](openspec/): propostas e specs geridas pelo [OpenSpec](https://openspec.dev).
- [archive/](archive/README.md): produtos descartados; não usar como referência.

O protótipo de busca das semanas 1 a 3 (API, embeddings e retrieval em `src/`) foi retirado; ele
continua no histórico do git (tag `legado-busca` e commits da `main`).

## Configurar Azure (DVC, MLflow e Deploy)

O ecossistema em nuvem na Azure padroniza o versionamento de dados, modelos e o deploy serverless (custo praticamente zero, sem computação 24h ligada).

### 1. Divisão de Papéis
- **DVC (Azure Blob Storage)**: Versiona dados brutos/processados, pipelines (`dvc.yaml`), o índice vetorial da **Camada 1** (`data/indices/camada1`) e o artefato `models/classificador.joblib`.
- **MLflow (Azure ML Workspace)**: Rastreia os parâmetros, métricas e artefatos de treino da **Camada 2**, registrando o modelo como `pyfunc` no Model Registry com o nome `checagens-camada2`. O deploy consome o modelo com o alias `producao`.
- **Application Insights**: Monitora a observabilidade em produção no Azure Container Apps (latência, volume de requisições e taxa de erros).
- **Azure Container Apps**: Hospeda o bot do Telegram em modo serverless com escala a zero (`min-replicas 0`).

### 2. Instalação e Dependências
Para instalar os pacotes de integração com a Azure:
```sh
pip install -e '.[azure,busca]'
```

### 3. Remote do DVC na Azure
O remote do DVC está configurado em `.dvc/config` apontando para:
`azure://dvc/res-ia-challenge-1` (Storage Account padrão: `stresiachallenge1`).

As credenciais **nunca** vão para o repositório git. Configure de uma das seguintes formas:
1. **Via Variável de Ambiente (Recomendado para CI/CD e local)**:
   ```sh
   export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
   ```
2. **Via Configuração Local do DVC**:
   ```sh
   dvc config --local remote.azure.connection_string "sua_connection_string"
   # ou com SAS token:
   # dvc config --local remote.azure.sas_token "seu_sas_token"
   ```

Para restaurar dados e índice da camada 1:
```sh
dvc pull                           # restaura todos os dados rastreados
dvc pull data/indices/camada1      # restaura especificamente o índice da camada 1
```

Para sincronizar novos dados com o remote:
```sh
dvc push
dvc status -c                      # verifica se o cache local e a Azure estão em sincronia
```

### 4. Rastreamento e Registro com MLflow (Azure ML)
O rastreamento via MLflow é **opcional**: se `MLFLOW_TRACKING_URI` não estiver definida, o treino roda normalmente em modo offline (garantindo determinismo RNF-10 e compatibilidade com `pytest`).

Para treinar registrando no Azure ML Studio:
1. Obtenha a Tracking URI do seu workspace Azure ML:
   ```sh
   export MLFLOW_TRACKING_URI=$(az ml workspace show --resource-group rg-res-ia --name mlw-res-ia --query mlflow_tracking_uri -o tsv)
   ```
2. Execute o treinamento:
   ```sh
   python -m inteligencia.treino    # ou: dvc repro -f treinar
   ```
   A execução registrará automaticamente:
   - Parâmetros do `params.yaml`
   - Métricas (`f1_macro`, `falso_alarme`, indicador numérico `go_no_go`)
   - Tags de rastreabilidade (`git_commit`, `hash_base`, `decisao`)
   - Artefatos JSON (`metricas_camada2.json`, `params_camada2.json`)
   - Modelo registrado como `checagens-camada2` (flavor `pyfunc` encapsulando `Classificador`)

### 5. Promoção Auditável para Produção
Como trava humana auditável antes do deploy, a promoção exige conferência dos critérios pré-registrados:
```sh
# Promove a versão aprovada (valida go/no-go) para o alias 'producao':
python scripts/promover_modelo.py --versao 1
```

### 6. Deploy Autocontido no Azure Container Apps
O deploy é automatizado via GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)):
1. **Download de Artefatos**: Baixados via `scripts/baixar_artefatos_deploy.py` (sincronizando o índice da Camada 1 via DVC e o modelo de produção da Camada 2 via Azure ML Model Registry).
2. **Build Docker Autocontido**: O [Dockerfile](Dockerfile) empacota o código, `params.yaml`, `models/` e `data/indices/` diretamente dentro da imagem.
3. **Registro de Contêineres (ACR)**: Enviado para o registro privado `crresiachallenge1.azurecr.io/res-ia-bot:latest`.
4. **Hospedagem no Azure Container Apps**: O contêiner roda no [Container App `aca-res-ia-bot`](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/providers/Microsoft.App/containerApps/aca-res-ia-bot) no ambiente `env-res-ia` com `--min-replicas 1 --max-replicas 1` para garantir polling contínuo sem conflitos no Telegram.
5. **Acesso do Usuário Final**: Qualquer pessoa pode testar o bot diretamente pelo Telegram em [@checaai_bot](https://t.me/checaai_bot).
6. **Observabilidade**: O monitoramento de requisições, latência e logs é agregado via Application Insights (`mlwresiainsightsd3c0939f`).


