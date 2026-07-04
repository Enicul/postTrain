#!/usr/bin/env python3
"""Authored SpanCase list for citation_train_expansion_v1.

Every case is anchored to a REAL span verified present in the fetched filing
(worksheet-derived, 2026-07-04). Labels follow the eval-v1 five-way contract and
the audit-pinned conventions:
  C1 contradiction precedence: any conflicting element -> contradicts (not partial)
  C2 period binding: a period claim the span cannot establish is not verified
  C3 materially weakens: a stale/lower span that undercuts the claim -> contradicts

`must_contain` lists the label-critical facts that MUST appear in the matched span
(F-2026-07-02-002 guard). `anchor` must match exactly ONE block (uniqueness guard).
Splits are train/dev ONLY (never test) and always keyword-passed.

Label balance target: verified_support / partial_support / insufficient /
contradicts spread across sources so the verdict head sees every class.
"""

from citation_train_expansion_v1_cases_impl import SpanCase  # dataclass shim

CASES: list[SpanCase] = []


def C(**kw):
    CASES.append(SpanCase(**kw))


# ============================ NVDA 10-K FY2026 ============================
C(case_key="x_nvda10k_custconc_vs", source_key="nvda_10k", split="train",
  anchor="sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14%",
  claim="For fiscal year 2026, one NVIDIA direct customer represented 22% of total revenue and another represented 14%, both primarily attributable to the Compute & Networking segment.",
  support_type="verified_support", claim_scope="composite", section="Notes / concentration of revenue",
  must_contain=("22%", "14%", "Compute"),
  rationale="The span states both customer concentrations and their Compute & Networking attribution.")
C(case_key="x_nvda10k_custconc_con", source_key="nvda_10k", split="train",
  anchor="sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14%",
  claim="For fiscal year 2026, NVIDIA's largest direct customer represented 22% of total revenue, primarily attributable to the Gaming segment.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / concentration of revenue",
  must_contain=("22%", "Compute"),
  rationale="The span attributes the concentration to Compute & Networking, not Gaming (C1).")
C(case_key="x_nvda10k_gaming_vs", source_key="nvda_10k", split="train",
  anchor="Gaming revenue for fiscal year 2026 was up 41% from a year ago, driven by strong Blackwell demand",
  claim="NVIDIA Gaming revenue for fiscal year 2026 was up 41% year over year, driven by strong Blackwell demand, and the company expects supply constraints to be a headwind to Gaming in the first quarter of fiscal 2027.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("41%", "Blackwell", "supply constraints"),
  rationale="The span states the 41% Gaming growth, the Blackwell driver, and the fiscal-2027 supply-constraint headwind.")
C(case_key="x_nvda10k_gaming_part", source_key="nvda_10k", split="dev",
  anchor="Gaming revenue for fiscal year 2026 was up 41% from a year ago, driven by strong Blackwell demand",
  claim="NVIDIA Gaming revenue for fiscal year 2026 rose 41% on Blackwell demand, and Gaming gross margin expanded year over year.",
  support_type="partial_support", claim_scope="composite", section="MD&A",
  must_contain=("41%", "Blackwell"),
  rationale="The span supports the 41% Blackwell-driven growth but says nothing about Gaming gross margin.")
C(case_key="x_nvda10k_buyback_vs", source_key="nvda_10k", split="train",
  anchor="In fiscal year 2026, we repurchased 282 million shares of our common stock for $40.4 billion",
  claim="In fiscal year 2026, NVIDIA repurchased 282 million shares for $40.4 billion, and as of January 25, 2026 was authorized to repurchase up to $58.5 billion more.",
  support_type="verified_support", claim_scope="composite", section="Repurchases",
  must_contain=("282 million", "40.4 billion", "58.5 billion"),
  rationale="The span states the shares and dollars repurchased and the remaining $58.5 billion authorization.")
C(case_key="x_nvda10k_buyback_con", source_key="nvda_10k", split="dev",
  anchor="In fiscal year 2026, we repurchased 282 million shares of our common stock for $40.4 billion",
  claim="NVIDIA did not repurchase any common stock during fiscal year 2026.",
  support_type="contradicts", claim_scope="single_fact", section="Repurchases",
  must_contain=("282 million", "40.4 billion"),
  rationale="The span states NVIDIA repurchased 282 million shares for $40.4 billion (C1).")
C(case_key="x_nvda10k_prior_insuff", source_key="nvda_10k", split="train",
  anchor="For fiscal year 2024, sales to one direct customer represented 13% of total revenue",
  claim="For fiscal year 2026, NVIDIA's single largest customer represented 22% of total revenue.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / concentration of revenue",
  must_contain=("fiscal year 2024", "13%"),
  rationale="This span reports the fiscal 2024 concentration only; it cannot establish the fiscal 2026 figure (C2).")

# ============================ NVDA 10-Q Q1 FY2027 ============================
C(case_key="x_nvda10q_geo_vs", source_key="nvda_10q", split="train",
  anchor="Revenue from sales to customers headquartered outside of the United States accounted for 22% of total revenue for the first quarter of fiscal year 2027",
  claim="Sales to customers headquartered outside the United States were 22% of NVIDIA's total revenue in the first quarter of fiscal year 2027, down from 42% in the prior-year quarter.",
  support_type="verified_support", claim_scope="composite", section="Notes / revenue disaggregation",
  must_contain=("22%", "42%", "first quarter of fiscal year 2027"),
  rationale="The span states both the 22% current-quarter and 42% prior-year-quarter shares.")
C(case_key="x_nvda10q_geo_con", source_key="nvda_10q", split="train",
  anchor="Revenue from sales to customers headquartered outside of the United States accounted for 22% of total revenue for the first quarter of fiscal year 2027",
  claim="Outside-U.S. customers accounted for 42% of NVIDIA's total revenue in the first quarter of fiscal year 2027.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / revenue disaggregation",
  must_contain=("22%", "42%"),
  rationale="42% is the prior-year quarter; the fiscal 2027 first-quarter figure is 22% (C1).")
C(case_key="x_nvda10q_div_vs", source_key="nvda_10q", split="train",
  anchor="On May 18, 2026, we increased our quarterly cash dividend from $ 0.01 per share to $ 0.25 per share",
  claim="On May 18, 2026, NVIDIA increased its quarterly cash dividend from $0.01 to $0.25 per share, payable June 26, 2026.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("May 18, 2026", "0.25", "June 26, 2026"),
  rationale="The span states the dividend increase to $0.25 and the June 26, 2026 payment date.")
C(case_key="x_nvda10q_div_part", source_key="nvda_10q", split="dev",
  anchor="On May 18, 2026, we increased our quarterly cash dividend from $ 0.01 per share to $ 0.25 per share",
  claim="NVIDIA raised its quarterly dividend to $0.25 per share on May 18, 2026, a 25-fold increase reflecting confidence in fiscal 2027 free cash flow guidance.",
  support_type="partial_support", claim_scope="composite", section="Notes / equity",
  must_contain=("0.25", "0.01"),
  rationale="The span supports the raise to $0.25 from $0.01 but says nothing about free-cash-flow guidance.")
C(case_key="x_nvda10q_cust3_vs", source_key="nvda_10q", split="train",
  anchor="three direct customers represented 21 %, 17 %, and 16 % of total revenue, all of which was primarily attributable to the Compute Networking segment",
  claim="In the first quarter of fiscal year 2027, three NVIDIA direct customers represented 21%, 17%, and 16% of total revenue, primarily attributable to the Compute & Networking segment.",
  support_type="verified_support", claim_scope="composite", section="Notes / concentration of revenue",
  must_contain=("21", "17", "16", "Compute"),
  rationale="The span states the 21/17/16% concentrations and the Compute & Networking attribution.")
C(case_key="x_nvda10q_invcommit_insuff", source_key="nvda_10q", split="dev",
  anchor="Total Investment commitments were $ 27 billion as of April 26, 2026",
  claim="NVIDIA's total revenue grew 20% sequentially in the first quarter of fiscal year 2027.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / commitments",
  must_contain=("27 billion", "April 26, 2026"),
  rationale="The span covers investment commitments, not revenue growth (C2).")

# ============================ AMD 10-K 2025 ============================
C(case_key="x_amd10k_dc_vs", source_key="amd_10k", split="train",
  anchor="Data Center net revenue of $16.6 billion in 2025 increased by 32%, compared to net revenue of $12.6 billion in 2024",
  claim="AMD Data Center net revenue was $16.6 billion in 2025, up 32% from $12.6 billion in 2024, driven primarily by demand for EPYC processors and Instinct GPU accelerators.",
  support_type="verified_support", claim_scope="composite", section="MD&A / segment results",
  must_contain=("16.6 billion", "32%", "EPYC", "Instinct"),
  rationale="The span states the segment revenue, growth, base, and the EPYC/Instinct demand drivers.")
C(case_key="x_amd10k_client_vs", source_key="amd_10k", split="train",
  anchor="Client net revenue of $10.6 billion in 2025 increased by 51%, compared to net revenue of $7.1 billion in 2024",
  claim="AMD Client net revenue was $10.6 billion in 2025, up 51% from $7.1 billion in 2024, driven by a 31% increase in processor unit shipments and a 15% increase in average selling price.",
  support_type="verified_support", claim_scope="composite", section="MD&A / segment results",
  must_contain=("10.6 billion", "51%", "31%", "15%"),
  rationale="The span states the Client revenue, growth, and both the 31% volume and 15% ASP drivers.")
C(case_key="x_amd10k_embedded_con", source_key="amd_10k", split="train",
  anchor="Embedded net revenue of $3.5 billion in 2025 decreased by 3%, compared to net revenue of $3.6 billion in 2024",
  claim="AMD's Embedded segment net revenue grew in 2025 compared to 2024.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A / segment results",
  must_contain=("3.5 billion", "decreased by 3%"),
  rationale="The span states Embedded net revenue decreased 3% to $3.5 billion (C1).")
C(case_key="x_amd10k_gm_vs", source_key="amd_10k", split="dev",
  anchor="Gross margin of 50% increased by 1% compared to 49% in 2024",
  claim="AMD's 2025 gross margin was 50%, up one point from 49% in 2024, partially offset by roughly $440 million of inventory and related charges tied to the U.S. export control on Instinct MI308 GPUs.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("50%", "49%", "440 million", "MI308"),
  rationale="The span states the 50% gross margin, the 49% comparison, and the ~$440 million MI308 export-control charge.")
