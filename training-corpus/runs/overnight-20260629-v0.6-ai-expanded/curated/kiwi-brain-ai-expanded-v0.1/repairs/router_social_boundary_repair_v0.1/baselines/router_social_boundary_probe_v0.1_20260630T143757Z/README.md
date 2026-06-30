# KIWI Specialist CPU Baselines

These are lightweight baseline classifiers for narrow KIWI specialists.
They are not final post-training models; they are the measurable floor before GPU fine-tuning.

## Run

- run id: `router_social_boundary_probe_v0.1_20260630T143757Z`
- created at: `2026-06-30T14:37:57Z`
- source data: `/Users/lucine/Documents/Job/projects/postTrain/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1/repaired_datasets`

## Results

| Dataset | Target | Train | Dev | Test | Test acc | Test macro F1 | Majority acc |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| router_classifier | route_label | 7324 | 1454 | 1473 | 0.9966 | 0.9975 | 0.1833 |

## Artifacts

- `config.json`: exact run configuration.
- `checkpoint.json`: resumability/status record.
- `events.jsonl`: chronological training log.
- `manifest.json`: environment and git state.
- `<dataset>/model.joblib`: trained sklearn baseline.
- `<dataset>/metrics.json`: metrics and confusion matrix.
- `<dataset>/prediction_samples_*.jsonl`: capped row-level prediction samples.
- `<dataset>/error_samples_*.jsonl`: capped row-level error samples.
- Full row-level `predictions_*.jsonl` are only written with `--record-mode full`.

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
