# RES-IA-Challenge-1

Bot no Telegram que confere mensagens e links sobre as eleições de 2026: busca checagens de
agências (camada 1) e, sem checagem parecida, mostra uma faixa de alerta (camada 2).

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
