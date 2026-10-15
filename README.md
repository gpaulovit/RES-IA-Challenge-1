# RES-IA-Challenge-1

Bot no Telegram para quem recebeu uma mensagem ou link sobre as eleições de 2026 e quer saber,
antes de repassar, se aquilo já foi desmentido. O bot nunca dá veredito próprio de "verdade" ou
"mentira". O desenho completo está em [Requisitos](docs/requisitos.md).

> [!TIP]
> **Links de Acesso**:
> - **Bot no Telegram**: [https://t.me/checaai_bot](https://t.me/checaai_bot) (`@checaai_bot`)
> - **Documentação Online (GitHub Pages)**: [https://gpaulovit.github.io/RES-IA-Challenge-1/](https://gpaulovit.github.io/RES-IA-Challenge-1/)
> - **Azure Portal (Resource Group `rg-res-ia`)**: [https://portal.azure.com/.../rg-res-ia](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/overview)
> - **Azure ML Studio (Model Registry & MLflow)**: [https://ml.azure.com/.../mlw-res-ia](https://ml.azure.com/?wsid=/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourcegroups/rg-res-ia/workspaces/mlw-res-ia)
> - **Azure Container Apps (`aca-res-ia-bot`)**: [https://portal.azure.com/.../aca-res-ia-bot](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/providers/Microsoft.App/containerApps/aca-res-ia-bot)

## Divisão da Equipe e Responsabilidades

| Integrante | Papel / Frente | Foco Principal |
|---|---|---|
| **Ana Júlia** | Produto e Decisão | Especificação funcional, redação de mensagens do bot, fluxos de experiência do usuário e apresentação executiva. |
| **Cibelly Lourenço** | Domínio de Dados | Curadoria, saneamento e balanceamento das bases de checagens históricas e de treino do classificador. |
| **Eduarda** | Engenharia de Software | Desenvolvimento do bot no Telegram (`python-telegram-bot`), extração de links e integração de comandos. |
| **Paulo** | Modelos de IA | Calibração de limiares da Camada 1, treinamento do classificador baseline da Camada 2 e relatório Go/No-Go. |
| **Ingrid Soares** | [DevOps e MLOps](docs/devops-mlops.md) | Arquitetura em nuvem (Azure), esteira de CI/CD (GitHub Actions), DVC, MLflow Model Registry, Docker e testes automatizados. |

### Frente de DevOps e MLOps (Ingrid Soares)

A especificação completa de infraestrutura, esteira automatizada e governança está detalhada em **[docs/devops-mlops.md](docs/devops-mlops.md)**. Em resumo:

* **Nuvem Azure**: Provisionamento serverless do Resource Group `rg-res-ia`, Azure Blob Storage (`stresiachallenge1` / `dvc`), Azure Container Registry (`crresiachallenge1`) e Azure Container Apps (`aca-res-ia-bot` no ambiente `env-res-ia` com réplica contínua e telemetria no Application Insights).
* **DVC e Versionamento**: Remote oficial `azure://dvc/res-ia-challenge-1` rastreando o índice da Camada 1 (12.245 checagens com vetores de 384 dimensões), dados de treino/teste e integridade SHA-256.
* **MLflow e Governança**: Rastreamento de parâmetros, métricas e tags no Azure ML Workspace (`mlw-res-ia`), modelo `checagens-camada2` empacotado em `pyfunc` e trava humana de homologação (`scripts/promover_modelo.py`) para o alias `producao`.
* **Docker e CI/CD**: Contêiner autocontido com [params.yaml](params.yaml) e pipeline no GitHub Actions ([.github/workflows/ci.yml](.github/workflows/ci.yml)) executando 115 testes automatizados (Python 3.11/3.12), auditoria LGPD de registros anônimos e deploy contínuo na Azure.





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

## Como rodar o bot no Telegram

1. Crie o arquivo `.env` na raiz, copiando `.env.example`, e preencha `TELEGRAM_BOT_TOKEN` com o token do BotFather. O `.env` nunca vai para o GitHub.
2. Instale as dependências (seção acima).
3. Rode o bot:

   ```sh
   python -m checagens.bot
   ```

   O terminal mostra o que está ligado: camada 1 e camada 2.

Para ver as respostas sem token e sem Telegram, rode `python scripts/testar_bot_terminal.py`.
Só um computador pode rodar o bot por vez. Detalhes e variáveis de ambiente: [Engenharia do bot](docs/engenharia-bot.md).

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

## Configuração e Deploy na Azure (DVC, MLflow e Container Apps)

O ecossistema em nuvem na Microsoft Azure padroniza o versionamento de dados, a governança de modelos e o deploy serverless contínuo do bot. O guia detalhado de infraestrutura e operações está documentado em **[docs/devops-mlops.md](docs/devops-mlops.md)**.

### Comandos Rápidos de Operação

```sh
# Instalação das dependências de nuvem
pip install -e '.[azure,busca]'

# Restaurar artefatos e índice vetorial da Camada 1 via DVC
dvc pull

# Treinamento com tracking no Azure ML (opcional se MLFLOW_TRACKING_URI estiver definida)
python -m inteligencia.treino

# Promoção auditável da versão do modelo para produção
python scripts/promover_modelo.py --versao 1

# Download de artefatos para deploy autocontido
python scripts/baixar_artefatos_deploy.py
```

### Resumo dos Componentes da Arquitetura

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




