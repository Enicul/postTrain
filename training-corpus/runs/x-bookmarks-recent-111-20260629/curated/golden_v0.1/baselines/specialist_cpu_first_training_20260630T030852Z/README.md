# KIWI Specialist CPU Baselines

These are lightweight baseline classifiers for narrow KIWI specialists.
They are not final post-training models; they are the measurable floor before GPU fine-tuning.

## Run

- run id: `specialist_cpu_first_training_20260630T030852Z`
- created at: `2026-06-30T03:08:53Z`
- source data: `/Users/lucine/Documents/Job/projects/postTrain/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/datasets`

## Results

| Dataset | Target | Train | Dev | Test | Test acc | Test macro F1 | Majority acc |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| router_classifier | route_label | 249 | 47 | 48 | 0.9167 | 0.9368 | 0.3542 |
| risk_reviewer | risk_level | 121 | 23 | 37 | 0.5946 | 0.3986 | 0.4595 |
| citation_verifier | support_type | 108 | 27 | 31 | 0.2581 | 0.1441 | 0.4839 |

## Artifacts

- `config.json`: exact run configuration.
- `checkpoint.json`: resumability/status record.
- `events.jsonl`: chronological training log.
- `manifest.json`: environment and git state.
- `<dataset>/model.joblib`: trained sklearn baseline.
- `<dataset>/metrics.json`: metrics and confusion matrix.
- `<dataset>/predictions_*.jsonl`: row-level predictions for error analysis.

## How To Re-run

```bash
python3 training-corpus/scripts/train_specialist_baselines.py
```

For a stable output directory on a server:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_baselines_server_test \
  --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines
```
