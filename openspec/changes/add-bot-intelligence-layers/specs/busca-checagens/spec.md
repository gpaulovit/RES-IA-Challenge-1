## Purpose

Find agency fact-checks similar to a user message (layer 1) and classify how close the best match is (RF-06, RF-07, RN-05, RN-06).

## ADDED Requirements

### Requirement: Return the k most similar fact-checks
The system SHALL expose `buscar(texto: str, k: int = 3) -> list[dict]` returning up to k fact-checks ordered by decreasing similarity, each with every field of the fact-check base plus `semelhanca` in [0, 1] and `faixa` (RF-06).

#### Scenario: Default search
- **WHEN** `buscar` is called with a non-empty text and no k
- **THEN** it returns 3 items, each with `id`, `alegacao`, `veredito_original`, `veredito_normalizado`, `agencia`, `data`, `link`, `fonte_dataset`, `semelhanca` and `faixa`

#### Scenario: Empty text
- **WHEN** `buscar` is called with an empty or whitespace-only text
- **THEN** it raises `ValueError`

### Requirement: Similarity bands
The system SHALL assign `faixa` from `semelhanca` using thresholds read from `params.yaml`: `ja_checado` at or above the high threshold, `relacionada` between the medium and high thresholds, `baixa` below the medium threshold (RN-05).

#### Scenario: High similarity
- **WHEN** a result has `semelhanca` greater than or equal to the high threshold and no negation mismatch
- **THEN** its `faixa` is `ja_checado`

### Requirement: Negation downgrade
The system SHALL downgrade `ja_checado` to `relacionada` when exactly one of the query and the fact-check contains a negation word (RN-06).

#### Scenario: Query negates the fact-check
- **WHEN** the query "Anitta NÃO retirou o apoio" matches "Anitta retira apoio à candidatura de Lula" above the high threshold
- **THEN** the `faixa` is `relacionada`

### Requirement: Calibrated against the benchmark
The thresholds SHALL be chosen on `data/testes_benchmark.json` so that the correct fact-check is in the top 3 for at least 70% of the 24 rewrites (RNF-04) and at most 2 of the 32 controls are `ja_checado` (RNF-05), with the 6 negation cases reported separately.

#### Scenario: Calibration report
- **WHEN** the calibration script runs
- **THEN** it writes `experiments/results/calibracao_camada1.csv` with top-3 hit rate, controls marked `ja_checado` and negation outcomes for each threshold pair, and stores the chosen pair in `params.yaml`
