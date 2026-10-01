# PRs, issues e próximos passos

Este quadro ajuda o grupo a enxergar o que já foi entregue e o que ainda precisa acontecer. Um PR pode apoiar uma issue sem concluir todas as suas tarefas. Isso evita marcar uma entrega como pronta antes de haver evidência.

| Item | O que já existe | O que ainda falta | Onde acompanhar |
| --- | --- | --- | --- |
| Busca k-NN | A comparação exata e o índice experimental estão prontos. | Escolher um modelo com dados aprovados e passar os cenários reais. | Issue #14 |
| Pontos de corte | Há exemplos que mostram erros de busca por palavras. | Medir casos reais, controles verdadeiros e falsos candidatos. | Issue #18 |
| Política de decisão | A demonstração valida entradas, limita o texto e avisa que semelhança não é verdade. | Tratar alegação mista, divergência entre agências e explicar cada candidato. | Issue #19 |
| Política escrita | A arquitetura registra riscos, limites e evidências. | Unir os thresholds e os casos difíceis em uma política final. | Issue #20 |
| Banco vetorial | A medição atual indica que a busca exata atende ao tamanho conhecido do corpus. | Reavaliar se o volume, o tempo completo de resposta ou o uso simultâneo mostrarem necessidade. | ADR-002 |

## Como ler “adiado”

Adiar uma tecnologia não é esquecer uma tarefa. No caso do banco vetorial e do modelo semântico, o grupo precisa primeiro provar que a mudança melhora a busca e resolve um problema real. A escolha será revisada quando houver alegações aprovadas por Dados para entrar no índice, consultas reais com resposta esperada, medição repetível de acertos e erros, e uma meta clara de uso.

Exemplo fictício: se a consulta “a prefeitura não proibiu carros” recuperar a checagem “a prefeitura proibiu carros”, o sistema encontrou palavras parecidas, mas não uma resposta aplicável. Antes de definir uma faixa de confiança, o grupo precisa medir quantas vezes esse tipo de erro acontece.

## Relação com os PRs atuais

- O PR #27 apoia as issues #18 e #20: documenta as condições para decidir, mas não escolhe thresholds nem escreve a política final.
- O PR #28 apoia as issues #14 e #19: mede a demonstração e melhora entradas, mas não integra modelo aprovado nem trata os casos responsáveis da política.

As issues seguem abertas porque suas entregas principais ainda dependem de Dados, Modelos de IA, Produto e Engenharia. Cada comentário nas issues aponta a evidência já disponível e o próximo passo, sem mudar responsáveis ou prazos.

## Resumo da etapa

O repositório passa a mostrar com clareza a diferença entre uma base pronta, uma decisão em estudo e uma funcionalidade final. Assim, o grupo consegue avançar sem confundir testes de demonstração com entrega de produto.
