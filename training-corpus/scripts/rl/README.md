# RL Phase 2 scripts (Plan A)

Pull-and-run on an A100. The reward/label/env logic is CPU-only and has no
heavy deps; only sft_/grpo_ training and adapter eval need the GPU stack.

**Owner: run `GPU_RUNBOOK.md` - it has the exact command order, kill criteria,
monitoring, what-to-save, and the failure protocol.** This file is the concept
reference.

Every training run lands in `out-dir/<run_id>/` (`run_id = <UTC>-<git sha>`);
the trainers REFUSE to overwrite a non-empty run dir, so failed runs are
preserved as interview evidence. Each run writes `run_manifest.json` (config,
seeds, git sha, pip freeze, `parent_run_id`), `trainer_log.jsonl`,
`metrics.json`, and (GRPO) `generations.jsonl` + `reward_trace.jsonl`. The
manifest's pip freeze is the authoritative dependency record per run;
`requirements-rl.txt` pins are only a known-good starting point.

ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1
CENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/citation_real_eval_v1

## 0. CPU smoke (no GPU, no install)
    python reward_escalation.py $ENV
    python build_sft_labels.py --env-dir $ENV --split train --lambda 0.3 --out /tmp/sft_train.jsonl

## 1. Motivation gate (A1) - prompted small model, no training
Dump a prompted-small-model policy to preds.jsonl (rows: seed_id/qid, first, on_fail),
then:
    python eval_escalation_policy.py --env-dir $ENV --split test --pred-file preds.jsonl
KILL: if reward is within 3 pts of oracle AND gate_recall>=0.99, stop - small
models need no training either (record the negative). Else continue.

## 2. argmax-SFT baseline (A2, GPU)
    pip install -r requirements-rl.txt
    python build_sft_labels.py --env-dir $ENV --split train --lambda 0.3 --out sft_train.jsonl
    python sft_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --train sft_train.jsonl \
        --out-dir runs/sft_qwen05b --seed 0
    # note the printed run_id, then eval that run's adapter:
    python eval_escalation_policy.py --env-dir $ENV --split test \
        --model Qwen/Qwen2.5-0.5B-Instruct \
        --adapter runs/sft_qwen05b/<RUN_ID>/adapter --out sft_eval.json
Record the SFT reward at lambda 0.3 -> BASELINE.

## 3. GRPO (A3, GPU)
    python grpo_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --env-dir $ENV --lambda 0.3 \
        --init-adapter runs/sft_qwen05b/<SFT_RUN_ID>/adapter --out-dir runs/grpo_qwen05b \
        --seed 0 --save-steps 50
    python eval_escalation_policy.py --env-dir $ENV --split test \
        --model Qwen/Qwen2.5-0.5B-Instruct \
        --adapter runs/grpo_qwen05b/<GRPO_RUN_ID>/adapter \
        --baseline-reward <SFT_BASELINE> --out grpo_eval.json
The eval prints the pre-registered kill check (GRPO must beat SFT by >=3 pts
and hold gate_recall). Commit manifests + jsonl logs + *_eval.json +
metrics.json only - no base weights, no large checkpoints (they are gitignored;
RECORDING_PROTOCOL / D-2026-06-30-006). Resume an interrupted run with
`--resume runs/<arm>/<RUN_ID>/checkpoint-<N>`; link a failure re-run with
`--parent-run <failed_run_id>`.

## 3b. GRPO gate-oversample (mixed-group fix)
`grpo_escalation.py` new flags:
- `--gate-oversample N` (default 1): repeats every gate-required seed N times in
  the train prompt list. **Why:** GRPO advantage is *group-relative* over the K
  samples of one prompt. On a gate-required seed where all K samples miss the
  gate, every sample gets the same reward, so the advantage is identically zero
  and no gradient flows on exactly the seeds that matter most. Oversampling gate
  seeds seeds more chances for a correctly-gating member to appear in a group,
  breaking the all-violate tie so advantage stops zeroing. Recorded in
  `run_manifest.json` (`gate_oversample`, `gate_prompt_rows`, `total_prompt_rows`).
- `--num-generations K` (default 8) / `--batch-size` (default 16): passed to
  GRPOConfig. K must divide the batch (validated early with a clear error).
- `--kl-beta` (default None -> TRL default): GRPOConfig `beta` if set.

`eval_escalation_policy.py --dump-preds PATH` (model mode): writes per-seed jsonl
`{seed_id, first, on_fail, gate_needed, oracle_action, completion}` so the exact
missed-gate seeds are identifiable (filter `gate_needed==true && first!="gate"`).

