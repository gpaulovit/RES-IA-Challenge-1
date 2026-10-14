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
| **Ingrid Soares** | DevOps e MLOps | Arquitetura em nuvem (Azure), esteira de CI/CD (GitHub Actions), DVC, MLflow Model Registry, Docker e testes automatizados. |

#### Contribuições de MLOps, Nuvem e Qualidade (Ingrid Soares)

A frente de DevOps e MLOps liderada por Ingrid Soares viabilizou a infraestrutura e a homologação em nuvem do projeto:
* **Infraestrutura Azure (Serverless)**: Provisionamento do Resource Group `rg-res-ia`, Azure Blob Storage (`stresiachallenge1` / `dvc`), Azure Container Registry (`crresiachallenge1`) e Azure Container Apps (`aca-res-ia-bot` no ambiente `env-res-ia` com réplica contínua e telemetria no Application Insights).
* **Versionamento com DVC**: Configuração do remote `azure://dvc/res-ia-challenge-1` e rastreamento de 12.245 checagens com vetores densos (`data/indices/camada1`), datasets de treino e testes com verificação SHA-256.
* **Governança com MLflow**: Rastreamento de parâmetros, métricas e tags no Azure ML Workspace (`mlw-res-ia`), empacotamento `pyfunc` e trava humana de promoção para produção (`scripts/promover_modelo.py`).
* **Contêiner e CI/CD**: Dockerfile autocontido com inclusão de `params.yaml` e esteira automatizada no GitHub Actions com 115 testes passando em Python 3.11/3.12 e conformidade LGPD.



## Conteúdo

- [Perguntas](perguntas.md): problema, dados por eixo e respostas de MLOps.
- [Dados do bot](dados.md) — base de checagens (camada 1) e base de treino do classificador (camada 2): fontes, campos, tamanhos, licenças, limitações e como regenerar.
- [Requisitos](requisitos.md): o bot no Telegram, com decisões, requisitos funcionais e não funcionais, regras e prioridade.
- [Histórias de usuário](historias.md): quem usa o bot e para quê, com critérios de aceitação.
- [Referências](refs.md): datasets usados, MLOps e SDD.
- [Relatório da camada 2](relatorio-camada2.md): critério de go/no-go do classificador, escrito antes do teste, e resultado.
- [Guia da arquiteta](guia-arquiteta.md): fluxo e dependências da Engenharia.
- [Testes e benchmark](testes.md): testes automatizados, robustez, transparência e benchmark.
- [Avaliação do benchmark](avaliacao-benchmark.md): metodologia da avaliação de recuperação.
