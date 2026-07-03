# Capability Matrix - vs CN/US Agentic-RL / Post-Training Roles - 2026-07-03

## Purpose

An honest, evidence-grounded self-assessment of this portfolio against
agentic-RL and post-training internship roles at Chinese frontier labs
(ByteDance Seed, DeepSeek, Moonshot/Kimi) and US labs. Every score cites a
concrete path in this repo and names the honest gap. The framework is the
six-dimension / five-archetype model from the hands-on-modern-RL industrial
appendix.

This document is a mirror, not a pitch. Where the evidence is thin it says so.
The recurring strength across the whole portfolio is **judging discipline**
(pre-registered kills, frozen rulers, failure-as-evidence); the recurring
weakness is **scale** (single-A100, small corpus, no multi-node).

---

## The six capability dimensions

| Dimension | Score | One-line justification |
| --- | :---: | --- |
| Algorithm | 4/5 | Ran the full SFT -> argmax-SFT -> GRPO chain on a real reward, with a pre-registered promotion bar and an honest fail verdict. |
| Data | 4/5 | Data-contract repair, realistic-holdout discipline, audited frozen rulers, and a measured label-leak bias - the whole loop, at small scale. |
| Evaluation | 5/5 | Three audited frozen evals, pre-registered kill criteria, two-pool separation, anonymized-id discipline after a measured +11.6pt leak. |
| Systems | 2/5 | Run provenance / manifest / never-overwrite-failure infra built and used, but single-A100 scale; no distributed / multi-node experience. |
| Product | 4/5 | KIWI dual-gate governance + retrospective flywheel that ties the reward to a real product loop, with a concrete trajectory-export design. |
| Safety | 4/5 | Deterministic code-level gate floor (not promptable), hard gate-recall constraint on every RL arm, three shipped guardrail contradictions found by audit. |

### Algorithm - 4/5

**Justification.** The portfolio does not stop at "we could run GRPO." The
A1-A3 GPU chain (2026-07-03) actually ran SFT and GRPO on Qwen2.5 0.5B/1.5B
against the escalation env's cost-shaped reward, initialized GRPO from the SFT
adapters, and tested a pre-registered promotion bar. Headline result: the
**trained 1.5B (SFT reward 0.7495) beats the prompted 7B (0.7447)** - a 4.7x
smaller model, post-trained, edging out a frontier-of-family prompt. GRPO added
+4.9 reward pts at 1.5B (0.7981, within 4.9 of the analytic oracle 0.8473) but
did **not** clear the promotion bar (gate recall 0.875 < 0.99), and the 0.5B
GRPO run suffered a fully documented **policy collapse** (gate action extinct,
reward -22.3 vs SFT). The GRPO instability was caught in `reward_trace.jsonl`
BEFORE eval confirmed it.

**Strongest evidence.**
- `EXPERIMENT_LOG.md` EXP-2026-07-03-002 (SFT) and EXP-2026-07-03-003 (GRPO)
- `training-corpus/scripts/rl/{sft_escalation.py,grpo_escalation.py,reward_escalation.py,build_sft_labels.py}`
- `training-corpus/scripts/rl/runs/grpo_qwen05/20260703T1507Z-e571324/` (6400 rollout generations, `reward_trace.jsonl`)

**Honest gap.** No DPO run yet (scheduled tonight); no RM training (a
judge-calibration report exists instead); no PPO. GRPO was run at 0.5B/1.5B on a
model-derived reward on a single A100, not at production scale. The algorithm
breadth is real but shallow-by-scale, and one of the two RL runs collapsed.

### Data - 4/5

**Justification.** The whole first half of the post-training loop is here and
was driven by failures, not by hope: data-contract repair (router labels
`risk_review`/`clarification_needed`, five-way citation support contract),
realistic-holdout evaluation that caught template leakage (expanded pack
scored 1.0 accuracy, real tool-trace pilot scored 0.0), and real citation-span
collection (29 seed + audited real spans with source hashes, point-in-time
dates, no raw HTML dumps). The failure taxonomy is explicit and the repairs are
tracked as canonical vs failed checkpoints.

**Strongest evidence.**
- `docs/PORTFOLIO_REPORT_20260701.md` (data assets, failure taxonomy, router/risk/citation results)
- `README.md` (realistic-holdout table showing the 0.0 real-tool-trace catch)
- `FAILURE_LOG.md` F-2026-07-02-006 (measured +11.6pt label-leak bias)

**Honest gap.** Corpus scale is small vs industry: 131 audited citation rows,
160 escalation train labels (v0.3), low-hundreds specialist rows. This proves
the pipeline and the discipline, not generalization at scale. Real long-research
medium-risk rows are still a build dependency (`risk_contract_repair_v0.1b`).

