# Realistic Holdout Evaluation

This run loads an existing CPU baseline and evaluates it on external
holdouts. It does not train new models.

## Why

The expanded train/dev/test split produced very high router and risk
metrics. This holdout run checks whether those scores survive older
golden rows, long-research traces, and real tool traces.

## Run

- run id: `realistic_holdout_eval_v0.1_20260630T083000Z`
- baseline: `/Users/lucine/Documents/Job/projects/postTrain/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z`
- created at: `2026-06-30T08:31:38Z`

## Results

| Holdout | Dataset | Rows | Acc all | Macro F1 all | Comparable rows | Acc seen-labels | Schema gap | Unseen true labels |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| golden_v0.1_router_all | router_classifier | 344 | 0.3023 | 0.2632 | 288 | 0.3611 | True | clarification_needed, risk_review |
| golden_v0.1_risk_all | risk_reviewer | 181 | 0.2762 | 0.2369 | 112 | 0.4464 | True | medium |
| golden_v0.1_citation_all | citation_verifier | 166 | 0.4819 | 0.1692 | 115 | 0.6957 | True | contradicts, insufficient, partial_support |
| long_research_repair_25_router_all | router_classifier | 25 | 0.48 | 0.1081 | 25 | 0.48 | False |  |
| long_research_repair_25_risk_all | risk_reviewer | 25 | 0.0 | 0.0 | 0 | None | True | medium |
| long_research_repair_25_citation_all | citation_verifier | 417 | 0.0 | 0.0 | 0 | None | True | candidate_evidence, search_snippet_candidate_evidence |
| real_tool_trace_pilot_10_router | router_classifier | 10 | 0.0 | 0.0 | 9 | 0.0 | True | risk_review |

## Reading The Metrics

- `accuracy_all_rows` treats unseen labels as failures. This is useful for
  finding schema gaps.
- `accuracy_seen_labels_only` evaluates only rows whose gold label existed
  in the baseline model's training label set. This is useful for measuring
  transfer on comparable rows without hiding the schema gap.
- A `schema_gap` means the model was never trained to emit one or more
  labels in this holdout, so the fix is data/schema work before model work.
