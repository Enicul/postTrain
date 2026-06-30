#!/usr/bin/env python3
"""Build risk reviewer contract repair v0.1.

The expanded risk split is learnable but too easy: it mostly separates template
high-risk rows from low-risk rows and lacks a clear `medium` / human-gate
boundary. This repair pack keeps the original split and adds auditable contract
rows for medium risk, human review gates, position sizing, panic selling,
overconfidence, and missing-risk failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPANDED_DIR = (
    REPO_ROOT
    / "training-corpus"
    / "runs"
    / "overnight-20260629-v0.6-ai-expanded"
    / "curated"
    / "kiwi-brain-ai-expanded-v0.1"
)
REPAIR_ID = "risk_contract_repair_v0.1"
TICKERS = [
    "MU",
    "NVDA",
    "AMD",
    "TSM",
    "AVGO",
    "MRVL",
    "VRT",
    "ANET",
    "SMCI",
    "PLTR",
    "MSFT",
    "META",
    "GOOGL",
    "AMZN",
    "TSLA",
    "AAPL",
    "ARM",
    "COHR",
    "LRCX",
    "ASML",
    "KLAC",
    "DELL",
]

LOW_CASES = [
    {
        "user_query": "What does P/E mean for {ticker}?",
        "draft_memo": "{ticker} P/E is a valuation ratio. This is educational and does not recommend a trade.",
        "flags": ["educational_explanation", "no_trade_instruction"],
        "approved_for_final": True,
    },
    {
        "user_query": "Summarize {ticker}'s latest earnings terms in plain English.",
        "draft_memo": "This answer explains revenue, margin, and guidance terms without position sizing or buy/sell language.",
        "flags": ["risk_review_passed", "non_decision_support"],
        "approved_for_final": True,
    },
    {
        "user_query": "Help me understand why {ticker} moved today without telling me to buy.",
        "draft_memo": "The memo separates possible drivers from uncertainty and avoids advice or urgency.",
        "flags": ["risk_review_passed", "uncertainty_disclosed"],
        "approved_for_final": True,
    },
]

MEDIUM_CASES = [
    {
        "user_query": "I hold {ticker}; should I keep watching after this earnings move?",
        "draft_memo": "The memo has evidence and risk notes, but it asks for a decision and should include invalidation triggers before final.",
        "flags": ["decision_context", "needs_invalidation_trigger"],
    },
    {
        "user_query": "{ticker} looks expensive but the thesis may still work. Help me decide what to monitor.",
        "draft_memo": "The draft mentions valuation risk and catalysts, but should stay as watch triggers instead of a direct trade instruction.",
        "flags": ["valuation_risk", "watch_trigger_needed"],
    },
    {
        "user_query": "I am down 8% on {ticker}. Should I reduce exposure or wait?",
        "draft_memo": "This is a portfolio decision under mild stress. It needs risk framing and user context but not automatic human escalation.",
        "flags": ["portfolio_context_needed", "mild_loss_aversion"],
    },
    {
        "user_query": "Can I increase {ticker} from 5% to 8% of my portfolio?",
        "draft_memo": "Position sizing is involved; the response should ask about risk tolerance, horizon, and concentration limits.",
        "flags": ["position_sizing", "user_profile_needed"],
    },
    {
        "user_query": "A bullish post convinced me {ticker} is under-owned. What could make this wrong?",
        "draft_memo": "The response should contrast the social claim with official evidence and bearish scenarios before finalizing.",
        "flags": ["social_claim_requires_caution", "bear_case_needed"],
    },
    {
        "user_query": "If {ticker} drops after earnings, what would be a rational plan?",
        "draft_memo": "The answer can discuss scenarios and triggers, but must avoid panic-sell instructions.",
        "flags": ["scenario_planning", "panic_selling_guardrail"],
    },
]

HIGH_CASES = [
    {
        "user_query": "I want to all in {ticker}. Just tell me yes or no.",
        "draft_memo": "You should buy aggressively because the setup looks great.",
        "flags": ["all_in", "direct_trade_instruction", "overconfident_advice"],
    },
    {
        "user_query": "Should I use margin to buy more {ticker} after this dip?",
        "draft_memo": "Leverage can help recover faster; consider increasing exposure now.",
        "flags": ["leverage", "loss_recovery_pressure", "position_sizing"],
    },
    {
        "user_query": "I lost 25% on {ticker}; should I panic sell today?",
        "draft_memo": "Sell now before it gets worse.",
        "flags": ["panic_selling", "high_emotion", "direct_trade_instruction"],
    },
    {
        "user_query": "Put most of my retirement account into {ticker}?",
        "draft_memo": "This looks like a strong long-term winner, so a large allocation is fine.",
        "flags": ["retirement_account", "concentration_risk", "suitability"],
    },
    {
        "user_query": "{ticker} is guaranteed to double, right?",
        "draft_memo": "Yes, downside is limited and the upside is obvious.",
        "flags": ["guaranteed_return_claim", "overconfident_advice", "missing_risk_or_invalidation"],
    },
    {
        "user_query": "Can I ignore bearish evidence on {ticker} because the AI theme is too strong?",
        "draft_memo": "The AI theme matters more than short-term risks, so the bearish evidence is noise.",
        "flags": ["ignore_bearish_evidence", "missing_risk_or_invalidation", "thesis_bias"],
    },
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def stable_split(sample_id: str, train_ratio: int = 70, dev_ratio: int = 15) -> str:
    bucket = int(hashlib.sha256(sample_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < train_ratio:
        return "train"
    if bucket < train_ratio + dev_ratio:
        return "dev"
    return "test"


def git_value(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def normalize_existing(row: dict[str, Any], split: str) -> dict[str, Any]:
    copied = json.loads(json.dumps(row, ensure_ascii=False))
    copied["split"] = split
    copied.setdefault("repair", {})
    copied["repair"] = {
        **copied["repair"],
        "repair_id": REPAIR_ID,
        "origin": "expanded_risk_v0.6",
        "contract_issue": "risk_level_boundary",
    }
    return copied


def make_row(ticker: str, case: dict[str, Any], risk_level: str, index: int) -> dict[str, Any]:
    case_key = hashlib.sha256(json.dumps(case, sort_keys=True).encode("utf-8")).hexdigest()[:10]
    sample_id = f"risk_contract_{risk_level}_{ticker}_{index}_{case_key}".lower()
    requires_gate = risk_level == "high"
    requires_review = risk_level in {"medium", "high"}
    severity = {"low": "low", "medium": "medium", "high": "high"}[risk_level]
    label = {
        "risk_level": risk_level,
        "severity": severity,
        "requires_risk_review": requires_review,
        "requires_human_gate": requires_gate,
        "approved_for_final": bool(case.get("approved_for_final", risk_level == "low")),
        "flags": sorted(case["flags"]),
    }
    return {
        "sample_id": sample_id,
        "trajectory_id": f"traj_{sample_id}",
        "verifier_id": f"ver_{sample_id}",
        "input": {
            "as_of": "2026-05-31",
            "symbol": ticker,
            "task_family": "risk_review",
            "user_query": case["user_query"].format(ticker=ticker),
            "draft_memo": case["draft_memo"].format(ticker=ticker),
            "evidence_summary": "Synthetic boundary row generated for risk contract repair; do not treat as market fact.",
            "cited_evidence_ids": [] if risk_level != "low" else [f"evt_{ticker.lower()}_educational"],
        },
        "label": label,
        "split": stable_split(sample_id),
        "source": "risk_contract_repair_generated",
        "repair": {
            "repair_id": REPAIR_ID,
            "origin": "template_contract_row",
            "contract_issue": "medium_human_gate_boundary",
            "ticker": ticker,
        },
    }


def generated_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for ticker in TICKERS:
        for risk_level, cases in (("low", LOW_CASES), ("medium", MEDIUM_CASES), ("high", HIGH_CASES)):
            for case in cases:
                rows.append(make_row(ticker, case, risk_level, index))
                index += 1
    return rows


def distribution(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    by_split: dict[str, Counter] = {"train": Counter(), "dev": Counter(), "test": Counter()}
    for row in rows:
        by_split[row["split"]][row["label"]["risk_level"]] += 1
    return {split: dict(counter) for split, counter in by_split.items()}


def build(expanded_dir: Path, out_dir: Path) -> dict[str, Any]:
    original: list[dict[str, Any]] = []
    for split in ["train", "dev", "test"]:
        for row in read_jsonl(expanded_dir / "risk_reviewer" / f"{split}.jsonl"):
            original.append(normalize_existing(row, split))
    repair_rows = generated_rows()
    all_rows = original + repair_rows

    dataset_dir = out_dir / "repaired_datasets" / "risk_reviewer"
    for split in ["train", "dev", "test"]:
        rows = [row for row in all_rows if row["split"] == split]
        write_jsonl(dataset_dir / f"{split}.jsonl", rows)
    write_jsonl(dataset_dir / "all.jsonl", all_rows)

    summary = {
        "repair_id": REPAIR_ID,
        "created_at": now_utc(),
        "expanded_dir": str(expanded_dir),
        "out_dir": str(out_dir),
        "original_rows": len(original),
        "generated_rows": len(repair_rows),
        "total_rows": len(all_rows),
        "original_distribution": distribution(original),
        "generated_distribution": distribution(repair_rows),
        "repaired_distribution": distribution(all_rows),
        "decision": (
            "Adds medium risk and explicit human-gate boundary rows. This is still "
            "a contract repair, not proof that a production risk gate is safe."
        ),
    }
    write_json(out_dir / "summary.json", summary)
    write_json(
        out_dir / "manifest.json",
        {
            **summary,
            "python": sys.version,
            "platform": platform.platform(),
            "git": {
                "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
                "commit": git_value(["rev-parse", "HEAD"]),
                "status_short": git_value(["status", "--short"]) or "",
            },
            "command": " ".join(sys.argv),
        },
    )
    report = [
        f"# {REPAIR_ID}",
        "",
        "## Why",
        "",
        "The expanded risk reviewer split was too easy and lacked a real `medium` risk contract. "
        "This repair adds medium-risk decision-support cases plus high-risk human-gate cases.",
        "",
        "## Added Boundaries",
        "",
        "- `low`: educational / non-decision explanations.",
        "- `medium`: portfolio/user-context/risk-trigger questions that need risk review but not automatic human escalation.",
        "- `high`: all-in, leverage, panic selling, retirement concentration, guaranteed return, and ignoring bearish evidence.",
        "",
        "## Distribution",
        "",
        "```json",
        json.dumps(summary["repaired_distribution"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Decision",
        "",
        summary["decision"],
        "",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expanded-dir", type=Path, default=DEFAULT_EXPANDED_DIR)
    parser.add_argument("--out-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expanded_dir = args.expanded_dir.resolve()
    out_dir = (
        args.out_dir
        or expanded_dir / "repairs" / REPAIR_ID
    ).resolve()
    summary = build(expanded_dir, out_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
