#!/usr/bin/env python3
"""Aggregate multi-seed escalation eval jsons into mean/std error bars (Plan, batch 4).

All portfolio numbers so far are SINGLE-SEED (seed 0); this is the top
credibility gap. Given N eval-json paths for the SAME config at DIFFERENT seeds
(each the output of eval_escalation_policy.py, i.e. `scores[<lambda>]` with
reward/cost/success/gate_recall), emit mean/std/min/max for reward@each-lambda
and gate_recall, plus n_seeds and the per-seed values, to --out json, and print
a compact markdown table.

Stdlib only, no GPU, no torch: safe to run on the CPU box or in CI.

Population std (ddof=0) is used so a single-seed input yields std 0.0 rather
than a divide-by-zero; with n_seeds >= 2 that is the exact spread of the sample.

Usage:
  python aggregate_seeds.py --config sft_qwen15 --out runs/agg/sft_qwen15.json \
      runs/sft_qwen15/<S0>/sft_test_eval.json \
      runs/sft_qwen15_seed1/<S1>/sft_test_eval.json \
      runs/sft_qwen15_seed2/<S2>/sft_test_eval.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def mean_std_min_max(xs: list[float]) -> dict:
    """mean / population-std (ddof=0) / min / max over a non-empty list."""
    n = len(xs)
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / n  # population variance, n>=1 safe
    return {"mean": round(mean, 4), "std": round(math.sqrt(var), 4),
            "min": round(min(xs), 4), "max": round(max(xs), 4)}


def load_eval(path: Path) -> dict:
    """Load one eval json; return {lambda(str): {reward, gate_recall, ...}}."""
    d = json.loads(Path(path).read_text())
    if "scores" not in d:
        raise SystemExit(f"{path}: not an eval json (no 'scores' key)")
    return d


def aggregate(paths: list[Path], config: str) -> dict:
    evals = [load_eval(p) for p in paths]
    # lambdas present in every seed's json (sorted numerically for stable output)
    lam_sets = [set(e["scores"].keys()) for e in evals]
    lambdas = sorted(set.intersection(*lam_sets), key=float) if lam_sets else []

    per_lambda = {}
    for lam in lambdas:
        rewards = [e["scores"][lam]["reward"] for e in evals]
        gate = [e["scores"][lam]["gate_recall"] for e in evals]
        per_lambda[lam] = {
            "reward": mean_std_min_max(rewards),
            "gate_recall": mean_std_min_max(gate),
            "per_seed_reward": [round(r, 4) for r in rewards],
            "per_seed_gate_recall": [round(g, 4) for g in gate],
        }
    return {
        "config": config,
        "n_seeds": len(evals),
        "lambdas": lambdas,
        "eval_paths": [str(p) for p in paths],
        "per_lambda": per_lambda,
    }


def markdown_table(agg: dict) -> str:
    """Compact md: one row per lambda, reward mean±std [min,max] and gate_recall."""
    lines = [f"### {agg['config']}  (n_seeds={agg['n_seeds']})",
             "",
             "| lambda | reward mean±std | reward [min,max] | gate_recall mean±std |",
             "|---|---|---|---|"]
    for lam in agg["lambdas"]:
        r = agg["per_lambda"][lam]["reward"]
        g = agg["per_lambda"][lam]["gate_recall"]
        lines.append(
            f"| {lam} | {r['mean']:.4f}±{r['std']:.4f} | "
            f"[{r['min']:.4f}, {r['max']:.4f}] | "
            f"{g['mean']:.4f}±{g['std']:.4f} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("evals", nargs="+", type=Path,
                    help="eval-json paths, same config, different seeds")
    ap.add_argument("--config", default="config",
                    help="label for the aggregated config (table heading)")
    ap.add_argument("--out", type=Path, default=None, help="write aggregate json here")
    args = ap.parse_args()

    agg = aggregate(args.evals, args.config)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(agg, ensure_ascii=False, indent=1))
    print(markdown_table(agg))


if __name__ == "__main__":
    main()
