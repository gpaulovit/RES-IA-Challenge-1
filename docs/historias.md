# Histórias de usuário

> **Reenquadramento (2026-10-06).** As histórias anteriores descreviam um buscador de checagens
> já existentes (US-03 a US-09 dependiam dele). O produto passou a ser um bot que estima a chance
> de uma notícia nova ser falsa a partir de padrões narrativos de boatos já checados (change
> [`add-fake-news-pattern-scoring`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-fake-news-pattern-scoring)).
> A versão anterior está no histórico do git. US-10 e o método de critérios foram mantidos.

O [protótipo de Engenharia](funcionalidades.md) ainda segue o contrato antigo de busca e não
conclui nenhuma história abaixo.

Cada história segue o padrão **quero** / **para que**: alguém quer fazer X, para conseguir Y.

No SDD deste projeto, “usuário” da história é quem **usa o software**. Isso não é a mesma coisa que o público que **sofre o problema** (por exemplo, pessoas 40+ que recebem e encaminham boato no WhatsApp). Quem cai no boato é o beneficiário; quem cola o texto e lê o resultado é o usuário. Os dois só coincidem se essa pessoa decidir conferir.

Nesta fase, as duas primeiras histórias são da equipe de pesquisa. As demais são de quem envia uma notícia ao bot para saber se ela se parece com boatos conhecidos.

Os critérios de aceitação são requisitos não funcionais: uma **métrica** com alvo numérico e uma **entrega** (relatório, conjunto de teste ou comportamento mensurável). Uma **classificação auxiliar** complementa a métrica para não virar um número cego.

Alvos numéricos desta página são **provisórios da fase de concepção**. Os que dependem do gate (US-01, US-03) seguem o critério pré-registrado do design da change (Decisão 4); a US-08 segue a Decisão 6. Os dois foram fixados antes de qualquer avaliação. A história só fecha com número publicado — não com impressão.

## Classificações auxiliares

| Classificação | Faixas |
|---|---|
| Decisão do gate | `go` / `no-go` / `inconclusivo` |
| Adequação da base | `suficiente` / `limitada` / `insuficiente` (por ano, classe e fonte) |
| Tipo de reescrita | `original` / `paráfrase` / `gíria ou apelido` / `erro proposital` / `negação` (esta à parte) |
| Faixa de resposta | `compatível com narrativas falsas` / `incerto` / `pouco compatível` / `fora dos padrões` |
| Completude da explicação | `completa` / `parcial` / `ausente` |
| Rótulo normalizado | `falsa` / `enganosa` / `verdadeira` / `inconclusiva` / `sem mapeamento` |

Termos usados nas métricas:

- **AUC:** probabilidade de o modelo dar score maior a uma notícia falsa do que a uma verdadeira, sorteadas ao acaso (0,5 = acaso; 1 = separação perfeita).
- **ECE (erro de calibração):** distância média entre o que o modelo diz (ex.: 80%) e a fração de falsas que acontece de fato entre os itens com aquele score.
- **Falso alarme:** notícia verdadeira colocada na faixa `compatível com narrativas falsas`.

---

## Pesquisa — sem isso, o resto não justifica o bot

### US-01 — A narrativa volta e serve para o futuro?

Como pesquisador(a), **quero** testar se um modelo treinado com boatos de um período separa falsas de verdadeiras num período posterior, **para que** só exponhamos o bot se o padrão narrativo se repetir de verdade.

**Critério de aceitação**

| | |
|---|---|
| Métrica | AUC no período de avaliação dos testes A (mesma fonte, ano seguinte) e B (outra fonte, anos depois), no geral e por fonte |
| Alvo | Definido no critério pré-registrado do design (Decisão 4). `go` só se A e B passarem; A passa e B não → `inconclusivo` |
| Entrega | Relatório do gate com as métricas, o modelo-controle e a decisão, escrito **antes** de qualquer score ser exposto |
| Classificação auxiliar | Decisão do gate |

### US-02 — A base é boa o bastante e não ensina atalho?

Como pesquisador(a), **quero** medir a cobertura da base por ano, classe e fonte, e quanto fonte e ano sozinhos predizem o rótulo, **para que** não confundamos estilo do veículo com padrão de boato.

**Critério de aceitação**

| | |
|---|---|
| Métrica | (a) itens por classe em cada conjunto de treino e avaliação; (b) AUC do modelo-controle que só vê fonte e ano; (c) % de títulos com carimbo de agência ("É #FAKE", "#boato") depois da limpeza |
| Alvo | (a) ≥ 300 itens por classe em cada conjunto de A e B (provisório); (b) relatado lado a lado com o modelo principal; (c) 0% |
| Entrega | Relatório de cobertura e auditoria de atalho, publicado junto com o gate |
| Classificação auxiliar | Adequação da base |

