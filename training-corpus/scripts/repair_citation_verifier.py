#!/usr/bin/env python3
"""Build a citation verifier repair pack from row-level baseline errors.

This script does not overwrite the golden data. It creates a repair artifact
with:

- test-set error taxonomy,
- row-level audit file,
- probe metrics for possible feature/schema repairs,
- repaired dataset variants for follow-up baselines.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
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
DEFAULT_BASELINE_RUN = "specialist_cpu_first_training_20260630T030852Z"
SUPPORTIVE_TYPES = {"supports", "partial_support"}


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


def git_value(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def source_domain(url: Any) -> str:
    parsed = urlparse(str(url or ""))
    return parsed.netloc.lower().removeprefix("www.")


def support_type(row: dict[str, Any]) -> str:
    label = row.get("label") or row.get("output") or {}
    return str(label.get("support_type") or label.get("original_support_type") or "")


def support_binary(row: dict[str, Any]) -> str:
    return "some_support" if support_type(row) in SUPPORTIVE_TYPES else "no_support"


def text_base(row: dict[str, Any]) -> str:
    inp = row.get("input") or {}
    return "\n".join(
        [
            f"claim: {inp.get('claim', '')}",
            f"evidence_span: {inp.get('evidence_span', '')}",
            f"source_class: {inp.get('source_class', '')}",
        ]
    )


def text_url(row: dict[str, Any]) -> str:
    inp = row.get("input") or {}
    source_url = inp.get("source_url")
    return "\n".join(
        [
            text_base(row),
            f"source_domain: {source_domain(source_url)}",
            f"source_url: {source_url or ''}",
        ]
    )


def text_url_trace(row: dict[str, Any]) -> str:
    provenance = row.get("provenance") or {}
    return "\n".join([text_url(row), f"trace_id: {provenance.get('trace_id', '')}"])


def train_probe(
    rows_by_split: dict[str, list[dict[str, Any]]],
    text_fn: Callable[[dict[str, Any]], str],
    label_fn: Callable[[dict[str, Any]], str],
) -> dict[str, Any]:
    model = Pipeline(
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
            (
                "clf",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    solver="liblinear",
                    random_state=7,
                ),
            ),
        ]
    )
    train_rows = rows_by_split["train"]
    model.fit([text_fn(row) for row in train_rows], [label_fn(row) for row in train_rows])
    labels = sorted({label_fn(row) for rows in rows_by_split.values() for row in rows})
    metrics: dict[str, Any] = {}
    for split, rows in rows_by_split.items():
        y_true = [label_fn(row) for row in rows]
        y_pred = list(model.predict([text_fn(row) for row in rows]))
        metrics[split] = {
            "accuracy": round(accuracy_score(y_true, y_pred), 4),
            "macro_f1": round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4),
            "label_distribution": dict(Counter(y_true)),
            "prediction_distribution": dict(Counter(map(str, y_pred))),
            "confusion_matrix": {
                "labels": labels,
                "rows": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
            },
        }
    return metrics


def classify_error(row: dict[str, Any], prediction: dict[str, Any]) -> list[str]:
    if prediction.get("correct"):
        return ["correct"]
    expected = str(prediction.get("expected_label"))
    predicted = str(prediction.get("predicted_label"))
    inp = row.get("input") or {}
    label = row.get("label") or {}
    claim = str(inp.get("claim") or "").lower()
    rationale = str(label.get("supports_claim_part") or "").lower()
    source_class = str(inp.get("source_class") or "")
    failure_types: list[str] = []

    if {expected, predicted} <= {"supports", "partial_support", "not_supported"}:
        failure_types.append("support_boundary_confusion")
    if expected == "supports" and predicted == "not_supported":
        failure_types.append("positive_support_missed")
    if expected == "not_supported" and predicted in SUPPORTIVE_TYPES:
        failure_types.append("hard_negative_overaccepted")
    if expected == "partial_support" or "partial" in rationale or "but" in rationale:
        failure_types.append("partial_support_boundary")
    if expected in {"insufficient", "contradicts"} or predicted in {"insufficient", "contradicts"}:
        failure_types.append("rare_negative_class_boundary")
    if source_class in {"primary_official", "regulatory_warning", "institutional_research"} and expected in SUPPORTIVE_TYPES:
        if predicted in {"not_supported", "contradicts", "insufficient"}:
            failure_types.append("source_quality_feature_missing")
    if any(token in claim for token in [" and ", ";", ",", "basket", "cycle", "many ", "also "]):
        failure_types.append("composite_claim")
    return sorted(set(failure_types)) or ["unclassified_error"]


def repair_action(failure_types: list[str]) -> str:
    if "partial_support_boundary" in failure_types:
        return "Split binary any-support detection from later full-vs-partial support typing."
    if "source_quality_feature_missing" in failure_types:
        return "Expose source URL/domain as a source-quality feature; do not expose trace_id."
    if "hard_negative_overaccepted" in failure_types:
        return "Add hard negatives with similar topical overlap but unsupported claim scope."
    if "rare_negative_class_boundary" in failure_types:
        return "Collect more contradicts/insufficient examples before trusting five-way labels."
    if "positive_support_missed" in failure_types:
        return "Add more positive official-source spans and inspect claim/evidence granularity."
    return "Manual audit required."


def build_repaired_row(row: dict[str, Any], dataset_name: str) -> dict[str, Any]:
    inp = dict(row.get("input") or {})
    inp["source_domain"] = source_domain(inp.get("source_url"))
    original_label = row.get("label") or {}
    if dataset_name == "citation_support_binary":
        label = {
            "support_binary": support_binary(row),
            "original_support_type": support_type(row),
            "support_score": original_label.get("support_score"),
            "supports_claim_part": original_label.get("supports_claim_part"),
        }
    else:
        label = dict(original_label)
    repaired = {
        **row,
        "input": inp,
        "label": label,
        "repair": {
            "dataset": dataset_name,
            "repair_id": "citation_verifier_repair_v0.1",
            "original_support_type": support_type(row),
            "why": "Feature/schema repair probe generated from citation verifier error analysis.",
        },
    }
    return repaired


def build_readme(out_dir: Path, payload: dict[str, Any]) -> None:
    taxonomy = payload["error_taxonomy"]["failure_type_counts"]
    probes = payload["probe_metrics"]
    lines = [
        "# Citation Verifier Repair v0.1",
        "",
        "This repair pack is generated from the first tracked citation verifier baseline.",
        "It does not overwrite `golden_v0.1`; it creates audit artifacts and dataset variants.",
        "",
        "## Baseline Problem",
        "",
        "- Five-way citation support classification underperformed on held-out data.",
        "- Test accuracy was `0.2581`; test macro F1 was `0.1441`.",
        "- The majority baseline test accuracy was `0.4839`.",
        "",
        "## Error Taxonomy",
        "",
    ]
    for name, count in sorted(taxonomy.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{name}`: {count}")
    lines.extend(
        [
            "",
            "## Probe Metrics",
            "",
            "| Probe | Dev acc | Dev macro F1 | Test acc | Test macro F1 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, result in probes.items():
        lines.append(
            f"| {name} | {result['dev']['accuracy']} | {result['dev']['macro_f1']} | "
            f"{result['test']['accuracy']} | {result['test']['macro_f1']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- `trace_id` is useful diagnostically but should not become a model feature because it leaks task identity.",
            "- `source_url`/domain is allowed as source context, but the normalized v0.1 probe does not solve the task.",
            "- A scratch probe that rendered missing URLs as literal `None` overstated the source-URL gain; this pack normalizes missing URLs to empty strings.",
            "- Binary any-support detection is easier to explain as stage 1, but still does not solve the data problem alone.",
            "- Next repair should add hard negatives and more clean positive/partial/insufficient spans.",
            "",
            "## Artifacts",
            "",
            "- `error_taxonomy.json`",
            "- `error_taxonomy.md`",
            "- `test_error_audit.jsonl`",
            "- `probe_metrics.json`",
            "- `repaired_datasets/citation_verifier_url/`",
            "- `repaired_datasets/citation_support_binary/`",
            "",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    parser.add_argument("--baseline-run", default=DEFAULT_BASELINE_RUN)
    parser.add_argument("--repair-id", default="citation_verifier_repair_v0.1")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    golden_dir = args.golden_dir.resolve()
    data_dir = golden_dir / "datasets" / "citation_verifier"
    baseline_dir = golden_dir / "baselines" / args.baseline_run / "citation_verifier"
    out_dir = golden_dir / "repairs" / args.repair_id
    rows_by_split = {split: read_jsonl(data_dir / f"{split}.jsonl") for split in ["train", "dev", "test"]}
    test_predictions = read_jsonl(baseline_dir / "predictions_test.jsonl")
    test_rows_by_id = {row["sample_id"]: row for row in rows_by_split["test"]}

    audit_rows: list[dict[str, Any]] = []
    failure_type_counts: Counter[str] = Counter()
    confusion_counts: Counter[str] = Counter()
    for prediction in test_predictions:
        sample_id = prediction["sample_id"]
        row = test_rows_by_id[sample_id]
        failure_types = classify_error(row, prediction)
        if failure_types != ["correct"]:
            failure_type_counts.update(failure_types)
            confusion_counts[f"{prediction['expected_label']}->{prediction['predicted_label']}"] += 1
        audit_rows.append(
            {
                "sample_id": sample_id,
                "correct": prediction["correct"],
                "expected_label": prediction["expected_label"],
                "predicted_label": prediction["predicted_label"],
                "failure_types": failure_types,
                "repair_action": repair_action(failure_types),
                "claim": row["input"].get("claim"),
                "evidence_span": row["input"].get("evidence_span"),
                "source_class": row["input"].get("source_class"),
                "source_url": row["input"].get("source_url"),
                "source_domain": source_domain(row["input"].get("source_url")),
                "support_score": row["label"].get("support_score"),
                "supports_claim_part": row["label"].get("supports_claim_part"),
                "provenance": row.get("provenance"),
            }
        )

    probe_metrics = {
        "5way_base": train_probe(rows_by_split, text_base, support_type),
        "5way_source_url": train_probe(rows_by_split, text_url, support_type),
        "5way_url_plus_trace_leakage_probe": train_probe(rows_by_split, text_url_trace, support_type),
        "binary_base": train_probe(rows_by_split, text_base, support_binary),
        "binary_source_url": train_probe(rows_by_split, text_url, support_binary),
        "binary_url_plus_trace_leakage_probe": train_probe(rows_by_split, text_url_trace, support_binary),
    }
    taxonomy = {
        "generated_at": now_utc(),
        "repair_id": args.repair_id,
        "baseline_run": args.baseline_run,
        "baseline_prediction_file": str(baseline_dir / "predictions_test.jsonl"),
        "test_rows": len(test_predictions),
        "test_errors": sum(1 for row in test_predictions if not row["correct"]),
        "confusion_counts": dict(confusion_counts),
        "failure_type_counts": dict(failure_type_counts),
        "decision": {
            "use_trace_id_as_model_feature": False,
            "why_not_trace_id": "It improves probe metrics by leaking task identity and should remain diagnostic-only.",
            "use_source_url_or_domain_as_model_feature": True,
            "why_source_url": "Source identity is available at verification time and can encode source quality/context.",
            "source_url_probe_result": "After missing source URLs are normalized to an empty string, source URL/domain does not solve the five-way task.",
            "ad_hoc_probe_artifact": "An earlier scratch probe rendered missing source_url as the literal token 'None', which overstated source_url gains.",
            "use_binary_stage": True,
            "why_binary_stage": "Any-support detection is a clearer first-stage verifier than five-way support typing.",
        },
    }

    for dataset_name in ["citation_verifier_url", "citation_support_binary"]:
        for split, rows in rows_by_split.items():
            repaired_rows = [build_repaired_row(row, dataset_name) for row in rows]
            write_jsonl(out_dir / "repaired_datasets" / dataset_name / f"{split}.jsonl", repaired_rows)
        all_rows = [
            build_repaired_row(row, dataset_name)
            for split in ["train", "dev", "test"]
            for row in rows_by_split[split]
        ]
        write_jsonl(out_dir / "repaired_datasets" / dataset_name / "all.jsonl", all_rows)

    payload = {
        "repair_id": args.repair_id,
        "generated_at": now_utc(),
        "golden_dir": str(golden_dir),
        "baseline_run": args.baseline_run,
        "python": sys.version,
        "platform": platform.platform(),
        "sklearn_version": sklearn.__version__,
        "git": {
            "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
            "commit": git_value(["rev-parse", "HEAD"]),
            "status_short": git_value(["status", "--short"]) or "",
        },
        "error_taxonomy": taxonomy,
        "probe_metrics": probe_metrics,
        "repaired_datasets": {
            "citation_verifier_url": str(out_dir / "repaired_datasets" / "citation_verifier_url"),
            "citation_support_binary": str(out_dir / "repaired_datasets" / "citation_support_binary"),
        },
    }
    write_json(out_dir / "manifest.json", payload)
    write_json(out_dir / "error_taxonomy.json", taxonomy)
    write_json(out_dir / "probe_metrics.json", probe_metrics)
    write_jsonl(out_dir / "test_error_audit.jsonl", audit_rows)
    taxonomy_md = [
        "# Citation Verifier Error Taxonomy",
        "",
        f"- repair id: `{args.repair_id}`",
        f"- baseline run: `{args.baseline_run}`",
        f"- test rows: `{taxonomy['test_rows']}`",
        f"- test errors: `{taxonomy['test_errors']}`",
        "",
        "## Failure Types",
        "",
    ]
    for name, count in sorted(failure_type_counts.items(), key=lambda item: (-item[1], item[0])):
        taxonomy_md.append(f"- `{name}`: {count}")
    taxonomy_md.extend(["", "## Confusions", ""])
    for name, count in sorted(confusion_counts.items(), key=lambda item: (-item[1], item[0])):
        taxonomy_md.append(f"- `{name}`: {count}")
    (out_dir / "error_taxonomy.md").write_text("\n".join(taxonomy_md) + "\n", encoding="utf-8")
    build_readme(out_dir, payload)
    print(json.dumps({"repair_id": args.repair_id, "out_dir": str(out_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
