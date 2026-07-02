#!/usr/bin/env python3
"""Assemble the audited, frozen citation_real_eval_v1 pack.

Inputs: the two as-collected span packs (untouched, kept as historical
evidence) plus the blind-audit artifacts (two independent vote files and the
adjudication record). Output: 131 rows with an `audit` block per row and
adjudicated labels applied. dev+test are the frozen evaluation split for the
three-task ladder; prompts and experience libraries may iterate on train/dev
but never on test.

Audit protocol (2026-07-02): every row was independently relabeled by two
blind auditors (labels hidden) against the five-way contract; rows where any
auditor disagreed with the stored label were adjudicated. Conventions pinned
by the audit (C1 contradiction precedence, C2 period binding, C3 materially
weakens) are recorded in audit/adjudications.json.
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
BASE_REPAIR_DIR = (
    REPO_ROOT
    / "training-corpus"
    / "runs"
    / "overnight-20260629-v0.6-ai-expanded"
    / "curated"
    / "kiwi-brain-ai-expanded-v0.1"
    / "repairs"
    / "citation_contract_repair_v0.1"
)
SOURCE_PACKS = ["real_citation_spans_v0.1", "report_and_filing_spans_v0.1"]
EVAL_ID = "citation_real_eval_v1"
OUT_DIR = BASE_REPAIR_DIR / EVAL_ID
AUDIT_DATE = "2026-07-02"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, required=True,
                        help="Directory with votes_passA.jsonl, votes_passB.jsonl, adjudications.json")
    args = parser.parse_args()

    votes_a = {r["sample_id"]: r for r in load_jsonl(args.audit_dir / "votes_passA.jsonl")}
    votes_b = {r["sample_id"]: r for r in load_jsonl(args.audit_dir / "votes_passB.jsonl")}
    adjudications = json.loads((args.audit_dir / "adjudications.json").read_text())
    adj_by_id = {d["sample_id"]: d for d in adjudications["decisions"]}

    rows: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    for pack in SOURCE_PACKS:
        for row in load_jsonl(BASE_REPAIR_DIR / pack / "spans" / "all.jsonl"):
            sid = row["sample_id"]
            original_label = row["label"]["support_type"]
            va, vb = votes_a.get(sid), votes_b.get(sid)
            adj = adj_by_id.get(sid)
            audited_label = adj["audited_label"] if adj else original_label
            status = "corrected" if (adj and adj["audited_label"] != adj["original_label"]) else "confirmed"

            if status == "corrected":
                row["label"]["support_type"] = audited_label
                row["label"]["support_score"] = adj["support_score"]
                row["label"]["original_support_type"] = original_label
                row["label"]["supports_claim_part"] = adj["rationale"]
                changed.append({"sample_id": sid, "from": original_label, "to": audited_label, "split": row["split"]})

            row["audit"] = {
                "audit_id": EVAL_ID,
                "audit_date": AUDIT_DATE,
                "protocol": "blind_double_annotation_plus_adjudication",
                "audited_by": "claude (two independent blind auditor agents + main-session adjudicator); no human pass",
                "vote_pass_a": (va or {}).get("label"),
                "vote_pass_b": (vb or {}).get("label"),
                "status": status,
                "adjudication_note": adj["rationale"] if adj else None,
            }
            row["provenance"]["requires_human_audit"] = False
            row["provenance"]["audit_note"] = "AI blind double-annotation audit completed 2026-07-02; see audit block."
            rows.append(row)

    assert len(rows) == 131, f"expected 131 rows, got {len(rows)}"
    label_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    for row in rows:
        label_counts[row["label"]["support_type"]] = label_counts.get(row["label"]["support_type"], 0) + 1
        split_counts[row["split"]] = split_counts.get(row["split"], 0) + 1

    by_split: dict[str, list[dict[str, Any]]] = {"train": [], "dev": [], "test": []}
    for row in rows:
        by_split[row["split"]].append(row)

    write_jsonl(OUT_DIR / "rows" / "all.jsonl", rows)
    for split, split_rows in by_split.items():
        write_jsonl(OUT_DIR / "rows" / f"{split}.jsonl", split_rows)
    # audit evidence travels with the pack
    (OUT_DIR / "audit").mkdir(parents=True, exist_ok=True)
    for name in ["votes_passA.jsonl", "votes_passB.jsonl", "adjudications.json"]:
        (OUT_DIR / "audit" / name).write_bytes((args.audit_dir / name).read_bytes())

    manifest = {
        "eval_id": EVAL_ID,
        "created_at": now_utc(),
        "audit_date": AUDIT_DATE,
        "row_count": len(rows),
        "label_counts": label_counts,
        "split_counts": split_counts,
        "corrections": changed,
        "correction_rate": round(len(changed) / len(rows), 4),
        "frozen": {
            "eval_splits": ["dev", "test"],
            "rule": "test is untouchable; prompts and experience libraries iterate on train/dev only; any change to dev/test requires a new eval_id",
        },
        "source_packs": {
            pack: sha256_file(BASE_REPAIR_DIR / pack / "spans" / "all.jsonl") for pack in SOURCE_PACKS
        },
        "contract_id": "citation_contract_repair_v0.1",
        "git": {
            "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
            "commit": git_value(["rev-parse", "HEAD"]),
        },
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
