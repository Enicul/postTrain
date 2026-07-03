# GPU Runbook - Escalation SFT/GRPO on the A100

Owner-facing, step-by-step. One A100 80GB. Chain:
**A1 prompted-eval -> A2 SFT (LoRA) -> A3 GRPO (TRL GRPOTrainer, K=8)**,
env = escalation env v0.3 (the loader already prefers v0.3's 160 train labels).

Every run lands in `out-dir/<run_id>/` where `run_id = <UTC>-<git sha>` (e.g.
`20260703T0412Z-1111bfc`). The scripts REFUSE to overwrite a non-empty run dir.
Failed runs are interview evidence: never deleted, never overwritten.

---

## 0. Setup

```bash
cd training-corpus/scripts/rl
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-rl.txt          # pins are known-good; manifest records the real freeze
ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1
```

Data dirs to have present (pull with the repo):
- the env dir above (`env_seeds_v0.3.json`, `outcome_table_v0.3.json`,
  `cost_table_v0.1.json`, `env_anon_mapping.json`),
- nothing else - the reward/label logic is CPU-only and self-contained.

CPU smoke before touching the GPU (no install needed):

```bash
python reward_escalation.py $ENV
python build_sft_labels.py --env-dir $ENV --split train --lambda 0.3 --out /tmp/sft_train.jsonl
```

---

## 1. A1 - motivation gate (prompted small model, no training)

Dump a prompted-small-model policy to `preds.jsonl` (rows: `seed_id`/`qid`,
`first`, `on_fail`), then:

```bash
python eval_escalation_policy.py --env-dir $ENV --split test --pred-file preds.jsonl
```

KILL: if reward is within 3 pts of oracle AND `gate_recall >= 0.99`, stop -
small models need no training (record the negative). Else continue to A2.

---

## 2. A2 - argmax-SFT baseline (GPU)

```bash
python build_sft_labels.py --env-dir $ENV --split train --lambda 0.3 --out sft_train.jsonl
python sft_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --train sft_train.jsonl \
    --out-dir runs/sft_qwen05b --seed 0
```

Note the printed `run_id`, then evaluate that run's adapter:

```bash
python eval_escalation_policy.py --env-dir $ENV --split test \
    --model Qwen/Qwen2.5-0.5B-Instruct \
    --adapter runs/sft_qwen05b/<RUN_ID>/adapter --out sft_eval.json
```

Record the SFT reward at lambda 0.3 -> **BASELINE**.

---

## 3. A3 - GRPO (GPU)

```bash
python grpo_escalation.py --model Qwen/Qwen2.5-0.5B-Instruct --env-dir $ENV \
    --lambda 0.3 --init-adapter runs/sft_qwen05b/<SFT_RUN_ID>/adapter \
    --out-dir runs/grpo_qwen05b --seed 0 --save-steps 50
python eval_escalation_policy.py --env-dir $ENV --split test \
    --model Qwen/Qwen2.5-0.5B-Instruct \
    --adapter runs/grpo_qwen05b/<GRPO_RUN_ID>/adapter \
    --baseline-reward <SFT_BASELINE> --out grpo_eval.json
```

KILL (pre-registered): GRPO must beat argmax-SFT by **>= 3 reward pts** AND not
drop gate recall (`>= 0.99`), else record "SFT suffices". The eval prints this
check.

### 7B arm / OOM knobs
If you scale to a 7B model, use per-device batch 8 + `--grad-accum 2`, consider
the TRL vLLM generation backend for GRPO rollouts, and reach for **gradient
checkpointing as the first OOM knob**. See the "7B arm" note in
`training-corpus/scripts/rl/README.md`.

---

## Monitoring

In a second terminal on the GPU box:

```bash
python monitor_run.py runs/grpo_qwen05b/<RUN_ID>      # one-line status every 60s
```

It exits nonzero + LOUD on NaN/inf loss/reward or a dead heartbeat (>10 min
with no new trainer_log line). Handy tails:

```bash
tail -f runs/grpo_qwen05b/<RUN_ID>/trainer_log.jsonl     # every on_log dict
tail -f runs/grpo_qwen05b/<RUN_ID>/reward_trace.jsonl    # per-batch mean_reward, gate_violation_rate, action_mix
tail -f runs/grpo_qwen05b/<RUN_ID>/generations.jsonl     # every completion + parsed plan + reward
```

To resume after an interruption (checkpoints are under the run dir):

```bash
python grpo_escalation.py ... --out-dir runs/grpo_qwen05b --resume runs/grpo_qwen05b/<RUN_ID>/checkpoint-150
```

(Resume mints a NEW run_id/dir but continues optimizer state from the given
checkpoint. Link it to the interrupted run with `--parent-run <RUN_ID>`.)

---

## WHAT TO SAVE

Save **everything** under `runs/`:
- checkpoints (`checkpoint-*/`), `adapter/`,
- `run_manifest.json`, `trainer_log.jsonl`,
- `generations.jsonl`, `reward_trace.jsonl`,
- `metrics.json`, `*_eval.json`.

**Failed runs are NEVER deleted or overwritten - they are interview evidence.**
Weights/checkpoints stay off git (see "bring the results home"); the jsonls,
manifests, and summaries come home.

---

## FAILURE PROTOCOL

When a run fails, collapses, or hits a kill criterion:

1. **Keep the dir untouched.** Do not delete, do not re-use the run_id.
2. **Write a `FAILURE_LOG.md` entry** at the repo root using this template:

   ```markdown
   ## F-<YYYY-MM-DD>-NNN - <one-line symptom>

   Symptom:
   <what you saw - loss NaN at step X, gate_violation_rate climbing, OOM, etc.>

   Evidence files:
   runs/<arm>/<failed_run_id>/trainer_log.jsonl
   runs/<arm>/<failed_run_id>/reward_trace.jsonl
   runs/<arm>/<failed_run_id>/generations.jsonl
   runs/<arm>/<failed_run_id>/run_manifest.json

   Diagnosis:
   <root cause - lr too high, reward hacking a parse fallback, batch too big...>

   Fix:
   <the one change - lower lr, add grad-accum, clamp completion length...>

   New run:
   run_id <new_run_id>, launched with --parent-run <failed_run_id>
   ```

3. **Re-run with the linkage:**

   ```bash
   python grpo_escalation.py ... --out-dir runs/grpo_qwen05b --parent-run <FAILED_RUN_ID>
   ```

   The new run's `run_manifest.json` records `parent_run_id`, closing the
   error-correction chain (what failed -> diagnosis -> change -> re-run link).

---

## Bring the results home

Weights and checkpoints stay OFF git (they are large; `.gitignore` excludes the
`runs/**` adapter/checkpoint patterns - verify with `git check-ignore`). Bring
the tree back and commit the summaries only:

```bash
rsync -av <gpu-box>:/path/to/postTrain/training-corpus/scripts/rl/runs/ ./runs/
# commit: manifests, *_eval.json, metrics.json, FAILURE_LOG.md entries, summaries
# do NOT commit: checkpoint-*/, adapter/ weight files
```
