---
title: "第 18 篇：道氏理论与斐波那契"
date: 2026-09-17
weight: 18
tags: ["交易技术分析"]
draft: false
summary: "2025 年 3 月 14 日，SPY 从 2 月的高点回撤到整段涨幅的 61.8%，连着三天在那里停住，当天反弹 2.1%。这一篇先讲道氏理论的六条原则，它们大多已经在前面的篇目里变成了代码；再讲斐波那契比例从哪里来、回撤和扩展怎么画、起点和终点怎么选（换一种选法，61.8% 的价位能差出 7%）。动手部分把「回撤到某个比例之后停住没有」写成不看未来的检验，比较斐波那契比例和它左右的普通比例；再量一量事后画线的威力：随便挑起点和终点，一半以上的转折点都能找到一条「准确」的回撤位——换成平移过的普通比例也一样。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **本篇位置** | 第四部分「形态」的最后一篇。道氏理论把第 7、8、10 篇串起来；斐波那契用第 8 篇的 ZigZag 摆动点画线，检验方法沿用第 11 篇的「先碰到哪条线」和第 9 篇的打乱检验 |
| **用到的数据** | SPY、AAPL 日线（2016-09 至 2026-09）；BTCUSDT 现货日线，以及用 1 分钟线合成的 4 小时线和 1 小时线（2017-08 至 2026-08） |
| **动手** | `talab.patterns` 第三部分：回撤位、扩展位、摆动比例、回撤位的实时检验，附 5 个测试；统计回撤到斐波那契位和回撤到普通比例位之后的表现 |
| **读完你能** | 说出道氏理论六条原则各自对应课程里的哪个工具；画斐波那契回撤和扩展，并知道起点终点的选择会让价位移动多少；判断「某个比例特别灵」这类说法需要什么样的对照 |

---

## 一、先做一个决定

现在是 **2025 年 3 月 14 日美股收盘**。

SPY 从 2024 年 8 月 5 日收盘的 517.38，一路涨到 2025 年 2 月 19 日收盘的 612.93，涨了 18.47%。然后三周多跌了近 10%。

把这一段涨幅画上斐波那契回撤：

- 23.6%：590.38
- 38.2%：576.43
- 50%：565.16
- **61.8%：553.88**
- 78.6%：537.83

3 月 11 日最低 552.02，3 月 13 日最低 549.68，都刚好碰到 61.8% 附近，收盘都没有离开太远。今天，3 月 14 日，SPY 收在 **562.81**，比 61.8% 回撤位高 1.61%，当天涨了 2.1%。

![SPY 日线和斐波那契回撤位，2024-07 至 2025-03-14](/images/trade-analysis/18/decision.png)

```python
t = pd.Timestamp("2025-03-14")
known = spy.loc[:t]                                           # 只用决策当天收盘为止的数据
swings = X.zigzag(known["close"], 0.05)
print(swings.tail(3).to_string(index=False))
start, end = swings["price"].iloc[-2], swings["price"].iloc[-1]
levels = Pt.retracement_levels(start, end)
print(f"从 {swings['time'].iloc[-2].date()} 的 {start:.2f} 涨到 {swings['time'].iloc[-1].date()} 的 {end:.2f}，涨了 {end / start - 1:.2%}")
print(levels.round(2).to_string())
print(known.loc["2025-03-07":, ["open", "high", "low", "close"]].to_string())
level = levels[0.618]
print(f"61.8% 回撤位 {level:.2f}；3 月 11 日最低 {known['low']['2025-03-11']:.2f}，3 月 13 日最低 {known['low']['2025-03-13']:.2f}，"
      f"3 月 14 日收盘 {known['close'][t]:.2f}，高出回撤位 {known['close'][t] / level - 1:.2%}")
```

```text
      time  price  kind confirmed_at
2024-07-16 564.86     1   2024-08-02
2024-08-05 517.38    -1   2024-08-14
2025-02-19 612.93     1   2025-03-04
从 2024-08-05 的 517.38 涨到 2025-02-19 的 612.93，涨了 18.47%
0.236    590.38
0.382    576.43
0.500    565.16
0.618    553.88
0.786    537.83
              open     high       low   close
date                                         
2025-03-07  570.90  577.390  565.6300  575.92
2025-03-10  567.59  569.540  555.5900  560.58
2025-03-11  559.40  564.020  552.0200  555.92
2025-03-12  562.17  563.110  553.6900  558.87
2025-03-13  558.49  559.105  549.6800  551.42
2025-03-14  556.11  563.830  551.4917  562.81
61.8% 回撤位 553.88；3 月 11 日最低 552.02，3 月 13 日最低 549.68，3 月 14 日收盘 562.81，高出回撤位 1.61%
```

61.8% 被称为「黄金回撤位」。价格碰到它，连续三天没有收在它下方太多，今天大涨收回。看起来它「守住了」。

你会怎么做？

- A. **买入**：黄金回撤位守住了，止损放在 78.6% 下方
- B. **等更多确认**：等价格收回 50% 回撤位上方再买
- C. **不理它**：一个比例说明不了什么

**先写下你的选择。** 第六节揭晓，第八、九节看「回撤到 61.8% 停住」在全部历史上意味着什么。

---

## 二、先开枪，后画靶

### 打个比方

有一个老笑话叫「德州神枪手」：一个人对着谷仓的墙随便开了几十枪，然后走过去，在子弹最密的地方画上靶心，宣布自己枪法如神。

斐波那契回撤很容易变成这个故事：

- **子弹孔是价格的转折点**：每一次回调停下来、掉头的地方。
- **靶心是斐波那契价位**：23.6%、38.2%、50%、61.8%、78.6%，一共五个。
- **画靶的人可以挑起点和终点**：从哪个低点量到哪个高点？用收盘价还是最高最低价？用大一点的波段还是小一点的？每换一次，五个靶心就整体挪一次。

五个靶心已经把 0 到 1 之间的空间分得相当密了，再加上可以挑起点终点，**几乎任何一个转折点，都能找到一条离它很近的斐波那契线。** 第九节会量出这个「几乎」是多少。

所以要检验斐波那契，只有一种办法：**先画靶，后开枪。** 在价格回撤之前就把线画好，然后看价格碰到线的时候会不会停，而且要和「碰到一条普通的线」比。这就是第八节的动手部分。

---

## 三、道氏理论的六条原则

### 来历

道氏理论来自 Charles Dow 在 1900 至 1902 年间给《华尔街日报》写的社论。他的继任者 William Hamilton 在 1902 至 1929 年间继续用这套思路写评论，1922 年出版了《The Stock Market Barometer》。Robert Rhea 研读了两人的 252 篇社论，在 1932 年的《The Dow Theory》里把它整理成系统的原则。

今天说的「六条原则」，是后人对这些著作的归纳。这门课前面的很多篇，其实都是在把其中一条写成代码：

