# KIWI Post-Training Data Checkpoint

Timestamp: 2026-06-29

## What We Built

This checkpoint turns X/bookmark market narratives into auditable post-training artifacts for KIWI.

Architecture framing:

- `POST_TRAINING_ARCHITECTURE_FRAMING.md`
- Core idea: we are not only using KIWI outputs to train models; we are using post-training logic to make KIWI's agent workflow observable, evaluable, diagnosable, and repairable.

The key boundary is preserved:

```text
X/bookmarks = market narrative and user-language seeds
official/auditable sources = evidence labels
runtime DB = product state
training corpus = frozen offline data
```

## Frozen Golden Source

The strict pilot has been frozen as v0.1:

- 25 verified market-narrative traces
- 74 claim/evidence spans
- 25 router samples
- 74 citation-verifier samples
- 25 risk-reviewer samples

Files:

- `pilot/strict_pilot_trace_25/official_verification_traces.jsonl`
- `pilot/strict_pilot_trace_25/claim_evidence_spans.jsonl`
- `pilot/strict_pilot_trace_25/decisions.md`

## Golden v0.1 Specialist Pack

Path:

```text
kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1
```

Datasets:

| Dataset | Rows | Train | Dev | Test | Purpose |
| --- | ---: | ---: | ---: | ---: | --- |
| router_classifier | 344 | 249 | 47 | 48 | Route fast answer / price / news / calculation / evidence check / deep research / risk review |
| citation_verifier | 166 | 108 | 27 | 31 | Judge claim-evidence support, including mismatch and missing-evidence negatives |
| risk_reviewer | 181 | 121 | 23 | 37 | Detect high-risk investment framing, downgrade behavior, and human-gate cases |

This is enough for:

- baseline classifier experiments
- SFT-style cold-start for narrow specialists
- interview portfolio evidence
- eval harness development

This is not enough for:

- final production post-training
- robust generalization across all market regimes
- replacing deterministic calculators or official-source retrieval

## Real Tool Trace Pilot

Path:

```text
kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/real_tool_trace_pilot_10
```

What ran:

- 10 real research tasks
- 30 real KIWI provider calls
- tools: `market_price_lookup`, `news_search`, `sec_edgar`
- 59 observation spans
- 8 complete traces
- 2 partial traces
- 0 tool-call errors

Partial traces are not hidden:

- `NVDA`: missing relevant news observation in RSS filter
- `SPY`: missing primary source, expected for an ETF/index risk task

This proves we have run an actual read-only agentic research workflow. It does not prove trading execution, and it should not: KIWI is a research copilot, not an auto-trading agent.

## Simulated User Trace Pilot

Path:

```text
kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/user_simulation_trace_pilot_50
```

What ran:

- 50 simulated user inputs
- routes covered: fast answer, price lookup, news retrieval, evidence check, deep research, risk review, clarification needed
- 77 real read-only tool calls
- 159 observation spans
- 50 router samples
- 159 citation-verifier samples
- 50 risk-reviewer samples
- 0 tool-call errors

Main blockers found:

- `registry_tool_suggestion_overbroad`: 15 cases
  - Fast-answer and clarification routes still received broad tool suggestions such as `market_price_lookup`.
  - This is not a runtime crash, but it can cause over-routing and unnecessary tool use if the coordinator blindly follows registry suggestions.

- `missing_news_observation`: 3 cases
  - News provider returned successfully, but relevance filtering left no usable headline for several NVDA tasks.
  - This points to source coverage / relevance filter tuning rather than model failure.

This confirms the next architecture repair target:

```text
coordinator route decision
-> allowed tool set
-> registry suggestion contract
```

Fast-answer and clarification flows should not inherit default market/research tools unless a second policy layer explicitly authorizes them.

## Long Research Trace Pilot

Path:

```text
kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/long_research_trace_pilot_5
```

What ran:

```text
memory_read_gate
-> plan
-> search query 1
-> open page
-> read paragraph
-> extract claim
-> search query 2
-> open/read/extract again
-> search query 3 risk
-> open/read/extract risk evidence
-> extract risk snippet claims
-> source registry
-> compare sources
-> revise thesis
-> write memo
-> reviewer
-> rewrite
-> final short answer
-> memory_write_gate
```

Results:

- 5 long research traces
- 44 pages opened
- 24 pages opened successfully
- 96 claim/evidence spans extracted
- 70 source records with raw links and provenance
- 5 router samples
- 96 citation-verifier samples
- 5 risk-reviewer samples
- 5 memory-gate samples
- 5 long2short samples
- 5 memo-quality/evidence-chain samples
- 5 evidence-chain eval records
- 5 pending memory proposals
- 0 fatal errors
- 5 contradiction regression cases
- 10 evidence-chain negative regression cases

Verdicts:

- `complete`: 5

Source access status:

