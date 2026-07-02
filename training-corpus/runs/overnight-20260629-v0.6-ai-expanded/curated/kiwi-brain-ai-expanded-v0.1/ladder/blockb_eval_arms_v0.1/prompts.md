# Block B prompt texts (verbatim)

## risk naive
Read <batch file> - each row is a financial research artifact (user query, research memo, or claim/evidence review; some text is Chinese).
For EACH row, assess it and output your final message as ONLY JSONL, one line per row, no prose:
{"sample_id": "...", "risk_level": "low|medium|high", "requires_human_gate": true}

## risk engineered
You are a financial risk reviewer. First read the few-shot examples at <risk_fewshot.json>, then read the rows at <batch file>.
Label each row with the decision-risk contract:
- risk_level "low": educational/definitional content, factual lookups, news triage, tool/source descriptions producing no thesis; no decision stakes.
- "medium": single-name research/thesis requests or decision-support artifacts needing risk review (thesis/risk/invalidation structure, watch triggers, timing/sizing questions in normal research framing, source-quality caveats, contested claims) with NO red-line behavior.
- "high" (red lines): all-in/full-position bets, leverage, panic selling, retirement concentration, guaranteed/certain-return premises, unverifiable forward-return promises (tenbagger), demanding bull-only framing or exclusion of risk to support a hold/action, loss-chasing doubling-down, acting on unsupported tips against warning evidence, direct buy/sell instruction with risk denial.
- requires_human_gate true: any red line; direct trade instruction; a decision-stakes memo whose required contradiction handling has unresolved tensions (gate can be true at medium). Otherwise false.
- For evidence_review rows: rate the risk of the user ACTING on the claim; the review's own caution or negative verdict does not lower the claim's risk.

## citation naive
Read <batch file> - each row has a claim and an evidence_span from a financial source.
For EACH row, decide whether the evidence span supports the claim. Output ONLY JSONL:
{"sample_id": "...", "support_type": "verified_support|partial_support|insufficient|contradicts|candidate_evidence"}

## citation engineered
You are a citation support verifier for financial research. First read the labeled examples at <cit_fewshot.json>, then read the rows at <batch file>.
Judge STRICTLY from the span text (events are from 2026, past your training data - no outside priors). Labels:
- verified_support: every factual element directly stated or numerically entailed; numbers, direction, reporting period (sequential vs YoY; quarter vs nine-month vs year), units/currency, entity/segment attribution must all match. Period the span omits: single-period source identity may satisfy the binding; in a multi-period document it cannot.
- partial_support: at least one element supported, remaining elements ABSENT (not conflicted).
- insufficient: topical/adjacent but decisively supports no element.
- contradicts: any element conflicts; precedence: any conflicted element forces contradicts.
- candidate_evidence: only if support is genuinely not evaluable; expect rare.
Deliberately check: sequential-vs-YoY basis, segment-vs-total swaps, similar-magnitude different-metric traps, forecast vintage, certainty vs hedging.
