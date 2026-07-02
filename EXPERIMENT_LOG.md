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

## EXP-2026-06-30-008 - Recording protocol migration

Goal:

Move future local runs from full row-level recording to summary-first recording.

Why:

The old artifact contract was useful while the datasets were tiny, but it
encouraged every experiment to write full prediction and error JSONL files. That
pattern can overload the local machine as KIWI data expands into long research
trajectories, real tool traces, social radar captures, and larger holdout sets.

Changed:

- Added `docs/RECORDING_PROTOCOL.md`.
- Patched `train_specialist_baselines.py` to default to `--record-mode summary`.
- Patched `evaluate_baseline_holdouts.py` to default to `--record-mode summary`.
- Added explicit `--record-mode full` only for deliberate deep error-analysis
  runs.
- Updated agent, Codex, server, progress, todo, checkpoint, decision, and failure
  docs so future agents do not copy the old full-output pattern.

Verification:

```bash
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py training-corpus/scripts/evaluate_baseline_holdouts.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
python3 training-corpus/scripts/evaluate_baseline_holdouts.py --help
python3 training-corpus/scripts/train_specialist_baselines.py --run-id smoke_summary_router --datasets router_classifier --out-root /tmp/posttrain-recording-smoke
python3 training-corpus/scripts/evaluate_baseline_holdouts.py --run-id smoke_summary_holdout --out-root /tmp/posttrain-holdout-recording-smoke
find /tmp/posttrain-recording-smoke /tmp/posttrain-holdout-recording-smoke -type f \( -name 'predictions*.jsonl' -o -name 'errors.jsonl' -o -name 'errors_*.jsonl' \) -print
```

Result:

The smoke runs wrote `prediction_samples*.jsonl` and `error_samples*.jsonl`
only. The final `find` command returned no full `predictions*.jsonl` or
`errors*.jsonl` files.

Decision:

Use summary mode for all local repair and baseline work unless the output target
has been explicitly chosen for a full row-level analysis run.

Next:

Continue with data-contract repair using the new recording mode.

## EXP-2026-06-30-009 - Router contract repair v0.1c

Goal:

Repair the router label contract before any learned router or GPU SFT/DPO work.

Why:

The expanded router baseline had high internal metrics but failed realistic
holdouts. It lacked `risk_review` and `clarification_needed`, and real tool
traces were mostly misrouted as `financial_calculation`.

Script:

```text
training-corpus/scripts/build_router_contract_repair_v01.py
```

Canonical repair pack:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c
```

Canonical baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c/baselines/router_contract_repair_probe_v0.1c_20260630T143244Z
```

Canonical holdout eval:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c/baselines/router_contract_repair_probe_v0.1c_20260630T143244Z/holdouts/router_contract_repair_holdout_eval_v0.1c_20260630T143256Z
```

Repair data:

| Split | Rows | clarification_needed | risk_review |
| --- | ---: | ---: | ---: |
| train | 7047 | 173 | 250 |
| dev | 1410 | 31 | 47 |
| test | 1422 | 39 | 53 |

Iteration trail:

| Run | Result | Decision |
| --- | --- | --- |
| v0.1 | real tool trace improved 0.0 -> 0.5, but every real trace became `deep_research` | add real-tool-style evidence/risk boundary rows |
| v0.1b | real tool trace stayed 0.5, overcorrected toward `evidence_check`/`risk_review` | add real-tool-style deep-research positive rows |
| v0.1c | real tool trace reached 1.0 and schema gap disappeared | use as current router checkpoint |

Holdout comparison:

| Holdout | Old expanded acc | v0.1c acc | Old schema gap | v0.1c schema gap |
| --- | ---: | ---: | --- | --- |
| golden_v0.1_router_all | 0.3023 | 0.8895 | yes | no |
| long_research_repair_25_router_all | 0.4800 | 0.9600 | no | no |
| real_tool_trace_pilot_10_router | 0.0000 | 1.0000 | yes | no |

Remaining failure:

Golden social/bookmark rows still expose a boundary where long social claims
asking for evidence verification can be downgraded to `fast_answer`. This should
be a targeted `router_social_boundary_repair_v0.1`, not a reason to start GPU
training yet.

## EXP-2026-06-30-010 - Router social boundary candidate v0.1

Goal:

Reduce the remaining router failure where long X/bookmark market narratives that
ask for evidence verification are downgraded to `fast_answer`.

What changed:

- Added social/bookmark generated boundary rows to
  `build_router_contract_repair_v01.py`.
- Generated `router_social_boundary_repair_v0.1`.
- Ran router-only CPU baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1/baselines/router_social_boundary_probe_v0.1_20260630T143757Z
```

