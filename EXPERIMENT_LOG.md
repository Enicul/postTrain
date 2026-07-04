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

## EXP-2026-07-02-003 - Risk contract repair v0.1b with audited real eval

Goal:

Block A2: repair the risk ruler (fractured semantics, degenerate 25-row
all-medium holdout) and the v0.1 medium-transfer failure in one pass.

Data:

256 real rows normalized from three families: golden_v0.1 risk (181),
long_research_repair_25 (25), user_simulation_trace_pilot_50 (50).
Train adds 166 real rows to v0.1's 8,229 synthetic rows.

Method:

Blind double annotation of all 90 eval rows (labels hidden; golden syn rows
re-audited after a normalizer bug first rendered them empty), adjudication,
conventions R1-R5 pinned, train synced via provenance-mechanical rules.

Commands:

```bash
python3 training-corpus/scripts/build_risk_contract_repair_v01b.py --audit-dir <audit dir>
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir .../repairs/risk_contract_repair_v0.1b/repaired_datasets \
  --out-root .../repairs/risk_contract_repair_v0.1b/baselines \
  --run-id risk_contract_repair_probe_v0.1b_20260702T031246Z \
  --datasets risk_reviewer
```

Metrics:

| Item | Value |
| --- | ---: |
| Eval rows audited | 90 |
| Double-confirmed | 73 |
| Corrected | 17 (18.9%) |
| Gold kept against 2/2 auditors (R3) | 2 |
| Train rows rule-synced | 51 |
| Probe dev acc / macro F1 | 0.8421 / 0.7764 |
| Probe test acc / macro F1 | 0.8269 / 0.7537 |
| Medium recall dev / test | 1.00 / 1.00 (v0.1: 0.0) |
| High (gated) recall dev / test | 0.64 / 0.73 |
| Majority accuracy | 0.42 |

Failures:

- Normalizer family-dispatch bug rendered 47 golden syn eval rows empty in
  the first audit round; caught by auditors' "empty row" notes (F-2026-07-02-004).
- v0.1's synthetic labels violated v0.1's own documented boundary on
  missing_bear_case rows (F-2026-07-02-005).
- v0.1's 0.0 on long-research medium was partly a featurization gap
  (memo.* fields never featurized), not pure distribution shift.

Decision:

Medium transfer is repaired (0.0 -> 1.00 recall on audited real rows). The
sklearn rung is NOT a safe gate: high/gate recall 0.64-0.73, missing Chinese
red-line templates and R3 evidence red lines - that measured gap is exactly
what the ladder's rules/prompt arms must close (Act 1 kill criterion: gate
recall >= 0.99). `risk_real_eval_v1` (90 rows, high 33 / medium 48 / low 9)
is the frozen Act 1 ruler.

Next:

Block B: rules arm + naive/engineered prompt arms on the two frozen rulers
(risk_real_eval_v1, citation_real_eval_v1) plus the router holdouts.

## EXP-2026-07-02-004 - Block B: rules and prompt arms on the frozen rulers

Goal:

Fill the ladder's rungs 0/2/3 on both frozen audited rulers using Claude
subagents (claude-haiku-4-5, claude-sonnet-5) as the LLM arms, plus
deterministic rules arms, with per-arm token cost proxies.

Artifacts:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/blockb_eval_arms_v0.1
```

Metrics (see REPORT.md for full tables):

Risk (90 rows, 45 gated): rules 0.811 acc / 0.733 gate recall; naive haiku
0.667/0.867; naive sonnet 0.733/1.000; prompted haiku 0.800/1.000; prompted
sonnet 0.811/1.000. Citation (69 rows, anonymized ids): rules 0.449; naive
haiku 0.826; naive sonnet 0.870; prompted haiku 0.957; prompted sonnet 0.899.

Failures:

- Citation sample_ids leaked authored labels via case-key suffixes; caught
  when one arm's transcript admitted using them; all citation arms re-run
  with anonymized ids; measured inflation +11.6 points on the preserved
  leaked arm (F-2026-07-02-006).
- naive sonnet dropped 2 citation rows (counted as errors).

Decision:

- Act 2 (citation) is KILLED at rung 3: an engineered contract prompt takes
  the SMALL model to 0.957 (>= the 0.85 rung-4 bar). No experience library,
  no weights, at frontier-family scale. Small local verifier deferred as a
  separate decision.
- Act 1 (risk) is NOT killed: gate recall 1.000 on every engineered arm (the
  safety half passes) but best accuracy 0.811 < 0.90. The ~zero-cost regex
  rules arm ties prompted sonnet on accuracy; rung 4 candidate is a
  rules-for-gate + LLM-for-level hybrid / experience library aimed at the
  low/medium boundary.
- The acts reassigned themselves by measurement - the ladder is doing its
  job. Act 3 (escalation router) remains the weights candidate.

Next:

Block C/D for risk (learning-pool rollouts -> experience library / hybrid
arm), Act 3 escalation environment construction, then the kill-criteria
checkpoint before any weights.

## EXP-2026-07-02-005 - Rung 4 risk hybrid: Act 1 killed without training

Goal:

Close Act 1's accuracy gap (0.811 -> >=0.90) while holding gate recall
>= 0.99, using a training-free rung: rules gate + prompted LLM + experience
library.

Method:

Opus extracted 5 contrastive lessons from DEV-split errors only
(risk_explib_v1); hybrid arms (haiku, sonnet) re-ran the frozen 90-row eval
with anonymized ids; gate = LLM UNION deterministic rules v1.1.

Artifacts:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/rung4_risk_hybrid_v0.1
training-corpus/scripts/risk_gate_rules_v11.py
```

Metrics:

| Arm | Acc | Acc conf-only | Gate recall | Gate FP | Kill |
| --- | ---: | ---: | ---: | ---: | --- |
| hybrid haiku | 0.900 | 0.890 | 1.000 | 0 | MET |
| hybrid sonnet | 0.978 | 0.973 | 1.000 | 0 | MET |

Failures:

- The explib alone regressed gate recall 1.000 -> 0.956 (both lost gates =
  the two R3 adjudication rows); caught by the kill-criteria check, escalated
  to the owner, resolved by policy decision A (defense-in-depth) implemented
  as code-level gate rules. See F-2026-07-02-007.

Decision:

Act 1 KILLED at rung 4. Two of three acts now closed without weights; Act 3
(cost-aware escalation router) is the sole training candidate. See
D-2026-07-02-006.

Next:

Act 3 environment: cost table from real traces, cheap-path outcome table
(Block C K=8 rollouts), argmax-SFT collapse baseline, lambda sweep - then
Block E within the budget cap.

## EXP-2026-07-02-006 - Escalation environment v0.1 built (Act 3 / Block C)

Goal:

Construct the offline environment for the sole surviving training candidate:
cost table from real traces, stochastic cheap-path outcome table, simulator
with reward + analytic oracle.

Artifacts:

```text
.../kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1/
training-corpus/scripts/escalation_env_v01.py
```

Method / metrics:

- 256 seeds (160/48/48) stratified over 8 routes from router v0.1c; 64
  gate-required.
- Cost units from real_tool_trace_pilot_10: cheap 0.128 / deep 1.0 / gate
  0.15 (median tool-call latency 0.36s, 3 calls/trace).
- p_cheap_success: 12 blind haiku judgments (3 framings x 4 batches,
  anonymized ids), 256/256 complete; 74 seeds in the stochastic middle;
  route-level sanity holds (fast/price 1.0 ... deep/evcheck 0.0).
- Analytic oracle (pre-training math): for lambda < 1 the strategy mix is
  lambda-invariant; deep beats cheap-first iff p < 0.128. Oracle mix
  70/58/64/64, mean expected reward 0.955/0.865/0.730 at lambda 0.1/0.3/0.6.

Failures:

- 6 of 12 outcome agents wrote files instead of returning JSONL; recovered
  from their output files (format drift, no data loss).
- Lambda sweep insight doubles as a design correction: the planned
  "Pareto front over lambda" collapses analytically below lambda=1; the
  deliverable reframes to "policy quality at inferring p/gate from text",
  which is the honest learnable quantity.

Decision:

Environment frozen as v0.1 with fidelity limits documented (model-derived p,
always-adequate deep path, small cost sample). Next: rules/prompt arms on
the env, argmax-SFT oracle-label baseline, then GRPO under the budget cap.

## EXP-2026-07-02-007 - Act 3 env arms: engineered prompt matches the oracle (provisional)

Goal:

Run rungs 0/2/3 (rules / naive / engineered prompt) on escalation_env_v0.1
before argmax-SFT and GRPO, to see whether prompting already reaches the
analytic reward ceiling.

