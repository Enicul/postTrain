# Router Contract Repair v0.1c Report

## Goal

Repair the first KIWI router contract gap exposed by realistic holdouts:

- expanded router data lacked `risk_review`;
- expanded router data lacked `clarification_needed`;
- real tool traces were misrouted as `financial_calculation`;
- `evidence_check` vs `deep_research` was underspecified.

## Current Checkpoint

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c
```

Canonical baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c/baselines/router_contract_repair_probe_v0.1c_20260630T143244Z
```

Canonical holdout eval:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c/baselines/router_contract_repair_probe_v0.1c_20260630T143244Z/holdouts/router_contract_repair_holdout_eval_v0.1c_20260630T143256Z
```

## Iteration Trail

| Run | What Changed | Main Result | Remaining Problem |
| --- | --- | --- | --- |
| old expanded | no repair | real tool trace acc 0.0; schema gap true | missing labels and shortcut to `financial_calculation` |
| v0.1 | added missing labels, old golden, user-sim, real trace, boundary rows | golden acc 0.8983; real tool acc 0.5 | real traces all predicted `deep_research` |
| v0.1b | added real-tool-style `evidence_check` and `risk_review` rows | real tool still 0.5 | repair overcorrected; many deep rows became evidence/risk |
| v0.1c | added real-tool-style `deep_research` positive rows | real tool acc 1.0; schema gap false | social bookmark long claims can still be downgraded to `fast_answer` |

## Holdout Comparison

| Holdout | Old Expanded Acc | v0.1c Acc | Old Schema Gap | v0.1c Schema Gap |
| --- | ---: | ---: | --- | --- |
| golden_v0.1_router_all | 0.3023 | 0.8895 | true | false |
| long_research_repair_25_router_all | 0.4800 | 0.9600 | false | false |
| real_tool_trace_pilot_10_router | 0.0000 | 1.0000 | true | false |

Additional v0.1c signals:

```text
internal router test accuracy: 0.9965
internal router macro F1: 0.9974
internal safety recall: 1.0
real_tool_trace_pilot_10 safety recall: 1.0
golden_v0.1_router_all safety recall: 0.9688
```

## Interpretation

This repair fixed the most visible router contract failure: the model can now
emit `risk_review` and `clarification_needed`, and real tool traces no longer
collapse into `financial_calculation`.

It is still not enough for GPU fine-tuning. The next router repair should target
social/bookmark market narratives where long claims asking for evidence
verification are sometimes downgraded to `fast_answer`.

## Next

Build `router_social_boundary_repair_v0.1`:

- social bookmark long claim -> `evidence_check` or `deep_research`, not
  `fast_answer`;
- source-discovery / agent-research signal -> clarify whether this is financial
  relevance or agent-research archive;
- high-risk social claims with "all in", "can't lose", or portfolio language ->
  `risk_review`;
- keep summary-first recording.
