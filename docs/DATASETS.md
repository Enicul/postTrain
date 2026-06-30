# Dataset Inventory

## Current Frozen Data

Path:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1
```

## Current Expanded Data

Path:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Purpose:

This is the larger server-portable pack imported from the Agent/KIWI workspace.
It is useful for pipeline readiness, small specialist training preparation, and
future SFT/DPO/GRPO formatting work. It should not replace `golden_v0.1` as the
strict failure-analysis pack.

Imported selected rows:

| Dataset | Train | Dev | Test | Intended use |
| --- | ---: | ---: | ---: | --- |
| calculation_verifier | 2,000 | 500 | 500 | deterministic calculation task data |
| citation_verifier | 6,000 | 1,200 | 1,200 | claim-evidence support classifier |
| event_extractor | 6,000 | 1,200 | 1,200 | structured market/filing/news event extraction |
| grpo_rollouts | 8,000 | 1,600 | 1,600 | future verifiable RL rollout substrate |
| memo_quality_scorer | 8,000 | 1,600 | 1,600 | memo quality / revision classifier |
| preference_pairs | 8,000 | 1,600 | 1,600 | future DPO / preference tuning pairs |
| risk_reviewer | 8,000 | 1,600 | 1,600 | risk/safety review classifier |
| router_classifier | 6,000 | 1,200 | 1,200 | coordinator route classifier |
| sft_trajectories | 8,000 | 1,600 | 1,600 | structured trajectory SFT rows |

CPU baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Baseline result:

| Specialist | Test accuracy | Test macro F1 | Judgment |
| --- | ---: | ---: | --- |
| router_classifier | 1.0000 | 1.0000 | likely template-easy; needs realistic holdout |
| risk_reviewer | 1.0000 | 1.0000 | likely easy binary schema; needs boundary cases |
| citation_verifier | 0.9000 | 0.8978 | learnable, but synthetic negatives may be easier than real grounding |

Data quality judgment:

- Expanded data is useful for GPU-readiness and end-to-end artifact packaging.
- The split is balanced and learnable, but likely too template-heavy for
  real-world claims.
- Router/risk specialists need external holdouts: real user queries, long
  research traces, high-risk edge cases, and over/under-routing probes.
- Citation verification still needs audited official paragraphs, citation
  spans, partial-support boundaries, and contradictions before claiming
  real grounding quality.

## Golden Specialist Datasets

| Dataset | Rows | Train | Dev | Test | Purpose |
| --- | ---: | ---: | ---: | ---: | --- |
| router_classifier | 344 | 249 | 47 | 48 | choose workflow route |
| risk_reviewer | 181 | 121 | 23 | 37 | detect risk level and gate policy |
| citation_verifier | 166 | 108 | 27 | 31 | classify claim-evidence support |

## Long Research Repair Run

Path:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/long_research_trace_source_quality_repair_25
```

Known contents:

- 25 complete long-research traces,
- 397 source records with raw links and provenance,
- 532 extracted claims,
- 417 citation verifier rows,
- 25 router/risk/memory/memo-quality rows,
- 25 long2short pairs,
- 50 evidence-chain negative regression cases.

## Citation Verifier Repair v0.1

Path:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1
```

Purpose:

Diagnose why the first five-way `citation_verifier` baseline failed and create
scoped repair probes without overwriting the frozen golden data.

Known contents:

- `error_taxonomy.md` and `error_taxonomy.json`,
- `test_error_audit.jsonl`,
- `probe_metrics.json`,
- `repaired_datasets/citation_verifier_url`,
- `repaired_datasets/citation_support_binary`,
- `baselines/citation_repair_probe_v0.1`.

Key result:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy |
| --- | ---: | ---: | ---: |
| original citation_verifier | 0.2581 | 0.1441 | 0.4839 |
| citation_verifier_url | 0.2581 | 0.1390 | 0.4839 |
| citation_support_binary | 0.3871 | 0.3767 | 0.5806 |

Decision:

This repair clarified failure modes but did not make the citation verifier ready
for GPU fine-tuning. Next data work should add hard negatives, cleaner positive
official spans, partial-support boundary cases, and rare negative examples.

## Citation Verifier Repair v0.2

Path:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2
```

Purpose:

Run a train-only targeted augmentation loop based on the v0.1 failure taxonomy.
The original dev/test splits are unchanged, so v0.2 can be compared with v0.1.

Known contents:

- `candidate_generation_pool.jsonl`,
- `manifest.json`,
- `repaired_datasets/citation_verifier_url`,
- `repaired_datasets/citation_support_binary`,
- `baselines/citation_repair_probe_v0.2`.

Selected training strategy:

| Dataset | Train rows | Generated rows used |
| --- | ---: | --- |
| citation_verifier_url | 178 | hard negatives + missing evidence |
| citation_support_binary | 148 | hard negatives only |

Key result:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy |
| --- | ---: | ---: | ---: |
| v0.2 citation_verifier_url | 0.3871 | 0.3333 | 0.4839 |
| v0.2 citation_support_binary | 0.4194 | 0.4139 | 0.5806 |

Decision:

This repair shows that the taxonomy is actionable, but the verifier is still not
GPU-ready. Next data work should use audited real spans rather than more
synthetic flooding.

## Data Boundaries

- X/social/bookmark material is a seed, not truth.
- Official/IR/SEC/press release material can be evidence if captured with URL,
  date, source class, and span.
- Long research traces store short paragraph spans and hashes, not full article
  bodies.
- Runtime memory and offline training corpus stay separate.

## Current Data Quality Judgment

- Router data is good enough for first baseline.
- Risk data is enough for weak baseline, but target design may need adjustment.
- Citation data is not yet good enough for GPU fine-tuning; v0.1 repair shows
  the main gap is data/schema quality, not just model capacity.
- Citation verifier repair v0.2 improves the repair probes, but it still does
  not beat the majority baseline on test accuracy. Continue real-span audit
  before GPU fine-tuning.
- AI expanded v0.1 is large enough to test training plumbing, but its easy
  router/risk metrics mean the next quality step is realistic holdout
  evaluation, not immediate overclaiming.
