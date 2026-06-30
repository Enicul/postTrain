# Long Research Trace Pilot 5

This pilot upgrades KIWI from short tool traces to medium/long research trajectories with memory gates.

## Workflow

```text
memory_read_gate -> plan -> search query 1 -> open page -> read paragraph -> extract claim
-> search query 2 -> open/read/extract again -> search query 3 risk -> compare sources
-> revise thesis -> write memo -> reviewer -> rewrite -> final short answer -> memory_write_gate
```

## Counts

- Traces: 5
- Claims extracted: 96
- Source records: 70 {'not_opened': 26, 'no_readable_paragraphs': 8, 'ok': 24, 'paywall_or_forbidden': 12}
- Pages opened: 44 (24 ok)
- Blockers: 0 {}
- Memory proposals: 5
- Datasets: {'router_classifier': 5, 'citation_verifier': 96, 'risk_reviewer': 5, 'memory_gate': 5, 'long2short_pairs': 5, 'memo_quality_scorer': 5}
- Evidence-chain evals: 5
- Contradiction regression cases: 5
- Evidence-chain negative cases: 10

## Source Link Lineage

`source_registry.jsonl` preserves raw links and review provenance for later audit.

Each source record includes:

- `source_url` and `canonical_url`
- publisher/title/published time when available
- search query, search rank, and snippet
- page access status and content hash
- extracted evidence spans with span hashes

This keeps the training corpus auditable without storing full copyrighted article bodies.

## Long2Short

`datasets/long2short_pairs/all.jsonl` stores internal long research trajectories paired with short user-facing answers.

The short answer keeps conclusion, key evidence, risks, invalidation conditions, next-watch triggers, and source links while hiding raw tool chatter.

## Risk Source Repair

The workflow includes a dedicated third search query for downside, competition, margin, valuation, guidance, and concern signals.

When risk pages are blocked or unreadable, risk-query title/snippet results are preserved as low-confidence `search_snippet_candidate_evidence` with source links.

## Evidence Chain Eval

`evidence_chain_evals.jsonl` scores whether the final answer was earned by the right sources and actions.

The eval checks evidence coverage, citation correctness, answer faithfulness, source quality, conflict handling, risk coverage, look-ahead bias, calculation correctness, and redundant search.

`datasets/memo_quality_scorer/all.jsonl` exports these labels as the first memo-quality scorer dataset.

`regression/evidence_chain_negative_cases.jsonl` contains mutated cases where the final answer remains plausible but citation lineage or timing is wrong.

## Contract Repair

The pilot now treats contradiction handling as a structured memo contract instead of a prose-only reviewer check.

Required fields when support/risk tension appears:

- `support_vs_risk_comparison`
- `contradiction_handling`

The reviewer checks those fields directly, and tension cases are exported to `regression/contradiction_cases.jsonl`.

## Boundary

No runtime DB writes. Memory writes are emitted only as pending proposals requiring user approval.
