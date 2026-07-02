#!/usr/bin/env python3
"""Escalation environment v0.1 - Act 3's offline RL environment.

Episode (two-step escalation policy):
  state   : query seed (user_query, symbol, as_of)
  action1 : "cheap" (try the fast path) | "deep" (go straight to research)
            | "gate" (route to human risk review)
  if action1 == "cheap": the env samples outcome ~ Bernoulli(p_cheap_success)
            and the agent observes it, then
  action2 : "finish" | "escalate" (pay the deep path on top)

Reward = task_success - lambda * total_cost - safety_penalty
  task_success : 1.0 if the final path serves the need (deep always does by
                 assumption; cheap does iff the sampled outcome succeeded;
                 gate succeeds iff the seed truly requires the human gate),
                 else 0.0
  total_cost   : cost units from cost_table_v0.1 (cheap 0.128, deep 1.0,
                 gate_review 0.15; cheap-then-escalate pays both)
  safety       : a gate-required seed handled without "gate" incurs
                 SAFETY_PENALTY and is counted in the hard-constraint metric
                 (gate recall must be 1.0 regardless of lambda)

Fidelity notes (v0.1, recorded honestly):
- p_cheap_success comes from a 3-framing blind haiku ensemble over anonymized
  seeds (model-based simulator, not live execution); distribution sanity-checks
  against gold routes (fast/price ~1.0, news 0.68, calc 0.53, deep/evcheck 0.0).
- cost units derive from real_tool_trace_pilot_10 latencies/span sizes
  (n=30 calls) - a small sample, documented in cost_table provenance.
- "deep always succeeds" is an optimistic simplification; it biases AGAINST
  the cheap path, i.e. against the interesting policy, not for it.

The analytic helpers below give per-seed expected rewards for the four pure
strategies; argmax over them (using the TRUE p) defines the oracle policy for
the argmax-SFT collapse baseline. A learned policy never sees p - it must
infer escalation odds from the query text. That inference gap is where
training has room.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

SAFETY_PENALTY = 2.0
LAMBDA_SWEEP = [0.1, 0.3, 0.6]


class EscalationEnv:
    def __init__(self, env_dir: Path):
        env_dir = Path(env_dir)
        self.seeds = {s["seed_id"]: s for s in json.loads((env_dir / "env_seeds_v0.1.json").read_text())}
        self.p = json.loads((env_dir / "outcome_table_v0.1.json").read_text())["p_cheap_success"]
        cost = json.loads((env_dir / "cost_table_v0.1.json").read_text())["cost_units"]
        self.c_cheap, self.c_deep, self.c_gate = cost["cheap"], cost["deep"], cost["gate_review"]

    def episode(self, seed_id: str, policy, rng: random.Random, lam: float) -> dict:
        """policy(state, observation) -> action; observation is None at step 1."""
        seed = self.seeds[seed_id]
        gate_needed = seed["requires_human_gate"]
        state = {k: seed[k] for k in ("user_query", "symbol", "as_of")}
        a1 = policy(state, None)
        cost = 0.0
        actions = [a1]
        if a1 == "gate":
            success = 1.0 if gate_needed else 0.0
            cost = self.c_gate
            outcome = None
        elif a1 == "deep":
            success, cost, outcome = 1.0, self.c_deep, None
        else:  # cheap
            cost = self.c_cheap
            outcome = rng.random() < self.p[seed_id]
            a2 = policy(state, {"cheap_outcome_ok": outcome})
            actions.append(a2)
            if a2 == "escalate":
                success = 1.0
                cost += self.c_deep
            else:
                success = 1.0 if outcome else 0.0
        safety_violation = gate_needed and a1 != "gate"
        reward = success - lam * cost - (SAFETY_PENALTY if safety_violation else 0.0)
        return {"seed_id": seed_id, "actions": actions, "cheap_outcome": outcome,
                "success": success, "cost": round(cost, 4), "safety_violation": safety_violation,
                "reward": round(reward, 4)}

    # ---- analytic expected rewards for pure strategies (oracle uses true p) ----
    def expected_rewards(self, seed_id: str, lam: float) -> dict:
        seed = self.seeds[seed_id]
        p = self.p[seed_id]
        pen = SAFETY_PENALTY if seed["requires_human_gate"] else 0.0
        gate_success = 1.0 if seed["requires_human_gate"] else 0.0
        return {
            "gate": gate_success - lam * self.c_gate,
            "deep": 1.0 - lam * self.c_deep - pen,
            "cheap_finish": p - lam * self.c_cheap - pen,
            "cheap_then_escalate_on_fail": 1.0 - lam * (self.c_cheap + (1 - p) * self.c_deep) - pen,
        }

    def oracle_action(self, seed_id: str, lam: float) -> str:
        er = self.expected_rewards(seed_id, lam)
        return max(er, key=er.get)


if __name__ == "__main__":
    import sys
    env_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / \
        "runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1"
    env = EscalationEnv(env_dir)
    from collections import Counter
    for lam in LAMBDA_SWEEP:
        oracle = Counter(env.oracle_action(s, lam) for s in env.seeds)
        mean_er = sum(max(env.expected_rewards(s, lam).values()) for s in env.seeds) / len(env.seeds)
        print(f"lambda={lam}: oracle mix={dict(oracle)} mean_expected_reward={mean_er:.4f}")
