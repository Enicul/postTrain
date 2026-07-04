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

## F-2026-07-02-006 - Eval sample_ids leaked gold labels into LLM arms

Symptom:

In Block B's first citation run, an arm's transcript said "consistent with
rubric and sample_id" - the case-key suffix of every citation sample_id
spells out the authored label ("..._contradicts", "..._partial_support").

Cause:

Human-readable case keys were designed for provenance, then reused verbatim
as eval row ids shown to the models being evaluated.

Change:

All citation arms re-run with opaque anonymized ids (mapping preserved in
the artifact). Leaked predictions kept as failure evidence. Measured
inflation on the preserved leaked arm: naive haiku 0.942 leaked vs 0.826
anonymized (+11.6 points). Risk ids are hashes/scenario names without
labels and were unaffected. New standing rule: every eval batch shown to a
model uses anonymized row ids.

Effect:

Citation comparison table now reflects anonymized runs only.

Remaining risk:

The A1/A2 blind audits saw the same suffixes, biasing toward CONFIRMING
authored labels; all label corrections were made against the leaked hint
(which strengthens them), but confirmation counts are softer than they look.
A leak-free spot re-audit of a random confirmed subset is cheap insurance
and is now in TODO.

## F-2026-07-02-007 - Experience library silently traded safety for accuracy

Symptom:

The rung-4 explib lifted hybrid sonnet accuracy 0.811 -> 0.978 but dropped
gate recall 1.000 -> 0.956. The two lost gates were exactly the two R3
adjudication rows (red-line-claim evidence reviews) - the only rows where
the adjudicator had kept gold against 2/2 blind auditor votes; the explib's
"requests-for-research are not red lines" lesson pulled the models back to
the auditors' reading.

Cause:

Lessons optimized against dev accuracy can re-litigate contested label
conventions; nothing in the lesson loop protects a convention that exists
only in the adjudicator's head.

Change:

Escalated to the project owner as a product-policy question. Ruling: option
A, defense-in-depth - red-line CLAIM topics always gate even when the
review's verdict rejects the claim. Implemented as deterministic gate rules
v1.1 (code, not prompt), derivation restricted to the pre-registered
contract red-line list plus dev rows. Dissent trail preserved in the explib
artifact.

Effect:

Both hybrid arms meet the kill criteria (0.978/1.000 and 0.900/1.000, zero
gate false positives).

Remaining risk:

Contested conventions should be flagged to a human BEFORE a lesson round,
not after; added to the ladder plan's operating notes. The safety floor now
lives in versioned code, so future explib iterations cannot silently erode
it.

## F-2026-07-02-008 - Account spend limit truncated the Act 3 engineered sweep

Symptom:

Six of the sixteen Act-3 env-arm subagents returned "You've hit your monthly
spend limit" instead of predictions: engineered haiku b2/b3/b4 and engineered
sonnet b2/b3/b4. Engineered coverage fell to 64/256 (batch 1 only).

Cause:

The day's multi-block fan-out (Block B, rung 4, Act 3 outcome ensemble, Act 3
arms) consumed the monthly subagent spend budget.

Change:

Scored only certainty-attributed inline arms; filename collisions among
agent-written disk files made the file-only arms unsafe to attribute, so they
were excluded rather than guessed. The engineered result is reported on its
64-seed subset with an explicit provisional flag; the full sweep is deferred
to the next spend cycle.

Effect:

The full-256 rules/naive/oracle comparison is complete and solid; the
headline "engineered = oracle" claim is honest but on 25% of the eval.

Remaining risk:

The provisional Act-3 kill could break on the unseen 192 seeds. That is
tracked as the explicit deferred step; either outcome (confirm the close, or
re-open weights with a concrete target) is a publishable result. Operational
lesson: budget the spend envelope before a multi-block subagent day.

## F-2026-07-02-009 - Three guardrail contradictions in KIWI found by the QA audit

Symptom:

The Opus QA audit of the KIWI copilot (218/218 tests pass) found three places
where shipped behavior contradicts the stated safety design:

1. Disclaimer suppressed by default - `SHOW_DISCLAIMER` defaults to `"0"`, so
   `config.footer()` returns `""` (`config.py:151,162-164`); the "the decision
   is always yours" disclaimer never renders in the default config.
2. Never-"buy-now" is prompt-only - `COMPLIANCE_RULES` (`prompts.py:8-16`)
   instructs the model but there is no output-side scrubber to detect/block an
   imperative if the model emits one anyway.
