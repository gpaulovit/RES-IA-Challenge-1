## Why

Uma parcela relevante da desinformação política brasileira é conteúdo
reciclado: boatos antigos ressurgem reescritos sob nova roupagem em novos
eventos eleitorais. Busca lexical ou manual não detecta essa recorrência
por definição, porque a superfície do texto muda a cada reescrita — mesmo
quando a checagem daquela alegação já existe e está catalogada. Isso deixa
tanto o público quanto as próprias agências de checagem sem forma prática
de identificar quando uma alegação nova é, na verdade, algo já verificado.
Esta mudança propõe validar essa hipótese empiricamente e, se confirmada,
construir uma capacidade de recuperação semântica sobre o corpus de
alegações já verificadas (FactPolCheckBr) capaz de reconhecer essa
reincidência de forma robusta e responsável.

## What Changes

- Nova capacidade de indexação semântica do corpus de alegações verificadas
  (título + texto de verificação), cobrindo as ~1.882 alegações de 10
  agências do FactPolCheckBr.
- Gate de decisão empírico e prévio a qualquer indexação: clusterização
  temática latente e análise de sazonalidade/ressurgimento temporal do
  corpus, sem depender de rótulo manual, para confirmar que a reciclagem de
  boato é um fenômeno mensurável nos dados disponíveis.
- Recuperação semântica top-k para uma alegação de entrada, robusta a
  paráfrase, gíria, apelido, erro ortográfico proposital, inversão de
  negação e reescrita através do tempo (reincidência temporal, não apenas
  paráfrase síncrona).
- Política de decisão em faixas de confiança (match confirmado / provável /
  sem match / alegação inédita), com tratamento responsável de match
  parcial (não endossar a parte não checada de uma alegação mista) e
  exposição de divergência de veredito entre agências para a mesma
  alegação semântica.
- Normalização dos rótulos de veredito entre as 10 agências de origem
  (hoje heterogêneos: "Falsa", "Fake", "Enganosa" etc.) como pré-requisito
  de dado para o restante da capacidade.
- **Fora de escopo deste change**: indicadores de impacto social/
  comportamental pós-lançamento (concentração de vulnerabilidade,
  padrões por canal). Dependem de dado de uso real e não são resolvíveis
  na fase de concepção — ficam para um change futuro.

## Capabilities

### New Capabilities
- `claim-recurrence-retrieval`: recuperação semântica de alegações
  políticas reincidentes (recicladas/reescritas ao longo do tempo) sobre o
  corpus de checagens já catalogadas, incluindo o gate de validação
  empírica da reciclagem, o índice de retrieval, e a política de decisão
  em faixas de confiança com tratamento responsável de match parcial ou
  divergente.

### Modified Capabilities
<!-- Nenhuma capacidade existente é modificada; este é um change greenfield. -->

## Impact

- Dataset externo: [FactPolCheckBr](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr)
  sob licença CC BY-NC-SA 4.0 (uso não comercial) — ~1.882 alegações, 10
  agências, rótulos de veredito heterogêneos entre agências, sem janela
  temporal documentada no README de origem.
- Nenhum código ou infraestrutura existente é afetado — projeto greenfield;
  `openspec/config.yaml` ainda não declara stack técnico.
- Escolha de modelo de embeddings, threshold(s) da política de confiança e
  estrutura de indexação ficam para `design.md`, condicionadas ao
  resultado do gate empírico de reciclagem descrito acima.
