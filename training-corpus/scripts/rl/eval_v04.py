#!/usr/bin/env python3
"""Model-evaluation harness for escalation env v0.4 - the MEMORY arms.

Scores a routing policy on the v0.4 twin-pair memory exam under one arm
(`--memory-mode none|digest|raw`). It MIRRORS eval_escalation_policy.py's
model loading + greedy generation + dump-preds + structured-report style, but
scores with the env's OWN v0.4 reward math (dynamic deep cost, arm-appropriate
p via p_no_memory, gate logic) - it does NOT reimplement any of that math.

WHAT IS REUSED (import, not copied):
  - reward_escalation.render_prompt_v04(seed, memory_mode)  -> the arm prompt
  - reward_escalation.parse_plan(text)                       -> (first, on_fail)
  - escalation_env_v04.EscalationEnvV04                      -> the v0.4 env:
        .expected_rewards(seed_id, lam, memory_mode)  (dynamic cost + seed_p)
        .deep_cost(seed) / .seed_p(seed_id, mode) / .oracle_action(...)
    The plan-reward is read STRAIGHT off expected_rewards() by mapping the
    parsed (first, on_fail) plan onto the matching analytic component, so the
    none-arm uses p_no_memory, digest/raw use p, and the deep path pays the
    dynamic c_deep_cached on fresh-cache seeds - all for free from the env.

WHAT IS COPY-ADAPTED (from eval_escalation_policy.py, said so honestly):
  - the model/adapter loading block (causal|auto loader, LoRA, chat-template
    wrapping, greedy single decode, dump-preds writer). Copied rather than
    imported because eval_escalation_policy.build_prompt() renders the v0.3
    (memory-free) prompt; v0.4 needs render_prompt_v04 with a memory_mode, so
    the generation loop is adapted to call that renderer. Structure, flags, and
    tokenization are kept byte-for-byte equivalent to the v0.3 harness.

HEADLINE METRIC: twin-pair DISCRIMINATION rate - the fraction of twin pairs
(present in the split) where the model emits DIFFERENT plans for the two
members. Identical surface query, memory alone flips the correct action, so a
stateless policy MUST tie on some pairs; discrimination is the direct measure
of whether the policy attends to the memory block.

Heavy imports (torch/transformers/peft) live INSIDE main()'s model branch so
`--help` and `--selftest` are GPU-free and import-free.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# reused CPU-only helpers (no torch): the v0.4 prompt renderer + plan parser and
# the v0.4 env (analytic reward, dynamic cost, arm-aware p, oracle).
SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "rl"))
from reward_escalation import render_prompt_v04, parse_plan  # noqa: E402
from escalation_env_v04 import EscalationEnvV04  # noqa: E402

LAMBDAS = [0.1, 0.3, 0.6]


# =====================================================================
# SCORING - reads the plan reward off the env's own expected_rewards()
# =====================================================================
def plan_reward(env: EscalationEnvV04, seed_id: str, first: str, on_fail: str,
                lam: float, memory_mode: str) -> float:
    """Analytic reward of ONE parsed plan under the v0.4 arm math.

    We do NOT recompute cost/p/penalty here; we map the (first, on_fail) plan
    onto the matching component of env.expected_rewards(seed_id, lam,
    memory_mode). That dict already bakes in: the DYNAMIC deep cost
    (c_deep_cached on fresh-cache seeds via env.deep_cost), the arm-appropriate
    cheap-success odds (p_no_memory for the none arm, memory-resolved p for
    digest/raw, via env.seed_p), and the missed-gate safety penalty. So this
    function is pure plan->component selection; all the math lives in the env.
    """
    er = env.expected_rewards(seed_id, lam, memory_mode)
    if first == "gate":
        return er["gate"]
    if first == "deep":
        return er["deep"]
    # cheap
    if on_fail == "escalate":
        return er["cheap_then_escalate_on_fail"]
    return er["cheap_finish"]


def plan_cost_success(env: EscalationEnvV04, seed_id: str, first: str,
                      on_fail: str, memory_mode: str) -> tuple[float, float]:
    """The (expected cost, expected success) of a plan under the arm math.

    Uses env.deep_cost (dynamic) and env.seed_p (arm-aware) so the reported
    cost/success are consistent with the reward - not a re-derivation of them.
    """
    seed = env.seeds[seed_id]
    gate_needed = seed["requires_human_gate"]
    c_deep = env.deep_cost(seed)
    p = env.seed_p(seed_id, memory_mode)
    if first == "gate":
        return env.c_gate, (1.0 if gate_needed else 0.0)
    if first == "deep":
        return c_deep, 1.0
    if on_fail == "escalate":
        return env.c_cheap + (1 - p) * c_deep, 1.0
    return env.c_cheap, p


def score_arm(env: EscalationEnvV04, plan_of: dict, ids: list[str],
              memory_mode: str) -> dict:
    """Per-lambda reward / cost / success / gate_recall over the arm."""
    out = {}
    for lam in LAMBDAS:
        tot_r = tot_c = succ = 0.0
        gn = hit = 0
        for sid in ids:
            first, on_fail = plan_of[sid]
            seed = env.seeds[sid]
            if seed["requires_human_gate"]:
                gn += 1
                if first == "gate":
                    hit += 1
            tot_r += plan_reward(env, sid, first, on_fail, lam, memory_mode)
            c, s = plan_cost_success(env, sid, first, on_fail, memory_mode)
            tot_c += c
            succ += s
        n = max(1, len(ids))
        out[lam] = {
            "reward": round(tot_r / n, 4),
            "cost": round(tot_c / n, 4),
            "success": round(succ / n, 4),
            "gate_recall": round(hit / max(1, gn), 4),
        }
    return out


def twin_discrimination(env: EscalationEnvV04, plan_of: dict,
                        ids: list[str]) -> dict:
    """Fraction of twin pairs (both members in `ids`) with DIFFERENT plans.

    The headline metric. A pair discriminates iff the policy's (first, on_fail)
    differs between the two members - i.e. the model let the memory block flip
    its action on identical surface query text. Pairs are de-duplicated via a
    frozenset key; only pairs whose BOTH members are in the scored id set count
    (a twin split across dev/test is impossible by the validator, but a partial
    id filter could still drop one member).
    """
    idset = set(ids)
    seen: set[frozenset] = set()
    total = 0
    discriminated = 0
    examples: list[dict] = []
    for sid in ids:
        seed = env.seeds[sid]
        tid = seed.get("twin_id")
        if not tid or tid not in idset:
            continue
        key = frozenset((sid, tid))
        if key in seen:
            continue
        seen.add(key)
        total += 1
        pa = plan_of[sid]
        pb = plan_of[tid]
        differ = pa != pb
        if differ:
            discriminated += 1
        if len(examples) < 8:
            examples.append({
                "pair": sorted((sid, tid)),
                "query": seed.get("user_query", "")[:80],
                "plan_a": {"seed": sid, "first": pa[0], "on_fail": pa[1]},
                "plan_b": {"seed": tid, "first": pb[0], "on_fail": pb[1]},
                "discriminated": differ,
            })
    return {
        "twin_pairs_scored": total,
        "twin_pairs_discriminated": discriminated,
        "twin_discrimination_rate": round(discriminated / max(1, total), 4),
        "examples": examples,
    }


def plan_accuracy_by_class(env: EscalationEnvV04, plan_of: dict,
                           ids: list[str]) -> dict:
    """Per-difficulty_class plan accuracy: plan == gold (gold_first+gold_on_fail).

    Gold is the env's own oracle frozen into the seed at build time.
    """
    by_class_hit: dict[str, int] = defaultdict(int)
    by_class_tot: dict[str, int] = defaultdict(int)
    overall_hit = overall_tot = 0
    for sid in ids:
        seed = env.seeds[sid]
        cls = seed.get("difficulty_class", "unknown")
        gold = (seed["gold_first"], seed["gold_on_fail"])
        got = plan_of[sid]
        by_class_tot[cls] += 1
        overall_tot += 1
        if got == gold:
            by_class_hit[cls] += 1
            overall_hit += 1
    per_class = {
        cls: {
            "n": by_class_tot[cls],
            "plan_accuracy": round(by_class_hit[cls] / max(1, by_class_tot[cls]), 4),
        }
        for cls in sorted(by_class_tot)
    }
    return {
        "overall_plan_accuracy": round(overall_hit / max(1, overall_tot), 4),
        "per_difficulty_class": per_class,
    }


def oracle_gap(env: EscalationEnvV04, plan_of: dict, ids: list[str],
               memory_mode: str, lam: float = 0.3) -> dict:
    """Arm-appropriate oracle gap at lam: mean(oracle_reward - policy_reward).

    Oracle = env.oracle_action under THIS arm's math (so the none-arm oracle
    already faces p_no_memory - the arm-appropriate ceiling, not the digest
    ceiling). Positive gap = policy below its own arm's oracle.
    """
    tot_oracle = tot_policy = 0.0
    for sid in ids:
        er = env.expected_rewards(sid, lam, memory_mode)
        tot_oracle += max(er.values())
        first, on_fail = plan_of[sid]
        tot_policy += plan_reward(env, sid, first, on_fail, lam, memory_mode)
    n = max(1, len(ids))
    mo = tot_oracle / n
    mp = tot_policy / n
    return {
        "lambda": lam,
        "arm_oracle_mean_reward": round(mo, 4),
        "policy_mean_reward": round(mp, 4),
        "oracle_gap": round(mo - mp, 4),
    }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_report(env: EscalationEnvV04, plan_of: dict, ids: list[str],
                 memory_mode: str, extra: dict) -> dict:
    """Assemble the full structured report for one arm run."""
    disc = twin_discrimination(env, plan_of, ids)
    acc = plan_accuracy_by_class(env, plan_of, ids)
    gap = oracle_gap(env, plan_of, ids, memory_mode, lam=0.3)
    report = {
        "memory_mode": memory_mode,
        "env_dir": str(env.env_dir),
        "seeds_version": env.seeds_version,
        "split": extra.get("split"),
        "n": len(ids),
        "scores": score_arm(env, plan_of, ids, memory_mode),
        "twin_pair_discrimination": disc,
        "plan_accuracy": acc,
        "arm_oracle_gap_lambda0.3": gap,
    }
    report.update(extra.get("provenance", {}))
    return report


def mean_prompt_tokens(env: EscalationEnvV04, ids: list[str], memory_mode: str,
                       tok=None) -> dict:
    """Mean prompt-token count for the arm (quantifies raw-vs-digest context cost).

    If a HF tokenizer is passed (model mode), token counts are exact. In CPU
    modes (no tokenizer) it falls back to a ~4-chars/token estimate and flags it,
    so the metric is always populated without requiring a GPU.
    """
    total = 0
    exact = tok is not None
    for sid in ids:
        prompt = render_prompt_v04(env.seeds[sid], memory_mode)
        if exact:
            total += len(tok(prompt).input_ids)
        else:
            total += len(prompt) / 4.0
    n = max(1, len(ids))
    return {
        "mean_prompt_tokens": round(total / n, 1),
        "token_count_method": "tokenizer" if exact else "chars_over_4_estimate",
    }


# =====================================================================
# SELFTEST - CPU, no model. Loads the REAL dataset, scores 3 fabricated
# completions against 3 real seeds, and demonstrates the three properties.
# =====================================================================
def _selftest(env_dir: Path) -> int:
    """CPU self-test on the real dataset (no model).

    Demonstrates, with real seeds:
      (A) TWIN-DISCRIMINATION computation - pick one real twin pair, feed
          DIFFERENT completions -> rate 1.0; feed the SAME completion -> 0.0.
      (B) none-vs-digest p SWITCHING - an anaphora seed (p_no_memory set)
          scored under the SAME plan gives a DIFFERENT expected reward across
          arms, because seed_p returns p_no_memory for none and p for digest.
      (C) DYNAMIC-COST effect - a cache_cost twin pair: the fresh-cache member's
          deep plan is scored with c_deep_cached (cheaper) than the stale twin's.
    Fabricates 3 completions (raw model-style text) and runs them through
    parse_plan + the scoring path, so the parse->score wiring is exercised too.
    """
    print(f"[selftest] loading REAL dataset from {env_dir}")
    env = EscalationEnvV04(env_dir)
    print(f"[selftest] {len(env.seeds)} seeds loaded ({env.seeds_version})")
    fails = 0

    # ---- find real seeds to exercise each property ----
    # (A)+(C): a cache_cost twin pair where one member is cache-fresh.
    cache_pair = None
    for sid, s in env.seeds.items():
        tid = s.get("twin_id")
        if s.get("difficulty_class") != "cache_cost" or not tid:
            continue
        twin = env.seeds.get(tid)
        if twin is None:
            continue
        fresh, stale = None, None
        for m in (s, twin):
            if m.get("cache_hit") and m.get("cache_fresh"):
                fresh = m
            else:
                stale = m
        if fresh is not None and stale is not None:
            cache_pair = (fresh, stale)
            break
    # (B): an anaphora seed carrying p_no_memory.
    anaphora = next((s for s in env.seeds.values()
                     if s.get("difficulty_class") == "anaphora"
                     and s.get("p_no_memory") is not None), None)

    if cache_pair is None or anaphora is None:
        print("[selftest] FAIL: could not find required real seeds "
              f"(cache_pair={cache_pair is not None}, "
              f"anaphora={anaphora is not None})")
        return 1
    fresh, stale = cache_pair
    print(f"[selftest] using cache_cost twin pair: fresh={fresh['seed_id']} "
          f"stale={stale['seed_id']}")
    print(f"[selftest] using anaphora seed: {anaphora['seed_id']} "
          f"(p={env.seed_p(anaphora['seed_id'], 'digest'):.3f}, "
          f"p_no_memory={anaphora['p_no_memory']})")

    # 3 fabricated raw completions (model-style chatter around the JSON) run
    # through parse_plan, so the parse wiring is part of the test.
    comp_deep = 'I will do full research. {"first": "deep", "on_fail": "finish"}'
    comp_cheap_esc = 'quick look first. {"first":"cheap","on_fail":"escalate"} ok'
    comp_cheap_fin = 'a lookup suffices {"first": "cheap", "on_fail": "finish"}'
    plan_deep = parse_plan(comp_deep)
    plan_cheap_esc = parse_plan(comp_cheap_esc)
    plan_cheap_fin = parse_plan(comp_cheap_fin)
    print(f"[selftest] parse_plan wiring: {comp_deep!r} -> {plan_deep}")
    assert plan_deep == ("deep", "finish"), plan_deep
    assert plan_cheap_esc == ("cheap", "escalate"), plan_cheap_esc
    assert plan_cheap_fin == ("cheap", "finish"), plan_cheap_fin

    lam = 0.3

    # ---------------------------------------------------------------
    # (A) TWIN-DISCRIMINATION computation on the real pair
    # ---------------------------------------------------------------
    print("\n[selftest] (A) TWIN-DISCRIMINATION computation")
    ids_pair = [fresh["seed_id"], stale["seed_id"]]
    # different plans on the two members -> discriminated
    plan_of_diff = {fresh["seed_id"]: plan_deep,
                    stale["seed_id"]: plan_cheap_esc}
    d_diff = twin_discrimination(env, plan_of_diff, ids_pair)
    # same plan on both -> NOT discriminated (stateless tie)
    plan_of_same = {fresh["seed_id"]: plan_deep,
                    stale["seed_id"]: plan_deep}
    d_same = twin_discrimination(env, plan_of_same, ids_pair)
    print(f"           different-plan pair -> rate="
          f"{d_diff['twin_discrimination_rate']} "
          f"({d_diff['twin_pairs_discriminated']}/"
          f"{d_diff['twin_pairs_scored']})")
    print(f"           same-plan pair      -> rate="
          f"{d_same['twin_discrimination_rate']} "
          f"({d_same['twin_pairs_discriminated']}/"
          f"{d_same['twin_pairs_scored']})")
    if d_diff["twin_discrimination_rate"] == 1.0 and \
            d_same["twin_discrimination_rate"] == 0.0:
        print("           OK: differing plans discriminate, identical plans tie")
    else:
        fails += 1
        print("           FAIL: discrimination computation wrong")

    # ---------------------------------------------------------------
    # (B) none-vs-digest p SWITCHING: SAME plan, DIFFERENT expected reward
    # ---------------------------------------------------------------
    print("\n[selftest] (B) none-vs-digest p SWITCHING (same plan)")
    aid = anaphora["seed_id"]
    p_none = env.seed_p(aid, "none")
    p_dig = env.seed_p(aid, "digest")
    # score the SAME cheap/finish plan under both arms; reward tracks p directly
    r_none = plan_reward(env, aid, "cheap", "finish", lam, "none")
    r_dig = plan_reward(env, aid, "cheap", "finish", lam, "digest")
    print(f"           anaphora seed {aid}")
    print(f"           seed_p: none={p_none:.3f} digest={p_dig:.3f}")
    print(f"           cheap/finish reward: none={r_none:.4f} "
          f"digest={r_dig:.4f}  (delta={r_dig - r_none:+.4f})")
    if p_none != p_dig and abs(r_dig - r_none) > 1e-9:
        print("           OK: none arm uses p_no_memory, digest uses p -> "
              "same plan scores differently")
    else:
        fails += 1
        print("           FAIL: p did not switch across arms")

    # ---------------------------------------------------------------
    # (C) DYNAMIC-COST effect in scoring: fresh cache -> cheaper deep
    # ---------------------------------------------------------------
    print("\n[selftest] (C) DYNAMIC-COST effect in scoring")
    fid, stid = fresh["seed_id"], stale["seed_id"]
    dc_fresh = env.deep_cost(fresh)
    dc_stale = env.deep_cost(stale)
    # score the SAME deep/finish plan on each; the fresh-cache member pays
    # c_deep_cached so its deep reward is HIGHER (cost enters as -lam*cost).
    r_deep_fresh = plan_reward(env, fid, "deep", "finish", lam, "digest")
    r_deep_stale = plan_reward(env, stid, "deep", "finish", lam, "digest")
    print(f"           fresh {fid}: deep_cost={dc_fresh} "
          f"deep/finish reward={r_deep_fresh:.4f}")
    print(f"           stale {stid}: deep_cost={dc_stale} "
          f"deep/finish reward={r_deep_stale:.4f}")
    if dc_fresh < dc_stale and r_deep_fresh > r_deep_stale:
        print("           OK: fresh cache lowers deep cost -> same deep plan "
              "scores higher on the fresh twin")
    else:
        fails += 1
        print("           FAIL: dynamic cost did not affect scoring")

    # ---------------------------------------------------------------
    # full report assembly over the 3 real seeds (3 fabricated completions)
    # ---------------------------------------------------------------
    print("\n[selftest] full report over 3 real seeds x 3 fabricated plans")
    ids3 = [fresh["seed_id"], stale["seed_id"], anaphora["seed_id"]]
    plan_of3 = {
        fresh["seed_id"]: plan_deep,          # fresh cache -> deep
        stale["seed_id"]: plan_cheap_esc,     # stale cache -> cheap/escalate
        anaphora["seed_id"]: plan_cheap_fin,  # anaphora    -> cheap/finish
    }
    for mode in ("none", "digest", "raw"):
        rep = build_report(env, plan_of3, ids3, mode,
                           {"split": "selftest",
                            "provenance": {"note": "selftest_fabricated"}})
        tokmeta = mean_prompt_tokens(env, ids3, mode)
        print(f"           mode={mode:6s} reward@0.3="
              f"{rep['scores'][0.3]['reward']:.4f} "
              f"twin_disc={rep['twin_pair_discrimination']['twin_discrimination_rate']} "
              f"oracle_gap={rep['arm_oracle_gap_lambda0.3']['oracle_gap']:.4f} "
              f"mean_tok={tokmeta['mean_prompt_tokens']:.0f}")

    if fails == 0:
        print("\n[selftest] ALL CHECKS PASSED")
        return 0
    print(f"\n[selftest] {fails} CHECK(S) FAILED")
    return 1


# =====================================================================
# CLI / MAIN
# =====================================================================
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env-dir", type=Path,
                    help="v0.4 dataset dir (holds env_seeds_v0.4.json)")
    ap.add_argument("--split", default="test", choices=["dev", "test"])
    ap.add_argument("--memory-mode", default="digest",
                    choices=["none", "digest", "raw"],
                    help="the ARM switch: none=arm1, digest=arm2/4, raw=arm3")
    ap.add_argument("--model", default=None,
                    help="hub id or local full_model dir")
    ap.add_argument("--adapter", type=Path, default=None,
                    help="optional LoRA adapter dir")
    ap.add_argument("--loader", default="causal", choices=["causal", "auto"],
                    help="'causal' (default, Qwen path) or 'auto' (fall back to "
                         "AutoModelForImageTextToText for non-CausalLM archs)")
    ap.add_argument("--chat-template", action="store_true",
                    help="wrap the rendered prompt as a single user message via "
                         "apply_chat_template(add_generation_prompt=True)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="0 (default) = greedy/argmax; >0 samples")
    ap.add_argument("--n-samples", type=int, default=1,
                    help="1 (default) = single greedy decode")
    ap.add_argument("--dump-preds", type=Path, default=None,
                    help="model mode: write per-seed jsonl {seed_id, first, "
                         "on_fail, gate_needed, twin_id, difficulty_class, "
                         "gold_first, gold_on_fail, oracle_action, completion}")
    ap.add_argument("--out", type=Path, default=None,
                    help="write the JSON report here")
    ap.add_argument("--selftest", action="store_true",
                    help="CPU self-test on the real dataset (no model): "
                         "twin-discrimination, none-vs-digest p switch, "
                         "dynamic-cost effect. Uses --env-dir or the shipped v0.4 dir.")
    args = ap.parse_args()

    # ---- selftest: CPU, no model, no heavy imports ----
    if args.selftest:
        env_dir = args.env_dir or (
            SCRIPTS.parents[0] /
            "runs/overnight-20260629-v0.6-ai-expanded/curated/"
            "kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.4")
        raise SystemExit(_selftest(Path(env_dir)))

    if args.env_dir is None:
        ap.error("--env-dir is required (except in --selftest with the shipped dir)")

    env = EscalationEnvV04(args.env_dir)
    ids = [sid for sid, s in env.seeds.items() if s["split"] == args.split]
    if not ids:
        raise SystemExit(f"no seeds in split {args.split!r} under {args.env_dir}")

    plan_of: dict[str, tuple[str, str]] = {}
    completions: dict[str, str] = {}

    if not args.model:
        raise SystemExit("provide --model (or use --selftest for a CPU dry run)")

    # ---- model mode: heavy imports live HERE so --help/--selftest are GPU-free
    #      (structure copy-adapted from eval_escalation_policy.py; see module
    #      docstring - only the prompt renderer differs, to inject the arm memory)
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    transformers.set_seed(args.seed)
    tok = AutoTokenizer.from_pretrained(args.model)
    if args.loader == "causal":
        model = AutoModelForCausalLM.from_pretrained(
            args.model, torch_dtype=torch.bfloat16, device_map="auto")
    else:
        try:
            model = AutoModelForCausalLM.from_pretrained(
                args.model, torch_dtype=torch.bfloat16, device_map="auto")
        except (ValueError, KeyError, OSError, TypeError) as e:
            from transformers import AutoModelForImageTextToText
            print(json.dumps({"loader_fallback": "AutoModelForImageTextToText",
                              "causal_error": str(e)[:200]}))
            model = AutoModelForImageTextToText.from_pretrained(
                args.model, torch_dtype=torch.bfloat16, device_map="auto")
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(args.adapter))
    model.eval()

    def build_input(prompt_text: str):
        # default (no --chat-template) reproduces the v0.3 harness path: wrap as
        # a single user message and apply the chat template.
        msgs = [{"role": "user", "content": prompt_text}]
        text = tok.apply_chat_template(msgs, tokenize=False,
                                       add_generation_prompt=True)
        return tok(text, return_tensors="pt").to(model.device)

    sampled = args.n_samples > 1
    dump_fh = None
    if args.dump_preds:
        args.dump_preds.parent.mkdir(parents=True, exist_ok=True)
        dump_fh = args.dump_preds.open("w", encoding="utf-8")

    for sid in ids:
        seed = env.seeds[sid]
        prompt = render_prompt_v04(seed, args.memory_mode)
        enc = build_input(prompt)
        if sampled:
            with torch.no_grad():
                gen = model.generate(
                    **enc, max_new_tokens=48, do_sample=True,
                    temperature=args.temperature,
                    num_return_sequences=args.n_samples,
                    pad_token_id=tok.pad_token_id or tok.eos_token_id)
            plans = [parse_plan(tok.decode(row[enc.input_ids.shape[1]:],
                                           skip_special_tokens=True))
                     for row in gen]
            plan_of[sid] = Counter(plans).most_common(1)[0][0]
            comp = f"<{args.n_samples} samples; majority>"
        else:
            with torch.no_grad():
                gen = model.generate(**enc, max_new_tokens=48, do_sample=False,
                                     pad_token_id=tok.pad_token_id or tok.eos_token_id)
            comp = tok.decode(gen[0][enc.input_ids.shape[1]:],
                              skip_special_tokens=True)
            plan_of[sid] = parse_plan(comp)
        completions[sid] = comp
        if dump_fh is not None:
            first, on_fail = plan_of[sid]
            dump_fh.write(json.dumps({
                "seed_id": sid, "first": first, "on_fail": on_fail,
                "gate_needed": bool(seed["requires_human_gate"]),
                "twin_id": seed.get("twin_id"),
                "difficulty_class": seed.get("difficulty_class"),
                "gold_first": seed["gold_first"],
                "gold_on_fail": seed["gold_on_fail"],
                "oracle_action": env.oracle_action(sid, 0.3, args.memory_mode),
                "completion": comp}, ensure_ascii=False) + "\n")
    if dump_fh is not None:
        dump_fh.close()

    # any unparsed/absent seed -> safest legal plan (gate/finish), as v0.3 harness
    missing = [s for s in ids if s not in plan_of]
    for s in missing:
        plan_of[s] = ("gate", "finish")

    provenance = {
        "model": args.model,
        "adapter": str(args.adapter) if args.adapter else None,
        "loader": args.loader,
        "chat_template": bool(args.chat_template),
        "seed": args.seed,
        "decode": {"mode": "sampled" if sampled else "greedy",
                   "temperature": args.temperature,
                   "n_samples": args.n_samples},
        "missing_filled_as_gate": len(missing),
    }
    report = build_report(env, plan_of, ids, args.memory_mode,
                          {"split": args.split, "provenance": provenance})
    report.update(mean_prompt_tokens(env, ids, args.memory_mode, tok=tok))

    print(json.dumps(report, ensure_ascii=False, indent=1))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
