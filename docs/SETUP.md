# Setup & CPU baselines (relocated from the old README)

This file preserves the environment/run commands that used to live in the root
README, so the README can stay a 90-second front door. Nothing here is deleted —
only moved. The GPU escalation-env work is the current spine; the CPU specialist
baselines below are the earlier data-pipeline proof and remain reproducible.

## GPU / RL runbook

See `scripts/rl/GPU_RUNBOOK.md` for the escalation-env flow (CPU smoke → A1
prompted → A2 SFT → A3 GRPO, plus the failure protocol) and
`scripts/rl/requirements-rl.txt` for validated pins
(trl 0.15.2 / transformers 4.49.0 / peft 0.14.0). All runs are on one A100 80GB;
weights are git-excluded, so each run dir under
`training-corpus/scripts/rl/runs/` ships its `run_manifest.json` (config + git
sha + pip freeze), `*_eval.json`, and logs as the reproducible record.

## CPU specialist baselines (earlier pipeline proof)

First CPU specialist baseline on the smaller `golden_v0.1` pack:

```bash
python3 -m pip install -r training-corpus/requirements-baseline.txt
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_baselines_v0.1
```

Results on `golden_v0.1`:

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

Results on the expanded pack:

| Specialist | Target | Test accuracy | Test macro F1 | Status |
| --- | --- | ---: | ---: | --- |
| router_classifier | route_label | 1.0000 | 1.0000 | easy split; needs realistic holdout |
| risk_reviewer | risk_level | 1.0000 | 1.0000 | easy binary schema; needs edge cases |
| citation_verifier | support/verdict | 0.9000 | 0.8978 | learnable, but needs harder real spans |

The expanded pack proves the pipeline can ingest larger KIWI datasets and run
repeatable baselines; it does not prove real-world generalization.

Realistic holdout result (this is what blocked immediate GPU fine-tuning and
forced the data-contract repair):

```bash
python3 training-corpus/scripts/evaluate_baseline_holdouts.py \
  --run-id realistic_holdout_eval_v0.1_20260630T083000Z
```

| Holdout | Dataset | Rows | Accuracy all rows | Schema gap |
| --- | --- | ---: | ---: | --- |
| golden_v0.1_router_all | router_classifier | 344 | 0.3023 | yes |
| golden_v0.1_risk_all | risk_reviewer | 181 | 0.2762 | yes |
| golden_v0.1_citation_all | citation_verifier | 166 | 0.4819 | yes |
| long_research_repair_25_router_all | router_classifier | 25 | 0.4800 | no |
| real_tool_trace_pilot_10_router | router_classifier | 10 | 0.0000 | yes |

The fix was data-contract repair: add missing router labels (`risk_review`,
`clarification_needed`), add `medium` risk semantics, and align citation labels
across candidate evidence and verified support — which is what led into the
escalation-env ladder that the README now foregrounds.

## Agent operating docs

Every agent working in this repo should read, in order: `AGENTS.md` (universal
operating protocol), `CODEX.md` (Codex workflow/command rules), `PROGRESS.md`
(status + last checkpoint), `TODO.md` (prioritized queue), `CHECKPOINTS.md`
(where to resume), `LEARNING_SOURCES.md` (what we adopted from external reports
and what we deliberately did not), `EXPERIMENT_LOG.md` / `FAILURE_LOG.md`, and
`docs/RECORDING_PROTOCOL.md` (summary-first recording rules).