| 原则 | 说的是什么 | 在这门课里 |
|---|---|---|
| 1. 平均指数反映一切 | 所有已知的信息都已经体现在价格里 | 第 1、2 篇：价格是成交的记录，对面是谁 |
| 2. 市场有三种趋势 | 主要趋势（一年以上）、次级回调（几周到几个月）、短期波动（几天） | 第 7 篇：潮汐、波浪、涟漪，就是道氏理论的比方 |
| 3. 主要趋势有三个阶段 | 积累、大众参与、派发 | 第 10 篇：量价关系；第 25 篇会讲持仓量 |
| 4. 平均指数必须相互验证 | 工业指数和运输指数要同时创新高，趋势才算确认 | 第 19 篇：相对强度、多个标的一起看 |
| 5. 成交量验证趋势 | 趋势方向上的成交量应该放大 | 第 10 篇：量价关系的检验 |
| 6. 趋势持续到明确的反转信号出现 | 高点和低点的结构改变之前，趋势还在 | 第 8 篇：高低点定义的趋势状态；第 11 篇：市场状态 |

第 6 条就是第 8 篇趋势定义的源头：**上升趋势是高点和低点都在抬高。** 第 8 篇已经量过它：摆动点要等确认才知道，确认的滞后是这个定义最大的代价。

### 能检验的一条：次级回调回撤 1/3 到 2/3

Rhea 在书里写道，次级回调通常持续三周到三个月，**回撤主要趋势涨跌幅的 33% 到 66%**。这是道氏理论里少数带着具体数字的说法，可以直接检验。

用第 8 篇的 ZigZag 摆动点，每一段的长度除以前一段的长度，就是这一段对前一段的**回撤比例**（大于 1 表示把前一段整段吃掉了）。看看小于 1 的那些回撤里，落在 1/3 到 2/3 之间的有多少，再和打乱顺序的随机价格比：

```python
def shuffle_bars(df, rng):
    """打乱 K 线顺序：保留每根 K 线相对前一根收盘价的形状，重新拼成价格（第 9 篇）。"""
    relative = np.log(df[Pt.OHLC].div(df["close"].shift(1), axis=0))
    relative = relative.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    previous_close = df["close"].iloc[0] * np.exp(relative["close"].cumsum().shift(1, fill_value=0))
    out = np.exp(relative[Pt.OHLC]).mul(previous_close, axis=0)
    out.index = df.index[1:]
    return out


def ratio_summary(close, threshold):
    """回撤比例和扩展比例的几个统计量。"""
    ratios = Pt.swing_ratios(X.zigzag(close, threshold))
    r, e = ratios["retracement"].dropna().to_numpy(), ratios["extension"].dropna().to_numpy()
    partial = r[r < 1]                                            # 没有把前一段整段吃掉的回撤
    near = lambda x, levels, width: np.mean(np.min(np.abs(x[:, None] - np.array(levels)[None, :]), axis=1) <= width)
    return {"段数": len(r), "回撤 < 1 的比例": np.mean(r < 1), "其中在 1/3 到 2/3": np.mean((partial >= 1 / 3) & (partial <= 2 / 3)),
            "回撤离斐波那契比例 ≤ 0.02": near(partial, Pt.FIB_RETRACEMENTS, 0.02),
            "扩展离斐波那契比例 ≤ 0.05": near(e, Pt.FIB_EXTENSIONS, 0.05)}


rows = []
for name, df in datasets:
    real = ratio_summary(df["close"], thresholds[name])
    shuffled = pd.DataFrame([ratio_summary(shuffle_bars(df, rng)["close"], thresholds[name]) for _ in range(20)]).mean()
    rows.append({"数据": name, "口径": "真实"} | real)
    rows.append({"数据": name, "口径": "打乱 20 次平均"} | shuffled.to_dict())
table = pd.DataFrame(rows)
table["段数"] = table["段数"].round().astype(int)
print(table.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
```

```text
       数据        口径   段数  回撤 < 1 的比例  其中在 1/3 到 2/3  回撤离斐波那契比例 ≤ 0.02  扩展离斐波那契比例 ≤ 0.05
   SPY 日线        真实  205       0.502          0.524             0.252             0.049
   SPY 日线 打乱 20 次平均  215       0.500          0.441             0.252             0.072
  AAPL 日线        真实  249       0.502          0.440             0.256             0.073
  AAPL 日线 打乱 20 次平均  256       0.496          0.423             0.240             0.072
   BTC 日线        真实  342       0.482          0.382             0.255             0.059
   BTC 日线 打乱 20 次平均  364       0.502          0.423             0.240             0.069
BTC 4 小时线        真实 1927       0.513          0.395             0.235             0.066
BTC 4 小时线 打乱 20 次平均 2012       0.503          0.420             0.244             0.068
BTC 1 小时线        真实 7625       0.508          0.425             0.233             0.071
BTC 1 小时线 打乱 20 次平均 7777       0.499          0.429             0.242             0.067
```

先看前三列：

- **大约一半的回撤会把前一段整段吃掉**（「回撤 < 1 的比例」在 48% 到 51% 之间），真实和打乱几乎一样。这是 ZigZag 本身的性质：没有趋势记忆的随机价格，下一段比上一段长或短的机会差不多各一半。
- **小于 1 的回撤里，落在 1/3 到 2/3 的占 38% 到 52%**。打乱之后是 42% 到 44%。只有 SPY 高一些（52.4% 对 44.1%），BTC 日线反而低（38.2% 对 42.3%）。

所以「回撤 1/3 到 2/3」是对回撤幅度一个大致的描述，**但随机价格的回撤也差不多这样分布**，它不是市场特有的规律。

⚠️ 这里的 ZigZag 阈值（SPY 2%、AAPL 3%、BTC 日线 5%、4 小时线 2%、1 小时线 1%，和第 17 篇相同）找到的是中短期的摆动，不完全是道氏理论说的「主要趋势」和「次级回调」。换更大的阈值只会让样本更少（练习 3）。

表的后两列留到第七节再看。

---

## 四、斐波那契比例从哪里来

斐波那契数列：每一项等于前两项之和。

```python
fib = [1, 1]
while len(fib) < 16:
    fib.append(fib[-1] + fib[-2])
print("斐波那契数列：", fib)
print("相邻两项之比：", [round(fib[k + 1] / fib[k], 4) for k in range(9, 15)])
phi = (1 + 5 ** 0.5) / 2
print(f"黄金比例 φ = {phi:.6f}；1/φ = {1 / phi:.6f}；1/φ² = {1 / phi ** 2:.6f}；1/φ³ = {1 / phi ** 3:.6f}；"
      f"√(1/φ) = {(1 / phi) ** 0.5:.6f}；φ² = {phi ** 2:.6f}；√φ = {phi ** 0.5:.6f}")
```

```text
斐波那契数列： [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
相邻两项之比： [1.6182, 1.618, 1.6181, 1.618, 1.618, 1.618]
黄金比例 φ = 1.618034；1/φ = 0.618034；1/φ² = 0.381966；1/φ³ = 0.236068；√(1/φ) = 0.786151；φ² = 2.618034；√φ = 1.272020
```

相邻两项之比越来越接近**黄金比例 φ ≈ 1.618**。交易里用的比例都从 φ 推出来：

| 比例 | 来历 | 用途 |
|---|---|---|
| 23.6% | 1/φ³ | 回撤 |
| 38.2% | 1/φ² | 回撤 |
| 50% | **不是**斐波那契比例，是交易员习惯加上的「一半」 | 回撤 |
| 61.8% | 1/φ | 回撤，「黄金回撤位」 |
| 78.6% | √(1/φ) | 回撤 |
| 127.2% | √φ | 扩展 |
| 161.8% | φ | 扩展 |
| 261.8% | φ² | 扩展 |

