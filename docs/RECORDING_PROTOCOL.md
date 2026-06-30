# Recording Protocol

This repo uses summary-first recording by default. The goal is to preserve the
post-training audit trail without overloading the local machine with large
append-only logs or full row-level prediction dumps.

## Why This Changed

The old protocol treated every run artifact as something to keep locally:
`events.jsonl`, full `predictions_*.jsonl`, full `errors.jsonl`, checkpoints,
metrics, models, and README files. That was acceptable for tiny toy runs, but it
does not scale once KIWI data moves toward real trajectories, social radar
captures, long-research traces, and larger specialist datasets.

The new rule is:

```text
Record enough to resume, audit, and explain decisions.
Do not record every row by default.
```

## Default Local Artifacts

Every run should write:

```text
config.json
manifest.json
logs/checkpoint.json
logs/events.jsonl
metrics.json
README.md
prediction_samples*.jsonl
error_samples*.jsonl
```

`events.jsonl` should contain phase-level events only: run start, dataset start,
split loaded, evaluation complete, failure, and run complete. It should not log
per-row activity.

Prediction and error files should be capped samples by default. The current
script defaults are:

```text
record_mode = summary
prediction_sample_limit = 200
error_sample_limit = 200
```

## Full Recording

Full row-level prediction or error dumps are allowed only when explicitly
requested:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --record-mode full

python3 training-corpus/scripts/evaluate_baseline_holdouts.py \
  --record-mode full
```

Before using full mode, make sure the output target can handle the size. For GPU
runs, large model checkpoints, rollout traces, and full prediction dumps should
stay on the server, in object storage, or in a release/LFS-style artifact store,
not in the local Git working tree.

## What To Commit

Commit:

- scripts,
- configs,
- metrics summaries,
- manifests,
- checkpoints,
- README files,
- small model/joblib artifacts only when they are intentionally part of a small
  CPU baseline,
- capped samples needed for error analysis.

Do not commit by default:

- large GPU checkpoints,
- full rollout dumps,
- full prediction dumps from large runs,
- raw browser/session captures,
- private data, secrets, cookies, profiles, or `.env` files.

## How To Preserve Failure Evidence

A failure does not require full logs. Capture:

```text
symptom
command
run id
failed stage
small error excerpt
root cause or best hypothesis
fix/change
rerun result
remaining risk
```

Store that in `FAILURE_LOG.md`, `EXPERIMENT_LOG.md`, and the run README. If the
failure needs row-level evidence, write a capped `error_samples*.jsonl` file.

## Resume Rule

When resuming, read in this order:

1. `PROGRESS.md`
2. `TODO.md`
3. `CHECKPOINTS.md`
4. `FAILURE_LOG.md`
5. the run's `metrics.json`
6. capped `error_samples*.jsonl` or `prediction_samples*.jsonl`

Only use full row-level files if the previous agent deliberately ran with
`--record-mode full`.
