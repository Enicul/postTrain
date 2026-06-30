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

## EXP-2026-06-30-004 - Citation verifier repair v0.2

Goal:

Test whether targeted train-only citation augmentation can improve the weak
v0.1 repair probes without leaking dev/test information.

Data:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/datasets/citation_verifier
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2
```

Commands:

```bash
python3 training-corpus/scripts/build_citation_repair_v02.py

python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/repaired_datasets \
  --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/baselines \
  --run-id citation_repair_probe_v0.2 \
  --datasets citation_verifier_url,citation_support_binary
```

Artifacts:

```text
training-corpus/scripts/build_citation_repair_v02.py
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/README.md
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/manifest.json
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/candidate_generation_pool.jsonl
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/repaired_datasets/
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/baselines/citation_repair_probe_v0.2/
```

Candidate generation:

| Rule | Candidate rows |
| --- | ---: |
| atomic_positive_from_supports_claim_part | 34 |
| hard_negative_cross_trace_overlap | 40 |
| missing_evidence_insufficient | 30 |
| partial_support_boundary_upsample | 20 |

Local ablation:

| Strategy | Five-way test acc / macro F1 | Binary test acc / macro F1 | Decision |
| --- | --- | --- | --- |
| original URL probe | 0.2581 / 0.1390 | 0.3871 / 0.3767 | weak baseline |
| hard negatives only | 0.3548 / 0.2400 | 0.4194 / 0.4139 | best binary repair |
| missing-evidence only | 0.2581 / 0.2944 | 0.3871 / 0.3845 | helps five-way macro F1 |
| hard negatives + missing evidence | 0.3871 / 0.3333 | 0.3871 / 0.3845 | best five-way repair |
| all generated rows | 0.2581 / 0.2575 | 0.3548 / 0.3376 | hurt binary boundary |

Selected training strategy:

| Dataset | Train rows | Selected generated rows |
| --- | ---: | --- |
| citation_verifier_url | 178 | hard negatives + missing evidence |
| citation_support_binary | 148 | hard negatives only |

Metrics:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy | Interpretation |
| --- | ---: | ---: | ---: | --- |
| original citation_verifier | 0.2581 | 0.1441 | 0.4839 | failed baseline |
| v0.1 citation_verifier_url | 0.2581 | 0.1390 | 0.4839 | URL/domain alone did not help |
| v0.1 citation_support_binary | 0.3871 | 0.3767 | 0.5806 | clearer but weak |
| v0.2 citation_verifier_url | 0.3871 | 0.3333 | 0.4839 | targeted repair improved five-way macro F1 |
| v0.2 citation_support_binary | 0.4194 | 0.4139 | 0.5806 | targeted hard negatives improved binary macro F1 |

Failures:

- Adding every generated row hurt the binary support task. Synthetic data can
  flood the training split and blur a cleaner decision boundary.
- v0.2 still does not beat the majority baseline on accuracy. This is an
  improvement, not a green light for GPU fine-tuning.
- The repair is train-only and synthetic-derived. It still needs real official
  paragraph spans and manually/LLM-audited support boundaries.

Decision:

Keep citation-verifier work in the data-repair phase. v0.2 proves that the
failure taxonomy is actionable, but the next repair should collect higher
quality real evidence spans instead of scaling model size.

Next:

Build a small human/LLM-audited citation golden set with:

```text
official positive spans
partial-support boundaries
rare contradicts / insufficient rows
source-quality labels
```

## EXP-2026-06-30-005 - Import KIWI ai-expanded v0.1 curated checkpoint

Goal:

Bring the larger Agent/KIWI v0.6 curated training pack into the standalone
`postTrain` repo so it can be moved to a server without depending on the Agent
workspace.

Source data:

```text
/Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Command:

```bash
rsync -a --delete \
  /Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ \
  training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/
```

Artifacts:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Imported selected rows:

| Dataset | Train | Dev | Test |
| --- | ---: | ---: | ---: |
| calculation_verifier | 2,000 | 500 | 500 |
| citation_verifier | 6,000 | 1,200 | 1,200 |
| event_extractor | 6,000 | 1,200 | 1,200 |
| grpo_rollouts | 8,000 | 1,600 | 1,600 |
| memo_quality_scorer | 8,000 | 1,600 | 1,600 |
| preference_pairs | 8,000 | 1,600 | 1,600 |
| risk_reviewer | 8,000 | 1,600 | 1,600 |
| router_classifier | 6,000 | 1,200 | 1,200 |
| sft_trajectories | 8,000 | 1,600 | 1,600 |

Failures:

None during import.

Decision:

Use this as the next checkpoint for expanded-data baselines, but preserve the
smaller `golden_v0.1` as the stricter social/bookmark-derived trace pack.

Next:

Run CPU baselines on the expanded data and then evaluate against harder
realistic holdouts.

