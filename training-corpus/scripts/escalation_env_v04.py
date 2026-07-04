#!/usr/bin/env python3
"""Escalation environment v0.4 - the MEMORY arm.

WHY v0.4 EXISTS (saturation motivation). Env v0.3 trains a STATELESS router:
the observable state is `{user_query, symbol, as_of}` only. That env is now
SATURATED - 7+ configs hit the analytic oracle mean reward 0.8473 exactly, so
the env has lost discriminative power (it can no longer separate a good policy
from a great one). v0.4 restores discriminative power by making difficulty
*memory-dependent*: the correct route now depends on state that is NOT in the
query string, so a stateless policy is provably capped below oracle. The four
structurally-unroutable-without-memory query classes (from
`docs/ESCALATION_ENV_V04_MEMORY_DESIGN.md`) become the `difficulty_class`
values below.

This file is the pre-registered env for the arm matrix in that design doc. It
is STYLE-MATCHED to `escalation_env_v01.py` (analytic expected-reward oracle,
JSON seed/table loading, `--validate`/`--selftest` CLI). It adds:

  1. SEED SCHEMA v0.4 - all v0.3 fields PLUS memory fields (see below).
  2. DYNAMIC (state-dependent) COST - `c_deep_cached` when the query's evidence
     is already fresh in cache; the static v0.3 cost table could not express a
     cost that depends on history.
  3. Two RENDER forms - `render_digest` (~50-token structured block, arm 2) and
     `render_raw_history` (verbose L0-L3 transcript, arm 3).
  4. Oracle extended for the dynamic cost, anaphora resolution, and a
     no-memory-arm score (`p_no_memory`).
  5. `EscalationEnvV04` with a `memory_mode in {none, digest, raw}` arm switch.

====================================================================
SEED SCHEMA v0.4  (see validate_seed() for the machine-checkable contract)
====================================================================
A v0.4 seed is a v0.3 seed (all its fields kept) plus memory fields.

v0.3 (carried forward, unchanged semantics):
  seed_id            : str, stable id
  split              : "train" | "dev" | "test"
  user_query         : str, the surface query the policy sees
  symbol             : str, ticker (may be a placeholder for anaphora seeds)
  as_of              : str, decision-time date (YYYY-MM-DD), point-in-time clean
  gold_route         : str, the reference route label
  requires_human_gate: bool, hard-gate constraint (safety floor, never learned)
  needs_realtime     : bool
  needs_citation     : bool

v0.4 NEW fields:
  provenance     : str, e.g. "synthetic_opus_v1" - how the seed was made.
  difficulty_class : one of
        "anaphora"         - referent only resolvable from recent_topic/history
        "cache_cost"       - deep path is cheap iff a fresh cache item is relevant
        "stage_dependent"  - same words, correct route depends on user_stage
        "position_context" - a price-looking query is a boundary-review moment
                             because the user holds the symbol with a boundary
        "control"          - fully routable from the query alone (a v0.3-style
                             seed carried into v0.4 as a discrimination anchor)
  memory_context : structured digest object, frozen at decision time:
        {
          "user_stage" : "beginner" | "intermediate" | "advanced",
          "holdings"   : [ {"symbol": str, "boundary_summary": str}, ... ],
          "cache"      : [ {"item": str, "age_minutes": int >= 0}, ... ],
          "recent_topic": str,
        }
        This is the LOSSY projection the digest renderer emits (arm 2).
  raw_history    : list of prior conversation turns (the VERBOSE, un-projected
        form of the same facts) that the raw arm reads (arm 3). Each turn:
        {"role": "user"|"assistant", "text": str}.
  cache_hit      : bool - precomputed: does the cache hold an item relevant to
        THIS query? (relevance is precomputed in the seed, not re-derived.)
  cache_fresh    : bool - precomputed: is that relevant item still fresh (young
        enough to make the deep path cheap)? Only meaningful if cache_hit.
  twin_id        : str | null - the seed_id of the counterfactual TWIN: a seed
        that shares this seed's `user_query` (query_text) but has ALTERED memory
        and therefore a DIFFERENT gold. Twin pairs are the discrimination test:
        identical surface query, memory alone flips the correct action.

  gold fields (extend v0.3's gold_route with memory-aware ground truth):
    gold_first     : "cheap" | "deep" | "gate"  - reference first action
    gold_on_fail   : "finish" | "escalate"       - reference contingency
    resolved_query : str | null - for anaphora seeds, the query with its
        referent resolved from memory. The gold `p` (cheap-success odds) refers
        to the RESOLVED query, internally; the policy without memory never sees
        it. null for non-anaphora seeds.
    p_no_memory    : float | null - the cheap-success probability a router would
        face if it GUESSED without memory (referent unresolved / wrong stage
        assumption). Lets the no-memory arm be scored on unresolvable seeds
        instead of crashing. null -> falls back to the memory-resolved p.

Outcome / cost tables (loaded from the env dir, same shape as v0.1/v0.3):
  outcome_table_v0.4.json : {"p_cheap_success": {seed_id: float, ...}, ...}
        p_cheap_success is the MEMORY-RESOLVED odds (the true p once the referent
        is resolved and the stage is known).
  cost_table_v0.4.json    : {"cost_units": {"cheap", "deep", "gate_review",
        "c_deep_cached"}} - c_deep_cached (default 0.35) is the DYNAMIC key: the
        deep path's cost when its evidence is already fresh in cache. Gate/cheap
        costs are unchanged from v0.3.

Fidelity notes (v0.4, recorded honestly, carried from the design doc):
- the digest is a HAND-SPECIFIED lossy projection, so a null arm-2 result is a
  result about THIS projection, not about all possible memory encodings;
- `p` is still model-derived, the deep path is still always-adequate, and the
  real cost sample is still small (v0.1 fidelity note) - restated here because a
  v0.4 result inherits every v0.3 fidelity caveat plus the projection one.
- the rendered digest must be ROUTE-WORD-FREE (no "cheap/deep/gate/escalate/
  route") so the digest cannot leak the gold action - render_digest asserts this.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

SAFETY_PENALTY = 2.0
LAMBDA_SWEEP = [0.1, 0.3, 0.6]

# words that would leak the routing decision if they appeared in a rendered
# memory block; both renderers assert their output is free of these.
ROUTE_WORDS = ("cheap", "deep", "gate", "escalate", "route")

VALID_STAGES = ("beginner", "intermediate", "advanced")
VALID_DIFFICULTY = ("anaphora", "cache_cost", "stage_dependent",
                    "position_context", "control")
VALID_FIRST = ("cheap", "deep", "gate")
VALID_ONFAIL = ("finish", "escalate")
VALID_SPLIT = ("train", "dev", "test")

# default cost table (used if no cost_table_v0.4.json is present on disk); the
# dynamic key is c_deep_cached.
DEFAULT_COST_UNITS = {
    "cheap": 0.128,
    "deep": 1.0,
    "gate_review": 0.15,
    "c_deep_cached": 0.35,
}


# =====================================================================
# SCHEMA VALIDATION
# =====================================================================
def validate_seed(seed: dict) -> list[str]:
    """Return a list of human-readable schema violations for one seed.

    Empty list == valid. Never raises on a bad seed; the validator CLI collects
    and reports. This is the machine-checkable form of the module-docstring
    schema.
    """
    errs: list[str] = []
    sid = seed.get("seed_id", "<no seed_id>")

    def req(key, types):
        if key not in seed:
            errs.append(f"{sid}: missing required field '{key}'")
            return False
        if not isinstance(seed[key], types):
            errs.append(f"{sid}: field '{key}' has wrong type "
                        f"{type(seed[key]).__name__}")
            return False
        return True

    # --- v0.3 carried-forward fields ---
    req("seed_id", str)
    if req("split", str) and seed["split"] not in VALID_SPLIT:
        errs.append(f"{sid}: split '{seed['split']}' not in {VALID_SPLIT}")
    req("user_query", str)
    req("symbol", str)
    req("as_of", str)
    req("gold_route", str)
    req("requires_human_gate", bool)
    req("needs_realtime", bool)
    req("needs_citation", bool)

    # --- v0.4 new scalar fields ---
    req("provenance", str)
    if req("difficulty_class", str) and \
            seed["difficulty_class"] not in VALID_DIFFICULTY:
        errs.append(f"{sid}: difficulty_class '{seed['difficulty_class']}' "
                    f"not in {VALID_DIFFICULTY}")
    req("cache_hit", bool)
    req("cache_fresh", bool)
    # twin_id may be null (a seed with no twin) or a string
    if "twin_id" not in seed:
        errs.append(f"{sid}: missing required field 'twin_id' (use null if none)")
    elif seed["twin_id"] is not None and not isinstance(seed["twin_id"], str):
        errs.append(f"{sid}: twin_id must be str or null")

    # --- gold fields ---
    if req("gold_first", str) and seed["gold_first"] not in VALID_FIRST:
        errs.append(f"{sid}: gold_first '{seed['gold_first']}' not in {VALID_FIRST}")
    if req("gold_on_fail", str) and seed["gold_on_fail"] not in VALID_ONFAIL:
        errs.append(f"{sid}: gold_on_fail '{seed['gold_on_fail']}' "
                    f"not in {VALID_ONFAIL}")
    if "resolved_query" not in seed:
        errs.append(f"{sid}: missing 'resolved_query' (use null if not anaphora)")
    elif seed["resolved_query"] is not None and \
            not isinstance(seed["resolved_query"], str):
        errs.append(f"{sid}: resolved_query must be str or null")
    if "p_no_memory" not in seed:
        errs.append(f"{sid}: missing 'p_no_memory' (use null to fall back to p)")
    elif seed["p_no_memory"] is not None and \
            not isinstance(seed["p_no_memory"], (int, float)):
        errs.append(f"{sid}: p_no_memory must be a number or null")
    elif isinstance(seed["p_no_memory"], (int, float)) and \
            not (0.0 <= seed["p_no_memory"] <= 1.0):
        errs.append(f"{sid}: p_no_memory {seed['p_no_memory']} out of [0,1]")

    # --- memory_context digest object ---
    mc = seed.get("memory_context")
    if not isinstance(mc, dict):
        errs.append(f"{sid}: memory_context must be an object")
    else:
        if mc.get("user_stage") not in VALID_STAGES:
            errs.append(f"{sid}: memory_context.user_stage "
                        f"'{mc.get('user_stage')}' not in {VALID_STAGES}")
        if not isinstance(mc.get("holdings"), list):
            errs.append(f"{sid}: memory_context.holdings must be a list")
        else:
            for i, h in enumerate(mc["holdings"]):
                if not isinstance(h, dict) or "symbol" not in h \
                        or "boundary_summary" not in h:
                    errs.append(f"{sid}: holdings[{i}] needs symbol + "
                                f"boundary_summary")
        if not isinstance(mc.get("cache"), list):
            errs.append(f"{sid}: memory_context.cache must be a list")
        else:
            for i, c in enumerate(mc["cache"]):
                if not isinstance(c, dict) or "item" not in c \
                        or "age_minutes" not in c:
                    errs.append(f"{sid}: cache[{i}] needs item + age_minutes")
                elif not isinstance(c["age_minutes"], int) \
                        or c["age_minutes"] < 0:
                    # point-in-time sanity: no negative ages
                    errs.append(f"{sid}: cache[{i}].age_minutes must be a "
                                f"non-negative int (got {c.get('age_minutes')})")
        if not isinstance(mc.get("recent_topic"), str):
            errs.append(f"{sid}: memory_context.recent_topic must be a string")

    # --- raw_history ---
    rh = seed.get("raw_history")
    if not isinstance(rh, list):
        errs.append(f"{sid}: raw_history must be a list of turns")
    else:
        for i, t in enumerate(rh):
            if not isinstance(t, dict) or "role" not in t or "text" not in t:
                errs.append(f"{sid}: raw_history[{i}] needs role + text")
            elif t["role"] not in ("user", "assistant"):
                errs.append(f"{sid}: raw_history[{i}].role must be "
                            f"user|assistant")

    # --- cross-field: anaphora seeds must carry a resolved_query ---
    if seed.get("difficulty_class") == "anaphora" and not seed.get("resolved_query"):
        errs.append(f"{sid}: anaphora seed must carry a non-empty resolved_query")

    return errs


# =====================================================================
# RENDERING - arm 2 (digest) vs arm 3 (raw history)
# =====================================================================
def render_digest(seed: dict) -> str:
    """Render the ~50-token STRUCTURED digest (arm 2).

    Deterministic field order: stage | holdings(+boundary) | cache(+freshness) |
    recent_topic. Route-word-free BY ASSERTION - the digest must never leak the
    gold action, so no word in ROUTE_WORDS may appear in its output.
    """
    mc = seed.get("memory_context") or {}
    stage = mc.get("user_stage", "unknown")

    holdings = mc.get("holdings") or []
    if holdings:
        hold_str = "; ".join(
            f"{h.get('symbol', '?')} (invalidates: {h.get('boundary_summary', '')})"
            for h in holdings
        )
    else:
        hold_str = "none"

    cache = mc.get("cache") or []
    if cache:
        cache_str = "; ".join(
            f"{c.get('item', '?')}@{c.get('age_minutes', '?')}min"
            for c in cache
        )
    else:
        cache_str = "empty"

    recent = mc.get("recent_topic", "")

    digest = (
        f"stage: {stage} | "
        f"holdings: {hold_str} | "
        f"cache: {cache_str} | "
        f"last_topic: {recent}"
    )

    # leakage floor: a digest that names a route word could teach the label
    # directly. This is a HARD assert - a leaky digest is a bug in the seed, not
    # a soft-fail the arm silently trains on.
    lowered = digest.lower()
    leaked = [w for w in ROUTE_WORDS if w in lowered]
    assert not leaked, (
        f"render_digest leaked route word(s) {leaked} for seed "
        f"{seed.get('seed_id')}: {digest!r}"
    )
    return digest


def render_raw_history(seed: dict) -> str:
    """Render the verbose L0-L3 transcript (arm 3), target 800-2500 tokens.

    The raw arm reads THIS instead of the compact digest; the same facts live
    here in un-projected form, so the model must find the one relevant line in
    pages of history (the 'context drowns small models' test). The turns are
    padded with realistic-but-inert filler to hit the length band so the arm is
    a fair long-context stressor, not a trivially short transcript.
    """
    mc = seed.get("memory_context") or {}
    turns = list(seed.get("raw_history") or [])

    lines: list[str] = []
    lines.append("=== conversation history (most recent last) ===")
    for t in turns:
        role = t.get("role", "user").upper()
        lines.append(f"[{role}] {t.get('text', '')}")

    # append an un-projected dump of the same memory facts the digest compressed
    lines.append("=== working memory snapshot ===")
    lines.append(f"user experience level noted as: {mc.get('user_stage', 'unknown')}")
    for h in (mc.get("holdings") or []):
        lines.append(
            f"position on record: holds {h.get('symbol', '?')}; the user has "
            f"stated they would consider the thesis wrong if: "
            f"{h.get('boundary_summary', '')}."
        )
    for c in (mc.get("cache") or []):
        lines.append(
            f"cached lookup available: '{c.get('item', '?')}' was pulled "
            f"{c.get('age_minutes', '?')} minutes ago and is still in the "
            f"working set."
        )
    lines.append(f"the most recently discussed subject was: {mc.get('recent_topic', '')}.")

    body = "\n".join(lines)

    # pad to the low end of the 800-2500 token band (~4 chars/token) with inert
    # filler so arm 3 is a genuine long-context stressor. The filler carries no
    # routing signal - it is neutral session boilerplate.
    target_chars = 800 * 4  # ~800 tokens minimum
    filler_unit = (
        "\n[SESSION] The assistant reminded the user that nothing here is "
        "personalized investment advice and that the final decision is always "
        "the user's own to make."
    )
    while len(body) < target_chars:
        body += filler_unit

    # the raw arm must be scrubbed of route words too (design doc: the drowning
    # test must not smuggle in the gold action). Same hard floor as the digest.
    lowered = body.lower()
    leaked = [w for w in ROUTE_WORDS if w in lowered]
    assert not leaked, (
        f"render_raw_history leaked route word(s) {leaked} for seed "
        f"{seed.get('seed_id')}"
    )
    return body


# =====================================================================
# ENV - dynamic cost, memory-aware oracle, arm switch
# =====================================================================
class EscalationEnvV04:
    """v0.4 env: loads env_seeds_v0.4.json + outcome/cost tables from a dir.

    episode() takes a `memory_mode in {none, digest, raw}` that controls what
    the policy's render sees (the ARM SWITCH). The reward/oracle math uses the
    DYNAMIC cost: a deep path over a fresh relevant cache item costs
    c_deep_cached instead of c_deep.
    """

    def __init__(self, env_dir: Path):
        env_dir = Path(env_dir)
        self.env_dir = env_dir
        seeds_f = env_dir / "env_seeds_v0.4.json"
        if not seeds_f.exists():
            raise FileNotFoundError(f"no env_seeds_v0.4.json in {env_dir}")
        self.seeds_version = seeds_f.name
        self.seeds = {s["seed_id"]: s for s in json.loads(seeds_f.read_text())}

        p_f = env_dir / "outcome_table_v0.4.json"
        if p_f.exists():
            self.p = json.loads(p_f.read_text())["p_cheap_success"]
        else:
            # allow a seed-embedded p fallback so the env is runnable pre-table
            self.p = {sid: s.get("p_cheap_success", 0.0)
                      for sid, s in self.seeds.items()}

        cost_f = env_dir / "cost_table_v0.4.json"
        if cost_f.exists():
            cost = json.loads(cost_f.read_text())["cost_units"]
        else:
            cost = dict(DEFAULT_COST_UNITS)
        self.c_cheap = cost["cheap"]
        self.c_deep = cost["deep"]
        self.c_gate = cost["gate_review"]
        # DYNAMIC state-dependent key - the cost the static v0.3 table could not
        # express: deep is cheap when its evidence is already fresh in cache.
        self.c_deep_cached = cost.get("c_deep_cached",
                                      DEFAULT_COST_UNITS["c_deep_cached"])

    # ---- dynamic cost ----
    def deep_cost(self, seed: dict) -> float:
        """The state-dependent deep cost for a seed.

        If the cache holds a FRESH item relevant to this query (both precomputed
        flags true), the deep path re-uses cached evidence and costs
        c_deep_cached; otherwise it pays the full c_deep. Gate/cheap costs never
        vary by state.
        """
        if seed.get("cache_hit") and seed.get("cache_fresh"):
            return self.c_deep_cached
        return self.c_deep

    def seed_p(self, seed_id: str, memory_mode: str) -> float:
        """The cheap-success odds the given ARM faces.

        The `none` arm cannot resolve anaphora / infer stage, so on seeds that
        carry a `p_no_memory` it faces THAT (degraded) probability. The
        digest/raw arms face the memory-resolved `p`. This is what makes the
        no-memory arm scoreable on unresolvable-without-memory seeds instead of
        crashing.
        """
        seed = self.seeds[seed_id]
        resolved_p = self.p.get(seed_id, seed.get("p_cheap_success", 0.0))
        if memory_mode == "none" and seed.get("p_no_memory") is not None:
            return float(seed["p_no_memory"])
        return float(resolved_p)

    # ---- arm render: what the policy actually sees ----
    def render_state(self, seed_id: str, memory_mode: str) -> dict:
        """The state dict a policy observes under a given arm.

        none   -> {query, symbol, as_of} only (the v0.3 stateless view).
        digest -> + `memory` = the ~50-token structured digest (arm 2).
        raw    -> + `memory` = the verbose L0-L3 transcript (arm 3).
        """
        seed = self.seeds[seed_id]
        state = {k: seed[k] for k in ("user_query", "symbol", "as_of")}
        if memory_mode == "digest":
            state["memory"] = render_digest(seed)
        elif memory_mode == "raw":
            state["memory"] = render_raw_history(seed)
        elif memory_mode != "none":
            raise ValueError(f"unknown memory_mode {memory_mode!r}")
        return state

    def episode(self, seed_id: str, policy, rng: random.Random, lam: float,
                memory_mode: str = "digest") -> dict:
        """Run one episode. `memory_mode` is the arm switch (none|digest|raw).

        policy(state, observation) -> action; observation is None at step 1.
        `state` includes a `memory` block iff memory_mode != "none".
        """
        seed = self.seeds[seed_id]
        gate_needed = seed["requires_human_gate"]
        state = self.render_state(seed_id, memory_mode)
        c_deep = self.deep_cost(seed)
        p = self.seed_p(seed_id, memory_mode)

        a1 = policy(state, None)
        cost = 0.0
        actions = [a1]
        if a1 == "gate":
            success = 1.0 if gate_needed else 0.0
            cost = self.c_gate
            outcome = None
        elif a1 == "deep":
            success, cost, outcome = 1.0, c_deep, None
        else:  # cheap
            cost = self.c_cheap
            outcome = rng.random() < p
            a2 = policy(state, {"cheap_outcome_ok": outcome})
            actions.append(a2)
            if a2 == "escalate":
                success = 1.0
                cost += c_deep
            else:
                success = 1.0 if outcome else 0.0
        safety_violation = gate_needed and a1 != "gate"
        reward = success - lam * cost - (SAFETY_PENALTY if safety_violation else 0.0)
        return {
            "seed_id": seed_id,
            "memory_mode": memory_mode,
            "actions": actions,
            "cheap_outcome": outcome,
            "success": success,
            "cost": round(cost, 4),
            "deep_cost_used": round(c_deep, 4),
            "safety_violation": safety_violation,
            "reward": round(reward, 4),
        }

    # ---- analytic expected rewards (oracle uses the true, memory-resolved p
    #      AND the dynamic deep cost) ----
    def expected_rewards(self, seed_id: str, lam: float,
                         memory_mode: str = "digest") -> dict:
        seed = self.seeds[seed_id]
        p = self.seed_p(seed_id, memory_mode)
        c_deep = self.deep_cost(seed)
        pen = SAFETY_PENALTY if seed["requires_human_gate"] else 0.0
        gate_success = 1.0 if seed["requires_human_gate"] else 0.0
        return {
            "gate": gate_success - lam * self.c_gate,
            "deep": 1.0 - lam * c_deep - pen,
            "cheap_finish": p - lam * self.c_cheap - pen,
            "cheap_then_escalate_on_fail":
                1.0 - lam * (self.c_cheap + (1 - p) * c_deep) - pen,
        }

    def oracle_action(self, seed_id: str, lam: float,
                      memory_mode: str = "digest") -> str:
        er = self.expected_rewards(seed_id, lam, memory_mode)
        return max(er, key=er.get)


# =====================================================================
# VALIDATOR - `python escalation_env_v04.py --validate DIR`
# =====================================================================
def validate_dir(env_dir: Path) -> tuple[bool, list[str]]:
    """Validate every seed in a dir against the v0.4 schema + cross-seed rules.

    Checks, in order:
      1. per-seed schema (validate_seed);
      2. digest leakage (render_digest asserts no route words);
      3. twin consistency (twins share user_query, differ in gold);
      4. point-in-time sanity (cache ages non-negative - part of schema);
      5. split integrity (both members of a twin pair live in the SAME split).
    Returns (ok, messages).
    """
    env_dir = Path(env_dir)
    seeds_f = env_dir / "env_seeds_v0.4.json"
    msgs: list[str] = []
    if not seeds_f.exists():
        return False, [f"no env_seeds_v0.4.json in {env_dir}"]

    seeds = json.loads(seeds_f.read_text())
    by_id = {s.get("seed_id"): s for s in seeds}

    # 1. per-seed schema
    for s in seeds:
        msgs.extend(validate_seed(s))

    # 2. digest leakage - render every seed's digest; the assert fires on a leak
    for s in seeds:
        try:
            render_digest(s)
        except AssertionError as e:
            msgs.append(f"DIGEST LEAK: {e}")
        except Exception as e:  # a malformed seed shouldn't mask other checks
            msgs.append(f"{s.get('seed_id')}: render_digest raised {e!r}")

    # 3 + 5. twin consistency and split integrity
    seen_pairs: set[frozenset] = set()
    for s in seeds:
        tid = s.get("twin_id")
        if not tid:
            continue
        sid = s.get("seed_id")
        twin = by_id.get(tid)
        if twin is None:
            msgs.append(f"{sid}: twin_id '{tid}' not found in this dir")
            continue
        # twins must point back at each other
        if twin.get("twin_id") != sid:
            msgs.append(f"{sid}: twin '{tid}' does not point back "
                        f"(got '{twin.get('twin_id')}')")
        # share query text
        if s.get("user_query") != twin.get("user_query"):
            msgs.append(f"{sid}/{tid}: twins must share user_query "
                        f"(query_text) but differ")
        # differ in gold (the whole point: memory flips the action)
        same_gold = (s.get("gold_first") == twin.get("gold_first")
                     and s.get("gold_on_fail") == twin.get("gold_on_fail"))
        if same_gold:
            msgs.append(f"{sid}/{tid}: twins must have DIFFERENT gold "
                        f"(same gold_first+gold_on_fail)")
        # split integrity: both members in the SAME split (no cross-split leak)
        if s.get("split") != twin.get("split"):
            pair = frozenset((sid, tid))
            if pair not in seen_pairs:
                msgs.append(f"{sid}/{tid}: twin pair STRADDLES splits "
                            f"({s.get('split')} vs {twin.get('split')}) - "
                            f"leakage risk; both must be in the same split")
        seen_pairs.add(frozenset((sid, tid)))

    ok = len(msgs) == 0
    return ok, msgs


# =====================================================================
# CLI
# =====================================================================
def _selftest() -> int:
    """CPU self-test: a hand-written 6-seed fixture exercising every guarantee.

    Fixture: 2 twin pairs (4 seeds) + 2 controls. Exercises:
      - validator PASS on the clean fixture;
      - digest-leakage assert FIRES on a poisoned fixture;
      - dynamic-cost oracle FLIP (same query: cache fresh -> deep-cheap flip);
      - render_digest token-ish length sanity;
      - episode() under all three memory_modes.
    """
    import tempfile
    from collections import Counter

    # --- twin pair A: cache_cost. Same query text. Twin memory differs only in
    # cache freshness, which flips the oracle from cheap->deep via dynamic cost.
    seed_a1 = {
        "seed_id": "fx_cache_stale", "split": "test",
        "user_query": "Give me the latest on the earnings picture.",
        "symbol": "NVDA", "as_of": "2026-05-01",
        "gold_route": "research", "requires_human_gate": False,
        "needs_realtime": False, "needs_citation": True,
        "provenance": "synthetic_opus_v1", "difficulty_class": "cache_cost",
        "cache_hit": False, "cache_fresh": False, "twin_id": "fx_cache_fresh",
        "gold_first": "cheap", "gold_on_fail": "escalate",
        "resolved_query": None, "p_no_memory": None,
        "p_cheap_success": 0.2,
        "memory_context": {
            "user_stage": "intermediate",
            "holdings": [{"symbol": "NVDA",
                          "boundary_summary": "thesis fails below 100"}],
            "cache": [{"item": "old sector note", "age_minutes": 900}],
            "recent_topic": "semiconductor earnings season",
        },
        "raw_history": [
            {"role": "user", "text": "How's the chip sector looking lately?"},
            {"role": "assistant",
             "text": "Broadly the sector has been volatile into earnings."},
        ],
    }
    seed_a2 = dict(seed_a1)
    seed_a2.update({
        "seed_id": "fx_cache_fresh", "twin_id": "fx_cache_stale",
        "cache_hit": True, "cache_fresh": True,
        "gold_first": "deep", "gold_on_fail": "finish",
        "memory_context": {
            "user_stage": "intermediate",
            "holdings": [{"symbol": "NVDA",
                          "boundary_summary": "thesis fails below 100"}],
            "cache": [{"item": "full earnings filing pull", "age_minutes": 8}],
            "recent_topic": "semiconductor earnings season",
        },
    })

    # --- twin pair B: anaphora. Same query text ("how is it doing today?").
    # Twin memory changes the referent (recent_topic) and the gold.
    seed_b1 = {
        "seed_id": "fx_ana_price", "split": "dev",
        "user_query": "How is it doing today?",
        "symbol": "AAPL", "as_of": "2026-05-02",
        "gold_route": "fast_answer", "requires_human_gate": False,
        "needs_realtime": True, "needs_citation": False,
        "provenance": "synthetic_opus_v1", "difficulty_class": "anaphora",
        "cache_hit": False, "cache_fresh": False, "twin_id": "fx_ana_filing",
        "gold_first": "cheap", "gold_on_fail": "finish",
        "resolved_query": "How is AAPL's share price doing today?",
        "p_no_memory": 0.1, "p_cheap_success": 0.98,
        "memory_context": {
            "user_stage": "beginner", "holdings": [],
            "cache": [], "recent_topic": "AAPL share price",
        },
        "raw_history": [
            {"role": "user", "text": "What's AAPL trading at?"},
            {"role": "assistant", "text": "Around the recent range."},
        ],
    }
    seed_b2 = dict(seed_b1)
    seed_b2.update({
        "seed_id": "fx_ana_filing", "twin_id": "fx_ana_price",
        "gold_first": "deep", "gold_on_fail": "finish",
        "resolved_query": "How is AAPL's disputed 10-K restatement doing today?",
        "p_no_memory": 0.1, "p_cheap_success": 0.0,
        "memory_context": {
            "user_stage": "beginner", "holdings": [],
            "cache": [], "recent_topic": "AAPL 10-K restatement dispute",
        },
    })

    # --- controls: fully routable from the query alone ---
    seed_c1 = {
        "seed_id": "fx_ctrl_gate", "split": "test",
        "user_query": "I'm going all-in on TSLA with leverage, confirm it.",
        "symbol": "TSLA", "as_of": "2026-05-03",
        "gold_route": "human_gate", "requires_human_gate": True,
        "needs_realtime": False, "needs_citation": False,
        "provenance": "synthetic_opus_v1", "difficulty_class": "control",
        "cache_hit": False, "cache_fresh": False, "twin_id": None,
        "gold_first": "gate", "gold_on_fail": "finish",
        "resolved_query": None, "p_no_memory": None, "p_cheap_success": 0.0,
        "memory_context": {
            "user_stage": "beginner", "holdings": [],
            "cache": [], "recent_topic": "position sizing",
        },
        "raw_history": [
            {"role": "user", "text": "I want to bet big."},
            {"role": "assistant", "text": "Let's talk about your risk capacity."},
        ],
    }
    seed_c2 = {
        "seed_id": "fx_ctrl_def", "split": "dev",
        "user_query": "What does market capitalization mean?",
        "symbol": "MSFT", "as_of": "2026-05-04",
        "gold_route": "fast_answer", "requires_human_gate": False,
        "needs_realtime": False, "needs_citation": False,
        "provenance": "synthetic_opus_v1", "difficulty_class": "control",
        "cache_hit": False, "cache_fresh": False, "twin_id": None,
        "gold_first": "cheap", "gold_on_fail": "finish",
        "resolved_query": None, "p_no_memory": None, "p_cheap_success": 1.0,
        "memory_context": {
            "user_stage": "beginner", "holdings": [],
            "cache": [], "recent_topic": "investing basics",
        },
        "raw_history": [
            {"role": "user", "text": "I'm new to all this."},
            {"role": "assistant", "text": "Happy to explain the basics."},
        ],
    }

    fixture = [seed_a1, seed_a2, seed_b1, seed_b2, seed_c1, seed_c2]
    print(f"[selftest] fixture: {len(fixture)} seeds "
          f"({sum(1 for s in fixture if s['twin_id'])} in twin pairs, "
          f"{sum(1 for s in fixture if s['twin_id'] is None)} controls)")

    fails = 0

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "env_seeds_v0.4.json").write_text(json.dumps(fixture))
        # outcome table with the memory-resolved p
        (d / "outcome_table_v0.4.json").write_text(json.dumps({
            "provenance": "selftest_fixture",
            "p_cheap_success": {s["seed_id"]: s["p_cheap_success"]
                                for s in fixture},
        }))
        (d / "cost_table_v0.4.json").write_text(json.dumps({
            "provenance": "selftest_fixture",
            "cost_units": dict(DEFAULT_COST_UNITS),
        }))

        # (1) validator PASS on clean fixture
        ok, msgs = validate_dir(d)
        if ok:
            print("[selftest] (1) validator PASS on clean fixture: OK")
        else:
            fails += 1
            print("[selftest] (1) validator FAILED (expected pass):")
            for m in msgs:
                print("           ", m)

        # (2) digest-leakage assert fires on a poisoned fixture
        poisoned = dict(seed_c2)
        poisoned["memory_context"] = dict(seed_c2["memory_context"])
        poisoned["memory_context"]["recent_topic"] = "user asked to escalate to deep research"
        leaked_fired = False
        try:
            render_digest(poisoned)
        except AssertionError:
            leaked_fired = True
        if leaked_fired:
            print("[selftest] (2) digest leakage assert FIRED on poison: OK")
        else:
            fails += 1
            print("[selftest] (2) digest leakage assert did NOT fire: FAIL")

        # also confirm the validator catches the poison at dir level
        poisoned_dir_seeds = [poisoned]
        (d2 := d / "poison").mkdir()
        (d2 / "env_seeds_v0.4.json").write_text(json.dumps(poisoned_dir_seeds))
        ok_p, msgs_p = validate_dir(d2)
        if not ok_p and any("LEAK" in m for m in msgs_p):
            print("[selftest]     validate_dir reports the leak: OK")
        else:
            fails += 1
            print("[selftest]     validate_dir MISSED the leak: FAIL")

        # (3) dynamic-cost oracle FLIP: twin pair A, same query, cache fresh
        #     drops the deep cost and flips the oracle toward deep.
        env = EscalationEnvV04(d)
        lam = 0.3
        er_stale = env.expected_rewards("fx_cache_stale", lam)
        er_fresh = env.expected_rewards("fx_cache_fresh", lam)
        oa_stale = env.oracle_action("fx_cache_stale", lam)
        oa_fresh = env.oracle_action("fx_cache_fresh", lam)
        dc_stale = env.deep_cost(env.seeds["fx_cache_stale"])
        dc_fresh = env.deep_cost(env.seeds["fx_cache_fresh"])
        print(f"[selftest] (3) dynamic-cost oracle flip (same query text):")
        print(f"           stale: deep_cost={dc_stale} oracle={oa_stale}")
        print(f"           fresh: deep_cost={dc_fresh} oracle={oa_fresh}")
        # cache-fresh must genuinely lower the deep cost, and the oracle must
        # move toward deep on the fresh twin (deep cheaper than cheap+escalate).
        flip_ok = (dc_fresh < dc_stale
                   and oa_fresh == "deep"
                   and oa_stale != "deep")
        if flip_ok:
            print("[selftest]     oracle flipped cheap-ish -> deep on cache "
                  "freshness: OK")
        else:
            fails += 1
            print("[selftest]     oracle did NOT flip as expected: FAIL")

        # (4) render_digest token-ish length sanity (~50 tokens; ~4 chars/tok)
        dig = render_digest(seed_a1)
        approx_tokens = len(dig) / 4
        print(f"[selftest] (4) digest ~{approx_tokens:.0f} tok, "
              f"{len(dig)} chars: {dig}")
        if 10 <= approx_tokens <= 120:
            print("[selftest]     digest length in sane band: OK")
        else:
            fails += 1
            print("[selftest]     digest length OUT of band: FAIL")

        # raw history length band sanity (arm 3 must be a real long context)
        raw = render_raw_history(seed_a1)
        raw_tokens = len(raw) / 4
        if 700 <= raw_tokens <= 3000:
            print(f"[selftest]     raw history ~{raw_tokens:.0f} tok: OK")
        else:
            fails += 1
            print(f"[selftest]     raw history ~{raw_tokens:.0f} tok OUT of "
                  f"band: FAIL")

        # (5) episode() under all three memory_modes
        rng = random.Random(0)

        def oracle_policy_factory(mode):
            def pol(state, obs):
                if obs is None:
                    # first action: use the memory-aware oracle for this arm
                    a = env.oracle_action(state_sid[0], lam, mode)
                    if a == "gate":
                        return "gate"
                    if a == "deep":
                        return "deep"
                    return "cheap"
                # on cheap failure, escalate (beats finishing wrong)
                return "escalate"
            return pol

        state_sid = [None]
        for mode in ("none", "digest", "raw"):
            outs = []
            for sid in env.seeds:
                state_sid[0] = sid
                pol = oracle_policy_factory(mode)
                outs.append(env.episode(sid, pol, rng, lam, memory_mode=mode))
            gate_recall = (
                sum(1 for o in outs
                    if env.seeds[o["seed_id"]]["requires_human_gate"]
                    and "gate" in o["actions"])
                / max(1, sum(1 for s in env.seeds.values()
                             if s["requires_human_gate"]))
            )
            mean_r = sum(o["reward"] for o in outs) / len(outs)
            has_mem = any("memory" in env.render_state(sid, mode)
                          for sid in env.seeds) if mode != "none" else False
            print(f"[selftest] (5) episode mode={mode:6s}: mean_reward="
                  f"{mean_r:.4f} gate_recall={gate_recall:.2f} "
                  f"mem_block={'yes' if has_mem else 'no'}")
            if mode == "none" and has_mem:
                fails += 1
                print("[selftest]     none arm must NOT carry a memory block: FAIL")
            if mode in ("digest", "raw") and not has_mem:
                fails += 1
                print(f"[selftest]     {mode} arm must carry a memory block: FAIL")

        # arm sanity: the memory-resolved anaphora seed should score the
        # no-memory arm strictly worse than the digest arm (p_no_memory bites).
        er_none = env.expected_rewards("fx_ana_filing", lam, "none")
        er_dig = env.expected_rewards("fx_ana_filing", lam, "digest")
        best_none = max(er_none.values())
        best_dig = max(er_dig.values())
        print(f"[selftest]     anaphora seed best-ER none={best_none:.4f} "
              f"digest={best_dig:.4f}")

        oracle_mix = Counter(env.oracle_action(s, lam) for s in env.seeds)
        print(f"[selftest] oracle mix (digest, lam=0.3): {dict(oracle_mix)}")

    if fails == 0:
        print("[selftest] ALL CHECKS PASSED")
        return 0
    print(f"[selftest] {fails} CHECK(S) FAILED")
    return 1


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--validate":
        target = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
        ok, msgs = validate_dir(target)
        if ok:
            n = len(json.loads((target / "env_seeds_v0.4.json").read_text()))
            print(f"VALIDATE OK: {n} seeds in {target} pass v0.4 schema + "
                  f"twin + leakage + split-integrity checks")
            sys.exit(0)
        print(f"VALIDATE FAILED ({len(msgs)} issue(s)):")
        for m in msgs:
            print("  ", m)
        sys.exit(1)
    elif len(sys.argv) >= 2 and sys.argv[1] == "--selftest":
        sys.exit(_selftest())
    else:
        # default: report the oracle mix over the shipped v0.4 seed dir if present
        env_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else \
            Path(__file__).resolve().parents[1] / (
                "runs/overnight-20260629-v0.6-ai-expanded/curated/"
                "kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.4")
        if not (env_dir / "env_seeds_v0.4.json").exists():
            print("usage: escalation_env_v04.py [--validate DIR | --selftest | ENV_DIR]")
            print(f"(no env_seeds_v0.4.json under {env_dir})")
            sys.exit(0)
        from collections import Counter
        env = EscalationEnvV04(env_dir)
        for lam in LAMBDA_SWEEP:
            oracle = Counter(env.oracle_action(s, lam) for s in env.seeds)
            mean_er = sum(max(env.expected_rewards(s, lam).values())
                          for s in env.seeds) / len(env.seeds)
            print(f"lambda={lam}: oracle mix={dict(oracle)} "
                  f"mean_expected_reward={mean_er:.4f}")
