# Especificação de Requisitos do Sistema (RES-IA-Challenge-1)

Gerados via OpenSpec, na proposta de mudança
[`add-fake-news-pattern-scoring`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-fake-news-pattern-scoring).
Os requisitos abaixo ainda não estão implementados nem arquivados: os requisitos formais só
migram para `openspec/specs/` quando a implementação for concluída.

> **Reenquadramento (2026-10-06).** A versão anterior desta página descrevia um produto de
> recuperação da checagem já existente (change
> [`add-recycled-claim-semantic-retrieval`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-recycled-claim-semantic-retrieval),
> mantida como histórico dos gates). A equipe descartou essa ideia; a versão anterior desta
> página está no histórico do git.

O [protótipo de Engenharia](funcionalidades.md) com três exemplos fictícios ainda segue o contrato
antigo de busca e não conclui nenhum requisito desta página.

Esta página segue a hierarquia dos tipos de requisito: o **requisito de negócio** alimenta os
**requisitos de usuário** ([histórias](historias.md)), que alimentam os **requisitos funcionais**.
**Regras de negócio**, **atributos de qualidade**, **interfaces externas** e **restrições** também
moldam os requisitos funcionais. As perguntas que sustentam cada etapa estão em
[Perguntas](perguntas.md).

| Seção | Tipo de requisito | Código |
|---|---|---|
| 1. Problema | contexto | — |
| 2. Requisito de negócio | objetivo de negócio de alto nível | — |
| 3. Objetivos específicos | desdobramento por eixo | — |
| 4. Regras de negócio | política que restringe o produto | RN |
| 5. Requisitos de usuário | o que cada classe de usuário precisa fazer | US (em [histórias](historias.md)) |
| 6. Requisitos funcionais | comportamento do sistema sob condições específicas | RF |
| 7. Requisitos não funcionais | atributos de qualidade, interface externa, restrições e operação de ML | RNF, IE |
| 8. Priorização e rastreabilidade | MoSCoW e ligação entre requisitos, histórias e frentes | — |
| 9. Gestão de requisitos | como os requisitos mudam | — |

A prioridade segue o método **MoSCoW**: *Must* (essencial), *Should* (importante, só sai com
justificativa), *Could* (desejável se houver tempo) e *Won't* (fora do escopo desta fase).

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

## 2. Requisito de negócio (objetivo de produto)

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

## 4. Regras de negócio

Políticas que valem para qualquer versão do produto e limitam o que os requisitos funcionais podem
fazer.

* **RN-01 (Sem gate, sem score):** nenhuma estimativa é mostrada a usuários enquanto o gate de generalização temporal não tiver resultado `go`.
* **RN-02 (Critério antes do resultado):** os limites do gate são registrados e commitados antes de qualquer avaliação nos períodos de teste. Um limite alterado depois de ver resultados invalida o gate.
* **RN-03 (Escopo rediscutido em caso de falha):** se o gate der `no-go` ou `inconclusivo`, a construção do produto para e o escopo volta a ser discutido antes de seguir.
* **RN-04 (O bot nunca dá veredito):** o veredito sobre uma notícia é sempre da agência de checagem. O produto informa semelhança com narrativas já checadas e aponta para as agências.
* **RN-05 (Uso não comercial):** o uso é não comercial, condição herdada do FactPolCheckBr (CC BY-NC-SA 4.0). As licenças de Fake.br, FakeRecogna e Central de Fatos são conferidas antes do deploy.

## 5. Requisitos de usuário

Os requisitos de usuário estão escritos como histórias (*como … quero … para que …*) em
[Histórias de usuário](historias.md), com critério de aceitação mensurável. Há duas classes de
usuário: **pesquisador(a)** da equipe (US-01, US-02, US-10) e **quem envia uma notícia** ao bot
(US-03 a US-09). Quem recebe e compartilha boatos no WhatsApp é **usuário indireto**: é
beneficiado pelo resultado mesmo sem usar o sistema.

