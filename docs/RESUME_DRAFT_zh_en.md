# Resume Draft — zh / en (agentic-RL / post-training internships)

> **OWNER-ONLY HONESTY NOTE — NOT FOR THE RESUME.** Every number below traces to a
> repo doc, but three claim-classes are what an interviewer will probe hardest, so
> know the caveat cold before you put any of them on paper:
> 1. **Simulation-based rewards.** The escalation env's `p_cheap-success` comes from
>    a blind model-ensemble outcome table, **not live tool execution** — the reward
>    ruler is model-derived. Say "faithful simulation of KIWI routing, not the running
>    product." Never imply live-traffic RL.
> 2. **Synthetic personas.** The env v0.4 twin dataset is grown from **36 simulated
>    KIWI users** (tag `synthetic_opus_v1`), not real user logs. Say "simulated
>    personas, point-in-time clean," never "real users."
> 3. **Single-seed items.** Only **two** configs are seed-replicated with zero variance
>    (3B LoRA-GRPO, 7B full-SFT). The 7B oracle solve, the 1.5B/3B full-FT grid-fill
>    solves, and the citation capacity/RL nulls are **single-seed (seed 0)**. Never
>    state a single-seed number as a general result. Also: the "trained 1.5B beats
>    prompted 7B" line is **seed-0-only** — do NOT put it on the resume; it did not
>    survive multi-seed averaging.
> Additional honest framing to hold: env v0.4 is **built but not yet run** (no v0.4
> policy numbers exist); everything ran on a **single, shared/borrowed A100 80GB**
> (say "single-A100 budget," never "cluster"); the citation verdict at 0.387 is a
> confirmed *direction*, not a solved task.

---

## Block 1 — PROJECT: Agentic-RL post-training campaign (postTrain)

**中文**

- 从真实金融产品 KIWI 的查询出发，从零搭建了一个**可验证奖励的升级路由环境**：成本感知路由 +
  安全门（gate）约束 + 解析式 oracle 奖励（final correctness − λ·累计成本，漏门惩罚 −2.0），
  把"该在哪里升级到人工/更强模型"变成可执行、可打分的目标而非主观判断。
- 在**单块 A100 预算**下跑完整方法矩阵 **SFT / DPO / GRPO × 0.5B–7B × LoRA/全量微调**，
  每条实验都带**预注册的 kill 标准**（奖励 ≥ SFT+3 且 gate recall ≥ 0.99），让"训练不划算"
  成为一等结论而非被藏起来的失败。
- 诊断并**机制性解释了一次 GRPO 策略坍缩**：gate 种子仅占训练分布 15%，当同组 K 个补全全部
  同样违门时组内优势 ≈ 0、−2.0 惩罚不产生梯度；量化为 0.5B 全违门率 **0.55（66/120 组）**
  对比 1.5B **0.00（0/95 组）**，坍缩在 **5900+ 条已记录 rollout** 的 `reward_trace` 里
  比 eval 提前暴露。
- 由证据驱动完成**五次自我修正**：多种子把"1.5B 胜过被提示的 7B"降级为仅 seed-0 结论；
  AMD_00 标签审裁（R6 三层防御）；0.5B 坍缩重新归因为 **adapter 容量**而非模型容量；
  7B "掉点"经学习率对照消解为**配置伪影**（LoRA 标准 lr 对 7B 全量微调是错的）；
  env v0.3 判定**饱和**后升级考卷。
- 判定 env v0.3 **饱和**（7+ 配置命中解析 oracle）后自建 **env v0.4 考卷**：**592 个种子**
  （360 base + 232 twin，每对 twin 都翻转 gold），来自 **36 个模拟 KIWI 用户画像**
  （12 初级 / 12 中级 / 12 高级），gold 全部由环境 oracle 计算、零手工标注。
- 做了**跨族证伪**：提示版 Gemma 4（E2B/E4B）gate recall 0.875，推翻"小模型天生守不住门"
  的普适假设——门约束是**族相关**（指令微调 / 安全先验），而受训 Qwen 3B 仍领先约 10 分且完美守门。
- 做了**判官校准**：对两个冻结 ruler 做盲双标注，两遍一致率 **98.5% / 100%**；
  测得 eval id 泄露把小模型注意力带偏 **+11.6 分**，据此上线**匿名化协议**。
- 建了完整**溯源 / 可复现基建**：run manifest（config + git sha + pip freeze）、
  代码级"永不覆盖失败运行"保护、checkpoint/resume，让失败保留成为代码属性而非操作纪律。

**English**

- Built a **verifiable-reward escalation environment** from scratch, seeded from a real
  financial product's (KIWI) queries: cost-aware routing + a safety gate + an analytic
  oracle reward (final correctness − λ·accumulated cost, −2.0 penalty for a missed gate),
  turning "when to escalate to a human / stronger model" into an executable, scorable
  target rather than a judgment call.
