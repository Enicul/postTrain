#!/usr/bin/env python3
"""Collect real paragraph-level citation spans under citation_contract_repair_v0.1.

This is deliberately a small, auditable collection pass. It fetches real
official/IR/SEC pages, extracts selected paragraph/list/table-cell spans, then
labels exact claim-support boundaries. It does not store raw HTML.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import platform
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


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
COLLECTION_ID = "real_citation_spans_v0.1"
DEFAULT_OUT_DIR = BASE_REPAIR_DIR / COLLECTION_ID
USER_AGENT = "KiwiPostTrainingResearch/0.1 (+https://github.com/Enicul/postTrain)"


@dataclass(frozen=True)
class SourceSpec:
    source_key: str
    ticker: str
    source_url: str
    evidence_title: str
    source_class: str
    published_at: str
    as_of: str
    fallback_note: str | None = None


@dataclass(frozen=True)
class SpanCase:
    case_key: str
    source_key: str
    anchor: str
    claim: str
    support_type: str
    claim_scope: str
    rationale: str
    point_in_time_allowed: bool = True
    split: str | None = None


SOURCES: dict[str, SourceSpec] = {
    "amd_q1_2026_press": SourceSpec(
        source_key="amd_q1_2026_press",
        ticker="AMD",
        source_url="https://ir.amd.com/news-events/press-releases/detail/1284/amd-reports-first-quarter-2026-financial-results",
        evidence_title="AMD Reports First Quarter 2026 Financial Results",
        source_class="press_release",
        published_at="2026-05-05",
        as_of="2026-05-06",
    ),
    "amd_q1_2026_8k": SourceSpec(
        source_key="amd_q1_2026_8k",
        ticker="AMD",
        source_url="https://ir.amd.com/financial-information/sec-filings/content/0000002488-26-000072/amd-20260505.htm",
        evidence_title="AMD Form 8-K filed May 5 2026",
        source_class="sec_filing",
        published_at="2026-05-05",
        as_of="2026-05-06",
    ),
    "msft_fy26_q3_press": SourceSpec(
        source_key="msft_fy26_q3_press",
        ticker="MSFT",
        source_url="https://www.microsoft.com/en-us/investor/earnings/fy-2026-q3/press-release-webcast",
        evidence_title="Microsoft FY26 Q3 Press Release and Webcast",
        source_class="press_release",
        published_at="2026-04-29",
        as_of="2026-04-30",
    ),
    "mu_fq3_2026_press": SourceSpec(
        source_key="mu_fq3_2026_press",
        ticker="MU",
        source_url="https://www.globenewswire.com/news-release/2026/06/24/3317151/14450/en/micron-technology-inc-reports-record-results-for-the-third-quarter-of-fiscal-2026.html",
        evidence_title="Micron Reports Record Results for Fiscal Q3 2026",
        source_class="press_release_wire",
        published_at="2026-06-25",
        as_of="2026-06-26",
        fallback_note="Micron IR page repeatedly timed out during scripted collection; used the issuer press-release mirror on GlobeNewswire.",
    ),
    "nvda_fq1_2027_news": SourceSpec(
        source_key="nvda_fq1_2027_news",
        ticker="NVDA",
        source_url="https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2027",
        evidence_title="NVIDIA Announces Financial Results for First Quarter Fiscal 2027",
        source_class="official_news",
        published_at="2026-05-27",
        as_of="2026-05-28",
        fallback_note="Used NVIDIA News Center because the investor.nvidia.com page returned Cloudflare 403 during collection.",
    ),
}


CASES: list[SpanCase] = [
    SpanCase(
        "amd_overview_verified",
        "amd_q1_2026_press",
        "First quarter revenue was $10.3 billion",
        "AMD reported first-quarter 2026 revenue of $10.3 billion.",
        "verified_support",
        "single_fact",
        "The paragraph directly states the first-quarter 2026 revenue figure.",
        split="train",
    ),
    SpanCase(
        "amd_overview_partial",
        "amd_q1_2026_press",
        "First quarter revenue was $10.3 billion",
        "AMD reported first-quarter revenue of $10.3 billion and said Data Center revenue rose 57% year over year.",
        "partial_support",
        "composite",
        "The span supports the company-level revenue figure but not the Data Center segment growth.",
        split="dev",
    ),
    SpanCase(
        "amd_overview_contradicts",
        "amd_q1_2026_press",
        "First quarter revenue was $10.3 billion",
        "AMD reported first-quarter 2026 revenue of $8.0 billion.",
        "contradicts",
        "single_fact",
        "The span gives a different revenue figure than the claim.",
        split="test",
    ),
    SpanCase(
        "amd_dc_verified",
        "amd_q1_2026_press",
        "Data Center segment revenue was $5.8 billion",
        "AMD Data Center segment revenue was $5.8 billion and grew 57% year over year.",
        "verified_support",
        "single_fact",
        "The span directly states both the segment revenue and year-over-year growth.",
        split="train",
    ),
    SpanCase(
        "amd_dc_insufficient",
        "amd_q1_2026_press",
        "Data Center segment revenue was $5.8 billion",
        "AMD guided second-quarter 2026 revenue to approximately $11.2 billion.",
        "insufficient",
        "forward_looking",
        "The span is about Data Center segment results, not second-quarter guidance.",
        split="train",
    ),
    SpanCase(
        "amd_guidance_verified",
        "amd_q1_2026_press",
        "For the second quarter of 2026, AMD expects revenue to be approximately $11.2 billion",
        "AMD expected second-quarter 2026 revenue to be approximately $11.2 billion, plus or minus $300 million.",
        "verified_support",
        "forward_looking",
        "The span directly states the Q2 2026 revenue outlook and range.",
        split="train",
    ),
    SpanCase(
        "amd_guidance_partial",
        "amd_q1_2026_press",
        "For the second quarter of 2026, AMD expects revenue to be approximately $11.2 billion",
        "AMD expected second-quarter 2026 revenue to be about $11.2 billion and non-GAAP gross margin to be 58%.",
        "partial_support",
        "composite",
        "The span supports the revenue guidance but states a different gross-margin expectation.",
        split="dev",
    ),
    SpanCase(
        "amd_8k_verified",
        "amd_q1_2026_8k",
        "Item 2.02 Results of Operations and Financial Condition",
        "AMD's May 2026 Form 8-K included Item 2.02 for results of operations and financial condition.",
        "verified_support",
        "filing_metadata",
        "The filing span directly names Item 2.02 and its section title.",
        split="train",
    ),
    SpanCase(
        "amd_8k_insufficient",
        "amd_q1_2026_8k",
        "Item 2.02 Results of Operations and Financial Condition",
        "AMD's first-quarter 2026 Data Center segment revenue was $5.8 billion.",
        "insufficient",
        "single_fact",
        "The filing metadata span proves the item section, not the segment revenue fact.",
        split="test",
    ),
    SpanCase(
        "msft_revenue_verified",
        "msft_fy26_q3_press",
        "Revenue was $82.9 billion",
        "Microsoft FY26 Q3 revenue was $82.9 billion and increased 18%.",
        "verified_support",
        "single_fact",
        "The bullet directly states revenue and growth.",
        split="train",
    ),
    SpanCase(
        "msft_revenue_contradicts",
        "msft_fy26_q3_press",
        "Revenue was $82.9 billion",
        "Microsoft FY26 Q3 revenue declined 18%.",
        "contradicts",
        "single_fact",
        "The span says revenue increased, while the claim says it declined.",
        split="test",
    ),
    SpanCase(
        "msft_cloud_verified",
        "msft_fy26_q3_press",
        "Microsoft Cloud revenue was $54.5 billion",
        "Microsoft Cloud revenue was $54.5 billion and increased 29%.",
        "verified_support",
        "single_fact",
        "The span directly states Microsoft Cloud revenue and growth.",
        split="train",
    ),
    SpanCase(
        "msft_cloud_partial",
        "msft_fy26_q3_press",
        "Microsoft Cloud revenue was $54.5 billion",
        "Microsoft Cloud revenue was $54.5 billion and Azure revenue increased 40%.",
        "partial_support",
        "composite",
        "The span supports Microsoft Cloud revenue, but not Azure growth.",
        split="dev",
    ),
    SpanCase(
        "msft_azure_verified",
        "msft_fy26_q3_press",
        "Azure and other cloud services revenue increased 40%",
        "Azure and other cloud services revenue increased 40%.",
        "verified_support",
        "single_fact",
        "The span directly states Azure and other cloud services growth.",
        split="train",
    ),
    SpanCase(
        "msft_operating_income_verified",
        "msft_fy26_q3_press",
        "Operating income was $38.4 billion",
        "Microsoft FY26 Q3 operating income was $38.4 billion and increased 20%.",
        "verified_support",
        "single_fact",
        "The span directly states operating income and growth.",
        split="train",
    ),
    SpanCase(
        "msft_operating_income_insufficient",
        "msft_fy26_q3_press",
        "Operating income was $38.4 billion",
        "Microsoft Cloud revenue was $54.5 billion.",
        "insufficient",
        "single_fact",
        "The operating income span does not establish Microsoft Cloud revenue.",
        split="dev",
    ),
    SpanCase(
        "mu_revenue_verified",
        "mu_fq3_2026_press",
        "Revenue of $41.46 billion",
        "Micron fiscal Q3 2026 revenue was $41.46 billion.",
        "verified_support",
        "single_fact",
        "The span directly states the revenue figure.",
        split="train",
    ),
    SpanCase(
        "mu_revenue_partial",
        "mu_fq3_2026_press",
        "Revenue of $41.46 billion",
        "Micron fiscal Q3 revenue was $41.46 billion and adjusted free cash flow was $18.3 billion.",
        "partial_support",
        "composite",
        "The span supports revenue but not adjusted free cash flow.",
        split="dev",
    ),
    SpanCase(
        "mu_revenue_contradicts",
        "mu_fq3_2026_press",
        "Revenue of $41.46 billion",
        "Micron fiscal Q3 2026 revenue was $23.86 billion.",
        "contradicts",
        "single_fact",
        "The span identifies $23.86 billion as the prior quarter, not fiscal Q3 revenue.",
        split="test",
    ),
    SpanCase(
        "mu_hbm4_verified",
        "mu_fq3_2026_press",
        "HBM4, built on 1-beta DRAM technology, is in high-volume shipments",
        "Micron said HBM4 built on 1-beta DRAM technology was in high-volume shipments for its lead customer's platform.",
        "verified_support",
        "single_fact",
        "The span directly supports the HBM4 shipment claim.",
        split="train",
    ),
    SpanCase(
        "mu_hbm4_partial",
        "mu_fq3_2026_press",
        "HBM4, built on 1-beta DRAM technology, is in high-volume shipments",
        "Micron said HBM4 was in high-volume shipments and HBM4E volume production had already started.",
        "partial_support",
        "composite",
        "The span supports HBM4 shipments but says HBM4E volume production is expected later.",
        split="dev",
    ),
    SpanCase(
        "mu_cash_verified",
        "mu_fq3_2026_press",
        "cash, marketable investments, and restricted cash of $30.2 billion",
        "Micron ended the quarter with cash, marketable investments, and restricted cash of $30.2 billion.",
        "verified_support",
        "single_fact",
        "The span directly states the cash and investments figure.",
        split="train",
    ),
    SpanCase(
        "nvda_revenue_verified",
        "nvda_fq1_2027_news",
        "record revenue for the first quarter ended April 26, 2026, of $81.6 billion",
        "NVIDIA reported first-quarter fiscal 2027 revenue of $81.6 billion.",
        "verified_support",
        "single_fact",
        "The span directly states the first-quarter revenue figure.",
        split="train",
    ),
    SpanCase(
        "nvda_revenue_contradicts",
        "nvda_fq1_2027_news",
        "record revenue for the first quarter ended April 26, 2026, of $81.6 billion",
        "NVIDIA reported first-quarter fiscal 2027 revenue of $75.2 billion.",
        "contradicts",
        "single_fact",
        "The span states total revenue was $81.6 billion; $75.2 billion refers to Data Center revenue elsewhere.",
        split="test",
    ),
    SpanCase(
        "nvda_dc_verified",
        "nvda_fq1_2027_news",
        "Record Data Center revenue of $75.2 billion",
        "NVIDIA Data Center revenue was $75.2 billion, up 92% from a year ago.",
        "verified_support",
        "single_fact",
        "The span directly states Data Center revenue and growth.",
        split="train",
    ),
    SpanCase(
        "nvda_dc_partial",
        "nvda_fq1_2027_news",
        "Record Data Center revenue of $75.2 billion",
        "NVIDIA Data Center revenue was $75.2 billion and Edge Computing revenue was $6.4 billion.",
        "partial_support",
        "composite",
        "The span supports Data Center revenue but not Edge Computing revenue.",
        split="dev",
    ),
    SpanCase(
        "nvda_guidance_verified",
        "nvda_fq1_2027_news",
        "Revenue is expected to be $91.0 billion",
        "NVIDIA expected second-quarter fiscal 2027 revenue to be $91.0 billion, plus or minus 2%.",
        "verified_support",
        "forward_looking",
        "The span directly states the outlook.",
        split="train",
    ),
    SpanCase(
        "nvda_guidance_insufficient",
        "nvda_fq1_2027_news",
        "Revenue is expected to be $91.0 billion",
        "NVIDIA reported first-quarter revenue of $81.6 billion.",
        "insufficient",
        "single_fact",
        "The guidance span does not prove first-quarter reported revenue.",
        split="test",
    ),
    SpanCase(
        "nvda_reporting_framework_verified",
        "nvda_fq1_2027_news",
        "NVIDIA is transitioning to a new reporting framework",
        "NVIDIA said it was transitioning to a new reporting framework with Data Center and Edge Computing market platforms.",
        "verified_support",
        "single_fact",
        "The span directly describes the new reporting framework.",
        split="train",
    ),
]


class TextExtractor(HTMLParser):
    """Lightweight paragraph/list/table-cell extractor."""

    BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "td", "div", "span"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._tag_stack: list[str] = []
        self._parts: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.BLOCK_TAGS:
            self._tag_stack.append(tag.lower())
            self._parts = []
        elif self._tag_stack and tag.lower() == "br":
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._tag_stack:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._tag_stack and tag.lower() == self._tag_stack[-1]:
            text = normalize_space(html.unescape(" ".join(self._parts)))
            if 20 <= len(text) <= 1200:
                self.blocks.append(text)
            self._tag_stack.pop()
            self._parts = []


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def normalize_for_match(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", normalize_space(text).lower()).strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def git_value(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def fetch_source(spec: SourceSpec, timeout_seconds: int) -> tuple[list[str], dict[str, Any]]:
    started_at = now_utc()
    last_error: str | None = None
    response: requests.Response | None = None
    for attempt in range(1, 4):
        try:
            response = requests.get(
                spec.source_url,
                timeout=timeout_seconds,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            )
            response.raise_for_status()
            break
        except Exception as exc:
            last_error = repr(exc)
            if attempt < 3:
                time.sleep(attempt * 2)

    if response is None or not response.ok:
        return [], {
            "source_key": spec.source_key,
            "source_url": spec.source_url,
            "status": "fetch_failed",
            "error": last_error or "unknown fetch error",
            "started_at": started_at,
            "captured_at": now_utc(),
        }

    extractor = TextExtractor()
    extractor.feed(response.text)
    seen: set[str] = set()
    blocks: list[str] = []
    for block in extractor.blocks:
        if block not in seen:
            blocks.append(block)
            seen.add(block)

    return blocks, {
        "source_key": spec.source_key,
        "source_url": spec.source_url,
        "source_domain": source_domain(spec.source_url),
        "source_class": spec.source_class,
        "ticker": spec.ticker,
        "status": "ok",
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "raw_html_sha256": sha256_text(response.text),
        "raw_html_bytes": len(response.content),
        "extracted_block_count": len(blocks),
        "published_at": spec.published_at,
        "as_of": spec.as_of,
        "fallback_note": spec.fallback_note,
        "started_at": started_at,
        "captured_at": now_utc(),
    }


def find_span(blocks: list[str], anchor: str) -> tuple[int | None, str | None]:
    normalized_anchor = normalize_for_match(anchor)
    for index, block in enumerate(blocks):
        if normalized_anchor in normalize_for_match(block):
            return index, block
    return None, None


def build_rows(timeout_seconds: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    captured_at = now_utc()
    blocks_by_source: dict[str, list[str]] = {}
    source_audits: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for spec in SOURCES.values():
        blocks, audit = fetch_source(spec, timeout_seconds)
        blocks_by_source[spec.source_key] = blocks
        source_audits.append(audit)
        if audit["status"] != "ok":
            failures.append(audit)

    rows: list[dict[str, Any]] = []
    for index, case in enumerate(CASES):
        spec = SOURCES[case.source_key]
        block_index, span = find_span(blocks_by_source.get(case.source_key, []), case.anchor)
        if span is None:
            failures.append(
                {
                    "case_key": case.case_key,
                    "source_key": case.source_key,
                    "status": "anchor_not_found",
                    "anchor": case.anchor,
                    "source_url": spec.source_url,
                }
            )
            continue

        sample_id = f"{COLLECTION_ID}_{index:04d}_{case.case_key}"
        row = {
            "sample_id": sample_id,
            "source": COLLECTION_ID,
            "split": case.split or split_for_index(index),
            "input": {
                "claim": case.claim,
                "evidence_span": span,
                "evidence_id": f"{case.source_key}:block:{block_index}",
                "evidence_title": spec.evidence_title,
                "source_url": spec.source_url,
                "source_domain": source_domain(spec.source_url),
                "source_class": spec.source_class,
                "ticker": spec.ticker,
                "as_of": spec.as_of,
                "published_at": spec.published_at,
                "captured_at": captured_at,
                "claim_scope": case.claim_scope,
                "point_in_time_allowed": case.point_in_time_allowed,
            },
            "label": {
                "support_type": case.support_type,
                "support_score": support_score(case.support_type),
                "supports_claim_part": case.rationale,
            },
            "provenance": {
                "collection_id": COLLECTION_ID,
                "source_key": case.source_key,
                "case_key": case.case_key,
                "anchor": case.anchor,
                "paragraph_index": block_index,
                "paragraph_sha256": sha256_text(span),
                "source_raw_html_sha256": next(
                    (
                        audit.get("raw_html_sha256")
                        for audit in source_audits
                        if audit.get("source_key") == case.source_key
                    ),
                    None,
                ),
                "labeling_mode": "manual_contract_label_from_real_source_span",
                "requires_human_audit": True,
                "fallback_note": spec.fallback_note,
            },
            "repair": {
                "contract_id": "citation_contract_repair_v0.1",
                "collection_id": COLLECTION_ID,
                "origin": "real_web_source",
                "why": "Real paragraph span collected before training citation verifier repair v0.3.",
            },
        }
        rows.append(row)
    return rows, source_audits, failures


def split_for_index(index: int) -> str:
    if index % 10 in {7, 8}:
        return "dev"
    if index % 10 == 9:
        return "test"
    return "train"


def support_score(support_type: str) -> float:
    return {
        "verified_support": 1.0,
        "partial_support": 0.55,
        "candidate_evidence": 0.35,
        "insufficient": 0.0,
        "contradicts": -1.0,
    }[support_type]


def write_report(out_dir: Path, rows: list[dict[str, Any]], source_audits: list[dict[str, Any]], failures: list[dict[str, Any]]) -> None:
    label_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for row in rows:
        label = row["label"]["support_type"]
        split = row["split"]
        source_key = row["provenance"]["source_key"]
        label_counts[label] = label_counts.get(label, 0) + 1
        split_counts[split] = split_counts.get(split, 0) + 1
        source_counts[source_key] = source_counts.get(source_key, 0) + 1

    lines = [
        "# Real Citation Spans v0.1",
        "",
        "This collection adds real paragraph/list/table-cell spans under",
        "`citation_contract_repair_v0.1`. It is a small data-quality pass, not a",
        "training run.",
        "",
        "## Summary",
        "",
        f"- Rows: {len(rows)}",
        f"- Sources fetched: {sum(1 for audit in source_audits if audit.get('status') == 'ok')} / {len(source_audits)}",
        f"- Fetch or anchor failures: {len(failures)}",
        f"- Labels: `{json.dumps(label_counts, sort_keys=True)}`",
        f"- Splits: `{json.dumps(split_counts, sort_keys=True)}`",
        "",
        "## Why",
        "",
        "The previous citation data often treated topical evidence as if it were exact",
        "support. This pack forces the verifier to distinguish exact support from",
        "partial, insufficient, and contradictory spans.",
        "",
        "## Source Mix",
        "",
    ]
    for source_key, count in sorted(source_counts.items()):
        spec = SOURCES[source_key]
        lines.append(f"- `{source_key}` ({spec.source_class}, {spec.ticker}): {count} rows")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "- `spans/all.jsonl`: all collected rows.",
            "- `repaired_datasets/citation_verifier/{train,dev,test,all}.jsonl`: baseline-compatible splits.",
            "- `sources.json`: source metadata and fetch hashes.",
            "- `failures.json`: fetch/anchor failures, if any.",
            "- `manifest.json`: reproducibility metadata.",
            "",
            "## Decision",
            "",
            "Do not train `citation_verifier_repair_v0.3` from this pack alone. Use it as",
            "the first official-source span seed, then expand with more paragraph spans",
            "from filings, transcripts, IR releases, and high-quality news.",
        ]
    )
    (out_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout-seconds", type=int, default=45)
    args = parser.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, source_audits, failures = build_rows(args.timeout_seconds)

    by_split: dict[str, list[dict[str, Any]]] = {"train": [], "dev": [], "test": []}
    for row in rows:
        by_split.setdefault(row["split"], []).append(row)

    write_jsonl(out_dir / "spans" / "all.jsonl", rows)
    for split, split_rows in by_split.items():
        write_jsonl(out_dir / "repaired_datasets" / "citation_verifier" / f"{split}.jsonl", split_rows)
    write_jsonl(out_dir / "repaired_datasets" / "citation_verifier" / "all.jsonl", rows)
    write_json(out_dir / "sources.json", {"sources": source_audits})
    write_json(out_dir / "failures.json", {"failures": failures})

    manifest = {
        "collection_id": COLLECTION_ID,
        "created_at": now_utc(),
        "row_count": len(rows),
        "failure_count": len(failures),
        "source_count": len(SOURCES),
        "contract_id": "citation_contract_repair_v0.1",
        "git": {
            "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
            "commit": git_value(["rev-parse", "HEAD"]),
            "status_short": git_value(["status", "--short"]) or "",
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    }
    write_json(out_dir / "manifest.json", manifest)
    write_report(out_dir, rows, source_audits, failures)

    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