## 6. Requisitos funcionais

Cada requisito abaixo realiza um dos objetivos específicos acima e traz código, histórias de
origem e prioridade. O texto normativo, em inglês,
está no [spec da change](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-fake-news-pattern-scoring/specs/fake-news-pattern-scoring/spec.md).

### RF-01 — Gate de generalização temporal antes do produto

*Realiza o objetivo específico do Eixo 2 · Histórias: US-01, US-02 · Prioridade: **Must**.*

O sistema NÃO DEVE expor score a usuários sem que um modelo treinado só com itens até um ano de
corte tenha passado no critério pré-registrado de generalização, avaliado em itens posteriores a
esse ano. O critério (métricas e limites) DEVE ser registrado antes da avaliação.

- **Cenário — gate avaliado num período posterior**: quando o modelo é treinado até o ano de
  corte e avaliado depois dele, o resultado traz as métricas pré-registradas, no geral e por
  fonte, e registra `go` ou `no-go`.
- **Cenário — gate não aprovado**: quando o resultado é `no-go`, nenhum score aparece na
  interface e o motivo fica registrado.

### RF-02 — Estimar de forma calibrada a chance de ser falsa

*Realiza o objetivo específico do Eixo 2 · Histórias: US-03 · Prioridade: **Must**.*

O sistema DEVE devolver, para uma notícia enviada, uma estimativa da probabilidade de ela ser
falsa, calibrada: entre os itens com estimativa perto de p, a fração de falsos observada em dados
não vistos fica perto de p.

- **Cenário — score para texto válido**: quando alguém envia um texto não vazio, o sistema
  devolve uma estimativa entre 0 e 1 e a faixa correspondente.
- **Cenário — calibração medida, não presumida**: na avaliação, a calibração é relatada junto com
  a discriminação, e as faixas saem das estimativas calibradas.

### RF-03 — Apresentar em faixas, com estado "fora dos padrões"

*Realiza o objetivo específico do Eixo 3 · Histórias: US-04, US-05 · Prioridade: **Must**.*

O sistema DEVE apresentar a estimativa em uma de quatro faixas: compatível com narrativas falsas
conhecidas, incerto, pouco compatível ou fora dos padrões conhecidos. "Fora dos padrões" vale
quando o texto não se parece com nenhuma narrativa do treino, qualquer que seja a probabilidade.

- **Cenário — estimativa intermediária**: entre os limites inferior e superior, a resposta é
  "incerto" e não pende para falsa nem para verdadeira.
- **Cenário — texto longe de tudo o que o modelo conhece**: abaixo do limite de semelhança, a
  resposta é "fora dos padrões conhecidos" e diz que o modelo não tem base para avaliar.

### RF-04 — Nunca apresentar o resultado como veredito

*Realiza o objetivo específico do Eixo 3 · Histórias: US-07 · Prioridade: **Must**.*

O sistema NÃO DEVE afirmar nem sugerir que a notícia é verdadeira ou falsa. Toda resposta DEVE
dizer que o resultado mede semelhança com padrões de boatos já checados e DEVE indicar as fontes
de checagem para o veredito.

- **Cenário — estimativa alta**: na faixa "compatível com narrativas falsas conhecidas", a
  resposta diz que a notícia se parece com narrativas falsas já checadas, traz o aviso de
  limitação e não usa "falsa" ou "fake" como conclusão sobre a notícia.

### RF-05 — Explicar pelo que já foi checado

*Realiza o objetivo específico do Eixo 3 · Histórias: US-06 · Prioridade: **Must**.*

O sistema DEVE mostrar, com cada resultado, as notícias já checadas mais próximas do texto
enviado, cada uma com agência, data e o rótulo publicado pela agência.

- **Cenário — usuário vê por que recebeu o score**: com cada score vêm os itens checados mais
  próximos, com fonte, data e rótulo da agência.

