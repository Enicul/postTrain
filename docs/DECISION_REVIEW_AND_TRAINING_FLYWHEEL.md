# Decision-Review System + Post-Training Flywheel - 2026-07-02

Two things in one document, because they are the same machine viewed twice:

1. **Product**: KIWI's retrospective system - the feedback loop that turns a
   novice into a good investor by reviewing *reasoning*, not outcomes.
2. **Post-training**: the same system is a real-trajectory data engine that
   closes the "sim != reality" gap in the escalation environment - every
   matured decision becomes a point-in-time-clean, reality-anchored training
   sample.

Scope: AI upstream/downstream equities only (semis, memory, power, data-center
- the same vertical the postTrain rulers are already calibrated on: NVDA, AMD,
MU, TSM, AVGO, META, GOOGL, AMZN, plus MRVL/VRT/LRCX/KLAC/ANET/ARM/ASML/AMAT/
SMCI/CRWV/SNDK/DELL/ORCL).

---

## Part 1 - The retrospective system (product)

### Design principle (the one that must never be violated)

> A retrospective evaluates **the reasoning that was available at decision
> time**, never the price that happened afterward.

Outcome-based review trains outcome-chasing (the exact retail failure the risk
gate flags as red-line). Reasoning-based review trains judgment. The
counterfactual is a tool to test the reasoning, never to compute regret.

### 1. Decision snapshot (the atomic unit, frozen at decision time)

At every decision - **including skip and "almost bought but didn't"** - freeze
a point-in-time record:

```
decision_id, timestamp, symbol, action ∈ {take, skip, modify}
thesis        : why (the user's reasoning, in their words)
boundary      : "I am wrong if ___" (the invalidation condition)
review_trigger: when to revisit
evidence_set  : ONLY evidence available at this timestamp, each with
                source + published_at + the citation-verifier support label
                (verified/partial/insufficient/contradicts)
confidence    : the user's stated confidence
system_state  : KIWI's own recommendation + risk-gate verdict at the time
user_stage    : the capability-model stage + what the profile knew then
```

**Point-in-time integrity is the core guarantee, and it is exactly the
`as_of` / `published_at` / `point_in_time_allowed` discipline from the citation
work.** A decision snapshot is a frozen point-in-time state, the same object as
a citation span. No future data ever enters a snapshot. The postTrain
obsession with temporal leakage IS the product's integrity guarantee.

### 2. Outcome maturation (accrues over weeks/months, append-only)

```
price_path, fundamental_path since the decision
boundary_triggered: did the "I am wrong if" condition fire? when?
attributable_causes: what actually drove the move (news/earnings/macro)
```

### 3. The retrospective judgment - separating luck from judgment (the core IP)

Two INDEPENDENT axes:

- **Process quality** (uses the trained judges): given evidence available *at
  decision time*, was the reasoning sound? The citation-verifier checks
  whether cited evidence was real and sufficient; the risk-reviewer checks
  whether red flags were ignored; the boundary check asks whether the user
  even stated a falsifiable condition.
- **Outcome**: what happened.

Four quadrants - the labels the user actually sees:

| | good outcome | bad outcome |
| --- | --- | --- |
| **sound reasoning** | reinforce (skill) | **LUCK against you** - accept it, do NOT change the process |
| **flawed reasoning** | **LUCK for you - DANGER** - flag hard, this is where wrong lessons form | genuine mistake -> extract the cognitive-bias lesson |

The two "luck" cells are the whole point. A retrospective tool that only says
"you would have made 30%" trains the top-right and bottom-left into *wrong*
lessons. This system names them as luck and protects the discipline.

### 4. Aggregation - weekly / monthly / yearly (tracks judgment, not returns)

Never "your paper return is +18%". Instead:

- **% of decisions with sound process** (regardless of outcome)
- **recurring cognitive biases** - mapped to the risk-gate red-line taxonomy
  (chasing, anchoring, ignoring counter-evidence, sizing)
- **discipline execution rate** - when a boundary triggered, did the user act?
- **calibration** - did high-confidence decisions actually have better process?

Output updates the capability model (L2) and promotes validated lessons (L1).

### 5. Smart features, reframed to serve growth (per the earlier discussion)

- "recommend hot stocks" -> **surface *review moments***: "MU just reported;
  a data point contradicts your original thesis - want to re-examine?"
  (drives the invalidation trigger, teaches sell discipline, not chasing).
