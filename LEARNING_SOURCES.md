# Learning Sources

This file records external model reports, papers, posts, and case studies that
influence the post-training artifact.

It is not a bibliography-only file. Every entry must answer:

- what we learned,
- why it matters for KIWI/postTrain,
- what we adopted,
- what we deliberately did not adopt,
- what concrete repo or system change follows from it.

The goal is to keep interview reasoning auditable. We should be able to explain
not only "we read GLM/Qwen/Kimi/DeepSeek/MiniMax", but also what changed in our
data, harness, verifier, or training plan because of that reading.

## Entry Template

```text
Source id:
Title:
Link:
Source type:
Read date:
Confidence:

Core idea:

What we extracted:

Why we extracted it:

What we did not adopt:

Why not:

Mapping to KIWI/postTrain:

Concrete action:

Status:
```

## SRC-2026-06-30-001 - GLM ARC: Agentic + Reasoning + Coding

Source links:

- GLM-4.5 technical report: https://arxiv.org/abs/2508.06471
- GLM-4.5 model/repo page: https://github.com/zai-org/GLM-4.5
- Z.ai GLM-4.5 blog: https://z.ai/blog/glm-4.5
- GLM-5 technical report draft: https://arxiv.org/html/2602.15763v1

Source type:

```text
model report / official blog / repo note / interview-prep synthesis
```

Read date:

```text
2026-06-30
```

Confidence:

```text
medium
```

Reason:

We have captured the core ARC framing from public material and interview-prep
discussion, but still need a deeper source-by-source read before citing exact
training recipes as facts.

### Core Idea

GLM's ARC framing should not be treated as three unrelated capabilities.

```text
Reasoning = understand, plan, self-check, diagnose failure
Coding = turn reasoning into executable and verifiable work
Agentic = observe, act, receive environment feedback, revise
```

The useful abstraction is a loop:

```text
reason about task
  -> act in an environment
  -> get verifier/tool feedback
  -> diagnose the failure
  -> revise the plan or action
```

Coding is important because it is one of the cleanest agentic RL environments:
compilers, unit tests, execution results, and benchmarks provide high-confidence
reward signals.

### What We Extracted

1. Agentic ability depends on reasoning.

   Tool use is not just calling APIs. The model needs to understand the task,
   plan the next action, interpret observations, and diagnose why a previous
   action failed.

2. Coding is a verifier-rich agentic domain.

   Code tasks are valuable because reward can come from executable checks:
   compiler results, tests, patches, and benchmarks. This is the discipline we
   want to mirror in financial research with citation, source, schema, and risk
   verifiers.

3. The training target is the loop, not only the final answer.

   For KIWI, a final memo may look plausible while the evidence chain is wrong.
   We therefore need trajectory-level data: route, search, open/read, extract,
   compare, memo, reviewer, rewrite, and memory gate.

4. Unified ARC is a long-term north star, not our first implementation.

   GLM can aim for a stronger unified agent model. With our current resources,
   the practical version is a coordinator plus narrow specialists, structured
   I/O contracts, deterministic tools, and verifier gates.

5. Reasoning RL, Agentic RL, and General RL should remain separated in our
   mental model.

   Reasoning RL can often use high-confidence answer/verifier signals. Agentic
   RL has harder credit assignment because the failure may live in routing,
   search, reading, tool observation, synthesis, or memory writing. General RL
   then protects assistant behavior and product usability.

### Why We Extracted It

KIWI is not just a report generator. It needs to:

- reason about thesis, risk, contradiction, and invalidation,
- act through tools such as search, filing/news reading, calculators, and
  reviewers,
- use evidence and verifier feedback to revise output,
- decide what should or should not enter memory,
- keep the final user answer concise while preserving a longer internal
  trajectory.

The GLM ARC framing helps us explain why our artifact focuses on structured
trajectories, verifiers, and loop engineering before large-scale model training.

### What We Did Not Adopt

1. We do not adopt "train one unified GLM-like model" as the immediate plan.

2. We do not adopt coding benchmarks as the main portfolio artifact.

3. We do not treat market return as a high-confidence reward signal for first
   stage RL.

4. We do not use ARC as a slogan without data, evals, and failure traces.

5. We do not train a model to perform deterministic calculations when code can
   calculate and verify them more reliably.

### Why Not

- Resource mismatch: we currently plan around one A100 80GB and small-model
  training, not frontier-scale unified model training.
- Domain mismatch: KIWI is a financial research assistant, not primarily a
  software-engineering coding agent.
- Reward mismatch: short-horizon financial outcomes are noisy and unsafe as
  first-stage RL reward. Citation correctness, schema validity, risk coverage,
  and point-in-time freshness are cleaner early rewards.
- Safety mismatch: user preference can influence style and research focus, but
  it must not override risk/compliance boundaries.

### Mapping To KIWI/postTrain

| GLM ARC idea | KIWI/postTrain mapping |
| --- | --- |
| Reasoning | thesis/risk reasoning, contradiction handling, invalidation triggers |
| Coding verifier discipline | citation/source/schema/risk verifiers and deterministic calculators |
| Agentic loop | route -> search/read -> extract -> compare -> memo -> reviewer -> rewrite -> memory gate |
| Unified ARC model | current coordinator + structured specialists; possible future small unified router/tool model |
| High-confidence verifier | exact/source-backed subtasks before noisy market-return tasks |

### Concrete Actions

- Keep narrow specialists as the first trainable units:
  `router_classifier`, `risk_reviewer`, `citation_verifier`,
  `memo_quality_scorer`, and `memory_gate`.
- Add/keep trajectory fields that expose agentic credit assignment:
  route, tool/action, observation, evidence span, contradiction, reviewer issue,
  rewrite, memory proposal, and final quality.
- Treat coding-agent verifier discipline as a template for financial verifiers.
- Use ARC as interview framing for why the project is about loop engineering and
  post-training infrastructure, not only fine-tuning a small model.

### Status

```text
adopted_as_architecture_framing
```

Next learning-source entries should cover Qwen, DeepSeek, Kimi, and MiniMax /
WebExplorer with the same adopt / not-adopt structure.

### Interview Version

GLM's ARC framing is useful for KIWI because it shows that modern agent ability
is not just better chatting. Reasoning gives the model planning, diagnosis, and
self-checking; coding shows how complex tasks can become executable and
verifiable; agentic ability puts the model into an observe-act-feedback-revise
loop. We do not have the resources to train a unified GLM-scale agent model, so
we translate this into KIWI's harness: a coordinator, narrow specialists,
structured tool traces, deterministic verifiers, and memory gates. In short, we
adopt the ARC loop as system architecture, not as a claim that we have trained a
frontier-scale unified model.
