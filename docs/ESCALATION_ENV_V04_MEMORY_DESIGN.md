# Escalation Env v0.4 - Memory-Form Experiment (Pre-Registered) - 2026-07-02

Status: **DESIGNED, NOT YET RUN.** Scheduled after the A1-A3 chain on
escalation env v0.3 completes and is written up. This doc pre-registers the arm
matrix, kill criteria, and data/infra needs BEFORE any arm is measured, so that
every stop/continue decision cites numbers against a bar fixed in advance
(same discipline as `docs/THREE_TASK_LADDER_PLAN_20260702.md` and
`docs/RL_PHASE2_SMALL_MODEL_PLAN.md`).

---

## Motivation

The current escalation env (v0.3) trains a **STATELESS router**: the observable
state is `{user_query, symbol, as_of}` only. This is a documented ceiling, not a
bug - four query classes are structurally **unroutable without memory**:

1. **Anaphora** - "how is it doing today?" has no resolvable referent without
   the prior turn; the symbol is not in the query.
2. **Cache-state-dependent cost** - a filing pulled two hours ago makes the
   "deep" path cheap *now*. The static per-route cost table cannot express a
   cost that depends on what is already in cache; the same route has two
   different true costs depending on history.
3. **User-stage-dependent handling** - a novice and an expert asking the same
   words want different escalation (more scaffolding / gating vs a terse
   expensive-path answer). Identical `user_query` -> different correct action.
4. **Position-context** - a plain price query is actually a boundary-review
   moment when the user holds the stock *with a stated invalidation condition*.
   The query looks like `fast_answer` but the right action is the review path.

The core design question is therefore **NOT** "should we add memory" - it
obviously must be added to lift this ceiling. The question is:

> **In WHAT FORM should state enter a small model?**

This matters because long-context degradation
(lost-in-the-middle / context rot) hits small models hardest. Dumping raw
L0-L3 memory into a 0.5B model's context would drown it - the relevant field is
one line inside pages of history. Our hypothesis:

> A **compressed STRUCTURED state** (~50 tokens:
> `user_stage | active thesis+boundary | cache freshness | recent topic`)
> beats raw history, and training specifically teaches a small model to attend
> to the right fields.

Evidence that model attention is steerable by context artifacts:
F-2026-07-02-006 (eval `sample_id`s leaked gold labels and inflated LLM arms
+11.6 points). If a spurious id can steer attention that hard, a *deliberately*
structured, high-signal digest should be learnable to attend to - and the
inverse (raw history) should be learnable to drown in. That is the measurement.

---

## Pre-registered arm matrix

Same env, same frozen eval seeds, same reward (final correctness
- lambda * accumulated cost) with the hard gate-recall constraint. Only the
**state representation** and the **train/prompt** treatment vary across arms.

| # | Model | State form | Treatment | Role |
| --- | --- | --- | --- | --- |
| 1 | small (Qwen 0.5B/1.5B) | none (`{query, symbol, as_of}`) | post-trained | **baseline** = A3 continuation |
| 2 | small (Qwen 0.5B/1.5B) | **structured digest** (~50 tok) | prompted vs post-trained | **MAIN hypothesis**: training enables compact-memory use |
| 3 | small (Qwen 0.5B/1.5B) | **raw long context** (L0-L3) | post-trained | tests "context drowns small models"; expected < arm 2 |
| 4 | Sonnet | structured digest (same as arm 2) | prompt-only | frontier reference + cost/latency comparison |

Notes:

- Arm 2 is the load-bearing arm: the *prompted vs post-trained* split inside it
  is the direct test of whether training (not just showing the digest) is what
  lets a small model use compact memory.
- Arm 3 is not a strawman we expect to fail quietly - the **gap between arm 3
  and arm 2 quantifies the value of harness-side state compression**. If the
  gap is large, the digest is doing real work; if it is zero, our compression
  thesis is wrong and we say so (see kill criteria).
