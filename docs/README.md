# RES-IA-Challenge-1

Bot no Telegram que confere mensagens e links sobre as eleições de 2026: busca checagens de
agências (camada 1) e, sem checagem parecida, mostra uma faixa de alerta (camada 2).

### Acessos e Links Rápidos

* **Bot Oficial no Telegram**: [https://t.me/checaai_bot](https://t.me/checaai_bot) (`@checaai_bot`)
* **Código-Fonte no GitHub**: [https://github.com/gpaulovit/RES-IA-Challenge-1](https://github.com/gpaulovit/RES-IA-Challenge-1)
* **Infraestrutura Azure**:
  * [Resource Group `rg-res-ia`](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/overview)
  * [Azure ML Studio (Model Registry)](https://ml.azure.com/?wsid=/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourcegroups/rg-res-ia/workspaces/mlw-res-ia)
  * [Container App `aca-res-ia-bot`](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/providers/Microsoft.App/containerApps/aca-res-ia-bot)

### Divisão da Equipe e Responsabilidades

| Integrante | Papel / Frente | Foco Principal |
|---|---|---|
| **Ana Júlia** | Produto e Decisão | Especificação funcional, redação de mensagens do bot, fluxos de experiência do usuário e apresentação executiva. |
| **Cibelly Lourenço** | Domínio de Dados | Curadoria, saneamento e balanceamento das bases de checagens históricas e de treino do classificador. |
| **Eduarda** | Engenharia de Software | Desenvolvimento do bot no Telegram (`python-telegram-bot`), extração de links e integração de comandos. |
| **Paulo** | Modelos de IA | Calibração de limiares da Camada 1, treinamento do classificador baseline da Camada 2 e relatório Go/No-Go. |
| **Ingrid Soares** | [DevOps e MLOps](devops-mlops.md) | Arquitetura em nuvem (Azure), esteira de CI/CD (GitHub Actions), DVC, MLflow Model Registry, Docker e testes automatizados. |

#### Frente de DevOps e MLOps (Ingrid Soares)

A especificação completa de infraestrutura, esteira automatizada e governança está detalhada em **[DevOps e MLOps](devops-mlops.md)**. Em resumo:
* **Nuvem Azure**: Provisionamento serverless do Resource Group `rg-res-ia`, Azure Blob Storage (`stresiachallenge1` / `dvc`), Azure Container Registry (`crresiachallenge1`) e Azure Container Apps (`aca-res-ia-bot` no ambiente `env-res-ia` com réplica contínua e telemetria no Application Insights).
* **DVC e Versionamento**: Remote oficial `azure://dvc/res-ia-challenge-1` rastreando o índice da Camada 1 (12.245 checagens com vetores de 384 dimensões), dados de treino/teste e integridade SHA-256.
* **MLflow e Governança**: Rastreamento de parâmetros, métricas e tags no Azure ML Workspace (`mlw-res-ia`), modelo `checagens-camada2` empacotado em `pyfunc` e trava humana de homologação (`scripts/promover_modelo.py`) para o alias `producao`.
* **Docker e CI/CD**: Contêiner autocontido com `params.yaml` e pipeline no GitHub Actions executando 115 testes automatizados (Python 3.11/3.12), auditoria LGPD de registros anônimos e deploy contínuo na Azure.



## Conteúdo

- [DevOps e MLOps](devops-mlops.md): infraestrutura em nuvem (Azure), remote DVC, tracking MLflow, deploy no Container Apps e CI/CD.

- [Perguntas](perguntas.md): problema, dados por eixo e respostas de MLOps.
- [Dados do bot](dados.md) — base de checagens (camada 1) e base de treino do classificador (camada 2): fontes, campos, tamanhos, licenças, limitações e como regenerar.
- [Requisitos](requisitos.md): o bot no Telegram, com decisões, requisitos funcionais e não funcionais, regras e prioridade.
- [Histórias de usuário](historias.md): quem usa o bot e para quê, com critérios de aceitação.
- [Referências](refs.md): datasets usados, MLOps e SDD.
- [Relatório da camada 2](relatorio-camada2.md): critério de go/no-go do classificador, escrito antes do teste, e resultado.
- [Testes e benchmark](testes.md): testes automatizados, robustez, transparência e benchmark.
- [Avaliação do benchmark](avaliacao-benchmark.md): metodologia da avaliação de recuperação.
