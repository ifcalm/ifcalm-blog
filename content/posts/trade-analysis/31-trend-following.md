---
title: "第 31 篇：趋势跟随与突破"
date: 2026-09-17
weight: 31
tags: ["交易技术分析"]
draft: false
summary: "2022 年 9 月到 2023 年 10 月，BTC 一共突破了十次 20 日通道，七次是假的。十笔加起来只有 +4.36R，而且其中 +7.67R 全来自一笔——把它拿掉，另外九笔合计 −3.31R。现在第十一个信号来了，买不买？这一篇讲趋势跟随：唐奇安通道、海龟法则、2N 止损、金字塔加仓，以及它为什么长成这个形状——**胜率 32.9%、盈亏比 10.06、中位数一笔是 −1R**，拿掉最赚的 15% 的交易，九年收益归零。最后用第六部分四篇的全套方法检验一次：**把趋势拆掉之后，100 条假数据没有一条比真实的好。**"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **本篇位置** | 第七部分「策略原型」第一篇。前面六部分在造工具和检验工具，从这一篇开始讲**被检验的东西** |
| **用到的数据** | BTC 现货日线、SPY、AAPL（全部沿用前面几篇，不需要新下载） |
| **动手** | 新模块 `talab.trend`：`donchian`、`breakouts`、`follow_through`、`TurtlePlan` + `turtle`（含 2N 止损、按 N 定仓位、金字塔加仓、多空）、`r_profile`、`contribution`、`convexity`，附 14 个测试 |
| **读完你能** | 完整实现一套 1983 年的海龟系统，并说清它为什么在七成信号都是假的情况下还能赚钱 |

---

## 一、先做一个决定

规则只有一条：**价格碰到 20 日通道的上轨就买；跌破 10 日通道的下轨就走。**进场价往下 2 个 ATR 放一个止损。

下面是 BTC 从 2022 年 9 月到 2023 年 10 月的全部十次信号：

```text
       进场日  第一个单位的价        出场日       出场价   原因      R  根数
2022-09-12 21900.00 2022-09-13 20046.573   止损 -1.000   1
2022-09-13 22488.00 2022-09-14 20173.620   止损 -1.247   1
2022-10-26 20456.60 2022-11-08 19089.497   止损 -1.000  13
2022-12-05 17324.00 2022-12-16 16678.830 通道出场 -0.501  11
2023-01-08 17061.27 2023-02-09 22500.000 通道出场  7.671  32
2023-02-15 24255.00 2023-02-24 22881.787   止损 -1.000   9
2023-03-14 24599.59 2023-04-20 28170.000 通道出场  1.808  37
2023-05-29 28331.42 2023-06-02 26548.976   止损 -1.000   4
2023-06-20 27835.51 2023-07-17 29701.020 通道出场  1.058  27
2023-10-01 27483.57 2023-10-11 26954.090 通道出场 -0.425  10

2022-09-12 到 2023-10-11，十三个月，十次突破：3 次走出去了、7 次是假的
合计 +4.36R —— 赚的三笔 +10.54R，亏的七笔 -6.17R
而这 +4.36R 里有 +7.67R 来自 2023-01-08 那一笔；把它拿掉，另外九笔合计 -3.31R

现在是 2023-10-16，BTC 又一次碰到 20 日通道上轨 28,580.00。买不买？
```

![决策点](/images/trade-analysis/31/decision.png)

**十三个月，十次突破，七次是假的。**十笔加起来 +4.36R——而这 +4.36R 里有 +7.67R 来自 2023 年 1 月那一笔。**把那一笔拿掉，另外九笔合计 −3.31R。**

现在是 2023-10-16，BTC 又一次碰到 20 日通道上轨 28,580。

买不买？

---

## 二、打个比方：早期投资

**趋势跟随的收益结构，和一支早期投资基金一模一样。**

| 早期投资 | 趋势跟随 |
|---|---|
| 投 30 家，20 家会死 | 十次突破，七次是假的 |
| 死掉的那家，最多亏掉投进去的钱 | 2N 止损：最多亏 1R |
| 一家上市，把整只基金赚回来 | 一笔 +10R，把前面十次的亏损全填上 |
| **不知道哪一家会成，所以每一家都要投** | 不知道哪次突破是真的，所以每次都要进 |
| 跑得好的那家追加投资 | **金字塔加仓**：顺着走就再加一个单位 |
| 不会因为「已经涨了三倍」就卖掉 | 不设固定止盈（第 23 篇已经量过） |
| 基金的全部收益集中在极少数几笔上 | 拿掉最赚的 15% 的交易，九年收益归零 |

这个比方里有一件事特别关键，它也是这一篇里最难接受的一条：

> **绝大多数交易都是亏的，而且你没法提前知道哪一笔不是。**

一支基金如果只投「看起来最稳的那五家」，它的收益不会是原来的六分之一，**而是零**——因为那五家里很可能一家都不是最后那个赢家。趋势跟随也一样：**放过任何一次信号，都是在赌你能分辨真假，而这一篇后面会证明你分辨不了。**

---

## 三、唐奇安通道：一条画在前面的线

唐奇安通道就是两条线：**过去 n 根的最高价**和**过去 n 根的最低价**。

```python
def donchian(high: pd.Series, low: pd.Series, n: int = 20) -> pd.DataFrame:
    """唐奇安通道：过去 n 根的最高价、最低价，以及两者的中点。

    ⚠️ 两条轨都 `shift(1)`：**第 i 根上用的是第 i−1 根为止的最高价**。
    不推迟的话，「创 20 日新高」这个条件会永远成立（今天的最高价当然是包含今天的最高价之一）。
    """
    return pd.DataFrame({
        "上轨": high.rolling(n).max().shift(1),
        "下轨": low.rolling(n).min().shift(1),
    }).assign(中轨=lambda t: (t["上轨"] + t["下轨"]) / 2)
```

⚠️ 两条轨都要 `shift(1)`。不推迟的话，「创 n 日新高」这个条件**永远成立**——今天的最高价当然是包含今天在内的最高价之一。测试里专门钉了这一条：忘了 `shift` 的写法在一路上涨的数据上一个信号都给不出来。

### 3.1 假突破到底有多假

先不考虑止损和出场，只问一件最朴素的事：**价格突破通道之后，二十根 K 线之后还在突破价上方吗？**

```python
rows = []
for name, (frame, periods) in MARKETS.items():
    for n in (20, 55):
        table = T.breakouts(frame, n, horizon=20)
        stats = T.follow_through(table)
        rows.append({"标的": name, "通道": f"{n} 日", "突破次数": int(stats["突破次数"]),
                     "假突破比例": stats["假突破比例"], "真的那些平均涨": stats["真的那些平均涨"],
                     "假的那些平均跌": stats["假的那些平均跌"], "全部平均": stats["全部平均"],
                     "最大顺势中位": stats["最大顺势中位"], "最大逆势中位": stats["最大逆势中位"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的   通道  突破次数  假突破比例  真的那些平均涨  假的那些平均跌   全部平均  最大顺势中位  最大逆势中位
 SPY 20 日   260 0.2885   0.0267  -0.0324 0.0097  0.0252 -0.0167
 SPY 55 日   205 0.3220   0.0254  -0.0317 0.0070  0.0231 -0.0161
AAPL 20 日   206 0.3107   0.0729  -0.0554 0.0343  0.0597 -0.0240
AAPL 55 日   149 0.3289   0.0721  -0.0599 0.0287  0.0514 -0.0243
 BTC 20 日   218 0.4174   0.1765  -0.0904 0.0672  0.0794 -0.0680
 BTC 55 日   144 0.3264   0.1794  -0.0897 0.0955  0.0938 -0.0578
```

![假突破](/images/trade-analysis/31/breakout.png)

这已经是**最宽松**的口径了——只要二十根之后还比突破价高一分钱就算「真的」。结果：

| 标的 | 20 日通道突破次数 | 假突破比例 | 真的那些平均涨 | 假的那些平均跌 |
|---|---|---|---|---|
| SPY | 260 | 28.85% | +2.67% | −3.24% |
| AAPL | 206 | 31.07% | +7.29% | −5.54% |
| BTC | 218 | **41.74%** | **+17.65%** | −9.04% |

⚠️ 注意这里的 29%–42% 和开头那句「十次里七次是假的」**不是同一个数**。差别在于：上面只问「二十根之后在哪」，而开头那十次是**真的按海龟规则交易**的结果——中间有 2N 止损，很多最终走出去的突破在半路就被止损打掉了。**止损把「假突破」的比例从四成推到了近七成，同时把每次假突破的代价从「跌 9%」压到了「亏 1R」。**这是同一枚硬币的两面，后面第八节会算这笔账。

真正值得看的是右边那一列：**BTC 上真的那些平均涨 17.65%，假的那些平均跌 9.04%。**赢的时候赢得比输的时候多——趋势跟随全部的生计就在这个不对称上。

---

## 四、揭晓：第十一次

```text
2023-10-16 买在 28,580.00，2023-12-29 按 通道出场 卖在 41,637.60，拿了 74 根 K 线
R = +10.66，10 万美元的账户上赚了 17,392
这一笔在全部 67 笔里排第 2
同期 BTC：28,501 → 42,067
如果只有这一笔没做：九年合计从 76.2R 变成 65.6R
```

![揭晓](/images/trade-analysis/31/reveal.png)

**+10.66R。**这一笔在九年 67 笔里排第 2。十三个月的忍耐，一次性还清。

左边那张图是刚才那笔：一个单位，进场 28,580，74 根 K 线之后按 10 日通道下轨出在 41,637。右边是**同一笔**，按海龟原版的金字塔规则加到四个单位——**R 从 +10.66 变成 +36.43**。加仓怎么加、为什么不是无脑放大风险，第九节专门讲。

而最后那一行才是这一篇真正的主题：

> 如果只有这一笔没做，九年合计从 76.2R 变成 65.6R。

一笔交易，九年收益的 **14%**。而在做出这个决定的那一刻，你能掌握的全部信息就是：**过去十次里有七次是假的。**

---

## 五、海龟法则

1983 年，Richard Dennis 和 Bill Eckhardt 打了个赌：交易能不能教会。他们登广告招人、培训两周，把一套写死的规则交出去。这就是海龟法则，而它的核心可以完整地装进一个 dataclass：

```python
@dataclass
class TurtlePlan:
    """海龟交易法则，1983 年那一版的核心设定。

    原版有两套系统：系统一是 20 日突破进、10 日突破出，系统二是 55 日进、20 日出。
    这里用同一个 dataclass 表示，改两个数字就换系统。
    """
    entry: int = 20                        # 进场：突破几日通道
    exit: int = 10                         # 出场：反向几日通道
    atr_period: int = 20                   # N（原版就叫 N，其实是 20 日 ATR）
    stop_atr: float = 2.0                  # 止损放在进场价外几个 N
    risk: float = 0.01                     # 一个「单位」冒账户的百分之几
    max_units: int = 4                     # 最多加到几个单位
    add_atr: float = 0.5                   # 每走几个 N 加一个单位
    side: str = "long"                     # long / short / both
    fill: str = "touch"                    # touch：碰到通道就成交；next_open：等下一根开盘
    fee_rate: float = 0.0                  # 单边费率（第 28 篇）

    def __post_init__(self):
        if self.side not in SIDES:
            raise ValueError(f"side 只能是 {SIDES} 之一，收到 {self.side!r}")
        if self.fill not in FILLS:
            raise ValueError(f"fill 只能是 {FILLS} 之一，收到 {self.fill!r}")
        if self.entry < 2 or self.exit < 2 or self.atr_period < 2:
            raise ValueError("三个窗口都要至少是 2")
        if self.max_units < 1:
            raise ValueError("至少要允许一个单位")

    def describe(self) -> pd.Series:
        return pd.Series({
            "进场": f"突破 {self.entry} 日通道",
            "出场": f"反向突破 {self.exit} 日通道",
            "N": f"{self.atr_period} 日 ATR",
            "初始止损": f"{self.stop_atr} 个 N",
            "一个单位的风险": f"账户的 {self.risk:.1%}",
            "加仓": f"每走 {self.add_atr} 个 N 加一个单位，最多 {self.max_units} 个",
            "方向": {"long": "只做多", "short": "只做空", "both": "多空都做"}[self.side],
            "成交": {"touch": "碰到通道就成交", "next_open": "等下一根开盘"}[self.fill],
        })
```

两套系统，改两个数字就换：

```text
进场                       突破 20 日通道
出场                     反向突破 10 日通道
N                         20 日 ATR
初始止损                       2.0 个 N
一个单位的风险                   账户的 1.0%
加仓         每走 0.5 个 N 加一个单位，最多 4 个
方向                             只做多
成交                         碰到通道就成交
```

六条规则，一条一条说：

1. **进场**：碰到 20 日通道上轨就买。不看基本面，不看别的指标，不等确认。
2. **出场**：跌破 10 日通道下轨就走。**出场窗口比进场窗口短**，这样才能在趋势转向时比进场更快地反应。
3. **N**：20 日 ATR。它是这套系统的**度量衡**——止损、仓位、加仓间距全部用 N 表示，所以同一套参数能直接搬到波动率差十倍的另一个市场上。
4. **止损**：进场价往下 2 个 N。
5. **仓位**：一个「单位」冒账户 **1%** 的风险。于是单位数量 = 账户 × 1% ÷ (2N)——这正是第 26 篇的固定风险仓位。
6. **加仓**：价格每顺着走 0.5 个 N 就加一个单位，最多四个；**每加一次，把全部止损上移到最新那个单位往下 2N**。