3. `stock_decision` path bypasses the dual gate - it hardcodes
   `requires_user_approval:True` (`stock_decision.py:226,478`) instead of
   routing through `policy.py`/`critic.py`; only `/memory/govern` and
   `/memory/proposals/generate` exercise the dual gate.

Cause:

Each is a case of the safety intent living only at a soft layer (a default env
value, a prompt instruction, or a per-endpoint hardcode) rather than as a
code-level floor. Passing tests did not catch them because the tests exercise
the configured/prompted happy path, not the default-config render, the
model-emits-imperative case, or the un-gated `stock_decision` route.

Change (fix plan):

1. Default `SHOW_DISCLAIMER` on.
2. Add a post-generation regex scrubber as a code-level floor - same philosophy
   as postTrain's `risk_gate_rules_v11`: the safety floor lives in versioned
   code, never in prompts.
3. Route all proposals through `critic.evaluate` instead of the per-endpoint
   `requires_user_approval:True` hardcode.

These are recorded in `docs/DECISION_NODE_RECORDING_SPEC.md` (guardrail-
contradictions section) and TODO.md; implementation is on the KIWI side.

Effect:

Documented as product-side failures found by audit, with a concrete fix plan.
The fixes move each guardrail from a soft/promptable layer to a versioned
code floor, consistent with the project's stance that safety must not be
promptable.

Remaining risk:

The fixes touch existing KIWI files and are therefore blocked on landing/
stashing the ~118 uncommitted KIWI changes (same block as the recording
fixes). Until then the contradictions remain live in the default config;
tracked in TODO.md "P1 - Retrospective Recording".

## F-2026-07-03-001 - trl 0.11.4 missing transitive `rich` crashes SFTTrainer import

Symptom:

First A2 launch crashed on import: `SFTTrainer` (trl) pulled in a module that
imports `rich`, which was not installed - ImportError before any training step.
Failed launch produced a manifest-only run dir with no adapter.

Evidence files:

```text
runs/sft_qwen05/20260703T1504Z-e571324/run_manifest.json
runs/sft_qwen15/20260703T1504Z-e571324/run_manifest.json
(manifest + trainer_log stub only; no adapter/, no metrics.json)
```

Diagnosis:

`rich` is a transitive dependency of trl's console/logging path that pip did not
resolve into the env, and requirements-rl.txt did not list it explicitly. The
pin set was assembled without a local GPU env to install-and-validate against,
so the missing transitive dep was invisible until first real launch.

Fix:

`pip install rich`, and add `rich` to requirements-rl.txt so a clean install
cannot reproduce it. Re-ran into fresh run dirs (20260703T1505Z / T1506Z).

New run:

run_id 20260703T1505Z-e571324 (0.5B), 20260703T1506Z-e571324 (1.5B).

Effect / lesson:

Recoverable in minutes once seen; the manifest-only failed dirs are preserved as
the linkage record. Lesson reinforced with F-2026-07-03-002: version pins chosen
without a GPU env to validate against are guesses - the per-run manifest pip
freeze is the authoritative environment record.

## F-2026-07-03-002 - TRL API mismatch: scripts use `processing_class` + GRPOTrainer, but pins were trl 0.11.4

Symptom:

The A2/A3 scripts are written for the modern trl API (`processing_class=` on
SFTTrainer, and `GRPOTrainer`/`GRPOConfig` for A3), but requirements-rl.txt
pinned `trl==0.11.4`, which uses the old `tokenizer=` argument AND does not
contain GRPOTrainer at all (it only landed in trl 0.14). So A2 would take the
wrong kwarg and A3 could not import its trainer.

Evidence files:

```text
runs/sft_qwen05/20260703T1504Z-e571324/run_manifest.json   (failed-era manifest)
runs/gpu_session_20260703/{run_a2.sh,run_a3.sh,a2_batch.log,a3_batch.log}
runs/*/*/run_manifest.json  pip_freeze now records trl==0.15.2 (authoritative)
```

Diagnosis:

The pins were chosen from memory of a "known-good" trl era without a local GPU
environment to install-and-run against, so the script/pin API drift (0.11.x vs
the 0.14+ processing_class + GRPOTrainer world) went undetected until launch.

Fix:

Upgrade the env to `trl==0.15.2`, `transformers==4.49.0`, `peft==0.14.0`;
verified SFTTrainer accepts `processing_class` and GRPOConfig exposes all six
args the scripts use (num_generations, max_completion_length, save_steps,
save_total_limit, gradient_accumulation_steps, seed). Updated requirements-rl.txt
to the validated pins.

