# Post-Training Logic as KIWI Architecture

Date: 2026-06-29

## Core Framing

We are not simply using KIWI outputs to post-train a model.

We are using post-training logic to rebuild KIWI's agent architecture.

In other words, post-training is not only a model-training stage. It is a system-stabilization method:

```text
data -> evaluation -> diagnosis -> harness repair -> re-evaluation
```

For KIWI, this means turning a loose financial research agent into a workflow whose nodes are observable, evaluable, reversible, and repairable.

## Why This Matters

A weak framing would be:

```text
KIWI generates outputs.
We collect those outputs.
Then we fine-tune a model.
```

That sounds like ordinary data collection.

The stronger and more accurate framing is:

```text
We clean trajectories and feedback.
Cleaning exposes failure modes at specific agent nodes.
Those failures drive harness, tool-contract, memory, and loop fixes.
Only after the system becomes measurable do we train small specialist models.
```

This is closer to how post-training teams actually work: the hard part is not naming SFT, DPO, or GRPO. The hard part is building a reliable environment where failures can be attributed.

## KIWI Migration

KIWI's financial research workflow is decomposed into checkpoints:

```text
user intent
point-in-time context
retrieval / source discovery
source link registry
evidence extraction
citation verification
calculation / metric checking
risk review
memo synthesis
long2short final answer
memory update candidate
final user response
```

Each checkpoint should have:

- structured input
- structured output
- provenance
- verifier or grader
- failure taxonomy
- fallback behavior
- replayable trace

This lets us distinguish:

- model misunderstanding
- bad retrieval
- missing source
- stale data
- citation mismatch
- overconfident advice
- memory pollution
- unnecessary deep research
- risk-review omission
- tool failure

## Data Cleaning as Architecture Debugging

When we curate trajectory data, we are not merely filtering examples.

We are debugging the agent architecture.

Examples:

| Data cleaning finding | Architecture implication |
| --- | --- |
| Claim has only social evidence | Add evidence gate before memo synthesis |
| Citation span does not support claim | Strengthen citation verifier and source contract |
| User asks all-in / full-position question | Force risk-review route and human gate |
| Simple query triggers deep research | Improve router to reduce over-routing |
| Complex decision gets fast answer | Improve safety recall and under-routing checks |
| Tool returns empty news | Preserve source failure and avoid hallucinated news |
| Memory update is too aggressive | Add pending approval / memory proposal gate |
| Analyst output format drifts | Tighten structured I/O contract |
| Support and risk evidence both appear | Add `support_vs_risk_comparison`, `contradiction_handling`, and regression cases |
| Source is hard to revisit later | Preserve raw links, canonical URLs, search query, access status, and span hashes |
| Internal research is too verbose for users | Export long2short pairs: long internal trajectory, short useful answer |
| Deep research finds only upside evidence | Add `search_query_3_risk`, risk-page reads, and risk-snippet fallback evidence |

This is the main value of the current work: each dataset curation pass tells us which part of KIWI's harness is unstable.

## Example Harness Repair

The long research pilot exposed two concrete architecture issues.

First, memory write was too permissive: reviewer-flagged traces could still emit memory proposals. We tightened `memory_write_gate` so only reviewer-clean, evidence-grounded traces can create pending proposals, and even those still require user approval.

Second, contradiction handling was too implicit. MU and NVDA traces contained both support and risk evidence, but the reviewer was judging handling by whether the thesis prose sounded balanced. We changed this into a structured contract:

```text
compare_sources
-> support_vs_risk_comparison
-> revise_thesis
-> contradiction_handling
-> reviewer checks fields
-> regression/contradiction_cases.jsonl
```

This is the post-training loop applied to agent architecture: a trace failure became a named failure mode, then a structured I/O contract, then a reviewer check, then a regression set.

The v0.2 long-research schema added another production-grade requirement: source lineage. KIWI now exports a source registry for each long trace:

```text
search result
-> raw source URL
-> canonical URL
-> publisher/title/published time
-> search query/rank/snippet
-> page access status
-> content hash
-> evidence span + span hash
```

This lets us inspect where a claim came from later, even if the final answer is short.

The same run also added Kiwi's long2short training target:

```text
internal long research trajectory
-> source comparison
-> reviewer
-> rewrite
-> short user-facing answer with evidence, risks, invalidation, triggers, and links
```

