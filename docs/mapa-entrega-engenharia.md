# Mapa da entrega de Engenharia

Este mapa ajuda quem chega ao projeto a encontrar a tarefa, sua entrada, a
saída esperada e quem precisa aprová-la. As issues descrevem os critérios
atuais; caixas marcadas registram somente o que já foi demonstrado. Situação
conferida em 01/10/2026.

| Ordem | Issue | Entrada → saída | Quem decide o significado | Situação |
| --- | --- | --- | --- | --- |
| 1 | [#4 — corpus](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/4) | CSV original → corpus JSON e relatório de lacunas | Dados: alegação, datas, vazios e uso no gate | Conversão técnica feita; aceite de Dados pendente |
| 2 | [#9 — vetores](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/9) | Corpus aprovado → vetores, metadados e manifesto | Modelos de IA: candidato e versão; Dados: campo indexado | Baseline técnico feito; candidato ainda não integrado |
| 3 | [#14 — busca](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/14) | Índice aprovado + consulta → Top-K com evidência | Modelos: gate e métricas; Produto: casos esperados | k-NN exato feito; qualidade semântica pendente |
| 4 | [#19 — decisão](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/19) | Candidatos e scores → faixa de correspondência | Modelos: calibração; Produto: linguagem e custo dos erros | Metas propostas, sem medição validada |
| 5 | [#24 — evidências e entrega](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/24) | Busca + política → resposta responsável e testes finais | Dados: pares divergentes; Produto: resposta | Implementação e aceite pendentes |

## Três cuidados antes de fechar uma issue

1. O FactPolCheckBr tem 1.882 registros e 1.820 rótulos `Falsa` (cerca de
   96,7%). Preservar todos os registros e mostrar os resultados por classe.
2. A fonte cobre agosto a dezembro de 2022. Não há nela pares reais separados
   por 180 dias. Essa meta requer uma fonte complementar aprovada ou uma mudança
   formal do horizonte de avaliação.
3. Os 32 controles externos são casos de teste. Os limiares de 60%, a precisão
   de 90% e o Recall@5 são **metas**, até que resultados rotulados, versões e
   denominadores sejam publicados. Similaridade não é prova de verdade.

## Caminho curto para retomar o trabalho

Leia esta página e a issue da sua etapa. Em seguida consulte apenas o contrato
necessário: [Dados](semana-1-dados.md),
[índice](semana-2-engenharia.md), [busca](semana-3-engenharia.md) ou
[OpenSpec](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/openspec/changes/add-recycled-claim-semantic-retrieval/tasks.md).
Registre na issue a versão da fonte, modelo, comandos, hashes, IDs testados,
resultado obtido, falhas e a decisão do papel responsável. Use a amostra de três
registros para conferir o caminho técnico antes de medir qualidade no corpus
real. Preserve índices e resultados anteriores ao repetir um experimento.

O código em `main` oferece uma demonstração fictícia e infraestrutura
experimental. A branch `feat/cobertura-dados` já foi incorporada a `main`;
`feat/testsmodelo` contém experimentos que precisam de revisão e integração
antes de virarem o modelo oficial. Nenhuma destas branches, sozinha, conclui o
gate ou o produto.