`eval_escalation_policy.py --temperature T --n-samples N` (model mode,
F-2026-07-04-002 follow-up): default `0 / 1` = greedy, unchanged. With `N>1` it
samples N plans/seed at temperature T and reports BOTH `scores_per_sample_avg`
(every sampled plan scored, averaged) AND `scores_majority_vote` (the per-seed
majority plan scored), plus `gate_action_presence` = fraction of gate-needed
seeds where `>=1` of the N samples chose gate. In sampled mode `--dump-preds`
writes `{seed_id, majority_first, majority_on_fail, gate_needed, oracle_action,
samples:[...]}`. Purpose: quantify whether 0.5B-v2's surviving sampled gate
behaviour is recoverable by decoding strategy (see the pre-registered bar below).

## 4. DPO arm (`dpo_escalation.py`)
Same task, prompt renderer, and reward ruler as SFT/GRPO; the signal is one
preference pair per train seed:
- **chosen** = the analytic ORACLE plan JSON (argmax expected reward).
- **rejected** = the *most tempting wrong* plan: the non-oracle strategy with
  the highest analytic expected reward for that seed (from `env.expected_rewards`,
  oracle strategy excluded), rendered in the same one-line plan JSON. This pushes
  probability mass off the single closest competitor (e.g. cheap_finish vs
  cheap_then_escalate, or a gate replaced by the least-bad wrong action) rather
  than off a random wrong plan.

`--pairs-version {v1,v2}` (default v1, frozen): v2 (D-2026-07-04-004) keeps every
v1 pair and ADDS a `failed_to_escalate` hard negative (chosen=cheap_then_escalate,
rejected=cheap_finish) on each seed whose oracle is `cheap_then_escalate_on_fail`,
so escalation is the WINNER on the seeds where it should fire (v1 taught "never
escalate" by putting escalate on the rejected side of cheap seeds).

CPU-buildable pair inspection (no GPU/torch):
    python dpo_escalation.py --env-dir $ENV --lambda 0.3 --pairs-version v2 \
        --pairs-only --pairs-out /tmp/dpo_pairs.jsonl
Prints n_pairs, `pair_type_mix`, chosen/rejected label mix, and two invariants
that must both be 0: `pairs_with_chosen_eq_rejected` and
`pairs_where_rejected_beats_chosen_er`.
The trainer path refuses to train if any chosen==rejected. GPU run:
    python dpo_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --env-dir $ENV \
        --init-adapter runs/sft_qwen05b/<RUN_ID>/adapter \
        --out-dir runs/dpo_qwen05b --beta 0.1 --epochs 3
Uses the same LoRA config as SFT, `--init-adapter` (default: init from the SFT
adapter arg), TRL 0.15.2 DPOConfig (`beta`, `max_length`, `max_prompt_length`),
`processing_class`, full run_logging provenance, `save_total_limit=None`,
`--resume`, `--parent-run`. **Evaluate on the SAME frozen eval-256 as SFT/GRPO**
(`eval_escalation_policy.py --adapter ...`): DPO is judged on the identical ruler.

## 5. Citation env first GRPO run (`grpo_citation.py`, Plan B)
First GRPO on `CitationAgenticEnv`: the policy emits
`{"cite": <evidence_id>, "verdict": <label>}` in one generation; reward is the
env's process+outcome score (valid-citation shaping, fabricated-id hard negative,
gold-span bonus, verdict match). Same K/batch flags and provenance as
`grpo_escalation.py`; `reward_trace.jsonl` logs `mean_reward`, `fabricated_rate`
(cite not in pool), `gold_cite_rate`, `verdict_acc`; `generations.jsonl` logs
every completion + parsed cite/verdict + reward parts.

