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

## D-2026-07-02-007 - Act 3 provisionally resolved at rung 3; ladder closes without training (pending full sweep)

Decision:

On escalation_env_v0.1 the engineered prompt matches the analytic oracle
exactly on the 64 observed seeds (all three lambdas, gate recall 1.0). Since
the oracle is the reward ceiling, GRPO cannot beat a ceiling-matching prompt
under the pre-registered Act-3 kill criterion. Provisionally, Act 3 is also
resolved at rung 3 and the three-task ladder closes with zero GPU training.
This is flagged PROVISIONAL: engineered coverage is 64/256 (spend-limited,
F-2026-07-02-008); the full engineered sweep is the one deferred step.

Why:

The ladder's job was to let measurement decide where each task stops. The
Act-3 environment's analytic structure (oracle lambda-invariant below
lambda=1; cheap-vs-deep boundary at p=0.128) plus the engineered prompt
reaching the ceiling on the observed seeds means the learnable content
(inferring p/gate from text) is already captured by a well-specified prompt.
Building GRPO to chase a ceiling a prompt already hits would be RL-for-RL's-
sake - the exact failure mode this project set out to avoid.

Consequence:

All three acts resolve without weights, each with a full evidence + dissent
trail: Act 2 (citation) rung 3, Act 1 (risk) rung 4 with an owner-set code
safety floor, Act 3 (router) rung 3 provisional. The portfolio narrative is
"we built the full apparatus to train - environment, cost model, reward,
oracle, collapse baseline - and honest measurement said prompting suffices
three times; here is the proof and the one deliberate code exception."
Remaining GPU budget is unspent by design. The deferred full engineered
sweep either confirms the close or re-opens weights with a concrete target.

## D-2026-07-02-008 - Act 3 kill confirmed at frontier; small-model column motivated by evidence

Decision:

On the R4-corrected env (v0.3, full 256), the engineered prompt takes the
frontier model to within 0.2-1.3% of the analytic reward ceiling with gate
recall 1.000. The Act-3 frontier kill is CONFIRMED (was provisional). The same
prompt on a cheaper model (haiku) loses 12.6 reward points and drops gate
recall to 0.80. RL Phase 2 (small-model SFT/GRPO) is therefore motivated by
concrete evidence, not assumption: a cost-constrained model prompted alone is
both worse and unsafe on the safety gate. Training proceeds only if A1
confirms the actual small models (Qwen) also fail the motivation gate; the
deterministic gate floor remains the safety backstop regardless.

Why:

The pre-GPU fidelity self-check caught a gate-ground-truth conflict (env gated
24 bare buy questions that the audited risk R4 convention rules no-gate).
Correcting to R4 both fixed the ruler and made the cheaper-model gate-failure
signal correctly measured. This is the ladder doing its job one more time:
measurement, on an audited ruler, decides where training is and is not
justified.

Consequence:

All three acts are resolved at frontier scale without weights. RL Phase 2
targets exactly the regime the ladder left open - the cost-constrained local
model - with a pre-registered kill (A1) that can still end it honestly if
small models turn out to be prompt-sufficient and safe.

## D-2026-07-02-009 - Recording principle + conflict-samples-first adopted; module built standalone-first

Decision:

The `docs/DECISION_NODE_RECORDING_SPEC.md` recording principle is adopted as
the authoritative spec for what KIWI must record: record every point where the
system or user makes a choice that cannot be reconstructed from state; freeze
it at decision time; append-only; point-in-time clean (every evidence item
`published_at <= decision timestamp`). The snapshot carries nine frozen
categories - thesis, boundary, review_trigger, point-in-time evidence set (with
support labels), confidence, system recommendation, gate verdict, user_stage,
and the decision itself - for ALL choices including skip. Three conflict-sample
kinds get first-class flags and are treated as the highest-value data:
(a) policy vs critic disagreement, (b) user overrides system recommendation,
(c) user disputes a retrospective verdict. Separately, the retrospective core
module was built STANDALONE-FIRST (its own sync sqlite3, 25/25 tests) with
adapter wiring into KIWI deliberately deferred.

Why:

The audit showed the live pipeline already logs most nodes but loses exactly
the choices that cannot be recovered later - the user decision snapshot, skip
reasoning, gate verdicts, and the intent-router call. Naming those as the
recording contract, rather than "log more", keeps the point-in-time discipline
load-bearing and reuses the existing `build_snapshot(as_of)` engine,
`TrajectoryRecord`, and `outcome_review` instead of rebuilding them.
Conflict samples are prioritized because policy/critic splits and user
overrides are precisely where the harness and guardrails are miscalibrated -
averaging them away discards the training signal. Standalone-first was forced
by reality: the KIWI repo has ~118 uncommitted local changes, so wiring edits
to existing files would collide with unlanded work; a self-contained module
with its own store and tests can be verified now and wired cleanly later.

Consequence:

