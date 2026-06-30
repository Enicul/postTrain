# Progress

Last updated: 2026-06-30

## Current State

The repo has been initialized as a standalone post-training artifact repo for
KIWI interview preparation.

Recording protocol update:

- local experiments now use summary-first recording by default;
- full row-level prediction dumps require explicit `--record-mode full`;
- see `docs/RECORDING_PROTOCOL.md`.

Latest router repair checkpoint:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c
```

Router v0.1c repaired the missing-label contract and real-tool trace shortcut:

| Holdout | Old expanded acc | v0.1c acc |
| --- | ---: | ---: |
| golden_v0.1_router_all | 0.3023 | 0.8895 |
| long_research_repair_25_router_all | 0.4800 | 0.9600 |
| real_tool_trace_pilot_10_router | 0.0000 | 1.0000 |

Imported from the Agent/KIWI workspace:

- golden training corpus `golden_v0.1`,
- CPU specialist baseline script,
- baseline requirements,
- first CPU baseline run artifacts.

Initial GitHub push is complete.

```text
remote: git@github.com:Enicul/postTrain.git
branch: main
initial commit: 7d64753 docs: initialize post-training artifact repo
learning source registry commit: d048963 docs: add learning source registry
```

## Current Checkpoint

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1
```

Important subpaths:

```text
datasets/
baselines/specialist_cpu_baselines_v0.1/
baselines/specialist_cpu_first_training_20260630T030852Z/
repairs/citation_verifier_repair_v0.1/
repairs/citation_verifier_repair_v0.2/
```

Latest expanded checkpoint:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Canonical expanded CPU baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Latest realistic holdout eval:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z/holdouts/realistic_holdout_eval_v0.1_20260630T083000Z
```

## Baseline Results

| Specialist | Target | Test accuracy | Test macro F1 | Status |
| --- | --- | ---: | ---: | --- |
| router_classifier | route_label | 0.9167 | 0.9368 | usable first baseline |
| risk_reviewer | risk_level | 0.5946 | 0.3986 | weak baseline |
| citation_verifier | support_type | 0.2581 | 0.1441 | data repair needed |

Latest tracked training run:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_first_training_20260630T030852Z
```

## Interpretation

- Router is the first credible specialist baseline.
- Risk reviewer is directionally useful but too weak to use as a gate alone.
- Citation verifier failed on held-out data. `citation_verifier_repair_v0.1`
  produced an error taxonomy and repair probes, but the result still points to
  data repair before GPU work.

## Citation Verifier Repair v0.1

Repair pack:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1
```

Top error types:

| Failure type | Count |
| --- | ---: |
| composite_claim | 22 |
| support_boundary_confusion | 17 |
| source_quality_feature_missing | 10 |
| hard_negative_overaccepted | 8 |
| partial_support_boundary | 6 |
| rare_negative_class_boundary | 6 |
| positive_support_missed | 5 |

Repair probe results:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy | Status |
| --- | ---: | ---: | ---: | --- |
| original citation_verifier | 0.2581 | 0.1441 | 0.4839 | failed baseline |
| citation_verifier_url | 0.2581 | 0.1390 | 0.4839 | source URL/domain alone did not help |
| citation_support_binary | 0.3871 | 0.3767 | 0.5806 | clearer task, still weak |

Decision:

Do not start citation-verifier GPU fine-tuning yet. Build
`citation_verifier_repair_v0.2` with more hard negatives, cleaner positive
official spans, partial-support boundary cases, and rare negative examples.

## Citation Verifier Repair v0.2

Repair pack:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2
```

What changed:

- Added `build_citation_repair_v02.py`.
- Generated train-only citation candidates from the original frozen train split.
- Kept dev/test unchanged for comparability.
- Ran a local ablation before choosing which generated rows to train on.
- Selected dataset-specific augmentation instead of using every synthetic row.

Selected strategy:

| Dataset | Train rows | Added rows |
| --- | ---: | --- |
| citation_verifier_url | 178 | hard negatives + missing evidence |
| citation_support_binary | 148 | hard negatives only |

Repair probe results:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy | Status |
| --- | ---: | ---: | ---: | --- |
| v0.2 citation_verifier_url | 0.3871 | 0.3333 | 0.4839 | improved, still not enough |
| v0.2 citation_support_binary | 0.4194 | 0.4139 | 0.5806 | improved, still not enough |

Decision:

v0.2 is a real repair signal, but it is still not strong enough for citation
verifier GPU fine-tuning. The next step is real span audit, not more synthetic
flooding.

## AI Expanded v0.1 Import + CPU Baseline

Imported curated v0.6 data from the Agent/KIWI workspace into this standalone
repo:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Source curation summary:

| Dataset | Train | Dev | Test |
| --- | ---: | ---: | ---: |
| router_classifier | 6,000 | 1,200 | 1,200 |
| risk_reviewer | 8,000 | 1,600 | 1,600 |
| citation_verifier | 6,000 | 1,200 | 1,200 |
| sft_trajectories | 8,000 | 1,600 | 1,600 |
| preference_pairs | 8,000 | 1,600 | 1,600 |
| grpo_rollouts | 8,000 | 1,600 | 1,600 |

Canonical baseline run:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1 \
  --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines \
  --run-id specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Results:

| Specialist | Target | Test accuracy | Test macro F1 | Majority accuracy | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| router_classifier | route_label | 1.0000 | 1.0000 | 0.1667 | easy-distribution baseline; needs realistic holdout |
| risk_reviewer | risk_level | 1.0000 | 1.0000 | 0.6669 | easy binary schema; do not overclaim |
| citation_verifier | support/verdict | 0.9000 | 0.8978 | 0.3333 | much better than golden v0.1, but synthetic/easy negatives likely help |

Decision:

The expanded schema is learnable and useful for GPU-readiness plumbing, but the
near-perfect router/risk scores indicate an easy/template-heavy distribution.
Before GPU fine-tuning, run external holdouts from real/long-research traces and
add harder boundary examples.

## Realistic Holdout Eval v0.1

Script:

```text
training-corpus/scripts/evaluate_baseline_holdouts.py
```

Command:

```bash
python3 training-corpus/scripts/evaluate_baseline_holdouts.py \
  --run-id realistic_holdout_eval_v0.1_20260630T083000Z
```

Output:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z/holdouts/realistic_holdout_eval_v0.1_20260630T083000Z
```

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

Interpretation:

The expanded split was learnable but not robust. External holdouts exposed
schema gaps and distribution shift:

- router expanded data lacks `risk_review` and `clarification_needed`;
- risk expanded data lacks `medium`;
- citation expanded labels do not cover `partial_support`, `insufficient`,
  `contradicts`, `candidate_evidence`, or `search_snippet_candidate_evidence`;
- real tool traces are routed mostly as `financial_calculation`, showing a
  shortcut learned from the expanded synthetic split.

Decision:

Do not start GPU fine-tuning yet. Build a router/risk/citation contract repair
set from real tool traces and long-research rows first.

## Learning Source Registry

`LEARNING_SOURCES.md` has been added as the canonical place to record external
model reports and what we extracted from them.

Current source entries:

| Source | Status | Extracted use |
| --- | --- | --- |
| GLM ARC: Agentic + Reasoning + Coding | adopted as architecture framing | use ARC to explain why KIWI needs reasoning, verifier-rich tasks, agentic loops, and process-level verifiers, while not claiming a GLM-scale unified model |

## Last Verified Commands

```bash
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
python3 training-corpus/scripts/train_specialist_baselines.py --run-id smoke_router_only2 --datasets router_classifier --out-root /tmp/posttrain-baseline-smoke2
python3 training-corpus/scripts/train_specialist_baselines.py --run-id specialist_cpu_first_training_20260630T030852Z
python3 training-corpus/scripts/repair_citation_verifier.py --repair-id citation_verifier_repair_v0.1
python3 training-corpus/scripts/train_specialist_baselines.py --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/repaired_datasets --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/baselines --run-id citation_repair_probe_v0.1 --datasets citation_verifier_url,citation_support_binary
python3 -m py_compile training-corpus/scripts/build_citation_repair_v02.py training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/build_citation_repair_v02.py --help
python3 training-corpus/scripts/build_citation_repair_v02.py
python3 training-corpus/scripts/train_specialist_baselines.py --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/repaired_datasets --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/baselines --run-id citation_repair_probe_v0.2 --datasets citation_verifier_url,citation_support_binary
rsync -a --delete /Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --data-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1 --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines --run-id specialist_cpu_ai_expanded_v0.1_20260630T080225Z
python3 -m py_compile training-corpus/scripts/evaluate_baseline_holdouts.py
python3 training-corpus/scripts/evaluate_baseline_holdouts.py --help
python3 training-corpus/scripts/evaluate_baseline_holdouts.py --run-id realistic_holdout_eval_v0.1_20260630T083000Z
git push -u origin main
```

The imported baseline checkpoint reports:

```json
{"status": "complete", "run_id": "specialist_cpu_baselines_v0.1"}
```

## Next Best Step

Repair the data contracts exposed by realistic holdout eval v0.1:

1. build `router_social_boundary_repair_v0.1` for long social/bookmark claims
   that still downgrade to `fast_answer`;
2. build `risk_contract_repair_v0.1` with `medium` and human-gate semantics;
3. define citation label mapping for candidate evidence vs verified support;
4. rerun repaired baselines as probes before any GPU fine-tuning;
5. keep repaired runs in summary recording mode unless full row-level analysis is
   explicitly needed;
6. add Qwen, DeepSeek, Kimi, and MiniMax/WebExplorer source entries using the
   same extracted / not-adopted structure.
