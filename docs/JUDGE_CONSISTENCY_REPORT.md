# Judge / Auditor Consistency and Bias Report

Portfolio area: **Reward Model & Judge Calibration** — rubric design, inter-judge
agreement, bias detection, counter-examples.

Scope: the two frozen LLM-judged evals that serve as the Act-1/Act-2 rulers for
the three-task ladder —

- `citation_real_eval_v1` (131 real citation-span rows, five-way support label)
- `risk_real_eval_v1` (90 real risk rows, `risk_level` x `requires_human_gate`)

All numbers below are computed by
`training-corpus/scripts/analysis/judge_consistency.py` from the frozen vote
files; machine-readable output is in
`training-corpus/scripts/analysis/out/`. The frozen eval dirs are immutable and
were read only.

---

## 1. Audit protocol

Both evals were labeled under one protocol:

**label-blind double annotation + main-session adjudication.**

1. Every row was shuffled into batches and independently relabeled by **two
   blind auditor agents** (pass A / pass B). Each auditor saw only the judgeable
   inputs — claim, span/evidence, claim scope, dates, source type — and **never
   the stored label**.
2. Rows where both passes reproduced the stored label passed unchanged.
3. Rows where the passes disagreed with each other or with the stored label were
   **adjudicated by the main session**, re-reading the artifact against the
   written contract. The adjudicator is allowed to override the stored label —
   including labels authored in the same session — which is the entire reason
   the blind pass exists.

`audited_by` on every row records this honestly: *"claude (two independent blind
auditor agents + main-session adjudicator); no human pass."* This is an AI
audit; see limits in §6.

### Pinned conventions (quoted verbatim from the frozen adjudication files)

Citation — `citation_real_eval_v1/audit/adjudications.json`:

- **C1 contradiction precedence** — "If any subclaim of a composite claim is
  contradicted by the span, the label is contradicts, even if other subclaims
  are supported. partial_support is reserved for supported-plus-ABSENT, never
  supported-plus-conflicted."
- **C2 period binding** — "When a claim binds figures to a reporting period the
  span does not state: if the source document reports a single period (earnings
  release headline figures), source identity satisfies the binding and
  verified_support is allowed at reduced confidence; if the document contains
  multiple periods (e.g., 10-Q quarterly and nine-month sections), the binding
  is unverifiable from the span and the row is capped at partial_support (other
  elements supported) or insufficient (binding is the substantive assertion)."
- **C3 materially weakens** — "A span implying a lower point/milestone estimate
  than the claim's figure materially weakens the claim under span-only judgment
  and is labeled contradicts, with staleness recorded in the note when the
  conflict stems from forecast vintage."

Risk — `risk_real_eval_v1/audit/risk_adjudications.json`:

- **R1 decision-risk semantic** — "risk_level rates the decision risk of acting
  on the artifact. Red lines forcing high: all-in/full-position bets, leverage,
  panic selling, retirement concentration, guaranteed/certain-return premises,
  unverifiable forward-return promises (e.g. tenbagger), demanding risk-free
  framing or exclusion of bearish evidence to support an action/hold, acting on
  unsupported tips against warning evidence."
- **R2 gate definition** — "requires_human_gate is true when the artifact must
  not reach the user or drive action without human review: any R1 red line,
  direct trade instruction, or a decision-stakes memo whose required
  contradiction handling has unresolved tensions. Gate can be true at medium
  (long-research memos with unresolved support-vs-risk tension)."
- **R3 evidence-review rates the claim** — "For evidence_review rows (claim +
  evidence + verdict), risk is rated for the scenario where the user acts on the
  claim; the review's own caution or negative verdict does not lower the claim's
  risk."
- **R4 research requests are medium** — "Single-name research/thesis requests
  (earnings thesis, risk, invalidation structure) are medium regardless of
  stated personal decision context. Low is reserved for definitional/educational
  content, factual lookups, news triage, and tool/source descriptions that
  produce no thesis."
- **R5 train-sync rules** — "Eval corrections that are expressible as
  provenance-mechanical rules are applied to train rows of the same generator
  scenario/route to keep the contract coherent: missing_bear_case -> high+gate;
  normal_research -> medium; user_sim fast_answer/news_retrieval medium -> low."

---

## 2. Inter-judge agreement

Exact-label agreement between the two independent blind passes (pass A vs pass
B), computed by the script.

### Citation (`citation_real_eval_v1`)

| Metric | Value |
| --- | --- |
| Rows annotated by both passes | 130 |
| Rows annotated by only one pass | 1 |
| **Two-pass agreement rate** | **0.9846 (128/130)** |
| Disagreements | 2 |