- "when to sell" -> **watch the user's own stated boundary**: the system never
  predicts a sell point; it notices the "I am wrong if" condition the user
  wrote and reminds them to *decide*. User decides; system guards the
  discipline. Dodges the compliance wall, builds the hardest skill.

---

## Part 2 - The same system as a post-training flywheel

### What each matured snapshot becomes

A real, point-in-time-clean trajectory:

```
input   : state at decision time (query + evidence_set + user_stage)
action  : the decision (take/skip/modify)
reward  : PROCESS quality - was the reasoning sound given available evidence
          - NOT the outcome
verifiable components (machine-checkable, not model-guessed):
  - citation validity: cited evidence exists + paragraph-hash matches
  - boundary firing: did the stated invalidation condition trigger (real path)
  - risk-flag presence: rule + model over the decision text
```

### Why this fixes the escalation env's honest weakness

The escalation environment's `p` (will the cheap path succeed?) is currently a
**haiku ensemble guessing** - the "sim != reality" caveat stamped on every
result. The retrospective system **observes real outcomes and real reasoning
quality**. So it upgrades every model-guessed label in the postTrain work into
a reality-anchored one:

| postTrain today | with the retrospective flywheel |
| --- | --- |
| `p` = model guess of cheap-path success | `p` = observed success on real decisions |
| reward = analytic over guessed p | reward = process quality on real trajectories |
| eval labels = blind AI audit | eval labels = AI audit *anchored to real outcomes + boundary firings* |

This is the DeepSeek/Kimi "environment that generates its own verifiable
trajectories" story, made concrete: the product IS the environment, and it
emits verifiable, point-in-time-clean episodes as a by-product of being used.

### The training loop

```
users make decisions -> snapshots (point-in-time clean)
   -> outcomes mature (weeks/months)
   -> retrospective judges process quality (citation + risk + boundary judges)
   -> verified trajectories accumulate
   -> SFT/GRPO on them improves the judges
   -> better judges make retrospectives sharper and coaching better
   -> more users, more decisions  (flywheel)
```

The three postTrain models are the flywheel's engine, not a resume side-quest:
risk-reviewer classifies the cognitive-bias category; citation-verifier decides
whether a signal *should have been visible* with the evidence then available
(the luck-vs-judgment separator); the cost-aware router paces coaching depth by
user stage.

### Honesty limits (state these wherever the flywheel is claimed)

- **Time-gated cold start.** Real outcomes take weeks-to-months; you cannot
  train from real retrospectives on day one. Bootstrap with the current
  audited/synthetic data, then *progressively replace* model-guessed labels
  with matured real trajectories. Track the mix (% real vs % synthetic) as a
  first-class metric.
- **Process-quality label is still a judgment**, now LLM-as-judge or human -
  but ANCHORED to real outcomes and real boundary firings, which is strictly
  stronger than the pure model-guessed `p` it replaces. It is not ground
  truth, it is reality-anchored judgment.
- **Selection / survivorship bias.** Only retained users generate long
  trajectories; churned users' decisions are truncated. Model the churn, don't
  pretend the sample is representative.
- **Point-in-time discipline is load-bearing.** One future-leaked snapshot
  poisons a trajectory. The citation work's temporal-leakage checks must run
  on every snapshot ingestion.

---

## What exists vs what to build

- **Have (KIWI)**: decision paper-tracking incl. skip, thesis+boundary+
  invalidation, outcome_review, lesson loop, decision gate, policy/critic
  governance, user_profile (L2).
- **Have (postTrain)**: the three judges (risk / citation / cost-router),
  frozen audited rulers, the AI-vertical calibration.
- **Build**: (1) the decision-snapshot schema with point-in-time integrity;
  (2) the four-quadrant luck-vs-judgment retrospective; (3) the capability-model
  stage tracker; (4) the trajectory exporter that turns matured snapshots into
  postTrain-format episodes; (5) the real-vs-synthetic mix metric.

## One-line interview throughline

> "The product's retrospective loop and my post-training pipeline are the same
> machine. Every decision a user reviews becomes a point-in-time-clean,
> reality-anchored trajectory that trains the exact judges the product runs on.
> I scored reasoning, never outcome - so the reward that improves the model is
> the same reward that makes a novice a better investor."