C(case_key="x_amd10k_buyback_vs", source_key="amd_10k", split="train",
  anchor="In 2025, we returned a total of $1.3 billion to shareholders through the repurchase of 12.4 million shares",
  claim="In 2025 AMD returned $1.3 billion to shareholders by repurchasing 12.4 million shares, with $9.4 billion remaining under the program as of December 27, 2025.",
  support_type="verified_support", claim_scope="composite", section="Repurchases",
  must_contain=("1.3 billion", "12.4 million", "9.4 billion"),
  rationale="The span states the $1.3 billion returned, 12.4 million shares, and the $9.4 billion remaining authorization.")
C(case_key="x_amd10k_buyback_part", source_key="amd_10k", split="dev",
  anchor="In 2025, we returned a total of $1.3 billion to shareholders through the repurchase of 12.4 million shares",
  claim="AMD repurchased 12.4 million shares for $1.3 billion in 2025 and also paid a quarterly cash dividend.",
  support_type="partial_support", claim_scope="composite", section="Repurchases",
  must_contain=("1.3 billion", "12.4 million"),
  rationale="The span supports the repurchase but says nothing about a dividend.")
C(case_key="x_amd10k_comp_insuff", source_key="amd_10k", split="train",
  anchor="We depend on a small number of customers for a substantial portion of our business",
  claim="AMD's Data Center segment net revenue increased 32% in 2025.",
  support_type="insufficient", claim_scope="single_fact", section="Risk Factors",
  must_contain=("small number of customers",),
  rationale="This customer-concentration risk span does not address Data Center revenue growth (C2).")

# ============================ AMD 10-Q Q1 2026 ============================
C(case_key="x_amd10q_dc_vs", source_key="amd_10q", split="train",
  anchor="Data Center net revenue of $5.8 billion for the three months ended March 28, 2026 increased by 57%",
  claim="AMD Data Center net revenue was $5.8 billion for the three months ended March 28, 2026, up 57% year over year, driven by 5th-gen EPYC and Instinct MI350 GPUs.",
  support_type="verified_support", claim_scope="composite", section="MD&A / segment results",
  must_contain=("5.8 billion", "57%", "MI350"),
  rationale="The span states the segment revenue, 57% growth, and the EPYC/MI350 drivers.")
C(case_key="x_amd10q_dc_con", source_key="amd_10q", split="train",
  anchor="Data Center net revenue of $5.8 billion for the three months ended March 28, 2026 increased by 57%",
  claim="AMD Data Center net revenue declined year over year in the first quarter of 2026.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A / segment results",
  must_contain=("5.8 billion", "increased by 57%"),
  rationale="The span states Data Center revenue increased 57% (C1).")
C(case_key="x_amd10q_gaming_vs", source_key="amd_10q", split="dev",
  anchor="Gaming net revenue of $720 million for the three months ended March 28, 2026 increased by 11%",
  claim="AMD Gaming net revenue was $720 million for the three months ended March 28, 2026, up 11% year over year, driven by higher Radeon demand.",
  support_type="verified_support", claim_scope="composite", section="MD&A / segment results",
  must_contain=("720 million", "11%", "Radeon"),
  rationale="The span states the $720 million Gaming revenue, 11% growth, and the Radeon driver.")
C(case_key="x_amd10q_buyback_vs", source_key="amd_10q", split="train",
  anchor="the Company repurchased 1.1 million shares of its common stock under the Repurchase Program for $ 221 million",
  claim="During the three months ended March 28, 2026 AMD repurchased 1.1 million shares for $221 million, leaving $9.2 billion available under its repurchase program.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("1.1 million", "221 million", "9.2 billion"),
  rationale="The span states the shares, dollars, and the $9.2 billion remaining authorization.")

# ============================ MU 10-Q FQ3 2026 ============================
C(case_key="x_mu10q_div_vs", source_key="mu_10q", split="train",
  anchor="On June 24, 2026, our Board of Directors declared a quarterly dividend of $ 0.15 per share, payable in cash on July 21, 2026",
  claim="On June 24, 2026, Micron's Board declared a quarterly dividend of $0.15 per share, payable in cash on July 21, 2026.",
  support_type="verified_support", claim_scope="single_fact", section="Notes / equity",
  must_contain=("June 24, 2026", "0.15", "July 21, 2026"),
  rationale="The span states the declaration date, amount, and payment date.")
C(case_key="x_mu10q_div_con", source_key="mu_10q", split="train",
  anchor="We declared and paid dividends of $ 0.115 per share in the first and second quarters of 2026 and $ 0.15 per share in the third quarter of 2026",
  claim="Micron's dividend was $0.15 per share in each of the first, second, and third quarters of fiscal 2026.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / equity",
  must_contain=("0.115", "0.15", "third quarter"),
  rationale="The span states the first and second quarter dividends were $0.115, not $0.15 (C1).")
C(case_key="x_mu10q_div_part", source_key="mu_10q", split="dev",
  anchor="We declared and paid dividends of $ 0.115 per share in the first and second quarters of 2026 and $ 0.15 per share in the third quarter of 2026",
  claim="Micron paid a $0.115 per-share dividend in the first two quarters of fiscal 2026 and raised it to $0.15 in the third quarter, its first dividend increase since 2024.",
  support_type="partial_support", claim_scope="composite", section="Notes / equity",
  must_contain=("0.115", "0.15"),
  rationale="The span supports the $0.115-to-$0.15 progression but not the 'first increase since 2024' claim.")

# ============================ MU 10-K FY2025 ============================
C(case_key="x_mu10k_nand_vs", source_key="mu_10k", split="train",
  anchor="Total reported NAND revenue was $8.50 billion in 2025, $7.23 billion in 2024, and $4.21 billion in 2023",
  claim="Micron's total reported NAND revenue was $8.50 billion in fiscal 2025, up from $7.23 billion in fiscal 2024.",
  support_type="verified_support", claim_scope="composite", section="Business / segment revenue",
  must_contain=("8.50 billion", "7.23 billion"),
  rationale="The span states NAND revenue of $8.50 billion in 2025 and $7.23 billion in 2024.")
C(case_key="x_mu10k_cmbu_vs", source_key="mu_10k", split="train",
  anchor="Total reported CMBU revenue was $13.52 billion in 2025, $3.79 billion in 2024, and $1.87 billion in 2023",
  claim="Micron's Compute and Memory Business Unit reported $13.52 billion of revenue in fiscal 2025, more than tripling from $3.79 billion in fiscal 2024.",
  support_type="verified_support", claim_scope="composite", section="Business / segment revenue",
  must_contain=("13.52 billion", "3.79 billion"),
  rationale="The span states CMBU revenue of $13.52 billion in 2025 versus $3.79 billion in 2024.")
C(case_key="x_mu10k_cmbu_con", source_key="mu_10k", split="dev",
  anchor="Total reported CMBU revenue was $13.52 billion in 2025, $3.79 billion in 2024, and $1.87 billion in 2023",
  claim="Micron's CMBU revenue declined from fiscal 2024 to fiscal 2025.",
  support_type="contradicts", claim_scope="single_fact", section="Business / segment revenue",
  must_contain=("13.52 billion", "3.79 billion"),
  rationale="The span shows CMBU revenue rose from $3.79 billion to $13.52 billion (C1).")
C(case_key="x_mu10k_ny_insuff", source_key="mu_10k", split="train",
  anchor="construction of a leading-edge DRAM memory manufacturing site, consisting of up to four fabs to be built over the next 20-plus years, in Clay, New York",
  claim="Micron's total reported CDBU revenue was $7.23 billion in fiscal 2025.",
  support_type="insufficient", claim_scope="single_fact", section="Business",
  must_contain=("Clay, New York", "four fabs"),
  rationale="This span describes the New York fab plan and does not state CDBU revenue (C2).")

# ============================ META 10-Q Q1 2026 ============================
C(case_key="x_meta10q_rev_vs", source_key="meta_10q", split="train",
  anchor="Total revenue for the first quarter of 2026 was $56.31 billion, an increase of 33% compared to the first quarter of 2025",
  claim="Meta's total revenue for the first quarter of 2026 was $56.31 billion, up 33% year over year, driven by an increase in advertising revenue.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("56.31 billion", "33%", "advertising"),
  rationale="The span states the $56.31 billion revenue, 33% growth, and the advertising driver.")
C(case_key="x_meta10q_rev_con", source_key="meta_10q", split="train",
  anchor="Total revenue for the first quarter of 2026 was $56.31 billion, an increase of 33% compared to the first quarter of 2025",
  claim="Meta's first-quarter 2026 revenue rose 33% year over year on a constant-currency basis.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("33%", "constant currency", "29%"),
  rationale="The span states constant-currency revenue would have increased 29%; the 33% figure is as-reported (C1).")
C(case_key="x_meta10q_rev_part", source_key="meta_10q", split="dev",
  anchor="Total revenue for the first quarter of 2026 was $56.31 billion, an increase of 33% compared to the first quarter of 2025",
  claim="Meta's Q1 2026 revenue was $56.31 billion, up 33%, and its operating margin expanded year over year.",
  support_type="partial_support", claim_scope="composite", section="MD&A",
  must_contain=("56.31 billion", "33%"),
  rationale="The span supports the revenue and growth but says nothing about operating margin.")
C(case_key="x_meta10q_ni_vs", source_key="meta_10q", split="train",
  anchor="Net income was $26.77 billion, with diluted earnings per share (EPS) of $10.44 for the three months ended March 31, 2026",
  claim="Meta reported net income of $26.77 billion and diluted EPS of $10.44 for the three months ended March 31, 2026.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("26.77 billion", "10.44"),
  rationale="The span states net income of $26.77 billion and diluted EPS of $10.44.")
C(case_key="x_meta10q_camt_vs", source_key="meta_10q", split="dev",
  anchor="we recognized an $ 8.03 billion discrete income tax benefit during the first quarter of 2026, which partially offsets the $ 15.93 billion discrete charge",
  claim="In the first quarter of 2026 Meta recognized an $8.03 billion discrete income tax benefit that partially offset a $15.93 billion discrete charge taken in the third quarter of 2025.",
  support_type="verified_support", claim_scope="composite", section="Notes / income taxes",
  must_contain=("8.03 billion", "15.93 billion"),
  rationale="The span states both the $8.03 billion benefit and the $15.93 billion offsetting charge.")