Method:

Contingent policies (first + on_fail) scored by exact expected reward; oracle
= argmax pure strategy on the true p. Subagent arms (haiku/sonnet).

Metrics:

Full 256: rules reward 0.760/0.654/0.494 (gate 0.625), naive_sonnet
0.666/0.577/0.443 (gate 0.672), ORACLE 0.955/0.865/0.730 (gate 1.0) at
lambda 0.1/0.3/0.6.
Batch-1 subset (64, engineered available): engineered_sonnet
0.954/0.862/0.725 gate 1.0 = ORACLE exactly, at all three lambdas.

Failures / limits:

- SPEND LIMIT hit mid fan-out: engineered coverage is 64/256; haiku arms and
  engineered batches 2-4 did not return. Full engineered sweep deferred.
  Recorded as F-2026-07-02-008.
- "engineered = oracle" is under the v0.1 simulator (model-derived p, shared
  model family) - a fidelity caveat, not a reality claim.

Decision (provisional):

The engineered prompt reaches the analytic reward ceiling on the observed
seeds, so GRPO has no room to beat it under the pre-registered kill criterion.
On available evidence Act 3 is also resolved at rung 3 -> the ladder closes
with ZERO GPU training. Flagged PROVISIONAL pending the full 256-seed
engineered sweep. The argmax-SFT collapse baseline and GRPO remain buildable
if the ceiling match breaks on the unseen 192 seeds.

Next:

Next spend cycle: complete the engineered sweep (haiku + sonnet, batches
2-4). Either it confirms the three-act "prompting suffices" close, or it
re-opens the weights question with a concrete target.

## EXP-2026-07-02-008 - RL Phase 2 scaffolding (A/B/C), non-GPU parts

Goal:

Lay every non-GPU piece of the A/B/C small-model RL plan so the GPU segments
are pull-and-run and the negative/positive results are pre-wired.

Artifacts:

```text
docs/RL_PHASE2_SMALL_MODEL_PLAN.md
training-corpus/scripts/rl/{reward_escalation,build_sft_labels,sft_escalation,
  grpo_escalation,eval_escalation_policy,citation_agentic_env,training_free_grpo}.py
training-corpus/scripts/rl/{requirements-rl.txt,README.md}
training-corpus/scripts/expand_env_seeds.py
.../ladder/escalation_env_v0.1/{env_seeds_v0.2.json,outcome_table_v0.2.json}
```

What works (CPU-verified):

- Plan A reward wrapper reuses the frozen env; oracle-as-predfile reproduces
  the env reward exactly (test: 0.956/0.868/0.737, gate 1.0) - the eval
  harness is trustworthy.
- Oracle SFT labels generate cleanly (160 train rows, 4-way action mix
  44/36/40/40); GRPO/SFT trainers compile and are documented pull-and-run.
- A0 seed expansion: 256 -> 1,120 (1,024 train) from the router pool; new
  train seeds use a route-mean p proxy with MAE 0.064 vs the ensemble p on
  the 256 (eval-256 keeps ensemble p; fidelity gap logged).
- Plan B citation agentic env: 131 claims / 86-span pool; perfect play +1.5,
  fabricated citation -1.0 (hallucination hard negative fires).
- Plan C training-free GRPO loop: iterative rollout -> semantic advantage ->
  no-regression lesson gate -> dry-round stop; self-test learns round 1,
  stops round 2.

Decision:

Non-GPU scaffolding for all three plans is done and smoke-verified. Remaining
work is exactly: (1) Act-3 full sweep + Plan A A1 motivation measurement +
A2/A3 training on the user's A100; (2) Plan B corpus growth to 300-500 rows
then its GRPO; (3) Plan C run with an inference backend. Every GPU step has a
pre-registered kill criterion.

Next:

User pulls training-corpus/scripts/rl to an A100 and runs the README chain
(A1 -> A2 -> A3). B/C run when their inference backends are available.

## EXP-2026-07-02-009 - Act 3 engineered sweep on v0.3 (full 256, corrected labels)

Goal:

Re-run the frontier engineered sweep on the R4-gate-corrected env (v0.3),
full 256 coverage, to firm the Act-3 kill and quantify cheaper-model
degradation as RL Phase 2 motivation.

Metrics (full 256):

| lambda | oracle | sonnet | gap | haiku | gap | haiku gate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.1 | 0.9470 | 0.9448 (gate 1.0) | +0.002 | 0.8203 | +0.127 | 0.80 |
| 0.3 | 0.8410 | 0.8344 (gate 1.0) | +0.007 | 0.7147 | +0.126 | 0.80 |
| 0.6 | 0.6819 | 0.6688 (gate 1.0) | +0.013 | 0.5563 | +0.126 | 0.80 |

Findings:

- Act 3 frontier kill CONFIRMED (was provisional): sonnet within 0.2-1.3% of
  oracle with gate recall 1.000 on full 256 corrected seeds; GRPO cannot beat
  a ceiling-matching, perfectly-gating prompt at frontier scale.
- Cheaper-model signal (RL Phase 2 motivation): identical prompt on haiku
  loses 12.6 reward points and drops gate recall to 0.80 (misses 20% of
  required gates). Capability down -> prompted policy worse AND unsafe.

Artifacts:

```text
.../ladder/act3_env_arms_v0.3/  (preds + scores + REPORT.md)
```

Decision:

Act 3 closes at rung 3 for the frontier scale (confirmed). The small-model
column (A1/A2/A3) is now motivated by concrete evidence - a cheaper model
prompted alone is unsafe on the gate. A1 with real Qwen models runs next on
the GPU box; SFT/GRPO proceed only if A1 confirms small models fail the
motivation gate. Gate floor stays in code as the safety backstop.

Next:

GPU box: A1 prompted Qwen-0.5B/1.5B/3B/7B on env v0.3 -> motivation gate;
then A2/A3 per RL_PHASE2 plan. All three acts now resolved at frontier scale
without training; RL Phase 2 targets the cost-constrained small-model regime.

## EXP-2026-07-03-001 - A1 prompted small-model motivation gate (Qwen2.5 0.5B/1.5B/3B/7B, env v0.3)

Goal:

First real-GPU step of RL Phase 2. Measure prompted (no-training) Qwen2.5 base
models on escalation env v0.3 test split to decide whether small-model training
is motivated at all. Pre-registered KILL: if any prompted model lands within 3
reward points of the oracle AND holds gate recall >= 0.99 at lambda=0.3, small
models already solve the task prompted and training is unnecessary.

Data:

env v0.3 test split, n=48 (8 gate-required seeds). Greedy, temp-0, seed 0.
Oracle test reward at lambda=0.3 = 0.8473. Base commit e571324. Single A100
80GB, GPU 0.

Command:

```text
runs/gpu_session_20260703/run_a1.sh  (eval_escalation_policy.py per model, prompted)
```

Metrics (test @lambda=0.3):

| model | reward | vs oracle | success | gate_recall |
| --- | ---: | ---: | ---: | ---: |
| Qwen2.5-0.5B | 0.3063 | -0.541 | 0.517 | 0.50 |
| Qwen2.5-1.5B | 0.6444 | -0.203 | 1.000 | 0.50 |
| Qwen2.5-3B  | 0.4232 | -0.424 | 0.958 | 0.00 |
| Qwen2.5-7B  | 0.7447 | -0.103 | 1.000 | 0.75 |

Findings:

- KILL CHECK: NO model passes (none within 3 pts of oracle with gate >= 0.99).
  Training is MOTIVATED.
- Key insight: success rates are already fine (1.5B and 7B = 1.000). What small
  models lack is GATE DISCIPLINE - even the 7B only recalls 0.75 of required
  gates, and the 3B recalls 0.00. The bottleneck is the safety action, not
  task competence.
- Non-monotone in size (3B gate 0.00 < 1.5B gate 0.50) - prompted gate behavior
  is not a smooth function of capacity, reinforcing that it is a discipline
  problem a prompt does not reliably induce.

Artifacts:

```text
runs/a1_prompted/{qwen05,qwen15,qwen3,qwen7}_test_eval.json
runs/a1_prompted/a1_manifest.json  (git_sha, gpu, split, seed)
runs/a1_prompted/a1_batch.log
runs/gpu_session_20260703/run_a1.sh
```

Decision:

A1 confirms the motivation gate: small prompted models are cheaper but unsafe on
the gate, exactly the regime RL Phase 2 targets. Proceed to A2 (argmax-SFT) on
0.5B and 1.5B - the two arms where a compact trained policy is the interesting
question (0.5B = hardest capacity, 1.5B = the "beat prompted 7B" target).

