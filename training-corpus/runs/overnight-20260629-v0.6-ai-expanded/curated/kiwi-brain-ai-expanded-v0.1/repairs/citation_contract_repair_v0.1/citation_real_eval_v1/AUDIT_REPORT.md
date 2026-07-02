# Citation Real Eval v1 - Audit Report (2026-07-02)

Frozen, audited pack of all 131 real citation span rows (29 from
`real_citation_spans_v0.1` + 102 from `report_and_filing_spans_v0.1`).

## Protocol

Blind double annotation plus adjudication, performed by AI (no human pass):

1. All 131 rows were shuffled into 4 batches; each batch was independently
   relabeled by TWO blind auditor agents that saw only claim, span,
   claim_scope, dates, and source type - never the stored label.
2. Rows where both auditors confirmed the stored label passed (126/131).
3. The remaining 5 rows were adjudicated by the main session by re-reading
   span vs claim against the five-way contract. The adjudicator sided with
   the auditors against the original label in 3 cases, including one where
   the original label was authored in the same session - the blind protocol
   exists precisely to make that override possible.

## Results

| Outcome | Rows |
| --- | ---: |
| Both auditors confirm stored label | 126 |
| Corrected after adjudication | 3 |
| Confirmed after adjudication (split vote / missing vote) | 2 |
| Correction rate | 2.3% |
| Test-split corrections | 0 |

Corrections:

| Row | From | To | Why |
| --- | --- | --- | --- |
| `amd_guidance_partial` (seed, dev) | partial | contradicts | span says ~56% margin, claim says 58%: conflicted subclaim, not absent (C1) |
| `msft10q_rev_verified` (new, train) | verified | partial | 10-Q holds near-identical quarterly/nine-month paragraphs; span cannot verify the "quarterly" binding (C2) |
| `siaq1_trillion_insufficient` (new, dev) | insufficient | contradicts | May span frames $1T as the 2026 trajectory, materially weakening the $1.5T claim (C3); staleness lesson kept in note |

## Conventions pinned by this audit

- **C1 contradiction precedence**: a conflicted subclaim forces `contradicts`;
  `partial_support` is supported-plus-ABSENT, never supported-plus-conflicted.
- **C2 period binding**: single-period source identity may satisfy a period
  binding; in multi-period documents the span itself must establish the
  period, else the row caps at partial/insufficient.
- **C3 materially weakens**: a span implying a lower point/milestone estimate
  contradicts a higher-figure claim under span-only judgment.

Full machine-readable record: `audit/adjudications.json`,
`audit/votes_passA.jsonl`, `audit/votes_passB.jsonl`.

## Freeze rule

`dev` + `test` are the frozen evaluation splits for the three-task ladder
(Act 2). `test` is untouchable. Prompts and experience libraries iterate on
`train`/`dev` only. Any change to dev/test requires a new eval id.

## Known limitations

- This is an AI audit, not a human audit; `audited_by` records that honestly.
- One auditor omitted one row from its output (31/32); that row was confirmed
  by the other auditor and the adjudicator.
- Block extraction loses section headers, which is why C2 exists; a future
  collector version should carry section headers so period bindings become
  span-verifiable.