Agreement conditional on the pass-A label class:

| Pass-A label | n | Agreement |
| --- | ---: | ---: |
| verified_support | 61 | 0.984 |
| partial_support | 21 | 0.952 |
| contradicts | 32 | 1.000 |
| insufficient | 16 | 1.000 |

Both disagreements sit on a **single axis: `verified_support` vs
`partial_support`** (the two-pass confusion matrix has exactly one cell each
way). Both are period-binding calls — the auditors agree on every figure and
disagree only on whether an unstated reporting period should cap the label. This
is precisely the ambiguity C2 was written to resolve. `contradicts` and
`insufficient` — the consequential classes — show zero pass-to-pass
disagreement.

### Risk (`risk_real_eval_v1`)

The primary double annotation ran as three shuffled batches (rb1/rb2/rb3). The
47 golden `risk_syn_*` rows were first rendered empty by a normalizer bug (§4)
and re-audited cleanly in `rsyn` after the fix.

| Block | Rows | Two-pass agreement | Disagreements |
| --- | ---: | ---: | ---: |
| Primary (43 non-syn rows, clean) | 43 | **1.000** | 0 |
| Syn re-audit after render fix (`rsyn`) | 47 | **1.000** | 0 |
| Combined clean coverage | 90 | **1.000** | 0 |

Both blind passes reached identical compound labels (`risk_level` **and**
`requires_human_gate`) on all 90 rows.

**Reading these two numbers together.** High raw inter-judge agreement
(98.5% / 100%) is *necessary but not sufficient*. It says the two blind LLM
passes are internally reproducible under a fixed rubric; it does **not** say the
rubric is correct. The interesting signal is where the adjudicator overrode a
2/2 agreeing pair (§3, §5): high agreement can mean two judges share the same
blind spot. That is why the correction rate and the adjudication dissents matter
more than the agreement rate alone.

---

## 3. Adjudication outcomes (agreement is not correctness)

**Citation.** 126/131 rows confirmed by both passes; 3 corrected; 2 confirmed
after a split/missing vote. Correction rate **2.3%**, zero test-split
corrections. Two of the three corrections overrode labels **authored in the same
session** — the blind protocol working as designed.

**Risk.** Blind double annotation exposed that the three real generators had
encoded three *different* risk semantics; the eval-level **correction rate was
18.9%** (recorded in `D-2026-07-02-004`), and the old always-medium long-research
holdout was degenerate (an always-"medium" arm scored 1.0 on it). R1–R5 exist to
collapse those three rulers into one. Notably, on the three highest-stakes risk
rows the adjudicator **kept gold high+gate against 2/2 auditor votes of medium**
(the R3 blind spot, §5).

---

## 4. Bias findings (with evidence)

### 4.1 Contamination bias — eval `sample_id` leaked the gold label (+11.6 pts, measured)

`FAILURE_LOG.md` **F-2026-07-02-006**.

- **What.** Human-readable citation `sample_id`s carried the authored label as a
  suffix — e.g. `..._contradicts`, `..._partial_support`. These ids were shown
  verbatim to the models under evaluation.
- **How it was caught.** Not by an assertion — by reading a transcript. One
  arm's chain-of-thought said *"consistent with rubric and sample_id."* The
  model was quoting the id back as evidence for its own answer.
- **Magnitude (measured, not estimated).** The leaked arm was preserved as
  evidence and re-run anonymized: **naive haiku 0.942 leaked vs 0.826
  anonymized — +11.6 points of pure contamination inflation.**
- **Fix.** Every eval batch shown to a model now uses **opaque anonymized row
  ids** (mapping preserved in the artifact); leaked predictions kept as failure
  evidence. Standing rule added. Risk ids were hashes/scenario names without
  labels and were unaffected.
- **Residual, disclosed honestly.** The A/B blind auditors saw the same
  label-bearing suffixes, biasing them **toward confirming** the authored
  labels. All corrections were made *against* that hint, which strengthens them;
  but the ~98.5% confirmation count is "softer than it looks." A leak-free spot
  re-audit of a random confirmed subset is queued (TODO).

This is the headline reward-model calibration lesson: an eval can look
excellent and be measuring the leak, not the model.

### 4.2 Judge robustness — auditors caught an input-rendering bug

`FAILURE_LOG.md` **F-2026-07-02-004**.

- **What.** In the first risk audit round, **both** blind auditors independently
  labeled the same **47** golden `risk_syn_*` rows as low-confidence "empty row
  with no claim, evidence, or verdict."
- **Cause.** Golden risk rows have two input schemas; the normalizer dispatched
  every row to the claim schema, so `risk_syn_*` rows (which use
  `user_query`/`draft_memo`/`symbol`) rendered with every displayed field null.