- Ran holdout eval:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1/baselines/router_social_boundary_probe_v0.1_20260630T143757Z/holdouts/router_social_boundary_holdout_eval_v0.1_20260630T143807Z
```

Result:

| Holdout | Router v0.1c acc | Social v0.1 acc |
| --- | ---: | ---: |
| golden_v0.1_router_all | 0.8895 | 0.9012 |
| long_research_repair_25_router_all | 0.9600 | 0.9600 |
| real_tool_trace_pilot_10_router | 1.0000 | 0.9000 |

Decision:

Treat social v0.1 as a candidate/tradeoff repair, not the canonical router
checkpoint. It improves golden social routing and safety recall, but it slightly
regresses real-tool trace routing by classifying a GOOGL capex/source-support
deep-research query as `evidence_check`.

Next:

Move to `risk_contract_repair_v0.1`. Router social repair can be revisited with
forced train anchors for real-tool-style capex/source-support deep research.

## EXP-2026-06-30-011 - Risk contract repair v0.1

Goal:

Add an explicit `medium` risk contract and human-gate semantics before any GPU
fine-tuning.

Data:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/risk_reviewer
```

Commands:

```bash
python3 training-corpus/scripts/build_risk_contract_repair_v01.py

python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1/repaired_datasets \
  --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1/baselines \
  --run-id risk_contract_repair_probe_v0.1_20260630T145518Z \
  --datasets risk_reviewer \
  --record-mode summary

python3 training-corpus/scripts/evaluate_baseline_holdouts.py \
  --baseline-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1/baselines/risk_contract_repair_probe_v0.1_20260630T145518Z \
  --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1/baselines/risk_contract_repair_probe_v0.1_20260630T145518Z/holdouts \
  --run-id risk_contract_holdout_eval_v0.1_20260630T145518Z \
  --record-mode summary
```

Artifacts:

```text
training-corpus/scripts/build_risk_contract_repair_v01.py
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1/baselines/risk_contract_repair_probe_v0.1_20260630T145518Z
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1/baselines/risk_contract_repair_probe_v0.1_20260630T145518Z/holdouts/risk_contract_holdout_eval_v0.1_20260630T145518Z
```

Metrics:

| Eval | Accuracy | Macro F1 | Medium behavior |
| --- | ---: | ---: | --- |
| internal dev | 0.9970 | 0.9622 | 20/20 medium recall |
| internal test | 0.9928 | 0.9073 | 16/16 medium recall |
| golden_v0.1_risk_all | 0.3923 | 0.3349 | 0/69 medium recall |
| long_research_repair_25_risk_all | 0.0000 | 0.0000 | 0/25 medium recall |

Failure:

The repair fixed the schema gap but did not transfer to real medium-risk
long-research phrasing. See `F-2026-06-30-019`.

Decision:

Do not start GPU fine-tuning from this risk checkpoint. Build
`risk_contract_repair_v0.1b` with real long-research medium examples before
treating the risk reviewer as usable.

Next:

Move citation verifier work to schema design while risk repair waits for real
medium examples.

## EXP-2026-06-30-012 - Citation contract design v0.1

Goal:

Separate "candidate evidence" from actual span-level claim support before
training the next citation verifier.

Artifacts:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/schema.json
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/REPORT.md
```

Label contract:

```text
candidate_evidence
verified_support
partial_support
insufficient
contradicts
```

Decision:

No training run yet. First collect real paragraph spans from official/IR/SEC,
press release, transcript, and reputable news sources under this contract.

## EXP-2026-07-01-001 - Real citation paragraph spans v0.1

Goal:

Collect the first real paragraph/list/table-cell citation spans under
`citation_contract_repair_v0.1`, using auditable source URLs instead of
synthetic evidence strings or headline-only spans.

Command:

```bash
python3 -m py_compile training-corpus/scripts/collect_real_citation_spans_v01.py

