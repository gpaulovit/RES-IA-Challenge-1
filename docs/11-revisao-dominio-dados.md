# Revisão de arquitetura da entrega de Domínio de Dados

O [PR #26 — cobertura dos dados](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/26) foi incorporado à `main` em 29/09/2026. Esta nota acompanha a entrega e indica as decisões que ainda faltam para usar o corpus em um produto. Ela não reabre a aprovação do PR nem atribui falhas que não apareceram no código.

## O que a entrega acrescentou

A frente de Dados mediu 1.882 checagens da campanha de 2022, organizou a contagem de vereditos e registrou limites de cobertura em [Semana 1 — Domínio de Dados](semana-1-dados.md). O comando `python -m checagens.cobertura` produz um relatório local; ele não treina um modelo e não muda os registros de origem.

Repeti a análise em 29/09/2026 com a cópia local da versão indicada pela fonte, sem gravar ou alterar o CSV: 1.882 registros, os quatro totais de veredito abaixo, 243 registros com um título parecido e os seis links com data divergente. O relatório distingue 11 nomes de agência; nove têm pelo menos 50 registros, como explica a entrega de Dados.

| Ponto levantado | O que foi conferido | Situação |
| --- | --- | --- |
| 1.820 falsos e 9 verdadeiros | Há ainda 3 parciais e 50 sem veredito. O acervo foi montado para checar boatos e cobre só agosto a dezembro de 2022. | **Risco de avaliação e cobertura confirmado.** |
| 50 sem veredito | O relatório transforma `None` em `sem_veredito` e há teste com esse caso. A busca experimental pode carregar o valor vazio como metadado; a API atual usa apenas exemplos fictícios validados. | **Falha por `NoneType` não demonstrada. Regra de uso futuro pendente.** |
| 738 datas ambíguas | O relatório usa mês/dia com evidência dos links: 256 de 262 links com data confirmam essa leitura; seis divergem e 476 não trazem data no link. O corpus mantém o valor original e a ambiguidade. | **Interpretação proposta para análise; seis casos precisam de revisão.** |
| Caminhos dos arquivos | Os scripts usam `Path("data/...")`, sem diretório particular de outro computador. | **Risco de caminho absoluto não encontrado.** Os comandos devem rodar na raiz do repositório. |

## 1. Como falar do desbalanceamento

Não é correto concluir que a busca atual “aprendeu que quase tudo é falso”: o TF-IDF e o índice experimental recuperam textos parecidos e **não são classificadores treinados com esses vereditos**. Ainda assim, entre as checagens disponíveis, cerca de 97% têm veredito `falso`. Uma consulta sobre uma notícia verdadeira pode receber um candidato falso sobre o mesmo assunto. A pontuação mede proximidade, não a chance de a consulta ser falsa.

Exemplo fictício: a base contém “A prefeitura proibiu carros no centro” com veredito histórico falso; a pessoa pergunta “A prefeitura não proibiu carros no centro”. Um buscador pode mostrar a checagem por causa das palavras em comum. Se a interface tratar o veredito antigo como resposta à nova frase, terá mudado o sentido da pergunta.

**Encaminhamento:** Produto e Modelos de IA devem reunir controles verdadeiros e negativos difíceis, com fonte e direito de uso registrados, para medir candidatos indevidos e calibrar uma futura regra de “sem correspondência”. Não acrescentar registros só para igualar números nem prometer que isso, por si só, melhora a busca. A [ADR-002](decisoes/ADR-002-busca-e-armazenamento.md) mantém a escolha do modelo dependente dessa avaliação.

## 2. O que fazer com vereditos e datas ausentes ou incertos

O relatório de cobertura aceita o veredito vazio de forma explícita. Isso **não significa** que uma resposta pública deva apresentar `null` sem explicação. Os 50 registros incluem, em sua maioria, matérias sobre várias alegações ou textos explicativos; um título pode não representar uma afirmação única. Antes da indexação real, Dados e Produto precisam decidir quais alegações podem ser separadas e revisadas. Até lá, marcar o registro como `revisar` ou `nao_indexavel`, preservando a checagem original. A [ADR-001](decisoes/ADR-001-texto-alegacao.md) já propõe esses estados.

As datas ambíguas também exigem cuidado: a leitura mês/dia é bem sustentada para a análise agregada, mas não transforma automaticamente cada data em fato confirmado. Os seis registros cujos links divergem devem continuar identificados e não servir como prova de recorrência temporal até revisão.

## 3. Como repetir em outro computador

Abra o terminal na raiz do repositório e siga a ordem indicada pela [entrega de Dados](semana-1-dados.md): inspeção, organização e cobertura. Os arquivos gerados ficam em `data/` e fora do Git. O caminho relativo funciona em outra máquina **quando o comando parte da raiz**; executá-lo de uma pasta diferente pode causar “arquivo não encontrado”. Se o projeto precisar rodar de qualquer diretório ou como serviço, Engenharia deverá tornar a localização dos arquivos configurável e testar esse modo de uso.

## Pendências para o grupo

| Decisão | Responsáveis | Evidência para fechar |
| --- | --- | --- |
| Quais textos representam alegações indexáveis, inclusive matérias com várias afirmações? | Dados + Produto | Amostra revisada, `claim_id`, origem e motivo de inclusão ou exclusão. |
| Como medir erros com notícias verdadeiras e alegações parecidas, mas diferentes? | Produto + Modelos de IA | Conjunto de controle rastreável e relatório de erros por categoria. |
| Quais datas podem sustentar uma alegação de recorrência? | Dados | Regra aprovada e revisão dos seis links divergentes. |
| O programa precisará executar fora da raiz do repositório? | Engenharia + operação | Requisito de execução e teste no ambiente escolhido. |

## Resumo da etapa

O colega mostrou onde a base é forte e onde ela é limitada. O código do relatório já lida com veredito vazio e usa caminhos portáveis a partir da raiz. O cuidado seguinte é impedir que um candidato parecido vire um veredito automático e decidir, com Dados e Produto, quais registros podem entrar na busca real.
