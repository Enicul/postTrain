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
0.5B–7B) on a cost-shaped escalation-routing task. The crown-jewel result is
**reproducible with zero variance**: a **3B lands exactly on the analytic oracle
(0.8473 / gate 1.000) across three seeds (std 0)**. A secondary result — a
**trained 1.5B beating a prompted 7B** — held at our first seed but did **not**
survive multi-seed averaging, and we say so: it is a seed-0-only claim, downgraded
to a mean±std (0.7024 ± 0.0333). Throughout, the hard safety constraint (when to
escalate a risky action to a human) is kept as a **versioned code floor**, not
something we hope RL learns — because our own instrumented RL runs show pure RL
strands exactly that kind of rare, hard constraint. Every negative result is
logged as honestly as every positive one — including the ones that forced us to
walk a headline back.

---

## 2. Headline table — 4 sizes × {prompted, SFT, GRPO-v2}, plus DPO and Gemma cross-family

Escalation env v0.3, test split n=48 (8 gate-required seeds), greedy decode,
seed-0 eval, λ=0.3. **Analytic oracle reward = 0.8473.** Each cell is
`reward / gate_recall`. **Three configs now carry error bars** (mean ± std over
training seeds {0,1,2}); all other cells are **single-seed (seed 0), flagged `[s0]`**.

| Base model | Prompted `[s0]` | SFT (LoRA, 160 labels) | GRPO-v2 (oversample×4) | Evidence |
| --- | --- | --- | --- | --- |
| **0.5B** | 0.3063 / 0.50 | 0.6061 / 0.50 `[s0]` | **0.4721 ± 0.1221 / gate 0.1667 ± 0.2357** (collapse 2/3 seeds) | `runs/a1_prompted/`, `runs/sft_qwen05/…T1505Z…/`, `runs/agg/grpo_qwen05.json` |
| **1.5B** | 0.6444 / — | **0.7024 ± 0.0333 / gate 0.75 ± 0.102** (seed 0 = 0.7495 is the max) | 0.7997 / 0.875 `[s0]` | `runs/a1_prompted/`, `runs/agg/sft_qwen15.json`, `runs/grpo_v2_qwen15/…T1551Z…/` |
| **3B** | 0.4232 / 0.00 | 0.8428 / 1.000 `[s0]` | **0.8473 ± 0.0000 / gate 1.000 ± 0.0 = ORACLE ×3 seeds** | `runs/a1_prompted/`, `runs/sft_qwen3/…T1623Z…/`, `runs/agg/grpo_v2_qwen3.json` |
| **7B** | 0.7447 / 0.75 | 0.7147 / 0.75 `[s0]` | 0.7997 / 0.875 `[s0]` | `runs/a1_prompted/`, `runs/sft_qwen7/…T1646Z…/`, `runs/grpo_v2_qwen7/…T1648Z…/` |

**DPO rows (1.5B):** v1 (β=0.1) 0.5382 / gate 1.000 / success 0.58; **v2** (rebalanced
"failed-to-escalate" pairs) 0.5213 / gate 1.000 / success 0.5833 — gate-perfect,
reward-collapsed, and the pair fix did **not** buy back exploration (next lever = β
sweep). Evidence: `runs/dpo_qwen15/…T1607Z…/`, `runs/dpo_v2_qwen15/…T0059Z…/`.

**Gemma 4 cross-family row (prompted, no training):** E2B (eff 2.3B) 0.7440 / gate
0.875 / success 0.9375; E4B (eff 4.5B) 0.7452 / gate 0.875 / success 0.9375. Evidence:
`runs/gemma_prompted/{e2b,e4b}_test_eval.json`. **Caveat:** Gemma 4 is a MatFormer with
*effective* (selective-activation) params, not dense — size comparisons to dense Qwen
are approximate.

**Oracle line:** analytic oracle reward 0.8473 at λ=0.3 (the mix is
λ-invariant below λ=1; the learnable quantity is inferring p_cheap-success and
gate from text). Only the 3B GRPO-v2 cell reaches it — and now reaches it on all
three seeds with **std 0**.

