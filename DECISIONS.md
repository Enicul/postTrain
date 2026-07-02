# Decisions

## D-2026-06-30-001 - Keep post-training artifact in a separate repo

Decision:

Use `Enicul/postTrain` as the dedicated post-training artifact repo.

Why:

The Agent/KIWI product repo is large and dirty. This interview artifact needs a
clean, pushable, resume-friendly history with data, scripts, checkpoints, and
logs.

Consequence:

Only curated data and reusable scripts should be copied here. Product runtime
work stays in Agent/KIWI.

## D-2026-06-30-002 - CPU baselines before GPU fine-tuning

Decision:

Run cheap sklearn baselines for router, risk reviewer, and citation verifier
before using the A100 for small LLM fine-tuning.

Why:

We need a measurable floor. If a small LLM cannot beat a cheap baseline, the GPU
run is not meaningful.

Consequence:

GPU work starts only after the data and baseline error analysis are clear.

## D-2026-06-30-003 - Train specialists, not one generic financial model

Decision:

Split tasks into narrow specialists: router, risk reviewer, citation verifier,
memo quality scorer, memory gate, and later long2short.

Why:

Small models have limited capacity, and the task types are heterogeneous.
Structured specialist outputs are easier to evaluate, replace, and debug.

Consequence:

The general model remains the orchestrator/synthesizer. Specialists provide
structured checks and scores.

## D-2026-06-30-004 - Do not train calculation verifier first

Decision:

Keep calculations deterministic for now.

Why:

If code can calculate it, a model should not guess it. Models may identify which
calculation is needed, but correctness should be checked by code.

Consequence:

No GPU work on `calculation_verifier` until a separate task family proves that a
model is needed.

## D-2026-06-30-005 - Record learning sources as adopt / not-adopt decisions

Decision:

Maintain `LEARNING_SOURCES.md` as a source-to-system registry.

Why:

The interview artifact needs to show how we learned from GLM, Qwen, DeepSeek,
Kimi, MiniMax, WebExplorer, and other post-training systems without blindly
copying them. Each source should record what we extracted, why it matters, what
we did not adopt, and why it does not fit our current resources or domain.

Consequence:

Any future architecture or training-plan change inspired by an external source
should update `LEARNING_SOURCES.md` before it is treated as a project decision.

## D-2026-06-30-006 - Keep small baseline artifacts in Git for now

Decision:

Keep the current sklearn baseline artifacts, including `model.joblib`, in Git.

Why:

The first tracked training batch is small, about 2.3 MB, and the repo's purpose
is interview-facing reproducibility. Keeping the model files, metrics,
predictions, manifest, events, and checkpoint together makes the artifact easier
to inspect and resume.

Consequence:

If future GPU checkpoints or model files become large, move those to releases,
external object storage, or Git LFS. For now, small CPU baseline artifacts stay
versioned in the repo.

## D-2026-06-30-007 - Citation verifier needs data repair before GPU work

Decision:

Do not start citation-verifier GPU fine-tuning after `citation_verifier_repair_v0.1`.

Why:

The repair probe clarified the failure but did not produce a strong enough
baseline. Adding normalized source URL/domain did not improve the five-way task
meaningfully. The binary any-support task improved macro F1 relative to the
five-way baseline, but it still did not beat the majority baseline on accuracy.
The trace-id leakage probe improved metrics, but trace identity is not a valid
model feature.

Consequence:

The next citation-verifier work should add better data rather than train a
larger model: hard negatives, clean positive official spans, partial-support
boundary cases, and more insufficient/contradict examples.

## D-2026-06-30-008 - Treat v0.2 as data-repair evidence, not GPU readiness

Decision:

Do not start citation-verifier GPU fine-tuning after
`citation_verifier_repair_v0.2`.

Why:

The targeted train-only repair improved the five-way and binary probes, but both
tasks still underperform the majority baseline on test accuracy. The ablation
also showed that adding every synthetic row can hurt the cleaner binary support
boundary, so more synthetic volume is not automatically better.

Consequence:

The next citation-verifier iteration should prioritize audited real evidence
spans: official positive paragraphs, partial-support boundaries, and rare
contradict / insufficient rows. GPU work should wait until the repair baseline
is strong enough to make model capacity the likely bottleneck.

