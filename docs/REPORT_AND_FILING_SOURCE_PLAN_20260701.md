# Report and Filing Source Plan - 2026-07-01

This document records the next source-expansion checkpoint after
`real_citation_spans_v0.1`.

## Why

The first real citation span seed proved that KIWI can store paragraph-level
evidence with source URLs, source hashes, point-in-time dates, and support
labels. The next step is to move beyond press-release snippets into richer
financial research sources:

- company filings and financial reports;
- earnings call transcripts and prepared remarks;
- investor presentations and financial tables;
- public industry research reports;
- high-quality news paragraphs;
- social/bookmark seeds only as market radar, not truth.

This matters because a financial research agent should not only cite news. It
should know when a claim is supported by a filing, management commentary,
financial table, public industry report, or merely an opinion source.

## Source Tiers

| Tier | Examples | Training use | Storage rule |
| --- | --- | --- | --- |
| Company filings | SEC 10-K, 10-Q, 8-K, XBRL facts | high-confidence facts, risk factors, MD&A, segment data | store URL, section, short span, hash, as_of |
| Company IR | earnings release, financial tables, investor presentation | reported numbers, guidance, management framing | store URL, short span, hash, as_of |
| Earnings transcripts | prepared remarks, analyst Q&A | thesis/risk extraction, contradiction handling | store URL, short span, speaker/section if available |
| Public research | SIA, Deloitte, PwC, McKinsey, public white papers | industry context and macro/sector theses | store URL, short span, license note |
| Reputable news | Reuters/AP/company beat reporting if accessible | event confirmation and third-party context | store URL, short span, publication time |
| Social/X/Weibo/XHS | user bookmarks, selected high-quality commentators | task seeds, market radar, opinion contrast | do not treat as final support without auditable evidence |
| Paywalled sell-side research | Goldman, Morgan Stanley, JPM, Citi, etc. | metadata or user-provided private notes only | do not store full text; do not train on copyrighted report text |

## Data Contract

Each extracted row should follow the citation contract:

```json
{
  "source_url": "...",
  "source_type": "10-Q / 10-K / 8-K / earnings_release / transcript / public_research / news",
  "published_at": "YYYY-MM-DD",
  "as_of": "YYYY-MM-DD",
  "ticker": "MU",
  "section": "Risk Factors / MD&A / Outlook / Analyst Q&A",
  "claim": "...",
  "evidence_span": "...",
  "support_type": "verified_support / partial_support / insufficient / contradicts",
  "source_hash": "...",
  "paragraph_hash": "...",
  "license_note": "public / official / paywalled_do_not_store_full_text"
}
```

## Guardrails

- Do not store full raw reports in Git by default.
- Do not train from paywalled sell-side report text.
- Do not treat social posts as ground truth.
- Preserve point-in-time dates: the row must include `published_at` and `as_of`.
- For filings, prefer section-aware spans over whole-document chunks.
- For transcripts, preserve speaker/section when available.
- For public research PDFs, store short extracted spans and source metadata, not
  entire copyrighted content.

## Next Target

Build the next citation source pack:

```text
report_and_filing_spans_v0.1
```

Minimum target before `citation_verifier_repair_v0.3`:

- at least 100 audited rows total;
- at least 30 SEC filing rows;
- at least 20 earnings transcript / prepared remarks rows;
- at least 20 public research or high-quality news rows;
- balanced boundary labels: `verified_support`, `partial_support`,
  `insufficient`, and `contradicts`;
- capped samples only; no raw HTML/PDF dumps in Git.

## Candidate First Tickers

Use the current AI/semiconductor/mega-cap focus:

```text
MU, NVDA, AMD, MSFT, TSM, AVGO, GOOGL, AMZN, META
```

Start with official filings/IR sources for each ticker before adding public
industry reports.

## Resume Checklist

1. Add a source collector for SEC/company IR/transcript/public research spans.
2. Keep output under `citation_contract_repair_v0.1`.
3. Run schema sanity checks before committing.
4. Record fetch failures and source fallbacks in `FAILURE_LOG.md`.
5. Do not start GPU fine-tuning until the expanded citation pack has passed
   audit and CPU probe evaluation.
