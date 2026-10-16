# Relatório técnico: modelos de IA do bot de checagem

RES IA ELD UnB, Turma 2 · Frente de Modelos · Paulo Vitor Gomes · 15/10/2026
Repositório: <https://github.com/gpaulovit/RES-IA-Challenge-1>

## 1. Resumo

O bot do Telegram recebe uma mensagem sobre as eleições de 2026 e diz se ela já foi checada por
uma agência. Ele nunca dá veredito próprio de "verdade" ou "mentira". Para isso, usa duas camadas
de aprendizado de máquina:

| Camada | Função | Modelo | Resultado | Decisão |
| --- | --- | --- | --- | --- |
| 1. Busca de checagens | Acha checagens de agências parecidas com a mensagem | Embeddings pré-treinados (`paraphrase-multilingual-MiniLM-L12-v2`) + busca híbrida + reranker (cross-encoder pré-treinado) | Top-3 de 87,5% (meta 70%); 0 de 32 notícias reais marcadas como "já checado" | **Vai ao ar** |
| 2. Sinais de alerta | Sem checagem parecida, diz se o texto tem cara de desinformação | TF-IDF + regressão logística, treinado pela equipe | F1 macro 0,673 (meta 0,75); falso alarme 30,8% (meta 15%) | **No-go**: não aparece ao usuário |

Conclusão: o bot vai ao ar só com a camada 1 (RN-04). Quando não há checagem parecida, ele avisa
que não encontrou e indica as agências e o TSE.

## 2. Dados

| Conjunto | Uso | Tamanho | Origem |
| --- | --- | --- | --- |
| Base de checagens | Índice da camada 1 | 10.442 checagens (07/2013 a 12/2022) | FactPolCheckBr, FACTCK.BR e FactChecks.br (Central de Fatos e FakeRecogna), unificados pela frente de Dados |
| Benchmark | Calibração e avaliação da camada 1 | 62 mensagens: 30 com checagem correspondente + 32 notícias reais sem checagem (controles) | `data/testes_benchmark.json` |
| Treino da camada 2 | Treino e escolha das faixas | 9.934 textos até 15/09/2018 | Fake.br-Corpus e FakeWhatsApp.Br |
| Teste da camada 2 | Decisão go/no-go | 3.295 mensagens de WhatsApp de 16/09 a 28/10/2018 (1.628 falsas, 1.667 verdadeiras) | FakeWhatsApp.Br |
| Teste extra | Só relato complementar | 297 tweets (199 falsos, 98 verdadeiros) | FakeTweet.Br |

 Textos do teste idênticos a textos do treino seriam removidos; nenhum foi encontrado. O SHA-256 de cada arquivo está em `experiments/results/params_camada2.json`. A documentação completa das bases fica em
`docs/dados.md`, no repositório.

As 30 mensagens com checagem do benchmark se dividem em 5 categorias de 6 mensagens: erro
ortográfico, gíria, apelido ("Xandão", "Molusco"), recorrência temporal (boato antigo com data
nova) e negação ("Lula NÃO prometeu…"). As quatro primeiras são reescritas: a mensagem diz o mesmo que a checagem, com outras palavras.

## 3. Camada 1: busca de checagens

### Como funciona

A busca tem três etapas. A primeira usa só o modelo de embeddings, e as outras duas corrigem
erros que ele cometia sozinho.

1. **Normalização.** A mensagem passa por dicionários de apelidos e internetês ("Xandão" →
   "Alexandre de Moraes", "ñ" → "não").
2. **Cosseno (embeddings).** O modelo `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
   (revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, pré-treinado) transforma o texto num
   vetor de 384 dimensões, comparado por cosseno com os vetores das 10.442 checagens. Esse
   cosseno é o campo `semelhanca` devolvido ao bot.
3. **Candidatas (busca híbrida).** Juntam-se as 20 checagens de maior cosseno e as 20 de maior
   nota `cosseno + 0,2 × cobertura do assunto`. A cobertura é a fração das palavras da mensagem
   que não são nomes ("tesouraço", "fraudar") presentes na checagem, pesadas pela raridade na base.
4. **Reranker.** Um cross-encoder multilíngue (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`,
   revisão `1427fd652930e4ba29e8149678df786c240d8825`, pré-treinado) lê a mensagem e cada
   candidata juntas e dá uma nota de "falam da mesma coisa". A ordem e a faixa saem dessa nota:

| Faixa | Regra | O bot diz |
| --- | --- | --- |
| `ja_checado` | nota ≥ 9, cosseno ≥ 0,86 e a mesma negação nos dois textos | "Essa informação já foi checada" |
| `relacionada` | nota ≥ 4 | "Encontrei uma checagem relacionada" |
| `baixa` | o resto | Nada é mostrado |

**Por que as etapas 3 e 4.** O MiniLM quase ignora palavras que não conhece, e o vetor fica
dominado pelos nomes famosos. "Flávio Bolsonaro e o tesouraço" saía como "já checado" com uma
checagem sobre outro assunto, só por citar Flávio Bolsonaro.

**Negação (RN-06).** Uma lista de palavras (não, nunca, jamais, nem, nenhum, "falso que",
"mentira que") é procurada nos dois textos, sem caixa e acento. Se só um deles tem negação, a
faixa máxima é `relacionada`. Assim, "X NÃO fez Y" nunca sai como "já checado" para a checagem
"X fez Y".

**Integridade.** O índice guarda o SHA-256 dos vetores e das checagens
(`data/indices/camada1/manifesto.json`). O código confere os hashes ao carregar e recusa um
índice alterado.

### Calibração

Os limites foram escolhidos por grade no próprio benchmark, com esta regra:

1. **Teto de falsos positivos.** No máximo 2 dos 32 controles podem sair como `ja_checado`
   (RNF-05). Além disso, no máximo 8 deles podem receber alguma checagem. Este segundo teto é
   nosso: sem ele, quase toda notícia real recebia uma checagem sem relação.
2. **Cobertura.** Respeitado o teto, maximizar as reescritas em que a checagem certa é mostrada.
3. **Desempate.** Preferir menos notícias reais em `ja_checado`.

O limite de cosseno 0,86 veio dessa grade na versão só com cosseno
(`experiments/results/calibracao_camada1.csv`). As notas 4 e 9 do reranker e os pesos da busca
híbrida foram escolhidos depois, pela mesma regra. Segundo o registro da equipe, notas de 3 a 5
dão o mesmo resultado.

### Resultados

Avaliação de 15/10/2026: o código atual da busca (`src/inteligencia/busca.py`) rodou nas 62
mensagens do benchmark, comparando as três versões. A coluna "Só cosseno" reproduz exatamente a
calibração anterior, o que confirma que a medida é a mesma.

| Métrica | Só cosseno | + busca híbrida | + reranker (**versão do bot**) | Meta |
| --- | ---: | ---: | ---: | --- |
| Checagem certa no top-3 (24 reescritas) | 17 (70,8%) | 21 (87,5%) | **21 (87,5%)** | ≥ 70% (RNF-04) ✅ |
| Checagem certa em 1º | 15 | 17 | 13 | — |
| Checagem certa mostrada ao usuário | 9 (37,5%) | 11 (45,8%) | **17 (70,8%)** | — |
| Notícias reais (32) em `ja_checado` | 0 | 0 | **0** | ≤ 2 (RNF-05) ✅ |
| Notícias reais com alguma checagem mostrada | 2 | 0 | **2** | ≤ 8 (critério interno) ✅ |
| Negações (6) em `ja_checado` | 0 | 0 | **0** | 0 (RN-06) ✅ |
| Negações com a checagem certa no top-3 | 1 | 4 | **5** | — |
| Tempo médio por busca, com modelos já carregados | 0,015 s | 0,008 s | **0,047 s** | < 5 s (RNF-01) ✅ |

O maior ganho do reranker está nas checagens mostradas: o bot passa de 9 para 17 das 24
reescritas, sem nenhuma notícia real como "já checado". Ele piora um pouco a 1ª posição
(15 → 13). Nesses casos, a checagem certa continua no top-3, mas abaixo de outra.

As 2 notícias reais que recebem uma checagem "relacionada" na versão do bot:

- "RealTime Big Data: Flávio Bolsonaro tem 45%, contra 44% de Lula no 2º turno" → checagem
  sobre uma pesquisa Ipec de Bolsonaro contra Lula.
