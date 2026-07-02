# risk_contract_repair_v0.1b

Block A2 of the three-task ladder: repair the risk ruler and the medium
transfer gap together.

## What Changed vs v0.1

1. **Real rows, normalized.** 256 real rows from three families (golden 181,
   long-research 25, user-simulation 50) normalized into the v0.1 flat input
   schema. This also fixes a featurization gap: long-research memo content
   lived under `input.memo.*`, which `risk_text` never read, so those rows
   were nearly featureless in v0.1's holdout eval - part of the famous 0.0
   was a harness bug, not pure distribution shift.
2. **Audited ruler.** All 90 dev/test rows carry a blind double-annotation
   audit (per-row votes + adjudication). 73 confirmed, 17 corrected (18.9%).
   The golden pack mixed three implicit semantics; conventions R1-R5 unify
   them (see `risk_real_eval_v1/audit/risk_adjudications.json`).
3. **Contract self-consistency fix.** v0.1's own docs list "ignoring bearish
   evidence" as high risk, yet its `missing_bear_case` synthetic rows were
   labeled medium/no-gate. All 26 relabeled high+gate (5 in eval, 2/2
   auditor votes).
4. **Train synced by rule (R5).** Eval corrections expressible as
   provenance-mechanical rules were applied to train rows of the same
   scenario/route (68 rows total), so train and eval share one contract.

## Probe Result (rung 1 of the ladder)

Run: `baselines/risk_contract_repair_probe_v0.1b_20260702T031246Z`
Train: 8,395 rows (8,229 v0.1 synthetic + 166 real). Eval: audited real rows.

| Split | Rows | Accuracy | Macro F1 | Medium recall | High recall | Majority acc |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev | 38 | 0.8421 | 0.7764 | 1.00 (23/23) | 0.64 | 0.42 |
| test | 52 | 0.8269 | 0.7537 | 1.00 (25/25) | 0.73 | 0.42 |

Versus v0.1: realistic medium recall went 0.0 -> 1.00. The medium-transfer
failure is repaired.

## Honest Remaining Gap

High (all gated) recall is 0.64/0.73: the sklearn rung misses red-line rows
phrased as Chinese templates ("一定翻倍" price-guarantee buys, 满仓
concentration) and the R3 evidence-review red lines (tenbagger,
cannot-lose-money). The sklearn rung is NOT a safe gate alone. This is the
measured gap the ladder's rules/prompt/LLM arms must close - Act 1's kill
criterion demands gate recall >= 0.99.

## Freeze

`risk_real_eval_v1` (dev 38 / test 52; high 33 / medium 48 / low 9; gate 45)
is the frozen Act 1 ruler. Test is untouchable; prompts and experience
libraries iterate on train/dev only.
