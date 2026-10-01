# Guia de qualidade — como o trabalho passa para a versão final

**Situação em 01/10/2026:** este é o contrato de trabalho proposto para o grupo. Há testes, busca e benchmark em diferentes estados de maturidade, mas **não há Juiz LLM implementado nem prova de que a `main` seja bloqueada por todas as métricas abaixo**. O [estado do projeto](estado_do_projeto.md) mostra o que existe em cada frente.

## O caminho de uma mudança

Um *portão de qualidade* é uma pergunta objetiva, feita antes de aceitar uma etapa. Cada resposta precisa de entrada conhecida, regra, resultado medido e pessoa que aceitou. Essa rotina de casos, comandos, versões e resultados é o nosso *harness*: permite repetir a avaliação e descobrir onde uma mudança piorou a solução.

| Passagem | Entrada → transformação → saída | Dono e prova para seguir |
| --- | --- | --- |
| **1. Dado** | Fonte FactPolCheckBr → organizar sem esconder lacunas → corpus e relatório com 1.882 registros. | **Dados** aceita significado, cobertura, duplicatas e datas; **Engenharia** mostra contagem, versão, hash e comando de geração na [#4](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/4). |
| **2. Índice** | Corpus aceito + modelo escolhido → gerar vetores → índice, metadados e manifesto. | **Modelos** aprova candidato, versão e texto usado; **Engenharia** prova alinhamento 1 registro indexado ↔ 1 vetor, hashes e recusa de índice incompatível na [#9](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/9). A amostra de três registros valida o encanamento, não a qualidade final. |
| **3. Busca e benchmark** | Índice + consultas rotuladas → recuperar Top-5 → IDs, scores e medidas. | **Produto/Dados** validam referência esperada; **Modelos** interpreta erro; **DevOps/MLOps** publica execução reprodutível. **Engenharia** integra na [#14](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/14). Meta global: Recall@5 ≥70%. |
| **4. Decisão** | Candidatos + scores + política aprovada → `confirmado`, `provável`, `sem match` ou `inédito`. | **Produto e Modelos** aprovam faixas e revisão humana; **Engenharia** implementa na [#19](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/19). Meta de precisão de `confirmado` ≥90%, ainda não medida. |
| **5. Resposta e publicação** | Decisão + fontes → resposta com alegação, link, agência, data e veredito de cada fonte; lacunas permanecem explícitas. | **Produto** aceita clareza; **Engenharia** testa texto misto e divergências na [#24](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/24); **DevOps/MLOps** automatiza os casos aprovados e registra os checks. Revisão do grupo precede integração à `main`. |

Na issue ou no PR, anexar **comando, commit, fonte e versão do modelo, hashes, IDs testados, denominador, resultado observado, falhas e quem aceitou**. Congelar um conjunto de teste final diferente dos casos usados para escolher o limiar. Preservar o resultado e o índice anterior para comparar e voltar atrás. Um check verde sobre exemplos fictícios não é aprovação do corpus real.

## A regra dos “60%”: três coisas diferentes

| Número | O que significa | Situação |
| --- | --- | --- |
| `0,60` de similaridade | Corte **provisório** para examinar possível correspondência; score não mede a chance de uma notícia ser falsa. | Produto e Modelos precisam calibrar e aprovar. |
| Recall@5 histórico ≥60% | Meta para pares de alegações com intervalo ≥180 dias. | A fonte atual só cobre agosto–dezembro de 2022; não há base válida para medir essa meta. |
| Recall@5 global de 60% | Resultado inicial relatado para o benchmark em branch. | Está abaixo da meta global de ≥70%; não é aceite. |

Nos 32 controles externos, [RNF-01](requisitos.md) admite taxa de falso positivo ≤5%, enquanto o [registro de Produto](semana-1-produto.md) exige **todos** os controles com score `<0,60` e sem confirmação. “Score alto” e “confirmado errado” devem ser contados separadamente. Produto e Modelos precisam escolher e registrar a regra, denominador, versão e motivo; até lá, nenhum limiar pode ser anunciado como aprovado. Os **32 casos devem ser avaliados individualmente** em toda rodada final, mesmo se houver amostragem para auditoria de outros casos.

## Juiz de Qualidade: desenho de auditoria, ainda não automático

O fluxo proposto é **busca rápida → escolha de casos para auditoria → análise assistida → comparação com gabarito humano → revisão da política**. O Juiz pode apontar suspeitas. Quem define a alegação correta, o veredito e a publicação é a equipe, com Dados, Produto e Modelos conforme o tema. Não usar saída do Juiz como gabarito novo ou mudar o limiar automaticamente.

1. **Revisar todos os casos na zona cinzenta** em torno do corte. Antes de implementá-la, definir se “±10%” são dez pontos de score ou 10% relativos ao corte e registrar os limites exatos.
2. **Fora da zona cinzenta, sortear amostras propostas:** 2% dos matches confirmados, 1% dos rejeitados e 2–5% da base geral. Definir a janela, tamanho de cada população, regra de arredondamento e semente do sorteio. Deduplicar quem saiu em mais de um grupo e guardar IDs selecionados.
3. **Avaliar os 32 controles por inteiro**, além das amostras, e relatar score, decisão e erro de cada um. Separar erro de recuperar o registro errado, confirmar sem referência válida e deixar de recuperar referência existente.
4. **Investigar e decidir.** Guardar caso, fonte, versão, comentário humano e gravidade. Se for preciso trocar o corte ou o modelo, propor nova versão, testar em conjunto congelado e pedir aceite. Antes de usar serviço LLM externo, verificar licença dos textos, privacidade, custo e acesso.

Amostragem serve para descobrir falhas com custo controlado; não autoriza afirmar que todos os casos foram revisados. O conjunto final e seus denominadores mostram o desempenho observado. [Mapa técnico](mapa-entrega-engenharia.md) traz os pesos de triagem e as pendências já encontradas.

## Como retomar uma tarefa sem perder o contexto

Comece pelo [estado do projeto](estado_do_projeto.md), abra a **issue do seu papel** e leia apenas a entrada, a saída esperada, as decisões ainda abertas e a evidência mais recente. Execute o comando registrado com as mesmas versões; depois altere uma coisa por vez e compare o resultado. Se o contrato de outra frente estiver indefinido, registre o bloqueio na issue e peça a decisão ao dono indicado. Isso mantém o contexto curto e o histórico recuperável.

## Como apresentar ao grupo

> Para evitar que a IA confirme uma alegação sem base, vamos exigir dados aceitos, testes reproduzíveis e revisão dos casos duvidosos. O “Juiz” é uma proposta de auditoria; ainda precisamos aprovar sua regra e implementá-lo. Cada frente sabe qual prova entregar, e os 32 controles serão examinados um a um antes de chamar a solução de pronta.
