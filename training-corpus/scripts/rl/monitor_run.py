#!/usr/bin/env python3
"""Zero-dependency watchdog for an escalation training run.

Run in a second terminal on the GPU box, pointed at a run dir:

    python monitor_run.py runs/grpo_qwen05b/20260703T0412Z-1111bfc

Every 60s it prints a one-line status checking:
  (a) trainer_log.jsonl mtime heartbeat  - warn if stale > 10 min
  (b) last loss / reward                  - LOUD exit(2) on NaN or inf
  (c) gate_violation_rate trend           - warn if > 0.05 and rising
  (d) disk free                           - warn if low

Exits nonzero with a loud message on NaN/inf or a dead heartbeat (>10 min),
so it doubles as a kill signal you can watch. Pure stdlib.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import time
from pathlib import Path

HEARTBEAT_STALE_S = 10 * 60
GATE_VIOL_WARN = 0.05
DISK_WARN_GB = 5.0
POLL_S = 60


def _tail_json(path: Path, n: int = 1) -> list[dict]:
    """Return the last n parseable JSON objects from a jsonl file."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-n:]


def _is_bad(x) -> bool:
    try:
        return math.isnan(float(x)) or math.isinf(float(x))
    except (TypeError, ValueError):
        return False


def check(run_dir: Path) -> tuple[str, bool]:
    """Return (status_line, fatal). fatal -> caller should exit nonzero loudly."""
    log = run_dir / "trainer_log.jsonl"
    trace = run_dir / "reward_trace.jsonl"
    now = time.time()
    parts, warns, fatal = [], [], False

    # (a) heartbeat
    if log.exists():
        age = now - log.stat().st_mtime
        parts.append(f"heartbeat={int(age)}s")
        if age > HEARTBEAT_STALE_S:
            warns.append(f"DEAD heartbeat ({int(age)}s > {HEARTBEAT_STALE_S}s)")
            fatal = True
    else:
        parts.append("heartbeat=NONE")

    # (b) last loss / reward NaN/inf
    last = _tail_json(log, 1)
    if last:
        rec = last[0]
        for k in ("loss", "reward", "reward_mean", "train_loss"):
            if k in rec:
                parts.append(f"{k}={rec[k]}")
                if _is_bad(rec[k]):
                    warns.append(f"{k} is NaN/inf ({rec[k]})")
                    fatal = True

    # (c) gate_violation_rate trend
    tr = _tail_json(trace, 5)
    if tr:
        last_gv = tr[-1].get("gate_violation_rate")
        parts.append(f"gate_viol={last_gv}")
        if last_gv is not None and _is_bad(tr[-1].get("mean_reward")):
            warns.append("mean_reward NaN/inf")
            fatal = True
        if last_gv is not None and last_gv > GATE_VIOL_WARN and len(tr) >= 2:
            first_gv = tr[0].get("gate_violation_rate")
            if first_gv is not None and last_gv > first_gv:
                warns.append(f"gate_violation_rate rising ({first_gv}->{last_gv})")

    # (d) disk free
    try:
        free_gb = shutil.disk_usage(run_dir).free / 1e9
        parts.append(f"disk_free={free_gb:.1f}GB")
        if free_gb < DISK_WARN_GB:
            warns.append(f"low disk ({free_gb:.1f}GB)")
    except OSError:
        pass

    status = " ".join(parts)
    if warns:
        status += "  WARN: " + "; ".join(warns)
    return status, fatal


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir", type=Path, help="run dir (out-dir/<run_id>/)")
    ap.add_argument("--interval", type=int, default=POLL_S)
    ap.add_argument("--once", action="store_true", help="check once and exit")
    args = ap.parse_args()

    if not args.run_dir.exists():
        print(f"[monitor] run dir not found: {args.run_dir}", file=sys.stderr)
        sys.exit(3)

    while True:
        ts = time.strftime("%H:%M:%S")
        status, fatal = check(args.run_dir)
        print(f"[monitor {ts}] {status}", flush=True)
        if fatal:
            print("\n*** MONITOR FATAL: NaN/inf or dead heartbeat - "
                  "STOP AND INSPECT THE RUN. Do NOT delete the dir; it is "
                  "interview evidence. ***", file=sys.stderr, flush=True)
            sys.exit(2)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
