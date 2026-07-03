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