Next:

A2 argmax-SFT from oracle labels, then A3 GRPO from the SFT adapters.

## EXP-2026-07-03-002 - A2 argmax-SFT (LoRA) on 0.5B and 1.5B (env v0.3)

Goal:

Supervised behavior-clone the oracle's argmax action onto small models and test
whether SFT alone closes the A1 gap - both reward and gate discipline.

Data:

160 env v0.3 train labels (oracle argmax action). LoRA, 3 epochs. Init from
Qwen2.5-0.5B-Instruct and -1.5B-Instruct. Test split n=48, greedy temp-0, seed 0,
lambda=0.3. Base commit e571324.

Command:

```text
runs/gpu_session_20260703/run_a2.sh
runs/gpu_session_20260703/sft_train.jsonl  (the 160 labels)
sft_escalation.py --model <qwen> --out-dir runs/sft_qwen{05,15} (processing_class API)
```

Metrics (test @lambda=0.3):

| model | SFT reward | vs A1 prompted | gate_recall | success | final_loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.5B | 0.6061 | +0.300 | 0.50 (unchanged) | 0.951 | 1.183 |
| 1.5B | 0.7495 | +0.105 | 0.875 (up from 0.50) | 0.927 | 1.236 |

Findings:

- HEADLINE: the trained 1.5B (0.7495) beats the PROMPTED 7B (0.7447) - a 4.7x
  smaller model, post-trained, edges out a frontier-of-family prompt. This is
  the core "small + trained > large + prompted" result.
- 0.5B gains +30 reward points but its gate recall does NOT move (still 0.50) -
  SFT buys the 0.5B cost/success behavior but not gate discipline at that
  capacity. 1.5B gate recall lifts 0.50 -> 0.875 (7/8), the biggest safety win
  of the day.
- Both within striking distance of oracle 0.8473: 1.5B is -0.098, and it does
  it while cutting cost (0.4531 vs prompted-7B 0.5731).

Artifacts:

```text
runs/sft_qwen05/20260703T1505Z-e571324/{sft_test_eval.json,metrics.json,
  trainer_log.jsonl,run_manifest.json}
runs/sft_qwen15/20260703T1506Z-e571324/{same}
(failed first-launch dirs preserved: sft_qwen05/20260703T1504Z-e571324/,
 sft_qwen15/20260703T1504Z-e571324/ - manifest-only, see F-2026-07-03-001/002)
```

Decision:

SFT is the clear win of the session and is promotable on the 1.5B arm as the
cost-efficient policy. Adapters carry into A3 as the GRPO init. Open question
A3 must answer: can RL push past SFT and, crucially, close the residual gate
gap (1.5B still misses 1/8; 0.5B still at 0.50)?

Next:

A3 GRPO (K=8, lambda=0.3) initialized from these SFT adapters.

## EXP-2026-07-03-003 - A3 GRPO from SFT adapters, 0.5B and 1.5B (env v0.3)

Goal:

Reinforcement-optimize the SFT policies with GRPO under the cost-shaped reward
(lambda=0.3) and test the pre-registered PROMOTION bar: beat SFT by >= 3 reward
points AND hold gate recall >= 0.99 at lambda=0.3.

Data:

TRL 0.15.2 GRPOTrainer, K=8 (num_generations), 400 steps, lambda=0.3, save-steps
50, init from the A2 SFT adapters. Test split n=48, greedy temp-0, seed 0. Base
commit e571324.

Command:

```text
runs/gpu_session_20260703/run_a3.sh
grpo_escalation.py --model <qwen> --init-adapter <sft_adapter> --lambda 0.3 \
  --num-generations 8 --max-steps 400 --save-steps 50 --out-dir runs/grpo_qwen{05,15}
```

Metrics (test @lambda=0.3):

| model | GRPO reward | delta vs SFT | gate_recall | cost | kill-check |
| --- | ---: | ---: | ---: | ---: | --- |
| 0.5B | 0.383  | -0.223 | 0.00 | 0.9455 | FAIL (collapse) |
| 1.5B | 0.7981 | +0.049 | 0.875 | 0.534  | FALSE (gate < 0.99) |

Findings:

- 0.5B: POLICY COLLAPSE. Degenerated to near-always-deep (cost ~= deep 1.0,
  success 1.0, gate action extinct). Reward fell 22.3 pts below SFT and gate
  recall dropped to 0.00. Training KL drifted to ~2.0 throughout; reward_trace
  action_mix shows gate -> 0 in late batches (batch 371: gate_violation_rate
  1.0, mean_reward -1.51). Full failure diagnosis + mechanism hypothesis in
  F-2026-07-03-003 (the interview-grade one - early warning was visible in
  reward_trace before eval confirmed).
- 1.5B: HEALTHY training. Reward +4.86 pts over SFT (0.7981, within 4.9 pts of
  oracle 0.8473), KL stayed ~0.3, gate action alive in action_mix. BUT gate
  recall is 0.875 - the SAME single missed gate (7/8) as SFT; GRPO improved cost
  optimization without fixing that residual seed. So kill-check is FALSE
  (reward bar met, gate bar not).
- The reward gains from GRPO at 1.5B are REAL. The hard safety constraint is
  NOT met by pure RL at either scale.

Artifacts:

```text
runs/grpo_qwen05/20260703T1507Z-e571324/{grpo_test_eval.json,generations.jsonl
  (5936+ rollouts),reward_trace.jsonl,trainer_log.jsonl,metrics.json,run_manifest.json}
runs/grpo_qwen15/20260703T1520Z-e571324/{same}
```

Decision (pre-registered verdict, recorded honestly):

"GRPO does not meet the promotion bar at these scales." The reward gain at 1.5B
is real (+4.9, within 4.9 of oracle) but pure RL leaves the hard gate constraint
unmet (0.875 < 0.99) and collapses the gate entirely at 0.5B. Product/architecture
takeaway: the safety floor stays in versioned code (risk_gate_rules_v11; the
Act-1 hybrid already demonstrated rules+model gate recall 1.000). RL optimizes
cost ABOVE the floor; it never carries the floor alone. Recorded as
D-2026-07-03-003.

Next:

Pre-registered (not yet committed to run): gate-seed oversampling in GRPO
batches, larger K, exploration bonus on the gate action, or accept the hybrid as
the product answer. See D-2026-07-03-003. Also queued: failure-trajectory
taxonomy from grpo_qwen05 generations.jsonl, and identify the 1-missed-gate seed
at 1.5B.

## EXP-2026-07-04-001 - Night 1: GRPO-v2 oversample fix (1.5B), DPO (1.5B), 0.5B collapse-prevention ablation (env v0.3)

Goal:

Three follow-ups to the A3 GRPO verdict, all initialized from yesterday's SFT
adapters, all on escalation env v0.3 (test n=48, 8 gate seeds, greedy temp-0,
seed 0, lambda=0.3, oracle 0.8473):

- R1: does gate-seed oversampling (x4) - the pre-registered fix from
  D-2026-07-03-003 - close the residual 1/8 gate miss at 1.5B?
- R2: a DPO arm at 1.5B (beta=0.1) to complete an SFT/DPO/GRPO three-way table
  on one ruler.
- R4: does oversample x4 + a stronger KL beta (0.2) prevent the 0.5B collapse?

Data:

Base commit e571324, TRL 0.15.2, K=8, 400 GRPO steps (R1/R4), DPO 60 steps
(R2, 3 epochs over 160 preference pairs). Init adapters: 1.5B from
`runs/sft_qwen15/20260703T1506Z-e571324/adapter`, 0.5B from
`runs/sft_qwen05/20260703T1505Z-e571324/adapter`.

Command:

```text
runs/gpu_session_20260703/run_night.sh
grpo_escalation.py --gate-oversample 4 ...            (R1 1.5B, R4 0.5B +--kl-beta 0.2)
dpo_escalation.py  --beta 0.1 ...                     (R2 1.5B)
```

Metrics (test @lambda=0.3):

| arm | reward | delta vs SFT | gate_recall | cost | success | kill-check |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| R1 GRPO-v2 1.5B (oversample x4) | 0.7997 | +0.0502 | 0.875 | 0.5287 | 1.00 | FALSE (gate<0.99) |
| R2 DPO 1.5B (beta 0.1)          | 0.5382 | -0.2113 | 1.000 | 0.139  | 0.58 | FALSE (reward<bar) |
| R4 GRPO-v2 0.5B (osx4+klbeta.2) | 0.383  | -0.2231 | 0.00  | 0.9455 | 1.00 | FAIL (collapse)    |

