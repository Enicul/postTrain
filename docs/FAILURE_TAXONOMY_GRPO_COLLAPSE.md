# Failure-Trajectory Taxonomy: GRPO Policy Collapse (Qwen2.5-0.5B)

> **2026-07-04 addendum:** reattributed to adapter capacity — see EXP-2026-07-04-015 / D-2026-07-04-011; full-param 0.5B GRPO does not collapse (reward 0.7533 / gate 0.75). The collapse below is real but is an **adapter-capacity floor (LoRA r=16)**, not a model-capacity floor. Original analysis unchanged.

**Run:** `training-corpus/scripts/rl/runs/grpo_qwen05/20260703T1507Z-e571324/`
**Contrast (healthy):** `training-corpus/scripts/rl/runs/grpo_qwen15/20260703T1520Z-e571324/`
**Config:** Qwen2.5-0.5B-Instruct + LoRA, GRPO K=8, 400 steps, escalation env v0.3, actions {cheap, deep, gate}, λ=0.3, safety penalty −2.0 for un-gated gate-required seeds. Gate-required seeds = 24/160 train (recovered empirically; see below).
**Outcome:** test reward **0.383** (SFT baseline 0.6061, Δ **−0.2231**), **gate_recall 0.00**, cost 0.9455. The policy degenerated toward *always-deep* and the **gate action went extinct**.
**Analysis source:** `training-corpus/scripts/analysis/analyze_grpo_collapse.py` → `collapse_analysis.json` in each run dir. All numbers below are machine-computed from `generations.jsonl` (6400 rollouts/run), `reward_trace.jsonl` (400 batches), `trainer_log.jsonl`.

### How gate-required seeds are identified
The env source is not needed. A seed is *gate-required* iff any **non-gate first action** on it incurs the safety penalty (reward < −1.0), while a gate first action is rewarded. On the 0.5B run this recovers exactly **24/160** seeds — matching the stated config. On gate-required seeds, gate-first → reward **+0.955** (constant); every non-gate first action → reward in **[−2.04, −1.19]**. "Violation" of a gate-required seed = first action ≠ gate.

---

## (a) Timeline of the 0.5B collapse

Action shares are first-action shares over raw rollouts, per 50-step window. "All-violate rate" = fraction of gate-required-seed K-groups (all 8 completions) that violated → **zero within-group reward variance → zero GRPO advantage → zero gradient** on exactly the seeds that most need learning signal.

| Steps | gate share | deep share | cheap share | gate-req all-violate rate (groups) | KL (window end) |
|------:|-----------:|-----------:|------------:|-----------------------------------:|----------------:|
| 1–50    | **0.626** | 0.076 | 0.297 | 0.00 (0/20)  | 0.95 |
| 51–100  | 0.370 | 0.158 | 0.472 | 0.00 (0/8)   | 1.59 |
| 101–150 | 0.136 | 0.369 | 0.495 | **0.421 (8/19)** | 5.07 (peak) |
| 151–200 | **0.019** | 0.593 | 0.389 | 0.636 (7/11) | 4.68 |
| 201–250 | 0.019 | 0.693 | 0.289 | 0.722 (13/18) | 4.14 |
| 251–300 | 0.019 | 0.662 | 0.319 | 0.867 (13/15) | 2.65 |
| 301–350 | 0.018 | 0.642 | 0.340 | 0.769 (10/13) | 2.12 |
| 351–400 | 0.015 | **0.696** | 0.289 | **0.938 (15/16)** | 1.68 |

