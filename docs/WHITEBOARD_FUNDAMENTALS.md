# 白板基本功 · Whiteboard Fundamentals

*给 Lucine 的面试白板生存手册。你三天前用类比学懂了 seeds / SFT / GRPO 是什么;这份文档把它们的**数学**从零推到你能在白板上一步不跳地写出来。*

**用法**:每节四块结构 —
- **① 从零推导**:每一步都写出来,不跳步,每个符号都解释。
- **② 直觉**:一句人话。
- **③ 面试官会怎么问**:2-3 个典型追问 + 简答。
- **④ 和我们项目的连接**:用真实数字(全部来自 `docs/PORTFOLIO_INDEX.md` 和 `docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md`)。

**语言约定**:讲解用中文,所有数学符号、术语、公式一律用 English / LaTeX 记号。

**记号表(全文通用)**:
- $s$ = state(状态),在 LLM 里就是"到目前为止的 token 序列(prompt + 已生成部分)"。
- $a$ = action(动作),在 LLM 里就是"下一个 token"。
- $\pi_\theta$ = policy(策略),参数为 $\theta$。就是我们的语言模型。
- $\tau$ = trajectory(轨迹),一条完整的序列。
- $R(\tau)$ = return / reward(回报),一条轨迹拿到的分数(标量)。
- $\mathbb{E}$ = expectation(期望)。$\mathbb{E}_{x \sim p}[f(x)] = \sum_x p(x) f(x)$。
- $\nabla_\theta$ = 对参数 $\theta$ 求梯度。
- $\sigma(x) = \frac{1}{1+e^{-x}}$ = sigmoid 函数。

---

## 目录

1. 语言模型即策略 (LM as policy)
2. Policy Gradient 从零推导
3. Baseline 为什么降方差且无偏
4. PPO 的 clip 在干嘛
5. GRPO 完整拼图
6. DPO 从 Bradley-Terry 推出来
7. GAE 是什么(概念级)
8. KL 散度两用
9. 快查表(考前一页复习)
10. 手推练习(答案折叠在文末)

---

## 1. 语言模型即策略 (Language Model as Policy)

### ① 从零推导

一个语言模型在做一件事:给定"到目前为止的文本",预测"下一个 token 的概率分布"。

把"到目前为止的文本"叫 **state** $s$,把"下一个 token"叫 **action** $a$。于是语言模型就是一个条件概率:

$$\pi_\theta(a \mid s)$$

读作:"在状态 $s$ 下,策略 $\pi$(参数 $\theta$)选择动作 $a$ 的概率"。这跟强化学习里的 policy 定义**一模一样** —— 这就是为什么 LLM 后训练能用 RL。

**一条 completion 是一条 trajectory。** 假设 prompt 是 $x$,模型生成的回答是 token 序列 $y = (y_1, y_2, \dots, y_T)$,长度 $T$。生成是 **autoregressive(自回归)** 的:第 $t$ 个 token 依赖前面所有 token。

第 1 步:状态 $s_1 = x$(只有 prompt),动作 $a_1 = y_1$。
第 2 步:状态 $s_2 = (x, y_1)$,动作 $a_2 = y_2$。
第 $t$ 步:状态 $s_t = (x, y_{1:t-1})$,动作 $a_t = y_t$。

所以整条轨迹是 $\tau = (s_1, a_1, s_2, a_2, \dots, s_T, a_T)$。状态转移是**确定性**的(把选中的 token 拼接到序列末尾就是下一个状态),唯一的随机性来自策略的采样。

**整个序列的概率(autoregressive factorization)。** 用概率的链式法则(chain rule):

$$P(y_1, y_2, \dots, y_T \mid x) = P(y_1 \mid x) \cdot P(y_2 \mid x, y_1) \cdots P(y_T \mid x, y_{1:T-1})$$

这一步是**恒等式**,不是近似 —— 任何联合概率都可以这样拆。写成连乘:

$$\pi_\theta(y \mid x) = \prod_{t=1}^{T} \pi_\theta(y_t \mid x, y_{1:t-1})$$

**为什么要取 log(log-prob)。** 连乘在数值上会下溢(很多小于 1 的数相乘 → 趋近 0),而且梯度不好算。取对数把连乘变连加:

$$\log \pi_\theta(y \mid x) = \sum_{t=1}^{T} \log \pi_\theta(y_t \mid x, y_{1:t-1})$$

推导用的就是 $\log(ab) = \log a + \log b$,反复用 $T-1$ 次。**这个式子后面每一节都要用**,记牢:**一个序列的 log-prob = 每个 token 的 log-prob 之和**。

### ② 直觉

语言模型就是一个"下一个词的概率机器";把 prompt+回答看成一步步选词的过程,就是一条 RL 轨迹;整句话的概率 = 每个词概率连乘,取 log 后 = 每个词 log 概率相加。

### ③ 面试官会怎么问

**Q: 为什么 completion 可以看成 trajectory?state 和 action 分别是什么?**
A: state 是"已有的 token 前缀"(prompt 加已生成部分),action 是"下一个 token"。状态转移确定(拼接),随机性只来自采样。所以生成一句话 = 走一条轨迹。

**Q: 为什么用 log-prob 而不是直接用 prob?**
A: 三个原因:(1) 数值稳定,避免连乘下溢;(2) 连乘变连加,求梯度简单;(3) 后面 policy gradient 的 log-derivative trick 天然出现 $\nabla \log \pi$,log 形式直接对接。

**Q: 这个分解是近似吗?**
A: 不是,是概率链式法则的**恒等式**。近似的地方在于我们用有限参数 $\theta$ 去拟合真实分布,但"联合 = 条件连乘"这一步是精确的。

### ④ 和我们项目的连接

我们的 escalation router 里,一个 completion 就是模型输出的一个 plan,比如 `{"first": "gate", "on_fail": "finish"}`。这整个 JSON 串就是一条 trajectory $y$;它的概率 $\pi_\theta(y\mid x)$ 是每个 token log-prob 的和。GRPO 每个 prompt 采 $K=8$ 条这样的 trajectory,靠它们的 reward 差异算梯度(下面第 5 节)。我们的 base 模型是 Qwen2.5 0.5B–7B。

---

## 2. Policy Gradient 从零推导

### ① 从零推导

**目标函数(objective)。** 我们想让策略产生的轨迹平均 reward 最高:

$$J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}[R(\tau)]$$

读作:"在策略 $\pi_\theta$ 生成的轨迹分布下,reward $R(\tau)$ 的期望"。我们要对 $\theta$ 做梯度上升(gradient ascent)来最大化它。所以核心问题是:**怎么算 $\nabla_\theta J(\theta)$?**

难点:轨迹分布 $\pi_\theta$ **本身依赖 $\theta$**,期望的求梯度不能直接把 $\nabla$ 塞进去。

**第 1 步:把期望写成求和(或积分)。** 记 $\pi_\theta(\tau)$ 为整条轨迹的概率:

$$J(\theta) = \sum_\tau \pi_\theta(\tau)\, R(\tau)$$

(连续情形是积分 $\int$,推导一模一样。$R(\tau)$ 不依赖 $\theta$ —— reward 是环境给的,与参数无关。)

**第 2 步:梯度进入求和。** 求和与求梯度可交换,且 $R(\tau)$ 是常数:

$$\nabla_\theta J(\theta) = \sum_\tau \nabla_\theta \pi_\theta(\tau)\, R(\tau)$$

