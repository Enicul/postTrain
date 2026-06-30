# postTrain

Auditable post-training and agentic-RL portfolio repo for KIWI.

This repository is built for interview preparation for Agent Harness,
post-training, and agentic-RL internship roles. It is not just a final-code
dump. It is an experiment archive: data, scripts, checkpoints, failures,
decisions, and resume instructions should all be preserved.

## What This Repo Proves

KIWI is treated as a point-in-time financial research environment:

```text
raw market/social/official seed
  -> trainable task
  -> trajectory
  -> verifier / scorer
  -> specialist dataset
  -> baseline / post-training experiment
```

The goal is to show that we can run the post-training workflow ourselves:

- define verifiable tasks,
- collect and freeze trajectory data,
- build small specialist datasets,
- run baselines before GPU fine-tuning,
- preserve failure cases,
- improve data and harness based on observed failures.

## Start Here

Every agent should read these files first:

1. `AGENTS.md` - universal agent operating protocol.
2. `CODEX.md` - Codex-specific workflow and command rules.
3. `PROGRESS.md` - current status and last known checkpoint.
4. `TODO.md` - prioritized next work.
5. `CHECKPOINTS.md` - where to resume from.
6. `EXPERIMENT_LOG.md` and `FAILURE_LOG.md` - what happened and what broke.

## Current Baseline

First CPU specialist baseline:

```bash
python3 -m pip install -r training-corpus/requirements-baseline.txt
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_baselines_v0.1
```

Current results on `golden_v0.1`:

| Specialist | Target | Test accuracy | Test macro F1 | Status |
| --- | --- | ---: | ---: | --- |
| router_classifier | route_label | 0.9167 | 0.9368 | usable first baseline |
| risk_reviewer | risk_level | 0.5946 | 0.3986 | weak baseline |
| citation_verifier | support_type | 0.2581 | 0.1441 | needs data repair before fine-tuning |

Artifacts:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/
  datasets/
  baselines/specialist_cpu_baselines_v0.1/
```

## Repo Map

```text
AGENTS.md
CODEX.md
PROGRESS.md
TODO.md
CHECKPOINTS.md
EXPERIMENT_LOG.md
FAILURE_LOG.md
DECISIONS.md
docs/
  DATASETS.md
  GIT_WORKFLOW.md
  SERVER_RUNBOOK.md
training-corpus/
  requirements-baseline.txt
  scripts/train_specialist_baselines.py
  runs/.../golden_v0.1/
```

## Boundary

This repo is not claiming that KIWI is a production trading agent. The current
artifact is a training/evaluation substrate for financial research agents:
router, risk reviewer, citation verifier, memo scorer, memory gate, and later
SFT/DPO/GRPO experiments on verifiable subtasks.
