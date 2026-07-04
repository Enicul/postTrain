# TODO

## P0 - Three-Task Ladder (docs/THREE_TASK_LADDER_PLAN_20260702.md)

Block A - fix the rulers (blocks every LLM arm):

- [x] A1: Audit all 131 real citation span rows (29 seed + 102
  `report_and_filing_spans_v0.1`); correct label boundary issues; freeze the
  eval split as `citation_real_eval_v1`. Done 2026-07-02 via blind double
  annotation + adjudication: 126 double-confirmed, 3 corrected (2.3%),
  conventions C1-C3 pinned. Optional cheap insurance: human spot-check of
  the 5 adjudicated rows.
- [x] A2: Build `risk_contract_repair_v0.1b` from real long-research
  medium-risk rows; freeze the repaired risk holdout. Done 2026-07-02:
  256 real rows normalized (three families), 90-row eval blind-audited
  (17 corrected, 18.9%; conventions R1-R5 pinned), train rule-synced;
  probe medium recall 0.0 -> 1.00, high/gate recall 0.64-0.73 is the
  measured headroom for the prompt arms. Optional: human spot-check of
  the 2 R3 keep-decisions.

Block B - eval pools (no GPU):

- [x] Hand-rules arm (rung 0) for risk and citation; escalation-router rules
  arm waits for the Act 3 environment.
- [x] LLM naive-prompt and engineered-prompt arms (rungs 2-3) for risk and
  citation on the frozen rulers via Claude subagents (haiku/sonnet), token
  cost proxies logged. Act 2 killed at rung 3 (prompted haiku 0.957); Act 1
  gate recall 1.000 but accuracy 0.811 < 0.90 -> continues to rung 4. See
  `ladder/blockb_eval_arms_v0.1` and D-2026-07-02-005.
- [ ] Leak-free spot re-audit of a random confirmed subset of both rulers
  (anonymized ids), cheap insurance after F-2026-07-02-006.

Block C - learning pools:

- [x] Act-3 cheap-path outcome table: 3-framing blind haiku ensemble over
  256 anonymized seeds (K=8 execution rollouts superseded - acts 1-2 were
  killed before needing learning pools; act 3 uses the ensemble-derived
  p_cheap_success). `ladder/escalation_env_v0.1/outcome_table_v0.1.json`.
- [x] Escalation environment v0.1: seeds + real-trace cost table + simulator
  + analytic oracle (`escalation_env_v01.py`). EXP-2026-07-02-006.

Block D - training-free RL:

- [x] Contrastive lesson extraction -> experience library v1 for risk
  (opus, dev-only errors); citation needed none (killed at rung 3).
  Artifact: `ladder/rung4_risk_hybrid_v0.1/risk_explib_v1.json`.
- [x] Kill-criteria checkpoint for acts 1-2: BOTH KILLED. Act 1 at rung 4
  (hybrid sonnet 0.978/1.000, owner policy decision A on the R3 rows,
  gate floor moved into code: `risk_gate_rules_v11.py`); Act 2 at rung 3.
  See D-2026-07-02-005/006, EXP-2026-07-02-004/005.

Block E - weights (Act 3 escalation router is the sole survivor; hard budget cap):

- [x] Build the Act 3 environment first: done, escalation_env_v0.1
  (EXP-2026-07-02-006). Analytic note: oracle mix is lambda-invariant below
  lambda=1; the learnable quantity is inferring p/gate from text.
- [x] Rules arm + prompted arms ON THE ENV (rungs 0/2/3 for Act 3). Rules
  0.760 (gate .625), naive_sonnet 0.666 (gate .672) on full 256; engineered
  sonnet = ORACLE exactly on batch-1 (64/256, spend-limited). See
  `ladder/act3_env_arms_v0.1`, EXP/D/F -2026-07-02-007/007/008.
- [x] Completed engineered sweep on full 256 (env v0.3, R4-corrected labels):
  Act-3 frontier kill CONFIRMED (sonnet within 0.2-1.3% of oracle, gate 1.0);
  cheaper haiku 12.6 pts below oracle + gate 0.80 = RL Phase 2 motivation.
  EXP-2026-07-02-009, D-2026-07-02-008.
- [ ] argmax-label SFT collapse check, SFT LoRA, GRPO with lambda sweep.
  CONDITIONAL: only if the full engineered sweep breaks the ceiling match on
  the unseen 192 seeds. On current evidence the engineered prompt = oracle,
  so GRPO has no room to win and this stays unbuilt (RL-for-RL's-sake
  avoided). See D-2026-07-02-007.

