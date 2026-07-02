#!/usr/bin/env python3
"""Collect report/filing/transcript/public-research citation spans.

Second real-source collection pass under `citation_contract_repair_v0.1`,
following `real_citation_spans_v0.1`. It fetches SEC filings, earnings call
transcript pages, public industry research, and reputable news articles, then
extracts anchored paragraph spans and labels exact claim-support boundaries.

It does not store raw HTML. Every row keeps source URL, source type, section,
short evidence span, source hash, paragraph hash, published_at, as_of, and a
license note, per docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md.

All labels are manual contract labels from real source spans and are marked
`requires_human_audit`.
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
COLLECTION_ID = "report_and_filing_spans_v0.1"
DEFAULT_OUT_DIR = BASE_REPAIR_DIR / COLLECTION_ID
COLLECTION_AS_OF = "2026-07-02"
SEC_USER_AGENT = "KiwiPostTrainingResearch/0.1 (contact: lsj8310d@gmail.com)"
WEB_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


@dataclass(frozen=True)
class SourceSpec:
    source_key: str
    ticker: str
    source_url: str
    evidence_title: str
    source_class: str
    source_type: str
    source_tier: str
    published_at: str
    license_note: str
    fetch_profile: str = "web"
    fallback_note: str | None = None


@dataclass(frozen=True)
class SpanCase:
    case_key: str
    source_key: str
    anchor: str
    claim: str
    support_type: str
    claim_scope: str
    section: str
    rationale: str
    split: str
    point_in_time_allowed: bool = True


SOURCES: dict[str, SourceSpec] = {
    # --- SEC filings -------------------------------------------------------
    "nvda_10k_fy2026": SourceSpec(
        source_key="nvda_10k_fy2026",
        ticker="NVDA",
        source_url="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm",
        evidence_title="NVIDIA Form 10-K for fiscal year 2026 (ended January 25, 2026)",
        source_class="sec_filing",
        source_type="10-K",
        source_tier="company_filing",
        published_at="2026-02-25",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "nvda_10q_q1fy27": SourceSpec(
        source_key="nvda_10q_q1fy27",
        ticker="NVDA",
        source_url="https://www.sec.gov/Archives/edgar/data/1045810/000104581026000052/nvda-20260426.htm",
        evidence_title="NVIDIA Form 10-Q for the first quarter of fiscal year 2027 (ended April 26, 2026)",
        source_class="sec_filing",
        source_type="10-Q",
        source_tier="company_filing",
        published_at="2026-05-20",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "amd_10k_2025": SourceSpec(
        source_key="amd_10k_2025",
        ticker="AMD",
        source_url="https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/amd-20251227.htm",
        evidence_title="AMD Form 10-K for fiscal year 2025 (ended December 27, 2025)",
        source_class="sec_filing",
        source_type="10-K",
        source_tier="company_filing",
        published_at="2026-02-04",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "msft_10q_fy26q3": SourceSpec(
        source_key="msft_10q_fy26q3",
        ticker="MSFT",
        source_url="https://www.sec.gov/Archives/edgar/data/789019/000119312526191507/msft-20260331.htm",
        evidence_title="Microsoft Form 10-Q for the quarter ended March 31, 2026 (FY26 Q3)",
        source_class="sec_filing",
        source_type="10-Q",
        source_tier="company_filing",
        published_at="2026-04-29",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "mu_10q_fq3_2026": SourceSpec(
        source_key="mu_10q_fq3_2026",
        ticker="MU",
        source_url="https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/mu-20260528.htm",
        evidence_title="Micron Form 10-Q for the third quarter of fiscal 2026 (ended May 28, 2026)",
        source_class="sec_filing",
        source_type="10-Q",
        source_tier="company_filing",
        published_at="2026-06-25",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "meta_10k_2025": SourceSpec(
        source_key="meta_10k_2025",
        ticker="META",
        source_url="https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm",
        evidence_title="Meta Platforms Form 10-K for fiscal year 2025 (ended December 31, 2025)",
        source_class="sec_filing",
        source_type="10-K",
        source_tier="company_filing",
        published_at="2026-01-29",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "googl_10q_q1_2026": SourceSpec(
        source_key="googl_10q_q1_2026",
        ticker="GOOGL",
        source_url="https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm",
        evidence_title="Alphabet Form 10-Q for the quarter ended March 31, 2026",
        source_class="sec_filing",
        source_type="10-Q",
        source_tier="company_filing",
        published_at="2026-04-30",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "amzn_10q_q1_2026": SourceSpec(
        source_key="amzn_10q_q1_2026",
        ticker="AMZN",
        source_url="https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm",
        evidence_title="Amazon Form 10-Q for the quarter ended March 31, 2026",
        source_class="sec_filing",
        source_type="10-Q",
        source_tier="company_filing",
        published_at="2026-04-30",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "avgo_10q_fq2_2026": SourceSpec(
        source_key="avgo_10q_fq2_2026",
        ticker="AVGO",
        source_url="https://www.sec.gov/Archives/edgar/data/1730168/000173016826000054/avgo-20260503.htm",
        evidence_title="Broadcom Form 10-Q for the fiscal quarter ended May 3, 2026 (FQ2 2026)",
        source_class="sec_filing",
        source_type="10-Q",
        source_tier="company_filing",
        published_at="2026-06-09",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    "tsm_6k_may_2026_revenue": SourceSpec(
        source_key="tsm_6k_may_2026_revenue",
        ticker="TSM",
        source_url="https://www.sec.gov/Archives/edgar/data/1046179/000104617926000367/tsm-revenue20260610.htm",
        evidence_title="TSMC Form 6-K: May 2026 revenue report",
        source_class="sec_filing",
        source_type="6-K",
        source_tier="company_filing",
        published_at="2026-06-10",
        license_note="public_sec_filing",
        fetch_profile="sec",
    ),
    # --- Earnings call transcript pages ------------------------------------
    "ts_nvda_q1_fy2027": SourceSpec(
        source_key="ts_nvda_q1_fy2027",
        ticker="NVDA",
        source_url="https://www.fool.com/earnings/call-transcripts/2026/05/20/nvidia-nvda-q1-2027-earnings-transcript/",
        evidence_title="NVIDIA Q1 FY2027 earnings call transcript page (The Motley Fool)",
        source_class="transcript",
        source_type="transcript",
        source_tier="earnings_transcript",
        published_at="2026-05-20",
        license_note="public_web_transcript_page_short_span_quote",
        fallback_note="Metric bullets on the transcript page are the publisher's structured call summary, not verbatim speaker text.",
    ),
    "ts_amd_q1_2026": SourceSpec(
        source_key="ts_amd_q1_2026",
        ticker="AMD",
        source_url="https://www.fool.com/earnings/call-transcripts/2026/05/06/amd-amd-q1-2026-earnings-call-transcript/",
        evidence_title="AMD Q1 2026 earnings call transcript page (The Motley Fool)",
        source_class="transcript",
        source_type="transcript",
        source_tier="earnings_transcript",
        published_at="2026-05-06",
        license_note="public_web_transcript_page_short_span_quote",
        fallback_note="Metric bullets on the transcript page are the publisher's structured call summary, not verbatim speaker text.",
    ),
    "ts_msft_fy26_q3": SourceSpec(
        source_key="ts_msft_fy26_q3",
        ticker="MSFT",
        source_url="https://www.fool.com/earnings/call-transcripts/2026/04/29/microsoft-msft-q3-2026-earnings-transcript/",
        evidence_title="Microsoft FY2026 Q3 earnings call transcript page (The Motley Fool)",
        source_class="transcript",
        source_type="transcript",
        source_tier="earnings_transcript",
        published_at="2026-04-29",
        license_note="public_web_transcript_page_short_span_quote",
        fallback_note="Metric bullets on the transcript page are the publisher's structured call summary, not verbatim speaker text.",
    ),
    "ts_googl_q1_2026": SourceSpec(
        source_key="ts_googl_q1_2026",
        ticker="GOOGL",
        source_url="https://www.fool.com/earnings/call-transcripts/2026/04/29/alphabet-googl-q1-2026-earnings-call-transcript/",
        evidence_title="Alphabet Q1 2026 earnings call transcript page (The Motley Fool)",
        source_class="transcript",
        source_type="transcript",
        source_tier="earnings_transcript",
        published_at="2026-04-29",
        license_note="public_web_transcript_page_short_span_quote",
        fallback_note="Metric bullets on the transcript page are the publisher's structured call summary, not verbatim speaker text.",
    ),
    "ts_amzn_q1_2026": SourceSpec(
        source_key="ts_amzn_q1_2026",
        ticker="AMZN",
        source_url="https://www.fool.com/earnings/call-transcripts/2026/04/29/amazon-amzn-q1-2026-earnings-call-transcript/",
        evidence_title="Amazon Q1 2026 earnings call transcript page (The Motley Fool)",
        source_class="transcript",
        source_type="transcript",
        source_tier="earnings_transcript",
        published_at="2026-04-29",
        license_note="public_web_transcript_page_short_span_quote",
        fallback_note="Metric bullets on the transcript page are the publisher's structured call summary, not verbatim speaker text.",
    ),
    "ts_avgo_fq2_2026": SourceSpec(
        source_key="ts_avgo_fq2_2026",
        ticker="AVGO",
        source_url="https://www.fool.com/earnings/call-transcripts/2026/06/03/broadcom-avgo-q2-2026-earnings-transcript/",
        evidence_title="Broadcom FQ2 2026 earnings call transcript page (The Motley Fool)",
        source_class="transcript",
        source_type="transcript",
        source_tier="earnings_transcript",
        published_at="2026-06-03",
        license_note="public_web_transcript_page_short_span_quote",
        fallback_note="Metric bullets on the transcript page are the publisher's structured call summary, not verbatim speaker text.",
    ),
    # --- Public research ----------------------------------------------------
    "sia_april_2026_sales": SourceSpec(
        source_key="sia_april_2026_sales",
        ticker="SOX",
        source_url="https://www.semiconductors.org/global-semiconductor-sales-increase-11-month-to-month-in-april/",
        evidence_title="SIA: Global Semiconductor Sales Increase 11% Month-to-Month in April",
        source_class="public_research",
        source_type="public_research",
        source_tier="public_research",
        published_at="2026-06-05",
        license_note="public_industry_association_press_release",
    ),
    "sia_q1_2026_sales": SourceSpec(
        source_key="sia_q1_2026_sales",
        ticker="SOX",
        source_url="https://www.semiconductors.org/global-semiconductor-sales-increase-25-from-q4-2025-to-q1-2026/",
        evidence_title="SIA: Global Semiconductor Sales Increase 25% from Q4 2025 to Q1 2026",
        source_class="public_research",
        source_type="public_research",
        source_tier="public_research",
        published_at="2026-05-04",
        license_note="public_industry_association_press_release",
    ),
    "sia_ai_rack_report": SourceSpec(
        source_key="sia_ai_rack_report",
        ticker="SOX",
        source_url="https://www.semiconductors.org/new-report-finds-semiconductors-account-for-95-of-an-ai-data-server-racks-value-encompassing-the-full-stack-of-chip-technologies/",
        evidence_title="SIA/Deloitte report release: semiconductors account for 95% of an AI data server rack's value",
        source_class="public_research",
        source_type="public_research",
        source_tier="public_research",
        published_at="2026-06-01",
        license_note="public_industry_association_press_release",
    ),
    "deloitte_semis_outlook_2026": SourceSpec(
        source_key="deloitte_semis_outlook_2026",
        ticker="SOX",
        source_url="https://www.deloitte.com/us/en/insights/industry/technology/technology-media-telecom-outlooks/semiconductor-industry-outlook.html",
        evidence_title="Deloitte 2026 global semiconductor industry outlook",
        source_class="public_research",
        source_type="public_research",
        source_tier="public_research",
        published_at="2026-02-04",
        license_note="public_web_research_article_short_span_quote",
    ),
    # --- Reputable news -----------------------------------------------------
    "ap_nvda_china_stall": SourceSpec(
        source_key="ap_nvda_china_stall",
        ticker="NVDA",
        source_url="https://apnews.com/article/ai-chips-nvidia-huawei-china-1ae6228c4928ddbb43f984e9b38f49dd",
        evidence_title="AP: Nvidia's AI chip sales in China stall, as local chipmakers like Huawei take the lead",
        source_class="news",
        source_type="news",
        source_tier="reputable_news",
        published_at="2026-06-29",
        license_note="public_news_article_short_span_quote",
    ),
    "ap_samsung_hynix_fabs": SourceSpec(
        source_key="ap_samsung_hynix_fabs",
        ticker="MU",
        source_url="https://apnews.com/article/korea-samsung-ai-hynix-chips-22352d95c7a821c5f4548b2d1a4ebde8",
        evidence_title="AP: Samsung and SK Hynix to build new chipmaking hub in southwestern South Korea",
        source_class="news",
        source_type="news",
        source_tier="reputable_news",
        published_at="2026-06-29",
        license_note="public_news_article_short_span_quote",
        fallback_note="Ticker set to MU because the memory-supply expansion is direct competitive context for Micron; Samsung/SK Hynix do not trade on US exchanges.",
    ),
}


CASES: list[SpanCase] = [
    # ---------------- NVDA 10-K FY2026 (6 rows) ----------------
    SpanCase(
        case_key="nvda10k_rev_verified",
        source_key="nvda_10k_fy2026",
        anchor="Revenue for fiscal year 2026 was $215.9 billion",
        claim="NVIDIA revenue for fiscal year 2026 was $215.9 billion, up 65% from the prior year.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span directly states fiscal year 2026 revenue and the 65% growth rate.",
        split="train",
    ),
    SpanCase(
        case_key="nvda10k_rev_contradicts",
        source_key="nvda_10k_fy2026",
        anchor="Revenue for fiscal year 2026 was $215.9 billion",
        claim="NVIDIA reported fiscal year 2026 revenue of $130.5 billion.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span states fiscal year 2026 revenue was $215.9 billion, not $130.5 billion.",
        split="test",
    ),
    SpanCase(
        case_key="nvda10k_h20_charge_verified",
        source_key="nvda_10k_fy2026",
        anchor="we incurred a $4.5 billion charge in the first quarter of fiscal year 2026 associated with H20",
        claim="NVIDIA incurred a $4.5 billion charge in the first quarter of fiscal year 2026 associated with H20 excess inventory and purchase obligations.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="Item 1 Business / export controls",
        rationale="The span directly states the $4.5 billion H20 charge and its cause.",
        split="train",
    ),
    SpanCase(
        case_key="nvda10k_h20_partial",
        source_key="nvda_10k_fy2026",
        anchor="We generated approximately $60 million in H20 revenue under those licenses",
        claim="After the USG granted licenses in August 2025, NVIDIA generated approximately $60 million in H20 revenue and recovered its prior China data center market share.",
        support_type="partial_support",
        claim_scope="composite",
        section="MD&A / export controls",
        rationale="The span supports the August 2025 licenses and the ~$60 million H20 revenue, but says nothing about recovering China market share.",
        split="dev",
    ),
    SpanCase(
        case_key="nvda10k_dc_growth_insufficient",
        source_key="nvda_10k_fy2026",
        anchor="approximately 42,000 employees in 38 countries",
        claim="NVIDIA Data Center revenue for fiscal year 2026 grew 68% year over year.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="Human Capital",
        rationale="The span covers headcount, not Data Center revenue. The claim is stated elsewhere in the filing, but this span cannot verify it.",
        split="test",
    ),
    SpanCase(
        case_key="nvda10k_gaming_verified",
        source_key="nvda_10k_fy2026",
        anchor="Gaming revenue for fiscal year 2026 was up 41% from a year ago",
        claim="NVIDIA Gaming revenue for fiscal year 2026 was up 41%, and the company expects supply constraints to be a headwind to Gaming in the first quarter of fiscal 2027.",
        support_type="verified_support",
        claim_scope="composite",
        section="MD&A",
        rationale="The span directly states both the 41% Gaming growth and the expected supply-constraint headwind.",
        split="dev",
    ),
    # ---------------- NVDA 10-Q Q1 FY2027 (5 rows) ----------------
    SpanCase(
        case_key="nvda10q_geo_verified",
        source_key="nvda_10q_q1fy27",
        anchor="accounted for 22 % of total revenue for the first quarter of fiscal year 2027",
        claim="Sales to customers headquartered outside the United States accounted for 22% of NVIDIA's total revenue in the first quarter of fiscal year 2027.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="Notes / revenue disaggregation",
        rationale="The span directly states the 22% share for the first quarter of fiscal year 2027.",
        split="train",
    ),
    SpanCase(
        case_key="nvda10q_geo_contradicts",
        source_key="nvda_10q_q1fy27",
        anchor="accounted for 22 % of total revenue for the first quarter of fiscal year 2027",
        claim="Sales to customers headquartered outside the United States accounted for 42% of NVIDIA's total revenue in the first quarter of fiscal year 2027.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="Notes / revenue disaggregation",
        rationale="The span assigns 42% to the first quarter of fiscal year 2026; the fiscal 2027 first-quarter figure is 22%.",
        split="test",
    ),
    SpanCase(
        case_key="nvda10q_customers_verified",
        source_key="nvda_10q_q1fy27",
        anchor="three direct customers represented 21 %, 17 %, and 16 % of total revenue",
        claim="In the first quarter of fiscal year 2027, three direct customers each represented at least 16% of NVIDIA's total revenue, primarily attributable to the Compute & Networking segment.",
        support_type="verified_support",
        claim_scope="composite",
        section="Notes / concentration of revenue",
        rationale="The span states the 21%, 17%, and 16% customer concentrations and their Compute Networking attribution.",
        split="train",
    ),
    SpanCase(
        case_key="nvda10q_customers_contradicts",
        source_key="nvda_10q_q1fy27",
        anchor="three direct customers represented 21 %, 17 %, and 16 % of total revenue",
        claim="NVIDIA's three largest direct customers in the first quarter of fiscal year 2027 were primarily attributable to the Gaming segment.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="Notes / concentration of revenue",
        rationale="The span attributes the concentration primarily to the Compute Networking segment, not Gaming.",
        split="dev",
    ),
    SpanCase(
        case_key="nvda10q_goodwill_insufficient",
        source_key="nvda_10q_q1fy27",
        anchor="goodwill increased by $ 62 million from acquisitions",
        claim="NVIDIA's total revenue increased 20% sequentially in the first quarter of fiscal year 2027.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="Notes / goodwill",
        rationale="The span covers a goodwill change from acquisitions and does not address revenue growth.",
        split="train",
    ),
    # ---------------- AMD 10-K 2025 (5 rows) ----------------
    SpanCase(
        case_key="amd10k_rev_verified",
        source_key="amd_10k_2025",
        anchor="net revenue increasing 34% to $34.6 billion, compared to $25.8 billion in 2024",
        claim="AMD net revenue increased 34% to $34.6 billion in 2025, compared to $25.8 billion in 2024.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span directly states the 2025 net revenue, growth rate, and 2024 comparison.",
        split="train",
    ),
    SpanCase(
        case_key="amd10k_embedded_contradicts",
        source_key="amd_10k_2025",
        anchor="net revenue increasing 34% to $34.6 billion, compared to $25.8 billion in 2024",
        claim="AMD's Embedded segment net revenue grew strongly in 2025.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span states Embedded net revenue of $3.5 billion decreased by 3% compared to 2024.",
        split="test",
    ),
    SpanCase(
        case_key="amd10k_dc_verified",
        source_key="amd_10k_2025",
        anchor="Data Center net revenue of $16.6 billion in 2025 increased by 32%",
        claim="AMD Data Center net revenue of $16.6 billion in 2025 increased 32% from $12.6 billion in 2024, driven primarily by demand for EPYC processors and Instinct GPU accelerators.",
        support_type="verified_support",
        claim_scope="composite",
        section="MD&A / segment results",
        rationale="The span states the segment revenue, growth, comparison base, and demand drivers.",
        split="train",
    ),
    SpanCase(
        case_key="amd10k_dc_partial",
        source_key="amd_10k_2025",
        anchor="Data Center net revenue of $16.6 billion in 2025 increased by 32%",
        claim="AMD Data Center net revenue was $16.6 billion in 2025, and Data Center operating income doubled year over year.",
        support_type="partial_support",
        claim_scope="composite",
        section="MD&A / segment results",
        rationale="The span supports the segment revenue figure but says nothing about operating income.",
        split="dev",
    ),
    SpanCase(
        case_key="amd10k_competition_insufficient",
        source_key="amd_10k_2025",
        anchor="we compete primarily against Intel Corporation (Intel) and Nvidia Corporation",
        claim="AMD holds the second-largest share of the data center GPU market.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="Item 1 Business / competition",
        rationale="The span names AMD's data center competitors but provides no market-share evidence.",
        split="dev",
    ),
    # ---------------- MSFT 10-Q FY26 Q3 (5 rows) ----------------
    SpanCase(
        case_key="msft10q_rev_verified",
        source_key="msft_10q_fy26q3",
        anchor="Revenue increased $12.8 billion or 18% driven by growth in Microsoft Cloud",
        claim="Microsoft's quarterly revenue increased $12.8 billion, or 18%, driven by growth in Microsoft Cloud.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span directly states the quarterly revenue increase and its driver.",
        split="train",
    ),
    SpanCase(
        case_key="msft10q_mpc_contradicts",
        source_key="msft_10q_fy26q3",
        anchor="Revenue increased $12.8 billion or 18% driven by growth in Microsoft Cloud",
        claim="Microsoft's More Personal Computing revenue increased in the quarter, driven by strong Devices and Gaming hardware sales.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span states More Personal Computing revenue decreased with lower hardware sales across Devices and Gaming.",
        split="test",
    ),
    SpanCase(
        case_key="msft10q_cor_verified",
        source_key="msft_10q_fy26q3",
        anchor="Cost of revenue increased $4.9 billion or 22% driven by growth in Microsoft Cloud",
        claim="Microsoft's cost of revenue increased $4.9 billion, or 22%, driven by growth in Microsoft Cloud.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span directly states the cost-of-revenue increase and its driver.",
        split="train",
    ),
    SpanCase(
        case_key="msft10q_azure_partial",
        source_key="msft_10q_fy26q3",
        anchor="Revenue increased $12.8 billion or 18% driven by growth in Microsoft Cloud",
        claim="Microsoft's revenue increased 18% driven by Microsoft Cloud, with Azure revenue growing 39% year over year.",
        support_type="partial_support",
        claim_scope="composite",
        section="MD&A",
        rationale="The span supports the 18% total growth and its driver but does not state an Azure growth rate.",
        split="dev",
    ),
    SpanCase(
        case_key="msft10q_ninemonth_insufficient",
        source_key="msft_10q_fy26q3",
        anchor="Revenue increased $36.5 billion or 18% driven by growth in Microsoft Cloud",
        claim="Microsoft's revenue for the third quarter of fiscal year 2026 increased $36.5 billion, or 18%.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span does not identify the reporting period; the $36.5 billion increase is the nine-month figure, and the span alone cannot verify a quarterly attribution.",
        split="dev",
    ),
    # ---------------- MU 10-Q FQ3 2026 (6 rows) ----------------
    SpanCase(
        case_key="mu10q_qoq_verified",
        source_key="mu_10q_fq3_2026",
        anchor="increased 74% as compared to the second quarter of 2026",
        claim="Micron's total revenue for the third quarter of fiscal 2026 increased 74% compared to the second quarter of fiscal 2026.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span directly states the 74% sequential revenue increase.",
        split="train",
    ),
    SpanCase(
        case_key="mu10q_yoy_contradicts",
        source_key="mu_10q_fq3_2026",
        anchor="increased 346% as compared to the third quarter of 2025",
        claim="Micron's total revenue for the third quarter of fiscal 2026 increased 74% compared to the third quarter of fiscal 2025.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span states the year-over-year increase was 346%; 74% was the sequential increase, so the claim misstates the comparison basis.",
        split="test",
    ),
    SpanCase(
        case_key="mu10q_dram_verified",
        source_key="mu_10q_fq3_2026",
        anchor="Sales of DRAM products increased 67%",
        claim="Micron's DRAM sales increased 67%, driven primarily by a low-60% range increase in average selling prices.",
        support_type="verified_support",
        claim_scope="composite",
        section="MD&A",
        rationale="The span states both the 67% DRAM increase and the ASP driver.",
        split="train",
    ),
    SpanCase(
        case_key="mu10q_dividend_verified",
        source_key="mu_10q_fq3_2026",
        anchor="declared a quarterly dividend of $ 0.15 per share, payable in cash on July 21, 2026",
        claim="On June 24, 2026, Micron's Board of Directors declared a quarterly dividend of $0.15 per share, payable July 21, 2026.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="Notes / equity",
        rationale="The span directly states the declaration date, amount, and payment date.",
        split="dev",
    ),
    SpanCase(
        case_key="mu10q_pricebands_partial",
        source_key="mu_10q_fq3_2026",
        anchor="strategic customer agreements with price bands, even at floor pricing levels",
        claim="Micron expects gross margins from strategic customer agreements with price bands to stay above past peak quarterly margins, and it has already locked in 100% of calendar 2027 supply under such agreements.",
        support_type="partial_support",
        claim_scope="composite",
        section="MD&A / industry conditions",
        rationale="The span supports the gross-margin expectation but says nothing about 100% of calendar 2027 supply being committed.",
        split="dev",
    ),
    SpanCase(
        case_key="mu10q_nand_insufficient",
        source_key="mu_10q_fq3_2026",
        anchor="Focused on memory solutions for large hyperscale cloud customers",
        claim="Micron's NAND sales increased 99% sequentially in the third quarter of fiscal 2026.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="Notes / business unit description",
        rationale="The span describes a business unit's focus and does not address NAND sales. The claim is stated elsewhere in the filing, but this span cannot verify it.",
        split="train",
    ),
    # ---------------- META 10-K 2025 (6 rows) ----------------
    SpanCase(
        case_key="meta10k_costsplit_verified",
        source_key="meta_10k_2025",
        anchor="82% of our total costs and expenses were recognized in FoA and 18% were recognized in RL",
        claim="In 2025, 82% of Meta's total costs and expenses were recognized in Family of Apps and 18% in Reality Labs.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="Item 1 Business / investments",
        rationale="The span directly states the 82%/18% cost split between FoA and RL.",
        split="train",
    ),
    SpanCase(
        case_key="meta10k_rl_loss_verified",
        source_key="meta_10k_2025",
        anchor="Our total RL investments were $21.40 billion in 2025",
        claim="Meta's Reality Labs investments totaled $21.40 billion in 2025, and Meta expects the RL segment to continue operating at a loss for the foreseeable future.",
        support_type="verified_support",
        claim_scope="composite",
        section="Item 1 Business / investments",
        rationale="The span states the $21.40 billion RL investment and the expectation of continued RL losses.",
        split="train",
    ),
    SpanCase(
        case_key="meta10k_wearables_verified",
        source_key="meta_10k_2025",
        anchor="approximately 70% of our Reality Labs operating expenses on our wearables initiatives",
        claim="Meta expects to spend approximately 70% of its 2026 Reality Labs operating expenses on wearables initiatives and the remaining 30% on VR and Horizon initiatives.",
        support_type="verified_support",
        claim_scope="composite",
        section="Item 1 Business / Reality Labs",
        rationale="The span directly states the 70%/30% expected 2026 RL spending split.",
        split="dev",
    ),
    SpanCase(
        case_key="meta10k_wearables_partial",
        source_key="meta_10k_2025",
        anchor="approximately 70% of our Reality Labs operating expenses on our wearables initiatives",
        claim="Meta expects approximately 70% of its 2026 Reality Labs operating expenses to go to wearables initiatives, reflecting the strong profitability of its AI glasses product line.",
        support_type="partial_support",
        claim_scope="composite",
        section="Item 1 Business / Reality Labs",
        rationale="The span supports the 70% wearables allocation but provides no evidence about AI glasses profitability.",
        split="test",
    ),
    SpanCase(
        case_key="meta10k_segments_verified",
        source_key="meta_10k_2025",
        anchor="We report financial results for two segments: Family of Apps (FoA) and Reality Labs (RL)",
        claim="Meta reports two segments, Family of Apps and Reality Labs, and generates substantially all of its revenue from advertising.",
        support_type="verified_support",
        claim_scope="composite",
        section="Item 1 Business / segments",
        rationale="The span states the two segments and that substantially all revenue comes from advertising.",
        split="train",
    ),
    SpanCase(
        case_key="meta10k_rl_risk_contradicts",
        source_key="meta_10k_2025",
        anchor="our Reality Labs strategy and investments may not be successful in the foreseeable future",
        claim="Meta stated that its Reality Labs strategy is certain to succeed in the foreseeable future.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="Risk Factors",
        rationale="The span is an explicit risk disclosure that the RL strategy may not be successful, which conflicts with a certainty claim.",
        split="test",
    ),
    # ---------------- GOOGL 10-Q Q1 2026 (5 rows) ----------------
    SpanCase(
        case_key="googl10q_rev_verified",
        source_key="googl_10q_q1_2026",
        anchor="Revenues were $109.9 billion, an increase of 22% year over year",
        claim="Alphabet Q1 2026 revenues were $109.9 billion, up 22% year over year, including Google Cloud revenue growth of 63%.",
        support_type="verified_support",
        claim_scope="composite",
        section="MD&A",
        rationale="The span states total revenues, the growth rate, and the 63% Google Cloud increase.",
        split="train",
    ),
    SpanCase(
        case_key="googl10q_cloud_contradicts",
        source_key="googl_10q_q1_2026",
        anchor="Revenues were $109.9 billion, an increase of 22% year over year",
        claim="Google Cloud revenues grew 16% year over year in Q1 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span attributes 16% growth to Google Services; Google Cloud grew 63%.",
        split="test",
    ),
    SpanCase(
        case_key="googl10q_youtube_verified",
        source_key="googl_10q_q1_2026",
        anchor="YouTube ads revenues increased $956 million",
        claim="YouTube ads revenues increased $956 million year over year in Q1 2026, driven by direct response advertising products.",
        support_type="verified_support",
        claim_scope="composite",
        section="MD&A / revenues",
        rationale="The span states the $956 million increase and the direct-response driver.",
        split="train",
    ),
    SpanCase(
        case_key="googl10q_youtube_insufficient",
        source_key="googl_10q_q1_2026",
        anchor="YouTube ads revenues increased $956 million",
        claim="YouTube's total revenue including subscriptions exceeded $15 billion in Q1 2026.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="MD&A / revenues",
        rationale="The span covers only the YouTube ads increase and provides no total for ads plus subscriptions.",
        split="dev",
    ),
    SpanCase(
        case_key="googl10q_doj_verified",
        source_key="googl_10q_q1_2026",
        anchor="A final judgment was entered in December 2025",
        claim="A final judgment in the DOJ search antitrust case against Google was entered in December 2025, and Google appealed in January 2026.",
        support_type="verified_support",
        claim_scope="composite",
        section="Notes / legal matters",
        rationale="The span states the December 2025 final judgment and the January 2026 appeal.",
        split="dev",
    ),
    # ---------------- AMZN 10-Q Q1 2026 (4 rows) ----------------
    SpanCase(
        case_key="amzn10q_opinc_verified",
        source_key="amzn_10q_q1_2026",
        anchor="Operating income increased from $18.4 billion in Q1 2025 to $23.9 billion in Q1 2026",
        claim="Amazon's operating income increased from $18.4 billion in Q1 2025 to $23.9 billion in Q1 2026.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span directly states both operating income figures.",
        split="train",
    ),
    SpanCase(
        case_key="amzn10q_opinc_contradicts",
        source_key="amzn_10q_q1_2026",
        anchor="Operating income increased from $18.4 billion in Q1 2025 to $23.9 billion in Q1 2026",
        claim="Amazon's operating income declined year over year in Q1 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="MD&A",
        rationale="The span shows operating income increased from $18.4 billion to $23.9 billion.",
        split="test",
    ),
    SpanCase(
        case_key="amzn10q_aws_def_verified",
        source_key="amzn_10q_q1_2026",
        anchor="The AWS segment consists of amounts earned from global sales of compute, storage, database, and other services",
        claim="Amazon's AWS segment consists of amounts earned from global sales of compute, storage, database, and other services.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="Notes / segment information",
        rationale="The span is the filing's own definition of the AWS segment.",
        split="train",
    ),
    SpanCase(
        case_key="amzn10q_aws_rev_insufficient",
        source_key="amzn_10q_q1_2026",
        anchor="AWS segment assets primarily consist of property and equipment",
        claim="AWS generated $37.6 billion of revenue in Q1 2026.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="Notes / segment information",
        rationale="The span describes AWS segment assets and does not state segment revenue.",
        split="dev",
    ),
    # ---------------- AVGO 10-Q FQ2 2026 (5 rows) ----------------
    SpanCase(
        case_key="avgo10q_concentration_verified",
        source_key="avgo_10q_fq2_2026",
        anchor="accounted for 42% of our net revenue for each of the fiscal quarter and two fiscal quarters ended May 3, 2026",
        claim="Direct sales to one distributor customer accounted for 42% of Broadcom's net revenue in the fiscal quarter ended May 3, 2026.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="Notes / concentration of credit risk",
        rationale="The span directly states the 42% single-customer concentration for the quarter.",
        split="train",
    ),
    SpanCase(
        case_key="avgo10q_concentration_contradicts",
        source_key="avgo_10q_fq2_2026",
        anchor="accounted for 42% of our net revenue for each of the fiscal quarter and two fiscal quarters ended May 3, 2026",
        claim="No single customer accounted for more than 10% of Broadcom's net revenue in the fiscal quarter ended May 3, 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="Notes / concentration of credit risk",
        rationale="The span states one customer accounted for 42% of net revenue.",
        split="test",
    ),
    SpanCase(
        case_key="avgo10q_backstop_verified",
        source_key="avgo_10q_fq2_2026",
        anchor="we entered into a backstop agreement with the investor partner",
        claim="In June 2026, Broadcom entered a backstop agreement covering a customer's AI rack lease obligations, with a maximum exposure of $29 billion.",
        support_type="verified_support",
        claim_scope="composite",
        section="Notes / commitments and contingencies",
        rationale="The span states the June 8, 2026 arrangement, the backstop agreement, and the $29 billion maximum exposure.",
        split="train",
    ),
    SpanCase(
        case_key="avgo10q_backstop_partial",
        source_key="avgo_10q_fq2_2026",
        anchor="we entered into a backstop agreement with the investor partner",
        claim="Broadcom's June 2026 AI rack backstop arrangement has a maximum exposure of $29 billion and added $5 billion of revenue in the quarter.",
        support_type="partial_support",
        claim_scope="composite",
        section="Notes / commitments and contingencies",
        rationale="The span supports the backstop and the $29 billion exposure, but provides no revenue impact for the quarter.",
        split="dev",
    ),
    SpanCase(
        case_key="avgo10q_segments_verified",
        source_key="avgo_10q_fq2_2026",
        anchor="Our semiconductor solutions segment includes all of our semiconductor-based product lines",
        claim="Broadcom has two reportable segments: semiconductor solutions and infrastructure software.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="Notes / segment information",
        rationale="The span states the two reportable segments and what each includes.",
        split="dev",
    ),
    # ---------------- TSM 6-K May 2026 revenue (4 rows) ----------------
    SpanCase(
        case_key="tsm6k_may_verified",
        source_key="tsm_6k_may_2026_revenue",
        anchor="revenue for May 2026 was approximately NT$416.98 billion",
        claim="TSMC's May 2026 consolidated revenue was approximately NT$416.98 billion, up 1.5% from April 2026 and 30.1% from May 2025.",
        support_type="verified_support",
        claim_scope="composite",
        section="Monthly revenue report",
        rationale="The span states the May 2026 revenue and both comparison percentages.",
        split="train",
    ),
    SpanCase(
        case_key="tsm6k_may_contradicts",
        source_key="tsm_6k_may_2026_revenue",
        anchor="revenue for May 2026 was approximately NT$416.98 billion",
        claim="TSMC's May 2026 revenue declined from April 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="Monthly revenue report",
        rationale="The span states May 2026 revenue increased 1.5 percent from April 2026.",
        split="test",
    ),
    SpanCase(
        case_key="tsm6k_ytd_partial",
        source_key="tsm_6k_may_2026_revenue",
        anchor="revenue for May 2026 was approximately NT$416.98 billion",
        claim="TSMC's January-through-May 2026 revenue totaled NT$1,961.80 billion, up 30.0% year over year, keeping TSMC on track to exceed its full-year US-dollar revenue guidance.",
        support_type="partial_support",
        claim_scope="composite",
        section="Monthly revenue report",
        rationale="The span supports the year-to-date total and growth but says nothing about full-year guidance.",
        split="dev",
    ),
    SpanCase(
        case_key="tsm6k_netincome_insufficient",
        source_key="tsm_6k_may_2026_revenue",
        anchor="revenue for May 2026 was approximately NT$416.98 billion",
        claim="TSMC's second-quarter 2026 net income grew more than 40% year over year.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="Monthly revenue report",
        rationale="The span is a monthly revenue disclosure and contains no net income information.",
        split="train",
    ),
    # ---------------- NVDA transcript Q1 FY2027 (5 rows) ----------------
    SpanCase(
        case_key="tsnvda_rev_verified",
        source_key="ts_nvda_q1_fy2027",
        anchor="Total Revenue -- $82 billion, up 85% year over year",
        claim="NVIDIA reported total revenue of $82 billion for the quarter, up 85% year over year and 20% sequentially.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states total revenue, the year-over-year growth, and the sequential growth.",
        split="train",
    ),
    SpanCase(
        case_key="tsnvda_rev_contradicts",
        source_key="ts_nvda_q1_fy2027",
        anchor="Total Revenue -- $82 billion, up 85% year over year",
        claim="NVIDIA's total revenue for the quarter was $75 billion.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="call summary metrics",
        rationale="The span states total revenue of $82 billion; $75 billion was the Data Center figure.",
        split="test",
    ),
    SpanCase(
        case_key="tsnvda_dc_verified",
        source_key="ts_nvda_q1_fy2027",
        anchor="Data Center Revenue -- $75 billion, up 92% year over year",
        claim="NVIDIA Data Center revenue was $75 billion, up 92% year over year, driven by Blackwell architecture demand.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states the Data Center revenue, growth, and Blackwell driver.",
        split="train",
    ),
    SpanCase(
        case_key="tsnvda_vera_partial",
        source_key="ts_nvda_q1_fy2027",
        anchor="Anticipated $20 billion in standalone CPU revenue for the year",
        claim="NVIDIA anticipates $20 billion in standalone Vera CPU revenue for the year, and Vera CPUs contributed $5 billion of revenue this quarter.",
        support_type="partial_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span supports the $20 billion annual anticipation but gives no in-quarter Vera contribution.",
        split="dev",
    ),
    SpanCase(
        case_key="tsnvda_rubin_contradicts",
        source_key="ts_nvda_q1_fy2027",
        anchor="Production Shipments of VeraRubin -- Set to begin in Q3",
        claim="NVIDIA said VeraRubin production shipments already began this quarter.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="call summary metrics",
        rationale="The span states production shipments are set to begin in Q3, not the current quarter.",
        split="test",
    ),
    # ---------------- AMD transcript Q1 2026 (4 rows) ----------------
    SpanCase(
        case_key="tsamd_rev_verified",
        source_key="ts_amd_q1_2026",
        anchor="Total Revenue -- $10.3 billion, up 38%",
        claim="AMD reported first-quarter revenue of $10.3 billion, up 38%, driven by accelerating AI infrastructure demand.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states the revenue, growth rate, and AI-demand driver.",
        split="train",
    ),
    SpanCase(
        case_key="tsamd_guide_verified",
        source_key="ts_amd_q1_2026",
        anchor="Projected at approximately $11.2 billion (plus or minus $300 million)",
        claim="AMD guided Q2 2026 revenue to approximately $11.2 billion, plus or minus $300 million.",
        support_type="verified_support",
        claim_scope="forward_looking",
        section="call summary metrics",
        rationale="The span directly states the Q2 2026 revenue guidance and range.",
        split="train",
    ),
    SpanCase(
        case_key="tsamd_guide_contradicts",
        source_key="ts_amd_q1_2026",
        anchor="Projected at approximately $11.2 billion (plus or minus $300 million)",
        claim="AMD guided Q2 2026 revenue to approximately $10.0 billion.",
        support_type="contradicts",
        claim_scope="forward_looking",
        section="call summary metrics",
        rationale="The span states guidance of approximately $11.2 billion, not $10.0 billion.",
        split="test",
    ),
    SpanCase(
        case_key="tsamd_fcf_partial",
        source_key="ts_amd_q1_2026",
        anchor="Reached a record $2.6 billion, more than tripling, representing 25% of revenue",
        claim="AMD's free cash flow reached a record $2.6 billion, representing 25% of revenue, and gross margin reached a record 60%.",
        support_type="partial_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span supports the free-cash-flow record and revenue share but says nothing about gross margin.",
        split="dev",
    ),
    # ---------------- MSFT transcript FY26 Q3 (4 rows) ----------------
    SpanCase(
        case_key="tsmsft_ocf_verified",
        source_key="ts_msft_fy26_q3",
        anchor="Cash Flow from Operations -- $46.7 billion, up 26%",
        claim="Microsoft's cash flow from operations was $46.7 billion, up 26%, driven by strong cloud billings and collections.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states the operating cash flow, growth, and driver.",
        split="train",
    ),
    SpanCase(
        case_key="tsmsft_capex_verified",
        source_key="ts_msft_fy26_q3",
        anchor="Capital Expenditures -- $31.9 billion, with two-thirds spent on short-lived assets",
        claim="Microsoft's capital expenditures were $31.9 billion, with about two-thirds spent on short-lived assets such as GPUs and CPUs.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states the capex total and the two-thirds short-lived asset mix.",
        split="train",
    ),
    SpanCase(
        case_key="tsmsft_capex_contradicts",
        source_key="ts_msft_fy26_q3",
        anchor="Capital Expenditures -- $31.9 billion, with two-thirds spent on short-lived assets",
        claim="Microsoft's $31.9 billion of capital expenditures went primarily to long-lived datacenter buildings.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="call summary metrics",
        rationale="The span states two-thirds was spent on short-lived assets (GPUs and CPUs), not primarily long-lived buildings.",
        split="test",
    ),
    SpanCase(
        case_key="tsmsft_rpo_partial",
        source_key="ts_msft_fy26_q3",
        anchor="$627 billion, up 99% year over year (including OpenAI)",
        claim="Microsoft's commercial remaining performance obligation reached $627 billion, up 99% year over year, and commercial bookings doubled year over year.",
        support_type="partial_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span supports the RPO figure and growth, but bookings behavior is not covered by this span.",
        split="dev",
    ),
    # ---------------- GOOGL transcript Q1 2026 (4 rows) ----------------
    SpanCase(
        case_key="tsgoogl_netincome_insufficient",
        source_key="ts_googl_q1_2026",
        anchor="Consolidated Revenue -- $109.9 billion, up 22%",
        claim="Alphabet's net income was $62.6 billion in Q1 2026.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="call summary metrics",
        rationale="The span covers consolidated revenue only; net income is not addressed in this span.",
        split="train",
    ),
    SpanCase(
        case_key="tsgoogl_cloud_verified",
        source_key="ts_googl_q1_2026",
        anchor="Google Cloud Revenue -- $20 billion, up 63%",
        claim="Google Cloud revenue was $20 billion, up 63%, with operating margin reaching 32.9%.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states Cloud revenue, growth, and the 32.9% operating margin.",
        split="train",
    ),
    SpanCase(
        case_key="tsgoogl_cloudmargin_contradicts",
        source_key="ts_googl_q1_2026",
        anchor="Google Cloud Revenue -- $20 billion, up 63%",
        claim="Google Cloud's operating margin declined to 17.8% in Q1 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="call summary metrics",
        rationale="The span states the margin reached 32.9%, up from 17.8%, so the claim inverts the direction.",
        split="test",
    ),
    SpanCase(
        case_key="tsgoogl_backlog_partial",
        source_key="ts_googl_q1_2026",
        anchor="Cloud Backlog -- $462 billion, nearly doubled sequentially",
        claim="Google Cloud backlog reached $462 billion, nearly doubling sequentially, driven primarily by a single large customer commitment.",
        support_type="partial_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span supports the backlog level and sequential change but attributes no single-customer driver.",
        split="dev",
    ),
    # ---------------- AMZN transcript Q1 2026 (4 rows) ----------------
    SpanCase(
        case_key="tsamzn_aws_verified",
        source_key="ts_amzn_q1_2026",
        anchor="AWS Revenue -- $37.6 billion, up 28% year over year",
        claim="AWS revenue was $37.6 billion, up 28% year over year, the largest Q4-to-Q1 sequential increase in AWS history.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states AWS revenue, growth, and the record sequential increase.",
        split="train",
    ),
    SpanCase(
        case_key="tsamzn_backlog_verified",
        source_key="ts_amzn_q1_2026",
        anchor="$364 billion as of Q1, explicitly not including over $100 billion",
        claim="AWS backlog was $364 billion as of Q1, explicitly not including over $100 billion from a new deal with Anthropic.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states the backlog and the exclusion of the Anthropic deal.",
        split="dev",
    ),
    SpanCase(
        case_key="tsamzn_backlog_contradicts",
        source_key="ts_amzn_q1_2026",
        anchor="$364 billion as of Q1, explicitly not including over $100 billion",
        claim="AWS's $364 billion Q1 backlog already includes the new Anthropic deal.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="call summary metrics",
        rationale="The span explicitly states the backlog does not include the Anthropic deal.",
        split="test",
    ),
    SpanCase(
        case_key="tsamzn_leo_insufficient",
        source_key="ts_amzn_q1_2026",
        anchor="cost increase of approximately $1 billion related to Amazon LEO",
        claim="Amazon expects AWS operating margin to decline in Q2 2026.",
        support_type="insufficient",
        claim_scope="forward_looking",
        section="remarks summary",
        rationale="The span covers an Amazon LEO cost increase affecting overall Q2 operating income and does not address AWS segment margin.",
        split="train",
    ),
    # ---------------- AVGO transcript FQ2 2026 (4 rows) ----------------
    SpanCase(
        case_key="tsavgo_rev_verified",
        source_key="ts_avgo_fq2_2026",
        anchor="The company reported $22.2 billion for fiscal Q2 2026",
        claim="Broadcom reported $22.2 billion of revenue for fiscal Q2 2026, up 48% year over year, driven by AI semiconductor demand.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states the revenue, growth rate, and AI-demand driver.",
        split="train",
    ),
    SpanCase(
        case_key="tsavgo_ai_verified",
        source_key="ts_avgo_fq2_2026",
        anchor="AI semiconductor revenue -- $10.8 billion, up 143% year-on-year",
        claim="Broadcom's AI semiconductor revenue was $10.8 billion, up 143% year over year, with AI bookings exceeding $30 billion.",
        support_type="verified_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span states AI revenue, growth, and the bookings level.",
        split="train",
    ),
    SpanCase(
        case_key="tsavgo_ai_partial",
        source_key="ts_avgo_fq2_2026",
        anchor="AI semiconductor revenue -- $10.8 billion, up 143% year-on-year",
        claim="Broadcom's AI semiconductor revenue was $10.8 billion, and management guided AI revenue to double again next quarter.",
        support_type="partial_support",
        claim_scope="composite",
        section="call summary metrics",
        rationale="The span supports the AI revenue figure but contains no next-quarter doubling guidance.",
        split="dev",
    ),
    SpanCase(
        case_key="tsavgo_networking_contradicts",
        source_key="ts_avgo_fq2_2026",
        anchor="Networking accounted for nearly 40% of AI semiconductor revenue",
        claim="Networking accounted for the majority of Broadcom's AI semiconductor revenue in fiscal Q2 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="call summary metrics",
        rationale="The span states networking was nearly 40% of AI semiconductor revenue, which is not a majority.",
        split="test",
    ),
    # ---------------- SIA April 2026 sales (5 rows) ----------------
    SpanCase(
        case_key="siaapril_sales_verified",
        source_key="sia_april_2026_sales",
        anchor="global semiconductor sales were $110.5 billion during the month of April 2026",
        claim="Global semiconductor sales were $110.5 billion in April 2026, up 11% from March 2026 and 93.9% year over year.",
        support_type="verified_support",
        claim_scope="composite",
        section="press release body",
        rationale="The span states the April total and both comparison percentages.",
        split="train",
    ),
    SpanCase(
        case_key="siaapril_sales_contradicts",
        source_key="sia_april_2026_sales",
        anchor="global semiconductor sales were $110.5 billion during the month of April 2026",
        claim="Global semiconductor sales declined month over month in April 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="press release body",
        rationale="The span states an 11% month-to-month increase in April 2026.",
        split="test",
    ),
    SpanCase(
        case_key="siaapril_forecast_verified",
        source_key="sia_april_2026_sales",
        anchor="projects annual global sales will grow by 90% to $1.5 trillion in 2026",
        claim="SIA endorsed the WSTS Spring 2026 forecast projecting annual global semiconductor sales to grow 90% to $1.5 trillion in 2026.",
        support_type="verified_support",
        claim_scope="forward_looking",
        section="press release body",
        rationale="The span states the endorsement and the 90% / $1.5 trillion forecast.",
        split="train",
    ),
    SpanCase(
        case_key="siaapril_forecast_partial",
        source_key="sia_april_2026_sales",
        anchor="projects annual global sales will grow by 90% to $1.5 trillion in 2026",
        claim="The WSTS Spring 2026 forecast projects $1.5 trillion of 2026 global semiconductor sales, driven mainly by automotive and industrial chips.",
        support_type="partial_support",
        claim_scope="composite",
        section="press release body",
        rationale="The span supports the $1.5 trillion forecast but attributes no automotive/industrial driver.",
        split="dev",
    ),
    SpanCase(
        case_key="siaapril_regions_contradicts",
        source_key="sia_april_2026_sales",
        anchor="year-to-year sales in April were up in the Americas (115.8%)",
        claim="China posted the fastest year-to-year regional semiconductor sales growth in April 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="press release body",
        rationale="The span shows the Americas grew 115.8% year to year while China grew 78.6%, so China was not the fastest region.",
        split="dev",
    ),
    # ---------------- SIA Q1 2026 sales (4 rows) ----------------
    SpanCase(
        case_key="siaq1_sales_verified",
        source_key="sia_q1_2026_sales",
        anchor="global semiconductor sales were $298.5 billion during the first quarter of 2026",
        claim="Global semiconductor sales were $298.5 billion in the first quarter of 2026, up 25% from Q4 2025.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="press release body",
        rationale="The span states the Q1 2026 total and the 25% quarter-over-quarter increase.",
        split="train",
    ),
    SpanCase(
        case_key="siaq1_sales_contradicts",
        source_key="sia_q1_2026_sales",
        anchor="global semiconductor sales were $298.5 billion during the first quarter of 2026",
        claim="Global semiconductor sales in the first quarter of 2026 totaled $99.5 billion.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="press release body",
        rationale="The span states $298.5 billion for the quarter; $99.5 billion was the March monthly figure.",
        split="test",
    ),
    SpanCase(
        case_key="siaq1_trillion_insufficient",
        source_key="sia_q1_2026_sales",
        anchor="on track to reach $1 trillion in 2026",
        claim="Global semiconductor sales are projected to reach $1.5 trillion in 2026.",
        support_type="insufficient",
        claim_scope="forward_looking",
        section="press release body",
        rationale="As of this May 4 release, SIA said sales were on track to reach $1 trillion in 2026; the later $1.5 trillion WSTS forecast is not in this span, so it cannot verify the claim.",
        split="dev",
    ),
    SpanCase(
        case_key="siaq1_japan_contradicts",
        source_key="sia_q1_2026_sales",
        anchor="year-to-year sales in March were up in the Asia Pacific/All Other (108.5%)",
        claim="Japan posted the strongest year-to-year semiconductor sales growth in March 2026.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="press release body",
        rationale="The span shows Japan grew 7.4% year to year, the slowest of the listed regions, not the strongest.",
        split="train",
    ),
    # ---------------- SIA/Deloitte AI rack report (4 rows) ----------------
    SpanCase(
        case_key="siarack_value_verified",
        source_key="sia_ai_rack_report",
        anchor="chips account for more than 95% of a leading AI server rack",
        claim="The SIA/Deloitte report finds chips account for more than 95% of a leading AI server rack's content value and more than 50% of AI data center capital expenditures.",
        support_type="verified_support",
        claim_scope="composite",
        section="press release body",
        rationale="The span states both the 95% content-value share and the 50% capex share.",
        split="train",
    ),
    SpanCase(
        case_key="siarack_2028_contradicts",
        source_key="sia_ai_rack_report",
        anchor="chips account for more than 95% of a leading AI server rack",
        claim="The report projects annual revenue for semiconductors used in AI data centers could reach $2.8 trillion by 2028.",
        support_type="contradicts",
        claim_scope="forward_looking",
        section="press release body",
        rationale="The span projects $1.2 trillion of AI data center semiconductor revenue by 2028; $2.8 trillion is the separate semiconductor-investment figure through 2028.",
        split="test",
    ),
    SpanCase(
        case_key="siarack_invest_verified",
        source_key="sia_ai_rack_report",
        anchor="invest over $4 trillion in new data center infrastructure through 2028",
        claim="Government and industry will invest over $4 trillion in new data center infrastructure through 2028, of which up to $2.8 trillion will be spent on semiconductors.",
        support_type="verified_support",
        claim_scope="forward_looking",
        section="press release body",
        rationale="The span states both the $4 trillion infrastructure figure and the $2.8 trillion semiconductor share.",
        split="dev",
    ),
    SpanCase(
        case_key="siarack_share_insufficient",
        source_key="sia_ai_rack_report",
        anchor="in partnership with Deloitte, today released a report",
        claim="The SIA/Deloitte report projects NVIDIA will retain more than 90% share of AI accelerators.",
        support_type="insufficient",
        claim_scope="forward_looking",
        section="press release body",
        rationale="The span announces the report release and contains no vendor market-share projection.",
        split="train",
    ),
    # ---------------- Deloitte 2026 semiconductor outlook (5 rows) ----------------
    SpanCase(
        case_key="deloitte_975_verified",
        source_key="deloitte_semis_outlook_2026",
        anchor="expected to reach US$975 billion in annual sales in 2026",
        claim="Deloitte's 2026 outlook expected the global semiconductor industry to reach US$975 billion in annual sales in 2026, with growth accelerating from 22% in 2025 to 26% in 2026.",
        support_type="verified_support",
        claim_scope="composite",
        section="outlook overview",
        rationale="The span states the US$975 billion 2026 expectation and both growth rates.",
        split="train",
    ),
    SpanCase(
        case_key="deloitte_15t_contradicts",
        source_key="deloitte_semis_outlook_2026",
        anchor="expected to reach US$975 billion in annual sales in 2026",
        claim="Deloitte's 2026 outlook projected US$1.5 trillion of global semiconductor sales in 2026.",
        support_type="contradicts",
        claim_scope="forward_looking",
        section="outlook overview",
        rationale="The span states a US$975 billion expectation. The later WSTS Spring 2026 forecast of $1.5 trillion comes from a different, newer source; against this February span the claim is contradicted.",
        split="test",
    ),
    SpanCase(
        case_key="deloitte_genai_verified",
        source_key="deloitte_semis_outlook_2026",
        anchor="generative AI chips will approach US$500 billion in revenue in 2026",
        claim="Deloitte predicted generative AI chips would approach US$500 billion in revenue in 2026, roughly half of global chip sales.",
        support_type="verified_support",
        claim_scope="forward_looking",
        section="outlook overview",
        rationale="The span states the US$500 billion prediction and the roughly-half share.",
        split="train",
    ),
    SpanCase(
        case_key="deloitte_genai_partial",
        source_key="deloitte_semis_outlook_2026",
        anchor="generative AI chips will approach US$500 billion in revenue in 2026",
        claim="Deloitte predicted gen AI chips would approach US$500 billion of 2026 revenue, and AMD CEO Lisa Su estimated a US$1 trillion AI accelerator TAM by 2030, which Deloitte called conservative.",
        support_type="partial_support",
        claim_scope="composite",
        section="outlook overview",
        rationale="The span supports the US$500 billion prediction and Lisa Su's US$1 trillion TAM estimate, but Deloitte calling it conservative is not in the span.",
        split="dev",
    ),
    SpanCase(
        case_key="deloitte_pc_verified",
        source_key="deloitte_semis_outlook_2026",
        anchor="personal computing device and smartphone sales, which were anticipated to grow in 2025",
        claim="Personal computing device and smartphone sales are now expected to decline in 2026 due to rising memory prices.",
        support_type="verified_support",
        claim_scope="forward_looking",
        section="outlook overview",
        rationale="The span directly states the expected 2026 decline and the memory-price cause.",
        split="dev",
    ),
    # ---------------- AP: NVIDIA China stall (4 rows) ----------------
    SpanCase(
        case_key="apnvda_overtake_verified",
        source_key="ap_nvda_china_stall",
        anchor="Chinese companies like Huawei overtake global industry leaders like Nvidia in their home market",
        claim="AP reported that Chinese companies like Huawei are overtaking global leaders like Nvidia in China's AI hardware market.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="article body",
        rationale="The span directly states that Chinese companies like Huawei are overtaking leaders like Nvidia in their home market.",
        split="train",
    ),
    SpanCase(
        case_key="apnvda_huang_verified",
        source_key="ap_nvda_china_stall",
        anchor="the U.S. has lost its edge in China",
        claim="Jensen Huang has acknowledged that the U.S. has lost its edge in China's advanced AI chip market.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="article body",
        rationale="The span directly reports Huang's acknowledgment.",
        split="dev",
    ),
    SpanCase(
        case_key="apnvda_huang_contradicts",
        source_key="ap_nvda_china_stall",
        anchor="the U.S. has lost its edge in China",
        claim="Jensen Huang said Nvidia retains a commanding lead in China's advanced AI chip market.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="article body",
        rationale="The span reports Huang acknowledging the U.S. lost its edge, which conflicts with a commanding-lead claim.",
        split="test",
    ),
    SpanCase(
        case_key="apnvda_zero_insufficient",
        source_key="ap_nvda_china_stall",
        anchor="AI chip sales in China stall",
        claim="Nvidia's China data center revenue fell to zero in mid-2026.",
        support_type="insufficient",
        claim_scope="single_fact",
        section="headline",
        rationale="The headline says sales stalled; it does not quantify revenue, and a stall is not evidence of zero revenue.",
        split="train",
    ),
    # ---------------- AP: Samsung/SK Hynix fabs (4 rows) ----------------
    SpanCase(
        case_key="apkorea_fabs_verified",
        source_key="ap_samsung_hynix_fabs",
        anchor="together produce about two-thirds of the world",
        claim="Samsung and SK Hynix, which together produce about two-thirds of the world's memory chips, will each build two fabrication plants in southwestern South Korea.",
        support_type="verified_support",
        claim_scope="composite",
        section="article body",
        rationale="The span states the two-thirds memory share and the two-fabs-each plan in the southwest.",
        split="train",
    ),
    SpanCase(
        case_key="apkorea_fabs_partial",
        source_key="ap_samsung_hynix_fabs",
        anchor="together produce about two-thirds of the world",
        claim="Samsung and SK Hynix will each build two fabs in southwestern South Korea, with both companies targeting completion by 2030.",
        support_type="partial_support",
        claim_scope="composite",
        section="article body",
        rationale="The span supports the fab plan but gives no completion timeline; the article elsewhere says timing was not specified.",
        split="dev",
    ),
    SpanCase(
        case_key="apkorea_timing_contradicts",
        source_key="ap_samsung_hynix_fabs",
        anchor="The companies didn't specify when the fabs in the southwest regions would be completed",
        claim="Samsung and SK Hynix committed to completing the new southwestern fabs by 2028.",
        support_type="contradicts",
        claim_scope="single_fact",
        section="article body",
        rationale="The span explicitly states the companies did not specify completion timing, which conflicts with a 2028 commitment claim.",
        split="test",
    ),
    SpanCase(
        case_key="apkorea_gwangju_verified",
        source_key="ap_samsung_hynix_fabs",
        anchor="new fabs will be built in the southwestern city of Gwangju",
        claim="Samsung's chairman said the company's new fabs will be built in the southwestern city of Gwangju.",
        support_type="verified_support",
        claim_scope="single_fact",
        section="article body",
        rationale="The span directly states the Gwangju location for Samsung's new fabs.",
        split="dev",
    ),
]


SCOUTING_FAILURES: list[dict[str, Any]] = [
    {
        "stage": "source_scouting",
        "source": "https://www.gartner.com/en/newsroom",
        "status": "fetch_failed_403",
        "note": "Gartner newsroom blocked scripted fetch; excluded from public research sources.",
    },
    {
        "stage": "source_scouting",
        "source": "https://my.idc.com/getdoc.jsp?containerId=prUS53229425",
        "status": "fetch_failed_404",
        "note": "IDC press-release URL guess returned 404; IDC excluded rather than guessing further.",
    },
    {
        "stage": "source_scouting",
        "source": "https://www.fool.com/earnings-call-transcripts/?page=N",
        "status": "pagination_ineffective",
        "note": "Archive pagination returned the same first page; large-cap transcripts were located via monthly sitemaps instead.",
    },
    {
        "stage": "source_scouting",
        "source": "https://html.duckduckgo.com/html/",
        "status": "bot_challenge",
        "note": "DuckDuckGo HTML search returned challenge pages (202) for transcript queries; replaced by fool.com sitemap enumeration.",
    },
    {
        "stage": "source_scouting",
        "source": "micron fiscal Q3 2026 earnings call transcript",
        "status": "not_found_in_sitemap",
        "note": "No Micron FQ3 2026 transcript in fool.com June/July 2026 sitemaps at collection time; Micron transcript-tier rows deferred, Micron covered via 10-Q instead.",
    },
]


class TextExtractor(HTMLParser):
    """Lightweight paragraph/list/table-cell extractor (same family as v0.1 collector)."""

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
    user_agent = SEC_USER_AGENT if spec.fetch_profile == "sec" else WEB_USER_AGENT
    last_error: str | None = None
    response: requests.Response | None = None
    for attempt in range(1, 4):
        try:
            response = requests.get(
                spec.source_url,
                timeout=timeout_seconds,
                headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"},
            )
            response.raise_for_status()
            break
        except Exception as exc:
            last_error = repr(exc)
            response = None
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
        "source_type": spec.source_type,
        "source_tier": spec.source_tier,
        "ticker": spec.ticker,
        "status": "ok",
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "raw_html_sha256": sha256_text(response.text),
        "raw_html_bytes": len(response.content),
        "extracted_block_count": len(blocks),
        "published_at": spec.published_at,
        "as_of": COLLECTION_AS_OF,
        "license_note": spec.license_note,
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


def support_score(support_type: str) -> float:
    return {
        "verified_support": 1.0,
        "partial_support": 0.55,
        "candidate_evidence": 0.35,
        "insufficient": 0.0,
        "contradicts": -1.0,
    }[support_type]


def build_rows(timeout_seconds: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    captured_at = now_utc()
    blocks_by_source: dict[str, list[str]] = {}
    source_audits: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = list(SCOUTING_FAILURES)

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
                    "stage": "anchor_match",
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
            "split": case.split,
            "input": {
                "claim": case.claim,
                "evidence_span": span,
                "evidence_id": f"{case.source_key}:block:{block_index}",
                "evidence_title": spec.evidence_title,
                "source_url": spec.source_url,
                "source_domain": source_domain(spec.source_url),
                "source_class": spec.source_class,
                "source_type": spec.source_type,
                "source_tier": spec.source_tier,
                "section": case.section,
                "ticker": spec.ticker,
                "as_of": COLLECTION_AS_OF,
                "published_at": spec.published_at,
                "captured_at": captured_at,
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
                "why": "Report/filing/transcript/public-research span pack collected before training citation verifier repair v0.3.",
            },
        }
        rows.append(row)
    return rows, source_audits, failures


def run_sanity_checks(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Schema and target sanity checks for the collected pack."""
    required_input_fields = [
        "claim",
        "evidence_span",
        "source_url",
        "source_class",
        "source_type",
        "source_tier",
        "section",
        "as_of",
        "published_at",
        "license_note",
    ]
    allowed_labels = {"verified_support", "partial_support", "insufficient", "contradicts", "candidate_evidence"}
    problems: list[str] = []
    tier_counts: dict[str, int] = {}
    label_counts: dict[str, int] = {}
    split_counts: dict[str, int] = {}
    seen_ids: set[str] = set()

    for row in rows:
        sample_id = row.get("sample_id", "<missing>")
        if sample_id in seen_ids:
            problems.append(f"duplicate sample_id: {sample_id}")
        seen_ids.add(sample_id)
        for field in required_input_fields:
            if not row.get("input", {}).get(field):
                problems.append(f"{sample_id}: missing input.{field}")
        label = row.get("label", {}).get("support_type")
        if label not in allowed_labels:
            problems.append(f"{sample_id}: bad support_type {label!r}")
        if row.get("split") not in {"train", "dev", "test"}:
            problems.append(f"{sample_id}: bad split {row.get('split')!r}")
        if not row.get("provenance", {}).get("paragraph_sha256"):
            problems.append(f"{sample_id}: missing paragraph_sha256")
        if row["input"]["published_at"] > row["input"]["as_of"]:
            problems.append(f"{sample_id}: temporal leakage published_at > as_of")
        tier = row["input"]["source_tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        label_counts[label] = label_counts.get(label, 0) + 1
        split_counts[row["split"]] = split_counts.get(row["split"], 0) + 1

    targets = {
        "total_rows_gte_100": len(rows) >= 100,
        "sec_filing_rows_gte_30": tier_counts.get("company_filing", 0) >= 30,
        "transcript_rows_gte_20": tier_counts.get("earnings_transcript", 0) >= 20,
        "research_news_rows_gte_20": tier_counts.get("public_research", 0) + tier_counts.get("reputable_news", 0) >= 20,
        "all_four_boundary_labels_present": {"verified_support", "partial_support", "insufficient", "contradicts"}
        <= set(label_counts),
    }
    return {
        "row_count": len(rows),
        "problems": problems,
        "tier_counts": tier_counts,
        "label_counts": label_counts,
        "split_counts": split_counts,
        "targets": targets,
        "passed": not problems and all(targets.values()),
    }


def write_report(
    out_dir: Path,
    rows: list[dict[str, Any]],
    source_audits: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    sanity: dict[str, Any],
) -> None:
    source_counts: dict[str, int] = {}
    for row in rows:
        source_key = row["provenance"]["source_key"]
        source_counts[source_key] = source_counts.get(source_key, 0) + 1

    lines = [
        "# Report and Filing Spans v0.1",
        "",
        "Second real-source citation span pack under `citation_contract_repair_v0.1`,",
        "following `real_citation_spans_v0.1`. Sources now include SEC filings (10-K,",
        "10-Q, 6-K), earnings call transcript pages, public industry research, and",
        "reputable news, per `docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md`.",
        "",
        "## Summary",
        "",
        f"- Rows: {len(rows)}",
        f"- Sources fetched: {sum(1 for audit in source_audits if audit.get('status') == 'ok')} / {len(source_audits)}",
        f"- Failures recorded (scouting + fetch + anchor): {len(failures)}",
        f"- Labels: `{json.dumps(sanity['label_counts'], sort_keys=True)}`",
        f"- Splits: `{json.dumps(sanity['split_counts'], sort_keys=True)}`",
        f"- Source tiers: `{json.dumps(sanity['tier_counts'], sort_keys=True)}`",
        f"- Sanity checks passed: {sanity['passed']}",
        "",
        "## Targets",
        "",
    ]
    for target, ok in sanity["targets"].items():
        lines.append(f"- `{target}`: {'yes' if ok else 'NO'}")
    lines.extend(
        [
            "",
            "## Why",
            "",
            "A financial research agent should know whether a claim is supported by a",
            "filing, management commentary, a financial table, public industry research,",
            "or merely a headline. This pack adds those source tiers with exact",
            "claim-support boundaries, including cross-period traps (sequential vs",
            "year-over-year), figure-swap traps (segment vs total), attribution traps,",
            "and stale-forecast traps across sources with different `published_at` dates.",
            "",
            "## Source Mix",
            "",
        ]
    )
    for source_key, count in sorted(source_counts.items()):
        spec = SOURCES[source_key]
        lines.append(f"- `{source_key}` ({spec.source_type}, {spec.ticker}): {count} rows")
    lines.extend(
        [
            "",
            "## Guardrails Applied",
            "",
            "- No raw HTML/PDF dumps stored; only anchored spans plus hashes.",
            "- Paywalled sell-side research was not collected.",
            "- Transcript-tier spans come from a public transcript page; metric bullets",
            "  are the publisher's structured call summary, and the license/section",
            "  fields record that so they are not confused with verbatim speaker text.",
            "- Every row is `requires_human_audit: true`; labels are manual contract",
            "  labels, not model outputs.",
            "",
            "## Output Files",
            "",
            "- `spans/all.jsonl`: all collected rows.",
            "- `repaired_datasets/citation_verifier/{train,dev,test,all}.jsonl`: baseline-compatible splits.",
            "- `sources.json`: source metadata and fetch hashes.",
            "- `failures.json`: scouting, fetch, and anchor failures.",
            "- `sanity_check.json`: schema/target check results.",
            "- `manifest.json`: reproducibility metadata.",
            "",
            "## Decision",
            "",
            "This pack, combined with `real_citation_spans_v0.1`, is the candidate input",
            "for `citation_verifier_repair_v0.3`. Before training: run the human/Claude",
            "label audit pass over all rows (every row is flagged `requires_human_audit`)",
            "and run a CPU probe under summary recording. Do not start GPU fine-tuning",
            "from this pack alone.",
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
    sanity = run_sanity_checks(rows)

    by_split: dict[str, list[dict[str, Any]]] = {"train": [], "dev": [], "test": []}
    for row in rows:
        by_split.setdefault(row["split"], []).append(row)

    write_jsonl(out_dir / "spans" / "all.jsonl", rows)
    for split, split_rows in by_split.items():
        write_jsonl(out_dir / "repaired_datasets" / "citation_verifier" / f"{split}.jsonl", split_rows)
    write_jsonl(out_dir / "repaired_datasets" / "citation_verifier" / "all.jsonl", rows)
    write_json(out_dir / "sources.json", {"sources": source_audits})
    write_json(out_dir / "failures.json", {"failures": failures})
    write_json(out_dir / "sanity_check.json", sanity)

    manifest = {
        "collection_id": COLLECTION_ID,
        "created_at": now_utc(),
        "as_of": COLLECTION_AS_OF,
        "row_count": len(rows),
        "case_count": len(CASES),
        "failure_count": len(failures),
        "source_count": len(SOURCES),
        "sanity_passed": sanity["passed"],
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
    write_report(out_dir, rows, source_audits, failures, sanity)

    print(json.dumps({"manifest": manifest, "sanity": sanity}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
