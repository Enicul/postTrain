# Server Runbook

Use this when moving work to a VPS or A100 box.

## Clone

```bash
git clone https://github.com/Enicul/postTrain.git
cd postTrain
```

## Python Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r training-corpus/requirements-baseline.txt
```

## CPU Baseline Smoke Test

```bash
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
python3 -m py_compile training-corpus/scripts/evaluate_baseline_holdouts.py
python3 training-corpus/scripts/evaluate_baseline_holdouts.py --help
```

## Re-run Specialist Baselines

Default recording is summary-first. It writes metrics, checkpoint, phase events,
and capped prediction/error samples. It does not write full row-level prediction
dumps unless `--record-mode full` is passed.

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_baselines_server_$(date -u +%Y%m%dT%H%M%SZ)
```

Then inspect:

```bash
RUN_DIR=$(ls -td training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_baselines_server_* | head -1)
cat "$RUN_DIR/logs/checkpoint.json"
sed -n '1,140p' "$RUN_DIR/README.md"
```

Use full recording only for a deliberate deep error-analysis run:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --record-mode full \
  --run-id specialist_cpu_baselines_full_$(date -u +%Y%m%dT%H%M%SZ)
```

## After Run

Update:

- `EXPERIMENT_LOG.md`
- `FAILURE_LOG.md` if anything failed or underperformed
- `PROGRESS.md`
- `CHECKPOINTS.md`
- `TODO.md`

Then commit and push.

Do not commit large GPU checkpoints, full rollout dumps, or large prediction
files. Keep those on the server, in object storage, or in a release/LFS-style
artifact store.

## GPU Work Later

Do not start GPU SFT/DPO/GRPO until:

- CPU baseline is recorded,
- target dataset is audited,
- expected improvement over baseline is defined,
- rollback/resume path is clear.