现在卡住了:$\nabla_\theta \pi_\theta(\tau)$ 不是一个期望的形式(前面没有概率权重),没法用采样估计。

**第 3 步:log-derivative trick(乘一除一)。** 关键技巧。对任意概率 $\pi_\theta(\tau) > 0$,同时乘以并除以它自己:

$$\nabla_\theta \pi_\theta(\tau) = \pi_\theta(\tau) \cdot \frac{\nabla_\theta \pi_\theta(\tau)}{\pi_\theta(\tau)}$$

这一步只是乘 1,恒等变形。而右边那个分式,正好是 $\log$ 的导数 —— 微积分基本事实:

$$\frac{d}{d\theta} \log \pi_\theta(\tau) = \frac{1}{\pi_\theta(\tau)} \cdot \frac{d}{d\theta}\pi_\theta(\tau) = \frac{\nabla_\theta \pi_\theta(\tau)}{\pi_\theta(\tau)}$$

(用的是链式法则 $\frac{d}{dx}\log f(x) = \frac{f'(x)}{f(x)}$。)所以:

$$\nabla_\theta \pi_\theta(\tau) = \pi_\theta(\tau) \cdot \nabla_\theta \log \pi_\theta(\tau)$$

**第 4 步:代回去,认出期望。** 把第 3 步的结果代入第 2 步:

$$\nabla_\theta J(\theta) = \sum_\tau \pi_\theta(\tau) \cdot \nabla_\theta \log \pi_\theta(\tau) \cdot R(\tau)$$

现在前面有 $\pi_\theta(\tau)$ 当权重,整个求和**就是一个期望**:

$$\boxed{\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\big[\, R(\tau)\, \nabla_\theta \log \pi_\theta(\tau) \,\big]}$$

这是 **policy gradient theorem**。它的美妙之处:梯度重新变成一个"在当前策略下采样的期望",可以用蒙特卡洛(采几条轨迹取平均)估计。

**第 5 步:REINFORCE(把 trajectory log-prob 展开)。** 用第 1 节的结论,$\log \pi_\theta(\tau) = \sum_t \log \pi_\theta(a_t \mid s_t)$,代入:

$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[ R(\tau) \sum_{t=1}^{T} \nabla_\theta \log \pi_\theta(a_t \mid s_t) \right]$$

用 $N$ 条采样轨迹估计(REINFORCE 算法):

$$\nabla_\theta J(\theta) \approx \frac{1}{N} \sum_{i=1}^{N} R(\tau_i) \sum_{t=1}^{T_i} \nabla_\theta \log \pi_\theta(a_t^{(i)} \mid s_t^{(i)})$$

**直观意义:** 每个 token 的 log-prob 梯度,被整条轨迹的 reward 加权。reward 高 → 推高这条轨迹里所有动作的概率;reward 低(或负)→ 压低。这就是"好的行为多做,坏的行为少做"的数学形式。

**为什么 high variance(高方差)。** 三个来源:
1. **整条轨迹共用一个标量 $R(\tau)$**:即使轨迹里只有一步是关键的好动作,其余是无关动作,整条的 reward 也把它们一视同仁地加权,信号很粗。
2. **reward 的绝对尺度直接进梯度**:如果所有 reward 都是大正数(比如都在 +100 附近),即使它们之间差异很小,梯度也会被这个大基数放大,估计噪声大。
3. **蒙特卡洛采样本身**:$N$ 条轨迹的平均是无偏的,但方差随 $N$ 才慢慢下降;$N$ 小时抖得厉害。

第 3 条尤其是下一节 baseline 要治的病。

### ② 直觉

想让平均分变高,就把"高分轨迹里的每个动作"概率调高、"低分轨迹里的"调低,调整幅度正比于这条轨迹的分数。问题是只有一个总分、尺度还乱飘,所以估出来的梯度噪声很大。

### ③ 面试官会怎么问

**Q: log-derivative trick 那一步为什么能乘一除一?前提是什么?**
A: 前提是 $\pi_\theta(\tau) > 0$(否则除以 0)。乘 $\frac{\pi_\theta}{\pi_\theta}=1$ 是恒等变形,目的是把"裸的 $\nabla\pi$"变成"$\pi$ 乘以 $\nabla\log\pi$",从而前面凑出概率权重、整体变回期望,才能用采样估计。

**Q: policy gradient 为什么方差高?怎么降?**
A: 因为整条轨迹共享一个标量 reward、且 reward 的绝对尺度直接进梯度。降方差的标准手段:(1) 减去 baseline(下一节,把 reward 中心化);(2) 用 advantage 而非 raw reward;(3) reward-to-go(每步只用未来的 reward);(4) 更大的 batch。

**Q: 这个梯度是有偏还是无偏估计?**
A: 蒙特卡洛估计是**无偏**的(期望等于真梯度),问题纯粹在方差。减 baseline 后仍然无偏(下一节证明),所以是"免费降方差"。

### ④ 和我们项目的连接

我们的 escalation env 是 **sequence-level reward**:一条 plan 生成完,环境给一个标量(比如 gate-required seed 上 gate-first = +0.955,非 gate = −1.3 到 −2.0)。这正是 $R(\tau)$。GRPO(第 5 节)本质是 policy gradient 的一个方差更低的变体 —— 它不训练额外的 value model,而是用"同一 prompt 的 $K=8$ 条轨迹的组均值"当 baseline。高方差问题在 0.5B 上尤其致命:采样覆盖不足,直接导致我们观测到的 collapse。

---

## 3. Baseline 为什么降方差且无偏

### ① 从零推导

**想法:** 从 reward 里减掉一个基准值 $b$,梯度变成

$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\big[(R(\tau) - b)\, \nabla_\theta \log \pi_\theta(\tau)\big]$$

我们要证两件事:**(A) 减 $b$ 不改变梯度的期望(无偏)**;**(B) 选对 $b$ 能降方差**。

**(A) 证明无偏 —— 核心是 $\mathbb{E}[b \cdot \nabla \log \pi] = 0$。**

只要证明减掉的那一项期望为 0 即可(这里 $b$ 是常数,不依赖 $\tau$):

$$\mathbb{E}_{\tau \sim \pi_\theta}\big[b \cdot \nabla_\theta \log \pi_\theta(\tau)\big] = b \cdot \mathbb{E}_{\tau \sim \pi_\theta}\big[\nabla_\theta \log \pi_\theta(\tau)\big]$$

现在把这个期望展开成求和,并用 log-derivative trick **反着**用一次:

$$\mathbb{E}_{\tau}\big[\nabla_\theta \log \pi_\theta(\tau)\big] = \sum_\tau \pi_\theta(\tau)\, \nabla_\theta \log \pi_\theta(\tau)$$

由第 2 节第 3 步,$\pi_\theta(\tau)\nabla_\theta\log\pi_\theta(\tau) = \nabla_\theta \pi_\theta(\tau)$,所以:

$$= \sum_\tau \nabla_\theta \pi_\theta(\tau) = \nabla_\theta \sum_\tau \pi_\theta(\tau) = \nabla_\theta (1) = 0$$

**每一步都点破:** 倒数第二个等号,梯度和求和交换;最后一个,$\sum_\tau \pi_\theta(\tau) = 1$(概率归一,对任何 $\theta$ 恒等于常数 1),常数的梯度是 0。

于是:

$$\mathbb{E}[b \cdot \nabla_\theta \log \pi_\theta] = b \cdot 0 = 0$$

**结论:** 减 baseline 不改变期望梯度 —— **无偏**。这也解释了为什么 $b$ 可以依赖 state $s$(只要不依赖 action $a$),因为对每个 $s$ 上面这套归一化论证都成立。

**(B) 为什么降方差(centering 直觉)。**

严格的最优 baseline 有个闭式解,但白板上讲直觉就够:policy gradient 的每一项是 $(R - b) \cdot g$,其中 $g = \nabla\log\pi$。方差 $\mathrm{Var}[(R-b)g]$ 里含 $\mathbb{E}[(R-b)^2 g^2]$ 这样的项。如果不减 $b$,当所有 $R$ 都在一个大正数附近(比如都 ≈ +100),$(R)^2$ 很大 → 方差爆炸,即使动作之间的**相对**好坏差异很小。减去一个接近平均 reward 的 $b$,把 $(R-b)$ **中心化**到 0 附近(有正有负),量级变小 → 方差变小。**期望不变(已证),方差变小 → 免费的午餐。**

**Advantage(优势函数)。** 把中心化后的量正式命名:

$$A(\tau) = R(\tau) - b$$

当 $b$ 取"该状态下的期望 reward"(即 value $V(s)$)时,$A = R - V$ 就是标准的 advantage:"这个动作比平均水平好多少"。正的 advantage → 推高概率,负的 → 压低。

### ② 直觉

比较要有参照系:"考了 80 分"没意义,"比班级平均高 15 分"才有意义。baseline 就是那个平均分;减掉它,梯度只关心"比平均好还是差",不被分数的绝对高低带偏。数学上还证明了这么减不会让梯度跑偏(无偏),纯赚方差。

### ③ 面试官会怎么问

**Q: 证明减 baseline 无偏。**(几乎必考)
A: 只需证 $\mathbb{E}[b\nabla\log\pi]=0$。把它写成 $b\sum_\tau \pi_\theta\nabla\log\pi_\theta = b\sum_\tau\nabla\pi_\theta = b\nabla\sum_\tau\pi_\theta = b\nabla(1) = 0$。关键是 $\sum\pi=1$、常数梯度为 0。

**Q: baseline 可以依赖什么、不能依赖什么?**
A: 可以依赖 state $s$,**不能依赖 action $a$**。因为无偏证明依赖"对给定 $s$,$\sum_a \pi(a\mid s)=1$";若 $b$ 依赖 $a$,这个归一化论证就破了,会引入偏差。

**Q: 最优 baseline 是什么?**
A: 严格最优是"用 $\nabla\log\pi$ 的平方加权的 reward 期望";实践中常用 $V(s)$(状态价值)近似,已经能大幅降方差。白板上说"取接近平均 reward 的值来中心化"即可。

### ④ 和我们项目的连接(重要 —— 这是我们 collapse 的数学根源)

**GRPO 的 group mean 就是 baseline,而且是"推导出来的、不是训练出来的"。** GRPO 对同一个 prompt 采 $K$ 条,用这 $K$ 条 reward 的**组均值** $\bar R = \frac{1}{K}\sum_k R_k$ 当 baseline,advantage $A_i = R_i - \bar R$(再除以组标准差)。它省掉了 PPO 里那个要单独训练的 value model —— 这是 GRPO 省一半显存/算力的核心(第 5 节)。

**但这带来一个致命边界情况:当组内 $K$ 个 reward 全相等时,$\bar R = R_i$,于是 $A_i \equiv 0$ —— 梯度为零。** 这正是我们 0.5B collapse 的机制:在 gate-required seed 上,gate-first 恒为 +0.955、非 gate 恒为 −1.3~−2.0。一旦策略在某个 seed 上 8 条采样**全是**非 gate(all-violate),这 8 个 reward 全等 → std ≈ 0 → advantage ≈ 0 → **梯度为零**。哪怕有 −2.0 的重罚,也传不出任何学习信号。

真实数字:0.5B 上 **55%(66/120)** 的 gate-required 组是 all-violate,而 1.5B 是 **0%(0/95)**。这就是为什么 0.5B collapse、1.5B 不会 —— 不是 reward 设计错了(两边 reward 函数完全一样),而是弱策略采样覆盖不足,触发了 baseline 的零梯度陷阱。

---

## 4. PPO 的 clip 在干嘛

### ① 从零推导

**动机:** REINFORCE 每采一批数据只能更新一次(on-policy);更新后策略变了,旧数据就"过期"。能不能用旧策略采的数据多更新几步?可以,但要防止策略一步跨太远把自己搞坏。PPO 就是干这个的。

**第 1 步:importance ratio(重要性比值)。** 设 $\pi_{old}$ 是采样时用的旧策略,$\pi_\theta$ 是正在更新的新策略。定义比值:

$$r_t(\theta) = \frac{\pi_\theta(a_t \mid s_t)}{\pi_{old}(a_t \mid s_t)}$$

它衡量"新策略相对旧策略,对这个动作的偏好变了多少"。$r_t = 1$ 表示没变;$r_t > 1$ 表示新策略更喜欢这个动作;$r_t < 1$ 表示更不喜欢。注意 $r_t(\theta_{old}) = 1$,且 $\nabla_\theta r_t = r_t \nabla_\theta \log\pi_\theta$ —— 所以 $r_t \cdot A$ 在 $\theta=\theta_{old}$ 处的梯度就退回普通 policy gradient。

**第 2 步:未裁剪目标。** 用 importance sampling 把 policy gradient 改写成用旧数据算的目标:

$$L^{CPI}(\theta) = \mathbb{E}\big[ r_t(\theta)\, A_t \big]$$

($A_t$ 是 advantage;CPI = conservative policy iteration。)问题:如果某步 $A_t > 0$,优化器会把 $r_t$ 推到很大(无限放大这个动作的概率),策略一步跑飞;$A_t < 0$ 时同理往下崩。

**第 3 步:clip(裁剪)—— 造一个信赖域(trust region)。** PPO 的核心目标:

$$L^{CLIP}(\theta) = \mathbb{E}\Big[ \min\big(\, r_t A_t,\ \ \mathrm{clip}(r_t,\, 1-\epsilon,\, 1+\epsilon)\, A_t \,\big) \Big]$$

其中 $\mathrm{clip}(r, 1-\epsilon, 1+\epsilon)$ 把 $r$ 限制在 $[1-\epsilon, 1+\epsilon]$ 区间($\epsilon$ 常取 0.2)。**逐项理解这个 $\min$:**

- **当 $A_t > 0$(好动作)**:我们想增大 $r_t$。但一旦 $r_t > 1+\epsilon$,裁剪项 $(1+\epsilon)A_t$ 成为常数,不再随 $r_t$ 增大 —— 梯度归零,**不再奖励更激进的推高**。$\min$ 保证取较小者,即被裁剪住的那个。
- **当 $A_t < 0$(坏动作)**:我们想减小 $r_t$。一旦 $r_t < 1-\epsilon$,裁剪项 $(1-\epsilon)A_t$(注意 $A_t<0$,这是个"没那么负"的数)成为下界。$\min$ 在负 advantage 下取更负的那个,效果是:压低到 $1-\epsilon$ 就够了,不鼓励压得更狠。

**净效果:** 只要新旧策略偏差还在 $[1-\epsilon, 1+\epsilon]$ 内,目标就跟普通 policy gradient 一样;一旦超出,梯度被砍掉 —— 相当于给"每一步策略能变多少"上了一道**软性信赖域**,防止破坏性更新(destructive update)。

**第 4 步:value model 在 PPO 里干嘛(learned baseline)。** PPO 需要 $A_t$,而 $A_t = R - V(s)$ 需要一个 value 估计 $V(s)$。PPO 单独训练一个 **value network**(通常和 policy 共享 backbone 或独立一个网络),用回归损失 $\big(V_\phi(s_t) - \hat R_t\big)^2$ 拟合。这个学出来的 $V$ 就是第 3 节的 baseline —— **learned baseline**。

**它的代价:** 你要同时在显存里放 policy + value 两个网络、跑两套前向/反向、调两组超参、承担 value 拟合不准带来的额外偏差。对小显存/小模型场景是实打实的负担 —— 这正是 GRPO 要砍掉的东西。

### ② 直觉

允许用旧数据多更新几步,但给每步策略变化套个"安全带":变化在 ±20% 以内照常学,超出就松油门(梯度归零),防止一步跳崖。value model 是那个提供"平均分参照"的副驾驶,好用但要额外养一个。

### ③ 面试官会怎么问

**Q: clip 的 $\min$ 为什么要取 min?去掉会怎样?**
A: $\min$ 保证"当动作好($A>0$)且策略已经推得够远时,不再给正向梯度"。若不取 min(只用 $r A$),优化器会把好动作的概率推到爆,策略崩。min 把 objective 变成真实提升的**下界(lower bound / pessimistic bound)**,只在信赖域内老实提升。

**Q: 为什么 clip 是"软"信赖域,和 TRPO 的硬约束区别?**
A: TRPO 用 KL 硬约束(带约束优化,要算二阶/共轭梯度,复杂)。PPO 用 clip 把约束**折进目标函数**,一阶 SGD 就能跑,工程上简单得多 —— 这是 PPO 流行的原因。

**Q: PPO 里 value model 出问题会怎样?**
A: value 拟合不准 → advantage 估计有偏 → 梯度方向带偏。而且它吃显存/算力。GRPO 的动机之一就是"能不能不训 value,直接用组内相对比较当 baseline"。

### ④ 和我们项目的连接

我们的 GRPO 用的正是 **PPO 式的 clipped surrogate**(带 importance ratio 和 clip),只是把 value model 换成了组均值 baseline。省掉 value network 让我们在**单张 A100 80GB** 上跑得动 7B(batch 8 / grad-accum 2)。clip 的信赖域作用在我们的 collapse 分析里也有回响:0.5B 的 KL 跑到 5.07(健康的 1.5B 只有 0.36),说明策略偏离旧策略太远 —— clip/KL 这类信赖域机制正是为了防这种失控漂移(第 8 节)。

---

## 5. GRPO 完整拼图 (Group Relative Policy Optimization)

### ① 从零推导

GRPO = **去掉 value model 的 PPO**,用"同一 prompt 的一组样本"内部比较来算 advantage。逐块拼起来:

**第 1 步:每个 prompt 采 K 个样本。** 对每个 prompt $x$,用旧策略采 $K$ 条 completion(我们 $K=8$):$y_1, \dots, y_K$,拿到各自 reward $R_1, \dots, R_K$。

**第 2 步:group-relative advantage(组内相对优势)。** 用这 $K$ 个 reward 的组内均值和标准差把每个 reward 标准化:

$$\hat A_i = \frac{R_i - \mathrm{mean}(R_{1:K})}{\mathrm{std}(R_{1:K})}$$

其中 $\mathrm{mean} = \frac{1}{K}\sum_{k=1}^K R_k$,$\mathrm{std} = \sqrt{\frac{1}{K}\sum_k (R_k - \mathrm{mean})^2}$(实现里常加一个小 $\epsilon$ 防除零)。

**为什么这就是 baseline:** 分子 $R_i - \mathrm{mean}$ 就是第 3 节的 $R - b$,$b$ 取组均值。它是**推导出来的、不是训练出来的** —— 不需要 value network,组均值天然是这个 prompt 的无偏 baseline(每条样本对称,均值就是该 prompt 的期望 reward 的样本估计)。除以 std 是额外的白化(whitening),让不同 prompt 的 advantage 尺度可比,进一步稳梯度。

**第 3 步:PPO 式 clipped surrogate,用组 advantage。** 把 $\hat A_i$ 塞进第 4 节的 clipped 目标(token 级或序列级;我们是序列级 reward,见下方"简化说明"):

$$L^{GRPO}(\theta) = \mathbb{E}_i\Big[ \min\big( r_i(\theta)\hat A_i,\ \mathrm{clip}(r_i(\theta), 1-\epsilon, 1+\epsilon)\hat A_i \big) \Big] - \beta\, \mathrm{KL}\big(\pi_\theta \,\|\, \pi_{ref}\big)$$

其中 $r_i(\theta) = \pi_\theta(y_i\mid x)/\pi_{old}(y_i\mid x)$。

> **简化说明(白板要主动交代,别被追问):** 严格的 GRPO 是 **per-token** 的:ratio、clip、KL 都在每个 token 上算,同一条序列里所有 token 共享该序列的 $\hat A_i$。我这里为了讲清楚写成 per-sequence 形式。对我们的 escalation 任务这个简化基本无害,因为 reward 是**序列级**的(整条 plan 一个分数),没有 per-token 的价值差异。面试时说一句"我知道实现是 per-token,这里为讲解简化成序列级"就足够 —— 这正是面试官想听到的诚实。

**第 4 步:KL penalty(拴绳项)。** $-\beta\,\mathrm{KL}(\pi_\theta\|\pi_{ref})$ 把当前策略拴在参考策略 $\pi_{ref}$(通常是 SFT 后、RL 前的模型)附近,防止 RL 把模型带得离原始能力太远。$\beta$ 是拴绳松紧(第 8 节详述)。

**为什么不要 value model(核心卖点):** PPO 需要 value network 提供 baseline;GRPO 用组均值代替。**代价对比:** 少一个和 policy 同量级的网络 → **显存/算力大致减半**,少调一组超参,少一个偏差来源。代价是每个 prompt 必须采 $K$ 条(采样成本上升),且 baseline 质量依赖组内多样性 —— 这是它的软肋(见 failure modes)。

**Failure modes(三个,全部在我们项目里观测到):**

1. **Zero-spread groups(组内零方差 → 零梯度)。** 若组内 $K$ 个 reward 全等,$\mathrm{std}\to 0$、$\hat A_i \to 0$ → 梯度消失。这是第 3 节讲的机制。真实:0.5B 上 55% 的 gate 组 all-violate。

2. **Low-frequency action squeezed(低频动作被挤压 → 灭绝)。** gate 是稀有动作(24/160 ≈ 15% 的 seed 需要)。一旦它概率下滑,采 8 条全避开它的概率上升,组变哑,gate 得不到反梯度,同时被大量非 gate seed 的梯度压力持续压低 → **gate 动作灭绝(gate extinction)**。真实:我们的 gate first-action share 从 62.6%(step 1–50)→ 1.9%(step 151–200)→ 灭绝。

3. **KL runaway(KL 失控)。** 策略漂离参考太远,KL 一路涨。真实:0.5B 崩溃时 KL 峰值 **5.07**(step 150,正是 gate 灭绝之时),末段稳定在 ~2.1;健康的 1.5B 只有 **0.36**(6 倍差)。KL 越过 1.5 并停在那里,是崩溃的**领先指标**(比 eval 报出 gate_recall=0 更早)。

### ② 直觉

GRPO 的省钱大招:与其单独养一个"打分副驾驶"(value model),不如对同一道题让模型答 8 遍,拿这 8 个分数的组内排名当参照 —— 谁比组平均好就推高谁。副作用:如果 8 遍答得一模一样(尤其在稀有正确动作上全答错),组内没差异,就学不到任何东西。

### ③ 面试官会怎么问

**Q: GRPO 和 PPO 的核心区别?省了什么、代价是什么?**
A: 核心区别是 baseline 来源:PPO 用**训练出来的** value network,GRPO 用**同一 prompt 的组均值**。省了整个 value network(显存/算力约减半、少一组超参、少一个偏差源)。代价:每 prompt 要采 $K$ 条(采样贵),且 baseline 质量依赖组内多样性 —— 组内零方差就零梯度。

**Q: 什么情况下 GRPO 学不到东西?**(考 collapse 机制)
A: 当某 prompt 的 $K$ 个样本 reward 全相等,advantage 全为 0,梯度消失。最危险的是稀有高罚动作:一旦策略开始少做它,采样全避开它 → 组全等 → 零梯度 → 该动作彻底灭绝,自我强化。我们在 0.5B 上量化到 55% 的 gate 组 all-violate。

**Q: 怎么救?**
A: (1) **gate-seed oversampling / 强制混合组**:保证每组至少有一条 gate 样本 → 组内有方差 → advantage 非零(这是我们的主修复);(2) 更大的 $K$:$P(\text{all-violate}) = (1-p)^K$,K 越大越难全哑;(3) 更紧的 KL 控制,减慢漂移,给信号纠正的时间。

### ④ 和我们项目的连接

GRPO 是我们的**皇冠成果**来源:**3B GRPO-v2 三个 seed 全部命中 analytic oracle 0.8473 / gate 1.000,std = 0**(零方差复现)。同时它也是我们**最深的失败分析**来源:0.5B collapse(2/3 seed,reward 0.383 / gate 0.00)。关键洞见:这个 collapse 后来被**重新归因** —— 换成**全参数**(而非 LoRA r=16)重跑同一个 0.5B GRPO **不崩**(reward 0.7533 / gate 0.75),所以是 **adapter 容量地板**,不是模型容量地板。RL 增量是**任务相关**的:escalation 1.5B 上 RL 比 SFT +4.9 分,3B 上只 +0.45(已被 oracle 封顶),citation verdict 上 **+0.0**(数据健康后 RL 一分不加)。"不为 RL 而 RL"是我们用数字证出来的,不是口号。

---

## 6. DPO 从 Bradley-Terry 推出来 (Direct Preference Optimization)

### ① 从零推导

DPO 的魔法:**跳过训练 reward model 和跑 RL,直接用偏好对(preference pairs)优化策略**。它的推导是把 RLHF 的最优解反解出来,代进偏好模型。一步步来。

**第 1 步:Bradley-Terry(BT)偏好模型。** 给定两个回答 $y_w$(winner,偏好的)和 $y_l$(loser),假设它们有隐含奖励 $r(y_w), r(y_l)$。BT 模型说"偏好 $y_w$ 的概率"是奖励差的 sigmoid:

$$P(y_w \succ y_l) = \frac{\exp(r(y_w))}{\exp(r(y_w)) + \exp(r(y_l))}$$

分子分母同除 $\exp(r(y_w))$:

$$= \frac{1}{1 + \exp(r(y_l) - r(y_w))} = \frac{1}{1 + \exp\big(-(r(y_w) - r(y_l))\big)} = \sigma\big(r(y_w) - r(y_l)\big)$$

用了 $\sigma(x) = \frac{1}{1+e^{-x}}$。**所以偏好概率 = sigmoid(奖励差)。** 记牢这个形式。

**第 2 步:RLHF 的 KL 约束目标 → 最优策略闭式解。** RLHF 优化的目标是"最大化 reward,同时别离参考策略太远":

$$\max_\pi\ \mathbb{E}_{y\sim\pi}\big[r(y)\big] - \beta\, \mathrm{KL}\big(\pi(y) \,\|\, \pi_{ref}(y)\big)$$

$\beta$ 控制"追求 reward"和"贴着 $\pi_{ref}$"之间的权衡。这个带 KL 约束的优化有**闭式最优解**(标准结论,推导见下方补充):

$$\pi^*(y) = \frac{1}{Z}\, \pi_{ref}(y)\, \exp\!\Big(\frac{1}{\beta} r(y)\Big)$$

其中 $Z = \sum_y \pi_{ref}(y)\exp(\frac{1}{\beta}r(y))$ 是归一化常数(partition function),保证 $\pi^*$ 是合法概率分布。

> **补充(闭式解怎么来的,面试可能追问):** 把 KL 展开成 $\sum_y \pi(y)\log\frac{\pi(y)}{\pi_{ref}(y)}$,对 $\pi$ 做带"$\sum\pi=1$"约束的变分/拉格朗日优化,令导数为 0,解出 $\pi^*(y) \propto \pi_{ref}(y)\exp(r(y)/\beta)$。直觉:最优策略 = 参考策略被 reward **指数级重加权**。

**第 3 步:反解 —— 用 $\pi$ 表达 $r$。** 这是 DPO 的关键一招。把上式两边取 log 并解出 $r(y)$:

$$\log \pi^*(y) = \log \pi_{ref}(y) + \frac{1}{\beta} r(y) - \log Z$$

移项:

$$\frac{1}{\beta} r(y) = \log \pi^*(y) - \log \pi_{ref}(y) + \log Z$$

$$r(y) = \beta \log \frac{\pi^*(y)}{\pi_{ref}(y)} + \beta \log Z$$

**关键观察:** reward 被表达成了"策略与参考策略的 log 比值",外加一个只依赖 $\beta$ 和 $Z$、**不依赖 $y$** 的项 $\beta\log Z$。我们把待优化的策略 $\pi_\theta$ 当作 $\pi^*$ 来学。

**第 4 步:代入 BT loss —— $\log Z$ 消掉。** 现在算奖励差 $r(y_w) - r(y_l)$。注意 $\beta\log Z$ 这项对 $y_w$ 和 $y_l$ 是**同一个常数**($Z$ 不依赖具体的 $y$),相减时抵消:

$$r(y_w) - r(y_l) = \Big(\beta\log\frac{\pi_\theta(y_w)}{\pi_{ref}(y_w)} + \beta\log Z\Big) - \Big(\beta\log\frac{\pi_\theta(y_l)}{\pi_{ref}(y_l)} + \beta\log Z\Big)$$

$$= \beta\log\frac{\pi_\theta(y_w)}{\pi_{ref}(y_w)} - \beta\log\frac{\pi_\theta(y_l)}{\pi_{ref}(y_l)}$$

**$\log Z$ 消失了 —— 这就是 DPO 不需要算那个麻烦的归一化常数、也不需要 reward model 的原因。**

**第 5 步:组装 DPO loss。** 把奖励差代进第 1 步的 BT 概率 $P(y_w\succ y_l) = \sigma(r(y_w)-r(y_l))$,再取负对数似然(negative log-likelihood,最大化偏好数据的似然):

$$\boxed{\ \mathcal{L}_{DPO}(\theta) = -\log\sigma\!\left(\beta\log\frac{\pi_\theta(y_w)}{\pi_{ref}(y_w)} - \beta\log\frac{\pi_\theta(y_l)}{\pi_{ref}(y_l)}\right)\ }$$

**这就是完整的 DPO 损失。** 它只需要:偏好对 $(y_w, y_l)$、当前策略 $\pi_\theta$、冻结的参考策略 $\pi_{ref}$。没有 reward model、没有采样、没有 RL loop —— 一个监督式的分类损失。

**$\beta$ 的含义(拴绳):** $\beta$ 是"策略能偏离 $\pi_{ref}$ 多远"的松紧。$\beta$ **大** → 拴得**紧**,策略贴着参考,保守、探索少;$\beta$ **小** → 拴得**松**,允许策略为满足偏好而大幅偏离参考,探索多但可能不稳。它扮演的角色和第 5 节 GRPO 里 KL 项的 $\beta$ 是同一个"信赖域旋钮"(第 8 节把两者统一)。

### ② 直觉

不用先训一个打分器再跑 RL,而是发现"最优策略和 reward 之间有个可反解的公式",于是把 reward 换成"新旧模型的 log 概率比",直接拿"好答案 vs 坏答案"的对子做一个 sigmoid 分类:推高好答案相对参考的概率、压低坏答案的。$\beta$ 是那根拴住模型别跑太远的绳。

### ③ 面试官会怎么问

**Q: DPO 为什么不需要 reward model?$\log Z$ 去哪了?**
A: 因为把 RLHF 最优策略反解成 $r = \beta\log(\pi/\pi_{ref}) + \beta\log Z$,代进 BT 的**奖励差**时,$\beta\log Z$ 对 winner/loser 是同一个常数,**相减抵消**。于是 loss 里根本不出现 $Z$,也不出现显式 reward —— reward 被隐式地表达成 log 概率比。

**Q: $\beta$ 调大调小分别什么效果?**
A: $\beta$ 大 = 拴得紧 = 贴 $\pi_{ref}$、保守、探索少;$\beta$ 小 = 拴得松 = 允许大幅偏离、探索多但可能不稳。它是 KL 约束的强度。

**Q: DPO 和 PPO/GRPO 相比,优劣?**
A: 优:无 reward model、无采样、无 RL 不稳定性,一个监督 loss,简单稳定。劣:只能用**离线偏好对**,不能在线探索;数据里没覆盖的行为学不到 —— 所以 DPO 常表现得保守/安全但探索不足(这正是我们观测到的)。

### ④ 和我们项目的连接

我们把 DPO 也跑了,结论很干净:**DPO = 安全,GRPO = 效率,SFT = 平衡基线**(三方法对比已 final)。DPO 在 1.5B 上是 **gate 1.000(完美安全)但 success 只有 0.58**(v1)—— 门把得死死的,但探索差、reward 塌。我们做了 **β sweep(0.1 / 0.3 / 0.5)**:放松 β 只把 success 从 0.58 拉到 0.67,**仍比 SFT 基线 0.7495 低约 15 分**,而且 β=0.3 和 β=0.5 产出**逐位相同的 greedy policy**。跨 **2 种配对设计 × 3 个 β** 都稳定,所以 DPO 的"安全优先 / 探索贫乏"性格是**结构性的(STRUCTURAL)**,不是超参意外。这印证了 ③ 里"DPO 保守但探索不足"的理论预期。

---

## 7. GAE 是什么(概念级即可 —— 我们没用到)

### ① 从零推导(概念级)

GAE = Generalized Advantage Estimation,PPO 里估 advantage 的标准方法。我们的 GRPO 用序列级组均值 advantage,**没用 GAE**,所以只需概念级理解、能应对追问即可。

**TD error(时序差分误差)。** 定义单步的 TD error:

$$\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)$$

读作:"实际拿到的即时 reward $r_t$ 加上折扣后的下一状态价值 $\gamma V(s_{t+1})$,减去当前状态价值 $V(s_t)$"。它是"这一步比预期好多少"的单步估计($\gamma$ 是折扣因子,$V$ 是 value 函数)。

**GAE = TD error 的几何加权和。**

$$\hat A_t^{GAE} = \sum_{k=0}^{\infty} (\gamma\lambda)^k\, \delta_{t+k} = \delta_t + (\gamma\lambda)\delta_{t+1} + (\gamma\lambda)^2\delta_{t+2} + \cdots$$

$\lambda \in [0,1]$ 是一个**偏差-方差旋钮**:
- $\lambda = 0$:$\hat A_t = \delta_t$,退化成 **TD(0)** —— 只看一步,**低方差、高偏差**(严重依赖 $V$ 估得准不准)。
- $\lambda = 1$:变成 **Monte Carlo** advantage(用整条轨迹的实际 return)—— **高方差、低偏差**(不依赖 $V$ 的准确度)。
- 中间值:在两者之间平滑插值,实践中常取 $\lambda \approx 0.95$。

### ② 直觉

GAE 是一个旋钮($\lambda$),在"只信一步、稳但可能有系统偏差"和"信整条轨迹、准但抖"之间找平衡点。

### ③ 面试官会怎么问

**Q: GAE 的 $\lambda$ 调的是什么?**
A: bias-variance trade-off。$\lambda\to 0$ 偏 TD(0),低方差高偏差;$\lambda\to 1$ 偏 Monte Carlo,高方差低偏差。

**Q: GRPO 为什么不需要 GAE?**(一句话)
A: 因为我们的 reward 是**序列级**的(整条 completion 一个标量分数),没有 per-token 的 value 需要 bootstrap;GAE 是为**逐 token / 逐时间步**的价值估计设计的。GRPO 直接用组内相对 reward 当 advantage,绕过了 per-step value 估计,所以用不上 GAE。

### ④ 和我们项目的连接

我们全程没用 GAE —— escalation 和 citation 都是序列级 reward(一条 plan / 一个 verdict 一个分数)。面试时如果被追问"你为什么不用 GAE",标准答案就是上面那句:序列级 reward + 无 per-token value + GRPO 的组相对 advantage 已经提供了 baseline。这是主动交代简化、避免被戳的点。

---

## 8. KL 散度两用 (KL Divergence, two roles)

### ① 从零推导

**定义。** 两个分布 $P, Q$ 的 KL 散度:

$$\mathrm{KL}(P \,\|\, Q) = \sum_x P(x)\log\frac{P(x)}{Q(x)} = \mathbb{E}_{x\sim P}\Big[\log\frac{P(x)}{Q(x)}\Big]$$

它衡量"用 $Q$ 近似 $P$ 时损失了多少信息"。性质:$\mathrm{KL}\geq 0$,当且仅当 $P=Q$ 时为 0;**不对称** —— $\mathrm{KL}(P\|Q)\neq\mathrm{KL}(Q\|P)$。

**Forward vs Reverse(一句话区分)。**
- **Forward** $\mathrm{KL}(P\|Q)$(数据在 $P$):$Q$ 会"mass-covering"(铺开去覆盖 $P$ 的所有众数,宁可胖不遗漏)。
- **Reverse** $\mathrm{KL}(Q\|P)$(期望在 $Q$):$Q$ 会"mode-seeking"(缩到 $P$ 的一个众数上,宁可窄不出错)。RL 里的 KL 惩罚通常是 reverse 方向 $\mathrm{KL}(\pi_\theta\|\pi_{ref})$。

**KL 的两个用途(白板重点):**

**用途一:drift-brake(漂移刹车)—— 在 RLOO / GRPO / PPO 里。** 在 RL 目标里加 $-\beta\,\mathrm{KL}(\pi_\theta\|\pi_{ref})$,把当前策略拴在参考策略(SFT 后模型)附近。作用:防止 RL 为了刷 reward 把模型带到离原始语言能力很远的畸形区域(reward hacking / 语言退化)。$\beta$ 是刹车力度。

**用途二:DPO 里的 $\beta$。** 第 6 节推导中,RLHF 的 KL 约束目标 $\max \mathbb{E}[r] - \beta\mathrm{KL}(\pi\|\pi_{ref})$ 里的那个 KL,反解后变成 DPO loss 里的 $\beta$ 系数。**所以 DPO 的 $\beta$ 本质就是一个 KL 约束的强度** —— 和用途一是同一个东西,只是一个显式出现在 loss 里(GRPO),一个被吸收进 log 概率比的系数里(DPO)。

### ② 直觉

KL 就是"两个分布差多远"的尺子,而且方向不对称。它在后训练里扮演同一个角色的两个化身:一根拴住模型别跑太野的绳。在 GRPO 里绳子明晃晃写在 loss 里($\beta\cdot$KL),在 DPO 里绳子藏在 $\beta$ 系数里。

### ③ 面试官会怎么问

**Q: forward 和 reverse KL 有什么区别,RL 里用哪个?**
A: forward $\mathrm{KL}(P\|Q)$ mass-covering(铺开);reverse $\mathrm{KL}(Q\|P)$ mode-seeking(收窄)。RL 惩罚通常用 reverse $\mathrm{KL}(\pi_\theta\|\pi_{ref})$,期望在当前策略下取,惩罚它偏离参考。

**Q: GRPO 的 KL 和 DPO 的 β 是一回事吗?**
A: 本质是同一个 KL 约束。GRPO 里显式写成 loss 项 $-\beta\mathrm{KL}(\pi_\theta\|\pi_{ref})$;DPO 里,那个 KL 约束在推导时被反解、吸收成了 log 概率比前面的 $\beta$ 系数。两者都是"拴绳松紧"。

**Q: KL 太大意味着什么?怎么用它做诊断?**
A: KL 持续走高 = 策略正在剧烈偏离参考,通常预示不稳定或崩溃。它是**领先指标**:eval 报出问题之前,训练 trace 里的 KL 已经涨了。

### ④ 和我们项目的连接

KL 是我们 collapse 诊断的**核心信号**。0.5B 崩溃时 KL 峰值 **5.07**(step 150,恰是 gate 动作灭绝的时刻),末段稳定 **~2.1**;健康的 1.5B 全程只有 **0.36**(6 倍差)。我们把"KL 越过 1.5 并停在那里"列为崩溃的**领先指标**(比 eval 报出 gate_recall=0 更早触发)。诊断规则:gate share 崩塌 **且** KL > 1.5 同时出现 → 提前中止,不用烧完剩余预算等 eval 确认。这是"用 KL 当刹车"和"用 KL 当诊断"两个用途在我们真实数据里的交汇。

---

## 9. 快查表(考前一页复习)

| 概念 | 公式 | 一句话直觉 |
|---|---|---|
| **LM = policy** | $\pi_\theta(a\mid s)$ | 语言模型 = 下一个词的概率机器 |
| **序列 log-prob** | $\log\pi_\theta(y\mid x)=\sum_t\log\pi_\theta(y_t\mid x,y_{<t})$ | 整句 log 概率 = 每词 log 概率相加 |
| **PG 目标** | $J(\theta)=\mathbb{E}_{\tau\sim\pi_\theta}[R(\tau)]$ | 让平均 reward 最高 |
| **Policy gradient** | $\nabla J=\mathbb{E}[R(\tau)\nabla\log\pi_\theta(\tau)]$ | reward 加权的 log-prob 梯度;好行为多做 |
| **log-derivative trick** | $\nabla\pi=\pi\nabla\log\pi$ | 乘一除一,把裸梯度变回期望 |
| **Baseline 无偏** | $\mathbb{E}[b\nabla\log\pi]=b\nabla\sum\pi=b\nabla 1=0$ | 减 baseline 不改期望,纯降方差 |
| **Advantage** | $A=R-b$(常取 $b=V(s)$) | 比平均好多少 |
| **PPO ratio** | $r_t(\theta)=\pi_\theta/\pi_{old}$ | 新旧策略偏好之比 |
| **PPO clip** | $\min(rA,\ \mathrm{clip}(r,1\pm\epsilon)A)$ | 变化 ±ε 内照学,超出松油门(软信赖域) |
| **GRPO advantage** | $\hat A_i=\frac{R_i-\mathrm{mean}}{\mathrm{std}}$($K$ 样本) | 组均值当 baseline,推导出来非训练;组内零方差→零梯度 |
| **GRPO 目标** | clipped surrogate $+$ $\beta\mathrm{KL}(\pi_\theta\|\pi_{ref})$,无 value model | 去掉 value 的 PPO,显存减半 |
| **BT model** | $P(y_w\succ y_l)=\sigma(r(y_w)-r(y_l))$ | 偏好概率 = sigmoid(奖励差) |
| **RLHF 最优策略** | $\pi^*\propto\pi_{ref}\exp(r/\beta)$ | 参考策略被 reward 指数重加权 |
| **DPO loss** | $-\log\sigma\big(\beta\log\frac{\pi_\theta(y_w)}{\pi_{ref}(y_w)}-\beta\log\frac{\pi_\theta(y_l)}{\pi_{ref}(y_l)}\big)$ | 反解 reward 代进 BT;$\log Z$ 抵消;监督式分类 |
| **TD error** | $\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)$ | 这一步比预期好多少 |
| **GAE** | $\hat A_t=\sum_k(\gamma\lambda)^k\delta_{t+k}$ | $\lambda$ 旋钮:TD(0) 稳↔MC 准 |
| **KL** | $\mathrm{KL}(P\|Q)=\mathbb{E}_P[\log\frac{P}{Q}]\geq 0$ | 分布距离;不对称;当拴绳/诊断用 |

