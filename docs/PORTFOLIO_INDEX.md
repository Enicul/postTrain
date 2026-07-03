# Portfolio Index — Small-Model Post-Training for a Financial Copilot

*The interviewer front door. Start here; every claim links to its evidence.*

Last updated: 2026-07-04.

---

## 1. The story in one paragraph

We built a financial copilot (KIWI), then treated "where does it fail?" as a
measurement problem rather than a vibe. We defined the target behaviors as
executable environments and rulers, audited and froze the evals so we could not
fool ourselves, measured where prompting alone falls short, and **trained only
where the data said training pays** — post-training small open models (Qwen2.5
0.5B–7B) on a cost-shaped escalation-routing task. The headline is
counterintuitive and reproducible: a **trained 1.5B beats a prompted 7B**, and a
**3B lands exactly on the analytic oracle** while a 7B trained on the same tiny
data does worse than the 3B. Throughout, the hard safety constraint (when to
escalate a risky action to a human) is kept as a **versioned code floor**, not
something we hope RL learns — because our own instrumented RL runs show pure RL
strands exactly that kind of rare, hard constraint. Every negative result is
logged as honestly as every positive one.

---

## 2. Headline table — 4 sizes × {prompted, SFT, GRPO-v2}, plus DPO

Escalation env v0.3, test split n=48 (8 gate-required seeds), greedy decode,
seed 0, λ=0.3. **Analytic oracle reward = 0.8473.** Each cell is `reward / gate_recall`.

| Base model | Prompted | SFT (LoRA, 160 labels) | GRPO-v2 (oversample×4) | Evidence |
| --- | --- | --- | --- | --- |
| **0.5B** | 0.3063 / 0.50 | 0.6061 / 0.50 | **0.383 / 0.00** (collapse) | `runs/a1_prompted/`, `runs/sft_qwen05/…T1505Z…/`, `runs/grpo_v2_qwen05/…T1608Z…/` |
| **1.5B** | 0.6444 / — | 0.7495 / 0.875 | 0.7997 / 0.875 | `runs/a1_prompted/`, `runs/sft_qwen15/…T1506Z…/`, `runs/grpo_v2_qwen15/…T1551Z…/` |
| **3B** | 0.4232 / 0.00 | 0.8428 / 1.000 | **0.8473 / 1.000 = ORACLE** | `runs/a1_prompted/`, `runs/sft_qwen3/…T1623Z…/`, `runs/grpo_v2_qwen3/…T1624Z…/` |
| **7B** | 0.7447 / 0.75 | 0.7147 / 0.75 | 0.7997 / 0.875 | `runs/a1_prompted/`, `runs/sft_qwen7/…T1646Z…/`, `runs/grpo_v2_qwen7/…T1648Z…/` |

**DPO row (1.5B, β=0.1):** 0.5382 / gate 1.000 / success 0.58 — gate-perfect,
reward-collapsed. Evidence: `runs/dpo_qwen15/…T1607Z…/`, `runs/dpo_qwen15_pairs.jsonl`.

**Oracle line:** analytic oracle reward 0.8473 at λ=0.3 (the mix is
λ-invariant below λ=1; the learnable quantity is inferring p_cheap-success and
gate from text). Only the 3B GRPO-v2 cell reaches it to 4 decimals.

**How to read it.** Prompting alone never clears the bar (no size passes the
motivation kill). SFT is the workhorse: the trained 1.5B (0.7495) edges the
prompted 7B (0.7447) — a 4.7× smaller, post-trained model beating a
frontier-of-family prompt. Gate discipline (the hard safety metric) is a
**capacity** phenomenon: it emerges 1.5B→3B under identical SFT (0.875→1.000)
and degrades again at 7B under tiny-data SFT. RL adds real cost gains at 1.5B/7B
but never carries the gate; at 0.5B it collapses.

All runs on one A100 80GB. Weights are git-excluded; every cell links to a run
dir with `run_manifest.json` (config + git sha + pip freeze), `*_eval.json`,
`trainer_log.jsonl`, and for GRPO `generations.jsonl` + `reward_trace.jsonl`.

---

## 3. The five-element interview framework → artifacts

A post-training project is judged on five things. Here is where each lives.

**1 — Target behavior.** The escalation router as an executable environment
(env v0.3): given a KIWI query, choose a first action (cheap / deep / gate) and
an on-fail action, scored by a cost-shaped reward with a −2.0 safety penalty for
failing to gate a risk-review row. Routing is grounded in real KIWI query
classes.
→ `scripts/rl/` (env + reward), `docs/THREE_TASK_LADDER_PLAN_20260702.md`
(router / risk / citation ladder).

**2 — Data & leak prevention.** Frozen, blind-double-annotated rulers
(`citation_real_eval_v1`, `risk_real_eval_v1`), point-in-time-clean seeds, and
anonymized eval ids. We caught a real leak: a spurious identifier steered a small
model's attention **+11.6 points** (F-2026-07-02-006), which is why eval ids are
anonymized and why we treat a small model's attention as steerable by context
artifacts.
→ `docs/DATASETS.md`, `docs/DECISION_NODE_RECORDING_SPEC.md`, `FAILURE_LOG.md`
(F-2026-07-02-006), the frozen rulers under
`…/ladder/…/citation_real_eval_v1`.

**3 — Algorithm & hyper-parameters.** LoRA SFT, GRPO (K=8, group-relative
advantage, oversampling, kl-beta), and DPO — all as versioned scripts with a
per-run manifest recording the exact config, git sha, and pip freeze that ran.
→ `scripts/rl/` (`sft_escalation.py`, `grpo_escalation.py`, `dpo_escalation.py`,
`grpo_citation.py`), every `run_manifest.json`, `scripts/rl/requirements-rl.txt`
(validated pins trl 0.15.2 / transformers 4.49.0 / peft 0.14.0).