Findings:

- R1 (oversample fix, 1.5B) is a NULL RESULT. Reward is digit-identical to
  yesterday's plain GRPO (0.7997) and gate recall is still 0.875 - the SAME
  single missed seed. The reason is diagnostic, not a tuning miss: the collapse
  taxonomy (docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md) already showed the 1.5B had
  ZERO all-violate groups, so the oversampling fix targeted a 0.5B disease the
  1.5B patient never had. The missed seed, identified from
  `test_preds.jsonl`, is `router_contract_realtool_risk_review_AMD_00`: the
  model emits `{"first":"cheap","on_fail":"escalate"}` (cheap-then-escalate)
  where the oracle wants `gate` (escalate immediately). Policy says
  cheap -> escalate for this row across SFT / v1 / v2 - a genuine semantic
  boundary case, queued for human review (see DECISIONS D-2026-07-04-003).
- R2 (DPO) is the MIRROR-IMAGE of GRPO. It nailed the safety constraint (gate
  recall 1.000, the day's only perfect-gate learned policy besides 3B) but
  COLLAPSED exploration: success fell to 0.58, cost to 0.139, deep/escalate went
  near-zero. Mechanism: for cheap seeds the rejected action in the pair is often
  `cheap_then_escalate`, so DPO literally trains "never escalate" (pair sample:
  chosen `{"first":"cheap","on_fail":"finish"}` vs rejected
  `{"first":"cheap","on_fail":"escalate"}`). Pref-acc 0.8625, final loss 0.4346.
  So the three-way table on one ruler now reads: SFT = balanced (0.7495 / gate
  0.875), GRPO = reward-optimal / gate-imperfect (0.7997 / 0.875), DPO =
  gate-perfect / reward-collapsed (0.5382 / 1.000). See F-2026-07-04-004 for the
  pair-design artifact.
- R4 (0.5B collapse-prevention) trained fully (400 steps) but did NOT fix the
  decoded policy. KL spiked to 37.1 at step 10 (then settled ~0.7). The
  training-time SAMPLES kept the gate action alive - late reward_trace batches
  show up to 11/16 gate with gate_violation_rate as low as 0.0 - yet the GREEDY
  eval collapsed to the same always-deep attractor: 0.383 / gate 0.00 / cost
  0.9455, DIGIT-IDENTICAL to yesterday's v1 collapse. This is a distinct
  observation worth recording: a SAMPLING-vs-GREEDY split, where the sampled
  policy explores the gate but the argmax-decoded policy does not. Verdict:
  capacity floor at 0.5B - the mitigations changed training DYNAMICS but not the
  DECODED policy. See F-2026-07-04-002.

Artifacts:

```text
runs/grpo_v2_qwen15/20260703T1551Z-e571324/{grpo_v2_test_eval.json,test_preds.jsonl,
  generations.jsonl,reward_trace.jsonl,trainer_log.jsonl,metrics.json,run_manifest.json}
runs/dpo_qwen15/20260703T1607Z-e571324/{dpo_test_eval.json,test_preds.jsonl,
  trainer_log.jsonl,metrics.json,run_manifest.json}
runs/dpo_qwen15_pairs.jsonl   (160 preference pairs)
runs/grpo_v2_qwen05/20260703T1608Z-e571324/{grpo_v2_test_eval.json,generations.jsonl,
  reward_trace.jsonl,trainer_log.jsonl,metrics.json,run_manifest.json}
  (parent-run 20260703T1507Z-e571324, the v1 0.5B collapse)
```

Decision:

The oversample fix is confirmed size-specific (works on the disease's actual
host, 0.5B, in training samples; irrelevant at 1.5B). DPO and GRPO bracket the
tradeoff: neither pure-preference nor pure-RL carries BOTH reward and the hard
gate. The AMD_00 seed is escalated to human review before any label change
(D-2026-07-04-003), and the DPO pair set gets a v2 that includes
failed-to-escalate negatives (D-2026-07-04-004).

Next:

Night 2 scale sweep (does more capacity, not more RL, solve the gate?) and
Night 3 citation env first-training. DPO pair v2 and 0.5B temperature-sweep probe
queued in TODO.

## EXP-2026-07-04-002 - Night 2: scale sweep 0.5B/1.5B/3B/7B (SFT then GRPO-v2), env v0.3

Goal:

Ask the capacity question directly: with the SAME recipe (LoRA SFT on 160 oracle
labels, then GRPO-v2 oversample x4 from those adapters), how do reward and gate
discipline move as the base model scales 0.5B -> 1.5B -> 3B -> 7B? Yesterday
covered 0.5B/1.5B; this adds 3B and 7B and reads the whole curve.

Data:

env v0.3, test n=48, greedy temp-0, seed 0, lambda=0.3, oracle 0.8473. Base
commit e571324. 7B GRPO ran with per-device batch 8, gradient-accumulation 2 to
fit. Pre-registered promotion bar unchanged (>= +3 reward over SFT AND gate
recall >= 0.99).

Command:

```text
runs/gpu_session_20260703/run_night2.sh
sft_escalation.py  --model Qwen/Qwen2.5-{3B,7B}-Instruct ...
grpo_escalation.py --gate-oversample 4 --init-adapter <that SFT> ...
```

Metrics (test @lambda=0.3):

| model | SFT reward | SFT gate | GRPO-v2 reward | GRPO-v2 gate | delta | kill-check |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0.5B | 0.6061 | 0.50  | 0.383 (collapse) | 0.00  | -0.223 | FAIL   |
| 1.5B | 0.7495 | 0.875 | 0.7997           | 0.875 | +0.050 | FALSE  |
| 3B   | 0.8428 | 1.000 | 0.8473           | 1.000 | +0.0045| FALSE  |
| 7B   | 0.7147 | 0.75  | 0.7997           | 0.875 | +0.085 | FALSE  |

(0.5B/1.5B SFT rows carried from EXP-2026-07-03-002 for the full curve.)

Findings:

- HEADLINE SCALE CURVE (reward / gate_recall @lambda=0.3): 0.5B 0.606/0.50
  (SFT best; GRPO collapses) -> 1.5B 0.800/0.875 -> 3B 0.8473/1.000 (the ORACLE,
  the ONLY size to hit perfect reward AND perfect gate) -> 7B 0.800/0.875.
  Non-monotonic in BOTH directions: 3B is the sweet spot; both smaller and
  larger models fall short of it.
- 3B SFT alone reaches 0.8428 / gate 1.000 (from a prompted 3B of 0.423 / gate
  0.00). 3B GRPO-v2 reaches 0.8473 = EXACTLY the analytic oracle to 4 decimals.
  The kill-check is FALSE by design: GRPO beats SFT by only +0.0045 (< +3), so
  the pre-registered criterion fires as "SFT SUFFICES AT 3B" - the RL step buys
  nothing because SFT already sits on the oracle. This is the pre-registered bar
  working exactly as intended (record a null RL result honestly rather than
  claim a 0.004-point "win").
- 7B is NON-MONOTONIC DOWN: 7B SFT (0.7147 / gate 0.75) is WORSE than both 3B
  SFT and 1.5B SFT. Hypothesis: a 160-row LoRA cannot move 7B's stronger priors
  (or the shared lr is mismatched for 7B) - too little data to steer the larger
  model. 7B GRPO-v2 recovers +8.5 pts to 0.7997 and lifts gate 0.75 -> 0.875,
  but still lands where 1.5B already was.
- So gate discipline EMERGES 1.5B -> 3B under SFT (0.875 -> 1.000) and then
  DEGRADES again at 7B under the same tiny-data SFT (back to 0.75). Capacity
  helps until the data is too thin to move the priors.

Artifacts:

```text
runs/sft_qwen3/20260703T1623Z-e571324/{sft_test_eval.json,test_preds.jsonl,
  trainer_log.jsonl,metrics.json,run_manifest.json}
runs/grpo_v2_qwen3/20260703T1624Z-e571324/{grpo_v2_test_eval.json,generations.jsonl,
  reward_trace.jsonl,trainer_log.jsonl,metrics.json,run_manifest.json}
runs/sft_qwen7/20260703T1646Z-e571324/{sft_test_eval.json,test_preds.jsonl,...}
runs/grpo_v2_qwen7/20260703T1648Z-e571324/{grpo_v2_test_eval.json,...}
```

Decision:

3B is the sweet-spot size and "SFT suffices at 3B" is recorded via the
pre-registered bar (D-2026-07-04-001). The 7B non-monotonic dip is a tiny-data
LoRA / lr result, not evidence that 7B is worse in principle - flagged as an
open item, not promoted.

Next:

Cross-family confirmation (Gemma 4 arm, needs HF license acceptance) to test
whether the 3B sweet-spot and the non-monotonic 7B dip are Qwen-specific or
general. See TODO.

## EXP-2026-07-04-003 - Night 3: citation env first training run (1.5B, eval_dir citation_real_eval_v1)

Goal:

First-ever training on the citation agentic env (the second rung of the
three-task ladder, Plan B). Can GRPO teach a 1.5B to (a) stop fabricating
citations and (b) cite the gold evidence, under a reward of citation validity +
verdict correctness with a hallucinated-citation hard negative? Pre-registered
bar: fabricated_rate == 0 AND verdict reward improves by >= +5.

Data:

eval_dir `citation_real_eval_v1` (the frozen, blind-double-annotated real span
ruler; test n=31). 1.5B base, GRPO ~200 steps, base commit e571324. Prompted
baseline measured first as the control.

Command:

```text
runs/gpu_session_20260703/run_night3.sh
grpo_citation.py --eval-dir <citation_real_eval_v1> --model Qwen2.5-1.5B ...
  (the required --eval-dir was omitted by the earlier run_night.sh -> crash;
   fixed in run_night3.sh, see F-2026-07-04-001)
```

Metrics (test n=31):

| arm | verdict_acc | cite_gold_rate | cite_valid_rate | fabricated_rate | mean_reward |
| --- | ---: | ---: | ---: | ---: | ---: |
| prompted baseline | 0.2581 | 0.0645 | 0.129 | 0.871 | -0.5613 |
| GRPO ~200 steps   | 0.1935 | 0.1935 | 0.258 | 0.742 | -0.4323 |

Findings:

- HONEST NEGATIVE. The pre-registered bar (fabricated == 0 AND verdict +5)
  MASSIVELY failed. Fabrication only fell 0.871 -> 0.742 (still fabricating on
  ~3 of every 4 rows), nowhere near 0. Mean reward improved (-0.561 -> -0.432)
  and cite_gold_rate TRIPLED (0.0645 -> 0.1935) - so RL did move the model toward
  real evidence - but verdict_acc actually DROPPED (0.2581 -> 0.1935): the model
  traded verdict correctness for citation behavior and still fabricates.
- Mechanism hypothesis: verbatim long-id copying is the WRONG ACTION SPACE for a
  1.5B. Asking the model to reproduce long evidence identifiers character-for-
  character is asking it to do the harness's bookkeeping; a small model cannot
  reliably copy long ids, so it fabricates. Fix is a harness-design change, not
  more RL: re-render the candidate evidence as letter choices (A-F) and let the
  harness map the chosen letter back to the id. "Don't make the model do the
  harness's job." Pre-registered as citation env v2 (D-2026-07-04-002).

Artifacts:

```text
runs/citation_prompted15_test_eval.json                 (prompted control)
runs/grpo_citation15/20260703T1725Z-e571324/{citation_grpo_test_eval.json,
  generations.jsonl,reward_trace.jsonl,trainer_log.jsonl,metrics.json,run_manifest.json}
```

Decision:

Record the honest negative; do NOT iterate on hparams for the verbatim-copy
action space. Pre-register citation env v2 with a letter-indexed (A-F) action
space mapped back by the harness (D-2026-07-04-002), then re-run before drawing
any conclusion about whether a 1.5B can do citation verification.

Next:

Implement citation env v2 (letter-indexed candidates) and re-run the 1.5B GRPO
against the same `citation_real_eval_v1` ruler. See TODO.
## EXP-2026-07-04-004 - Round 3 F1: citation LETTERS action space (1.5B), prompted vs GRPO

Goal:

Test the citation env v2 hypothesis (D-2026-07-04-002): if the fabrication in the
Night-3 negative (EXP-2026-07-04-003) is a WRONG-ACTION-SPACE problem - asking a
1.5B to copy long evidence ids verbatim - then re-rendering candidates as LETTER
choices (A-F) with the harness mapping the letter back to the id should make
fabrication structurally impossible and let the model actually pick evidence.
Same frozen `citation_real_eval_v1` ruler (test n=31), same pre-registered bar
(fabricated_rate == 0 AND verdict reward improves by >= +5).

Data:

`citation_real_eval_v1` (frozen, blind-double-annotated, test n=31). 1.5B base
(Qwen2.5-1.5B-Instruct), letter-indexed action space. Prompted-letters baseline
first as control; then GRPO-letters. Base commit e571324.

Metrics (test n=31, letters action space):

| arm | verdict_acc | cite_gold_rate | cite_valid_rate | fabricated_rate | mean_reward |
| --- | ---: | ---: | ---: | ---: | ---: |
| prompted-letters | 0.0968 | 0.7419 | 1.000 | 0.0 | 0.5452 |
| GRPO-letters     | 0.0968 | 0.8710 | 1.000 | 0.0 | 0.5710 |

For reference, v1 raw-id prompted (EXP-2026-07-04-003): fabricated 0.871,
cite_gold 0.0645, verdict_acc 0.2581.

Findings:

- ACTION-SPACE HYPOTHESIS CONFIRMED for the citation half. Letters drove
  fabricated_rate 0.871 -> 0.0 and cite_gold 0.0645 -> 0.7419 in the PROMPTED
  arm alone (no training) - the harness now does the id bookkeeping, exactly as
  designed. GRPO then lifted cite_gold 0.7419 -> 0.8710. So "don't make the model
  do the harness's job" is validated: reshaping the action space, not more RL,
  killed fabrication.
- BUT verdict_acc FELL 0.2581 (v1 raw-id prompted) -> 0.0968 (letters). The honest
  reading: the old higher verdict number was partly LUCKY GUESSING while citations
  were wrong; once letters made citation easy, the (broken) verdict head was
  exposed with nothing to hide behind. GRPO moved cite_gold up (0.7419 -> 0.8710)
  while verdict_acc stayed FLAT (0.0968) - COMPONENT-REWARD DECOUPLING: the reward
  can drive the citation component without touching the verdict component.
- Pre-registered bar is HALF-MET: fabricated_rate == 0 PASSES; verdict +5 FAILS
  (verdict flat). Recorded as an HONEST PARTIAL - the citation-fabrication problem
  is solved by the action-space fix; the 5-way verdict problem is a SEPARATE,
  unsolved capability (probed further in EXP-2026-07-04-009).

Artifacts:

```text
runs/citation_letters_prompted15_test_eval.json                 (prompted-letters control)
runs/grpo_citation_letters15/20260704T0045Z-e571324/{citation_letters_grpo_test_eval.json,
  generations.jsonl,reward_trace.jsonl,trainer_log.jsonl,metrics.json,run_manifest.json}
```

Decision:

Citation env v2 letter action space is ADOPTED (fabrication solved). The residual
verdict failure is not an RL-objective artifact but a verdict-head capability gap;
probe whether SUPERVISED training also fails it before blaming the objective
(-> EXP-2026-07-04-009), and grow the corpus (backlog).

Next:

Run citation SFT-letters to isolate whether the verdict head is data-starved /
capacity-limited rather than an RL decoupling artifact (EXP-2026-07-04-009).

## EXP-2026-07-04-005 - Round 3 F2: DPO pairs v2 (1.5B) - does the pair fix restore exploration?

Goal:

Test DPO pair v2 (D-2026-07-04-004): the v1 DPO collapse (gate-perfect,
reward-collapsed) was diagnosed as a pair artifact (rejected == the escalate
action, teaching "never escalate"). v2 adds "failed-to-escalate" negatives so
escalation is the WINNER on hard seeds. Does balancing the pair distribution
restore success/exploration while keeping gate discipline?

Data:

Escalation env v0.3, test n=48, greedy seed 0, lambda sweep. Same 1.5B init and
ruler as v1 for a clean read. `runs/dpo_v2_qwen15_pairs.jsonl` (rebalanced pairs).

Metrics (test n=48, lambda=0.3 headline; greedy):

| arm | reward | gate_recall | success | cost |
| --- | ---: | ---: | ---: | ---: |
| DPO v1 (EXP-2026-07-04-001) | 0.5382 | 1.000 | 0.58 | 0.139 |
| DPO v2                      | 0.5213 | 1.000 | 0.5833 | 0.2068 |

(v2 lambda sweep: reward 0.5627 @0.1, 0.5213 @0.3, 0.4593 @0.6; gate 1.000 and
success 0.5833 at all lambda.)

Findings:

- HONEST NEGATIVE / INSUFFICIENT FIX. Success barely moved (0.58 -> 0.5833) and
  reward is flat-to-slightly-lower (0.5382 -> 0.5213 @0.3). The pre-registered
  kill-check fails (delta -0.2282 vs the SFT 0.7495 baseline; gate 1.000 held but
  reward far below baseline).
- INTERPRETATION: the pair fix ALONE is insufficient. Over-conservatism is NOT
  (only) a one-sided-pair artifact - balancing the pair distribution did not buy
  back exploration. The DPO policy still under-explores (success stuck ~0.58) even
  when escalation is no longer uniformly the rejected action. So the next lever is
  not more pair surgery but a BETA SWEEP (beta 0.1 may be over-constraining the
  policy toward the reference); recorded to backlog.

Artifacts:

```text
runs/dpo_v2_qwen15/20260704T0059Z-e571324/{dpo_v2_test_eval.json,test_preds.jsonl,
  trainer_log.jsonl,metrics.json,run_manifest.json}
runs/dpo_v2_qwen15_pairs.jsonl
```

Decision:

Record the honest negative; do not iterate further on pair construction. Promote a
DPO beta sweep to the backlog as the next lever (D-2026-07-04-004 amended). SFT
1.5B remains the promotable policy; DPO stays a bracketing datapoint, not a winner.

Next:

DPO beta sweep (backlog). No further pair-design iterations.

## EXP-2026-07-04-006 - Round 3 F3: 0.5B temperature probe - collapse = knowledge loss, not a decoding artifact?

Goal:

Settle the sampling-vs-greedy split from F-2026-07-04-002: the collapsed 0.5B v2
adapter kept the gate action alive in training SAMPLES but collapsed to gate 0.00
in GREEDY eval. Is the greedy-0.00 a DECODING-MODE artifact (the gate mode exists
but greedy misses it) or GENUINE KNOWLEDGE LOSS (the gate capability is gone)?
Pre-registered threshold: gate_action_presence_rate >= 0.90 across sampled decode
would mean "mode exists, greedy just misses it"; below it means knowledge loss.

Data:

The collapsed 0.5B GRPO-v2 adapter (`runs/grpo_v2_qwen05/20260703T1608Z-e571324`),
escalation env v0.3 test n=48, 8 gate-needed seeds. Sampled decode at T=0.7 and
T=1.0, n_samples=8, with `gate_action_presence` reported.

Metrics (test n=48, sampled n=8):

| decode | gate_action_presence_rate | seeds_with_gate_in_samples / 8 | per-sample gate_recall @0.3 |
| --- | ---: | ---: | ---: |
| T=0.7 | 0.0    | 0/8 | 0.0    |
| T=1.0 | 0.25   | 2/8 | 0.0625 |

Findings:

- PRE-REGISTERED THRESHOLD NOT MET. At T=0.7 the gate action is entirely absent
  from all 8 gate seeds' samples (presence 0.0); at T=1.0 only 2 of 8 gate seeds
  ever surface a gate action across 8 samples (presence 0.25), and per-sample gate
  recall is 0.0625. Presence 0.25 << 0.90 threshold.
- CONCLUSION: the collapse is GENUINE KNOWLEDGE LOSS, not a decoding-mode artifact.
  The gate action is not merely a non-modal but reachable branch; at low temp it is
  extinct and even at T=1.0 it barely surfaces. The capacity-floor claim for the
  0.5B (previously OBSERVED from the greedy collapse) is now UPGRADED to TESTED: the
  gate capability itself is destroyed under group-relative advantage at 0.5B, not
  hidden behind greedy decoding. (Consistent with the all-violate-group taxonomy:
  0.55 all-violate at 0.5B - no gradient to preserve the action.)

Artifacts:

```text
runs/grpo_v2_qwen05/20260703T1608Z-e571324/{sampled_T0.7_eval.json,sampled_T1.0_eval.json}
  (each carries gate_action_presence: {gate_needed_seeds, seeds_with_gate_in_samples,
   gate_action_presence_rate} + scores_per_sample_avg)
```

Decision:

Capacity-floor claim upgraded observed -> tested. The 0.5B kill verdict stands and
is now evidenced at the mechanism level (knowledge loss, not decode mode). No
further 0.5B mitigation attempts warranted at this size.

Next:

None for 0.5B. The multi-seed batch (EXP-2026-07-04-007) separately shows the
collapse is high-probability (2/3 seeds) rather than deterministic.

## EXP-2026-07-04-007 - Batch 4 Phase A: multi-seed error bars (SFT 1.5B, GRPO-v2 3B, GRPO 0.5B), seeds {0,1,2}

Goal:

Put ERROR BARS on the three load-bearing single-seed claims from the scale sweep by
re-running each at seeds {0,1,2} and aggregating mean +/- std: (1) the "trained 1.5B
beats prompted 7B" headline (SFT 1.5B), (2) the 3B oracle crown jewel (GRPO-v2 3B,
which isolates GRPO SAMPLING variance since all three init from the same seed-0 3B
SFT), (3) the 0.5B collapse (GRPO 0.5B plain - is it deterministic or probabilistic?).