> 一套 1983 年定下来的参数，这一篇要拿 2016–2026 年的数据去跑。**这是这门课里最干净的一次样本外检验**——参数比数据早了四十年，不可能是在这份数据上挑出来的（第 30 篇那条尖峰再也不可能出现在这里）。

---

## 六、时钟规矩的一个例外

第 27 篇立了一条规矩：**收盘算出来的信号，最早下一根成交。**而这一篇的进场是「盘中碰到通道就买」，看起来像在违规。

不是。判据始终是同一句话：**这个数，在那一刻能不能算出来？**

- 均线、RSI、「收盘创 20 日新高」——都要等**当根收盘**才知道，所以只能下一根成交。
- 通道那条线是用**前面 20 根**的最高价算的，**开盘之前就已经画好了**。价格在这一根里碰到它，是当时就看得见的事。

话虽如此，一个假设值不值得信，要拿数据说话。把成交方式换成「等下一根开盘」再跑一遍：

```python
rows = []
for name, (frame, periods) in MARKETS.items():
    for how in ("touch", "next_open"):
        result = T.turtle(frame, T.TurtlePlan(fill=how))
        curve = result["资金曲线"]
        rows.append({"标的": name, "成交方式": {"touch": "碰到通道就成交", "next_open": "等下一根开盘"}[how],
                     "年化": RP.annual_return(curve, periods),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "最大回撤": RP.max_drawdown(curve), "笔数": len(result["交易"]),
                     "合计 R": result["交易"]["R"].sum(), "记账误差": result["记账误差"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的    成交方式     年化     夏普    最大回撤  笔数     合计 R  记账误差
 SPY 碰到通道就成交 0.0468 0.6822 -0.1711  67  47.5013   0.0
 SPY  等下一根开盘 0.0467 0.6788 -0.0955  67  47.1247   0.0
AAPL 碰到通道就成交 0.1690 1.2604 -0.1187  59 166.8484   0.0
AAPL  等下一根开盘 0.1344 1.0549 -0.2176  59 136.4348   0.0
 BTC 碰到通道就成交 0.3160 1.3669 -0.2156  70 295.9295   0.0
 BTC  等下一根开盘 0.2980 1.3508 -0.2276  64 282.0023   0.0
```

| 标的 | 碰到通道就成交 | 等下一根开盘 | 差 |
|---|---|---|---|
| SPY | 4.68% | 4.67% | −0.01 个百分点 |
| AAPL | 16.90% | 13.44% | **−3.46 个百分点** |
| BTC | 31.60% | 29.80% | −1.80 个百分点 |

**这个假设值 0 到 3.5 个百分点，不是 0，但也远不是收益的来源。**如果晚一根就塌掉一大半，那说明这条策略赚的是「那一瞬间的价格」而不是趋势，该扔掉；现在它没塌，说明赚的确实是后面那段路。

⚠️ 记账误差那一列全程是 0——现金 + 持仓 × 价格 = 权益，一分不差（第 27 篇那条规矩）。

---

## 七、三个标的上跑一遍

```python
runs, rows = {}, []
for name, (frame, periods) in MARKETS.items():
    result = T.turtle(frame, T.TurtlePlan())
    runs[name] = result
    curve, trades = result["资金曲线"], result["交易"]
    rows.append({"标的": name, "年化": RP.annual_return(curve, periods),
                 "最大回撤": RP.max_drawdown(curve),
                 "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                 "卡玛": RP.calmar(curve, periods), "笔数": len(trades),
                 "在场比例": float(trades["根数"].sum()) / len(curve),
                 "期末": float(curve.iloc[-1]), "记账误差": result["记账误差"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的     年化    最大回撤     夏普     卡玛  笔数   在场比例           期末  记账误差
 SPY 0.0468 -0.1711 0.6822 0.2737  67 0.5355  157179.1026   0.0
AAPL 0.1690 -0.1187 1.2604 1.4234  59 0.5016  468098.0406   0.0
 BTC 0.3160 -0.2156 1.3669 1.4657  70 0.3785 1179570.7508   0.0
```

| 标的 | 年化 | 最大回撤 | 夏普 | 卡玛 | 笔数 | 在场比例 |
|---|---|---|---|---|---|---|
| SPY | 4.68% | −17.11% | 0.682 | 0.274 | 67 | 53.6% |
| AAPL | 16.90% | −11.87% | 1.260 | 1.423 | 59 | 50.2% |
| BTC | **31.60%** | **−21.56%** | **1.367** | **1.466** | 70 | **37.9%** |

先记住两件事，后面都要用：

1. **在场比例只有 38%–54%。**一多半时间这套系统是空仓的——这是它回撤浅的全部原因。BTC 买入持有的最大回撤是 −83.19%，它只有 −21.56%。
2. **这是原版口径：一个单位冒 1%，最多四个，总风险 4%。**海龟当年同时交易几十个市场，1% 是给一个组合定的；放在单个市场上它只用了账户很小的一部分。后面和主线策略对照时会换成同样的风险预算。

---

## 八、收益结构：低胜率、高盈亏比

```python
print(pd.DataFrame({name: T.r_profile(result["交易"]["R"]) for name, result in runs.items()}).round(3).to_string())
```

```text
           SPY     AAPL      BTC
笔数      67.000   59.000   70.000
胜率       0.448    0.458    0.329
平均盈利 R   3.002    8.023   16.147
平均亏损 R   1.151    1.556    1.605
盈亏比      2.610    5.158   10.059
期望 R     0.709    2.828    4.228
中位 R    -0.358   -0.812   -1.000
偏度       1.171    1.204    3.369
最大一笔 R   7.651   18.051   76.442
最差一笔 R  -3.149   -4.259   -2.613
合计 R    47.501  166.848  295.929
```

![收益结构](/images/trade-analysis/31/structure.png)

这张表值得逐行读：

| | SPY | AAPL | BTC |
|---|---|---|---|
| 胜率 | 44.8% | 45.8% | **32.9%** |
| 平均盈利 | 3.00R | 8.02R | **16.15R** |
| 平均亏损 | 1.15R | 1.56R | 1.61R |
| 盈亏比 | 2.61 | 5.16 | **10.06** |
| **中位数一笔** | **−0.36R** | **−0.81R** | **−1.00R** |
| 偏度 | 1.17 | 1.20 | **3.37** |
| 最大一笔 | 7.65R | 18.05R | **76.44R** |

**三个标的上，中位数那一笔全是负的。**BTC 上正好是 −1.00R——也就是说，**这套系统最典型的一次交易，就是碰到通道、买进去、被 2N 止损打掉。**

而平均亏损全部贴在 1.6R 以下，这不是运气，是 2N 止损**定义**出来的：你能亏多少，在进场那一刻就写死了。至于能赚多少，没有上限——BTC 上最大的一笔 76.44R。

> **止损做的是「把亏损这一头变成可预料的」。**盈利那一头之所以不可预料，正是因为你没有给它设上限。第 23 篇量过：给趋势跟随加固定止盈，胜率会上升，总收益会下降。

### 8.1 收益集中在几笔上

```python
for name, result in runs.items():
    print(f"--- {name} ---")
    print(T.contribution(result["交易"]["R"]).round(4).to_string(index=False))
```

```text
--- BTC ---
 拿掉最赚的几笔   剩下多少 R    占原来的   占总笔数
       0 295.9295  1.0000 0.0000
       1 219.4870  0.7417 0.0143
       3 145.2090  0.4907 0.0429
       5  88.1760  0.2980 0.0714
      10  -6.9578 -0.0235 0.1429
```

| 拿掉最赚的几笔 | SPY 剩下 | AAPL 剩下 | BTC 剩下 |
|---|---|---|---|
| 0 笔 | 100% | 100% | 100% |
| 1 笔（约 1.5%） | 83.9% | 89.2% | 74.2% |
| 3 笔（约 4.5%） | 51.8% | 68.1% | 49.1% |
| 5 笔（约 7.5%） | 24.7% | 50.2% | 29.8% |
| **10 笔（约 15%）** | **−17.5%** | 12.6% | **−2.3%** |

**在 SPY 和 BTC 上，拿掉最赚的十笔——不到 15% 的交易——九年的全部收益变成负数。**

这条性质有一个很实际的后果：**你不能挑着做。**「这次形态不好看」「这次成交量不配合」「上次刚亏完这次先观望一下」——只要你放过的那几次里有一次是那十笔之一，九年的成绩就没了。

---

## 九、凸性：它长得像一份期权

把市场按「最近 20 根涨了多少」分成五组，看策略在每一组里赚多少：

```python
for name, (frame, periods) in MARKETS.items():
    for label, plan in [("只做多", T.TurtlePlan()), ("多空都做", T.TurtlePlan(side="both"))]:
        curve = runs[name]["资金曲线"] if label == "只做多" else T.turtle(frame, plan)["资金曲线"]
        strategy = curve.pct_change().dropna()
        market = frame["close"].pct_change().reindex(strategy.index)
        print(f"--- {name}（{label}）---")
        print(T.convexity(strategy, market, buckets=5, window=20).round(4).to_string())
```

```text
--- BTC（只做多）---
               根数    市场中位    策略中位    策略平均  策略赚钱的比例
按市场 20 根涨跌分组                                      
第 1 组         653 -0.1601  0.0000 -0.0105   0.0046
第 2 组         652 -0.0444 -0.0086 -0.0126   0.0123
第 3 组         652  0.0095 -0.0021 -0.0096   0.0951
第 4 组         652  0.0814  0.0009  0.0113   0.5245
第 5 组         652  0.2482  0.0834  0.1062   0.8911
```

![凸性](/images/trade-analysis/31/convexity.png)

**只做多的时候，它长得像一份看涨期权**：市场大涨时赚很多（BTC 第 5 组中位 +8.34%、89.1% 的时候赚钱），市场平静或下跌时小亏（第 1–3 组中位 0 到 −0.86%）。那点小亏就是权利金——**你每年付出一点点，换的是「大行情来的时候一定在场」。**

多空都做的时候，左边那一头会抬起来：

```text
--- BTC（多空都做）---
               根数    市场中位    策略中位    策略平均  策略赚钱的比例
按市场 20 根涨跌分组                                      
第 1 组         653 -0.1601  0.0145  0.0250   0.6110
第 2 组         652 -0.0444 -0.0165 -0.0179   0.1028
第 3 组         652  0.0095 -0.0160 -0.0175   0.1258
第 4 组         652  0.0814 -0.0045  0.0050   0.4264
第 5 组         652  0.2482  0.0804  0.1006   0.8313
```

**BTC 上第 1 组（20 根跌了 16.01%）策略中位 +1.45%、61.1% 的时候赚钱**——这才是一条真正的微笑曲线，形状和「买了一份跨式期权」一样。

⚠️ 但图上另外两张说了同样重要的话：**SPY 和 AAPL 上那条线的左半边没有抬起来，反而更低了。**在长期向上的标的上做空趋势，是在逆着漂移做。第十一节会把这笔账算清楚。

---

## 十、金字塔加仓值不值

海龟最有特色的一条是加仓：每顺走 0.5 个 N 加一个单位，最多四个。它到底带来了什么？

为了公平，把总风险固定在 4%：一个单位冒 4%、两个各冒 2%、四个各冒 1%。

```python
rows = []
for name, (frame, periods) in MARKETS.items():
    for units, risk in [(1, 0.04), (2, 0.02), (4, 0.01)]:
        result = T.turtle(frame, T.TurtlePlan(max_units=units, risk=risk))
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"标的": name, "最多几个单位": units, "每个单位冒的风险": risk,
                     "总风险": units * risk, "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "平均用了几个单位": trades["单位数"].mean(), "最大一笔 R": trades["R"].max()})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的  最多几个单位  每个单位冒的风险  总风险     年化    最大回撤     夏普  平均用了几个单位  最大一笔 R
 SPY       1      0.04 0.04 0.0726 -0.1189 0.9020    1.0000  7.4601
 SPY       2      0.02 0.04 0.0634 -0.1165 0.8220    1.5606  7.4601
 SPY       4      0.01 0.04 0.0468 -0.1711 0.6822    2.4478  7.6509
AAPL       1      0.04 0.04 0.1954 -0.1314 1.3156    1.0000  6.8565
AAPL       2      0.02 0.04 0.1921 -0.1270 1.3474    1.8214  9.4455
AAPL       4      0.01 0.04 0.1690 -0.1187 1.2604    3.0847 18.0509
 BTC       1      0.04 0.04 0.3212 -0.3466 1.3148    1.0000 17.7823
 BTC       2      0.02 0.04 0.3207 -0.2681 1.3492    1.7761 37.0366
 BTC       4      0.01 0.04 0.3160 -0.2156 1.3669    2.9714 76.4425
```

