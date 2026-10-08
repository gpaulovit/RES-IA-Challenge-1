## Purpose

Estimates how likely a new, never-checked Brazilian political news item is to be false, based on
narrative patterns of previously fact-checked hoaxes, and presents that estimate as a calibrated,
explained band rather than a verdict.

## ADDED Requirements

### Requirement: Temporal generalization gate precedes the product
The system SHALL NOT expose a likelihood score to users unless a model trained only on items
published up to a cutoff year has passed the pre-registered temporal generalization criterion on
items published after that cutoff. The criterion (metrics and thresholds) SHALL be recorded before
the held-out period is evaluated.

#### Scenario: Gate evaluated on a later period
- **WHEN** the candidate model is trained on items up to the cutoff year and evaluated on items
  from after the cutoff year
- **THEN** the gate result reports the pre-registered metrics on the held-out period, overall and
  per data source, and records go or no-go against the pre-registered thresholds

#### Scenario: Gate not passed
- **WHEN** the gate result is no-go
- **THEN** no score is exposed through the user-facing interface and the result is recorded with
  the reason

### Requirement: Calibrated likelihood score for new text
The system SHALL return, for a submitted news text, an estimate of the probability that it is
false, calibrated so that among items given an estimate near p, the observed share of false items
is close to p on held-out data.

#### Scenario: Score returned for a valid text
- **WHEN** a user submits a non-empty news text
- **THEN** the system returns a probability estimate between 0 and 1 together with its band

#### Scenario: Calibration is measured, not assumed
- **WHEN** the model is evaluated on held-out data
- **THEN** the evaluation reports a calibration measure alongside discrimination, and the bands
  are derived from the calibrated estimates

### Requirement: Banded presentation with an out-of-pattern state
The system SHALL present the estimate as one of a defined set of bands: compatible with known false
narratives, uncertain, weakly compatible, or outside known patterns. It SHALL use "outside known
patterns" when the text is not semantically close to any narrative the model was trained on,
regardless of the probability estimate.

#### Scenario: Mid-range estimate
- **WHEN** the estimate falls between the lower and upper band thresholds
- **THEN** the system presents the result as "uncertain" and does not lean toward false or true

#### Scenario: Text far from all known narratives
- **WHEN** the submitted text's similarity to every known narrative is below the out-of-pattern
  threshold
- **THEN** the system presents "outside known patterns" and states that the model has no basis to
  assess it

### Requirement: Result is never presented as a verdict
The system SHALL NOT state or imply that a submitted item is true or false. Every response SHALL say
that the result measures similarity to patterns of previously checked hoaxes and SHALL point the
user to fact-checking sources for a verdict.

#### Scenario: High estimate
- **WHEN** the estimate falls in the "compatible with known false narratives" band
- **THEN** the response describes the item as resembling known false narratives, includes the
  limitation notice, and does not use the words "falsa" or "fake" as a conclusion about the item

### Requirement: Explanation by nearest known narratives
The system SHALL show, with each result, the previously checked items most similar to the
submitted text, each with its source agency, date, and verdict label as published by that agency.

#### Scenario: User sees why the score was given
- **WHEN** a score is returned
- **THEN** the response lists the most similar previously checked items with their source, date,
  and the agency's verdict label

### Requirement: Score stability under surface rewriting
The system SHALL keep the band of an item unchanged, within a tolerated rate of band changes
recorded in the design, when the item is rewritten by paraphrase, slang, nickname substitution, or
deliberate misspelling. Negation SHALL NOT be treated as a surface rewrite, because it can invert
the meaning.

#### Scenario: Slang and nickname rewrite
- **WHEN** an item and its slang or nickname rewrite are both scored
- **THEN** both receive the same band in at least the tolerated share of test cases

#### Scenario: Negation evaluated separately
- **WHEN** an item and its negated form are scored
- **THEN** the evaluation reports their results as a separate category and does not count a band
  change as a robustness failure

### Requirement: Verdict label normalization before training
The system SHALL map each source's verdict labels to a single normalized taxonomy before any label
is used for training or evaluation, and SHALL exclude items whose label has no mapping.

#### Scenario: Unmapped label
- **WHEN** an item's source label has no entry in the normalization mapping
- **THEN** the item is excluded from training and evaluation and counted in a coverage report

### Requirement: Input validation
The system SHALL reject empty or malformed input with an explanatory error, without returning a
score.

#### Scenario: Empty text
- **WHEN** a user submits an empty or whitespace-only text
- **THEN** the system returns a validation error and no score
