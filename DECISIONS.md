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
