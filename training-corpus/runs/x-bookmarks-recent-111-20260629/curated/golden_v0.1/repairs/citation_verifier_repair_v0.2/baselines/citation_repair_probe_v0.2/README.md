# KIWI Specialist CPU Baselines

These are lightweight baseline classifiers for narrow KIWI specialists.
They are not final post-training models; they are the measurable floor before GPU fine-tuning.

## Run

- run id: `citation_repair_probe_v0.2`
- created at: `2026-06-30T05:29:47Z`
- source data: `/Users/lucine/Documents/Job/projects/postTrain/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/repaired_datasets`

## Results

| Dataset | Target | Train | Dev | Test | Test acc | Test macro F1 | Majority acc |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| citation_verifier_url | support_type | 178 | 27 | 31 | 0.3871 | 0.3333 | 0.4839 |
| citation_support_binary | support_binary | 148 | 27 | 31 | 0.4194 | 0.4139 | 0.5806 |

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