New run:

Same re-run dirs as F-2026-07-03-001 (T1505Z/T1506Z for A2; A3 T1507Z/T1520Z).

Effect / lesson:

Both A2 and A3 ran cleanly on the upgraded env. Standing lesson: version pins
are a convenient starting point only; the per-run `run_manifest.json` pip freeze
is the authoritative record of what actually ran.

## F-2026-07-03-003 - GRPO 0.5B policy collapse: gate action extinct under group-relative advantage

Symptom:

A3 GRPO on Qwen2.5-0.5B (init from the SFT adapter) collapsed. Test @lambda=0.3
reward fell to 0.383 (-22.3 pts vs SFT 0.6061), gate_recall dropped to 0.00, and
cost climbed to 0.9455 (~ always-deep). The policy degenerated to near-always
choosing the deep/expensive action: cost ~= deep 1.0, success 1.0, gate action
extinct. Kill check FAIL.

Evidence files:

```text
runs/grpo_qwen05/20260703T1507Z-e571324/reward_trace.jsonl   (action_mix gate -> 0)
runs/grpo_qwen05/20260703T1507Z-e571324/generations.jsonl    (5936+ rollouts)
runs/grpo_qwen05/20260703T1507Z-e571324/trainer_log.jsonl    (KL ~2.0 throughout)
runs/grpo_qwen05/20260703T1507Z-e571324/grpo_test_eval.json  (kill_check delta -0.2231)
runs/grpo_qwen05/20260703T1507Z-e571324/run_manifest.json
```

Early warning (interview-grade):

The collapse was visible in reward_trace BEFORE the eval confirmed it. The
per-batch action_mix shows the gate count decaying to 0 in late batches; batch
371 recorded gate_violation_rate 1.0 with mean_reward -1.51. The reward_trace
is the early-warning instrument: gate count -> 0 is the leading indicator of the
collapse that the held-out eval then measured.

Diagnosis (mechanism hypothesis):

Gate-required seeds are only 24/160 = 15% of the training distribution. GRPO
uses group-relative advantage: it normalizes reward WITHIN the K=8 completions
for a given seed. When all 8 completions on a gate seed violate the gate
identically (easy at 0.5B capacity), their rewards are all ~equal, so the
within-group advantage is ~0 - the -2.0 safety penalty produces NO gradient
signal because there is no relative winner to reinforce. Meanwhile the abundant
non-gate seeds provide a clean cost gradient. Combined with high KL drift (~2.0)
at 0.5B capacity, cost-optimization squeezed the low-frequency, gradient-starved
gate action out of the policy entirely. In short: a rare hard-constraint action,
under group-relative advantage, can receive zero learning signal exactly when it
is failing uniformly - and then gets optimized away.

Fix (not yet run - pre-registered options, see D-2026-07-03-003):

No single-line fix; this is a method/regime result. Candidate interventions
pre-registered but not committed: (a) gate-seed oversampling so gate seeds are
not 15% of batches, (b) larger K to raise the chance of an intra-group winner on
gate seeds, (c) an explicit exploration bonus on the gate action, or (d) accept
the rules+model hybrid as the product answer (the safety floor lives in code,
not in the RL policy). The 1.5B run did NOT collapse (KL ~0.3, gate alive), so
this is partly a capacity-plus-KL-control failure specific to 0.5B.

Effect / lesson:

This is the day's interview-grade evidence: a concrete, instrumented RL failure
with a mechanistic explanation and a leading indicator that fired before the
eval. It is also the direct evidence for the standing architecture decision
(D-2026-07-03-003): pure RL cannot be trusted to carry a hard, low-frequency
safety constraint - the floor stays in versioned code.

## F-2026-07-04-001 - citation launcher authored against an unfrozen interface: missing `--eval-dir` crashes argparse

Symptom:

The Night-3 citation run crashed instantly, three times. `grpo_citation.py`
exited on argparse with `error: the following arguments are required:
--eval-dir` before any model loaded.

Evidence files:

```text
runs/gpu_session_20260703/night_batch.log    (x3 "error: the following arguments are required: --eval-dir")
runs/gpu_session_20260703/run_night.sh       (the launcher that omitted --eval-dir)
runs/gpu_session_20260703/run_night3.sh       (the corrected launcher, passes --eval-dir $CEVAL)
```

