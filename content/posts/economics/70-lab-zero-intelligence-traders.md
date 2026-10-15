---
title: "实验 70 零智能交易者：价格自己收敛到均衡"
date: 2026-10-08
weight: 70
tags: ["经济学"]
summary: "如果，市场上的 24 个交易者，都是没有脑子的程序，只会在\"不亏本\"的范围里，随机报价，他们，能把资源配置得多好？价格，会不会，自己，找到均衡？这个实验，用纯 Python 和 NumPy，手写一个连续双向拍卖：先是，没有约束的随机交易者（效率，只有 75%），再是，不亏本的随机交易者（效率，约 96%，可是，价格，一直，散得很开），再加上，一点点学习（ZIP：效率，约 99%，价格，3 个周期，就收敛，需求冲击之后，也跟得上），最后，换一个不对称的市场，看，零智能，在哪里，会失灵。第 7 讲留下的问题：市场的好处，有多少，来自结构，有多少，来自，交易者的智能。"
showToc: true
tocOpen: false
---

这是第一个**实验**。前面的讲，是"读"；实验，是"做"：你，把一个模型，**一段一段，亲手搭起来**，再看它，跑出什么。

**怎么用**：代码块，是**接着往下写**的：后面的块，会用到前面块里定义的东西。把它们，**依次，拼成一个文件**（比如，`lab70.py`），用 `python lab70.py` 运行，约 40 秒；也可以，一段一段，在 Python 交互环境里，依次运行。**只需要 Python 3 和 NumPy**。每个块下面的"输出"，是我真实跑出来的（随机数的种子，固定了，所以，你会得到**完全一样**的数字）。

## 一、一个问题

第 7 讲，我们，用一个，很简单的模拟，看到：交易者，没有脑子，只要，不愿意亏本，市场，就能，把资源，配置得相当好；可是，价格，没有，精确地，找到均衡价。当时，留下了一个问题（第 7 讲，7.2 节）："要想让价格收敛得更准，需要让交易者**看到别人的报价并作出调整**。" 这个实验，就是，做这件事。

**先停一下：请先猜一猜。** 一个市场：12 个买家，12 个卖家，每个人，只买（卖）1 件。买家的愿付价，从 200，到 90；卖家的成本，从 50，到 160。所有人，都**不知道**别人的底牌，也**没有**任何策略：只会，在"不亏本"的范围里，**随机**，报价。你猜：

1. 成交几对？理论上，应该是 8 对；
2. 总的剩余，能达到，最大值的百分之几？
3. 成交价，会不会，集中在，均衡价附近？

**先写下你的猜测**，我们，在每一步，回来对照。

## 二、实验的设计

### 2.1 市场，和规则

- **买家**：愿付价（私人价值）：200，190，……，90。**卖家**：成本：50，60，……，160。每个人，每个周期，最多，成交 1 件。
- **竞争均衡**：成交 8 对；均衡价，在 120 到 130 之间（取 p* = 125）；最大总剩余 = 640（第 7 讲、第 12 讲）。
- **连续双向拍卖**（Vernon Smith 1962 年用过的规则；第 7 讲，7.3 节）：每一步，随机，挑一个，还没成交的交易者，让他，报一个价：
  - 新的**买价**，必须，**高于**，当前最高的买价，才算数；新的**卖价**，必须，**低于**，当前最低的卖价；
  - 如果，新的买价，≥ 当前最低的卖价（或者，新的卖价，≤ 当前最高的买价），**成交**，价格 = **先挂着的**那个报价；成交的双方，退出；报价簿，清空；
  - **所有人**，都能，看到，报价和成交。

### 2.2 三种交易者

| 交易者 | 怎么报价 | 会不会亏本 | 会不会学习 |
|------|------|------|------|
| **ZI-U**（零智能，没有约束） | 在 [1, 200] 里，随便抽 | 会 | 不会 |
| **ZI-C**（零智能，有约束） | 买家，在 [1, 愿付价] 里抽；卖家，在 [成本, 200] 里抽 | **不会** | 不会 |
| **ZIP**（零智能 Plus） | 有一个"利润率"，报价 = 愿付价 ×（1 − 利润率），或成本 ×（1 + 利润率）；根据，看到的成交价和报价，**调整**利润率 | **不会** | **会一点** |

（ZI-U 和 ZI-C，来自 Dhananjay Gode 和 Shyam Sunder 1993 年，*Journal of Political Economy*，101 卷 1 期，119–137 页；ZIP，是 Dave Cliff 1997 年，提出的（HP Labs 技术报告 HPL-97-91）。**我这里的 ZIP，是一个简化版**：思想，来自 Cliff，参数的范围，是我自己选的，不是，原版的所有细节。）

### 2.3 我们，怎么衡量

- **配置效率**：实际成交的所有买卖对的"愿付价 − 成本"之和，÷ 最大总剩余（640）。100% = 资源，配置得，最好。
- **Smith 的收敛系数 α**：成交价，对均衡价 p* 的**均方根偏离**，÷ p*，× 100。α 越小，价格，越集中在 p* 附近。（这个指标，由 Vernon Smith 1962 年，引入，用来，衡量，价格，是否，收敛；定义的细节，我是按后来的文献，转述的。）
- **不该成交的**：成交的买卖对里，有买家或卖家，**不是**应该成交的那 8 对里的人。

## 三、第一步：把市场搭起来

