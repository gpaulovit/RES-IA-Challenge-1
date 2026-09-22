# Requisitos

Gerados via OpenSpec, na proposta de mudança
[`add-recycled-claim-semantic-retrieval`](https://github.com/gpaulovit/RES-IA-Challenge-1/tree/main/openspec/changes/add-recycled-claim-semantic-retrieval).
Os requisitos do produto real abaixo ainda não estão implementados/arquivados — os requisitos formais oficiais só migram
para `openspec/specs/` quando a implementação for concluída.

Já existe um [protótipo de Engenharia](funcionalidades.md) com três exemplos
fictícios e comparação por palavras. Ele tem critérios próprios na proposta e
não conclui os requisitos de busca semântica e confiança descritos nesta página.

Esta página segue o fluxo completo trabalhado durante a concepção do
produto: **problema → objetivo de produto → objetivos específicos →
requisitos**. As perguntas orientadoras que sustentam cada etapa estão em
[Perguntas](perguntas.md).

## 1. Problema

O público e as próprias agências de checagem não têm como identificar, de
forma rápida e sistemática, quando uma alegação política nova é, na
verdade, um boato reciclado que já foi checado anteriormente sob outra
redação. Busca lexical ou manual não detecta essa recorrência por
definição, porque a superfície do texto muda a cada reescrita — mesmo
quando a checagem daquela alegação já existe e está catalogada.

**Pergunta norteadora do problema:** existe evidência suficiente, nesta
fase de concepção, de que o principal gargalo do combate à desinformação
política no Brasil é a falta de acesso rápido e comparável a checagens já
existentes — e não a falta de checagens em si, a falta de vontade do
público em checar, ou uma barreira estrutural das plataformas de
mensageria — de forma que um produto de recuperação semântica endereça a
causa raiz do problema, e não apenas um sintoma secundário dele?

## 2. Objetivo de produto

Construir uma capacidade de recuperação semântica sobre o corpus de
alegações políticas já verificadas
([FactPolCheckBr](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr)),
capaz de reconhecer alegações reincidentes — recicladas ou reescritas ao
longo do tempo — de forma robusta e responsável, classificando cada
correspondência por nível de confiança em vez de retornar um veredito
único e opaco.

- **Capacidade:** `claim-recurrence-retrieval`.
- **Validação prévia obrigatória:** um gate empírico (clusterização
  temática latente + análise de sazonalidade/ressurgimento temporal, sem
  depender de rótulo manual) precede qualquer trabalho de indexação, para
  confirmar que a reciclagem de boato é um fenômeno mensurável nesta base.
- **Fora de escopo deste change:** indicadores de impacto social/
  comportamental pós-lançamento — dependem de dado de uso real e ficam
  para um change futuro.

## 3. Objetivos específicos

Cada eixo de investigação da concepção do produto se traduz em um
objetivo específico, testável ainda nesta fase de concepção.

### Eixo 1 — Dados e Contexto Eleitoral

**Objetivo específico:** validar que a base FactPolCheckBr tem volume,
cobertura temática e temporal suficientes para sustentar um índice
semântico representativo do universo de boatos políticos brasileiros,
por meio de clusterização e análise de distribuição.

### Eixo 2 — IA e NLP

**Objetivo específico:** selecionar (ou ajustar) um modelo de embeddings
que recupere corretamente a checagem correspondente para uma parcela
relevante de alegações parafraseadas ou informais, validando
empiricamente a busca semântica como abordagem superior à classificação
estilística de "fake ou não".

### Eixo 3 — Decisão, Validação e Produto

**Objetivo específico:** definir uma política de decisão (faixas de
confiança + tratamento de fallback) que separe de forma confiável
alegações já checadas de alegações inéditas ou ambíguas, dentro de
margens de erro toleráveis para uso público.

### Eixo 4 — Impacto Social e Cidadania *(fora de escopo deste change)*

**Objetivo específico (reformulado):** projetar, com os dados e a
literatura disponíveis nesta fase, indicadores mensuráveis de impacto
social (concentração temática de vulnerabilidade, padrões por canal) que
sirvam de baseline — deixando explícito que a validação causal do efeito
sobre o comportamento do eleitor depende de dados de uso pós-lançamento e
não é resolvível na etapa de concepção. Não gera requisitos nesta
proposta.

## 4. Requisitos

Cada requisito abaixo realiza um dos objetivos específicos acima.

### Indexar o corpus para recuperação semântica

*Realiza o objetivo específico do Eixo 1.*

O sistema DEVE indexar o corpus de alegações políticas catalogadas (texto da
alegação e seu veredito de checagem associado) em uma forma que suporte
recuperação por similaridade.

- **Cenário — alegação recuperável após indexação**: quando uma alegação do
  corpus catalogado foi indexada, uma consulta de entrada semanticamente
  equivalente a essa alegação a retorna como candidata de recuperação.

### Recuperar a alegação catalogada sob reescrita

*Realiza o objetivo específico do Eixo 2.*

O sistema DEVE recuperar a alegação catalogada correta para uma alegação de
entrada que seja paráfrase, substituição por gíria/apelido, erro ortográfico
proposital, inversão de negação, ou uma alegação que ressurge em um período
posterior sob redação de superfície diferente — dentro de uma degradação
tolerável de acurácia de recuperação em relação a alegações não modificadas.

- **Cenário — alegação histórica reescrita é reconhecida como recorrência**:
  quando uma alegação de entrada é uma versão reescrita de uma alegação
  catalogada em um período anterior, o sistema retorna a alegação catalogada
  original entre os top-k candidatos de recuperação.
- **Cenário — paráfrase adversarial não falha silenciosamente**: quando uma
  alegação de entrada usa gíria, substituição por apelido, ou erro
  ortográfico proposital de uma alegação catalogada, o sistema retorna a
  alegação catalogada entre os top-k candidatos, ou classifica a consulta
  conforme o requisito de faixas de confiança abaixo, em vez de retornar um
  resultado não relacionado silenciosamente.

### Classificar cada resultado por faixa de confiança

*Realiza o objetivo específico do Eixo 3.*

O sistema DEVE classificar cada resultado de recuperação em uma de um
conjunto definido de faixas de confiança (match confirmado, match provável
que requer revisão, sem match, alegação inédita) em vez de retornar um único
veredito binário sim/não.

- **Cenário — similaridade ambígua é sinalizada, não resolvida
  silenciosamente**: quando o escore de similaridade do candidato principal
  de recuperação cai entre os limiares de match confirmado e sem match, o
  sistema classifica o resultado como "match provável" e não o apresenta
  como confirmado.

### Tratar com responsabilidade alegações parciais e mistas

*Realiza o objetivo específico do Eixo 3.*

O sistema NÃO DEVE aplicar um veredito catalogado a partes de uma alegação de
entrada que não foram cobertas por aquela checagem catalogada, quando a
alegação de entrada mistura conteúdo previamente verificado com conteúdo
novo e não verificado.

- **Cenário — alegação mista não é totalmente endossada por um match
  parcial**: quando uma alegação de entrada combina uma alegação falsa
  previamente catalogada com uma afirmação adicional não catalogada, a
  resposta do sistema aborda apenas a parte catalogada e marca a afirmação
  adicional como não coberta/não verificada.

### Expor divergências de veredito entre agências

*Realiza o objetivo específico do Eixo 3.*

O sistema DEVE expor quando duas ou mais agências de checagem emitiram
vereditos divergentes para alegações semanticamente equivalentes, em vez de
selecionar um silenciosamente.

- **Cenário — veredictos divergentes são ambos exibidos**: quando um match
  recuperado corresponde a alegações checadas por mais de uma agência com
  veredictos diferentes, o sistema apresenta ambos os veredictos e suas
  fontes em vez de resolver a divergência automaticamente.

### Apresentar os resultados de forma explicável

*Realiza o objetivo específico do Eixo 3.*

O sistema DEVE apresentar resultados de recuperação como uma lista
ranqueada de candidatos com a justificativa/evidência de cada
correspondência, em vez de uma única resposta não explicada.

- **Cenário — usuário consegue ver por que um match foi retornado**: quando
  uma consulta retorna candidatos de recuperação, cada candidato é
  apresentado junto com o texto da alegação/veredito fonte contra o qual foi
  comparado, não uma conclusão única e opaca.

### Normalizar rótulos de veredito entre agências

*Realiza o objetivo específico do Eixo 3 (pré-requisito de dado).*

O sistema DEVE mapear os rótulos de veredito heterogêneos usados pelas
agências contribuintes do corpus (ex.: "Falsa", "Fake", "Enganosa") para uma
taxonomia normalizada única antes de aplicar a classificação por faixas de
confiança ou a lógica de match parcial.

- **Cenário — rótulo específico de agência é normalizado antes da
  classificação**: quando uma alegação de qualquer agência contribuinte é
  indexada, seu rótulo de veredito original é mapeado para a taxonomia de
  veredito normalizada do sistema antes de ser usado na lógica de
  classificação.

## Fora de escopo

Indicadores de impacto social/comportamental pós-lançamento (concentração de
vulnerabilidade, padrões por canal). Dependem de dado de uso real e não são
resolvíveis na fase de concepção — ficam para um change futuro.
