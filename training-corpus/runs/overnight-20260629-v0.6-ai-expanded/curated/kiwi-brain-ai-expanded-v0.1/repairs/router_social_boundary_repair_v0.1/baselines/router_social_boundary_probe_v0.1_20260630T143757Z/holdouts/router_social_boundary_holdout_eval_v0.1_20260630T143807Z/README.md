# Realistic Holdout Evaluation

This run loads an existing CPU baseline and evaluates it on external
holdouts. It does not train new models.

## Why

The expanded train/dev/test split produced very high router and risk
metrics. This holdout run checks whether those scores survive older
golden rows, long-research traces, and real tool traces.

## Run

- run id: `router_social_boundary_holdout_eval_v0.1_20260630T143807Z`
- baseline: `/Users/lucine/Documents/Job/projects/postTrain/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1/baselines/router_social_boundary_probe_v0.1_20260630T143757Z`
- created at: `2026-06-30T14:38:08Z`

## Results

| Holdout | Dataset | Rows | Acc all | Macro F1 all | Comparable rows | Acc seen-labels | Schema gap | Unseen true labels |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| golden_v0.1_router_all | router_classifier | 344 | 0.9012 | 0.9332 | 344 | 0.9012 | False |  |
| long_research_repair_25_router_all | router_classifier | 25 | 0.96 | 0.1224 | 25 | 0.96 | False |  |
| real_tool_trace_pilot_10_router | router_classifier | 10 | 0.9 | 0.3472 | 10 | 0.9 | False |  |

## Recording Mode

- mode: `summary`
- prediction sample limit: `200`
- error sample limit: `200`

Default holdout runs write capped samples instead of full row-level
prediction files. Use `--record-mode full` only when full error
analysis is necessary and the output location can handle it.

## Reading The Metrics

- `accuracy_all_rows` treats unseen labels as failures. This is useful for
  finding schema gaps.
- `accuracy_seen_labels_only` evaluates only rows whose gold label existed
  in the baseline model's training label set. This is useful for measuring
  transfer on comparable rows without hiding the schema gap.
- A `schema_gap` means the model was never trained to emit one or more
  labels in this holdout, so the fix is data/schema work before model work.
