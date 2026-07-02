# RL Phase 2 - Small-Model Training Plan (A / B / C) - 2026-07-02

## Why this phase exists

The three-task ladder resolved every act WITHOUT training - but only for the
question "is a frontier model + a good prompt enough?" Each kill decision
left one door open (D-2026-07-02-005): a small LOCAL model for
cost/latency/privacy is a separate decision.

That door is where training is genuinely motivated. The router and gate run
on EVERY KIWI query; doing that with a frontier model is ~100x the cost,
seconds of latency, and ships user queries to an external API. Production
constraints force a small local decision model - and a small model may not
absorb the engineered contract prompt that the frontier model did.

That is a testable hypothesis, not an excuse. Phase 2 runs the experiment
that either kills the last column honestly or authorizes training with data.

## The deliverable

A four-row comparison table on `escalation_env_v0.1`, plus the B and C
columns:

```
policy                  reward(lambda sweep)   gate_recall   cost   verdict
prompted small model    ...                    ...           ...    (motivation gate)
argmax-SFT small model  ...                    ...           ...    (does supervision suffice?)
GRPO small model        ...                    ...           ...    (does RL beat SFT?)
oracle (ceiling)        0.955/0.865/0.730      1.000         0.451  reference
```

## Plan A - small-model SFT vs GRPO on the escalation env (core)

The full apparatus already exists: environment, real-trace cost table,
stochastic outcome table, reward, analytic oracle, argmax-SFT design, budget
cap. Shortest path from here to a real GRPO run.

Steps:

- **A0 seed expansion** (no GPU): grow train seeds 256 -> ~1,024 from the
  9,879 router pool. New train-seed p via a rule-proxy calibrated against the
  256-seed ensemble p (proxy error reported); the frozen eval-256 keeps its
  ensemble p. Fidelity difference logged.
- **A1 motivation measurement** (no GPU beyond inference): Qwen2.5-0.5B and
  1.5B, prompted with the SAME engineered contract, scored on the env.
  KILL: if a prompted small model reaches within 3 reward points of the
  oracle AND gate recall >= 0.99, the last column dies honestly - record
  "small models need no training either" and stop A at A1.
- **A2 argmax-SFT** (GPU, <1h): LoRA-SFT the small model on oracle action
  labels (analytic, already generatable for all seeds). This is the
  "is supervision enough?" baseline.
- **A3 GRPO** (GPU, hours): TRL GRPOTrainer, reward = the env's expected
  reward (deterministic per parsed plan; advantage comes from within-group
  plan diversity), K=8, lambda sweep {0.1, 0.3, 0.6}.
- **A4 ratio table**: prompted / SFT / GRPO / oracle x reward, gate recall,
  cost.

KILL (pre-registered): GRPO must beat argmax-SFT by >= 3 reward points AND
not drop gate recall, else record "SFT suffices; RL not worth it here" - a
publishable negative. Budget: A100 SFT <1h + GRPO ~2-4h ~= USD 20-50, inside
the USD 100 / 24 A100h cap.

Where RL has real room: SFT learns a hard text->action map from ~800 oracle
labels; GRPO gets graded reward (the cost term is a continuous signal) and can
learn calibrated escalation on the ~74 stochastic-middle seeds where labels
are sparse. Outcome unknown - that is the experiment.

## Plan B - citation evidence-chain agentic env (the "agentic" showcase)

A genuinely multi-step episode: given a claim, the policy RETRIEVES spans from
the audited corpus, CITES (quote + paragraph-hash machine-checked; a
fabricated citation is a hard negative reward), then emits a five-way verdict.
Process reward (citation validity) + outcome reward (verdict vs audited
label), all machine-checkable. This is the minimal same-shape version of the
Kimi-Researcher evidence-chain reward already registered in LEARNING_SOURCES.

- Data: grow the 131 audited rows to 300-500 (collector proven at ~100
  rows/night; SEC/transcript pipeline exists).
- Engineering: ~2-3x Plan A (retrieval tool, episode format). Kept
  TRL-compatible via a flattened "emit the whole evidence chain in one
  generation" formulation, verified step-by-step by the reward.
- Scope: second depth after A lands; if time is short, ship the ENVIRONMENT +
  design doc only (the environment itself is presentable).

## Plan C - Training-Free GRPO formalization (one evening, contrast column)

Rung 4 already did one hand pass of contrast-extraction -> experience library.
Formalize it into the iterative version (group rollout -> semantic advantage
-> library update x N rounds) = the Tencent Training-Free GRPO shape. Goes in
the comparison table as the no-weights control for weight-GRPO, and shows the
work tracks current literature. Inference-only; a supplement, not the main
course.

## Dependency order (non-GPU parts first, per owner)

1. **Act 3 full engineered sweep** (192 remaining seeds) - firms or flips the
   provisional Act-3 kill; prerequisite for the honest "column 4" framing.
   Needs a subagent spend cycle.
2. **A0 seed expansion** + **A-SFT label generation** (pure local compute).
3. **A1 motivation measurement** scaffolding (scoring harness ready; run needs
   small-model inference - local or the user's GPU box).
4. **C** training-free loop (inference-only).
5. **B** environment build + data expansion.
6. GPU segments last, batched: A2/A3 (user pulls to A100), then B training if
   pursued.

## Honesty rules carried forward

- Every eval batch shown to a model uses anonymized ids (F-2026-07-02-006).
- The gate safety floor stays in code (risk_gate_rules_v11.py), never trusted
  to a learned policy.
- env fidelity limits (model-derived p, always-adequate deep, small cost
  sample) are restated wherever a training result is reported.
- No large GPU checkpoints in git; adapters/metrics/samples only.
- A negative result (prompt suffices / SFT suffices) is a first-class
  deliverable, recorded with numbers in DECISIONS.md.