**How to read it.** Prompting alone never clears the gate 0.99 bar (no size passes the
motivation kill). The **crown jewel is the 3B GRPO-v2 oracle, replicated ×3 with zero
variance** (caveat: this isolates GRPO *sampling* variance — all three share the seed-0
3B SFT init — not full SFT+GRPO variance). The **"trained 1.5B beats prompted 7B"** line
is **honestly downgraded**: it holds at seed 0 (SFT 0.7495 > prompted 7B 0.7447) but the
3-seed mean (0.7024) sits *below* the prompted 7B, so it is a seed-0-only claim, not a
general one. The **0.5B collapse is a 2/3-seed instability**, not deterministic — seed 1
partially recovered (0.6448 / gate 0.5, beating the SFT baseline) — but no seed comes
near the gate bar, so the kill stands. Gate discipline is **not** a universal small-model
deficit: prompted **Gemma 4 reaches gate 0.875** where prompted Qwen 3B is 0.00 — it is
**family-dependent** (instruction-tuning / safety priors). Still, no prompted model
carries the gate to 0.99, and trained Qwen 3B leads the best prompted Gemma by ~10 pts
*and* gates perfectly — training beats the best cross-family prompt.

All runs on one A100 80GB. Weights are git-excluded; every cell links to a run
dir with `run_manifest.json` (config + git sha + pip freeze), `*_eval.json`,
`trainer_log.jsonl`, and for GRPO `generations.jsonl` + `reward_trace.jsonl`;
multi-seed cells link to a `runs/agg/*.json` aggregate (mean / std / min / max +
per-seed + `eval_paths`).

---

## 2b. The gate is a three-tier defense, and every gate number is reported under two conventions

The "gate" is not a single binary. An owner ruling (D-2026-07-04-005) established a
**three-tier defense** for risky queries: (1) **code red-lines → human gate**, unchanged
— the deterministic `risk_gate_rules_v11.py` floor for red-line pitch / leverage /
concentration language; (2) **concern-type advisory queries** (a worry is expressed but
there is no first-person action intent) → a **smart-review tier** (a stronger model or a
dedicated agent that retrieves evidence + user memory, then judges) — *not* the human
gate and *not* the cheap path; (3) the **human gate is reserved for red-line actions and
genuine user decisions**. Product principle: don't bounce the user's anxiety back at
them — do the evidence/memory work first, then judge.

This ruling reclassified one seed
(`router_contract_realtool_risk_review_AMD_00`, a "what should KIWI quickly check?"
worry with no action intent) from human-gate to smart-review, so it **leaves the gate
set: the test gate denominator drops 8 → 7 (convention R6)**. Because this is a
**ruling, not a model improvement**, every historical gate number is **rescored offline
under both conventions side by side** from the dumped `test_preds.jsonl` — no number is
silently restated. Models that *missed* AMD_00 (played cheap→escalate) see their gate
recall rise purely because a by-ruling non-gate row leaves the miss column; models that
*gated* it were over-gating a no-gate row.

| Run | v0.3 gate (denom 8) | R6 gate (denom 7) | AMD_00 plan |
| --- | --- | --- | --- |
| GRPO-v2 3B (seed 0/1/2) | 8/8 = 1.000 | 7/7 = 1.000 | gate (HIT) — unaffected |
| SFT 3B (s0) | 8/8 = 1.000 | 7/7 = 1.000 | gate (HIT) |
| DPO v1 / v2 1.5B | 8/8 = 1.000 | 7/7 = 1.000 | gate (HIT) — was over-gating |
| GRPO-v2 1.5B (s0) | 7/8 = 0.875 | 7/7 = 1.000 | cheap→escalate (MISS) |
| GRPO-v2 7B (s0) | 7/8 = 0.875 | 7/7 = 1.000 | cheap→escalate (MISS) |
| SFT 7B (s0) | 6/8 = 0.750 | 6/7 = 0.857 | cheap→finish (MISS) |
| Gemma 4 E2B / E4B (prompted) | 7/8 = 0.875 | 7/7 = 1.000 | cheap→escalate (MISS) |
| GRPO 0.5B (s1 / s2) | 4/8 = 0.500 / 0/8 = 0.0 | 4/7 = 0.571 / 0/7 = 0.0 | MISS / MISS |
| GRPO-v2 0.5B (s0) | 0/8 = 0.0 | 0/7 = 0.0 | deep→finish (MISS) |

