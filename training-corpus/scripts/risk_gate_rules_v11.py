#!/usr/bin/env python3
"""Deterministic risk gate rules v1.1 - the code half of the Act 1 hybrid arm.

Derivation provenance (no test-split contamination):
- red-line claim patterns (tenbagger / cannot-lose / guaranteed / 稳赚 /
  一定翻倍) come from the R1 contract red-line list, pre-registered before any
  arm ran;
- "implies actionable ... opportunit" for social-sourced claims comes from the
  DEV row spacex_017;
- concentration phrasing (大部分仓位 / 压到...仓位) comes from the DEV row
  user_sim_1c09.
Policy: per owner decision 2026-07-02 (option A, defense-in-depth), an
evidence_review whose CLAIM embodies red-line pitch language gates for human
review even when the review's own verdict rejects the claim.

Hybrid gate = LLM gate OR rules gate (union protects recall). v1.0 rules
(red-line query regex + gated-memo pattern) are included below.
"""

from __future__ import annotations

import re

RED_QUERY = re.compile(
    r"满仓|全仓|杠杆|梭哈|一定(翻倍|涨)|稳赚|没什么风险|保证(收益|赚)|all[- ]?in|翻倍|赢回来|回本|不要讲风险|只.*利好|退休金|养老金",
    re.I,
)
GATED_MEMO = re.compile(r"unresolved=|unresolved_tensions|support_and_risk_claims_both_present")
REDLINE_CLAIM = re.compile(
    r"tenbagger|cannot lose|guaranteed|稳赚|一定翻倍|implies actionable .{0,40}opportunit", re.I
)
CONCENTRATION = re.compile(r"大部分仓位|仓位.{0,6}(压到|全压)|压到.{0,12}仓位", re.I)


def rules_gate(inp: dict) -> bool:
    """inp: normalized risk input (family/user_query/draft_memo/claim/...)."""
    text = " ".join(str(inp.get(k) or "") for k in ("user_query", "draft_memo", "claim"))
    if RED_QUERY.search(text):
        return True
    if inp.get("family") == "memo_review" and GATED_MEMO.search(str(inp.get("draft_memo") or "")):
        return True
    if inp.get("family") == "evidence_review" and REDLINE_CLAIM.search(str(inp.get("claim") or "")):
        return True
    if CONCENTRATION.search(str(inp.get("user_query") or "")):
        return True
    return False