这些比例在向日葵花盘、鹦鹉螺壳里都能找到，这是它们在交易里流行起来的主要理由之一（20 世纪中叶随艾略特波浪理论传播开）。但**植物生长符合黄金比例，并不说明价格回调也会停在黄金比例上**，这需要用价格数据单独检验。

---

## 五、回撤和扩展怎么画

### 回撤

一段行情从 A 走到 B，回撤 r 的价位是：

> 回撤位 = B - r × (B - A)

上涨段的回撤位在 B 下方，下跌段在 B 上方，同一个公式。

### 扩展

A 走到 B，回撤到 C 之后，下一段的**扩展目标**是：

> 扩展位 = C + r × (B - A)

也就是从 C 出发，再走 AB 那一段长度的 127.2%、161.8% 或 261.8%。

### 起点和终点怎么选

这是斐波那契最大的自由度。决策点那一段，换四种画法：

```python
rows = []
spy_high, spy_low = spy.loc["2025-02-19", "high"], spy.loc["2024-08-05", "low"]
for label, a, b in [("收盘价 ZigZag 5%：2024-08-05 收盘 → 2025-02-19 收盘", start, end),
                    ("用最低价和最高价：2024-08-05 最低 → 2025-02-19 最高", spy_low, spy_high)]:
    rows.append({"起点和终点": label} | Pt.retracement_levels(a, b).round(2).rename(lambda r: f"{r:.1%}").to_dict())
for threshold in [0.03, 0.08]:
    sw = X.zigzag(known["close"], threshold)
    ups = [(sw["price"].iloc[k - 1], sw["price"].iloc[k], sw["time"].iloc[k - 1].date(), sw["time"].iloc[k].date())
           for k in range(1, len(sw)) if sw["kind"].iloc[k] == 1]
    a, b, ta, tb = ups[-1]
    rows.append({"起点和终点": f"收盘价 ZigZag {threshold:.0%}：{ta} → {tb}"}
                | Pt.retracement_levels(a, b).round(2).rename(lambda r: f"{r:.1%}").to_dict())
print(pd.DataFrame(rows).to_string(index=False))
print("假如回撤就停在 61.8%，下一段的扩展目标：")
print(Pt.extension_levels(start, end, levels[0.618]).round(2).to_string())
```

```text
                                      起点和终点  23.6%  38.2%  50.0%  61.8%  78.6%
收盘价 ZigZag 5%：2024-08-05 收盘 → 2025-02-19 收盘 590.38 576.43 565.16 553.88 537.83
     用最低价和最高价：2024-08-05 最低 → 2025-02-19 最高 588.93 573.90 561.75 549.60 532.30
      收盘价 ZigZag 3%：2025-01-10 → 2025-02-19 605.27 600.54 596.71 592.88 587.43
      收盘价 ZigZag 8%：2024-08-05 → 2025-02-19 590.38 576.43 565.16 553.88 537.83
假如回撤就停在 61.8%，下一段的扩展目标：
1.272    675.42
1.618    708.48
2.618    804.03
```

- **收盘价 ZigZag 5% 和 8%**：找到的是同一段（2024-08-05 到 2025-02-19），61.8% 在 553.88。
- **用最低价和最高价**：起点更低、终点更高，61.8% 移到 549.60，差了 4.28。3 月 13 日的最低价 549.68 离它只有 0.08——换成这种画法，那天的「命中」比原来还准。
- **收盘价 ZigZag 3%**：小阈值找到的最近一段是 2025-01-10 到 2025-02-19，61.8% 在 592.88，比原来高了 **7%**。按这种画法，2 月 27 日收盘 585.05 就跌穿了 78.6%，「黄金回撤位」两周前就失效了。

还有更多选择：用周线还是日线的摆动点？从 2024 年 8 月还是 2023 年 10 月的低点量起？**同一个日子，不同的画法可以给出「守住了」「刚碰到」「早就跌穿了」三种完全不同的结论。**

决策点用的是收盘价 ZigZag 5%，这是这门课从第 8 篇起一直在用的摆动点算法，而且在 3 月 14 日之前就能画出来。这一点很重要：**起点和终点必须用当时就能确定的规则选，不能看着价格停在哪里再挑。**

### ✋ 小检查 1

(a) BTC 从 60,000 涨到 100,000。38.2%、50%、61.8% 的回撤位各是多少？

(b) 接上题，如果回撤到 75,000 就掉头，161.8% 的扩展目标是多少？

(c) 同一段上涨，用收盘价画和用最高最低价画，哪一种的回撤位更低？为什么？

答案在文末。

---

## 六、揭晓

**61.8% 守住了将近三周。然后 SPY 跌穿了整段涨幅的起点。**

![揭晓：SPY 日线和斐波那契回撤位，2024-07 至 2025-07](/images/trade-analysis/18/reveal.png)

```python
after = spy.loc["2025-03-17":"2025-06-30"]
full_levels = Pt.retracement_levels(start, end)
for when in ["2025-03-25", "2025-04-03", "2025-04-08", "2025-04-09", "2025-05-12", "2025-06-27"]:
    close = spy.loc[when, "close"]
    nearest = (full_levels - close).abs().idxmin()
    print(f"{when}：收盘 {close:.2f}，离得最近的回撤位是 {nearest:.1%}（{full_levels[nearest]:.2f}），相差 {close / full_levels[nearest] - 1:+.2%}")
print(f"4 月 8 日收盘 {spy.loc['2025-04-08', 'close']:.2f}，比这一段的起点 {start:.2f} 还低 {spy.loc['2025-04-08', 'close'] / start - 1:.2%}；"
      f"第一次收盘回到 2 月 19 日 {end:.2f} 上方：{after.index[after['close'] > end][0].date()}")
```

```text
2025-03-25：收盘 575.46，离得最近的回撤位是 38.2%（576.43），相差 -0.17%
2025-04-03：收盘 536.70，离得最近的回撤位是 78.6%（537.83），相差 -0.21%
2025-04-08：收盘 496.48，离得最近的回撤位是 78.6%（537.83），相差 -7.69%
2025-04-09：收盘 548.62，离得最近的回撤位是 61.8%（553.88），相差 -0.95%
2025-05-12：收盘 582.99，离得最近的回撤位是 38.2%（576.43），相差 +1.14%
2025-06-27：收盘 614.91，离得最近的回撤位是 23.6%（590.38），相差 +4.15%
4 月 8 日收盘 496.48，比这一段的起点 517.38 还低 -4.04%；第一次收盘回到 2 月 19 日 612.93 上方：2025-06-27
```

- **3 月 25 日**收盘 575.46，反弹到 38.2% 回撤位 576.43 下方 0.17% 就停了。
- **4 月 3 日**美国宣布大范围加征关税，SPY 收在 536.70，正好在 78.6% 回撤位 537.83 下方 0.21%。
- **4 月 8 日**收盘 496.48，比这一段的起点 517.38 还低 4.04%：整段涨幅被吃干净了。
- **6 月 27 日**收盘 614.91，才第一次回到 2 月 19 日的高点上方。

三个选择：

- **选 A（在 61.8% 买入、止损放在 78.6% 下方）的**：先反弹了 2%，然后在 4 月 3 日跌破 78.6% 被止损。
- **选 B（等收回 50% 回撤位再买）的**：3 月 17 日收盘 567.15，收回了 565.16，买入；同样在 4 月初被打下去。
- **选 C（不理它）的**：错过了 3 月下旬 2% 的反弹，也躲过了 4 月初的暴跌。

