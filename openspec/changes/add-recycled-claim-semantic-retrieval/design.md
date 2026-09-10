## Context

See proposal.md - Why. Current state: greenfield project — no code, no
chosen tech stack (`openspec/config.yaml` has no `context` yet), and no
existing specs. The only concrete asset is the external
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

## Decisions

- **The recycling-validation gate precedes indexing work.** Before any
  indexing or retrieval implementation, run an empirical check directly on
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