| 标的 | 最多单位数 | 年化 | 最大回撤 | 夏普 |
|---|---|---|---|---|
| BTC | 1 | 32.12% | −34.66% | 1.315 |
| BTC | 2 | 32.07% | −26.81% | 1.349 |
| BTC | **4** | 31.60% | **−21.56%** | **1.367** |
| AAPL | 1 | 19.54% | −13.14% | 1.316 |
| AAPL | 4 | 16.90% | −11.87% | 1.260 |
| SPY | 1 | 7.26% | −11.89% | 0.902 |
| SPY | **4** | **4.68%** | **−17.11%** | **0.682** |

**在 BTC 上，加仓几乎不改变年化（32.12% → 31.60%），却把最大回撤砍掉了三分之一（−34.66% → −21.56%）。**

原因很朴素：**加仓让你「一开始小、确认对了才大」。**四分之一的仓位在进场那一刻就位，剩下四分之三要等价格真的顺着走了 0.5、1.0、1.5 个 N 才加上去。假突破在第一个单位上就被打掉，永远等不到后面三个。

⚠️ 但这不是普适的：**AAPL 上加仓略微变差，SPY 上明显变差**（年化 7.26% → 4.68%，回撤反而从 −11.89% 深到 −17.11%）。SPY 的日波动小、20 日 ATR 也小，0.5 个 N 的加仓间距被走得太轻易，结果是在震荡里反复加满又反复止损。**加仓是一个和标的波动结构有关的选择，不是一条普适的改进。**

---

## 十一、做空那一半

海龟原版是多空都做的（他们交易的是期货）。把三个标的分开量一量：

```python
rows = []
for name, (frame, periods) in MARKETS.items():
    for side in ("long", "short", "both"):
        result = T.turtle(frame, T.TurtlePlan(side=side, risk=0.025))
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"标的": name, "方向": {"long": "只做多", "short": "只做空", "both": "多空都做"}[side],
                     "年化": RP.annual_return(curve, periods), "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods), "笔数": len(trades),
                     "胜率": float((trades["R"] > 0).mean()), "合计 R": trades["R"].sum()})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的   方向      年化    最大回撤      夏普  笔数     胜率     合计 R
 SPY  只做多  0.0688 -0.1156  0.8299  64 0.5469  37.5090
 SPY  只做空 -0.1502 -0.8064 -0.5075  58 0.1034 -69.1582
 SPY 多空都做 -0.0903 -0.6592 -0.2157 121 0.3388 -30.6492
AAPL  只做多  0.2237 -0.1517  1.3730  56 0.5357  88.2173
AAPL  只做空 -0.1479 -0.8184 -0.5657  51 0.1176 -59.2419
AAPL 多空都做  0.0427 -0.4036  0.2904 107 0.3364  28.9754
 BTC  只做多  0.4691 -0.4238  1.2817  69 0.3478 179.4161
 BTC  只做空  0.0498 -0.6789  0.3047  67 0.2836  32.2142
 BTC 多空都做  0.5465 -0.4973  1.1749 135 0.3185 212.6303
```

| 标的 | 只做多 | 只做空 | 多空都做 |
|---|---|---|---|
| SPY | +6.88% | **−15.02%** | −9.03% |
| AAPL | +22.37% | **−14.79%** | +4.27% |
| BTC | +46.91% | +4.98% | **+54.65%** |

**在 SPY 和 AAPL 上，做空那一半是纯亏损**——胜率只有 10.3% 和 11.8%，把整条策略从正收益拖成负收益。BTC 上做空只赚了 4.98%（九年），但它不是拖累：加上之后总年化从 46.91% 升到 54.65%。

这和第 26 篇的发现是同一件事：**股票和股指有长期向上的漂移，做空趋势等于逆着漂移下注**；BTC 的大跌够深够快，做空才勉强收支平衡。

> **原型不等于配方。**海龟的多空对称是为了几十个期货品种的组合设计的，照搬到长期向上的股票上就是亏钱。

---

## 十二、什么时候有效

趋势跟随需要趋势。把每一笔交易按进场那天的**效率比**（第 8 篇：这 20 根走了多远 ÷ 走了多少路）分成三组：

```python
for name, (frame, periods) in MARKETS.items():
    trades = runs[name]["交易"].copy()
    trades["效率比"] = ST.efficiency_ratio(frame["close"], 20).reindex(trades["进场日"]).to_numpy()
    groups = pd.qcut(trades["效率比"], 3, labels=["低（来回震荡）", "中", "高（一直朝一个方向）"])
    print(f"--- {name} ---")
    print(trades.groupby(groups, observed=True)["R"].agg(
        笔数="size", 胜率=lambda x: float((x > 0).mean()), 平均="mean", 中位="median", 合计="sum"
    ).round(3).to_string())
```

```text
            笔数     胜率     平均     中位       合计
效率比                                         
低（来回震荡）     24  0.208  0.576 -1.000   13.824
中           23  0.348  5.139 -0.856  118.190
高（一直朝一个方向）  23  0.435  7.127 -0.705  163.915
```

BTC 上这个关系非常干净：

| 进场时的效率比 | 笔数 | 胜率 | 平均 R | 合计 R |
|---|---|---|---|---|
| 低（来回震荡） | 24 | 20.8% | 0.58 | **13.8** |
| 中 | 23 | 34.8% | 5.14 | 118.2 |
| 高（一直朝一个方向） | 23 | 43.5% | 7.13 | **163.9** |

**在「一直朝一个方向」的环境里进场，九年合计 163.9R；在「来回震荡」的环境里进场，只有 13.8R。**

⚠️ 但 SPY 和 AAPL 上看不出这个规律（SPY 上反而是低效率比那一组合计最高）。**每组只有二十笔出头**——第 29 篇讲过，二十笔什么都证明不了。所以这一节的诚实版本是：**BTC 上这个关系成立；美股上样本量不够，别下结论。**

---

## 十三、动手：`talab.trend`

```python
"""talab.trend：趋势跟随与突破。第 31 篇。

第六部分讲完了怎么检验，这一篇开始讲**被检验的东西**：一类真实存在、公开了四十年、
到现在还有人靠它管钱的策略原型。

趋势跟随的全部内容可以写成一句话：**价格创新高就买，跌破就走。**
它没有预测，没有估值，没有「这次不一样」。它唯一的假设是——

> 大的行情会持续得比大多数人愿意相信的更久，而小的行情会来回震荡。

这个假设**大部分时候是错的**（第 31 篇实测：七成的突破是假的），
但它错的时候亏得少、对的时候赚得多。这个模块就是把这句话拆成可以测量的零件：

1. **通道与突破**：`donchian`、`breakouts`、`follow_through`
2. **海龟系统**：`TurtlePlan` + `turtle`（含 2N 止损、按 N 定仓位、金字塔加仓）
3. **收益结构**：`r_profile`、`contribution`、`convexity`

⚠️ **通道突破是这门课里唯一可以「当根成交」的信号**：通道那条线是用**前面几根**的
最高价算出来的，开盘之前就已经画好了，价格在这一根里碰到它是一件**当时就能看见**的事。
这和第 27 篇「收盘算出来的信号只能下一根成交」不矛盾——那条规矩管的是用到**当根收盘价**
的信号（均线、RSI、收盘价创新高）。判据始终是同一句：**这个数，在那一刻能不能算出来。**
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from talab.backtest import Account

SIDES = ("long", "short", "both")
```

### 突破与假突破

```python
def breakouts(df: pd.DataFrame, n: int = 20, horizon: int = 20) -> pd.DataFrame:
    """每一次**向上**突破 n 日通道：突破时的价格，以及之后 horizon 根里发生了什么。

    连续多根都在通道上方只算**一次**突破（第一次算，后面的不算），
    否则一段大趋势会被数成几十次「突破」，假突破的比例就被稀释成假的。
    """
    channel = donchian(df["high"], df["low"], n)
    high, low, close = (df[x].to_numpy(float) for x in ["high", "low", "close"])
    upper = channel["上轨"].to_numpy()
    rows, armed = [], True
    for i in range(len(close)):
        if np.isnan(upper[i]):
            continue
        if high[i] > upper[i]:
            if armed:
                ahead = close[i + 1:i + 1 + horizon]
                worst = low[i + 1:i + 1 + horizon]
                rows.append({"时间": df.index[i], "突破价": upper[i], "收盘": close[i],
                             "之后最高收盘": float(ahead.max()) if len(ahead) else np.nan,
                             "之后最低价": float(worst.min()) if len(worst) else np.nan,
                             f"{horizon} 根后": float(ahead[-1]) if len(ahead) == horizon else np.nan})
                armed = False
        elif close[i] < upper[i]:
            armed = True                                  # 回到通道里面，下一次才算新的突破
    out = pd.DataFrame(rows)
    if len(out):
        out["之后涨幅"] = out[f"{horizon} 根后"] / out["突破价"] - 1
        out["最大顺势"] = out["之后最高收盘"] / out["突破价"] - 1
        out["最大逆势"] = out["之后最低价"] / out["突破价"] - 1
    return out


def follow_through(table: pd.DataFrame, threshold: float = 0.0) -> pd.Series:
    """一批突破里，有多少是「走出去了」的，有多少是假的。

    `threshold` 是判定标准（`之后涨幅` 要超过它才算真）。默认 0：**只要没回到突破价以下就算真**——
    这已经是最宽松的口径了，而第 31 篇实测下来仍然只有三成多能过。
    """
    real = table["之后涨幅"] > threshold
    return pd.Series({
        "突破次数": float(len(table)), "走出去的": float(real.sum()),
        "假突破比例": float((~real).mean()),
        "真的那些平均涨": float(table.loc[real, "之后涨幅"].mean()) if real.any() else np.nan,
        "假的那些平均跌": float(table.loc[~real, "之后涨幅"].mean()) if (~real).any() else np.nan,
        "全部平均": float(table["之后涨幅"].mean()),
        "最大顺势中位": float(table["最大顺势"].median()),
        "最大逆势中位": float(table["最大逆势"].median()),
    })
```

### 海龟引擎

