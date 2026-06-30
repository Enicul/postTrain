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

## EXP-2026-06-30-003 - Citation verifier repair v0.1

Goal:

Diagnose why the first citation verifier baseline failed, create an auditable
error taxonomy, generate repaired dataset variants, and run scoped repair
baselines before any GPU fine-tuning.

Data:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/datasets/citation_verifier
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_first_training_20260630T030852Z/citation_verifier/predictions_test.jsonl
```

Commands:

```bash
python3 training-corpus/scripts/repair_citation_verifier.py \
  --repair-id citation_verifier_repair_v0.1

python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/repaired_datasets \
  --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/baselines \
  --run-id citation_repair_probe_v0.1 \
  --datasets citation_verifier_url,citation_support_binary
```

Artifacts:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1
```

Important files:

```text
README.md
error_taxonomy.md
error_taxonomy.json
test_error_audit.jsonl
probe_metrics.json
repaired_datasets/citation_verifier_url/
repaired_datasets/citation_support_binary/
baselines/citation_repair_probe_v0.1/
```

Taxonomy:

| Failure type | Count |
| --- | ---: |
| composite_claim | 22 |
| support_boundary_confusion | 17 |
| source_quality_feature_missing | 10 |
| hard_negative_overaccepted | 8 |
| partial_support_boundary | 6 |
| rare_negative_class_boundary | 6 |
| positive_support_missed | 5 |

Metrics:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy | Interpretation |
| --- | ---: | ---: | ---: | --- |
| original citation_verifier | 0.2581 | 0.1441 | 0.4839 | failed baseline |
| citation_verifier_url | 0.2581 | 0.1390 | 0.4839 | source URL/domain alone did not help |
| citation_support_binary | 0.3871 | 0.3767 | 0.5806 | clearer stage-1 task, but still weak |

Failures:

- A scratch URL probe first overstated improvement because missing `source_url`
  values were rendered as literal `None`. The repair script normalizes missing
  URLs to empty strings. See `F-2026-06-30-008`.
- `trace_id` improves probe metrics, but this is task-identity leakage and must
  stay diagnostic-only.
- Binary support schema improves macro F1 versus the five-way baseline but does
  not beat the majority baseline on accuracy.

Decision:

Do not start citation-verifier GPU fine-tuning yet. The next repair must add
more clean hard negatives, positive official spans, partial-support spans, and
insufficient/contradict examples before model-side work is meaningful.

Next:

Create `citation_verifier_repair_v0.2` with new rows targeted at:

```text
hard_negative_overaccepted
partial_support_boundary
rare_negative_class_boundary
source_quality_feature_missing
```
