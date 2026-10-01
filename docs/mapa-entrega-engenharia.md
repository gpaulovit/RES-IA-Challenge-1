# Mapa de verdade e plano de entrega

Este guia distingue **implementado**, **experimental** e **pendente**, para que
Dados, Produto, Modelos e Engenharia terminem o projeto sem refazer trabalho.
Para ver as cinco frentes e as entregas por semana, consulte o
[estado do projeto](estado_do_projeto.md). O
[guia de qualidade](guia_de_qualidade.md) explica os portões e a amostragem em
linguagem simples.
Conferido em 01/10/2026: `main` `d612370`, `feat/testsmodelo` `2981f5a`,
`feat/ci-mlops` `6d649f7` e `feat/benchmark-mlops` `4b4ea03`.

## O que de fato existe

| Peça | Já existe | Para declarar pronta |
| --- | --- | --- |
| Corpus | `src/checagens/organizacao.py` preserva linhas e relata lacunas. | Dados conferir 1.882 registros, datas e duplicatas e registrar aceite. Datas incertas ficam explícitas. |
| Vetores | `src/checagens/embeddings.py` gera índice, metadados e manifesto com hashes; há baseline por hashing e adaptador para outro modelo. | Modelos decidir candidato, versão e texto indexado. O manifesto marca o índice como experimental, não apto para produto. |
| Busca | `src/checagens/retrieval.py` faz k-NN exato por cosseno e confere hashes, alinhamento e modelo. | Medir paráfrases com IDs estáveis, aplicar política de decisão e integrar à API. `src/checagens/api.py` ainda usa exemplos fictícios com TF-IDF. |
| Benchmark | `data/testes_benchmark.json` tem 62 casos: 30 de referência e 32 controles externos. A branch `feat/benchmark-mlops` mede Recall e MRR. | Ligar referências a IDs do corpus, validar rótulos e separar calibração do teste final. Baseline documentado: Recall@5 de 60%, abaixo da meta de 70%; precisão de “confirmado” não medida. |
| CI | A branch `feat/ci-mlops` roda testes e busca em amostra fictícia. | Revisar/integrar a branch e criar portões reais para corpus, benchmark e controles. Não há prova de bloqueio da `main` por essas métricas. |
| Juiz | Existe o desenho de amostragem, severidade e feedback. | Não há Juiz LLM nem auto-calibração implementados nas branches examinadas. Fechar política, custo, privacidade e aprovação humana antes de codificar. |

O experimento de Modelos em `feat/testsmodelo` usa MiniLM; isso **não escolhe
BERTimbau nem outro modelo oficial**. A branch registra **NO-GO** para
recorrência dentro do mesmo ciclo eleitoral; o estudo entre ciclos continua.
Nela, cinco duplicatas são retiradas *apenas da análise experimental*
(1.882 → 1.877), sem autorização para apagar registros do corpus de
Engenharia. O DVC aponta para armazenamento local de uma pessoa, ainda não
reprodutível pelo grupo.

## Cinco guias de finalização

