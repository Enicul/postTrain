# KIWI X Bookmark Golden Pack v0.1

This pack freezes the 25-record strict verification pilot and adds deterministic bootstrap data for KIWI's first trainable small specialists.

Latest long-research baseline:

```text
long_research_trace_source_quality_repair_25
```

This run supersedes `long_research_trace_expanded_25` as the preferred long-research corpus because it adds fixed official source anchors and removes the source-quality weakness found in the first 25-trace expansion.

## What Each Dataset Trains

- `router_classifier`: decide fast answer, price lookup, news retrieval, financial calculation, evidence check, deep research, risk review, or clarification.
- `citation_verifier`: classify whether an evidence span supports a market claim.
- `risk_reviewer`: detect unsafe or low-evidence investment framing and decide downgrade/human-gate behavior.

## Counts

- `router_classifier`: 344 rows; splits {'train': 249, 'dev': 47, 'test': 48}; synthetic {'False': 136, 'True': 208}
- `citation_verifier`: 166 rows; splits {'train': 108, 'dev': 27, 'test': 31}; synthetic {'False': 74, 'True': 92}
- `risk_reviewer`: 181 rows; splits {'train': 121, 'dev': 23, 'test': 37}; synthetic {'False': 25, 'True': 156}

Long-research repair run:

- 25 complete long research traces
- 397 source records with raw links and provenance
- 532 extracted claims
- 417 citation-verifier rows
- 25 router / risk-reviewer / memory-gate / memo-quality rows
- 25 long2short pairs
- 50 evidence-chain negative regression cases
- `source_quality_weak`: 16/25 -> 0/25
- blockers: 0

## First Baseline

Router baseline:

```text
baselines/router_classifier_tfidf_v0.1
```

Model:

```text
TF-IDF char n-grams + balanced logistic regression
```

Training setup:

- Train/dev/test: `datasets/router_classifier`
- Repaired long-research router rows: regression holdout only
- Label-derived `required_tools` are excluded from input features to avoid leakage

Results:

- test route accuracy: 0.9167
- test macro F1: 0.9368
- majority baseline test accuracy: 0.3542
- test over-trigger rate: 0.0
- test under-trigger rate: 0.0
- test safety recall: 1.0
- repaired long-research holdout accuracy: 0.64

Interpretation:

- The router baseline is strong enough to serve as an eval reference.
- The repaired long-research holdout reveals the main remaining weakness:
  medium-risk investment research prompts can be confused with `evidence_check`
  instead of full `deep_research`.

## Boundary

X/bookmark data is a narrative sensor. It is never citation truth unless a separate official/auditable evidence span supports the claim.

## Next Step

Continue narrow baselines and router repair:

1. Add more boundary cases for `evidence_check` vs `deep_research`.
2. Train `risk_reviewer`.
3. Train `citation_verifier` after a small audit of official-source anchors and warning cases.

Keep `calculation_verifier` deterministic for now; do not train it as a model until a separate calculation task family requires it.
