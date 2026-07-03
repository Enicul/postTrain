#!/usr/bin/env python3
"""Analyze a GRPO run for policy-collapse signatures (gate extinction / deep collapse).

Stdlib + json only. Computes, per run directory:
  - per-50-step action-share curves (cheap / deep / gate / parse_fallback)
  - gate-action share over time (per batch, smoothed into windows)
  - per-window share of gate-REQUIRED-seed K-groups whose *entire* K-group violated
    (the zero-within-group-advantage condition that kills the GRPO gradient)
  - KL curve (from trainer_log.jsonl)
  - reward curve (from reward_trace.jsonl mean_reward + trainer_log reward)

A gate-required seed is identified empirically: it is a seed for which any
non-gate first action incurs the safety penalty (reward < -1.0), while a gate
first action is rewarded (reward >= 0). This recovers the 24/160 gate seeds
without needing the env source.

Writes collapse_analysis.json into each run dir and prints a compact summary.

Usage:
  python3 analyze_grpo_collapse.py RUN_DIR [RUN_DIR ...]
  python3 analyze_grpo_collapse.py          # defaults to the two known runs
"""
import json
import os
import sys
from collections import defaultdict

# K completions per (seed, step) group in this GRPO config.
K = 8
# Safety penalty applied to un-gated gate-required seeds is -2.0; use -1.0 as a
# robust classification threshold (all real violations land < -1.18 in practice).
PENALTY_THRESHOLD = -1.0
WINDOW = 50  # steps per aggregation window

DEFAULT_RUNS = [
    "training-corpus/scripts/rl/runs/grpo_qwen05/20260703T1507Z-e571324",
    "training-corpus/scripts/rl/runs/grpo_qwen15/20260703T1520Z-e571324",
]


