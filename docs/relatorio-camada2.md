# Relatório da camada 2 (classificador de sinais de alerta)

> Responsável: Paulo (Modelos de IA). Atende US-08, RN-04, RNF-02, RNF-03, RNF-10 e RF-14.

Esta página decide se a faixa de alerta (camada 2) aparece para o usuário. O critério abaixo foi
escrito antes da execução no conjunto de teste (08/10/2026). A data do
commit está no `git log` desta página. 

## Critério de decisão

A camada 2 é **`go`** se, e somente se, as três condições valem no conjunto de teste:

| # | Condição | Requisito |
| --- | --- | --- |
| 1 | F1 macro ≥ 0,75 | RNF-02 |
| 2 | Falso alarme ≤ 15% | RNF-03 |
| 3 | Pelo menos 100 notícias falsas e 100 verdadeiras no teste | tamanho mínimo para as condições 1 e 2 terem precisão |

Qualquer condição não atendida dá **`no-go`**, com o motivo registrado. Se a condição 3 falhar, o
resultado é "inconclusivo" e conta como `no-go`. Com `no-go`, o bot vai ao ar só com a camada 1
(RN-04).

Definições:

- **Classe positiva:** notícia falsa.
- **F1 macro:** média do F1 das duas classes, com a previsão binária "falsa" quando a
  probabilidade do modelo é ≥ 0,5.
- **Falso alarme:** fração das notícias **verdadeiras** do teste que caem na faixa
  `muitos_sinais`.

## Protocolo

### Dados e divisão (RN-04)

> **Emenda de 09/10/2026, registrada antes de qualquer execução no teste.** A base de treino entregue pela frente de Dados ([docs/dados.md](dados.md)) usa as fontes (Fake.br, FakeWhatsApp.Br e FakeTweet.Br) e vai só até 2019. Adotamos a divisão temporal já feita pela frente de Dados, que atende à RN-04 (teste posterior ao treino), o critério de decisão não mudou. A divisão original está no histórico do git desta página (commit `7b39f08`).

- **Treino:** `data/processados/treino/treino.csv`, com textos até 15/09/2018 (Fake.br e
  FakeWhatsApp.Br).
- **Teste (decide `go`/`no-go`):** `teste.csv`, com mensagens do FakeWhatsApp.Br de 16/09 a
  28/10/2018.
- **Teste extra (só relato complementar):** `teste_curtos.csv`, com tweets do FakeTweet.Br de 2010
  a 2019.
- A frente de Dados já remove repetições e quase-duplicatas entre os arquivos. O protocolo confere de novo: um texto do teste que, depois de normalizar caixa, acento e espaços, for idêntico a um texto do treino sai do teste. Assim, o teste não premia memorização.
- **Limitação:** o teste é do mesmo canal e de semanas logo depois do treino, então a métrica tende a ser otimista para mensagens de 2026.

### Modelo 

- `TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2), min_df=2)`.
- `LogisticRegression(class_weight="balanced", C=1.0, max_iter=1000, random_state=42)`.
- Semente 42 em toda etapa aleatória (RNF-10). Os parâmetros ficam em `params.yaml`.

### Faixas (escolhidas só com o treino)

As probabilidades fora da amostra vêm de validação cruzada estratificada em 5 partes
(`StratifiedKFold(shuffle=True, random_state=42)`) dentro do treino.

- `corte_alto`: o menor limiar em que no máximo 10% das verdadeiras do treino ficam com probabilidade ≥ limiar. A margem de 10% abaixo dos 15% da RNF-03 cobre a mudança de época.
- `corte_baixo`: o maior limiar em que no máximo 10% das falsas do treino ficam com probabilidade ≤ limiar.
- Faixas: `muitos_sinais` se p ≥ `corte_alto`; `poucos_sinais` se p ≤ `corte_baixo`; `incerto` entre os dois.

### Sinais mostrados (RF-08)

Para cada termo do texto, a contribuição é o valor TF-IDF × o coeficiente do modelo. O bot mostra os 3 termos de maior contribuição na direção da faixa (para `incerto`, os de maior valor absoluto). A probabilidade nunca é exposta (RNF-06)Palavras vazias ("no", "vai", "das") não são exibidas. O filtro vale só para a exibição: o modelo e as métricas usam todas as palavras.

### Relato complementar

Para interpretar o resultado, o relatório traz também:

