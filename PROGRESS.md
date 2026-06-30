# Progress

Last updated: 2026-06-30

## Current State

The repo has been initialized as a standalone post-training artifact repo for
KIWI interview preparation.

Imported from the Agent/KIWI workspace:

- golden training corpus `golden_v0.1`,
- CPU specialist baseline script,
- baseline requirements,
- first CPU baseline run artifacts.

## Current Checkpoint

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1
```

Important subpaths:

```text
datasets/
baselines/specialist_cpu_baselines_v0.1/
```

## Baseline Results

| Specialist | Target | Test accuracy | Test macro F1 | Status |
| --- | --- | ---: | ---: | --- |
| router_classifier | route_label | 0.9167 | 0.9368 | usable first baseline |
| risk_reviewer | risk_level | 0.5946 | 0.3986 | weak baseline |
| citation_verifier | support_type | 0.2581 | 0.1441 | data repair needed |

## Interpretation

- Router is the first credible specialist baseline.
- Risk reviewer is directionally useful but too weak to use as a gate alone.
- Citation verifier failed on held-out data; this is now a data-quality and
  feature-design problem before GPU work.

## Last Verified Commands

```bash
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
```

The imported baseline checkpoint reports:

```json
{"status": "complete", "run_id": "specialist_cpu_baselines_v0.1"}
```

## Next Best Step

Commit and push this initialization, then start citation verifier repair:

1. inspect citation test prediction errors,
2. identify label/schema problems,
3. add a repaired citation verifier dataset,
4. rerun the CPU baseline,
5. compare metrics and log the change.