```python
import numpy as np

N = 12            # 买家 12 人，卖家 12 人，每人，每个周期，最多买（卖）1 件

def schedule(shift=0):
    """每个买家的愿付价（私人价值），和每个卖家的成本。shift：需求，整体，上移多少。"""
    vals = np.array([210 - 10 * k + shift for k in range(1, N + 1)], float)   # 200, 190, ..., 90
    costs = np.array([40 + 10 * k for k in range(1, N + 1)], float)            # 50, 60, ..., 160
    return vals, costs

def equilibrium(vals, costs):
    """竞争均衡：成交数 q*、均衡价 p*（取价格区间的中点）、最大总剩余。"""
    v, c = np.sort(vals)[::-1], np.sort(costs)           # 愿付价，从高到低；成本，从低到高
    q = int(np.sum(v >= c))                               # 第 k 个买家的愿付价，还不低于第 k 个卖家的成本：这样的 k，有几个
    lo = max(c[q - 1], v[q] if q < len(v) else 0)         # 价格区间的下限、上限
    hi = min(v[q - 1], c[q] if q < len(c) else 1e9)
    return q, (lo + hi) / 2, float(np.sum(v[:q] - c[:q])), (lo, hi)

vals, costs = schedule()
q, p_star, s_max, (lo, hi) = equilibrium(vals, costs)
print("买家的愿付价：", vals.astype(int).tolist())
print("卖家的成本  ：", costs.astype(int).tolist())
print(f"竞争均衡：成交 {q} 对；均衡价格，在 [{lo:.0f}, {hi:.0f}] 之间，取中点 p* = {p_star:.0f}；最大总剩余 = {s_max:.0f}")
print("逐对看：第 k 个买家，和第 k 个卖家")
for k in range(N):
    ok = vals[k] >= costs[k]
    print(f"  k = {k + 1:>2}：愿付价 {vals[k]:>4.0f}，成本 {costs[k]:>4.0f}，剩余 {vals[k] - costs[k]:>+5.0f}  {'← 应该成交' if ok else ''}")
vals2, costs2 = schedule(40)
q2, p2, s2, (lo2, hi2) = equilibrium(vals2, costs2)
print(f"\n需求，整体上移 40 之后：成交 {q2} 对；均衡价在 [{lo2:.0f}, {hi2:.0f}]，p* = {p2:.0f}；最大总剩余 = {s2:.0f}")
```

输出：

```text
买家的愿付价： [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90]
卖家的成本  ： [50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
竞争均衡：成交 8 对；均衡价格，在 [120, 130] 之间，取中点 p* = 125；最大总剩余 = 640
逐对看：第 k 个买家，和第 k 个卖家
  k =  1：愿付价  200，成本   50，剩余  +150  ← 应该成交
  k =  2：愿付价  190，成本   60，剩余  +130  ← 应该成交
  k =  3：愿付价  180，成本   70，剩余  +110  ← 应该成交
  k =  4：愿付价  170，成本   80，剩余   +90  ← 应该成交
  k =  5：愿付价  160，成本   90，剩余   +70  ← 应该成交
  k =  6：愿付价  150，成本  100，剩余   +50  ← 应该成交
  k =  7：愿付价  140，成本  110，剩余   +30  ← 应该成交
  k =  8：愿付价  130，成本  120，剩余   +10  ← 应该成交
  k =  9：愿付价  120，成本  130，剩余   -10  
  k = 10：愿付价  110，成本  140，剩余   -30  
  k = 11：愿付价  100，成本  150，剩余   -50  
  k = 12：愿付价   90，成本  160，剩余   -70  

需求，整体上移 40 之后：成交 10 对；均衡价在 [140, 150]，p* = 145；最大总剩余 = 1000
```

![实验的市场：12 个买家，12 个卖家](/images/economics/70-market.svg)

逐段看：

- 理论预测：**8 对**成交；价格区间 [120, 130]；最大总剩余 **640**（8 对的剩余，150 + 130 + …… + 10）。第 9 对：愿付价 120，成本 130，剩余 −10：成交了，反而亏。
- 需求，整体上移 40 之后（后面，会用）：成交 10 对，p* = 145。

## 四、第二步：双向拍卖的引擎，和零智能交易者

`play_period` 是整个实验的核心：它，实现了，2.1 节的规则。交易者，只需要，会做两件事：**报价**（`quote`），和**观察**（`observe`）。