### RF-06 — Manter a faixa sob reescrita de superfície

*Realiza o objetivo específico do Eixo 2 · Histórias: US-08 · Prioridade: **Must**.*

O sistema DEVE manter a faixa de uma notícia, dentro de uma tolerância registrada no design,
quando ela é reescrita por paráfrase, gíria, apelido ou erro de digitação proposital. A negação
NÃO é tratada como reescrita de superfície, porque pode inverter o sentido.

- **Cenário — reescrita com gíria e apelido**: a notícia e a reescrita recebem a mesma faixa em
  pelo menos a fração tolerada dos casos de teste.
- **Cenário — negação avaliada à parte**: a notícia e a versão negada são relatadas numa categoria
  separada, e mudança de faixa ali não conta como falha de robustez.

### RF-07 — Normalizar rótulos antes do treino

*Realiza o objetivo específico do Eixo 1 (pré-requisito de dado) · Histórias: US-10 · Prioridade: **Must**.*

O sistema DEVE mapear os rótulos de cada fonte para uma taxonomia única antes de qualquer uso em
treino ou avaliação, e DEVE excluir itens cujo rótulo não tenha mapeamento.

- **Cenário — rótulo sem mapeamento**: o item fica fora do treino e da avaliação e é contado no
  relatório de cobertura.

### RF-08 — Validar a entrada

*Realiza o objetivo específico do Eixo 3 · Histórias: — · Prioridade: **Must**.*

O sistema DEVE recusar entrada vazia ou malformada com um erro explicativo, sem devolver score.

- **Cenário — texto vazio**: texto vazio ou só com espaços gera erro de validação e nenhum
  score.

## 7. Requisitos não funcionais

Os RNF dão número aos alvos de qualidade das [histórias de usuário](historias.md). Os limites
do gate (RNF-01 a RNF-04 e a primeira parte do RNF-05) vêm do critério pré-registrado no
[design da change](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-fake-news-pattern-scoring/design.md)
(Decisão 4). Se houver divergência, vale o design. Os alvos marcados como *provisório* ainda
podem mudar na concepção. Todos os outros valem antes do uso público.

### 7.1 Atributos de qualidade do modelo (gate de generalização temporal)

* **RNF-01 (Generalização temporal):** o modelo deve separar falsas de verdadeiras em um período posterior ao do treino, com AUC-ROC ≥ 0,85 no teste A (mesma fonte, ano seguinte) e ≥ 0,80 no teste B (outra fonte, anos depois). AUC < 0,75 em qualquer um dos dois é `no-go`. *(Vinculado a **US-01**)*
* **RNF-02 (Calibração):** no período de avaliação, a estimativa deve ter ECE ≤ 0,05 (10 faixas) e Brier skill score > 0 em relação a prever a proporção de falsas. *(Vinculado a **US-03**)*
* **RNF-03 (Ganho sobre linha de base léxica):** a AUC do modelo deve superar em pelo menos +0,05 a de TF-IDF + regressão logística treinada com a mesma separação temporal. *(Vinculado a **US-01**)*
* **RNF-04 (Ausência de atalho):** a AUC do modelo deve superar em pelo menos +0,10 a do modelo-controle que só vê fonte e ano. Depois da limpeza, 0% dos títulos podem manter carimbo de agência ("É #FAKE", "#boato", "Boato –"). Cada conjunto de treino e avaliação dos testes A e B deve ter ≥ 300 itens por classe *(provisório)*. *(Vinculado a **US-02**)*

### 7.2 Atributos de qualidade do produto

