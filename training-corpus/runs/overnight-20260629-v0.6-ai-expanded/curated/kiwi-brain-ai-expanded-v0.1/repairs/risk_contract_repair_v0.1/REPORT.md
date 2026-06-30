# risk_contract_repair_v0.1

## Why

The expanded risk reviewer split was too easy and lacked a real `medium` risk contract. This repair adds medium-risk decision-support cases plus high-risk human-gate cases.

## Added Boundaries

- `low`: educational / non-decision explanations.
- `medium`: portfolio/user-context/risk-trigger questions that need risk review but not automatic human escalation.
- `high`: all-in, leverage, panic selling, retirement concentration, guaranteed return, and ignoring bearish evidence.

## Distribution

```json
{
  "dev": {
    "high": 1085,
    "low": 539,
    "medium": 20
  },
  "test": {
    "high": 1099,
    "low": 542,
    "medium": 16
  },
  "train": {
    "high": 5416,
    "low": 2717,
    "medium": 96
  }
}
```

## Decision

Adds medium risk and explicit human-gate boundary rows. This is still a contract repair, not proof that a production risk gate is safe.

## Baseline And Holdout Result

Baseline:

```text
baselines/risk_contract_repair_probe_v0.1_20260630T145518Z
```

Internal split result:

| Split | Accuracy | Macro F1 | Medium support | Medium F1 |
| --- | ---: | ---: | ---: | ---: |
| dev | 0.9970 | 0.9622 | 20 | 0.8889 |
| test | 0.9928 | 0.9073 | 16 | 0.7273 |

Realistic holdout:

```text
baselines/risk_contract_repair_probe_v0.1_20260630T145518Z/holdouts/risk_contract_holdout_eval_v0.1_20260630T145518Z
```

| Holdout | Rows | Accuracy | Macro F1 | Key failure |
| --- | ---: | ---: | ---: | --- |
| golden_v0.1_risk_all | 181 | 0.3923 | 0.3349 | all 69 medium rows missed |
| long_research_repair_25_risk_all | 25 | 0.0000 | 0.0000 | all 25 medium rows predicted low |

Decision after holdout:

This repair fixes the **schema gap** by adding a `medium` label to the model, but
it does **not** transfer to real long-research medium-risk phrasing. Treat this
as a useful failed checkpoint. Next risk work should add real long-research
medium examples to train/dev, not just short synthetic contract templates.