- as métricas por fonte do teste;
- a matriz de confusão;
- a distribuição das três faixas por classe;
- duas linhas de base: a classe majoritária e um modelo que só vê a fonte.

Como ler o atalho de estilo do veículo. O gate anterior mostrou que a fonte sozinha prevê o rótulo (registro em `archive/experiments/`). Por isso, o modelo pode estar reconhecendo o estilo de escrita de um veículo, e não sinais de desinformação. São duas leituras, das mais fracas às mais fortes:

1. **Modelo que só vê a fonte:** mede quanto o rótulo é previsível só pela origem. Se ele chegar perto do modelo, o resultado é suspeito. Superá-lo não basta para descartar o atalho, porque o estilo de escrita é uma pista mais rica que o nome da fonte.
2. **F1 macro dentro de cada fonte com as duas classes no teste** (com pelo menos 30 itens por classe): dentro de uma mesma fonte, o estilo é constante. F1 perto de 0,5 ali indica que o modelo separa as classes pela fonte, não pelo conteúdo. Este é o teste direto do atalho.

Essas leituras não mudam a decisão de `go`/`no-go`. Elas acompanham o resultado para dizer por que o modelo acerta ou erra.

## Reprodução

Um comando gera modelo, métricas e parâmetros juntos (RF-14), versionados com DVC:

```bash
dvc repro treinar
```

Saída: `experiments/results/metricas_camada2.json`. Rodar duas vezes deve dar o mesmo arquivo
(RNF-10).

## Resultado

Rodada de 09/10/2026, depois da emenda (commit `2aa871d`). Todos os números vêm de
[`experiments/results/metricas_camada2.json`](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/experiments/results/metricas_camada2.json);
parâmetros e hashes das bases estão em
[`params_camada2.json`](https://github.com/gpaulovit/RES-IA-Challenge-1/blob/main/experiments/results/params_camada2.json).

| Métrica | Valor | Condição | Atende? |
| --- | --- | --- | --- |
| F1 macro | 0,673 | ≥ 0,75 | ❌ |
| Falso alarme | 30,8% (513 de 1.667 verdadeiras) | ≤ 15% | ❌ |
| Falsas / verdadeiras no teste | 1.628 / 1.667 | ≥ 100 / ≥ 100 | ✅ |
| **Decisão** | **`no-go`** | | |

**Consequência (RN-04):** a camada 2 não aparece para o usuário. Sem checagem parecida, o bot diz
que não encontrou e indica as agências e o TSE.

### Matriz de confusão (teste, previsão com p ≥ 0,5)

| Real \ Previsto | verdadeira | falsa |
| --- | ---: | ---: |
| verdadeira | 1.070 | 597 |
| falsa | 480 | 1.148 |

### Relato complementar

| | Valor |
| --- | --- |
| Linha de base: classe majoritária (F1 macro) | 0,336 |
| Linha de base: só a fonte (F1 macro) | 0,336 (o teste tem uma fonte só) |
| Faixas das verdadeiras: muitos / incerto / poucos sinais | 513 / 161 / 993 |
| Faixas das falsas: muitos / incerto / poucos sinais | 1.063 / 152 / 413 |
| Cortes das faixas (escolhidos no treino) | alto 0,527 · baixo 0,483 |
| Teste extra, tweets (`teste_curtos`): F1 macro / falso alarme | 0,584 / 37,8% |
| Reprodutibilidade (RNF-10) | duas execuções geram arquivos idênticos byte a byte |

### Leitura

- **O modelo aprende algo** (F1 0,67 contra 0,34 da classe majoritária), mas não o bastante, e
  erra demais nas verdadeiras: 3 em cada 10 recebem "muitos sinais de alerta".
- **Ele aprendeu o veículo** (docs/dados.md, "Limitações"). 72% do
  treino é Fake.br, onde as verdadeiras são texto de jornal. Os termos de maior peso para
  "verdadeira" são de estilo jornalístico ("nesta quarta-feira", "segundo", "tribunal", "g1"), não
  de conteúdo. Mensagens de WhatsApp verdadeiras não têm esse estilo e caem como falsas, o que
  explica o falso alarme alto.
- **A faixa `incerto` quase não existe** (cortes 0,48 a 0,53). No treino, a validação cruzada
  separa bem as classes, porque o estilo do veículo é fácil. Os cortes escolhidos ali não
  transferem para o WhatsApp.
- **No teste extra (tweets, outra fonte)** o resultado piora: F1 0,58 e falso alarme 38%.