* **RNF-05 (Robustez a reescrita de superfície):** no gate, a variação da probabilidade entre a notícia e a reescrita (gíria, apelido, erro proposital) deve ter média ≤ 0,10, com no máximo 5% dos pares acima de 0,25. Depois de definidas as faixas, ≥ 92% dos pares devem manter a faixa. Abaixo de 85%, as faixas ou o modelo voltam para revisão. A negação é relatada à parte e não entra nesses números. *(Vinculado a **US-08**)*
* **RNF-06 (Falso alarme):** no máximo 5% das notícias verdadeiras não vistas podem cair na faixa "compatível com narrativas falsas" *(provisório)*. Os 32 controles do g1 de 2022 são relatados à parte, com o n e o intervalo de confiança. *(Vinculado a **US-04**)*
* **RNF-07 (Fora do domínio):** ≥ 90% dos textos fora do domínio (não políticos ou de assuntos ausentes do treino) devem cair em "fora dos padrões conhecidos" *(provisório)*. *(Vinculado a **US-05**)*
* **RNF-08 (Viés por figura pública):** nenhuma figura pública mencionada pode ter taxa de falso alarme maior que o dobro da média *(provisório)*. O relatório por entidade, com o n de cada uma, é publicado mesmo quando o alvo é atingido. *(Vinculado a **US-09**)*
* **RNF-09 (Completude da explicação):** 100% dos itens mostrados como explicação devem trazer texto, agência, data e rótulo publicado pela agência. *(Vinculado a **US-06**)*
* **RNF-10 (Linguagem sem veredito):** 0% das respostas podem usar "falsa" ou "fake" como conclusão sobre a notícia, e 100% devem trazer o aviso de limitação e a indicação de agências de checagem. *(Vinculado a **US-07**)*
* **RNF-11 (Cobertura dos rótulos):** 100% dos rótulos de origem usados em treino ou avaliação devem estar mapeados para a taxonomia única, com acurácia ≥ 95% numa amostra revisada de pelo menos 100 registros, antes do treino. *(Vinculado a **US-10**)*
* **RNF-12 (Tempo de resposta):** o score, a faixa e os itens da explicação devem voltar em menos de 2 segundos por consulta *(provisório)*. *(Vinculado a **US-03, US-06**)*

### 7.3 Interface externa

* **IE-01 (API de score):** o sistema expõe uma API REST que recebe o texto de uma notícia e devolve a faixa, a estimativa, os itens da explicação e o aviso de limitação. Ela substitui o contrato `POST /buscar` do protótipo e só é publicada depois do `go` (RN-01). Entrada inválida gera erro HTTP 422 com mensagem explicativa (RF-08). *(Vinculado a **US-03, US-06, US-07**)*
* **IE-02 (Bot do Telegram):** quem usa o produto envia o texto da notícia a um bot do Telegram, criado pelo @BotFather, e recebe na conversa a faixa, os itens da explicação com o link de cada checagem e o aviso de limitação. O bot é um cliente da API de score (IE-01) e não tem lógica de decisão própria. Mensagens sem texto (foto, áudio, figurinha) recebem uma orientação para enviar o texto. *(Vinculado a **US-03, US-06, US-07**)*

### 7.4 Restrições

* **RNF-13 (Arquitetura simplificada em memória):** a busca dos itens da explicação usa k-NN exato em memória, sem banco vetorial dedicado, enquanto o volume do corpus permitir. *(Vinculado a **US-06**)*
* **RNF-14 (Privacidade):** o sistema não deve armazenar nem persistir dados pessoais identificáveis presentes nas notícias enviadas pelos usuários. Os registros de uso (RNF-17 e RNF-19) guardam só metadados. No bot do Telegram, o identificador do usuário e do chat não é persistido. *(Vinculado a **US-03**)*
* **RNF-22 (Segredo do bot):** o token do bot do Telegram fica fora do repositório (variável de ambiente ou cofre de segredos) e é trocado pelo @BotFather se for exposto. *(Vinculado a **US-03**)*

### 7.5 Operação de ML (MLOps)

