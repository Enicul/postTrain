# Router Classifier Baseline v0.1

Model: TF-IDF char n-grams + balanced logistic regression.

Purpose: establish a measurable coordinator/router baseline before small-LM fine-tuning.

## Inputs

- main router train/dev/test: `/Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/datasets/router_classifier`
- repaired long-research holdout: `/Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/long_research_trace_source_quality_repair_25/datasets/router_classifier/all.jsonl`

The repaired long-research rows are not used as the main training set because all 25 rows are `deep_research`.

Feature hygiene: label-derived `required_tools` are intentionally excluded from the model input to avoid leakage.

## Key Metrics

- test route accuracy: 0.9167
- test macro F1: 0.9368
- majority baseline test accuracy: 0.3542
- test over-trigger rate: 0.0
- test under-trigger rate: 0.0
- test safety recall: 1.0
- repaired long-research holdout accuracy: 0.64

## Artifacts

- `model.joblib`
- `metrics.json`
- `predictions_train.jsonl`
- `predictions_dev.jsonl`
- `predictions_test.jsonl`
- `predictions_long_research_repair_holdout.jsonl`

## Interpretation

This baseline is useful for routing eval and error analysis. It should not be presented as the final trained Kiwi model.

The repaired long-research holdout is the most important residual gap: errors there indicate the router still confuses `evidence_check` with full `deep_research` for medium-risk investment research prompts.