- `ok`: 24
- `not_opened`: 26
- `paywall_or_forbidden`: 12
- `no_readable_paragraphs`: 8

Architecture repair completed:

- Previous blocker: `contradiction_not_handled` appeared in MU and NVDA traces.
- Root cause: reviewer was checking whether the thesis prose contained a balancing phrase instead of checking a structured memo contract.
- Fix: `compare_sources` now emits `support_vs_risk_comparison`; `revise_thesis` and `write_memo` now emit `contradiction_handling`; reviewer checks those fields directly.
- Regression set: `long_research_trace_pilot_5/regression/contradiction_cases.jsonl`
- Current result: 5 support-vs-risk tension cases, all reviewer-clean.

Schema upgrade completed:

- Added `source_registry.jsonl` to preserve raw source links, canonical URLs, publisher/title/published time, search query, search rank, snippets, access status, content hash, and extracted evidence spans.
- Added `datasets/long2short_pairs/all.jsonl` to pair internal long research trajectories with short user-facing answers.
- The corpus keeps source lineage and short spans/hashes for audit, without storing full copyrighted article bodies.

Risk-source repair completed:

- Previous finding: `risk_omission` appeared in MRVL and VRT.
- Root cause: the trace only had broad recent evidence and official/source confirmation queries; it did not force a downside/risk search path.
- Fix: added `search_query_3_risk` for downside, competition, margin, valuation, guidance, and concern signals.
- Additional fix: when pages are paywalled or unreadable, risk-query headline/snippet results are kept as low-confidence `search_snippet_candidate_evidence` with source links.
- Current result: `risk_omission` is 0 across 5 long traces.

Evidence-chain eval added:

- Added `evidence_chain_evals.jsonl` to score whether the final answer was earned by traceable, timely, source-grounded evidence.
- Added `datasets/memo_quality_scorer/all.jsonl` as the first memo-quality scorer dataset.
- Eval dimensions: evidence coverage, citation correctness, answer faithfulness, source quality, conflict handling, risk coverage, point-in-time/look-ahead safety, calculation correctness, and redundant-search penalty.
- Added `regression/evidence_chain_negative_cases.jsonl` with 10 mutated cases:
  - 5 citation mismatch cases
  - 5 look-ahead bias cases
- Current normal traces are runtime-clean, but evidence-chain eval still flags `source_quality_weak` for MRVL, META, and VRT. This is useful: final answer can be complete while source quality remains an eval target.

Memory behavior:

- Memory read gate runs on every long trace.
- Memory write gate emits only pending proposals, never runtime DB writes.
- During the first run, memory write was too permissive and proposed updates even when reviewer found issues.
- The gate was tightened so memory proposals require reviewer-clean traces and still require user approval.

## Expanded Long Research Trace Run

Path:

```text
kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/long_research_trace_expanded_25
```

Why we ran this:

- The 5-trace pilot proved the schema, but was still too small for an interview-grade portfolio artifact.
- We expanded to 25 AI / semiconductor / cloud-infrastructure names to test whether the same harness survives broader ticker coverage.
- The goal was not to simulate trading execution; it was to generate real long research episodes with search, source links, evidence spans, support/risk comparison, reviewer feedback, rewrite, long2short output, and memory-write gating.

Tickers covered:

```text
MU, NVDA, MRVL, META, VRT, AMD, TSM, AVGO, MSFT, GOOGL, AMZN, AAPL, TSLA,
PLTR, SMCI, ARM, ASML, AMAT, LRCX, KLAC, ANET, DELL, ORCL, SNDK, CRWV
```

Results:

- 25 long research traces
- 25 complete verdicts
- 0 blockers
- 1 source warning: `AMZN` had `broad_search_no_results`, but official/risk searches still returned usable evidence
- 339 source records with raw links and provenance
- 211 opened pages
- 121 successfully readable pages
- 433 citation-verifier rows
- 25 router rows
- 25 risk-reviewer rows
- 25 memory-gate rows
- 25 memo-quality/evidence-chain rows
- 25 long2short pairs
- 25 contradiction regression cases
- 50 evidence-chain negative cases
- 24 pending memory proposals

What the scale-up exposed:

- Official-source classification was initially too narrow for the expanded ticker universe.
  - ASML and other non-US / infrastructure names need their own IR and company domains in `source_class`.
  - Fix: expanded the official-domain allowlist to cover the 25-stock AI supply-chain universe.

- `search1_no_results` was too severe as a blocker.
  - A broad/news query can fail while official-source and risk-source queries still return enough evidence.
  - Fix: broad, official, and risk query misses are now `source_warnings`; only `all_searches_no_results` becomes a high-severity blocker.

- Evidence-chain quality still has room to improve.
  - Normal traces are complete, but 16/25 evidence-chain evals still flag `source_quality_weak`.
  - This is useful signal, not a hidden failure: next curation should add more official paragraph spans, SEC / IR / press release excerpts, and earnings-transcript spans.