---

## O bot funcionando

### US-03 — Quanto isso se parece com boato?

Como quem envia uma notícia, **quero** receber uma estimativa da chance de ela ser falsa que signifique o que diz, **para que** um "80%" seja de fato 80%.

**Critério de aceitação**

| | |
|---|---|
| Métrica | ECE e Brier no período de avaliação, antes e depois da calibração |
| Alvo | Definido no critério pré-registrado (Decisão 4) |
| Entrega | Curva de calibração e tabela de métricas no relatório do gate |
| Classificação auxiliar | Faixa de resposta |

### US-04 — Não me assuste à toa

Como quem envia uma notícia verdadeira, **quero** que ela não seja apontada como parecida com boato, **para que** o bot não desacredite informação correta.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Taxa de falso alarme em notícias verdadeiras não vistas (período de avaliação e controles do g1) |
| Alvo | ≤ 5% (provisório) |
| Entrega | Matriz classe real × faixa atribuída, com os controles do g1 relatados à parte |
| Classificação auxiliar | Faixa de resposta |

### US-05 — Isso o modelo não conhece

Como quem envia uma notícia sobre algo que o modelo nunca viu, **quero** ouvir "fora dos padrões conhecidos", **para que** a falta de base não vire um score inventado.

**Critério de aceitação**

| | |
|---|---|
| Métrica | % de textos fora do domínio (notícias não políticas e de assuntos ausentes do treino) que caem em `fora dos padrões` |
| Alvo | ≥ 90% (provisório) |
| Entrega | Conjunto de textos fora do domínio + distribuição por faixa |
| Classificação auxiliar | Faixa de resposta |

### US-06 — Me mostra o porquê

Como quem envia uma notícia, **quero** ver as notícias já checadas mais parecidas com a minha, com fonte, data e o rótulo da agência, **para que** eu entenda de onde vem o score e vá à checagem original.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Completude da explicação: % de respostas cujos itens mostrados trazem texto, agência, data e rótulo |
| Alvo | 100% `completa`; 0% `ausente` |
| Entrega | Checagem automática de campos em todas as respostas do conjunto de avaliação |
| Classificação auxiliar | Completude da explicação |

---

## O bot não mentir nem simplificar demais

### US-07 — Não me dê um veredito

Como quem envia uma notícia, **quero** que o bot diga a semelhança com boatos conhecidos e não que a notícia "é falsa", **para que** eu não tome um score por checagem.

**Critério de aceitação**

| | |
|---|---|
| Métrica | (a) % de respostas que usam "falsa" ou "fake" como conclusão sobre a notícia; (b) % de respostas com o aviso de limitação e a indicação de agências |
| Alvo | (a) 0%; (b) 100% |
| Entrega | Textos das quatro faixas publicados + verificação automática em todas as respostas do conjunto de avaliação |
| Classificação auxiliar | Faixa de resposta |

### US-08 — Gíria não muda a resposta

Como quem envia uma notícia escrita do jeito que chegou no WhatsApp, **quero** a mesma faixa que a versão bem escrita receberia, **para que** a forma não decida mais do que o conteúdo.

**Critério de aceitação**

| | |
|---|---|
| Métrica | % de pares (original × reescrita) com a mesma faixa, por tipo de reescrita; negação relatada à parte |
| Alvo | ≥ 92% dos pares mantêm a faixa; abaixo de 85%, faixas ou modelo voltam para revisão (design, Decisão 6). No gate, o modelo já passou pelo critério de variação da probabilidade (Decisão 4) |
| Entrega | Tabela por tipo de reescrita com `experiments/results/teste_reescrita.csv`, sem a categoria negação, mais um relatório só da negação |
| Classificação auxiliar | Tipo de reescrita |

### US-09 — Não condenar quem é muito citado

Como quem envia uma notícia verdadeira sobre uma figura pública que concentra boatos, **quero** que ela não seja marcada só por mencionar essa pessoa, **para que** o bot não reproduza o viés da base.

**Critério de aceitação**

| | |
|---|---|
| Métrica | Taxa de falso alarme em notícias verdadeiras, por figura pública mencionada |
| Alvo | Nenhuma figura com falso alarme maior que o dobro da média (provisório); relatório publicado mesmo quando o alvo é atingido |
| Entrega | Tabela de falso alarme por entidade, com n de cada uma |
| Classificação auxiliar | Faixa de resposta |

### US-10 — Falar a mesma língua

