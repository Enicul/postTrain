# Decision-Node Recording Spec - 2026-07-02

Authoritative specification for **which decision nodes KIWI must record**, so
that every user- or system-made choice becomes a point-in-time-clean,
append-only snapshot that feeds the retrospective system and the post-training
flywheel (see `docs/DECISION_REVIEW_AND_TRAINING_FLYWHEEL.md`).

This spec is the recording contract. The flywheel doc is the *why*; this doc is
the *where* and the *what to freeze*.

---

## Context

An Opus audit of the KIWI copilot (**218/218 tests pass**) mapped **21 decision
nodes** in the live pipeline and located exactly where each node's choice is (or
is not) durably recorded.

In parallel, a build agent shipped a standalone **retrospective module** in the
KIWI repo under `src/retrospective/`:

- `snapshot` / `maturation` / `quadrant` / `aggregate` / `exporter`
- **25/25 tests pass**
- append-only SQLite
- temporal-leakage validation (strict point-in-time check)
- four-quadrant luck-vs-judgment classifier
- process-based reward exporter (postTrain-format episodes)

The module is **uncommitted new files only** - it is standalone by rule and does
not yet wire into the live pipeline (see the integration-seams and constraints
sections below).

---

## The recording principle

> Record every point where the system or the user makes a choice that **cannot
> later be reconstructed from state**. Freeze it at the moment it happens.
> Append-only. Point-in-time clean.

Point-in-time clean means: **every evidence item carries `published_at <=
decision timestamp`.** No future data ever enters a snapshot. This is the same
`as_of` / `published_at` / `point_in_time_allowed` discipline from the citation
work - the temporal-leakage obsession IS the product's integrity guarantee.

### Conflict samples are first-class

Three kinds of conflict get explicit first-class flags on the snapshot, because
they are the **highest-value data for harness and guardrail updates**:

1. **policy vs critic disagreement** - the dual gate's two evaluators diverge.
2. **user overrides the system recommendation** - user does the opposite of what
   KIWI recommended.
3. **user disputes a retrospective verdict** - user rejects the process-quality
   judgment the retrospective assigned.

These three are exactly the episodes that expose where the harness, the gate, or
the judges are miscalibrated. They must never be silently averaged away.

---

## P0 recording gaps (found by the audit - must fix first)

These four are the blocking gaps. Until they are closed, the retrospective loop
cannot reconstruct "why a decision was made" from durable state.

1. **DecisionSnapshot at user decision time** - `api/memory.py:96`
   (`POST /decisions`). Currently stores only `choice` + a short
   `recommended_action` string + `rationale`. It **must freeze**:
   - thesis full text + system confidence
   - boundary (`"I am wrong if ..."`)
   - the evidence set visible at decision time, each item with `published_at`
     and its support label
   - system recommendation
   - gate verdict
   - `user_stage`

   For **ALL** choices **INCLUDING SKIP**.

2. **Skip asymmetry** - `api/memory.py:139` only creates a `Thesis` for
   `take`/`modify`; **skip never captures thesis/boundary**, so *"why I didn't
   buy"* cannot be reconstructed afterward. Skips must snapshot their reasoning
   too. (A skip with a stated thesis and boundary is a full decision, not the
   absence of one.)

3. **Gate verdicts not persisted** - `policy.py:61-80` + `critic.py:44-57`
   return `action` + both reasonings to the caller, and then the result is lost.
   Persist **every gate evaluation** as a durable row: policy verdict, critic
   verdict, fused result, and the triggering terms.

4. **Intent router not trajectory-logged** - `pipeline.py:186-206` is the
   **only LLM call in the pipeline not written to `TrajectoryRecord`**. Log it:
   prompt, decision, and the `fallback-used` flag.

---

## P1 recording improvements

- **As-of enforcement in the live path.** `user_state.build_snapshot(as_of=...)`
  (`user_state.py:82`) is already a correct point-in-time engine: it filters all
  tables `<= now`, produces a content-hashed `snapshot_id`, and suppresses
  forward-looking semantic recall. But the live pipeline never calls it with a
  *past* `as_of`. Wire decision snapshots through it.
- **Generalize the `missing_as_of` verifier audit** from watch-scan-only to all
  evidence kinds (`long_horizon_guardian.py:132-135`).
- **Persist more ephemeral decisions**: notification decisions (currently
  dispatch-only), guardian research-trigger booleans, and opinion-gate context
  snapshots. Add `as_of` to profile synthesis.

---

## The full 21-node inventory (audit reference)

Logged-status is as of the audit.