- Arm 4 is the ceiling/cost anchor: it is not competing on price (a local 0.5B
  trivially wins on tokens and latency), it fixes what "good" looks like so
  the small-model quality gap can be reported as a percentage.

---

## Pre-registered kill criteria

Fixed here before any arm runs. Revise only with a logged reason in
`DECISIONS.md`. Every result below is a first-class deliverable, negative
included.

1. **Main hypothesis kill.** If arm-2 *post-trained* does **not** beat arm-1
   *post-trained* by **>= 3 reward points** at `lambda = 0.3` (with gate recall
   held **>= 0.99**), record honestly: **"memory does not pay at this model
   size."** A small model that cannot convert even a hand-compressed digest into
   reward is evidence the ceiling is not liftable at 0.5B-1.5B, and that is the
   finding.

2. **Compression-thesis kill.** If arm-3 (raw long context) does **NOT**
   collapse relative to arm-2 (digest), record that too - it **falsifies the
   compression thesis** (raw history was fine; the harness-side digest bought
   nothing). We do not get to keep the digest story if the ablation refuses to
   separate.

3. **Cost/speed vs Sonnet.** Measure **tokens + wall-clock latency per routing
   decision** for every arm. The question is *not* who is cheaper (arm 1/2/3
   local 0.5B trivially win) but **how small the quality gap gets**. Report as
   **"% of Sonnet quality at % of Sonnet cost"** (reward-vs-arm-4 and
   tokens/latency-vs-arm-4), so the deliverable is a point on a quality-cost
   frontier, not a single win/lose bit.

---

## Data / infra needed

- **env v0.4 seeds.** Extend the seed schema with two new fields:
  - `memory_context` - the structured digest
    (`user_stage | active thesis+boundary | cache freshness | recent topic`),
    frozen at decision time;
  - `raw_history` - the corresponding L0-L3 raw memory the digest was
    compressed from (arm 3 reads this instead of the digest).
- **New seed construction.** Seeds must come from KIWI conversation/memory data,
  not invented. The decision-snapshot recording spec,
  `docs/DECISION_NODE_RECORDING_SPEC.md`, defines exactly the fields to freeze
  (thesis, boundary, review_trigger, point-in-time evidence set, confidence,
  system recommendation, gate verdict, `user_stage`, and the decision itself,
  point-in-time clean). The digest is a lossy projection of that snapshot; the
  `raw_history` field is the same snapshot's un-projected form. Both must stay
  point-in-time clean (`published_at <= decision timestamp`) so the memory
  experiment inherits the same temporal-leakage guarantee as the rest of the
  artifact.
- **Fidelity restatement.** As with v0.1-v0.3, the known env-fidelity limits
  (model-derived `p`, always-adequate deep path, small real cost sample) are
  restated wherever a v0.4 result is reported; the memory arms add one more:
  the digest is a *hand-specified* projection, so a null result on arm 2 is a
  result about *this* projection, not about all possible memory encodings.

Status: **DESIGNED, NOT YET RUN.** Scheduled after the A1-A3 chain on env v0.3
completes and is written up. No v0.4 seed is built and no arm is measured until
the v0.3 small-model chain has a written verdict, so the memory experiment does
not compete for the same GPU/spend window as the still-open A1-A3 runs.

---

## Honesty rules carried forward

- Two physically separated pools: `memory_context`/`raw_history` digests iterate
  on train/dev seeds only; the frozen eval seeds are scored once per arm at
  temperature 0.
- Every eval batch shown to a model uses anonymized ids (F-2026-07-02-006) - the
  arm-3 raw-history field must be scrubbed of any id that could leak the gold
  action, or the drowning test measures a leak instead of context rot.
- The deterministic gate floor (`risk_gate_rules_v11.py`) stays in code; no
  memory arm is trusted to learn the safety gate. Gate recall is a hard
  constraint on every arm, not a learned objective.
- A negative result (memory does not pay / raw context did not drown / the gap
  to Sonnet is large) is a first-class deliverable, recorded with numbers in
  `DECISIONS.md`.
