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
