# long_research_trace_source_quality_smoke_1

This pilot upgrades KIWI from short tool traces to medium/long research trajectories with memory gates.

## Workflow

```text
memory_read_gate -> plan -> search query 1 -> open page -> read paragraph -> extract claim
-> search query 2 -> open/read/extract again -> open official source anchors
-> read/extract official paragraphs -> search query 3 risk -> compare sources
-> revise thesis -> write memo -> reviewer -> rewrite -> final short answer -> memory_write_gate
```

## Counts

- Traces: 1
- Claims extracted: 29
- Source records: 17 {'http_error': 1, 'ok': 7, 'not_opened': 6, 'paywall_or_forbidden': 3}
- Pages opened: 9 (7 ok)
- Blockers: 0 {}
- Source warnings: 0 {}
- Memory proposals: 1
- Datasets: {'router_classifier': 1, 'citation_verifier': 24, 'risk_reviewer': 1, 'memory_gate': 1, 'long2short_pairs': 1, 'memo_quality_scorer': 1}
- Evidence-chain evals: 1
- Contradiction regression cases: 1
- Evidence-chain negative cases: 2

## Source Link Lineage

`source_registry.jsonl` preserves raw links and review provenance for later audit.

Each source record includes:

- `source_url` and `canonical_url`
- publisher/title/published time when available
- search query, search rank, and snippet
- page access status and content hash
- extracted evidence spans with span hashes

This keeps the training corpus auditable without storing full copyrighted article bodies.

## Official Source Anchors

The workflow opens fixed official anchors for each ticker, such as SEC browse pages, investor-relations homepages, and quarterly-results or press-release hubs.

This is a source-quality repair: search may miss primary pages, but analyst-style research should still check known official sources directly.

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