Block F - live demo:

- [ ] Thin replay runner over the rollout store; 15-20 trap-row demo subset;
  explib on/off toggle.

## P0 - RL Phase 2 (docs/RL_PHASE2_SMALL_MODEL_PLAN.md)

- [x] Master plan A/B/C with per-step kill criteria + budget.
- [x] Plan A GPU scripts (reward wrapper, oracle SFT labels, LoRA SFT, GRPO,
  eval harness with kill check); CPU-smoke verified. `scripts/rl/`.
- [x] A0 seed expansion 256 -> 1,120 (route-mean p proxy, MAE 0.064).
- [x] Plan B citation agentic env scaffold (reward: cite validity + verdict;
  hallucinated-citation hard negative). `scripts/rl/citation_agentic_env.py`.
- [x] Plan C training-free GRPO loop (rollout -> semantic advantage ->
  no-regression lesson gate). `scripts/rl/training_free_grpo.py`.
- [x] GPU-launch hardening (2026-07-03): checkpoint+resume, run-dir
  provenance + never-overwrite failures, per-completion generations +
  per-batch reward trace, seed/grad-accum flags, `monitor_run.py` watchdog,
  `GPU_RUNBOOK.md` with failure protocol, pinned `requirements-rl.txt`,
  gitignore for run weights. CPU-smoke verified. CP-2026-07-03-001,
  D-2026-07-03-001.
- [x] Pull the repo to the A100 and run A1 (prompted-eval motivation gate) per
  `scripts/rl/GPU_RUNBOOK.md` (2026-07-03). A2 SFT and A3 GRPO also run, each
  into `out-dir/<run_id>/`. See EXP-2026-07-03-001..003, CP-2026-07-03-002.
- [x] A1 (GPU): prompted Qwen-0.5B/1.5B/3B/7B on env v0.3 -> motivation gate.
  NO model passed kill (0.5B 0.3063 / 1.5B 0.6444 / 3B 0.4232 / 7B 0.7447);
  bottleneck is gate discipline, not success -> training motivated.
- [x] A2/A3 (A100): argmax-SFT then GRPO. SFT 1.5B (0.7495) beats prompted 7B;
  GRPO verdict recorded honestly (not promoted: 1.5B +4.9 but gate 0.875, 0.5B
  collapse). EXP-2026-07-03-002/003, D-2026-07-03-003.
- [x] GRPO next-iteration option (a) gate-seed oversampling x4: RAN (2026-07-04).
  NULL at 1.5B (0.7997/gate 0.875, digit-identical to plain GRPO - the 1.5B had
  zero all-violate groups, so the fix targeted a 0.5B disease). At 0.5B (+kl-beta
  0.2) the collapse REPEATED in greedy eval despite samples keeping the gate alive
  (capacity floor). EXP-2026-07-04-001/002, F-2026-07-04-002. Options (b) larger K,
  (c) exploration bonus remain un-run; (d) hybrid stands as the product answer.
- [x] DPO round on the existing `preference_pairs`: RAN (2026-07-04, 1.5B beta 0.1).
  Gate-perfect (1.000) but reward-collapsed (0.5382, success 0.58) - pair artifact
  (rejected == escalate action). Completes the SFT/DPO/GRPO three-way table.
  EXP-2026-07-04-001, F-2026-07-04-004.
- [x] Failure-trajectory taxonomy from the 0.5B collapse rollouts:
  `docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md` (55%-vs-0% all-violate-group evidence).
- [x] Identify the 1-missed-gate seed at 1.5B: it is
  `router_contract_realtool_risk_review_AMD_00` (model plays cheap-then-escalate;
  oracle says gate). Same seed across SFT / v1 / v2. Escalated to human review
  before any label change (D-2026-07-04-003).
- [x] Judge-consistency report: `docs/JUDGE_CONSISTENCY_REPORT.md`.
- [x] Capability matrix doc (per-model x metric): `docs/CAPABILITY_MATRIX.md`.
- [x] MORNING HUMAN-REVIEW: rule on `router_contract_realtool_risk_review_AMD_00`.
  RULED 2026-07-04 (owner, Option C / Convention R6): concern-type advisory queries
  route to a smart-review tier, NOT the human gate. AMD_00 relabeled no-gate. See
  D-2026-07-04-005, docs/RULING_DOSSIER_risk_review_AMD_00.md.
