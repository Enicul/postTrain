# Failure Log

Failures are first-class evidence. Record them instead of hiding them.

## F-2026-06-30-014 - Old artifact protocol could overload local machine

Symptom:

The old experiment protocol encouraged keeping `events.jsonl`, full
`predictions_*.jsonl`, full `errors.jsonl`, metrics, models, and README files for
every run. This is manageable for tiny CPU baselines but becomes risky once data
expands into large trajectory and holdout sets.

Cause:

We treated every row-level output as a default local/Git artifact instead of
separating resumability evidence from heavy analysis dumps.

Change:

Added `docs/RECORDING_PROTOCOL.md` and changed the baseline/evaluation scripts
to default to summary-first recording with capped prediction/error samples.
Full row-level outputs now require explicit `--record-mode full`.

Effect:

Future runs preserve checkpoint, metrics, failure samples, and decision evidence
without writing full prediction dumps by default.

Remaining risk:

Older run directories still contain full row-level files and old READMEs. Treat
them as historical artifacts; do not copy that pattern into new runs.

## F-2026-06-30-015 - Router repair first pass overgeneralized real tool traces

Symptom:

`router_contract_repair_v0.1` improved real tool trace accuracy from 0.0 to 0.5,
but predicted every real tool trace as `deep_research`.

Cause:

Only a few real-tool-style `evidence_check` and `risk_review` examples were
present in train. The classifier learned that the real-tool trace context itself
mostly implied `deep_research`.

Change:

Generated `router_contract_repair_v0.1b` with more real-tool-style
`evidence_check` and `risk_review` boundary rows.

Effect:

The model overcorrected: real tool trace accuracy remained 0.5, but predictions
shifted toward `evidence_check` and `risk_review`.

Status:

Fixed in v0.1c by adding real-tool-style `deep_research` positive rows for
memo/thesis/SEC filings/capex/FCF/risk synthesis prompts.

## F-2026-06-30-016 - Router repair canonical run id typo

Symptom:

The first router repair probe used:

```text
router_contract_repair_probe_v0.1_20260630Tsummary
```

Cause:

The run id was manually typed instead of generated with a real UTC timestamp.

Change:

Reran the same v0.1 probe with:

```text
router_contract_repair_probe_v0.1_20260630T142954Z
```

Effect:

The non-canonical run is preserved as process evidence, but the timestamped run
is used for reporting.

Status:

Fixed.

## F-2026-07-01-001 - Citation span collection split labels were passed positionally

Symptom:

The first `real_citation_spans_v0.1` run created valid rows but the split
distribution ignored the intended per-case `train/dev/test` assignments.

Cause:

`SpanCase` defines `point_in_time_allowed` before `split`. The first case list
passed `"train"`, `"dev"`, and `"test"` as positional arguments, so those string
values were assigned to `point_in_time_allowed` instead of `split`.

Change:

Updated every case to use explicit `split="train"`, `split="dev"`, or
`split="test"`.

Effect:

The final collection now has the intended split distribution:

```text
train: 16
dev: 7
test: 6
```

Status:

Fixed.

## F-2026-07-01-002 - Real source collection exposed fetch and DOM extractor gaps

Symptom:

The first real citation span collection produced 21 rows and 9 failures. Micron
IR timed out under scripted fetch, and the AMD 8-K anchor was not found.

Cause:

- The Micron IR page was unstable for scripted collection.
- The initial HTML extractor only read paragraph/list/table cells; the AMD 8-K
  section text was inside `div/span` nodes.

Change:

- Added fetch retries.
- Added `div` and `span` to the block extractor.
- Switched the Micron source to the issuer press-release mirror on GlobeNewswire
  and recorded that fallback in source provenance.

Effect:

The final run collected 29 rows from 5 sources with 0 final fetch/anchor
failures.

Status:

Fixed, with remaining source-quality caveat: Micron rows are from a
press-release wire mirror rather than the unstable IR page.

## F-2026-06-30-017 - Social bookmark long claims still sometimes downgrade to fast_answer

Symptom:

In `router_contract_repair_v0.1c`, real tool trace routing is fixed, but
`golden_v0.1_router_all` still has social/bookmark rows where long market
narratives asking for evidence verification are predicted as `fast_answer`.

Cause:

The v0.1c repair focused on real-tool-style boundaries. It did not yet add enough
social/bookmark-specific long-claim boundary rows.

Change:

Not repaired yet.

Effect:

`golden_v0.1_router_all` improved from 0.3023 to 0.8895, but under-trigger rate
remains 0.1325.

Status:

Open. Next repair should be `router_social_boundary_repair_v0.1`.

## F-2026-06-30-018 - Router social repair regressed one real-tool deep research row

Symptom:

`router_social_boundary_repair_v0.1` improved the golden router holdout from
0.8895 to 0.9012, but real tool trace routing dropped from 1.0 to 0.9.

The remaining real-tool error:

```text
GOOGL AI capex 相关判断需要哪些来源支持？
expected: deep_research
predicted: evidence_check
```

Cause:

Adding social/bookmark evidence-check examples strengthened the model's tendency
to treat "needs source support" phrasing as `evidence_check`, even when the query
is asking for capex/thesis judgment that should remain `deep_research`.

Change:

Not fixed yet. The social repair is kept as a candidate rather than replacing
the canonical router checkpoint.

Status:

Open. If router work resumes, add forced train anchors for real-tool-style
capex/source-support deep research before adopting social repair as canonical.

## F-2026-06-30-019 - Risk contract v0.1 fixed schema but failed real medium transfer

Symptom:

`risk_contract_repair_v0.1` added the `medium` label and achieved strong internal
metrics:

```text
internal test accuracy: 0.9928
internal test macro F1: 0.9073
medium recall on internal test: 16/16
```

But realistic holdouts failed:

```text
golden_v0.1_risk_all: accuracy 0.3923, macro F1 0.3349, medium recall 0/69
long_research_repair_25_risk_all: accuracy 0.0000, macro F1 0.0000, medium recall 0/25
```

Cause:

The synthetic medium rows taught short, explicit risk-review phrasing. The real
holdouts express medium risk through long research memo structure, partial
support, missing risk coverage, and user-decision nuance. The model learned the
new label exists but not the real phrasing distribution.

Change:

Recorded `risk_contract_repair_v0.1` as a useful failed checkpoint and updated
the TODO to build `risk_contract_repair_v0.1b` from real long-research
medium-risk rows.

Effect:

We now have evidence for the interview story: adding a label schema is not
enough; post-training data must cover the real trajectory language where the
verifier will be used.

Status:

Open. Do not start GPU fine-tuning from risk v0.1.

## F-2026-06-30-001 - Python 3.9 `datetime.UTC` import failure

Symptom:

```text
ImportError: cannot import name 'UTC' from 'datetime'
```

Cause:

The initial baseline script used `datetime.UTC`, which is unavailable in the
macOS system Python 3.9 runtime.

Change:

Replaced it with `datetime.now(timezone.utc)`.

Effect:

The script compiles and runs under Python 3.9.

Status:

Fixed.

## F-2026-06-30-012 - Holdout evaluator event payload collided with logger argument

Symptom:

```text
TypeError: append_event() got multiple values for argument 'path'
```

Cause:

`evaluate_baseline_holdouts.py` reused `path` as an event payload key, while
`append_event()` already takes the log file path as its first positional
argument.

Change:

Renamed the event payload field from `path` to `source_path`.

Effect:

The same run id `realistic_holdout_eval_v0.1_20260630T083000Z` was rerun
successfully. The failed event remains in `events.jsonl`, preserving the
debugging trail.

Status:

Fixed.

## F-2026-06-30-013 - Expanded baselines collapsed on realistic holdouts

Symptom:

Expanded split metrics were high:

```text
router_classifier test accuracy: 1.0000
risk_reviewer test accuracy: 1.0000
citation_verifier test accuracy: 0.9000
```

But realistic holdout eval showed:

```text
golden_v0.1_router_all accuracy_all_rows: 0.3023
golden_v0.1_risk_all accuracy_all_rows: 0.2762
golden_v0.1_citation_all accuracy_all_rows: 0.4819
long_research_repair_25_router_all accuracy_all_rows: 0.4800
real_tool_trace_pilot_10_router accuracy_all_rows: 0.0000
```

Likely cause:

The expanded split is learnable but too easy/template-heavy. It also uses a
narrower label contract than the older realistic data:

- router lacks `risk_review` and `clarification_needed`;
- risk lacks `medium`;
- citation lacks `partial_support`, `insufficient`, `contradicts`,
  `candidate_evidence`, and `search_snippet_candidate_evidence`;
- real tool trace router prompts were often predicted as
  `financial_calculation`, suggesting a shortcut rather than robust routing.

Change:

Added `evaluate_baseline_holdouts.py` to expose all-row accuracy,
seen-label-only accuracy, schema gaps, and row-level error files.

Effect:

This blocked immediate GPU fine-tuning and created a concrete repair plan:
build router/risk/citation contract repair data before SFT/DPO/GRPO.

Status:

Open.

## F-2026-06-30-010 - Expanded baseline first run used placeholder timestamp

Symptom:

The first expanded-data baseline run completed successfully, but its run id used
a placeholder timestamp:

```text
specialist_cpu_ai_expanded_v0.1_20260630T000000Z
```

Cause:

The command was launched with a manually typed placeholder run id instead of a
real UTC timestamp.

Change:

Reran the same baseline with a canonical timestamped run id:

```text
specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Effect:

The canonical run completed and is the one referenced in progress docs and
experiment logs. The placeholder run should be treated as a superseded duplicate
and not used as the resume point.

Status:

Fixed; canonical run recorded.

## F-2026-06-30-011 - Expanded baseline scores are probably template-easy

Symptom:

The expanded CPU baseline reported perfect held-out accuracy for
`router_classifier` and `risk_reviewer`:

```text
router_classifier test accuracy / macro F1: 1.0000 / 1.0000
risk_reviewer test accuracy / macro F1: 1.0000 / 1.0000
```

Cause:

The expanded checkpoint is balanced and heavily template/synthetic. The split is
chronological, but many labels are recoverable from highly regular query/memo
patterns. This makes it useful for pipeline validation but not enough to prove
realistic generalization.

Change:

Recorded the result as an easy-distribution baseline rather than a final model
quality claim. The next step is to add realistic holdout evaluation from real
tool traces, long-research traces, and harder boundary examples.

Effect:

The expanded baseline is useful as a GPU-readiness sanity check, while the
interview story remains honest: high synthetic performance must be tested
against harder, provenance-rich holdouts.

Status:

Open until external holdout evaluation is added.

## F-2026-06-30-009 - All v0.2 generated citation rows hurt binary support

Symptom:

The first v0.2 repair attempt used every generated row in both repaired
datasets. It improved the five-way probe's macro F1 versus v0.1, but it made the
binary `some_support` / `no_support` probe worse:

```text
all generated rows binary test: accuracy 0.3548, macro F1 0.3376
v0.1 binary test: accuracy 0.3871, macro F1 0.3767
```

Cause:

The generated pool mixed several purposes: atomic positive rows, hard negatives,
missing-evidence insufficient rows, and partial-support upsampling. That volume
helped expose five-way boundaries but flooded the binary training split with
synthetic boundary cases and weakened the cleaner support/no-support decision.

Change:

Ran a local ablation and selected different train-only augmentation policies:

```text
citation_verifier_url = original + hard_negative_cross_trace_overlap + missing_evidence_insufficient
citation_support_binary = original + hard_negative_cross_trace_overlap
```

Effect:

The selected strategy recovered and improved both repair probes:

```text
v0.2 citation_verifier_url test: accuracy 0.3871, macro F1 0.3333
v0.2 citation_support_binary test: accuracy 0.4194, macro F1 0.4139
```

Status:

Fixed in `citation_verifier_repair_v0.2`, but the broader citation verifier
still needs real audited spans before GPU fine-tuning.

## F-2026-06-30-002 - Event logger keyword collision

Symptom:

```text
TypeError: append_event() got multiple values for argument 'path'
```

Cause:

The event logger's first argument was named `path`, and the code also passed an
event field named `path`.

Change:

Renamed the event field to `file_path`.

Effect:

The run completed and preserved a clean `events.jsonl` trail.

Status:

Fixed.

## F-2026-06-30-003 - Citation verifier baseline failed on held-out data

Symptom:

`citation_verifier` test accuracy was `0.2581` and macro F1 was `0.1441`.

Likely cause:

The task is harder than the current feature/data setup. Labels include
`supports`, `partial_support`, `not_supported`, `contradicts`, and
`insufficient`; short TF-IDF features do not capture enough claim-evidence
semantics, and the golden citation set still needs span/label audit.

Change:

Generated `citation_verifier_repair_v0.1`, including an error taxonomy,
row-level audit file, repaired dataset variants, and a repair probe baseline.
The repair probe showed that source URL/domain alone does not fix the five-way
task, and a binary support schema is clearer but still weak.

Effect:

This failure created the next task: add more hard negatives, clean positive
official spans, partial-support spans, and rare negative examples before GPU
fine-tuning.

Status:

Open.

## F-2026-06-30-004 - Router long-research boundary gap

Symptom:

Previous router baseline performed well on test but only reached `0.64` accuracy
on repaired long-research holdout.

Likely cause:

Medium-risk investment research prompts can be confused with `evidence_check`
instead of full `deep_research`.

Change:

Not repaired in this repo yet.

Status:

Open.

## F-2026-06-30-005 - HTTPS GitHub push could not read username

Symptom:

```text
fatal: could not read Username for 'https://github.com': Device not configured
```

Cause:

The new clone initially used the HTTPS remote, but this local environment does
not have an interactive GitHub HTTPS credential flow available.

Change:

Changed the remote to SSH:

```bash
git remote set-url origin git@github.com:Enicul/postTrain.git
```

Effect:

`git push -u origin main` succeeded and `main` now tracks `origin/main`.

Status:

Fixed.

## F-2026-06-30-006 - One-off metric summary assumed wrong schema

Symptom:

```text
KeyError: 'splits'
```

Cause:

The training run completed, but the first ad hoc inspection script assumed
`metrics.json` had a top-level per-dataset `splits` key. The baseline artifact
stores split-level row information in prediction files and detailed metrics,
not in that key.

Change:

The inspection was rerun using row counts from
`predictions_train.jsonl`, `predictions_dev.jsonl`, and
`predictions_test.jsonl`.

Effect:

The run summary was recovered without changing training code or artifacts.

Status:

Fixed.

## F-2026-06-30-007 - Ad hoc source-domain probe did not stringify URLs

Symptom:

```text
TypeError: a bytes-like object is required, not 'str'
```

Cause:

A scratch source-domain probe assumed every `source_url` value would behave like
a normal string before URL parsing and domain normalization.

Change:

The formal `repair_citation_verifier.py` script uses `str(url or "")` before
calling `urlparse`.

Effect:

The repair builder handles missing or non-string URL values robustly.

Status:

Fixed.

## F-2026-06-30-008 - Scratch source URL probe leaked missingness as `None`

Symptom:

A scratch probe suggested that adding `source_url` improved five-way citation
test accuracy much more than the formal repair pack later showed.

Cause:

The scratch text builder rendered missing URLs as the literal token `None`.
That gave the classifier an unintended missing-evidence feature and overstated
the effect of source URL features.

Change:

`repair_citation_verifier.py` normalizes missing source URLs to empty strings
and records a separate leakage probe for `trace_id`, which remains
diagnostic-only.

Effect:

The honest repair result is weaker but more reliable:
`citation_verifier_url` stayed at `0.2581` test accuracy and `0.1390` macro F1.

Status:

Fixed.

## F-2026-07-02-001 - Several planned report/transcript sources were not scriptably reachable

Symptom:

During source scouting for `report_and_filing_spans_v0.1`: Gartner newsroom
returned 403, an IDC press-release URL returned 404, fool.com transcript
archive pagination returned the same first page for every page number, and
DuckDuckGo HTML search returned bot-challenge pages instead of results. No
Micron FQ3 2026 transcript was present in fool.com monthly sitemaps.

Cause:

Bot protection and dynamic pagination on commercial research/news properties;
the Micron transcript simply had not been published to the sitemap yet.

Change:

- Dropped Gartner and IDC rather than trying to evade bot protection.
- Enumerated fool.com monthly sitemaps (2026/04-2026/07) to locate the six
  large-cap transcripts.
- Covered Micron through its freshly filed 10-Q instead of a transcript.
- Recorded all scouting failures in the pack's `failures.json` so the artifact
  itself carries the fallback evidence.

Effect:

Final run fetched 22/22 sources with 0 fetch or anchor failures.

Remaining risk:

Transcript-tier coverage depends on one publisher (fool.com). Metric bullets
there are the publisher's structured call summaries, not verbatim speaker
text; rows record this in `license_note`/`section`, and a future pass should
add issuer prepared-remarks PDFs as a second transcript source.

## F-2026-07-02-002 - Anchor matched a duplicated filing paragraph missing the labeled fact

Symptom:

In the first `report_and_filing_spans_v0.1` run, the NVDA H20 partial-support
case anchored on the $4.5 billion charge sentence. That sentence appears twice
in the 10-K (risk factors and MD&A). First-match anchoring picked the risk
factor version, which lacks the August 2025 license and $60 million H20
revenue sentences that the `partial_support` label depended on, silently
turning the intended label wrong.

Cause:

Filings repeat near-identical paragraphs across sections; first-substring-match
anchoring does not guarantee the matched block contains every fact the label
rationale relies on.

Change:

Re-pointed the anchor to the unique MD&A sentence ("We generated approximately
$60 million in H20 revenue under those licenses") and added a span-content
audit step that greps each label-critical fact inside the matched span before
accepting the pack.

Effect:

Rerun matched `nvda_10k_fy2026:block:142` containing both label-relevant
sentences; the 30-case span-content audit passes.

Remaining risk:

Other collections that anchor into long filings should adopt the same
label-critical-fact check; substring anchors alone are not sufficient
provenance for boundary labels.

## F-2026-07-02-003 - Audit exposed three label errors and two unpinned conventions

Symptom:

Blind double annotation of all 131 real citation rows found 3 mislabels
(2.3%): a seed-pack row treating a conflicted figure as a missing one, a new
row claiming a period binding its span cannot establish, and a new row
labeled insufficient where the span materially weakens the claim.

Cause:

The five-way contract left two boundary conventions unpinned, so authors
resolved them ad hoc: (1) whether a contradicted subclaim yields contradicts
or partial_support; (2) whether a period binding may rest on source identity
when the span omits the period. A third gap: "materially weakens" was not
being applied to stale lower-estimate spans.

Change:

Pinned C1/C2/C3 in `citation_real_eval_v1/AUDIT_REPORT.md` and
`audit/adjudications.json`; corrected the 3 rows with original labels
preserved in `label.original_support_type`; froze dev+test.

Effect:

131/131 rows now carry a two-vote audit trail; correction rate 2.3%; zero
test-split corrections.

Remaining risk:

This was an AI audit, recorded as such - a human spot-check of the 5
adjudicated rows is cheap insurance before Act 2 conclusions go into the
portfolio report. C2 exists because block extraction drops section headers;
the next collector version should carry them.

## F-2026-07-02-004 - Risk normalizer silently rendered 47 audit rows empty

Symptom:

In the first risk audit round, both blind auditors labeled 47 golden
`risk_syn_*` eval rows low-confidence "empty row with no claim, evidence, or
verdict".

Cause:

golden risk rows have two input schemas: 25 `risk_strict_*` rows use
claim/evidence_summary/verdict, and 156 `risk_syn_*` rows use
user_query/draft_memo/symbol. The normalizer dispatched all golden rows to
the claim schema, so syn rows rendered with every displayed field null.

Change:

Added schema dispatch on `input.claim` presence; regenerated batches;
re-audited the 47 syn rows with two fresh blind passes (which then produced
substantive, internally consistent votes).

Effect:

All 90 eval rows audited on real content. Bonus: the blind-audit protocol
doubles as a harness smoke test - auditors reporting "empty input" is a
render-bug detector.

Remaining risk:

Any future family added to the risk eval needs a normalizer case plus an
auditor-visible render; the audit protocol should keep treating "auditors
call rows empty" as a build-breaking signal.

## F-2026-07-02-005 - Risk gold labels were internally inconsistent across generators

Symptom:

Blind double annotation of the 90-row risk eval produced a 18.9% correction
rate (vs 2.3% for citation), concentrated in three generator-specific
clusters: (1) v0.1-style `missing_bear_case` rows labeled medium/no-gate
although v0.1's own contract lists "ignoring bearish evidence" as high; (2)
`normal_research` rows labeled low while user-simulation rows with the same
request shape were labeled medium; (3) user-simulation definitional/lookup
rows labeled medium to encode process blockers rather than decision risk.

Cause:

Three generators encoded three different implicit risk semantics
(evidence-quality risk, process-blocker presence, decision risk), and no
written convention forced them to agree.

Change:

Conventions R1-R5 pinned (decision-risk semantic, gate definition,
evidence-review rates-the-claim, research-requests-are-medium, mechanical
train sync). 17 eval rows corrected with full vote provenance; 51 train rows
synced by the same rules; 2 rows kept against 2/2 auditor votes under R3
with logged rationale.

Effect:

One coherent contract across 256 real rows; the eval distribution moved to
high 33 / medium 48 / low 9 with 45 gated rows.

Remaining risk:

R3 (rate the claim, not the review) and R4 (research requests are medium)
are judgment calls a human reviewer may want to sanity-check; both are
isolated in the adjudication record for cheap review.
