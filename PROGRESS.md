# Progress

Last updated: 2026-07-04

## Round 6 Wrap-Up: citation chain CLOSED - capacity null, RL null, data is the lever (2026-07-04)

Two clean negatives closed the citation attribution chain, and the founding "do we need
RL" question now has a measured, task-dependent answer.

**Capacity probe -> capacity is NOT the citation-verdict lever (EXP-2026-07-04-013).**
Held the data fixed (same 122-row class-balanced expanded pool, same frozen test n=31,
letters) and scaled the model 1.5B -> 3B. 3B is WORSE: verdict_acc 0.3871 -> 0.2903,
cite_gold 0.9355 -> 0.9032, fabricated 0.0, mean_reward 0.8742 -> 0.7710. So at this data
size capacity is not the bottleneck (same tiny-data-dip flavor as the 7B escalation SFT
non-monotonicity); "scale up to fix the verdict" is CLOSED. Caveat: single seed each,
n=31, construction-labeled train.

**RL-increment on healthy data -> RL adds exactly 0.0 for the citation verdict
(EXP-2026-07-04-014).** GRPO-letters (1.5B) initialized from the expanded-SFT adapter,
300 train batches (train-time batch verdict_acc reached ~0.94), then frozen-test eval is
DIGIT-IDENTICAL to its SFT init on every metric (verdict_acc 0.3871, cite_gold 0.9355,
fabricated 0.0, mean_reward 0.8742). Digit-identical = the greedy policy did not change;
train reward rose (train-set saturation) with no behavioral change on test. Minor honest
note: one train-time completion emitted a literal "<label>" template artifact (in
reward_trace verdict_mix); it does not appear in the frozen-test outputs and does not
affect the metrics.

**THE SYNTHESIS - "do we need RL, and how much" is TASK-DEPENDENT and now measured
(D-2026-07-04-010).** RL over the best SFT baseline, per task, on the same frozen eval:
escalation routing adds +4.9 pts at 1.5B (0.7495 -> 0.7997) and +0.45 at 3B (0.8428 ->
0.8473 = oracle, capped by the ceiling); the citation verdict adds exactly 0.0 on
class-balanced SFT data. Fabrication was fixed by ACTION-SPACE design, the verdict by DATA
BALANCE - neither by capacity, neither by RL. "Not RL for RL's sake" is now an empirical,
per-task result. The citation attribution chain is CLOSED end to end (action space -> data
-> capacity X -> RL X); the sole remaining live lever is data (collection batch-2 ->
400+). Citation line status: CLOSED pending that data.

Evidence (all local this round; weights git-excluded): `runs/sft_citation3b_expanded/`,
`runs/grpo_citation15_postexp/`. Log ids: EXP-2026-07-04-013 (capacity probe), -014
(RL-increment); D-2026-07-04-010 (task-dependent RL synthesis + chain closed);
CP-2026-07-04-004.

## Round 5 Wrap-Up: DPO beta closure, citation data-scaling confirmed 6x (2026-07-04)

Two lines closed with evidence.

**DPO beta sweep -> over-conservatism is STRUCTURAL (three-method comparison final).**
The F2 next-lever from EXP-2026-07-04-005 (pairs v2 gate-perfect but reward-collapsed)
was a beta sweep. Sweeping beta 0.3 and 0.5 (from beta=0.1) recovers SOME exploration -
success 0.5833 -> 0.6667, reward 0.5213 -> 0.5989 at lambda0.3 - but PLATEAUS ~15 pts of
success / ~0.15 reward below the SFT baseline 0.7495 and never re-crosses the kill line
(delta -0.1506, gate 1.000 throughout). Robust now across 2 pair designs x 3 betas, so
DPO's safety-first / exploration-poor character on this task is STRUCTURAL, not a
hyperparameter accident. Observation (not a failure): beta=0.3 and beta=0.5 converge to
DIGIT-IDENTICAL greedy policies (0.5989 / 0.6667 / 0.2258 / gate 1.0) despite different
loss curves - same greedy argmax trajectory. The three-method comparison is now FINAL:
GRPO = efficiency (analytic oracle at 3B), DPO = safety (gate 1.000 at ~half the
success), SFT = balanced baseline. DPO arm closed for further beta/pair tuning.
(EXP-2026-07-04-010, D-2026-07-04-009.)

**Citation corpus expansion v1 (build).** Committed earlier as b6c909a; backfilled to
the EXPERIMENT_LOG as EXP-2026-07-04-011. +146 construction-labeled TRAIN/dev rows (train
122 / dev 24, NO test) from 21 AI-vertical SEC issuers (40 filings: 10-K 68 / 10-Q 72 /
20-F 5 / 8-K 1), EDGAR submissions API, 0 fetch/anchor failures. Label mix verified 70 /
contradicts 35 / partial 22 / insufficient 19 - the key move: the old train pool had 1
contradicts + 1 partial, so this UN-STARVES the boundary classes. 10.3% blind spot-audit,
93.3% agreement (>=90% gate), one C2 correction; opaque sample_ids; frozen eval untouched.
Combined train pool now 131 + 146 = 277 (target 300-500, one more batch).