```python
def turtle(df: pd.DataFrame, plan: TurtlePlan | None = None, equity: float = 100_000.0) -> dict:
    """按海龟法则跑一遍历史。

    每一根 K 线上按固定顺序做五件事（和第 27 篇的引擎同一套规矩）：

    0. **补成交**：`fill="next_open"` 时，上一根定下来的动作用这一根的开盘价成交
    1. **出场**：先看止损，再看反向通道；两个都碰到时按**先止损**算（悲观口径）
    2. **加仓**：价格又顺走了 `add_atr` 个 N 就加一个单位，并把**全部**止损上移
    3. **估值**：按收盘价记权益
    4. **进场**：空仓时，价格碰到 `entry` 日通道就进

    通道线来自前面几根，所以 1、2、4 默认在**当根**成交（见模块开头那条 ⚠️）。
    把 `fill` 换成 `"next_open"` 就能量出「当根成交」这个假设值多少钱——
    如果它值很多，那说明这条策略靠的是那一瞬间的价格，不是趋势。
    返回资金曲线、逐笔交易（一整个仓位算一笔，带 R 倍数）、每一次加仓的明细。
    """
    from talab import indicators as I

    plan = plan or TurtlePlan()
    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    n_value = I.atr(df["high"], df["low"], df["close"], plan.atr_period).shift(1).to_numpy()
    enter = donchian(df["high"], df["low"], plan.entry)
    leave = donchian(df["high"], df["low"], plan.exit)
    up_in, down_in = enter["上轨"].to_numpy(), enter["下轨"].to_numpy()
    up_out, down_out = leave["上轨"].to_numpy(), leave["下轨"].to_numpy()

    # ⚠️ 空头的数量只记在 `units` 里，`account.shares` 全程是 0——
    # 所以权益一律用下面的 `position_value` 算，不要用 `account.equity`。
    account = Account(cash=float(equity))
    curve, trades, adds, error = [], [], [], 0.0
    side = 0                                   # +1 做多，−1 做空，0 空仓
    units: list[tuple[float, float]] = []      # 每个单位的（成交价，数量）
    stop = last_price = risk_amount = np.nan
    opened_at = -1

    def position_value(price: float) -> float:
        """权益：做多是「现金 + 持仓市值」，做空是「现金 − 买回来要花的钱」。

        ⚠️ 做空时卖出所得已经记在现金里了，所以**不要再减一次借来的钱**——
        第一版就是这么写的，结果最大回撤算出 −106%（权益跑到 0 以下）。
        「回撤超过 100%」永远是记账错了，不是策略真的这么惨。
        """
        held = sum(q for _, q in units)
        return account.cash + side * held * price

    def close_all(i: int, price: float, reason: str) -> None:
        nonlocal side, units, stop, opened_at
        held = sum(q for _, q in units)
        cost = sum(p * q for p, q in units)
        if side > 0:
            account.sell(price, held, plan.fee_rate)
            profit = price * held - cost - abs(price * held) * plan.fee_rate
        else:
            account.cash -= price * held * (1 + plan.fee_rate)      # 买回来平掉空头
            account.fees += price * held * plan.fee_rate
            profit = cost - price * held - abs(price * held) * plan.fee_rate
        trades.append({"进场日": df.index[opened_at], "方向": "多" if side > 0 else "空",
                       "第一个单位的价": units[0][0], "平均价": cost / held if held else np.nan,
                       "单位数": len(units), "出场日": df.index[i], "出场价": price,
                       "原因": reason, "盈亏": profit, "R": profit / risk_amount,
                       "根数": i - opened_at})
        side, units, stop, opened_at = 0, [], np.nan, -1

    def open_unit(i: int, price: float, direction: int) -> bool:
        nonlocal side, stop, last_price, risk_amount
        step = plan.stop_atr * n_value[i]
        want = position_value(price) * plan.risk / step          # 一个单位：冒账户的 risk
        if direction > 0:
            shares = min(want, account.affordable(price, plan.fee_rate))
        else:
            shares = min(want, position_value(price) / (price * (1 + plan.fee_rate)))
        if shares <= 1e-12:
            return False                                         # 买不起了：别再往下加
        if direction > 0:
            account.buy(price, shares, plan.fee_rate)
        else:
            account.cash += price * shares * (1 - plan.fee_rate)
            account.fees += price * shares * plan.fee_rate
        if not units:
            side = direction
            risk_amount = shares * step                          # 1R = 第一个单位的初始风险
        units.append((price, shares))
        last_price = price
        stop = price - direction * step                          # 加仓之后全部止损跟着走
        adds.append({"时间": df.index[i], "第几个单位": len(units), "成交价": price,
                     "数量": shares, "止损移到": stop})
        return True

    first = int(np.argmax(~np.isnan(n_value) & ~np.isnan(up_in) & ~np.isnan(down_in)))
    pending: tuple | None = None               # fill="next_open" 时挂着的动作
    for i in range(first, len(c)):
        # 第 0 步：上一根定下来的动作，用这一根的开盘价成交
        if pending is not None:
            what, extra = pending
            pending = None
            if what == "close" and side:
                close_all(i, o[i], extra)
            elif what == "add" and side and len(units) < plan.max_units:
                open_unit(i, o[i], side)
            elif what == "open" and not side:
                opened_at = i
                open_unit(i, o[i], extra)

        # 第 1 步：出场
        later = plan.fill == "next_open"
        if side > 0:
            if l[i] <= stop:
                pending = ("close", "止损") if later else pending
                if not later:
                    close_all(i, min(o[i], stop), "止损")
            elif l[i] <= down_out[i]:
                pending = ("close", "通道出场") if later else pending
                if not later:
                    close_all(i, min(o[i], down_out[i]), "通道出场")
        elif side < 0:
            if h[i] >= stop:
                pending = ("close", "止损") if later else pending
                if not later:
                    close_all(i, max(o[i], stop), "止损")
            elif h[i] >= up_out[i]:
                pending = ("close", "通道出场") if later else pending
                if not later:
                    close_all(i, max(o[i], up_out[i]), "通道出场")

        # 第 2 步：加仓
        while side and pending is None and len(units) < plan.max_units:
            level = last_price + side * plan.add_atr * n_value[i]
            if side > 0 and h[i] >= level:
                if later:
                    pending = ("add", None)
                    break
                if not open_unit(i, max(o[i], level), 1):
                    break
            elif side < 0 and l[i] <= level:
                if later:
                    pending = ("add", None)
                    break
                if not open_unit(i, min(o[i], level), -1):
                    break
            else:
                break

        # 第 3 步：估值
        value = position_value(c[i])
        held = sum(q for _, q in units)
        error = max(error, abs(account.cash + side * held * c[i] - value))
        curve.append(value)

        # 第 4 步：进场
        if not side and pending is None and n_value[i] > 0:
            if plan.side in ("long", "both") and h[i] > up_in[i]:
                if later:
                    pending = ("open", 1)
                else:
                    opened_at = i
                    open_unit(i, max(o[i], up_in[i]), 1)
            elif plan.side in ("short", "both") and l[i] < down_in[i]:
                if later:
                    pending = ("open", -1)
                else:
                    opened_at = i
                    open_unit(i, min(o[i], down_in[i]), -1)

    if side:                                                     # 最后一根还拿着
        close_all(len(c) - 1, c[-1], "未平仓")
    index = df.index[first:]
    columns = ["进场日", "方向", "第一个单位的价", "平均价", "单位数", "出场日", "出场价",
               "原因", "盈亏", "R", "根数"]
    return {"资金曲线": pd.Series(curve, index=index, name="权益"),
            "交易": pd.DataFrame(trades, columns=columns),
            "加仓": pd.DataFrame(adds, columns=["时间", "第几个单位", "成交价", "数量", "止损移到"]),
            "手续费合计": account.fees, "记账误差": error,
            "权益最低点": float(min(curve)) if curve else np.nan}
```

⚠️ `position_value` 上面那条注释是踩过的坑：**做空时卖出所得已经记在现金里了，不要再减一次借来的钱。**第一版这么写的结果是最大回撤算出 **−106%**——权益跑到 0 以下。**「回撤超过 100%」永远是记账错了，不是策略真的这么惨。**

### 收益结构

```python
def r_profile(r) -> pd.Series:
    """一串 R 倍数的形状：胜率、盈亏比、期望，以及**偏度**。

    趋势跟随的招牌是「胜率低、盈亏比高、偏度为正」。
    第 23 篇的 `risk.expectancy` 给的是前两项，这里补上尾巴那一头——
    **正偏度的意思是「亏损可以预料，盈利不可以」**，而策略的全部收益都藏在那个不可预料的尾巴里。
    """
    r = pd.Series(r).dropna().astype(float)
    wins, losses = r[r > 0], r[r <= 0]
    return pd.Series({
        "笔数": float(len(r)), "胜率": float((r > 0).mean()),
        "平均盈利 R": float(wins.mean()) if len(wins) else 0.0,
        "平均亏损 R": float(-losses.mean()) if len(losses) else 0.0,
        "盈亏比": float(wins.mean() / -losses.mean()) if len(losses) and losses.mean() else np.inf,
        "期望 R": float(r.mean()), "中位 R": float(r.median()),
        "偏度": float(r.skew()), "最大一笔 R": float(r.max()), "最差一笔 R": float(r.min()),
        "合计 R": float(r.sum()),
    })


def contribution(r, tops=(1, 3, 5, 10)) -> pd.DataFrame:
    """把最赚钱的几笔拿掉，还剩多少。

    这张表回答一个很不舒服的问题：**这条策略的收益，有多少集中在极少数几笔上？**
    集中度高不是缺点，是趋势跟随的**定义**——但你必须知道它有多高，
    因为那意味着「错过那几笔」和「策略失效」在账户上是同一件事。
    """
    r = pd.Series(r).dropna().astype(float).sort_values(ascending=False)
    total = r.sum()
    rows = [{"拿掉最赚的几笔": 0, "剩下多少 R": total, "占原来的": 1.0, "占总笔数": 0.0}]
    for n in tops:
        if n >= len(r):
            break
        left = total - r.iloc[:n].sum()
        rows.append({"拿掉最赚的几笔": n, "剩下多少 R": left, "占原来的": left / total if total else np.nan,
                     "占总笔数": n / len(r)})
    return pd.DataFrame(rows)


def convexity(strategy: pd.Series, market: pd.Series, buckets: int = 5,
              window: int = 20) -> pd.DataFrame:
    """凸性表：把市场按 `window` 根的涨跌分成几组，看策略在每一组里赚多少。

    趋势跟随的收益应该是一条**微笑曲线**——市场大涨时赚、市场大跌时也赚（或者至少不怎么亏）、
    市场不涨不跌时小亏。这个形状和「买了一份跨式期权」是一回事，
    小亏就是权利金。第 32 篇的均值回归会给出正好相反的形状（凹性）。
    """
    if not 0 < buckets <= 20:
        raise ValueError("buckets 要在 1 和 20 之间")
    both = pd.concat([strategy.rename("策略"), market.rename("市场")], axis=1).dropna()
    rolled = pd.DataFrame({
        "策略": (1 + both["策略"]).rolling(window).apply(np.prod, raw=True) - 1,
        "市场": (1 + both["市场"]).rolling(window).apply(np.prod, raw=True) - 1,
    }).dropna()
    groups = pd.qcut(rolled["市场"], buckets, labels=False, duplicates="drop")
    out = rolled.groupby(groups).agg(根数=("市场", "size"), 市场中位=("市场", "median"),
                                     策略中位=("策略", "median"), 策略平均=("策略", "mean"),
                                     策略赚钱的比例=("策略", lambda x: float((x > 0).mean())))
    out.index = [f"第 {i + 1} 组" for i in range(len(out))]
    out.index.name = f"按市场 {window} 根涨跌分组"
    return out
```

### 测试

十四个测试里最该看的两条。一条钉住那条「必须 shift」的规矩：

```python
def test_donchian_shifts_by_one_bar():
    """不推迟一根，「创 n 日新高」会永远成立——今天的最高价当然是包含今天在内的最高价之一。"""
    bars = frame([1, 2, 3, 4, 5])
    channel = T.donchian(bars["high"], bars["low"], 3)
    assert np.isnan(channel["上轨"].iloc[2])                 # 前三根凑不齐「前 3 根」
    assert channel["上轨"].iloc[3] == 3 and channel["下轨"].iloc[3] == 1
    assert channel["中轨"].iloc[3] == 2
    assert (bars["high"] > channel["上轨"]).iloc[3:].all()   # 一路新高：确实每根都突破
    wrong = bars["high"].rolling(3).max()                    # 忘了 shift 的写法
    assert not (bars["high"] > wrong).iloc[3:].any()         # 永远不成立，信号一个都没有
```

另一条钉住「碰到通道就成交」和「等下一根开盘」的区别，顺便把**横盘必须用锯齿**那个坑写进了注释（真实波幅全是 0 的话 N 也是 0，海龟一笔都开不出来）：

```python
def test_turtle_next_open_fills_one_bar_later():
    zigzag = frame([100 + (1 if i % 2 else -1) for i in range(14)], spread=0.02)
    assert float(zigzag["high"].iloc[4:14].max()) == pytest.approx(103.02)   # 10 日通道上轨
    # 第 15 根：开在通道下方 102，盘中穿上去；第 16 根直接开在 107
    extra = pd.DataFrame({"open": [102.0, 107.0, 110.0], "high": [106.0, 111.0, 114.0],
                          "low": [101.0, 106.0, 109.0], "close": [105.0, 110.0, 113.0]},
                         index=pd.date_range(zigzag.index[-1] + pd.Timedelta(days=1), periods=3))
    bars = pd.concat([zigzag, extra])
    common = dict(entry=10, exit=5, atr_period=5, max_units=1)
    touch = T.turtle(bars, T.TurtlePlan(fill="touch", **common))["交易"].iloc[0]
    later = T.turtle(bars, T.TurtlePlan(fill="next_open", **common))["交易"].iloc[0]
    assert touch["第一个单位的价"] == pytest.approx(103.02)       # 就在通道那条线上成交
    assert later["进场日"] == touch["进场日"] + pd.Timedelta(days=1)
    assert later["第一个单位的价"] == pytest.approx(107.0)        # 等一根，开盘已经 107 了
```

---

## 十四、用第六部分的方法检验一遍

### 14.1 参数曲面与 walk-forward

```python
GRID = [(e, x) for e in [10, 15, 20, 30, 40, 55, 80, 100] for x in [5, 10, 15, 20, 30, 40] if x < e]
DEFAULT = (20, 10)
print(f"网格 {len(GRID)} 组（进场 10–100 日 × 出场 5–40 日，出场必须比进场短）")
rows, matrices = [], {}
for name, (frame, periods) in MARKETS.items():
    daily = np.array([T.turtle(frame, T.TurtlePlan(entry=e, exit=x))["资金曲线"]
                      .pct_change().reindex(frame.index).fillna(0).to_numpy() for e, x in GRID])
    matrices[name] = daily
    scores = daily.mean(axis=1) / daily.std(axis=1, ddof=1) * np.sqrt(periods)
    table = pd.DataFrame({"进场": [e for e, x in GRID], "出场": [x for e, x in GRID], "夏普": scores})
    face = V.surface(table, "进场", "出场", "夏普")
    around = V.neighbourhood(face, DEFAULT)
    splits = V.walk_forward(daily.shape[1], int(periods * 2), periods)
    picked = V.walk_forward_run(daily, splits, names=GRID)
    stitched = V.stitch(daily, splits, [GRID.index(p) for p in picked["选了谁"]])
    rolling = RP.to_curve(pd.Series(stitched, index=pd.RangeIndex(len(stitched))))
    held = daily[GRID.index(DEFAULT), splits[0][1].start:splits[-1][1].stop]
    kept = RP.to_curve(pd.Series(held, index=pd.RangeIndex(len(held))))
    rows.append({"标的": name, "1983 年那组 (20,10)": scores[GRID.index(DEFAULT)],
                 "排第几": f"{int((scores > scores[GRID.index(DEFAULT)]).sum()) + 1}/{len(GRID)}",
                 "邻居中位": around["邻居中位"], "落差": around["落差"],
                 "网格最好": scores.max(), "网格中位": float(np.median(scores)),
                 "亏钱的格子": float((daily.sum(axis=1) < 0).mean()),
                 "白捡的门槛": V.expected_max_sharpe(len(GRID), scores.std()),
                 "PBO": V.pbo(daily, 16)["过拟合概率 PBO"],
                 "每年重挑的年化": RP.annual_return(rolling, periods),
                 "一直用 (20,10) 的年化": RP.annual_return(kept, periods)})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
网格 33 组（进场 10–100 日 × 出场 5–40 日，出场必须比进场短）
  标的  1983 年那组 (20,10)  排第几   邻居中位     落差   网格最好   网格中位  亏钱的格子  白捡的门槛    PBO  每年重挑的年化  一直用 (20,10) 的年化
 SPY            0.6792 6/33 0.5268 0.1523 0.7580 0.5211    0.0 0.3354 0.5904   0.0330           0.0372
AAPL            1.2548 2/33 1.0521 0.2027 1.2860 0.8121    0.0 0.3920 0.0210   0.1815           0.1957
 BTC            1.3623 1/33 1.1928 0.1695 1.3623 1.0496    0.0 0.3175 0.2082   0.2113           0.2429
```