C(case_key="x_meta10q_buyback_con", source_key="meta_10q", split="train",
  anchor="We did not repurchase any shares of Class A common stock during the three months ended March 31, 2026",
  claim="Meta repurchased Class A common stock during the three months ended March 31, 2026.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / equity",
  must_contain=("did not repurchase", "March 31, 2026"),
  rationale="The span states Meta did not repurchase any Class A stock in the quarter (C1).")

# ============================ META 10-K 2025 ============================
C(case_key="x_meta10k_ipo_insuff", source_key="meta_10k", split="dev",
  anchor="shares of our Class A common stock were sold in our initial public offering in May 2012 at a price of $38.00 per share",
  claim="Meta's Reality Labs segment reported an operating loss in fiscal 2025.",
  support_type="insufficient", claim_scope="single_fact", section="Risk Factors",
  must_contain=("May 2012", "38.00"),
  rationale="This span covers the 2012 IPO price and stock-price range; it says nothing about Reality Labs (C2).")

# ============================ GOOGL 10-Q Q1 2026 ============================
C(case_key="x_googl10q_backlog_vs", source_key="googl_10q", split="train",
  anchor="As of March 31, 2026, we had $ 467.6 billion of remaining performance obligations ( revenue backlog ), of which $ 462.3 billion related to Google Cloud",
  claim="As of March 31, 2026, Alphabet had $467.6 billion of remaining performance obligations, of which $462.3 billion related to Google Cloud.",
  support_type="verified_support", claim_scope="composite", section="Notes / revenue",
  must_contain=("467.6 billion", "462.3 billion", "Google Cloud"),
  rationale="The span states the $467.6 billion total backlog and the $462.3 billion Google Cloud portion.")
C(case_key="x_googl10q_backlog_con", source_key="googl_10q", split="train",
  anchor="As of March 31, 2026, we had $ 467.6 billion of remaining performance obligations ( revenue backlog ), of which $ 462.3 billion related to Google Cloud",
  claim="As of March 31, 2026, essentially all of Alphabet's $467.6 billion revenue backlog was outside Google Cloud.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / revenue",
  must_contain=("467.6 billion", "462.3 billion", "Google Cloud"),
  rationale="The span states $462.3 billion of the $467.6 billion backlog related to Google Cloud (C1).")
C(case_key="x_googl10q_div_vs", source_key="googl_10q_b", split="train",
  anchor="In April 2026, the company's Board of Directors declared a quarterly cash dividend of $ 0.22 per share, representing a 5 % increase from the previous quarterly dividend of $ 0.21 per share",
  claim="In April 2026 Alphabet declared a quarterly cash dividend of $0.22 per share, a 5% increase from $0.21, payable June 15, 2026.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("0.22", "5 %", "June 15, 2026"),
  rationale="The span states the $0.22 dividend, the 5% increase, and the June 15, 2026 payment date.")
C(case_key="x_googl10q_backstop_vs", source_key="googl_10q_b", split="dev",
  anchor="we entered into additional agreements with certain third parties to backstop certain obligations relating to third-party data centers that we expect to be accounted for as credit derivatives with notional amounts totaling approximately $ 15.3 billion",
  claim="In April 2026 Alphabet entered agreements to backstop third-party data-center obligations, expected to be accounted for as credit derivatives, with notional amounts totaling about $15.3 billion.",
  support_type="verified_support", claim_scope="composite", section="Notes / commitments",
  must_contain=("backstop", "15.3 billion", "credit derivatives"),
  rationale="The span states the backstop arrangements, the credit-derivative treatment, and the ~$15.3 billion notional.")
C(case_key="x_googl10q_buyback_con", source_key="googl_10q_b", split="train",
  anchor="In the three months ended March 31, 2026, there were no repurchases of the company's Class A or Class C shares",
  claim="Alphabet repurchased Class A and Class C shares during the three months ended March 31, 2026.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / equity",
  must_contain=("no repurchases", "March 31, 2026"),
  rationale="The span states there were no repurchases in the quarter (C1).")

# ============================ GOOGL 10-K 2025 ============================
C(case_key="x_googl10k_adshare_vs", source_key="googl_10k", split="train",
  anchor="We generated more than 70% of total revenues from online advertising in 2025",
  claim="Alphabet generated more than 70% of its total revenues from online advertising in 2025.",
  support_type="verified_support", claim_scope="single_fact", section="Business",
  must_contain=("more than 70%", "advertising"),
  rationale="The span directly states the >70% advertising revenue share for 2025.")
C(case_key="x_googl10k_buyback_insuff", source_key="googl_10k", split="dev",
  anchor="In April 2024, the company's Board of Directors authorized a $70.0 billion share repurchase program for its Class A and Class C shares",
  claim="Alphabet declared its first-ever quarterly cash dividend in 2024.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / equity",
  must_contain=("70.0 billion", "repurchase"),
  rationale="The span covers the buyback authorization and says nothing about dividends (C2).")

# ============================ AMZN 10-Q Q1 2026 ============================
C(case_key="x_amzn10q_sales_vs", source_key="amzn_10q", split="train",
  anchor="Sales increased 17% in Q1 2026 compared to the comparable prior year period",
  claim="Amazon's net sales increased 17% in the first quarter of 2026 versus the prior-year period.",
  support_type="verified_support", claim_scope="single_fact", section="MD&A",
  must_contain=("increased 17%", "Q1 2026"),
  rationale="The span states net sales increased 17% in Q1 2026.")
C(case_key="x_amzn10q_backlog_vs", source_key="amzn_10q", split="train",
  anchor="those commitments not yet recognized were approximately $ 364 billion as of March 31, 2026. The weighted-average remaining life of our long-term contracts is 5.5 years",
  claim="As of March 31, 2026, Amazon's unrecognized performance obligations (primarily AWS) were approximately $364 billion, with a weighted-average remaining contract life of 5.5 years.",
  support_type="verified_support", claim_scope="composite", section="Notes / revenue",
  must_contain=("364 billion", "5.5 years"),
  rationale="The span states the ~$364 billion of unrecognized obligations and the 5.5-year weighted-average life.")
C(case_key="x_amzn10q_backlog_part", source_key="amzn_10q", split="dev",
  anchor="those commitments not yet recognized were approximately $ 364 billion as of March 31, 2026. The weighted-average remaining life of our long-term contracts is 5.5 years",
  claim="Amazon's ~$364 billion of unrecognized commitments as of March 31, 2026 excludes a new multi-year deal with Anthropic worth over $100 billion.",
  support_type="partial_support", claim_scope="composite", section="Notes / revenue",
  must_contain=("364 billion",),
  rationale="The span supports the $364 billion figure but says nothing about an Anthropic deal or its exclusion.")
C(case_key="x_amzn10q_buyback_con", source_key="amzn_10q", split="train",
  anchor="There were no repurchases of our common stock during the three months ended March 31, 2025 or 2026. As of March 31, 2026, we have $ 6.1 billion remaining under the repurchase program",
  claim="Amazon repurchased common stock during the three months ended March 31, 2026.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / equity",
  must_contain=("no repurchases", "6.1 billion"),
  rationale="The span states there were no repurchases in the quarter (C1).")

# ============================ AMZN 10-K 2025 ============================
C(case_key="x_amzn10k_aws_vs", source_key="amzn_10k", split="train",
  anchor="AWS sales increased 20% in 2025, compared to the prior year",
  claim="Amazon's AWS sales increased 20% in 2025 compared with the prior year, primarily reflecting increased customer usage.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("AWS sales increased 20%", "customer usage"),
  rationale="The span states the 20% AWS growth and the increased-usage driver.")
C(case_key="x_amzn10k_na_con", source_key="amzn_10k", split="train",
  anchor="North America sales increased 10% in 2025, compared to the prior year",
  claim="Amazon's North America sales grew faster than its International sales in 2025.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("North America sales increased 10%",),
  rationale="North America grew 10% while International grew 13%, so North America did not grow faster (C1); International growth is stated in an adjacent span.")
C(case_key="x_amzn10k_guide_vs", source_key="amzn_10k", split="dev",
  anchor="Operating income is expected to be between $16.5 billion and $21.5 billion, compared with $18.4 billion in first quarter 2025",
  claim="Amazon guided first-quarter operating income to a range of $16.5 billion to $21.5 billion, versus $18.4 billion a year earlier, including about $1 billion of higher year-over-year Amazon Leo costs.",
  support_type="verified_support", claim_scope="composite", section="MD&A / guidance",
  must_contain=("16.5 billion", "21.5 billion", "Leo"),
  rationale="The span states the operating-income guidance range, the prior-year base, and the ~$1 billion Leo cost headwind.")
C(case_key="x_amzn10k_guide_part", source_key="amzn_10k", split="train",
  anchor="Net sales are expected to be between $173.5 billion and $178.5 billion, or to grow between 11% and 15% compared with first quarter 2025",
  claim="Amazon guided net sales to $173.5-$178.5 billion, or 11-15% growth, and expects operating margin to expand year over year.",
  support_type="partial_support", claim_scope="composite", section="MD&A / guidance",
  must_contain=("173.5 billion", "178.5 billion", "11%"),
  rationale="The span supports the net-sales guidance but says nothing about operating margin.")

# ============================ AVGO 10-Q FQ2 2026 ============================
C(case_key="x_avgo10q_div_vs", source_key="avgo_10q", split="train",
  anchor="On June 2, 2026 , our Board of Directors declared a quarterly cash dividend of $ 0.65 per share",
  claim="On June 2, 2026, Broadcom's Board declared a quarterly cash dividend of $0.65 per share, payable June 30, 2026.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("June 2, 2026", "0.65", "June 30, 2026"),
  rationale="The span states the declaration date, the $0.65 amount, and the June 30, 2026 payment date.")
C(case_key="x_avgo10q_div_con", source_key="avgo_10q", split="dev",
  anchor="On June 2, 2026 , our Board of Directors declared a quarterly cash dividend of $ 0.65 per share",
  claim="Broadcom's quarterly cash dividend declared on June 2, 2026 was $0.55 per share.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / equity",
  must_contain=("0.65",),
  rationale="The span states the dividend was $0.65 per share, not $0.55 (C1).")