| Ordem | Issue | Entrada → saída | Regra de ouro | Pronta quando |
| --- | --- | --- | --- | --- |
| 1 | [#4 — corpus](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/4) | Fonte bruta → JSON e relatório | Preservar 1.882 registros; não adivinhar lacunas. | Contagem e hashes reproduzíveis, relatório revisado e aceite de Dados. |
| 2 | [#9 — vetores](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/9) | Corpus aprovado → vetores, metadados e manifesto | Um vetor corresponde a um registro e a uma versão de modelo. | Amostra 3→3 alinhada, hashes conferidos e candidato documentado por Modelos. |
| 3 | [#14 — busca](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/14) | Índice + consulta → Top-5 com fontes | Similaridade recupera candidatos; não prova veracidade. | Identidade, paráfrase e histórico medidos com IDs estáveis; modelo incompatível rejeitado. |
| 4 | [#19 — decisão](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/19) | Candidatos + scores → faixa | Zona cinza e notícia externa não viram confirmação automática. | Limites calibrados; precisão “confirmado” ≥90% e 32 controles testados um a um. |
| 5 | [#24 — evidências](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/24) | Busca + política → resposta | Não estender veredito a trecho novo; expor divergências. | Top-5 com fonte, data, agência e veredito; divergências e texto misto testados. |

Esses números são **metas**, não resultados. FactPolCheckBr tem 1.820 rótulos
`Falsa` em 1.882 registros (aprox. 96,7%): relatar métricas por classe e não
tratar score como probabilidade de falsidade. A fonte cobre agosto a dezembro
de 2022 e não contém pares reais separados por 180 dias. A meta histórica
precisa de fonte complementar aprovada ou revisão formal do requisito.

## Portões de qualidade: situação e contrato

O fluxo desejado é **dado → modelo → benchmark → integração**. Portão é um
teste com entrada, medida e critério publicados; ainda não se pode dizer que
a `main` está protegida pelos portões abaixo.

| Portão | Evidência para passar | Situação |
| --- | --- | --- |
| Dado | 1.882 registros preservados, relatório, versão da fonte e aceite de Dados | Conversor existe; aceite e teste com fonte real pendentes. |
| Desempenho | Recall@5 global ≥70%; histórico ≥60% com base válida; precisão “confirmado” ≥90%; denominadores públicos | Benchmark inicial em branch tem Recall@5 de 60%; precisão não medida. |
| Controle | Testar **todos** os 32 casos externos: score <0,60 e nenhum “confirmado”, segundo política a fechar | Casos existem; benchmark em branch registra scores, mas não impõe esse portão. |
| Regressão | Alinhamento, manifesto, API, evidências e segurança exercitados na CI | CI experimental cobre pytest e amostra fictícia, não o fluxo completo. |

Há um conflito: `docs/requisitos.md` permite até 5% de falsos positivos no
RNF-01, enquanto `docs/semana-1-produto.md` pede **todos** os 32 controles
abaixo de 0,60. Produto precisa escolher, justificar e versionar a regra.
Por enquanto, o critério mais protetivo é **meta de validação**, não resultado
observado nem limiar universal de confirmação. `docs/semana-3-produto.md`
está vazio na `main`, embora o commit anuncie relatório de aceite. O
ground truth inicial existe; faltam IDs, execução e aceite formal, não começar
do zero.

## Juiz de qualidade: desenho a validar

O caminho proposto é consulta → busca rápida → seleção para auditoria → Juiz
LLM → comparação com rótulo humano. O Juiz sugere revisão; ele não cria o
gabarito nem decide sozinho o que o produto publica.

1. Auditar todos os casos perto do limite. Definir se “±10%” quer dizer dez
   pontos de score ou 10% relativo ao limite; registrar a escolha.
2. Fora da zona cinza, sortear 2% dos *matches confirmados*, 1% dos casos
   rejeitados e 2–5% de base geral. Deduplicar sorteios e registrar população,
   tamanho, semente e custo. “Falsa” é veredito da checagem, não classe de
   correspondência: não misturar os dois.
3. Avaliar **100% dos 32 controles** no benchmark offline. Antes de enviar
   textos a serviço LLM externo, conferir licença, privacidade e custo.

| Erro | Significado | Peso de triagem |
| --- | --- | --- |
| Falso positivo | “Confirmado” para caso sem referência válida no corpus | 5 |
| Falso match | Há referência, mas foi apontado o registro errado | 3 |
| Falso negativo | Existia referência e o sistema não a recuperou/confirmou | 1 |
| Vazamento de controle | Controle externo com score ≥0,60 | 5 |

Pesos ordenam investigação; não substituem precisão, recall ou revisão
humana. Ao detectar erro, **propor** novo `τ` e repetir avaliação num conjunto
rotulado e congelado. Ajuste ±0,05, ampliação da zona cinza ou fine-tuning
são hipóteses, não mudanças automáticas em produção. Preservar versão anterior
e retorno; Dados, Produto e Modelos aprovam antes de Engenharia publicar.

## Próxima rodada, sem retrabalho

1. **Dados:** revisar corpus, alegação, duplicatas, datas e evidências; deixar
   aceite ou pendências na #4.
2. **Produto:** revisar os 62 casos e IDs esperados, resolver a regra dos 32
   controles e completar o relatório de aceite hoje vazio.
3. **Modelos:** publicar candidato, versão, benchmark reproduzível e leitura do
   NO-GO; não promover hashing ou MiniLM por inferência.
4. **Engenharia/MLOps:** integrar branches por revisão, ligar testes ao corpus
   e às métricas reais, e só então anunciar portões que barram regressões.

Ao fechar uma issue, anexar comando, versão de fonte e modelo, hashes, IDs
testados, denominador, resultado observado, falhas e quem aceitou. A amostra
de três registros verifica o encanamento; o aceite exige corpus e testes reais.
Preservar índices e resultados anteriores em novas execuções.