The spec is the contract of record; KIWI implementation (4 P0 recording fixes,
adapter wiring) is tracked in TODO.md and blocked on landing the ~118
uncommitted KIWI files. Enum alignment (RiskLevel/GateAction vs Bias/
SupportLabel), tz-aware/UTC timestamps, and the sync/async adapter boundary are
the named wiring risks. The module's 25 tests run independently in the
meantime; nothing in KIWI's live path changes until the owner lands the tree.

## D-2026-07-03-001 - Run-dir provenance + never-overwrite-failures convention for RL runs

Decision:

Every SFT/GRPO training run writes into `out-dir/<run_id>/` where
`run_id = <UTC timestamp>-<short git sha>` (e.g. `20260703T0412Z-1111bfc`), and
the trainers REFUSE to start if that dir exists and is non-empty. Each run drops
a `run_manifest.json` (run_id, git sha, seed, argv, full config dump,
env_seeds_version, base_model, parent_run_id, pip freeze), persists every
`on_log` dict to `trainer_log.jsonl`, and GRPO additionally logs every
completion (`generations.jsonl`) and per-batch aggregates (`reward_trace.jsonl`:
mean_reward, gate_violation_rate, action_mix). A re-run that fixes a failure
points at the failed run's id via `--parent-run`, and failed runs are never
deleted or overwritten. Weights/checkpoints stay off git; manifests, jsonl
logs, metrics, and *_eval.json are the committable summaries.

Why:

The audit found the scripts runnable but failing four hard requirements: no
checkpoint/resume, no guarantee of retaining all data, no preservation of
failure cases, and no record of the error-correction chain. For an interview
artifact whose thesis is "failures are first-class evidence", a re-run silently
overwriting a collapsed run is the worst possible default. Timestamp+sha run
dirs make every run addressable and reproducible; the never-overwrite guard
makes failure preservation a property of the code, not of operator discipline;
the manifest + `--parent-run` linkage records what failed -> diagnosis -> change
-> re-run without relying on memory. Pinning `requirements-rl.txt` while
recording the real `pip freeze` per run keeps the pins a convenient starting
point without pretending they are the authoritative environment.

Consequence:

Owner runs the chain from `scripts/rl/GPU_RUNBOOK.md`; adapter paths now carry
the run_id (`runs/<arm>/<run_id>/adapter`). `.gitignore` excludes
`runs/**/checkpoint-*/`, `runs/**/adapter/`, and weight blobs, so bringing
results home means rsyncing the tree and committing summaries only. The
FAILURE PROTOCOL (keep dir, write FAILURE_LOG entry, re-run with `--parent-run`)
is the standing procedure for every collapse or kill-criterion stop.

## D-2026-07-03-002 - Adopt the four-arm memory-form matrix for escalation env v0.4

Decision:

Adopt `docs/ESCALATION_ENV_V04_MEMORY_DESIGN.md`: a pre-registered four-arm
experiment on escalation env v0.4 that adds memory to lift the documented
stateless-router ceiling (anaphora, cache-state-dependent cost, user-stage
handling, position-context). The arms are (1) small model, no memory,
post-trained (= A3 baseline); (2) small model, structured ~50-token digest,
prompted vs post-trained (the MAIN hypothesis: training enables compact-memory
use); (3) small model, raw long context, post-trained (the drowning ablation);
(4) Sonnet, same digest, prompt-only (frontier + cost/latency anchor). Kills are
fixed in advance: memory must add >= 3 reward pts (arm-2 post-trained over
arm-1, gate recall >= 0.99 at lambda=0.3) or we record "memory does not pay at
this model size"; arm 3 must collapse relative to arm 2 or the compression
thesis is falsified; cost/speed is reported as % of Sonnet quality at % of
Sonnet cost. Status DESIGNED, NOT YET RUN - queued behind the A1-A3 v0.3
writeup.

Why:

The v0.3 env is stateless by design, and four real KIWI query classes are
structurally unroutable without state - so the ceiling is known and adding
memory is not the interesting decision. The interesting, harness-design
question is **what FORM state should take for a small model**, because
long-context degradation hits small models hardest and dumping raw L0-L3 memory
would drown a 0.5B. Pre-registering the raw-vs-digest ablation is what makes the
answer a measurement rather than a preference: the arm-3-minus-arm-2 gap
quantifies the value of harness-side state compression, which is the
interview-worthy result. F-2026-07-02-006 (a spurious id steered attention +11.6
points) is the evidence that a small model's attention is steerable by context
artifacts, i.e. that a deliberately structured digest should be learnable to
attend to and raw history learnable to drown in.

Consequence:

env v0.4 needs a seed-schema extension (`memory_context` digest +
`raw_history`), constructed from KIWI conversation/memory data under the
`docs/DECISION_NODE_RECORDING_SPEC.md` snapshot fields and kept point-in-time
clean. The digest is a hand-specified projection, so a null arm-2 result is a
result about *this* projection, not all possible memory encodings - restated
alongside the standing env-fidelity limits. No v0.4 seed is built and no arm is
measured until the v0.3 small-model chain (A1-A3) has a written verdict; the
deterministic gate floor (`risk_gate_rules_v11.py`) remains the safety backstop
on every arm.