C(case_key="x_avgo10q_rpo_insuff", source_key="avgo_10q", split="train",
  anchor="We expect approximately 30 % of this amount to be recognized as revenue over the next 12 months",
  claim="Broadcom's AI semiconductor revenue was $10.8 billion in fiscal Q2 2026.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / revenue",
  must_contain=("30 %", "next 12 months"),
  rationale="The span covers the timing of remaining-performance-obligation recognition, not AI revenue (C2).")

# ============================ AVGO 10-K FY2025 ============================
C(case_key="x_avgo10k_conc_vs", source_key="avgo_10k", split="train",
  anchor="Direct sales to one semiconductor solutions customer, which is a distributor, accounted for 32% and 28% of our net revenue for fiscal years 2025 and 2024",
  claim="Broadcom's direct sales to one distributor customer were 32% of net revenue in fiscal 2025, up from 28% in fiscal 2024.",
  support_type="verified_support", claim_scope="composite", section="Risk Factors / concentration",
  must_contain=("32%", "28%"),
  rationale="The span states the 32% fiscal-2025 and 28% fiscal-2024 concentrations.")
C(case_key="x_avgo10k_gm_vs", source_key="avgo_10k", split="dev",
  anchor="gross margin was 68% and 63% of net revenue for the fiscal years 2025 and 2024, respectively",
  claim="Broadcom's gross margin was 68% of net revenue in fiscal 2025, up from 63% in fiscal 2024.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("68%", "63%"),
  rationale="The span states gross margin of 68% in 2025 and 63% in 2024.")
C(case_key="x_avgo10k_top5_con", source_key="avgo_10k", split="train",
  anchor="aggregate sales to our top five end customers, through all channels, accounted for approximately 40% of our net revenue for each of the fiscal years 2025 and 2024",
  claim="Broadcom's top five end customers accounted for less than 10% of net revenue in fiscal 2025.",
  support_type="contradicts", claim_scope="single_fact", section="Risk Factors / concentration",
  must_contain=("top five end customers", "40%"),
  rationale="The span states the top five end customers were ~40% of net revenue (C1).")


# ============================ MRVL 10-Q Q1 FY2027 ============================
C(case_key="x_mrvl10q_rev_vs", source_key="mrvl_10q", split="train",
  anchor="Our net revenue for the three months ended May 2, 2026 increased by $522.5 million, or 28%, compared to net revenue for the three months ended May 3, 2025. This was primarily due to a 27% increase in sales from the data center end market",
  claim="Marvell's net revenue for the three months ended May 2, 2026 increased $522.5 million, or 28%, year over year, primarily due to a 27% increase in data center end-market sales on strong AI-related demand.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("522.5 million", "28%", "27% increase", "data center"),
  rationale="The span states the $522.5 million / 28% revenue increase and the 27% data-center driver.")
C(case_key="x_mrvl10q_rev_con", source_key="mrvl_10q", split="train",
  anchor="Our net revenue for the three months ended May 2, 2026 increased by $522.5 million, or 28%, compared to net revenue for the three months ended May 3, 2025. This was primarily due to a 27% increase in sales from the data center end market",
  claim="Marvell's net revenue growth in the quarter ended May 2, 2026 was driven primarily by its automotive ethernet product portfolio.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("data center", "automotive ethernet"),
  rationale="The span attributes growth to data center and notes automotive ethernet sales decreased after a divestiture (C1).")
C(case_key="x_mrvl10q_conc_vs", source_key="mrvl_10q", split="dev",
  anchor="Our accounts receivable were concentrated with three customers at May 2, 2026, who represented a total of 75% of gross accounts receivable",
  claim="At May 2, 2026, three customers represented 75% of Marvell's gross accounts receivable, compared with five customers at 72% a year earlier.",
  support_type="verified_support", claim_scope="composite", section="Notes / concentration",
  must_contain=("three customers", "75%", "72%"),
  rationale="The span states the three-customer 75% concentration and the prior-year five-customer 72% figure.")
C(case_key="x_mrvl10q_buyback_vs", source_key="mrvl_10q", split="train",
  anchor="During the three months ended May 2, 2026, the Company repurchased 1.4 million shares of its common stock for $ 200.0 million",
  claim="During the three months ended May 2, 2026, Marvell repurchased 1.4 million shares for $200.0 million.",
  support_type="verified_support", claim_scope="single_fact", section="Notes / equity",
  must_contain=("1.4 million", "200.0 million"),
  rationale="The span states 1.4 million shares repurchased for $200.0 million in the quarter.")
C(case_key="x_mrvl10q_return_part", source_key="mrvl_10q", split="dev",
  anchor="We returned $253.8 million to stockholders in the three months ended May 2, 2026 through $200.0 million in repurchases",
  claim="Marvell returned $253.8 million to stockholders in the quarter ended May 2, 2026 through $200.0 million of buybacks and $53.8 million of dividends, and raised its quarterly dividend.",
  support_type="partial_support", claim_scope="composite", section="MD&A",
  must_contain=("253.8 million", "200.0 million", "53.8 million"),
  rationale="The span supports the $253.8 million total and its split but says nothing about a dividend increase.")

# ============================ MRVL 10-K FY2026 ============================
C(case_key="x_mrvl10k_div_vs", source_key="mrvl_10k", split="train",
  anchor="Our Board of Directors declared quarterly cash dividends of $0.06 per share payable to holders of our common stock in each quarter of fiscal 2026",
  claim="Marvell's Board declared a $0.06 per-share quarterly cash dividend in each quarter of fiscal 2026, and the company paid $205.1 million in total dividends that year.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("0.06 per share", "205.1 million"),
  rationale="The span states the $0.06 quarterly dividend and the $205.1 million paid in fiscal 2026.")
C(case_key="x_mrvl10k_asr_insuff", source_key="mrvl_10k", split="dev",
  anchor="From August 2010, when our Board of Directors initially authorized a stock repurchase program, through January 31, 2026, a total of 348.5 million shares have been repurchased",
  claim="Marvell's net revenue increased 28% in fiscal 2026.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / equity",
  must_contain=("348.5 million", "5.5 billion"),
  rationale="The span covers cumulative buybacks since 2010 and does not address revenue growth (C2).")

# ============================ VRT 10-Q Q1 2026 ============================
C(case_key="x_vrt10q_sales_vs", source_key="vrt_10q", split="train",
  anchor="Net sales were $2,649.5 in the first quarter of 2026, an increase of $613.5, or 30.1%, compared with $2,036.0 in the first quarter of 2025",
  claim="Vertiv's net sales were $2,649.5 million in the first quarter of 2026, up $613.5 million, or 30.1%, from $2,036.0 million a year earlier, driven by higher sales volumes.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("2,649.5", "30.1%", "2,036.0"),
  rationale="The span states the Q1 2026 net sales, the 30.1% increase, and the prior-year base.")
C(case_key="x_vrt10q_emea_con", source_key="vrt_10q", split="train",
  anchor="Europe, Middle East Africa net sales of $321.4 in the first quarter of 2026, decreased by $82.1, or (20.3)%, from the first quarter of 2025",
  claim="Vertiv's EMEA net sales grew in the first quarter of 2026 versus the prior-year quarter.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("321.4", "decreased", "20.3"),
  rationale="The span states EMEA net sales decreased 20.3% (C1).")
C(case_key="x_vrt10q_capex_vs", source_key="vrt_10q", split="dev",
  anchor="We expect to have capital expenditures (including capitalized software) of $425.0 to $525.0 for the full year 2026",
  claim="Vertiv expects full-year 2026 capital expenditures, including capitalized software, of $425.0 million to $525.0 million to support capacity expansion.",
  support_type="verified_support", claim_scope="composite", section="MD&A / liquidity",
  must_contain=("425.0", "525.0", "capital expenditures"),
  rationale="The span states the $425-$525 million full-year 2026 capex guidance and its capacity-expansion purpose.")

# ============================ VRT 10-K 2025 ============================
C(case_key="x_vrt10k_sales_vs", source_key="vrt_10k", split="train",
  anchor="Net sales were $10,229.9 in 2025, an increase of $2,218.1, or 27.7%, compared with $8,011.8 in 2024",
  claim="Vertiv's net sales were $10,229.9 million in 2025, up $2,218.1 million, or 27.7%, from $8,011.8 million in 2024.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("10,229.9", "27.7%", "8,011.8"),
  rationale="The span states the 2025 net sales, the 27.7% increase, and the 2024 base.")
C(case_key="x_vrt10k_americas_part", source_key="vrt_10k", split="dev",
  anchor="Americas net sales of $6,386.3 in 2025 increased $1,885.7, or 41.9%, from 2024",
  claim="Vertiv's Americas net sales rose 41.9% to $6,386.3 million in 2025, and the Americas was the company's fastest-growing region that year.",
  support_type="partial_support", claim_scope="composite", section="MD&A",
  must_contain=("6,386.3", "41.9%"),
  rationale="The span supports the Americas growth but does not compare growth rates across regions.")
C(case_key="x_vrt10k_buyback_vs", source_key="vrt_10k", split="train",
  anchor="The Company did not repurchase any shares under its stock repurchase program in the second half of 2024 or in 2025. As of December 31, 2025, $2.4 billion remains for additional share repurchases",
  claim="Vertiv did not repurchase any shares under its buyback program during 2025, leaving $2.4 billion available as of December 31, 2025.",
  support_type="verified_support", claim_scope="composite", section="Repurchases",
  must_contain=("did not repurchase", "2025", "2.4 billion"),
  rationale="The span states no 2025 repurchases and the $2.4 billion remaining authorization.")

# ============================ LRCX 10-Q Q3 FY2026 ============================
C(case_key="x_lrcx10q_asr_vs", source_key="lrcx_10q", split="train",
  anchor="On March 11, 2026, the Company entered into an accelerated share repurchase agreement (the March 2026 ASR ) with a financial institution to repurchase a total of $ 200.0 million of Common Stock",
  claim="On March 11, 2026, Lam Research entered an accelerated share repurchase agreement to repurchase $200.0 million of common stock, taking initial delivery of about 685 thousand shares.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("March 11, 2026", "200.0 million", "685 thousand"),
  rationale="The span states the ASR date, the $200.0 million size, and the ~685 thousand-share initial delivery.")