Data:

Escalation env v0.3, test n=48 (8 gate seeds), greedy seed-0 eval, lambda sweep.
Three training seeds per config. Aggregated by `scripts/rl/aggregate_seeds.py`
into `runs/agg/{sft_qwen15,grpo_v2_qwen3,grpo_qwen05}.json`.

Metrics (lambda=0.3, mean +/- std over 3 seeds; per-seed in the agg jsons):

| config | reward mean+/-std [min,max] | gate_recall mean+/-std | per-seed reward |
| --- | --- | --- | --- |
| SFT 1.5B      | 0.7024 +/- 0.0333 [0.6772, 0.7495] | 0.75 +/- 0.102 | [0.7495, 0.6772*, 0.6805] |
| GRPO-v2 3B    | 0.8473 +/- 0.0000 [0.8473, 0.8473] | 1.000 +/- 0.0  | [0.8473, 0.8473, 0.8473] |
| GRPO 0.5B     | 0.4721 +/- 0.1221 [0.383, 0.6448]  | 0.1667 +/- 0.2357 | [0.383, 0.6448, 0.383] |

(*SFT 1.5B per-seed gate_recall [0.875, 0.625, 0.75]; seed-0's 0.7495 is the MAX
of the three. GRPO 0.5B per-seed gate_recall [0.0, 0.5, 0.0].)

