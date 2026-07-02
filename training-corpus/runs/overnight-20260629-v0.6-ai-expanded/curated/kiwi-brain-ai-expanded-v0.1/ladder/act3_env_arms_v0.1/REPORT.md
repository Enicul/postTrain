# Act 3 Env Arms v0.1 (rungs 0/2/3 on the escalation environment)

Rules / naive-prompt / engineered-prompt policies scored against the
escalation_env_v0.1 analytic reward. Policies are contingent plans
(first action + on_fail), so expected reward is computed exactly (no MC
noise). Oracle = argmax over pure strategies using the TRUE per-seed p; it is
the analytic reward ceiling.

## SPEND-LIMIT CAVEAT (read first)

The subagent fan-out hit the account monthly spend limit mid-run. Reliable
inline coverage: rules arm (256, deterministic), naive_sonnet (256),
engineered_sonnet (64 = batch 1 only). The other engineered batches and the
haiku arms did not return. The engineered result below is therefore on 25% of
the eval; the full engineered sweep is DEFERRED to the next spend cycle. The
naive/rules/oracle full-256 numbers are complete.

## Full 256 (complete arms)

| lambda | rules | naive_sonnet | ORACLE |
| ---: | ---: | ---: | ---: |
| 0.1 | 0.760 (gate .625) | 0.666 (gate .672) | 0.955 (gate 1.0) |
| 0.3 | 0.654 | 0.577 | 0.865 |
| 0.6 | 0.494 | 0.443 | 0.730 |

Neither the rules arm nor naive prompting reaches the ceiling, and both miss
gates (rules .625, naive .672) — naive prompting is NOT a safe policy.

## Batch-1 subset (64 seeds; engineered available)

| lambda | rules | naive_sonnet | engineered_sonnet | ORACLE |
| ---: | ---: | ---: | ---: | ---: |
| 0.1 | 0.824 (gate .667) | 0.773 (gate .833) | **0.954 (gate 1.0)** | 0.954 (gate 1.0) |
| 0.3 | 0.721 | 0.695 | **0.862** | 0.862 |
| 0.6 | 0.568 | 0.578 | **0.725** | 0.725 |

**The engineered prompt exactly matches the oracle on all 64 seeds at all
three lambdas, including perfect gate recall.**

## Why this (provisionally) kills Act 3 without training

1. The oracle is the analytic reward ceiling (it uses the true p; no policy
   can exceed it).
2. GRPO's best possible outcome is to match the oracle.
3. The argmax-SFT collapse baseline trains on oracle actions and also
   approaches the oracle.
4. The engineered prompt already reaches the oracle on the observed 64 seeds.

Under the pre-registered Act 3 kill criterion ("GRPO must beat
max(best-prompt, argmax-SFT) by >= 3 points of mean reward"), a prompt that
equals the ceiling leaves GRPO no room to win. So on the available evidence
Act 3 is also resolved at rung 3.

Why the exact match is believable (not a bug): the seed p-distribution
clusters near 0 / 0.5 / 1, so few seeds sit near the cheap-vs-deep decision
boundary (p = c_cheap/c_deep = 0.128); the engineered prompt was given that
threshold (publicly derivable from the cost table, not from private p) and
the red-line gate list, and the gate cases are lexically obvious.

## Honesty limits on the "kill"

- Coverage is 64/256; treat the kill as PROVISIONAL until the full engineered
  sweep runs. The full-256 rules/naive/oracle numbers are solid; the
  engineered claim is on a quarter of the eval.
- "engineered = oracle" means matching the best policy UNDER THIS SIMULATOR,
  whose p is model-derived (env v0.1 fidelity limit) and shares model family
  with the arms — a possible shared blind spot.
- The safety floor for the gate remains code (risk_gate_rules_v11.py), not
  trusted to the prompt, consistent with the owner's Act-1 decision.

## Deferred next step (not blocking the narrative)

Re-run the 3 remaining engineered batches (haiku + sonnet) next spend cycle
to confirm the ceiling match on the full 256. If it holds, the ladder closes
with zero GPU training and a clean three-act "prompting suffices, and here is
the proof and the one deliberate code exception" story. If it breaks on the
unseen 192 seeds, that failure re-opens the weights question with a concrete
target — either outcome is a publishable result.
