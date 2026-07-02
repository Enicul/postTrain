#!/usr/bin/env python3
"""Build risk_contract_repair_v0.1b and the audited frozen risk_real_eval_v1.

Block A2 of the three-task ladder. Three real risk families are normalized
into the v0.1-compatible flat input schema (fixing the featurization gap that
left long-research memo rows nearly featureless), the 90 eval rows carry a
blind double-annotation audit trail, and the adjudicated conventions R1-R5
are applied both to eval (via audit) and to train (via provenance-mechanical
sync rules, R5) so the contract stays coherent across splits.

Outputs under repairs/risk_contract_repair_v0.1b/:
  risk_real_eval_v1/rows/{dev,test,all}.jsonl   - frozen audited ruler
  risk_real_eval_v1/audit/*                      - votes + adjudications
  repaired_datasets/risk_reviewer/{train,dev,test}.jsonl
      train = v0.1 synthetic train + 166 normalized real rows (rule-synced)
      dev/test = the audited real eval rows
  manifest.json, REPORT stub printed to stdout
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLD = REPO_ROOT / "training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1"
V01 = (
    REPO_ROOT
    / "training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1"
    / "repairs/risk_contract_repair_v0.1"
)
OUT = (
    REPO_ROOT
    / "training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1"
    / "repairs/risk_contract_repair_v0.1b"
)
EVAL_ID = "risk_real_eval_v1"
AUDIT_DATE = "2026-07-02"


def load_jsonl(p: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def write_jsonl(p: Path, rows: list[dict[str, Any]]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as h:
        for r in rows:
            h.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def git_value(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def clip(x: Any, n: int = 260) -> str:
    s = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)
    return s[:n]


# ---------------- family normalizers (fixes F: memo rows featurized empty) ----


def norm_golden(row: dict[str, Any]) -> dict[str, Any]:
    inp = row["input"]
    if inp.get("claim") is not None:
        return {
            "family": "evidence_review",
            "claim": inp.get("claim"),
            "evidence_summary": inp.get("evidence_summary"),
            "verdict": inp.get("verdict"),
            "user_query": None,
            "symbol": None,
            "draft_memo": None,
            "task_family": "golden_bookmark_evidence_review",
        }
    return {
        "family": "query_review",
        "user_query": inp.get("user_query"),
        "symbol": inp.get("symbol"),
        "draft_memo": inp.get("draft_memo"),
        "claim": None,
        "evidence_summary": inp.get("evidence_summary") or None,
        "verdict": None,
        "task_family": "golden_synthetic_risk_bootstrap",
    }


def norm_lr(row: dict[str, Any]) -> dict[str, Any]:
    inp = row["input"]
    memo = inp.get("memo", {})
    parts = [f"thesis: {clip(memo.get('thesis'), 400)}", f"confidence: {memo.get('confidence')}"]
    for key, cap in [("risks", 3), ("invalidation_conditions", 3), ("next_watch_triggers", 2)]:
        vals = memo.get(key) or []
        if vals:
            parts.append(f"{key}: " + " | ".join(clip(v, 160) for v in vals[:cap]))
    svr = memo.get("support_vs_risk_comparison")
    if svr:
        parts.append(f"support_vs_risk: {clip(svr, 240)}")
    ch = memo.get("contradiction_handling") or {}
    if ch:
        parts.append(
            f"contradiction_handling: required={ch.get('required')} handled={ch.get('handled')} "
            f"unresolved={','.join(ch.get('unresolved_tensions') or [])}"
        )
    parts.append(f"direct_trade_instruction: {memo.get('direct_trade_instruction')}")
    warns = inp.get("source_warnings") or []
    if warns:
        parts.append("source_warnings: " + " | ".join(clip(w, 160) for w in warns[:3]))
    blockers = inp.get("blockers") or []
    if blockers:
        parts.append("blockers: " + " | ".join(clip(b, 120) for b in blockers[:3]))
    return {
        "family": "memo_review",
        "user_query": None,
        "symbol": memo.get("symbol"),
        "draft_memo": "\n".join(parts),
        "claim": None,
        "evidence_summary": None,
        "verdict": None,
        "task_family": "long_research_memo_review",
    }


def norm_us(row: dict[str, Any]) -> dict[str, Any]:
    inp = row["input"]
    stub = inp.get("final_stub") or {}
    parts = [
        f"route: {inp.get('route')}",
        f"final_stub_mode: {stub.get('mode')}",
        f"final_stub_memo: {clip(stub.get('memo'), 300)}",
    ]
    blockers = inp.get("blockers") or []
    if blockers:
        parts.append("blockers: " + " | ".join(clip(b, 120) for b in blockers[:4]))
    return {
        "family": "interaction_review",
        "user_query": inp.get("user_query"),
        "symbol": None,
        "draft_memo": "\n".join(parts),
        "claim": None,
        "evidence_summary": None,
        "verdict": None,
        "task_family": "user_simulation_interaction_review",
    }


# ---------------- R5 mechanical sync rules ------------------------------------


def apply_rules(row: dict[str, Any], family: str) -> tuple[dict[str, Any], str | None]:
    """Return (label_overrides, rule_id) under conventions R1-R5."""
    lab = row["label"]
    if family == "golden_v0.1_risk" and row["sample_id"].startswith("risk_syn_"):
        scenario = (row.get("provenance") or {}).get("scenario_id")
        if scenario == "missing_bear_case":
            return {"risk_level": "high", "requires_human_gate": True}, "rule_missing_bear_case_high"
        if scenario == "normal_research":
            return {"risk_level": "medium"}, "rule_normal_research_medium"
    if family == "user_simulation_trace_pilot_50" and lab.get("risk_level") == "medium":
        route = row["input"].get("route")
        if route in ("fast_answer", "news_retrieval"):
            return {"risk_level": "low"}, f"rule_us_{route}_low"
    return {}, None


BESPOKE = {
    "risk_strict_risk_strict_trace_002_european_photonics_basket": (
        {"risk_level": "medium"},
        "adjudication: basket overreach without any R1 red line is medium (see audit/risk_adjudications.json)",
    ),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit-dir", type=Path, required=True,
                    help="dir with rb*_[AB].jsonl, rsyn_[AB].jsonl, risk_adjudications.json")
    args = ap.parse_args()

    votes: dict[str, dict[str, dict[str, Any]]] = {}

    def load_votes(fname: str, passname: str, only_syn: bool | None) -> None:
        p = args.audit_dir / fname
        if not p.exists():
            return
        for r in load_jsonl(p):
            sid = r["sample_id"]
            is_syn = sid.startswith("risk_syn_")
            if only_syn is True and not is_syn:
                continue
            if only_syn is False and is_syn:
                continue
            votes.setdefault(sid, {})[passname] = r

    for f in ["rb1_A.jsonl", "rb2_A.jsonl", "rb3_A.jsonl"]:
        load_votes(f, "A", only_syn=False)
    for f in ["rb1_B.jsonl", "rb2_B.jsonl", "rb3_B.jsonl"]:
        load_votes(f, "B", only_syn=False)
    load_votes("rsyn_A.jsonl", "A", only_syn=True)
    load_votes("rsyn_B.jsonl", "B", only_syn=True)
    adjudications = json.loads((args.audit_dir / "risk_adjudications.json").read_text())

    # -------- collect + normalize the three real families ----------
    records: list[dict[str, Any]] = []

    for split_name in ["train", "dev", "test"]:
        for row in load_jsonl(GOLD / f"datasets/risk_reviewer/{split_name}.jsonl"):
            records.append(("golden_v0.1_risk", split_name, norm_golden(row), row))

    lr = sorted(
        load_jsonl(GOLD / "long_research_trace_source_quality_repair_25/datasets/risk_reviewer/all.jsonl"),
        key=lambda r: r["sample_id"],
    )
    for i, row in enumerate(lr):
        split = "train" if i < 13 else ("dev" if i < 19 else "test")
        records.append(("long_research_repair_25", split, norm_lr(row), row))

    us = sorted(
        load_jsonl(GOLD / "user_simulation_trace_pilot_50/datasets/risk_reviewer/all.jsonl"),
        key=lambda r: r["sample_id"],
    )
    strata: dict[Any, list[dict[str, Any]]] = {}
    for row in us:
        strata.setdefault((row["label"]["risk_level"], bool(row["label"].get("requires_human_gate"))), []).append(row)
    for key, rows in sorted(strata.items()):
        n = len(rows)
        n_dev = max(1, round(n * 0.2)) if n >= 3 else (1 if n == 2 else 0)
        n_test = max(1, round(n * 0.2)) if n >= 3 else (1 if n >= 1 else 0)
        for i, row in enumerate(rows):
            split = "test" if i < n_test else ("dev" if i < n_test + n_dev else "train")
            records.append(("user_simulation_trace_pilot_50", split, norm_us(row), row))

    # -------- build final rows ----------
    real_rows: list[dict[str, Any]] = []
    rule_counts: dict[str, int] = {}
    eval_corrections: list[dict[str, Any]] = []
    for family, split, ninp, row in records:
        sid = row["sample_id"]
        lab = dict(row["label"])
        original = {"risk_level": lab.get("risk_level"), "requires_human_gate": bool(lab.get("requires_human_gate"))}
        overrides, rule_id = apply_rules(row, family)
        note = None
        if sid in BESPOKE:
            overrides, note = BESPOKE[sid]
            rule_id = "bespoke_adjudication"
        for k, v in overrides.items():
            lab[k] = v
        changed = (
            lab.get("risk_level") != original["risk_level"]
            or bool(lab.get("requires_human_gate")) != original["requires_human_gate"]
        )
        if changed:
            lab["original_risk_level"] = original["risk_level"]
            lab["original_requires_human_gate"] = original["requires_human_gate"]
            rule_counts[rule_id or "?"] = rule_counts.get(rule_id or "?", 0) + 1
            if split in ("dev", "test"):
                eval_corrections.append({"sample_id": sid, "rule": rule_id, "from": original,
                                         "to": {"risk_level": lab["risk_level"],
                                                "requires_human_gate": bool(lab.get("requires_human_gate"))}})

        out = {
            "sample_id": sid,
            "source": "risk_real_v1",
            "split": split,
            "input": ninp,
            "label": lab,
            "provenance": {
                **(row.get("provenance") or {}),
                "source_family": family,
                "normalized_by": "build_risk_contract_repair_v01b",
                "original_input_schema": sorted(row["input"].keys()),
            },
            "repair": {
                "contract_id": "risk_contract_repair_v0.1b",
                "origin": "real_trace_normalized",
                "conventions": "R1-R5, see risk_real_eval_v1/audit/risk_adjudications.json",
            },
        }
        if split in ("dev", "test"):
            v = votes.get(sid, {})
            status = "corrected" if changed else "confirmed"
            out["audit"] = {
                "audit_id": EVAL_ID,
                "audit_date": AUDIT_DATE,
                "protocol": "blind_double_annotation_plus_adjudication",
                "audited_by": "claude (two independent blind auditor agents + main-session adjudicator); no human pass",
                "vote_pass_a": {k: v.get("A", {}).get(k) for k in ("risk_level", "requires_human_gate")},
                "vote_pass_b": {k: v.get("B", {}).get(k) for k in ("risk_level", "requires_human_gate")},
                "status": status,
                "note": note,
            }
        real_rows.append(out)

    eval_rows = [r for r in real_rows if r["split"] in ("dev", "test")]
    train_real = [r for r in real_rows if r["split"] == "train"]

    # -------- assemble output dirs ----------
    write_jsonl(OUT / EVAL_ID / "rows" / "all.jsonl", eval_rows)
    write_jsonl(OUT / EVAL_ID / "rows" / "dev.jsonl", [r for r in eval_rows if r["split"] == "dev"])
    write_jsonl(OUT / EVAL_ID / "rows" / "test.jsonl", [r for r in eval_rows if r["split"] == "test"])
    (OUT / EVAL_ID / "audit").mkdir(parents=True, exist_ok=True)
    for name in ["rb1_A.jsonl", "rb1_B.jsonl", "rb2_A.jsonl", "rb2_B.jsonl", "rb3_A.jsonl", "rb3_B.jsonl",
                 "rsyn_A.jsonl", "rsyn_B.jsonl", "risk_adjudications.json"]:
        src = args.audit_dir / name
        if src.exists():
            (OUT / EVAL_ID / "audit" / name).write_bytes(src.read_bytes())

    v01_train = load_jsonl(V01 / "repaired_datasets/risk_reviewer/train.jsonl")
    write_jsonl(OUT / "repaired_datasets/risk_reviewer/train.jsonl", v01_train + train_real)
    write_jsonl(OUT / "repaired_datasets/risk_reviewer/dev.jsonl", [r for r in eval_rows if r["split"] == "dev"])
    write_jsonl(OUT / "repaired_datasets/risk_reviewer/test.jsonl", [r for r in eval_rows if r["split"] == "test"])
    write_jsonl(OUT / "repaired_datasets/risk_reviewer/all.jsonl", v01_train + real_rows)

    def dist(rows: list[dict[str, Any]]) -> dict[str, int]:
        d: dict[str, int] = {}
        for r in rows:
            d[r["label"]["risk_level"]] = d.get(r["label"]["risk_level"], 0) + 1
        return d

    audit_summary = {
        "eval_rows": len(eval_rows),
        "eval_confirmed": sum(1 for r in eval_rows if r["audit"]["status"] == "confirmed"),
        "eval_corrected": len(eval_corrections),
        "correction_rate": round(len(eval_corrections) / len(eval_rows), 4),
        "gold_kept_against_auditors": [d["sample_id"] for d in adjudications["bespoke_decisions"]
                                       if d["original"] == d["audited"]],
        "rule_counts_all_splits": rule_counts,
    }
    manifest = {
        "repair_id": "risk_contract_repair_v0.1b",
        "eval_id": EVAL_ID,
        "created_at": now_utc(),
        "audit_date": AUDIT_DATE,
        "real_rows": len(real_rows),
        "train_rows_total": len(v01_train) + len(train_real),
        "train_rows_real_added": len(train_real),
        "eval_label_dist": dist(eval_rows),
        "eval_gate_true": sum(1 for r in eval_rows if r["label"].get("requires_human_gate")),
        "train_real_label_dist": dist(train_real),
        "audit": audit_summary,
        "eval_corrections": eval_corrections,
        "frozen": {
            "eval_splits": ["dev", "test"],
            "rule": "test untouchable; prompts/experience libraries iterate on train/dev only; changes require a new eval id",
        },
        "conventions": "R1-R5 pinned in risk_real_eval_v1/audit/risk_adjudications.json",
        "git": {"branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]), "commit": git_value(["rev-parse", "HEAD"])},
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
