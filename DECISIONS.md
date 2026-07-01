# Decisions

## D-2026-06-30-001 - Keep post-training artifact in a separate repo

Decision:

Use `Enicul/postTrain` as the dedicated post-training artifact repo.

Why:

The Agent/KIWI product repo is large and dirty. This interview artifact needs a
clean, pushable, resume-friendly history with data, scripts, checkpoints, and
logs.

Consequence:

Only curated data and reusable scripts should be copied here. Product runtime
work stays in Agent/KIWI.

## D-2026-06-30-002 - CPU baselines before GPU fine-tuning

Decision:

Run cheap sklearn baselines for router, risk reviewer, and citation verifier
before using the A100 for small LLM fine-tuning.

Why:

We need a measurable floor. If a small LLM cannot beat a cheap baseline, the GPU
run is not meaningful.

Consequence:

GPU work starts only after the data and baseline error analysis are clear.

## D-2026-06-30-003 - Train specialists, not one generic financial model

Decision:

Split tasks into narrow specialists: router, risk reviewer, citation verifier,
memo quality scorer, memory gate, and later long2short.

Why:

Small models have limited capacity, and the task types are heterogeneous.
Structured specialist outputs are easier to evaluate, replace, and debug.

Consequence:

The general model remains the orchestrator/synthesizer. Specialists provide
structured checks and scores.

## D-2026-06-30-004 - Do not train calculation verifier first

Decision:

Keep calculations deterministic for now.

Why:

If code can calculate it, a model should not guess it. Models may identify which
calculation is needed, but correctness should be checked by code.

Consequence:

No GPU work on `calculation_verifier` until a separate task family proves that a
model is needed.

## D-2026-06-30-005 - Record learning sources as adopt / not-adopt decisions

Decision:

Maintain `LEARNING_SOURCES.md` as a source-to-system registry.

Why:

The interview artifact needs to show how we learned from GLM, Qwen, DeepSeek,
Kimi, MiniMax, WebExplorer, and other post-training systems without blindly
copying them. Each source should record what we extracted, why it matters, what
we did not adopt, and why it does not fit our current resources or domain.

Consequence:

Any future architecture or training-plan change inspired by an external source
should update `LEARNING_SOURCES.md` before it is treated as a project decision.

## D-2026-06-30-006 - Keep small baseline artifacts in Git for now

Decision:

Keep the current sklearn baseline artifacts, including `model.joblib`, in Git.

Why:

The first tracked training batch is small, about 2.3 MB, and the repo's purpose
is interview-facing reproducibility. Keeping the model files, metrics,
predictions, manifest, events, and checkpoint together makes the artifact easier
to inspect and resume.

Consequence:

If future GPU checkpoints or model files become large, move those to releases,
external object storage, or Git LFS. For now, small CPU baseline artifacts stay
versioned in the repo.

## D-2026-06-30-007 - Citation verifier needs data repair before GPU work

Decision:

Do not start citation-verifier GPU fine-tuning after `citation_verifier_repair_v0.1`.

Why:

The repair probe clarified the failure but did not produce a strong enough
baseline. Adding normalized source URL/domain did not improve the five-way task
meaningfully. The binary any-support task improved macro F1 relative to the
five-way baseline, but it still did not beat the majority baseline on accuracy.
The trace-id leakage probe improved metrics, but trace identity is not a valid
model feature.

Consequence:

The next citation-verifier work should add better data rather than train a
larger model: hard negatives, clean positive official spans, partial-support
boundary cases, and more insufficient/contradict examples.

## D-2026-06-30-008 - Treat v0.2 as data-repair evidence, not GPU readiness

Decision:

Do not start citation-verifier GPU fine-tuning after
`citation_verifier_repair_v0.2`.

Why:

The targeted train-only repair improved the five-way and binary probes, but both
tasks still underperform the majority baseline on test accuracy. The ablation
also showed that adding every synthetic row can hurt the cleaner binary support
boundary, so more synthetic volume is not automatically better.

Consequence:

The next citation-verifier iteration should prioritize audited real evidence
spans: official positive paragraphs, partial-support boundaries, and rare
contradict / insufficient rows. GPU work should wait until the repair baseline
is strong enough to make model capacity the likely bottleneck.

## D-2026-07-01-001 - Real citation spans are a seed, not GPU readiness

Decision:

Use `real_citation_spans_v0.1` as the first real-source seed for citation
verification, but do not start citation-verifier GPU fine-tuning from it alone.

Why:

The collection now has real source URLs, paragraph hashes, support labels, and
clean provenance, but it only contains 29 rows. It proves the data contract and
collection flow, not model readiness.

Consequence:

Before `citation_verifier_repair_v0.3`, expand the pack to at least 100 audited
rows with more SEC filings, earnings transcript spans, official IR releases,
and reputable news paragraphs. Run a CPU baseline/holdout probe before any GPU
LoRA/SFT/DPO work.

## D-2026-07-01-002 - Use filings and public reports, not paywalled report text

Decision:

Expand citation/research data with company filings, earnings releases,
financial tables, transcripts, public industry reports, and reputable news.
Do not store or train on full paywalled sell-side research report text.

Why:

Financial research agents need deeper evidence than headlines. SEC filings,
company IR, transcripts, and public reports provide auditable evidence for
facts, risk factors, management guidance, and industry context. Paid sell-side
reports may be useful as user-provided context or metadata, but storing their
full text in a training repo creates copyright and provenance risk.

Consequence:

Create `report_and_filing_spans_v0.1` under
`citation_contract_repair_v0.1`. Store source URL, section, short evidence
span, source hash, paragraph hash, `published_at`, `as_of`, support label, and
license note. Keep social sources as market radar/task seeds unless backed by
auditable evidence.

## D-2026-06-30-009 - Use summary-first local recording

Decision:

Local runs now default to summary-first recording. Scripts should write metrics,
manifests, checkpoints, phase-level events, capped prediction samples, and capped
error samples. Full row-level predictions, full rollout dumps, and large
checkpoints require an explicit `--record-mode full` or external artifact-store
decision.

Why:

The old protocol was useful for tiny baselines, but full append-only logs and
full prediction dumps can overload the local machine as data grows. The
interview artifact needs enough evidence to resume, audit, and explain failure
decisions, not every row by default.

Consequence:

Future agents should read `docs/RECORDING_PROTOCOL.md` before running
experiments. Git should carry scripts, configs, docs, summaries, small baseline
artifacts, and capped samples. Heavy outputs belong on the server, in object
storage, releases, or Git LFS.

## D-2026-06-30-010 - Treat router v0.1c as contract repair, not GPU readiness

Decision:

Use `router_contract_repair_v0.1c` as the current router repair checkpoint.

Why:

It fixes the most important label-contract gap: the router can now emit
`risk_review` and `clarification_needed`, and real tool trace routing improved
from 0.0 to 1.0 accuracy on the pilot holdout. However, golden social/bookmark
rows still show a separate failure mode where long evidence-verification claims
can be misrouted to `fast_answer`.

Consequence:

The next router work should be social/bookmark boundary repair, not GPU
fine-tuning. Router v0.1c is strong enough to show the data-contract repair loop
in interviews, but not enough to claim production router quality.

## D-2026-06-30-011 - Keep social router repair as candidate, not canonical

Decision:

Do not replace `router_contract_repair_v0.1c` with
`router_social_boundary_repair_v0.1` as the canonical router checkpoint yet.

Why:

The social repair improves the golden router holdout from 0.8895 to 0.9012 and
restores golden safety recall to 1.0, but it regresses real tool trace routing
from 1.0 to 0.9 by misrouting one GOOGL capex/source-support deep-research query
as `evidence_check`.

Consequence:

The current portfolio story should present v0.1c as the canonical router repair
and social v0.1 as a candidate/tradeoff run. The next main work is risk contract
repair; router social work can resume after adding real-tool-style deep-research
anchors.
