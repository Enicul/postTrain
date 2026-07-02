# Escalation Environment v0.1 (Act 3)

The offline RL environment for the ladder's sole surviving training
candidate: a two-step cost-aware escalation policy (try cheap -> observe ->
finish or escalate; or go deep / gate immediately).

## Components

| File | What | Provenance |
| --- | --- | --- |
| `env_seeds_v0.1.json` | 256 real query seeds (train 160 / dev 48 / test 48; 8 routes x stratified; 64 gate-required) | router_contract_repair_v0.1c, deterministic sample |
| `cost_table_v0.1.json` | cost units cheap 0.128 / deep 1.0 / gate 0.15 | real_tool_trace_pilot_10 latencies (30 calls) + span-size token proxy; small sample, noted |
| `outcome_table_v0.1.json` | p_cheap_success per seed | 3 blind haiku framings (capability / user-satisfaction / info-need) on anonymized ids; ok=1, partial=0.5, fail=0; p = mean |
| `outcome_votes/` | all 12 raw vote files | audit trail |
| `../../../../../../../scripts/escalation_env_v01.py` | simulator + analytic oracle | - |

## Outcome table sanity

p by gold route: fast_answer 1.00, price_lookup 1.00, news_retrieval 0.68,
financial_calculation 0.53, risk_review 0.15, evidence_check / deep_research /
clarification_needed 0.00. 74/256 seeds sit in the stochastic middle
(0.17-0.83) - the region where escalation policy is a real decision.

## Reward

`reward = success - lambda * cost - 2.0 * safety_violation`, lambda sweep
{0.1, 0.3, 0.6}; gate recall on the 64 gate-required seeds is a hard
constraint tracked independently of lambda.

## Analytic result (computed before any training)

For lambda < 1 the oracle strategy mix is lambda-invariant:
escalate-on-fail dominates finish-on-fail unless p = 1, and direct deep beats
cheap-first iff p < c_cheap/c_deep = 0.128. Oracle mix on the 256 seeds:
cheap_finish 70 / cheap_then_escalate 58 / deep 64 / gate 64, mean expected
reward 0.955 / 0.865 / 0.730 at lambda 0.1 / 0.3 / 0.6.

Implication, stated before Block E: the learnable content of this task is
INFERRING p and gate-need from query text (the oracle uses true p; a policy
never sees it). The argmax-SFT collapse baseline = train on oracle actions;
GRPO must beat it under the same information constraint to justify weights.

## Fidelity limits (v0.1)

- p is model-derived (ensemble simulator), not live execution;
- deep path assumed always-adequate (biases against the cheap path);
- cost sample is small (10 traces).
These are recorded as the environment's known gaps; upgrading any of them is
future work and must not happen silently between arms being compared.