**我们项目的关键数字(考前扫一眼):** 3B GRPO oracle 0.8473 / gate 1.000 / std 0(×3 seed)。0.5B collapse:reward 0.383 / gate 0.00,all-violate 55%(66/120),KL 峰 5.07。1.5B 健康:all-violate 0%(0/95),KL 0.36。DPO 1.5B:gate 1.000 / success 0.58,β sweep 0.1/0.3/0.5 结构性保守。RL 增量:escalation 1.5B +4.9、3B +0.45、citation +0.0。

---

## 10. 手推练习(答案折叠在文末)

先自己在白板上推,再对答案。这 5 道覆盖了最可能被问的推导。

**练习 1.** 从 $J(\theta)=\mathbb{E}_{\tau\sim\pi_\theta}[R(\tau)]$ 出发,推出带 baseline 的 policy gradient $\nabla J=\mathbb{E}[(R(\tau)-b)\nabla\log\pi_\theta(\tau)]$。写出 log-derivative trick 那一步。

**练习 2.** 证明 group-mean baseline 无偏,即 $\mathbb{E}[b\cdot\nabla\log\pi_\theta]=0$。点破用到 $\sum\pi=1$ 的地方。

**练习 3.** 一组 4 个样本的 reward 是 $\{0.7,\ 0.7,\ 0.66,\ -0.04\}$。计算 GRPO 的 4 个 advantage $\hat A_i=\frac{R_i-\mathrm{mean}}{\mathrm{std}}$(用总体 std,即除以 $K$)。

