# Requisitos

Gerados via OpenSpec, na proposta de mudança
[`add-fake-news-pattern-scoring`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-fake-news-pattern-scoring).
Os requisitos abaixo ainda não estão implementados nem arquivados: os requisitos formais só
migram para `openspec/specs/` quando a implementação for concluída.

> **Reenquadramento (2026-10-06).** A versão anterior desta página descrevia um produto de
> recuperação da checagem já existente (change
> [`add-recycled-claim-semantic-retrieval`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-recycled-claim-semantic-retrieval),
> mantida como histórico dos gates). A equipe descartou essa ideia; a versão anterior desta
> página está no histórico do git.

Nenhum requisito desta página está implementado: o protótipo de busca anterior foi removido (tag
git `legado-busca`) e o gate temporal deu NO-GO na 1ª rodada (veja [Engenharia](engenharia.md)).

Esta página segue o fluxo da concepção do produto: **problema → objetivo de produto → objetivos
específicos → requisitos**. As perguntas que sustentam cada etapa estão em
[Perguntas](perguntas.md).

## 1. Problema

Quem recebe uma notícia política nova pelo WhatsApp não tem como saber, na hora, se ela se parece
com boatos que já circularam. A maior parte do que chega nunca foi checada, e a checagem humana
demora. Os gates do projeto mostraram que a mesma alegação raramente volta (1,4% dentro de um
ciclo; 1,6% entre ciclos), mas que a mesma **narrativa** volta com frequência: 62 de 71 pares
dentro de 2022 e 53 de 59 pares entre 2013–2021 e 2022 foram rotulados como mesma alegação ou
mesmo tema.

**Pergunta norteadora do problema:** o padrão semântico das notícias falsas sobre política no
Brasil se repete ao longo do tempo a ponto de um modelo treinado com boatos já checados de um
período estimar, com confiabilidade, a chance de uma notícia nova de um período posterior ser
falsa — sem que o que ele aprendeu seja só o veículo, a época ou o formato do texto?

## 2. Objetivo de produto

Construir um bot que estime, de forma calibrada e explicada, a chance de uma notícia política nova
ser falsa, a partir dos padrões narrativos de boatos já checados, apresentando o resultado em
faixas e nunca como veredito.

- **Capacidade:** `fake-news-pattern-scoring`.
- **Validação prévia obrigatória:** um gate de generalização temporal — o modelo treinado até um
  ano precisa separar falsas de verdadeiras em um período posterior, inclusive quando a fonte
  muda, com critério escrito antes de rodar. Sem passar no gate, nenhum score é exposto.
- **Fora de escopo deste change:** dizer se uma notícia é verdadeira ou falsa; verificação de
  fatos automatizada; indicadores de impacto social/comportamental pós-lançamento.

## 3. Objetivos específicos

Cada eixo de investigação da concepção se traduz em um objetivo específico, testável ainda nesta
fase.

### Eixo 1 — Dados e Contexto Eleitoral

**Objetivo específico:** montar uma base no recorte político com exemplos falsos (FactPolCheckBr,
Central de Fatos) e verdadeiros (Fake.br, FakeRecogna), com rótulos normalizados e carimbos de
agência removidos, e medir quanto do rótulo é explicado só pela fonte e pela época.

### Eixo 2 — IA e NLP

**Objetivo específico:** treinar um modelo sobre embeddings que estime de forma calibrada a chance
de uma notícia política ser falsa em um período posterior ao do treino, estável a reescritas de
superfície, e cujo desempenho não seja explicado pela fonte ou pela época.

### Eixo 3 — Decisão, Validação e Produto

**Objetivo específico:** definir faixas de resposta e uma linguagem que comuniquem a estimativa sem
afirmar veredito, com taxa de falso alarme sobre notícias verdadeiras dentro de uma margem
tolerável e com uma saída honesta ("fora dos padrões conhecidos") para o que o modelo não conhece.

### Eixo 4 — Impacto Social e Cidadania *(fora de escopo deste change)*

**Objetivo específico (reformulado):** projetar, com os dados e a literatura disponíveis nesta
fase, indicadores mensuráveis de impacto social (concentração temática de vulnerabilidade,
padrões por canal) que sirvam de baseline — deixando explícito que a validação causal do efeito
sobre o comportamento do eleitor depende de dados de uso pós-lançamento e não é resolvível na
etapa de concepção. Não gera requisitos nesta proposta.

## 4. Requisitos

Cada requisito abaixo realiza um dos objetivos específicos acima. O texto normativo, em inglês,
está no [spec da change](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-fake-news-pattern-scoring/specs/fake-news-pattern-scoring/spec.md).

### Gate de generalização temporal antes do produto

*Realiza o objetivo específico do Eixo 2.*