Requisitos derivados dos princípios de MLOps de Kreuzberger, Kühl e Hirschl (2023), *Machine
Learning Operations (MLOps): Overview, Definition, and Architecture* (P1 a P9). Eles garantem
que o resultado do gate possa ser refeito, auditado e mantido depois da entrega.

* **RNF-15 (Versionamento — P4):** dados, código e modelo são versionados: o código no Git, os dados e os conjuntos dos testes A, B e C no DVC, com hash registrado em `experiments/README.md`, e cada modelo treinado com identificador de versão. *(Vinculado a **US-01, US-02**)*
* **RNF-16 (Reprodutibilidade — P3):** qualquer pessoa da equipe deve conseguir refazer o gate e obter os mesmos números, a partir de um remote DVC compartilhado e das versões fixadas em `experiments/requirements.txt`. *(Vinculado a **US-01**)*
* **RNF-17 (Rastreamento de metadados — P7):** cada execução de treino ou avaliação registra a versão do modelo de embeddings, o hash dos dados, os parâmetros, as métricas e a data. Cada resposta da API registra a versão do modelo que a gerou, sem o texto enviado (RNF-14). *(Vinculado a **US-01, US-03**)*
* **RNF-18 (Integração contínua — P1):** os testes automatizados (`pytest`) rodam a cada pull request, incluindo as verificações de validação de entrada (RF-08), de completude da explicação (RNF-09) e de linguagem sem veredito (RNF-10). *(Vinculado a **US-06, US-07**)*
* **RNF-19 (Monitoramento contínuo — P8):** depois do uso público, a distribuição das faixas e a fração de respostas "fora dos padrões" são acompanhadas ao longo do tempo. Uma mudança acima do limite definido antes do lançamento dispara revisão do modelo, porque a hipótese central do produto é que o padrão se mantém no tempo. *(Vinculado a **US-01, US-05**)*
* **RNF-20 (Treino e avaliação contínuos — P6):** um novo modelo só substitui o atual se passar nos mesmos critérios do gate (RNF-01 a RNF-05), avaliado num período posterior ao do seu treino. *(Vinculado a **US-01**)*
* **RNF-21 (Ciclo de feedback — P9):** usuários e agências podem contestar um resultado. Os casos contestados são revisados e entram no conjunto de avaliação seguinte. *(Vinculado a **US-04, US-09**)*

## 8. Priorização e rastreabilidade

A prioridade MoSCoW abaixo é a proposta de Produto para esta fase. A frente responsável segue os
papéis do [cronograma](cronograma.md), alinhados aos papéis de MLOps do artigo citado em 7.5
(Produto ≈ *business stakeholder*, Modelos ≈ *data scientist*, Dados ≈ *data engineer*,
Engenharia ≈ *software engineer*, DevOps e MLOps ≈ *DevOps / ML engineer*).

