# Guia simples para a arquiteta de software

Este guia ajuda a acompanhar as entregas de Engenharia das semanas 1 a 3.
Ele serve como roteiro de trabalho e de conversa com o grupo.

## 1. Qual é o objetivo do projeto

O projeto quer receber uma alegação política e procurar, em checagens já
publicadas, textos com o mesmo sentido. Assim, um boato antigo pode ser
encontrado mesmo quando volta escrito de outra forma.

A arquiteta de software ajuda as partes do projeto a se conectarem. Neste
projeto, isso significa combinar com o grupo:

- qual dado entra em cada etapa;
- qual resultado cada etapa deve entregar;
- como executar o processo novamente;
- como saber se a entrega funcionou;
- quais decisões e problemas ainda estão pendentes.

A arquiteta não precisa escolher sozinha o significado dos dados, o melhor
modelo de IA ou a forma final de apresentar o resultado. Essas decisões são
compartilhadas com as frentes responsáveis.

## 2. Como as partes se conectam

```text
Fonte → Corpus organizado → Embeddings → Índice → Busca → Resposta
```

| Parte | Explicação simples | Principal colaboração |
| --- | --- | --- |
| **Fonte** | O arquivo original do FactPolCheckBr, preservado como foi publicado. | Domínio de dados |
| **Corpus organizado** | Os mesmos registros em um formato previsível, com lacunas e ambiguidades visíveis. | Engenharia + Domínio de dados |
| **Embeddings** | Números que representam o sentido dos textos para permitir comparação. | Modelos de IA + Engenharia |
| **Índice** | Estrutura que guarda os vetores e a ligação com texto, veredito, agência e data. | Engenharia |
| **Busca** | Comparação da consulta com os itens do índice para encontrar os vizinhos mais próximos. | Engenharia + Modelos de IA |
| **Resposta** | Lista de candidatos e suas evidências para a pessoa avaliar. | Engenharia + Produto e decisão |

Cada seta é um acordo entre duas partes. Por exemplo, Engenharia precisa saber
quais campos Dados vai entregar antes de montar os embeddings. Também precisa
saber como o modelo recebe textos e devolve vetores antes de criar o índice.

## 3. Onde estamos agora

A inspeção encontrou os **1.882 registros** esperados. Data e agência estão
preenchidas, mas ainda existem problemas que precisam permanecer visíveis:

- 738 datas podem ser interpretadas de duas formas;
- 8 datas usam um formato diferente do informado pela fonte;
- 50 vereditos e 4 textos estão vazios;
- há possíveis registros duplicados;
- o título da checagem pode conter uma correção e não apenas a alegação original.

Por isso, a inspeção está concluída, mas o corpus ainda não está pronto para a
análise. O diagnóstico detalhado e os comandos de reprodução estão em
[Semana 1 — Engenharia](semana-1-engenharia.md).

## 4. Mapa das entregas de Engenharia