**练习 4.** 从 BT 模型 $P(y_w\succ y_l)=\sigma(r(y_w)-r(y_l))$ 和 RLHF 闭式最优解 $\pi^*\propto\pi_{ref}\exp(r/\beta)$ 出发,推出 DPO loss。(引导:反解 $r$;算奖励差;看 $\log Z$ 如何消掉;代进 BT 取负 log。)

**练习 5.** 用 3 句话向一个新手解释:为什么"一组奖励全相等"会让 GRPO 学不到东西。

---
---

<details>
<summary><b>👉 点开看答案(练习 1–5)</b></summary>

### 答案 1

$$J(\theta)=\sum_\tau\pi_\theta(\tau)R(\tau)$$
$$\nabla_\theta J=\sum_\tau\nabla_\theta\pi_\theta(\tau)\,R(\tau)\quad(R\text{ 与 }\theta\text{ 无关})$$

**log-derivative trick(乘一除一):**
$$\nabla_\theta\pi_\theta(\tau)=\pi_\theta(\tau)\frac{\nabla_\theta\pi_\theta(\tau)}{\pi_\theta(\tau)}=\pi_\theta(\tau)\nabla_\theta\log\pi_\theta(\tau)$$

代回,认出期望:
$$\nabla_\theta J=\sum_\tau\pi_\theta(\tau)\nabla_\theta\log\pi_\theta(\tau)R(\tau)=\mathbb{E}_{\tau\sim\pi_\theta}[R(\tau)\nabla_\theta\log\pi_\theta(\tau)]$$