**Narrative.**
- **Gate death is early and fast.** Gate first-action share collapses from **62.6% (steps 1–50) → 13.6% (101–150) → 1.9% (151–200)** and never recovers. By step 150 gate is functionally extinct; the residual ~1.5–1.9% is noise from the 24 gate seeds still occasionally sampled, not a policy that chooses to gate. Aggregate gate-seed violation rate rises from **70.7% (steps 1–200) to 97.0% (steps 201–400)**.
- **Deep collapse fills the vacuum.** Deep share rises inversely, 7.6% → 69.6%, becoming the dominant degenerate route.
- **The zero-advantage trap deepens as gate dies.** All-violate rate on gate-required groups goes **0.00 → 0.42 (step ~101–150) → 0.94 (step 351–400)**. Overall across the run: **0.55 (66/120 gate-required groups were all-violate)**. Once a group is all-violate, GRPO produces no gradient to rescue the gate action — the collapse is self-reinforcing.
- **KL trajectory.** Init KL is an artifact-high **36.99 @ step 10** (LoRA warm-start transient), drops to ~0.8, then **climbs past the >1.5 danger line at step 70 (1.35→2.60) and peaks at 5.07 @ step 150** — exactly when gate goes extinct. It settles to **~2.1** over the last quarter (still 6× the healthy run's 0.36). KL crossing 1.5 and staying there is the leading indicator; the eval-time gate_recall=0 is a lagging confirmation.
- **Reward-penalty spikes.** 7 batches went mean_reward < −1.0: batches **107 (−1.32), 124 (−1.26), 238 (−1.05), 285 (−1.34), 357 (−1.54), 371 (−1.51), 385 (−1.41)** — each a batch that drew multiple gate-required seeds while the policy had no gate action left, taking the −2.0 penalty across the group (`gate_violation_rate = 1.0`).

---

## (b) Failure taxonomy (counts over all 6400 rollouts, 0.5B)

| Category | What it is | Count | % of rollouts |
|---|---|---:|---:|
| **gate-extinction** (deep on gate-required seed) | Should gate; routed *deep* → −2.0 safety penalty. Signature of gate death. | **559** | 8.7% |
| **cost-blind cheap on hopeless seed** (cheap on gate-required seed) | Should gate; routed *cheap* → safety penalty. Cheapest action on a seed where only gate is safe. | **250** | 3.9% |
| **deep-collapse** (deep on non-gate seed) | Degenerate always-deep routing; often over-pays cost where cheap would score similar/better. | **2552** | 39.9% |
| cheap on non-gate seed (mostly benign) | Cost-optimal on many seeds; not a failure per se but part of the bimodal deep/cheap-only policy. | 2062 | 32.2% |
| gate on non-gate seed (over-caution residue) | Early SFT-inherited caution; mostly in steps 1–100, decays with gate extinction. | 826 | 12.9% |
| **correct gate** (gate on gate-required seed) | The behavior being extinguished. | **151** | 2.4% |
| parse fallbacks (unparseable completion) | **0** in this run — the model always emitted a parseable first action. | **0** | 0.0% |

Total gate-required-seed rollouts = 960; of these only **151 (15.7%)** were correctly gated, **809 (84.3%)** violated (559 deep + 250 cheap). **Sum of all negative reward over the run = −1216.8**, essentially all of it from the 809 gate violations.

**Note on `parse_fallback`:** the taxonomy prompt asked to verify parse fallbacks as a category. Both the raw `parsed_plan` field (0 empty) and the `reward_trace` `action_mix.parse_fallback` counter (0/6400) confirm **no parse failures occurred** in either run. Collapse here is purely a *routing-distribution* failure, not a format/decode failure.

---

## (c) Side-by-side with the healthy 1.5B run

Same config, same env, K=8, 400 steps; only model size differs (0.5B → 1.5B). The 1.5B run recovered 19/160 gate-required seeds (different train sample).

| Metric | 0.5B (collapsed) | 1.5B (healthy) |
|---|---:|---:|
| Test reward @λ0.3 | **0.383** | **0.7981** |
| Δ vs SFT baseline | −0.2231 | +0.0486 |
| **gate_recall** | **0.00** | **0.875** |
| gate share, steps 1–50 | 0.626 | 0.241 |
| gate share, steps 351–400 | **0.015** (extinct) | **0.140** (alive) |
| deep share, steps 351–400 | 0.696 | 0.374 |
| **overall gate-req all-violate rate** | **0.55 (66/120)** | **0.00 (0/95)** |
| all-violate rate, last window | 0.938 (15/16) | 0.000 (0/13) |
| KL: max | 36.99 (init transient) | 3.62 |
| KL: settled (last quarter) | **2.11** | **0.36** |
| batches with mean_reward < −1.0 | **7** | **0** |

The decisive difference: **at 1.5B, no gate-required K-group ever went all-violate (0/95).** Every group that contained gate-required seeds retained at least one gated completion → non-zero within-group advantage → a gradient pointing back toward gate. The gate action stayed alive (10–24% share throughout) and KL never ran away (settled 0.36). At 0.5B, 55% of such groups collapsed to all-violate, gate got no gradient, and it went extinct.

---

## (d) Mechanism: group-relative advantage → zero gradient on rare high-penalty seeds

GRPO computes each completion's advantage **relative to its own K-group mean** for that prompt/seed:
`A_i = (r_i − mean_k r_k) / std_k r_k`.

On a **gate-required seed**, reward is bimodal and near-degenerate:
- gate first action → **+0.955** (constant), or
- any non-gate first action → **≈ −1.3 to −2.0** (constant per seed).

If all K=8 completions for that seed's group choose non-gate (all-violate), then `r_1 = … = r_K` ⇒ `std ≈ 0` and `A_i ≈ 0` for every completion ⇒ **no gradient** — neither punishing the violation nor rewarding gate, because there was no gated completion to contrast against. The seed contributes *nothing* to learning precisely when the policy has already stopped gating it.

This is a **rare-event × high-penalty × on-policy-sampling** trap:
- gate-required seeds are only **24/160 = 15%** of train, so they are sparsely sampled;
- once gate share dips, the probability that all 8 samples for such a seed avoid gate rises sharply;
- from then on the group is silent, and the gate action decays under gradient pressure from the abundant non-gate seeds (where deep/cheap dominate) with no counter-signal.

**Quantified difference in how often the trap fired:**
- **0.5B: 66/120 gate-required groups (55%)** were all-violate — rising monotonically 0.00 → 0.42 → 0.94 across training. Self-reinforcing extinction.
- **1.5B: 0/95 (0%)** — the stronger model kept enough gate probability mass that every group had a gated exemplar, so the advantage signal survived and gate was continuously reinforced.

The collapse is therefore not a reward-shaping bug (the reward function is identical and correct in both runs) — it is an **exploration/coverage failure specific to the weaker policy** interacting with group-relative advantage on low-frequency, high-variance-of-outcome seeds.

---

## (e) Early-warning checklist (signals that predicted collapse *before* eval)

All of these were visible in the training traces well before the eval reported gate_recall=0:

- [x] **Gate first-action share → 0.** Dropped below 5% by step ~150 (window 151–200: 1.9%). *A dying low-frequency action share is the single earliest signal.* Trip-wire: gate share < 0.10 for 2 consecutive windows.
- [x] **Gate-required-group all-violate rate climbing.** Crossed 0.4 at step ~101–150, before the eval. Trip-wire: all-violate rate > 0.25 on any window.
- [x] **KL crossing and holding > 1.5.** Crossed at step 70, peaked 5.07 @ step 150, settled ~2.1. Healthy run stayed ≤ 0.68 after step 120. Trip-wire: settled KL > 1.0.
- [x] **Batch-371-style reward spikes to ≈ −1.5 with `gate_violation_rate = 1.0`.** Seven such batches (107, 124, 238, 285, 357, 371, 385). Each is a batch that drew gate-required seeds the policy could no longer gate. Trip-wire: any batch mean_reward < −1.0.
- [x] **Deep share monotonically rising toward a single-mode policy** (7.6% → 69.6%). Trip-wire: any single action share > 0.6.

If any two of these fire together (gate share collapsing **and** KL > 1.5), abort/adjust before burning the remaining budget — eval will confirm gate_recall ≈ 0.

---

## (f) Pre-registered fixes this motivates

The mechanism (§d) points to fixes that restore within-group advantage on gate-required seeds and/or slow the policy drift:

1. **Gate-seed oversampling → mixed groups (primary fix).** Oversample gate-required seeds and/or force group composition so each K-group mixes gate-required and non-gate prompts, guaranteeing at least one gated exemplar and thus non-zero advantage even as gate probability falls. This directly attacks the 55% all-violate rate. **Run R1 tonight tests exactly this.**
2. **Larger K.** With K=8 and gate probability p, P(all-violate) = (1−p)^8; a larger K lowers the chance a group goes fully silent for any given residual gate probability, keeping the gate gradient alive longer.
3. **Explicit KL control.** The 0.5B KL ran to 5+ and settled at ~2.1 vs the healthy 0.36. A tighter KL coefficient / target-KL schedule would slow the drift away from the SFT gate behavior, buying time for the advantage signal to correct.

Secondary levers to hold in reserve: per-action reward-baseline / advantage flooring for gate-required seeds, or a small auxiliary imitation term on gate exemplars to prevent full extinction.

---

## Verbatim example completions (from `generations.jsonl`)

Quoted exactly; `\n` shown as literal for compactness. Seed IDs truncated to 8 chars.

**1. gate-extinction — deep on a gate-required seed (step 253, seed `router_c`), reward −1.3**
> ` {"first": "deep", "on_fail": "finish"}`
The clean JSON plan is correct in *format* but routes `deep` on a seed that requires `gate` → −2.0 safety penalty. The same seed was correctly gated at step 1 (below).

**2. gate-extinction — deep on gate-required seed `0655b4d0` (step 302), reward −1.3**
> ` {"first": "deep", "on_fail": "finish"}`
Late-run; by this point deep is the default first action even on hopeless-without-gate seeds.

**3. cost-blind cheap on hopeless seed — cheap on gate-required seed `0655b4d0` (step 302), reward −2.0384**
> ` {"first": "cheap|deep", "on_fail": "finish|escalate"}`
Cheapest action chosen on a seed where only gate avoids the penalty — the maximal-penalty variant (−2.04).

**4. cost-blind cheap on hopeless seed — cheap→escalate on gate-required seed `router_c` (step 305), reward −1.3384**
> ` If cheap fails you may escalate (pay 1.0 more). If deep fails you may escalate (pay 1.0 more). If gate fails you may escalate (finish 1.0 check). Reward = success - lambda*`
Verbose restatement of the prompt that still parses to a `cheap` first action; penalized.

**5. deep-collapse — deep on non-gate seed `01091fbd` (step 361), reward 0.7**
> ` {"first": "deep", "on_fail": "finish"}`
Degenerate always-deep routing. Reward 0.7 (success − λ·cost) is *tolerable* here, which is why deep-collapse is stable — it is locally fine on the 85% non-gate seeds and only catastrophic on the 15% gate seeds.

**6. deep-collapse — deep on non-gate seed `003ad180` (step 361), reward 0.7**
> ` {"first": "deep|gate", "on_fail": "finish|escalate"}`
Notice the `|`-menu format leaking through; parser takes the first token (`deep`). Format noise, still parsed.

**7. healthy gate (contrast) — gate on gate-required seed `router_c` (step 1), reward +0.955**
> ` if on_fail: finish\nsymbol: KLAC\nas_of: 2026-02-15\nanswer: if on_fail: finish\n\nsymbol: KIWI\nas_of: 2026`
Same `router_c` seed that later collapsed to deep (examples 1). Early in training the policy still gated it and earned +0.955.

**8. verbose/degenerate (early) — deep on gate-required seed `0655b4d0` (step 33), reward −1.3**
> ` If an investor is confident, he usually tries deep research and only a half-decent amount of red-light analysis can really change an investment. Only a full investigation and rigo...`
A rambling free-text completion that still parses to a `deep` first action — an early instance of the same gate-required seed being mis-routed, foreshadowing the extinction.

---

*Generated from local run evidence. Reproduce with:*
`python3 training-corpus/scripts/analysis/analyze_grpo_collapse.py`