Full table (all 14 rescoreable runs + per-run AMD_00 plan): **`runs/r6_rescore_summary.json`**,
produced by **`scripts/analysis/rescore_r6.py`** (stdlib only, no GPU). The seed-0
`sft_qwen15` / `grpo_qwen15` / `grpo_qwen05` / `sft_qwen05` runs did not dump
`test_preds` and are **not** rescoreable — stated in the summary rather than glossed.
The env patch itself is **`env_seeds_v0.3.1.json`** (AMD_00 `requires_human_gate=false`
+ `gate_convention` field), placed next to v0.3; the env loader's preference order is
deliberately **unchanged** (`("v0.3","v0.1")`) so future runs opt into v0.3.1 explicitly
rather than silently switching conventions mid-portfolio.

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

**5 — Failures & next.** A dedicated failure taxonomy for the GRPO collapse, six
session failures (including a wrong model-family id caught at review, and a
hand-rolled smoke test that masked a working real path), the env v0.4 memory design,
and citation env v2 (adopted for fabrication; verdict head still data-starved).
→ `docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md`, `FAILURE_LOG.md`
(F-2026-07-04-001..006), `docs/ESCALATION_ENV_V04_MEMORY_DESIGN.md`,
citation env v2 (D-2026-07-04-002/008).

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

2. **The 3B oracle, replicated with zero variance.** 3B GRPO-v2 hits 0.8473 = the
   analytic oracle to 4 decimals on **all three seeds (std 0)**, and 3B SFT alone
   already reaches gate 1.000 — "SFT suffices at 3B," recorded via the pre-registered
   bar (D-2026-07-04-001). Caveat: the ×3 isolates GRPO *sampling* variance (common
   seed-0 SFT init), not full SFT+GRPO variance (EXP-2026-07-04-007).

3. **Multi-seed forced a headline walk-back.** The "trained 1.5B beats prompted 7B"
   line held at seed 0 (SFT 0.7495 > 0.7447) but the 3-seed mean is 0.7024 ± 0.0333,
   *below* the prompted 7B. It is downgraded to a seed-0-only claim; portfolio headlines
   are now mean±std with single-seed cells flagged (D-2026-07-04-006). This is exactly
   why we reseeded.

4. **Collapse is probabilistic, not deterministic.** 0.5B GRPO collapses in **2/3 seeds**
   (0.383 / gate 0.0); seed 1 partially recovered (0.6448 / gate 0.5, beating SFT). And
   the temperature probe showed the collapse is **genuine knowledge loss, not a decoding
   artifact**: on the collapsed adapter the gate action is absent at T=0.7 (presence 0.0)
   and barely surfaces at T=1.0 (presence 0.25 / per-sample gate 0.0625) — below the
   pre-registered 0.9 threshold (EXP-2026-07-04-006/007).

5. **Non-monotonic 7B.** 7B SFT (0.7147 / gate 0.75) is *worse* than 3B and 1.5B
   SFT — a 160-row LoRA is too thin to move 7B priors. Scale helps until the data
   is too thin to steer the larger model.

6. **DPO / GRPO mirror image, and pair fixes have a ceiling.** On one ruler at 1.5B:
   GRPO is reward-optimal / gate-imperfect (0.7997 / 0.875); DPO is gate-perfect /
   reward-collapsed (v1 0.5382, v2 0.5213 / gate 1.000). Rebalancing the pairs
   ("failed-to-escalate" negatives) did **not** buy back exploration (success stuck
   ~0.58) — over-conservatism is not only a pair artifact; next lever is a β sweep
   (EXP-2026-07-04-005).