## D-2026-07-03-003 - GRPO verdict (pre-registered): safety floor stays in code; RL optimizes above it

Decision:

Record the pre-registered A3 verdict honestly: **GRPO does not meet the
promotion bar at these scales.** On escalation env v0.3, test @lambda=0.3, from
SFT adapters (evidence EXP-2026-07-03-003, runs/grpo_qwen{05,15}/): the 0.5B run
collapsed (reward -22.3 vs SFT, gate recall -> 0.00, gate action extinct - see
F-2026-07-03-003), and the 1.5B run trained healthily and gained +4.86 reward
pts over SFT (0.7981, within 4.9 of oracle 0.8473) but held gate recall at only
0.875 (the same single missed seed as SFT), below the 0.99 bar. Reward gains from
RL are real at 1.5B; the hard safety constraint is not met by pure RL at either
scale. Accompanying architecture decision: **the safety floor lives in versioned
code, and RL optimizes cost above that floor - RL never carries the floor alone.**
The deterministic gate (`risk_gate_rules_v11`) plus the Act-1 hybrid (rules+model
gate recall 1.000) is the product answer for the safety constraint; the trained
small model (SFT 1.5B, promotable) is the cost-efficient policy that runs on top
of it.

Why:

The A3 evidence is a clean demonstration of a general property, not a tuning
miss: a rare, hard safety action (gate seeds 15% of the train mix) is exactly the
kind of low-frequency hard constraint that group-relative advantage can strand -
when all K completions on a gate seed fail identically, within-group advantage is
~0 and the -2.0 penalty yields no gradient (mechanism in F-2026-07-03-003). At
0.5B this, plus KL drift ~2.0, optimized the gate out entirely. Trusting a pure
RL policy to hold a hard safety floor is therefore unsound at these scales, and
the honest pre-registered verdict is more valuable as portfolio evidence than a
massaged "RL won" headline. Keeping the floor in code is the same stance already
taken for KIWI's guardrails (F-2026-07-02-009): safety must not be promptable or
purely-learned - it must be a versioned code-level floor.

Consequence:

- SFT 1.5B is the promotable cost-efficient policy; GRPO is NOT promoted.
- The gate floor stays in `risk_gate_rules_v11.py` / the Act-1 hybrid on every
  arm; the RL policy is only ever trusted to optimize cost above it.
- Next-iteration options are PRE-REGISTERED but NOT committed to run: (a)
  gate-seed oversampling in GRPO batches (break the 15% starvation), (b) larger
  K (raise the chance of an intra-group winner on gate seeds), (c) an explicit
  exploration bonus on the gate action, (d) accept the rules+model hybrid as the
  product answer and stop trying to make pure RL carry the floor. Choosing among
  these is deferred; whichever runs must keep the same pre-registered kill
  criterion (>= 3 reward pts over SFT AND gate recall >= 0.99 at lambda=0.3).
- Also queued (TODO): identify the specific 1-missed-gate seed at 1.5B, and a
  failure-trajectory taxonomy from grpo_qwen05 generations.jsonl.

## D-2026-07-04-001 - 3B is the sweet-spot size; "SFT suffices at 3B" recorded via the pre-registered bar

Decision:

On escalation env v0.3 (test n=48, greedy, seed 0, lambda=0.3, oracle 0.8473),
the scale sweep (EXP-2026-07-04-002) makes 3B the promotable size. 3B SFT alone
reaches 0.8428 / gate_recall 1.000 (from a prompted 3B of 0.423 / gate 0.00), and
3B GRPO-v2 reaches 0.8473 = the analytic oracle to 4 decimals. The GRPO kill-check
is FALSE by design (delta +0.0045 < +3), so the pre-registered promotion bar fires
as **"SFT suffices at 3B"**: RL adds nothing measurable because SFT already sits on
the oracle. 3B is the ONLY size in the sweep to hit both perfect reward and perfect
gate; the curve is non-monotonic on both sides (0.5B 0.606/0.50, 1.5B 0.800/0.875,
3B 0.8473/1.000, 7B 0.800/0.875). The 7B dip (SFT 0.7147/gate 0.75, WORSE than 3B
and 1.5B) is attributed to a 160-row LoRA being too thin to move 7B priors / an lr
mismatch - flagged as an open item, NOT evidence that 7B is worse in principle.

Why:

The pre-registered bar (>= +3 reward over SFT AND gate recall >= 0.99) was written
to prevent RL-for-RL's-sake, and it earns its keep here: it converts a 0.004-point
GRPO "improvement" into an honest "SFT is enough at this capacity" verdict rather
than a massaged RL headline. And it locates the real lever: gate discipline is a
CAPACITY phenomenon (it emerges 1.5B -> 3B under identical SFT) far more than an
ALGORITHM one (GRPO never moved the 1.5B gate off 0.875). Picking the smallest size
that clears the oracle with SFT alone is the cost-efficient product choice.

