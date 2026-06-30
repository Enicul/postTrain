# Git Workflow

## Remote

```text
https://github.com/Enicul/postTrain
```

## Push Cadence

Push at meaningful checkpoints:

- repo scaffold complete,
- reusable script added,
- baseline run completed,
- failed run diagnosed,
- dataset repaired/frozen,
- before server/GPU transfer,
- before ending a long session.

## Commit Style

Use artifact-state messages:

```text
docs: initialize post-training operating protocol
baseline: add CPU specialist runner and v0.1 metrics
data: repair citation verifier span labels
experiment: log router boundary regression
```

## Before Commit

Run:

```bash
git status --short
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
```

If committing a run artifact, verify:

```bash
cat <run_dir>/logs/checkpoint.json
sed -n '1,120p' <run_dir>/README.md
```

## Dirty Worktree Rule

Do not leave a dirty worktree without explaining why in `PROGRESS.md` or
`CHECKPOINTS.md`.