再看一遍上面那几行输出：**3 月 25 日的反弹停在 38.2%，4 月 3 日的收盘停在 78.6%，4 月 9 日（暴涨 10.5% 那天）收在 61.8% 下方 0.95%。** 事后看这张图，斐波那契回撤位「神准」：几乎每个重要的收盘都贴着一条线。

这就是第二节说的德州神枪手：**五条线之间的间隔只有 11 到 16 美元，而 SPY 在这几周每天的波动就有好几美元。** 价格停在哪里，附近都会有一条线。

---

## 七、回撤比例有没有偏爱斐波那契

第三节那张表的后两列，回答的是最直接的问题：**价格的回撤比例，是不是特别容易落在斐波那契比例附近？**

- 「回撤离斐波那契比例 ≤ 0.02」：小于 1 的回撤里，离 23.6%、38.2%、50%、61.8%、78.6% 中某一个不到 0.02 的比例。真实数据 23.3% 到 25.6%，**打乱之后 24.0% 到 25.2%**。
- 「扩展离斐波那契比例 ≤ 0.05」：扩展比例离 127.2%、161.8%、261.8% 不到 0.05 的比例。真实 4.9% 到 7.3%，打乱 6.7% 到 7.2%。

真实和打乱几乎一样。五个比例、每个左右各 0.02，一共覆盖了 0.2 的宽度，所以随便一个回撤比例落进去的机会本来就有两成多。

![回撤比例的分布：BTC 1 小时线](/images/trade-analysis/18/ratio-histogram.png)

BTC 1 小时线有 3,875 段小于 1 的回撤，样本最多。直方图里，**斐波那契比例的位置上没有尖峰**，真实数据和打乱的随机价格走势一致。0.57 和 0.69 附近有两根高一些的柱子，但它们不在任何斐波那契比例上，而且同样大小的起伏在别处也有。

---

## 八、先画靶，后开枪

### 检验怎么设计

第七节看的是「回撤最后停在哪」，那已经是事后的结果了。交易员真正关心的是：**价格回撤到某条线的时候，它会不会停？** 这要在当时就能回答：

1. 每一段 A→B，要等 B 被 ZigZag 确认之后才知道这一段存在。确认之前已经碰过的价位不算。
2. 在确认之后，价格**第一次**碰到某个比例的回撤位时，从那个价位出发，上下各放 1 个 ATR。
3. 之后 20 根里，**先朝原方向走出 1 个 ATR 记为「停住了」**，先反向走出 1 个 ATR 记为「穿过了」。碰到回撤位的那一根自己就走过了反向的线，记为穿过。
4. 价格收盘越过 B（创出新高）或越过 A（整段吃掉），就不再看这一段。

对照是**普通比例**：从 0.14 到 0.86，每隔 0.01 一个比例，全部用同样的办法检验。如果斐波那契比例特别，它们「停住」的比例应该比左右的普通比例高。

具体比较的是：每个斐波那契比例，和它左右各 0.03、0.06 的四个邻居比（比如 61.8% 和 55.8%、58.8%、64.8%、67.8% 比），五个差再取平均。和自己左右对称的邻居比，可以抵消「回撤越浅越容易停住」这种随比例平滑变化的趋势。区间用「按段重抽样」：同一段的各个比例结果相关，所以整段一起抽。

`talab.patterns.retracement_tests` 就是上面这四步。

```python
offsets = (-0.06, -0.03, 0.03, 0.06)
neighbors = {f: np.round(np.array(offsets) + f, 3) for f in Pt.FIB_RETRACEMENTS}          # 每个斐波那契比例左右各两个邻居
grid = np.unique(np.round(np.concatenate([np.arange(0.14, 0.8601, 0.01), Pt.FIB_RETRACEMENTS,
                                          *neighbors.values()]), 3))


def fib_versus_neighbors(tests, n=1000):
    """每个斐波那契比例的「停住」比例减去它四个邻居的平均，五个比例再取平均；按「段」重抽样 n 次给出 95% 区间和 p 值。

    和自己左右对称的邻居比，可以抵消「回撤越浅越容易停住」这种随比例平滑变化的趋势。
    """
    tests = tests.dropna(subset=["held"])
    wins = tests.pivot_table(index="end", columns="ratio", values="held", aggfunc="sum", fill_value=0)
    counts = tests.pivot_table(index="end", columns="ratio", values="held", aggfunc="count", fill_value=0)

    def stat(rows):
        rate = wins.iloc[rows].sum() / counts.iloc[rows].sum()
        return np.mean([rate[f] - rate[neighbors[f]].mean() for f in Pt.FIB_RETRACEMENTS])

    everyone = np.arange(len(wins))
    boot = np.array([stat(rng.integers(0, len(wins), len(wins))) for _ in range(n)])
    return stat(everyone), np.percentile(boot, [2.5, 97.5]), 2 * min((boot <= 0).mean(), (boot >= 0).mean())


rows, curves = [], {}
for name, df in datasets:
    atr = I.atr(df["high"], df["low"], df["close"])
    tests = Pt.retracement_tests(df["high"], df["low"], df["close"], X.zigzag(df["close"], thresholds[name]), atr, grid)
    curves[name] = tests.groupby("ratio")["held"].mean()
    diff, (low, high), p = fib_versus_neighbors(tests)
    by_ratio = tests.dropna(subset=["held"]).groupby("ratio")["held"]
    rows.append({"数据": name, "段数": tests["end"].nunique(), "碰到 61.8% 的次数": int(by_ratio.count().get(0.618, 0))}
                | {f"{r:.1%}": by_ratio.mean().get(r, np.nan) for r in Pt.FIB_RETRACEMENTS}
                | {"斐波那契 - 左右邻居": diff, "95% 区间": f"{low:+.3f} ~ {high:+.3f}", "p": p})
    if name == "BTC 1 小时线":
        hourly_tests = tests
print("回撤位被碰到之后「停住」的比例（先朝原方向走出 1 个 ATR）：")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("BTC 1 小时线，逐个比例和它的四个邻居比，再按 2022 年前后分开：")
rows = []
for label, part in [("全部", hourly_tests), ("2022 年前", hourly_tests[hourly_tests["touched_at"] < pd.Timestamp("2022-01-01", tz="UTC")]),
                    ("2022 年起", hourly_tests[hourly_tests["touched_at"] >= pd.Timestamp("2022-01-01", tz="UTC")])]:
    rate = part.dropna(subset=["held"]).groupby("ratio")["held"].mean()
    rows.append({"时段": label} | {f"{f:.1%}": rate[f] - rate[neighbors[f]].mean() for f in Pt.FIB_RETRACEMENTS})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
```

### 结果

