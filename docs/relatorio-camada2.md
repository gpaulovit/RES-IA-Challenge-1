# Relatório da camada 2 (classificador de sinais de alerta)

> Responsável: Paulo (Modelos de IA). Atende US-08, RN-04, RNF-02, RNF-03, RNF-10 e RF-14.

Esta página decide se a faixa de alerta (camada 2) aparece para o usuário. **O critério abaixo foi
escrito e commitado antes de qualquer execução no conjunto de teste** (08/10/2026). A data do
commit no `git log` desta página é a prova. Nada nas seções "Critério" e "Protocolo" muda depois
de ver o resultado.

## Critério de decisão

A camada 2 é **`go`** se, e somente se, as três condições valem no conjunto de teste:

| # | Condição | Requisito |
| --- | --- | --- |
| 1 | F1 macro ≥ 0,75 | RNF-02 |
| 2 | Falso alarme ≤ 15% | RNF-03 |
| 3 | Pelo menos 100 notícias falsas e 100 verdadeiras no teste | tamanho mínimo para as condições 1 e 2 terem precisão |

Qualquer condição não atendida dá **`no-go`**, com o motivo registrado. Se a condição 3 falhar, o
resultado é "inconclusivo" e conta como `no-go`. Com `no-go`, o bot vai ao ar só com a camada 1
(RN-04). **`no-go` não é fracasso.**

Definições:

- **Classe positiva:** notícia falsa.
- **F1 macro:** média do F1 das duas classes, com a previsão binária "falsa" quando a
  probabilidade do modelo é ≥ 0,5.
- **Falso alarme:** fração das notícias **verdadeiras** do teste que caem na faixa
  `muitos_sinais`.

## Protocolo

### Dados e divisão (RN-04)

> **Emenda de 09/10/2026, registrada antes de qualquer execução no teste.** A base de treino
> entregue pela frente de Dados ([docs/dados.md](dados.md)) usa fontes diferentes das previstas
> (Fake.br, FakeWhatsApp.Br e FakeTweet.Br) e vai só até 2019. Com ela, a regra "treino ≤ 2020,
> teste ≥ 2021" deixaria o teste vazio. Adotamos a divisão temporal já feita pela frente de Dados,
> que atende à RN-04 (teste posterior ao treino). **O critério de decisão não muda.** A divisão
> original está no histórico do git desta página (commit `7b39f08`).

- **Treino:** `data/processados/treino/treino.csv`, com textos até 15/09/2018 (Fake.br e
  FakeWhatsApp.Br).
- **Teste (decide `go`/`no-go`):** `teste.csv`, com mensagens do FakeWhatsApp.Br de 16/09 a
  28/10/2018.
- **Teste extra (só relato complementar):** `teste_curtos.csv`, com tweets do FakeTweet.Br de 2010
  a 2019.
- A frente de Dados já remove repetições e quase-duplicatas entre os arquivos. O protocolo confere
  de novo: um texto do teste que, depois de normalizar caixa, acento e espaços, for idêntico a um
  texto do treino sai do teste. Assim, o teste não premia memorização.
- **Limitação, segundo a própria frente de Dados:** o teste é do mesmo canal e de semanas logo
  depois do treino, então a métrica tende a ser otimista para mensagens de 2026.

### Modelo (fixo, sem ajuste no teste)

- `TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2), min_df=2)`.
- `LogisticRegression(class_weight="balanced", C=1.0, max_iter=1000, random_state=42)`.
- Semente 42 em toda etapa aleatória (RNF-10). Os parâmetros ficam em `params.yaml`.

### Faixas (escolhidas só com o treino)

As probabilidades fora da amostra vêm de validação cruzada estratificada em 5 partes
(`StratifiedKFold(shuffle=True, random_state=42)`) dentro do treino.

- `corte_alto`: o menor limiar em que **no máximo 10%** das verdadeiras do treino ficam com
  probabilidade ≥ limiar. A margem de 10% abaixo dos 15% da RNF-03 cobre a mudança de época.
- `corte_baixo`: o maior limiar em que **no máximo 10%** das falsas do treino ficam com
  probabilidade ≤ limiar.
- Faixas: `muitos_sinais` se p ≥ `corte_alto`; `poucos_sinais` se p ≤ `corte_baixo`; `incerto`
  entre os dois.

### Sinais mostrados (RF-08)

Para cada termo do texto, a contribuição é o valor TF-IDF × o coeficiente do modelo. O bot mostra
os 3 termos de maior contribuição na direção da faixa (para `incerto`, os de maior valor
absoluto). A probabilidade nunca é exposta (RNF-06). Palavras vazias ("no", "vai", "das") não são
exibidas. O filtro vale só para a exibição: o modelo e as métricas usam todas as palavras.

### Relato complementar (não entra no critério)

Para interpretar o resultado, o relatório traz também:

- as métricas por fonte do teste;
- a matriz de confusão;
- a distribuição das três faixas por classe;
- duas linhas de base: a classe majoritária e um modelo que só vê a fonte.

**Como ler o atalho de estilo do veículo.** O gate anterior mostrou que a fonte sozinha prevê o
rótulo (registro em `archive/experiments/`). Por isso, o modelo pode estar reconhecendo o estilo de
escrita de um veículo, e não sinais de desinformação. São duas leituras, das mais fracas às mais
fortes:

1. **Modelo que só vê a fonte:** mede quanto o rótulo é previsível só pela origem. Se ele chegar
   perto do nosso modelo, o resultado é suspeito. Superá-lo não basta para descartar o atalho,
   porque o estilo de escrita é uma pista mais rica que o nome da fonte.
2. **F1 macro dentro de cada fonte com as duas classes no teste** (com pelo menos 30 itens por
   classe): dentro de uma mesma fonte, o estilo é constante. F1 perto de 0,5 ali indica que o
   modelo separa as classes pela fonte, não pelo conteúdo. Este é o teste direto do atalho.

Essas leituras não mudam a decisão de `go`/`no-go`. Elas acompanham o resultado para dizer **por
que** o modelo acerta ou erra.

## Reprodução

Um comando gera modelo, métricas e parâmetros juntos (RF-14), versionados com DVC:

```bash
dvc repro treinar
```

Saída: `experiments/results/metricas_camada2.json`. Rodar duas vezes deve dar o mesmo arquivo
(RNF-10).

## Resultado

*Pendente: aguardando a base de treino da frente de Dados.*

| Métrica | Valor | Condição | Atende? |
| --- | --- | --- | --- |
| F1 macro | | ≥ 0,75 | |
| Falso alarme | | ≤ 15% | |
| Falsas / verdadeiras no teste | | ≥ 100 / ≥ 100 | |
| **Decisão** | | | |
