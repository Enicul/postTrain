# TODO

## P0 - Repo Hygiene

- [x] Commit and push initial repo scaffold to `Enicul/postTrain`.
- [ ] Confirm GitHub renders `README.md`, `AGENTS.md`, `CODEX.md`,
  `PROGRESS.md`, and `TODO.md`.
- [x] Decide whether `model.joblib` artifacts stay in Git or move to release/LFS
  later. Current baseline artifacts are small enough for Git.

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
- [ ] Add cleaner positive official-source spans for composite claims from real
  official/IR/SEC/press-release paragraphs.
- [ ] Add partial-support boundary cases where one evidence span supports only
  part of the claim.
- [ ] Add more `insufficient` and `contradicts` rows before trusting five-way
  support typing.
- [ ] Build `citation_verifier_repair_v0.3` from audited real spans instead of
  relying on synthetic train augmentation.

## P1 - Risk Reviewer Improvement

- [ ] Inspect risk reviewer confusion matrix.
- [ ] Decide whether target should be `risk_level`, `requires_human_gate`, or a
  multi-label risk flag task.
- [ ] Add high-risk negative examples: all-in, leverage, direct buy/sell,
  unsupported confidence, missing risk.

## P1 - Router Boundary Repair

- [ ] Add examples separating `evidence_check` from full `deep_research`.
- [ ] Keep safety recall as a hard metric.
- [ ] Add long-research holdout to the unified runner.

## P2 - WebExplorer-Style Seed-to-Task Generator

- [ ] Convert raw X/Weibo/Xiaohongshu/official seeds into:
  `question`, `answer/verifier target`, `evidence_chain`, `required_hops`,
  optional `teacher_trace`, and negative paths.
- [ ] Store raw source links and provenance.
- [ ] Do not treat social posts as truth without official/auditable evidence.

## P2 - GPU Post-Training

- [ ] Run Qwen 0.5B/1.5B/3B LoRA SFT for structured specialist JSON outputs.
- [ ] Try DPO on strong-vs-weak trajectory pairs.
- [ ] Try tiny GRPO/RLVR only on verifiable subtasks: routing, schema,
  citation support, freshness.

## P3 - Interview Packaging

- [ ] Write a short portfolio report.
- [ ] Add architecture diagram.
- [ ] Add failure taxonomy and representative traces.
- [ ] Add a "what we do not claim" section.