```python
PMAX = 200.0       # 价格的上限（报价，不会超过它）

class ZIU:
    """零智能、没有约束：报价，在 [1, PMAX] 里，随便抽，不管，会不会亏本。"""
    def __init__(self, rng, is_buyer, limit):
        self.rng, self.buyer, self.limit = rng, is_buyer, limit
    def quote(self):
        return self.rng.uniform(1, PMAX)
    def observe(self, kind, price, active):    # 看到别人的报价、成交：什么也不做
        pass

class ZIC(ZIU):
    """零智能、有约束：买家，只在 [1, 愿付价] 里报价；卖家，只在 [成本, PMAX] 里报价：保证，不亏本。"""
    def quote(self):
        return self.rng.uniform(1, self.limit) if self.buyer else self.rng.uniform(self.limit, PMAX)

def play_period(kind, vals, costs, rng, traders=None, steps=400):
    """一个周期的"连续双向拍卖"。每一步：随机挑一个还没成交的交易者，让他报一个价。
       规则：新的买价，必须，高于，当前最高的买价（才算数）；新的卖价，必须，低于，当前最低的卖价；
             如果，新的买价 ≥ 当前最低的卖价（或者，新的卖价 ≤ 当前最高的买价），就成交，价格 = 先挂着的那个报价。成交之后，双方退出，报价簿清空。"""
    nb, ns = len(vals), len(costs)
    if traders is None:
        traders = {("b", i): kind(rng, True, vals[i]) for i in range(nb)}
        traders.update({("s", j): kind(rng, False, costs[j]) for j in range(ns)})
    for (_, _), t in traders.items():
        t.active = True
    best_bid, best_ask = (0.0, None), (PMAX, None)       # (价格, 谁)
    trades = []                                           # (买家 i, 卖家 j, 成交价)
    for _ in range(steps):
        active = [key for key, t in traders.items() if t.active]
        if not active:
            break
        key = active[rng.integers(len(active))]
        side, idx = key
        q = traders[key].quote()
        event = None
        if side == "b":
            if best_ask[1] is not None and q >= best_ask[0]:           # 成交
                j = best_ask[1]
                trades.append((idx, j, best_ask[0])); traders[key].active = False; traders[("s", j)].active = False
                best_bid, best_ask = (0.0, None), (PMAX, None); event = ("trade", trades[-1][2])
            elif q > best_bid[0]:
                best_bid = (q, idx); event = ("bid", q)
        else:
            if best_bid[1] is not None and q <= best_bid[0]:
                i = best_bid[1]
                trades.append((i, idx, best_bid[0])); traders[key].active = False; traders[("b", i)].active = False
                best_bid, best_ask = (0.0, None), (PMAX, None); event = ("trade", trades[-1][2])
            elif q < best_ask[0]:
                best_ask = (q, idx); event = ("ask", q)
        if event is not None:
            for t in traders.values():
                t.observe(event[0], event[1], t.active)     # 所有人，都能，看到
    return trades

def measure(trades, vals, costs, q_star, p_star, s_max):
    """成交的数量、总剩余占最大值的比例（配置效率）、Smith 的收敛系数 α、不该成交的（边际外）成交数。"""
    prices = np.array([p for _, _, p in trades])
    surplus = sum(vals[i] - costs[j] for i, j, _ in trades)
    alpha = 100 * np.sqrt(np.mean((prices - p_star) ** 2)) / p_star if len(prices) else np.nan
    extra = sum(1 for i, j, _ in trades if vals[i] < costs[j] or i >= q_star or j >= q_star)
    return len(trades), surplus / s_max, alpha, extra

# 先看一个具体的周期：零智能（有约束）的交易者
rng = np.random.default_rng(7)
trades = play_period(ZIC, vals, costs, rng)
n, eff, alpha, extra = measure(trades, vals, costs, q, p_star, s_max)
print(f"一个周期里，ZI-C 的成交，按先后顺序（均衡价 p* = {p_star:.0f}，应该成交 {q} 对）：")
print(f"  {'序号':>4}{'买家愿付价':>10}{'卖家成本':>9}{'成交价':>8}{'这一对的剩余':>12}{'是否应该成交':>12}")
for k, (i, j, p) in enumerate(trades, 1):
    should = (i < q and j < q)
    print(f"  {k:>4}{vals[i]:>10.0f}{costs[j]:>9.0f}{p:>8.1f}{vals[i] - costs[j]:>12.0f}{'是' if should else '不应该':>10}")
print(f"  成交 {n} 对（其中，不该成交的 {extra} 对），总剩余是最大值的 {eff:.1%}；成交价，从 {min(p for _, _, p in trades):.1f} 到 {max(p for _, _, p in trades):.1f}，α = {alpha:.1f}")
```

输出：

```text
一个周期里，ZI-C 的成交，按先后顺序（均衡价 p* = 125，应该成交 8 对）：
    序号     买家愿付价     卖家成本     成交价      这一对的剩余      是否应该成交
     1       200      130   151.0          70       不应该
     2       170       70    98.0         100         是
     3       150      100   100.4          50         是
     4       140       50   118.8          90         是
     5       100       90    96.5          10       不应该
     6       110       60   106.5          50       不应该
     7       190      140   149.1          50       不应该
     8       180       80   143.0         100         是
     9       160      120   146.6          40         是
    10       130      110   114.2          20         是
  成交 10 对（其中，不该成交的 4 对），总剩余是最大值的 90.6%；成交价，从 96.5 到 151.0，α = 17.3
```

逐段看：

- 一个周期里，ZI-C 的 10 笔成交：成交价，从 96.5，到 151.0，**差了 50 多**；其中，4 笔，是"不该成交的"（比如，第 1 笔：愿付价 200 的买家，买了成本 130 的卖家，价格 151：**占了，成本，只有 50~70 的卖家的位置**）。总剩余，是最大值的 **90.6%**。
- 即使，是这样，**没有一个人，是亏本的**：每一笔，"愿付价 − 成本"，都是正的。

## 五、第三步：200 次运行，比较 ZI-U 和 ZI-C

一次运行，说明不了什么。用 200 个不同的随机种子，各跑一次。

```python
# 200 次独立的运行（200 个随机种子），比较：ZI-U（没约束）和 ZI-C（不亏本）
def many(kind, seeds, vals, costs, n_periods=1):
    q_, p_, s_, _ = equilibrium(vals, costs)
    rows, all_prices = [], []
    for sd in seeds:
        rng = np.random.default_rng(1000 + sd)
        trades = play_period(kind, vals, costs, rng)
        rows.append(measure(trades, vals, costs, q_, p_, s_)); all_prices += [p for _, _, p in trades]
    return np.array(rows), np.array(all_prices)

print(f"理论：成交 {q} 对，p* = {p_star:.0f}，最大总剩余 = {s_max:.0f}")
print(f"  {'':<22}{'成交数':>7}{'不该成交的':>10}{'效率 平均':>9}{'效率 最低':>9}{'α 平均':>8}{'价格 平均':>9}{'价格 10%–90%':>16}")
for name, kind in (("ZI-U（没有约束）", ZIU), ("ZI-C（不亏本的约束）", ZIC)):
    R, P = many(kind, range(200), vals, costs)
    lo10, hi90 = np.percentile(P, [10, 90])
    print(f"  {name:<18}{R[:, 0].mean():>7.1f}{R[:, 3].mean():>10.1f}{R[:, 1].mean():>9.1%}{R[:, 1].min():>9.1%}{np.nanmean(R[:, 2]):>8.1f}{P.mean():>9.1f}{f'{lo10:.0f}–{hi90:.0f}':>16}")
print(f"  对照：随便猜一个价（均匀分布在 1 到 {PMAX:.0f} 之间），平均 {(1 + PMAX) / 2:.1f}")
print("  ZI-U 的效率，每次，都一模一样（75.0%）：因为，所有 12 对，最后，都成交了；总剩余 = 所有买家的愿付价之和 − 所有卖家的成本之和 = 480，和谁配对，无关。")
```