Diagnosis:

Process failure, not a code bug in the trainer. `run_night.sh` was written by the
overnight orchestrator BEFORE `grpo_citation.py`'s CLI was finalized - it was
authored against an unfrozen interface. When `--eval-dir` was made a required arg
on the script, the pre-written launcher had no way to know, so it invoked the
script without the flag and argparse rejected it immediately. Same failure class
as F-2026-07-03-002 (script/pin API drift): a caller committed to an interface
before that interface was frozen.

Fix:

Author the citation launch in `run_night3.sh` with the required
`--eval-dir $CEVAL` (pointing at `citation_real_eval_v1`), for both the
`--eval-only` baseline pass and the training pass. Reran successfully.

New run:

run_id 20260703T1725Z-e571324 (grpo_citation15) - see EXP-2026-07-04-003.

Effect / lesson:

Zero-cost failure (crashed before any GPU work), fully recoverable once the
missing flag was supplied. Standing lesson: a launcher is a caller of an
interface; do not author it against an interface that is still changing. When a
script's required args are not yet frozen, the launcher should be written (or
regenerated) AFTER the script, or the script should default the arg rather than
require it. The preserved `run_night.sh` + `night_batch.log` are the linkage
record.

## F-2026-07-04-002 - 0.5B GRPO collapse REPEATS despite oversample x4 + kl-beta 0.2: capacity floor, and a sampling-vs-greedy split

Symptom:

The Night-1 collapse-prevention ablation (R4: GRPO-v2 on Qwen2.5-0.5B, init from
the SFT adapter, gate-oversample x4 AND kl-beta 0.2) trained fully (400 steps)
but the GREEDY eval @lambda=0.3 collapsed to 0.383 / gate_recall 0.00 / cost
0.9455 - DIGIT-IDENTICAL to yesterday's un-mitigated v1 collapse
(F-2026-07-03-003). The mitigations did not change the decoded policy.

Evidence files:

```text
runs/grpo_v2_qwen05/20260703T1608Z-e571324/grpo_v2_test_eval.json  (0.383 / gate 0.00, kill FAIL)
runs/grpo_v2_qwen05/20260703T1608Z-e571324/reward_trace.jsonl      (late batches keep gate alive)
runs/grpo_v2_qwen05/20260703T1608Z-e571324/trainer_log.jsonl       (KL 37.1 @ step 10)
runs/grpo_v2_qwen05/20260703T1608Z-e571324/run_manifest.json       (gate_oversample 4, kl_beta 0.2,
                                                                    parent-run 20260703T1507Z-e571324)
```

Diagnosis:

The mitigations DID change training dynamics: gate-oversampling raised the gate
seed frequency and kl-beta 0.2 tightened the trust region, and the training-time
SAMPLES kept the gate action alive - late `reward_trace` batches show up to
11/16 gate completions with gate_violation_rate as low as 0.0 (vs v1, where gate
count decayed to 0). KL spiked to 37.1 at step 10 before settling (~0.7).

But the GREEDY (argmax, temp-0) eval still collapsed to the always-deep
attractor, identically to v1. This is the distinct observation: a
SAMPLING-vs-GREEDY split. Under sampling the 0.5B explores the gate; under argmax
decoding it does not - the mode of the 0.5B's action distribution sits on "deep"
even when the distribution has non-trivial gate mass. Oversampling and KL control
moved the DISTRIBUTION but not its MODE, and eval reads the mode. Verdict:
capacity floor at 0.5B. The gate action is representable in the 0.5B's sampled
policy but not recoverable as its greedy decode at this capacity.

Fix (not a one-liner; options, not committed):

This is a regime result, consistent with the scale-sweep finding that gate
discipline only emerges at 3B (EXP-2026-07-04-002). Candidate probes, none
promoted: (a) a temperature-sweep eval on this exact adapter to quantify the
sampling-vs-greedy gap (queued, optional, TODO); (b) accept the capacity floor
and stop trying to make 0.5B carry the gate under greedy decode; (c) the standing
architecture answer - the safety floor lives in versioned code, not in a 0.5B RL
policy (D-2026-07-03-003). The 3B result (SFT alone hits gate 1.000) is the
constructive alternative to fighting the 0.5B floor.

Effect / lesson:

Two mitigations that provably worked in TRAINING (samples kept the gate) failed
to move the DECODED policy - a clean caution that training-time action mix is not
the deliverable; the greedy-decoded eval is. Always read the eval mode you will
ship, not the sampling stats that look healthy. Reinforces the capacity-floor
line of D-2026-07-03-003.