**加 baseline:** 由答案 2,$\mathbb{E}[b\nabla\log\pi]=0$,所以可以自由减去:
$$\nabla_\theta J=\mathbb{E}_{\tau\sim\pi_\theta}[(R(\tau)-b)\nabla_\theta\log\pi_\theta(\tau)]$$
期望不变(无偏),方差因中心化而降。$\blacksquare$

### 答案 2

$b$ 是常数(或只依赖 state):
$$\mathbb{E}_{\tau\sim\pi_\theta}[b\nabla_\theta\log\pi_\theta(\tau)]=b\sum_\tau\pi_\theta(\tau)\nabla_\theta\log\pi_\theta(\tau)$$

用 log-derivative trick 反着用:$\pi_\theta\nabla\log\pi_\theta=\nabla\pi_\theta$:
$$=b\sum_\tau\nabla_\theta\pi_\theta(\tau)=b\,\nabla_\theta\underbrace{\sum_\tau\pi_\theta(\tau)}_{=\,1}=b\,\nabla_\theta(1)=b\cdot 0=0$$

**关键点破:** $\sum_\tau\pi_\theta(\tau)=1$(概率归一,对任何 $\theta$ 恒为常数 1),常数的梯度为 0。所以减 baseline 不引入偏差。$\blacksquare$

