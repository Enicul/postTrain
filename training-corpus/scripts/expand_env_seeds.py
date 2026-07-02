#!/usr/bin/env python3
"""A0: expand escalation env train seeds from the router pool with proxy p.

The frozen eval-256 keeps its ensemble-derived p (untouched). New TRAIN seeds
draw from the 9,879-row router v0.1c pool (deduped vs existing) and get a
route-mean p proxy calibrated on the 256. Proxy error (MAE vs ensemble p) is
reported so the fidelity gap is explicit. Training seeds tolerate coarse p
(GRPO explores); the eval that decides anything stays ensemble-based.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / (
    "runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1")
ENVDIR = BASE / "ladder/escalation_env_v0.1"
POOL = BASE / "repairs/router_contract_repair_v0.1c/repaired_datasets/router_classifier/train.jsonl"


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target-train", type=int, default=864, help="new train seed count to add")
    ap.add_argument("--out", type=Path, default=ENVDIR / "env_seeds_v0.2.json")
    args = ap.parse_args()

    seeds = json.loads((ENVDIR / "env_seeds_v0.1.json").read_text())
    p_tab = json.loads((ENVDIR / "outcome_table_v0.1.json").read_text())["p_cheap_success"]

    # route-mean p proxy + calibration MAE on the existing 256
    by_route_p = collections.defaultdict(list)
    for s in seeds:
        by_route_p[s["gold_route"]].append(p_tab[s["seed_id"]])
    route_mean = {r: round(sum(v) / len(v), 4) for r, v in by_route_p.items()}
    mae = sum(abs(p_tab[s["seed_id"]] - route_mean[s["gold_route"]]) for s in seeds) / len(seeds)

    existing_ids = {s["seed_id"] for s in seeds}
    pool = [r for r in load_jsonl(POOL) if r["sample_id"] not in existing_ids]
    by_route = collections.defaultdict(list)
    for r in pool:
        by_route[r["label"]["route_label"]].append(r)
    routes = sorted(route_mean)
    per = max(1, args.target_train // len(routes))

    new_seeds = []
    for route in routes:
        for r in sorted(by_route.get(route, []), key=lambda x: x["sample_id"])[:per]:
            new_seeds.append({
                "seed_id": r["sample_id"], "split": "train",
                "user_query": r["input"]["user_query"], "symbol": r["input"].get("symbol"),
                "as_of": r["input"].get("as_of"),
                "gold_route": route,
                "requires_human_gate": bool(r["label"].get("requires_human_gate")),
                "needs_realtime": bool(r["label"].get("needs_realtime_data")),
                "needs_citation": bool(r["label"].get("needs_citation")),
                "p_source": "route_mean_proxy",
            })
    for s in seeds:
        s.setdefault("p_source", "ensemble")
    combined = seeds + new_seeds

    # extend outcome table with proxy p for new seeds
    new_p = dict(p_tab)
    for s in new_seeds:
        new_p[s["seed_id"]] = route_mean[s["gold_route"]]

    args.out.write_text(json.dumps(combined, ensure_ascii=False, indent=1))
    (ENVDIR / "outcome_table_v0.2.json").write_text(json.dumps({
        "provenance": "eval/original-256 = ensemble p (v0.1); new train seeds = route_mean_proxy",
        "route_mean_proxy": route_mean,
        "proxy_mae_vs_ensemble_on_256": round(mae, 4),
        "p_cheap_success": new_p,
    }, ensure_ascii=False, indent=1))
    print(json.dumps({
        "existing": len(seeds), "added_train": len(new_seeds), "total": len(combined),
        "route_mean_proxy": route_mean, "proxy_mae_vs_ensemble_on_256": round(mae, 4),
        "split_mix": dict(collections.Counter(s["split"] for s in combined)),
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
