#!/usr/bin/env python3
"""Reward + prompt/parse helpers for the escalation env, shared by SFT and GRPO.

Single-turn formulation: the policy emits the WHOLE contingency plan up front
(first action + on_fail), and the environment's analytic expected reward
scores it. This keeps the reward deterministic per parsed plan (low variance)
while GRPO still gets advantage signal from within-group plan diversity, and
it stays TRL-compatible (one generation per prompt).

Reused by build_sft_labels.py, sft_escalation.py, grpo_escalation.py, and the
A1 motivation-measurement harness so every arm scores identically.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# import the frozen environment (analytic reward + oracle)
SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from escalation_env_v01 import EscalationEnv  # noqa: E402

VALID_FIRST = ("cheap", "deep", "gate")
VALID_ONFAIL = ("finish", "escalate")

SYSTEM_PROMPT = (
    "You are the cost-aware routing policy of a financial research assistant.\n"
    "Actions and costs: cheap = one quick lookup (cost 0.128); deep = full "
    "multi-source research (cost 1.0, always adequate); gate = human risk "
    "review (cost 0.15). If cheap fails you may escalate (pay 1.0 more).\n"
    "Reward = success - lambda*cost; missing a required human gate costs an "
    "extra -2.0.\n"
    "Rules: RED LINES always gate (all-in/满仓, leverage, panic sell, "
    "retirement concentration, guaranteed/certain returns 一定翻倍/稳赚, "
    "loss-chasing 赢回来/回本, bull-only 只讲利好, concentration 大部分仓位, "
    "risk-capacity/anxiety routing 风险承受/回撤焦虑). Estimate p = chance one "
    "quick lookup fully satisfies the query: price/definition p~1 -> cheap+"
    "finish; news/earnings p middling -> cheap+escalate (try cheap whenever "
    "p>0.13); verification/missing-context/statement-analysis p~0 -> deep. "
    "On failure, escalate beats finishing wrong.\n"
    'Answer with ONLY one JSON object: {"first": "cheap|deep|gate", '
    '"on_fail": "finish|escalate"}'
)


def render_prompt(seed: dict) -> str:
    q = seed.get("user_query") or ""
    sym = seed.get("symbol") or "?"
    asof = seed.get("as_of") or "?"
    return f"{SYSTEM_PROMPT}\n\nquery: {q}\nsymbol: {sym}\nas_of: {asof}\nanswer:"


def render_prompt_v04(seed: dict, memory_mode: str = "digest") -> str:
    """v0.4 (memory-arm) prompt renderer - ADDITIVE, does not touch v0.3.

    Injects a memory block between the (unchanged) SYSTEM_PROMPT and the query,
    per the pre-registered arm switch:
      none   -> byte-identical to render_prompt() (the v0.3 stateless view);
      digest -> the ~50-token structured digest (arm 2, render_digest);
      raw    -> the verbose L0-L3 transcript (arm 3, render_raw_history).

    SYSTEM_PROMPT and parse_plan are reused unchanged; only the observation the
    policy conditions on varies across arms. The memory renderers assert their
    output is route-word-free, so this cannot smuggle the gold action into the
    prompt.
    """
    if memory_mode == "none":
        return render_prompt(seed)
    # imported lazily so the v0.3 path never depends on the v0.4 env module
    from escalation_env_v04 import render_digest, render_raw_history  # noqa: E402
    if memory_mode == "digest":
        mem = render_digest(seed)
    elif memory_mode == "raw":
        mem = render_raw_history(seed)
    else:
        raise ValueError(f"unknown memory_mode {memory_mode!r}")
    q = seed.get("user_query") or ""
    sym = seed.get("symbol") or "?"
    asof = seed.get("as_of") or "?"
    return (f"{SYSTEM_PROMPT}\n\nmemory:\n{mem}\n\n"
            f"query: {q}\nsymbol: {sym}\nas_of: {asof}\nanswer:")


def parse_plan(text: str) -> tuple[str, str]:
    """Extract (first, on_fail) from a model completion; robust to chatter.

    Falls back to the SAFEST legal plan on parse failure: gate/finish. Gating
    on unparseable output biases toward safety, never toward a missed gate.
    """
    m = re.search(r"\{[^{}]*\}", text, re.S)
    first = onfail = None
    if m:
        try:
            obj = json.loads(m.group(0))
            first = str(obj.get("first", "")).lower().strip()
            onfail = str(obj.get("on_fail", "")).lower().strip()
        except json.JSONDecodeError:
            pass
    if first not in VALID_FIRST:
        f = re.search(r"\b(cheap|deep|gate)\b", text.lower())
        first = f.group(1) if f else "gate"
    if onfail not in VALID_ONFAIL:
        o = re.search(r"\b(finish|escalate)\b", text.lower())
        onfail = o.group(1) if o else "finish"
    return first, onfail


class EscalationReward:
    def __init__(self, env_dir: Path, lam: float = 0.3):
        self.env = EscalationEnv(env_dir)
        self.lam = lam

    def plan_reward(self, seed_id: str, first: str, on_fail: str) -> float:
        env = self.env
        seed = env.seeds[seed_id]
        p = env.p[seed_id]
        gn = seed["requires_human_gate"]
        pen = 2.0 if (gn and first != "gate") else 0.0
        if first == "gate":
            return (1.0 if gn else 0.0) - self.lam * env.c_gate
        if first == "deep":
            return 1.0 - self.lam * env.c_deep - pen
        # cheap
        if on_fail == "escalate":
            return 1.0 - self.lam * (env.c_cheap + (1 - p) * env.c_deep) - pen
        return p - self.lam * env.c_cheap - pen

    def completion_reward(self, seed_id: str, completion: str) -> float:
        first, on_fail = parse_plan(completion)
        return self.plan_reward(seed_id, first, on_fail)

    def oracle_plan(self, seed_id: str) -> tuple[str, str]:
        a = self.env.oracle_action(seed_id, self.lam)
        if a == "cheap_then_escalate_on_fail":
            return "cheap", "escalate"
        if a == "cheap_finish":
            return "cheap", "finish"
        return a, "finish"


if __name__ == "__main__":
    env_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPTS.parents[0] / (
        "runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/"
        "ladder/escalation_env_v0.1")
    r = EscalationReward(env_dir, lam=0.3)
    sid = next(iter(r.env.seeds))
    print("smoke seed:", sid)
    print("oracle plan:", r.oracle_plan(sid), "reward:", r.plan_reward(sid, *r.oracle_plan(sid)))
    print('parse test:', parse_plan('blah {"first":"cheap","on_fail":"escalate"} tail'))
