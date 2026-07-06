# postTrain — small-model post-training for a financial copilot

We trained cost-aware, safety-gated escalation-routing policies for a real
financial copilot (KIWI) on a single A100 80GB. Every target behavior is an
**executable environment with a pre-registered kill criterion** (≥ +3 reward
over SFT *and* gate recall ≥ 0.99), so the data — not a vibe — decides where
training pays. The campaign is an honesty ledger as much as a results table: it
contains **five evidence-forced self-corrections**, including walking back a
headline that held at seed 0 but not at the 3-seed mean, and re-attributing a
whole "scale curve" to a hyperparameter confound. We drove the first environment
(v0.3) to **saturation** — seven-plus configs land exactly on the analytic
oracle — then froze it as a historical ruler and **rebuilt a harder exam**
(v0.4: memory-dependent twin seeds, dynamic cost, 592 items). The safety
constraint (when to escalate a risky action to a human) is never something we
hope RL learns — it lives as a **versioned code floor** on every arm.

## The headline matrix

Escalation env v0.3, frozen test n=48, greedy decode, λ=0.3. Cells are
`reward / gate_recall`. **Analytic oracle reward = 0.8473.** Error bars are
mean ± std over seeds {0,1,2}; single-seed cells flagged `[s0]`.

| Base | Prompted `[s0]` | SFT (LoRA) | GRPO-v2 | Full-SFT | Full-GRPO |
| --- | --- | --- | --- | --- | --- |
| **0.5B** | 0.3063 / 0.50 | 0.6061 / 0.50 `[s0]` | 0.4721 ± 0.122 / 0.167 ± 0.24 (collapse 2/3) | 0.5899 / 0.75 `[s0]` | **0.7846 ± 0.044 / 0.833 ± 0.12** (oracle 1/3) |
| **1.5B** | 0.6444 / — | 0.7024 ± 0.033 / 0.75 ± 0.10 | 0.7997 / 0.875 `[s0]` | **0.8473 / 1.000 = ORACLE** `[s0]` | **0.8473 / 1.000 = ORACLE** `[s0]` |
| **3B** | 0.4232 / 0.00 | 0.8428 / 1.000 `[s0]` | **0.8473 ± 0.000 / 1.000 ± 0.0 = ORACLE ×3** | **0.8473 / 1.000 = ORACLE** `[s0]` | — |
| **7B** | 0.7447 / 0.75 | 0.7147 / 0.75 `[s0]` | 0.7997 / 0.875 `[s0]` | **0.8473 ± 0.000 / 1.000 = ORACLE ×3** | — |

The two **zero-variance replicated** oracle solvers are **3B LoRA-GRPO** and
**7B full-SFT**. No prompted model ever clears the gate 0.99 bar. Full companion
rows (DPO β-sweep, Gemma-4 cross-family, R6 dual-convention gate rescore) live in
`docs/PORTFOLIO_INDEX.md`.

## Three things to look at if you have 10 minutes

1. **`docs/PORTFOLIO_INDEX.md`** — the claim → evidence map. Every number above
   links to a run dir with its manifest, git sha, and eval JSON.
2. **`docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md`** — the collapse autopsy: GRPO's
   group-relative advantage strands a rare hard constraint (all-K-violate rate
   0.55 at 0.5B vs 0.00 at 1.5B → zero gradient on the −2.0 safety penalty).
3. **`DECISIONS.md` — D-2026-07-04-013 (saturation) + the R6 ruling
   (D-2026-07-04-005)** — judgment under ambiguity: retiring a saturated ruler,
   and reclassifying one gate seed by owner ruling with every historical number
   rescored under both conventions rather than silently restated.

## Honest limits

The deployment claim ("1.5B full-FT reaches oracle") is on a **simulated,
saturated, n=48** env v0.3; the grid-fill oracle cells are single-seed; v0.4 is
**built but not yet run** (no v0.4 policy numbers exist). Full ledger:
`docs/PORTFOLIO_INDEX.md` §5.

## Repo map

```text
docs/PORTFOLIO_INDEX.md           claim→evidence front door (start here)
docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md   instrumented collapse autopsy
docs/PITCH_3MIN_zh.md             spoken 3-minute pitch (中文)
docs/SETUP.md                     env setup + CPU specialist baselines
scripts/rl/                       env + reward + SFT/DPO/GRPO trainers + runs/
DECISIONS.md / EXPERIMENT_LOG.md / FAILURE_LOG.md   append-only ledgers
```
