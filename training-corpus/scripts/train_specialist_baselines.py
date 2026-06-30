#!/usr/bin/env python3
"""Train reproducible CPU baselines for KIWI narrow specialists.

These are intentionally cheap baselines, not final post-training runs. The goal
is to make each specialist measurable before spending GPU time on small LLM
SFT/DPO/GRPO.
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
from urllib.parse import urlparse

import joblib
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_DIR = (
    REPO_ROOT
    / "training-corpus"
    / "runs"
    / "x-bookmarks-recent-111-20260629"
    / "curated"
    / "golden_v0.1"
)

LOW_COST_ROUTES = {"fast_answer", "clarification_needed", "price_lookup"}
HIGH_COST_ROUTES = {"deep_research", "risk_review"}
SAFETY_OK_ROUTES = {"deep_research", "risk_review", "evidence_check"}


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
    row = {"ts": now_utc(), "event": event, **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def row_id(row: dict[str, Any], index: int) -> str:
    return row.get("sample_id") or row.get("id") or f"row_{index:05d}"


def input_obj(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("input") or row.get("task", {}).get("input") or {}


def label_obj(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("label") or row.get("output") or {}


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def router_text(row: dict[str, Any]) -> str:
    inp = input_obj(row)
    market = inp.get("market_context") or {}
    parts = [
        f"user_query: {stringify(inp.get('user_query'))}",
        f"user_profile: {stringify(inp.get('user_profile_summary') or inp.get('user_profile'))}",
        f"page_context: {stringify(inp.get('page_context'))}",
        f"symbol: {stringify(inp.get('symbol'))}",
        f"tickers: {stringify(market.get('detected_tickers') or inp.get('tickers'))}",
        f"tags: {stringify(market.get('narrative_tags') or inp.get('tags'))}",
    ]
    return "\n".join(parts)


def risk_text(row: dict[str, Any]) -> str:
    inp = input_obj(row)
    return "\n".join(
        [
            f"user_query: {stringify(inp.get('user_query') or inp.get('user_request'))}",
            f"symbol: {stringify(inp.get('symbol'))}",
            f"task_family: {stringify(inp.get('task_family'))}",
            f"claim: {stringify(inp.get('claim'))}",
            f"draft_memo: {stringify(inp.get('draft_memo'))}",
            f"evidence_summary: {stringify(inp.get('evidence_summary'))}",
            f"cited_evidence_ids: {stringify(inp.get('cited_evidence_ids'))}",
            f"verdict: {stringify(inp.get('verdict'))}",
            f"source: {stringify((row.get('provenance') or {}).get('source_url'))}",
        ]
    )


def citation_text(row: dict[str, Any]) -> str:
    inp = input_obj(row)
    return "\n".join(
        [
            f"claim: {stringify(inp.get('claim'))}",
            f"evidence_span: {stringify(inp.get('evidence_span') or inp.get('evidence_text'))}",
            f"evidence_id: {stringify(inp.get('evidence_id'))}",
            f"source_class: {stringify(inp.get('source_class'))}",
            f"source: {stringify(inp.get('source'))}",
        ]
    )


def source_domain(url: Any) -> str:
    parsed = urlparse(str(url or ""))
    return parsed.netloc.lower().removeprefix("www.")


def citation_text_with_url(row: dict[str, Any]) -> str:
    inp = input_obj(row)
    source_url = inp.get("source_url")
    return "\n".join(
        [
            f"claim: {stringify(inp.get('claim'))}",
            f"evidence_span: {stringify(inp.get('evidence_span') or inp.get('evidence_text'))}",
            f"evidence_id: {stringify(inp.get('evidence_id'))}",
            f"source_class: {stringify(inp.get('source_class'))}",
            f"source: {stringify(inp.get('source'))}",
            f"source_domain: {source_domain(source_url)}",
            f"source_url: {stringify(source_url)}",
        ]
    )


def router_label(row: dict[str, Any]) -> str:
    return stringify(label_obj(row).get("route_label"))


def risk_label(row: dict[str, Any]) -> str:
    return stringify(label_obj(row).get("risk_level"))


def citation_label(row: dict[str, Any]) -> str:
    label = label_obj(row)
    value = label.get("support_type") or label.get("verdict")
    if value == "supported":
        value = "supports"
    elif value == "unsupported":
        value = "not_supported"
    return stringify(value)


def citation_binary_label(row: dict[str, Any]) -> str:
    label = label_obj(row)
    if label.get("support_binary"):
        return stringify(label.get("support_binary"))
    support_type = stringify(label.get("support_type") or label.get("original_support_type"))
    return "some_support" if support_type in {"supports", "partial_support"} else "no_support"


def build_pipeline(num_labels: int) -> Pipeline:
    if num_labels <= 1:
        classifier = DummyClassifier(strategy="most_frequent")
    else:
        classifier = LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            solver="liblinear",
            random_state=7,
        )
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(2, 5),
                    min_df=1,
                    max_features=8000,
                    lowercase=True,
                ),
            ),
            ("clf", classifier),
        ]
    )


def majority_baseline(x_train: list[str], y_train: list[str], x_eval: list[str], y_eval: list[str]) -> dict[str, Any]:
    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(x_train, y_train)
    pred = list(dummy.predict(x_eval)) if x_eval else []
    return {
        "accuracy": round(accuracy_score(y_eval, pred), 4) if y_eval else None,
        "macro_f1": round(f1_score(y_eval, pred, average="macro", zero_division=0), 4) if y_eval else None,
        "predicted_label": pred[0] if pred else None,
    }


def route_extra_metrics(y_true: list[str], y_pred: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    over_candidates = [i for i, actual in enumerate(y_true) if actual in LOW_COST_ROUTES]
    under_candidates = [i for i, actual in enumerate(y_true) if actual in HIGH_COST_ROUTES]
    safety_candidates = [
        i
        for i, row in enumerate(rows)
        if label_obj(row).get("risk_level") == "high" or bool(label_obj(row).get("requires_human_gate"))
    ]
    return {
        "over_trigger_rate": round(
            sum(1 for i in over_candidates if y_pred[i] in HIGH_COST_ROUTES) / len(over_candidates), 4
        )
        if over_candidates
        else None,
        "under_trigger_rate": round(
            sum(1 for i in under_candidates if y_pred[i] in LOW_COST_ROUTES) / len(under_candidates), 4
        )
        if under_candidates
        else None,
        "safety_recall": round(
            sum(1 for i in safety_candidates if y_pred[i] in SAFETY_OK_ROUTES) / len(safety_candidates), 4
        )
        if safety_candidates
        else None,
    }


def evaluate(
    model: Pipeline,
    rows: list[dict[str, Any]],
    labels: list[str],
    text_fn: Callable[[dict[str, Any]], str],
    label_fn: Callable[[dict[str, Any]], str],
    dataset: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    x = [text_fn(row) for row in rows]
    y_true = [label_fn(row) for row in rows]
    y_pred = list(model.predict(x)) if rows else []
    report = classification_report(y_true, y_pred, labels=labels, zero_division=0, output_dict=True)
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    metrics = {
        "accuracy": round(accuracy_score(y_true, y_pred), 4) if y_true else None,
        "macro_f1": round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4) if y_true else None,
        "weighted_f1": round(f1_score(y_true, y_pred, average="weighted", zero_division=0), 4) if y_true else None,
    }
    if dataset == "router_classifier":
        metrics.update(route_extra_metrics(y_true, y_pred, rows))

    predictions = []
    for index, row in enumerate(rows):
        predictions.append(
            {
                "sample_id": row_id(row, index),
                "expected_label": y_true[index],
                "predicted_label": y_pred[index],
                "correct": y_true[index] == y_pred[index],
                "input_preview": text_fn(row)[:800],
                "provenance": row.get("provenance"),
                "source": row.get("source"),
                "synthetic": row.get("synthetic"),
            }
        )
    return (
        {
            "metrics": metrics,
            "label_distribution": dict(Counter(y_true)),
            "prediction_distribution": dict(Counter(y_pred)),
            "classification_report": report,
            "confusion_matrix": {"labels": labels, "rows": matrix.tolist()},
        },
        predictions,
    )


DATASETS: dict[str, dict[str, Any]] = {
    "router_classifier": {
        "text_fn": router_text,
        "label_fn": router_label,
        "target": "route_label",
        "why": "Coordinator routing baseline before learned router or prompt-harness replacement.",
    },
    "risk_reviewer": {
        "text_fn": risk_text,
        "label_fn": risk_label,
        "target": "risk_level",
        "why": "Safety/risk classifier baseline for overconfidence, missing-risk, and gate policy.",
    },
    "citation_verifier": {
        "text_fn": citation_text,
        "label_fn": citation_label,
        "target": "support_type",
        "why": "Claim-evidence support classifier baseline before small verifier fine-tuning.",
    },
    "citation_verifier_url": {
        "text_fn": citation_text_with_url,
        "label_fn": citation_label,
        "target": "support_type",
        "why": "Feature repair probe: include source URL/domain as source-quality context without trace-id leakage.",
    },
    "citation_support_binary": {
        "text_fn": citation_text_with_url,
        "label_fn": citation_binary_label,
        "target": "support_binary",
        "why": "Schema repair probe: first determine whether a span gives any support before five-way support typing.",
    },
}


def train_one(dataset: str, data_dir: Path, out_dir: Path, events_path: Path) -> dict[str, Any]:
    spec = DATASETS[dataset]
    text_fn: Callable[[dict[str, Any]], str] = spec["text_fn"]
    label_fn: Callable[[dict[str, Any]], str] = spec["label_fn"]

    split_rows: dict[str, list[dict[str, Any]]] = {}
    for split in ["train", "dev", "test"]:
        path = data_dir / dataset / f"{split}.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Missing split for {dataset}: {path}")
        split_rows[split] = read_jsonl(path)
        append_event(events_path, "loaded_split", dataset=dataset, split=split, rows=len(split_rows[split]), file_path=str(path))

    train_rows = split_rows["train"]
    x_train = [text_fn(row) for row in train_rows]
    y_train = [label_fn(row) for row in train_rows]
    labels = sorted({label_fn(row) for rows in split_rows.values() for row in rows if label_fn(row)})
    if not labels:
        raise ValueError(f"No labels found for {dataset}")

    append_event(events_path, "train_start", dataset=dataset, train_rows=len(train_rows), labels=labels)
    model = build_pipeline(len(set(y_train)))
    model.fit(x_train, y_train)
    append_event(events_path, "train_complete", dataset=dataset, model_class=type(model.named_steps["clf"]).__name__)

    ds_out = out_dir / dataset
    ds_out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ds_out / "model.joblib")

    evaluations: dict[str, Any] = {}
    predictions_by_split: dict[str, list[dict[str, Any]]] = {}
    for split, rows in split_rows.items():
        evaluation, predictions = evaluate(model, rows, labels, text_fn, label_fn, dataset)
        evaluations[split] = evaluation
        predictions_by_split[split] = predictions
        write_jsonl(ds_out / f"predictions_{split}.jsonl", predictions)
        append_event(events_path, "eval_complete", dataset=dataset, split=split, metrics=evaluation["metrics"])

    majority = majority_baseline(
        x_train,
        y_train,
        [text_fn(row) for row in split_rows["test"]],
        [label_fn(row) for row in split_rows["test"]],
    )
    summary = {
        "dataset": dataset,
        "target": spec["target"],
        "why": spec["why"],
        "model": "tfidf_char_ngrams_logistic_regression"
        if len(set(y_train)) > 1
        else "tfidf_char_ngrams_dummy_most_frequent",
        "rows": {split: len(rows) for split, rows in split_rows.items()},
        "labels": labels,
        "train_distribution": dict(Counter(y_train)),
        "metrics": evaluations,
        "majority_baseline": majority,
        "artifacts": {
            "model": str(ds_out / "model.joblib"),
            "metrics": str(ds_out / "metrics.json"),
            "predictions": {split: str(ds_out / f"predictions_{split}.jsonl") for split in split_rows},
        },
        "notes": [
            "CPU baseline; use this as a floor before GPU LoRA/SFT/DPO/GRPO.",
            "Feature text is built from input fields only; label fields are not included as model features.",
        ],
    }
    write_json(ds_out / "metrics.json", summary)
    return summary


def build_readme(out_dir: Path, run_summary: dict[str, Any]) -> None:
    lines = [
        "# KIWI Specialist CPU Baselines",
        "",
        "These are lightweight baseline classifiers for narrow KIWI specialists.",
        "They are not final post-training models; they are the measurable floor before GPU fine-tuning.",
        "",
        "## Run",
        "",
        f"- run id: `{run_summary['run_id']}`",
        f"- created at: `{run_summary['created_at']}`",
        f"- source data: `{run_summary['source_data_dir']}`",
        "",
        "## Results",
        "",
        "| Dataset | Target | Train | Dev | Test | Test acc | Test macro F1 | Majority acc |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dataset, result in run_summary["datasets"].items():
        test_metrics = result["metrics"]["test"]["metrics"]
        lines.append(
            f"| {dataset} | {result['target']} | {result['rows']['train']} | {result['rows']['dev']} | "
            f"{result['rows']['test']} | {test_metrics['accuracy']} | {test_metrics['macro_f1']} | "
            f"{result['majority_baseline']['accuracy']} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `config.json`: exact run configuration.",
            "- `checkpoint.json`: resumability/status record.",
            "- `events.jsonl`: chronological training log.",
            "- `manifest.json`: environment and git state.",
            "- `<dataset>/model.joblib`: trained sklearn baseline.",
            "- `<dataset>/metrics.json`: metrics and confusion matrix.",
            "- `<dataset>/predictions_*.jsonl`: row-level predictions for error analysis.",
            "",
            "## How To Re-run",
            "",
            "```bash",
            "python3 training-corpus/scripts/train_specialist_baselines.py",
            "```",
            "",
            "For a stable output directory on a server:",
            "",
            "```bash",
            "python3 training-corpus/scripts/train_specialist_baselines.py \\",
            "  --run-id specialist_cpu_baselines_server_test \\",
            "  --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines",
            "```",
            "",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    parser.add_argument("--data-dir", type=Path, default=None, help="Directory containing datasets/<name>/{train,dev,test}.jsonl")
    parser.add_argument("--out-root", type=Path, default=None, help="Directory under which run artifacts are written")
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--datasets",
        default="router_classifier,risk_reviewer,citation_verifier",
        help=f"Comma-separated subset: {','.join(DATASETS)}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = (args.data_dir or (args.golden_dir / "datasets")).resolve()
    out_root = (args.out_root or (args.golden_dir / "baselines")).resolve()
    run_id = args.run_id or f"specialist_cpu_baselines_{timestamp_id()}"
    out_dir = out_root / run_id
    logs_dir = out_dir / "logs"
    events_path = logs_dir / "events.jsonl"
    checkpoint_path = logs_dir / "checkpoint.json"

    selected = [item.strip() for item in args.datasets.split(",") if item.strip()]
    unknown = [item for item in selected if item not in DATASETS]
    if unknown:
        raise SystemExit(f"Unknown datasets: {unknown}. Known: {sorted(DATASETS)}")

    config = {
        "run_id": run_id,
        "created_at": now_utc(),
        "source_data_dir": str(data_dir),
        "out_dir": str(out_dir),
        "datasets": selected,
        "model_family": "sklearn_tfidf_logistic_regression",
        "boundary": "CPU baseline only; not a production post-training model.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "config.json", config)
    write_json(
        out_dir / "manifest.json",
        {
            **config,
            "python": sys.version,
            "platform": platform.platform(),
            "sklearn_version": sklearn.__version__,
            "command": " ".join(sys.argv),
            "cwd": os.getcwd(),
            "git": git_state(),
        },
    )
    write_json(checkpoint_path, {"ts": now_utc(), "status": "running", "run_id": run_id, "completed": [], "pending": selected})
    append_event(events_path, "run_start", run_id=run_id, selected=selected)

    results: dict[str, Any] = {}
    completed: list[str] = []
    try:
        for dataset in selected:
            write_json(
                checkpoint_path,
                {"ts": now_utc(), "status": "running", "run_id": run_id, "current": dataset, "completed": completed},
            )
            append_event(events_path, "dataset_start", dataset=dataset)
            results[dataset] = train_one(dataset, data_dir, out_dir, events_path)
            completed.append(dataset)
            append_event(events_path, "dataset_complete", dataset=dataset)
    except Exception as exc:
        append_event(events_path, "run_error", error=repr(exc), completed=completed)
        write_json(
            checkpoint_path,
            {
                "ts": now_utc(),
                "status": "failed",
                "run_id": run_id,
                "completed": completed,
                "error": repr(exc),
            },
        )
        raise

    run_summary = {**config, "completed_at": now_utc(), "datasets": results}
    write_json(out_dir / "metrics.json", run_summary)
    build_readme(out_dir, run_summary)
    write_json(checkpoint_path, {"ts": now_utc(), "status": "complete", "run_id": run_id, "completed": completed})
    append_event(events_path, "run_complete", run_id=run_id, completed=completed)
    print(json.dumps({"run_id": run_id, "out_dir": str(out_dir), "datasets": list(results)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