Como pesquisador(a), **quero** os rótulos de todas as fontes traduzidos para uma lista única, **para que** o modelo não aprenda com rótulos que não são a mesma coisa.

**Critério de aceitação**

| | |
|---|---|
| Métrica | (a) cobertura do mapeamento; (b) acurácia amostral do mapeamento |
| Alvo | 100% dos rótulos de origem mapeados (nada usado em treino como `sem mapeamento`); acurácia ≥ 95% numa amostra revisada de pelo menos 100 registros |
| Entrega | Tabela curada rótulo-de-origem → rótulo normalizado + ata da amostragem, **antes** do treino |
| Classificação auxiliar | Rótulo normalizado |

---

## Em uma linha

| US | Quero | Para que | Métrica (alvo) |
|---|---|---|---|
| 01 | Testar se o padrão serve para o futuro | Só expor o bot se ele se repetir | AUC em A e B (pré-registro) → `go` / `no-go` |
| 02 | Medir cobertura e atalho | Não confundir veículo com boato | ≥ 300 por classe; controle relatado; 0% carimbo |
| 03 | Score que signifique o que diz | "80%" ser 80% | ECE e Brier (pré-registro) |
| 04 | Notícia verdadeira não ser apontada | Não desacreditar o que é correto | Falso alarme ≤ 5% |
| 05 | Ouvir "fora dos padrões" | Não inventar score | ≥ 90% fora do domínio em `fora dos padrões` |
| 06 | Ver as checagens mais parecidas | Entender o score | 100% explicação `completa` |
| 07 | Não receber veredito | Não tomar score por checagem | 0% "falsa/fake" como conclusão; 100% com aviso |
| 08 | Mesma faixa com gíria | A forma não decidir | ≥ 92% dos pares na mesma faixa; negação à parte |
| 09 | Não marcar quem é muito citado | Não reproduzir viés | Nenhuma figura > 2× a média de falso alarme |
| 10 | Unificar rótulos das fontes | Treinar com rótulos iguais | 100% mapeados; ≥ 95% corretos na amostra |

---

## Contabilidade SMART

Cada história foi checada nos cinco critérios. Onde o “prazo” não é uma data de calendário, o limite é a **fase de entrega** (gate, conjunto de teste ou antes do uso público).

| US | Specific | Measurable | Achievable | Relevant | Time-bound | Resultado |
|---|---|---|---|---|---|---|
| 01 | Testes A e B com treino e avaliação em anos diferentes | AUC por teste e por fonte; decisão do gate | As duas classes existem em 2016–2018 e 2020–2021 | Sem padrão que se repete, o bot não tem base | Relatório **antes** de expor score | Passa |
| 02 | Cobertura por ano, classe e fonte + atalho | Contagens, AUC do controle, % de carimbo | Os campos existem nas fontes | Atalho fabrica falso desempenho | Junto com o gate | Passa |
| 03 | Calibração no período de avaliação | ECE, Brier | Calibração por validação dentro do treino | Score sem calibração engana | Com o gate | Passa |
| 04 | Notícias verdadeiras não vistas | Taxa de falso alarme | Período de avaliação + 32 controles do g1 | Falso alarme é o pior erro | Antes de uso público | Passa, com **ressalva**: 2022 só tem os 32 controles |
| 05 | Textos fora do domínio | % em `fora dos padrões` | Conjunto fora do domínio pode ser montado agora | Sem isso, o bot inventa | Antes de uso público | Passa |
| 06 | Campos obrigatórios por item mostrado | % `completa` = 100 | Checagem automática de campos | Score sem explicação vira selo opaco | Em todas as respostas do conjunto de avaliação | Passa |
| 07 | Linguagem das faixas | 0% veredito; 100% aviso | Verificação automática de texto | Evita confundir score com checagem | Antes de uso público | Passa |
| 08 | Pares original × reescrita | Estabilidade por tipo | Conjunto de 534 consultas já existe | WhatsApp não escreve bem | Na avaliação do modelo escolhido | Passa |
| 09 | Verdadeiras por entidade | Falso alarme por entidade | Depende de n por entidade; entidades raras ficam como "n insuficiente" | Viés contra figuras muito citadas | Antes de uso público | Passa, com **ressalva** de n |
| 10 | Todas as fontes → taxonomia única | 100% mapeados; ≥ 95% na amostra ≥ 100 | Conjunto de rótulos é finito e curável à mão | Rótulos diferentes estragam o treino | **Antes** do treino | Passa |

Nenhuma história ficou só como desejo. Se o gate (US-01) der `no-go` ou `inconclusivo`, US-03 a US-09 não são entregues e o escopo volta a ser discutido, como está no `tasks.md` da change.