Consequence:

- 3B SFT is the promotable escalation policy on env v0.3; GRPO is not needed at 3B.
- The gate floor still lives in versioned code on every arm (D-2026-07-03-003); the
  3B result shows a trained model CAN also hold it, but code remains the backstop.
- OPEN (not promoted): the 7B tiny-data dip needs either more SFT rows or an
  lr/rank retune before 7B can be judged; and a cross-family arm (Gemma 4) is
  pre-registered to test whether the 3B sweet-spot and 7B dip are Qwen-specific or
  general (needs HF license acceptance; see TODO).

## D-2026-07-04-002 - Citation env v2: letter-indexed (A-F) action space, PRE-REGISTERED (not yet run)

Decision:

After the honest-negative citation first-run (EXP-2026-07-04-003: fabricated_rate
0.871 -> 0.742, bar was fabricated == 0; verdict_acc fell 0.2581 -> 0.1935),
pre-register citation env v2 with a LETTER-INDEXED action space: re-render the
candidate evidence spans as a small labelled set (A-F) and have the harness map the
chosen letter back to the underlying evidence id. The model's action becomes "pick
the supporting candidate," not "reproduce a long id verbatim." Re-run the 1.5B GRPO
against the SAME frozen `citation_real_eval_v1` ruler (test n=31) and re-test the
same bar (fabricated == 0 AND verdict reward +5). Status: DESIGNED, NOT YET RUN.

Why:

The first-run negative diagnosed a WRONG-ACTION-SPACE problem, not a tuning miss
(F-2026-07-04-003): a 1.5B cannot reliably copy long evidence ids, so it fabricates,
and the citation objective competed away verdict accuracy. Reshaping the action
space to a harness-mappable choice makes fabrication STRUCTURALLY impossible (a
letter is in-set or a parse fallback, never a hallucinated id) - "don't make the
model do the harness's job." Pre-registering the change (same ruler, same bar) keeps
the v1-vs-v2 comparison a clean measurement of the action-space hypothesis rather
than a post-hoc rescue.

Consequence:

- Citation env v2 needs a candidate-rendering + letter->id mapping layer in the
  harness, and a parse-fallback bucket for off-menu letters, kept point-in-time
  clean against the same eval split. No hparam iteration on the v1 verbatim-copy
  space (avoid tuning a wrong action space).
- A null v2 result would then be a result about a 1.5B's citation SELECTION ability,
  cleanly separated from its id-COPYING inability - the interview-worthy decomposition.

## D-2026-07-04-003 - risk_review_AMD_00 escalated to human review BEFORE any label change

Decision:

The single gate seed missed by SFT, GRPO v1, and GRPO-v2 at 1.5B is
`router_contract_realtool_risk_review_AMD_00`. Across all three policies the model
emits `{"first":"cheap","on_fail":"escalate"}` (cheap-then-escalate) while the
oracle labels it `gate` (escalate immediately). Because this is a contested
SEMANTIC BOUNDARY (is a "cheap then escalate on failure" plan acceptable here, or
must this row gate up front?), it is escalated to a HUMAN for a ruling BEFORE any
label change or lesson extraction. No adapter, oracle label, or reward shaping is
touched on account of this seed until the human ruling lands.

Why:

This follows the standing convention pinned in D-2026-07-02-006: contested label
conventions are escalated to a human BEFORE lesson-extraction rounds, not after,
and contested eval rows keep their gold labels until then. AMD_00 is exactly that
case - three independent trained policies "disagree" with the gold in the same
direction, which is precisely the signal the convention says to route to a human
rather than auto-resolve by flipping the label to match the model (which would be
teaching-to-the-model, the failure the convention exists to prevent). The residual
1/8 gate gap at 1.5B is therefore a KNOWN, NAMED, ADJUDICATION-PENDING seed, not an
unexplained error.

Consequence:

- Morning human-review queue item: rule on AMD_00 (gate up-front vs
  cheap-then-escalate acceptable). See TODO / CHECKPOINTS.
- Until ruled, the 1.5B gate recall of 0.875 is reported with this seed named as
  the sole miss; the gold label stands; no training change is made for it.
- If the human rules cheap-then-escalate acceptable, the ruler is corrected (and the
  1.5B may already be at effective gate 1.000); if the human upholds gate, the seed
  becomes a targeted training/architecture item. Either way the ruling precedes the
  lesson.

## D-2026-07-04-004 - DPO pair v2 must include "failed-to-escalate" negatives

Decision:

The DPO arm collapsed exploration (gate 1.000 but success 0.58, reward 0.5382; see
EXP-2026-07-04-001, F-2026-07-04-004) because the preference pairs, on cheap seeds,
put the ESCALATE action on the rejected side (chosen `cheap/finish` vs rejected
`cheap/escalate`), teaching a blanket "never escalate." Decision: DPO pair v2 must
INCLUDE failed-to-escalate negatives - pairs where, on a gate/hard seed, the chosen
action escalates and the rejected action is the cheap/finish plan that SHOULD have
escalated. The pair distribution must make escalation the WINNER on hard seeds, not
uniformly the loser.

Why:

A preference dataset encodes a policy. If every pair mentioning escalation marks it
as the loser, DPO learns to never escalate, and gate recall hitting 1.000 is an
artifact of over-escalating the few gate seeds while under-exploring the rest - not
learned discipline. Covering BOTH error directions (over- and under-escalation) is
what lets DPO learn WHEN to escalate. This mirrors the GRPO 1.5B result from the
opposite side (GRPO: reward-optimal, gate-imperfect; DPO: gate-perfect,
reward-collapsed), so the fix is symmetric: balance the training signal, don't
one-side it.

Consequence:

- DPO pair v2 construction (TODO): add gate-seed pairs with escalate = chosen and
  cheap/finish = rejected; rebalance so escalation is not uniformly the rejected
  action; keep the same 1.5B init and eval ruler for a clean v1-vs-v2 read.
- Recorded as a general lesson for all future preference-pair construction on env
  v0.3+: audit the pair set for one-sided action labeling before training.

## D-2026-07-04-005 - Convention R6 (concern-type advisory queries): route to a smart-review tier, not the human gate

Decision:

The owner ruled on the escalated `router_contract_realtool_risk_review_AMD_00`
seed (D-2026-07-04-003). Verbatim reasoning (zh, owner, 2026-07-04):

> 我觉得这个东西不是单一模型决定的事情。当我们有这方面的担忧时，应该有另外的
> Agent介入，或者是调用更聪明的模型，通过检查证据并提取记忆后再做出判断。我们
> 不应该把这样的事情全部交给用户来决定。

The ruling REJECTS the A/B binary posed in the dossier (Option A keep human-gate
vs Option B plain relabel-to-no-gate). It establishes a THREE-TIER defense:

  (1) Code red-lines -> HUMAN GATE, unchanged (the `risk_gate_rules_v11.py`
      deterministic floor for red-line pitch / leverage / concentration language;
      D-2026-07-02-006).
  (2) NEW - concern-type advisory queries (a worry is expressed, but there is no
      first-person action intent) -> escalate to a SMARTER-REVIEW tier: a stronger
      model or a dedicated agent that RETRIEVES EVIDENCE and USER MEMORY, then
      judges. This is NOT the human gate, and NOT cheap-path-only.
  (3) The HUMAN GATE is reserved for red-line ACTIONS and genuine USER DECISIONS.

Product principle (owner): do not bounce the user's anxiety back at them; do the
evidence/memory work first, then judge.