### Evaluation - 5/5

**Justification.** This is the portfolio's strongest dimension and the one that
most differentiates it. Three audited frozen evals; a three-act ladder where
each rung may only be attempted if the rung below is measured on the same frozen
holdout, with pre-registered kill criteria per act; two physically separated
pools (learning vs eval/demo) with the rule that one tuning pass against a frozen
test invalidates that column; and - after a real incident where eval `sample_id`s
leaked gold labels and inflated LLM arms +11.6 points - a standing rule that
every eval batch uses anonymized ids. The evaluation is adversarial toward its
own results.

**Strongest evidence.**
- `docs/THREE_TASK_LADDER_PLAN_20260702.md` (ladder, kill criteria, two-pool honesty rules)
- `FAILURE_LOG.md` F-2026-07-02-006 (leak measured, quantified, ruler re-frozen)
- `training-corpus/scripts/rl/eval_escalation_policy.py` (prints the pre-registered kill check)

**Honest gap.** The escalation env's `p` (cheap-path success) is a haiku-ensemble
guess, so the reward ruler is model-derived - the "sim != reality" caveat is
stamped on every result, and the fix (real-trajectory anchoring via the
retrospective flywheel) is designed but not yet run. One Act-3 engineered sweep
was truncated by a spend limit and reported on 25% of seeds with an explicit
provisional flag (F-2026-07-02-008).

### Systems - 2/5

**Justification.** The infra that exists is genuinely good and was built in
response to an audit: run-dir provenance (`run_id = <UTC>-<git sha>`), trainers
that REFUSE to overwrite a non-empty run dir (failure preservation as a code
property, not operator discipline), `run_manifest.json` with full config + pip
freeze + `parent_run_id`, `trainer_log.jsonl`, GRPO `generations.jsonl` +
`reward_trace.jsonl`, a `monitor_run.py`, and checkpoint/resume support. The
staleness/monitoring concepts a rollout-infra role needs are understood and
partially instantiated.

**Strongest evidence.**
- `DECISIONS.md` D-2026-07-03-001 (run provenance + never-overwrite-failures convention)
- `training-corpus/scripts/rl/{run_logging.py,monitor_run.py,GPU_RUNBOOK.md}`
- `training-corpus/scripts/rl/runs/` (real manifests, logs, preserved failed-launch dirs)

**Honest gap.** This is the honest weak dimension. Everything ran on a single
A100 80GB. There is **no distributed / multi-node experience**: no
tensor/pipeline parallelism, no async rollout worker fleet, no real
generation-training staleness handling under load, no throughput engineering
beyond noting the vLLM backend and grad-checkpointing knobs in the runbook. The
2/5 reflects concepts-understood-via-design, not systems-operated-at-scale.

### Product - 4/5

**Justification.** The portfolio closes the product loop, which is exactly the
China-lab emphasis. KIWI is a real financial-research copilot with a dual-gate
(policy/critic) governance layer and a retrospective module (standalone-first,
25/25 tests). The decision-review-and-flywheel design argues - concretely, with
a trajectory-export schema - that the product's retrospective loop and the
post-training pipeline are the same machine: every matured user decision becomes
a point-in-time-clean, reality-anchored trajectory that trains the exact judges
the product runs on, scoring reasoning and never outcome.

**Strongest evidence.**
- `docs/DECISION_REVIEW_AND_TRAINING_FLYWHEEL.md` (product loop == data engine, trajectory exporter, real-vs-synthetic mix metric)
- `docs/DECISION_NODE_RECORDING_SPEC.md` (nine frozen snapshot categories, conflict-sample flags)
- `DECISIONS.md` tail (retrospective module standalone-first, 25/25 tests)

**Honest gap.** The flywheel is time-gated cold-start: real outcomes take
weeks-to-months, so today it bootstraps on audited/synthetic data. The
retrospective module is built standalone but not yet wired into KIWI (blocked on
~118 uncommitted KIWI changes), and three shipped guardrail contradictions
(F-2026-07-02-009) are documented but not yet fixed in the live default config.

### Safety - 4/5

**Justification.** Safety here is a code-level floor, not a prompt. The risk gate
lives in versioned code (`risk_gate_rules_v11.py`), gate recall is a HARD
constraint on every RL arm (never a learned objective), and when the experience
library silently traded gate recall 1.000 -> 0.956 for accuracy, that was caught,
escalated, and fixed as a deterministic defense-in-depth rule
(F-2026-07-02-007). The GRPO verdict explicitly refuses to let RL carry the
safety floor: pure RL missed the gate at 1.5B and collapsed it at 0.5B, so the
floor stays in code and RL only optimizes cost above it. An Opus QA audit found
three shipped guardrail contradictions where safety intent lived only at a soft
layer.