```text
回撤位被碰到之后「停住」的比例（先朝原方向走出 1 个 ATR）：
       数据   段数  碰到 61.8% 的次数  23.6%  38.2%  50.0%  61.8%  78.6%  斐波那契 - 左右邻居          95% 区间     p
   SPY 日线  103            53  0.583  0.625  0.472  0.377  0.375        0.083 -0.001 ~ +0.171 0.052
  AAPL 日线  118            62  0.500  0.400  0.500  0.516  0.435       -0.032 -0.116 ~ +0.046 0.454
   BTC 日线  168            73  0.750  0.588  0.460  0.370  0.440       -0.007 -0.094 ~ +0.072 0.832
BTC 4 小时线  849           409  0.667  0.518  0.444  0.482  0.541       -0.007 -0.039 ~ +0.026 0.694
BTC 1 小时线 3166          1455  0.709  0.552  0.513  0.524  0.560        0.015 +0.000 ~ +0.029 0.046
BTC 1 小时线，逐个比例和它的四个邻居比，再按 2022 年前后分开：
     时段  23.6%  38.2%  50.0%  61.8%  78.6%
     全部 +0.060 +0.017 +0.001 -0.002 -0.000
2022 年前 +0.084 +0.019 +0.003 -0.008 -0.001
2022 年起 +0.026 +0.015 -0.004 +0.004 -0.000
```

![回撤到各个比例之后停住的比例](/images/trade-analysis/18/held-curve.png)

- **61.8% 本身**：SPY 37.7%、AAPL 51.6%、BTC 日线 37.0%、4 小时线 48.2%、1 小时线 52.4%。**和随手扔一枚硬币差不多，SPY 和 BTC 日线还低于一半。**
- **斐波那契减邻居**：BTC 日线和 4 小时线都是 -0.7 个百分点，AAPL -3.2 个百分点，都不显著。SPY +8.3 个百分点，但区间 -0.001 到 +0.171，碰到 61.8% 的只有 53 次；BTC 1 小时线 +1.5 个百分点，p 0.046，刚好擦线。
- **BTC 1 小时线逐个看**：那 1.5 个百分点几乎全部来自 **23.6%**（+6.0），而 61.8% 是 -0.2，78.6% 是 0.0。2022 年前后分开看，61.8% 分别是 -0.8 和 +0.4。**「黄金回撤位」在 1,455 次检验里和它的邻居没有区别。**
- 图上的曲线：浅的回撤（0.2 附近）更容易停住，深的回撤停住的机会接近一半。**斐波那契比例（圆点）落在曲线的起伏之中，没有一个明显突出。**

为什么浅的回撤更容易「停住」？因为这里的「停住」是朝原方向走出 1 个 ATR，浅回撤离原来的趋势方向近，趋势还在的可能性大一些。这和斐波那契无关，是比例本身的性质，所以对照必须用邻居，不能用全部比例的平均。

---

## 九、事后画线能有多准

第六节看到，事后画线时斐波那契「神准」。量一量这件事：

对每一个 ZigZag 转折点 C，用它之前已经走完的波段画回撤位，看有没有一条线离 C 在 **0.25 个 ATR** 以内（大约是一天波动的四分之一）。两种画法：

- **只画一次**：只用同一个阈值下、C 之前最近的那一段
- **随便挑起点终点**：阈值取基准的 0.6、1、1.6、2.5 倍，每个阈值取 C 之前最近的两段，一共最多 8 种画法，只要有一种命中就算

对照是**平移后的比例**：把五个斐波那契比例整体平移 ±0.01 到 ±0.06（一共 12 组），间距不变，只是换了位置。

```python
def sharpshooter(df, base, level_sets, anchors_per_threshold=2, width=0.25):
    """每个结束了一段回撤的摆动点 C：用 C 之前已经走完的若干段作起点和终点画回撤位，看有没有一条落在 C 的 width 个 ATR 以内。

    阈值取 base 的 0.6、1、1.6、2.5 倍；每个阈值取 C 之前最近的 anchors_per_threshold 段。
    返回「只用最近一段、一个阈值」和「所有段、所有阈值」两种画法下，命中的比例（对每组比例分别算）。
    """
    close = df["close"]
    atr = I.atr(df["high"], df["low"], close)
    turns = X.zigzag(close, base)
    candidates = {m: X.zigzag(close, base * m).sort_values("time").reset_index(drop=True) for m in (0.6, 1.0, 1.6, 2.5)}
    one, many, counted = np.zeros(len(level_sets)), np.zeros(len(level_sets)), 0
    for row in turns.itertuples():
        if np.isnan(atr[row.time]):
            continue
        legs = []
        for m, sw in candidates.items():
            earlier = sw[sw["time"] < row.time]
            for k in range(len(earlier) - 1, max(len(earlier) - 1 - anchors_per_threshold, 0), -1):
                a, b = earlier["price"].iloc[k - 1], earlier["price"].iloc[k]
                if (b - a) * (row.price - b) < 0:                  # 只要方向和这次回撤相反的那些段
                    legs.append((m, a, b))
        if not legs:
            continue
        counted += 1
        natural = [leg for leg in legs if leg[0] == 1.0][:1]
        for s, ratios in enumerate(level_sets):
            ratios = np.asarray(ratios)
            hit = lambda group: any(np.min(np.abs(b - ratios * (b - a) - row.price)) <= width * atr[row.time] for _, a, b in group)
            one[s] += hit(natural)
            many[s] += hit(legs)
    return one / counted, many / counted, counted


shifts = [d for d in np.round(np.arange(-0.06, 0.0601, 0.01), 2) if d != 0]
shifted_sets = [np.array(Pt.FIB_RETRACEMENTS) + d for d in shifts]          # 同样的间距，整体平移
rows = []
for name, df in datasets[:4]:
    one, many, counted = sharpshooter(df, thresholds[name], [Pt.FIB_RETRACEMENTS] + shifted_sets)
    rows.append({"数据": name, "转折点": counted, "只画一次：斐波那契": one[0], "只画一次：平移后的比例": one[1:].mean(),
                 "随便挑起点终点：斐波那契": many[0], "随便挑起点终点：平移后的比例": many[1:].mean(),
                 "平移的 12 组里不低于斐波那契的": int((many[1:] >= many[0]).sum())})
print("转折点离某条回撤位 0.25 个 ATR 以内的比例：")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
```

```text
转折点离某条回撤位 0.25 个 ATR 以内的比例：
       数据  转折点  只画一次：斐波那契  只画一次：平移后的比例  随便挑起点终点：斐波那契  随便挑起点终点：平移后的比例  平移的 12 组里不低于斐波那契的
   SPY 日线  206      0.340        0.337         0.534           0.524                  1
  AAPL 日线  250      0.356        0.350         0.564           0.546                  3
   BTC 日线  342      0.383        0.382         0.558           0.564                  9
BTC 4 小时线 1927      0.389        0.392         0.593           0.604                 12
```

两件事：

1. **只画一次，三分之一的转折点就能「命中」一条回撤位**（34.0% 到 38.9%）。允许挑起点和终点，命中率升到 **53% 到 60%**。
2. **斐波那契比例和平移后的普通比例命中率几乎一样**。最后一列是 12 组平移比例里命中率不低于斐波那契的有几组：SPY 1 组、AAPL 3 组、BTC 日线 9 组、4 小时线全部 12 组。如果斐波那契比例特别，应该稳定地排在最前面。

也就是说，**你在图上看到的「价格精准地停在 61.8%」，一半以上可以用「有五条线、可以挑起点」来解释**，而且换成任何一组间距差不多的比例，看到的「精准」一样多。

### ✋ 小检查 2

(a) 五条回撤线把一段 100 美元的行情切开，价格回撤停在任意位置的机会均等。如果「离某条线 1 美元以内」算命中，命中的概率大约是多少？允许从 4 种互不相关的画法里挑一种呢？