**4 — Evaluation.** Pre-registered kill criteria (>= +3 reward over SFT AND gate
recall >= 0.99), a λ sweep (0.1 / 0.3 / 0.6) on every run, the gate constraint as
a first-class metric, and a judge-consistency report so the ruler itself is
audited.
→ `*_eval.json` (kill_check + λ scores in each), `docs/JUDGE_CONSISTENCY_REPORT.md`,
`docs/CAPABILITY_MATRIX.md` (per-model × metric).

**5 — Failures & next.** A dedicated failure taxonomy for the GRPO collapse, this
session's four new failures, the env v0.4 memory design, and citation env v2.
→ `docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md`, `FAILURE_LOG.md`
(F-2026-07-04-001..004), `docs/ESCALATION_ENV_V04_MEMORY_DESIGN.md`,
citation env v2 (D-2026-07-04-002).

---

## 4. Research findings

1. **The collapse mechanism, instrumented.** GRPO's group-relative advantage
   strands a rare hard constraint: when all K completions on a gate seed violate
   identically, within-group advantage is ~0 and the −2.0 penalty yields no
   gradient. The taxonomy quantifies it — 0.5B all-violate rate **0.55 (66/120
   gate groups)** vs 1.5B **0.00 (0/95)** — which is *why* 0.5B collapses and
   1.5B does not. The leading indicator (gate share → 0 in `reward_trace`) fired
   before the eval confirmed it.
   → `docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md`, F-2026-07-03-003.

2. **The 3B oracle.** 3B GRPO-v2 hits 0.8473 = the analytic oracle to 4 decimals,
   and 3B SFT alone already reaches gate 1.000 — "SFT suffices at 3B," recorded
   via the pre-registered bar (D-2026-07-04-001).

3. **Non-monotonic 7B.** 7B SFT (0.7147 / gate 0.75) is *worse* than 3B and 1.5B
   SFT — a 160-row LoRA is too thin to move 7B priors. Scale helps until the data
   is too thin to steer the larger model.

4. **DPO / GRPO mirror image.** On one ruler at 1.5B: GRPO is reward-optimal /
   gate-imperfect (0.7997 / 0.875); DPO is gate-perfect / reward-collapsed
   (0.5382 / 1.000). Neither pure-preference nor pure-RL carries both.

5. **Sampling-vs-greedy split.** At 0.5B, oversampling + kl-beta kept the gate
   action alive in training *samples* (up to 11/16 gate) yet the *greedy* decode
   still collapsed to 0.383 / gate 0.00 — the distribution moved, its mode did
   not. Read the eval mode you will ship, not the sampling stats
   (F-2026-07-04-002).

6. **Action-space lesson (citation).** A 1.5B cannot reliably copy long evidence
   ids, so it fabricates (fabricated_rate 0.742 after training). The fix is
   harness-side — re-render candidates as letter choices (A–F) mapped back by the
   harness — not more RL. "Don't make the model do the harness's job"
   (D-2026-07-04-002, F-2026-07-04-003).

---

## 5. Honest limits — what we do *not* claim

- **Single seed per config.** Every cell is one seed (seed 0, greedy). No
  variance bars; treat small deltas as directional, not significant.
- **Small test split.** Escalation test is n=48 (8 gate seeds); citation is
  n=31. Enough to separate collapse from health, not to certify a production SLA.
- **Simulated, not live.** p_cheap-success comes from a blind-ensemble outcome
  table, not live tool execution; the env is a faithful simulation of KIWI
  routing, not the running product.
- **Single-GPU scale.** One A100 80GB; 7B used batch 8 / grad-accum 2 to fit. The
  7B tiny-data dip may be an lr/rank artifact, not a capability ceiling — un-retuned.
- **Corpus sizes.** SFT is 160 oracle labels; citation training is ~31-row-eval
  scale. The 7B result specifically is a *tiny-data* result.
- **One family, so far.** All sizes are Qwen2.5; the cross-family Gemma 4 arm
  (to test whether the 3B sweet-spot generalizes) is queued, not run.

---

## 6. Links to every major doc

| Doc | What it is |
| --- | --- |
| `docs/THREE_TASK_LADDER_PLAN_20260702.md` | The router/risk/citation ladder — the portfolio spine |
| `docs/DECISION_REVIEW_AND_TRAINING_FLYWHEEL.md` | The review → lesson → training flywheel |
| `docs/DECISION_NODE_RECORDING_SPEC.md` | Decision-node recording spec (leak-clean snapshots) |
| `docs/ESCALATION_ENV_V04_MEMORY_DESIGN.md` | Pre-registered v0.4 four-arm memory-form experiment |
| `docs/CAPABILITY_MATRIX.md` | Per-model × per-metric capability matrix |
| `docs/JUDGE_CONSISTENCY_REPORT.md` | Judge / ruler consistency audit |
| `docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md` | Instrumented GRPO-collapse taxonomy |
| `scripts/rl/GPU_RUNBOOK.md` | GPU runbook (CPU smoke → A1 → A2 → A3, failure protocol) |
| `EXPERIMENT_LOG.md` / `FAILURE_LOG.md` / `DECISIONS.md` | Append-only experiment, failure, and decision logs |
| `PROGRESS.md` / `CHECKPOINTS.md` / `TODO.md` | Progress narrative, checkpoints, and the live queue |
| `docs/PORTFOLIO_REPORT_20260701.md` | Earlier standalone portfolio report |

*Evidence convention: run dirs are under `training-corpus/scripts/rl/runs/`;
weights (`*.safetensors`, `adapter/`, `checkpoint-*/`) are git-excluded, so each
run dir ships its manifest, logs, and eval JSON as the reproducible record.*