**Strongest evidence.**
- `training-corpus/scripts/risk_gate_rules_v11.py` (safety floor in code)
- `FAILURE_LOG.md` F-2026-07-02-007 (explib eroded gate recall; fixed as a code-level rule) and F-2026-07-02-009 (three guardrail contradictions)
- `EXPERIMENT_LOG.md` EXP-2026-07-03-003 / `DECISIONS.md` D-2026-07-03-003 (RL never carries the floor alone)

**Honest gap.** This is reward-hacking / safety-gate discipline on narrow
verifiable tasks, not frontier-scale safety (no jailbreak red-teaming at scale,
no RLHF-safety, no adversarial-robustness eval suite). The hacking-detection
story is one measured incident plus a standing rule, which is strong evidence but
a small sample.

---

## Role archetype fit

| Archetype | Fit | Regional lean |
| --- | :---: | --- |
| Post-Training Algorithm Engineer (SFT/DPO/RM/PPO/GRPO/RLVR) | Medium-Strong | both |
| Reward-Judge Engineer (rubrics, judge consistency, hacking detection) | Strong | US |
| RL-GRPO Training Engineer (verifiable reward, on-policy sampling, instability diagnosis) | Strong | both |
| Agentic Post-Training Engineer (env+tools, trajectory recording, failure taxonomy, grader) | Strong | both |
| RL Systems Infra (rollout pipeline, staleness, monitoring) | Weak-Medium | US |

### Post-Training Algorithm Engineer - Medium-Strong

**Say in the interview.** "I ran the full ladder end-to-end: sklearn baseline ->
prompted -> engineered prompt -> experience library -> argmax-SFT -> GRPO, all on
the same frozen ruler, and the headline is a trained 1.5B beating a prompted 7B.
My deliverables are exactly a data sheet (contract repair + audited spans), a
training report (EXPERIMENT_LOG SFT/GRPO entries with manifests), and a badcase
analysis (the failure log with a measured +11.6pt leak and a documented policy
collapse)." Ground it in `EXPERIMENT_LOG.md` EXP-2026-07-03-002/003.

**What's missing.** No DPO run yet (scheduled tonight - fix this before the
interview), no RM training (offer the judge-calibration report as the analogue),
no PPO, no RLVR at scale. The breadth is SFT+GRPO with a designed-but-unrun DPO.

### Reward-Judge Engineer - Strong

**Say in the interview.** "My strongest axis is judging discipline. I have three
audited frozen rulers, a five-way citation support rubric with deliberately
embedded traps, and I caught two real judge-consistency failures: an eval-id leak
that inflated arms +11.6 points, and an experience library that silently
re-litigated a contested label convention and eroded gate recall. Both are
measured, both drove a versioned fix." Ground it in `FAILURE_LOG.md`
F-2026-07-02-006/007 and the ladder plan's two-pool rules.

**What's missing.** No trained reward model - the judge work is rubric +
LLM-as-judge calibration + hacking detection, not a learned RM. Frame the
judge-calibration report as the deliverable and be explicit that RM training is
the next step.

### RL-GRPO Training Engineer - Strong

**Say in the interview.** "I ran GRPO on a verifiable reward with K=8 on-policy
sampling, initialized from an SFT adapter, and I diagnosed instability from the
signal, not from the eval: KL drifted to ~2.0 and `reward_trace.jsonl` showed the
gate action going extinct BEFORE the eval confirmed the 0.5B collapse. I have a
mechanism hypothesis and a pre-registered failure postmortem. The 1.5B run was
healthy (+4.9 reward, KL ~0.3) but honestly failed the promotion bar on the hard
gate constraint - and I recorded that negative as a first-class result." Ground
it in `EXPERIMENT_LOG.md` EXP-2026-07-03-003, `FAILURE_LOG.md` F-2026-07-03-003,
and the 6400 rollout trajectories under `runs/grpo_qwen05/`.

**What's missing.** Single-A100 scale; the reward `p` is model-derived (fidelity
caveat); only two GRPO runs so far. No large-K throughput or async-rollout
experience.

### Agentic Post-Training Engineer - Strong

**Say in the interview.** "I built the escalation environment myself: a
two-to-three step cost-aware policy with an analytic verifiable reward
(final correctness - lambda * accumulated cost), a cost table measured from real
KIWI traces, a per-episode rollout schema, an anonymized-id discipline, and a
hard gate-recall constraint. I have a designed multi-step citation evidence-chain
agentic env (retrieve -> cite with paragraph-hash machine-check -> five-way
verdict) as the next agentic showcase, plus a decision-node recording spec and a
9+ entry failure taxonomy." Ground it in `docs/THREE_TASK_LADDER_PLAN_20260702.md`
(rollout schema), `training-corpus/scripts/rl/citation_agentic_env.py`, and
`docs/DECISION_NODE_RECORDING_SPEC.md`.