**THE D-008 DATA-STARVATION TEST (the payoff).** Re-ran SFT-letters (1.5B) on the
class-balanced EXPANDED train pool (122 rows) and evaluated on the SAME FROZEN test
(n=31, letters): verdict_acc 0.0645 (@62 rows) -> 0.3871 (~6x; also 6x over prompted
0.0968), cite_gold 0.8387 -> 0.9355, fabricated 0.0, mean_reward 0.5323 -> 0.8742.
HYPOTHESIS CONFIRMED: the verdict head was data-starved, specifically CLASS-starved
(contradicts/partial). Attribution chain now COMPLETE: action-space (fixed, fabrication
0) -> data (confirmed today) -> capacity (next probe: 3B on the same data). Honest
caveats: 0.387 is still far from usable; single seed; n=31; construction-labeled train
data (spot-audited 93.3%). Data-scaling path VALIDATED (D-2026-07-04-009); pre-registered
next levers: collection batch 2 -> ~400+, then 3B citation capacity probe, then
GRPO-letters on the expanded pool. (EXP-2026-07-04-012.)

Evidence (all local this round; weights git-excluded): `runs/dpo_v2_beta03_qwen15/`,
`runs/dpo_v2_beta05_qwen15/`, `runs/sft_citation15_expanded/`, dataset
`…/citation_train_expansion_v1/` (commit b6c909a).

## Rounds 3/4 Wrap-Up: multi-seed error bars, Gemma cross-family, citation SFT probe, R6 rescore (2026-07-04)

Closed out the round-3 discussion items and the batch-4 GPU run with the honest
revisions they forced.

**Round 3 (three probes).** F1 - citation LETTERS action space (1.5B, n=31):
the action-space hypothesis is CONFIRMED - letters drove fabricated_rate
0.871 -> 0.0 and cite_gold 0.065 -> 0.742 in the PROMPTED arm alone (harness does the
id copying), and GRPO lifted cite_gold to 0.871; but verdict_acc FELL 0.258 -> 0.097
(the old higher verdict number was partly lucky guessing while citations were
wrong), and GRPO moved cite_gold with verdict flat = component-reward decoupling.
Pre-registered bar (fabricated==0 AND verdict+5) HALF-met -> honest partial. F2 -
DPO pairs v2 (1.5B): success barely moved (0.58 -> 0.5833), reward 0.5213 - the pair
fix is INSUFFICIENT; over-conservatism is not (only) a pair artifact; next lever is a
beta sweep (backlog). F3 - 0.5B temperature probe on the collapsed v2 adapter: T0.7
gate presence 0.0, T1.0 presence 0.25 / per-sample gate_recall 0.0625 -
pre-registered threshold (presence>=0.9) NOT met, so the collapse is GENUINE
KNOWLEDGE LOSS, not a decoding artifact; capacity-floor claim upgraded observed ->
tested.

**Batch 4 (three phases).** Phase A multi-seed {0,1,2}: SFT 1.5B reward@0.3
0.7024 +/- 0.0333 [0.6772,0.7495] - SEED 0 WAS THE BEST, so "trained 1.5B beats
prompted 7B (0.7447)" holds ONLY at seed 0, NOT at the mean (HONEST DOWNGRADE).
GRPO-v2 3B 0.8473 +/- 0.0000, gate 1.000 +/- 0.0 - three seeds hit the analytic
oracle EXACTLY (crown jewel replicated; isolates GRPO sampling variance only). GRPO
0.5B plain 0.4721 +/- 0.1221, gate 0.1667 +/- 0.2357 - collapse in 2/3 seeds (seed 1
partial, gate 0.5, beat SFT) -> collapse is high-probability instability, not
determinism; kill unchanged. Phase B - Gemma 4 cross-family prompted (E2B eff 2.3B /
E4B eff 4.5B): BOTH 0.744/0.7452, gate 0.875, success 0.9375 - Qwen's small-prompted
gate blindness does NOT replicate; cross-family hypothesis REFUTED (family-dependent,
not a universal small-model law); Gemma-2.3B-eff prompted ~ Qwen-7B prompted. Neither
prompted Gemma clears gate 0.99; trained Qwen 3B still leads by ~10 pts -> motivation
stands, sharper. Phase C - citation SFT-letters (1.5B, n=31): verdict_acc 0.0645
(LOWER than prompted 0.0968, cite_gold 0.8387, fab 0.0) - SUPERVISED training ALSO
fails the 5-way verdict, so it is NOT the RL objective's fault; the verdict is
data-starved (62 train rows) / capacity-limited. Next lever: corpus growth 131 ->
300-500 and/or bigger model.

