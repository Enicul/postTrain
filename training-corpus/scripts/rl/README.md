# RL Phase 2 scripts (Plan A)

Pull-and-run on an A100. The reward/label/env logic is CPU-only and has no
heavy deps; only sft_/grpo_ training and adapter eval need the GPU stack.

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
        --out-dir runs/sft_qwen05b
    python eval_escalation_policy.py --env-dir $ENV --split test \
        --model Qwen/Qwen2.5-0.5B-Instruct --adapter runs/sft_qwen05b/adapter --out sft_eval.json
Record the SFT reward at lambda 0.3 -> BASELINE.

## 3. GRPO (A3, GPU)
    python grpo_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --env-dir $ENV --lambda 0.3 \
        --init-adapter runs/sft_qwen05b/adapter --out-dir runs/grpo_qwen05b
    python eval_escalation_policy.py --env-dir $ENV --split test \
        --model Qwen/Qwen2.5-0.5B-Instruct --adapter runs/grpo_qwen05b/adapter \
        --baseline-reward <SFT_BASELINE> --out grpo_eval.json
The eval prints the pre-registered kill check (GRPO must beat SFT by >=3 pts
and hold gate_recall). Commit adapters + *_eval.json + metrics.json only - no
base weights, no large checkpoints (RECORDING_PROTOCOL / D-2026-06-30-006).

## Budget
A100: SFT <1h, GRPO ~2-4h, ~USD 20-50, inside the USD 100 / 24 A100h cap.
Fidelity limits (model-derived p, always-adequate deep, small cost sample)
apply to every number here - see escalation_env_v0.1/README.md.
