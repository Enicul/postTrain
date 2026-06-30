# Experiment Log

Append-only experiment record. Do not delete failed runs.

## Template

```text
## EXP-YYYY-MM-DD-NNN - name

Goal:
Data:
Command:
Artifacts:
Metrics:
Failures:
Decision:
Next:
```

## EXP-2026-06-30-001 - CPU specialist baselines v0.1

Goal:

Establish cheap, reproducible CPU baselines before spending GPU time on small
LLM fine-tuning.

Data:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/datasets
```

Command:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_baselines_v0.1
```

Artifacts:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_baselines_v0.1
```

Metrics:

| Specialist | Target | Test accuracy | Test macro F1 |
| --- | --- | ---: | ---: |
| router_classifier | route_label | 0.9167 | 0.9368 |
| risk_reviewer | risk_level | 0.5946 | 0.3986 |
| citation_verifier | support_type | 0.2581 | 0.1441 |

Failures:

- First implementation used `datetime.UTC`, which fails on Python 3.9.
- Event logger had a `path` keyword collision.
- Citation verifier underperformed badly on held-out data.

Decision:

- Router baseline is usable as coordinator reference.
- Risk reviewer remains a weak baseline.
- Citation verifier should not move to GPU fine-tuning until citation-span data
  quality and label schema are repaired.

Next:

Inspect citation verifier prediction errors and create a repaired citation
audit set.

## EXP-2026-06-30-002 - First tracked CPU training batch

Goal:

Run the first explicit training batch after repo initialization and preserve it
as a separate checkpoint from the imported reference baseline.

Data:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/datasets
```

Command:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_first_training_20260630T030852Z
```

Artifacts:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_first_training_20260630T030852Z
```

Metrics:

| Specialist | Target | Train | Dev | Test | Test accuracy | Test macro F1 | Majority accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| router_classifier | route_label | 249 | 47 | 48 | 0.9167 | 0.9368 | 0.3542 |
| risk_reviewer | risk_level | 121 | 23 | 37 | 0.5946 | 0.3986 | 0.4595 |
| citation_verifier | support_type | 108 | 27 | 31 | 0.2581 | 0.1441 | 0.4839 |

Failures:

- Training itself completed.
- A one-off metric-summary helper failed because it assumed a non-existent
  `splits` key in `metrics.json`. The corrected inspection used prediction file
  row counts instead. See `F-2026-06-30-006`.
- Citation verifier again underperformed and remained worse than the majority
  baseline on test accuracy.

Decision:

The baseline training chain is reproducible. This is enough to treat the repo as
ready for the first repair loop, but not enough to start citation-verifier GPU
fine-tuning.

Next:

Start citation-verifier error analysis from:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_first_training_20260630T030852Z/citation_verifier/predictions_test.jsonl
```
