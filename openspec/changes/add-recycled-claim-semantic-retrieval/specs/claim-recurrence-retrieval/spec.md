## Purpose

Retrieves semantically equivalent, previously fact-checked political claims
for a new input claim — including reworded, slang, or recycled versions
that resurface across time — and classifies each match by confidence
instead of returning a single opaque verdict.

## ADDED Requirements

### Requirement: Corpus indexing for semantic retrieval
The system SHALL index the corpus of catalogued political claims (claim
text and its associated fact-check verdict) into a form that supports
similarity-based retrieval.

#### Scenario: Claim is retrievable after indexing
- **WHEN** a claim from the catalogued corpus has been indexed
- **THEN** a semantically equivalent input query for that claim returns it
  as a retrieval candidate

### Requirement: Robust retrieval under claim rewriting
The system SHALL retrieve the correct catalogued claim for an input claim
that is a paraphrase, slang/nickname substitution, deliberate misspelling,
negation-inverted, or a claim re-emerging in a later time period under
different surface wording — within a tolerable degradation of retrieval
accuracy relative to unmodified claims.

#### Scenario: Reworded historical claim is recognized as recurrence
- **WHEN** an input claim is a reworded version of a claim catalogued in an
  earlier period
- **THEN** the system returns the original catalogued claim among the
  top-k retrieval candidates

#### Scenario: Adversarial paraphrase does not silently fail
- **WHEN** an input claim uses slang, a nickname substitution, or a
  deliberate misspelling of a catalogued claim
- **THEN** the system returns the catalogued claim among the top-k
  candidates, or classifies the query per the confidence-band requirement
  below, rather than returning an unrelated result silently

### Requirement: Confidence-banded match classification
The system SHALL classify each retrieval result into one of a defined set
of confidence bands (confirmed match, probable match requiring review, no
match, novel claim) rather than returning a single binary yes/no verdict.

#### Scenario: Ambiguous similarity is flagged, not resolved silently
- **WHEN** the top retrieval candidate's similarity score falls between
  the confirmed-match and no-match thresholds
- **THEN** the system classifies the result as "probable match" and does
  not present it as confirmed

### Requirement: Responsible handling of partial and mixed claims
The system SHALL NOT apply a catalogued verdict to portions of an input
claim that were not covered by that catalogued check, when the input
claim mixes previously-verified content with new, unverified content.

#### Scenario: Mixed claim is not fully endorsed by a partial match
- **WHEN** an input claim combines a previously catalogued false claim
  with an additional, uncatalogued assertion
- **THEN** the system's response addresses only the catalogued portion and
  marks the additional assertion as not covered/unverified

### Requirement: Exposure of cross-agency verdict divergence
The system SHALL surface when two or more fact-checking agencies have
issued differing verdicts for semantically equivalent claims, rather than
silently selecting one.

#### Scenario: Divergent verdicts are both shown
- **WHEN** a retrieved match corresponds to claims checked by more than one
  agency with different verdicts
- **THEN** the system presents both verdicts and their sources rather than
  resolving the divergence automatically

### Requirement: Explainable top-k presentation
The system SHALL present retrieval results as a ranked list of candidates
with the rationale/evidence for each match rather than a single
unexplained answer.

#### Scenario: User can see why a match was returned
- **WHEN** a query returns retrieval candidates
- **THEN** each candidate is presented together with the source claim/
  verdict text it was matched against, not a single opaque conclusion

### Requirement: Verdict label normalization across agencies
The system SHALL map the heterogeneous verdict labels used by the
corpus's contributing agencies (e.g., "Falsa", "Fake", "Enganosa") to a
single normalized taxonomy before applying confidence-band classification
or partial-match logic.

#### Scenario: Agency-specific label is normalized before classification
- **WHEN** a claim from any contributing agency is indexed
- **THEN** its original verdict label is mapped to the system's
  normalized verdict taxonomy before being used in classification logic