## EXP-2026-06-30-006 - AI expanded CPU baseline v0.1

Goal:

Establish a measurable CPU floor on the larger `kiwi-brain-ai-expanded-v0.1`
datasets before GPU small-model work.

Data:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Code change:

`train_specialist_baselines.py` was updated to support the newer expanded
schema:

- `risk_reviewer` now reads `user_query`, `symbol`, `task_family`,
  `draft_memo`, and `cited_evidence_ids`;
- `citation_verifier` now reads `evidence_text`, `evidence_id`, and `source`;
- `citation_verifier` accepts `label.verdict` and maps `supported` to
  `supports`.

Canonical command:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1 \
  --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines \
  --run-id specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Artifacts:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Metrics:

| Specialist | Target | Train | Dev | Test | Test accuracy | Test macro F1 | Majority accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| router_classifier | route_label | 6,000 | 1,200 | 1,200 | 1.0000 | 1.0000 | 0.1667 |
| risk_reviewer | risk_level | 8,000 | 1,600 | 1,600 | 1.0000 | 1.0000 | 0.6669 |
| citation_verifier | support/verdict | 6,000 | 1,200 | 1,200 | 0.9000 | 0.8978 | 0.3333 |

Failures / caveats:

- First run used a placeholder timestamp in the run id
  `specialist_cpu_ai_expanded_v0.1_20260630T000000Z`. It is non-canonical and
  superseded by the timestamped run above.
- Router and risk reviewer scores are too clean to treat as proof of real-world
  generalization. The expanded data is balanced and template-heavy.
- Citation verifier improved strongly, but synthetic mismatched and
  missing-evidence negatives likely make the task easier than real citation
  grounding.

Decision:

The expanded datasets are useful as a GPU-readiness and pipeline sanity
checkpoint, but the next step must be realistic holdout evaluation before
claiming model quality.

Next:

Evaluate the expanded router/risk/citation baselines on real tool traces,
long-research episodes, and harder evidence-chain negatives.

## EXP-2026-06-30-007 - Realistic holdout eval v0.1

Goal:

Test whether the expanded CPU baselines generalize beyond their own
train/dev/test split before starting GPU fine-tuning.

Why:

The expanded router and risk baselines reached 1.0 on their own test split.
That is a warning sign: the split may be template-heavy or too similar across
train/dev/test. A post-training artifact should prove that we can detect this,
not just report flattering metrics.

Script:

```text
training-corpus/scripts/evaluate_baseline_holdouts.py
```

Command:

```bash
python3 training-corpus/scripts/evaluate_baseline_holdouts.py \
  --run-id realistic_holdout_eval_v0.1_20260630T083000Z
```

Baseline under test:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Artifacts:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z/holdouts/realistic_holdout_eval_v0.1_20260630T083000Z
```

What the evaluator does:

- loads existing `model.joblib` artifacts;
- does not train new models;
- evaluates old golden rows, long-research rows, and real tool trace router
  rows;
- reports both all-row accuracy and seen-label-only accuracy;
- marks schema gaps when holdout labels were never present in the model's
  training labels.

Results:

| Holdout | Dataset | Rows | Accuracy all rows | Accuracy seen-labels only | Schema gap |
| --- | --- | ---: | ---: | ---: | --- |
| golden_v0.1_router_all | router_classifier | 344 | 0.3023 | 0.3611 | yes |
| golden_v0.1_risk_all | risk_reviewer | 181 | 0.2762 | 0.4464 | yes |
| golden_v0.1_citation_all | citation_verifier | 166 | 0.4819 | 0.6957 | yes |
| long_research_repair_25_router_all | router_classifier | 25 | 0.4800 | 0.4800 | no |
| long_research_repair_25_risk_all | risk_reviewer | 25 | 0.0000 | n/a | yes |
| long_research_repair_25_citation_all | citation_verifier | 417 | 0.0000 | n/a | yes |
| real_tool_trace_pilot_10_router | router_classifier | 10 | 0.0000 | 0.0000 | yes |

Failures:

- The first script run failed because `append_event()` received `path` twice.
  The event payload field was renamed to `source_path` and the run was retried.
- The router baseline over-predicted `financial_calculation` on social and real
  tool trace prompts.
- The expanded router label set lacks `risk_review` and
  `clarification_needed`.
- The expanded risk label set lacks `medium`.
- The expanded citation label set does not cover old/long-research labels:
  `partial_support`, `insufficient`, `contradicts`, `candidate_evidence`, and
  `search_snippet_candidate_evidence`.

Decision:

The realistic holdout result invalidates the idea of going straight to GPU
fine-tuning. The next step is data-contract repair and boundary-case generation.

Next:

Create a repair pack that:

```text
router: add real_tool_trace rows, risk_review, clarification_needed,
        evidence_check vs deep_research boundaries
risk: add medium and human-gate semantics
citation: separate candidate evidence from verified support labels
```
