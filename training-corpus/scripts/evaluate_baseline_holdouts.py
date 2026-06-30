#!/usr/bin/env python3
"""Evaluate trained KIWI CPU baselines on external realistic holdouts.

This script does not train new models. It loads existing `model.joblib`
artifacts and runs them against older golden data, long-research traces, and
real tool traces. The goal is to detect distribution shift and schema gaps
before spending GPU time on SFT/DPO/GRPO.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import joblib
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

import train_specialist_baselines as baseline


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPANDED_BASELINE = (
    REPO_ROOT
    / "training-corpus"
    / "runs"
    / "overnight-20260629-v0.6-ai-expanded"
    / "curated"
    / "kiwi-brain-ai-expanded-v0.1"
    / "baselines"
    / "specialist_cpu_ai_expanded_v0.1_20260630T080225Z"
)
DEFAULT_GOLDEN_DIR = (
    REPO_ROOT
    / "training-corpus"
    / "runs"
    / "x-bookmarks-recent-111-20260629"
    / "curated"
    / "golden_v0.1"
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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


def append_event(path: Path, event: str, **payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"ts": now_utc(), "event": event, **payload}, ensure_ascii=False, sort_keys=True) + "\n")


def git_value(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def git_state() -> dict[str, Any]:
    return {
        "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": git_value(["rev-parse", "HEAD"]),
        "status_short": git_value(["status", "--short"]) or "",
        "diff_stat": git_value(["diff", "--stat"]) or "",
    }


def model_labels(model: Any) -> list[str]:
    classifier = getattr(model, "named_steps", {}).get("clf")
    classes = getattr(classifier, "classes_", [])
    return [str(item) for item in classes]


def route_extra_metrics(y_true: list[str], y_pred: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return baseline.route_extra_metrics(y_true, y_pred, rows)


def evaluate_rows(
    model: Any,
    rows: list[dict[str, Any]],
    text_fn: Callable[[dict[str, Any]], str],
    label_fn: Callable[[dict[str, Any]], str],
    dataset: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    x = [text_fn(row) for row in rows]
    y_true = [label_fn(row) for row in rows]
    y_pred = list(model.predict(x)) if rows else []
    train_labels = model_labels(model)
    true_labels = sorted({label for label in y_true if label})
    union_labels = sorted(set(train_labels) | set(true_labels))
    unseen_true_labels = sorted(set(true_labels) - set(train_labels))
    comparable_indices = [index for index, label in enumerate(y_true) if label in set(train_labels)]

    metrics: dict[str, Any] = {
        "rows": len(rows),
        "accuracy_all_rows": round(accuracy_score(y_true, y_pred), 4) if rows else None,
        "macro_f1_all_labels": round(f1_score(y_true, y_pred, labels=union_labels, average="macro", zero_division=0), 4)
        if rows
        else None,
        "weighted_f1_all_labels": round(
            f1_score(y_true, y_pred, labels=union_labels, average="weighted", zero_division=0), 4
        )
        if rows
        else None,
        "comparable_rows": len(comparable_indices),
        "unseen_true_labels": unseen_true_labels,
        "schema_gap": bool(unseen_true_labels),
    }
    if comparable_indices:
        y_true_comparable = [y_true[index] for index in comparable_indices]
        y_pred_comparable = [y_pred[index] for index in comparable_indices]
        metrics["accuracy_seen_labels_only"] = round(accuracy_score(y_true_comparable, y_pred_comparable), 4)
        metrics["macro_f1_seen_labels_only"] = round(
            f1_score(y_true_comparable, y_pred_comparable, labels=train_labels, average="macro", zero_division=0),
            4,
        )
    else:
        metrics["accuracy_seen_labels_only"] = None
        metrics["macro_f1_seen_labels_only"] = None
    if dataset == "router_classifier":
        metrics.update(route_extra_metrics(y_true, y_pred, rows))

    report = classification_report(y_true, y_pred, labels=union_labels, zero_division=0, output_dict=True)
    matrix = confusion_matrix(y_true, y_pred, labels=union_labels)
    predictions = []
    for index, row in enumerate(rows):
        expected = y_true[index]
        predicted = y_pred[index]
        predictions.append(
            {
                "sample_id": baseline.row_id(row, index),
                "expected_label": expected,
                "predicted_label": predicted,
                "correct": expected == predicted,
                "expected_label_seen_in_training": expected in set(train_labels),
                "input_preview": text_fn(row)[:1000],
                "provenance": row.get("provenance"),
                "source": row.get("source"),
                "synthetic": row.get("synthetic"),
            }
        )
    summary = {
        "metrics": metrics,
        "model_labels": train_labels,
        "true_label_distribution": dict(Counter(y_true)),
        "prediction_distribution": dict(Counter(y_pred)),
        "classification_report": report,
        "confusion_matrix": {"labels": union_labels, "rows": matrix.tolist()},
    }
    return summary, predictions


def real_tool_trace_router_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for trace in read_jsonl(path):
        symbol = trace.get("symbol")
        tool_names = [item.get("tool_name") for item in trace.get("tool_calls") or [] if item.get("tool_name")]
        rows.append(
            {
                "sample_id": f"router_{trace.get('trace_id') or trace.get('task_id')}",
                "input": {
                    "user_query": trace.get("user_query"),
                    "user_profile_summary": "risk-aware financial research user; wants evidence-first market explanation",
                    "page_context": "real_tool_trace_pilot_10",
                    "symbol": symbol,
                    "market_context": {
                        "detected_tickers": [symbol] if symbol else [],
                        "narrative_tags": ["real_tool_trace", trace.get("verdict")],
                    },
                },
                "label": {
                    "route_label": trace.get("route"),
                    "risk_level": "medium",
                    "required_tools": tool_names,
                    "needs_citation": True,
                    "needs_realtime_data": True,
                    "requires_human_gate": trace.get("route") == "risk_review",
                },
                "provenance": {
                    "trace_id": trace.get("trace_id"),
                    "task_id": trace.get("task_id"),
                    "source_type": "real_tool_trace_pilot_10",
                    "verdict": trace.get("verdict"),
                    "failure_taxonomy": trace.get("failure_taxonomy") or [],
                },
                "source": "real_tool_trace_pilot_10",
                "synthetic": False,
            }
        )
    return rows


def holdout_specs(golden_dir: Path) -> list[dict[str, Any]]:
    long_dir = golden_dir / "long_research_trace_source_quality_repair_25"
    real_tool_dir = golden_dir / "real_tool_trace_pilot_10"
    return [
        {
            "name": "golden_v0.1_router_all",
            "dataset": "router_classifier",
            "kind": "static_jsonl",
            "path": golden_dir / "datasets" / "router_classifier" / "all.jsonl",
            "why": "Older strict social/bookmark router rows with labels absent from the expanded split.",
        },
        {
            "name": "golden_v0.1_risk_all",
            "dataset": "risk_reviewer",
            "kind": "static_jsonl",
            "path": golden_dir / "datasets" / "risk_reviewer" / "all.jsonl",
            "why": "Older risk reviewer rows with partial-support research-risk phrasing.",
        },
        {
            "name": "golden_v0.1_citation_all",
            "dataset": "citation_verifier",
            "kind": "static_jsonl",
            "path": golden_dir / "datasets" / "citation_verifier" / "all.jsonl",
            "why": "Strict citation rows containing partial support, insufficient, and contradiction labels.",
        },
        {
            "name": "long_research_repair_25_router_all",
            "dataset": "router_classifier",
            "kind": "static_jsonl",
            "path": long_dir / "datasets" / "router_classifier" / "all.jsonl",
            "why": "Long research router rows that should generally route to deep research.",
        },
        {
            "name": "long_research_repair_25_risk_all",
            "dataset": "risk_reviewer",
            "kind": "static_jsonl",
            "path": long_dir / "datasets" / "risk_reviewer" / "all.jsonl",
            "why": "Long research memo risk labels with medium-risk and human-gate fields.",
        },
        {
            "name": "long_research_repair_25_citation_all",
            "dataset": "citation_verifier",
            "kind": "static_jsonl",
            "path": long_dir / "datasets" / "citation_verifier" / "all.jsonl",
            "why": "Candidate evidence spans from real long-research trajectories; exposes citation schema mismatch.",
        },
        {
            "name": "real_tool_trace_pilot_10_router",
            "dataset": "router_classifier",
            "kind": "real_tool_trace_router",
            "path": real_tool_dir / "real_tool_traces.jsonl",
            "why": "Read-only real tool execution traces converted into router holdout rows.",
        },
    ]


def load_holdout_rows(spec: dict[str, Any]) -> list[dict[str, Any]]:
    path = Path(spec["path"])
    if spec["kind"] == "static_jsonl":
        return read_jsonl(path)
    if spec["kind"] == "real_tool_trace_router":
        return real_tool_trace_router_rows(path)
    raise ValueError(f"Unknown holdout kind: {spec['kind']}")


def build_readme(out_dir: Path, run_summary: dict[str, Any]) -> None:
    lines = [
        "# Realistic Holdout Evaluation",
        "",
        "This run loads an existing CPU baseline and evaluates it on external",
        "holdouts. It does not train new models.",
        "",
        "## Why",
        "",
        "The expanded train/dev/test split produced very high router and risk",
        "metrics. This holdout run checks whether those scores survive older",
        "golden rows, long-research traces, and real tool traces.",
        "",
        "## Run",
        "",
        f"- run id: `{run_summary['run_id']}`",
        f"- baseline: `{run_summary['baseline_dir']}`",
        f"- created at: `{run_summary['created_at']}`",
        "",
        "## Results",
        "",
        "| Holdout | Dataset | Rows | Acc all | Macro F1 all | Comparable rows | Acc seen-labels | Schema gap | Unseen true labels |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for name, result in run_summary["holdouts"].items():
        metrics = result["metrics"]
        unseen = ", ".join(metrics["unseen_true_labels"]) if metrics["unseen_true_labels"] else ""
        lines.append(
            f"| {name} | {result['dataset']} | {metrics['rows']} | "
            f"{metrics['accuracy_all_rows']} | {metrics['macro_f1_all_labels']} | "
            f"{metrics['comparable_rows']} | {metrics['accuracy_seen_labels_only']} | "
            f"{metrics['schema_gap']} | {unseen} |"
        )
    lines.extend(
        [
            "",
            "## Reading The Metrics",
            "",
            "- `accuracy_all_rows` treats unseen labels as failures. This is useful for",
            "  finding schema gaps.",
            "- `accuracy_seen_labels_only` evaluates only rows whose gold label existed",
            "  in the baseline model's training label set. This is useful for measuring",
            "  transfer on comparable rows without hiding the schema gap.",
            "- A `schema_gap` means the model was never trained to emit one or more",
            "  labels in this holdout, so the fix is data/schema work before model work.",
            "",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_EXPANDED_BASELINE)
    parser.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    parser.add_argument("--out-root", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_dir = args.baseline_dir.resolve()
    golden_dir = args.golden_dir.resolve()
    run_id = args.run_id or f"realistic_holdout_eval_v0.1_{timestamp_id()}"
    out_root = (args.out_root or (baseline_dir / "holdouts")).resolve()
    out_dir = out_root / run_id
    logs_dir = out_dir / "logs"
    events_path = logs_dir / "events.jsonl"
    checkpoint_path = logs_dir / "checkpoint.json"
    out_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "run_id": run_id,
        "created_at": now_utc(),
        "baseline_dir": str(baseline_dir),
        "golden_dir": str(golden_dir),
        "out_dir": str(out_dir),
        "boundary": "External holdout evaluation only; no training.",
    }
    write_json(out_dir / "config.json", config)
    write_json(
        out_dir / "manifest.json",
        {
            **config,
            "python": sys.version,
            "platform": platform.platform(),
            "command": " ".join(sys.argv),
            "cwd": os.getcwd(),
            "git": git_state(),
        },
    )
    append_event(events_path, "run_start", run_id=run_id)
    write_json(checkpoint_path, {"ts": now_utc(), "status": "running", "run_id": run_id, "completed": []})

    loaded_models: dict[str, Any] = {}
    results: dict[str, Any] = {}
    completed: list[str] = []
    try:
        for spec in holdout_specs(golden_dir):
            name = spec["name"]
            dataset = spec["dataset"]
            data_spec = baseline.DATASETS[dataset]
            model_path = baseline_dir / dataset / "model.joblib"
            if not model_path.exists():
                append_event(events_path, "holdout_skip", holdout=name, reason="missing_model", model_path=str(model_path))
                continue
            if dataset not in loaded_models:
                loaded_models[dataset] = joblib.load(model_path)
                append_event(events_path, "model_loaded", dataset=dataset, model_path=str(model_path))
            rows = load_holdout_rows(spec)
            append_event(
                events_path,
                "holdout_loaded",
                holdout=name,
                dataset=dataset,
                rows=len(rows),
                source_path=str(spec["path"]),
            )
            summary, predictions = evaluate_rows(
                loaded_models[dataset],
                rows,
                data_spec["text_fn"],
                data_spec["label_fn"],
                dataset,
            )
            result = {
                "holdout": name,
                "dataset": dataset,
                "why": spec["why"],
                "source_path": str(spec["path"]),
                **summary,
            }
            results[name] = result
            holdout_dir = out_dir / name
            write_json(holdout_dir / "metrics.json", result)
            write_jsonl(holdout_dir / "predictions.jsonl", predictions)
            write_jsonl(holdout_dir / "errors.jsonl", [item for item in predictions if not item["correct"]])
            completed.append(name)
            append_event(events_path, "holdout_complete", holdout=name, metrics=summary["metrics"])
            write_json(checkpoint_path, {"ts": now_utc(), "status": "running", "run_id": run_id, "completed": completed})
    except Exception as exc:
        append_event(events_path, "run_error", error=repr(exc), completed=completed)
        write_json(
            checkpoint_path,
            {"ts": now_utc(), "status": "failed", "run_id": run_id, "completed": completed, "error": repr(exc)},
        )
        raise

    run_summary = {**config, "completed_at": now_utc(), "holdouts": results}
    write_json(out_dir / "metrics.json", run_summary)
    build_readme(out_dir, run_summary)
    write_json(checkpoint_path, {"ts": now_utc(), "status": "complete", "run_id": run_id, "completed": completed})
    append_event(events_path, "run_complete", run_id=run_id, completed=completed)
    print(json.dumps({"run_id": run_id, "out_dir": str(out_dir), "holdouts": completed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
