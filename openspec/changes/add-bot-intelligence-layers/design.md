## Context

- Requisitos: [docs/requisitos.md](../../../docs/requisitos.md). Histórias: US-03, US-04, US-08.
- A base de checagens (`data/processados/checagens/checagens.json`) e a base de treino vêm da
  frente de Dados (Cibelly).
- Prazo: entrega em 13/10/2026 (R-03), com integração na sexta, 09/10.

## Decisions

### 1. Protótipo em `experiments/`, depois `src/checagens/`

Cada camada nasce em `experiments/` e é validada com a base real. Só então sobe para
`src/checagens/`, com testes que não baixam modelo. O código de busca antigo foi removido no
refactor e não é reaproveitado.

### 2. Esquema da base de checagens

Lista de registros com `id`, `alegacao` (texto indexado), `veredito_original`,
`veredito_normalizado` (RN-02), `agencia`, `data` (AAAA-MM-DD), `link` e `fonte_dataset`. A
validação fica numa função só, para que uma mudança de esquema mexa num lugar só.

### 3. Camada 1: embeddings

- Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, com revisão fixada em
  `experiments/modelos.py`. É leve o bastante para o limite de 5 s (RNF-01).
- Vetores normalizados, então a semelhança é o produto escalar, limitado ao intervalo [0, 1].
- O índice é salvo com hash SHA-256 dos arquivos e conferido ao carregar.
- Limites iniciais 0,85 / 0,60 (RN-05), recalibrados no benchmark. O resultado fica em
  `params.yaml` e o arquivo de origem em `experiments/results/calibracao_camada1.csv`.
- Negação (RN-06): uma lista de palavras de negação, depois de normalizar caixa e acento. Se só um
  dos dois textos (consulta ou checagem) tiver negação, a faixa máxima é `relacionada`.

### 4. Camada 2: classificador

- `TfidfVectorizer` seguido de `LogisticRegression(class_weight="balanced")`, com semente fixa
  (RNF-10).
- Divisão por época: treino até 2019, validação 2020 (só para escolher os cortes das faixas),
  teste 2021–2022 (RN-04).
- Sinais: os termos presentes no texto com maior contribuição (`tfidf × coeficiente`) na direção
  da faixa.

### 5. Critério de go/no-go (escrito antes do teste)

`go` ⇔ F1 macro ≥ 0,75 (RNF-02) **e** no máximo 15% das notícias verdadeiras do teste em
`muitos_sinais` (RNF-03). O critério é registrado em `docs/relatorio-camada2.md` antes da primeira
execução no teste. Com `no-go`, o bot vai ao ar só com a camada 1.

### 6. Versionamento (RF-14)

`dvc.yaml` com os stages de índice, calibração e treino; `dvc repro` é o comando único. Os
parâmetros ficam em `params.yaml` e as métricas em JSON em `experiments/results/`.

## Risks

- **Atalho de fonte:** o gate anterior mostrou que fonte e ano previam o rótulo (ver `/archive`).
  O relatório traz as métricas também por `fonte`.
- **Poucas notícias verdadeiras** nos corpora de checagem, o que limita a medida do falso
  alarme (RNF-03).
- A base da Cibelly ainda não foi publicada, então calibração e métricas dependem dela.
