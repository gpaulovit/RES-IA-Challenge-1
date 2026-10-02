# Estado do projeto — mapa da verdade

**Fotografia em 01/10/2026.** Este quadro mostra o que foi encontrado no checkout local. A `main` local está em `d612370`; trabalho em branch ou PR ainda precisa de revisão e integração. Antes de anunciar uma entrega como concluída, confira o PR e a issue no GitHub, o teste e o aceite do papel responsável. O [cronograma](cronograma.md) organiza cinco semanas **por entregáveis**, sem datas de início e fim; por isso não atribuímos uma “semana atual” de calendário.

## Papel → entregue → falta

| Papel | O que já entregou ou registrou | O que falta para aceitar | Evidência e próxima decisão |
| --- | --- | --- | --- |
| **Domínio de dados** (`papel: dominio-dados`) | Análise de cobertura, vereditos, datas e limitações dos 1.882 registros. O conversor de Engenharia preserva os registros e relata lacunas. | Conferir alegações, duplicatas, datas e significado dos campos; aceitar o corpus e os rótulos usados no benchmark. | [Análise da semana 1](semana-1-dados.md), [#4](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/4). Dados registra aceite ou pendências na issue. |
| **Modelos de IA** (`papel: modelos-ia`) | Experimento em `feat/testsmodelo` com MiniLM e decisão **NO-GO** para recorrência no mesmo ciclo eleitoral. | Escolher e versionar modelo candidato, texto indexado e protocolo de avaliação; estudar recorrência entre ciclos. MiniLM e o baseline por hashing ainda não são modelo oficial. | Branch `feat/testsmodelo`, [#9](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/9) e [#14](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/14). Modelos publica a decisão e suas medidas. |
| **Produto e decisão** (`papel: produto-decisao`) | Requisitos, cenários e orientação para zonas cinzentas; conjunto inicial de 30 referências e 32 controles externos. | Validar casos e IDs esperados; decidir a política para controles, limiares, revisão humana e resposta ao usuário. O relatório `semana-3-produto.md` está vazio na `main` local. | [Requisitos](requisitos.md), [semana 1 de Produto](semana-1-produto.md), [#19](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/19) e [#24](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/24). Produto registra a regra aprovada. |
| **Engenharia** (`papel: engenharia`) | Na `main`, conversor, gerador de vetores com manifesto e hashes, e busca k-NN exata. Há API demonstrativa com três exemplos fictícios e TF-IDF. O mapa técnico está no [PR #29](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/29). | Ligar corpus e modelo aprovados à API, política de decisão, fontes e testes de ponta a ponta. Não apresentar o protótipo como produto validado. | [Mapa técnico](mapa-entrega-engenharia.md), [#4](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/4), [#9](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/9), [#14](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/14), [#19](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/19), [#24](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/24). Engenharia integra após os aceites. |
| **DevOps e MLOps** (`papel: devops-mlops`) | CI de testes e busca em amostra fictícia na branch `feat/ci-mlops` ([PR #30](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/30)); benchmark com Recall e MRR em `feat/benchmark-mlops` ([PR #31](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/31)). | Revisar os PRs, reproduzir ambiente e artefatos pelo grupo e ligar CI às medidas reais, controles, contrato da API e regras de aprovação. Não há prova de que as métricas protejam a `main`. | Branches e PRs citados. DevOps/MLOps mostra execução, logs, versões e critérios de bloqueio antes de chamar o gate de automático. |

O [cronograma](cronograma.md) associa nomes a quatro frentes e deixa o nome de Engenharia em branco. Não inferimos essa pessoa a partir de commits. Se alguma entrega ou responsável ficou de fora, atualizem o quadro com link para a evidência.

## Do início até esta fotografia

- **08/09:** início do repositório (`750ede6`); o cronograma de cinco semanas foi registrado depois, sem datas fixas para cada semana.
- **22–24/09:** demonstração fictícia, organização do corpus, vetores e busca exata chegaram à `main` em etapas. Isso não equivale à validação do produto real.
- **29/09:** cobertura de Dados entrou na `main` pelo [PR #26](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/26). O [PR #27](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/27) documenta arquitetura; o [PR #28](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/28) testa limites de entrada e avaliação da demonstração. Ambos seguem abertos.
- **01/10:** os PRs [#29](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/29) (mapa), [#30](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/30) (CI) e [#31](https://github.com/gpaulovit/RES-IA-Challenge-1/pull/31) (benchmark) seguem abertos. Branch pronta para revisão não significa entrega integrada ou aceita.

## Onde cada entrega está

| Marco do cronograma | Situação em 01/10/2026 | Próxima prova necessária |
| --- | --- | --- |
| **Semana 1 — problema e dados** | Estudo e relatório de cobertura documentados; conversão local dos 1.882 registros. | Aceite de Dados sobre conteúdo e lacunas; preservar versão e hash da fonte. |
| **Semana 2 — modelos e validação** | Pipeline de vetores na `main`; experimento de Modelos em branch, com NO-GO limitado ao mesmo ciclo. | Decisão documentada sobre modelo e escopo de recorrência. |
| **Semana 3 — busca** | Busca k-NN no código; benchmark inicial em branch. A API da `main` continua demonstrativa. | IDs de referência válidos, execução reprodutível, integração e relatório de resultados. |
| **Semana 4 — política e resposta** | Requisitos e desenho da decisão existem. | Produto aprovar limiares, controles, revisão humana e apresentação das fontes; implementar e medir. |
| **Semana 5 — integração e entrega** | Ainda não há evidência de aceite de ponta a ponta. | Cenários completos, CI com dados e métricas reais, documentação e revisão do grupo. |

Os cinco roteiros de Engenharia seguem a ordem **[#4 corpus](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/4) → [#9 vetores](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/9) → [#14 busca](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/14) → [#19 decisão](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/19) → [#24 resposta](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/24)**. Eles podem avançar em paralelo, mas a saída aceita de uma etapa é a entrada confiável da próxima. As issues já têm histórico e checklists: registrar novos resultados sem apagar progresso anterior.

## Pendências que impedem anunciar qualidade final

- **Base enviesada:** 1.820 dos 1.882 registros têm rótulo `Falsa` (aprox. 96,7%). Medir resultados por classe e para controles externos; score de similaridade não é probabilidade de falsidade.
- **Recorrência de 180 dias:** a fonte atual cobre agosto a dezembro de 2022 e não oferece pares reais com intervalo ≥180 dias. A meta histórica exige fonte complementar aceita ou revisão formal do requisito.
- **Três usos de 60%:** o corte de score `0,60` é provisório; Recall@5 histórico ≥60% é uma meta; Recall@5 global de 60% é resultado inicial registrado em branch, abaixo da meta global ≥70%. Nenhum deles substitui os outros.
- **Controles e decisão:** [RNF-01](requisitos.md) admite FPR ≤5%, mas [Produto na semana 1](semana-1-produto.md) pede os 32 controles abaixo de `0,60`. Produto e Modelos devem aprovar uma regra versionada antes de configurá-la como bloqueio na CI.
- **Juiz de Qualidade:** existe um desenho de auditoria, não um Juiz LLM nem ajuste automático de limiar em execução. Veja o [guia de qualidade](guia_de_qualidade.md).

## Como apresentar ao grupo

> Pessoal, organizei o que cada frente já entregou, o que está em branch e o que ainda precisa de aceite. Vejam se faltou alguma entrega de vocês e incluam o link para ela. Assim seguimos sem repetir trabalho nem chamar experimento de entrega final.