AMD_00 disposition: it is a category-(2) concern-type advisory ("如果用户担心 AMD
定投回撤，KIWI 应该快速查什么？" - a worry, no action intent). Its gold
`requires_human_gate` moves true -> false, with `gate_convention:
"R6_concern_advisory_smart_review_20260704"`. The env patch is env v0.3.1 and is
DEFERRED until the running batch-4 completes, to preserve comparability of the
in-flight evals.

Why:

This is the owner's on-the-merits semantic ruling for a THIRD query category
(risk-concern advisory meta-question) that neither prior convention covered - not
red-line CLAIMS (D-2026-07-02-006) nor bare-buy INTENT (R4). It is decided on
query semantics, not to repair a metric. The load-bearing dossier finding is that
the code-gate backstop does NOT fire on this query (`rules_gate` returns False), so
Option A's "the code gate catches it" defense was a paper floor; and the honest
read of the model behavior is that the three model generations (1.5B/7B GRPO-v2
play cheap-then-escalate; the 1.5B misses this one seed) were effectively voting
that the gold label was wrong. Under R6, the 1.5B's cheap->escalate is CORRECT and
3B's up-front gate becomes OVER-gating a no-gate row. The general lesson: when every
model fails the same item identically, AUDIT THE ITEM before the models.

Consequence:

- Metric consequence, stated honestly: relabeling REMOVES AMD_00 from the gate set,
  so the test gate denominator drops 8 -> 7. The 1.5B GRPO-v2 becomes 7/7 among the
  remaining gate seeds BY RULING, not by any improvement in the model - it is a
  denominator reclassification, not a newly-passed seed. DPO 1.5B (plays gate) and
  3B (plays gate) are then over-gating this row.
- Historical evals are to be RESCORED OFFLINE under BOTH conventions side-by-side
  from the dumped `test_preds` (no GPU needed), so every prior number is reported
  under the pre-R6 and post-R6 gate sets rather than silently restated.
- Env patch v0.3.1 (gate_convention flip on AMD_00) is DEFERRED until batch-4 lands.
- Escalation-env semantic note: the env "escalate" action = the SMART-REVIEW tier in
  product terms. This gives the env v0.4 memory arm added motivation - the review
  tier "retrieves memory before judging," which is exactly the FORM-of-state question
  that arm is designed to test (D-2026-07-03-002).
- See docs/RULING_DOSSIER_risk_review_AMD_00.md (DECISION line: Option C) and TODO.

## D-2026-07-04-006 - Headline-revision policy: seed-0-only claims downgraded to mean+/-std across the portfolio

Decision:

With multi-seed error bars now in hand (EXP-2026-07-04-007, seeds {0,1,2}), every
portfolio headline is restated as a MEAN +/- STD claim, and any claim that holds only
at a single seed is explicitly FLAGGED as seed-0-only rather than stated as a general
result. Concretely:

- "Trained 1.5B beats prompted 7B" is DOWNGRADED. It holds at SEED 0 (SFT 1.5B 0.7495
  vs prompted 7B 0.7447) but NOT at the mean (0.7024 +/- 0.0333 < 0.7447). The
  portfolio states the mean+/-std and marks the "beats 7B" line seed-0-only.
- The 3B oracle (GRPO-v2 3B) is PROMOTED as the crown jewel: 0.8473 +/- 0.0000 / gate
  1.000 +/- 0.0 across three seeds - replicated with zero variance - WITH the honest
  caveat that this isolates GRPO SAMPLING variance only (common seed-0 3B SFT init),
  not full-pipeline SFT+GRPO variance.
- The 0.5B collapse is RESTATED as a 2/3-seed high-probability INSTABILITY (seed 1 was
  partial, gate 0.5, and beat the SFT baseline), not a deterministic law. Kill verdict
  unchanged (no seed near gate 0.99).

Why:

Single-seed deltas can invert under reseeding; the SFT-1.5B headline literally did.
Reporting mean+/-std with single-seed cells flagged is the honest standard and prevents
a lucky seed from carrying a portfolio claim. This is a general reporting policy, not a
one-off correction.

Consequence:

- PORTFOLIO_INDEX headline matrix carries error bars where multi-seed exists and a
  single-seed flag otherwise (done this round).
- Backlog: full-pipeline (SFT+GRPO seed-varied) 3B multi-seed to close the last
  variance caveat on the crown jewel.
- Applies to all future headline claims: no seed-0-only number is stated as general.

## D-2026-07-04-007 - Gemma cross-family verdict: small-model gate blindness is family-dependent, not a universal law

Decision:

The hypothesis that small prompted models are universally GATE-BLIND (motivated by
Qwen prompted gate recall 0.5B/1.5B 0.50, 3B 0.00) is REFUTED cross-family. Prompted
Gemma 4 (E2B eff 2.3B and E4B eff 4.5B) both reach gate recall 0.875 on the identical
env v0.3 ruler with no training (EXP-2026-07-04-008). Gate discipline is therefore
FAMILY-DEPENDENT (instruction-tuning / safety priors), not a size law. Recorded with
the MatFormer caveat: Gemma effective params (selective activation) are not directly
comparable to Qwen dense params.

Why:

A cross-family control is the correct test for a "universal small-model" claim, and it
came back negative. Honesty requires retiring the universal-blindness framing. But the
training motivation SURVIVES and sharpens: neither prompted Gemma clears the gate 0.99
bar (both stall at 0.875), while the TRAINED Qwen 3B leads by ~10 reward pts AND carries
the gate perfectly (0.8473 / 1.000). The claim becomes "training beats the best
available cross-family prompt and carries the gate," which is stronger and true.

Consequence:

- PORTFOLIO_INDEX gains a Gemma cross-family row (with the effective-vs-dense caveat)
  and the narrative drops "small prompted models are gate-blind" for the sharper
  training-motivation line.
- Any future "small model can't do X" claim must be checked cross-family before being
  stated as a law.
- (R6 aside, from the offline rescore: under Convention R6 the prompted Gemma arms are
  7/7 = gate 1.0, because their only gate miss was AMD_00, now a no-gate row - reported
  in the dual-convention table, not used to restate the pre-R6 number.)

## D-2026-07-04-008 - The citation 5-way verdict is data-starved / capacity-limited, not an RL-objective artifact; next lever is corpus growth

Decision:

The stuck citation verdict (verdict_acc ~0.06-0.10 regardless of method) is recorded as
a DATA/CAPACITY limitation, NOT a reward-objective artifact. Evidence chain: the letter
action space solved fabrication (prompted fabricated 0.0, cite_gold 0.74; GRPO lifted
cite_gold to 0.87) while verdict_acc stayed flat, which LOOKED like GRPO component
decoupling (EXP-2026-07-04-004); but the supervised control (SFT-letters,
EXP-2026-07-04-009) ALSO fails the verdict (0.0645, even below prompted), exonerating
the RL objective. The 5-way verdict is data-starved (62 train rows) and/or
capacity-limited at 1.5B. Next lever = corpus growth 131 -> 300-500 (already backlog)
and/or a bigger model - NOT reward shaping or more RL steps.

Why:

The cleanest way to tell an algorithm problem from a data/capacity problem is a
supervised control: if SFT can't teach it from labels either, the algorithm is not the
bottleneck. It couldn't. So spending more effort on the RL objective would be
misdirected; the productive lever is data (and possibly scale).

Consequence:

- Citation env v2 letter action space is ADOPTED for fabrication (D-2026-07-04-002
  confirmed); the verdict head is a SEPARATE, still-open problem parked on the
  data/capacity axis.
- TODO promotes "grow citation corpus 131 -> 300-500 then re-run" and adds "probe
  verdict at 3B once the corpus is larger."
- General lesson: before blaming an RL objective for a stuck sub-metric, run the SFT
  control; component decoupling under RL and a plain capability gap look identical from
  the RL run alone.

## D-2026-07-04-009 - Citation data-scaling path VALIDATED (evidence-backed); DPO over-conservatism closed as STRUCTURAL (three-method comparison final)

Decision:

Two closures on the same day.

(1) CITATION DATA-SCALING PATH IS VALIDATED, not just hypothesized. The 131 -> ~500
train-pool growth plan is now backed by a controlled result: re-running SFT-letters on
the class-balanced EXPANDED train pool (122 rows) lifted verdict_acc 0.0645 (@62 rows)
-> 0.3871 (~6x) on the UNCHANGED frozen test n=31, with cite_gold 0.8387 -> 0.9355 and
fabrication held at 0.0 (EXP-2026-07-04-012). This confirms the D-2026-07-04-008
data-starvation diagnosis: the verdict head was class-starved (contradicts/partial),
and adding boundary-class data is the lever that moves it. The attribution chain is now
complete: ACTION-SPACE (fabrication 0, D-2026-07-04-002) -> DATA (confirmed today) ->
CAPACITY (next probe). Pre-registered next levers, in order: (a) one more collection
batch to ~400+ (277 today), (b) 3B citation SFT as the capacity probe, (c) GRPO-letters
on the expanded pool to test whether RL adds anything on top of healthy SFT data.

(2) DPO'S OVER-CONSERVATISM IS STRUCTURAL - three-method comparison closed. The DPO
beta sweep (beta 0.3, 0.5; EXP-2026-07-04-010) recovers SOME exploration over beta=0.1
(success 0.5833 -> 0.6667, reward 0.5213 -> 0.5989 at lambda0.3) but PLATEAUS ~15 pts of
success / ~0.15 reward below the SFT baseline (0.7495) and never re-crosses the kill
line. Robust across 2 pair designs x 3 betas, gate perfect (1.000) throughout. So DPO's
safety-first / exploration-poor character on this task is a STRUCTURAL property, not a
hyperparameter accident. The three-method comparison is FINAL: GRPO = efficiency
(analytic oracle at 3B), DPO = safety (gate 1.000 at ~half the success), SFT = balanced
baseline.

Why:

(1) The cleanest way to convert a data-starvation DIAGNOSIS into a validated PATH is to
add the missing data and re-run the same control on the same frozen eval; a 6x verdict
jump with everything else held constant is that confirmation. (2) An over-conservatism
claim needs a hyperparameter sweep before it can be called structural; sweeping beta
(the KL anchor most directly tied to exploration) across two pair designs and finding a
persistent ~15-pt success plateau is that evidence. An interesting side observation:
beta=0.3 and beta=0.5 converge to DIGIT-IDENTICAL greedy policies despite different loss
curves - the greedy argmax trajectory is the same (recorded as an observation in the
EXPERIMENT entry, not a failure).

Consequence:

- TODO: mark DPO beta sweep, corpus expansion batch-1, and the D-008 data-starvation
  test DONE; queue collection batch-2 (~400+), 3B citation capacity probe, GRPO-letters
  on the expanded pool; env v0.4 memory-arm construction stays the standing big-ticket.
- PORTFOLIO_INDEX: the citation line carries the full attribution-chain story
  (fabrication 87% -> 0 via action space; verdict 6x via class balance; capacity probe
  queued); the finalized three-method (GRPO/DPO/SFT) framing; refreshed honest limits
  (0.387 still far from usable, single seed, n=31, construction-labeled train data).
- The DPO escalation arm is CLOSED for further beta/pair tuning.
- General lesson: to promote a "data will fix it" hypothesis to a validated path, add
  the specific missing slice (here the boundary classes) and re-run the identical
  control on the frozen eval - a targeted class-balanced add is more informative than
  bulk rows.

## D-2026-07-04-010 - "Do we need RL, and how much does it buy" now has a measured, TASK-DEPENDENT answer; the citation attribution chain is CLOSED (capacity null, RL null, data is the lever)

Decision:

The founding question of this whole project - "do we ACTUALLY need RL, and how much does
it buy?" - now has an empirical, per-task answer, and two clean negatives today close the
citation attribution chain.

(1) THE CITATION CHAIN IS CLOSED - four questions, four answers. We ran the last two
links today, both on the SAME frozen test (n=31, letters), holding everything else fixed:
  - ACTION SPACE fixed FABRICATION: letter choices (A-F) mapped back by the harness drop
    fabricated_rate 0.87 -> 0.0 (D-2026-07-04-002). "Don't make the model do the harness's
    job."
  - DATA BALANCE fixed the VERDICT: class-balanced expanded pool lifted verdict_acc 6x
    (0.0645 -> 0.3871) (D-2026-07-04-009 / EXP-2026-07-04-012).
  - CAPACITY is NOT the lever: 3B on the IDENTICAL 122-row pool is WORSE than 1.5B
    (verdict_acc 0.3871 -> 0.2903; cite_gold 0.9355 -> 0.9032; mean_reward 0.8742 ->
    0.7710) (EXP-2026-07-04-013). Scaling the model did not buy the verdict at this data
    size; "scale up to fix it" is closed.
  - RL is NOT the lever ON HEALTHY DATA: GRPO-letters initialized from the expanded-SFT
    adapter, 300 train batches (train-time batch verdict_acc reached ~0.94), then
    frozen-test eval is DIGIT-IDENTICAL to its SFT init on every metric (verdict_acc
    0.3871, cite_gold 0.9355, fabricated 0.0, mean_reward 0.8742) (EXP-2026-07-04-014).
    Train reward rose, greedy test policy did not change: zero measurable increment.
  So: fabrication was fixed by ACTION-SPACE design, the verdict by DATA BALANCE; NEITHER
  was fixed by capacity, and NEITHER by RL. The sole remaining live lever is data
  (collection batch-2 -> 400+). Citation line status: CLOSED pending that data.

(2) "DO WE NEED RL, AND HOW MUCH" IS TASK-DEPENDENT - and now measured. Putting the two
tasks side by side gives a clean, honest, per-task RL-increment table (RL over the best
SFT baseline on the same frozen eval):

| task | RL increment over SFT | note |
| --- | --- | --- |
| escalation routing, 1.5B | +4.9 pts reward (0.7495 -> 0.7997) | RL buys efficiency below the oracle |
| escalation routing, 3B   | +0.45 pts (0.8428 -> 0.8473 = ORACLE) | capped by the analytic oracle; SFT already near it |
| citation verdict, 1.5B   | +0.0 (digit-identical) | on class-balanced (healthy) SFT data |

  RL adds a real but small increment on escalation (larger at 1.5B where SFT is further
  from the oracle, near-zero at 3B where SFT already hits the oracle), and EXACTLY zero on
  the citation verdict once the SFT data is healthy. "Not RL for RL's sake" is therefore
  an EMPIRICAL, per-task result, not a slogan: RL earned its place on escalation (and only
  above a code-enforced safety floor, D-2026-07-03-003) and did not earn it on citation,
  where DATA was the whole story.

Why:

The cleanest way to answer "does X buy the metric" is to hold everything else constant and
toggle only X on the frozen eval. We did exactly that for both remaining citation levers:
capacity (1.5B vs 3B, identical data) and RL (SFT vs GRPO-from-that-SFT, identical eval).
Two digit-level negatives - 3B < 1.5B, and GRPO == its SFT init - are strong, legible
answers precisely because nothing else moved. And the only way to make "do we need RL"
non-hand-wavy is to report the increment per task with the oracle as the ceiling; the
result is that RL's value is real, bounded, and task-shaped.

Consequence:

- TODO: mark the 3B capacity probe and the RL-increment (GRPO-on-healthy-data) DONE; set
  the citation line status to CLOSED pending collection batch-2 (277 -> ~400+). Standing
  queue unchanged in order: collection batch-2, env v0.4 memory arm (big-ticket), then
  second tier (Plan C training-free/inference-backend GRPO, lambda=0.6 exploration arm,
  full seed-varied 3B).
- PORTFOLIO_INDEX: mark the citation section COMPLETE with the four-question/four-answer
  chain (action space -> data -> capacity X -> RL X) and add the task-dependent RL table
  (escalation +4.9 / +0.45 vs citation 0.0); refresh honest limits (single-seed probes,
  n=31).
- No further capacity or RL tuning on the CURRENT citation pool; re-open only after the
  corpus grows (a larger N may legitimately re-open the capacity question at 400+, but not
  at 122 rows).
- General lesson: "do we need RL" is not a yes/no - it is an increment you MEASURE per
  task against the SFT baseline and the oracle ceiling. Here RL bought escalation
  efficiency and bought nothing on citation; the honest deliverable is the table, not a
  verdict.
- Caveat carried forward: both today's probes are single-seed, n=31, construction-labeled
  train - directional negatives that closed the OPEN levers, not certified laws.