python3 training-corpus/scripts/collect_real_citation_spans_v01.py \
  --timeout-seconds 30
```

Artifacts:

```text
training-corpus/scripts/collect_real_citation_spans_v01.py
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/real_citation_spans_v0.1
```

Output files:

```text
spans/all.jsonl
repaired_datasets/citation_verifier/train.jsonl
repaired_datasets/citation_verifier/dev.jsonl
repaired_datasets/citation_verifier/test.jsonl
repaired_datasets/citation_verifier/all.jsonl
sources.json
failures.json
manifest.json
REPORT.md
```

Source mix:

| Source | Class | Rows |
| --- | --- | ---: |
| AMD Q1 2026 press release | press_release | 7 |
| AMD May 2026 8-K | sec_filing | 2 |
| Microsoft FY26 Q3 press release | press_release | 7 |
| Micron FY26 Q3 press-release mirror | press_release_wire | 6 |
| NVIDIA FY2027 Q1 News Center release | official_news | 7 |

Label distribution:

| Label | Rows |
| --- | ---: |
| `verified_support` | 15 |
| `partial_support` | 6 |
| `insufficient` | 4 |
| `contradicts` | 4 |

Split distribution:

| Split | Rows |
| --- | ---: |
| train | 16 |
| dev | 7 |
| test | 6 |

Validation:

```text
schema_sanity_ok rows= 29
```

Intermediate errors:

- First run produced only 21 rows because Micron IR timed out and AMD 8-K text
  was inside `div/span` nodes not covered by the first extractor.
- First script version passed `"train"`, `"dev"`, and `"test"` positionally to
  `SpanCase`; because `split` comes after `point_in_time_allowed`, split labels
  were not applied as intended. This was fixed by using explicit `split=...`.
- Micron IR remained unstable under scripted fetch, so the collection uses the
  issuer press-release mirror on GlobeNewswire and records the fallback note in
  provenance.

Decision:

This is the first real-source seed for `citation_verifier_repair_v0.3`, not a
training-ready dataset. Do not start citation GPU fine-tuning from 29 rows.
Next expand to at least 100 audited real spans with more SEC, transcript, and
reputable news paragraphs.

## EXP-2026-07-02-001 - Report and filing spans v0.1

Goal:

Expand real citation spans past the 29-row seed by collecting an auditable
100+ row pack from SEC filings, earnings call transcript pages, public
industry research, and reputable news under `citation_contract_repair_v0.1`,
per `docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md`.

Data:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/report_and_filing_spans_v0.1
```

Command:

```bash
python3 training-corpus/scripts/collect_report_and_filing_spans_v01.py \
  --timeout-seconds 45
```

Artifacts:

```text
spans/all.jsonl
repaired_datasets/citation_verifier/{train,dev,test,all}.jsonl
sources.json
failures.json
sanity_check.json
manifest.json
REPORT.md
```

Metrics:

| Metric | Value |
| --- | ---: |
| Rows | 102 |
| Sources fetched | 22 / 22 |
| Anchor failures (final run) | 0 |
| SEC filing rows (10-K/10-Q/6-K) | 51 |
| Earnings transcript rows | 25 |
| Public research rows | 18 |
| Reputable news rows | 8 |
| `verified_support` | 48 |
| `contradicts` | 26 |
| `partial_support` | 15 |
| `insufficient` | 13 |
| Splits train/dev/test | 46 / 31 / 25 |
| Schema sanity checks | passed |

Sources: NVDA 10-K FY2026 + 10-Q Q1 FY2027, AMD 10-K 2025, MSFT 10-Q FY26Q3,
MU 10-Q FQ3 2026, META 10-K 2025, GOOGL/AMZN 10-Q Q1 2026, AVGO 10-Q FQ2 2026,
TSM 6-K May 2026 revenue, six large-cap transcript pages (NVDA, AMD, MSFT,
GOOGL, AMZN, AVGO), three SIA releases, the Deloitte 2026 semiconductor
outlook, and two AP news articles.

