#!/usr/bin/env python3
"""Plan C: Training-Free GRPO loop (formalization of the rung-4 method).

The rung-4 risk pass already did ONE round of this by hand: sample a policy,
find where it errs, extract contrastive lessons, inject them, re-measure. This
formalizes it into the iterative shape of Tencent's Training-Free GRPO - no
gradient steps, the "learned parameter" is a natural-language experience
library:

  for round in 1..N:
    1. rollout: run the current policy (prompt + library) on a batch of TRAIN
       seeds via a pluggable rollout_backend, K samples each
    2. semantic advantage: within each seed's group, contrast higher-reward vs
       lower-reward rollouts (reward from a pluggable reward_fn on TRAIN only)
    3. library update: distill the contrast into <=M new/edited lessons
       (lesson_backend), keeping the library small; run a regression check so a
       new lesson cannot drop reward on already-solved seeds
    4. stop when a round yields no accepted lesson (dry) or N reached

This module is backend-agnostic: rollout_backend and lesson_backend are
callables (LLM subagents, an API, or cached transcripts). It ships the loop,
the semantic-advantage/regression logic, and provenance logging; the compute
backend is supplied by the caller. TEST is never touched here - final scoring
uses eval_escalation_policy.py against the frozen eval.

Recorded honestly: this is the no-weights CONTROL column for weight-GRPO, and
it is the same family of method the rung-4 risk explib used - so its ceiling
is "how far a prompt+library can go", by construction below weight training's
potential only where label-sparse reward shaping matters.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Lesson:
    lesson_id: str
    trigger: str
    rule: str
    round_added: int


@dataclass
class ExperienceLibrary:
    lessons: list[Lesson] = field(default_factory=list)

    def as_prompt_block(self) -> str:
        if not self.lessons:
            return ""
        return "ADJUDICATED LESSONS (apply; lesson wins over instinct):\n" + "\n".join(
            f"- [{l.lesson_id}] when {l.trigger}: {l.rule}" for l in self.lessons)


def semantic_advantage(group: list[dict]) -> dict | None:
    """group: [{"seed_id","completion","reward"}]. Return a contrast pair
    (best vs worst) if there is reward spread worth learning from, else None."""
    if len(group) < 2:
        return None
    hi = max(group, key=lambda g: g["reward"])
    lo = min(group, key=lambda g: g["reward"])
    if hi["reward"] - lo["reward"] < 1e-6:
        return None
    return {"seed_id": hi["seed_id"], "better": hi, "worse": lo,
            "advantage": round(hi["reward"] - lo["reward"], 4)}


def run(
    train_seed_ids: list[str],
    rollout_backend: Callable[[list[str], ExperienceLibrary, int], list[dict]],
    reward_fn: Callable[[str, str], float],
    lesson_backend: Callable[[list[dict], ExperienceLibrary], list[Lesson]],
    regression_reward: Callable[[ExperienceLibrary], float],
    rounds: int = 4,
    k: int = 8,
    max_new_lessons_per_round: int = 3,
) -> dict:
    lib = ExperienceLibrary()
    history = []
    for rnd in range(1, rounds + 1):
        rollouts = rollout_backend(train_seed_ids, lib, k)  # [{seed_id,completion}]
        by_seed: dict[str, list[dict]] = {}
        for r in rollouts:
            r["reward"] = reward_fn(r["seed_id"], r["completion"])
            by_seed.setdefault(r["seed_id"], []).append(r)
        contrasts = [c for c in (semantic_advantage(g) for g in by_seed.values()) if c]
        contrasts.sort(key=lambda c: -c["advantage"])
        before = regression_reward(lib)
        proposed = lesson_backend(contrasts[:max_new_lessons_per_round], lib)
        accepted = []
        for les in proposed:
            trial = ExperienceLibrary(lib.lessons + [les])
            if regression_reward(trial) + 1e-9 >= before:  # no-regression gate
                lib = trial
                accepted.append(les)
        after = regression_reward(lib)
        history.append({"round": rnd, "contrasts": len(contrasts),
                        "proposed": len(proposed), "accepted": len(accepted),
                        "train_reward_before": round(before, 4),
                        "train_reward_after": round(after, 4)})
        if not accepted:  # dry round
            break
    return {"final_library": [l.__dict__ for l in lib.lessons], "history": history}


if __name__ == "__main__":
    # self-test with a trivial deterministic backend (no LLM): shows the loop,
    # the no-regression gate, and dry-round stopping.
    seeds = ["s1", "s2", "s3"]
    gold = {"s1": "A", "s2": "B", "s3": "A"}

    def reward_fn(sid, comp):
        return 1.0 if comp == gold[sid] else 0.0

    state = {"round": 0}

    def rollout(ids, lib, k):
        # round 1 the policy is random-ish; after a lesson it answers correctly
        state["round"] += 1
        good = bool(lib.lessons)
        out = []
        for sid in ids:
            for j in range(k):
                comp = gold[sid] if (good or j == 0) else ("A" if sid != "s2" else "C")
                out.append({"seed_id": sid, "completion": comp})
        return out

    def lesson_backend(contrasts, lib):
        if contrasts and not lib.lessons:
            return [Lesson("L1", "any query", "answer the gold letter", 1)]
        return []

    def regression_reward(lib):
        # perfect once the lesson exists
        return 1.0 if lib.lessons else 0.5

    print(json.dumps(run(seeds, rollout, reward_fn, lesson_backend, regression_reward,
                         rounds=3, k=4), indent=1))
