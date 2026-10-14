# RES-IA-Challenge-1

Bot no Telegram que confere mensagens e links sobre as eleições de 2026: busca checagens de
agências (camada 1) e, sem checagem parecida, mostra uma faixa de alerta (camada 2).

### Acessos e Links Rápidos

* 🤖 **Bot Oficial no Telegram**: [https://t.me/checaai_bot](https://t.me/checaai_bot) (`@checaai_bot`)
* 📄 **Código-Fonte no GitHub**: [https://github.com/gpaulovit/RES-IA-Challenge-1](https://github.com/gpaulovit/RES-IA-Challenge-1)
* ☁️ **Infraestrutura Azure**:
  * [Resource Group `rg-res-ia`](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/overview)
  * [Azure ML Studio (Model Registry)](https://ml.azure.com/?wsid=/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourcegroups/rg-res-ia/workspaces/mlw-res-ia)
  * [Container App `aca-res-ia-bot`](https://portal.azure.com/#@ingridsssoaresoutlook.onmicrosoft.com/resource/subscriptions/93afb629-e1be-497f-9482-0d67829f4016/resourceGroups/rg-res-ia/providers/Microsoft.App/containerApps/aca-res-ia-bot)


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