def _read_jsonl(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def first_action(rec):
    plan = rec.get("parsed_plan") or []
    if not plan:
        return "parse_fallback"
    return plan[0]


def classify_gate_seeds(gens):
    """Return set of gate-required seed_ids: a non-gate first action triggers the
    safety penalty (reward < PENALTY_THRESHOLD)."""
    by_seed = defaultdict(list)
    for r in gens:
        by_seed[r["seed_id"]].append((first_action(r), r["reward"]))
    gate_seeds = set()
    for seed, rows in by_seed.items():
        if any(rew < PENALTY_THRESHOLD for act, rew in rows if act != "gate"):
            gate_seeds.add(seed)
    return gate_seeds


def analyze_run(run_dir):
    gens = _read_jsonl(os.path.join(run_dir, "generations.jsonl"))
    trace = _read_jsonl(os.path.join(run_dir, "reward_trace.jsonl"))
    tlog = _read_jsonl(os.path.join(run_dir, "trainer_log.jsonl"))
    try:
        eval_json = json.load(open(os.path.join(run_dir, "grpo_test_eval.json")))
    except FileNotFoundError:
        eval_json = {}

    gate_seeds = classify_gate_seeds(gens)

    # Group generations by (step_counter, seed_id) -> the K-group.
    groups = defaultdict(list)  # (step, seed) -> list of (first_action, reward)
    for r in gens:
        groups[(r["step_counter"], r["seed_id"])].append(
            (first_action(r), r["reward"])
        )

    max_step = max(r["step_counter"] for r in gens)

    # ---- Per-window aggregates ----
    windows = []
    for lo in range(0, max_step, WINDOW):
        hi = lo + WINDOW  # steps (lo, hi] in 1-indexed => step in (lo, hi]
        w_lo, w_hi = lo + 1, hi

        # action shares from raw generations in this window
        counts = {"cheap": 0, "deep": 0, "gate": 0, "parse_fallback": 0, "other": 0}
        n_roll = 0
        for r in gens:
            if w_lo <= r["step_counter"] <= w_hi:
                a = first_action(r)
                counts[a if a in counts else "other"] += 1
                n_roll += 1

        # gate-required K-groups: how many were ALL-violate (zero within-group advantage)
        gr_groups = 0
        gr_allviolate = 0
        for (step, seed), rows in groups.items():
            if seed not in gate_seeds:
                continue
            if not (w_lo <= step <= w_hi):
                continue
            gr_groups += 1
            # violation = first action != gate (i.e. safety penalty on a gate seed)
            all_violate = all(act != "gate" for act, rew in rows)
            if all_violate:
                gr_allviolate += 1

        share = lambda k: (counts[k] / n_roll) if n_roll else 0.0
        windows.append({
            "window": f"{w_lo}-{w_hi}",
            "step_lo": w_lo,
            "step_hi": w_hi,
            "n_rollouts": n_roll,
            "action_share": {
                "cheap": round(share("cheap"), 4),
                "deep": round(share("deep"), 4),
                "gate": round(share("gate"), 4),
                "parse_fallback": round(share("parse_fallback"), 4),
            },
            "gate_required_groups": gr_groups,
            "gate_required_all_violate_groups": gr_allviolate,
            "gate_required_all_violate_rate": round(gr_allviolate / gr_groups, 4)
            if gr_groups else None,
        })

    # ---- KL curve from trainer_log ----
    kl_curve = [
        {"step": r["step"], "kl": round(r["kl"], 4)}
        for r in tlog if "kl" in r and r.get("kl") is not None
    ]
    kl_vals = [p["kl"] for p in kl_curve]
    kl_max = max(kl_vals) if kl_vals else None
    kl_max_step = kl_curve[kl_vals.index(kl_max)]["step"] if kl_vals else None
    # settled KL = mean over last quarter of logged steps
    tail = kl_vals[len(kl_vals) * 3 // 4:] if kl_vals else []
    kl_settled = round(sum(tail) / len(tail), 4) if tail else None

    # ---- reward curve from reward_trace (per batch) ----
    reward_curve = [
        {"batch": r["batch_idx"], "mean_reward": r["mean_reward"],
         "gate_violation_rate": r.get("gate_violation_rate")}
        for r in trace
    ]

    # ---- gate-share per batch (for extinction timing) ----
    gate_share_batch = []
    for r in trace:
        mix = r["action_mix"]
        tot = sum(mix.values())
        gate_share_batch.append({
            "batch": r["batch_idx"],
            "gate_share": round(mix.get("gate", 0) / tot, 4) if tot else 0.0,
        })
    # first batch where gate share drops below 5% and stays effectively dead
    gate_death_batch = None
    for i, p in enumerate(gate_share_batch):
        rest = gate_share_batch[i:]
        if p["gate_share"] < 0.05 and all(q["gate_share"] < 0.10 for q in rest):
            gate_death_batch = p["batch"]
            break
    last_gate_batch = None
    gate_batches = [r["batch_idx"] for r in trace if r["action_mix"].get("gate", 0) > 0]
    if gate_batches:
        last_gate_batch = max(gate_batches)

    # ---- whole-run aggregate all-violate rate over gate-required groups ----
    total_gr = sum(w["gate_required_groups"] for w in windows)
    total_gr_av = sum(w["gate_required_all_violate_groups"] for w in windows)
    overall_all_violate = round(total_gr_av / total_gr, 4) if total_gr else None

    # ---- negative-reward batch spikes (early-warning) ----
    neg_batches = [
        {"batch": r["batch_idx"], "mean_reward": r["mean_reward"],
         "gate_violation_rate": r.get("gate_violation_rate")}
        for r in trace if r["mean_reward"] < -1.0
    ]

    summary = {
        "run_dir": run_dir,
        "config": {"K": K, "penalty_threshold": PENALTY_THRESHOLD,
                   "window_steps": WINDOW},
        "n_rollouts": len(gens),
        "n_seeds": len(set(r["seed_id"] for r in gens)),
        "n_gate_required_seeds": len(gate_seeds),
        "max_step": max_step,
        "action_share_windows": windows,
        "gate_share_by_batch_summary": {
            "first_batch": gate_share_batch[0]["gate_share"] if gate_share_batch else None,
            "gate_extinction_batch": gate_death_batch,
            "last_batch_with_gate": last_gate_batch,
        },
        "kl": {
            "curve": kl_curve,
            "first": kl_vals[0] if kl_vals else None,
            "max": kl_max,
            "max_step": kl_max_step,
            "settled_last_quarter": kl_settled,
        },
        "gate_required_all_violate": {
            "overall_rate": overall_all_violate,
            "total_groups": total_gr,
            "total_all_violate_groups": total_gr_av,
        },
        "negative_reward_batches": neg_batches,
        "reward_curve": reward_curve,
        "eval": eval_json.get("kill_check_lambda0.3", eval_json),
    }
    return summary


def print_summary(s):
    print(f"\n=== {s['run_dir']} ===")
    print(f"  rollouts={s['n_rollouts']} seeds={s['n_seeds']} "
          f"gate-required-seeds={s['n_gate_required_seeds']}")
    gs = s["gate_share_by_batch_summary"]
    print(f"  gate share batch1={gs['first_batch']} "
          f"extinction@batch={gs['gate_extinction_batch']} "
          f"last-gate-batch={gs['last_batch_with_gate']}")
    print("  action-share windows (gate | deep | cheap) + gate-req all-violate rate:")
    for w in s["action_share_windows"]:
        a = w["action_share"]
        print(f"    {w['window']:>9}: gate={a['gate']:.3f} deep={a['deep']:.3f} "
              f"cheap={a['cheap']:.3f}  allviol={w['gate_required_all_violate_rate']} "
              f"({w['gate_required_all_violate_groups']}/{w['gate_required_groups']})")
    k = s["kl"]
    print(f"  KL first={k['first']} max={k['max']}@{k['max_step']} "
          f"settled={k['settled_last_quarter']}")
    gv = s["gate_required_all_violate"]
    print(f"  overall gate-req all-violate rate={gv['overall_rate']} "
          f"({gv['total_all_violate_groups']}/{gv['total_groups']})")
    print(f"  negative-reward batches (<-1.0): "
          f"{[(b['batch'], round(b['mean_reward'],3)) for b in s['negative_reward_batches']]}")
    ev = s.get("eval") or {}
    if isinstance(ev, dict):
        print(f"  eval: policy={ev.get('policy_reward')} "
              f"baseline={ev.get('baseline_reward')} gate_recall={ev.get('gate_recall')}")


def main(argv):
    runs = argv[1:] if len(argv) > 1 else DEFAULT_RUNS
    for run_dir in runs:
        s = analyze_run(run_dir)
        out = os.path.join(run_dir, "collapse_analysis.json")
        with open(out, "w") as f:
            json.dump(s, f, indent=2)
        print_summary(s)
        print(f"  -> wrote {out}")


if __name__ == "__main__":
    main(sys.argv)
