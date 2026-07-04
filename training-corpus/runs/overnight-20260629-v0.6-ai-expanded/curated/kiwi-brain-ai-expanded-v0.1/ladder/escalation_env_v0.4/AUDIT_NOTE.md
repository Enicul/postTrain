# Escalation Env v0.4 — Build Audit Note

`as_of = 2026-07-04`. BUILDER round. Records the blind spot-audit, the R6 gate
verification, and honest limitations found while assembling the dataset.

## 1. Blind spot-audit (10% stratified, two independent label-blind passes)

**Method.** A 10% sample stratified by `(difficulty_class × split)` — **58 of 592
seeds (9.8%)**, seed `20260704`. Two passes re-derive `(gold_first, gold_on_fail)`
from the README conventions **without reading the stored gold**, then agreement
with stored gold is measured.

**Honesty disclosure.** Both passes run in the **same session / one process**, so
they are two *independent re-implementations of the convention*, not two separate
human raters. They deliberately take **different decision paths** to the same
labels:

- **Pass A** — forward arithmetic: stored `p_cheap_success` + the dynamic deep
  cost (`c_deep_cached` iff `cache_hit ∧ cache_fresh`) → the analytic oracle.
- **Pass B** — reason from the **memory fields** (boundary present? cache fresh?
  stage? referent?) to an *expected* `p` blind to the stored `p`, then oracle.

**Result.**

| Pass | Agreement with stored gold | Disagreements |
| --- | --- | --- |
| A (arithmetic) | **100.0%** | 0 |
| B (memory-field reasoning) | **94.8%** | 3 |

**MIN agreement 94.8% ≥ 90% bar → PROCEED (commit).**

**The 3 Pass-B disagreements** are all `position_context` **twin** seeds where a
boundary holding was *added* by the twin mutation, but the query names the company
in **Chinese** (e.g. "英伟达今天多少钱一股了") while the holding is stored under
its **ticker** ("NVDA"). Pass-B's deliberately-simple blind heuristic matched
boundary relevance by `ticker-substring-in-query`, so it missed the Chinese-name→
ticker link and read the seed as no-boundary (→ cheap) instead of boundary
(→ deep). **The stored gold is correct** — the builder used the persona's actual
holding structure, not a substring heuristic. This is a limitation of the blind
re-derivation, not a gold error, and it is exactly the kind of finding a blind
pass is meant to surface. No relabeling required.

## 2. R6 gate verification (concern-advisory does NOT gate)

Per **D-2026-07-04-005 (R6)**, a concern-type advisory query (a worry with no
first-person ACTION intent) routes to a smart-review tier, **not** the human gate.
All source `control_redline` queries were scanned for first-person action markers
(all-in / leverage / margin / "帮我下/配/算" / concentration verbs, etc.).

- **One** query was found to lack action intent and was **reclassified**:
  - `P-I-02` — **"我要不要现在补仓摊低成本？"** ("should I average down now?") — a
    worry framed as a question, no committed action. Reclassified from
    `control_redline` to a **concern-advisory** control (R6): `requires_human_gate
    = false`, surface = `risk_review` (p = 0.151) → gold `cheap/escalate` (try the
    cheap read, escalate to the smart-review tier on miss). This matches the env
    semantics that "escalate" = the smart-review tier (D-2026-07-04-005).
- Two other action-lacking-*looking* strings retained the gate on inspection
  because they DO carry action intent (`P-B-05` "…全买微软"; `P-I-06`
  "把全部现金押在 VRT 这一只上，帮我操作").
- **Verification:** all **35** gate seeds in the final dataset are `control`
  (redline) class; **no** anaphora / cache_cost / position_context /
  stage_dependent seed carries `requires_human_gate = true`.

## 3. Honest limitations

1. **Synthetic personas.** Source data is `synthetic_opus_v1` (simulated user
   memory), not harvested KIWI logs. The design doc's ideal was real
   decision-snapshots; this dataset is the simulated stand-in, labeled as such in
   provenance.
2. **Anaphora twin artificiality.** Anaphora twins choose the alt referent's
   resolved surface **by search for the reading that flips the gold** (biased to
   the referent's real character). This guarantees discrimination but is more
   constructed than a naturally-occurring referent swap. Recorded so no reader
   over-reads anaphora twin realism.
3. **Twin-pair drop count is 0.** Because three of the four twin classes are
   flip-guaranteed by construction (freshness / boundary / stage all deterministic
   flips) and anaphora is flip-by-search, no pair reached the "same-gold → drop"
   branch. The drop mechanism is present and would fire for a genuinely
   non-discriminative pair (e.g. a single-symbol persona anaphora with no
   gold-flipping alt referent).
4. **Memory-value gap is conservative.** The reported 0.0204 test-split gap is the
   **anaphora-channel** value only (the env degrades the none-arm's `p` solely
   through `p_no_memory`, set only on anaphora by convention). The
   twin-discrimination value of the other three classes is real but shows up as a
   *trained stateless policy's* below-oracle score in the arm matrix, not in this
   oracle-vs-oracle number. See README "THE MEMORY-VALUE GAP".
5. **Fidelity caveats carried forward** from v0.1–v0.3 (model-derived `p`,
   always-adequate deep path, small real cost sample) plus the v0.4 hand-specified
   projection caveat.

## 4. Validator

`python training-corpus/scripts/escalation_env_v04.py --validate <dir>` →
**`VALIDATE OK: 592 seeds ... pass v0.4 schema + twin + leakage + split-integrity
checks`**. Route-word scan of `user_query` + `raw_history` across all 592 seeds:
**0 leaks**. Twin reciprocity + co-location: **0 issues**.