Findings:

- HEADLINE REVISION (SFT 1.5B, honest downgrade). SEED 0 (0.7495) is the BEST of
  the three; the MEAN is 0.7024 +/- 0.0333. The "trained 1.5B beats prompted 7B
  (0.7447)" claim therefore holds ONLY AT SEED 0; at the mean it does NOT
  (0.7024 < 0.7447). The portfolio headline is downgraded to a mean+/-std claim and
  the "beats 7B" line is flagged as seed-0-only. This is exactly why multi-seed was
  run.
- CROWN JEWEL REPLICATED (GRPO-v2 3B). All THREE seeds converge to 0.8473 / gate
  1.000 EXACTLY (std 0.0) - the analytic oracle, reproduced with zero variance.
  Caveat stated honestly: this isolates GRPO SAMPLING variance only (all three
  init from the same seed-0 3B SFT adapter), not full-pipeline (SFT+GRPO) variance.
  Still the strongest result in the portfolio and now replicated.
- COLLAPSE IS PROBABILISTIC, NOT DETERMINISTIC (GRPO 0.5B). Collapse in 2/3 seeds
  (seeds 0 and 2: 0.383 / gate 0.0); seed 1 was PARTIAL (0.6448 / gate 0.5) and
  actually BEAT the SFT baseline. Revision: the 0.5B collapse is a HIGH-PROBABILITY
  INSTABILITY (2/3), not a deterministic law. Kill verdict UNCHANGED - no seed
  comes near the gate 0.99 bar (best gate is 0.5), and the mean gate 0.1667 is far
  below promotable.

Artifacts:

```text
runs/agg/{sft_qwen15.json, grpo_v2_qwen3.json, grpo_qwen05.json}  (mean/std/min/max + per-seed + eval_paths)
runs/sft_qwen15_seed1/20260704T0135Z-e571324/  runs/sft_qwen15_seed2/20260704T0210Z-e571324/
runs/grpo_v2_qwen3_seed1/20260704T0136Z-e571324/  runs/grpo_v2_qwen3_seed2/20260704T0211Z-e571324/
runs/grpo_qwen05_seed1/20260704T0159Z-e571324/  runs/grpo_qwen05_seed2/20260704T0234Z-e571324/
runs/gpu_session_20260704/batch4.log
```