输出：

```text
理论：成交 8 对，p* = 125，最大总剩余 = 640
                            成交数     不该成交的    效率 平均    效率 最低    α 平均    价格 平均      价格 10%–90%
  ZI-U（没有约束）           12.0       6.7    75.0%    75.0%    49.5    100.6          23–181
  ZI-C（不亏本的约束）          8.8       1.9    96.2%    87.5%    18.6    121.1          90–152
  对照：随便猜一个价（均匀分布在 1 到 200 之间），平均 100.5
  ZI-U 的效率，每次，都一模一样（75.0%）：因为，所有 12 对，最后，都成交了；总剩余 = 所有买家的愿付价之和 − 所有卖家的成本之和 = 480，和谁配对，无关。
```

逐段看：

- **ZI-U**（没有约束）：12 对，**全部**成交（包括，6.7 对"不该成交的"：愿付价，比成本还低的买卖，也成交了，所以，亏本）；效率，**每次，都是 75.0%**：**不是巧合**：12 对，全都成交，总剩余，就是，所有买家的愿付价之和（1740），减去，所有卖家的成本之和（1260），= 480，480 ÷ 640 = 75%，和**谁**配对，**无关**。成交价，几乎，是在 1 到 200 之间，随便抽：平均 100.6，10%–90% 分位，23 到 181。**α = 49.5**。
- **ZI-C**（不亏本）：成交 8.8 对（理论 8 对），其中，1.9 对，不该成交；**效率，平均 96.2%**（最低，87.5%）。**只是加了"不亏本"这一条约束，效率，就从 75%，到了 96%**。
- **价格呢？** ZI-C 的平均成交价，121.1（p* = 125），差得不远；可是，**散得很开**：10%–90% 分位，90 到 152；**α = 18.6**，也就是说，**一次成交的价格，平均，偏离，均衡价，将近 19%**。
- **回到你的猜测**：（1）成交 8.8 对，接近 8；（2）96%，很高；（3）价格，**平均**，在附近，**每一笔**，不集中。
- Gode 和 Sunder，在 1993 年，报告了类似的现象：据一份，转载的原始结果表，ZI-C，在 5 个市场里，效率，在 97.1% 到 99.9%，ZI-U 在 48.8% 到 90.0%，人类的，在 90.2% 到 100%。我的数字（96%），略低，是**正常的**：市场的设计（每人 1 件、12 对）、成交的规则，不完全一样。

## 六、第四步：给他们，加一点点学习

ZIP 交易者，有一个**利润率**。每次，看到市场上的报价或成交，他，就把自己的报价，朝着"目标价"，挪一点：

- 如果，一笔成交的价格，**比我的卖价，高**（我本可以，要得更高）：卖家，提高利润率；如果，价格，**比我的卖价低**，而我，还没成交：我，降低要价，以免，卖不出去；买家，对称；
- "挪一点"，用的是，Widrow–Hoff 规则（每次，往目标，走 β 的比例），再加一点"动量"；
- **利润率，永远 ≥ 0**：永远，不亏本。

