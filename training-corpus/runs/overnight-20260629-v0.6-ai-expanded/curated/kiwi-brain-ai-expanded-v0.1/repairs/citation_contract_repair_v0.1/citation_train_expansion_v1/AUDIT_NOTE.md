# Spot-audit note — citation_train_expansion_v1

Date: 2026-07-04
Auditor: Claude (two independent label-blind auditor agents), no human pass.

## What this pack is

A TRAINING-POOL expansion for the data-starved five-way verdict head
(D-2026-07-04-008). 146 construction-labeled rows built from real SEC filings
across the AI vertical (21 issuers, 10-K / 10-Q / 20-F / 8-K), using the same
construction logic as the frozen `citation_real_eval_v1` (keyword-only anchors,
claim/evidence pairing, five-way labels via the C1–C3 conventions, point-in-time
`as_of` / `published_at`, `paragraph_sha256`). The frozen eval (131 rows) was
NOT touched. Splits are `train` (122) and a small label-stratified `dev` (24);
no `test` rows exist in this pack.

Labels carry `provenance.label_provenance = "construction_v1_unaudited"` because
they are construction-derived, not fully human-audited. This note records the
required blind spot-audit over a 10% sample.

## Method

- Sample: 15 rows (10.3% of 146), stratified by label so every verdict class is
  represented (7 verified_support, 4 contradicts, 2 insufficient, 2 partial).
  Selected deterministically (seed 20260704) from `rows/all.jsonl`.
- Blindness: each auditor saw only `claim`, `evidence_span`, `as_of`,
  `source_type` — never the stored label or the label-revealing `case_key`.
  (Sample_ids are opaque hashes per F-2026-07-02-006, so no leak was possible.)
- Two independent passes (agent A and agent B) each re-derived a five-way label
  from the rubric applied fresh. Votes are in `audit/spot_audit_votes.json`;
  the blind input is `audit/spot_audit_blind.json`.
- Rubric given verbatim to both auditors: the five-way contract plus the pinned
  conventions C1 (contradiction precedence), C2 (period binding), C3 (materially
  weakens).

## Result

- Agreement with stored label: **14 / 15 = 93.3%** (auditor A) and
  **14 / 15 = 93.3%** (auditor B).
- Inter-annotator agreement (A vs B): **15 / 15 = 100%**.
- Both-auditors-agree-with-stored (consensus): **14 / 15 = 93.3%**.
- Threshold was 90%. **93.3% ≥ 90% → the pack passes and is committed.**

## The one disagreement, and the correction applied

`x_msft10k_server_vs` (audit_id 1) — MSFT 10-K FY2025 MD&A.
- Claim: "Microsoft's Server products and cloud services revenue increased 23%
  in fiscal 2025, driven by Azure and other cloud services growth of 34%."
- Span: "Server products and cloud services revenue increased 23% driven by
  Azure and other cloud services revenue growth of 34%."
- Stored (pre-audit): `verified_support`. Both blind auditors: `partial_support`.
- Reasoning (both, independently): the span supports the 23%/34% figures but does
  not itself establish the "fiscal 2025" period the claim binds — convention C2
  (period binding). The MD&A block is period-ambiguous on its own.

This is a correct C2 call. The row was **corrected to `partial_support`** and the
pack rebuilt; the rationale field records the correction. Post-correction label
mix: verified_support 70, contradicts 35, partial_support 22, insufficient 19.

## Honesty caveats

- This is an AI-only audit (no human reviewer), consistent with how
  `citation_real_eval_v1` was audited. The 93.3% figure is a same-session,
  two-blind-agent estimate over a 10% stratified sample; it is not a full census.
- The remaining 90% of rows keep `label_provenance = construction_v1_unaudited`.
  A later full audit (or a leak-free re-audit like the one TODO'd for the eval)
  can promote the whole pack; until then these are TRAIN-grade labels, never used
  as an evaluation ground truth.
- The verified_support class was not perfectly balanced with the boundary classes
  by design: real filings state far more clean facts than traps, and the pack's
  contribution over the eval train split is precisely the boundary classes
  (eval train had only 1 contradicts / 1 partial; this pack adds 35 / 22).