(b) 第八节里，为什么要让斐波那契比例和它**左右对称**的邻居比，而不是和 0.14 到 0.86 所有比例的平均比？

(c) 有人说：「我只在 61.8% 和成交量放大同时出现的时候买，胜率很高。」你会让他补充哪两个对照？

答案在文末。

---

## 十、talab.patterns：第三部分

### 新增了什么

| 函数 | 作用 |
|---|---|
| `retracement_levels` | 一段行情的回撤位，默认五个斐波那契比例 |
| `extension_levels` | A→B 回撤到 C 之后的扩展目标，默认 127.2%、161.8%、261.8% |
| `swing_ratios` | 每一段相对前一段的回撤比例，和相对前面隔一段的扩展比例 |
| `retracement_tests` | 第八节的实时检验：每一段被确认之后，价格第一次碰到各个比例的价位时，是停住还是穿过 |

`fib_versus_neighbors`、`sharpshooter` 这些只在这一篇分析用的函数**不放进模块**，只在 `docs/trade-analysis/analysis/18_dow_fibonacci.py` 里。

### 代码

```python
# ---------------------------------------------------------------------------
# 五、斐波那契回撤与扩展（第 18 篇）
# ---------------------------------------------------------------------------

FIB_RETRACEMENTS = (0.236, 0.382, 0.5, 0.618, 0.786)
FIB_EXTENSIONS = (1.272, 1.618, 2.618)


def retracement_levels(start: float, end: float, ratios=FIB_RETRACEMENTS) -> pd.Series:
    """一段行情从 start 走到 end，回撤 ratio 的价位 = end - ratio × (end - start)。

    上涨段（end > start）的回撤位在 end 下方，下跌段在 end 上方，公式相同。返回以 ratio 为索引的价位。
    """
    ratios = np.asarray(ratios, dtype=float)
    return pd.Series(end - ratios * (end - start), index=ratios, name="level")


def extension_levels(a: float, b: float, c: float, ratios=FIB_EXTENSIONS) -> pd.Series:
    """A 走到 B、回撤到 C 之后，下一段的扩展目标 = C + ratio × (B - A)。返回以 ratio 为索引的价位。"""
    ratios = np.asarray(ratios, dtype=float)
    return pd.Series(c + ratios * (b - a), index=ratios, name="level")


def swing_ratios(swings: pd.DataFrame) -> pd.DataFrame:
    """每个摆动点结束的那一段，相对前面几段的比例。

    retracement：这一段的长度 ÷ 前一段的长度（前一段被回撤了多少，1 表示回撤到起点）
    extension：这一段的长度 ÷ 前面隔一段的那一段的长度（A→B、B→C、C→D 里的 CD ÷ AB）
    比例都用摆动点的价格算，第一、二个摆动点没有前一段，为 NaN。
    """
    ordered = swings.sort_values("time").reset_index(drop=True)
    p = ordered["price"].to_numpy(dtype=float)
    leg = np.abs(np.diff(p, prepend=np.nan))                 # 第 n 个摆动点结束的那一段的长度
    retracement = leg / np.roll(leg, 1)
    extension = leg / np.roll(leg, 2)
    retracement[:2], extension[:3] = np.nan, np.nan
    return pd.DataFrame({"time": ordered["time"], "kind": ordered["kind"], "retracement": retracement,
                         "extension": extension})


def retracement_tests(high: pd.Series, low: pd.Series, close: pd.Series, swings: pd.DataFrame, atr: pd.Series,
                      ratios, distance: float = 1.0, horizon: int = 20) -> pd.DataFrame:
    """实时地检验回撤位：每一段 A→B 被确认之后，价格第一次回撤到某个比例的价位时，看它是「停住」还是「穿过」。

    对每两个相邻的摆动点 A、B（B 在 confirmed_at 被确认）：
    1. 各个比例的价位 = B - ratio × (B - A)
    2. 从 B 到 confirmed_at 之间已经碰过的价位不算：那时还不知道这一段存在
    3. 从 confirmed_at 的下一根开始往后看，收盘价越过 B（新高，上涨段）或越过 A（整段被吃掉）就停止
    4. 某个价位第一次被碰到（上涨段看最低价 ≤ 价位）的那一根，记为 touched_at
    5. 从这个价位出发，上下各放 distance 个 ATR（用 confirmed_at 那一根的 ATR）。
       之后 horizon 根里，先朝原来方向走出 distance 个 ATR 记 1（停住了），先反向走出记 0（穿过了），都没有记 NaN。
       碰到价位的那一根自己就走过了反向的线，记 0
    返回每一次「碰到」一行：start、end、confirmed_at、ratio、level、touched_at、held。
    """
    h, l, c, a = (s.to_numpy(dtype=float) for s in (high, low, close, atr))
    pos = {t: i for i, t in enumerate(close.index)}
    ordered = swings.sort_values("time").reset_index(drop=True)
    ratios = np.asarray(ratios, dtype=float)
    rows = []
    for n in range(1, len(ordered)):
        start, end = ordered["price"].iloc[n - 1], ordered["price"].iloc[n]
        sign = 1 if end > start else -1                        # 1：上涨段，回撤向下
        seen = pos[ordered["confirmed_at"].iloc[n]]
        if np.isnan(a[seen]):
            continue
        levels = end - ratios * (end - start)
        width = distance * a[seen]
        k0 = pos[ordered["time"].iloc[n]]
        reached = (l[k0:seen + 1].min() if sign == 1 else h[k0:seen + 1].max())
        done = sign * (reached - levels) <= 0
        for j in range(seen + 1, len(c)):
            if sign * (c[j] - end) > 0 or sign * (c[j] - start) < 0 or done.all():
                break
            extreme = l[j] if sign == 1 else h[j]
            hit = ~done & (sign * (extreme - levels) <= 0)
            for g in np.flatnonzero(hit):
                level, held = levels[g], np.nan
                if sign * (extreme - (level - sign * width)) <= 0:
                    held = 0.0
                else:
                    for m in range(j + 1, min(j + 1 + horizon, len(c))):
                        if sign * ((l[m] if sign == 1 else h[m]) - (level - sign * width)) <= 0:
                            held = 0.0
                            break
                        if sign * ((h[m] if sign == 1 else l[m]) - (level + sign * width)) >= 0:
                            held = 1.0
                            break
                rows.append((ordered["time"].iloc[n - 1], ordered["time"].iloc[n], ordered["confirmed_at"].iloc[n],
                             ratios[g], level, close.index[j], held))
            done |= hit
    return pd.DataFrame(rows, columns=["start", "end", "confirmed_at", "ratio", "level", "touched_at", "held"])
```

### 读一遍代码

**`retracement_levels`** 用一个公式处理上涨段和下跌段：`end - ratios * (end - start)`。下跌段里 end - start 是负数，回撤位自然落在 end 上方。

**`swing_ratios`** 先用 `np.diff(p, prepend=np.nan)` 算出每一段的长度，再用 `np.roll` 拿到前一段、前面隔一段的长度。`np.roll` 会把末尾的值绕到开头，所以最后要把前两个（回撤）、前三个（扩展）设成 NaN。

**`retracement_tests` 的三个「不看未来」的细节**：