**What's missing.** The environment is single-turn-flattened for TRL
compatibility; the genuinely multi-step citation agentic env is designed, not
run. Memory-form (v0.4) is pre-registered, not run. Tool-use trajectories are
recorded at pilot scale.

### RL Systems Infra - Weak-Medium

**Say in the interview.** "I built the provenance and failure-preservation infra a
rollout pipeline needs - addressable run dirs, never-overwrite-failure guards,
per-run manifests with pip freeze and parent-run linkage, per-batch reward
tracing, and a run monitor - and I understand staleness and generation-training
separation conceptually. I have not operated this at multi-node scale, and I'd
say so." Ground it in `DECISIONS.md` D-2026-07-03-001 and
`training-corpus/scripts/rl/{run_logging.py,monitor_run.py}`.

**What's missing.** The load-bearing gap: no distributed/multi-node, no async
rollout fleet, no real staleness-under-load handling, no throughput engineering.
This is the archetype to NOT over-claim on; lead with the eval/agentic strengths
instead and position infra as a growth area with the design instincts already in
place.

---

## China vs US positioning

### Where this portfolio is strongest for each region

**China (ByteDance Seed, DeepSeek, Moonshot/Kimi): vertical + flywheel + product
closure.** This is the portfolio's natural home. It is calibrated on a single
vertical (AI upstream/downstream equities: semis, memory, power, data-center),
and the decision-review flywheel is a concrete instance of the DeepSeek/Kimi
"environment that generates its own verifiable trajectories" story - the product
IS the environment, emitting point-in-time-clean episodes as a by-product of
being used. The Kimi-Researcher evidence-chain reward is already registered as
the model for the citation agentic env. The product-closure narrative (dual-gate
governance, retrospective coaching, real-trace cost tables) is exactly the
vertical-domain + data-flywheel + product-closure emphasis Chinese labs weight.
Lead here with `docs/DECISION_REVIEW_AND_TRAINING_FLYWHEEL.md` and the vertical
calibration.

**US labs: training-systems + eval/grader discipline + agentic RL.** The eval and
grader discipline (5/5) and the GRPO instability-diagnosis + pre-registered-kill
rigor travel very well to US labs, which weight eval/grader discipline and
agentic RL. Lead here with the frozen rulers, the two-pool honesty rules, the
measured leak incident, and the honest GRPO negative. The one US-weighted
dimension to be candid about is training systems: the infra design is there but
the multi-node operation is not, so position it as understood-not-operated.

### Top 2-3 highest-ROI gap-fills

1. **Run the DPO experiment (scheduled tonight).** This is the single highest-ROI
   fill: it closes the most-named gap in the Post-Training Algorithm Engineer
   archetype at near-zero marginal cost (the apparatus, rulers, and honesty rules
   all exist). Turns "SFT+GRPO, DPO designed" into "SFT+DPO+GRPO run," which is
   the standard post-training trio. Do it before any interview.

2. **Ship one honest RM-training or judge-calibration deliverable.** The
   Reward-Judge fit is Strong but has a literal hole (no trained RM). Even a
   small local RM trained on the citation preference pairs, or a formal
   judge-calibration report with inter-rater/consistency numbers, converts the
   biggest remaining "what's missing" into a "here's the artifact." Lower cost
   than it looks because the audited preference/label data already exists.

3. **Write the systems gap honestly and instrument one staleness knob.** Rather
   than fake multi-node experience, add a short, concrete "what I'd change to go
   distributed" note grounded in the existing manifest/monitor infra, and
   optionally instrument one generation-training staleness metric on the
   single-A100 GRPO loop. This converts the 2/5 Systems weakness from a silent
   gap into a demonstrated understanding of the axis - which is what a US infra
   interviewer actually probes for.

Known gaps restated for the record: no DPO run yet (scheduled tonight); no
distributed/multi-node systems experience (honest: single-A100 scale, concepts
understood via monitor/manifest design); no RM training (judge-calibration
report exists instead); corpus scale small vs industry.

---

## One-line honest summary

Strongest as an **Agentic Post-Training / Reward-Judge / RL-GRPO engineer** who
judges before training and records failures as first-class evidence; weakest on
**distributed systems scale**; naturally positioned for **China vertical +
flywheel product-closure** roles and **US eval/grader + agentic-RL** roles, with
the DPO run as the one gap to close before walking into an interview.
