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
6. `LEARNING_SOURCES.md` - what we extracted from external model reports and
   what we deliberately did not adopt.
7. `EXPERIMENT_LOG.md` and `FAILURE_LOG.md` - what happened and what broke.

## Current Baseline

First CPU specialist baseline on the smaller `golden_v0.1` pack:

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

Expanded CPU specialist baseline on `kiwi-brain-ai-expanded-v0.1`:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1 \
  --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines \
  --run-id specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Current results on the expanded pack:

| Specialist | Target | Test accuracy | Test macro F1 | Status |
| --- | --- | ---: | ---: | --- |
| router_classifier | route_label | 1.0000 | 1.0000 | easy split; needs realistic holdout |
| risk_reviewer | risk_level | 1.0000 | 1.0000 | easy binary schema; needs edge cases |
| citation_verifier | support/verdict | 0.9000 | 0.8978 | learnable, but needs harder real spans |

Interpretation:

The expanded pack proves the pipeline can ingest larger KIWI datasets and run
repeatable baselines. It does not yet prove real-world generalization. The next
step is to evaluate these checkpoints on real tool traces, long-research
episodes, and harder evidence-chain negatives before GPU fine-tuning.

## Repo Map

```text
AGENTS.md
CODEX.md
PROGRESS.md
TODO.md
CHECKPOINTS.md
LEARNING_SOURCES.md
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
  runs/.../kiwi-brain-ai-expanded-v0.1/
```

## Boundary

This repo is not claiming that KIWI is a production trading agent. The current
artifact is a training/evaluation substrate for financial research agents:
router, risk reviewer, citation verifier, memo scorer, memory gate, and later
SFT/DPO/GRPO experiments on verifiable subtasks.
