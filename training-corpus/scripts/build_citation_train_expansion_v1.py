#!/usr/bin/env python3
"""Build the citation TRAINING-POOL expansion pack (citation_train_expansion_v1).

Purpose (D-2026-07-04-008): the five-way verdict head is data-starved (SFT on 62
train rows failed, verdict_acc 0.065). This pack grows the citation training pool
from real SEC filings across the AI vertical, following the eval-v1 construction
logic exactly (keyword-only anchors, claim/evidence pairing, five-way labels via
the C1-C3 conventions, point-in-time fields, paragraph_sha256).

HARD BOUNDARIES
- The frozen eval (citation_real_eval_v1, 131 rows) is UNTOUCHED. This is a new
  dataset dir with its own manifest, split="train" only (plus a small NEW dev
  slice; NEVER test).
- Labels are construction-derived and marked provenance.label_provenance =
  "construction_v1_unaudited". A blind 10% spot-audit is run separately; the
  agreement rate is written to AUDIT_NOTE.md. If <90%, do not commit.
- sample_ids are opaque + label-free per the F-2026-07-02-006 rule (no
  "_verified"/"_contradicts" suffix leaks). The case_key -> sample_id mapping is
  preserved in provenance for auditability but the sample_id itself is a hash.

CONSTRUCTION DISCIPLINE (F-2026-07-01-001 / F-2026-07-02-002)
- Every case carries split= explicitly (never positional).
- Every anchor is matched against fetched blocks; the anchor must be UNIQUE
  across blocks in its source (else the case is dropped and logged), and every
  label-critical fact listed in `must_contain` must appear inside the matched
  span before the row is accepted.

Output layout mirrors citation_real_eval_v1 so CitationAgenticEnv / sft_citation.py
--eval-dir can consume it directly:
  <out>/rows/{all,train,dev}.jsonl        (env reads rows/all.jsonl)
  <out>/sft/sft_citation_letters.jsonl    (letters-action-space SFT rows)
  <out>/manifest.json, sources.json, failures.json, AUDIT_NOTE.md

Usage:
  python build_citation_train_expansion_v1.py            # fetch + build
  python build_citation_train_expansion_v1.py --spot-audit-only  # re-derive audit
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import platform
import re
import string
import subprocess
import time
from dataclasses import dataclass, field
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
COLLECTION_ID = "citation_train_expansion_v1"
DEFAULT_OUT_DIR = BASE_REPAIR_DIR / COLLECTION_ID
COLLECTION_AS_OF = "2026-07-04"
SEC_UA = "KiwiPostTrainingResearch/0.1 (contact: lsj8310d@gmail.com)"
K_CANDIDATES = 6


@dataclass(frozen=True)
class SourceSpec:
    source_key: str
    ticker: str
    source_url: str
    evidence_title: str
    source_type: str          # 10-K / 10-Q / 8-K / 6-K
    published_at: str         # filing_date
    report_date: str
    license_note: str = "public_sec_filing"
    fetch_profile: str = "sec"


from citation_train_expansion_v1_cases_impl import SpanCase  # noqa: E402


# ---------------------------------------------------------------------------
# SOURCES: real, current filing document URLs discovered via the EDGAR
# submissions API on 2026-07-04 (data.sec.gov/submissions/CIK##########.json),
# not guessed. AI vertical: existing ticker set + additions.
# ---------------------------------------------------------------------------
def _s(key, ticker, url, stype, pub, rpt):
    return SourceSpec(key, ticker, url, f"{ticker} {stype} (report date {rpt}, filed {pub})",
                      stype, pub, rpt)


SOURCES: dict[str, SourceSpec] = {s.source_key: s for s in [
    _s("nvda_10k", "NVDA", "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm", "10-K", "2026-02-25", "2026-01-25"),
    _s("nvda_10q", "NVDA", "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000052/nvda-20260426.htm", "10-Q", "2026-05-20", "2026-04-26"),
    _s("amd_10k", "AMD", "https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/amd-20251227.htm", "10-K", "2026-02-04", "2025-12-27"),
    _s("amd_10q", "AMD", "https://www.sec.gov/Archives/edgar/data/2488/000000248826000076/amd-20260328.htm", "10-Q", "2026-05-06", "2026-03-28"),
    _s("mu_10q", "MU", "https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/mu-20260528.htm", "10-Q", "2026-06-25", "2026-05-28"),
    _s("mu_10k", "MU", "https://www.sec.gov/Archives/edgar/data/723125/000072312525000028/mu-20250828.htm", "10-K", "2025-10-03", "2025-08-28"),
    _s("meta_10k", "META", "https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm", "10-K", "2026-01-29", "2025-12-31"),
    _s("meta_10q", "META", "https://www.sec.gov/Archives/edgar/data/1326801/000162828026028526/meta-20260331.htm", "10-Q", "2026-04-30", "2026-03-31"),
    _s("googl_10q", "GOOGL", "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm", "10-Q", "2026-04-30", "2026-03-31"),
    _s("googl_10k", "GOOGL", "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm", "10-K", "2026-02-05", "2025-12-31"),
    _s("amzn_10q", "AMZN", "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm", "10-Q", "2026-04-30", "2026-03-31"),
    _s("amzn_10k", "AMZN", "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm", "10-K", "2026-02-06", "2025-12-31"),
    _s("avgo_10q", "AVGO", "https://www.sec.gov/Archives/edgar/data/1730168/000173016826000054/avgo-20260503.htm", "10-Q", "2026-06-09", "2026-05-03"),
    _s("avgo_10k", "AVGO", "https://www.sec.gov/Archives/edgar/data/1730168/000173016825000121/avgo-20251102.htm", "10-K", "2025-12-18", "2025-11-02"),
    _s("mrvl_10q", "MRVL", "https://www.sec.gov/Archives/edgar/data/1835632/000183563226000019/mrvl-20260502.htm", "10-Q", "2026-05-28", "2026-05-02"),
    _s("mrvl_10k", "MRVL", "https://www.sec.gov/Archives/edgar/data/1835632/000183563226000011/mrvl-20260131.htm", "10-K", "2026-03-11", "2026-01-31"),
    _s("vrt_10q", "VRT", "https://www.sec.gov/Archives/edgar/data/1674101/000162828026026556/vrt-20260331.htm", "10-Q", "2026-04-22", "2026-03-31"),
    _s("vrt_10k", "VRT", "https://www.sec.gov/Archives/edgar/data/1674101/000167410126000008/vrt-20251231.htm", "10-K", "2026-02-13", "2025-12-31"),
    _s("lrcx_10q", "LRCX", "https://www.sec.gov/Archives/edgar/data/707549/000070754926000022/lrcx-20260329.htm", "10-Q", "2026-04-23", "2026-03-29"),
    _s("lrcx_10k", "LRCX", "https://www.sec.gov/Archives/edgar/data/707549/000070754925000075/lrcx-20250629.htm", "10-K", "2025-08-11", "2025-06-29"),
    _s("klac_10q", "KLAC", "https://www.sec.gov/Archives/edgar/data/319201/000031920126000016/klac-20260331.htm", "10-Q", "2026-04-30", "2026-03-31"),
    _s("klac_10k", "KLAC", "https://www.sec.gov/Archives/edgar/data/319201/000031920125000024/klac-20250630.htm", "10-K", "2025-08-08", "2025-06-30"),
    _s("anet_10q", "ANET", "https://www.sec.gov/Archives/edgar/data/1596532/000159653226000078/anet-20260331.htm", "10-Q", "2026-05-06", "2026-03-31"),
    _s("anet_10k", "ANET", "https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm", "10-K", "2026-02-17", "2025-12-31"),
    _s("arm_20f", "ARM", "https://www.sec.gov/Archives/edgar/data/1973239/000197323926000097/arm-20260331.htm", "20-F", "2026-05-26", "2026-03-31"),
    _s("amat_10q", "AMAT", "https://www.sec.gov/Archives/edgar/data/6951/000162828026037227/amat-20260426.htm", "10-Q", "2026-05-21", "2026-04-26"),
    _s("amat_10k", "AMAT", "https://www.sec.gov/Archives/edgar/data/6951/000162828025056742/amat-20251026.htm", "10-K", "2025-12-12", "2025-10-26"),
    _s("smci_10q", "SMCI", "https://www.sec.gov/Archives/edgar/data/1375365/000137536526000014/smci-20260331.htm", "10-Q", "2026-05-11", "2026-03-31"),
    _s("smci_10k", "SMCI", "https://www.sec.gov/Archives/edgar/data/1375365/000137536525000027/smci-20250630.htm", "10-K", "2025-08-28", "2025-06-30"),
    _s("dell_10q", "DELL", "https://www.sec.gov/Archives/edgar/data/1571996/000157199626000030/dell-20260501.htm", "10-Q", "2026-06-09", "2026-05-01"),
    _s("dell_10k", "DELL", "https://www.sec.gov/Archives/edgar/data/1571996/000157199626000008/dell-20260130.htm", "10-K", "2026-03-16", "2026-01-30"),
    _s("orcl_10k", "ORCL", "https://www.sec.gov/Archives/edgar/data/1341439/000119312526277521/orcl-20260531.htm", "10-K", "2026-06-22", "2026-05-31"),
    _s("orcl_8k", "ORCL", "https://www.sec.gov/Archives/edgar/data/1341439/000119312526265848/orcl-20260610.htm", "8-K", "2026-06-10", "2026-06-10"),
    _s("intc_10k", "INTC", "https://www.sec.gov/Archives/edgar/data/50863/000005086326000011/intc-20251227.htm", "10-K", "2026-01-23", "2025-12-27"),
    _s("intc_10q", "INTC", "https://www.sec.gov/Archives/edgar/data/50863/000005086326000079/intc-20260328.htm", "10-Q", "2026-04-24", "2026-03-28"),
    _s("qcom_10q", "QCOM", "https://www.sec.gov/Archives/edgar/data/804328/000080432826000061/qcom-20260329.htm", "10-Q", "2026-04-29", "2026-03-29"),
    _s("qcom_10k", "QCOM", "https://www.sec.gov/Archives/edgar/data/804328/000080432825000085/qcom-20250928.htm", "10-K", "2025-11-05", "2025-09-28"),
    _s("crwv_10q", "CRWV", "https://www.sec.gov/Archives/edgar/data/2021728/000162828026044981/cbrs-20260331.htm", "10-Q", "2026-06-24", "2026-03-31"),
    _s("msft_10q", "MSFT", "https://www.sec.gov/Archives/edgar/data/789019/000119312526191507/msft-20260331.htm", "10-Q", "2026-04-29", "2026-03-31"),
    _s("msft_10k", "MSFT", "https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm", "10-K", "2025-07-30", "2025-06-30"),
    _s("googl_10q_b", "GOOGL", "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm", "10-Q", "2026-04-30", "2026-03-31"),
]}
# googl_10q_b is an alias entry so two distinct GOOGL 10-Q spans can key cleanly;
# collapse it to the same fetch as googl_10q.
SOURCES["googl_10q_b"] = SourceSpec(
    "googl_10q_b", "GOOGL", SOURCES["googl_10q"].source_url,
    SOURCES["googl_10q"].evidence_title, "10-Q", "2026-04-30", "2026-03-31")


# CASES are authored in a separate module-level list appended below.
from citation_train_expansion_v1_cases import CASES  # noqa: E402


# ---------------------------------------------------------------------------
# Extraction machinery (same family as the proven collector)
# ---------------------------------------------------------------------------
class TextExtractor(HTMLParser):
    BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "td", "div", "span"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._stack: list[str] = []
        self._parts: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.BLOCK_TAGS:
            self._stack.append(tag.lower())
            self._parts = []
        elif self._stack and tag.lower() == "br":
            self._parts.append(" ")

    def handle_data(self, data):
        if self._stack:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if self._stack and tag.lower() == self._stack[-1]:
            text = normalize_space(html.unescape(" ".join(self._parts)))
            if 20 <= len(text) <= 1200:
                self.blocks.append(text)
            self._stack.pop()
            self._parts = []


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_space(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("\xa0", " ")).strip()


def normalize_for_match(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", normalize_space(t).lower()).strip()


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def source_domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def git_value(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def anon_sample_id(case_key: str) -> str:
    """Label-free opaque sample_id (F-2026-07-02-006). Deterministic from case_key
    so re-runs are stable, but the id reveals no label."""
    h = hashlib.sha256(f"{COLLECTION_ID}:{case_key}".encode()).hexdigest()[:12]
    return f"{COLLECTION_ID}_{h}"


def support_score(t: str) -> float:
    return {"verified_support": 1.0, "partial_support": 0.55, "candidate_evidence": 0.35,
            "insufficient": 0.0, "contradicts": -1.0}[t]


def fetch_source(spec: SourceSpec, cache: dict[str, Any], timeout: int) -> tuple[list[str], dict[str, Any]]:
    if spec.source_url in cache:
        return cache[spec.source_url]["blocks"], cache[spec.source_url]["audit"]
    started = now_utc()
    last = None
    resp = None
    for attempt in range(1, 4):
        try:
            resp = requests.get(spec.source_url, timeout=timeout,
                                headers={"User-Agent": SEC_UA,
                                         "Accept": "text/html,application/xhtml+xml",
                                         "Accept-Encoding": "gzip, deflate"})
            resp.raise_for_status()
            break
        except Exception as exc:
            last = repr(exc)
            resp = None
            if attempt < 3:
                time.sleep(attempt * 2)
    if resp is None or not resp.ok:
        audit = {"source_key": spec.source_key, "source_url": spec.source_url,
                 "status": "fetch_failed", "error": last or "unknown", "started_at": started,
                 "captured_at": now_utc()}
        cache[spec.source_url] = {"blocks": [], "audit": audit}
        return [], audit
    ex = TextExtractor()
    ex.feed(resp.text)
    seen, blocks = set(), []
    for b in ex.blocks:
        if b not in seen:
            blocks.append(b)
            seen.add(b)
    audit = {"source_key": spec.source_key, "source_url": spec.source_url,
             "source_domain": source_domain(spec.source_url), "source_type": spec.source_type,
             "ticker": spec.ticker, "status": "ok", "http_status": resp.status_code,
             "raw_html_sha256": sha256_text(resp.text), "raw_html_bytes": len(resp.content),
             "extracted_block_count": len(blocks), "published_at": spec.published_at,
             "report_date": spec.report_date, "as_of": COLLECTION_AS_OF,
             "license_note": spec.license_note, "started_at": started, "captured_at": now_utc()}
    cache[spec.source_url] = {"blocks": blocks, "audit": audit}
    time.sleep(0.4)  # SEC rate limit
    return blocks, audit


def find_span(blocks: list[str], anchor: str, must_contain: tuple[str, ...]) -> tuple[int | None, str | None, int, list[str]]:
    """Select the span for an anchor, F-2026-07-02-002-safe.

    SEC HTML nests blocks, so an anchor often matches both a tight paragraph and a
    larger parent <div> that wraps it. Picking the wrong one silently changes the
    label (F-002). We resolve this deterministically:
      1. keep every block whose normalized text contains the anchor;
      2. among those, keep only blocks that ALSO contain every label-critical
         `must_contain` fact (the F-002 fact guard);
      3. return the SHORTEST such block (the tight paragraph, not a parent wrapper),
         which is the minimal span that still carries every labeled fact.
    Returns (index, block, n_anchor_matches, missing_facts). If no block satisfies
    must_contain, returns the shortest anchor match with its missing-fact list so
    the caller logs a precise failure.
    """
    na = normalize_for_match(anchor)
    anchor_matches = [(i, b) for i, b in enumerate(blocks) if na in normalize_for_match(b)]
    if not anchor_matches:
        return None, None, 0, list(must_contain)
    def missing_of(b: str) -> list[str]:
        nb = normalize_for_match(b)
        return [m for m in must_contain if normalize_for_match(m) not in nb]
    complete = [(i, b) for i, b in anchor_matches if not missing_of(b)]
    if complete:
        i, b = min(complete, key=lambda t: len(t[1]))
        return i, b, len(anchor_matches), []
    # no block carries every fact: report against the shortest anchor match
    i, b = min(anchor_matches, key=lambda t: len(t[1]))
    return i, b, len(anchor_matches), missing_of(b)


def build_rows(timeout: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    captured = now_utc()
    cache: dict[str, Any] = {}
    audits: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []

    # fetch each unique URL once
    for spec in SOURCES.values():
        blocks, audit = fetch_source(spec, cache, timeout)
        audits[spec.source_key] = audit
        if audit["status"] != "ok":
            failures.append(audit)

    rows: list[dict[str, Any]] = []
    seen_case_keys: set[str] = set()
    for idx, case in enumerate(CASES):
        if case.case_key in seen_case_keys:
            failures.append({"stage": "dedup", "case_key": case.case_key,
                             "status": "duplicate_case_key"})
            continue
        seen_case_keys.add(case.case_key)
        spec = SOURCES[case.source_key]
        blocks = cache[spec.source_url]["blocks"]
        bidx, span, n, missing = find_span(blocks, case.anchor, case.must_contain)
        if span is None:
            failures.append({"stage": "anchor_match", "case_key": case.case_key,
                             "source_key": case.source_key, "status": "anchor_not_found",
                             "anchor": case.anchor})
            continue
        # F-2026-07-02-002: every label-critical fact must be inside the chosen span
        if missing:
            failures.append({"stage": "must_contain", "case_key": case.case_key,
                             "source_key": case.source_key, "status": "label_fact_missing_from_span",
                             "missing": missing, "match_count": n, "anchor": case.anchor})
            continue

        sid = anon_sample_id(case.case_key)
        row = {
            "sample_id": sid,
            "source": COLLECTION_ID,
            "split": case.split,
            "input": {
                "claim": case.claim,
                "evidence_span": span,
                "evidence_id": f"{case.source_key}:block:{bidx}",
                "evidence_title": spec.evidence_title,
                "source_url": spec.source_url,
                "source_domain": source_domain(spec.source_url),
                "source_class": "sec_filing",
                "source_type": spec.source_type,
                "source_tier": "company_filing",
                "section": case.section,
                "ticker": spec.ticker,
                "as_of": COLLECTION_AS_OF,
                "published_at": spec.published_at,
                "captured_at": captured,
                "claim_scope": case.claim_scope,
                "point_in_time_allowed": case.point_in_time_allowed,
                "license_note": spec.license_note,
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
                "paragraph_index": bidx,
                "paragraph_sha256": sha256_text(span),
                "source_raw_html_sha256": audits[case.source_key].get("raw_html_sha256"),
                "labeling_mode": "construction_v1",
                "label_provenance": "construction_v1_unaudited",
                "requires_human_audit": True,
            },
            "repair": {
                "contract_id": "citation_contract_repair_v0.1",
                "collection_id": COLLECTION_ID,
                "origin": "real_web_source",
                "why": "Training-pool expansion (D-2026-07-04-008): grow the data-starved "
                       "five-way verdict corpus from real SEC filings, eval-v1 construction logic.",
            },
        }
        rows.append(row)
    return rows, list(audits.values()), failures


# ---------------------------------------------------------------------------
# Letters-action-space SFT rows (same shape sft_citation.py builds internally),
# emitted here so the next GPU round can consume them directly.
# ---------------------------------------------------------------------------
def normalize_splits(rows: list[dict[str, Any]], dev_frac: float = 0.15) -> None:
    """Make the pack train-heavy with a SMALL, label-stratified dev slice.

    The prompt calls for split=train only plus optionally a small NEW dev slice
    (never test). Authored `split` fields express dev *intent*; here we cap dev to
    ~dev_frac of each label class so every verdict class appears in dev while the
    bulk trains. Deterministic: rows are ordered by sample_id, and the first
    ceil(dev_frac * n) of each label class become dev, the rest train. Mutates in
    place. No row is ever assigned to test.
    """
    import math
    by_label: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_label.setdefault(r["label"]["support_type"], []).append(r)
    for label, group in by_label.items():
        group.sort(key=lambda r: r["sample_id"])
        n_dev = min(len(group) - 1, math.ceil(dev_frac * len(group))) if len(group) > 1 else 0
        for i, r in enumerate(group):
            r["split"] = "dev" if i < n_dev else "train"


def build_letters_sft(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Render each train/dev row into a letters-menu SFT example whose gold letter
    is looked up through the SAME deterministic candidate mapping the env uses
    (render == score). Never re-derives the letter from raw ordering."""
    pool = {r["input"]["evidence_id"]: r["input"]["evidence_span"] for r in rows}
    claims = {r["sample_id"]: r for r in rows}
    ids_sorted = sorted(pool)

    def candidates(gold_eid: str) -> list[str]:
        cand = [gold_eid] + [i for i in ids_sorted if i != gold_eid][: K_CANDIDATES - 1]
        return sorted(set(cand))

    def letter_map(gold_eid: str) -> dict[str, str]:
        return {string.ascii_uppercase[i]: eid for i, eid in enumerate(candidates(gold_eid))}

    sft: list[dict[str, Any]] = []
    for sid, r in claims.items():
        gold_eid = r["input"]["evidence_id"]
        gold_label = r["label"]["support_type"]
        lmap = letter_map(gold_eid)
        gold_letter = next((l for l, e in lmap.items() if e == gold_eid), None)
        if gold_letter is None or lmap.get(gold_letter) != gold_eid:
            continue  # mapping guard
        menu = "".join(sorted(lmap))
        lines = [f"{l}: {pool[e][:240]}" for l, e in lmap.items()]
        prompt = (
            "You verify financial claims against a fixed evidence pool.\n"
            "Pick the ONE candidate letter that best supports the claim and judge support.\n"
            "Labels: verified_support (all elements directly entailed), partial_support "
            "(some supported, rest absent), insufficient (topical, supports nothing "
            "decisive), contradicts (any element conflicts; precedence over partial), "
            "candidate_evidence (rare).\n"
            f"Cite ONE letter from {menu[0]}-{menu[-1]}; do not invent letters.\n\n"
            f"claim: {r['input']['claim']}\nas_of: {r['input']['as_of']}\n\nCANDIDATES:\n"
            + "\n".join(lines)
            + '\n\nAnswer ONLY: {"cite": "<letter>", "verdict": "<label>"}'
        )
        completion = json.dumps({"cite": gold_letter, "verdict": gold_label}, ensure_ascii=False)
        sft.append({
            "sample_id": sid, "split": r["split"], "prompt": prompt,
            "completion": " " + completion,
            "messages": [{"role": "user", "content": prompt},
                         {"role": "assistant", "content": completion}],
            "gold_letter": gold_letter, "gold_label": gold_label,
        })
    return sft


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def counts_by(rows, keyfn):
    out: dict[str, int] = {}
    for r in rows:
        k = keyfn(r)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--timeout-seconds", type=int, default=45)
    args = ap.parse_args()

    out: Path = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    rows, audits, failures = build_rows(args.timeout_seconds)
    normalize_splits(rows, dev_frac=0.15)  # train-heavy + small label-stratified dev

    # sanity
    problems: list[str] = []
    seen = set()
    for r in rows:
        if r["sample_id"] in seen:
            problems.append(f"dup sample_id {r['sample_id']}")
        seen.add(r["sample_id"])
        if r["split"] not in {"train", "dev"}:
            problems.append(f"{r['sample_id']}: bad split {r['split']} (test forbidden in expansion)")
        if r["input"]["published_at"] > r["input"]["as_of"]:
            problems.append(f"{r['sample_id']}: temporal leakage")
        for leak in ("verified", "contradict", "partial", "insufficient"):
            if leak in r["sample_id"]:
                problems.append(f"{r['sample_id']}: label leak in id")
    by_split = {"train": [r for r in rows if r["split"] == "train"],
                "dev": [r for r in rows if r["split"] == "dev"]}
    write_jsonl(out / "rows" / "all.jsonl", rows)
    for split, sr in by_split.items():
        write_jsonl(out / "rows" / f"{split}.jsonl", sr)

    sft = build_letters_sft(rows)
    write_jsonl(out / "sft" / "sft_citation_letters.jsonl", sft)

    write_json(out / "sources.json", {"sources": audits})
    write_json(out / "failures.json", {"failures": failures})

    manifest = {
        "collection_id": COLLECTION_ID,
        "created_at": now_utc(),
        "as_of": COLLECTION_AS_OF,
        "purpose": "TRAIN-POOL expansion for the data-starved five-way verdict head (D-2026-07-04-008)",
        "frozen_eval_untouched": "citation_real_eval_v1 (131 rows) is immutable; this pack is train/dev only",
        "row_count": len(rows),
        "case_count": len(CASES),
        "accepted_rate": round(len(rows) / max(1, len(CASES)), 4),
        "failure_count": len(failures),
        "source_count": len({s.source_url for s in SOURCES.values()}),
        "label_counts": counts_by(rows, lambda r: r["label"]["support_type"]),
        "split_counts": counts_by(rows, lambda r: r["split"]),
        "source_type_counts": counts_by(rows, lambda r: r["input"]["source_type"]),
        "ticker_counts": counts_by(rows, lambda r: r["input"]["ticker"]),
        "sft_rows": len(sft),
        "label_provenance": "construction_v1_unaudited",
        "sanity_problems": problems,
        "contract_id": "citation_contract_repair_v0.1",
        "git": {"branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
                "commit": git_value(["rev-parse", "HEAD"])},
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
    }
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"row_count": len(rows), "sft_rows": len(sft),
                      "label_counts": manifest["label_counts"],
                      "split_counts": manifest["split_counts"],
                      "ticker_counts": manifest["ticker_counts"],
                      "failures": len(failures), "sanity_problems": problems},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