7. **Gate discipline is family-dependent, not a universal small-model law.** Prompted
   Gemma 4 reaches gate 0.875 (E2B eff 2.3B and E4B eff 4.5B) where prompted Qwen 3B is
   0.00 — so the "small prompted models are gate-blind" hypothesis is **refuted
   cross-family**. Gemma-2.3B-eff prompted ≈ Qwen-7B prompted. Neither clears gate 0.99;
   trained Qwen 3B still leads by ~10 pts and gates perfectly (EXP-2026-07-04-008,
   D-2026-07-04-007).

8. **Action-space lesson (citation) — and where it stops.** A 1.5B cannot reliably copy
   long evidence ids, so it fabricates (fabricated_rate 0.742 after training). Re-render
   candidates as letter choices (A–F) mapped back by the harness and fabrication drops to
   **0.0 in the prompted arm alone** (cite_gold 0.74 → 0.87 after GRPO) — "don't make the
   model do the harness's job." But the **5-way verdict head stays stuck** (~0.06–0.10)
   regardless of method, and a **supervised control also fails it** (SFT verdict 0.0645),
   which *exonerates the RL objective*: the verdict is **data-starved** (62 train rows) /
   capacity-limited, not a reward-shaping problem. Next lever is corpus growth 131 →
   300–500, not more RL (D-2026-07-04-002/008, F-2026-07-04-003).

---

## 5. Honest limits — what we do *not* claim

- **Error bars on three configs only.** SFT 1.5B, GRPO-v2 3B, and GRPO 0.5B carry
  mean±std over seeds {0,1,2}; every other cell is **single seed (seed 0)**, flagged
  `[s0]` in the table — treat those deltas as directional, not significant.
- **GRPO variance isolated, not full-pipeline.** The 3B ×3-seed replication varies the
  GRPO *sampling* seed only (all three init from the same seed-0 3B SFT adapter). A
  full SFT+GRPO seed-varied 3B run (to bound total pipeline variance) is backlog.
- **Small test split.** Escalation test is n=48 (**gate denom 8 under v0.3, 7 under
  R6**); citation is n=31. Enough to separate collapse from health, not to certify a
  production SLA.
- **Simulated, not live.** p_cheap-success comes from a blind-ensemble outcome
  table, not live tool execution; the env is a faithful simulation of KIWI
  routing, not the running product.
- **Single-GPU scale.** One A100 80GB; 7B used batch 8 / grad-accum 2 to fit. The
  7B tiny-data dip may be an lr/rank artifact, not a capability ceiling — un-retuned.
- **Corpus sizes.** SFT is 160 oracle labels; the citation verdict head is trained on
  only 62 rows (data-starved, D-2026-07-04-008). The 7B result specifically is a
  *tiny-data* result.
- **Cross-family is prompted-only, and effective-vs-dense.** The Gemma 4 arm is
  *prompted* (no Gemma training yet); a Gemma SFT/GRPO sweep is backlog. Gemma 4 is a
  MatFormer reporting *effective* (selective-activation) params (E2B ≈ 2.3B, E4B ≈
  4.5B) — comparisons to dense Qwen sizes are approximate.

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
| `docs/RULING_DOSSIER_risk_review_AMD_00.md` | The AMD_00 owner ruling → three-tier gate / Convention R6 |
| `scripts/analysis/rescore_r6.py` → `runs/r6_rescore_summary.json` | Offline dual-convention (v0.3 vs R6) gate rescore |
| `scripts/rl/GPU_RUNBOOK.md` | GPU runbook (CPU smoke → A1 → A2 → A3, failure protocol) |
| `EXPERIMENT_LOG.md` / `FAILURE_LOG.md` / `DECISIONS.md` | Append-only experiment, failure, and decision logs |
| `PROGRESS.md` / `CHECKPOINTS.md` / `TODO.md` | Progress narrative, checkpoints, and the live queue |
| `docs/PORTFOLIO_REPORT_20260701.md` | Earlier standalone portfolio report |

*Evidence convention: run dirs are under `training-corpus/scripts/rl/runs/`;
weights (`*.safetensors`, `adapter/`, `checkpoint-*/`) are git-excluded, so each
run dir ships its manifest, logs, and eval JSON as the reproducible record.*
