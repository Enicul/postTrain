#!/usr/bin/env python3
"""Generate oracle-labeled SFT data for the escalation env (Plan A2 input).

Each row: rendered prompt -> oracle plan JSON completion, for a chosen lambda.
Oracle labels are analytic (no model, no leakage). Train split only by
default; the frozen eval-256 is never used for SFT. Output is chat-style JSONL
ready for TRL SFTTrainer or plain HF fine-tuning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reward_escalation import EscalationReward, render_prompt


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--env-dir", type=Path, required=True)
    ap.add_argument("--lambda", dest="lam", type=float, default=0.3)
    ap.add_argument("--split", default="train", choices=["train", "dev", "test", "all"])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    r = EscalationReward(args.env_dir, lam=args.lam)
    rows = []
    for sid, seed in r.env.seeds.items():
        if args.split != "all" and seed["split"] != args.split:
            continue
        first, on_fail = r.oracle_plan(sid)
        completion = json.dumps({"first": first, "on_fail": on_fail}, ensure_ascii=False)
        rows.append({
            "seed_id": sid,
            "prompt": render_prompt(seed),
            "completion": " " + completion,
            "messages": [
                {"role": "user", "content": render_prompt(seed)},
                {"role": "assistant", "content": completion},
            ],
            "oracle_reward": round(r.plan_reward(sid, first, on_fail), 4),
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    import collections
    mix = collections.Counter((r_["completion"].strip()) for r_ in rows)
    print(json.dumps({"split": args.split, "lambda": args.lam, "rows": len(rows),
                      "label_mix": dict(mix)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