- [ ] env v0.3.1 gate-convention patch: flip AMD_00 `requires_human_gate` true->false
  with `gate_convention: R6_concern_advisory_smart_review_20260704`; then OFFLINE
  dual-convention rescore of ALL historical `test_preds` under BOTH the pre-R6 (gate
  denom 8) and post-R6 (denom 7) gate sets, side-by-side (no GPU needed). DEFERRED
  until batch-4 completes, to preserve comparability. D-2026-07-04-005.
- [ ] KIWI product (design note, implementation deferred): route concern-signals
  (worry expressed, no action intent) to the critic/verifier SMART-REVIEW tier per R6
  — stronger model / dedicated agent that retrieves evidence + user memory before
  judging; do NOT bounce concern back to the user as a decision, and do NOT collapse
  it to the cheap path. Human gate stays reserved for red-line actions. D-2026-07-04-005.
- [ ] Gemma 4 cross-family arm: repeat the SFT/GRPO-v2 sweep on Gemma 4 to test
  whether the 3B sweet-spot and 7B non-monotonic dip are Qwen-specific or general.
  Needs user HF license acceptance + a fresh venv with transformers>=Gemma4 support.
- [ ] Citation env v2: letter-indexed (A-F) action space mapped back by the harness;
  re-run 1.5B GRPO vs the same `citation_real_eval_v1` ruler, same bar. PRE-REGISTERED
  (D-2026-07-04-002), not yet run.
- [ ] DPO pair v2: add "failed-to-escalate" negatives (escalate = chosen on gate
  seeds) so escalation is not uniformly the rejected action (D-2026-07-04-004).
- [ ] 0.5B temperature-sweep probe (OPTIONAL): quantify the sampling-vs-greedy gap on
  the 0.5B v2 adapter (samples keep gate alive; greedy collapses). F-2026-07-04-002.
- [ ] Consolidated project-plan doc (single index across the acts + RL Phase 2).
  PARTIALLY served by the new `docs/PORTFOLIO_INDEX.md` interviewer front door.
- [ ] Plan B: grow citation corpus to 300-500 rows, then GRPO.
- [ ] Plan C: run with an inference backend as the control column.
- [ ] env v0.4 memory-form experiment - designed, queued behind A3 writeup.
  Four-arm matrix (no-memory / structured-digest / raw-long-context / Sonnet)
  with pre-registered kills; tests what FORM state should take for a small
  model. See `docs/ESCALATION_ENV_V04_MEMORY_DESIGN.md`, D-2026-07-03-002.

## P0 - Repo Hygiene

- [x] Commit and push initial repo scaffold to `Enicul/postTrain`.
- [ ] Confirm GitHub renders `README.md`, `AGENTS.md`, `CODEX.md`,
  `PROGRESS.md`, and `TODO.md`.
- [x] Decide whether `model.joblib` artifacts stay in Git or move to release/LFS
  later. Current baseline artifacts are small enough for Git.
- [x] Add summary-first recording protocol to avoid local overload from full
  append-only logs and row-level prediction dumps.
- [ ] Audit older run READMEs that still advertise full `predictions_*.jsonl`
  as the default artifact.

## P0 - Learning Source Registry

- [x] Add `LEARNING_SOURCES.md` as the canonical source-to-decision registry.
- [x] Add GLM ARC entry: what we extracted, why, what we did not adopt, and why
  not.
- [ ] Add Qwen entries: Qwen2.5 assistant stability, Qwen3 routing/thinking
  control, Qwen3-Coder/agentic trajectory, Qwen2.5-Math self-improvement.
- [ ] Add DeepSeek entries: helpful/harmless reward model, R1/GRPO/RLVR,
  Harness framing, specialist/verifier implications.
- [ ] Add Kimi entries: k1.5 long2short, K2 agentic action trajectory,
  Kimi-Researcher evidence-chain reward.
- [ ] Add MiniMax/WebExplorer entries: teacher-assisted data synthesis,
  environment construction, student self-exploration, verifier reward.

## P1 - Citation Verifier Repair

- [x] Inspect `citation_verifier/predictions_test.jsonl`.
- [x] Group errors by failure type: source mismatch, partial support, ambiguous
  label, insufficient evidence, synthetic artifact.