`--action-space {raw_id,letters}` (default raw_id, v1 kept intact): `letters`
(v2, D-2026-07-04-002) re-renders the candidate pool as a lettered menu ("A:
<span>", ...); the policy answers `{"cite": "B", "verdict": ...}` and the harness
maps the letter back to the evidence_id before scoring. Fabrication is then an
off-menu letter (still the -1.0 hard negative), structurally not a hallucinated
id. Add `--action-space letters` to BOTH the baseline eval and the train/eval
runs so v1-vs-v2 is a clean action-space comparison on the same ruler.

First-run protocol:
    # CPU wiring smoke (no model): fake completion through env.reward
    python grpo_citation.py --eval-dir $CENV --dry-parse                     # v1
    python grpo_citation.py --eval-dir $CENV --dry-parse --action-space letters  # v2
    # prompted baseline (no adapter) on the test split -> the bar to beat
    python grpo_citation.py --model Qwen/Qwen2.5-0.5B-Instruct --eval-dir $CENV \
        --eval-only --split test --out runs/citation_baseline.json
    # GRPO on train, then eval the adapter on test  (add --action-space letters for v2)
    python grpo_citation.py --model Qwen/Qwen2.5-0.5B-Instruct --eval-dir $CENV \
        --out-dir runs/grpo_citation_qwen05b
    python grpo_citation.py --model Qwen/Qwen2.5-0.5B-Instruct --eval-dir $CENV \
        --eval-only --split test --adapter runs/grpo_citation_qwen05b/<RUN_ID>/adapter \
        --out runs/citation_grpo_eval.json
Eval reports `{verdict_acc, cite_valid_rate, cite_gold_rate, fabricated_rate,
mean_reward}`. (`$CENV` = the `citation_real_eval_v1` dir; corpus is small - 62
train / 31 test claims - so treat this as a scaffold shakeout, not a headline
number.)

## Plan C protocol (real run) - Training-Free GRPO

Plan C is the **no-weights control column**: the "learned parameter" is a
natural-language *experience library* (a JSON list of lessons `{lesson_id,
trigger, rule}`), and the *policy* is the base prompt + the library block
injected into the system prompt. `training_free_grpo.py` holds the
backend-agnostic loop; three scripts make it runnable on a real model. The
**orchestrator** (Claude, outside the scripts) runs the loop round-by-round and
supplies the two subagent-driven steps (contrast distillation); the scripts
provide the two GPU-bound primitives (rollout, regression gate).

**Honest framing (record it in the writeup):** the library is the *no-weights
CONTROL column* for weight-GRPO, and it is the SAME family of method the rung-4
risk explib used - so its ceiling is *how far a prompt+library can go*, i.e. the
**prompt-space ceiling**, by construction below weight training's potential
where label-sparse reward shaping matters. A Plan C win is "a prompt+library got
here without touching weights", never "training was unnecessary".

Env (paths as in section 0):

    ENV=../../runs/.../ladder/escalation_env_v0.1     # $ENV above
    MODEL=Qwen/Qwen2.5-1.5B-Instruct                  # the control model

### The round loop (orchestrator-driven; <=4 rounds, stop on a dry round)

Start with an EMPTY library (`library.json` = `[]` or omit `--library`).

1. **Rollout** (`tfgrpo_rollout.py`, GPU). One round of K sampled completions
   over the first-N TRAIN seeds with the current library injected:

       python tfgrpo_rollout.py --model $MODEL --env-dir $ENV --split train \
           --seed-subset 60 --library library.json --k 8 --temperature 1.0 \
           --lambda 0.3 --out runs/tfgrpo_rollout
       # writes runs/tfgrpo_rollout/<RUN_ID>/{rollouts.jsonl, contrasts.json,
       #   round_summary.json, run_manifest.json}

   `contrasts.json` is `semantic_advantage` per seed (best-vs-worst where reward
   spread > 0, sorted by advantage desc) - the raw material for step 2.
   `round_summary.json` carries mean reward, gate-violation rate, action mix,
   and the library sha the rollout was run under.

2. **Distill** (orchestrator + subagents, no GPU). Read `contrasts.json`; via
   subagents, distill **<= 3** new/edited lessons that explain why the
   higher-reward plan beat the lower-reward one (e.g. "when the query names a red
   line, first=gate"). Keep the library SMALL - edit/merge before adding.

3. **Regression-check on dev** (`tfgrpo_regression.py`, GPU). Score the CURRENT
   library and each TRIAL library (current + candidate lesson) on the fixed
   regression set (dev, greedy):

       python tfgrpo_regression.py --model $MODEL --env-dir $ENV --split dev \
           --library library_current.json --out runs/reg_current.json
       python tfgrpo_regression.py --model $MODEL --env-dir $ENV --split dev \
           --library library_trial.json   --out runs/reg_trial.json

   This is the natural-language no-regression gate from `training_free_grpo.run`.

4. **Accept/reject.** Accept the lesson iff `reg_trial.mean_reward >=
   reg_current.mean_reward` (no dev regression) - this mirrors the loop's
   `regression_reward(trial) >= before` gate. A round that accepts NO lesson is a
   **dry round**: stop. Otherwise repeat from step 1 with the updated library,
   for at most **4 rounds**.

Provenance: every rollout/regression call writes a `run_manifest.json` (or result
json) recording model, seeds, `library_sha256`, `n_lessons`, and git sha, so each
round is attributable to an exact library.

### FINAL scoring - pre-registered bars (frozen TEST, checked once at the end)

Freeze the accepted library, then score it on the **frozen TEST split** with the
library injected via the additive `--extra-system-file` (records
`extra_system_sha256` + path so the scored run is attributable):

    python eval_escalation_policy.py --env-dir $ENV --split test --model $MODEL \
        --extra-system-file library_final.txt --out plan_c_test.json
    # library_final.txt = the ExperienceLibrary.as_prompt_block() text of the
    #   frozen library (byte-identical to what the rollout/regression injected)

> **PRE-REGISTERED PROMOTION BAR.** Plan C promotes iff, on the frozen TEST
> split: test reward `>=` prompted-1.5B `+ 10 pts` (`0.644 -> 0.744`) AND gate
> recall `>=` the prompted-1.5B baseline. Both must hold.

Report the library as the **no-weights control column** next to the weight-GRPO
arms, and state the ceiling is prompt-space (see the honesty note above).

## Pre-registered promotion criteria (all arms, checked after the runs)
- **Escalation GRPO-v2** (gate-oversample) promotes iff, on the frozen test
  split: `gate_recall >= 0.99` AND `reward >= SFT_baseline + 3pts`.
- **DPO** is compared on the *same ruler* (same frozen eval-256, same
  reward/gate metric) and held to the same bar as escalation GRPO-v2.
- **Citation GRPO** (v1 raw-id) promotes iff `verdict_acc` beats the prompted
  baseline by `>= 5pts` AND `fabricated_rate == 0`.

### Three pre-registered bars for this iteration (D-2026-07-04-002/-004, F-2026-07-04-002)

**1. Citation env v2 (letter action space, `--action-space letters`, D-2026-07-04-002).**
Run 1.5B GRPO in `--action-space letters` against the SAME frozen
`citation_real_eval_v1` ruler (test n=31) that the v1 raw-id run used.
- **PASS bar:** `fabricated_rate == 0` (a letter is in-menu or off-menu, never a
  hallucinated id, so 0 is the structural expectation) AND `verdict_acc` beats a
  **prompted-letter baseline** (`--action-space letters --eval-only`, no adapter)
  by `>= 5pts`.
- **ALSO track (squeeze hypothesis):** report v2 `verdict_acc` next to the v1
  numbers (prompted 0.2581, GRPO 0.1935 from EXP-2026-07-04-003). If v2
  `verdict_acc` recovers relative to v1 while the citation component is met, that
  is evidence the v1 drop was a component-reward SQUEEZE (the verbatim-copy
  citation objective competing away verdict accuracy under a fixed budget), not a
  verdict-capability loss. A null v2 result is then a clean statement about a
  1.5B's citation SELECTION ability, separated from its id-COPYING inability.

**2. DPO pairs v2 (`--pairs-version v2`, D-2026-07-04-004).**
Rebuild the pair set with the failed-to-escalate hard negatives (v1 pairs kept;
196 = 160 + 36 pairs where oracle is `cheap_then_escalate_on_fail`, adding
`chosen=cheap_then_escalate` vs `rejected=cheap_finish`). Re-run 1.5B DPO from
the same SFT init and evaluate on the SAME frozen eval-256.
- **PASS bar:** on the frozen test split, DPO v2 must hold `gate_recall >= 0.99`
  (v1 already achieved 1.000) AND recover `success` and `reward` above the v1
  collapse (v1: success 0.58, reward 0.5382). Concretely: `reward >=
  SFT_baseline` (no net regression vs SFT) AND `success` materially above 0.58,
  i.e. the "never escalate" collapse is undone without losing the gate.
- Inspect the mix first: `--pairs-only` must print `pair_type_mix`
  (`oracle_vs_tempting` + `failed_to_escalate`) and keep both invariants at 0
  (`pairs_with_chosen_eq_rejected`, `pairs_where_rejected_beats_chosen_er`).

**3. Sampled-mode eval (`--temperature T --n-samples N`, F-2026-07-04-002 follow-up).**
On the 0.5B GRPO-v2 adapter (greedy `gate_recall == 0`), run
`eval_escalation_policy.py --n-samples 8 --temperature 1.0`. It reports BOTH
`scores_per_sample_avg` and `scores_majority_vote`, plus `gate_action_presence`
(fraction of gate-needed seeds where `>= 1` of the N samples chose gate).
- **PRE-REGISTERED READING:** if `gate_action_presence_rate >= 0.9` at T=1.0 N=8
  WHILE greedy `gate_recall == 0`, the collapse is a **DECODING-mode phenomenon**
  (the gate action survives in the sampled policy but not as the greedy mode),
  NOT a knowledge loss. If presence is also `~0`, the gate action is genuinely
  gone from the policy. Either outcome is a distinct, publishable finding.
- Defaults (`--n-samples 1 --temperature 0`) are greedy/argmax and leave the
  existing eval numbers unchanged.

## Batch 4 protocol (`run_batch4.sh`) - error bars, cross-family, citation SFT
Every portfolio number so far is SINGLE-SEED (seed 0) - the top credibility gap.
Batch 4 closes it and adds two cross-cutting probes. Pull-and-run on the A100;
`run_batch4.sh` has the exact command order (paths relative to this dir). Two
venvs: `PY=~/postTrain/.venv-rl/bin/python` (training, Qwen), and a SEPARATE
`GPY=~/postTrain/.venv-gemma/bin/python` (transformers 5.13, Gemma PROMPTED eval
only - the scripts must not assume the training venv, hence the additive
`--loader`/`--chat-template` flags and their lazy, guarded imports).

New tooling:
- `aggregate_seeds.py` (stdlib, no GPU): given N eval jsons for one config at
  different seeds, emits mean/std/min/max for reward@each-lambda and gate_recall,
  `n_seeds`, and the per-seed values to `--out` json + a compact markdown table.
  Population std (ddof=0): single-seed input -> std 0.0, no divide-by-zero.
- `sft_citation.py`: SFT baseline for the citation task in the LETTERS action
  space. Rows are built from `CitationAgenticEnv` split=="train" (62 claims):
  prompt = `env.render_prompt(cid)` (lettered menu), completion = one-line
  `{"cite": "<gold letter>", "verdict": "<gold label>"}`. The gold letter is
  looked up through `env.letter_map(cid)` and NEVER re-derived - the letter for
  the gold evidence depends on candidate ordering. `--labels-only` (stdlib)
  prints the letter/label mix and ASSERTS every gold letter maps back to the gold
  evidence_id (0 mismatches) before any GPU time. Eval the adapter via
  `grpo_citation.py --eval-only --action-space letters --adapter ...`.
- `eval_escalation_policy.py` additive flags: `--loader {causal,auto}` (default
  `causal` = unchanged Qwen path; `auto` tries `AutoModelForCausalLM` then falls
  back to `AutoModelForImageTextToText`, since Gemma 4 is
  `Gemma4ForConditionalGeneration`); `--chat-template` (explicit single-user-turn
  wrapping for Gemma-it). Default behaviour is byte-identical for existing Qwen
  runs.

Phase A design (pre-registered): GRPO seeds 1,2 REUSE the seed-0 SFT adapter as
init rather than retraining SFT per seed. This isolates GRPO SAMPLING variance
from SFT variance and keeps the batch inside budget. SFT variance is measured
SEPARATELY, and only at 1.5B, by retraining SFT-1.5B from scratch each seed. The
seed-0 eval jsons already on disk (`sft_qwen15/20260703T1506Z*`,
`grpo_v2_qwen3/20260703T1624Z*`, `grpo_qwen05/20260703T1507Z*`) are seed 0 of the
{0,1,2} aggregate.

### Three pre-registered claims this batch tests
1. **Multi-seed error bars.** Report `mean±std` over seeds {0,1,2}. The
   **3B-oracle** claim (GRPO-v2 3B reaches ~oracle reward + holds the gate) and
   the **0.5B-collapse** claim (plain GRPO 0.5B loses the gate) STAND ONLY IF
   they replicate across all 3 seeds - i.e. the effect must survive the std, not
   just seed 0.
2. **Gemma cross-family (prompted).** Does the small-model gate failure replicate
   CROSS-FAMILY on Gemma 4 E2B-it / E4B-it (prompted, no training)? Caveat: these
   are MatFormer models with EFFECTIVE params E2B=2.3B / E4B=4.5B vs Qwen dense,
   so the comparison is by effective-params band, not architecture-matched.
3. **Citation SFT (the decoupling probe).** Does SUPERVISED training move
   `verdict_acc` where GRPO's citation-component reward did NOT
   (EXP-2026-07-04-003)? `sft_citation.py` 1.5B in the letters space, evaluated on
   the same frozen `citation_real_eval_v1` test ruler, decouples "can a 1.5B learn
   the verdict when supervised on it" from "does the RL citation objective squeeze
   verdict accuracy away".

## 7B arm (A100 OOM knobs)
Scaling from Qwen2.5-0.5B to a 7B model on the single A100 80GB:
- per-device batch 8 + `--grad-accum 2` (both trainers take `--grad-accum`),
- consider the TRL vLLM generation backend for GRPO rollout throughput,
- reach for **gradient checkpointing first** if you OOM, before cutting batch.

## Full fine-tuning arms (E1 7B-SFT, E2 0.5B-GRPO probes)

All numbers so far are LoRA (r=16). Two open questions need FULL-parameter runs
on a single A100 80GB. Both trainers gain additive flags (default behaviour
unchanged; the LoRA + `adamw_torch` paths are byte-identical to before):

- `--full-finetune`: skip peft/LoRA wrapping, train ALL base params. The full
  model is saved to `<run_dir>/full_model/` (NOT `adapter/`); the manifest and
  `metrics.json` record `parameterization: "full"` vs `"lora"` plus `optim`.
- `--optim` (default `adamw_torch`): passed to the config. Use `adamw_bnb_8bit`
  for 7B (needs `bitsandbytes`, see `requirements-rl.txt`).
- `--gradient-checkpointing`: passed to the config; needed at 3B+/7B.
- GRPO only: `--init-model PATH` loads BASE weights from a local `full_model/`
  dir (e.g. a full-FT SFT run's output) instead of the hub `--model` id. This is
  the honest full-FT GRPO init. `--full-finetune` + `--init-adapter` is an ERROR
  (an adapter is a LoRA artifact) and points you at `--init-model`.

Evaluate a full model with `eval_escalation_policy.py --model <local full_model
dir>` and NO `--adapter`: the default `--loader causal` path calls
`AutoModelForCausalLM.from_pretrained` on the local dir (which holds `config.json`
+ safetensors + tokenizer written by `trainer.save_model`), so it loads exactly
like a hub id. No eval-script change is needed.

Memory (single A100 80GB, bf16):

| model | full-FT footprint | notes |
|-------|-------------------|-------|
| 0.5B  | ~8GB              | fits easily, `adamw_torch` |
| 1.5B  | ~24GB             | `adamw_torch` |
| 3B    | ~48GB             | add `--gradient-checkpointing` |
| 7B    | ~50GB             | needs `--optim adamw_bnb_8bit` (+ `--gradient-checkpointing`) |

### E1 - does 7B SFT degradation persist under full FT? (LoRA-was-binding)
Full-FT SFT the 7B and eval on the frozen eval-256. Bar (pre-registered):

> full-7B-SFT beats its LoRA version 0.7147 by >= 3 pts at lambda 0.3 -> "LoRA was binding"

    python sft_escalation.py --model Qwen/Qwen2.5-7B-Instruct \
        --train sft_train.jsonl --out-dir runs/sft_full_qwen7b \
        --full-finetune --optim adamw_bnb_8bit --gradient-checkpointing \
        --batch-size 8 --grad-accum 2 --seed 0
    python eval_escalation_policy.py --env-dir $ENV --split test \
        --model runs/sft_full_qwen7b/<RUN_ID>/full_model --out sft_full7b_eval.json

### E2 - does the 0.5B GRPO collapse persist with all params trainable? (capacity floor)
Honest design: full-FT GRPO from the BASE model AFTER a full-FT SFT init. First
full-FT SFT the 0.5B, then GRPO from its `full_model/` via `--init-model`. Bar:

> if full-FT 0.5B GRPO STILL loses the gate action (`gate_recall < 0.5` at greedy, matching the LoRA collapse pattern) across the run, the capacity floor is confirmed at the PARAMETERIZATION level; if it HOLDS `gate >= 0.99`, the collapse is reattributed to adapter capacity.

    python sft_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct \
        --train sft_train.jsonl --out-dir runs/sft_full_qwen05b --full-finetune --seed 0
    python grpo_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --env-dir $ENV \
        --lambda 0.3 --full-finetune \
        --init-model runs/sft_full_qwen05b/<SFT_RUN_ID>/full_model \
        --out-dir runs/grpo_full_qwen05b --seed 0 --save-steps 50
    python eval_escalation_policy.py --env-dir $ENV --split test \
        --model runs/grpo_full_qwen05b/<GRPO_RUN_ID>/full_model \
        --baseline-reward <SFT_BASELINE> --out grpo_full05b_eval.json

**Scope (honesty note):** full-FT results are SINGLE-SEED (seed 0) probes unless
promoted; do not report them as error-barred headline numbers without the
multi-seed follow-up that the LoRA arms get (Batch 4 protocol).

## Note on env_seeds versions
The env dir ships `env_seeds_v0.1/v0.2/v0.3.json`. The loader
(`escalation_env_v01.py`) prefers **v0.3** (gate-corrected, 160 train labels),
which is the A2 spec. `env_seeds_v0.2.json` (1024 expanded train seeds) exists
but is **intentionally NOT loaded** - A2 is a small-label supervision baseline,
so the 160-label v0.3 set is deliberate, not an oversight. Do not "fix" the
loader to grab v0.2. Each run's `run_manifest.json` records the exact
`env_seeds_version` used.

## Escalation env v0.4 - the MEMORY arm (`escalation_env_v04.py`)

**Saturation motivation.** Env v0.3 is a STATELESS router (observable state =
`{user_query, symbol, as_of}`) and it is now **SATURATED - 7+ configs hit the
analytic oracle mean reward 0.8473 exactly**, so the env has lost discriminative
power. v0.4 restores it by making difficulty **memory-dependent**: the correct
route now depends on state that is NOT in the query string, so a stateless
policy is provably capped below oracle. The pre-registered design lives in
`docs/ESCALATION_ENV_V04_MEMORY_DESIGN.md` (authoritative). This env is the CODE
for that design; **no arm is measured until the v0.3 small-model chain has a
written verdict** (the design doc gates the run, not this file).

### The four pre-registered arms (quoted from the design doc)

Same env, same frozen eval seeds, same reward (final correctness
`- lambda * accumulated cost`) with the hard gate-recall constraint. Only the
**state representation** and the **train/prompt** treatment vary.

| # | Model | State form | Treatment | Role |
| --- | --- | --- | --- | --- |
| 1 | small (Qwen 0.5B/1.5B) | none (`{query, symbol, as_of}`) | post-trained | **baseline** = A3 continuation |
| 2 | small (Qwen 0.5B/1.5B) | **structured digest** (~50 tok) | prompted vs post-trained | **MAIN hypothesis**: training enables compact-memory use |
| 3 | small (Qwen 0.5B/1.5B) | **raw long context** (L0-L3) | post-trained | tests "context drowns small models"; expected < arm 2 |
| 4 | Sonnet | structured digest (same as arm 2) | prompt-only | frontier reference + cost/latency comparison |

The `memory_mode in {none, digest, raw}` switch on `EscalationEnvV04.episode()`
(and on `render_prompt_v04(seed, memory_mode)` in `reward_escalation.py`) is
exactly this arm switch: `none` = arm 1, `digest` = arm 2/4, `raw` = arm 3.

### Pre-registered kills (quoted verbatim from the design doc)

> **1. Main hypothesis kill.** If arm-2 *post-trained* does **not** beat arm-1
> *post-trained* by **>= 3 reward points** at `lambda = 0.3` (with gate recall
> held **>= 0.99**), record honestly: **"memory does not pay at this model
> size."**

> **2. Compression-thesis kill.** If arm-3 (raw long context) does **NOT**
> collapse relative to arm-2 (digest), record that too - it **falsifies the
> compression thesis** (raw history was fine; the harness-side digest bought
> nothing).

> **3. Cost/speed vs Sonnet.** Measure **tokens + wall-clock latency per routing
> decision** for every arm. The question is *not* who is cheaper ... but **how
> small the quality gap gets**. Report as **"% of Sonnet quality at % of Sonnet
> cost"**.

A negative result (memory does not pay / raw context did not drown / the gap to
Sonnet is large) is a **first-class deliverable**, recorded with numbers in
`DECISIONS.md`.

### Twin-pair construction rationale

The env's discrimination test is the **counterfactual twin pair**: two seeds
that **share the same `user_query` (query_text) but have ALTERED memory and
therefore DIFFERENT gold**. Identical surface words, so a stateless policy MUST
score one member wrong - the only way to route both correctly is to attend to
the memory block. This is what re-separates a good policy from oracle after v0.3
saturated. Two integrity rules the validator enforces on every pair:
twins must point back at each other and differ in gold (`gold_first` +
`gold_on_fail`), and **both members must live in the SAME split** - a twin
straddling train/test would leak the query text across the split boundary and
turn the discrimination test into a memorization test.

### Dynamic (state-dependent) cost

The static v0.3 cost table could not express a cost that depends on history.
v0.4 adds `c_deep_cached` (default **0.35**): when the cache holds a **fresh**
item relevant to the query (precomputed `cache_hit && cache_fresh`), the deep
path re-uses cached evidence and costs `c_deep_cached` instead of `1.0`;
gate/cheap costs are unchanged. This is what lets a `cache_cost` twin pair flip
the oracle (same query: stale cache -> cheap-ish; fresh cache -> deep) purely on
state - demonstrated in the `--selftest` oracle-flip check.

### CPU verification (no GPU, no install)

    python escalation_env_v04.py --selftest            # 6-seed fixture: validator,
                                                       #   leakage assert, oracle flip,
                                                       #   digest length, 3 memory modes
    python escalation_env_v04.py --validate DIR        # schema + twin + leakage +
                                                       #   point-in-time + split integrity

Synthetic memory seeds are generated by parallel persona-simulator agents into
`.../ladder/escalation_env_v0.4/staging/` (interchange JSON); a later builder
agent assembles `env_seeds_v0.4.json` + `outcome_table_v0.4.json` +
`cost_table_v0.4.json` from staging - that assembly is NOT this env's job. The
env loads those three files from its dir once assembled.

### v0.4 model eval harness (`eval_v04.py`) - the arm matrix runner

`eval_v04.py` scores a policy on ONE arm (`--memory-mode none|digest|raw`) with
the env's OWN v0.4 reward math: it reuses `render_prompt_v04` + `parse_plan`
(from `reward_escalation.py`) and reads each plan's reward straight off
`EscalationEnvV04.expected_rewards(seed_id, lam, memory_mode)` - so the dynamic
deep cost (`c_deep_cached` on fresh-cache seeds), the arm-appropriate cheap odds
(`p_no_memory` on the none arm, memory-resolved `p` on digest/raw), gate logic,
and the missed-gate penalty are all inherited, never reimplemented. Model
loading / greedy generation / `--dump-preds` are copy-adapted from
`eval_escalation_policy.py` (only the prompt renderer differs, to inject the arm
memory block) - see the module docstring for the reuse/copy split.

Report (JSON): per-λ `{reward, cost, success, gate_recall}` at λ {0.1,0.3,0.6},
plus **twin-pair discrimination rate** (headline - fraction of twin pairs the
model gives DIFFERENT plans to), per-`difficulty_class` plan accuracy
(`plan == gold`), the arm-appropriate oracle gap at λ=0.3, and the mean
prompt-token count for the mode (quantifies raw-vs-digest context cost).
`memory_mode`, env dir, seeds version, and model/adapter provenance are recorded.

CPU verify (no GPU, no install):

    python eval_v04.py --selftest    # loads the REAL dataset, scores 3 fabricated
                                     #   completions vs 3 real seeds, demonstrates
                                     #   twin-discrimination, none-vs-digest p switch,
                                     #   and the dynamic-cost effect in scoring

Arm runs - **1.5B prompted, three arms, frozen TEST split** (arms 1/2/3 of the
matrix above; `ENV04` = the shipped v0.4 dir):

    ENV04=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.4

    # arm 1 (baseline, stateless):
    python eval_v04.py --env-dir $ENV04 --split test --memory-mode none \
        --model Qwen/Qwen2.5-1.5B-Instruct --dump-preds runs/eval_v04/none_preds.jsonl \
        --out runs/eval_v04/none_test.json
    # arm 2 (structured digest, MAIN hypothesis):
    python eval_v04.py --env-dir $ENV04 --split test --memory-mode digest \
        --model Qwen/Qwen2.5-1.5B-Instruct --dump-preds runs/eval_v04/digest_preds.jsonl \
        --out runs/eval_v04/digest_test.json
    # arm 3 (raw long context, "context drowns small models"):
    python eval_v04.py --env-dir $ENV04 --split test --memory-mode raw \
        --model Qwen/Qwen2.5-1.5B-Instruct --dump-preds runs/eval_v04/raw_preds.jsonl \
        --out runs/eval_v04/raw_test.json

Arm 4 (Sonnet, frontier reference / digest arm) is a **pred-file route for
later**: dump a Sonnet-produced `{seed_id, first, on_fail}` jsonl and score it
the same way (a `--pred-file` path can be added to `eval_v04.py` when that arm
runs; today's harness is the model/greedy path for the 1.5B arms). The
pre-registered kills for these arms (main-hypothesis, compression-thesis, and
cost/speed-vs-Sonnet) are the ones quoted verbatim above - not restated here.

### Fidelity notes carried forward (restate wherever a v0.4 number is reported)

The known env-fidelity limits (model-derived `p`, always-adequate deep path,
small real cost sample) all still apply. v0.4 adds one more: **the digest is a
HAND-SPECIFIED lossy projection**, so a null arm-2 result is a result about
*this* projection, not about all possible memory encodings.

## Budget
A100: SFT <1h, GRPO ~2-4h, ~USD 20-50, inside the USD 100 / 24 A100h cap.
Fidelity limits (model-derived p, always-adequate deep, small cost sample)
apply to every number here - see escalation_env_v0.1/README.md.
