# Rung 4 - Risk Hybrid Arm v0.1 (rules gate + prompted LLM + experience library)

Act 1's rung-4 attempt after Block B left it alive (gate recall 1.000 but
accuracy 0.811 < 0.90).

## Method

1. Lesson extraction (training-free RL step): dev-split errors of the two
   prompted arms (test never seen) were handed to a claude-opus extractor,
   which produced 5 contrastive lessons (risk_explib_v1.json). Core boundary:
   gate on COMMITMENT/URGING-with-risk-dismissal, not on topic; research
   requests about shaky claims are medium, not red lines.
2. Hybrid arm: engineered prompt + explib (haiku, sonnet; anonymized row ids
   per the F-2026-07-02-006 standing rule), gate = LLM gate UNION
   deterministic rules gate.

## Result on risk_real_eval_v1 (90 rows, 45 gated)

| Arm | Accuracy | Acc (confirmed-only) | Gate recall | Gate FP | Kill (>=0.90 & >=0.99) |
| --- | ---: | ---: | ---: | ---: | --- |
| Block B best (prompted sonnet) | 0.811 | 0.767 | 1.000 | - | no |
| hybrid haiku + rules v1.1 | 0.900 | 0.890 | 1.000 | 0 | **MET** |
| hybrid sonnet + rules v1.1 | **0.978** | 0.973 | **1.000** | **0** | **MET** |

**Act 1 is KILLED at rung 4.** Risk review needs no weight training: a
deterministic gate-rule floor plus a prompted LLM with five adjudicated
lessons clears both halves of the pre-registered kill criterion.

## The safety regression the process caught

The explib alone lifted sonnet accuracy 0.811 -> 0.978 but silently dropped
gate recall 1.000 -> 0.956: the two lost gates were exactly the two R3
adjudication rows (spacex tip review, tenbagger basket review) - the only
eval rows where the adjudicator had overruled 2/2 blind auditors. Four
independent model judgments now disagreed with that keep. The call was
escalated to the project owner, who ruled Option A (defense-in-depth):
red-line CLAIM topics always gate, even when the review's verdict rejects
the claim. Implemented as deterministic gate rules v1.1
(training-corpus/scripts/risk_gate_rules_v11.py) - the safety floor is code,
not prompt. Derivation is contract- and dev-only (no test contamination);
see the script docstring.

## Honesty notes

- The explib is largely contract-clarity repair: L1/L2 restore a boundary
  clause present in the audit rubric but omitted from the Block B arm prompt.
  Same finding as Act 2: contract precision, not model capacity, is the
  bottleneck on these two tasks.
- Label-provenance circularity bound: confirmed-only accuracy (0.973) is
  reported beside full accuracy.
- The R3 dissent trail (auditors vs adjudicator vs owner) is preserved in
  risk_explib_v1.json L6_policy_decision and the v0.1b audit record.

## Ladder state after this run

| Act | Status | Stopped at |
| --- | --- | --- |
| Act 1 risk review | KILLED | rung 4: rules gate + prompt + explib (0.978 / 1.000) |
| Act 2 citation | KILLED | rung 3: engineered prompt (haiku 0.957) |
| Act 3 escalation router | ALIVE | sole weights candidate; environment not yet built |