| 标的 | (20,10) 的夏普 | 排第几 | 落差 | 网格中位 | 亏钱的格子 | PBO | 每年重挑 | 一直用 (20,10) |
|---|---|---|---|---|---|---|---|---|
| SPY | 0.6792 | 6/33 | +0.152 | 0.521 | **0%** | 0.590 | 3.30% | **3.72%** |
| AAPL | 1.2548 | 2/33 | +0.203 | 0.812 | **0%** | 0.021 | 18.15% | **19.57%** |
| BTC | 1.3623 | **1/33** | +0.170 | 1.050 | **0%** | 0.208 | 21.13% | **24.29%** |

四件事：

1. **1983 年那组参数在 BTC 上排第 1、AAPL 上排第 2。**⚠️ 排第一本身不重要（33 格里总有一个第一）。重要的是**落差只有 +0.15 到 +0.20**——整片曲面都在 1.0–1.37，这是一片高地，不是第 30 篇那根针（那根针的落差是 +1.11）。
2. **33 组参数里，没有一组在任何一个标的上亏钱。**不是「挑到了好参数」，是**整个参数族都work**。
3. **每年重挑参数，三个标的上全部跑输「一直用 (20,10)」。**这是第 30 篇那个结论的又一次重演：walk-forward 是诚实的度量，不是提高收益的方法。
4. **SPY 上的 PBO 是 0.590**——在 SPY 上挑参数依然是抛硬币。AAPL 的 0.021 和 BTC 的 0.208 则说明在这两个标的上参数排名确实带一点信息。

### 14.2 蒙特卡洛：把趋势拆掉

最关键的一刀。用块自助法造出「同样的日收益率分布、同样的波动率聚集，但**没有那几段趋势**」的假价格，然后把同一套规则原样跑一遍：

```python
rows = []
for name, (frame, periods) in MARKETS.items():
    real = runs[name]["资金曲线"]
    real_annual = RP.annual_return(real, periods)
    real_sharpe = RP.sharpe(real.pct_change().dropna(), periods)
    fakes = []
    for path in V.synthetic_close(frame["close"], n=N_PATHS, block=20, seed=31):
        scale = path / frame["close"].to_numpy()          # 四个价按同一个比例缩放，保住 K 线的形状
        fake = pd.DataFrame({c: frame[c].to_numpy() * scale for c in ["open", "high", "low", "close"]},
                            index=frame.index)
        curve = T.turtle(fake, T.TurtlePlan())["资金曲线"]
        fakes.append((RP.annual_return(curve, periods),
                      RP.sharpe(curve.pct_change().dropna(), periods)))
    annuals = np.array([a for a, s in fakes])
    sharpes = np.array([s for a, s in fakes])
    rows.append({"标的": name, "真实年化": real_annual, "假数据年化中位": float(np.median(annuals)),
                 "假数据 95% 分位": float(np.percentile(annuals, 95)),
                 "真实夏普": real_sharpe, "假数据夏普中位": float(np.median(sharpes)),
                 "假的比真的好的比例": float((annuals >= real_annual).mean())})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的   真实年化  假数据年化中位  假数据 95% 分位   真实夏普  假数据夏普中位  假的比真的好的比例
 SPY 0.0468  -0.0569     -0.0069 0.6822  -0.7168        0.0
AAPL 0.1690  -0.0424      0.0312 1.2604  -0.3362        0.0
 BTC 0.3160  -0.0944      0.0001 1.3669  -0.6517        0.0
```

![蒙特卡洛](/images/trade-analysis/31/montecarlo.png)

| 标的 | 真实年化 | 假数据年化中位 | 假数据 95% 分位 | 假的比真的好的比例 |
|---|---|---|---|---|
| SPY | +4.68% | **−5.69%** | −0.69% | **0/100** |
| AAPL | +16.90% | **−4.24%** | +3.12% | **0/100** |
| BTC | +31.60% | **−9.44%** | +0.01% | **0/100** |

**把趋势拆掉之后，同一套规则在三个标的上都变成亏钱的，而且 300 条假数据里没有一条比真实的好。**

对比第 30 篇那条「年化 173.74%」的曲线：它在假数据上的 p 值是 **0.27**。这里是 **< 0.01**。

⚠️ 两条诚实的说明：

1. **块自助法保留了漂移。**假数据的期望日收益率和真实的一样，所以「假数据上亏钱」不是因为假市场不涨——它照样涨，只是涨法变成了没有方向的抖动。趋势跟随一多半时间空仓，接不住这种涨法。
2. **块长 20 保留了一个月以内的走势，破坏的是一个月以上的。**换成块长 1、5、60、120 重做，假数据年化中位在 −13.5% 到 −7.4% 之间，比例全是 0/60——结论对块长不敏感。

---

## 十五、和主线策略 v4、买入持有并排

全部含成本（BTC 用第 28 篇的现货 taker + 半个价差 + 止损滑点，美股用现抓的监管费 + 1 个基点价差）：

```python
schedule = pd.Series({"SEC 占卖出金额": 20.60 / 1e6, "TAF 每股": 0.000166, "TAF 每笔上限": 8.30})
us_cost = C.us_stock(100.0, 100.0, "sell", spread_bp=1.0, sec_rate=schedule["SEC 占卖出金额"],
                     taf_per_share=schedule["TAF 每股"], taf_cap=schedule["TAF 每笔上限"])["占名义价值"]
btc_cost = C.crypto(1.0, "现货 taker", spread_bp=C.BTC_PERP_SPREAD_BP)["占名义价值"] + 0.00097 / 2
rows = []
for name, (frame, periods) in MARKETS.items():
    price = frame["close"]
    fee = btc_cost if name == "BTC" else us_cost
    for label, plan in [("海龟（原版：每单位 1%，最多 4 个）", T.TurtlePlan(fee_rate=fee)),
                        ("海龟（和主线同样的风险预算：2.5% × 4）", T.TurtlePlan(risk=0.025, fee_rate=fee))]:
        result = T.turtle(frame, plan)
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"标的": name, "策略": label, "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "卡玛": RP.calmar(curve, periods), "笔数": len(trades),
                     "逐笔的 t 值": RP.trade_metrics(trades["R"])["t 值"],
                     "手续费": result["手续费合计"]})
    plan = BT.Plan(entry=((I.sma(price, 50) > I.sma(price, 200))
                          & (price >= price.rolling(20).max())).fillna(False),
                   exit=I.cross_below(I.sma(price, 50), I.sma(price, 200)).fillna(False),
                   stop="chandelier", k=3.0, trigger="close", sizing="risk",
                   risk_per_trade=0.10, fee_rate=fee)
    main = BT.run(frame, plan, 100_000.0)
    curve = main["资金曲线"]
    rows.append({"标的": name, "策略": "主线 v4", "年化": RP.annual_return(curve, periods),
                 "最大回撤": RP.max_drawdown(curve),
                 "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                 "卡玛": RP.calmar(curve, periods), "笔数": len(main["交易"]),
                 "逐笔的 t 值": RP.trade_metrics(main["交易"]["收益"])["t 值"],
                 "手续费": main["手续费合计"]})
    rows.append({"标的": name, "策略": "买入持有", "年化": RP.annual_return(price, periods),
                 "最大回撤": RP.max_drawdown(price),
                 "夏普": RP.sharpe(price.pct_change().dropna(), periods),
                 "卡玛": RP.calmar(price, periods), "笔数": 1, "逐笔的 t 值": np.nan, "手续费": 0.0})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的                      策略     年化    最大回撤     夏普     卡玛  笔数  逐笔的 t 值         手续费
 SPY    海龟（原版：每单位 1%，最多 4 个） 0.0459 -0.1735 0.6695 0.2648  67   2.2067   1088.4034
 SPY 海龟（和主线同样的风险预算：2.5% × 4） 0.0679 -0.1164 0.8185 0.5832  64   2.9010   1297.3414
 SPY                   主线 v4 0.0291 -0.1242 0.4184 0.2343  39   1.1180    655.2938
 SPY                    买入持有 0.1346 -0.3410 0.7913 0.3945   1      NaN      0.0000
AAPL    海龟（原版：每单位 1%，最多 4 个） 0.1682 -0.1194 1.2552 1.4089  59   3.4832   1651.7188
AAPL 海龟（和主线同样的风险预算：2.5% × 4） 0.2228 -0.1519 1.3678 1.4665  56   3.6582   2786.3123
AAPL                   主线 v4 0.0983 -0.2797 0.6975 0.3516  37   1.7917   1026.2642
AAPL                    买入持有 0.2888 -0.3852 1.0168 0.7497   1      NaN      0.0000
 BTC    海龟（原版：每单位 1%，最多 4 个） 0.3038 -0.2278 1.3221 1.3337  70   2.6989  53918.9576
 BTC 海龟（和主线同样的风险预算：2.5% × 4） 0.4444 -0.4361 1.2311 1.0191  69   2.7759 213025.6608
 BTC                   主线 v4 0.2063 -0.3362 0.8577 0.6137  30   1.2769  30926.0862
 BTC                    买入持有 0.3794 -0.8319 0.8192 0.4561   1      NaN      0.0000
```

![对照](/images/trade-analysis/31/compare.png)

| 标的 | 策略 | 年化 | 最大回撤 | 夏普 | 卡玛 | 笔数 | **逐笔 t 值** |
|---|---|---|---|---|---|---|---|
| SPY | 海龟（原版） | 4.59% | −17.35% | 0.670 | 0.265 | 67 | **2.21** |
| SPY | 海龟（同风险） | 6.79% | −11.64% | 0.819 | 0.583 | 64 | **2.90** |
| SPY | 主线 v4 | 2.91% | −12.42% | 0.418 | 0.234 | 39 | 1.12 |
| SPY | 买入持有 | **13.46%** | −34.10% | 0.791 | 0.395 | — | — |
| AAPL | 海龟（原版） | 16.82% | −11.94% | 1.255 | 1.409 | 59 | **3.48** |
| AAPL | 海龟（同风险） | 22.28% | −15.19% | **1.368** | **1.467** | 56 | **3.66** |
| AAPL | 主线 v4 | 9.83% | −27.97% | 0.698 | 0.352 | 37 | 1.79 |
| AAPL | 买入持有 | **28.88%** | −38.52% | 1.017 | 0.750 | — | — |
| BTC | 海龟（原版） | 30.38% | **−22.78%** | **1.322** | **1.334** | 70 | **2.70** |
| BTC | 海龟（同风险） | **44.44%** | −43.61% | 1.231 | 1.019 | 69 | 2.78 |
| BTC | 主线 v4 | 20.63% | −33.62% | 0.858 | 0.614 | 30 | 1.28 |
| BTC | 买入持有 | 37.94% | −83.19% | 0.819 | 0.456 | — | — |

三个结论：

**一，海龟在三个标的上全面优于主线 v4。**年化、夏普、卡玛、逐笔 t 值，没有一项输。主线 v4 的入场条件（金叉 + 创 20 日新高）其实就是一个更保守的突破，但它的出场靠死叉——**一个滞后得多的信号**，于是它把利润吐回去的速度慢得多。

**二，海龟是这门课里第一条逐笔 t 值全部超过 2 的策略。**2.21 / 3.48 / 2.70（原版）和 2.90 / 3.66 / 2.78（同风险），而主线 v4 是 1.12 / 1.79 / 1.28。第 29 篇那条线，它过了。

**三，它在年化上跑不赢买入持有，但在风险上赢很多。**SPY 4.59% 对 13.46%、AAPL 22.28% 对 28.88%，只有 BTC 的同风险版本（44.44%）超过了买入持有的 37.94%。但看回撤：BTC 上 −22.78% 对 −83.19%，卡玛 1.334 对 0.456。

> 第 30 篇结尾留了一个问题：**均线交叉在 BTC 上怎么挑参数都赢不了买入持有。**这一篇的答案是：**换一条规则可以，但赢的方式不是「赚得更多」，是「用四分之一的回撤赚到差不多的钱」。**如果你愿意为此加一点杠杆（把风险预算从 4% 提到 10%），年化就超过去了——代价是回撤回到 −43.61%。这是第 26 篇那条抛物线的又一次现身：**收益和回撤是同一个旋钮的两端。**

