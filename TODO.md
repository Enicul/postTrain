# TODO

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
- [ ] Build `risk_contract_repair_v0.1b` with real long-research medium-risk
  examples. v0.1 added the `medium` schema but collapsed on realistic medium
  holdouts.

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
