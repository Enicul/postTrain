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