- [x] Add repaired citation-span audit set.
- [x] Rerun `train_specialist_baselines.py`.
- [x] Log before/after metrics in `EXPERIMENT_LOG.md`.
- [x] Build `citation_verifier_repair_v0.2` with hard negatives that share
  topical overlap but do not support the exact claim.
- [x] Add first cleaner positive official-source spans from real
  official/IR/SEC/press-release/news paragraphs:
  `real_citation_spans_v0.1`.
- [x] Add first partial-support boundary cases where one evidence span supports
  only part of the claim.
- [x] Add first `insufficient` and `contradicts` rows under the five-way
  support contract.
- [x] Expand `real_citation_spans_v0.1` to at least 100 rows with more SEC
  filing paragraphs, earnings transcript spans, and reputable news paragraphs.
  Done via `report_and_filing_spans_v0.1` (102 rows; 131 combined).
- [ ] Run Claude/human audit on all 131 real span rows (29-row seed plus
  `report_and_filing_spans_v0.1`) and correct any label boundary issues before
  training. Mandatory: F-2026-07-02-002 shows one silent label error already
  slipped through collection.
- [x] Add report/filing/public-research source plan:
  `docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md`.
- [x] Build `report_and_filing_spans_v0.1` under
  `citation_contract_repair_v0.1`.
- [x] Add at least 30 SEC filing rows and 20 transcript/prepared-remarks rows.
  Collected 51 SEC filing rows and 25 transcript rows.
- [x] Add public research rows only from public/authorized sources; do not store
  paywalled sell-side report full text. SIA/Deloitte/AP only; Gartner and IDC
  dropped when they blocked scripted fetch.
- [ ] Add issuer prepared-remarks (e.g., Micron, NVIDIA CFO commentary) as a
  second transcript-tier source; current transcript rows come from a single
  publisher's call-summary pages.
- [ ] Run a citation CPU probe on the combined audited 131-row pack under
  summary recording.
- [ ] Build `citation_verifier_repair_v0.3` from audited real spans instead of
  relying on synthetic train augmentation.

## P1 - Risk Reviewer Improvement

- [x] Inspect risk reviewer confusion matrix.
- [x] Decide whether target should be `risk_level`, `requires_human_gate`, or a
  multi-label risk flag task.
- [x] Add high-risk negative examples: all-in, leverage, direct buy/sell,
  unsupported confidence, missing risk.
- [x] Build `risk_contract_repair_v0.1` with `medium`, human-gate,
  overconfidence, position sizing, panic selling, and missing-risk cases.
- [x] Run risk-only CPU baseline and realistic holdout under summary recording.
- [x] Build `risk_contract_repair_v0.1b` with real long-research medium-risk
  examples. v0.1 added the `medium` schema but collapsed on realistic medium
  holdouts. Repaired 2026-07-02: medium recall 1.00 on the audited real
  eval; see CP-2026-07-02-003.

## P1 - Router Boundary Repair

- [ ] Add examples separating `evidence_check` from full `deep_research`.
- [ ] Keep safety recall as a hard metric.
- [ ] Add long-research holdout to the unified runner.

## P1 - AI Expanded Baseline / Holdout Evaluation

- [x] Import `kiwi-brain-ai-expanded-v0.1` into the standalone `postTrain`
  repo.
- [x] Patch `train_specialist_baselines.py` for the expanded v0.6 schema.
- [x] Run canonical expanded CPU baseline:
  `specialist_cpu_ai_expanded_v0.1_20260630T080225Z`.
- [x] Record the non-canonical placeholder timestamp run as a failure instead
  of silently deleting it.
- [x] Build realistic holdout evaluator for real tool traces, long-research
  episodes, and evidence-chain negatives.
- [x] Run expanded router/risk/citation baselines on that holdout.
- [x] Diagnose why router/risk reach 1.0 on the expanded split: template
  leakage, label shortcuts, split similarity, or genuinely easy task.
- [ ] Add boundary cases before GPU fine-tuning: over-routing,
  under-routing, high-risk safety recall, partial support, stale evidence, and
  contradiction handling.

## P1 - Data Contract Repair v0.1

- [x] Build `router_contract_repair_v0.1` from real tool trace rows and old
  golden router rows.
- [x] Add router labels missing from expanded data:
  `risk_review` and `clarification_needed`.
- [x] Add router boundary rows for `evidence_check` vs `deep_research` and
  `financial_calculation` vs research tasks.
- [x] Build `router_social_boundary_repair_v0.1` for long X/bookmark market
  narratives that ask for evidence verification but are still sometimes routed
  to `fast_answer`.