This mirrors the post-training idea that the model or system should learn the long reasoning process first, then compress the user-facing output without losing decision-critical content.

The next repair targeted risk evidence coverage. MRVL and VRT initially produced `risk_omission` because the harness had broad and official-source searches, but no dedicated downside search. We added:

```text
search_query_3_risk
-> open/read risk pages
-> extract risk paragraph claims
-> preserve risk headline/snippet claims when pages are blocked
-> reviewer checks risk evidence
```

The current pilot has zero `risk_omission` blockers. This is a good interview example because the fix is not "make the model smarter"; it is "add the missing environment action and make the evidence observable."

The next scale-up moved from 5 long traces to 25 long traces across AI, semiconductor, cloud, networking, equipment, and storage names. This was not just "more data"; it was a harness generalization test.

The expanded run produced:

```text
25 complete long research traces
433 citation-verifier rows
339 source records
25 router / risk / memory / memo-quality rows
25 long2short pairs
25 contradiction regression cases
50 evidence-chain negative cases
```

It also exposed two useful system lessons.

First, official-source detection is part of the harness. A narrow allowlist can make a trace look weak even when the source is a real investor-relations or company source. The repair was to expand the official-domain classifier for the covered ticker universe.

Second, not every retrieval miss is a blocker. A broad/news search can return nothing while official-source and risk-source searches still provide usable evidence. The repair was to split source issues into:

```text
source_warnings:
  individual broad / official / risk query misses

blockers:
  all searches fail, missing evidence, temporal leakage, unsafe advice, or unrecoverable source failure
```

This distinction matters for agentic post-training. If the grader labels every noisy retrieval event as a failed episode, the training signal becomes too pessimistic. If it hides retrieval weakness entirely, the final answer can look clean while the evidence chain is fragile. KIWI now keeps both: complete episodes for training, plus source warnings for failure attribution and future regression tests.

The source-quality repair then turned this lesson into a concrete environment action.

The expanded run showed 16/25 traces with `source_quality_weak`. The failure was not "the model cannot reason"; it was "search does not reliably retrieve enough primary / reputable sources." That is a harness problem.

The repair added fixed official source anchors:

```text
task ticker
-> SEC browse page
-> investor-relations homepage
-> quarterly-results / press-release / financial-results hub
-> open_official_sources
-> read_official_paragraphs
-> extract_official_claims
```

After rerunning the 25-trace set:

```text
source_quality_weak: 16/25 -> 0/25
evidence-chain mean score: 0.954 -> 0.999
source records: 339 -> 397
claims: 433 -> 532
blockers: 0
```

This is a useful post-training lesson: if an eval reveals weak source grounding, the right fix may be to add a missing environment action, not to ask the model to "try harder." The dataset gets better because the harness exposes and repairs the missing source path.

## Runtime Harness Bridge

The same logic now needs to move from offline corpus building into KIWI's live
runtime.

The current weakness is not only model quality. KIWI still needs manual nudges:
we have to remind it to run checks, update memory proposals, inspect source
quality, and replay failures. That means the agent is not yet a stable research
environment. It has good components, but the operational loop is still too
manual.

The next architecture step is documented in:

```text
kiwi/docs/runtime-harness-refinement.md
```

The runtime migration is:

```text
offline failure cases
-> scheduled runtime checks
-> check_result artifacts
-> memory proposal digest
-> attention alerts only when useful
-> regression replay after harness edits
```

Concretely, the failures we found should become recurring checks:

| Offline finding | Runtime check |
| --- | --- |
| `source_quality_weak` | daily source-quality audit over recent evidence |
| `risk_omission` | evidence-chain regression requiring downside/risk evidence |
| `contradiction_not_handled` | memo contract check for support-vs-risk comparison |
| over-permissive memory proposals | memory write gate plus daily pending-proposal digest |
| `evidence_check` vs `deep_research` confusion | router boundary regression |
| plausible final answer with bad citation lineage | evidence-chain negative replay |

This matters for the interview story: post-training is not just "collect data,
then fine-tune." It is a discipline for making the agent environment run,
measure itself, expose failure modes, and repair the harness before training.

The first router baseline applies the same logic to coordinator behavior.

We trained a leakage-free TF-IDF + logistic-regression router on the 344-row
golden router split and evaluated the repaired 25 long-research router rows as
a holdout:

```text
test route accuracy: 0.9167
test macro F1: 0.9368
test safety recall: 1.0
long-research holdout accuracy: 0.64
```

The important lesson is the gap, not just the score. The model handles the main
router split, but it still confuses some full investment-research prompts with
`evidence_check`. This gives KIWI a concrete coordinator repair target:

```text
add boundary data
-> evidence_check vs deep_research
-> rerun router eval
-> only then consider a small router fine-tune
```

## Kimi Reference

Kimi k1.5 and Kimi K2 map to two different parts of KIWI.

Kimi k1.5 is most relevant to long reasoning and long2short:

```text
long reasoning trajectory
-> outcome / verifier selection
-> shorter useful answer
```

For KIWI, this becomes:

```text
internal long financial research
-> reviewer / source checks
-> short user-facing decision support
```

Kimi K2 is more relevant to agentic action trajectories:

```text
task
-> tool/action
-> observation
-> correction
-> final result
```

For KIWI, this is the full research workflow:

```text
route
-> search
-> open page
-> read paragraph
-> extract claim
-> compare support/risk
-> reviewer
-> rewrite
-> final answer
```

The interview distinction is:

```text
k1.5 trains long reasoning scaling.
K2 trains agentic action scaling.
KIWI needs both: long internal reasoning, plus recorded tool/action/observation trajectories.
```

Kimi-Researcher adds another lesson: research-agent reward cannot stop at the final answer.

A final answer can look plausible while the evidence chain is wrong. In KIWI, a memo may say "MU is cautiously positive" and still be unreliable if it used stale news, unsupported citations, bad calculations, missing bearish evidence, future data, or a source that never supported the claim.

So the reward/eval target must include the evidence chain:

```text
final answer reward:
  does the result look useful?

evidence chain reward:
  was the result supported by correct, timely, source-grounded evidence?
```

For KIWI, evidence-chain reward should check:

- evidence coverage
- citation correctness
- answer faithfulness
- source quality
- support/risk conflict handling
- calculation correctness
- point-in-time / look-ahead bias
- redundant-search penalty
- risk coverage

The interview version:

```text
Final answer reward tells us whether the output looks good.
Evidence chain reward tells us whether the output was earned by the right sources and actions.
```

In the current long-research pilot this is implemented as:

```text
evidence_chain_eval step
-> evidence_chain_evals.jsonl
-> datasets/memo_quality_scorer/all.jsonl
-> regression/evidence_chain_negative_cases.jsonl
```

The negative cases intentionally keep the final answer plausible while corrupting citation lineage or source timing. This gives the harness a way to catch "right-looking answer, wrong evidence chain" failures.

## Relation to Small Specialist Models

Training comes after architecture stabilization.

The first realistic trainable models are narrow specialists:

```text
router_classifier:
  decide which workflow should run

citation_verifier:
  decide whether a source span supports a claim

risk_reviewer:
  detect unsafe financial framing and downgrade behavior
```

We should not start by training a general financial analyst model.

KIWI's small models should mostly output structured judgments:

```json
{
  "risk_level": "high",
  "risk_flags": ["position_sizing_risk", "overconfident_advice"],
  "requires_human_gate": true,
  "safe_response_policy": "downgrade_to_risk_aware_research"
}
```

The large model remains the coordinator and synthesizer. The small specialists make the system more measurable and controllable.

## Interview Version

In KIWI, post-training is useful not only because we can later train small models, but because it gives us a method for rebuilding the agent system itself.

We turn each agent run into a point-in-time trajectory, split the workflow into checkpoints, and attach verifiers, failure taxonomy, and replayable logs to each node. During trajectory cleaning, we do not just ask whether the final answer was good. We ask which node failed: retrieval, citation, risk review, memory update, routing, or final synthesis. Then we repair the harness, I/O contract, eval gate, and loop behavior before training.

So our process is:

```text
trajectory collection
-> verifier / judge construction
-> failure attribution
-> harness repair
-> specialist dataset export
-> small-model training
-> regression evaluation
```

This makes KIWI a post-training-inspired agent architecture, not just a pile of generated answers.

## One-Sentence Version

We are migrating the post-training loop of data, reward, evaluation, failure attribution, and repair into KIWI's financial research agent architecture.