```python
class ZIP(ZIU):
    """ZIP（Zero-Intelligence Plus）：在 ZI 的基础上，加了一点点"学习"。
       每个人，有一个"利润率" mu：买家，报价 = 愿付价 × (1 − mu)；卖家，报价 = 成本 × (1 + mu)。mu ≥ 0：永远，不亏本。
       每次，看到市场上，有人报价、有人成交，就把自己的报价，往"目标价"那边，挪一点（Widrow–Hoff 学习规则，加上一点"动量"）。"""
    def __init__(self, rng, is_buyer, limit):
        super().__init__(rng, is_buyer, limit)
        self.beta = rng.uniform(0.1, 0.5)          # 学习速度
        self.gamma = rng.uniform(0.0, 0.1)         # 动量
        self.mu = rng.uniform(0.05, 0.35)          # 初始的利润率
        self.mom = 0.0
    def price(self):
        return self.limit * (1 - self.mu) if self.buyer else self.limit * (1 + self.mu)
    quote = price
    def _target(self, ref, price_up):
        # 目标价：想让自己的报价"涨"（price_up = True），目标，就在参考价的上方一点；想让它"降"，就在参考价的下方一点。随机抖动一点。
        R = self.rng.uniform(1.0, 1.05) if price_up else self.rng.uniform(0.95, 1.0)
        A = self.rng.uniform(0, 0.05) * (1 if price_up else -1)
        return R * ref + A
    def _move(self, target):
        delta = self.beta * (target - self.price())
        self.mom = self.gamma * self.mom + (1 - self.gamma) * delta
        new = self.price() + self.mom
        new = min(new, self.limit) if self.buyer else max(new, self.limit)      # 不亏本
        self.mu = max((1 - new / self.limit) if self.buyer else (new / self.limit - 1), 0.0)
    def observe(self, kind, price, active):
        p = self.price()
        if self.buyer:
            if kind == "trade":
                if p >= price: self._move(self._target(price, False))          # 我本可以，出得更低：降低报价
                elif active:   self._move(self._target(price, True))           # 价格，比我的报价高：我得，出高一点
            elif kind == "ask" and active and p >= price: self._move(self._target(price, False))
            elif kind == "bid" and active and p <= price: self._move(self._target(price, True))
        else:
            if kind == "trade":
                if p <= price: self._move(self._target(price, True))           # 我本可以，要得更高
                elif active:   self._move(self._target(price, False))          # 价格，比我的要价低：我得，要低一点
            elif kind == "bid" and active and p <= price: self._move(self._target(price, True))
            elif kind == "ask" and active and p >= price: self._move(self._target(price, False))

def run_periods(kind, seed, n_periods, shift_fn, steps=400):
    """同一批交易者，连续，交易 n_periods 个周期；每个周期，愿付价和成本，可以变（shift_fn(t) 给出需求的上移量）。"""
    rng = np.random.default_rng(seed)
    v0, c0 = schedule(0)
    traders = {("b", i): kind(rng, True, v0[i]) for i in range(N)}
    traders.update({("s", j): kind(rng, False, c0[j]) for j in range(N)})
    out = []
    for t in range(1, n_periods + 1):
        v, c = schedule(shift_fn(t))
        for i in range(N): traders[("b", i)].limit = v[i]
        for j in range(N): traders[("s", j)].limit = c[j]
        q_, p_, s_, _ = equilibrium(v, c)
        trades = play_period(kind, v, c, rng, traders, steps)
        out.append(measure(trades, v, c, q_, p_, s_) + (np.mean([p for _, _, p in trades]), p_))
    return out            # 每个周期：(成交数, 效率, α, 不该成交的, 平均成交价, p*)

# 一、ZIP，连续，交易 20 个周期（需求，不变）。200 个种子。对照：ZI-C
S = 200
print("需求不变，连续 20 个周期：α（价格，离均衡价的偏离，%），越小，越收敛")
print(f"  {'':<8}" + "".join(f"{'周期 ' + str(t):>9}" for t in (1, 2, 3, 5, 10, 20)))
res = {}
for name, kind in (("ZI-C", ZIC), ("ZIP", ZIP)):
    R = np.array([run_periods(kind, 5000 + s, 20, lambda t: 0) for s in range(S)])      # S × 20 × 6
    res[name] = R
    print(f"  {name:<6}α" + "".join(f"{np.nanmean(R[:, t - 1, 2]):>9.1f}" for t in (1, 2, 3, 5, 10, 20)))
for name in ("ZI-C", "ZIP"):
    R = res[name]
    print(f"  {name:<6}效率" + "".join(f"{np.mean(R[:, t - 1, 1]):>9.1%}" for t in (1, 2, 3, 5, 10, 20)))
for name in ("ZI-C", "ZIP"):
    R = res[name]
    print(f"  {name:<4}平均价格" + "".join(f"{np.nanmean(R[:, t - 1, 4]):>9.1f}" for t in (1, 2, 3, 5, 10, 20)))
print(f"  （均衡价 p* = {p_star:.0f}；成交数：ZI-C {res['ZI-C'][:, 9, 0].mean():.1f}，ZIP {res['ZIP'][:, 9, 0].mean():.1f}，理论 {q}）")
```

输出：

```text
需求不变，连续 20 个周期：α（价格，离均衡价的偏离，%），越小，越收敛
               周期 1     周期 2     周期 3     周期 5    周期 10    周期 20
  ZI-C  α     19.5     18.7     18.9     19.1     18.7     18.6
  ZIP   α     13.5      5.1      3.2      2.7      2.5      2.6
  ZI-C  效率    95.6%    95.9%    95.8%    95.9%    96.0%    95.6%
  ZIP   效率    96.7%    98.5%    98.9%    99.2%    99.4%    99.4%
  ZI-C平均价格    120.4    121.2    121.5    121.2    121.5    121.4
  ZIP 平均价格    120.7    123.7    124.2    125.0    124.9    125.2
  （均衡价 p* = 125；成交数：ZI-C 8.8，ZIP 8.3，理论 8）
```

![一个周期里的成交价：ZI-C，上蹿下跳；ZIP，贴着均衡价](/images/economics/70-prices.svg)

逐段看：

- **α**：ZI-C，一直，在 19 左右，**不会变**（它，没有，在学）；ZIP：第 1 个周期，13.5，第 2 个周期，5.1，第 3 个周期，3.2，到第 5 个周期，**2.7**，然后，稳定在 2.5 左右：**价格，3 个周期，就收敛了**。
- **效率**：ZIP，96.7%（第 1 个周期），到 99.4%（第 20 个周期）；ZI-C，一直，约 96%。
- **平均价格**：ZIP，从 120.7，到 125.2（p* = 125）；ZI-C，一直，121 左右，**偏低 3% 左右**（原因，下一节）。
- **成交数**：ZIP，8.3 对，更接近理论的 8 对。
- 图里：同一个市场，ZI-C，一个周期里的成交价，从 78，到 164，上蹿下跳；ZIP，在学了 20 个周期之后，8 笔成交，**都在，123 到 126 之间**。

## 七、第五步：需求，突然变了

真实的市场，不是，一成不变的。第 31 个周期，买家的愿付价，**整体，上移 40**（比如，一个需求冲击）。**均衡价，从 125，变成 145；成交，从 8 对，变成 10 对**。交易者，不知道，这件事。看，价格，能不能，跟上。

