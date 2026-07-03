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

CPU-buildable pair inspection (no GPU/torch):
    python dpo_escalation.py --env-dir $ENV --lambda 0.3 --pairs-only \
        --pairs-out /tmp/dpo_pairs.jsonl
Prints n_pairs, chosen/rejected label mix, and two invariants that must both be
0: `pairs_with_chosen_eq_rejected` and `pairs_where_rejected_beats_chosen_er`.
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

First-run protocol:
    # CPU wiring smoke (no model): fake completion through env.reward
    python grpo_citation.py --eval-dir $CENV --dry-parse
    # prompted baseline (no adapter) on the test split -> the bar to beat
    python grpo_citation.py --model Qwen/Qwen2.5-0.5B-Instruct --eval-dir $CENV \
        --eval-only --split test --out runs/citation_baseline.json
    # GRPO on train, then eval the adapter on test
    python grpo_citation.py --model Qwen/Qwen2.5-0.5B-Instruct --eval-dir $CENV \
        --out-dir runs/grpo_citation_qwen05b
    python grpo_citation.py --model Qwen/Qwen2.5-0.5B-Instruct --eval-dir $CENV \
        --eval-only --split test --adapter runs/grpo_citation_qwen05b/<RUN_ID>/adapter \
        --out runs/citation_grpo_eval.json
Eval reports `{verdict_acc, cite_valid_rate, cite_gold_rate, fabricated_rate,
mean_reward}`. (`$CENV` = the `citation_real_eval_v1` dir; corpus is small - 62
train / 31 test claims - so treat this as a scaffold shakeout, not a headline
number.)

## Pre-registered promotion criteria (all arms, checked after the runs)
- **Escalation GRPO-v2** (gate-oversample) promotes iff, on the frozen test
  split: `gate_recall >= 0.99` AND `reward >= SFT_baseline + 3pts`.
- **DPO** is compared on the *same ruler* (same frozen eval-256, same
  reward/gate metric) and held to the same bar as escalation GRPO-v2.
- **Citation GRPO** promotes iff `verdict_acc` beats the prompted baseline by
  `>= 5pts` AND `fabricated_rate == 0`.

## 7B arm (A100 OOM knobs)
Scaling from Qwen2.5-0.5B to a 7B model on the single A100 80GB:
- per-device batch 8 + `--grad-accum 2` (both trainers take `--grad-accum`),
- consider the TRL vLLM generation backend for GRPO rollout throughput,
- reach for **gradient checkpointing first** if you OOM, before cutting batch.

## Note on env_seeds versions
The env dir ships `env_seeds_v0.1/v0.2/v0.3.json`. The loader
(`escalation_env_v01.py`) prefers **v0.3** (gate-corrected, 160 train labels),
which is the A2 spec. `env_seeds_v0.2.json` (1024 expanded train seeds) exists
but is **intentionally NOT loaded** - A2 is a small-label supervision baseline,
so the 160-label v0.3 set is deliberate, not an oversight. Do not "fix" the
loader to grab v0.2. Each run's `run_manifest.json` records the exact
`env_seeds_version` used.

## Budget
A100: SFT <1h, GRPO ~2-4h, ~USD 20-50, inside the USD 100 / 24 A100h cap.
Fidelity limits (model-derived p, always-adequate deep, small cost sample)
apply to every number here - see escalation_env_v0.1/README.md.
