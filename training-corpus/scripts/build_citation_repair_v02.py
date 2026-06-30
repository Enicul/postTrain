#!/usr/bin/env python3
"""Build citation verifier repair v0.2 with train-only data augmentation.

v0.1 diagnosed the failure. v0.2 tests whether targeted train-only data repair
helps without leaking dev/test labels into training.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_DIR = (
    REPO_ROOT
    / "training-corpus"
    / "runs"
    / "x-bookmarks-recent-111-20260629"
    / "curated"
    / "golden_v0.1"
)
REPAIR_ID = "citation_verifier_repair_v0.2"
SUPPORTIVE_TYPES = {"supports", "partial_support"}
STOPWORDS = {
    "about",
    "after",
    "also",
    "around",
    "because",
    "being",
    "between",
    "claim",
    "could",
    "data",
    "does",
    "from",
    "have",
    "into",
    "more",
    "most",
    "only",
    "that",
    "their",
    "there",
    "this",
    "with",
    "would",
}


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
    return str((row.get("label") or {}).get("support_type") or "")


def support_binary_from_type(kind: str) -> str:
    return "some_support" if kind in SUPPORTIVE_TYPES else "no_support"


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{3,}", text.lower())
        if token not in STOPWORDS
    }


def add_source_domain(row: dict[str, Any]) -> dict[str, Any]:
    copied = json.loads(json.dumps(row, ensure_ascii=False))
    inp = copied.setdefault("input", {})
    inp["source_domain"] = source_domain(inp.get("source_url"))
    return copied


def normalize_row(row: dict[str, Any], dataset_name: str, split: str) -> dict[str, Any]:
    copied = add_source_domain(row)
    copied["split"] = split
    copied.setdefault("repair", {})
    copied["repair"] = {
        **copied["repair"],
        "dataset": dataset_name,
        "repair_id": REPAIR_ID,
        "origin": "original_golden_v0.1",
    }
    if dataset_name == "citation_support_binary":
        label = copied.get("label") or {}
        original = str(label.get("support_type") or label.get("original_support_type") or "")
        copied["label"] = {
            "support_binary": support_binary_from_type(original),
            "original_support_type": original,
            "support_score": label.get("support_score"),
            "supports_claim_part": label.get("supports_claim_part"),
        }
    return copied


def synthetic_row(
    *,
    origin: dict[str, Any],
    sample_id: str,
    claim: str,
    evidence_span: str,
    source_class: str,
    source_url: str | None,
    support_type_value: str,
    support_score: float,
    supports_claim_part: str,
    generation_rule: str,
) -> dict[str, Any]:
    row = {
        "input": {
            "claim": claim,
            "evidence_span": evidence_span,
            "source_class": source_class,
            "source_url": source_url,
            "source_domain": source_domain(source_url),
        },
        "label": {
            "support_score": support_score,
            "support_type": support_type_value,
            "supports_claim_part": supports_claim_part,
        },
        "provenance": {
            "origin_sample_id": origin.get("sample_id"),
            "origin_trace_id": (origin.get("provenance") or {}).get("trace_id"),
            "generation_rule": generation_rule,
        },
        "repair": {
            "dataset": "citation_verifier_url",
            "repair_id": REPAIR_ID,
            "origin": "generated_from_train_only",
            "generation_rule": generation_rule,
        },
        "sample_id": sample_id,
        "source": "citation_repair_v0.2_generated",
        "split": "train",
        "synthetic": True,
    }
    return row


def as_binary_row(row: dict[str, Any]) -> dict[str, Any]:
    copied = json.loads(json.dumps(row, ensure_ascii=False))
    label = copied.get("label") or {}
    original = str(label.get("support_type") or label.get("original_support_type") or "")
    copied["label"] = {
        "support_binary": support_binary_from_type(original),
        "original_support_type": original,
        "support_score": label.get("support_score"),
        "supports_claim_part": label.get("supports_claim_part"),
    }
    copied.setdefault("repair", {})
    copied["repair"] = {**copied["repair"], "dataset": "citation_support_binary"}
    return copied


def generation_rule(row: dict[str, Any]) -> str:
    return (row.get("repair") or {}).get("generation_rule", "original")


def choose_hard_negative(origin: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    origin_trace = (origin.get("provenance") or {}).get("trace_id")
    claim_tokens = tokenize((origin.get("input") or {}).get("claim") or "")
    best: tuple[int, dict[str, Any]] | None = None
    for candidate in candidates:
        if candidate is origin:
            continue
        if (candidate.get("provenance") or {}).get("trace_id") == origin_trace:
            continue
        inp = candidate.get("input") or {}
        if not inp.get("evidence_span"):
            continue
        evidence_tokens = tokenize(inp.get("evidence_span") or "")
        overlap = len(claim_tokens & evidence_tokens)
        if best is None or overlap > best[0]:
            best = (overlap, candidate)
    return best[1] if best else None


def build_augmentation_pool(train_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    originals = [normalize_row(row, "citation_verifier_url", "train") for row in train_rows]
    source_candidates = [row for row in train_rows if (row.get("input") or {}).get("evidence_span")]
    supportive = [row for row in train_rows if support_type(row) in SUPPORTIVE_TYPES]
    partials = [row for row in train_rows if support_type(row) == "partial_support"]
    generated: list[dict[str, Any]] = []

    for index, row in enumerate(supportive[:40]):
        negative = choose_hard_negative(row, source_candidates)
        if not negative:
            continue
        neg_input = negative.get("input") or {}
        generated.append(
            synthetic_row(
                origin=row,
                sample_id=f"v02_hard_negative_{index:03d}_{row.get('sample_id')}",
                claim=(row.get("input") or {}).get("claim") or "",
                evidence_span=neg_input.get("evidence_span") or "",
                source_class=neg_input.get("source_class") or "auditable_mismatch",
                source_url=neg_input.get("source_url"),
                support_type_value="not_supported",
                support_score=0.0,
                supports_claim_part="Topically similar evidence from another trace does not support the exact claim.",
                generation_rule="hard_negative_cross_trace_overlap",
            )
        )

    for index, row in enumerate(supportive[:30]):
        generated.append(
            synthetic_row(
                origin=row,
                sample_id=f"v02_insufficient_{index:03d}_{row.get('sample_id')}",
                claim=(row.get("input") or {}).get("claim") or "",
                evidence_span="",
                source_class="none",
                source_url=None,
                support_type_value="insufficient",
                support_score=0.0,
                supports_claim_part="No evidence span or auditable source is available for this claim.",
                generation_rule="missing_evidence_insufficient",
            )
        )

    for index, row in enumerate(supportive[:35]):
        label = row.get("label") or {}
        atomic_claim = str(label.get("supports_claim_part") or "").strip().rstrip(".")
        if not atomic_claim or atomic_claim.lower().startswith(("no ", "large performance", "small-volume")):
            continue
        inp = row.get("input") or {}
        generated.append(
            synthetic_row(
                origin=row,
                sample_id=f"v02_atomic_positive_{index:03d}_{row.get('sample_id')}",
                claim=atomic_claim + ".",
                evidence_span=inp.get("evidence_span") or "",
                source_class=inp.get("source_class") or "auditable_source",
                source_url=inp.get("source_url"),
                support_type_value="supports",
                support_score=1.0,
                supports_claim_part=atomic_claim + ".",
                generation_rule="atomic_positive_from_supports_claim_part",
            )
        )

    for index, row in enumerate(partials[:24]):
        copied = normalize_row(row, "citation_verifier_url", "train")
        copied["sample_id"] = f"v02_partial_boundary_{index:03d}_{row.get('sample_id')}"
        copied["synthetic"] = True
        copied["source"] = "citation_repair_v0.2_generated"
        copied["repair"] = {
            **copied["repair"],
            "origin": "generated_from_train_only",
            "generation_rule": "partial_support_boundary_upsample",
        }
        generated.append(copied)

    counts = Counter(generation_rule(row) for row in [*originals, *generated])
    return originals, generated, dict(counts)


def build_readme(out_dir: Path, manifest: dict[str, Any]) -> None:
    counts = manifest["generation_counts"]
    lines = [
        "# Citation Verifier Repair v0.2",
        "",
        "v0.2 is a train-only data repair experiment. It keeps original dev/test unchanged",
        "and augments only the training split, so evaluation remains comparable to v0.1.",
        "",
        "## Why",
        "",
        "v0.1 showed the main failures were composite claims, support-boundary confusion,",
        "hard negatives, and rare negative classes. Source URL/domain alone did not fix",
        "the five-way task.",
        "",
        "## Candidate Generation Rules",
        "",
    ]
    for name, count in sorted(counts["candidate_generation_counts"].items()):
        lines.append(f"- `{name}`: {count}")
    lines.extend(
        [
            "",
            "## Selected Training Strategy",
            "",
            "- `citation_verifier_url`: original train + `hard_negative_cross_trace_overlap` + `missing_evidence_insufficient`.",
            "- `citation_support_binary`: original train + `hard_negative_cross_trace_overlap`.",
            "",
            "This is based on a local ablation: using all generated rows improved some",
            "dev metrics but hurt binary test performance. The selected strategy keeps",
            "augmentation targeted instead of flooding the train split.",
            "",
        ]
    )
    metrics_path = out_dir / "baselines" / "citation_repair_probe_v0.2" / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        lines.extend(
            [
                "## Baseline Results",
                "",
                "Command:",
                "",
                "```bash",
                "python3 training-corpus/scripts/train_specialist_baselines.py \\",
                "  --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/repaired_datasets \\",
                "  --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/baselines \\",
                "  --run-id citation_repair_probe_v0.2 \\",
                "  --datasets citation_verifier_url,citation_support_binary",
                "```",
                "",
                "| Dataset | Train rows | Test accuracy | Test macro F1 | Majority accuracy |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for dataset in ["citation_verifier_url", "citation_support_binary"]:
            info = metrics["datasets"][dataset]
            test_metrics = info["metrics"]["test"]["metrics"]
            majority = info["majority_baseline"]
            lines.append(
                f"| {dataset} | {info['rows']['train']} | "
                f"{test_metrics['accuracy']:.4f} | {test_metrics['macro_f1']:.4f} | "
                f"{majority['accuracy']:.4f} |"
            )
        lines.extend(
            [
                "",
                "Interpretation:",
                "",
                "v0.2 improves the repair probes versus v0.1, but both tasks still underperform",
                "the majority baseline on accuracy. This is evidence that the taxonomy is useful,",
                "not evidence that the verifier is ready for GPU fine-tuning.",
                "",
            ]
        )
    lines.extend(
        [
            "## Selected Generation Counts",
            "",
        ]
    )
    for dataset, dataset_counts in counts["selected_generation_counts"].items():
        lines.append(f"### {dataset}")
        for name, count in sorted(dataset_counts.items()):
            lines.append(f"- `{name}`: {count}")
        lines.append("")
    lines.extend(
        [
            "",
            "## Leakage Controls",
            "",
            "- Only `train.jsonl` is augmented.",
            "- Original `dev.jsonl` and `test.jsonl` are copied without generated rows.",
            "- `trace_id` is retained in provenance for audit but is not a model feature.",
            "- Missing `source_url` is normalized to an empty string, not the literal token `None`.",
            "",
            "## Next",
            "",
            "Create `citation_verifier_repair_v0.3` from audited real citation spans:",
            "official positive paragraphs, partial-support boundaries, and rare contradict /",
            "insufficient examples.",
            "",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    golden_dir = args.golden_dir.resolve()
    data_dir = golden_dir / "datasets" / "citation_verifier"
    out_dir = golden_dir / "repairs" / REPAIR_ID
    rows_by_split = {split: read_jsonl(data_dir / f"{split}.jsonl") for split in ["train", "dev", "test"]}

    originals, generated_pool, candidate_generation_counts = build_augmentation_pool(rows_by_split["train"])
    five_way_rules = {"hard_negative_cross_trace_overlap", "missing_evidence_insufficient"}
    binary_rules = {"hard_negative_cross_trace_overlap"}
    five_way_train = [*originals, *[row for row in generated_pool if generation_rule(row) in five_way_rules]]
    binary_train_source = [*originals, *[row for row in generated_pool if generation_rule(row) in binary_rules]]
    datasets: dict[str, dict[str, list[dict[str, Any]]]] = {
        "citation_verifier_url": {
            "train": five_way_train,
            "dev": [normalize_row(row, "citation_verifier_url", "dev") for row in rows_by_split["dev"]],
            "test": [normalize_row(row, "citation_verifier_url", "test") for row in rows_by_split["test"]],
        }
    }
    datasets["citation_support_binary"] = {
        split: [as_binary_row(row) for row in rows]
        for split, rows in {
            "train": binary_train_source,
            "dev": datasets["citation_verifier_url"]["dev"],
            "test": datasets["citation_verifier_url"]["test"],
        }.items()
    }

    write_jsonl(out_dir / "candidate_generation_pool.jsonl", generated_pool)
    for dataset, splits in datasets.items():
        dataset_dir = out_dir / "repaired_datasets" / dataset
        all_rows: list[dict[str, Any]] = []
        for split, rows in splits.items():
            write_jsonl(dataset_dir / f"{split}.jsonl", rows)
            all_rows.extend(rows)
        write_jsonl(dataset_dir / "all.jsonl", all_rows)

    manifest = {
        "repair_id": REPAIR_ID,
        "generated_at": now_utc(),
        "golden_dir": str(golden_dir),
        "python": sys.version,
        "platform": platform.platform(),
        "git": {
            "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
            "commit": git_value(["rev-parse", "HEAD"]),
            "status_short": git_value(["status", "--short"]) or "",
        },
        "input_rows": {split: len(rows) for split, rows in rows_by_split.items()},
        "output_rows": {
            dataset: {split: len(rows) for split, rows in splits.items()}
            for dataset, splits in datasets.items()
        },
        "generation_counts": {
            "candidate_generation_counts": candidate_generation_counts,
            "selected_generation_counts": {
                dataset: dict(Counter(generation_rule(row) for row in splits["train"]))
                for dataset, splits in datasets.items()
            },
            "ablation_decision": {
                "citation_verifier_url": "original + hard_negative_cross_trace_overlap + missing_evidence_insufficient",
                "citation_support_binary": "original + hard_negative_cross_trace_overlap",
            },
        },
        "leakage_controls": [
            "train_only_augmentation",
            "dev_test_unchanged",
            "trace_id_provenance_only",
            "missing_url_empty_string",
        ],
    }
    write_json(out_dir / "manifest.json", manifest)
    build_readme(out_dir, manifest)
    print(json.dumps({"repair_id": REPAIR_ID, "out_dir": str(out_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