- Ran the full method matrix **SFT / DPO / GRPO × 0.5B–7B × LoRA/full-FT** on a
  **single-A100 budget**, every run under **pre-registered kill criteria** (reward ≥ SFT+3
  AND gate recall ≥ 0.99), making "training doesn't pay" a first-class result, not a
  hidden failure.
- Diagnosed and **mechanistically explained a GRPO policy collapse**: gate seeds are only
  15% of the training mix, so when all K in-group completions violate the gate identically,
  within-group advantage ≈ 0 and the −2.0 penalty yields no gradient — quantified as a
  0.5B all-violate rate of **0.55 (66/120 gate groups)** vs 1.5B **0.00 (0/95)**, with the
  collapse surfacing in the **5,900+ logged rollouts'** `reward_trace` before the eval confirmed it.
- Drove **five evidence-forced self-corrections**: a multi-seed headline downgrade
  ("trained 1.5B beats prompted 7B" → seed-0-only); a label-audit ruling (R6 three-tier
  defense); reattributing the 0.5B collapse to **adapter** capacity, not model capacity;
  resolving a learning-rate confound (the 7B "dip" was a **config artifact** — a LoRA-standard
  lr is wrong for 7B full-FT); and, on declaring **env v0.3 saturated**, upgrading the exam.
- After ruling env v0.3 **saturated** (7+ configs hit the analytic oracle), built the
  successor exam **env v0.4**: **592 seeds** (360 base + 232 twins, every twin pair flips gold)
  grown from **36 simulated KIWI user personas** (12 beginner / 12 intermediate / 12 advanced),
  with gold computed by the env's own oracle — **zero hand-assigned labels**.
- Ran a **cross-family falsification**: prompted Gemma 4 (E2B/E4B) reaches gate recall 0.875,
  refuting the "small models are inherently gate-blind" law — gate discipline is
  **family-dependent** (instruction-tuning / safety priors), while trained Qwen 3B still
  leads by ~10 pts and gates perfectly.
- Did **judge-calibration** work: blind double-annotation of two frozen rulers at
  **98.5% / 100%** two-pass agreement; measured a **+11.6-pt** label-leak that steered a small
  model's attention, and shipped an **anonymization protocol** in response.
- Built full **provenance / reproducibility infra**: per-run manifests (config + git sha +
  pip freeze), a code-level **never-overwrite-failed-runs** guard, and checkpoint/resume —
  making failure preservation a property of the code, not operator discipline.

---

## Block 2 — PRODUCT: KIWI financial decision-support copilot

**中文**

- 在代码里实现**双门治理**：`policy.py`（风险 × 置信度 → 动作）+ `critic.py`（独立否决），
  **更严者胜**，保证一层的宽松不会放行另一层判定为危险的操作。
- 构建**复盘系统**：决策快照、**运气 vs 判断力四象限**分类器（把盈利归因于运气还是判断），
  独立成模块、**25 个测试全绿**，只评判推理过程、从不以结果论英雄。
- 制定**决策节点记录规范**：对无法从状态还原的每个选择点冻结时间点干净的快照（九类字段），
  仅追加，把 policy/critic 分歧、用户否决等冲突样本作为最高价值数据。
- 设计**三层防御架构**——代码红线 → 智能复核 → 人工门——这套架构源于一次真实的标签审裁
  （AMD_00 忧虑型咨询查询：有担忧、无第一人称行动意图，应先取证据 / 记忆再判断，而非把
  焦虑直接抛回给用户）。

**English**

- Implemented **dual-gate governance in code**: `policy.py` (risk × confidence → action)
  + `critic.py` (independent veto), **stricter-wins**, so no single layer's leniency can
  release an action another layer flags as risky.
- Built a **retrospective system**: decision snapshots and a **luck-vs-judgment four-quadrant**
  classifier (attributing a win to luck vs judgment), as a standalone module with **25 tests
  passing**, scoring reasoning and never outcome.
- Authored a **decision-node recording spec**: point-in-time-clean, frozen, append-only
  snapshots (nine field categories) for every choice that can't be reconstructed from state,
  treating policy/critic disagreements and user overrides as the highest-value data.
- Designed a **three-tier defense architecture** — code red-lines → smart-review → human gate —
  born from a real label-audit ruling (the AMD_00 concern-type advisory query: a worry with no
  first-person action intent should retrieve evidence/memory and judge first, not bounce the
  user's anxiety back at them).

---

## Block 3 — SKILLS line (honest)

**中文**

TRL（SFT / DPO / GRPO）· PEFT/LoRA + 全量微调 · PyTorch · 评测设计与预注册（kill 标准 /
冻结 ruler / 判官校准）· 多智能体编排 · 实验溯源与可复现（manifest / 失败保留 / checkpoint）

**English**

TRL (SFT / DPO / GRPO) · PEFT/LoRA + full-FT · PyTorch · evaluation design &
pre-registration (kill criteria / frozen rulers / judge calibration) · multi-agent
orchestration · experiment provenance & reproducibility (manifests / failure preservation /
checkpoints)
