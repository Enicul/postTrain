# Router Contract Repair v0.1

This repair pack fixes the first router contract gap exposed by realistic holdouts.

## What It Repairs

- Adds `risk_review`, which expanded v0.6 did not train.
- Adds `clarification_needed`, which expanded v0.6 did not train.
- Adds boundary rows for `evidence_check` vs `deep_research`.
- Adds boundary rows for `financial_calculation` vs research tasks.
- Converts real read-only tool traces into router rows.

## Boundary

This is a contract repair dataset, not final proof of production routing.
Some rows are generated boundary cases and must be treated as synthetic.
Use realistic holdouts and real tool traces after training to check whether
the repaired contract improves behavior.

## Summary

```json
{
  "labels_total": {
    "clarification_needed": 243,
    "deep_research": 1730,
    "evidence_check": 1694,
    "fast_answer": 1498,
    "financial_calculation": 1498,
    "news_retrieval": 1433,
    "price_lookup": 1433,
    "risk_review": 350
  },
  "origins_total": {
    "expanded_router_v0.6": 8400,
    "generated_contract_boundary": 1050,
    "golden_v0.1_router": 344,
    "long_research_trace_source_quality_repair_25": 25,
    "real_tool_trace_pilot_10": 10,
    "user_simulation_trace_pilot_50": 50
  },
  "splits": {
    "dev": {
      "labels": {
        "clarification_needed": 31,
        "deep_research": 256,
        "evidence_check": 232,
        "fast_answer": 215,
        "financial_calculation": 217,
        "news_retrieval": 206,
        "price_lookup": 206,
        "risk_review": 47
      },
      "origins": {
        "expanded_router_v0.6": 1200,
        "generated_contract_boundary": 148,
        "golden_v0.1_router": 47,
        "long_research_trace_source_quality_repair_25": 3,
        "real_tool_trace_pilot_10": 3,
        "user_simulation_trace_pilot_50": 9
      },
      "rows": 1410
    },
    "test": {
      "labels": {
        "clarification_needed": 39,
        "deep_research": 242,
        "evidence_check": 251,
        "fast_answer": 217,
        "financial_calculation": 210,
        "news_retrieval": 204,
        "price_lookup": 206,
        "risk_review": 53
      },
      "origins": {
        "expanded_router_v0.6": 1200,
        "generated_contract_boundary": 163,
        "golden_v0.1_router": 48,
        "long_research_trace_source_quality_repair_25": 3,
        "real_tool_trace_pilot_10": 2,
        "user_simulation_trace_pilot_50": 6
      },
      "rows": 1422
    },
    "train": {
      "labels": {
        "clarification_needed": 173,
        "deep_research": 1232,
        "evidence_check": 1211,
        "fast_answer": 1066,
        "financial_calculation": 1071,
        "news_retrieval": 1023,
        "price_lookup": 1021,
        "risk_review": 250
      },
      "origins": {
        "expanded_router_v0.6": 6000,
        "generated_contract_boundary": 739,
        "golden_v0.1_router": 249,
        "long_research_trace_source_quality_repair_25": 19,
        "real_tool_trace_pilot_10": 5,
        "user_simulation_trace_pilot_50": 35
      },
      "rows": 7047
    }
  }
}
```

## Next

Run the router-only CPU baseline with summary recording:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir /Users/lucine/Documents/Job/projects/postTrain/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c/repaired_datasets \
  --out-root /Users/lucine/Documents/Job/projects/postTrain/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c/baselines \
  --run-id router_contract_repair_probe_v0.1 \
  --datasets router_classifier
```
