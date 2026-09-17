# Cronograma

## Como editar este cronograma

Este é um documento vivo. Mover datas, mover itens entre semanas ou
reescopar uma entrega é esperado conforme a equipe aprende mais sobre o
problema, o domínio e os modelos. Ao editar:

- Mantenha a estrutura de semanas (objetivo → base → atividades →
  entregável) mesmo se o conteúdo mudar.
- Registre toda mudança relevante na tabela [Log de edições](#log-de-edições)
  no final deste arquivo.

## Semana 1 — Estudo de caso, do problema e do domínio

**Objetivo de aprendizado:** entender por que o problema existe e o domínio
de dados em que a solução vai operar, antes de comprometer com qualquer
abordagem técnica.

**Base:** [`perguntas.md`](perguntas.md) (causa raiz, comportamento humano,
ecossistema, escala) · domínio de fact-checking político e dataset
FactPolCheckBr ([`refs.md`](refs.md)) · contexto regulatório (TSE, marco de
desinformação) já citado em `perguntas.md`.

**Atividades:**

- Leitura e discussão guiada das perguntas por eixo em `perguntas.md`.
- Pesquisa de ecossistema: quem já resolve pedaços do problema e onde está
  a lacuna.
- Exploração do corpus FactPolCheckBr (volume, cobertura temporal e
  temática).
- Mapeamento curado dos rótulos de veredito de cada agência para uma
  taxonomia normalizada (tarefas 2.1/2.2 de
  [`openspec/changes/add-recycled-claim-semantic-retrieval/tasks.md`](../openspec/changes/add-recycled-claim-semantic-retrieval/tasks.md)).

**Entregável:** síntese escrita respondendo a pergunta norteadora do
problema com evidência + relatório de cobertura do corpus.

## Semana 2 — Estudo dos modelos de IA e gate de validação

**Objetivo de aprendizado:** decidir, com evidência empírica, se a
abordagem de recuperação semântica se sustenta e qual modelo de embeddings
usar. Última semana majoritariamente de estudo antes da construção pesada
começar.

**Base:** Eixo 2 de [`perguntas.md`](perguntas.md) (robustez de embeddings
a paráfrase, gíria, erro ortográfico, inversão de negação, fine-tuning) ·
seção 1 e tarefas 3.1/3.2 de
[`openspec/.../tasks.md`](../openspec/changes/add-recycled-claim-semantic-retrieval/tasks.md)
(gate de validação empírica de reciclagem, comparação de modelos
candidatos: multilíngue genérico, BERTimbau, fine-tuned).

**Atividades:**

- Clusterização temática latente sobre os embeddings do corpus.
- Análise de recorrência temporal (taxa de alegações que reaparecem
  reescritas).
- Registro da decisão go/no-go do gate em
  [`design.md`](../openspec/changes/add-recycled-claim-semantic-retrieval/design.md).
- Montagem do conjunto de teste parafraseado/adversarial e comparação de
  acurácia top-k por modelo e por categoria de reescrita.

**Entregável:** decisão go/no-go do gate registrada + modelo de embeddings
selecionado com justificativa.

## Semana 3 — Construção: indexação e retrieval

**Objetivo de aprendizado → construção:** sair do estudo para código
funcionando. Primeira versão real do produto.

**Base:** tarefa 3.3 de
[`openspec/.../tasks.md`](../openspec/changes/add-recycled-claim-semantic-retrieval/tasks.md)
· [`historias.md`](historias.md) (US-03 a US-06, "o buscador funcionando").

**Atividades:**

- Implementação da indexação do corpus com o modelo selecionado.
- Implementação do retrieval k-NN exato.
- Validação contra os cenários "Claim is retrievable after indexing" e
  "Reworded historical claim is recognized as recurrence" do
  [spec](../openspec/changes/add-recycled-claim-semantic-retrieval/specs/claim-recurrence-retrieval/spec.md).

**Entregável:** buscador funcionando de ponta a ponta sobre o corpus
indexado (ainda sem a política de decisão completa).

## Semana 4 — Construção: política de decisão e produto

**Objetivo de aprendizado → construção:** transformar o buscador em
produto responsável — as decisões nas zonas cinzentas (thresholds, casos
ambíguos, divergência) são onde o produto mais pode causar dano se malfeito.

**Base:** Eixo 3 de [`perguntas.md`](perguntas.md) (faixas de confiança,
alegação parcial/mista, divergência entre agências, explicabilidade) ·
seção 4 de
[`openspec/.../tasks.md`](../openspec/changes/add-recycled-claim-semantic-retrieval/tasks.md)
· [`historias.md`](historias.md) (US-07 a US-10, "não mentir").

**Atividades:**

- Calibração dos thresholds de confiança (confirmado/provável/sem
  match/inédito).
- Implementação do tratamento de alegação parcial/mista (match só endossa a
  parte catalogada).
- Implementação da detecção e exposição de divergência de veredito entre
  agências.
- Implementação da apresentação explicável de top-k (texto-fonte de cada
  candidato).
- Revisão de [`requisitos.md`](requisitos.md) e [`historias.md`](historias.md)
  à luz do que foi construído nas semanas 2–4.

**Entregável:** produto com política de decisão implementada, cenários
4.1–4.4 do spec passando.

## Semana 5 — Integração, testes, buffer e entrega

**Objetivo:** fechar lacunas, validar de ponta a ponta, preparar a entrega
e a narrativa do que foi aprendido e construído.

**Atividades:**

- Buffer explícito para o que atrasou nas semanas 1–4 (esperado — aprendizado
  e construção competem por tempo).
- Execução completa dos cenários de aceitação do
  [spec](../openspec/changes/add-recycled-claim-semantic-retrieval/specs/claim-recurrence-retrieval/spec.md).
- Empacotamento e documentação final do produto.
- Preparação do material de apresentação.

**Entregável:** produto entregue com todos os cenários de aceitação
passando + material de apresentação.

## Frentes de trabalho

O grupo dividiu o trabalho em 5 frentes, uma por pessoa. As frentes
espelham os labels `papel:` usados nas issues e PRs do GitHub do
repositório, para manter cronograma e rastreamento de trabalho
consistentes:

- **Problema e ecossistema** (`papel: problema-ecossistema`) — investiga
  por que esse problema (boatos políticos reciclados) é real e importante,
  e o que já existe por aí tentando resolver algo parecido. É quem
  consegue explicar, em uma frase, por que vale a pena construir isso.
- **Domínio de dados** (`papel: dominio-dados`) — cuida da base de boatos
  e checagens usada pelo projeto: organiza, confere se tem informação
  suficiente e de várias épocas/temas, e se dá pra confiar nela antes de
  qualquer coisa ser construída em cima.
- **Modelos de IA** (`papel: modelos-ia`) — ensina o computador a
  reconhecer quando uma alegação nova é, na verdade, um boato antigo
  reescrito de outro jeito (com gíria, erro de digitação proposital,
  apelido etc.), e testa qual "modelo" faz esse reconhecimento melhor.
- **Produto e decisão** (`papel: produto-decisao`) — define como o
  sistema mostra o resultado para quem for usar (o que aparece na tela, o
  que precisa ficar claro, quando ele deve dizer "não tenho certeza" em
  vez de arriscar), escreve os requisitos e ajuda a contar essa história
  na apresentação final.
- **Engenharia** (`papel: engenharia`) — acompanha a construção do
  sistema do início ao fim, semana após semana, ajudando a transformar o
  que cada frente vai decidindo (os dados prontos, o modelo escolhido, as
  regras de produto) em código que realmente funciona e se conecta — não
  é uma etapa isolada só do final, e sim um trabalho contínuo junto com as
  outras frentes.

## Papéis e responsabilidades

| Nome | Foco principal |
| --- | --- |
| | Problema e ecossistema |
| | Domínio de dados |
| Paulo | Modelos de IA |
| | Produto e decisão |
| | Engenharia |

## Log de edições

| Data | O que mudou | Por quê |
| --- | --- | --- |
| 2026-09-17 | Adicionadas as frentes de trabalho e preenchida a tabela de papéis | Tornar explícita no cronograma a divisão de trabalho já usada nos labels `papel:` do GitHub |