---

## 十六、小检查

1. 「20 日通道突破」可以在当根成交，「收盘价创 20 日新高」只能下一根成交。这两句话的区别在哪里？
2. 一套趋势跟随系统的胜率是 33%、中位数一笔是 −1R。有人说「胜率这么低肯定不行」。你会怎么回答？
3. 你发现某次突破「量能不配合」，决定跳过这一次。这个决定有什么风险？
4. 海龟在 SPY 上做空那一半九年亏了 15%。这说明「趋势跟随不适用于股指」吗？
5. 蒙特卡洛对照里，假数据的期望日收益率和真实数据一样，可是同一套规则在假数据上亏钱。为什么？

---

## 十七、常见误用

**挑着做。**第 8.1 节：拿掉最赚的十笔（不到 15% 的交易），SPY 和 BTC 上九年收益变成负数。**「这次看着不对」是这套系统最贵的一句话**——你要么全做，要么别做。

**看到胜率 33% 就否定。**第八节：胜率和盈亏比是一枚硬币的两面。2N 止损把亏损那一头钉死在 1.6R 以下，赚的那一头没有上限（BTC 上最大一笔 76.44R）。**该看的是期望值和偏度，不是胜率。**

**给它加固定止盈。**第 23 篇量过，这一篇的收益分布再次说明为什么：收益全部集中在极少数几笔的尾巴上，而固定止盈**专门砍掉尾巴**。

**把加仓当成普适的改进。**第十节：BTC 上加仓把回撤砍掉三分之一，SPY 上反而让年化从 7.26% 掉到 4.68%。它是一个和波动结构有关的选择。

**照搬多空对称。**第十一节：SPY 和 AAPL 上做空那一半是纯亏损（胜率 10%–12%）。原型不等于配方。

**在震荡市里怪策略。**第十二节：BTC 上低效率比环境进场的 24 笔九年合计只有 13.8R。**趋势跟随在震荡市里亏钱不是失效，那正是它买保险付的权利金。**

**用「整个参数族都赚钱」当成有效的证明。**第 30 篇的实验三刚刚演示过反例：那条策略 1,575 组里 51.5% 的夏普都大于 1，照样样本外跑输买入持有。**真正的证据是蒙特卡洛对照**（第 14.2 节：0/300）和**逐笔 t 值**（第十五节：全部超过 2）。

**拿年化去比买入持有，然后得出「跑输了所以没用」。**第十五节：海龟在 BTC 上的年化低于买入持有，回撤只有它的四分之一。**两条曲线要放在同一个风险水平上比。**

---

## 十八、小结

- **趋势跟随的全部内容是一句话**：价格创新高就买，跌破就走。它唯一的假设是「大的行情会持续得比大多数人愿意相信的更久」，而这个假设**大部分时候是错的**。
- **假突破**：最宽松的口径下，20 日通道的突破有 28.85%（SPY）/ 31.07%（AAPL）/ **41.74%**（BTC）二十根之后还在突破价下方；真的按规则交易（带 2N 止损），亏钱的比例升到 55%–67%。**止损把假突破的代价从「跌 9%」压成「亏 1R」。**
- **收益结构**：胜率 44.8% / 45.8% / **32.9%**，盈亏比 2.61 / 5.16 / **10.06**，**三个标的的中位数一笔全是负的**（BTC 正好 −1.00R），偏度 1.17 / 1.20 / **3.37**。
- **集中度**：拿掉最赚的十笔（约 15% 的交易），SPY 剩 **−17.5%**、BTC 剩 **−2.3%**——九年收益归零。所以**不能挑着做**。
- **凸性**：只做多长得像一份看涨期权；多空都做，BTC 上左边那一头抬起来（20 根跌 16% 的那一组策略中位 +1.45%），是一条真正的微笑曲线。SPY 和 AAPL 上抬不起来。
- **金字塔加仓**：总风险固定在 4% 时，BTC 上年化几乎不变（32.12% → 31.60%）而回撤砍掉三分之一（−34.66% → **−21.56%**）；SPY 上反而更差。
- **做空那一半**：SPY −15.02%、AAPL −14.79%、BTC +4.98%。在长期向上的标的上做空趋势是逆着漂移下注。
- **检验**：1983 年那组 (20,10) 在 BTC 上排 1/33、落差只有 +0.17（不是尖峰是高地）；33 组参数**没有一组亏钱**；每年重挑参数三个标的**全部跑输固定参数**；**蒙特卡洛把趋势拆掉之后，300 条假数据里 0 条比真实的好**。
- **对照**：海龟在三个标的上全面优于主线 v4，而且是**这门课第一条逐笔 t 值全部超过 2 的策略**（2.21 / 3.48 / 2.70）。它在年化上跑不赢买入持有，但 BTC 上用 −22.78% 的回撤换来了 30.38%（买入持有是 −83.19% 换 37.94%）。
- 新模块 `talab.trend` 14 个测试，全课共 **322 个**（不装 TA-Lib 时 290 通过 + 32 跳过）。

---

## 十九、完整代码与测试

### `talab/trend.py`

