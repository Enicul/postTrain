# Three-Task Ladder Plan - 2026-07-02

## Purpose

Produce a verifiable, honest answer to one question, demonstrated live:

```text
On real KIWI tasks, when is prompting enough, when is training-free RL
(an injectable experience library) enough, and when is weight RL (GRPO)
actually worth its cost?
```

The deliverable is not "we ran GRPO". It is a per-task decision record with
numbers: each task climbs the same ladder, stops at the rung where the kill
criteria say further investment is not justified, and the stop itself is a
first-class result. The interview narrative: we did not choose methods, we
chose judging rules, and the data eliminated methods.

## The Ladder

Every task is evaluated on the same frozen holdouts, one column per rung:

| Rung | Arm | Cost class |
| --- | --- | --- |
| 0 | majority / hand-written rules | ~zero |
| 1 | sklearn baseline (already exists) | CPU minutes |
| 2 | LLM, naive prompt | inference only |
| 3 | LLM, engineered prompt (label definitions + few-shot) | inference only |
| 4 | LLM, engineered prompt + experience library (training-free RL) | inference + lesson extraction |
| 5 | small-model SFT LoRA (incl. argmax-label SFT where reward is enumerable) | small GPU |
| 6 | small-model GRPO | GPU + tuning time |

Rules:

- A rung may only be attempted if the rung below is measured on the same
  frozen holdout.
- Rungs 5-6 are budgeted for exactly ONE task. The other tasks stop at rung 4
  by design; their stopping decisions are part of the artifact.
- The experience library is an injectable, versioned, toggleable artifact.
  It is never baked into the system prompt. Only lessons that survive
  regression tests across library versions get promoted into permanent
  harness patches, with the promotion recorded in `DECISIONS.md`.

## The Three Acts (hypotheses, not commitments)

The act-to-winner mapping below is a prior. If measurements disagree, the
measurements win and the narrative changes. Pre-writing the ending would
invalidate the whole artifact.

### Act 1 - Risk reviewer (expected stop: rung 0/3)

Hypothesis: high-risk detection (all-in, leverage, panic selling, human-gate)
is easy for a strong prompted LLM plus a few hard rules; no training is
justified. This is the cheapest act and the one that proves we are not doing
RL for RL's sake.

Dependency: the current realistic medium-risk holdout is broken
(`long_research_repair_25_risk_all` = 0.0 under the v0.1 checkpoint's known
data gap). Build `risk_contract_repair_v0.1b` with real long-research medium
rows and freeze a repaired holdout BEFORE measuring any LLM arm. Measuring on
a broken ruler proves nothing.

### Act 2 - Citation verifier (expected stop: rung 4)

Hypothesis: five-way support classification has systematic error patterns
(partial-vs-verified boundary, sequential-vs-YoY misattribution, figure
swaps, stale forecasts) that contrastive lesson extraction fixes without
touching weights. The traps deliberately embedded in
`report_and_filing_spans_v0.1` are the ammunition for this act, and the
explib on/off toggle on those trap rows is the live demo centerpiece.

Dependency: audit all 131 real span rows (29 seed + 102 new) and freeze the
eval split as `citation_real_eval_v1`. F-2026-07-02-002 already proved one
silent label error slipped through collection; unaudited labels cannot judge
LLM arms.

### Act 3 - Cost-aware escalation router (expected: rungs 5-6 justified)

The task is NOT seven-way route classification. Single-step discrete routing
with a lookup-table reward has an enumerable optimal action per seed, so
argmax-label SFT would match GRPO and the act would collapse. The task is a
two-to-three step escalation policy:

```text
step 1: try the cheap path (memory / fast_answer)
step 2: observe the cheap result signal (answered? confident?)
step 3: finish, or escalate to the expensive path and pay again

reward = final correctness - lambda * accumulated cost
constraint: risk_review recall on safety rows = 1.0 (hard)
```

The optimal decision depends on the stochastic per-seed outcome of the cheap
path, which cannot be enumerated into labels offline. That is where weight RL
has structural room that prompts and lessons cannot reach (lambda cannot be
precisely verbalized).

Environment construction (offline, cheap):

- cost table per route measured from real KIWI traces (median tokens,
  latency), not invented;
- cheap-path outcome table built by running the cheap arm once over all
  train/dev seeds (these runs double as learning-pool rollouts);
- lambda swept over 2-3 values to produce a small quality-cost Pareto front
  instead of one magic number.

Mandatory collapse check: GRPO must beat BOTH the best prompt arm (rung 4)
AND argmax-label SFT (rung 5) to claim justification. Beating only prompts is
not sufficient evidence.

## Kill Criteria (initial; revise only with a logged reason in DECISIONS.md)