C(case_key="x_lrcx10q_buyauth_insuff", source_key="lrcx_10q", split="dev",
  anchor="In May 2024, the Board of Directors authorized the Company to repurchase up to an additional $ 10.00 billion of Common Stock; this authorization supplements the remaining balances from any prior authorizations",
  claim="Lam Research's quarterly dividend was $0.23 per share in fiscal 2026.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / equity",
  must_contain=("May 2024", "10.00 billion"),
  rationale="The span covers a buyback authorization and says nothing about the dividend (C2).")

# ============================ LRCX 10-K FY2025 ============================
C(case_key="x_lrcx10k_intl_vs", source_key="lrcx_10k", split="train",
  anchor="Non-U.S. sales, as reflected in Part II Item 7. Results of Operations of this 2025 Form 10-K, accounted for approximately 93%, 93%, and 91% of total revenue in fiscal years 2025, 2024, and 2023",
  claim="Non-U.S. sales accounted for approximately 93% of Lam Research's total revenue in fiscal 2025, the same share as in fiscal 2024.",
  support_type="verified_support", claim_scope="composite", section="Risk Factors",
  must_contain=("93%", "91%", "fiscal years 2025, 2024, and 2023"),
  rationale="The span states non-U.S. sales were ~93% in both fiscal 2025 and 2024.")
C(case_key="x_lrcx10k_intl_con", source_key="lrcx_10k", split="dev",
  anchor="Non-U.S. sales, as reflected in Part II Item 7. Results of Operations of this 2025 Form 10-K, accounted for approximately 93%, 93%, and 91% of total revenue in fiscal years 2025, 2024, and 2023",
  claim="A majority of Lam Research's fiscal 2025 revenue came from U.S. customers.",
  support_type="contradicts", claim_scope="single_fact", section="Risk Factors",
  must_contain=("93%",),
  rationale="The span states non-U.S. sales were ~93% of revenue, so most revenue was non-U.S. (C1).")
C(case_key="x_lrcx10k_div_vs", source_key="lrcx_10k", split="train",
  anchor="During fiscal year 2025, our quarterly dividend declared was $0.23 per share",
  claim="Lam Research's declared quarterly dividend was $0.23 per share during fiscal year 2025.",
  support_type="verified_support", claim_scope="single_fact", section="Notes / equity",
  must_contain=("0.23 per share", "fiscal year 2025"),
  rationale="The span states the $0.23 quarterly dividend for fiscal 2025.")

# ============================ KLAC 10-Q Q3 FY2026 ============================
C(case_key="x_klac10q_buyauth_vs", source_key="klac_10q", split="train",
  anchor="As of March 31, 2026, an aggregate of $ 10.31 billion of authorization was available for repurchase under the stock repurchase program",
  claim="As of March 31, 2026, KLA had $10.31 billion available for repurchase under its stock repurchase program.",
  support_type="verified_support", claim_scope="single_fact", section="Notes / equity",
  must_contain=("10.31 billion", "March 31, 2026"),
  rationale="The span states the $10.31 billion remaining buyback authorization as of March 31, 2026.")
C(case_key="x_klac10q_split_con", source_key="klac_10q", split="dev",
  anchor="As of March 31, 2026, an aggregate of $ 10.31 billion of authorization was available for repurchase under the stock repurchase program",
  claim="As of March 31, 2026, KLA had less than $1 billion remaining under its stock repurchase program.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / equity",
  must_contain=("10.31 billion",),
  rationale="The span states $10.31 billion remained available, not under $1 billion (C1).")

# ============================ KLAC 10-K FY2025 ============================
C(case_key="x_klac10k_div_vs", source_key="klac_10k", split="train",
  anchor="On August 7, 2025, we announced that our Board of Directors had declared a quarterly cash dividend of $1.90 per share to be paid on September 3, 2025",
  claim="On August 7, 2025, KLA's Board declared a quarterly cash dividend of $1.90 per share, payable September 3, 2025.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("August 7, 2025", "1.90 per share", "September 3, 2025"),
  rationale="The span states the declaration date, the $1.90 amount, and the September 3, 2025 payment date.")

# ============================ ANET 10-Q Q1 2026 ============================
C(case_key="x_anet10q_rev_vs", source_key="anet_10q", split="train",
  anchor="Product revenue increased by $618.8 million, or 36.6% for the three months ended March 31, 2026, compared to the same period in 2025",
  claim="Arista's product revenue increased $618.8 million, or 36.6%, for the three months ended March 31, 2026, and its service revenue increased $85.4 million, or 27.3%.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("618.8 million", "36.6%", "85.4 million", "27.3%"),
  rationale="The span states both the product and service revenue increases and their growth rates.")
C(case_key="x_anet10q_rev_con", source_key="anet_10q", split="train",
  anchor="Product revenue increased by $618.8 million, or 36.6% for the three months ended March 31, 2026, compared to the same period in 2025",
  claim="Arista's product revenue declined in the three months ended March 31, 2026 compared with the prior-year period.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("618.8 million", "increased"),
  rationale="The span states product revenue increased $618.8 million (C1).")
C(case_key="x_anet10q_rd_part", source_key="anet_10q", split="dev",
  anchor="Research and development expenses increased by $77.3 million, or 29.0% for the three months ended March 31, 2026, compared to the same period in 2025",
  claim="Arista's R&D expenses rose $77.3 million, or 29.0%, in the quarter ended March 31, 2026, outpacing its product revenue growth rate.",
  support_type="partial_support", claim_scope="composite", section="MD&A",
  must_contain=("77.3 million", "29.0%"),
  rationale="The span supports the R&D increase but does not itself compare it to product revenue growth.")

# ============================ ANET 10-K 2025 ============================
C(case_key="x_anet10k_conc_vs", source_key="anet_10k", split="train",
  anchor="sales to one end customer represented 16%, 15%, and 21% of our total revenue, and sales to the other end customer represented 26%, 20%, and 18% of our total revenue for the years ended December 31, 2025, 2024, and 2023",
  claim="For the year ended December 31, 2025, sales to one Arista end customer were 16% of total revenue and sales to another end customer were 26%.",
  support_type="verified_support", claim_scope="composite", section="Risk Factors / concentration",
  must_contain=("16%", "26%", "December 31, 2025"),
  rationale="The span states the two 2025 end-customer concentrations of 16% and 26%.")
C(case_key="x_anet10k_conc_con", source_key="anet_10k", split="dev",
  anchor="sales to one end customer represented 16%, 15%, and 21% of our total revenue, and sales to the other end customer represented 26%, 20%, and 18% of our total revenue for the years ended December 31, 2025, 2024, and 2023",
  claim="No single Arista end customer accounted for more than 10% of total revenue in 2025.",
  support_type="contradicts", claim_scope="single_fact", section="Risk Factors / concentration",
  must_contain=("16%", "26%"),
  rationale="The span states two end customers were 16% and 26% of 2025 revenue (C1).")

# ============================ ARM 20-F FY2026 ============================
C(case_key="x_arm20f_rev_vs", source_key="arm_20f", split="train",
  anchor="Total revenue increased $913 million, or 23%, to $4,920 million during the fiscal year ended March 31, 2026, from total revenue of $4,007 million during the fiscal year ended March 31, 2025",
  claim="Arm's total revenue increased $913 million, or 23%, to $4,920 million in the fiscal year ended March 31, 2026, from $4,007 million a year earlier.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("913 million", "23%", "4,920 million", "4,007 million"),
  rationale="The span states the revenue increase, the 23% growth, and both fiscal-year figures.")
C(case_key="x_arm20f_intl_vs", source_key="arm_20f", split="dev",
  anchor="revenue from sales to customers outside of the U.S. accounted for approximately 64% and approximately 57% of total revenue, respectively",
  claim="Revenue from customers outside the U.S. was about 64% of Arm's total revenue in fiscal 2026, up from about 57% in fiscal 2025.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("64%", "57%"),
  rationale="The span states outside-U.S. revenue was ~64% in fiscal 2026 and ~57% in fiscal 2025.")
C(case_key="x_arm20f_royalty_con", source_key="arm_20f", split="train",
  anchor="Royalty revenue increased $445 million, or 21%, during the fiscal year ended March 31, 2026 as compared to the fiscal",
  claim="Arm's royalty revenue declined during the fiscal year ended March 31, 2026.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("Royalty revenue increased", "445 million"),
  rationale="The span states royalty revenue increased $445 million, or 21% (C1).")

# ============================ AMAT 10-Q Q2 FY2026 ============================
C(case_key="x_amat10q_conc_vs", source_key="amat_10q", split="train",
  anchor="Two customers accounted for approximately 21 % and 15 %, respectively, of our revenue for the six months ended April 26, 2026",
  claim="Two customers accounted for approximately 21% and 15% of Applied Materials' revenue for the six months ended April 26, 2026.",
  support_type="verified_support", claim_scope="composite", section="Notes / concentration",
  must_contain=("21 %", "15 %", "April 26, 2026"),
  rationale="The span states the two customers at ~21% and ~15% of revenue for the period.")
C(case_key="x_amat10q_buyauth_vs", source_key="amat_10q", split="dev",
  anchor="As of April 26, 2026, approximately $ 13.2 billion remained available for future stock repurchases under the repurchase program",
  claim="As of April 26, 2026, Applied Materials had approximately $13.2 billion available for future stock repurchases.",
  support_type="verified_support", claim_scope="single_fact", section="Notes / equity",
  must_contain=("13.2 billion", "April 26, 2026"),
  rationale="The span states the ~$13.2 billion remaining repurchase authorization.")

# ============================ AMAT 10-K FY2025 ============================
C(case_key="x_amat10k_conc_vs", source_key="amat_10k", split="train",
  anchor="During fiscal 2025, two customers accounted for approximately 19% and 15%, respectively, of our net revenue",
  claim="During fiscal 2025, two customers accounted for approximately 19% and 15% of Applied Materials' net revenue.",
  support_type="verified_support", claim_scope="composite", section="Notes / concentration",
  must_contain=("19%", "15%", "fiscal 2025"),
  rationale="The span states the two customers at ~19% and ~15% of fiscal 2025 net revenue.")
