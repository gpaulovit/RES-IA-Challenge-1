## Purpose

Give an alert band with the terms that weighed most when no fact-check is similar enough (layer 2), and decide whether that band may be shown (RF-08, RF-14, RN-04, US-08).

## ADDED Requirements

### Requirement: Alert band with signals
The system SHALL expose `classificar(texto: str) -> dict` returning `faixa` in {`muitos_sinais`, `incerto`, `poucos_sinais`} and `sinais`, a list of 2 or 3 terms present in the text, without exposing any probability (RF-08, RNF-06).

#### Scenario: Classify a message
- **WHEN** `classificar` is called with a text that has at least 2 vocabulary terms
- **THEN** it returns a dict with exactly the keys `faixa` and `sinais`, and every term in `sinais` appears in the normalized text

### Requirement: Reproducible single-command training
Training SHALL be run by a single command that writes the model, the metrics and the parameters used, versioned together with DVC, with a fixed random seed (RF-14, RNF-10).

#### Scenario: Two runs with the same data
- **WHEN** training runs twice with the same data, code and parameters
- **THEN** the metrics files are identical

### Requirement: Pre-registered go/no-go
The go/no-go criterion SHALL be written before the first evaluation on the test set: go if macro F1 ≥ 0.75 (RNF-02) and at most 15% of true items in the test set fall in `muitos_sinais` (RNF-03). The test set SHALL come from a period later than training (RN-04).

#### Scenario: Metrics report
- **WHEN** training finishes
- **THEN** `experiments/results/metricas_camada2.json` contains macro F1, the confusion matrix, the false-alarm rate, the metrics per source and the go/no-go decision

#### Scenario: No-go
- **WHEN** the decision is no-go
- **THEN** the report records it and the bot uses only layer 1 (RN-04)
