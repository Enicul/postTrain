# Escalation env fidelity self-check + v0.3 gate correction (2026-07-02)

Run BEFORE any GPU training, exactly to avoid training against a broken ruler.

## C1 - label leakage: CLEAN (0/256)

The policy prompt never contains a seed's own p or oracle action - only the
generic, publicly-derivable threshold (p>0.13 = c_cheap/c_deep) and the cost
spec. An initial check reported 70/256; that was a check bug (the cost
literal "1.0" matched seeds with p=1.0), not leakage. Corrected check: 0.

## C2 - gate ground-truth conflict: FOUND and FIXED -> env v0.3

The env inherited `requires_human_gate` from router v0.1c (unaudited synthetic
repair), which gated 24 bare buy-decision questions ("我现在要不要买 X?",
"Is X a buy candidate?") as high-risk. This CONTRADICTED the audited risk
convention R4 (blind double-annotation + adjudication): a bare buy question
with no red-line lexicon is medium / no-gate.

Owner decision (2026-07-02): align to the audited R4 convention. The 24 bare
buy seeds -> requires_human_gate = False (original value preserved in
`gate_original_v0.1`, tagged `gate_convention: R4_bare_buy_no_gate_20260702`).
The 8 "all in X if bullish" seeds correctly STAY gated (genuine
concentration red line). The 32 risk_review-route seeds stay gated.

Effect: gate-required 64 -> 40. Oracle now sends bare buy questions to deep
research (correct) instead of gating them. Oracle mean reward
0.955/0.865/0.730 -> 0.947/0.841/0.682 (higher-cost deep replaces cheap gate
on those 24). Frozen as `env_seeds_v0.3.json` / `outcome_table_v0.3.json`;
EscalationEnv now loads the latest version automatically.

## C3 - penalty magnitude: PASS

At the worst lambda (0.6), gate reward 0.910 dominates the best gate-skip
(deep) reward -1.600, so a required gate is never worth skipping for cost.

## Consequence for the ladder

The provisional Act-3 kill was measured on v0.1 labels. It MUST be re-run on
v0.3 before it can be trusted or before any small-model training targets these
labels. That re-run is the immediate next step.
