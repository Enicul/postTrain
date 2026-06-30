# Agent Operating Protocol

This repo is an interview-facing post-training artifact. Treat it as an
auditable lab notebook plus reproducible codebase.

## Startup Checklist

At the start of every session:

1. Read `AGENTS.md`.
2. Read `CODEX.md` if you are Codex.
3. Read `PROGRESS.md` and `TODO.md`.
4. Read `CHECKPOINTS.md` for the latest resumable state.
5. Read `LEARNING_SOURCES.md` when the task touches model reports, papers,
   post-training strategy, or interview framing.
6. Read relevant entries in `EXPERIMENT_LOG.md` and `FAILURE_LOG.md`.
7. Run `git status --short`.
8. Before changing files, identify which log/docs must be updated.

## Project Goal

Build a portfolio-quality, reproducible KIWI post-training artifact for
Agent Harness / post-training / agentic-RL interviews.

The artifact must show:

- what data was collected,
- which specialist each dataset trains,
- how baselines were run,
- what failed,
- why it failed,
- what was changed,
- what improved or did not improve,
- where to resume.
- which external lessons shaped the system, and which tempting ideas were not
  adopted.

## Non-Negotiable Rules

- Do not hide failures. Failed runs are part of the artifact.
- Do not claim training success without metrics and a saved run directory.
- Do not overwrite raw data without preserving provenance.
- Do not mix runtime product memory with offline training data.
- Do not use future information in point-in-time examples.
- Do not train market-return prediction as the first reward.
- Do not put secrets, API keys, cookies, browser profiles, or private `.env`
  files in the repo.
- Prefer deterministic verifiers for calculations and schema checks.
- Use small structured specialists before GPU LLM fine-tuning.

## Experiment Protocol

Use summary-first recording. Read `docs/RECORDING_PROTOCOL.md` before creating
new run artifacts.

Every experiment should produce a bounded local record:

```text
config.json
manifest.json
logs/checkpoint.json
logs/events.jsonl
metrics.json
README.md
prediction_samples or output_samples for error analysis
error_samples for failure analysis
```

`logs/events.jsonl` should contain phase-level events only, not per-row logs.
Full row-level `predictions_*.jsonl` or rollout dumps are not written by default.
Use explicit full recording only when needed and only when the output target can
handle it.

Every experiment must be logged in `EXPERIMENT_LOG.md`.

## Learning Source Protocol

When a paper, model report, blog post, or company system design changes our
plan, update `LEARNING_SOURCES.md`.

Each source entry must include:

```text
source links
core idea
what we extracted
why we extracted it
what we did not adopt
why not
mapping to KIWI/postTrain
concrete action
status
```

This prevents vague claims like "we learned from Qwen/DeepSeek/Kimi". The repo
must show the exact system or data decision that came from the reading.

If anything breaks, add or update `FAILURE_LOG.md` with:

```text
symptom
root cause or best hypothesis
fix/change
verification result
remaining risk
```

## Checkpoint Protocol

Create enough checkpoints that another agent can resume without guessing:

- data checkpoint: frozen input data path and counts,
- code checkpoint: commit hash or dirty diff summary,
- run checkpoint: run id, command, output path, status,
- decision checkpoint: why a path was chosen or abandoned.

Update `CHECKPOINTS.md` after meaningful progress.

## Git Protocol

Push regularly at meaningful boundaries:

- after adding or changing reusable scripts,
- after a baseline run completes,
- after a failed run is diagnosed and documented,
- after data is frozen,
- before switching to server/GPU work,
- before ending a long session.

Commit messages should describe the artifact state, not just file changes.

Examples:

```text
docs: initialize post-training experiment protocol
baseline: add CPU specialist runner and golden checkpoint
data: repair citation span labels for verifier baseline
```

## Data Roles

- Social/X/Weibo/Xiaohongshu data: market radar and user-language seed.
- Official/IR/SEC/press release data: auditable evidence source.
- Generated trajectory: training/eval substrate.
- Negative path: DPO pair, regression, or failure taxonomy case.
- Baseline prediction: error-analysis artifact.
- Prediction sample: capped error-analysis artifact.

## Handoff Requirements

Before finishing a session, update:

1. `PROGRESS.md` if status changed.
2. `TODO.md` if priorities changed.
3. `EXPERIMENT_LOG.md` if anything was run.
4. `FAILURE_LOG.md` if anything failed or underperformed.
5. `CHECKPOINTS.md` if there is a new resume point.
6. `LEARNING_SOURCES.md` if a source changed the plan.

Then run verification commands and record the result in your final message.