O sistema NÃO DEVE expor score a usuários sem que um modelo treinado só com itens até um ano de
corte tenha passado no critério pré-registrado de generalização, avaliado em itens posteriores a
esse ano. O critério (métricas e limites) DEVE ser registrado antes da avaliação.

- **Cenário — gate avaliado num período posterior**: quando o modelo é treinado até o ano de
  corte e avaliado depois dele, o resultado traz as métricas pré-registradas, no geral e por
  fonte, e registra `go` ou `no-go`.
- **Cenário — gate não aprovado**: quando o resultado é `no-go`, nenhum score aparece na
  interface e o motivo fica registrado.

### Estimar de forma calibrada a chance de ser falsa

*Realiza o objetivo específico do Eixo 2.*

O sistema DEVE devolver, para uma notícia enviada, uma estimativa da probabilidade de ela ser
falsa, calibrada: entre os itens com estimativa perto de p, a fração de falsos observada em dados
não vistos fica perto de p.

- **Cenário — score para texto válido**: quando alguém envia um texto não vazio, o sistema
  devolve uma estimativa entre 0 e 1 e a faixa correspondente.
- **Cenário — calibração medida, não presumida**: na avaliação, a calibração é relatada junto com
  a discriminação, e as faixas saem das estimativas calibradas.

### Apresentar em faixas, com estado "fora dos padrões"

*Realiza o objetivo específico do Eixo 3.*

O sistema DEVE apresentar a estimativa em uma de quatro faixas: compatível com narrativas falsas
conhecidas, incerto, pouco compatível ou fora dos padrões conhecidos. "Fora dos padrões" vale
quando o texto não se parece com nenhuma narrativa do treino, qualquer que seja a probabilidade.

- **Cenário — estimativa intermediária**: entre os limites inferior e superior, a resposta é
  "incerto" e não pende para falsa nem para verdadeira.
- **Cenário — texto longe de tudo o que o modelo conhece**: abaixo do limite de semelhança, a
  resposta é "fora dos padrões conhecidos" e diz que o modelo não tem base para avaliar.

### Nunca apresentar o resultado como veredito

*Realiza o objetivo específico do Eixo 3.*

O sistema NÃO DEVE afirmar nem sugerir que a notícia é verdadeira ou falsa. Toda resposta DEVE
dizer que o resultado mede semelhança com padrões de boatos já checados e DEVE indicar as fontes
de checagem para o veredito.

- **Cenário — estimativa alta**: na faixa "compatível com narrativas falsas conhecidas", a
  resposta diz que a notícia se parece com narrativas falsas já checadas, traz o aviso de
  limitação e não usa "falsa" ou "fake" como conclusão sobre a notícia.

### Explicar pelo que já foi checado

*Realiza o objetivo específico do Eixo 3.*

O sistema DEVE mostrar, com cada resultado, as notícias já checadas mais próximas do texto
enviado, cada uma com agência, data e o rótulo publicado pela agência.

- **Cenário — usuário vê por que recebeu o score**: com cada score vêm os itens checados mais
  próximos, com fonte, data e rótulo da agência.

### Manter a faixa sob reescrita de superfície

*Realiza o objetivo específico do Eixo 2.*

O sistema DEVE manter a faixa de uma notícia, dentro de uma tolerância registrada no design,
quando ela é reescrita por paráfrase, gíria, apelido ou erro de digitação proposital. A negação
NÃO é tratada como reescrita de superfície, porque pode inverter o sentido.

- **Cenário — reescrita com gíria e apelido**: a notícia e a reescrita recebem a mesma faixa em
  pelo menos a fração tolerada dos casos de teste.
- **Cenário — negação avaliada à parte**: a notícia e a versão negada são relatadas numa categoria
  separada, e mudança de faixa ali não conta como falha de robustez.

### Normalizar rótulos antes do treino

*Realiza o objetivo específico do Eixo 1 (pré-requisito de dado).*

O sistema DEVE mapear os rótulos de cada fonte para uma taxonomia única antes de qualquer uso em
treino ou avaliação, e DEVE excluir itens cujo rótulo não tenha mapeamento.

- **Cenário — rótulo sem mapeamento**: o item fica fora do treino e da avaliação e é contado no
  relatório de cobertura.

### Validar a entrada

*Realiza o objetivo específico do Eixo 3.*

O sistema DEVE recusar entrada vazia ou malformada com um erro explicativo, sem devolver score.

- **Cenário — texto vazio**: texto vazio ou só com espaços gera erro de validação e nenhum
  score.

## Fora de escopo

- Afirmar a verdade ou a falsidade de uma notícia; verificação de fatos automatizada.
- Indicadores de impacto social/comportamental pós-lançamento (concentração de vulnerabilidade,
  padrões por canal). Dependem de dado de uso real e ficam para um change futuro.