Decision:

Portfolio headlines move from seed-0 single-point claims to mean+/-std claims
(D-2026-07-04-006). "1.5B beats 7B" is honestly downgraded to seed-0-only; the 3B
oracle is promoted as the replicated crown jewel (GRPO-variance-only caveat); the
0.5B collapse is restated as 2/3-seed instability.

Next:

Full-pipeline (SFT+GRPO seed-varied) 3B multi-seed would close the last variance
caveat (backlog). Report all headline cells with error bars in PORTFOLIO_INDEX.

## EXP-2026-07-04-008 - Batch 4 Phase B: Gemma 4 cross-family prompted (E2B / E4B) - does small-model gate blindness generalize?

Goal:

Test whether the Qwen small-prompted GATE BLINDNESS (prompted gate recall: 0.5B/1.5B
0.50, 3B 0.00) is a UNIVERSAL small-model law or FAMILY-DEPENDENT. Prompt Gemma 4
(cross-family) on the identical env v0.3 ruler with no training and compare.

Data:

Escalation env v0.3, test n=48 (8 gate seeds), greedy, lambda sweep. Gemma 4
prompted E2B (effective 2.3B) and E4B (effective 4.5B). NOTE the MatFormer caveat:
these are EFFECTIVE-param (selective activation) sizes, not dense params, so
size comparisons to dense Qwen are approximate.

Metrics (test n=48, lambda=0.3, greedy):

| arm | reward | gate_recall | success | cost |
| --- | ---: | ---: | ---: | ---: |
| Gemma-4 E2B (eff 2.3B) prompted | 0.7440 | 0.875 | 0.9375 | 0.5062 |
| Gemma-4 E4B (eff 4.5B) prompted | 0.7452 | 0.875 | 0.9375 | 0.5022 |
| (ref) Qwen-7B prompted          | 0.7447 | 0.75  | 1.0    | -     |
| (ref) Qwen-3B prompted          | 0.4232 | 0.00  | -      | -     |

Findings:

- CROSS-FAMILY HYPOTHESIS REFUTED. Qwen's small-prompted gate blindness does NOT
  replicate on Gemma 4: BOTH Gemma sizes reach gate 0.875 prompted (vs Qwen 3B's
  0.00 and 1.5B's 0.50). The gate-discipline-is-a-universal-small-model-deficit
  claim is FALSE; it is FAMILY-DEPENDENT (instruction-tuning / safety priors),
  not a size law. A Gemma-2.3B-effective PROMPTED already matches a Qwen-7B
  PROMPTED (0.744 vs 0.7447).
- MOTIVATION STANDS, SHARPENED. Neither prompted Gemma reaches the gate 0.99 bar
  (both stall at 0.875), and the TRAINED Qwen 3B (0.8473 / gate 1.000) leads the
  best prompted Gemma by ~10 reward pts AND carries the gate perfectly. So training
  still wins - the sharper framing is "training beats the best available prompt,
  cross-family," not "small prompted models are all gate-blind."

Artifacts:

```text
runs/gemma_prompted/{e2b_test_eval.json,e4b_test_eval.json,e2b_test_preds.jsonl,e4b_test_preds.jsonl}
runs/gpu_session_20260704/batch4.log
```

Decision:

Add the Gemma cross-family row to the portfolio with the effective-vs-dense param
caveat; record the cross-family-blindness REFUTATION (family-dependent, not
universal) as D-2026-07-04-007. Training motivation restated as "beats best
cross-family prompt + carries the gate."

Next:

A full Gemma 4 SFT/GRPO sweep would test whether the 3B sweet-spot / 7B dip
generalize across families (backlog, needs a Gemma-capable training path).

## EXP-2026-07-04-009 - Batch 4 Phase C: citation SFT (letters, 1.5B) - is the verdict head data-starved?

Goal:

Answer the component-decoupling probe from F1 (EXP-2026-07-04-004): GRPO-letters
lifted cite_gold while verdict_acc stayed flat (0.0968). Is the stuck verdict a
property of the RL OBJECTIVE (component decoupling) or a deeper CAPABILITY gap?
Supervised training is the cleanest control: if SFT ALSO fails to teach the 5-way
verdict, the objective is exonerated and the verdict is data-starved / capacity-
limited.

Data:

`citation_real_eval_v1` (test n=31), 1.5B, letters action space, argmax-SFT on the
citation oracle labels (62 train rows). Base commit e571324.

Metrics (test n=31, letters):

| arm | verdict_acc | cite_gold_rate | cite_valid_rate | fabricated_rate | mean_reward |
| --- | ---: | ---: | ---: | ---: | ---: |
| prompted-letters (EXP-...-004) | 0.0968 | 0.7419 | 1.000 | 0.0 | 0.5452 |
| GRPO-letters (EXP-...-004)     | 0.0968 | 0.8710 | 1.000 | 0.0 | 0.5710 |
| SFT-letters (this run)         | 0.0645 | 0.8387 | 1.000 | 0.0 | 0.5323 |

Findings:

- PROBE ANSWERED: NOT THE RL OBJECTIVE'S FAULT. SUPERVISED training ALSO fails to
  teach the verdict - SFT verdict_acc 0.0645 is actually LOWER than prompted 0.0968
  and GRPO 0.0968. So the flat verdict under GRPO is NOT an RL component-decoupling
  artifact; the 5-way verdict capability is genuinely DATA-STARVED (only 62 train
  rows) and/or capacity-limited at 1.5B. SFT reproduced the citation behavior
  (cite_gold 0.8387, fabricated 0.0) - it learns the easy citation half fine and
  still cannot move the verdict.
- The verdict failure is now localized to a DATA/CAPACITY axis, not an algorithm
  axis. Next levers are corpus growth (131 -> 300-500, already backlog) and/or a
  bigger model - NOT reward shaping.

Artifacts:

```text
runs/sft_citation15/20260704T0251Z-e571324/{citation_sft_test_eval.json,test_preds.jsonl,
  trainer_log.jsonl,metrics.json,run_manifest.json}
```

Decision:

Verdict-head failure recorded as DATA-STARVED / capacity-limited, not an RL-objective
artifact (D-2026-07-04-008). Promote citation corpus growth (131 -> 300-500) as the
next lever; consider a larger model for the verdict head. Close the citation-verdict
line at 1.5B.

Next:

Grow the citation corpus (backlog) and re-run; optionally probe verdict at 3B once
the corpus is larger.

## EXP-2026-07-04-010 - DPO beta sweep (1.5B, pairs v2, escalation @lambda0.3) - does relaxing beta buy back exploration?

Goal:

Close the F2 next-lever from EXP-2026-07-04-005: DPO pairs v2 was gate-perfect but
reward-collapsed (0.5213 / gate 1.0 / success 0.5833) and the pair rebalance alone did
not recover exploration. beta=0.1 pins the policy hard to the reference; sweep beta up
(0.3, 0.5) to test whether relaxing the KL anchor recovers success, or whether DPO's
safety-first / exploration-poor character is STRUCTURAL on this task.

Data:

Escalation env v0.3, test n=48 (8 gate seeds), greedy, lambda sweep {0.1,0.3,0.6}.
1.5B, DPO pairs v2 (196 pairs), init from the seed-0 SFT adapter
(runs/sft_qwen15/20260703T1506Z-e571324/adapter), 3 epochs. Two betas: 0.3 and 0.5.
Base commit e571324.

Command:

```text
dpo_escalation.py --model Qwen/Qwen2.5-1.5B-Instruct --env-dir .../escalation_env_v0.1 \
  --lambda 0.3 --init-adapter runs/sft_qwen15/20260703T1506Z-e571324/adapter \
  --pairs-version v2 --beta {0.3,0.5} --epochs 3 --out-dir runs/dpo_v2_beta{03,05}_qwen15 --seed 0
```

Metrics (test n=48, greedy; each beta swept over lambda):

| arm | lambda | reward | success | cost | gate_recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| DPO v2 beta=0.1 (EXP-...-005) | 0.3 | 0.5213 | 0.5833 | 0.139 | 1.000 |
| DPO v2 beta=0.3 (this run)    | 0.3 | 0.5989 | 0.6667 | 0.2258 | 1.000 |
| DPO v2 beta=0.5 (this run)    | 0.3 | 0.5989 | 0.6667 | 0.2258 | 1.000 |
| (ref) SFT baseline seed 0     | 0.3 | 0.7495 | -      | -     | 1.000 |

(beta=0.3 lambda sweep: 0.1 -> 0.6441, 0.3 -> 0.5989, 0.6 -> 0.5312, all success 0.6667
/ gate 1.000; beta=0.5 is DIGIT-IDENTICAL across the whole lambda sweep. final_loss
differs slightly, beta0.3 0.3782 vs beta0.5 0.3238, but the greedy policy is the same.)

Findings:

- OBSERVATION: TWO BETAS CONVERGED TO DIGIT-IDENTICAL GREEDY POLICIES. beta=0.3 and
  beta=0.5 produce the same reward/success/cost/gate to 4 decimals at every lambda -
  the greedy argmax action set is identical despite different KL anchoring. (Recorded
  as an observation in this entry, not a failure - the runs are healthy; the loss
  curves differ, the greedy decode collapses to the same trajectory.)
- Relaxing beta DOES recover SOME exploration: success 0.5833 (beta0.1) -> 0.6667
  (beta>=0.3), reward 0.5213 -> 0.5989 at lambda0.3. But it PLATEAUS ~15 pts of success
  and ~0.15 reward BELOW the SFT baseline (0.7495) and never re-crosses the kill line
  (beats_baseline_by_3pts_and_holds_gate = false; delta -0.1506).
- CONCLUSION: DPO's safety-first / exploration-poor character on this task is
  STRUCTURAL, not a hyperparameter accident. It is now robust across 2 pair designs
  (v1, v2) x 3 betas (0.1, 0.3, 0.5). Gate stays perfect (1.000) throughout - DPO buys
  gate discipline at the price of ~half the exploration/success the SFT baseline reaches.

Artifacts:

```text
runs/dpo_v2_beta03_qwen15/20260704T0624Z-e571324/{dpo_v2_beta03_test_eval.json,metrics.json,
  run_manifest.json,test_preds.jsonl,trainer_log.jsonl}
runs/dpo_v2_beta05_qwen15/20260704T0626Z-e571324/{dpo_v2_beta05_test_eval.json,metrics.json,
  run_manifest.json,test_preds.jsonl,trainer_log.jsonl}
```

Decision:

The three-method comparison is now FINAL and recorded in D-2026-07-04-009: GRPO =
efficiency (analytic oracle at 3B), DPO = safety (gate 1.000 at ~half the success),
SFT = balanced baseline. DPO's over-conservatism is closed as STRUCTURAL. No further
beta / pair work on this arm.

Next:

DPO arm closed. Remaining escalation levers: env v0.4 memory-arm matrix (standing
big-ticket), Plan C inference-backend control column, lambda=0.6 exploration arm.

## EXP-2026-07-04-011 - Citation training-pool expansion v1 build (construction-labeled, spot-audited)

Goal:

Grow the data-starved 5-way citation verdict train pool (D-2026-07-04-008: verdict
head stuck ~0.06-0.10 because the eval train split carried only 1 contradicts + 1
partial). Build a construction-labeled TRAIN/dev pack that un-starves the boundary
classes, on the same schema and point-in-time discipline as the frozen eval, WITHOUT
touching the frozen eval.

Data:

Committed earlier by the collection agent as commit b6c909a (this entry backfills the
EXPERIMENT_LOG record). Dataset:
`.../citation_contract_repair_v0.1/citation_train_expansion_v1/` (manifest.json).

Build summary (from manifest.json):

- 146 construction-labeled rows: train 122 + label-stratified dev 24, NO test rows.
- 21 AI-vertical issuers (40 source filings): NVDA/AMD 14 each, MRVL/AMZN 9, GOOGL/META
  8, AVGO/QCOM/VRT ~7, ... ; source types 10-K 68 / 10-Q 72 / 20-F 5 / 8-K 1.
- Filing URLs discovered via the EDGAR submissions API; 0 fetch / 0 anchor failures
  (accepted_rate 1.0). Every anchor verified present in the fetched filing with the
  label-critical-fact guard (F-2026-07-02-002) + shortest-containing-block selection.
- Label mix: verified_support 70 / contradicts 35 / partial_support 22 / insufficient
  19 - vs the eval train split's 1 contradicts + 1 partial, this UN-STARVES the
  boundary classes (the whole point).
- Labels marked construction_v1_unaudited. A 10.3% stratified blind two-pass
  spot-audit agreed 93.3% (>=90% gate); one C2 period-binding correction applied.
- Opaque sample_ids (F-2026-07-02-006); frozen eval citation_real_eval_v1 (131 rows)
  UNTOUCHED / immutable.
- Emits the letters-action-space SFT file; verified consumable by
  sft_citation.py --eval-dir --labels-only (122 train rows, 0 mapping mismatches).

Artifacts:

```text
commit b6c909a (data: citation training-pool expansion v1)
.../citation_train_expansion_v1/{manifest.json,rows/{all,train,dev}.jsonl,
  sources.json,failures.json,AUDIT_NOTE.md,audit/{spot_audit_blind,spot_audit_votes}.json,
  sft/sft_citation_letters.jsonl}
.../scripts/build_citation_train_expansion_v1.py (+ cases modules)
```

Metrics:

n/a (data build). Combined citation train pool now 131 + 146 = 277 (target 300-500,
one more batch to go).

Decision:

Feeds EXP-2026-07-04-012 (the data-starvation test) and D-2026-07-04-009 (data-scaling
path validated). Next collection batch reaches ~400+, then 3B capacity probe.

Next:

One more collection batch to ~400+; then re-run citation SFT/GRPO on the combined pool.

## EXP-2026-07-04-012 - D-008 data-starvation test: SFT-letters on the EXPANDED pool (1.5B, frozen test n=31)

Goal:

THE PAYOFF for the D-008 attribution chain. EXP-2026-07-04-009 showed SFT-letters on
62 train rows could not move the verdict (0.0645), localizing the failure to a
DATA/CAPACITY axis. Test the DATA half directly: re-run SFT-letters on the EXPANDED
(class-balanced) train pool and evaluate on the SAME FROZEN test (n=31, letters). If
verdict_acc jumps, the verdict head was data-starved (specifically class-starved);
capacity becomes the next probe.

Data:

Train = citation_train_expansion_v1 train split (122 rows, class-balanced). Eval =
frozen citation_real_eval_v1 test (n=31), letters action space. 1.5B, 3 epochs, lr 2e-4,
seed 0. Base commit e571324.

Command:

```text
sft_citation.py --eval-dir .../citation_train_expansion_v1 --split train \
  --model Qwen/Qwen2.5-1.5B-Instruct --out-dir runs/sft_citation15_expanded --seed 0
```

Metrics (frozen test n=31, letters):

| arm | train rows | verdict_acc | cite_gold | cite_valid | fabricated | mean_reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| prompted-letters (EXP-...-004) | 0   | 0.0968 | 0.7419 | 1.000 | 0.0 | 0.5452 |
| SFT-letters @62 (EXP-...-009)  | 62  | 0.0645 | 0.8387 | 1.000 | 0.0 | 0.5323 |
| SFT-letters @expanded (this)   | 122 | 0.3871 | 0.9355 | 1.000 | 0.0 | 0.8742 |

Findings:

- HYPOTHESIS CONFIRMED. verdict_acc 0.0645 (@62) -> 0.3871 (@expanded) = a ~6x jump
  (also 6x over prompted 0.0968) on the UNCHANGED frozen test. The verdict head was
  DATA-STARVED, specifically CLASS-STARVED (contradicts/partial): adding the boundary
  classes is what moved it.
- The easy citation half also improved (cite_gold 0.8387 -> 0.9355) and fabrication
  stayed 0.0; mean_reward 0.5323 -> 0.8742.
- ATTRIBUTION CHAIN COMPLETE: action-space (fixed - fabrication 0) -> data (confirmed
  today) -> capacity (next probe: 3B on the same expanded data).

Failures / honest caveats:

- 0.387 is still FAR from usable - this is a direction confirmed, not a solved task.
- Single seed; n=31 frozen test; the expansion train data is construction-labeled
  (spot-audited 93.3%, construction_v1_unaudited), not human-gold.

Artifacts:

```text
runs/sft_citation15_expanded/20260704T0647Z-e571324/{citation_sft_expanded_test_eval.json,
  metrics.json,run_manifest.json,trainer_log.jsonl}
```

Decision:

Data-scaling path VALIDATED (D-2026-07-04-009). Next levers pre-registered: one more
collection batch to ~400+, then 3B citation SFT (capacity probe), then GRPO-letters on
the expanded pool (does RL add anything on top of healthy SFT data).

Next:

Collection batch 2 -> ~400+; 3B capacity probe on the expanded pool; GRPO-letters on
the expanded pool.
