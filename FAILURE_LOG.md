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
