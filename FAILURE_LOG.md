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

No model-side fix yet. Decision is to repair data before GPU fine-tuning.

Effect:

This failure created the next task: citation-span quality repair and label
schema audit.

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