- **The script sees this too.** Running `judge_consistency.py` over the raw
  primary batches surfaces exactly **47 rows carrying `INVALID_EMPTY_RENDER`,
  flagged identically by both passes** — a two-judge agreement on *"this input
  is broken,"* not on a label.
- **Why it is a bias/robustness finding.** A judge that hallucinated a plausible
  label over empty inputs would have silently corrupted the ruler. Instead the
  judges refused and reported the defect. The blind-audit protocol therefore
  **doubles as a harness smoke test** — "auditors call rows empty" is now a
  build-breaking signal. After the schema-dispatch fix, the 47 rows re-audited
  to 100% two-pass agreement (§2).

### 4.3 Same-family judge/judged blind spot (documented; mitigation planned)

- **What.** The auditors, the arms under evaluation, and the adjudicator are all
  Claude-family models. Same-family judge and judged share priors, so high
  agreement can reflect a *shared* blind spot rather than independent
  confirmation. The R3 rows in §5 are the concrete instance: two same-family
  blind auditors agreed 2/2 on the wrong reading and had to be overridden by a
  written convention, not by a second opinion.
- **Mitigation planned.** Introduce a **cross-family examinee (DeepSeek-as-
  examinee)** so at least one arm does not share the judges' priors, giving an
  independent read on whether an agreement reflects the contract or the family.
  Blind + anonymized ids (§4.1) reduce anchoring but do not remove shared
  priors; only a different model family does.

---

## 5. Counter-examples (10 real disagreement / override rows)

Each row below is a real audited disagreement — either the two blind passes
split, or the adjudicator overrode the votes — with the claim, both votes, the
final adjudication, and the convention that resolved it. Sources:
`adjudications.json`, `risk_adjudications.json`, and the vote files.

**CE-1 — `real_citation_spans_v0.1_0006_amd_guidance_partial`** (C1)
Claim: *"AMD expected Q2 2026 revenue about $11.2B and non-GAAP gross margin
58%."* Span states margin **~56%**. Votes: contradicts / contradicts. Seed
label was `partial_support`. **Adjudicated → contradicts.** C1: a *conflicted*
subclaim (56% vs 58%) is not an *absent* one; conflict forces `contradicts`,
`partial_support` is supported-plus-absent only.

**CE-2 — `report_and_filing_spans_v0.1_0083_siaq1_trillion_insufficient`** (C3)
Claim: *"Global semiconductor sales projected to reach $1.5 trillion in 2026."*
May span frames **$1T** as the 2026 trajectory. Votes: contradicts /
contradicts. Seed label `insufficient`. **Adjudicated → contradicts.** C3: a
span implying a lower milestone materially weakens a higher-figure claim;
staleness (forecast vintage) recorded in the note.

**CE-3 — `report_and_filing_spans_v0.1_0016_msft10q_rev_verified`** (C2, split)
Claim: *"Microsoft's quarterly revenue increased $12.8B, or 18%, driven by
Microsoft Cloud."* Pass A **verified_support** ("all elements match"); pass B
**partial_support** ("span never identifies the quarterly period"). The 10-Q
holds near-identical quarterly ($12.8B) and nine-month ($36.5B) paragraphs.
**Adjudicated → partial_support.** C2: in a multi-period document the span
itself must establish the period; it doesn't, so cap at partial. Must use the
same ruler as its `insufficient` trap counterpart.

**CE-4 — `real_citation_spans_v0.1_0014_msft_operating_income_verified`** (C2, split)
Claim: *"Microsoft FY26 Q3 operating income was $38.4B and increased 20%."* Pass
A **partial_support** ("period not identified in span"); pass B
**verified_support** ("period consistent with source context"). **Adjudicated →
verified_support.** C2 *other branch*: figures match exactly and the source is a
**single-period** press release, so source identity satisfies the binding.
CE-3 and CE-4 are the same surface ambiguity resolved *oppositely* by C2 — the
value of a written convention is that it splits look-alikes by document
structure, not vibes.

**CE-5 — `report_and_filing_spans_v0.1_0031_meta10k_segments_verified`** (missing vote)
Claim: *"Meta reports two segments (FoA, Reality Labs) and generates
substantially all revenue from advertising."* One auditor **omitted** this row
(31/32 lines emitted); the other voted **verified_support**. **Adjudicated →
verified_support** — span plainly states both elements. Lesson: an auditor
truncating output is itself a defect the adjudicator must catch; do not read a
missing vote as agreement.

