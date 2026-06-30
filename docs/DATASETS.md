# Dataset Inventory

## Current Frozen Data

Path:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1
```

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
- Citation data is not yet good enough for GPU fine-tuning.
