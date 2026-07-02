# Report and Filing Spans v0.1

Second real-source citation span pack under `citation_contract_repair_v0.1`,
following `real_citation_spans_v0.1`. Sources now include SEC filings (10-K,
10-Q, 6-K), earnings call transcript pages, public industry research, and
reputable news, per `docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md`.

## Summary

- Rows: 102
- Sources fetched: 22 / 22
- Failures recorded (scouting + fetch + anchor): 5
- Labels: `{"contradicts": 26, "insufficient": 13, "partial_support": 15, "verified_support": 48}`
- Splits: `{"dev": 31, "test": 25, "train": 46}`
- Source tiers: `{"company_filing": 51, "earnings_transcript": 25, "public_research": 18, "reputable_news": 8}`
- Sanity checks passed: True

## Targets

- `total_rows_gte_100`: yes
- `sec_filing_rows_gte_30`: yes
- `transcript_rows_gte_20`: yes
- `research_news_rows_gte_20`: yes
- `all_four_boundary_labels_present`: yes

## Why

A financial research agent should know whether a claim is supported by a
filing, management commentary, a financial table, public industry research,
or merely a headline. This pack adds those source tiers with exact
claim-support boundaries, including cross-period traps (sequential vs
year-over-year), figure-swap traps (segment vs total), attribution traps,
and stale-forecast traps across sources with different `published_at` dates.

## Source Mix

- `amd_10k_2025` (10-K, AMD): 5 rows
- `amzn_10q_q1_2026` (10-Q, AMZN): 4 rows
- `ap_nvda_china_stall` (news, NVDA): 4 rows
- `ap_samsung_hynix_fabs` (news, MU): 4 rows
- `avgo_10q_fq2_2026` (10-Q, AVGO): 5 rows
- `deloitte_semis_outlook_2026` (public_research, SOX): 5 rows
- `googl_10q_q1_2026` (10-Q, GOOGL): 5 rows
- `meta_10k_2025` (10-K, META): 6 rows
- `msft_10q_fy26q3` (10-Q, MSFT): 5 rows
- `mu_10q_fq3_2026` (10-Q, MU): 6 rows
- `nvda_10k_fy2026` (10-K, NVDA): 6 rows
- `nvda_10q_q1fy27` (10-Q, NVDA): 5 rows
- `sia_ai_rack_report` (public_research, SOX): 4 rows
- `sia_april_2026_sales` (public_research, SOX): 5 rows
- `sia_q1_2026_sales` (public_research, SOX): 4 rows
- `ts_amd_q1_2026` (transcript, AMD): 4 rows
- `ts_amzn_q1_2026` (transcript, AMZN): 4 rows
- `ts_avgo_fq2_2026` (transcript, AVGO): 4 rows
- `ts_googl_q1_2026` (transcript, GOOGL): 4 rows
- `ts_msft_fy26_q3` (transcript, MSFT): 4 rows
- `ts_nvda_q1_fy2027` (transcript, NVDA): 5 rows
- `tsm_6k_may_2026_revenue` (6-K, TSM): 4 rows

## Guardrails Applied

- No raw HTML/PDF dumps stored; only anchored spans plus hashes.
- Paywalled sell-side research was not collected.
- Transcript-tier spans come from a public transcript page; metric bullets
  are the publisher's structured call summary, and the license/section
  fields record that so they are not confused with verbatim speaker text.
- Every row is `requires_human_audit: true`; labels are manual contract
  labels, not model outputs.

## Output Files

- `spans/all.jsonl`: all collected rows.
- `repaired_datasets/citation_verifier/{train,dev,test,all}.jsonl`: baseline-compatible splits.
- `sources.json`: source metadata and fetch hashes.
- `failures.json`: scouting, fetch, and anchor failures.
- `sanity_check.json`: schema/target check results.
- `manifest.json`: reproducibility metadata.

## Decision

This pack, combined with `real_citation_spans_v0.1`, is the candidate input
for `citation_verifier_repair_v0.3`. Before training: run the human/Claude
label audit pass over all rows (every row is flagged `requires_human_audit`)
and run a CPU probe under summary recording. Do not start GPU fine-tuning
from this pack alone.