1. `reached` 记下从 B 到确认那一根之间已经碰到的最远价位，这些比例直接标记为 `done`：那时候这一段还不存在，这些「碰到」不能算。
2. 扫描从确认的**下一根**开始。
3. 用 `sign` 统一上涨段和下跌段：上涨段的回撤向下，看最低价；下跌段的回撤向上，看最高价。所有不等式都乘上 `sign`，只写一遍。

### 测试

```python
# ---------------------------------------------------------------------------
# 斐波那契回撤与扩展（第 18 篇）
# ---------------------------------------------------------------------------

def test_retracement_and_extension_levels_by_hand():
    up = Pt.retracement_levels(100, 200)
    assert up.tolist() == pytest.approx([176.4, 161.8, 150, 138.2, 121.4])
    down = Pt.retracement_levels(200, 100)                                    # 下跌段的回撤位在上方
    assert down.tolist() == pytest.approx([123.6, 138.2, 150, 161.8, 178.6])
    assert Pt.extension_levels(100, 200, 150).tolist() == pytest.approx([277.2, 311.8, 411.8])


def test_swing_ratios_by_hand():
    close = pd.Series([100.0, 200, 150, 300, 225, 240], index=pd.date_range("2024-01-01", periods=6, freq="D"))
    swings = manual_swings(close, [(0, -1), (1, 1), (2, -1), (3, 1), (4, -1)])
    ratios = Pt.swing_ratios(swings)
    # 段长：100、50、150、75。回撤：50/100、150/50、75/150；扩展：150/100、75/50
    assert ratios["retracement"].tolist()[2:] == pytest.approx([0.5, 3.0, 0.5])
    assert ratios["extension"].tolist()[3:] == pytest.approx([1.5, 1.5])
    assert ratios["retracement"].iloc[:2].isna().all() and ratios["extension"].iloc[:3].isna().all()


def retracement_bars(after):
    """0 到 10 根从 100 涨到 200；第 11、12 根回落（第 12 根最低 175），之后按 after 给出的 (最高, 最低, 收盘)。"""
    rows = [(p, p, p) for p in np.linspace(100, 200, 11)] + [(200, 184, 185), (186, 175, 180)] + list(after)
    index = pd.date_range("2024-01-01", periods=len(rows), freq="D")
    frame = pd.DataFrame(rows, columns=["high", "low", "close"], index=index)
    swings = pd.DataFrame([(index[0], 100.0, -1, index[1]), (index[10], 200.0, 1, index[12])], columns=X.SWING_COLUMNS)
    return frame, swings, pd.Series(5.0, index=index)


def test_retracement_tests_by_hand():
    # 23.6% 的价位 176.4 在第 12 根（确认那一根）之前就碰过了，不算；38.2% 的价位 161.8 在第 14 根第一次被碰到
    frame, swings, atr = retracement_bars([(172, 168, 170), (165, 161, 163), (167, 162, 166), (170, 166, 169)])
    found = Pt.retracement_tests(frame["high"], frame["low"], frame["close"], swings, atr, [0.236, 0.382, 0.5])
    assert found["ratio"].tolist() == [0.382]
    assert found["touched_at"].iloc[0] == frame.index[14] and found["level"].iloc[0] == pytest.approx(161.8)
    assert found["held"].iloc[0] == 1.0                                       # 第 15 根最高 167 ≥ 161.8 + 5
    frame, swings, atr = retracement_bars([(172, 168, 170), (165, 161, 163), (164, 156, 158)])
    found = Pt.retracement_tests(frame["high"], frame["low"], frame["close"], swings, atr, [0.382])
    assert found["held"].iloc[0] == 0.0                                       # 第 15 根最低 156 ≤ 161.8 - 5


def test_retracement_tests_down_leg_mirror():
    frame, swings, atr = retracement_bars([(172, 168, 170), (165, 161, 163), (167, 162, 166), (170, 166, 169)])
    flipped = pd.DataFrame({"high": -frame["low"], "low": -frame["high"], "close": -frame["close"]})
    flipped_swings = swings.assign(price=-swings["price"], kind=-swings["kind"])
    up = Pt.retracement_tests(frame["high"], frame["low"], frame["close"], swings, atr, [0.236, 0.382, 0.5])
    down = Pt.retracement_tests(flipped["high"], flipped["low"], flipped["close"], flipped_swings, atr, [0.236, 0.382, 0.5])
    assert down["touched_at"].tolist() == up["touched_at"].tolist() and down["held"].tolist() == up["held"].tolist()
    assert down["level"].tolist() == pytest.approx((-up["level"]).tolist())


def test_retracement_tests_never_use_the_future():
    rng = np.random.default_rng(180)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 1500))), index=pd.date_range("2020-01-01", periods=1500, freq="D"))
    high, low = close * (1 + rng.uniform(0, 0.01, 1500)), close * (1 - rng.uniform(0, 0.01, 1500))
    atr = pd.Series(0.02 * close.to_numpy(), index=close.index)
    ratios = [0.382, 0.5, 0.618]
    full = Pt.retracement_tests(high, low, close, X.zigzag(close, 0.05), atr, ratios)
    assert len(full) > 20
    for k in [700, 1200]:
        part = Pt.retracement_tests(high.iloc[:k], low.iloc[:k], close.iloc[:k], X.zigzag(close.iloc[:k], 0.05), atr.iloc[:k], ratios)
        settled = lambda frame: frame[frame["touched_at"] <= close.index[k - 1 - 20]].reset_index(drop=True)
        pd.testing.assert_frame_equal(settled(part), settled(full))
```

- `test_retracement_and_extension_levels_by_hand`：上涨段、下跌段的回撤位和扩展位的手算。
- `test_swing_ratios_by_hand`：四段长度 100、50、150、75 的回撤比例和扩展比例。
- `test_retracement_tests_by_hand`：23.6% 在确认之前就碰过，不算；38.2% 在第 14 根第一次被碰到，之后先涨出 1 个 ATR 记为停住，换一组数据先跌出 1 个 ATR 记为穿过。
- `test_retracement_tests_down_leg_mirror`：把价格上下翻转，下跌段的结果和上涨段完全对称。
- `test_retracement_tests_never_use_the_future`：截断两次，已经有结果的那些「碰到」必须和用全部数据算出的一样。

```bash
pytest -q
```

```text
........................................................................ [ 91%]
.............                                                            [100%]
157 passed in 0.61s
```

没装 TA-Lib 时，结果是 125 passed、32 skipped。

---

## 十一、常见误用

**1. 看着价格停下来的地方，再去找起点和终点。**
允许挑起点终点，BTC 4 小时线上 59% 的转折点都能找到一条 0.25 个 ATR 以内的回撤位，平移过的普通比例也一样。

**2. 不说清楚用的是收盘价还是最高最低价、哪个级别的波段。**
决策点那一段，61.8% 的价位在 549.60 到 592.88 之间，差了 7%。

**3. 把「五条线里总有一条挨得近」当成「斐波那契很准」。**
五条线把一段行情切得很密，价格停在任何地方，附近都有线。

**4. 和「全部比例的平均」比，而不是和邻居比。**
浅回撤本来就更容易停住。拿 23.6% 和所有比例的平均比，会得出「23.6% 特别灵」的错觉。

**5. 把 50% 当作斐波那契比例。**
它只是「一半」，和斐波那契数列无关。