(对 group-mean baseline:$b=\mathrm{mean}_k R_k$ 是该 prompt 的组均值,对该 prompt 的样本对称,同样满足归一化论证 → 无偏。)

### 答案 3

reward $\{0.7,\ 0.7,\ 0.66,\ -0.04\}$,$K=4$。

**mean:**
$$\mathrm{mean}=\frac{0.7+0.7+0.66+(-0.04)}{4}=\frac{2.02}{4}=0.505$$

**离差(deviations)$R_i-\mathrm{mean}$:**
$$0.7-0.505=0.195,\quad 0.195,\quad 0.66-0.505=0.155,\quad -0.04-0.505=-0.545$$

**总体方差(除以 $K$):**
$$\mathrm{var}=\frac{0.195^2+0.195^2+0.155^2+(-0.545)^2}{4}=\frac{0.038025+0.038025+0.024025+0.297025}{4}$$
$$=\frac{0.3971}{4}=0.099275$$

**std:**
$$\mathrm{std}=\sqrt{0.099275}\approx 0.31508$$

**advantages $\hat A_i=(R_i-\mathrm{mean})/\mathrm{std}$:**
$$\hat A_1=\frac{0.195}{0.31508}\approx 0.619,\quad \hat A_2\approx 0.619$$
$$\hat A_3=\frac{0.155}{0.31508}\approx 0.492,\quad \hat A_4=\frac{-0.545}{0.31508}\approx -1.730$$