```python
# 第 31 个周期，需求，整体，上移 40：买家的愿付价，都高了 40（比如，一个需求冲击）。看，价格，能不能，跟上。
shock = lambda t: 40 if t >= 31 else 0
q2, p2 = equilibrium(*schedule(40))[:2]
print(f"第 31 个周期起：需求上移 40；新的均衡：成交 {q2} 对，p* = {p2:.0f}（原来 {q} 对，p* = {p_star:.0f}）")
S = 200
res2 = {}
for name, kind in (("ZI-C", ZIC), ("ZIP", ZIP)):
    res2[name] = np.array([run_periods(kind, 9000 + s, 60, shock) for s in range(S)])
periods = (29, 30, 31, 32, 33, 34, 35, 40, 60)
print(f"  {'':<10}" + "".join(f"{'周期 ' + str(t):>9}" for t in periods))
print(f"  {'p*':<10}" + "".join(f"{res2['ZIP'][0, t - 1, 5]:>9.0f}" for t in periods))
for name in ("ZI-C", "ZIP"):
    print(f"  {name + ' 平均价':<8}" + "".join(f"{np.nanmean(res2[name][:, t - 1, 4]):>9.1f}" for t in periods))
for name in ("ZI-C", "ZIP"):
    print(f"  {name + ' α':<8}" + "".join(f"{np.nanmean(res2[name][:, t - 1, 2]):>9.1f}" for t in periods))
for name in ("ZI-C", "ZIP"):
    print(f"  {name + ' 效率':<7}" + "".join(f"{np.mean(res2[name][:, t - 1, 1]):>9.1%}" for t in periods))
# 冲击之后，α 要几个周期，才回到冲击之前（第 21–30 个周期的平均）的 1.1 倍以内？（只有 ZIP，有"回到"可言：ZI-C 的 α，一直，很大；它的问题，在价格的偏差。）
pre = np.nanmean(res2["ZIP"][:, 20:30, 2])
first = next((t for t in range(31, 61) if np.nanmean(res2["ZIP"][:, t - 1, 2]) <= 1.1 * pre), None)
print(f"  ZIP：冲击之前，α = {pre:.1f}；冲击之后，α 第一次，回到 1.1 倍以内：第 {first} 个周期（冲击之后的第 {first - 30} 个周期）")
for name in ("ZI-C", "ZIP"):
    bias = [(np.nanmean(res2[name][:, t - 1, 4]) - p2) / p2 for t in range(41, 61)]
    print(f"  {name}：第 41–60 个周期，平均成交价，比 p* 平均，{np.mean(bias):+.1%}")
```

输出：

```text
第 31 个周期起：需求上移 40；新的均衡：成交 10 对，p* = 145（原来 8 对，p* = 125）
                周期 29    周期 30    周期 31    周期 32    周期 33    周期 34    周期 35    周期 40    周期 60
  p*              125      125      145      145      145      145      145      145      145
  ZI-C 平均价    122.0    121.4    136.8    136.9    137.0    136.2    136.8    136.6    136.8
  ZIP 平均价     125.0    125.1    142.4    143.8    144.5    144.7    144.8    145.4    144.9
  ZI-C α       19.2     19.0     20.7     21.2     21.4     21.4     20.9     20.8     20.6
  ZIP α         2.7      2.5      6.2      3.4      2.8      2.6      2.5      2.5      2.5
  ZI-C 效率    95.7%    96.2%    98.1%    98.0%    98.1%    97.9%    97.9%    97.9%    98.0%
  ZIP 效率     99.4%    99.4%    98.9%    99.3%    99.4%    99.3%    99.5%    99.5%    99.6%
  ZIP：冲击之前，α = 2.5；冲击之后，α 第一次，回到 1.1 倍以内：第 33 个周期（冲击之后的第 3 个周期）
  ZI-C：第 41–60 个周期，平均成交价，比 p* 平均，-5.7%
  ZIP：第 41–60 个周期，平均成交价，比 p* 平均，+0.0%
```

![价格，和 α，60 个周期；需求在第 31 个周期，上移 40](/images/economics/70-converge.svg)

逐段看：

- **ZIP**：冲击的当期，平均成交价，从 125，到 142.4；第 32、33、34 个周期，是 143.8、144.5、144.7；**到第 35 个周期，144.8**，几乎，回到 p* = 145。**α，在冲击的当期，跳到 6.2，到第 33 个周期，就回到了 2.8**（冲击之前的 2.5 的 1.1 倍以内）。
- **ZI-C**：平均成交价，从 121，到 136.8：它，**也，往上走了**（因为，买家的愿付价，上限，上移了，报价的范围，也跟着移了），可是，**一直，比 p* 低约 5.7%**；α，从 19，到 21，没有，变小。
- **效率**：两者，都在 98% 以上；ZIP，在 99% 以上。
- **提醒**：ZIP 的交易者，在第 31 个周期，知道，自己的"愿付价"，变了（这是，他们的私人信息），所以，报价，也会，**立刻**，跟着，移动一部分；**市场价格**，还是，要靠，**学习**，才能，对准新的均衡价。

## 八、第六步：零智能，在哪里，会失灵

Gode 和 Sunder 的结果，发表之后，Dave Cliff 和 Janet Bruten（1997 年，HP Labs 技术报告 HPL-97-141，《零还不够：连续双向拍卖市场里，智能的下限》）提出了一个批评：**当市场的供给和需求，是不对称的**，ZI 交易者的平均成交价，**会明显偏离**理论的均衡价；他们认为，Gode 和 Sunder 的结果，部分，是他们选择的实验设计，造成的。他们引入 ZIP，作为，"稍微多一点点智能"。

