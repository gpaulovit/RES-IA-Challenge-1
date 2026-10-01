## Context

See proposal.md - Why. The project started without application code or
an established stack. A local engineering demonstration now uses Python,
FastAPI and TF-IDF with fictional examples. The real-data reference remains the external
[FactPolCheckBr](https://github.com/Interfaces-UFSCAR/Dataset-FactPolCheckBr)
corpus: ~1,882 claims across 10 fact-checking agencies, CC BY-NC-SA 4.0
(non-commercial), verdict labels not normalized across agencies, no
documented time range.

## Goals / Non-Goals

**Goals:**
- Validate, before committing to the retrieval build-out, that claim
  recycling (semantic recurrence of a catalogued claim resurfacing later
  under different wording) is a measurable phenomenon in the corpus.
- Satisfy the behavior contract in `specs/claim-recurrence-retrieval` with
  an implementation approach that is proportionate to the corpus's small
  size.


**Non-Goals:**
- Benchmarking against, or defining success relative to, existing
  fact-check assistants (e.g., Aos Fatos' Fátima, TSE's "Fato ou Boato").
  Those remain ecosystem context (who else covers part of this problem),
  never the yardstick for this capability's requirements.
- Impact/behavioral metrics on public sharing habits (deferred; separate
  future change per proposal.md).
- Committing to a specific embedding model or numeric confidence
  thresholds in this document — both require empirical calibration against
  the corpus and are left as implementation decisions, not fixed here.

## Critério go/no-go (escrito em 2026-09-29, antes da grade)

- **GO se:** taxa ≥ 10 % no τ validado, com precisão manual ≥ 75 % e N = 7 dias.
- **NO-GO se:** taxa < 3% OU nenhuma faixa com precisão ≥ 75%.
- **Inconclusivo (entre 3% e 10%):** rotular mais pares e discutir o enquadramento do produto
  antes do Bloco 3.
- **Por que:** abaixo de ~3%, o checador raramente teria algo para recuperar. Abaixo de 75%
  de precisão, 1 em cada 4 sugestões estaria errada, o que acaba com a confiança na
  ferramenta. A taxa é um piso, porque o corpus cobre só 4 meses. N = 7 fica acima da
  janela de cobertura paralela (0 a 2 dias).
- **Taxa comparada:** a do menor τ cuja precisão acumulada é ≥ 75%.
- **Revisão (2026-09-29, depois de ver a grade):** os limites da taxa mudaram de NO-GO < 2% e
  inconclusivo 2–5% para NO-GO < 3% e inconclusivo 3–10%, e a taxa comparada foi definida
  como a leitura (a). A régua de precisão (75%) e o N = 7 são os do pré-registro.

## Gate Result (2026-09-29)

**Decisão: NO-GO** para "reciclagem temporal dentro de um ciclo eleitoral" como justificativa da capacidade.

Parâmetros: N = 7 dias; filtros de agregador e duplicata ativos; modelo `paraphrase-multilingual-MiniLM-L12-v2`;
71 pares validados manualmente por um único anotador, com cada alegação em no máximo 1 par;
datas lidas como mês/dia/ano, formato validado contra as datas das URLs (256 de 262 datas
ambíguas conferem, nenhuma como dia/mês). Reprodução, hashes e protocolo de rotulagem em
[`experiments/README.md`](../../../experiments/README.md); fonte dos números:
`experiments/results/precisao_por_faixa.csv` e `taxa_reciclagem_grade.csv`.

| Faixa de τ | n | Mesma | Precisão | IC 95% | Acumulada (≥ faixa) | IC 95% acum. |
|---|---|---|---|---|---|---|
| 0,75–0,80 | 8 | 1 | 12% | 2–47% | 48% | 37–59% |
| 0,80–0,85 | 30 | 9 | 30% | 17–48% | 52% | 40–64% |
| 0,85–0,90 | 25 | 17 | 68% | 48–83% | 73% | 56–85% |
| ≥ 0,90 | 8 | 7 | 88% | 53–98% | 88% | 53–98% |

- **Leitura usada (a):** taxa no menor τ com precisão acumulada ≥ 75%. Só τ = 0,90 atende,
  com taxa de **1,36%**, abaixo de 3%, então NO-GO.
- **Leitura complementar (b):** taxa ponderada pela precisão = **5,0%** (inconclusivo).
  A (a) foi escolhida por aplicar diretamente a régua de precisão do critério. A escolha
  foi feita depois de ver as duas leituras; mesmo pela (b), o resultado não seria GO.
- **Definição de "mesma":** pares com mesma história e detalhe diferente (data, número)
  contam como `mesma`. Contando como `tema`, a precisão acumulada em ≥ 0,90 cai para 75%,
  a taxa ponderada cai para 4,0% e a decisão pela (a) não muda.

**Ressalvas**
- O corpus cobre 122 dias (um ciclo): a reciclagem entre eleições não é observável. A conclusão
  vale para "dentro de um ciclo", não para "reciclagem não existe".
- A data é a da checagem, não a da circulação do boato.
- Um único modelo: a precisão por τ depende dele (reavaliar no Bloco 5).
- n de 8 nas faixas extremas: ICs largos.
- Um único anotador, sem medida de concordância entre anotadores.
- Os 16,6% (τ = 0,75) e a `reciclagem_por_cluster.csv` do notebook 03 são exploratórios:
  τ = 0,75 tem precisão de 12% e não é taxa de reciclagem.

**Consequência:** reenquadrar a capacidade como recuperação
robusta a reescrita (paráfrase, negação, gíria), sem a premissa temporal. Evidência:
26% das alegações têm vizinho com similaridade ≥ 0,85 (a mesma alegação checada por agências
diferentes com outra redação); dos 34 pares `mesma`, 13 são paráfrase, 7 são negação e 8 têm
detalhe diferente.
Próximos passos: conjunto de teste centrado em paráfrase e negação e comparação de modelos,
incluindo se algum eleva a precisão em τ menor.

## Gate complementar: reciclagem entre ciclos (critério, 2026-10-01)

**Pergunta:** que % das alegações de 2022 (FactPolCheckBr) têm uma alegação `mesma` já checada
entre 2013 e 2021 (Central de Fatos)?

**Dados e preparação** (fixados antes de rodar):
- 2022: `com_texto_limpo.csv` (hash `45b54bb3…`), sem `multi_claim` e sem data inválida.
- Antigo: `central_de_fatos.tsv` da release v0.1 do FactChecks.br (TSV `1b3c964b…`), título = 1ª linha
  do `review_text`, mesma `limpar_titulo()` (`experiments/limpeza.py`), sem `multi_claim` e sem `claim` vazio.
- Modelo: `paraphrase-multilingual-MiniLM-L12-v2`, revisão `e8f8c21`, embeddings normalizados.

**Métrica:** para cada alegação de 2022, o vizinho mais similar no corpus antigo.
Taxa = % de alegações de 2022 com vizinho ≥ τ. Grade τ ∈ {0,80; 0,85; 0,90; 0,95}.
Recorte secundário: só vizinhos de 2018 (eleição anterior).

**Validação:** rótulos novos (mesmo protocolo do gate: `mesma`/`tema`/`diferente` + `tipo`,
cada alegação em no máximo um par), 20 pares por faixa, semente 44.

**Taxa comparada:** a do menor τ com precisão acumulada ≥ 75%.

**Decisão:**
- GO (reabre a premissa temporal, agora entre ciclos): taxa ≥ 10%
- O cenário de recorrência do spec volta, redefinido como recorrência entre ciclos (base histórica 2013–2021)".
- NO-GO (confirma o reenquadramento): taxa < 3%
- Inconclusivo: entre os dois → Repetir com o melhor modelo testado e verificar se a pergunta é efetivamente respondida.
- **Por que esses limites:** Seguir o padrão já definido anteriormente, para efetivamente testar se a escolha do modelo funciona, ter algo efetivamente para recuperar.

**O que este gate NÃO muda:** o NO-GO dentro de um ciclo (Gate Result de 2026-09-29) continua valendo.

## Escolha do modelo de embeddings (critério, 2026-10-01, antes de qualquer resultado)

**Candidatos** (revisões fixadas em `experiments/06_modelos.ipynb`): multilíngue genérico
(`paraphrase-multilingual-MiniLM-L12-v2`, `paraphrase-multilingual-mpnet-base-v2`,
`multilingual-e5-base`, `bge-m3`) e BERTimbau (`bert-base-portuguese-cased` com mean pooling,
`bert-large-portuguese-cased-sts`). Fine-tuned: só se nenhum candidato atender ao piso abaixo.

**Avaliação definitiva:** índice com os dois corpora (2022 + Central de Fatos, 12.240 alegações),
conjunto de teste do `experiments/05_avaliacao.ipynb` (categorias `apelido`, `girias`,
`apelido+girias`, `negacao`, `digitacao`, `parafrase_real`), consulta com a normalização
`condicional`. A rodada só no índice de 2022 é preliminar e não decide.

**Regra:**

1. **Métrica principal:** Recall@5 médio entre as categorias (cada categoria pesa igual).
2. **Piso:** nenhuma categoria com Recall@5 abaixo de 80%. Modelo abaixo do piso em alguma
   categoria só é escolhido se todos estiverem abaixo; aí vale o melhor e a lacuna vira risco registrado.
3. **Empate** (diferença < 2 p.p. no Recall@5 médio): fica o mais barato para o deploy (menor tempo
   de codificação por mil textos).
4. **Desempate final:** maior Recall@5 em `parafrase_real`, a única categoria de reescritas reais.

**Ressalva conhecida antes de rodar:** os pares de `parafrase_real` foram sorteados entre os vizinhos
que o MiniLM já achava parecidos (cosseno ≥ 0,75), o que favorece o MiniLM nessa categoria. A
ressalva vai junto do resultado.


## Decisions

### Protótipo de Engenharia: exceção limitada ao gate

O gate é a decisão de continuar ou rever o projeto com base nos dados reais.
Antes dessa decisão, é permitido demonstrar as peças conectadas usando apenas
três checagens fictícias. Essa exceção não conclui os requisitos do produto real.

- Python 3.11+, FastAPI (API HTTP), Uvicorn (servidor), scikit-learn
  (TF-IDF e cosseno) e pytest (testes). Sem banco, serviços pagos ou modelos baixados.
- Dados em `data/exemplos.json`; código em `src/checagens/`, separado em dados,
  representação de textos, busca e API. Dependências em `pyproject.toml`.
- Cada exemplo tem `id`, `alegacao`, `checagem`, `agencia` e `veredito_original`.
  Campos são textos não vazios e ids são únicos. Erros nos dados impedem iniciar.
- Na inicialização, TF-IDF aprende o vocabulário das alegações e prepara seus
  vetores em memória. A consulta usa o mesmo vocabulário. A comparação por
  cosseno mede palavras compartilhadas; não prova equivalência de significado.
- `GET /health` retorna `status: ok` e `modo: demonstracao`.
- `POST /buscar` recebe `texto` não vazio e `top_k` inteiro de 1 a 10, padrão 3.
  Retorna `modo`, `metodo`, `status`, `aviso` e `candidatos`. Cada candidato tem
  os campos do exemplo e `pontuacao`. Resultados com pontuação maior que zero
  são ordenados por pontuação decrescente e id crescente em caso de empate.
- Lista vazia tem status `nao_encontrada`; caso contrário,
  `candidatos_encontrados`. Não se atribuem faixas de confiança nem um veredito
  à consulta. Entradas inválidas recebem HTTP 422 com explicação em português.
- A representação de textos é substituível por um componente com `metodo`,
  `preparar(textos)` e `transformar(textos)`, retornando matrizes numéricas.
  A troca de técnica não exige mudar a API, mas exige refazer os vetores da base.
- README e guias explicam execução, funcionalidades, testes (harness), ciclo
  semanal, glossário e apresentação. Testes fictícios verificam integração;
  não medem qualidade semântica ou validam os requisitos de confiança abaixo.

### Decisões para o produto com dados reais

#### Preparação do corpus — Etapa 2 da Semana 1

Consolidar a versão já inspecionada em um JSON local para análise, separado da
API demonstrativa. Não indexar nem emitir decisão go/no-go nesta entrega.
O comando `python -m checagens.organizacao` deve verificar o SHA-256 do CSV e
os metadados de origem antes de gerar a base e o relatório de organização.

- Um registro de saída para cada registro do CSV, na ordem original, com id
  formado pela versão da fonte e pelo número do registro. Não deduplicar.
- Preservar os sete campos originais integralmente em `original`. Nos campos
  organizados, retirar apenas espaços externos e representar vazios com `null`.
- Manter `titulo_checagem`, sem inventar a alegação original; preservar rótulos
  de veredito e nomes de agência, sem normalização de significado.
- Datas com interpretação única sob mês/dia/ano recebem `AAAA-MM-DD`.
  Datas ambíguas, impossíveis, ausentes ou válidas somente em dia/mês/ano
  ficam com valor padronizado `null`, status explícito e possibilidades de
  interpretação. Mesmo dia e mês não é ambiguidade. Não tratar essas regras
  sintáticas como verificação da data na página de origem.
- Sinalizar campos essenciais ausentes, datas pendentes e grupos de registros
  integralmente repetidos. Não completar lacunas nem excluir grupos.
- Guardar origem, licença e versão das regras no JSON; gerar relatório de
  contagens. Reexecutar com a mesma fonte e regras produz arquivos idênticos.
- Os dados gerados ficam fora do Git. Código e documentação ficam versionados.
  A tarefa 1.1 permanece aberta enquanto persistirem lacunas que afetam análise.

- **The recycling-validation gate precedes real-corpus indexing work.** Before
  indexing or retrieval implementation over real data, run an empirical check directly on
  the corpus: latent thematic clustering (no manual labels) and a temporal
  analysis of whether claims recur, reworded, across different periods.
  *Why*: the whole capability is only justified if this phenomenon is real
  and sizeable; building the index first and discovering otherwise would
  waste the harder work. *Alternative considered*: skip straight to
  building the retrieval index and assess recycling incidentally — rejected
  because it risks investing in indexing/threshold work under a premise
  that was never checked.

- **Exact k-NN search over embeddings, no ANN index.** *Why*: at ~1,882
  claims, a brute-force nearest-neighbor search is fast enough; approximate
  nearest-neighbor infrastructure would add operational complexity with no
  measurable benefit at this scale. *Alternative considered*: an ANN
  library (e.g., HNSW) — rejected for now as premature given the corpus
  size; revisit only if the corpus grows by an order of magnitude.

- **Embedding model choice is left open, to be settled empirically.**
  Candidates: a generic multilingual model, a Portuguese-specific model
  (e.g., BERTimbau), or a model fine-tuned on (informal claim → official
  verdict) pairs. *Why deferred*: the spec's "robust retrieval under claim
  rewriting" requirement can only be satisfied by whichever model actually
  performs best on this corpus's adversarial/paraphrase cases — a priori
  preference would be guessing. *Alternative considered*: default to the
  fine-tuned option immediately — rejected because the corpus is small
  (~1,882 examples) and a generic pretrained model may already suffice;
  the comparison itself is part of the implementation work.

- **Confidence-band thresholds are calibrated, not assumed.** *Why*: the
  spec requires distinct bands (confirmed/probable/no-match/novel) but not
  specific cut points; picking numbers now, before seeing similarity-score
  distributions on real adversarial test cases, would be arbitrary.

- **Verdict-label normalization is a one-time curated mapping**, not a
  learned classifier. *Why*: 10 agencies' labels is a small, enumerable
  set; a reviewed lookup table is simpler and more auditable than training
  a normalizer, and auditability is itself a requirement of this
  capability (explainable top-k presentation).

## Risks / Trade-offs

- [Risk] The recycling-validation gate finds recycling is *not* a
  measurable phenomenon in this corpus → Mitigation: this design and the
  associated spec's premise must be revisited with the user before
  continuing; the narrower "adversarial paraphrase robustness" framing
  (root B, without the temporal-recurrence angle) may need to replace it
  as the capability's justification.
- [Risk] The corpus is small and its time range is undocumented, so
  apparent "recycling" could be an artifact of limited/skewed coverage
  rather than a real pattern → Mitigation: treat the coverage check
  (volume/theme/time adequacy) as part of the same gate, not a separate
  afterthought; if coverage is inadequate, consider supplementing with
  the other Brazilian fact-check datasets listed in `docs/refs.md` (see
  Open Questions).
- [Risk] Incomplete or incorrect verdict-label normalization silently
  corrupts confidence-band classification (e.g., an unmapped label treated
  as "no verdict") → Mitigation: the normalization mapping must be
  reviewed/spot-checked before it feeds into any classification logic.
- [Risk] CC BY-NC-SA 4.0 licensing restricts the corpus to non-commercial
  use → Mitigation: treat as a standing constraint on any future
  productization decision; not a technical concern for this change.

## Migration Plan

Not applicable — greenfield capability; there is no existing system, data
store, or user-facing behavior to migrate from.

## Open Questions

- If the coverage check under the recycling-validation gate shows
  FactPolCheckBr's ~1,882 claims are insufficient in theme or time range,
  should the corpus be supplemented with one of the other Brazilian
  fact-check datasets listed in `docs/refs.md` (e.g., FACTCK.BR,
  Fake.br-Corpus)? Deferred until that gate's result is known — doesn't
  change this change's spec or approach today, only a possible future
  change's scope.