```python
"""talab.trend：趋势跟随与突破。第 31 篇。

第六部分讲完了怎么检验，这一篇开始讲**被检验的东西**：一类真实存在、公开了四十年、
到现在还有人靠它管钱的策略原型。

趋势跟随的全部内容可以写成一句话：**价格创新高就买，跌破就走。**
它没有预测，没有估值，没有「这次不一样」。它唯一的假设是——

> 大的行情会持续得比大多数人愿意相信的更久，而小的行情会来回震荡。

这个假设**大部分时候是错的**（第 31 篇实测：七成的突破是假的），
但它错的时候亏得少、对的时候赚得多。这个模块就是把这句话拆成可以测量的零件：

1. **通道与突破**：`donchian`、`breakouts`、`follow_through`
2. **海龟系统**：`TurtlePlan` + `turtle`（含 2N 止损、按 N 定仓位、金字塔加仓）
3. **收益结构**：`r_profile`、`contribution`、`convexity`

⚠️ **通道突破是这门课里唯一可以「当根成交」的信号**：通道那条线是用**前面几根**的
最高价算出来的，开盘之前就已经画好了，价格在这一根里碰到它是一件**当时就能看见**的事。
这和第 27 篇「收盘算出来的信号只能下一根成交」不矛盾——那条规矩管的是用到**当根收盘价**
的信号（均线、RSI、收盘价创新高）。判据始终是同一句：**这个数，在那一刻能不能算出来。**
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from talab.backtest import Account

SIDES = ("long", "short", "both")
FILLS = ("touch", "next_open")


# ---------------------------------------------------------------------------
# 一、唐奇安通道与突破
# ---------------------------------------------------------------------------

def donchian(high: pd.Series, low: pd.Series, n: int = 20) -> pd.DataFrame:
    """唐奇安通道：过去 n 根的最高价、最低价，以及两者的中点。

    ⚠️ 两条轨都 `shift(1)`：**第 i 根上用的是第 i−1 根为止的最高价**。
    不推迟的话，「创 20 日新高」这个条件会永远成立（今天的最高价当然是包含今天的最高价之一）。
    """
    return pd.DataFrame({
        "上轨": high.rolling(n).max().shift(1),
        "下轨": low.rolling(n).min().shift(1),
    }).assign(中轨=lambda t: (t["上轨"] + t["下轨"]) / 2)


def breakouts(df: pd.DataFrame, n: int = 20, horizon: int = 20) -> pd.DataFrame:
    """每一次**向上**突破 n 日通道：突破时的价格，以及之后 horizon 根里发生了什么。

    连续多根都在通道上方只算**一次**突破（第一次算，后面的不算），
    否则一段大趋势会被数成几十次「突破」，假突破的比例就被稀释成假的。
    """
    channel = donchian(df["high"], df["low"], n)
    high, low, close = (df[x].to_numpy(float) for x in ["high", "low", "close"])
    upper = channel["上轨"].to_numpy()
    rows, armed = [], True
    for i in range(len(close)):
        if np.isnan(upper[i]):
            continue
        if high[i] > upper[i]:
            if armed:
                ahead = close[i + 1:i + 1 + horizon]
                worst = low[i + 1:i + 1 + horizon]
                rows.append({"时间": df.index[i], "突破价": upper[i], "收盘": close[i],
                             "之后最高收盘": float(ahead.max()) if len(ahead) else np.nan,
                             "之后最低价": float(worst.min()) if len(worst) else np.nan,
                             f"{horizon} 根后": float(ahead[-1]) if len(ahead) == horizon else np.nan})
                armed = False
        elif close[i] < upper[i]:
            armed = True                                  # 回到通道里面，下一次才算新的突破
    out = pd.DataFrame(rows)
    if len(out):
        out["之后涨幅"] = out[f"{horizon} 根后"] / out["突破价"] - 1
        out["最大顺势"] = out["之后最高收盘"] / out["突破价"] - 1
        out["最大逆势"] = out["之后最低价"] / out["突破价"] - 1
    return out


def follow_through(table: pd.DataFrame, threshold: float = 0.0) -> pd.Series:
    """一批突破里，有多少是「走出去了」的，有多少是假的。

    `threshold` 是判定标准（`之后涨幅` 要超过它才算真）。默认 0：**只要没回到突破价以下就算真**——
    这已经是最宽松的口径了，而第 31 篇实测下来仍然只有三成多能过。
    """
    real = table["之后涨幅"] > threshold
    return pd.Series({
        "突破次数": float(len(table)), "走出去的": float(real.sum()),
        "假突破比例": float((~real).mean()),
        "真的那些平均涨": float(table.loc[real, "之后涨幅"].mean()) if real.any() else np.nan,
        "假的那些平均跌": float(table.loc[~real, "之后涨幅"].mean()) if (~real).any() else np.nan,
        "全部平均": float(table["之后涨幅"].mean()),
        "最大顺势中位": float(table["最大顺势"].median()),
        "最大逆势中位": float(table["最大逆势"].median()),
    })


# ---------------------------------------------------------------------------
# 二、海龟系统
# ---------------------------------------------------------------------------

@dataclass
class TurtlePlan:
    """海龟交易法则，1983 年那一版的核心设定。

    原版有两套系统：系统一是 20 日突破进、10 日突破出，系统二是 55 日进、20 日出。
    这里用同一个 dataclass 表示，改两个数字就换系统。
    """
    entry: int = 20                        # 进场：突破几日通道
    exit: int = 10                         # 出场：反向几日通道
    atr_period: int = 20                   # N（原版就叫 N，其实是 20 日 ATR）
    stop_atr: float = 2.0                  # 止损放在进场价外几个 N
    risk: float = 0.01                     # 一个「单位」冒账户的百分之几
    max_units: int = 4                     # 最多加到几个单位
    add_atr: float = 0.5                   # 每走几个 N 加一个单位
    side: str = "long"                     # long / short / both
    fill: str = "touch"                    # touch：碰到通道就成交；next_open：等下一根开盘
    fee_rate: float = 0.0                  # 单边费率（第 28 篇）

    def __post_init__(self):
        if self.side not in SIDES:
            raise ValueError(f"side 只能是 {SIDES} 之一，收到 {self.side!r}")
        if self.fill not in FILLS:
            raise ValueError(f"fill 只能是 {FILLS} 之一，收到 {self.fill!r}")
        if self.entry < 2 or self.exit < 2 or self.atr_period < 2:
            raise ValueError("三个窗口都要至少是 2")
        if self.max_units < 1:
            raise ValueError("至少要允许一个单位")

    def describe(self) -> pd.Series:
        return pd.Series({
            "进场": f"突破 {self.entry} 日通道",
            "出场": f"反向突破 {self.exit} 日通道",
            "N": f"{self.atr_period} 日 ATR",
            "初始止损": f"{self.stop_atr} 个 N",
            "一个单位的风险": f"账户的 {self.risk:.1%}",
            "加仓": f"每走 {self.add_atr} 个 N 加一个单位，最多 {self.max_units} 个",
            "方向": {"long": "只做多", "short": "只做空", "both": "多空都做"}[self.side],
            "成交": {"touch": "碰到通道就成交", "next_open": "等下一根开盘"}[self.fill],
        })


def turtle(df: pd.DataFrame, plan: TurtlePlan | None = None, equity: float = 100_000.0) -> dict:
    """按海龟法则跑一遍历史。

    每一根 K 线上按固定顺序做五件事（和第 27 篇的引擎同一套规矩）：

    0. **补成交**：`fill="next_open"` 时，上一根定下来的动作用这一根的开盘价成交
    1. **出场**：先看止损，再看反向通道；两个都碰到时按**先止损**算（悲观口径）
    2. **加仓**：价格又顺走了 `add_atr` 个 N 就加一个单位，并把**全部**止损上移
    3. **估值**：按收盘价记权益
    4. **进场**：空仓时，价格碰到 `entry` 日通道就进

    通道线来自前面几根，所以 1、2、4 默认在**当根**成交（见模块开头那条 ⚠️）。
    把 `fill` 换成 `"next_open"` 就能量出「当根成交」这个假设值多少钱——
    如果它值很多，那说明这条策略靠的是那一瞬间的价格，不是趋势。
    返回资金曲线、逐笔交易（一整个仓位算一笔，带 R 倍数）、每一次加仓的明细。
    """
    from talab import indicators as I

    plan = plan or TurtlePlan()
    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    n_value = I.atr(df["high"], df["low"], df["close"], plan.atr_period).shift(1).to_numpy()
    enter = donchian(df["high"], df["low"], plan.entry)
    leave = donchian(df["high"], df["low"], plan.exit)
    up_in, down_in = enter["上轨"].to_numpy(), enter["下轨"].to_numpy()
    up_out, down_out = leave["上轨"].to_numpy(), leave["下轨"].to_numpy()

    # ⚠️ 空头的数量只记在 `units` 里，`account.shares` 全程是 0——
    # 所以权益一律用下面的 `position_value` 算，不要用 `account.equity`。
    account = Account(cash=float(equity))
    curve, trades, adds, error = [], [], [], 0.0
    side = 0                                   # +1 做多，−1 做空，0 空仓
    units: list[tuple[float, float]] = []      # 每个单位的（成交价，数量）
    stop = last_price = risk_amount = np.nan
    opened_at = -1

    def position_value(price: float) -> float:
        """权益：做多是「现金 + 持仓市值」，做空是「现金 − 买回来要花的钱」。

        ⚠️ 做空时卖出所得已经记在现金里了，所以**不要再减一次借来的钱**——
        第一版就是这么写的，结果最大回撤算出 −106%（权益跑到 0 以下）。
        「回撤超过 100%」永远是记账错了，不是策略真的这么惨。
        """
        held = sum(q for _, q in units)
        return account.cash + side * held * price

    def close_all(i: int, price: float, reason: str) -> None:
        nonlocal side, units, stop, opened_at
        held = sum(q for _, q in units)
        cost = sum(p * q for p, q in units)
        if side > 0:
            account.sell(price, held, plan.fee_rate)
            profit = price * held - cost - abs(price * held) * plan.fee_rate
        else:
            account.cash -= price * held * (1 + plan.fee_rate)      # 买回来平掉空头
            account.fees += price * held * plan.fee_rate
            profit = cost - price * held - abs(price * held) * plan.fee_rate
        trades.append({"进场日": df.index[opened_at], "方向": "多" if side > 0 else "空",
                       "第一个单位的价": units[0][0], "平均价": cost / held if held else np.nan,
                       "单位数": len(units), "出场日": df.index[i], "出场价": price,
                       "原因": reason, "盈亏": profit, "R": profit / risk_amount,
                       "根数": i - opened_at})
        side, units, stop, opened_at = 0, [], np.nan, -1

    def open_unit(i: int, price: float, direction: int) -> bool:
        nonlocal side, stop, last_price, risk_amount
        step = plan.stop_atr * n_value[i]
        want = position_value(price) * plan.risk / step          # 一个单位：冒账户的 risk
        if direction > 0:
            shares = min(want, account.affordable(price, plan.fee_rate))
        else:
            shares = min(want, position_value(price) / (price * (1 + plan.fee_rate)))
        if shares <= 1e-12:
            return False                                         # 买不起了：别再往下加
        if direction > 0:
            account.buy(price, shares, plan.fee_rate)
        else:
            account.cash += price * shares * (1 - plan.fee_rate)
            account.fees += price * shares * plan.fee_rate
        if not units:
            side = direction
            risk_amount = shares * step                          # 1R = 第一个单位的初始风险
        units.append((price, shares))
        last_price = price
        stop = price - direction * step                          # 加仓之后全部止损跟着走
        adds.append({"时间": df.index[i], "第几个单位": len(units), "成交价": price,
                     "数量": shares, "止损移到": stop})
        return True

    first = int(np.argmax(~np.isnan(n_value) & ~np.isnan(up_in) & ~np.isnan(down_in)))
    pending: tuple | None = None               # fill="next_open" 时挂着的动作
    for i in range(first, len(c)):
        # 第 0 步：上一根定下来的动作，用这一根的开盘价成交
        if pending is not None:
            what, extra = pending
            pending = None
            if what == "close" and side:
                close_all(i, o[i], extra)
            elif what == "add" and side and len(units) < plan.max_units:
                open_unit(i, o[i], side)
            elif what == "open" and not side:
                opened_at = i
                open_unit(i, o[i], extra)

        # 第 1 步：出场
        later = plan.fill == "next_open"
        if side > 0:
            if l[i] <= stop:
                pending = ("close", "止损") if later else pending
                if not later:
                    close_all(i, min(o[i], stop), "止损")
            elif l[i] <= down_out[i]:
                pending = ("close", "通道出场") if later else pending
                if not later:
                    close_all(i, min(o[i], down_out[i]), "通道出场")
        elif side < 0:
            if h[i] >= stop:
                pending = ("close", "止损") if later else pending
                if not later:
                    close_all(i, max(o[i], stop), "止损")
            elif h[i] >= up_out[i]:
                pending = ("close", "通道出场") if later else pending
                if not later:
                    close_all(i, max(o[i], up_out[i]), "通道出场")

        # 第 2 步：加仓
        while side and pending is None and len(units) < plan.max_units:
            level = last_price + side * plan.add_atr * n_value[i]
            if side > 0 and h[i] >= level:
                if later:
                    pending = ("add", None)
                    break
                if not open_unit(i, max(o[i], level), 1):
                    break
            elif side < 0 and l[i] <= level:
                if later:
                    pending = ("add", None)
                    break
                if not open_unit(i, min(o[i], level), -1):
                    break
            else:
                break

        # 第 3 步：估值
        value = position_value(c[i])
        held = sum(q for _, q in units)
        error = max(error, abs(account.cash + side * held * c[i] - value))
        curve.append(value)

        # 第 4 步：进场
        if not side and pending is None and n_value[i] > 0:
            if plan.side in ("long", "both") and h[i] > up_in[i]:
                if later:
                    pending = ("open", 1)
                else:
                    opened_at = i
                    open_unit(i, max(o[i], up_in[i]), 1)
            elif plan.side in ("short", "both") and l[i] < down_in[i]:
                if later:
                    pending = ("open", -1)
                else:
                    opened_at = i
                    open_unit(i, min(o[i], down_in[i]), -1)

    if side:                                                     # 最后一根还拿着
        close_all(len(c) - 1, c[-1], "未平仓")
    index = df.index[first:]
    columns = ["进场日", "方向", "第一个单位的价", "平均价", "单位数", "出场日", "出场价",
               "原因", "盈亏", "R", "根数"]
    return {"资金曲线": pd.Series(curve, index=index, name="权益"),
            "交易": pd.DataFrame(trades, columns=columns),
            "加仓": pd.DataFrame(adds, columns=["时间", "第几个单位", "成交价", "数量", "止损移到"]),
            "手续费合计": account.fees, "记账误差": error,
            "权益最低点": float(min(curve)) if curve else np.nan}


# ---------------------------------------------------------------------------
# 三、收益结构
# ---------------------------------------------------------------------------

def r_profile(r) -> pd.Series:
    """一串 R 倍数的形状：胜率、盈亏比、期望，以及**偏度**。

    趋势跟随的招牌是「胜率低、盈亏比高、偏度为正」。
    第 23 篇的 `risk.expectancy` 给的是前两项，这里补上尾巴那一头——
    **正偏度的意思是「亏损可以预料，盈利不可以」**，而策略的全部收益都藏在那个不可预料的尾巴里。
    """
    r = pd.Series(r).dropna().astype(float)
    wins, losses = r[r > 0], r[r <= 0]
    return pd.Series({
        "笔数": float(len(r)), "胜率": float((r > 0).mean()),
        "平均盈利 R": float(wins.mean()) if len(wins) else 0.0,
        "平均亏损 R": float(-losses.mean()) if len(losses) else 0.0,
        "盈亏比": float(wins.mean() / -losses.mean()) if len(losses) and losses.mean() else np.inf,
        "期望 R": float(r.mean()), "中位 R": float(r.median()),
        "偏度": float(r.skew()), "最大一笔 R": float(r.max()), "最差一笔 R": float(r.min()),
        "合计 R": float(r.sum()),
    })


def contribution(r, tops=(1, 3, 5, 10)) -> pd.DataFrame:
    """把最赚钱的几笔拿掉，还剩多少。

    这张表回答一个很不舒服的问题：**这条策略的收益，有多少集中在极少数几笔上？**
    集中度高不是缺点，是趋势跟随的**定义**——但你必须知道它有多高，
    因为那意味着「错过那几笔」和「策略失效」在账户上是同一件事。
    """
    r = pd.Series(r).dropna().astype(float).sort_values(ascending=False)
    total = r.sum()
    rows = [{"拿掉最赚的几笔": 0, "剩下多少 R": total, "占原来的": 1.0, "占总笔数": 0.0}]
    for n in tops:
        if n >= len(r):
            break
        left = total - r.iloc[:n].sum()
        rows.append({"拿掉最赚的几笔": n, "剩下多少 R": left, "占原来的": left / total if total else np.nan,
                     "占总笔数": n / len(r)})
    return pd.DataFrame(rows)


def convexity(strategy: pd.Series, market: pd.Series, buckets: int = 5,
              window: int = 20) -> pd.DataFrame:
    """凸性表：把市场按 `window` 根的涨跌分成几组，看策略在每一组里赚多少。

    趋势跟随的收益应该是一条**微笑曲线**——市场大涨时赚、市场大跌时也赚（或者至少不怎么亏）、
    市场不涨不跌时小亏。这个形状和「买了一份跨式期权」是一回事，
    小亏就是权利金。第 32 篇的均值回归会给出正好相反的形状（凹性）。
    """
    if not 0 < buckets <= 20:
        raise ValueError("buckets 要在 1 和 20 之间")
    both = pd.concat([strategy.rename("策略"), market.rename("市场")], axis=1).dropna()
    rolled = pd.DataFrame({
        "策略": (1 + both["策略"]).rolling(window).apply(np.prod, raw=True) - 1,
        "市场": (1 + both["市场"]).rolling(window).apply(np.prod, raw=True) - 1,
    }).dropna()
    groups = pd.qcut(rolled["市场"], buckets, labels=False, duplicates="drop")
    out = rolled.groupby(groups).agg(根数=("市场", "size"), 市场中位=("市场", "median"),
                                     策略中位=("策略", "median"), 策略平均=("策略", "mean"),
                                     策略赚钱的比例=("策略", lambda x: float((x > 0).mean())))
    out.index = [f"第 {i + 1} 组" for i in range(len(out))]
    out.index.name = f"按市场 {window} 根涨跌分组"
    return out
```

### `talab/tests/test_trend.py`

