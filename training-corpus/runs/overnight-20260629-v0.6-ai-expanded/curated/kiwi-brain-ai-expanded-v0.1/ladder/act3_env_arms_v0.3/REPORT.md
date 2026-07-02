# Act 3 Env Arms on v0.3 (R4-corrected labels) - full 256

Re-run of the engineered sweep after the gate-ground-truth correction
(env v0.3: 24 bare buy questions regated to no-gate per audited R4). Full
256-seed coverage this time, both frontier Claude models.

## Result (full 256, corrected gate labels)

| lambda | oracle | sonnet (frontier) | gap | haiku (cheaper) | gap | haiku gate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.1 | 0.9470 | 0.9448 (gate 1.0) | +0.002 | 0.8203 | +0.127 | **0.80** |
| 0.3 | 0.8410 | 0.8344 (gate 1.0) | +0.007 | 0.7147 | +0.126 | **0.80** |
| 0.6 | 0.6819 | 0.6688 (gate 1.0) | +0.013 | 0.5563 | +0.126 | **0.80** |

## Two findings

**1. Act 3 frontier kill CONFIRMED (no longer provisional).** The engineered
prompt takes the frontier model (sonnet) to within 0.2-1.3% of the analytic
reward ceiling with PERFECT gate recall, on the full 256 corrected seeds.
GRPO's ceiling is the oracle; it cannot beat a policy already at the ceiling
with a perfect safety gate. At frontier scale, no training is justified.

**2. The cheaper-model degradation is the RL Phase 2 motivation, made
concrete.** The SAME engineered prompt on a cheaper model (haiku) loses 12.6
reward points AND drops gate recall to 0.80 - it misses one in five required
human gates. Capability down -> the prompted policy is both worse and UNSAFE.

This is the honest bridge to why the small-local-model column needs training:
a cost-constrained model prompted alone is unlikely to be safe. Qwen
0.5B-1.5B (A1) will very likely be worse than haiku, so SFT/GRPO - with the
deterministic gate floor as a safety backstop - is genuinely motivated. A1
with the actual small models still runs on the GPU box to make this concrete.

## Why the v0.3 correction mattered

On the wrong v0.1 gate labels, haiku's gate behavior would have been scored
against a target that itself contradicted the audited risk convention. The
pre-GPU fidelity self-check caught the conflict; aligning to R4 is what makes
the haiku gate-failure signal both real and correctly measured. Checking
before training earned its keep.

## Honesty limits (unchanged)

env fidelity: model-derived p, always-adequate deep, small cost sample.
"sonnet ~= oracle" and "haiku unsafe" are both under this simulator; haiku is
a within-family proxy for "cheaper model", not Qwen. A1 replaces it with real
small models.