**验算:** 四个 advantage 之和 $\approx 0.619+0.619+0.492-1.730=0.000$ ✓(标准化后组内均值必为 0,这是 advantage 的定义性质 —— 这个自检面试时也该主动做)。

**读法:** 前三条(reward 0.66–0.7)advantage 为正 → 推高;第四条(−0.04)显著为负(−1.73)→ 压低。注意即使 reward 差距不大,标准化后也拉出了清晰的相对信号 —— 这正是组内相对比较的价值。

> **对比 collapse:** 如果这 4 个 reward **全相等**(比如全是 −1.3),则离差全为 0,std = 0,每个 $\hat A_i=0/0$ → 零梯度。这就是答案 5 要讲的机制。

### 答案 4

**第 1 步(反解 $r$):** 从 $\pi^*(y)=\frac{1}{Z}\pi_{ref}(y)\exp(r(y)/\beta)$ 取 log 并解出 $r$:
$$\log\pi^*(y)=\log\pi_{ref}(y)+\frac{r(y)}{\beta}-\log Z\ \Rightarrow\ r(y)=\beta\log\frac{\pi^*(y)}{\pi_{ref}(y)}+\beta\log Z$$
把 $\pi^*$ 当成待学的 $\pi_\theta$。

**第 2 步(奖励差,$\log Z$ 抵消):** $\beta\log Z$ 不依赖 $y$,对 $y_w,y_l$ 相同,相减消掉:
$$r(y_w)-r(y_l)=\beta\log\frac{\pi_\theta(y_w)}{\pi_{ref}(y_w)}-\beta\log\frac{\pi_\theta(y_l)}{\pi_{ref}(y_l)}$$