```python
"""talab.trend 的测试（第 31 篇）。全部用手工构造的价格，每个数都能自己算一遍。"""
import numpy as np
import pandas as pd
import pytest

from talab import trend as T


def frame(closes, spread: float = 0.0) -> pd.DataFrame:
    """把一串收盘价变成 K 线：开盘 = 收盘，最高/最低按 spread 往两边撑开。"""
    close = np.asarray(closes, dtype=float)
    return pd.DataFrame({"open": close, "high": close * (1 + spread),
                         "low": close * (1 - spread), "close": close},
                        index=pd.date_range("2024-01-01", periods=len(close), freq="D"))


def ramp(flat: int = 30, up: int = 40, base: float = 100.0, step: float = 2.0) -> pd.DataFrame:
    """先横盘（锯齿），再一路上涨——足够海龟进场、加满四个单位、再被通道赶出来。"""
    noise = [base + (1 if i % 2 else -1) for i in range(flat)]
    rise = [base + step * (i + 1) for i in range(up)]
    fall = [rise[-1] - step * 3 * (i + 1) for i in range(15)]
    return frame(noise + rise + fall)


def test_donchian_shifts_by_one_bar():
    """不推迟一根，「创 n 日新高」会永远成立——今天的最高价当然是包含今天在内的最高价之一。"""
    bars = frame([1, 2, 3, 4, 5])
    channel = T.donchian(bars["high"], bars["low"], 3)
    assert np.isnan(channel["上轨"].iloc[2])                 # 前三根凑不齐「前 3 根」
    assert channel["上轨"].iloc[3] == 3 and channel["下轨"].iloc[3] == 1
    assert channel["中轨"].iloc[3] == 2
    assert (bars["high"] > channel["上轨"]).iloc[3:].all()   # 一路新高：确实每根都突破
    wrong = bars["high"].rolling(3).max()                    # 忘了 shift 的写法
    assert not (bars["high"] > wrong).iloc[3:].any()         # 永远不成立，信号一个都没有


def test_breakouts_counts_one_per_episode():
    """连着十根都在通道上方只算一次突破，否则一段趋势会被数成十次「突破」。"""
    bars = frame([10] * 5 + [11, 12, 13, 14, 15] + [9] * 5 + [16, 17])
    table = T.breakouts(bars, n=3, horizon=2)
    assert len(table) == 2                                   # 涨那一段一次，最后拉起来又一次
    assert table["时间"].iloc[0] == bars.index[5]
    assert table["突破价"].iloc[0] == 10


def test_breakouts_measures_what_happened_after():
    bars = frame([10] * 5 + [12, 14, 11])
    table = T.breakouts(bars, n=3, horizon=2)
    row = table.iloc[0]
    assert row["突破价"] == 10 and row["收盘"] == 12
    assert row["之后涨幅"] == pytest.approx(11 / 10 - 1)      # 两根之后收在 11
    assert row["最大顺势"] == pytest.approx(14 / 10 - 1)      # 中间最高收到 14
    assert row["最大逆势"] == pytest.approx(11 / 10 - 1)


def test_follow_through_splits_real_from_fake():
    table = pd.DataFrame({"之后涨幅": [0.1, -0.05, 0.2, -0.02],
                          "最大顺势": [0.3, 0.01, 0.25, 0.0],
                          "最大逆势": [-0.01, -0.08, -0.02, -0.05]})
    out = T.follow_through(table)
    assert out["突破次数"] == 4 and out["走出去的"] == 2
    assert out["假突破比例"] == pytest.approx(0.5)
    assert out["真的那些平均涨"] == pytest.approx(0.15)
    assert out["假的那些平均跌"] == pytest.approx(-0.035)
    assert out["全部平均"] == pytest.approx(0.0575)


def test_turtle_plan_validates_and_describes():
    text = T.TurtlePlan().describe()
    assert text["进场"] == "突破 20 日通道" and text["初始止损"] == "2.0 个 N"
    assert T.TurtlePlan(entry=55, exit=20).describe()["出场"] == "反向突破 20 日通道"
    for bad in [dict(side="随便"), dict(fill="随便"), dict(entry=1), dict(max_units=0)]:
        with pytest.raises(ValueError):
            T.TurtlePlan(**bad)


def test_turtle_books_balance_exactly():
    """现金 + 持仓 × 价格 = 权益，全程误差必须是 0（第 27 篇那条规矩）。"""
    result = T.turtle(ramp(), T.TurtlePlan(atr_period=5, entry=10, exit=5))
    assert result["记账误差"] == 0.0
    assert result["权益最低点"] > 0                          # 权益永远不该跌到 0 以下
    assert len(result["交易"]) >= 1


def test_turtle_enters_at_the_channel_and_stops_two_n_away():
    """止损正好放在 2 个 N 之外，被打掉的那一笔正好是 −1R。

    ⚠️ 横盘那一段要用锯齿而不是一条直线：**真实波幅全是 0 的话 N 也是 0**，
    除不了，海龟一笔都不会开——这是写这类测试时最容易踩的坑。
    """
    zigzag = [100 + (1 if i % 2 else -1) for i in range(14)]
    bars = frame(zigzag + [108, 60])                         # 锯齿 → 跳上去 → 砸下来
    plan = T.TurtlePlan(entry=10, exit=5, atr_period=5, stop_atr=2.0, max_units=1, risk=0.01)
    result = T.turtle(bars, plan)
    trade = result["交易"].iloc[0]
    add = result["加仓"].iloc[0]
    n = (trade["第一个单位的价"] - add["止损移到"]) / plan.stop_atr
    assert trade["第一个单位的价"] == pytest.approx(108)     # 开盘就跳过了通道，只能按开盘价成交
    assert add["止损移到"] == pytest.approx(trade["第一个单位的价"] - 2 * n)
    assert trade["原因"] == "止损"
    assert trade["R"] < -1.0                                 # 跳空跳过了止损：亏得比 1R 还多


def test_turtle_pyramids_and_walks_the_stop_up():
    result = T.turtle(ramp(), T.TurtlePlan(atr_period=5, entry=10, exit=5, max_units=4))
    adds = result["加仓"]
    first = adds[adds["第几个单位"] == 1].index[0]
    block = adds.loc[first:first + 3]
    assert list(block["第几个单位"]) == [1, 2, 3, 4]         # 最多加到四个
    assert block["成交价"].is_monotonic_increasing           # 每一个单位都买得更贵
    assert block["止损移到"].is_monotonic_increasing         # 止损跟着往上走
    assert (adds["第几个单位"] <= 4).all()


def test_turtle_max_units_changes_the_size_not_the_signal():
    """加仓只改仓位大小，不改进场出场的时点——笔数和进场日应该一模一样。"""
    bars = ramp()
    one = T.turtle(bars, T.TurtlePlan(atr_period=5, entry=10, exit=5, max_units=1))["交易"]
    four = T.turtle(bars, T.TurtlePlan(atr_period=5, entry=10, exit=5, max_units=4))["交易"]
    assert list(one["进场日"]) == list(four["进场日"])
    assert (four["单位数"] >= one["单位数"]).all()
    assert four["R"].sum() > one["R"].sum()                  # 涨上去的那一段，加仓赚得更多


def test_turtle_next_open_fills_one_bar_later():
    zigzag = frame([100 + (1 if i % 2 else -1) for i in range(14)], spread=0.02)
    assert float(zigzag["high"].iloc[4:14].max()) == pytest.approx(103.02)   # 10 日通道上轨
    # 第 15 根：开在通道下方 102，盘中穿上去；第 16 根直接开在 107
    extra = pd.DataFrame({"open": [102.0, 107.0, 110.0], "high": [106.0, 111.0, 114.0],
                          "low": [101.0, 106.0, 109.0], "close": [105.0, 110.0, 113.0]},
                         index=pd.date_range(zigzag.index[-1] + pd.Timedelta(days=1), periods=3))
    bars = pd.concat([zigzag, extra])
    common = dict(entry=10, exit=5, atr_period=5, max_units=1)
    touch = T.turtle(bars, T.TurtlePlan(fill="touch", **common))["交易"].iloc[0]
    later = T.turtle(bars, T.TurtlePlan(fill="next_open", **common))["交易"].iloc[0]
    assert touch["第一个单位的价"] == pytest.approx(103.02)       # 就在通道那条线上成交
    assert later["进场日"] == touch["进场日"] + pd.Timedelta(days=1)
    assert later["第一个单位的价"] == pytest.approx(107.0)        # 等一根，开盘已经 107 了


def test_turtle_short_side_is_the_mirror_image():
    falling = ramp()
    mirrored = falling.copy()
    top = float(falling["high"].max()) + 10
    mirrored["open"], mirrored["close"] = top - falling["open"], top - falling["close"]
    mirrored["high"], mirrored["low"] = top - falling["low"], top - falling["high"]
    plan = dict(atr_period=5, entry=10, exit=5)
    up = T.turtle(falling, T.TurtlePlan(side="long", **plan))
    down = T.turtle(mirrored, T.TurtlePlan(side="short", **plan))
    assert len(down["交易"]) == len(up["交易"])
    assert down["记账误差"] == 0.0
    assert down["交易"]["R"].sum() > 0                       # 镜像的下跌里，做空同样赚钱


def test_r_profile_matches_hand_arithmetic():
    out = T.r_profile([-1, -1, -1, 3, 5])
    assert out["笔数"] == 5 and out["胜率"] == pytest.approx(0.4)
    assert out["平均盈利 R"] == pytest.approx(4.0)
    assert out["平均亏损 R"] == pytest.approx(1.0)
    assert out["盈亏比"] == pytest.approx(4.0)
    assert out["期望 R"] == pytest.approx(1.0)
    assert out["中位 R"] == pytest.approx(-1.0)              # 典型的一笔是亏的
    assert out["合计 R"] == pytest.approx(5.0)
    assert out["偏度"] > 0                                   # 正偏：亏损可预料，盈利不可


def test_contribution_shows_how_concentrated_the_profit_is():
    out = T.contribution([-1, -1, -1, -1, 10], tops=(1, 2))
    assert out.loc[0, "剩下多少 R"] == pytest.approx(6.0)
    assert out.loc[1, "拿掉最赚的几笔"] == 1
    assert out.loc[1, "剩下多少 R"] == pytest.approx(-4.0)   # 拿掉那一笔就亏钱了
    assert out.loc[1, "占原来的"] < 0
    assert out.loc[1, "占总笔数"] == pytest.approx(0.2)


def test_convexity_finds_the_smile():
    """造一个真的趋势跟随者：顺着最近 20 根的方向做。它该在两头赚、中间亏。"""
    rng = np.random.default_rng(31)
    drift = np.concatenate([[0.005] * 200, [-0.005] * 200,
                            [0.005 if i % 2 else -0.005 for i in range(200)]])
    market = pd.Series(drift + rng.normal(0, 0.004, 600),   # 加一点噪声，免得分位数挤在一起
                       index=pd.date_range("2022-01-01", periods=600))
    direction = np.sign(market.rolling(20).sum().shift(1)).fillna(0.0)
    strategy = market * direction - 0.0005                   # 顺势做，外加一点点摩擦
    out = T.convexity(strategy, market, buckets=5, window=20)
    assert len(out) == 5 and out["根数"].sum() == 600 - 19
    assert out["市场中位"].is_monotonic_increasing           # 分组本身按市场涨跌排好了
    assert out["策略中位"].iloc[0] > out["策略中位"].iloc[2]  # 市场大跌那一组：做空赚钱
    assert out["策略中位"].iloc[-1] > out["策略中位"].iloc[2]  # 市场大涨那一组：做多赚钱
    with pytest.raises(ValueError):
        T.convexity(strategy, market, buckets=0)
```

### 两个 venv 的测试结果

```text
322 passed in 1.16s
290 passed, 32 skipped in 1.14s
```

---

## 练习

1. 海龟原版系统一有一条这里没实现的规则：**上一次系统一的信号如果赚钱了，这一次就跳过**（跳过的那次用系统二 55 日通道接住）。把它加进 `TurtlePlan`，在三个标的上量一量它值多少。
2. 第六节量的是「等下一根开盘」。再加一种：**要求收盘价站上通道才算突破**（第 20 篇的收盘触发）。它会滤掉多少假突破，又会让你错过多少真的？
3. `convexity` 现在按 20 根的市场涨跌分组。换成按**第 11 篇的市场状态**（趋势 / 震荡 / 过渡）分组，图会变成什么样？
4. 第十节的加仓间距固定是 0.5 个 N。把它当成一个参数扫一遍（0.25 到 2.0），在三个标的上看回撤和年化的取舍曲线——SPY 上有没有一个间距能让加仓变成正贡献？
5. 把海龟搬到第 19 篇那 704 个永续合约上，一次持有成交额前 20 里发出信号的那些（等权）。组合的回撤会比单个标的浅多少？⚠️ 记得用第 28 篇的「当时的名单」，不是今天的。
6. 第十五节的对照里，主线 v4 输在出场太慢。把主线的出场从「死叉」换成「跌破 10 日通道下轨」，其余不变，它能追上海龟多少？
7. 写一个 `stress(df, plan, ...)`：把 K 线的最高最低价按一个比例往外撑（模拟更宽的日内波动），看这套系统的成绩对「盘中路径」有多敏感（第 27 篇那个最贵的假设）。

---

## 小检查答案

1. 区别在于**这个数什么时候能算出来**。通道上轨用的是**前面 20 根**的最高价，开盘之前就画好了，所以价格在这一根里碰到它是当时就看得见的事；而「收盘价创 20 日新高」要等**当根收盘**才知道，那时候这一根已经结束了，最早只能下一根成交。第六节还量了这个假设值多少钱：0 到 3.5 个百分点。
2. 胜率低是**设计的结果**，不是缺陷。2N 止损把每次亏损钉死在 1R 左右，代价就是很多最终会走出去的突破也被打掉了；换来的是赚的那一头没有上限（BTC 盈亏比 10.06、最大一笔 76.44R）。该看的是**期望值**（BTC +4.23R/笔）和**偏度**（+3.37），以及第 29 篇的**逐笔 t 值**（2.70）。一个反问：如果有人给你一套胜率 90% 的系统，你要问的第一句话是「亏的那 10% 一次亏多少」。
3. 风险是**你跳过的那一次，可能正是撑起九年收益的那几笔之一**。第 8.1 节：拿掉最赚的十笔（不到 15%），SPY 和 BTC 上九年收益变成负数。而在信号发出的那一刻，你手上没有任何能分辨真假的信息——第三节的分布宽得离谱，第一节那十次里七次是假的。**要么全做，要么别做。**
4. **不能这么说，它说的是「在长期向上的标的上，趋势跟随的做空那一半不成立」。**只做多的版本在 SPY 上是 +6.88%（同风险口径）、夏普 0.819，并不差。海龟的多空对称是为几十个期货品种的组合设计的——那些品种没有股票这样的长期漂移。**原型要按标的的性质裁剪，不能照搬。**
5. 因为**趋势跟随赚的不是漂移，是序列相关性**。块自助法保留了每一天的收益率分布和一个月内的波动率聚集，但把一个月以上的走势打散了；假市场照样涨，只是涨法变成没有方向的抖动。这套系统一多半时间空仓（在场比例 38%–54%），接不住这种涨法，还要一次次付止损的钱。这也正好说明**它的收益来源是什么**——把趋势拿掉，收益就没了。

---

第 32 篇讲**均值回归**，也就是趋势跟随的镜像。决策点是：SPY 连跌五天、偏离 20 日均线两个标准差，买不买？内容是布林带回归、RSI 回归、区间交易，以及它的收益结构——**高胜率、偶发的大额亏损、凹性**（和这一篇的微笑曲线正好反过来）。最后把两条策略放进同一个账户，看资金曲线会变成什么样。