## Source Quality Repair Run

Path:

```text
kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/long_research_trace_source_quality_repair_25
```

Why we ran this:

- The expanded 25-trace run was complete, but 16/25 traces still had `source_quality_weak`.
- The issue was not that the memos had no evidence; it was that search did not reliably retrieve enough primary / official / reputable sources for every ticker.
- Real analyst workflow should not depend only on search ranking. It should also check known official anchors directly.

Harness repair:

- Added `OFFICIAL_SOURCE_URLS` for the 25-stock AI supply-chain universe.
- Added a new episode step:

```text
open_official_sources
-> read_official_paragraphs
-> extract_official_claims
```

- Each ticker now opens fixed anchors such as SEC browse pages, investor-relations homepages, quarterly-results pages, press-release hubs, or company financial-result pages.
- Official pages that are blocked, dynamic, or unreadable are preserved as source records and warnings instead of being silently dropped.

Results:

- 25 long research traces
- 25 complete verdicts
- 0 blockers
- `source_quality_weak`: 16/25 -> 0/25
- evidence-chain score mean: 0.954 -> 0.999
- evidence-chain score min: 0.889 -> 0.993
- source records: 339 -> 397
- extracted claims: 433 -> 532
- readable opened pages: 121 -> 143
- citation-verifier rows: 433 -> 417
- source warnings: 1 -> 8

Remaining source warnings:

- `broad_search_no_results`: 2
- `official_seed_no_readable_pages`: 6

Interpretation:

- The warnings are useful provenance, not failure. They tell us which official pages are blocked, dynamic, or hard to parse.
- The repair succeeded because the evidence-chain evaluator no longer flags source quality weakness while still preserving retrieval and access imperfections for future debugging.

## Router Baseline v0.1

Path:

```text
kiwi/training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/router_classifier_tfidf_v0.1
```

Why we ran this:

- After repairing source quality, the next question was whether Kiwi's coordinator/router can be trained and evaluated as a narrow specialist.
- The repaired long-research router set alone is not a good training set because all 25 rows are `deep_research`.
- Therefore the baseline trains on the 344-row multi-route `golden_v0.1/datasets/router_classifier` split and uses the repaired long-research set as a regression holdout.

Model:

```text
TF-IDF character n-grams
-> balanced logistic regression
```

Feature hygiene:

- The model uses user query, profile, page/source context, detected tickers, and narrative tags.
- It does not use label-derived `required_tools`, because that would leak the answer.

Results:

- train rows: 249
- dev rows: 47
- test rows: 48
- repaired long-research holdout rows: 25
- majority baseline test accuracy: 0.3542
- router test accuracy: 0.9167
- router test macro F1: 0.9368
- test over-trigger rate: 0.0
- test under-trigger rate: 0.0
- test safety recall: 1.0
- repaired long-research holdout accuracy: 0.64

What it exposed:

- The main test split is strong enough for a first eval baseline.
- The repaired long-research holdout is weaker: 9/25 deep-research rows were predicted as `evidence_check` or `financial_calculation`.
- This is not a fatal issue, but it is the next router repair target: Kiwi needs more boundary cases that teach the difference between verifying a claim and running full multi-source investment research.

## Iteration Errors We Caught

1. Risk export initially used list/set intersection incorrectly.
   - Fixed by keeping set logic for `requires_human_gate`.

2. Risk reviewer initially exported only severe examples.
   - Fixed by exporting all 25 traces with low/medium/high labels.

3. Golden freeze initially copied multiple `all.jsonl` inputs to the same filename.
   - Fixed by using relative-path-based freeze filenames.

4. Golden regeneration initially risked deleting child pilots.
   - Fixed by clearing only managed outputs and preserving child pilot directories.

5. User simulation exposed a tool-registry contract issue.
   - `fast_answer` and `clarification_needed` can still receive overbroad read-only tool suggestions.
   - This should become a harness repair before scaling the simulation much further.

6. Long research pilot exposed memory write policy risk.
   - Initial memory-write gate proposed updates even for reviewer-flagged traces.
   - Fixed by requiring zero reviewer issues before emitting a pending memory proposal.

7. Long research pilot exposed contradiction-handling weakness.
   - MU and NVDA traces exposed that contradiction handling was being judged by fragile thesis wording.
   - Fixed by adding `support_vs_risk_comparison` and `contradiction_handling` as structured memo fields.
   - Added `regression/contradiction_cases.jsonl` so support-vs-risk tension stays testable after future harness edits.