我们，来做一个，**需求很平、供给很陡**的市场：买家的愿付价，都在 138–160 之间；卖家的成本，从 40，一路，到 172。

```python
# 换一个市场：需求很"平"，供给很"陡"（买家的愿付价，都在 140–160 之间；卖家的成本，从 40 一直，到 172）
def schedule_asym():
    vals = np.array([160 - 2 * k for k in range(N)], float)           # 160, 158, ..., 138（平的需求）
    costs = np.array([40 + 12 * k for k in range(N)], float)           # 40, 52, ..., 172（陡的供给）
    return vals, costs
va, ca = schedule_asym()
qa, pa, sa, (loa, hia) = equilibrium(va, ca)
print(f"不对称的市场：买家 {va[0]:.0f}→{va[-1]:.0f}；卖家 {ca[0]:.0f}→{ca[-1]:.0f}；成交 {qa} 对，p* 在 [{loa:.0f}, {hia:.0f}]，取 {pa:.1f}；最大剩余 {sa:.0f}")
def run_periods_asym(kind, seed, n_periods):
    rng = np.random.default_rng(seed)
    traders = {("b", i): kind(rng, True, va[i]) for i in range(N)}
    traders.update({("s", j): kind(rng, False, ca[j]) for j in range(N)})
    out = []
    for t in range(n_periods):
        trades = play_period(kind, va, ca, rng, traders)
        prices = [p for _, _, p in trades]
        n_, eff_, al_, ex_ = measure(trades, va, ca, qa, pa, sa)
        out.append((n_, eff_, al_, np.mean(prices) if prices else np.nan))
    return out
print(f"  {'':<8}{'成交数':>7}{'效率':>8}{'α':>7}{'平均价':>8}{'平均价 − p*':>12}")
for name, kind in (("ZI-C", ZIC), ("ZIP", ZIP)):
    R = np.array([run_periods_asym(kind, 7000 + s, 20) for s in range(200)])
    last = R[:, 10:, :]                                    # 后 10 个周期
    print(f"  {name:<6}{last[:, :, 0].mean():>7.1f}{last[:, :, 1].mean():>8.1%}{np.nanmean(last[:, :, 2]):>7.1f}{np.nanmean(last[:, :, 3]):>8.1f}{np.nanmean(last[:, :, 3]) - pa:>+12.1f}")
```

输出：

```text
不对称的市场：买家 160→138；卖家 40→172；成交 9 对，p* 在 [142, 144]，取 143.0；最大剩余 576
              成交数      效率      α     平均价    平均价 − p*
  ZI-C      9.5   97.7%   18.8   125.8       -17.2
  ZIP       9.4   98.9%    1.8   144.0        +1.0
```

![不对称的市场：ZI-C 的平均成交价，偏离均衡价；ZIP，贴着](/images/economics/70-asym.svg)

逐段看：

- 这个市场里：成交 9 对；均衡价，在 [142, 144]；**p* = 143**。
- **ZI-C**：效率，97.7%（依然，很高！）；可是，平均成交价，**125.8，比 p* 低 17.2**：**偏差，比对称市场，大得多**；α，18.8。
- **ZIP**：效率，98.9%；平均成交价，**144.0，只比 p* 高 1.0**；α，**1.8**。
- **为什么？** 一个直觉（我没有，严格证明）：ZI-C 的报价，是在"愿付价以下"、"成本以上"的**整个区间里，均匀地**抽。一个愿付价 150 的买家，报价，平均，只有 75 左右，离 p* = 143 很远；而卖家，在 [成本, 200] 里抽，成本很低的卖家，报价，也可以很低。成交价，被，**报价的"范围"**，决定，而不是，被，"均衡"，决定。**配置的效率**（谁，成交了），对这个，不敏感；**价格**，很敏感。
- 所以，**零智能的"配置效率"，是稳健的；"价格"，不是**。

## 九、这个实验，说明了什么，没说明什么

**说明了**：

1. **配置效率，主要，来自，市场的结构，加上"不亏本"**：ZI-U → ZI-C，效率，从 75% 到 96%，**只加了一条约束**。没有任何一个交易者，需要，聪明（第 7 讲，7.2 节）。
2. **价格，要精确地，找到均衡价，需要"学习"**：ZIP，只多了，一点点学习（只看，最近的成交价和报价），α，就从 19，到 2.5，需求冲击之后，也，3 个周期，跟上。（和第 7 讲、第 12 讲：价格，传递信息；价格，是一种，被"交易"，不断，修正的东西。）
3. **零智能，也有"失灵"的地方**：对称市场里，效率，很高；不对称市场里，**价格**，偏离很大。

**没有说明**：

- **真实的人，是不是**零智能：不是；Vernon Smith 的，真人实验（1962 年）里，人类，收敛得，更快、更准（第 7 讲，7.3 节）；
- **效率，是不是，被"不亏本"约束，"偷偷地"带进来的**：有批评，认为，"不亏本"这条约束，已经，隐含了，**个体的理性**，不完全是，市场的结构（第 7 讲，7.3 节，后续文献）。所以，更稳妥的说法是：**结构，加上，最低限度的理性，就能，走很远**；
- **真实的市场**：有成百上千的交易者，多件商品，有交易成本、有信息的不对称（第 20 讲），有，做市商、策略性的报价（第 18 讲）。

**和后面的联系**：

