# Codex Workflow

This file is for Codex agents working in this repo.

## First Actions

Run:

```bash
pwd
git status --short
sed -n '1,220p' PROGRESS.md
sed -n '1,220p' TODO.md
sed -n '1,220p' CHECKPOINTS.md
```

Then inspect the relevant script, data, or run directory before proposing work.

## Editing Rules

- Use `apply_patch` for manual edits.
- Use `rg` for search.
- Do not delete prior run artifacts unless explicitly asked.
- Keep failures and bad metrics visible.
- Keep docs synchronized with code and run outputs.

## Completion Rule

Before saying something is done, run a fresh verification command and read the
output. For example:

```bash
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
cat training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_baselines_v0.1/logs/checkpoint.json
```

## Baseline Run

Default CPU baseline:

```bash
python3 -m pip install -r training-corpus/requirements-baseline.txt
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_baselines_local_test
```

Stable reference run:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_baselines_v0.1
```

## When Running Experiments

After a run:

1. Read `logs/checkpoint.json`.
2. Read `metrics.json`.
3. Inspect row-level predictions for suspicious failures.
4. Update `EXPERIMENT_LOG.md`.
5. Update `FAILURE_LOG.md` if metrics are weak or an error occurred.
6. Update `PROGRESS.md` and `TODO.md`.
7. Commit and push if the checkpoint is useful.

## What Not To Overclaim

Do not claim:

- the citation verifier is good,
- a GPU fine-tuned model is trained,
- KIWI is a trading agent,
- outcome return is a clean reward,
- synthetic data is production-quality.

Safe phrasing:

```text
We have a reproducible CPU baseline and an auditable data/checkpoint structure.
The router is a strong first baseline. Risk and citation need data/feature repair
before GPU fine-tuning.
```