## D-2026-07-01-001 - Real citation spans are a seed, not GPU readiness

Decision:

Use `real_citation_spans_v0.1` as the first real-source seed for citation
verification, but do not start citation-verifier GPU fine-tuning from it alone.

Why:

The collection now has real source URLs, paragraph hashes, support labels, and
clean provenance, but it only contains 29 rows. It proves the data contract and
collection flow, not model readiness.

Consequence:

Before `citation_verifier_repair_v0.3`, expand the pack to at least 100 audited
rows with more SEC filings, earnings transcript spans, official IR releases,
and reputable news paragraphs. Run a CPU baseline/holdout probe before any GPU
LoRA/SFT/DPO work.

## D-2026-07-01-002 - Use filings and public reports, not paywalled report text

Decision:

Expand citation/research data with company filings, earnings releases,
financial tables, transcripts, public industry reports, and reputable news.
Do not store or train on full paywalled sell-side research report text.

Why:

Financial research agents need deeper evidence than headlines. SEC filings,
company IR, transcripts, and public reports provide auditable evidence for
facts, risk factors, management guidance, and industry context. Paid sell-side
reports may be useful as user-provided context or metadata, but storing their
full text in a training repo creates copyright and provenance risk.

Consequence:

Create `report_and_filing_spans_v0.1` under
`citation_contract_repair_v0.1`. Store source URL, section, short evidence
span, source hash, paragraph hash, `published_at`, `as_of`, support label, and
license note. Keep social sources as market radar/task seeds unless backed by
auditable evidence.

## D-2026-06-30-009 - Use summary-first local recording

Decision:

Local runs now default to summary-first recording. Scripts should write metrics,
manifests, checkpoints, phase-level events, capped prediction samples, and capped
error samples. Full row-level predictions, full rollout dumps, and large
checkpoints require an explicit `--record-mode full` or external artifact-store
decision.

Why:

The old protocol was useful for tiny baselines, but full append-only logs and
full prediction dumps can overload the local machine as data grows. The
interview artifact needs enough evidence to resume, audit, and explain failure
decisions, not every row by default.

Consequence:

Future agents should read `docs/RECORDING_PROTOCOL.md` before running
experiments. Git should carry scripts, configs, docs, summaries, small baseline
artifacts, and capped samples. Heavy outputs belong on the server, in object
storage, releases, or Git LFS.

## D-2026-06-30-010 - Treat router v0.1c as contract repair, not GPU readiness

Decision:

Use `router_contract_repair_v0.1c` as the current router repair checkpoint.

Why:

It fixes the most important label-contract gap: the router can now emit
`risk_review` and `clarification_needed`, and real tool trace routing improved
from 0.0 to 1.0 accuracy on the pilot holdout. However, golden social/bookmark
rows still show a separate failure mode where long evidence-verification claims
can be misrouted to `fast_answer`.

Consequence:

The next router work should be social/bookmark boundary repair, not GPU
fine-tuning. Router v0.1c is strong enough to show the data-contract repair loop
in interviews, but not enough to claim production router quality.

## D-2026-06-30-011 - Keep social router repair as candidate, not canonical

Decision:

Do not replace `router_contract_repair_v0.1c` with
`router_social_boundary_repair_v0.1` as the canonical router checkpoint yet.

Why:

The social repair improves the golden router holdout from 0.8895 to 0.9012 and
restores golden safety recall to 1.0, but it regresses real tool trace routing
from 1.0 to 0.9 by misrouting one GOOGL capex/source-support deep-research query
as `evidence_check`.

Consequence:

The current portfolio story should present v0.1c as the canonical router repair
and social v0.1 as a candidate/tradeoff run. The next main work is risk contract
repair; router social work can resume after adding real-tool-style deep-research
anchors.

## D-2026-07-02-001 - Report/filing span pack is the v0.3 candidate input, gated on audit

Decision:

Treat `report_and_filing_spans_v0.1` (102 rows across SEC filings, earnings
transcript pages, public research, and reputable news) plus
`real_citation_spans_v0.1` (29 rows) as the candidate training input for
`citation_verifier_repair_v0.3`. Do not train until a label audit pass over
all 131 rows and a CPU probe under summary recording are complete.

Why:

The pack meets every minimum in the source plan (100+ rows, 30+ SEC, 20+
transcript, 20+ research/news, all four boundary labels present) and adds the
boundary traps the earlier synthetic packs lacked: sequential-vs-YoY
misattribution, segment-vs-total figure swaps, stale-forecast conflicts across
`published_at` dates, and explicit-absence traps. But all labels are manual
contract labels from one collection pass and are marked
`requires_human_audit`; the first collection run already produced one silent
label error from a duplicated filing paragraph (F-2026-07-02-002), which is
exactly the class of error an audit pass must catch.

Consequence:

Next citation steps are audit, then CPU probe, then v0.3 definition. Two
honesty boundaries are recorded in the rows themselves: transcript-tier metric
bullets are the publisher's call summaries (not verbatim speaker text), and
paywalled sell-side research remains excluded.

## D-2026-07-02-002 - Adopt the three-task ladder plan as the portfolio spine

Decision:

Adopt `docs/THREE_TASK_LADDER_PLAN_20260702.md`: three tasks (risk reviewer,
citation verifier, cost-aware escalation router) climb one shared ladder
(rules -> sklearn -> naive prompt -> engineered prompt -> prompt + experience
library -> SFT -> GRPO) on frozen holdouts, with pre-registered kill criteria
deciding where each task stops. Rungs 5-6 (weights) are budgeted for exactly
one task. Act 3 is a two-to-three step escalation policy, not single-step
route classification, and GRPO must beat both the best prompt arm and
argmax-label SFT to claim justification.

Why:

The repo so far has verifiers, frozen holdouts, and failure discipline, but
zero LLM columns - while the interview story requires "RL model vs plain LLM
vs prompt-only", all verifiable. Single-step discrete routing with an
enumerable reward would let argmax-label SFT match GRPO, silently collapsing
the RL act; the escalation reformulation is what gives weight RL structural
room. Pre-registered kill criteria are what make negative results (prompting
was enough / training-free was enough / GRPO not worth it) first-class
deliverables instead of failures to hide.

Consequence:

- Block A first: audit the 131 real citation rows (freeze
  `citation_real_eval_v1`) and build `risk_contract_repair_v0.1b`; no LLM arm
  is measured on a broken ruler.
- The rollout store (`rollout_store_v0.1` schema in the plan) is declared a
  bounded row-level DATA ASSET - an explicit, intentional exception to
  summary-first recording.
- Experience libraries stay injectable and versioned; only
  regression-stable lessons get promoted into permanent harness patches, each
  promotion logged here.
- Act 3 hard budget cap: 24 A100-hours / ~USD 100 / 5 evenings for rungs 5-6;
  exceeding the cap without a win is itself the recorded result.

## D-2026-07-02-003 - Freeze citation_real_eval_v1 and bind conventions C1-C3

Decision:

Freeze the audited 131-row pack as `citation_real_eval_v1`: dev (38) + test
(31) are the Act 2 evaluation splits; test is untouchable; prompts and
experience libraries iterate on train/dev only; any dev/test change requires
a new eval id. Conventions pinned by the audit become part of the citation
contract: C1 conflicted-subclaim precedence, C2 period binding, C3
materially-weakens. Downstream consumers use this pack, not the raw
collection packs, which remain as historical evidence.

Why:

Blind double annotation confirmed 126/131 labels and corrected 3; two of the
three corrections overrode labels authored in the same session, which is
exactly the failure mode a blind protocol exists to catch. An unaudited or
convention-ambiguous eval would make every ladder column on Act 2
unjudgeable.

Consequence:

Act 2 measurement can start once Block B runs; the audit trail (two vote
files + adjudications) ships inside the pack; future span collections must
follow C1-C3 or propose a contract revision here first.

## D-2026-07-02-004 - Freeze risk_real_eval_v1 under conventions R1-R5

Decision:

Freeze the audited 90-row real risk eval (`risk_contract_repair_v0.1b/
risk_real_eval_v1`; dev 38 / test 52; high 33 / medium 48 / low 9; 45 gated)
as the Act 1 ruler, under pinned conventions R1-R5: decision-risk semantic
with an explicit red-line list, gate definition, evidence-review rows rate
the acted-on claim (R3), single-name research requests are medium (R4), and
provenance-mechanical train sync (R5). Test is untouchable; prompts and
experience libraries iterate on train/dev only.

Why:

The old risk rulers were unusable for ladder judging: the 25-row
long-research holdout was degenerate (all medium, all gated - an
always-medium arm scores 1.0), and blind double annotation showed the three
real generators encoded three different risk semantics (18.9% eval
correction rate), including v0.1 synthetic labels that violated v0.1's own
documented boundary. A ruler that disagrees with itself cannot produce the
honest per-arm comparison the ladder exists for.

Consequence:

- `risk_contract_repair_v0.1b` replaces v0.1 as the canonical risk repair;
  v0.1 remains historical evidence.
- Probe evidence: medium transfer repaired (0.0 -> 1.00 recall on audited
  real rows), while high/gate recall 0.64-0.73 shows the sklearn rung is not
  a safe gate - the measured headroom for the rules/prompt/LLM arms.
- Two adjudications kept gold against 2/2 auditor votes under R3; both are
  flagged for cheap human spot-check alongside the citation audit's five.
- Any new risk data family must pass through the normalizer plus a blind
  audit round before touching the eval.

## D-2026-07-02-005 - Act 2 killed at rung 3; Act 1 continues; anonymized eval ids mandatory

Decision:

(1) Citation verification is resolved at the engineered-prompt rung for
frontier-family models: prompted claude-haiku-4-5 scores 0.957 on the frozen
69-row eval, above the pre-registered rung-4 kill bar (0.85), so Act 2 stops
- no experience library, no SFT/GRPO for citation at this scale. A small
LOCAL verifier for cost/privacy is explicitly a separate future decision.
(2) Risk continues to rung 4: every engineered arm hits gate recall 1.000
(safety half of the kill criterion passes) but best accuracy is 0.811 < 0.90;
the rung-4 candidate is a rules-for-gate + LLM-for-level hybrid or experience
library aimed at the low/medium boundary. (3) All future eval batches shown
to any model must use anonymized row ids (F-2026-07-02-006).

Why:

Pre-registered kill criteria plus measurements, not preferences: the
citation contract turned out to be promptable once written precisely (the
audit that pinned C1-C3 is what made the prompt work); risk's residual
low/medium boundary is real headroom; the id leak measurably inflated
results (+11.6 points) and must be structurally prevented.

Consequence:

The portfolio narrative gains its first completed act with an honest
negative ("we did not train a citation model, and we can show why"), and the
ladder's remaining budget concentrates on risk rung 4 and the Act 3
escalation environment.

## D-2026-07-02-006 - Owner policy: red-line claims always gate; Act 1 killed at rung 4

Decision:

(1) Product policy, decided by the owner on the escalated R3 dispute: an
evidence review whose CLAIM embodies red-line pitch language (tenbagger
promises, FOMO tips) requires the human gate even when the review's verdict
rejects the claim - defense-in-depth for a financial product. The two
contested eval rows keep their gold labels; the policy is enforced by
deterministic gate rules v1.1 in code. (2) With that floor in place, Act 1
is KILLED at rung 4: hybrid sonnet 0.978 accuracy / 1.000 gate recall / 0
false gates meets the pre-registered kill criterion. Risk review gets no
weight training.

Why:

Four independent model judgments disagreed with the adjudicator's keep on
those two rows; rather than silently re-labeling (tuning the ruler to the
arm) or silently overruling the models (baking one person's judgment into a
lesson), the call was escalated to the human owner as the audit record had
recommended. The owner chose conservatism; the implementation puts the
safety floor in versioned code where prompt iterations cannot erode it.

Consequence:

Two acts closed without training, each with a full dissent/decision trail.
Act 3 (cost-aware escalation router) holds the sole weights budget. The
ladder's operating notes gain a rule: contested label conventions are
escalated to a human before lesson-extraction rounds, not after.
