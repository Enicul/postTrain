# Block B - Eval-Pool Arms v0.1 (rules / naive prompt / engineered prompt)

First LLM columns of the three-task ladder, measured on the two frozen
audited rulers. LLM arms ran as Claude subagents (models: claude-haiku-4-5,
claude-sonnet-5), temperature not controllable in this harness (recorded as a
limitation); per-arm subagent token totals serve as the cost proxy. Rules
arms are deterministic scripts (regex red-lines for risk; lexical overlap for
citation) with ~zero cost.

## Risk (risk_real_eval_v1, 90 rows, 45 gated)

| Arm | Accuracy | Acc (confirmed-only) | Gate recall | Cost proxy (tokens) |
| --- | ---: | ---: | ---: | ---: |
| rules (regex) | 0.811 | 0.767 | 0.733 | ~0 |
| sklearn v0.1b (rung 1) | 0.833* | - | 0.64-0.73 | CPU |
| naive haiku | 0.667 | 0.671 | 0.867 | 63.5k |
| naive sonnet | 0.733 | 0.753 | **1.000** | 84.4k |
| prompted haiku | 0.800 | 0.753 | **1.000** | 67.6k |
| prompted sonnet | 0.811 | 0.767 | **1.000** | 89.5k |

*sklearn row is the v0.1b probe (dev/test weighted), for reference.

Findings:

- The SAFETY half of Act 1's kill criterion (gate recall >= 0.99) is met by
  every engineered-prompt arm and even naive sonnet. Prompted LLMs catch all
  Chinese red-line templates the sklearn rung missed.
- The ACCURACY half (>= 0.90) is NOT met: best prompt arm 0.811. Residual
  errors sit on the low/medium boundary. Notably the ~zero-cost regex rules
  arm matches prompted sonnet on accuracy (0.811) while failing gate recall -
  a rules-for-gate + LLM-for-level hybrid is the obvious rung-4 candidate.
- Act 1 verdict: NOT killed. Proceeds to rung 4 (experience library /
  hybrid) targeting the low/medium boundary.

## Citation (citation_real_eval_v1 dev+test, 69 rows, anonymized ids)

| Arm | Accuracy | Acc (confirmed-only) | Macro recall | Cost proxy (tokens) |
| --- | ---: | ---: | ---: | ---: |
| rules (lexical overlap) | 0.449 | 0.448 | 0.541 | ~0 |
| sklearn (golden v0.1, rung 1) | 0.258* | - | - | CPU |
| naive haiku | 0.826 | 0.836 | 0.867 | 59.1k |
| naive sonnet | 0.870 | 0.866 | 0.854 | 80.6k |
| prompted haiku | **0.957** | 0.955 | 0.925 | 62.1k |
| prompted sonnet | 0.899 | 0.895 | 0.884 | 73.0k |

*historical golden-pack sklearn, different split; shown for scale only.

Findings:

- The engineered prompt (contract definitions C1-C3 + 5 train-split
  few-shots) takes the SMALL model to 0.957 - above Act 2's rung-4 kill bar
  (0.85) one rung early. Prompting with a precise contract is enough for
  this task at frontier-family scale; no experience library, no weights.
- Prompted haiku outperforms prompted sonnet (0.957 vs 0.899): sonnet
  over-applies contradiction precedence to absent-element composites. Model
  scale is not the bottleneck; contract clarity is.
- Act 2 verdict: KILLED at rung 3 for frontier-family models. A small LOCAL
  verifier (cost/privacy) remains an explicitly separate future decision.

## The leak (F-2026-07-02-006)

The first citation run used original sample_ids whose case-key suffixes spell
out the authored label ("..._contradicts"). One arm's transcript admitted
consulting them. All citation arms were re-run with anonymized ids
(cit_anon_mapping.json). Quantified inflation on the one fully-preserved
leaked arm: naive haiku 0.942 leaked vs 0.826 anonymized = +11.6 points.
Leaked predictions are preserved in preds/cit_LEAKED_naive_haiku.jsonl as
failure evidence. Risk sample_ids do not encode labels (hashes/scenario
names) and were unaffected.

Caveats recorded: (1) eval labels were audited by Claude-family blind
auditors under the same contract text used in the engineered prompt -
confirmed-only accuracy is reported alongside to bound the circularity;
(2) subagent temperature is not controllable; (3) naive sonnet dropped 2 rows
(counted as errors).