- "TSE manda Instagram retirar vídeo que associa Flávio Bolsonaro ao Master" → checagem sobre o
  TSE e um vídeo de Bolsonaro.

Por categoria, na versão do bot:

| Categoria | Certa em 1º | Certa no top-3 | Certa mostrada |
| --- | ---: | ---: | ---: |
| Erro ortográfico | 4 de 6 | 6 de 6 | 6 de 6 |
| Apelido | 4 de 6 | 5 de 6 | 5 de 6 |
| Gíria | 2 de 6 | 4 de 6 | 3 de 6 |
| Recorrência temporal | 3 de 6 | 6 de 6 | 3 de 6 |
| Negação | 3 de 6 | 5 de 6 | 5 de 6 (todas como `relacionada`) |

O README do módulo (`src/inteligencia/README.md`) registra números do desenvolvimento um pouco
diferentes: 1 de 32 notícias reais mostradas e 12 de 24 reescritas mostradas. Este relatório usa
a reprodução de 15/10/2026.

## 4. Camada 2: classificador de sinais de alerta

### Modelo

- `TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2), min_df=2)`
- `LogisticRegression(class_weight="balanced", C=1.0, max_iter=1000, random_state=42)`
- Classe positiva: notícia falsa.

### Faixas e sinais

O modelo dá uma probabilidade de a mensagem ser falsa. Essa probabilidade nunca é mostrada ao
usuário (RNF-06). Ela vira uma de três faixas, com cortes escolhidos **só no treino**, por
validação cruzada estratificada em 5 partes:

- `muitos_sinais`: p ≥ 0,527. É o corte em que no máximo 10% das verdadeiras do treino ficam acima.
- `poucos_sinais`: p ≤ 0,483. É o corte em que no máximo 10% das falsas do treino ficam abaixo.
- `incerto`: entre os dois.

Junto com a faixa, o bot mostraria as 3 palavras do texto que mais pesaram na decisão
(valor TF-IDF × coeficiente do modelo).

### Critério de decisão (pré-registrado)

O critério foi escrito em 08/10/2026, antes da primeira execução no teste. A camada 2 só é `go`
se as três condições valem no teste:

1. F1 macro ≥ 0,75 (RNF-02). Média do F1 das duas classes, prevendo "falsa" quando p ≥ 0,5.
2. Falso alarme ≤ 15% (RNF-03). Fração das notícias **verdadeiras** que caem em `muitos_sinais`.
3. Pelo menos 100 notícias de cada classe no teste.

### Resultados (`experiments/results/metricas_camada2.json`)

| Métrica | Valor | Condição | Atende? |
| --- | --- | --- | --- |
| F1 macro | 0,673 | ≥ 0,75 | ❌ |
| Falso alarme | 30,8% (513 de 1.667 verdadeiras) | ≤ 15% | ❌ |
| Falsas / verdadeiras no teste | 1.628 / 1.667 | ≥ 100 / ≥ 100 | ✅ |
| **Decisão** | **no-go** | | |

Matriz de confusão (previsão com p ≥ 0,5):

| Real \ Previsto | Verdadeira | Falsa |
| --- | ---: | ---: |
| Verdadeira | 1.070 | 597 |
| Falsa | 480 | 1.148 |

Distribuição nas faixas:

| Classe real | `muitos_sinais` | `incerto` | `poucos_sinais` |
| --- | ---: | ---: | ---: |
| Verdadeiras (1.667) | 513 | 161 | 993 |
| Falsas (1.628) | 1.063 | 152 | 413 |

Comparações:

| Referência | F1 macro | Falso alarme |
| --- | --- | --- |
| Linha de base: sempre a classe majoritária | 0,336 | — |
| Modelo no teste (WhatsApp) | 0,673 | 30,8% |
| Modelo no teste extra (tweets) | 0,584 | 37,8% |

## 5. Análise e limitações

- **O modelo aprende alguma coisa, mas não o bastante.** O F1 de 0,673 é o dobro da linha de
  base (0,336), mas 3 em cada 10 mensagens verdadeiras receberiam "muitos sinais de alerta". Para
  um bot que não pode acusar notícias reais, isso é inaceitável.