| Código | Requisito | Tipo | Histórias | Prioridade | Frente |
|---|---|---|---|---|---|
| RN-01 a RN-05 | Regras de negócio | Regra de negócio | — | Must | Produto |
| RF-01 | Gate antes do produto | Funcional | US-01, US-02 | Must | Modelos |
| RF-02 | Estimativa calibrada | Funcional | US-03 | Must | Modelos |
| RF-03 | Faixas e "fora dos padrões" | Funcional | US-04, US-05 | Must | Produto + Modelos |
| RF-04 | Nunca dar veredito | Funcional | US-07 | Must | Produto |
| RF-05 | Explicação por itens checados | Funcional | US-06 | Must | Engenharia |
| RF-06 | Faixa estável sob reescrita | Funcional | US-08 | Must | Modelos |
| RF-07 | Normalização de rótulos | Funcional | US-10 | Must | Dados |
| RF-08 | Validação da entrada | Funcional | — | Must | Engenharia |
| RNF-01 a RNF-04 | Qualidade do modelo (gate) | Atributo de qualidade | US-01 a US-03 | Must | Modelos |
| RNF-05 | Robustez a reescrita | Atributo de qualidade | US-08 | Must | Modelos |
| RNF-06 | Falso alarme | Atributo de qualidade | US-04 | Must | Produto + Modelos |
| RNF-07 | Fora do domínio | Atributo de qualidade | US-05 | Should | Modelos |
| RNF-08 | Viés por figura pública | Atributo de qualidade | US-09 | Should | Produto + Dados |
| RNF-09 | Completude da explicação | Atributo de qualidade | US-06 | Must | Engenharia |
| RNF-10 | Linguagem sem veredito | Atributo de qualidade | US-07 | Must | Produto |
| RNF-11 | Cobertura dos rótulos | Atributo de qualidade | US-10 | Must | Dados |
| RNF-12 | Tempo de resposta | Atributo de qualidade | US-03, US-06 | Could | Engenharia |
| IE-01 | API de score | Interface externa | US-03, US-06, US-07 | Must (depois do `go`) | Engenharia |
| IE-02 | Bot do Telegram | Interface externa | US-03, US-06, US-07 | Must (depois do `go`) | Engenharia + DevOps e MLOps |
| RNF-13 | k-NN em memória | Restrição | US-06 | Should | Engenharia |
| RNF-14 | Privacidade | Restrição | US-03 | Must | Engenharia + DevOps e MLOps |
| RNF-22 | Segredo do bot | Restrição | US-03 | Must | DevOps e MLOps |
| RNF-15 | Versionamento | MLOps (P4) | US-01, US-02 | Must | DevOps e MLOps |
| RNF-16 | Reprodutibilidade | MLOps (P3) | US-01 | Must | DevOps e MLOps |
| RNF-17 | Rastreamento de metadados | MLOps (P7) | US-01, US-03 | Must | DevOps e MLOps |
| RNF-18 | Integração contínua | MLOps (P1) | US-06, US-07 | Should | DevOps e MLOps |
| RNF-19 | Monitoramento contínuo | MLOps (P8) | US-01, US-05 | Should | DevOps e MLOps |
| RNF-20 | Treino e avaliação contínuos | MLOps (P6) | US-01 | Could | Modelos + DevOps e MLOps |
| RNF-21 | Ciclo de feedback | MLOps (P9) | US-04, US-09 | Could | Produto + Engenharia |

## 9. Gestão de requisitos

* **Mudanças:** toda alteração nesta página entra por pull request com revisão da frente de Produto. A mudança é registrada no histórico abaixo.
* **Limites do gate:** só podem mudar antes de qualquer avaliação nos períodos de teste (RN-02). Depois disso, um limite novo vale apenas para um gate novo.
* **Fonte normativa:** em caso de divergência, o texto normativo é o [spec da change](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-fake-news-pattern-scoring/specs/fake-news-pattern-scoring/spec.md) e o design. Esta página precisa ser atualizada no mesmo pull request.

| Data | Mudança |
|---|---|
| 2026-10-06 | Reenquadramento: o produto deixa de recuperar a checagem existente e passa a estimar a semelhança com narrativas falsas. Os RF e RNF anteriores (busca, Recall@5, limiar 0,60, divergência entre agências, alegação mista) saem. Entram RN, RF, RNF, IE, a priorização MoSCoW e os requisitos de MLOps. O canal de uso passa a ser um bot do Telegram (IE-02). |

## Fora de escopo (*Won't have* nesta fase)

- Afirmar a verdade ou a falsidade de uma notícia; verificação de fatos automatizada (RN-04).
- Funções do produto anterior: busca da checagem existente para a alegação, faixas
  confirmado/provável/sem match/inédito, tratamento de alegação mista e exposição de divergência
  entre agências.
- Integração direta com o WhatsApp: o canal desta fase é o Telegram (IE-02).
- Indicadores de impacto social/comportamental pós-lançamento (concentração de vulnerabilidade,
  padrões por canal). Dependem de dado de uso real e ficam para um change futuro.