C(case_key="x_amat10k_restr_insuff", source_key="amat_10k", split="dev",
  anchor="we recognized $181 million of restructuring charges consisting primarily of severance",
  claim="Applied Materials' net revenue grew year over year in fiscal 2025.",
  support_type="insufficient", claim_scope="single_fact", section="MD&A",
  must_contain=("181 million", "restructuring"),
  rationale="The span covers a restructuring charge and does not state revenue growth (C2).")

# ============================ SMCI 10-K FY2025 ============================
C(case_key="x_smci10k_sales_vs", source_key="smci_10k", split="train",
  anchor="Net sales increased by 46.6% in fiscal year 2025 as compared to fiscal year 2024. driven by an increase in demand from customers for GPU servers, HPC and rack-scale solutions",
  claim="Super Micro's net sales increased 46.6% in fiscal 2025 versus fiscal 2024, driven by higher demand for GPU servers, HPC, and rack-scale solutions.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("46.6%", "GPU servers", "rack-scale"),
  rationale="The span states the 46.6% net-sales growth and the GPU/HPC/rack-scale demand drivers.")
C(case_key="x_smci10k_conc_vs", source_key="smci_10k", split="dev",
  anchor="Four customers each accounted for 10% or more of our net sales in fiscal year 2025 and one single customer accounted for 10% or more of net sales in fiscal year 2024",
  claim="Four customers each accounted for 10% or more of Super Micro's net sales in fiscal 2025, up from one such customer in fiscal 2024.",
  support_type="verified_support", claim_scope="composite", section="Business / concentration",
  must_contain=("Four customers", "fiscal year 2025", "one single customer"),
  rationale="The span states four 10%+ customers in fiscal 2025 versus one in fiscal 2024.")
C(case_key="x_smci10k_conc_con", source_key="smci_10k", split="train",
  anchor="Four customers each accounted for 10% or more of our net sales in fiscal year 2025 and one single customer accounted for 10% or more of net sales in fiscal year 2024",
  claim="No customer accounted for 10% or more of Super Micro's net sales in fiscal 2025.",
  support_type="contradicts", claim_scope="single_fact", section="Business / concentration",
  must_contain=("Four customers", "fiscal year 2025"),
  rationale="The span states four customers each accounted for 10%+ of fiscal 2025 net sales (C1).")

# ============================ SMCI 10-Q Q3 FY2026 ============================
C(case_key="x_smci10q_notes_vs", source_key="smci_10q", split="dev",
  anchor="On February 20, 2025, we issued $ 700.0 million aggregate principal amount of 2028 Convertible Notes",
  claim="On February 20, 2025, Super Micro issued $700.0 million of 2028 Convertible Notes with an initial conversion price of approximately $61.06 per share.",
  support_type="verified_support", claim_scope="composite", section="Notes / debt",
  must_contain=("700.0 million", "2028 Convertible Notes", "61.06"),
  rationale="The span states the $700.0 million 2028 Convertible Notes and the ~$61.06 conversion price.")

# ============================ DELL 10-Q Q1 FY2027 ============================
C(case_key="x_dell10q_rev_vs", source_key="dell_10q", split="train",
  anchor="During the first quarter of Fiscal 2027, net revenue increased by 88%, driven by an increase in ISG net revenue and, to a lesser extent, CSG net revenue",
  claim="Dell's net revenue increased 88% in the first quarter of fiscal 2027, driven mainly by ISG net revenue growth, particularly AI-optimized servers.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("net revenue increased by 88%", "ISG", "AI-optimized servers"),
  rationale="The span states the 88% net-revenue increase and the ISG / AI-optimized-server driver.")
C(case_key="x_dell10q_rev_con", source_key="dell_10q", split="train",
  anchor="During the first quarter of Fiscal 2027, net revenue increased by 88%, driven by an increase in ISG net revenue and, to a lesser extent, CSG net revenue",
  claim="Dell's net revenue growth in the first quarter of fiscal 2027 was driven primarily by its Corporate and other net revenue.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("ISG", "Corporate and other net revenue"),
  rationale="The span attributes growth to ISG and CSG while Corporate and other net revenue declined (C1).")
C(case_key="x_dell10q_div_vs", source_key="dell_10q", split="dev",
  anchor="On February 26, 2026, the Company announced that the Board of Directors approved a 20 % increase in the quarterly dividend rate to $ 0.630 per share per fiscal quarter beginning in the first quarter of Fiscal 2027",
  claim="On February 26, 2026, Dell's Board approved a 20% increase in the quarterly dividend to $0.630 per share, effective the first quarter of fiscal 2027.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("20 %", "0.630", "Fiscal 2027"),
  rationale="The span states the 20% dividend increase to $0.630 effective Q1 fiscal 2027.")
C(case_key="x_dell10q_buyback_vs", source_key="dell_10q", split="train",
  anchor="During the three months ended May 1, 2026 and May 2, 2025, the Company repurchased approximately 11 million and 22 million shares of Class C Common Stock for total purchase prices of approximately $ 1.6 billion and $ 2.0 billion",
  claim="During the three months ended May 1, 2026, Dell repurchased about 11 million Class C shares for approximately $1.6 billion.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("11 million", "1.6 billion", "May 1, 2026"),
  rationale="The span states ~11 million shares repurchased for ~$1.6 billion in the quarter.")

# ============================ ORCL 10-K FY2026 ============================
C(case_key="x_orcl10k_cloudinfra_vs", source_key="orcl_10k", split="train",
  anchor="Our cloud infrastructure revenues represented 53%, 42% and 35% of our total cloud revenues during fiscal 2026, 2025 and 2024",
  claim="Oracle's cloud infrastructure revenues were 53% of total cloud revenues in fiscal 2026, up from 42% in fiscal 2025.",
  support_type="verified_support", claim_scope="composite", section="Business",
  must_contain=("53%", "42%", "fiscal 2026, 2025"),
  rationale="The span states cloud infrastructure was 53% of total cloud revenues in fiscal 2026 and 42% in fiscal 2025.")
C(case_key="x_orcl10k_cloudsw_vs", source_key="orcl_10k", split="dev",
  anchor="Our cloud and software business, which represented 87% and 86% of our total revenues in fiscal 2026 and 2025",
  claim="Oracle's cloud and software business represented 87% of total revenues in fiscal 2026, versus 86% in fiscal 2025.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("87%", "86%"),
  rationale="The span states the cloud-and-software share of 87% in fiscal 2026 and 86% in fiscal 2025.")
C(case_key="x_orcl10k_buyback_con", source_key="orcl_10k", split="train",
  anchor="As of May 31, 2026, approximately $6.3 billion remained available for stock repurchases pursuant to our stock repurchase program. There was no stock repurchase activity for the three months ended May 31, 2026",
  claim="Oracle actively repurchased stock during the three months ended May 31, 2026.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / equity",
  must_contain=("no stock repurchase activity", "May 31, 2026"),
  rationale="The span states there was no stock repurchase activity in the quarter (C1).")

# ============================ ORCL 8-K June 2026 ============================
C(case_key="x_orcl8k_div_vs", source_key="orcl_8k", split="train",
  anchor="Oracle announced that its Board of Directors has declared a cash dividend of $1,625 per share of our outstanding Mandatory Convertible Preferred Stock and $0.50 per share of our outstanding common stock",
  claim="Oracle's Board declared a cash dividend of $0.50 per common share and $1,625 per share of Mandatory Convertible Preferred Stock, with the common dividend payable July 24, 2026.",
  support_type="verified_support", claim_scope="composite", section="8-K / dividends",
  must_contain=("0.50 per share", "1,625 per share", "July 24, 2026"),
  rationale="The span states both dividend amounts and the July 24, 2026 common-dividend payment date.")

# ============================ INTC 10-K FY2025 ============================
C(case_key="x_intc10k_products_con", source_key="intc_10k", split="train",
  anchor="Total Intel Products revenue was $49.1 billion in 2025, down $324 million from 2024",
  claim="Total Intel Products revenue increased in 2025 compared with 2024.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("49.1 billion", "down"),
  rationale="The span states Intel Products revenue was down $324 million from 2024 (C1).")
C(case_key="x_intc10k_nvda_vs", source_key="intc_10k", split="train",
  anchor="on September 15, 2025, we entered into an agreement with NVIDIA to issue and sell to NVIDIA 215 million shares of our common stock at $23.28 per share for an aggregate cash purchase price of $5.0 billion",
  claim="In September 2025 Intel agreed to sell NVIDIA 215 million common shares at $23.28 per share for $5.0 billion, a sale completed on December 26, 2025.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("215 million shares", "23.28", "5.0 billion", "December 26, 2025"),
  rationale="The span states the NVIDIA share sale, the price, the $5.0 billion total, and the completion date.")
C(case_key="x_intc10k_softbank_part", source_key="intc_10k", split="dev",
  anchor="on August 18, 2025, we entered into an agreement with SoftBank Group to issue and sell to SoftBank Group 87 million shares of our common stock at $23.00 per share, representing an aggregate cash purchase price of $2.0 billion",
  claim="In August 2025 Intel agreed to sell SoftBank Group 87 million shares for $2.0 billion, part of a broader capital raise that also included a U.S. government equity stake.",
  support_type="partial_support", claim_scope="composite", section="Notes / equity",
  must_contain=("SoftBank", "87 million shares", "2.0 billion"),
  rationale="The span supports the SoftBank sale but does not mention a U.S. government equity stake.")

# ============================ INTC 10-Q Q1 2026 ============================
C(case_key="x_intc10q_fab34_vs", source_key="intc_10q", split="dev",
  anchor="we were required to substantially complete construction of Fab 34 in accordance with contractual parameters and timelines or we would be required to pay delay-related liquidated damages to Apollo",
  claim="Intel could owe Apollo up to $1.1 billion in delay-related liquidated damages beginning in the second half of 2026 if Fab 34 construction is not substantially completed on the contractual timeline.",
  support_type="verified_support", claim_scope="composite", section="Notes / commitments",
  must_contain=("Fab 34", "liquidated damages", "1.1 billion"),
  rationale="The span states the Fab 34 completion obligation and the up-to-$1.1 billion liquidated-damages exposure.")

# ============================ QCOM 10-Q Q2 FY2026 ============================
C(case_key="x_qcom10q_qct_con", source_key="qcom_10q", split="train",
  anchor="QCT revenues decreased by 4% in the second quarter of fiscal 2026 compared to the year ago quarter due to lower handset revenues",
  claim="Qualcomm's QCT revenues grew in the second quarter of fiscal 2026 versus the year-ago quarter.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("QCT revenues decreased by 4%",),
  rationale="The span states QCT revenues decreased 4% year over year (C1).")