## F-2026-07-04-003 - citation GRPO cannot kill fabrication: wrong action space (verbatim long-id copy) for a 1.5B

Symptom:

First citation-env GRPO on the 1.5B (EXP-2026-07-04-003) missed its
pre-registered bar (fabricated_rate == 0 AND verdict +5) by a wide margin.
fabricated_rate only fell 0.871 -> 0.742 (still fabricating ~3 of 4 rows), and
verdict_acc actually DROPPED 0.2581 -> 0.1935.

Evidence files:

```text
runs/citation_prompted15_test_eval.json                              (baseline: fab 0.871, verdict_acc 0.2581,
                                                                      cite_gold 0.0645, reward -0.5613)
runs/grpo_citation15/20260703T1725Z-e571324/citation_grpo_test_eval.json  (fab 0.742, verdict_acc 0.1935,
                                                                      cite_gold 0.1935, reward -0.4323)
runs/grpo_citation15/20260703T1725Z-e571324/generations.jsonl        (rollouts show fabricated ids)
runs/grpo_citation15/20260703T1725Z-e571324/reward_trace.jsonl
```

Diagnosis:

RL did move the model the right direction on evidence (cite_gold_rate TRIPLED
0.0645 -> 0.1935, mean_reward -0.561 -> -0.432), but it could not stop fabrication
because the ACTION SPACE is wrong for the capacity. The env requires the model to
reproduce long evidence identifiers verbatim, character-for-character. A 1.5B
cannot reliably copy long ids, so it invents plausible-looking ones - that is the
fabrication. Worse, the citation objective competed with the verdict objective
(verdict_acc fell), so under a fixed budget the model traded verdict correctness
for citation behavior and still fabricated. This is a HARNESS-DESIGN failure, not
a training-hparam failure: verbatim long-id copying is making the model do the
harness's bookkeeping.

Fix (pre-registered, not yet run):

Citation env v2 (D-2026-07-04-002): re-render the candidate evidence spans as a
small set of LETTER choices (A-F) and have the harness map the chosen letter back
to the underlying id. The model's action becomes "pick the supporting candidate,"
which a 1.5B can do, and fabrication becomes structurally impossible (a letter is
either in-set or a parse fallback, never a hallucinated id). Then re-run 1.5B GRPO
against the same frozen `citation_real_eval_v1` ruler and re-test the bar.

Effect / lesson:

"Don't make the model do the harness's job." When a small model fabricates
structured tokens (long ids, exact quotes), first ask whether the action space is
asking it to be a database key store. Reshaping the action space to a
harness-mappable choice is usually the fix, not more RL steps. Directly motivates
citation env v2.

## F-2026-07-04-004 - DPO collapses exploration: a pair-design artifact (rejected == the escalate action)

Symptom:

The Night-1 DPO arm at 1.5B (beta=0.1, 60 steps) achieved perfect gate recall
(1.000) but collapsed everything else: success fell to 0.58, cost to 0.139,
reward to 0.5382 (-0.21 vs SFT), deep/escalate actions went near-zero. The model
learned "never escalate / never go deep."

Evidence files:

```text
runs/dpo_qwen15/20260703T1607Z-e571324/dpo_test_eval.json   (reward 0.5382, gate 1.000, success 0.58, cost 0.139)
runs/dpo_qwen15/20260703T1607Z-e571324/test_preds.jsonl
runs/dpo_qwen15_pairs.jsonl                                  (the 160 preference pairs - the artifact)
runs/dpo_qwen15/20260703T1607Z-e571324/metrics.json         (pref-acc 0.8625, final loss 0.4346)
```

Diagnosis:

Pair-design artifact, not a DPO-method failure. For cheap seeds, the constructed
pair frequently pits a chosen `{"first":"cheap","on_fail":"finish"}` against a
rejected `{"first":"cheap","on_fail":"escalate"}` - i.e. the REJECTED action is
the one that escalates. DPO therefore learns to down-weight escalation everywhere,
including where it is needed, which is why gate recall paradoxically hits 1.000
(the model over-escalates on the few gate seeds while under-exploring on the rest)
while success/cost collapse. The pairs taught "the escalate branch is the loser,"
which is only true on cheap seeds. This is the mirror image of the GRPO 1.5B
result (reward-optimal, gate-imperfect): DPO is gate-perfect, reward-collapsed.