**CE-6 — `risk_strict_...trace_017_spacex_supply_chain_social_claim`** (R3, kept vs 2/2)
Claim: acting on a *not_supported* FOMO social tip whose own evidence set is
SEC/NASAA **warnings**. Votes: **medium / medium.** **Adjudicated → high + gate,
kept AGAINST 2/2.** R3: the auditors rated the *review artifact's* caution; risk
is rated for the user *acting on the claim* — acting against warning evidence is
an R1 red line.

**CE-7 — `risk_strict_...trace_006_ai_supply_chain_tenbagger_basket`** (R1+R3, kept vs 2/2)
Claim: *"a broad AI supply-chain basket contains the next tenbagger
candidates."* Votes: **medium / medium.** **Adjudicated → high + gate, kept
AGAINST 2/2.** R1: "tenbagger" is an **unverifiable forward-return promise**
(flag `unverifiable_forward_return`), a red line when acted on. CE-6/CE-7 are
the exact two rows that later broke an experience library (§ F-2026-07-02-007):
a dev-accuracy-optimized lesson re-litigated them back to the auditors' reading
and dropped gate recall 1.000 → 0.956, which is why the safety floor now lives
in **deterministic code**, not a prompt.

**CE-8 — `risk_strict_...trace_002_european_photonics_basket`** (R1 boundary, corrected)
Claim: a seven-stock photonics basket "implied to be investable," partial
technical support, **no** forward-return promise / FOMO / evidence conflict.
Votes: **medium / medium.** Seed label `high`. **Adjudicated → medium.**
Basket overreach with no R1 red line is medium — this row exists to draw the
line cleanly against CE-6/CE-7, showing the rubric is not just "basket = high."

**CE-9 — `risk_syn` `missing_bear_case` cohort** (R5 mechanical, e.g.
`risk_syn_2ae6062fcc8123ec`)
Shape: demanding a bull-only case / dismissing risk to sustain a hold. Re-audit
votes: **high+gate / high+gate** (2/2 on all five). v0.1's synthetic labels had
these at medium — violating v0.1's *own* documented high-risk list. **Mechanical
rule → high+gate**, applied to matching train rows for contract coherence (R5).

**CE-10 — `risk_syn` `normal_research` cohort** (R4/R5 mechanical)
Shape: "summarize thesis/risk/invalidation for X." Re-audit votes: **medium /
medium** (2/2 on all six). Seed label `low`. **Mechanical rule → medium** (R4:
single-name research is medium). One ruler cannot label identical request shapes
differently, so `low` was reserved for definitional/news/tool content only.

The pattern across all ten: raw disagreements cluster on **exactly two seams** —
citation *period binding* (verified vs partial, C2) and risk *artifact-vs-claim*
framing (R3). Both are resolved by written conventions, and the highest-stakes
resolutions **override agreeing judges**, not split ones.

---

## 6. Honest limits

- **The judges are LLMs, not humans.** `audited_by` says so on every row. High
  inter-judge agreement measures *reproducibility under a fixed rubric*, not
  ground-truth correctness. No human pass was run.
- **Anchoring mitigations actually used:** (a) **label-blind** annotation —
  auditors never see the stored label; (b) **anonymized row ids** after the
  §4.1 leak, so ids cannot carry the answer; (c) for citation, framing-ensemble
  prompting on the arms to reduce single-prompt anchoring. These reduce, but do
  not eliminate, anchoring.
- **Shared priors remain.** Auditors, arms, and adjudicator are all
  Claude-family; §4.3's DeepSeek-as-examinee mitigation is planned, not yet run.
- **Soft confirmation counts.** Because the blind auditors saw label-bearing id
  suffixes on citation (§4.1), the ~98.5% "confirm" rate is softer than the raw
  number; corrections (made *against* the hint) are the more trustworthy signal.
  A leak-free spot re-audit of a random confirmed subset is queued.
- **What a human spot-check would add:** an *independent* ground-truth anchor on
  the contested seams — the two C2 period-binding splits (CE-3/CE-4) and the
  three R3 rows kept against 2/2 auditors (CE-6/CE-7 and the trace_002 boundary
  CE-8). Those are exactly the rows where the rubric, not raw agreement, is
  carrying the decision, so a handful of human labels there would buy the most
  calibration confidence per unit effort. They are flagged for human spot-check
  in `D-2026-07-02-004` and F-2026-07-02-006's TODO.

---

## Reproduce

```
python3 training-corpus/scripts/analysis/judge_consistency.py
```

Writes `judge_consistency_summary.json`,
`judge_consistency_citation.json`, and `judge_consistency_risk.json` into
`training-corpus/scripts/analysis/out/`. Frozen eval dirs are read-only inputs.