| Act | Stop rung 4 or below if... | Then record |
| --- | --- | --- |
| 1 risk | rules+prompted LLM reach >= 0.90 accuracy on repaired risk holdout AND high-risk/human-gate recall >= 0.99 | "training not justified for risk" |
| 2 citation | rung 4 arm reaches >= 0.85 five-way accuracy on `citation_real_eval_v1` AND fixes >= 50% of trap-row failures vs rung 3 | "weights not justified at this scale; small local verifier is a separate future decision" |
| 3 router | GRPO fails to beat max(rung 4, argmax-SFT) by >= 3 points of mean reward, or fails to dominate on the Pareto front, within budget cap | "GRPO not worth it here" - also a publishable honest result |

Act 3 budget cap (hard): 24 A100-hours / ~USD 100 / 5 working evenings for
rungs 5-6 combined. Exceeding the cap without a win IS the result.

## Honesty Rules

1. Two pools, physically separated:
   - learning pool: train/dev seeds only, K=8 samples, temperature ~1.0;
     feeds RL training, lesson extraction, prompt iteration;
   - eval/demo pool: frozen holdouts only, temperature 0, one run per arm.
2. Prompts and experience libraries iterate ONLY on train/dev. One tuning
   pass against a frozen test invalidates that column.
3. Demo subset: 15-20 story rows (trap cases) selected from holdouts, marked
   `split: demo`, replayed from cached traces by default; live rerun
   optional; explib toggled live.
4. Every stop/continue decision cites its kill-criteria numbers in
   `DECISIONS.md`.
5. RL rollouts never flow back into any eval row.

## Rollout Episode Schema (one store feeds all consumers)

```json
{
  "episode_id": "...",
  "task_id": "stable id from the frozen seed pack",
  "split": "train | dev | test | demo",
  "arm": "rules | llm_naive | llm_prompted | llm_prompted_explib_v1 | sft_v1 | argmax_sft_v1 | grpo_v1",
  "group_id": "task_id + arm + batch (GRPO group advantage)",
  "model": {"model_id": "...", "temperature": 1.0, "seed": 17, "max_tokens": 0},
  "prompt": {"prompt_id": "...", "prompt_sha256": "...", "exp_lib_version": null},
  "input": "task payload; large sources referenced by hash, not copied",
  "trace": "full messages + tool calls; large tool results stored as hash + capped excerpt",
  "output": "parsed structured answer",
  "verify": {
    "gold": "...",
    "correct": true,
    "reward_total": 0.0,
    "reward_components": {"accuracy": 0, "format": 0, "safety": 0, "cost_penalty": 0},
    "verifier_version": "..."
  },
  "error": {"failure_type": "tag from the existing error taxonomy", "note": "..."},
  "cost": {"prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0, "usd_est": 0},
  "provenance": {"git_commit": "...", "collection_id": "rollout_store_v0.1", "created_at": "..."}
}
```

Consumer dependencies: GRPO needs `group_id` + K high-temperature samples +
`reward_components` + verbatim trace; training-free RL needs contrastive
high/low reward rollouts + semantic `failure_type`; harness/prompt/skill
patches need `failure_type` clustering + the failing trace position; the live
demo needs `prompt_sha256`/seed/full trace for deterministic replay.

Recording-protocol exception (declared here and in DECISIONS): the rollout
store is a DATA ASSET, not a run log. Row-level retention is intentional and
bounded (K and episode counts capped, large payloads stored as hashes).

## Model Roster

- Big/prompted arms: strongest available model (API if available, otherwise
  strongest local); recorded per episode via `model_id`.
- Small arms: Qwen2.5 0.5B / 1.5B / 3B locally or on the A100. The same small
  model must appear as prompted rungs 2-4 before it appears as rungs 5-6,
  otherwise the before/after comparison is unfair.

## Execution Blocks

```text
Block A - fix the rulers (no LLM arms before this)
  A1 audit all 131 citation rows -> freeze citation_real_eval_v1
  A2 build risk_contract_repair_v0.1b (real long-research medium rows)
     -> freeze repaired risk holdout
Block B - eval pools, rungs 0/2/3, all three acts, temp=0, cost logged
     -> first LLM columns of the comparison table + demo trace cache
Block C - learning pools, K=8, train/dev seeds
     -> also yields act-3 cheap-path outcome table for the escalation env
Block D - experience library v1 per act (contrastive extraction),
     regression test, rung-4 column -> kill-criteria checkpoint for acts 1-2
Block E - surviving act only: argmax-SFT, SFT LoRA, GRPO on A100,
     lambda sweep -> ratio + Pareto deliverable, within budget cap
Block F - demo runner: thin replay shell over the rollout store
     (grows incrementally from Block B; lives in postTrain, not the Agent repo)
```

Rough budget: Blocks B-D are inference-only (a few evenings, dollars);
Block E is the only GPU spend and is capped above.

## Relation to Existing Plans

- Extends, does not replace, `docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md`
  (Act 2 consumes its output).
- `risk_contract_repair_v0.1b` is promoted from "second choice" to a Block A
  dependency.
- GPU discipline from AGENTS.md/TODO still holds: no LoRA/SFT/DPO/GRPO before
  Block D's kill-criteria checkpoint selects the surviving act.