Fix (pre-registered, not yet run):

DPO pair v2 (D-2026-07-04-004): the pair set must INCLUDE "failed-to-escalate"
negatives - pairs where, on a gate/hard seed, the chosen action escalates and the
rejected action is the cheap/finish one that should have escalated. Balancing the
pair distribution so escalation is the WINNER on hard seeds (not uniformly the
loser) is what lets DPO learn when to escalate rather than a blanket "don't."

Effect / lesson:

A preference dataset encodes a policy; if every pair that mentions escalation
marks it as the rejected side, DPO will learn to never escalate. Pair
construction must cover BOTH error directions (over- and under-escalation) or the
learned policy inherits the one-sidedness. Completes the SFT/DPO/GRPO three-way
picture on one ruler (EXP-2026-07-04-001).

## F-2026-07-04-005 - Gemma venv torch/driver mismatch, then a hand-rolled-generate smoke test masked a working real path

Symptom:

Standing up the Gemma 4 cross-family arm (EXP-2026-07-04-008) in a fresh venv, the
latest `torch` wheel refused to initialize CUDA - it required a newer NVIDIA driver
than the box shipped (driver 12050). After reinstalling the CUDA 12.4 (`cu124`)
wheels to match the box driver, torch worked; but a hand-rolled standalone smoke
test then threw an unrelated `AttributeError` from a hand-written `generate` call
against transformers 5.13, which briefly looked like the Gemma arm was broken.

Evidence:

```text
runs/gemma_prompted/{e2b_test_eval.json,e4b_test_eval.json}  (the REAL eval path, which worked)
runs/gpu_session_20260704/batch4.log                          (driver/wheel + smoke trace)
```

Diagnosis:

Two independent issues stacked. (1) A genuine environment mismatch: latest-torch
CUDA requirement > box driver 12050 -> fixed by pinning to `cu124` wheels that match
the driver. (2) A FALSE alarm: the transformers-5.13 `AttributeError` was in a
HAND-ROLLED `generate` wrapper written only for the smoke test, NOT in the actual
eval harness. The real eval path (the same harness used for every Qwen arm) ran
cleanly and produced the E2B/E4B numbers. The smoke test was testing a code path
that would never ship.

Fix:

Reinstall cu124 torch wheels to match driver 12050; DISCARD the hand-rolled smoke
harness and smoke-test THROUGH THE ACTUAL EVAL HARNESS instead.

Effect / lesson:

SMOKE-TEST THROUGH THE REAL PATH, NOT A HAND-ROLLED ONE. A bespoke smoke script can
fail (or pass) for reasons that have nothing to do with the code you will actually
run, wasting debugging time on a phantom. When validating a new model/family on an
existing harness, exercise the harness's own entry point on one row; do not
re-implement `generate`. Also: on a shared box, always pin CUDA wheels to the
installed driver rather than pulling "latest."

## F-2026-07-04-006 - Tooling agent wrote gemma-3n (2025 family) hub ids instead of gemma-4; caught at orchestration review

Symptom:

The tooling agent that drafted the Gemma arm wrote `gemma-3n` (the 2025 Gemma family)
Hugging Face hub ids into the launch config instead of the intended `gemma-4` hub ids.
The numbers such a run would have produced would have looked PERFECTLY NORMAL - a
plausible small-model prompted result - with nothing in the metrics to reveal that the
wrong model family had been evaluated.

Evidence:

```text
repo commit 40b42e9  (on-box sed fix of the gemma hub ids: gemma-3n -> gemma-4)
runs/gemma_prompted/{e2b,e4b}_run_manifest.json  (final, corrected model ids)
```

Diagnosis:

A model-id authoring error, caught at ORCHESTRATION REVIEW before launch (not by any
automated check). Because a wrong-family id still resolves to a real, loadable model
and yields sane-looking metrics, no runtime error or anomalous number would have
flagged it - the mistake is invisible downstream. Fixed on-box via `sed` and committed
(40b42e9).

Fix:

Corrected the hub ids to the gemma-4 family before launch; committed the fix.

Effect / lesson:

MODEL-ID REVIEW IS PART OF EXPERIMENT REVIEW. When an experiment's whole point is the
identity of the model (a cross-family arm), the model id is a LOAD-BEARING parameter
and must be reviewed like a hyperparameter - wrong-family numbers look completely
normal and would silently corrupt the cross-family conclusion. Add model-id
verification to the pre-launch review checklist for any model-identity experiment.