- 第 12 讲，完全竞争：零利润；价格，由，竞争，压到，成本；这里，ZIP 的价格，贴着 p*；
- 第 38 讲，有效市场：价格，反映，信息；这里，价格，靠，"看别人的报价"，学会；**但，ZIP，是，学会，一个，不变的 p***；p* 变了，要几个周期，才跟上，这也是，一个，"价格，不会，瞬间，反映，所有信息"的小例子。

## 十、练习

**1.** 把 `PMAX`（报价的上限）从 200，改成 300，重新运行第三步（比较 ZI-U 和 ZI-C）。ZI-U 的平均成交价，会是多少？ZI-C 的效率和平均成交价，会怎么变？

> 提示：ZI-U 的报价，在 [1, 300] 上，均匀抽，平均 = (1 + 300) ÷ 2 = **150.5**（运行结果：150.6）。ZI-C：效率，96.5%（几乎不变），平均成交价，**127.4**（原来是 121.1）：卖家的报价上限，变高了，价格，被"拉"高了一点：**价格，对"报价范围"，是敏感的**；效率，不是。

**2.** 为什么，ZI-U 的效率，每次，都是 75.0%？如果，市场，改成，需求整体上移 40（第 31 个周期之后的市场），ZI-U 的效率，是多少？先手算，再运行。

> 提示：12 对，全都成交，总剩余 = 所有买家的愿付价之和 − 所有卖家的成本之和。原来：1740 − 1260 = 480，480 ÷ 640 = **75%**。需求上移 40：愿付价之和 = 1740 + 12 × 40 = 2220；2220 − 1260 = 960；最大总剩余 = 1000；960 ÷ 1000 = **96%**。

**3.** 把 ZIP 的学习速度 β，**固定**为 0.1（慢），和 0.5（快），各跑 100 个种子、10 个周期。哪个，收敛得更快？哪个，最后，更稳？

> 提示：（运行结果）β = 0.1：α，在第 1、2、3、5、10 个周期，是 14.9、7.7、5.2、3.3、**2.1**；β = 0.5：13.6、3.8、3.1、3.4、**3.6**。**学得快的，早期，收敛得快，可是，最后，更"抖"（α，停在 3.6）；学得慢的，慢，但，最后，更准（2.1）**。这是学习里，一个，常见的权衡：**速度，和噪声**（第 1 讲：权衡）。

**4.** 把不对称的市场，**反过来**：需求很陡（买家的愿付价，200，188，176，……），供给很平（卖家的成本，100，102，104，……）。ZI-C 的平均成交价，会，高于，还是低于，均衡价？

> 提示：（运行结果）均衡：成交 8 对，p* 在 [114, 116]，取 115；ZI-C，平均成交价，比 p* **高 7.6**：偏差的**符号，翻转了**（这次，是供给，更平）：**ZI-C 的价格偏差，来自，供给和需求，形状的不对称**；ZIP，会，学掉，这个偏差（你，可以，自己，验证）。

**5.** （开放题）这个实验，把"市场的好处"，分成了，**结构**、**最低限度的理性**、**学习**三个层次。如果，你要，**设计**一个，新的市场（比如，一个，碳排放的交易市场，第 23 讲），这三个层次，各，对应，设计里的什么？哪一部分，是，**事实**问题（比如，"这个规则，会不会，让价格收敛"），哪一部分，是**价值判断**（比如，"我们，要效率，还是，要，公平"）？

> 提示：结构 = 交易规则（谁，可以，报价，信息，多公开，怎么成交）；最低限度的理性 = 参与者，不会，做明显亏本的交易（比如，需要，保证金、信息披露）；学习 = 参与者，能看到，历史的成交价（价格，要透明）。事实：这些规则，会让配置效率、价格的收敛，变成多少，可以，用，这样的模拟（和真实的实验）检验；价值判断：效率，对谁，有利（第 23 讲，初始的配额，怎么分），**是谁，得到了，效率，带来的好处**。

## 十一、局限

- **ZIP，是简化版**：参数的范围，是我选的；结果的数字，对这些选择，是敏感的；**定性的结论**（学习，让价格，收敛；ZI-C，在不对称的市场，偏差大），比，数字，稳健；
- **每人，只有 1 件**；真实的双向拍卖实验，每人，常有多件，有"边际单位"的次序；
- **成交的规则**（先挂着的报价的价格；成交后，清空报价簿），是 Gode 和 Sunder 的版本之一；别的规则，会改变，价格的分布；
- **随机性**：每个数字，是 200 次运行的平均；**不同的种子，会，得到，略有差别的数字**；
- **没有，交易成本、没有，策略**。

## 参考

- Smith, V. L. (1962). An Experimental Study of Competitive Market Behavior. *Journal of Political Economy*, 70(2), 111–137.
- Gode, D. K., & Sunder, S. (1993). Allocative Efficiency of Markets with Zero-Intelligence Traders: Market as a Partial Substitute for Individual Rationality. *Journal of Political Economy*, 101(1), 119–137.
- Cliff, D. (1997). Minimal-Intelligence Agents for Bargaining Behaviors in Market-Based Environments. Hewlett-Packard Laboratories Technical Report HPL-97-91.（据引用；没有读到全文，对 ZIP 的描述，来自我对它的理解，细节，请读原文）
- Cliff, D., & Bruten, J. (1997). Zero Is Not Enough: On the Lower Limit of Agent Intelligence for Continuous Double Auction Markets. Hewlett-Packard Laboratories Technical Report HPL-97-141.
- Gjerstad, S., & Dickhaut, J. (1998). Price Formation in Double Auctions. *Games and Economic Behavior*, 22(1), 1–29.（另一类、基于"信念"的、会学习的交易者；本实验没有实现）