**Also recorded.** Two failures: (F-2026-07-04-005) Gemma venv torch/driver mismatch
(latest torch needed a newer driver than the box's 12050; fixed via cu124 wheels) +
the lesson that a hand-rolled generate smoke test masked a working REAL eval path -
smoke-test through the actual harness; (F-2026-07-04-006) the tooling agent wrote
gemma-3n (2025 family) instead of gemma-4 hub ids, caught at orchestration review and
fixed on-box (sed + commit 40b42e9) - model-id review is part of experiment review,
wrong-family numbers look normal. Offline DUAL-CONVENTION R6 RESCORE: from every run's
dumped `test_preds.jsonl` (rescoreable: grpo_v2_qwen15, dpo, dpo_v2, sft/grpo_v2 3B x3
seeds, sft/grpo_v2 7B, grpo_qwen05 seed1/seed2, grpo_v2_qwen05, gemma e2b/e4b - 14
runs; the seed-0 sft_qwen15 / grpo_qwen15 / grpo_qwen05 / sft_qwen05 runs LACK
dump-preds and are not rescoreable), recomputed gate_recall under R6 (AMD_00 leaves
the gate set, denom 8 -> 7) alongside v0.3 via
`scripts/analysis/rescore_r6.py` -> `runs/r6_rescore_summary.json`. Ruling-driven, not
improvement (D-2026-07-04-005): missers of AMD_00 rise (3B GRPO-v2 8/8 -> 7/7 stays
1.0; gemma 7/8 -> 7/7 = 1.0), gaters were over-gating. env v0.3.1 patch created
(`env_seeds_v0.3.1.json` - AMD_00 requires_human_gate=false + gate_convention field)
next to v0.3; the loader preference order in `escalation_env_v01.py` is DELIBERATELY
UNCHANGED (still `("v0.3","v0.1")`) so future runs opt into v0.3.1 explicitly.

New/updated docs: `docs/PORTFOLIO_INDEX.md` full refresh (error-bar matrix, Gemma row,
crown-jewel + honest-downgrade narrative, R6 three-tier paragraph + rescore pointer,
refreshed honest-limits). See EXP-2026-07-04-004..009, F-2026-07-04-005..006,
D-2026-07-04-006..008, CP-2026-07-04-002.

## Overnight Scale Sweep + DPO + Collapse Ablation + Citation (2026-07-03 -> 07-04)

Second A100 session (GPU 0, env v0.3, test n=48, oracle 0.8473, greedy seed 0),
three nights of runs from yesterday's SFT adapters, all written up with evidence.

**Night 1** ran three follow-ups to the A3 verdict. The gate-seed oversampling
fix (R1, 1.5B) is a NULL RESULT - reward 0.7997 and gate 0.875 are digit-identical
to plain GRPO, because the collapse taxonomy already showed the 1.5B had ZERO
all-violate groups, so the fix targeted a 0.5B disease the 1.5B never had; the sole
missed seed is named (`router_contract_realtool_risk_review_AMD_00`,
cheap-then-escalate vs oracle gate). The DPO arm (R2, beta 0.1) is the MIRROR-IMAGE
of GRPO: gate recall 1.000 but success 0.58 / reward 0.5382 - it nailed safety and
collapsed exploration (pair artifact: rejected == the escalate action). The 0.5B
collapse-prevention ablation (R4, oversample x4 + kl-beta 0.2) REPEATED the collapse
in greedy eval (0.383 / gate 0.00, digit-identical to v1) even though training
SAMPLES kept the gate alive - a sampling-vs-greedy split and a capacity floor.

**Night 2** ran the scale sweep (SFT then GRPO-v2 at each size). The curve is
non-monotonic both ways: 0.5B 0.606/0.50 -> 1.5B 0.800/0.875 -> **3B 0.8473/1.000
(the oracle, the only perfect size)** -> 7B 0.800/0.875. 3B SFT alone hits gate
1.000, and "SFT suffices at 3B" is recorded via the pre-registered bar (GRPO adds
+0.0045). 7B SFT is non-monotonic DOWN (0.7147/gate 0.75, worse than 3B and 1.5B) -
a 160-row LoRA is too thin to move 7B priors.

**Night 3** was the first citation-env training (1.5B, frozen `citation_real_eval_v1`,
n=31). Honest negative: fabricated_rate only fell 0.871 -> 0.742 (bar was == 0) and
verdict_acc dropped 0.2581 -> 0.1935, though cite_gold_rate tripled (0.0645 -> 0.1935).
Diagnosis: verbatim long-id copying is the wrong action space for a 1.5B; citation
env v2 (letter-indexed A-F, harness-mapped) is pre-registered.

Four failures logged (citation launcher vs unfrozen interface, 0.5B collapse-repeat,
citation fabrication / action space, DPO exploration collapse). AMD_00 is escalated
to human review BEFORE any label change. New interviewer front-door index at
`docs/PORTFOLIO_INDEX.md`. All evidence in `scripts/rl/runs/`, weights git-excluded,
8 new manifests re-redacted (logging_dir hostname suffix -> `_REDACTED`). See EXP-2026-07-04-001..003,
F-2026-07-04-001..004, D-2026-07-04-001..004, CP-2026-07-04-001.

## RL Phase 2 GPU Session A1->A2->A3 (2026-07-03)

First real-GPU session of RL Phase 2 on a single A100 80GB: pulled the hardened
`scripts/rl/` chain to the box, set up access, and ran A1->A2->A3 on escalation
env v0.3 (test n=48, 8 gate-required seeds, greedy temp-0, seed 0, lambda=0.3,
oracle test reward 0.8473). **A1** prompted the base Qwen2.5 0.5B/1.5B/3B/7B with
no training: no model passed the kill check, and the diagnosis was that success
rates are already fine (1.5B/7B = 1.0) - what small models lack is gate
discipline (7B gate recall only 0.75, 3B 0.00), so training is motivated.
**A2** argmax-SFT (LoRA, 160 oracle labels, 3 epochs) delivered the headline:
the trained 1.5B (0.7495) beats the PROMPTED 7B (0.7447) - a 4.7x smaller model,
and its gate recall lifted 0.50 -> 0.875. **A3** GRPO (K=8, 400 steps, from the
SFT adapters) split: the 1.5B improved +4.9 reward pts to 0.7981 (within 4.9 of
oracle) with healthy training (KL ~0.3), but gate recall stayed at 0.875 (< 0.99
bar); the 0.5B collapsed - the gate action went extinct under group-relative
advantage (interview-grade failure, F-2026-07-03-003). Pre-registered verdict
recorded honestly: GRPO does not meet the promotion bar at these scales; SFT 1.5B
is the promotable cost-efficient policy and the safety floor stays in versioned
code (D-2026-07-03-003). Three failures logged (missing `rich`, trl API/pin
mismatch, the 0.5B collapse); requirements-rl.txt re-pinned to the validated
trl 0.15.2 / transformers 4.49.0 / peft 0.14.0 + rich env. Evidence rsynced to
`scripts/rl/runs/` (manifests, generations.jsonl, reward_trace.jsonl, evals;
weights git-excluded). See EXP-2026-07-03-001..003, F-2026-07-03-001..003,
D-2026-07-03-003, CP-2026-07-03-002.

## GPU-Launch Hardening (2026-07-03)

The A1->A2->A3 escalation RL scripts (`training-corpus/scripts/rl/`) were
audited runnable-but-unsafe: no checkpoint/resume, no run provenance, failed
runs could be overwritten, no failure/error-correction record. Hardened for the
owner's single-A100 pull-and-run:

- New `run_logging.py`: `new_run_dir` (each run -> `out-dir/<run_id>/`,
  `run_id = <UTC>-<git sha>`, REFUSES to overwrite a non-empty dir),
  `write_manifest` (config, seeds, git sha, pip freeze, `--parent-run`
  linkage), and a `JsonlLogCallback` that persists every `on_log` dict to
  `trainer_log.jsonl`.
- SFT + GRPO trainers: `--seed`, `--grad-accum`, `--resume`, `--parent-run`,
  `save_total_limit=None`; GRPO `--save-steps` (default 50). GRPO reward_fn now
  writes `generations.jsonl` (per completion) and `reward_trace.jsonl`
  (per-batch mean_reward, gate_violation_rate, action_mix) - R3 failure-case
  observability.
- New `monitor_run.py`: zero-dep watchdog, exits nonzero + loud on NaN/inf or a
  dead heartbeat.
- New `GPU_RUNBOOK.md`: exact A1/A2/A3 command order, kill criteria,
  monitoring, what-to-save, and the FAILURE PROTOCOL (keep the dir, write a
  FAILURE_LOG entry, re-run with `--parent-run`).
- `requirements-rl.txt` pinned to known-good (trl 0.11.4 era); `.gitignore`
  excludes run weights/checkpoints (jsonls/manifests/metrics stay committable).

CPU smoke passed: all edited modules import GPU-free, both trainers `--help`
work, `monitor_run.py` correctly flags NaN and dead-heartbeat on a fabricated
run dir. See CP-2026-07-03-001, D-2026-07-03-001.

## Current Direction

The portfolio spine is now the three-task ladder plan:

```text
docs/THREE_TASK_LADDER_PLAN_20260702.md
```

Three tasks (risk reviewer, citation verifier, cost-aware escalation router)
climb one shared ladder from hand rules through prompted LLM and
experience-library (training-free RL) rungs to SFT/GRPO, on frozen holdouts,
with pre-registered kill criteria deciding where each task stops. Weights are
budgeted for exactly one task. See D-2026-07-02-002.

Block A progress:

- A1 done (2026-07-02): `citation_real_eval_v1` is frozen - 131 rows audited
  by blind double annotation + adjudication, 3 labels corrected (2.3%), zero
  test-split changes, conventions C1-C3 pinned. See CP-2026-07-02-002 and
  D-2026-07-02-003.
- A2 done (2026-07-02): `risk_contract_repair_v0.1b` built and
  `risk_real_eval_v1` frozen - 256 real rows normalized from three
  families, 90-row eval blind-audited (17 corrected, 18.9%, conventions
  R1-R5), train rule-synced. Probe: medium recall 0.0 -> 1.00; high/gate
  recall 0.64-0.73 remains as the measured gap for prompt arms. See
  CP-2026-07-02-003 and D-2026-07-02-004.

Block A is complete. Block B (2026-07-02): rules + naive/engineered prompt
arms measured on both frozen rulers via Claude subagents. Headlines: Act 2
(citation) KILLED at rung 3 - engineered prompt takes claude-haiku-4-5 to
0.957, above the rung-4 kill bar, so no citation training is justified at
frontier-family scale; Act 1 (risk) passes the safety half (gate recall
1.000 on every engineered arm) but not accuracy (0.811 < 0.90) and proceeds
to rung 4 (rules+LLM hybrid / experience library on the low/medium
boundary). A label leak through citation sample_ids was caught, quantified
(+11.6 points), and fixed with anonymized ids (F-2026-07-02-006). See
`ladder/blockb_eval_arms_v0.1/REPORT.md`, EXP-2026-07-02-004,
D-2026-07-02-005.

Rung 4 (2026-07-02, same day): Act 1 KILLED. Opus-extracted experience
library + deterministic gate rules v1.1 took hybrid sonnet to 0.978
accuracy / 1.000 gate recall / 0 false gates. The explib initially traded
safety for accuracy on the two contested R3 rows; the dispute was escalated
to the owner, who ruled defense-in-depth (red-line claims always gate),
implemented in code. Two acts now closed without training; Act 3 is the
sole weights candidate. See CP-2026-07-02-004, D-2026-07-02-006,
F-2026-07-02-007.

Act 3 environment (2026-07-02): escalation_env_v0.1 built and frozen - 256
stratified real seeds, cost table from real trace latencies, stochastic
p_cheap_success from a 3-framing blind ensemble (74 seeds in the stochastic
middle), simulator + analytic oracle. Pre-training math shows the oracle mix
is lambda-invariant below lambda=1, so the learnable quantity is inferring
p/gate from query text. See EXP-2026-07-02-006.

Act 3 env arms (2026-07-02): the engineered prompt MATCHES THE ANALYTIC
ORACLE exactly on the 64 observed seeds (all lambdas, gate 1.0). Since the
oracle is the reward ceiling, GRPO has no room to win -> Act 3 is
PROVISIONALLY resolved at rung 3 and the ladder closes with ZERO GPU
training. Provisional because a spend limit truncated engineered coverage to
64/256 (F-2026-07-02-008); the one deferred step is the full engineered
sweep. All three acts now resolve without weights, each with a full evidence
+ dissent trail. Remaining GPU budget unspent by design. See
EXP-2026-07-02-007, D-2026-07-02-007, CP-2026-07-02-005.

RL Phase 2 (2026-07-02): the ladder's three kills opened one honest door -
a small LOCAL model for the router/gate under production cost constraints.
A/B/C plan written (docs/RL_PHASE2_SMALL_MODEL_PLAN.md); all non-GPU
scaffolding built and CPU-verified: Plan A pull-and-run SFT/GRPO scripts +
seed expansion to 1,120, Plan B citation agentic env (cite-validity +
verdict reward, hallucination hard negative), Plan C training-free GRPO
loop. GPU/inference steps (A1 motivation gate, A2/A3 training, B/C runs)
are pull-and-run with pre-registered kill criteria. See EXP-2026-07-02-008,
CP-2026-07-02-006.

Pre-GPU verification (2026-07-02): before any training, the env fidelity
self-check found (C1) no label leakage, (C3) sane penalty, and (C2) a real
gate-ground-truth conflict - the env gated 24 bare buy questions that the
AUDITED risk R4 convention rules no-gate. Owner aligned to R4; env v0.3
(gate-required 64->40, oracle recomputed). Re-running the Act-3 engineered
sweep on v0.3 (full 256): frontier sonnet within 0.2-1.3% of oracle with
gate recall 1.000 -> Act-3 kill CONFIRMED (no longer provisional). The same
prompt on cheaper haiku loses 12.6 reward pts and drops gate to 0.80 - the
concrete motivation for RL Phase 2's small-model column. See
EXP-2026-07-02-009, D-2026-07-02-008, escalation_env_v0.1/FIDELITY_CHECK_v0.3.md.
Next (GPU box): A1 prompted Qwen models -> motivation gate, then A2/A3.

Orchestration round (2026-07-02): a two-agent build/audit round on the KIWI
side, documented here. An Opus QA audit of the copilot (218/218 tests pass)
mapped the 21 decision nodes in the live pipeline and found 4 P0 recording
gaps (no DecisionSnapshot at user-decision time, skip never captures
thesis/boundary, gate verdicts not persisted, intent router not
trajectory-logged) plus 3 guardrail contradictions (disclaimer default-off,
prompt-only buy-now enforcement, stock_decision dual-gate bypass). In
parallel, a build agent shipped the retrospective core module in the KIWI
working tree - `src/retrospective/` (snapshot/maturation/quadrant/aggregate/
exporter), 8 files, 25/25 tests, append-only SQLite, temporal-leakage
validation, four-quadrant luck-vs-judgment classifier, process-based reward
exporter. The module is left UNCOMMITTED by rule: adapter wiring is deferred
until the ~118 uncommitted KIWI files land or are stashed. The authoritative
recording contract was written to `docs/DECISION_NODE_RECORDING_SPEC.md`. See
CP-2026-07-02-007, D-2026-07-02-009, F-2026-07-02-009.

## Current State

The repo has been initialized as a standalone post-training artifact repo for
KIWI interview preparation.

Recording protocol update:

- local experiments now use summary-first recording by default;
- full row-level prediction dumps require explicit `--record-mode full`;
- see `docs/RECORDING_PROTOCOL.md`.

Latest router repair checkpoint:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c
```

Router v0.1c repaired the missing-label contract and real-tool trace shortcut:

| Holdout | Old expanded acc | v0.1c acc |
| --- | ---: | ---: |
| golden_v0.1_router_all | 0.3023 | 0.8895 |
| long_research_repair_25_router_all | 0.4800 | 0.9600 |
| real_tool_trace_pilot_10_router | 0.0000 | 1.0000 |

Candidate social-boundary repair:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1
```

This candidate improves `golden_v0.1_router_all` to 0.9012, but slightly
regresses `real_tool_trace_pilot_10_router` to 0.9000. Keep router v0.1c as the
canonical checkpoint until that tradeoff is repaired.

Six-hour plan checkpoint:

```text
docs/NEXT_6H_PLAN_20260630.md
```

Runtime/KIWI card repairs completed in the Agent workspace before continuing
postTrain:

- Cloudflare Access no longer trusts localhost tunnel traffic as an auth bypass.
- Empty password login fails closed in password mode.
- Static default auth tokens were replaced with per-process random tokens unless
  explicit env tokens are set.
- Gateway settings reject localhost/private/link-local DNS targets in public
  modes.
- Codex search is bounded and races against DuckDuckGo fallback.
- Thesis reasoning-only stream no longer triggers a second non-streaming LLM call.
- Semantic memory sync is debounced on hot search paths.
- Chat pipeline DB session scope is shortened around long market/search/LLM calls.
- Watch and guardian loops now use bounded concurrency for slow external work.

Risk contract repair checkpoint:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1
```

What changed:

- Added 330 contract rows covering `low`, `medium`, and `high`.
- Added explicit `requires_human_gate` labels for high-risk cases.
- Added cases for all-in, leverage, panic selling, retirement concentration,
  guaranteed returns, ignored bearish evidence, position sizing, and
  medium-risk watch-trigger questions.

Risk-only CPU baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1/baselines/risk_contract_repair_probe_v0.1_20260630T145518Z
```

Internal result:

| Split | Accuracy | Macro F1 | Medium support | Medium F1 |
| --- | ---: | ---: | ---: | ---: |
| dev | 0.9970 | 0.9622 | 20 | 0.8889 |
| test | 0.9928 | 0.9073 | 16 | 0.7273 |

Realistic holdout:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1/baselines/risk_contract_repair_probe_v0.1_20260630T145518Z/holdouts/risk_contract_holdout_eval_v0.1_20260630T145518Z
```

| Holdout | Rows | Accuracy | Macro F1 | Decision |
| --- | ---: | ---: | ---: | --- |
| golden_v0.1_risk_all | 181 | 0.3923 | 0.3349 | medium transfer failed |
| long_research_repair_25_risk_all | 25 | 0.0000 | 0.0000 | all medium rows predicted low |

Decision:

`risk_contract_repair_v0.1` fixed the label schema but not the real medium-risk
behavior. Do not use it for GPU fine-tuning yet. Next risk work should add real
long-research medium examples.

Citation contract checkpoint:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1
```

Decision:

Use five citation labels before training: `candidate_evidence`,
`verified_support`, `partial_support`, `insufficient`, and `contradicts`.
Do not train `citation_verifier_repair_v0.3` until real paragraph spans are
collected under this contract.

Real citation span seed:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/real_citation_spans_v0.1
```

What exists:

- 29 real paragraph/list/table-cell span rows.
- 5 source pages: AMD press release, AMD 8-K, Microsoft press release, Micron
  issuer press-release mirror, and NVIDIA News Center.
- 0 final fetch/anchor failures.
- No raw HTML stored; each row keeps source URL, paragraph hash, raw-page hash,
  published date, `as_of`, and support label.

Label distribution:

| Label | Rows |
| --- | ---: |
| `verified_support` | 15 |
| `partial_support` | 6 |
| `insufficient` | 4 |
| `contradicts` | 4 |

Split distribution:

| Split | Rows |
| --- | ---: |
| train | 16 |
| dev | 7 |
| test | 6 |

Decision:

This completes the first real official-source citation seed. It is not enough
for `citation_verifier_repair_v0.3` training by itself; expand to more spans and
audit labels first.

Report/filing source expansion checkpoint:

```text
docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md
```

Decision:

The next source expansion should add company filings, financial reports,
earnings transcripts, financial tables, public research reports, and reputable
news. Paywalled sell-side research should not be stored as full text or used
directly for training. Social/X/Weibo/XHS content remains market radar and task
seed material unless supported by auditable sources.

Report/filing span pack checkpoint (2026-07-02):

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/report_and_filing_spans_v0.1
```

`report_and_filing_spans_v0.1` is now collected and sanity-checked. All plan
minimums pass:

| Target | Plan minimum | Collected |
| --- | ---: | ---: |
| Total rows | 100 | 102 |
| SEC filing rows (10-K/10-Q/6-K) | 30 | 51 |
| Earnings transcript rows | 20 | 25 |
| Public research + reputable news rows | 20 | 26 |

Label distribution: `verified_support` 48, `contradicts` 26,
`partial_support` 15, `insufficient` 13. Splits: train 46 / dev 31 / test 25.
Sources: nine tickers of SEC filings (NVDA, AMD, MSFT, MU, META, GOOGL, AMZN,
AVGO, TSM), six large-cap transcript pages, three SIA releases, the Deloitte
2026 semiconductor outlook, and two AP articles. Every row keeps source URL,
source type/tier, section, span, hashes, `published_at`, `as_of`, and a
license note; no raw HTML/PDF is stored. Scouting fallbacks (Gartner 403,
IDC 404, fool.com pagination, DDG bot wall, missing MU transcript) are
preserved in `failures.json` and `FAILURE_LOG.md`.

Decision:

Combined with the 29-row seed there are now 131 real spans under the five-way
contract. All rows are `requires_human_audit`; the first run produced one
silent label error from a duplicated filing paragraph (F-2026-07-02-002), so
the audit pass is mandatory before `citation_verifier_repair_v0.3`. GPU work
stays blocked.

Portfolio packaging checkpoint:

```text
docs/PORTFOLIO_REPORT_20260701.md
```

What it contains:

- one-sentence interview claim;
- system-shape diagram;
- current data assets;
- router/risk/citation key metrics;
- failure taxonomy;
- why the work is post-training relevant;
- explicit "what we do not claim";
- next work sequence.

Decision:

The 2026-06-30 six-hour plan is now complete. The portfolio report should be
treated as the compact interview narrative until the next data pack or training
run changes the evidence.

Imported from the Agent/KIWI workspace:

- golden training corpus `golden_v0.1`,
- CPU specialist baseline script,
- baseline requirements,
- first CPU baseline run artifacts.

Initial GitHub push is complete.

```text
remote: git@github.com:Enicul/postTrain.git
branch: main
initial commit: 7d64753 docs: initialize post-training artifact repo
learning source registry commit: d048963 docs: add learning source registry
```

## Current Checkpoint

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1
```

Important subpaths:

```text
datasets/
baselines/specialist_cpu_baselines_v0.1/
baselines/specialist_cpu_first_training_20260630T030852Z/
repairs/citation_verifier_repair_v0.1/
repairs/citation_verifier_repair_v0.2/
```

Latest expanded checkpoint:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Canonical expanded CPU baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Latest realistic holdout eval:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z/holdouts/realistic_holdout_eval_v0.1_20260630T083000Z
```

## Baseline Results

| Specialist | Target | Test accuracy | Test macro F1 | Status |
| --- | --- | ---: | ---: | --- |
| router_classifier | route_label | 0.9167 | 0.9368 | usable first baseline |
| risk_reviewer | risk_level | 0.5946 | 0.3986 | weak baseline |
| citation_verifier | support_type | 0.2581 | 0.1441 | data repair needed |

Latest tracked training run:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_first_training_20260630T030852Z
```

## Interpretation

- Router is the first credible specialist baseline.
- Risk reviewer is directionally useful but too weak to use as a gate alone.
- Citation verifier failed on held-out data. `citation_verifier_repair_v0.1`
  produced an error taxonomy and repair probes, but the result still points to
  data repair before GPU work.

## Citation Verifier Repair v0.1

Repair pack:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1
```

Top error types:

| Failure type | Count |
| --- | ---: |
| composite_claim | 22 |
| support_boundary_confusion | 17 |
| source_quality_feature_missing | 10 |
| hard_negative_overaccepted | 8 |
| partial_support_boundary | 6 |
| rare_negative_class_boundary | 6 |
| positive_support_missed | 5 |

Repair probe results:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy | Status |
| --- | ---: | ---: | ---: | --- |
| original citation_verifier | 0.2581 | 0.1441 | 0.4839 | failed baseline |
| citation_verifier_url | 0.2581 | 0.1390 | 0.4839 | source URL/domain alone did not help |
| citation_support_binary | 0.3871 | 0.3767 | 0.5806 | clearer task, still weak |

Decision:

Do not start citation-verifier GPU fine-tuning yet. Build
`citation_verifier_repair_v0.2` with more hard negatives, cleaner positive
official spans, partial-support boundary cases, and rare negative examples.

## Citation Verifier Repair v0.2

Repair pack:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2
```

What changed:

- Added `build_citation_repair_v02.py`.
- Generated train-only citation candidates from the original frozen train split.
- Kept dev/test unchanged for comparability.
- Ran a local ablation before choosing which generated rows to train on.
- Selected dataset-specific augmentation instead of using every synthetic row.

Selected strategy:

| Dataset | Train rows | Added rows |
| --- | ---: | --- |
| citation_verifier_url | 178 | hard negatives + missing evidence |
| citation_support_binary | 148 | hard negatives only |

Repair probe results:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy | Status |
| --- | ---: | ---: | ---: | --- |
| v0.2 citation_verifier_url | 0.3871 | 0.3333 | 0.4839 | improved, still not enough |
| v0.2 citation_support_binary | 0.4194 | 0.4139 | 0.5806 | improved, still not enough |

Decision:

v0.2 is a real repair signal, but it is still not strong enough for citation
verifier GPU fine-tuning. The next step is real span audit, not more synthetic
flooding.

## AI Expanded v0.1 Import + CPU Baseline

Imported curated v0.6 data from the Agent/KIWI workspace into this standalone
repo:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Source curation summary:

| Dataset | Train | Dev | Test |
| --- | ---: | ---: | ---: |
| router_classifier | 6,000 | 1,200 | 1,200 |
| risk_reviewer | 8,000 | 1,600 | 1,600 |
| citation_verifier | 6,000 | 1,200 | 1,200 |
| sft_trajectories | 8,000 | 1,600 | 1,600 |
| preference_pairs | 8,000 | 1,600 | 1,600 |
| grpo_rollouts | 8,000 | 1,600 | 1,600 |

Canonical baseline run:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1 \
  --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines \
  --run-id specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Results:

| Specialist | Target | Test accuracy | Test macro F1 | Majority accuracy | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| router_classifier | route_label | 1.0000 | 1.0000 | 0.1667 | easy-distribution baseline; needs realistic holdout |
| risk_reviewer | risk_level | 1.0000 | 1.0000 | 0.6669 | easy binary schema; do not overclaim |
| citation_verifier | support/verdict | 0.9000 | 0.8978 | 0.3333 | much better than golden v0.1, but synthetic/easy negatives likely help |

Decision:

The expanded schema is learnable and useful for GPU-readiness plumbing, but the
near-perfect router/risk scores indicate an easy/template-heavy distribution.
Before GPU fine-tuning, run external holdouts from real/long-research traces and
add harder boundary examples.

## Realistic Holdout Eval v0.1

Script:

```text
training-corpus/scripts/evaluate_baseline_holdouts.py
```

Command:

```bash
python3 training-corpus/scripts/evaluate_baseline_holdouts.py \
  --run-id realistic_holdout_eval_v0.1_20260630T083000Z
```

Output:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z/holdouts/realistic_holdout_eval_v0.1_20260630T083000Z
```

Results:

| Holdout | Dataset | Rows | Accuracy all rows | Accuracy seen-labels only | Schema gap |
| --- | --- | ---: | ---: | ---: | --- |
| golden_v0.1_router_all | router_classifier | 344 | 0.3023 | 0.3611 | yes |
| golden_v0.1_risk_all | risk_reviewer | 181 | 0.2762 | 0.4464 | yes |
| golden_v0.1_citation_all | citation_verifier | 166 | 0.4819 | 0.6957 | yes |
| long_research_repair_25_router_all | router_classifier | 25 | 0.4800 | 0.4800 | no |
| long_research_repair_25_risk_all | risk_reviewer | 25 | 0.0000 | n/a | yes |
| long_research_repair_25_citation_all | citation_verifier | 417 | 0.0000 | n/a | yes |
| real_tool_trace_pilot_10_router | router_classifier | 10 | 0.0000 | 0.0000 | yes |

Interpretation:

The expanded split was learnable but not robust. External holdouts exposed
schema gaps and distribution shift:

- router expanded data lacks `risk_review` and `clarification_needed`;
- risk expanded data lacks `medium`;
- citation expanded labels do not cover `partial_support`, `insufficient`,
  `contradicts`, `candidate_evidence`, or `search_snippet_candidate_evidence`;
- real tool traces are routed mostly as `financial_calculation`, showing a
  shortcut learned from the expanded synthetic split.

Decision:

Do not start GPU fine-tuning yet. Build a router/risk/citation contract repair
set from real tool traces and long-research rows first.

## Learning Source Registry

`LEARNING_SOURCES.md` has been added as the canonical place to record external
model reports and what we extracted from them.

Current source entries:

| Source | Status | Extracted use |
| --- | --- | --- |
| GLM ARC: Agentic + Reasoning + Coding | adopted as architecture framing | use ARC to explain why KIWI needs reasoning, verifier-rich tasks, agentic loops, and process-level verifiers, while not claiming a GLM-scale unified model |

## Last Verified Commands

```bash
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
python3 training-corpus/scripts/train_specialist_baselines.py --run-id smoke_router_only2 --datasets router_classifier --out-root /tmp/posttrain-baseline-smoke2
python3 training-corpus/scripts/train_specialist_baselines.py --run-id specialist_cpu_first_training_20260630T030852Z
python3 training-corpus/scripts/repair_citation_verifier.py --repair-id citation_verifier_repair_v0.1
python3 training-corpus/scripts/train_specialist_baselines.py --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/repaired_datasets --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/baselines --run-id citation_repair_probe_v0.1 --datasets citation_verifier_url,citation_support_binary
python3 -m py_compile training-corpus/scripts/build_citation_repair_v02.py training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/build_citation_repair_v02.py --help
python3 training-corpus/scripts/build_citation_repair_v02.py
python3 training-corpus/scripts/train_specialist_baselines.py --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/repaired_datasets --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/baselines --run-id citation_repair_probe_v0.2 --datasets citation_verifier_url,citation_support_binary
rsync -a --delete /Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --data-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1 --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines --run-id specialist_cpu_ai_expanded_v0.1_20260630T080225Z
python3 -m py_compile training-corpus/scripts/evaluate_baseline_holdouts.py
python3 training-corpus/scripts/evaluate_baseline_holdouts.py --help
python3 training-corpus/scripts/evaluate_baseline_holdouts.py --run-id realistic_holdout_eval_v0.1_20260630T083000Z
git push -u origin main
```

The imported baseline checkpoint reports:

```json
{"status": "complete", "run_id": "specialist_cpu_baselines_v0.1"}
```

## Next Best Step

Repair the data contracts exposed by realistic holdout eval v0.1:

1. build `risk_contract_repair_v0.1` with `medium` and human-gate semantics;
2. revisit router social repair only after adding real-tool-style capex/source
   support deep-research anchors;
3. define citation label mapping for candidate evidence vs verified support;
4. rerun repaired baselines as probes before any GPU fine-tuning;
5. keep repaired runs in summary recording mode unless full row-level analysis is
   explicitly needed;
6. add Qwen, DeepSeek, Kimi, and MiniMax/WebExplorer source entries using the
   same extracted / not-adopted structure.
