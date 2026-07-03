#!/usr/bin/env python3
"""Run provenance, never-overwrite run dirs, and training-log persistence.

Shared by sft_escalation.py and grpo_escalation.py. Pure-stdlib except for the
TrainerCallback base class, which is imported lazily so `--help` and CPU smoke
of the trainers keep working without the GPU stack installed.

Two jobs:
  * new_run_dir / write_manifest  - R1/R4 provenance: every run lands in
    out_dir/<run_id>/ (UTC timestamp + short git sha), refuses to clobber a
    non-empty dir, and drops a run_manifest.json capturing config, seeds, git
    sha, pip freeze, and the --parent-run linkage for error-correction chains.
  * JsonlLogCallback              - R2/R4 log persistence: appends every
    on_log dict (plus a timestamp) to <run_dir>/trainer_log.jsonl so no metric
    is lost to stdout.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def git_sha(short: bool = True) -> str:
    """Short git sha of HEAD, or 'nogit' outside a repo."""
    try:
        args = ["git", "rev-parse", "--short" if short else "HEAD", "HEAD"]
        if not short:
            args = ["git", "rev-parse", "HEAD"]
        return subprocess.check_output(args, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "nogit"


def utc_stamp() -> str:
    """Compact UTC stamp, e.g. 20260703T0412Z."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")


def make_run_id() -> str:
    """run_id = UTC timestamp + short git sha, e.g. 20260703T0412Z-1111bfc."""
    return f"{utc_stamp()}-{git_sha(short=True)}"


def pip_freeze() -> list[str]:
    """`pip freeze` output as a list of lines; empty list if unavailable."""
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"],
                                      stderr=subprocess.DEVNULL).decode()
        return [l for l in out.splitlines() if l.strip()]
    except Exception:
        return []


def new_run_dir(out_dir: Path) -> tuple[Path, str]:
    """Create and return (out_dir/<run_id>/, run_id). Never overwrite.

    Refuses (SystemExit) if the target dir already exists and is non-empty, so
    a failed run's evidence can never be clobbered by a re-run (R3).
    """
    run_id = make_run_id()
    run_dir = Path(out_dir) / run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty run dir: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir, run_id


def write_manifest(run_dir: Path, run_id: str, *, seed: int, argv: list[str],
                   config: dict, env_seeds_version: str | None, base_model: str,
                   parent_run_id: str | None) -> Path:
    """Write run_manifest.json capturing full provenance for the run."""
    manifest = {
        "run_id": run_id,
        "git_sha": git_sha(short=False),
        "seed": seed,
        "argv": argv,
        "config": config,
        "env_seeds_version": env_seeds_version,
        "base_model": base_model,
        "parent_run_id": parent_run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pip_freeze": pip_freeze(),
    }
    path = Path(run_dir) / "run_manifest.json"
    # default=str so non-serializable config values (paths, enums) never crash
    path.write_text(json.dumps(manifest, indent=1, default=str))
    return path


def make_log_callback(run_dir: Path):
    """Return a TrainerCallback that persists every on_log dict to jsonl.

    Imported lazily (transformers) so the trainers' --help works GPU-free.
    """
    from transformers import TrainerCallback

    class JsonlLogCallback(TrainerCallback):
        """Append each on_log dict + wall-clock timestamp to trainer_log.jsonl."""

        def __init__(self, run_dir: Path):
            self.path = Path(run_dir) / "trainer_log.jsonl"
            self._fh = open(self.path, "a", buffering=1)  # line-buffered

        def on_log(self, args, state, control, logs=None, **kwargs):
            rec = {"ts": time.time(), "step": getattr(state, "global_step", None),
                   **(logs or {})}
            self._fh.write(json.dumps(rec) + "\n")
            self._fh.flush()

        def on_train_end(self, args, state, control, **kwargs):
            try:
                self._fh.close()
            except Exception:
                pass

    return JsonlLogCallback(run_dir)