Boundary-trap coverage: sequential-vs-year-over-year misattribution (MU 74%
vs 346%), segment-vs-total figure swaps (NVDA $75B vs $82B; GOOGL 16% vs 63%),
attribution flips (NVDA customer concentration segment), stale-forecast
conflicts across `published_at` dates (Deloitte $975B Feb 2026 vs WSTS $1.5T
June 2026; SIA $1T May vs $1.5T June), and explicit-absence traps (AWS backlog
excluding the Anthropic deal; fab completion timing not specified).

Failures:

- Gartner newsroom returned 403 and an IDC press-release URL guess returned
  404 during scouting; both were excluded instead of scraped around.
- fool.com transcript archive pagination returned the same first page, and
  DuckDuckGo HTML search returned bot-challenge pages; large-cap transcripts
  were located via fool.com monthly sitemaps instead.
- No Micron FQ3 2026 transcript existed in the June/July sitemaps at
  collection time; Micron transcript rows were deferred and Micron is covered
  through its 10-Q.
- First collection run matched the NVDA H20 partial-support case to the risk
  factor duplicate of the H20 paragraph, which lacks the August 2025 license
  and $60 million revenue sentences the label depended on. The anchor was
  re-pointed at the MD&A sentence and the run repeated. See F-2026-07-02-002.

Decision:

Combined with `real_citation_spans_v0.1` (29 rows) this gives 131 real spans
under the five-way contract and meets every minimum in the source plan. It is
the candidate input for `citation_verifier_repair_v0.3`, but every row is
marked `requires_human_audit`; run the label audit pass and a CPU probe under
summary recording before any training run.

Next:

1. Audit labels for all 131 rows (29 seed + 102 new).
2. Run a citation CPU probe on the combined audited pack.
3. If probe quality holds, define `citation_verifier_repair_v0.3`; GPU work
   stays blocked until then.

## EXP-2026-07-02-002 - Blind double-annotation audit of 131 citation rows

Goal:

Block A1 of the three-task ladder: audit every real citation span row (29
seed + 102 report/filing) and freeze `citation_real_eval_v1` before any LLM
arm is measured on it.

Data:

```text
real_citation_spans_v0.1 (29 rows) + report_and_filing_spans_v0.1 (102 rows)
```

Method:

Blind double annotation + adjudication, all AI: 4 shuffled batches x 2
independent auditor agents per batch, labels hidden; 5 disputed rows
adjudicated in the main session against the five-way contract.

Command:

```bash
python3 training-corpus/scripts/build_citation_real_eval_v1.py \
  --audit-dir <scratchpad audit dir with votes_passA/B.jsonl, adjudications.json>
```

Artifacts:

```text
.../citation_contract_repair_v0.1/citation_real_eval_v1/
  rows/{train,dev,test,all}.jsonl
  audit/{votes_passA.jsonl,votes_passB.jsonl,adjudications.json}
  AUDIT_REPORT.md
  manifest.json
```

Metrics:

| Metric | Value |
| --- | ---: |
| Rows audited | 131 |
| Double-confirmed directly | 126 |
| Adjudicated | 5 |
| Labels corrected | 3 (2.3%) |
| Test-split corrections | 0 |
| Final labels V/P/I/C | 62 / 21 / 16 / 32 |
| Splits train/dev/test | 62 / 38 / 31 |

Corrections: seed `amd_guidance_partial` partial->contradicts (conflicted
margin subclaim); new `msft10q_rev_verified` verified->partial (period
binding unverifiable in multi-period 10-Q); new `siaq1_trillion_insufficient`
insufficient->contradicts (materially-weakens). Two of the three overrode
labels authored in this same session - the blind protocol worked as intended.

Failures:

- One auditor omitted one row from its output (31/32); resolved by the other
  auditor plus adjudication. See F-2026-07-02-003 for the label-convention
  gaps the audit exposed.

Decision:

`citation_real_eval_v1` is frozen: dev+test are the Act 2 evaluation splits;
test is untouchable; prompts/experience libraries iterate on train/dev only.
Conventions C1 (contradiction precedence), C2 (period binding), C3
(materially weakens) are now part of the citation contract and bind future
collection passes.

Next:

Block A2: `risk_contract_repair_v0.1b` from real long-research medium rows.
Then Block B prompted-LLM eval arms.
