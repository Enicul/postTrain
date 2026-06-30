# long_research_trace_expanded_25

This pilot upgrades KIWI from short tool traces to medium/long research trajectories with memory gates.

## Status

This run is preserved as the first 25-trace expansion and failure-history
artifact. It has been superseded as the preferred training baseline by:

```text
../long_research_trace_source_quality_repair_25
```

Reason:

- this run completed 25/25 traces with 0 blockers
- but 16/25 evidence-chain evals still had `source_quality_weak`
- the repair run adds fixed official source anchors and reduces
  `source_quality_weak` from 16/25 to 0/25

Keep this run for comparison and interview failure attribution. Use the repair
run for first narrow baseline experiments.

## Workflow

```text
memory_read_gate -> plan -> search query 1 -> open page -> read paragraph -> extract claim
-> search query 2 -> open/read/extract again -> search query 3 risk -> compare sources
-> revise thesis -> write memo -> reviewer -> rewrite -> final short answer -> memory_write_gate
```

## Counts

- Traces: 25
- Claims extracted: 433
- Source records: 339 {'not_opened': 128, 'ok': 121, 'paywall_or_forbidden': 39, 'no_readable_paragraphs': 47, 'http_error': 4}
- Pages opened: 211 (121 ok)
- Blockers: 0 {}
- Source warnings: 1 {'broad_search_no_results': 1}
- Memory proposals: 24
- Datasets: {'router_classifier': 25, 'citation_verifier': 433, 'risk_reviewer': 25, 'memory_gate': 25, 'long2short_pairs': 25, 'memo_quality_scorer': 25}
- Evidence-chain evals: 25
- Contradiction regression cases: 25
- Evidence-chain negative cases: 50

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