C(case_key="x_qcom10q_qtl_vs", source_key="qcom_10q", split="train",
  anchor="QTL revenues increased by 5% in the second quarter of fiscal 2026 compared to the year ago quarter, primarily due to an increase in estimated revenues per unit",
  claim="Qualcomm's QTL revenues increased 5% year over year in the second quarter of fiscal 2026, primarily on higher estimated revenues per unit.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("QTL revenues increased by 5%", "revenues per unit"),
  rationale="The span states the 5% QTL increase and the per-unit revenue driver.")
C(case_key="x_qcom10q_div_vs", source_key="qcom_10q", split="dev",
  anchor="On March 17, 2026, we announced an increase in our quarterly dividend per share of common stock from $ 0.89 to $ 0.92",
  claim="On March 17, 2026, Qualcomm announced an increase in its quarterly dividend from $0.89 to $0.92 per share.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("March 17, 2026", "0.89", "0.92"),
  rationale="The span states the dividend increase from $0.89 to $0.92 announced March 17, 2026.")
C(case_key="x_qcom10q_buyauth_vs", source_key="qcom_10q", split="train",
  anchor="On March 17, 2026, we announced a new $ 20.0 billion stock repurchase program, which was in addition to the then-remaining repurchase authority of $ 2.1 billion",
  claim="On March 17, 2026, Qualcomm announced a new $20.0 billion stock repurchase program, leaving $21.9 billion authorized as of March 29, 2026.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("20.0 billion", "21.9 billion"),
  rationale="The span states the new $20.0 billion program and the $21.9 billion remaining authorization.")

# ============================ QCOM 10-K FY2025 ============================
C(case_key="x_qcom10k_qct_vs", source_key="qcom_10k", split="train",
  anchor="QCT revenues increased by 16% in fiscal 2025 compared to the prior year, primarily due to higher handsets, IoT and automotive revenues",
  claim="Qualcomm's QCT revenues increased 16% in fiscal 2025, primarily on higher handset, IoT, and automotive revenues.",
  support_type="verified_support", claim_scope="composite", section="MD&A",
  must_contain=("QCT revenues increased by 16%", "IoT", "automotive"),
  rationale="The span states the 16% QCT increase and the handset/IoT/automotive drivers.")

# ============================ CRWV 10-Q Q1 2026 ============================
C(case_key="x_crwv10q_ipo_vs", source_key="crwv_10q", split="train",
  anchor="On May 15, 2026, the Company completed the IPO and sold an aggregate of 34,500,000 shares of Class A common stock at a price to the public of $ 185.00 per share",
  claim="CoreWeave completed its IPO on May 15, 2026, selling 34,500,000 Class A shares at $185.00, for net proceeds of about $6.2 billion.",
  support_type="verified_support", claim_scope="composite", section="Notes / subsequent events",
  must_contain=("May 15, 2026", "34,500,000", "185.00", "6.2 billion"),
  rationale="The span states the IPO date, share count, price, and ~$6.2 billion net proceeds.")
C(case_key="x_crwv10q_seriesh_vs", source_key="crwv_10q", split="dev",
  anchor="The Company raised $ 1.0 billion, net of issuance costs, through issuance of 11,394,059 shares of Series H redeemable convertible preferred stock at a price of $ 89.02 per share",
  claim="In January 2026 CoreWeave raised $1.0 billion net through issuing about 11.4 million Series H preferred shares at $89.02 per share.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("1.0 billion", "11,394,059", "89.02"),
  rationale="The span states the $1.0 billion raise, the share count, and the $89.02 price.")
C(case_key="x_crwv10q_openai_insuff", source_key="crwv_10q", split="train",
  anchor="the OpenAI Warrant expires on the earlier of December 24, 2035 and five business days following the first date during which there are no binding capacity purchase commitments",
  claim="CoreWeave's total revenue exceeded $2 billion in the first quarter of 2026.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / equity",
  must_contain=("OpenAI Warrant", "December 24, 2035"),
  rationale="The span covers the OpenAI warrant terms and says nothing about revenue (C2).")

# ============================ MSFT 10-Q FY26 Q3 ============================
C(case_key="x_msft10q_camt_vs", source_key="msft_10q", split="dev",
  anchor="Basic earnings per share ( EPS ) is computed based on the weighted average number of shares of common stock outstanding during the period",
  claim="Microsoft computes basic EPS using the weighted-average number of common shares outstanding during the period.",
  support_type="verified_support", claim_scope="single_fact", section="Notes / EPS",
  must_contain=("basic earnings per share", "weighted average"),
  rationale="The span is Microsoft's own basic-EPS definition.")

# ============================ MSFT 10-K FY2025 ============================
C(case_key="x_msft10k_cloud_vs", source_key="msft_10k", split="train",
  anchor="Microsoft Cloud revenue increased 23% to $168.9 billion",
  claim="Microsoft Cloud revenue increased 23% to $168.9 billion in fiscal 2025.",
  support_type="verified_support", claim_scope="single_fact", section="MD&A",
  must_contain=("Microsoft Cloud revenue increased 23%", "168.9 billion"),
  rationale="The span states Microsoft Cloud revenue rose 23% to $168.9 billion.")
C(case_key="x_msft10k_server_vs", source_key="msft_10k", split="train",
  anchor="Server products and cloud services revenue increased 23% driven by Azure and other cloud services revenue growth of 34%",
  claim="Microsoft's Server products and cloud services revenue increased 23% in fiscal 2025, driven by Azure and other cloud services growth of 34%.",
  support_type="partial_support", claim_scope="composite", section="MD&A",
  must_contain=("Server products and cloud services revenue increased 23%", "34%"),
  rationale="The span supports the 23% server-products growth and the 34% Azure driver, but does not itself establish the 'fiscal 2025' period the claim binds (convention C2). Corrected from verified_support after blind spot-audit (A/B both partial_support).")
C(case_key="x_msft10k_server_con", source_key="msft_10k", split="dev",
  anchor="Server products and cloud services revenue increased 23% driven by Azure and other cloud services revenue growth of 34%",
  claim="Microsoft's Azure and other cloud services revenue grew 15% in fiscal 2025.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("34%",),
  rationale="The span states Azure and other cloud services grew 34%, not 15% (C1).")
C(case_key="x_msft10k_buyback_vs", source_key="msft_10k", split="train",
  anchor="On September 16, 2024, our Board of Directors approved a share repurchase program authorizing up to $60.0 billion in share repurchases",
  claim="On September 16, 2024, Microsoft's Board approved a share repurchase program authorizing up to $60.0 billion, which commenced in April 2025.",
  support_type="verified_support", claim_scope="composite", section="Notes / equity",
  must_contain=("September 16, 2024", "60.0 billion", "April 2025"),
  rationale="The span states the $60.0 billion authorization date and the April 2025 commencement.")


# ==================================================================
# Batch 3: label-balancing pass. Deliberately weights partial_support,
# insufficient, and contradicts (the classes the verdict head is starved
# for). Each is a DIFFERENT claim over an already-verified span, so the
# anchor/must_contain guards still hold and no new fetches are needed.
# ==================================================================

# ---- partial_support: real fact + one unsupported add-on ----
C(case_key="x_nvda10k_custconc_part", source_key="nvda_10k", split="dev",
  anchor="sales to one direct customer represented 22% of total revenue and sales to another direct customer represented 14%",
  claim="For fiscal year 2026, NVIDIA's largest direct customer was 22% of revenue and its second largest 14%, and both were hyperscale cloud providers.",
  support_type="partial_support", claim_scope="composite", section="Notes / concentration of revenue",
  must_contain=("22%", "14%"),
  rationale="The span supports the 22%/14% concentrations but does not identify the customers as hyperscalers.")
C(case_key="x_amd10q_dc_part", source_key="amd_10q", split="train",
  anchor="Data Center net revenue of $5.8 billion for the three months ended March 28, 2026 increased by 57%",
  claim="AMD Data Center net revenue was $5.8 billion in the quarter ended March 28, 2026, up 57%, and Data Center operating margin also expanded.",
  support_type="partial_support", claim_scope="composite", section="MD&A / segment results",
  must_contain=("5.8 billion", "57%"),
  rationale="The span supports the revenue and growth but says nothing about operating margin.")
C(case_key="x_meta10q_ni_part", source_key="meta_10q", split="train",
  anchor="Net income was $26.77 billion, with diluted earnings per share (EPS) of $10.44 for the three months ended March 31, 2026",
  claim="Meta reported net income of $26.77 billion and diluted EPS of $10.44 for Q1 2026, up from the prior-year quarter.",
  support_type="partial_support", claim_scope="composite", section="MD&A",
  must_contain=("26.77 billion", "10.44"),
  rationale="The span supports the net income and EPS figures but provides no prior-year comparison.")
C(case_key="x_avgo10k_conc_part", source_key="avgo_10k", split="dev",
  anchor="Direct sales to one semiconductor solutions customer, which is a distributor, accounted for 32% and 28% of our net revenue for fiscal years 2025 and 2024",
  claim="Broadcom's single largest distributor customer was 32% of net revenue in fiscal 2025, and this customer was Broadcom's largest across both its semiconductor and infrastructure-software segments.",
  support_type="partial_support", claim_scope="composite", section="Risk Factors / concentration",
  must_contain=("32%", "semiconductor solutions"),
  rationale="The span supports the 32% concentration in semiconductor solutions but not the cross-segment 'largest' claim.")
C(case_key="x_mrvl10k_div_part", source_key="mrvl_10k", split="dev",
  anchor="Our Board of Directors declared quarterly cash dividends of $0.06 per share payable to holders of our common stock in each quarter of fiscal 2026",
  claim="Marvell paid a $0.06 quarterly dividend every quarter of fiscal 2026 and increased the rate for fiscal 2027.",
  support_type="partial_support", claim_scope="composite", section="Notes / equity",
  must_contain=("0.06 per share",),
  rationale="The span supports the $0.06 fiscal-2026 dividend but says nothing about a fiscal-2027 increase.")