- [ ] Repair `router_social_boundary_repair_v0.1` tradeoff: keep the golden
  social improvement while restoring real-tool trace accuracy to 1.0.
- [x] Build `risk_contract_repair_v0.1` with `medium` and human-gate semantics.
- [x] Build `citation_contract_repair_v0.1` that separates:
  `candidate_evidence`, `verified_support`, `partial_support`, `insufficient`,
  and `contradicts`.
- [x] Collect first real official/IR/SEC/press-release/news spans under
  `citation_contract_repair_v0.1`: `real_citation_spans_v0.1`.
- [x] Add transcript spans and more reputable news spans under
  `citation_contract_repair_v0.1`. 25 transcript rows and 8 AP news rows in
  `report_and_filing_spans_v0.1`.
- [x] Add financial report / SEC filing spans under
  `citation_contract_repair_v0.1`. 51 rows across 10-K/10-Q/6-K filings.
- [x] Add public research metadata and short spans with license notes; do not
  ingest paywalled report text. SIA and Deloitte rows carry `license_note`.
- [x] Rerun router CPU baseline after contract repair and compare against
  `realistic_holdout_eval_v0.1_20260630T083000Z`.
  Use default summary recording unless a full error-analysis run is explicitly
  needed.

## P2 - WebExplorer-Style Seed-to-Task Generator

- [ ] Convert raw X/Weibo/Xiaohongshu/official seeds into:
  `question`, `answer/verifier target`, `evidence_chain`, `required_hops`,
  optional `teacher_trace`, and negative paths.
- [ ] Store raw source links and provenance.
- [ ] Do not treat social posts as truth without official/auditable evidence.

## P2 - GPU Post-Training

- [ ] Do not start GPU LoRA/SFT/DPO/GRPO until the expanded baseline is tested
  on realistic holdouts.
- [ ] Run Qwen 0.5B/1.5B/3B LoRA SFT for structured specialist JSON outputs.
- [ ] Try DPO on strong-vs-weak trajectory pairs.
- [ ] Try tiny GRPO/RLVR only on verifiable subtasks: routing, schema,
  citation support, freshness.

## P3 - Interview Packaging

- [x] Write a short portfolio report:
  `docs/PORTFOLIO_REPORT_20260701.md`.
- [x] Add architecture diagram.
- [x] Add failure taxonomy and representative traces.
- [x] Add a "what we do not claim" section.
- [x] Add a concise README link from the repo root to the portfolio report.

## P1 - Retrospective Recording (docs/DECISION_NODE_RECORDING_SPEC.md)

From the 2026-07-02 QA audit + retrospective-module round. All KIWI-side
implementation happens in the Agent/KIWI repo, not here; tracked here because
this is the spec of record.

- [ ] Implement the 4 P0 recording fixes in KIWI (BLOCKED on landing/stashing
  the ~118 uncommitted KIWI files first):
  - [ ] DecisionSnapshot at user-decision time - freeze thesis + confidence +
    boundary + point-in-time evidence set + system recommendation + gate
    verdict + user_stage, for ALL choices including SKIP (`api/memory.py:96`).
  - [ ] Fix skip asymmetry - snapshot thesis/boundary on skip too
    (`api/memory.py:139`).
  - [ ] Persist every gate evaluation (policy verdict, critic verdict, fused
    result, triggering terms) as a durable row (`policy.py`, `critic.py`).
  - [ ] Trajectory-log the intent router (`pipeline.py:186-206`).
- [ ] Wire the standalone retrospective module into KIWI via an adapter layer
  (sync sqlite3 module <-> async SQLAlchemy DB; explicit enum alignment for
  RiskLevel/GateAction vs Bias/SupportLabel; tz-aware/UTC timestamps for the
  strict leakage check). Deferred until the KIWI tree lands.
- [ ] Fix the 3 guardrail contradictions in KIWI: default `SHOW_DISCLAIMER` on
  (`config.py`); add a post-generation buy-now regex scrubber as a code-level
  floor (`prompts.py`); route all proposals through `critic.evaluate` instead
  of hardcoding `requires_user_approval:True` (`stock_decision.py:226,478`).
- [ ] Design the capability-stage model (flywheel goal (a)) - currently ENTIRELY
  UNIMPLEMENTED: confirmed 0 hits for capability / stage / novice in KIWI `src`.
  Needs a stage tracker feeding `user_stage` into the DecisionSnapshot.
