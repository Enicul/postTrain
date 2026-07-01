# Real Citation Spans v0.1

This collection adds real paragraph/list/table-cell spans under
`citation_contract_repair_v0.1`. It is a small data-quality pass, not a
training run.

## Summary

- Rows: 29
- Sources fetched: 5 / 5
- Fetch or anchor failures: 0
- Labels: `{"contradicts": 4, "insufficient": 4, "partial_support": 6, "verified_support": 15}`
- Splits: `{"dev": 7, "test": 6, "train": 16}`

## Why

The previous citation data often treated topical evidence as if it were exact
support. This pack forces the verifier to distinguish exact support from
partial, insufficient, and contradictory spans.

## Source Mix

- `amd_q1_2026_8k` (sec_filing, AMD): 2 rows
- `amd_q1_2026_press` (press_release, AMD): 7 rows
- `msft_fy26_q3_press` (press_release, MSFT): 7 rows
- `mu_fq3_2026_press` (press_release_wire, MU): 6 rows
- `nvda_fq1_2027_news` (official_news, NVDA): 7 rows

## Output Files

- `spans/all.jsonl`: all collected rows.
- `repaired_datasets/citation_verifier/{train,dev,test,all}.jsonl`: baseline-compatible splits.
- `sources.json`: source metadata and fetch hashes.
- `failures.json`: fetch/anchor failures, if any.
- `manifest.json`: reproducibility metadata.

## Decision

Do not train `citation_verifier_repair_v0.3` from this pack alone. Use it as
the first official-source span seed, then expand with more paragraph spans
from filings, transcripts, IR releases, and high-quality news.