8. Long research v0.2 exposed risk-evidence coverage gaps.
   - After adding source lineage and long2short outputs, MRVL and VRT traces still lacked enough explicit risk evidence.
   - This is now visible as `risk_omission` instead of being hidden inside a polished final answer.
   - Fixed by adding `search_query_3_risk`, risk-page reads, and risk-snippet fallback evidence.
   - The repair increased citation-verifier examples from 47 to 96 and source records from 47 to 70.

9. Kimi-Researcher framing clarified evidence-chain reward.
   - A research answer can look correct while the evidence chain is wrong.
   - KIWI evals should not only score final answer quality; they should score evidence coverage, citation correctness, answer faithfulness, source quality, conflict handling, calculation correctness, point-in-time leakage, redundant search, and risk coverage.
   - This supports the current source-registry and long trajectory design: final answer reward checks usefulness, while evidence-chain reward checks whether the answer was earned by correct sources and actions.

10. Evidence-chain eval became an explicit dataset.
   - Added `evidence_chain_eval` as a trace step.
   - Added `memo_quality_scorer` labels from evidence-chain scores.
   - Added negative regression cases where the final answer stays plausible but citation lineage or timing is corrupted.
   - This is why we preserve source URLs, span IDs, hashes, and as-of timestamps instead of only storing final answers.

11. Expanded long-research run exposed official-source classifier coverage gaps.
   - Scaling from 5 to 25 tickers surfaced that some official investor-relations domains were not recognized as primary/official sources.
   - Fixed by expanding the official-domain allowlist for AI, semiconductor, cloud, networking, equipment, and storage names.

12. Expanded long-research run exposed blocker severity drift.
   - `search1_no_results` was initially treated as fatal even when later official/risk searches had enough evidence.
   - Fixed by separating retrieval warnings from true blockers.
   - Current rule: individual search misses become `source_warnings`; only total source failure becomes a high-severity blocker.

13. Source-quality repair exposed search-ranking fragility.
   - Search alone did not consistently retrieve enough official / primary / reputable sources.
   - Fixed by adding direct official source anchors as a first-class environment action.
   - This reduced `source_quality_weak` from 16/25 to 0/25 without hiding page-access warnings.

14. Router baseline initially had a feature leakage risk.
   - The first script draft included `required_tools` in the text features.
   - `required_tools` is part of the label, so it was removed before reporting metrics.
   - The final baseline excludes label-derived tool lists.

15. Router baseline exposed the `evidence_check` vs `deep_research` boundary.
   - Test accuracy is 0.9167, but repaired long-research holdout accuracy is 0.64.
   - Most holdout mistakes route full investment-research questions to `evidence_check`.
   - This becomes the next coordinator data target.

These are useful interview material because they show real data-pipeline debugging and curation decisions.

## What To Do Next

Priority order:

1. Turn the offline corpus into runtime harness checks.
   - Add or wire the plan in `kiwi/docs/runtime-harness-refinement.md`.
   - KIWI should not depend on manual reminders to run checks, inspect source
     quality, or generate memory proposals.
   - The first runtime loops should be: guardian heartbeat, source-quality
     audit, router-safety regression, evidence-chain regression, and daily
     memory proposal digest.
   - The boundary remains strict: read-only checks can run automatically;
     memory writes stay pending until user approval; financial actions are
     never automatic.

2. Add router boundary data for `evidence_check` vs `deep_research`.
   - Use the 9 repaired long-research holdout mistakes as seed cases.
   - Add examples where a claim needs citation checking but not full research.
   - Add examples where a medium-risk investment thesis needs full multi-source research.

3. Train the next narrow baseline: `risk_reviewer`.

4. Audit official-source warnings.
   - AVGO, TSLA, ARM, AMAT, DELL, and SNDK had `official_seed_no_readable_pages`.
   - Decide whether to add alternative official pages, API/file sources, or browser-rendered fetch for those cases.

5. Expand real tool traces from 10 to 30-50.
   - Keep read-only provider calls.
   - Record every source failure, empty result, and partial trace.

6. Repair coordinator/tool-registry contract.
   - Separate route label from optional fallback tool suggestions.
   - Ensure fast-answer and clarification paths do not over-trigger market/research tools.

7. Expand long-research regression coverage.
   - Keep `contradiction_handling` as a fixed memo contract.
   - Add more cases where support and risk evidence conflict across official filings, news, and social narratives.
   - Add failure examples where contradiction handling is intentionally missing, so the reviewer has negative cases too.
   - Preserve old `risk_omission` examples as negative reviewer cases.
   - Add evidence-chain negative cases where the final answer looks plausible but citations, timing, or source support are wrong.
   - Preserve old `source_quality_weak` cases from `long_research_trace_expanded_25` as regression examples, and use the repair run to test that official-source anchors prevent the same failure.

8. Audit synthetic data.
   - Sample with Claude/human review.
   - Remove unrealistic user queries and over-clean template rows.

9. Do not train calculation verifier yet.
   - Calculations should be code/rule verified before model training is considered.