| # | Node | Location | Logged status |
| ---: | --- | --- | --- |
| 1 | Deterministic intent | `pipeline.py:102` | NOT logged |
| 2 | LLM router | `pipeline.py:186` | NOT trajectory-logged |
| 3 | Symbol resolution | `stock_decision.py:105` | logged |
| 4 | Evidence fetch + status | `pipeline.py:621` | logged, no as-of filter |
| 5 | Triage fact-inference | `triage.py:105` | fully logged |
| 6 | Evidence verification rating | `stock_decision.py:343` | logged |
| 7 | Thesis action + confidence + boundary | `triage.py:232` | logged at generation |
| 8 | Portfolio risk posture | `stock_decision.py:443` | logged |
| 9 | Memory proposal | `stock_decision.py:464` | logged |
| 10 | Memory gate policy + critic | `policy.py:61`, `critic.py:44` | verdict NOT persisted |
| 11 | User decision | `api/memory.py:96` | partial - no snapshot |
| 12 | Thesis creation on decision | `api/memory.py:139` | skip excluded; confidence hardcoded 0.5 |
| 13 | Outcome label | `outcome_review.py:115` | logged with `label_available_at` guardrail |
| 14 | Boundary violation | `watch.py ~109` | logged |
| 15 | Lesson promotion | `proposals.py:83` | full audit trail |
| 16 | Profile synthesis | `profile.py ~104` | no as_of |
| 17 | Opinion gate | `api/opinions.py:217` | no context snapshot |
| 18 | Guardian research trigger | `long_horizon.py:284` | gate boolean ephemeral |
| 19 | Guardian verifier audit | `long_horizon_guardian.py:117` | logged - existing temporal-hygiene check |
| 20 | Loop status transition | `long_horizon.py:191` | logged |
| 21 | Notification decision | `long_horizon.py:267` | NOT persisted |

---

## Guardrail contradictions found (design-intent violations to fix)

These are separate from the recording gaps: they are places where the shipped
behavior contradicts the stated safety design.

1. **Disclaimer suppressed by default.** `SHOW_DISCLAIMER` defaults to `"0"`, so
   `config.footer()` returns `""` (`config.py:151,162-164`) - the *"the decision
   is always yours"* disclaimer **never renders in the default config**.
   **Fix:** default it on.

2. **Never-"buy-now" is prompt-only.** `COMPLIANCE_RULES` (`prompts.py:8-16`)
   instructs the model, but there is **no output-side scrubber** that
   detects/blocks an imperative if the model emits one anyway. **Fix:** add a
   post-generation regex scrubber as a code-level floor - same philosophy as
   postTrain's `risk_gate_rules_v11`: the safety floor lives in versioned code,
   never in prompts.

3. **`stock_decision` path bypasses the dual gate.** It hardcodes
   `requires_user_approval: True` (`stock_decision.py:226,478`) instead of
   routing through `policy.py` / `critic.py`; only `/memory/govern` and
   `/memory/proposals/generate` exercise the dual gate. **Fix:** route all
   proposals through `critic.evaluate`.

---

## Retrospective module integration seams (from the build agent)

- The **decision gate** lives in `stock_decision.py` (there is no `pipeline.py`
  wiring point for it). Outcome-maturation seams are `outcome_review.py` +
  `watch.py`.
- **Enum alignment must be explicit when wiring.** `policy.RiskLevel` /
  `policy.GateAction` and the new module's `Bias` / `SupportLabel` are
  independent string spaces; a silent string mismatch degrades to free text.
- **Timezone.** Existing code parses naive-UTC; decision timestamps must be
  consistently tz-aware/UTC, or the strict `>` leakage check can misfire at
  boundaries.
- **DB layer.** The existing DB layer is async SQLAlchemy; the retrospective
  module is deliberately sync `sqlite3`. Wiring is an **adapter layer**, not a
  shared session.
- **IMPORTANT constraint.** Wiring edits touch existing KIWI files, and the KIWI
  repo currently has **~118 uncommitted local changes**. Actual wiring should
  happen **only after the owner lands or stashes that work.** Until then the
  module stays standalone (its 25 tests run independently).

---

## Reuse map

Do not rebuild what already exists:

- **`TrajectoryRecord` + `/trajectories/export`** already join steps to outcome
  labels - the trajectory-export backbone.
- **`user_state.build_snapshot(as_of)`** is the snapshot engine.
- **`outcome_review`** is already point-in-time-correct.
- The **`Thesis` model** already has `claim` / `boundary` / `review_trigger` /
  `confidence`.
- **`PaperTrade`** already tracks multi-horizon outcomes, including skip.