| Semana e issue | Entrega de Engenharia | Depende de | Critério simples de conclusão |
| --- | --- | --- | --- |
| [#4 — preparar corpus e ambiente](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/4) | Gerar o corpus organizado, manter os sete campos originais, produzir relatório de lacunas e documentar o ambiente. | Dados confirmar o significado e o tratamento dos campos problemáticos. | Conversão repetível com 1.882 registros, integridade conferida e pendências registradas e aceitas pelo grupo. |
| [#9 — pipeline de embeddings e indexação](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/9) | Transformar o corpus em vetores e manter cada vetor ligado aos metadados da checagem. | Corpus da #4 e modelos candidatos definidos pela [#8](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/8). | O mesmo pipeline executa com os modelos comparados e mantém texto, veredito, agência e data rastreáveis. |
| [#14 — indexação e busca k-NN](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/14) | Indexar o corpus com o modelo escolhido e buscar os vizinhos mais próximos. | Gate favorável, modelo selecionado, revisão de Dados na [#11](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/11) e cenários de Produto na [#15](https://github.com/gpaulovit/RES-IA-Challenge-1/issues/15). | Uma alegação indexada é recuperada e uma versão reescrita aparece entre os primeiros resultados. |

A #9 pode preparar a estrutura com modelos candidatos. A #14 usa o modelo
selecionado depois do gate. Se o gate resultar em `no-go`, o grupo deve rever o
escopo antes de construir a busca real.

## 5. Responsabilidades e dependências

| Frente | O que Engenharia precisa receber | O que Engenharia devolve |
| --- | --- | --- |
| **Domínio de dados** | Significado dos campos, tratamento de datas, vazios, duplicações e texto da alegação. | Corpus organizado, relatório de lacunas e regras aplicadas na conversão. |
| **Modelos de IA** | Lista de modelos candidatos, modo de carregamento e modelo escolhido no gate. | Pipeline comum para gerar vetores e resultado técnico da integração. |
| **Produto e decisão** | Cenários que precisam funcionar e campos que devem aparecer na resposta. | Fluxo demonstrável, limites conhecidos e evidências disponíveis na busca. |
| **DevOps e MLOps** | Forma de instalar, executar e automatizar o ambiente. | Dependências, comandos e artefatos que precisam ser reproduzidos. |

Um bloqueio deve ser escrito de forma objetiva: **o que falta, quem pode
resolver, qual entrega está parada e até quando a resposta é necessária**.

Exemplo:

> Falta definir se o título pode representar a alegação. Domínio de dados e
> Produto precisam decidir antes de gerar os embeddings da #9.

## 6. Perguntas para levar ao grupo

### Sobre os dados

- Quem valida e aceita o corpus organizado da #4?
- Qual campo representa a alegação que será comparada na busca?
- Como devemos marcar datas ambíguas, textos vazios e vereditos ausentes?
- Os possíveis duplicados serão mantidos, agrupados ou removidos? Qual evidência
  sustenta essa decisão?

### Sobre modelos e avaliação

- Quais modelos serão testados na #8 e como Engenharia deve chamá-los?
- Quem registra a decisão `go` ou `no-go` do gate e onde ela será publicada?
- Como os casos do conjunto de teste da #10 apontam para os registros corretos
  do corpus?
- Qual resultado mínimo o grupo aceita para escolher o modelo?

### Sobre ambiente e demonstração

- Quem apoia a instalação e a execução reproduzível do ambiente?
- Onde os vetores e os metadados serão armazenados durante o projeto?
- Qual consulta será usada na demonstração da Semana 3?
- Quem confirma que a resposta contém as evidências necessárias?

## 7. Roteiro de trabalho por semana

### Semana 1 — issue #4

1. Repetir a inspeção e confirmar a versão e a integridade da fonte.
2. Organizar os 1.882 registros sem esconder valores originais ou pendências.
3. Gerar e revisar o relatório de lacunas.
4. Pedir à frente de Dados a decisão sobre os campos problemáticos.
5. Registrar na issue o comando usado, os resultados e o que ainda depende do grupo.

### Semana 2 — issue #9

1. Receber o corpus aceito e os modelos candidatos.
2. Definir uma entrada comum de texto e uma saída comum de vetores.
3. Ligar cada vetor aos metadados do registro de origem.
4. Executar o pipeline com os modelos usados na comparação.
5. Registrar diferenças, erros, tempo de execução e dependências para o gate.

### Semana 3 — issue #14

1. Confirmar que o gate foi favorável e identificar o modelo escolhido.
2. Gerar o índice real do corpus.
3. Implementar a busca exata dos vizinhos mais próximos.
4. Conferir os dois cenários mínimos do OpenSpec.
5. Preparar uma demonstração curta do caminho consulta → candidatos → evidências.

## 8. Roteiro para a reunião semanal

Use este roteiro e registre as respostas na issue correspondente:

1. **Entrega:** o que precisa estar pronto até o fim da semana?
2. **Evidência:** qual comando, arquivo ou demonstração comprova a entrega?
3. **Entradas:** o que preciso receber de cada frente e em qual formato?
4. **Responsáveis:** quem entrega ou decide cada item?
5. **Bloqueios:** o que está impedindo o avanço e qual é a data necessária?
6. **Decisões:** o que foi combinado e onde ficará registrado?
7. **Próximo passo:** qual é a menor atividade que pode começar agora?

Modelo de anotação:

```text
Entrega da semana:
Issue:
Responsável:
Entradas necessárias:
Decisões tomadas:
Como executar e conferir:
Bloqueios, responsável e prazo:
Próximo passo:
```

## 9. O que estudar primeiro

Não é necessário estudar arquitetura inteira antes de trabalhar. Comece pelos
conceitos que aparecem na entrega atual:

1. **Pipeline de dados:** entrada, transformação, saída e validação.
2. **Contrato entre partes:** formato que uma etapa entrega para a próxima.
3. **Reprodutibilidade:** outra pessoa executa os mesmos comandos e obtém o
   mesmo resultado.
4. **Embeddings e similaridade:** representação numérica e comparação de textos.
5. **k-NN e top-k:** busca dos itens mais próximos e quantidade de resultados.

O [Glossário](glossario.md) explica os termos do projeto. A
[Organização da Engenharia](engenharia.md) mostra a estrutura do protótipo atual.

## Resumo

A prioridade imediata é concluir a #4 com os dados preservados, lacunas visíveis
e decisões aceitas pelo grupo. Depois, a #9 prepara os vetores com os modelos
candidatos. A #14 somente cria a busca real após o gate e a escolha do modelo.
Em todas as semanas, o trabalho da arquiteta é manter claras as entradas, saídas,
dependências, evidências e decisões.
