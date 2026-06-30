# Router Social Boundary Repair v0.1 Report

## Goal

Repair the router failure where long X/bookmark market narratives that ask for
evidence verification are sometimes downgraded to `fast_answer`.

## Candidate Checkpoint

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1
```

Baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1/baselines/router_social_boundary_probe_v0.1_20260630T143757Z
```

Holdout eval:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1/baselines/router_social_boundary_probe_v0.1_20260630T143757Z/holdouts/router_social_boundary_holdout_eval_v0.1_20260630T143807Z
```

## Results

| Holdout | Router v0.1c | Social v0.1 |
| --- | ---: | ---: |
| golden_v0.1_router_all | 0.8895 | 0.9012 |
| long_research_repair_25_router_all | 0.9600 | 0.9600 |
| real_tool_trace_pilot_10_router | 1.0000 | 0.9000 |

Other signals:

```text
golden safety recall: 1.0
golden under-trigger rate: 0.1084
real tool safety recall: 1.0
```

## Interpretation

This is a useful candidate repair, not the canonical router checkpoint.

It improves social/bookmark routing and restores golden safety recall to 1.0,
but it introduces one real-tool regression:

```text
GOOGL AI capex 相关判断需要哪些来源支持？
expected: deep_research
predicted: evidence_check
```

The likely issue is that social evidence-check rows strengthened the feature
association between "needs source support" phrasing and `evidence_check`. For
capex/thesis judgment, that phrasing should still route to `deep_research`.

## Decision

Keep `router_contract_repair_v0.1c` as canonical for now. Treat this run as a
candidate that exposes the next boundary: social evidence-check vs real-tool
deep-research source-support prompts.

## Next

Move to `risk_contract_repair_v0.1`. If router work resumes, add real-tool-style
capex/source-support deep-research train anchors, then rerun the same holdouts.