- **O modelo aprendeu o estilo do veículo, não o conteúdo.** 72% do treino é Fake.br, onde as
  notícias verdadeiras são texto de jornal. Os termos que mais pesam para "verdadeira" são de
  estilo jornalístico ("nesta quarta-feira", "segundo", "tribunal", "g1"). Mensagens de WhatsApp
  verdadeiras não têm esse estilo e são marcadas como falsas. Isso explica o falso alarme alto.
- **A faixa `incerto` quase não existe.** Os cortes (0,483 a 0,527) estão muito próximos. No
  treino, o estilo do veículo separa as classes com facilidade, e os cortes escolhidos ali não se
  transferem para o WhatsApp.
- **Fora do canal, o desempenho piora.** Nos tweets, o F1 cai para 0,584 e o falso alarme sobe
  para 37,8%.
- **Mesmo os números do teste tendem a ser otimistas para 2026.** O teste é do mesmo canal e das
  semanas logo após o treino (2018).
- **A camada 1 foi calibrada e avaliada no mesmo benchmark.** Os limites, os pesos da busca
  híbrida e as notas do reranker foram escolhidos olhando as mesmas 62 mensagens usadas para
  medir o resultado, então os números da seção 3 tendem a ser otimistas. Os dicionários de
  apelidos também foram montados depois do benchmark.
- **O benchmark é pequeno.** Com 24 reescritas, cada caso vale cerca de 4 pontos percentuais no
  top-3.
- **A negação depende de uma regra, não do modelo.** Os embeddings não distinguem bem "fez" de
  "não fez". É a lista de palavras da RN-06 que impede o "já checado". Uma negação escrita de outro
  jeito ("é mentira", "desmentiu") não é reconhecida.

## 6. Decisão e próximos passos

- **Camada 1:** em produção, com busca híbrida e reranker (limite de cosseno 0,86 em `params.yaml`; notas e pesos no topo de `src/inteligencia/busca.py`).
- **Camada 2:** desligada (RN-04). O código e o modelo ficam versionados para nova avaliação.

Para a camada 2 voltar a ser avaliada:

1. Treinar com mensagens **verdadeiras de WhatsApp** (ou do mesmo canal do uso real), não com
   texto de jornal.
2. Medir o atalho de estilo dentro de uma mesma fonte, com as duas classes presentes.
3. Rodar com um conjunto de teste novo, sem reaproveitar o atual para ajustes.

Para a camada 1, os próximos passos são:

1. Montar um benchmark novo, não usado na calibração nem nos dicionários, para ter uma medida sem
   viés.
2. Atualizar `calibracao.py` para calibrar a busca completa: hoje ele mede só o cosseno.

## 7. Reprodutibilidade (RNF-10, RF-14)

- **Parâmetros:** `params.yaml` (semente 42, limites da camada 1, hiperparâmetros da camada 2).
- **Um comando por etapa** (no repositório, com DVC):

  ```bash
  dvc repro indice      # índice da camada 1
  dvc repro calibrar    # calibração do limite de cosseno (mede só a busca por cosseno)
  dvc repro treinar     # treino, métricas e decisão da camada 2
  ```

- **Determinismo:** duas execuções do treino geram `metricas_camada2.json` idêntico byte a byte.
  Isso foi confirmado de novo em 15/10/2026: o retreino reproduziu F1 0,673 e falso alarme 30,8%.
- **Rastreio:** os hashes das bases estão em `params_camada2.json` e os do índice em
  `manifesto.json`.

## Arquivos de origem

| Número no relatório | Arquivo |
| --- | --- |
| Métricas e decisão da camada 2 | `experiments/results/metricas_camada2.json` |
| Parâmetros, tamanhos e hashes das bases da camada 2 | `experiments/results/params_camada2.json` |
| Calibração do limite de cosseno da camada 1 | `experiments/results/calibracao_camada1.csv` |
| Resultados da camada 1 (seção 3) | Avaliação de 15/10/2026 do `Buscador` de `src/inteligencia/busca.py` no `data/testes_benchmark.json` |
| Modelo e hashes do índice | `data/indices/camada1/manifesto.json` |