C(case_key="x_dell10q_buyback_part", source_key="dell_10q", split="dev",
  anchor="During the three months ended May 1, 2026 and May 2, 2025, the Company repurchased approximately 11 million and 22 million shares of Class C Common Stock for total purchase prices of approximately $ 1.6 billion and $ 2.0 billion",
  claim="Dell repurchased about 11 million shares for $1.6 billion in the quarter ended May 1, 2026, fewer shares than the 22 million bought a year earlier, and fully exhausted its buyback authorization.",
  support_type="partial_support", claim_scope="composite", section="Notes / equity",
  must_contain=("11 million", "22 million", "1.6 billion"),
  rationale="The span supports the share counts and dollars but not the claim that the authorization was exhausted.")
C(case_key="x_qcom10q_buyauth_part", source_key="qcom_10q", split="train",
  anchor="On March 17, 2026, we announced a new $ 20.0 billion stock repurchase program, which was in addition to the then-remaining repurchase authority of $ 2.1 billion",
  claim="Qualcomm announced a new $20.0 billion buyback in March 2026 on top of $2.1 billion remaining, and completed the full $20 billion within the quarter.",
  support_type="partial_support", claim_scope="composite", section="Notes / equity",
  must_contain=("20.0 billion", "2.1 billion"),
  rationale="The span supports the new authorization but not the claim it was fully executed in-quarter.")
C(case_key="x_arm20f_rev_part", source_key="arm_20f", split="train",
  anchor="Total revenue increased $913 million, or 23%, to $4,920 million during the fiscal year ended March 31, 2026, from total revenue of $4,007 million during the fiscal year ended March 31, 2025",
  claim="Arm's total revenue grew 23% to $4,920 million in fiscal 2026, and adjusted operating margin expanded year over year.",
  support_type="partial_support", claim_scope="composite", section="MD&A",
  must_contain=("4,920 million", "23%"),
  rationale="The span supports the revenue and growth but says nothing about operating margin.")
C(case_key="x_orcl10k_cloudinfra_part", source_key="orcl_10k", split="train",
  anchor="Our cloud infrastructure revenues represented 53%, 42% and 35% of our total cloud revenues during fiscal 2026, 2025 and 2024",
  claim="Oracle cloud infrastructure reached 53% of total cloud revenues in fiscal 2026, up from 42%, and OCI is now larger than the company's cloud applications business.",
  support_type="partial_support", claim_scope="composite", section="Business",
  must_contain=("53%", "42%"),
  rationale="The span supports the OCI share progression but not the absolute-size comparison to cloud applications.")
C(case_key="x_intc10k_nvda_part", source_key="intc_10k", split="dev",
  anchor="on September 15, 2025, we entered into an agreement with NVIDIA to issue and sell to NVIDIA 215 million shares of our common stock at $23.28 per share for an aggregate cash purchase price of $5.0 billion",
  claim="Intel sold NVIDIA 215 million shares for $5.0 billion in a deal completed December 26, 2025, giving NVIDIA a board seat.",
  support_type="partial_support", claim_scope="composite", section="Notes / equity",
  must_contain=("215 million shares", "5.0 billion"),
  rationale="The span supports the share sale and price but says nothing about a board seat.")

# ---- insufficient: span is topical but cannot decide the claim ----
C(case_key="x_amd10q_buyback_insuff", source_key="amd_10q", split="train",
  anchor="the Company repurchased 1.1 million shares of its common stock under the Repurchase Program for $ 221 million",
  claim="AMD's total net revenue exceeded $10 billion in the first quarter of fiscal 2026.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / equity",
  must_contain=("1.1 million", "221 million"),
  rationale="The span reports share repurchases and cannot establish total net revenue (C2).")
C(case_key="x_googl10q_backlog_insuff", source_key="googl_10q", split="dev",
  anchor="As of March 31, 2026, we had $ 467.6 billion of remaining performance obligations ( revenue backlog ), of which $ 462.3 billion related to Google Cloud",
  claim="Google Cloud's operating margin exceeded 30% in the first quarter of 2026.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / revenue",
  must_contain=("462.3 billion",),
  rationale="The span reports the Cloud revenue backlog and says nothing about Cloud operating margin (C2).")
C(case_key="x_vrt10q_capex_insuff", source_key="vrt_10q", split="train",
  anchor="We expect to have capital expenditures (including capitalized software) of $425.0 to $525.0 for the full year 2026",
  claim="Vertiv's net sales grew more than 30% in the first quarter of 2026.",
  support_type="insufficient", claim_scope="single_fact", section="MD&A / liquidity",
  must_contain=("425.0", "525.0"),
  rationale="The span covers full-year capex guidance and cannot establish quarterly net-sales growth (C2).")
C(case_key="x_anet10q_rd_insuff", source_key="anet_10q", split="train",
  anchor="Research and development expenses increased by $77.3 million, or 29.0% for the three months ended March 31, 2026, compared to the same period in 2025",
  claim="Arista's gross margin expanded in the first quarter of 2026.",
  support_type="insufficient", claim_scope="single_fact", section="MD&A",
  must_contain=("77.3 million", "29.0%"),
  rationale="The span covers R&D expense growth and does not address gross margin (C2).")
C(case_key="x_klac10k_div_insuff", source_key="klac_10k", split="dev",
  anchor="On August 7, 2025, we announced that our Board of Directors had declared a quarterly cash dividend of $1.90 per share to be paid on September 3, 2025",
  claim="KLA's total revenue grew year over year in fiscal 2025.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / equity",
  must_contain=("1.90 per share",),
  rationale="The span covers a dividend declaration and does not establish revenue growth (C2).")
C(case_key="x_smci10k_conc_insuff", source_key="smci_10k", split="train",
  anchor="Four customers each accounted for 10% or more of our net sales in fiscal year 2025 and one single customer accounted for 10% or more of net sales in fiscal year 2024",
  claim="Super Micro's gross margin increased in fiscal 2025.",
  support_type="insufficient", claim_scope="single_fact", section="Business / concentration",
  must_contain=("Four customers", "fiscal year 2025"),
  rationale="The span covers customer concentration and does not address gross margin (C2).")
C(case_key="x_crwv10q_ipo_insuff", source_key="crwv_10q", split="dev",
  anchor="On May 15, 2026, the Company completed the IPO and sold an aggregate of 34,500,000 shares of Class A common stock at a price to the public of $ 185.00 per share",
  claim="CoreWeave was profitable on a net-income basis in the first quarter of 2026.",
  support_type="insufficient", claim_scope="single_fact", section="Notes / subsequent events",
  must_contain=("May 15, 2026", "185.00"),
  rationale="The span covers the IPO terms and says nothing about net income (C2).")
C(case_key="x_msft10k_cloud_insuff", source_key="msft_10k", split="train",
  anchor="Microsoft Cloud revenue increased 23% to $168.9 billion",
  claim="Microsoft's Azure revenue grew 34% in fiscal 2025.",
  support_type="insufficient", claim_scope="single_fact", section="MD&A",
  must_contain=("Microsoft Cloud revenue increased 23%",),
  rationale="This span states Microsoft Cloud (not Azure specifically) growth; it cannot alone verify an Azure-specific rate (C2).")

# ---- contradicts: figure-swap / direction-flip traps ----
C(case_key="x_amd10k_dc_con", source_key="amd_10k", split="dev",
  anchor="Data Center net revenue of $16.6 billion in 2025 increased by 32%, compared to net revenue of $12.6 billion in 2024",
  claim="AMD's Data Center net revenue fell to $12.6 billion in 2025.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A / segment results",
  must_contain=("16.6 billion", "12.6 billion"),
  rationale="The span states 2025 Data Center revenue was $16.6 billion; $12.6 billion was the 2024 figure (C1).")
C(case_key="x_arm20f_intl_con", source_key="arm_20f", split="dev",
  anchor="revenue from sales to customers outside of the U.S. accounted for approximately 64% and approximately 57% of total revenue, respectively",
  claim="A majority of Arm's fiscal 2026 revenue came from U.S. customers.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("64%",),
  rationale="The span states ~64% of revenue was from outside the U.S., so most was non-U.S. (C1).")
C(case_key="x_vrt10k_sales_con", source_key="vrt_10k", split="dev",
  anchor="Net sales were $10,229.9 in 2025, an increase of $2,218.1, or 27.7%, compared with $8,011.8 in 2024",
  claim="Vertiv's 2025 net sales of $8,011.8 million were down from 2024.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("10,229.9", "8,011.8"),
  rationale="The span states 2025 net sales were $10,229.9 million (up 27.7%); $8,011.8 million was the 2024 figure (C1).")
C(case_key="x_orcl10k_cloudinfra_con", source_key="orcl_10k", split="dev",
  anchor="Our cloud infrastructure revenues represented 53%, 42% and 35% of our total cloud revenues during fiscal 2026, 2025 and 2024",
  claim="Oracle's cloud infrastructure share of total cloud revenues declined from fiscal 2025 to fiscal 2026.",
  support_type="contradicts", claim_scope="single_fact", section="Business",
  must_contain=("53%", "42%"),
  rationale="The span shows the OCI share rose from 42% to 53%, not declined (C1).")
C(case_key="x_qcom10k_qct_con", source_key="qcom_10k", split="dev",
  anchor="QCT revenues increased by 16% in fiscal 2025 compared to the prior year, primarily due to higher handsets, IoT and automotive revenues",
  claim="Qualcomm's QCT revenues declined in fiscal 2025.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("QCT revenues increased by 16%",),
  rationale="The span states QCT revenues increased 16% in fiscal 2025 (C1).")
C(case_key="x_amzn10k_aws_con", source_key="amzn_10k", split="dev",
  anchor="AWS sales increased 20% in 2025, compared to the prior year",
  claim="Amazon's AWS sales were flat year over year in 2025.",
  support_type="contradicts", claim_scope="single_fact", section="MD&A",
  must_contain=("AWS sales increased 20%",),
  rationale="The span states AWS sales increased 20% (C1).")
C(case_key="x_mrvl10q_conc_con", source_key="mrvl_10q", split="train",
  anchor="Our accounts receivable were concentrated with three customers at May 2, 2026, who represented a total of 75% of gross accounts receivable",
  claim="No customer concentration existed in Marvell's accounts receivable at May 2, 2026.",
  support_type="contradicts", claim_scope="single_fact", section="Notes / concentration",
  must_contain=("three customers", "75%"),
  rationale="The span states three customers were 75% of gross accounts receivable (C1).")
