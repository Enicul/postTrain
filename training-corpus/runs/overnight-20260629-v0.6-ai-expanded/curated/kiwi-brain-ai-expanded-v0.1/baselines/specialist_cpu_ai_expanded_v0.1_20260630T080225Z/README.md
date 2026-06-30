# KIWI Specialist CPU Baselines

These are lightweight baseline classifiers for narrow KIWI specialists.
They are not final post-training models; they are the measurable floor before GPU fine-tuning.

## Run

- run id: `specialist_cpu_ai_expanded_v0.1_20260630T080225Z`
- created at: `2026-06-30T08:02:25Z`
- source data: `/Users/lucine/Documents/Job/projects/postTrain/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1`

## Results

| Dataset | Target | Train | Dev | Test | Test acc | Test macro F1 | Majority acc |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| router_classifier | route_label | 6000 | 1200 | 1200 | 1.0 | 1.0 | 0.1667 |
| risk_reviewer | risk_level | 8000 | 1600 | 1600 | 1.0 | 1.0 | 0.6669 |
| citation_verifier | support_type | 6000 | 1200 | 1200 | 0.9 | 0.8978 | 0.3333 |

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
