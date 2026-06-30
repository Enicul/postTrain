#!/usr/bin/env python3
"""Build router contract repair v0.1 for KIWI coordinator routing.

The expanded router split was balanced but missed important runtime labels:
`risk_review` and `clarification_needed`. It also confused real research traces
with `financial_calculation`. This repair pack adds contract rows while keeping
the provenance of each source visible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter, defaultdict
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
DEFAULT_GOLDEN_DIR = (
    REPO_ROOT
    / "training-corpus"
    / "runs"
    / "x-bookmarks-recent-111-20260629"
    / "curated"
    / "golden_v0.1"
)
REPAIR_ID = "router_contract_repair_v0.1"
ACTIVE_REPAIR_ID = REPAIR_ID

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
    "SPY",
    "QQQ",
    "ARM",
    "COHR",
    "LRCX",
    "ASML",
    "KLAC",
    "DELL",
]

RISK_REVIEW_TEMPLATES = [
    "我想 all in {ticker}，你直接告诉我能不能上。",
    "{ticker} 跌了很多，我要不要加杠杆回本？",
    "我准备把全部仓位换成 {ticker}，风险大吗？",
    "{ticker} 这波是不是稳赚？我想满仓。",
    "我亏了 25%，现在要不要清仓 {ticker}？",
    "朋友让我梭哈 {ticker}，你帮我判断是不是太激进。",
    "如果我用保证金买 {ticker}，最坏情况是什么？",
    "我想追高 {ticker}，但不想看长报告，只要一句建议。",
    "{ticker} 今天大涨，我是不是应该马上买入避免错过？",
    "我能不能把退休账户的大部分钱放进 {ticker}？",
]

CLARIFICATION_TEMPLATES = [
    "之前那只股票现在还能买吗？",
    "刚才说的那个 AI 股风险是不是变大了？",
    "这家公司最近怎么样？我忘了 ticker。",
    "你觉得它还能继续涨吗？",
    "我收藏的那条帖子靠谱吗？没有给你链接。",
    "帮我看看上次我们聊过的那个半导体公司。",
    "这个截图里的观点是不是对的？我还没上传截图。",
]

EVIDENCE_CHECK_TEMPLATES = [
    "我看到一条帖子说 {ticker} 会成为 AI 基建最大受益者，帮我验证证据是否支持。",
    "有人说 {ticker} 的增长已经反转，请检查这条 claim 有没有官方来源支持。",
    "这条新闻标题说 {ticker} 需求爆发，帮我区分事实、观点和需要继续验证的部分。",
    "博主认为 {ticker} 估值很便宜，帮我做 citation support check，不要写完整报告。",
]

DEEP_RESEARCH_TEMPLATES = [
    "{ticker} 的 AI thesis 还成立吗？请结合财报、新闻、估值和反方风险。",
    "请给我一份 {ticker} 的 point-in-time research memo，包含 bull/base/bear 和 invalidation triggers。",
    "{ticker} 最近的财报、guidance、行业数据是否支持一个谨慎乐观观点？",
    "比较 {ticker} 的最新 catalyst、风险、估值和竞争格局，给我一个证据优先的 memo。",
]

FINANCIAL_CALC_TEMPLATES = [
    "帮我计算 {ticker} 最近一季 revenue YoY growth 和 gross margin 变化。",
    "{ticker} 如果 EPS 是 3.2、股价是 160，对应 P/E 是多少？",
    "用给定数字算一下 {ticker} 的 forward multiple，不需要搜索新闻。",
]

REAL_TOOL_EVIDENCE_CHECK_TEMPLATES = [
    "{ticker} 的 connectivity 叙事需要哪些实时来源交叉验证？",
    "{ticker} 和 AI data-center 相关的市场信息需要怎样验证？",
    "{ticker} 是否适合作为 AI semiconductor 研究对象？先判断公开来源是否足够。",
    "{ticker} 在 AI memory theme 里是否有足够公开来源可供研究？",
    "{ticker} 这个主题现在应该先做 source check 还是完整 memo？",
]

REAL_TOOL_RISK_REVIEW_TEMPLATES = [
    "如果用户担心 {ticker} 定投回撤，KIWI 应该快速查什么？",
    "{ticker} 回撤让我很焦虑，先帮我判断是不是需要 risk review。",
    "我不确定 {ticker} 是否已经超出我的风险承受能力，KIWI 应该怎么路由？",
]

REAL_TOOL_DEEP_RESEARCH_TEMPLATES = [
    "{ticker} 最新财报和 AI demand 是否支持一个谨慎研究 memo？",
    "{ticker} 最新价格、新闻和 SEC filings 能支持 AI infra thesis 吗？",
    "{ticker} data center / AI accelerator thesis 的最新工具证据有哪些？",
    "{ticker} AI capex 对 FCF 和风险叙事有什么最新证据？",
    "{ticker} AI capex 相关判断需要哪些来源支持？",
    "{ticker} 的 thesis、风险和 invalidation trigger 需要怎样综合？",
]

SOCIAL_EVIDENCE_CHECK_TEMPLATES = [
    "我收藏到一条关于 {ticker} 的市场观点：有人说 {ticker} 是 AI 基建最大受益者。请帮我判断它有没有可靠证据支持，哪些部分需要官方来源验证，风险点是什么？",
    "我在 X 看到一条关于 {ticker} 的长帖，里面说需求拐点已经确认。请先做 evidence check，不要直接快速回答。",
    "博主说 {ticker} 的最新叙事已经被官方数据验证。请判断 citation 是否支持这个 claim。",
    "这条收藏把 {ticker} 和 AI agent 主题联系起来，请区分事实、观点和需要继续验证的来源。",
    "我收藏的帖子声称 {ticker} 的市场地位被低估，请检查证据是否足够支持，不要写完整投研报告。",
]

SOCIAL_DEEP_RESEARCH_TEMPLATES = [
    "我收藏到一条关于 {ticker} 的复杂市场观点，涉及 AI 产业链、估值、竞争格局和风险。请做多来源 research memo，而不是两句话解释。",
    "这条 X 长帖把 {ticker}、行业供需和宏观风险串在一起，请帮我做完整 thesis / risk / invalidation 分析。",
    "博主对 {ticker} 的观点包含多个 tickers、产业链推演和买卖窗口，请用官方来源和反方证据做 deep research。",
    "这条收藏里的 {ticker} 观点同时涉及财报、新闻、估值和风险，请生成证据优先的研究 memo。",
]

SOCIAL_RISK_REVIEW_TEMPLATES = [
    "我收藏到一条关于 {ticker} 的市场观点：博主说只要拿住就不可能亏钱。请判断风险，不要直接给快速答案。",
    "有人在 X 上说应该梭哈 {ticker}，请先做 risk review，检查过度自信和仓位风险。",
    "这条帖子建议满仓 {ticker} 等待翻倍，请判断它是否违反风险边界。",
    "博主说 {ticker} 现在是黄金买点且不用担心回撤，请先触发 risk review。",
]

SOCIAL_AGENT_ARCHIVE_TEMPLATES = [
    "我收藏到一条关于 AI agent memory 的帖子，没有明确金融决策。请把它作为 Agent Research 归档，不要误当成买卖建议。",
    "这条收藏是关于 WebExplorer / self-improvement 的 agent 研究资料，请判断是否应进入 Agent Research，而不是金融 deep research。",
    "我收藏了一条关于 post-training harness 的观点，帮我做 source check 并标到 Agent Research。",
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


def git_value(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def stable_split(sample_id: str, train_ratio: int = 70, dev_ratio: int = 15) -> str:
    bucket = int(hashlib.sha256(sample_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < train_ratio:
        return "train"
    if bucket < train_ratio + dev_ratio:
        return "dev"
    return "test"


def clone(row: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(row, ensure_ascii=False))


def label_of(row: dict[str, Any]) -> str:
    return str((row.get("label") or row.get("output") or {}).get("route_label") or "")


def normalize_router_row(row: dict[str, Any], *, origin: str, split: str) -> dict[str, Any]:
    copied = clone(row)
    copied["split"] = split
    copied.setdefault("source", origin)
    copied.setdefault("repair", {})
    copied["repair"] = {
        **copied["repair"],
        "repair_id": ACTIVE_REPAIR_ID,
        "origin": origin,
        "contract_issue": "router_label_boundary",
    }
    inp = copied.setdefault("input", {})
    if "user_profile_summary" not in inp and "user_profile" in inp:
        inp["user_profile_summary"] = inp["user_profile"]
    if "market_context" not in inp:
        ticker = inp.get("symbol")
        inp["market_context"] = {"detected_tickers": [ticker] if ticker else []}
    return copied


def source_rows_from_split_dir(base: Path, dataset_dir_name: str = "router_classifier") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split in ["train", "dev", "test"]:
        path = base / dataset_dir_name / f"{split}.jsonl"
        for row in read_jsonl(path):
            rows.append(normalize_router_row(row, origin="expanded_router_v0.6", split=split))
    return rows


def source_rows_from_all(path: Path, *, origin: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(read_jsonl(path)):
        sample_id = str(row.get("sample_id") or f"{origin}_{index:05d}")
        split = str(row.get("split") or stable_split(sample_id))
        rows.append(normalize_router_row(row, origin=origin, split=split))
    return rows


def tool_trace_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, trace in enumerate(read_jsonl(path)):
        trace_id = trace.get("trace_id") or trace.get("task_id") or f"real_tool_trace_{index:03d}"
        symbol = trace.get("symbol")
        tool_names = [item.get("tool_name") for item in trace.get("tool_calls") or [] if item.get("tool_name")]
        route = trace.get("route") or "deep_research"
        sample_id = f"router_{trace_id}"
        row = {
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
                "route_label": route,
                "risk_level": "high" if route == "risk_review" else "medium",
                "required_tools": tool_names,
                "needs_citation": route in {"deep_research", "evidence_check", "risk_review"},
                "needs_realtime_data": True,
                "requires_human_gate": route == "risk_review",
                "reason": "Read-only real tool trace converted into router contract row.",
            },
            "provenance": {
                "trace_id": trace_id,
                "task_id": trace.get("task_id"),
                "source_type": "real_tool_trace_pilot_10",
                "verdict": trace.get("verdict"),
                "failure_taxonomy": trace.get("failure_taxonomy") or [],
            },
            "sample_id": sample_id,
            "source": "real_tool_trace_pilot_10",
            "synthetic": False,
        }
        rows.append(normalize_router_row(row, origin="real_tool_trace_pilot_10", split=stable_split(sample_id, 60, 20)))
    return rows


def router_row(
    *,
    sample_id: str,
    query: str,
    route: str,
    risk_level: str,
    required_tools: list[str],
    needs_realtime_data: bool,
    needs_citation: bool,
    requires_human_gate: bool,
    reason: str,
    symbol: str | None,
    generation_rule: str,
    page_context: str = "router_contract_boundary_generation",
    narrative_tags: list[str] | None = None,
) -> dict[str, Any]:
    row = {
        "input": {
            "user_query": query,
            "user_profile_summary": "market-aware retail investor; needs evidence-first, risk-aware routing",
            "page_context": page_context,
            "symbol": symbol,
            "market_context": {
                "detected_tickers": [symbol] if symbol else [],
                "narrative_tags": narrative_tags or [generation_rule, route],
            },
        },
        "label": {
            "route_label": route,
            "risk_level": risk_level,
            "required_tools": required_tools,
            "needs_realtime_data": needs_realtime_data,
            "needs_citation": needs_citation,
            "requires_human_gate": requires_human_gate,
            "reason": reason,
        },
        "provenance": {
            "source_type": "router_contract_synthetic_boundary",
            "generation_rule": generation_rule,
            "not_market_fact": True,
        },
        "repair": {
            "repair_id": ACTIVE_REPAIR_ID,
            "origin": "generated_contract_boundary",
            "contract_issue": "router_label_boundary",
            "generation_rule": generation_rule,
        },
        "sample_id": sample_id,
        "source": "router_contract_repair_v0.1_generated",
        "synthetic": True,
    }
    return {**row, "split": stable_split(sample_id)}


def generated_boundary_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ticker in TICKERS:
        for index, template in enumerate(RISK_REVIEW_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_contract_risk_review_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="risk_review",
                    risk_level="high",
                    required_tools=["risk_reviewer", "portfolio_context", "clarification_prompt"],
                    needs_realtime_data=False,
                    needs_citation=False,
                    requires_human_gate=True,
                    reason="High-risk trading, leverage, all-in, or panic decision intent must trigger risk review before any research answer.",
                    symbol=ticker,
                    generation_rule="high_risk_trade_intent",
                )
            )
        for index, template in enumerate(EVIDENCE_CHECK_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_contract_evidence_check_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="evidence_check",
                    risk_level="medium",
                    required_tools=["source_search", "citation_verifier"],
                    needs_realtime_data=True,
                    needs_citation=True,
                    requires_human_gate=False,
                    reason="Single claim or social/news assertion needs claim-evidence verification, not a full research memo.",
                    symbol=ticker,
                    generation_rule="claim_verification_not_full_research",
                )
            )
        for index, template in enumerate(DEEP_RESEARCH_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_contract_deep_research_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="deep_research",
                    risk_level="medium",
                    required_tools=["price_lookup", "news_search", "filing_reader", "financial_calculator", "risk_reviewer"],
                    needs_realtime_data=True,
                    needs_citation=True,
                    requires_human_gate=False,
                    reason="Multi-source thesis, valuation, risk, and invalidation analysis requires deep research.",
                    symbol=ticker,
                    generation_rule="multi_source_thesis_research",
                )
            )
        for index, template in enumerate(FINANCIAL_CALC_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_contract_financial_calculation_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="financial_calculation",
                    risk_level="low",
                    required_tools=["financial_calculator"],
                    needs_realtime_data=False,
                    needs_citation=False,
                    requires_human_gate=False,
                    reason="The user asks for a bounded numeric calculation with provided or retrievable financial fields.",
                    symbol=ticker,
                    generation_rule="bounded_numeric_calculation",
                )
            )
        for index, template in enumerate(REAL_TOOL_EVIDENCE_CHECK_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_contract_realtool_evidence_check_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="evidence_check",
                    risk_level="medium",
                    required_tools=["market_price_lookup", "news_search", "source_search", "citation_verifier"],
                    needs_realtime_data=True,
                    needs_citation=True,
                    requires_human_gate=False,
                    reason="Real-tool trace asks whether evidence/source coverage is sufficient; verify sources before producing a full memo.",
                    symbol=ticker,
                    generation_rule="real_tool_style_source_verification",
                    page_context="real_tool_trace_pilot_10",
                    narrative_tags=["real_tool_trace", "complete_tool_trace", "source_verification"],
                )
            )
        for index, template in enumerate(REAL_TOOL_RISK_REVIEW_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_contract_realtool_risk_review_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="risk_review",
                    risk_level="high",
                    required_tools=["risk_reviewer", "portfolio_context", "clarification_prompt"],
                    needs_realtime_data=False,
                    needs_citation=False,
                    requires_human_gate=True,
                    reason="Real-tool trace contains user drawdown or suitability concern; risk review has priority over research depth.",
                    symbol=ticker,
                    generation_rule="real_tool_style_risk_review",
                    page_context="real_tool_trace_pilot_10",
                    narrative_tags=["real_tool_trace", "partial_tool_trace", "risk_review"],
                )
            )
        for index, template in enumerate(REAL_TOOL_DEEP_RESEARCH_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_contract_realtool_deep_research_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="deep_research",
                    risk_level="medium",
                    required_tools=["market_price_lookup", "news_search", "sec_edgar", "financial_calculator", "risk_reviewer"],
                    needs_realtime_data=True,
                    needs_citation=True,
                    requires_human_gate=False,
                    reason="Real-tool trace asks for thesis, memo, filings, capex, FCF, risk synthesis, or invalidation; this requires deep research rather than single-claim evidence check.",
                    symbol=ticker,
                    generation_rule="real_tool_style_thesis_synthesis",
                    page_context="real_tool_trace_pilot_10",
                    narrative_tags=["real_tool_trace", "complete_tool_trace", "thesis_synthesis"],
                )
            )
        for index, template in enumerate(SOCIAL_EVIDENCE_CHECK_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_social_evidence_check_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="evidence_check",
                    risk_level="medium",
                    required_tools=["source_search", "citation_verifier"],
                    needs_realtime_data=True,
                    needs_citation=True,
                    requires_human_gate=False,
                    reason="Long social/bookmark market claim asks for evidence verification; it is not a fast-answer concept question.",
                    symbol=ticker,
                    generation_rule="social_bookmark_claim_verification",
                    page_context="x_bookmark_market_narrative_recent_111",
                    narrative_tags=["social_bookmark", "claim_verification", "not_fast_answer"],
                )
            )
        for index, template in enumerate(SOCIAL_DEEP_RESEARCH_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_social_deep_research_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="deep_research",
                    risk_level="medium",
                    required_tools=["news_search", "company_ir", "sec_edgar", "price_api", "risk_reviewer"],
                    needs_realtime_data=True,
                    needs_citation=True,
                    requires_human_gate=False,
                    reason="Multi-source social/bookmark market narrative needs thesis, risk, and invalidation synthesis.",
                    symbol=ticker,
                    generation_rule="social_bookmark_multi_source_research",
                    page_context="x_bookmark_market_narrative_recent_111",
                    narrative_tags=["social_bookmark", "multi_source_thesis", "not_fast_answer"],
                )
            )
        for index, template in enumerate(SOCIAL_RISK_REVIEW_TEMPLATES):
            rows.append(
                router_row(
                    sample_id=f"router_social_risk_review_{ticker}_{index:02d}",
                    query=template.format(ticker=ticker),
                    route="risk_review",
                    risk_level="high",
                    required_tools=["risk_reviewer", "portfolio_context", "clarification_prompt"],
                    needs_realtime_data=False,
                    needs_citation=True,
                    requires_human_gate=True,
                    reason="Social/bookmark claim includes all-in, no-loss, full-position, or overconfident advice; risk review has priority.",
                    symbol=ticker,
                    generation_rule="social_bookmark_risk_review",
                    page_context="x_bookmark_market_narrative_recent_111",
                    narrative_tags=["social_bookmark", "market_risk_or_positioning", "risk_review"],
                )
            )
    for index, template in enumerate(CLARIFICATION_TEMPLATES * 30):
        sample_id = f"router_contract_clarification_needed_{index:03d}"
        rows.append(
            router_row(
                sample_id=sample_id,
                query=template,
                route="clarification_needed",
                risk_level="low",
                required_tools=["clarification_prompt"],
                needs_realtime_data=False,
                needs_citation=False,
                requires_human_gate=False,
                reason="The request is missing ticker, link, screenshot, or referent; clarify before searching or advising.",
                symbol=None,
                generation_rule="missing_referent_or_input",
            )
        )
    for index, template in enumerate(SOCIAL_AGENT_ARCHIVE_TEMPLATES * 20):
        sample_id = f"router_social_agent_archive_{index:03d}"
        rows.append(
            router_row(
                sample_id=sample_id,
                query=template,
                route="evidence_check",
                risk_level="low",
                required_tools=["source_search", "citation_verifier", "agent_research_archive"],
                needs_realtime_data=False,
                needs_citation=True,
                requires_human_gate=False,
                reason="Agent research bookmark needs source verification and archive routing, not a financial trade workflow.",
                symbol=None,
                generation_rule="social_bookmark_agent_research_archive",
                page_context="x_bookmark_agent_research",
                narrative_tags=["agent_research", "source_discovery_tooling", "not_financial_advice"],
            )
        )
    return rows


def summarize(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"splits": {}, "labels_total": {}, "origins_total": {}}
    label_total: Counter[str] = Counter()
    origin_total: Counter[str] = Counter()
    for split, rows in rows_by_split.items():
        labels = Counter(label_of(row) for row in rows)
        origins = Counter((row.get("repair") or {}).get("origin", row.get("source", "unknown")) for row in rows)
        label_total.update(labels)
        origin_total.update(origins)
        summary["splits"][split] = {
            "rows": len(rows),
            "labels": dict(sorted(labels.items())),
            "origins": dict(sorted(origins.items())),
        }
    summary["labels_total"] = dict(sorted(label_total.items()))
    summary["origins_total"] = dict(sorted(origin_total.items()))
    return summary


def build_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Router Contract Repair v0.1",
        "",
        "This repair pack fixes the first router contract gap exposed by realistic holdouts.",
        "",
        "## What It Repairs",
        "",
        "- Adds `risk_review`, which expanded v0.6 did not train.",
        "- Adds `clarification_needed`, which expanded v0.6 did not train.",
        "- Adds boundary rows for `evidence_check` vs `deep_research`.",
        "- Adds boundary rows for `financial_calculation` vs research tasks.",
        "- Converts real read-only tool traces into router rows.",
        "",
        "## Boundary",
        "",
        "This is a contract repair dataset, not final proof of production routing.",
        "Some rows are generated boundary cases and must be treated as synthetic.",
        "Use realistic holdouts and real tool traces after training to check whether",
        "the repaired contract improves behavior.",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Next",
        "",
        "Run the router-only CPU baseline with summary recording:",
        "",
        "```bash",
        "python3 training-corpus/scripts/train_specialist_baselines.py \\",
        f"  --data-dir {out_dir / 'repaired_datasets'} \\",
        f"  --out-root {out_dir / 'baselines'} \\",
        "  --run-id router_contract_repair_probe_v0.1 \\",
        "  --datasets router_classifier",
        "```",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expanded-dir", type=Path, default=DEFAULT_EXPANDED_DIR)
    parser.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    parser.add_argument("--repair-id", default=REPAIR_ID)
    parser.add_argument("--out-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    global ACTIVE_REPAIR_ID
    args = parse_args()
    ACTIVE_REPAIR_ID = args.repair_id
    expanded_dir = args.expanded_dir.resolve()
    golden_dir = args.golden_dir.resolve()
    out_dir = (args.out_dir or (expanded_dir / "repairs" / args.repair_id)).resolve()
    dataset_out = out_dir / "repaired_datasets" / "router_classifier"
    rows_by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)

    source_groups = [
        source_rows_from_split_dir(expanded_dir),
        source_rows_from_all(golden_dir / "datasets" / "router_classifier" / "all.jsonl", origin="golden_v0.1_router"),
        source_rows_from_all(
            golden_dir / "user_simulation_trace_pilot_50" / "datasets" / "router_classifier" / "all.jsonl",
            origin="user_simulation_trace_pilot_50",
        ),
        source_rows_from_all(
            golden_dir / "long_research_trace_source_quality_repair_25" / "datasets" / "router_classifier" / "all.jsonl",
            origin="long_research_trace_source_quality_repair_25",
        ),
        tool_trace_rows(golden_dir / "real_tool_trace_pilot_10" / "real_tool_traces.jsonl"),
        generated_boundary_rows(),
    ]

    seen: set[str] = set()
    for group in source_groups:
        for row in group:
            sample_id = str(row.get("sample_id"))
            if sample_id in seen:
                sample_id = f"{sample_id}_{len(seen)}"
                row["sample_id"] = sample_id
            seen.add(sample_id)
            split = str(row.get("split") or stable_split(sample_id))
            rows_by_split[split].append(row)

    for split in ["train", "dev", "test"]:
        rows_by_split[split].sort(key=lambda row: str(row.get("sample_id")))
        write_jsonl(dataset_out / f"{split}.jsonl", rows_by_split[split])
    all_rows = [row for split in ["train", "dev", "test"] for row in rows_by_split[split]]
    write_jsonl(dataset_out / "all.jsonl", all_rows)

    summary = summarize(rows_by_split)
    manifest = {
        "repair_id": args.repair_id,
        "created_at": now_utc(),
        "expanded_dir": str(expanded_dir),
        "golden_dir": str(golden_dir),
        "out_dir": str(out_dir),
        "python": sys.version,
        "platform": platform.platform(),
        "git": {
            "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
            "commit": git_value(["rev-parse", "HEAD"]),
            "status_short": git_value(["status", "--short"]) or "",
        },
        "summary": summary,
        "boundary": "Router contract repair only; not final production routing proof.",
    }
    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "summary.json", summary)
    build_readme(out_dir, summary)
    print(json.dumps({"repair_id": args.repair_id, "out_dir": str(out_dir), "summary": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