**6. 从自然界的黄金比例推出价格会停在黄金比例。**
向日葵的花盘符合 φ，是植物生长的几何规律，和交易者的买卖没有关系。要判断价格，只能用价格数据检验。

**7. 把道氏理论的每一条都当成可以直接交易的规则。**
它是一套描述市场的框架。其中能写成数字的（比如回撤 1/3 到 2/3），在数据上和随机价格差别不大；它真正的价值在于第 7、8、10 篇那些已经写成代码的概念。

---

## 十二、这一篇能回答什么，不能回答什么

| 这一篇**能**帮你回答 | 这一篇**不能**回答 |
|---|---|
| 道氏理论的六条原则分别是什么，对应课程里的哪个工具 | 道氏理论的「指数相互验证」在今天还有没有用（需要运输指数的数据） |
| 斐波那契比例的来历，回撤位和扩展位怎么画 | 其他作者的斐波那契变体（时间周期、扇形线、弧线） |
| 起点和终点的选择让价位移动多少 | 什么是「正确」的起点和终点 |
| 在这五组数据上，回撤到斐波那契位停住的机会，和回撤到邻近的普通比例有没有区别 | 当成千上万人同时盯着同一条 61.8% 时，那个价位的订单簿会不会不同（需要盘口数据） |
| 事后画线时，「命中」有多少是靠自由度得来的 | 你在实时交易中能不能克制住事后画线的冲动 |

---

## 十三、小结

1. **道氏理论的六条原则**大多已经在这门课里变成了工具：三种趋势是第 7 篇的多周期，成交量验证是第 10 篇，趋势持续到反转信号是第 8 篇的高低点定义。

2. **「次级回调回撤 1/3 到 2/3」在数据上和随机价格差不多**：小于 1 的回撤里有 38% 到 52% 落在这个区间，打乱之后是 42% 到 44%。

3. **斐波那契比例来自黄金比例 φ**：23.6%、38.2%、61.8%、78.6% 分别是 1/φ³、1/φ²、1/φ、√(1/φ)；50% 不是斐波那契比例。扩展比例是 √φ、φ、φ²。

4. **起点和终点决定一切。** 决策点那一段，换四种画法，61.8% 的价位能差出 7%。起点和终点必须用当时就能确定的规则选。

5. **回撤比例没有偏爱斐波那契**：真实数据里落在斐波那契比例 ±0.02 以内的有 23% 到 26%，打乱的随机价格一样多。

6. **回撤到斐波那契位之后，停住的机会和回撤到邻近的普通比例一样**：61.8% 的停住率在 37% 到 52% 之间；五组数据里只有 BTC 1 小时线擦线显著，而且来自 23.6%，61.8% 在 1,455 次里和邻居没有区别。

7. **事后画线的「准」主要来自自由度**：只画一次就有三分之一的转折点命中，允许挑起点终点就超过一半，换成平移过的普通比例也一样。

8. **决策点那次，61.8% 守了将近三周**，反弹停在 38.2%，暴跌停在 78.6%，然后跌穿了整段涨幅的起点。事后看每条线都「准」，当时按任何一条线交易都被打掉了。

最后回到谷仓的墙。斐波那契回撤不是没用：它给了你一套**事先画好的、有明确规则的参考价位**，让你在回调中不至于毫无头绪（第 21 篇写交易规则时，止损和目标总得放在某个地方）。但这些线的作用和「第 9 篇的前低」「第 15 篇的 N 倍 ATR」是同一类东西，**它们不会因为叫斐波那契就更灵**。先画靶，后开枪。

第四部分「形态」到这里结束。下一篇进入第五部分「从信号到交易」，第 19 篇：**标的筛选与相对强度**。Binance 上有几百个永续合约，美股有几千只股票，今天你交易哪几个？

---

## 练习

**练习 1（手算）**
一段下跌从 250 跌到 150。

- (a) 23.6%、38.2%、50%、61.8%、78.6% 的回撤位各是多少？
- (b) 如果反弹到 200 之后再次下跌，161.8% 的扩展目标是多少？
- (c) 如果反弹到 230 呢？这个扩展目标还有意义吗？

**练习 2（编程）**
给 `retracement_tests` 加一个参数 `touch="low"`：可以选择用收盘价（而不是最低最高价）碰到回撤位才算「碰到」。

- (a) 用收盘价重做第八节的表，61.8% 的停住率变了多少？
- (b) 为什么用收盘价判断「碰到」，停住的比例会下降？

**练习 3（数据）**
第三节用的 ZigZag 阈值偏小，更接近「次级回调」而不是「主要趋势」。

- (a) 把阈值放大到 SPY 8%、AAPL 12%、BTC 日线 20%，重做「回撤在 1/3 到 2/3 的比例」。样本还有多少段？
- (b) 结论变不变？打乱之后呢？

**练习 4（数据）**
第八节只看了回撤位。

- (a) 仿照 `retracement_tests` 写一个 `extension_tests`：A→B→C 确认之后，价格第一次到达 C + r × (B - A) 时，是停住还是穿过。
- (b) 比较 161.8% 和它的邻居。
- (c) 用第 9 篇的整数关口做同样的检验：价格第一次碰到整数千位（BTC）或整数十位（SPY）时停住的比例，和碰到非整数价位比。哪一个更像「有人盯着的价位」？

**练习 5（思考）**
有人说：「斐波那契有效，是因为大家都在用它，自我实现。」

- (a) 如果这个说法对，你预期第八节的表会是什么样子？
- (b) 实际的表支持这个说法吗？
- (c) 如果只在盘口数据上才能看出它的作用（比如 61.8% 附近挂单更多），第八节的方法为什么看不出来？

---

## 小检查答案

**小检查 1**

(a) 涨幅 40,000。38.2%：100,000 - 15,280 = **84,720**；50%：**80,000**；61.8%：100,000 - 24,720 = **75,280**。

(b) 75,000 + 1.618 × 40,000 = **139,720**。

(c) **用最高最低价画的回撤位更低**（对上涨段而言）。起点用最低价、终点用最高价，这一段的幅度比用收盘价大，同一个比例的回撤距离也更大；起点又更低，所以回撤位整体下移。决策点那段，61.8% 从 553.88 移到了 549.60。

**小检查 2**

(a) 五条线，每条左右各 1 美元，一共覆盖 10 美元，命中概率大约 **10%**。允许从 4 种互不相关的画法里挑，至少一种命中的概率是 1 - 0.9⁴ ≈ **34%**。实际的画法彼此相关（第九节的 8 种画法很多是同一段），所以没有这么高，但方向一样：可选的画法越多，命中率越高。

(b) 因为「停住」的比例随回撤深度**平滑地变化**：浅回撤更容易停住。如果拿 23.6% 和全部比例的平均比，它会因为「浅」而显得特别好，拿 78.6% 比，会因为「深」而显得特别差，这和斐波那契无关。和左右对称的邻居比，平滑的趋势在左右两边大致抵消，剩下的才是「这个比例本身」的效应。

(c) 两个对照：**61.8% 但成交量没有放大**（看成交量本身是不是就有用，第 10 篇），以及**成交量放大、但在普通比例（比如 55%、68%）上**（看 61.8% 在「成交量放大」这个条件下还有没有额外作用）。只有同时比过这两个，才能说「61.8% 加放量」比单独的放量更好。