**第 3 步(代进 BT):** $P(y_w\succ y_l)=\sigma(r(y_w)-r(y_l))$。

**第 4 步(负 log 似然):**
$$\mathcal{L}_{DPO}=-\log\sigma\!\left(\beta\log\frac{\pi_\theta(y_w)}{\pi_{ref}(y_w)}-\beta\log\frac{\pi_\theta(y_l)}{\pi_{ref}(y_l)}\right)$$

**为什么无需 reward model:** reward 被表达成 log 概率比,且归一化常数 $\log Z$ 被相减消掉 —— 整个 loss 只需要 $\pi_\theta$、$\pi_{ref}$、偏好对。$\blacksquare$

### 答案 5

(示例三句,可背)
1. GRPO 学习靠的是"同一道题的一组答案里,谁比组平均好、谁比组平均差"这个**差异**信号。
2. 如果这组答案的分数**全都一样**,组平均就等于每个分数,每条的"比平均好多少"(advantage)都是 0。
3. Advantage 全为 0 就意味着梯度为 0 —— 模型收不到"该往哪调"的信号,哪怕这些答案其实全错、罚分很重,它也学不到任何东西。

(项目落点:这正是我们 0.5B 在 gate seed 上 55% 组 all-violate → gate 动作灭绝的原因。)

</details>

---

*文档基于 `docs/PORTFOLIO_INDEX.md` 与 `docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md` 的真实实验数字撰写。所有推导已逐步核对;凡做简化(per-token vs per-sequence、GAE 概念级)处均已在正文显式标注,面试时应主动交代而非等追问。*
