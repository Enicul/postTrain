# Failure Log

Failures are first-class evidence. Record them instead of hiding them.

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
