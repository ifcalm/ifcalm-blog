---
title: "第 17 篇：经典图表形态"
date: 2026-09-17
weight: 17
tags: ["交易技术分析"]
draft: false
summary: "2025 年 1 月 8 日，BTC 的头肩顶右肩已经走出来，收盘价离颈线只有 2.2%。第二天它真的跌破了颈线，然后在 11 天里创出历史新高。这一篇把头肩形、双顶双底、三角形、楔形、通道都写成基于摆动点的算法，调参数看识别结果怎么变（换一个阈值，决策点的头肩顶就消失了）；统计「突破颈线才算成立」让胜率虚高多少（同样的交易，只数成立的，胜率从 39% 变成 87%）；按教科书的止损和量度目标交易，和「普通的跌破前低」比有没有多出东西；最后发现三角形、楔形的突破方向在打乱顺序的随机价格上几乎一模一样——那是识别规则的几何，不是市场的规律。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **本篇位置** | 第四部分「形态」的第二篇。形态建立在第 8 篇的 ZigZag 摆动点上，「普通的跌破前低」是第 11 篇的突破，打乱检验沿用第 9 篇 |
| **用到的数据** | BTCUSDT 现货日线，以及用 1 分钟线合成的 4 小时线和 1 小时线（2017-08 至 2026-08）；SPY、AAPL 日线（2016-09 至 2026-09） |
| **动手** | `talab.patterns` 第二部分：头肩形、双顶双底、三角形 / 楔形 / 通道的识别器，附 13 个测试；调参数观察识别结果的变化 |
| **读完你能** | 把一个图表形态写成可以运行的规则，并且说清楚每个参数改变了什么；识别「只统计成立的形态」这种偏差；分辨一个统计规律来自市场，还是来自你的识别规则 |

---

## 一、先做一个决定

现在是 **2025 年 1 月 8 日 UTC 收盘**。

过去两个月，BTC 走出了一个教科书式的**头肩顶**：

- **左肩**：11 月 22 日收盘 98,892
- **头**：12 月 17 日收盘 106,134，当时的历史最高收盘价
- **右肩**：1 月 6 日收盘 102,236，比头低，和左肩差不多高
- **颈线**：连接 11 月 26 日的 91,965 和 12 月 30 日的 92,792，每天抬高 24 美元

今天收盘 **95,061**，离颈线 93,011 只有 **2.2%**。

![BTCUSDT 日线，2024-11 至 2025-01-08，头肩顶](/images/trade-analysis/17/decision.png)

```python
t = pd.Timestamp("2025-01-08", tz="UTC")
known = day.loc[:t]                                           # 只用决策当天收盘为止的数据
close = known["close"]
swings = X.zigzag(close, 0.05)
print(swings[swings["time"] >= "2024-11-01"].to_string(index=False))
found = Pt.head_and_shoulders(close, swings)
row = found.iloc[-1]
print(row[["left", "neck_1", "head", "neck_2", "right", "confirmed_at", "left_price", "head_price", "right_price",
           "height"]].to_string())
pos = {x: k for k, x in enumerate(close.index)}
slope = (swings.set_index("time")["price"][row["neck_2"]] - swings.set_index("time")["price"][row["neck_1"]]) / \
        (pos[row["neck_2"]] - pos[row["neck_1"]])
neck_today = swings.set_index("time")["price"][row["neck_1"]] + slope * (pos[t] - pos[row["neck_1"]])
print(f"颈线每天抬高 {slope:,.2f}；1 月 8 日的颈线 {neck_today:,.2f}，收盘 {close[t]:,.2f}，高出 {close[t] / neck_today - 1:.2%}")
print(f"如果跌破，量度目标约为 {neck_today - row['height']:,.0f}（颈线减去高度 {row['height']:,.2f}）")
```

```text
                     time     price  kind              confirmed_at
2024-11-04 00:00:00+00:00  67850.01    -1 2024-11-06 00:00:00+00:00
2024-11-22 00:00:00+00:00  98892.00     1 2024-11-25 00:00:00+00:00
2024-11-26 00:00:00+00:00  91965.16    -1 2024-11-29 00:00:00+00:00
2024-12-17 00:00:00+00:00 106133.74     1 2024-12-18 00:00:00+00:00
2024-12-30 00:00:00+00:00  92792.05    -1 2025-01-03 00:00:00+00:00
2025-01-06 00:00:00+00:00 102235.60     1 2025-01-07 00:00:00+00:00
left            2024-11-22 00:00:00+00:00
neck_1          2024-11-26 00:00:00+00:00
head            2024-12-17 00:00:00+00:00
neck_2          2024-12-30 00:00:00+00:00
right           2025-01-06 00:00:00+00:00
confirmed_at    2025-01-07 00:00:00+00:00
left_price                        98892.0
head_price                      106133.74
right_price                      102235.6
height                       13657.853824
颈线每天抬高 24.32；1 月 8 日的颈线 93,010.93，收盘 95,060.61，高出 2.20%
如果跌破，量度目标约为 79,353（颈线减去高度 13,657.85）
```

注意第一行代码：`day.loc[:t]`，**只用 1 月 8 日收盘为止的数据**来找摆动点。右肩（1 月 6 日）在 1 月 7 日才被确认，所以今天这个形态是真实可见的，不是事后画的。

教科书上说：头肩顶是最可靠的顶部形态之一，跌破颈线之后，价格至少会跌一个「头到颈线的高度」，这里就是跌到 79,353 附近。

你会怎么做？

- A. **现在就做空**：右肩已经成形，止损放在右肩 102,236 上方
- B. **等收盘跌破颈线再做空**：这是教科书的标准做法，止损同样放在右肩上方
- C. **不做**：一个形态说明不了什么

**先写下你的选择。** 第六节揭晓，第七、八节看「等跌破」这条规矩在全部历史上意味着什么。

---

## 二、看星座

### 打个比方

夜空里的星星本来是一个个独立的光点。人把几颗星连起来，就有了猎户座、北斗七星。

- **摆动点是星星**：第 8 篇的 ZigZag 从价格里挑出的高点和低点。
- **ZigZag 的阈值是「多亮的星才算数」**：阈值 3% 能看见很多暗星，阈值 10% 只剩几颗最亮的。
- **形态是把星星连成的图案**：五颗星一高一低、中间最高，叫头肩顶。
- **参数是连线的规矩**：两肩要差不多高——差多少算「差不多」？颈线要大致水平——斜多少还算？

星座有三件事值得记住：

1. **同一片星空，换一个亮度门槛，看到的星座就不一样。** 这是第五节的「调参数」。
2. **星座是人画的，不是星星自己排的。** 星星之间几何上的巧合，随机撒一把点也会出现。这是第九节三角形和楔形的故事。
3. **只数「应验」的星象，星象就显得很准。** 古人记下了彗星出现后的大事，没记下彗星出现后什么都没发生的年份。这是第七节「突破颈线才算成立」的故事。

---

## 三、把头肩顶写成规则

### 规则

`talab.patterns.head_and_shoulders` 在摆动点序列里找**五个相邻的摆动点**：高、低、高、低、高，分别是左肩、颈线点 1、头、颈线点 2、右肩。

> 颈线：过两个颈线点的直线，向右延长
>
> 高度：头的价格 - 头所在位置的颈线值
>
> 量度目标：跌破时的颈线值 - 高度

形状条件（括号里是默认参数）：

1. 头比两个肩都高
2. 两个肩的高度差 ≤ 高度的 30%
3. 两个颈线点的高度差 ≤ 高度的 50%（颈线不能太斜）
4. 头到右肩的根数 ÷ 左肩到头的根数，在 1/3 到 3 之间（两边不能太不对称）

还有两个时刻：

- **confirmed_at**：右肩被 ZigZag 确认的那一根。在这之前右肩还不存在，形态也还不存在。
- **broken_at**：从 confirmed_at 起，左肩到右肩那么多根 K 线以内，第一次收盘价低于颈线。

头肩底把所有高低颠倒过来。

### 用一个玩具例子走一遍

```python
points = [(0, 100), (10, 110), (16, 102), (28, 120), (36, 104), (44, 112), (60, 96)]
path = np.interp(np.arange(61), [p[0] for p in points], [p[1] for p in points])
toy = pd.Series(path, index=pd.date_range("2024-01-01", periods=61, freq="D"))
toy_swings = X.zigzag(toy, 0.05)
print(toy_swings.to_string(index=False))
toy_found = Pt.head_and_shoulders(toy, toy_swings)
print(toy_found.drop(columns=["left", "neck_1", "neck_2"]).round(2).T.to_string())
```

```text
      time  price  kind confirmed_at
2024-01-01  100.0    -1   2024-01-06
2024-01-11  110.0     1   2024-01-16
2024-01-17  102.0    -1   2024-01-21
2024-01-29  120.0     1   2024-02-01
2024-02-06  104.0    -1   2024-02-12
2024-02-14  112.0     1   2024-02-20
                                     0
head               2024-01-29 00:00:00
right              2024-02-14 00:00:00
confirmed_at       2024-02-20 00:00:00
left_price                       110.0
head_price                       120.0
right_price                      112.0
neckline                         105.4
height                            16.8
broken_at          2024-02-21 00:00:00
neckline_at_break                105.5
target                            88.7
```

![把头肩顶写成规则](/images/trade-analysis/17/rules.png)

逐条核对：

1. **五个点**：左肩 110（第 10 根）、颈线点 102（第 16 根）、头 120（第 28 根）、颈线点 104（第 36 根）、右肩 112（第 44 根）。
2. **颈线**：从 102 到 104 用了 20 根，每根抬高 0.1。头在第 28 根，那里的颈线是 102 + 0.1 × 12 = 103.2，**高度** = 120 - 103.2 = **16.8**。
3. **形状条件**：两肩差 2，不超过 16.8 × 30% = 5.04；两个颈线点差 2，不超过 8.4；头到右肩 16 根，左肩到头 18 根，比值 0.89。全部满足。
4. **确认**：右肩 112 之后每根跌 1，第 50 根跌到 106，跌够了 5%（112 × 0.95 = 106.4），右肩在这一根被确认。这时颈线是 105.4，价格还在颈线上方。
5. **跌破**：第 51 根收盘 105，低于颈线 105.5。
6. **目标**：105.5 - 16.8 = **88.7**。

⚠️ 第 4 步很关键：**右肩要等价格从它那里跌够一个阈值才被确认。** 阈值越大，确认越晚，确认的时候价格离颈线越近，甚至已经跌破了。决策点那天价格离颈线只剩 2.2%，一部分原因就在这里：5% 的阈值把右肩确认的时刻推到了下跌途中。

---

## 四、双顶、三角形、楔形、通道

### 双顶和双底

`double_tops` 找**三个相邻的摆动点**：高、低、高。

- 颈线：中间低点的价格（水平线）
- 高度：两个顶里较高的那个 - 颈线
- 形状条件：两个顶的高度差 ≤ 高度的 10%
- 跌破：第二个顶被确认之后，两顶间隔那么多根以内，第一次收盘低于颈线
- 目标：颈线 - 高度

双顶的颈线就是最近一个已确认的摆动低点。所以「双顶跌破颈线」和第 11 篇的「跌破最近的低点」是同一个动作，唯一的区别是前面多了「两个差不多高的顶」这个条件。第八节会专门比较这两者。

### 三角形、楔形、通道

`converging` 用**四个相邻的摆动点**（两高两低）画两条线：上轨连两个高点，下轨连两个低点。然后按两条线的方向命名。

设第一个点处两线之间的宽度为 W，四个点从头到尾一共 T 根。每条线在 T 根里升降的幅度 ÷ W，叫这条线的**斜度**；斜度的绝对值 ≤ 0.2，算水平。

| 上轨 | 下轨 | 名字 | 教科书的说法 |
|---|---|---|---|
| 水平 | 向上 | 上升三角形 | 多数向上突破 |
| 向下 | 水平 | 下降三角形 | 多数向下突破 |
| 向下 | 向上 | 对称三角形 | 顺着原来的趋势突破 |
| 向上 | 向上，而且比上轨陡（在收窄） | 上升楔形 | 多数向下突破 |
| 向下，而且比下轨陡 | 向下 | 下降楔形 | 多数向上突破 |
| 水平 | 水平 | 矩形 | |
| 向上 | 向下 | 扩散 | |
| 同方向，不收窄 | | 通道 | 旗形是一段急涨急跌之后、短时间逆着方向的通道 |

突破：第四个摆动点被确认之后，T 根以内，第一次收盘在上轨上方（向上突破）或下轨下方（向下突破）。

⚠️ 这是「最少的点」版本：两条线各只用两个点。很多书要求每条线至少碰三次，那样找到的形态会少得多，也更「好看」。这是又一个参数（练习 4）。

---

## 五、调参数，识别结果怎么变

「基于摆动点的形态识别器」最大的问题是：**摆动点本身取决于参数**，形态又取决于摆动点。先看换一个 ZigZag 阈值会怎样：

```python
rows = []
for threshold in [0.03, 0.05, 0.08, 0.10, 0.15]:
    sw = X.zigzag(day["close"], threshold)
    hs_top, hs_bottom = Pt.head_and_shoulders(day["close"], sw), Pt.head_and_shoulders(day["close"], sw, "bottom")
    rows.append({"ZigZag 阈值": f"{threshold:.0%}", "摆动点": len(sw), "头肩顶": len(hs_top), "头肩底": len(hs_bottom),
                 "双顶": len(Pt.double_tops(day["close"], sw)), "双底": len(Pt.double_tops(day["close"], sw, "bottom")),
                 "三角形和楔形": int(Pt.converging(day["close"], sw)["name"].str.contains("三角|楔").sum()),
                 "决策点的头肩顶在不在": bool(((hs_top["head"] == pd.Timestamp("2024-12-17", tz="UTC"))
                                              & (hs_top["right"] == pd.Timestamp("2025-01-06", tz="UTC"))).any())})
print("BTC 日线，换 ZigZag 阈值：")
print(pd.DataFrame(rows).to_string(index=False))
rows = []
sw = X.zigzag(day["close"], 0.05)
for tol in [0.1, 0.2, 0.3, 0.5, 1.0]:
    rows.append({"两肩高度差上限（占高度）": tol, "头肩顶": len(Pt.head_and_shoulders(day["close"], sw, shoulder_tol=tol)),
                 "双顶": len(Pt.double_tops(day["close"], sw, tol=tol))})
print("BTC 日线，ZigZag 5%，换两肩（两顶）的高度差上限：")
print(pd.DataFrame(rows).to_string(index=False))
base = Pt.head_and_shoulders(h4["close"], X.zigzag(h4["close"], 0.02))
for threshold in [0.015, 0.025, 0.03]:
    other = Pt.head_and_shoulders(h4["close"], X.zigzag(h4["close"], threshold))
    same = base["head"].isin(other["head"]).mean()
    print(f"BTC 4 小时线：阈值 2% 找到的 {len(base)} 个头肩顶里，阈值换成 {threshold:.1%} 还能找到（头在同一根 K 线）的占 {same:.1%}；"
          f"那边一共 {len(other)} 个")
```

```text
BTC 日线，换 ZigZag 阈值：
ZigZag 阈值  摆动点  头肩顶  头肩底  双顶  双底  三角形和楔形  决策点的头肩顶在不在
       3%  585   21   20  25  28     295       False
       5%  344   15   11  15  21     180        True
       8%  219    7    3   5  17     103       False
      10%  159    6    2   6  10      71       False
      15%   85    2    1   1   5      43       False
BTC 日线，ZigZag 5%，换两肩（两顶）的高度差上限：
 两肩高度差上限（占高度）  头肩顶  双顶
          0.1    4  15
          0.2   11  30
          0.3   15  49
          0.5   18  90
          1.0   23 171
BTC 4 小时线：阈值 2% 找到的 76 个头肩顶里，阈值换成 1.5% 还能找到（头在同一根 K 线）的占 73.7%；那边一共 91 个
BTC 4 小时线：阈值 2% 找到的 76 个头肩顶里，阈值换成 2.5% 还能找到（头在同一根 K 线）的占 68.4%；那边一共 63 个
BTC 4 小时线：阈值 2% 找到的 76 个头肩顶里，阈值换成 3.0% 还能找到（头在同一根 K 线）的占 47.4%；那边一共 57 个
```

![同一段 BTC 日线，换一个 ZigZag 阈值](/images/trade-analysis/17/params.png)

四件事：

1. **阈值从 3% 换到 15%，头肩顶从 21 个变成 2 个，三角形和楔形从 295 个变成 43 个。** 形态的数量主要由你选的阈值决定。
2. **决策点的那个头肩顶，只在 5% 下存在。** 3% 的时候同一段行情里多出很多小摆动点，这五个点不再相邻；8% 的时候左肩和颈线点 1 都不够格当摆动点。图里能看得很清楚：3% 找到的两个头肩顶在别的位置，8% 一个都没有。
3. **两肩高度差的上限从 10% 放宽到 100%，头肩顶从 4 个变成 23 个，双顶从 15 个变成 171 个。**「两个顶差不多高」这句话，在代码里差一个数字，结果差十倍。
4. **稳定性**：BTC 4 小时线阈值 2% 找到的 76 个头肩顶，换成 2.5% 只剩 68.4% 还在，换成 3% 只剩不到一半。

这就是动手部分要你亲眼看到的：**「图上有一个头肩顶」不是一个客观事实，而是「在这组参数下，有一个头肩顶」。** 统计形态之前，参数必须先定好、写下来；统计之后再调参数，就是在挑结果（第 13 篇误用 7）。

这一篇下面的统计，阈值都在看结果之前按「大约 1.2 到 1.8 倍的 NATR 中位数」定好：SPY 2%、AAPL 3%、BTC 日线 5%、4 小时线 2%、1 小时线 1%。

```text
SPY 日线：NATR 中位数 1.09%
AAPL 日线：NATR 中位数 2.08%
BTC 日线：NATR 中位数 4.40%
BTC 4 小时线：NATR 中位数 1.64%
BTC 1 小时线：NATR 中位数 0.79%
```

### ✋ 小检查 1

(a) 一个头肩顶：左肩 50、颈线点 44、头 58、颈线点 46、右肩 51，两个颈线点之间 20 根、颈线点 1 到头 8 根。高度是多少？按默认参数，两肩高度差的上限是多少？这个形态成立吗？

(b) 同一个形态，如果跌破时的颈线是 46.5，量度目标是多少？

(c) 为什么 ZigZag 阈值越大，右肩被确认的时候，价格往往离颈线越近？

答案在文末。

---

## 六、揭晓

**第二天就跌破了颈线。然后 11 天创出历史新高。再过 7 周，量度目标也到了。**

![揭晓：BTCUSDT 日线，2024-11 至 2025-03-15](/images/trade-analysis/17/reveal.png)

```python
c = day["close"]
i = c.index.get_loc(t)
for n in [1, 2, 5, 12, 30, 61]:
    print(f"{n} 天后（{c.index[i + n].date()}）：收盘 {c.iloc[i + n]:,.2f}（{c.iloc[i + n] / c[t] - 1:+.2%}）")
full = Pt.head_and_shoulders(c, X.zigzag(c, 0.05))
pattern = full[full["head"] == pd.Timestamp("2024-12-17", tz="UTC")].iloc[0]
print(f"跌破颈线：{pattern['broken_at'].date()}，那天的颈线 {pattern['neckline_at_break']:,.2f}，收盘 {c[pattern['broken_at']]:,.2f}；"
      f"量度目标 {pattern['target']:,.2f}")
after = day.loc[pattern["broken_at"]:].iloc[1:]
over = after[after["close"] > pattern["right_price"]].index[0]
print(f"跌破之后，收盘价第一次回到右肩 {pattern['right_price']:,.2f} 上方：{over.date()}（收盘 {c[over]:,.2f}）；"
      f"之后到 1 月 31 日的最高价 {day['high'].loc[pattern['broken_at']:pd.Timestamp('2025-01-31', tz='UTC')].max():,.2f}")
reach = after[after["close"] <= pattern["target"]].index[0]
print(f"收盘价第一次到达量度目标：{reach.date()}（收盘 {c[reach]:,.2f}），跌破颈线之后第 {c.index.get_loc(reach) - c.index.get_loc(pattern['broken_at'])} 天")
```

```text
1 天后（2025-01-09）：收盘 92,552.49（-2.64%）
2 天后（2025-01-10）：收盘 94,726.11（-0.35%）
5 天后（2025-01-13）：收盘 94,536.10（-0.55%）
12 天后（2025-01-20）：收盘 102,260.01（+7.57%）
30 天后（2025-02-07）：收盘 96,506.80（+1.52%）
61 天后（2025-03-10）：收盘 78,595.86（-17.32%）
跌破颈线：2025-01-09，那天的颈线 93,035.25，收盘 92,552.49；量度目标 79,377.40
跌破之后，收盘价第一次回到右肩 102,235.60 上方：2025-01-17（收盘 104,077.48）；之后到 1 月 31 日的最高价 109,588.00
收盘价第一次到达量度目标：2025-03-10（收盘 78,595.86），跌破颈线之后第 60 天
```

- **1 月 9 日**收盘 92,552，低于当天的颈线 93,035，形态「成立」了。
- **1 月 17 日**收盘 104,077，回到右肩 102,236 上方；1 月 20 日盘中 109,588，**历史新高**。
- **3 月 10 日**收盘 78,596，到达量度目标 79,377。

三个选择：

- **选 A（1 月 8 日做空，止损右肩上方）的**：1 月 17 日最高价 105,865 碰到 102,236 的止损，亏 7.5%。
- **选 B（1 月 9 日收盘跌破后做空）的**：同样在 1 月 17 日被止损，入场价更低，亏 10.5%。
- **选 C（不做）的**：什么都没发生。

量度目标最后是到了，但这时候 A 和 B 早就被止损出局了。**如果你只看这张图的左边一半和右边一半，会觉得「头肩顶 → 跌破 → 到达目标」，一个完美的教科书案例。** 中间那次历史新高，在「形态成立率」的统计里通常不会出现，因为它既算「跌破了」，又算「到达目标了」。

---

## 七、「突破颈线才算成立」

### 书上的统计是怎么算的

很多形态统计的写法是：「头肩顶**跌破颈线之后**，X% 到达了量度目标。」

这句话本身没错，但它回答的是**已经跌破**的情况。在决策点那天（1 月 8 日），你还不知道会不会跌破。如果你用这个 X% 来决定「右肩一出现就做空」，你就犯了错：**你拿一个用到了未来信息（后来跌破了）的数字，去指导一个在当时做的决定。**

这和第 14 篇的「事后划分状态」、第 13 篇的「从事后才知道的高点算起」是同一类错误：**把只有事后才知道的条件，放进了统计的分组里。**

### 量一量虚高了多少

同一笔交易：**右肩被确认那一根收盘入场，止损放在右肩外侧，目标是量度目标**，看之后 60 根里先碰到哪一个。然后分两种方式统计：

- **全部候选**：决策时刻能看到的所有形态，不管后来有没有跌破
- **只算后来突破的**：同样的交易，只统计那些后来跌破了颈线的

```python
def trade(close, high, low, start, stop, target, sign, horizon=60):
    """在第 start 根收盘价做空（sign = 1）或做多（sign = -1），之后 horizon 根里先碰到目标记 1，先碰到止损记 0。

    同一根 K 线两个都碰到，分不清先后，按先碰到止损算；horizon 根里都没碰到记 NaN。
    """
    for j in range(start + 1, min(start + 1 + horizon, len(close))):
        hit_target = low[j] <= target if sign == 1 else high[j] >= target
        hit_stop = high[j] >= stop if sign == 1 else low[j] <= stop
        if hit_stop:
            return 0.0
        if hit_target:
            return 1.0
    return np.nan


def binomial_p(k, n, p0):
    """二项检验的双侧 p 值：成功概率为 p0 时，出现概率不高于「恰好 k 次」的所有结果的概率之和。"""
    probs = [math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(n + 1)]
    return sum(p for p in probs if p <= probs[k] * (1 + 1e-9))


def plain_breaks(close, threshold, sign):
    """「普通的跌破」：收盘价第一次跌破最近一个已确认的摆动低点的那一根（sign = -1 时是升破高点）。"""
    levels = X.trend_state(X.zigzag(close, threshold), close, close)
    line = levels["last_low"] if sign == 1 else levels["last_high"]
    crossed = (sign * (close - line) < 0) & (sign * (close.shift(1) - line.shift(1)) >= 0)
    return np.flatnonzero(crossed.to_numpy())


kinds = [("头肩顶", Pt.head_and_shoulders, "top"), ("头肩底", Pt.head_and_shoulders, "bottom"),
         ("双顶", Pt.double_tops, "top"), ("双底", Pt.double_tops, "bottom")]
rows_a, rows_b = [], []
for name, df in datasets:
    c = df["close"]
    high, low, close_ = df["high"].to_numpy(float), df["low"].to_numpy(float), c.to_numpy(float)
    sw = X.zigzag(c, thresholds[name])
    atr = I.atr(df["high"], df["low"], c).to_numpy()
    where = {x: k for k, x in enumerate(c.index)}
    for label, func, kind in kinds:
        sign = 1 if kind == "top" else -1
        stop_column = "right_price" if func is Pt.head_and_shoulders else "second_price"
        found = func(c, sw, kind)
        if found.empty:
            continue
        target = found["neckline"] - sign * found["height"]                   # 决策时刻就能算出的目标
        at_seen = np.array([trade(close_, high, low, where[x], s, g, sign)
                            for x, s, g in zip(found["confirmed_at"], found[stop_column], target)])
        broken = found["broken_at"].notna().to_numpy()
        rows_a.append({"数据": name, "形态": label, "候选": len(found), "后来突破": int(broken.sum()),
                       "决策时刻入场 全部候选": np.nanmean(at_seen), "只算后来突破的": np.nanmean(at_seen[broken])})
        plain = plain_breaks(c, thresholds[name], sign)
        plain = plain[~np.isnan(atr[plain])]
        wins, need, plain_rate, r_multiple, when = [], [], [], [], []
        for x in found[broken].itertuples():
            b = where[x.broken_at]
            stop = getattr(x, stop_column)
            goal = x.target
            risk, reward = abs(stop - close_[b]), abs(close_[b] - goal)
            outcome = trade(close_, high, low, b, stop, goal, sign)
            if np.isnan(outcome) or risk == 0:
                continue
            wins.append(outcome)
            when.append(x.broken_at)
            need.append(risk / (risk + reward))
            r_multiple.append(reward / risk if outcome == 1 else -1.0)
            risk_atr, reward_atr = risk / atr[b], reward / atr[b]                 # 对照用 ATR 为单位的同样距离
            starts = rng.choice(plain, 30)
            plain_rate.append(np.nanmean([trade(close_, high, low, s, close_[s] + sign * risk_atr * atr[s],
                                                close_[s] - sign * reward_atr * atr[s], sign) for s in starts]))
        if wins:
            k, n = int(sum(wins)), len(wins)
            early = np.array(when) < pd.Timestamp("2022-01-01", tz=c.index.tz)
            rows_b.append({"数据": name, "形态": label, "交易": n, "胜率": k / n, "盈亏平衡胜率": np.mean(need),
                           "平均盈亏（R）": np.mean(r_multiple), "普通跌破 同样距离": np.mean(plain_rate),
                           "p": binomial_p(k, n, float(np.mean(plain_rate))),
                           "2022 年前 胜率": np.mean(np.array(wins)[early]) if early.any() else np.nan,
                           "2022 年起 胜率": np.mean(np.array(wins)[~early]) if (~early).any() else np.nan})
table_a = pd.DataFrame(rows_a)
print("按教科书的止损（右肩或第二个顶外侧）和量度目标，先碰到目标的比例：")
print(table_a.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
table_b = pd.DataFrame(rows_b)
print("突破颈线的那根收盘入场，止损和目标同上：")
print(table_b.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
```

```text
按教科书的止损（右肩或第二个顶外侧）和量度目标，先碰到目标的比例：
       数据  形态  候选  后来突破  决策时刻入场 全部候选  只算后来突破的
   SPY 日线 头肩顶   5     5        0.400    0.400
   SPY 日线 头肩底   2     2        0.000    0.000
   SPY 日线  双顶  14     7        0.500    0.857
   SPY 日线  双底  13     8        0.545    0.833
  AAPL 日线 头肩顶   5     5        0.200    0.200
  AAPL 日线 头肩底   6     5        0.600    0.750
  AAPL 日线  双顶   4     3        0.250    0.333
  AAPL 日线  双底  17    11        0.438    0.545
   BTC 日线 头肩顶  15    12        0.333    0.417
   BTC 日线 头肩底  11    10        0.636    0.700
   BTC 日线  双顶  15     6        0.333    0.667
   BTC 日线  双底  21    13        0.476    0.692
BTC 4 小时线 头肩顶  76    60        0.294    0.370
BTC 4 小时线 头肩底  56    44        0.320    0.359
BTC 4 小时线  双顶  83    33        0.388    0.871
BTC 4 小时线  双底 101    46        0.258    0.452
BTC 1 小时线 头肩顶 256   189        0.393    0.517
BTC 1 小时线 头肩底 235   174        0.362    0.476
BTC 1 小时线  双顶 345   171        0.422    0.683
BTC 1 小时线  双底 339   172        0.424    0.687
```

![只统计「成立」的形态，胜率凭空高出一截](/images/trade-analysis/17/conditioning.png)

**同一笔交易、同一个入场时刻，只是换了统计的范围：**

- BTC 4 小时线的双顶：全部候选 38.8%，只算后来跌破的 **87.1%**
- BTC 1 小时线的双顶：42.2% 对 68.3%；双底 42.4% 对 68.7%
- BTC 日线的双顶：33.3% 对 66.7%

**头肩形的虚高小一些**（比如 1 小时线头肩顶 39.3% 对 51.7%），因为头肩形的候选本来就大多会跌破（1 小时线 256 个里 189 个），而双顶只有一半左右会跌破。**被排除掉的那部分越多，剩下的看起来越好。**

还有一件事：「全部候选」这一列，三组 BTC 数据里有 11 格低于 50%，最低 25.8%。量度目标通常比右肩到入场价的距离远，所以**在右肩确认时就进场，胜率天然偏低**；这本身不说明亏钱，要和盈亏平衡胜率比，下一节就做这件事。

---

## 八、按教科书交易：跌破之后再进场

选 B 的做法是完全正当的：**等收盘跌破颈线，那一根收盘入场**，止损放在右肩（双顶是第二个顶）外侧，目标是量度目标。这时候没有用到任何未来信息。它赚钱吗？

要回答「赚不赚钱」，要看两个对照：

1. **盈亏平衡胜率** = 止损距离 ÷ (止损距离 + 目标距离)。胜率高于它才赚钱。
2. **普通的跌破前低**：第 11 篇说过，BTC 1 小时线上「收盘跌破最近一个已确认的低点」本身就有一点延续。所以要问的是：**头肩形、双顶这些形状，比普通的跌破多出了什么？** 对照组取同一组数据里所有「第一次收盘跌破最近已确认低点」的 K 线，用**同样的止损和目标距离**（以 ATR 为单位）做同样的交易。

```text
突破颈线的那根收盘入场，止损和目标同上：
       数据  形态  交易    胜率  盈亏平衡胜率  平均盈亏（R）  普通跌破 同样距离     p  2022 年前 胜率  2022 年起 胜率
   SPY 日线 头肩顶   5 0.400   0.451   -0.323      0.393 1.000       1.000       0.250
   SPY 日线 头肩底   2 0.000   0.448   -1.000      0.626 0.140       0.000       0.000
   SPY 日线  双顶   7 0.857   0.648    0.352      0.558 0.142       0.800       1.000
   SPY 日线  双底   6 0.833   0.624    0.343      0.741 1.000       1.000       0.750
  AAPL 日线 头肩顶   5 0.600   0.346    0.883      0.304 0.168       0.333       1.000
  AAPL 日线 头肩底   4 0.750   0.469    0.831      0.471 0.349       0.750         NaN
  AAPL 日线  双顶   3 0.333   0.573   -0.537      0.567 0.583       0.500       0.000
  AAPL 日线  双底  11 0.636   0.601    0.056      0.668 0.760       0.333       1.000
   BTC 日线 头肩顶  12 0.500   0.442    0.187      0.342 0.361       0.600       0.429
   BTC 日线 头肩底  10 0.700   0.519    0.342      0.514 0.346       0.750       0.667
   BTC 日线  双顶   6 0.667   0.619    0.059      0.586 1.000       0.333       1.000
   BTC 日线  双底  13 0.692   0.606    0.125      0.570 0.417       0.667       0.714
BTC 4 小时线 头肩顶  55 0.400   0.428   -0.153      0.440 0.589       0.346       0.448
BTC 4 小时线 头肩底  38 0.421   0.465   -0.067      0.515 0.260       0.318       0.562
BTC 4 小时线  双顶  32 0.844   0.705    0.204      0.710 0.119       0.917       0.800
BTC 4 小时线  双底  43 0.512   0.622   -0.162      0.656 0.054       0.586       0.357
BTC 1 小时线 头肩顶 182 0.549   0.471    0.214      0.456 0.014       0.636       0.391
BTC 1 小时线 头肩底 163 0.540   0.466    0.237      0.478 0.117       0.531       0.554
BTC 1 小时线  双顶 162 0.741   0.664    0.136      0.646 0.011       0.787       0.648
BTC 1 小时线  双底 162 0.722   0.653    0.101      0.658 0.097       0.709       0.746
```

- **日线上样本太少**：每一格 2 到 13 笔，胜率从 0% 到 86% 都有，说明不了什么。
- **BTC 4 小时线**：四种形态都没有显著超过普通跌破，头肩顶、头肩底、双底的平均盈亏是负的。
- **BTC 1 小时线**：头肩顶 54.9% 对普通跌破的 45.6%（182 笔，p 0.014），平均 +0.214 R；双顶 74.1% 对 64.6%（162 笔，p 0.011）。头肩底和双底方向一样，但不显著。

这是这门课到目前为止，**第一个看起来像样的正面结果**。但右边两列必须一起看：

- 1 小时线头肩顶：**2022 年以前胜率 63.6%，2022 年起 39.1%**，低于 47.1% 的盈亏平衡胜率。
- 1 小时线双顶：78.7% → 64.8%，后者低于 66.4% 的盈亏平衡胜率。

**优势几乎全部来自前几年，最近几年消失了**，而且还没扣成本（1 小时线一年几十笔交易，第 28 篇会加上）。20 次检验里 2 次显著，都在同一组数据上。

### ✋ 小检查 2

(a) 某次头肩顶跌破时，收盘价 100，右肩 106，量度目标 88。盈亏平衡胜率是多少？如果胜率是 40%，平均每笔盈亏是多少 R？

(b) 第七节的表里，「只算后来突破的」比「全部候选」高。有人说：「这正说明等突破是对的，突破之后胜率更高。」这句话错在哪里？（提示：第八节的交易，入场时刻和第七节不同）

(c) BTC 1 小时线头肩顶的优势，2022 年前 63.6%、2022 年起 39.1%。你能想到哪些原因？如果要用它交易，你还需要什么证据？

答案在文末。

---

## 九、三角形和楔形：规律来自哪里

### 突破方向

教科书说：上升楔形多数向下突破，下降楔形多数向上突破，上升三角形多数向上突破。先看数据：

```python
def label_test(values, flag, n=2000):
    """flag 为真的组减去其余的平均值；把标签随机打乱 n 次，看差距不小于实际的比例（第 10 篇）。"""
    v, f = np.asarray(values, float), np.asarray(flag, bool)
    ok = ~np.isnan(v)
    v, f = v[ok], f[ok]
    if f.sum() == 0 or (~f).sum() == 0:
        return np.nan, np.nan
    observed = v[f].mean() - v[~f].mean()
    sims = np.array([v[p].mean() - v[~p].mean() for p in (rng.permutation(f) for _ in range(n))])
    return observed, (np.abs(sims) >= abs(observed)).mean()


def shuffle_bars(df, rng):
    """打乱 K 线顺序：保留每根 K 线相对前一根收盘价的形状，重新拼成价格（第 9 篇）。"""
    relative = np.log(df[Pt.OHLC].div(df["close"].shift(1), axis=0))
    relative = relative.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    previous_close = df["close"].iloc[0] * np.exp(relative["close"].cumsum().shift(1, fill_value=0))
    out = np.exp(relative[Pt.OHLC]).mul(previous_close, axis=0)
    out.index = df.index[1:]
    return out


names = ["上升三角形", "下降三角形", "对称三角形", "上升楔形", "下降楔形", "矩形", "通道", "扩散"]


def up_share(df, threshold):
    found = Pt.converging(df["close"], X.zigzag(df["close"], threshold))
    found = found[found["broken_at"].notna()]
    return found.groupby("name")["direction"].apply(lambda d: (d == 1).mean()).reindex(names)


rows = []
for name, df in datasets:
    c = df["close"]
    a = I.atr(df["high"], df["low"], c)
    found = Pt.converging(c, X.zigzag(c, thresholds[name]))
    found = found[found["broken_at"].notna() & a.reindex(found["broken_at"]).notna().to_numpy()]
    found["顺向"] = X.first_passage(c, df["high"], df["low"], a, found["broken_at"], found["direction"])
    shuffled = pd.concat([up_share(shuffle_bars(df, rng), thresholds[name]) for _ in range(10)], axis=1).mean(axis=1)
    for shape in names:
        m = (found["name"] == shape).to_numpy()
        _, p = label_test(found["顺向"], m)
        rows.append({"数据": name, "形态": shape, "突破": int(m.sum()), "向上突破": (found["direction"][m] == 1).mean(),
                     "打乱后 向上突破": shuffled[shape], "顺着突破方向": found["顺向"][m].mean(),
                     "其他形态的突破": found["顺向"][~m].mean(), "p": p})
table_c = pd.DataFrame(rows)
print(table_c.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print(f"「顺着突破方向」一共 {table_c['p'].notna().sum()} 次检验，p < 0.05 的有 {(table_c['p'] < 0.05).sum()} 次")
```

```text
       数据    形态   突破  向上突破  打乱后 向上突破  顺着突破方向  其他形态的突破     p
   SPY 日线 上升三角形   15 0.267     0.348   0.214    0.514 0.048
   SPY 日线 下降三角形   19 0.526     0.727   0.500    0.486 1.000
   SPY 日线 对称三角形   13 0.538     0.404   0.333    0.500 0.385
   SPY 日线  上升楔形   34 0.176     0.229   0.394    0.512 0.242
   SPY 日线  下降楔形   19 0.895     0.809   0.722    0.457 0.043
   SPY 日线    矩形    9 0.778     0.774   0.875    0.467 0.034
   SPY 日线    通道   49 0.327     0.440   0.458    0.500 0.729
   SPY 日线    扩散    9 0.333     0.674   0.857    0.470 0.055
  AAPL 日线 上升三角形   12 0.417     0.320   0.667    0.494 0.499
  AAPL 日线 下降三角形   24 0.792     0.715   0.591    0.491 0.511
  AAPL 日线 对称三角形   16 0.625     0.497   0.600    0.494 0.602
  AAPL 日线  上升楔形   44 0.227     0.278   0.310    0.558 0.005
  AAPL 日线  下降楔形   29 0.724     0.852   0.429    0.516 0.412
  AAPL 日线    矩形    1 1.000     0.701   0.000    0.505 0.503
  AAPL 日线    通道   67 0.463     0.426   0.621    0.450 0.046
  AAPL 日线    扩散   15 0.533     0.687   0.429    0.509 0.582
   BTC 日线 上升三角形   20 0.450     0.355   0.556    0.580 1.000
   BTC 日线 下降三角形   40 0.725     0.699   0.733    0.554 0.082
   BTC 日线 对称三角形   18 0.500     0.484   0.538    0.580 0.778
   BTC 日线  上升楔形   48 0.188     0.235   0.537    0.587 0.593
   BTC 日线  下降楔形   53 0.792     0.803   0.575    0.578 1.000
   BTC 日线    矩形    6 0.333     0.444   0.400    0.582 0.649
   BTC 日线    通道   66 0.515     0.466   0.545    0.588 0.633
   BTC 日线    扩散   28 0.500     0.625   0.609    0.574 0.837
BTC 4 小时线 上升三角形  144 0.347     0.341   0.514    0.530 0.763
BTC 4 小时线 下降三角形  180 0.689     0.681   0.593    0.520 0.110
BTC 4 小时线 对称三角形  137 0.438     0.479   0.471    0.534 0.260
BTC 4 小时线  上升楔形  252 0.214     0.233   0.467    0.540 0.064
BTC 4 小时线  下降楔形  233 0.781     0.816   0.547    0.525 0.619
BTC 4 小时线    矩形   24 0.458     0.466   0.400    0.531 0.257
BTC 4 小时线    通道  491 0.487     0.489   0.553    0.517 0.257
BTC 4 小时线    扩散  105 0.505     0.532   0.525    0.529 1.000
BTC 1 小时线 上升三角形  622 0.310     0.328   0.487    0.532 0.063
BTC 1 小时线 下降三角形  634 0.662     0.688   0.531    0.527 0.885
BTC 1 小时线 对称三角形  575 0.489     0.509   0.537    0.526 0.688
BTC 1 小时线  上升楔形  953 0.168     0.208   0.544    0.524 0.326
BTC 1 小时线  下降楔形  916 0.784     0.808   0.498    0.533 0.090
BTC 1 小时线    矩形   86 0.477     0.502   0.515    0.528 0.896
BTC 1 小时线    通道 1852 0.487     0.493   0.537    0.523 0.357
BTC 1 小时线    扩散  463 0.464     0.510   0.551    0.525 0.336
「顺着突破方向」一共 40 次检验，p < 0.05 的有 5 次
```

「向上突破」这一列：

- **上升楔形**：只有 16.8% 到 22.7% 向上突破，**绝大多数向下**，和教科书一致。
- **下降楔形**：72.4% 到 89.5% 向上突破，也和教科书一致。
- **上升三角形**：只有 26.7% 到 45.0% 向上突破，**和教科书相反**。
- **下降三角形**：52.6% 到 79.2% 向上突破，同样相反。

然后看旁边一列「打乱后 向上突破」：**把 K 线顺序打乱、拼成一条没有任何记忆的随机价格，比例几乎一模一样。** 4 小时线的上升楔形 21.4% 对打乱后 23.3%，下降楔形 78.1% 对 81.6%，上升三角形 34.7% 对 34.1%。

![三角形和楔形的突破方向：真实价格和打乱的价格](/images/trade-analysis/17/triangles.png)

### 为什么随机价格也有这个规律

因为方向是**识别规则的几何**决定的。两条线在收窄，价格夹在中间。**哪条线朝价格移动得更快，价格就更容易先碰到它。**

- 上升楔形：两条线都向上，下轨更陡。下轨追着价格往上走，价格更容易先从下轨掉出去。
- 上升三角形：上轨不动，下轨向上。只有下轨在追价格，所以向下突破更多。
- 下降三角形、下降楔形：反过来，上轨追着价格往下走，向上突破更多。
- 对称三角形、通道：两边速度差不多，接近一半一半。

这个道理对随机价格一样成立。所以「上升楔形多数向下突破」是**真的**，但它是你的画线方式带来的，**不是市场告诉你的**。至于上升三角形和教科书相反：很多书里的上升三角形要求价格多次碰到水平的上轨，那是另一种画法，结果也会不同。

### 突破之后

「顺着突破方向」这一列，看的是突破之后先碰到顺向 2 ATR 的比例，和其他形态的突破比：

- **40 次检验，5 次 p < 0.05**，全在美股日线，样本 9 到 67 次（比如 AAPL 上升楔形 31.0% 对 55.8%，更差；SPY 下降楔形 72.2% 对 45.7%，更好）。
- BTC 4 小时线和 1 小时线上，样本几百到上千次，**一次都不显著**，差距都在几个百分点以内。

**形态的名字，没有给突破之后的走势带来可测量的信息。**

---

## 十、talab.patterns：第二部分

### 新增了什么

| 函数 | 作用 |
|---|---|
| `head_and_shoulders` | 头肩顶 / 头肩底的全部候选：五个摆动点、颈线、高度、确认时刻、跌破时刻、量度目标 |
| `double_tops` | 双顶 / 双底的全部候选 |
| `converging` | 用最近两高两低画两条线，命名为三角形、楔形、矩形、扩散或通道，记录突破的时刻和方向 |

三个函数的共同约定：**返回全部候选，不只是成立的。** 每一行在 confirmed_at 那一刻就存在，broken_at 是之后才知道的事。这样才能做第七节那种比较。

`trade`、`plain_breaks`、`binomial_p` 这些只在这一篇分析用的函数**不放进模块**，只在 `docs/trade-analysis/analysis/17_chart_patterns.py` 里。

### 代码

```python
# ---------------------------------------------------------------------------
# 四、图表形态（第 17 篇）
# ---------------------------------------------------------------------------
#
# 图表形态由摆动点（structure.zigzag 或 structure.fractals）连成。每个函数返回全部「候选形态」：
# 最后一个摆动点被确认的那一刻（confirmed_at），形状条件已经满足，就记一行，不管之后有没有突破。
# broken_at 是之后第一次收盘越过颈线（或趋势线）的时刻，等不到就是 NaT。
# 这样既能统计「成立的形态」，也能统计「当时看得到、后来没有成立的形态」。

def _runs(swings: pd.DataFrame, kinds: list[int]) -> list[pd.DataFrame]:
    """按时间排序，找出种类依次等于 kinds 的每一组相邻摆动点。"""
    ordered = swings.sort_values("time").reset_index(drop=True)
    k = ordered["kind"].to_numpy()
    n = len(kinds)
    return [ordered.iloc[i:i + n] for i in range(len(ordered) - n + 1) if list(k[i:i + n]) == kinds]


def _first_close_beyond(close: np.ndarray, start: int, stop: int, line, sign: int):
    """从第 start 根到第 stop 根（不含），第一次 sign × (收盘价 - line(根号)) < 0 的根号；没有返回 None。"""
    for j in range(start, min(stop, len(close))):
        if sign * (close[j] - line(j)) < 0:
            return j
    return None


def head_and_shoulders(close: pd.Series, swings: pd.DataFrame, kind: str = "top", shoulder_tol: float = 0.3,
                       neck_tol: float = 0.5, time_ratio: float = 3.0, wait: int | None = None) -> pd.DataFrame:
    """头肩顶（kind="top"）或头肩底（kind="bottom"）的全部候选。

    头肩顶是五个相邻的摆动点：左肩（高）、颈线点 1（低）、头（高）、颈线点 2（低）、右肩（高）。
    颈线：连接两个颈线点的直线，向右延长。高度：头的价格减去头所在位置的颈线值。
    形状条件：
    1. 头比两个肩都高
    2. 两个肩的高度差不超过高度的 shoulder_tol
    3. 两个颈线点的高度差不超过高度的 neck_tol（颈线不能太斜）
    4. 头到右肩的根数 ÷ 左肩到头的根数，在 1 / time_ratio 到 time_ratio 之间
    confirmed_at：右肩被确认的时刻。在这之前，右肩还不存在，形态也就还不存在。
    broken_at：从 confirmed_at 这一根起，wait 根以内（默认等于左肩到右肩的根数），第一次收盘价低于颈线。
    target：跌破时的颈线值减去高度，也就是经典的「量度目标」；没有跌破为 NaN。
    头肩底把高低全部颠倒：颈线在上方，向上突破，目标在上方。返回的价格都是原始价格，height 总是正数。
    """
    if kind not in ("top", "bottom"):
        raise ValueError('kind 只能是 "top" 或 "bottom"')
    sign = 1 if kind == "top" else -1
    c = close.to_numpy(float)
    pos = {t: i for i, t in enumerate(close.index)}
    rows = []
    for run in _runs(swings, [sign, -sign, sign, -sign, sign]):
        left, neck_1, head, neck_2, right = (sign * run["price"].to_numpy())
        t = [pos[x] for x in run["time"]]
        slope = (neck_2 - neck_1) / (t[3] - t[1])
        line = lambda j, a=neck_1, b=t[1], m=slope: sign * (a + m * (j - b))           # 原始价格上的颈线
        height = head - (neck_1 + slope * (t[2] - t[1]))
        if not (head > left and head > right and height > 0):
            continue
        if abs(left - right) > shoulder_tol * height or abs(neck_2 - neck_1) > neck_tol * height:
            continue
        if not 1 / time_ratio <= (t[4] - t[2]) / (t[2] - t[0]) <= time_ratio:
            continue
        seen = pos[run["confirmed_at"].iloc[4]]
        limit = t[4] + (wait if wait is not None else t[4] - t[0]) + 1
        j = _first_close_beyond(c, seen, limit, line, sign)
        rows.append((*run["time"], run["confirmed_at"].iloc[4], sign * left, sign * head, sign * right,
                     line(seen), height, close.index[j] if j is not None else pd.NaT,
                     line(j) if j is not None else np.nan, line(j) - sign * height if j is not None else np.nan))
    return pd.DataFrame(rows, columns=["left", "neck_1", "head", "neck_2", "right", "confirmed_at", "left_price",
                                       "head_price", "right_price", "neckline", "height", "broken_at",
                                       "neckline_at_break", "target"])


def double_tops(close: pd.Series, swings: pd.DataFrame, kind: str = "top", tol: float = 0.1,
                wait: int | None = None) -> pd.DataFrame:
    """双顶（kind="top"）或双底（kind="bottom"）的全部候选。

    双顶是三个相邻的摆动点：第一个顶（高）、中间的低点、第二个顶（高）。
    颈线：中间低点的价格（水平线）。高度：两个顶中较高的那个减去颈线。
    形状条件：两个顶的高度差不超过高度的 tol。
    confirmed_at：第二个顶被确认的时刻。
    broken_at：从 confirmed_at 起，wait 根以内（默认等于两个顶之间的根数），第一次收盘价低于颈线。
    target：颈线减去高度（双底是加上高度），不管有没有跌破都给出。双底上下颠倒，height 总是正数。
    """
    if kind not in ("top", "bottom"):
        raise ValueError('kind 只能是 "top" 或 "bottom"')
    sign = 1 if kind == "top" else -1
    c = close.to_numpy(float)
    pos = {t: i for i, t in enumerate(close.index)}
    rows = []
    for run in _runs(swings, [sign, -sign, sign]):
        first, middle, second = sign * run["price"].to_numpy()
        t = [pos[x] for x in run["time"]]
        height = max(first, second) - middle
        if height <= 0 or abs(first - second) > tol * height:
            continue
        seen = pos[run["confirmed_at"].iloc[2]]
        limit = t[2] + (wait if wait is not None else t[2] - t[0]) + 1
        j = _first_close_beyond(c, seen, limit, lambda _, m=sign * middle: m, sign)
        rows.append((*run["time"], run["confirmed_at"].iloc[2], sign * first, sign * second, sign * middle,
                     height, close.index[j] if j is not None else pd.NaT, sign * (middle - height)))
    return pd.DataFrame(rows, columns=["first", "middle", "second", "confirmed_at", "first_price", "second_price",
                                       "neckline", "height", "broken_at", "target"])


def converging(close: pd.Series, swings: pd.DataFrame, flat: float = 0.2, wait: int | None = None) -> pd.DataFrame:
    """用最近两个摆动高点连上轨、两个摆动低点连下轨，按两条线的方向给形态命名。

    四个相邻的摆动点（两高两低，高低交替）决定两条线。设第一个点的位置两线之间的宽度为 W，
    四个点从头到尾的根数为 T，每条线在 T 根里的变化 ÷ W 叫这条线的「斜度」，绝对值不超过 flat 算水平。
    上轨水平、下轨向上：上升三角形；上轨向下、下轨水平：下降三角形；上轨向下、下轨向上：对称三角形
    两条线都向上且下轨更陡（在收窄）：上升楔形；都向下且上轨更陡：下降楔形
    两条线都水平：矩形；上轨向上、下轨向下：扩散；其余同方向而不收窄的：通道
    confirmed_at：第四个摆动点被确认的时刻。
    broken_at / direction：从 confirmed_at 起，wait 根以内（默认 T），第一次收盘价在上轨上方（1）或下轨下方（-1）。
    """
    c = close.to_numpy(float)
    pos = {t: i for i, t in enumerate(close.index)}
    rows = []
    ordered = swings.sort_values("time").reset_index(drop=True)
    for i in range(len(ordered) - 3):
        run = ordered.iloc[i:i + 4]
        kinds = run["kind"].to_numpy()
        if not all(kinds[1:] == -kinds[:-1]):
            continue
        t = np.array([pos[x] for x in run["time"]])
        price = run["price"].to_numpy(float)
        highs, lows = np.flatnonzero(kinds == 1), np.flatnonzero(kinds == -1)
        slope_up = (price[highs[1]] - price[highs[0]]) / (t[highs[1]] - t[highs[0]])
        slope_down = (price[lows[1]] - price[lows[0]]) / (t[lows[1]] - t[lows[0]])
        upper = lambda j, a=price[highs[0]], b=t[highs[0]], m=slope_up: a + m * (j - b)
        lower = lambda j, a=price[lows[0]], b=t[lows[0]], m=slope_down: a + m * (j - b)
        width, span = upper(t[0]) - lower(t[0]), t[3] - t[0]
        if width <= 0:
            continue
        du, dl = slope_up * span / width, slope_down * span / width
        up_flat, down_flat = abs(du) <= flat, abs(dl) <= flat
        if up_flat and down_flat:
            name = "矩形"
        elif up_flat and dl > 0:
            name = "上升三角形"
        elif down_flat and du < 0:
            name = "下降三角形"
        elif du < 0 < dl:
            name = "对称三角形"
        elif du > 0 and dl > du:
            name = "上升楔形"
        elif dl < 0 and du < dl:
            name = "下降楔形"
        elif du > 0 > dl:
            name = "扩散"
        else:
            name = "通道"
        seen = pos[run["confirmed_at"].iloc[3]]
        stop = t[3] + (wait if wait is not None else span) + 1
        j, direction = None, 0
        for k in range(seen, min(stop, len(c))):
            if c[k] > upper(k) or c[k] < lower(k):
                j, direction = k, 1 if c[k] > upper(k) else -1
                break
        rows.append((run["time"].iloc[0], run["time"].iloc[3], run["confirmed_at"].iloc[3], name, du, dl,
                     upper(seen), lower(seen), close.index[j] if j is not None else pd.NaT, direction))
    return pd.DataFrame(rows, columns=["start", "end", "confirmed_at", "name", "upper_slope", "lower_slope",
                                       "upper", "lower", "broken_at", "direction"])
```

### 读一遍代码

**`_runs`** 把摆动点按时间排好，找出种类依次符合要求的相邻几个点（头肩顶是 1, -1, 1, -1, 1）。所有形态都从这里开始。

**头肩底用一个 sign 统一处理**：`sign * run["price"]` 把头肩底的价格上下翻转，于是「头比肩高」「跌破颈线」这些条件只写一遍。返回时再乘回 sign，价格还是原始价格。

**`line` 这个 lambda 用了默认参数**（`a=neck_1, b=t[1], m=slope`），把当前这一组的数字「冻结」进去。不这样写的话，循环里的 lambda 会在调用时才去读变量，读到的是最后一组的值，这是 Python 闭包的经典陷阱。

**`_first_close_beyond`** 从 confirmed_at 那一根开始找，不是从右肩开始。右肩到确认之间的 K 线，在当时还不知道右肩存在，不能算作「跌破」。

### 测试

```python
# ---------------------------------------------------------------------------
# 图表形态（第 17 篇）
# ---------------------------------------------------------------------------

def toy_path(points, n):
    """按 (根号, 价格) 的折点线性插值出 n 根收盘价。"""
    values = np.interp(np.arange(n), [p[0] for p in points], [p[1] for p in points])
    return pd.Series(values, index=pd.date_range("2024-01-01", periods=n, freq="D"))


def manual_swings(close, rows):
    """rows 是 (根号, 种类) 的列表，价格取收盘价，确认时刻放在下一根。"""
    return pd.DataFrame([(close.index[k], close.iloc[k], kind, close.index[k + 1]) for k, kind in rows],
                        columns=["time", "price", "kind", "confirmed_at"])


def test_head_and_shoulders_by_hand():
    close = toy_path([(0, 100), (10, 110), (16, 102), (28, 120), (36, 104), (44, 112), (60, 96)], 61)
    found = Pt.head_and_shoulders(close, X.zigzag(close, 0.05))
    assert len(found) == 1
    row = found.iloc[0]
    # 颈线过 (16, 102) 和 (36, 104)，每根抬高 0.1；头在第 28 根，颈线 103.2，高度 120 - 103.2 = 16.8
    # 右肩 112 在第 44 根，价格每根跌 1，第 50 根跌到 106，跌够 5%，右肩被确认；那时颈线 105.4，还没跌破
    # 第 51 根收盘 105 低于颈线 105.5：跌破；目标 105.5 - 16.8 = 88.7
    assert row["head"] == close.index[28] and row["confirmed_at"] == close.index[50]
    assert row["neckline"] == pytest.approx(105.4) and row["height"] == pytest.approx(16.8)
    assert row["broken_at"] == close.index[51] and row["target"] == pytest.approx(88.7)


def test_head_and_shoulders_rules_and_bottom_mirror():
    close = toy_path([(0, 100), (10, 110), (16, 102), (28, 120), (36, 104), (44, 119), (60, 96)], 61)
    swings = X.zigzag(close, 0.05)
    assert Pt.head_and_shoulders(close, swings).empty                         # 两肩差 9，超过高度 16.8 的 30%
    assert len(Pt.head_and_shoulders(close, swings, shoulder_tol=0.6)) == 1
    top_close = toy_path([(0, 100), (10, 110), (16, 102), (28, 120), (36, 104), (44, 112), (60, 96)], 61)
    top_swings = X.zigzag(top_close, 0.05)
    flipped = 300 - top_close                                                  # 上下颠倒：头肩顶变成头肩底
    flipped_swings = top_swings.assign(price=300 - top_swings["price"], kind=-top_swings["kind"])
    top, bottom = Pt.head_and_shoulders(top_close, top_swings), Pt.head_and_shoulders(flipped, flipped_swings, "bottom")
    assert list(bottom["head"]) == list(top["head"]) and list(bottom["broken_at"]) == list(top["broken_at"])
    assert bottom["height"].iloc[0] == pytest.approx(top["height"].iloc[0])
    assert bottom["target"].iloc[0] == pytest.approx(300 - top["target"].iloc[0])


def test_double_tops_by_hand():
    close = toy_path([(0, 100), (10, 120), (20, 108), (30, 119), (45, 100)], 46)
    found = Pt.double_tops(close, X.zigzag(close, 0.05))
    assert len(found) == 1
    row = found.iloc[0]
    # 两个顶 120 和 119，中间低点 108：高度 12，两顶差 1 ≤ 1.2；第二个顶之后每根跌 19/15
    # 第 35 根跌到 112.67（跌够 5%）确认；第 39 根收盘 107.6 跌破 108；目标 108 - 12 = 96
    assert row["confirmed_at"] == close.index[35] and row["broken_at"] == close.index[39]
    assert row["neckline"] == 108 and row["height"] == 12 and row["target"] == 96
    assert Pt.double_tops(close, X.zigzag(close, 0.05), tol=0.05).empty      # 两顶差 1 > 12 × 5%


@pytest.mark.parametrize("highs,lows,name", [
    ((110, 108), (100, 102), "对称三角形"), ((110, 110), (100, 104), "上升三角形"), ((110, 106), (100, 100), "下降三角形"),
    ((110, 112), (100, 106), "上升楔形"), ((110, 104), (100, 98), "下降楔形"), ((110, 110), (100, 100), "矩形"),
    ((110, 114), (100, 96), "扩散"), ((110, 114), (100, 104), "通道")])
def test_converging_names_by_hand(highs, lows, name):
    close = pd.Series(105.0, index=pd.date_range("2024-01-01", periods=41, freq="D"))
    for k, price in zip([0, 20, 10, 30], [*highs, *lows]):
        close.iloc[k] = price
    swings = manual_swings(close, [(0, 1), (10, -1), (20, 1), (30, -1)])
    assert Pt.converging(close, swings)["name"].tolist() == [name]


def test_converging_breakout_by_hand():
    close = pd.Series(104.5, index=pd.date_range("2024-01-01", periods=61, freq="D"))
    for k, price in [(0, 110), (10, 100), (20, 108), (30, 102)]:
        close.iloc[k] = price
    close.iloc[36] = 120                                                      # 上轨在第 36 根是 106.4，收盘 120 升破
    found = Pt.converging(close, manual_swings(close, [(0, 1), (10, -1), (20, 1), (30, -1)]))
    assert found["name"].iloc[0] == "对称三角形"
    assert found["broken_at"].iloc[0] == close.index[36] and found["direction"].iloc[0] == 1


def test_chart_patterns_never_use_the_future():
    rng = np.random.default_rng(170)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 1500))),
                      index=pd.date_range("2020-01-01", periods=1500, freq="D"))
    full_swings = X.zigzag(close, 0.03)
    for func, kinds in [(Pt.head_and_shoulders, ["top", "bottom"]), (Pt.double_tops, ["top", "bottom"])]:
        for kind in kinds:
            full = func(close, full_swings, kind)
            assert len(full) > 3
            for k in [600, 1100]:
                cut = close.iloc[:k]
                part = func(cut, X.zigzag(cut, 0.03), kind)
                expected = full[full["confirmed_at"] <= cut.index[-1]].reset_index(drop=True)
                expected["broken_at"] = expected["broken_at"].where(expected["broken_at"] <= cut.index[-1])
                shape = [col for col in part.columns if col not in ("broken_at", "neckline_at_break", "target")]
                pd.testing.assert_frame_equal(part[shape], expected[shape])
                assert part["broken_at"].equals(expected["broken_at"])
```

- `test_head_and_shoulders_by_hand`：第三节的玩具例子，颈线、高度、确认时刻、跌破时刻、目标逐个核对。
- `test_head_and_shoulders_rules_and_bottom_mirror`：两肩差太多时不成立、放宽参数后成立；把价格上下翻转，头肩顶变成头肩底，时刻完全相同。
- `test_double_tops_by_hand`：双顶的手算，以及把高度差上限收紧到 5% 后不成立。
- `test_converging_names_by_hand`：8 组手工摆放的四个点，分别得到 8 个名字。
- `test_converging_breakout_by_hand`：对称三角形之后一根收盘越过上轨，记录为向上突破。
- `test_chart_patterns_never_use_the_future`：随机价格截断两次，截断后找到的形态必须和全部数据里「当时已经确认」的那些完全一样；跌破时刻如果在截断之后，截断版本里必须是 NaT。

```bash
pytest -q
```

```text
........................................................................ [ 94%]
........                                                                 [100%]
152 passed in 0.56s
```

没装 TA-Lib 时，结果是 120 passed、32 skipped。

---

## 十一、常见误用

**1. 在图上找到一个形态，就当作客观事实。**
决策点的头肩顶只在 ZigZag 5% 下存在，3% 和 8% 都找不到它。「有一个头肩顶」永远是「在某组参数下有」。

**2. 统计之后再调参数。**
两肩高度差的上限从 10% 放宽到 100%，双顶从 15 个变成 171 个。在结果里挑参数，就是在挑结果。

**3. 只统计「成立」的形态，再用这个胜率指导形态成立之前的决定。**
BTC 4 小时线双顶，同一笔交易，全部候选 38.8%，只算后来跌破的 87.1%。

**4. 忘了右肩要被确认。**
按摆动点所在的那一根算，右肩就是那一段的最高点，在最高点做空当然好看。实际上右肩要等价格跌够一个阈值才存在，那时离颈线往往已经很近。

**5. 只和「随便哪一天」比，不和「普通的跌破前低」比。**
双顶的颈线就是最近的低点。要知道「双顶」这个形状有没有用，对照必须是同样的跌破、同样的止损目标距离。

**6. 把识别规则的几何当成市场规律。**
上升楔形多数向下突破，打乱顺序的随机价格也是这样。

**7. 看到一个显著结果就停下来。**
BTC 1 小时线头肩顶的优势，2022 年之后就消失了。任何发现都要按时间切开看。

---

## 十二、这一篇能回答什么，不能回答什么

| 这一篇**能**帮你回答 | 这一篇**不能**回答 |
|---|---|
| 怎么把头肩形、双顶、三角形写成可以运行的规则 | 哪组参数「正确」 |
| 换参数、换阈值，识别结果会变多少 | 你肉眼认出的形态和算法认出的是不是同一批 |
| 「只统计成立的」让胜率虚高多少 | 更复杂的形态（杯柄、V 形反转、三重顶）的表现 |
| 按教科书的止损和目标交易，和普通跌破比，在这五组数据上有没有优势 | 加上成本之后还剩多少（第 28 篇） |
| 三角形、楔形的突破方向，有多少来自识别规则本身 | 其他画线方法（每条线碰三次、用最高最低价）的结论（练习 4） |

---

## 十三、小结

1. **图表形态是摆动点连成的图案。** 头肩形五个点，双顶三个点，三角形、楔形、通道四个点。每个形态都能写成几条带数字的规则。

2. **形态是参数的产物。** ZigZag 阈值从 3% 到 15%，BTC 日线的头肩顶从 21 个变成 2 个；决策点的头肩顶只在 5% 下存在；两肩高度差的上限放宽，双顶从 15 个变成 171 个。

3. **右肩要被确认才存在。** 阈值越大，确认越晚，确认时价格离颈线越近。

4. **「突破颈线才算成立」会让统计虚高。** 同一笔在右肩确认时入场的交易，只统计后来跌破的，胜率从 38.8% 变成 87.1%（BTC 4 小时线双顶）。用事后才知道的条件分组，是这门课第三次遇到这种错误。

5. **等跌破再进场是正当的做法**，但要和盈亏平衡胜率、和「普通的跌破前低」比。五组数据里，只有 BTC 1 小时线的头肩顶和双顶显著好于普通跌破，而且优势集中在 2022 年以前，最近几年消失了。

6. **三角形和楔形的突破方向，是识别规则的几何。** 上升楔形 77% 到 83% 向下突破，打乱顺序的随机价格也有 72% 到 79%。上升三角形在我们的画法下多数向下突破，和教科书相反。

7. **突破之后，形态的名字没有带来可测量的信息**：BTC 4 小时线和 1 小时线上，40 次检验里显著的 5 次都在美股日线的小样本上。

8. **决策点那次头肩顶，第二天就「成立」了，11 天后创出历史新高，7 周后才到达量度目标。** 按教科书止损的人，早在中间那次新高就出局了。

最后回到星空。星座很有用：它帮你记住星星的位置，给夜空起名字，跟别人讨论「猎户座腰带左边那颗」。图表形态也一样，它是描述价格结构的一套好用的词汇（第 8、9 篇的摆动点和关键位置，换了一种说法）。但星座不会告诉你明天的天气，而且它的形状，一半来自星星，一半来自画线的人。

下一篇是第 18 篇：**道氏理论与斐波那契**。价格从高点回撤到 61.8%，停住了。斐波那契比例真的特别吗？和回撤到随机比例比呢？

---

## 练习

**练习 1（手算）**
一组摆动点：高 80（第 0 根）、低 70（第 6 根）、高 90（第 14 根）、低 72（第 22 根）、高 81（第 30 根）。

- (a) 颈线的斜率、头所在位置的颈线值、高度各是多少？
- (b) 按默认参数，它是头肩顶吗？逐条检查四个条件。
- (c) 第 36 根收盘 73.5，那时的颈线是多少？跌破了吗？如果跌破，量度目标是多少？

**练习 2（编程）**
给 `talab.patterns` 加一个 `triple_tops`（三重顶）：五个摆动点，三个高点两两之差都不超过高度的 10%，颈线是两个低点中较低的那个。

- (a) 写出函数和一个手算测试。
- (b) 它和 `head_and_shoulders` 有没有重叠？什么情况下一组五个点会同时满足两者？

**练习 3（数据）**
第八节的对照是「普通的跌破前低」。

- (a) 把对照换成「随便哪一根 K 线，用同样的止损和目标距离」，结论变不变？
- (b) 把 BTC 1 小时线的样本按年份拆开，逐年算头肩顶的胜率和盈亏平衡胜率。优势是哪一年消失的？
- (c) 用第 12 篇的做法，给每笔交易扣掉 0.1% 的往返成本（手续费加滑点），平均盈亏还剩多少 R？

**练习 4（数据）**
第九节的画线只用两高两低。

- (a) 改成「每条线至少碰三次」：连续六个摆动点，三个高点大致在一条直线上（中间那个点离直线不超过 W 的 10%），低点同理。重做向上突破比例的表。
- (b) 打乱顺序后的比例还一样吗？
- (c) 如果用最高价、最低价画线（而不是收盘价的 ZigZag），结论会变吗？

**练习 5（思考）**
第七节说「只算后来突破的」用到了未来信息。

- (a) 如果你只在跌破之后才做决定，这个未来信息还是问题吗？
- (b) 某本书写道：「头肩顶跌破颈线后，78% 到达量度目标。」要用这个数字，你需要先确认书里的统计有哪三件事和你的做法一致？

---

## 小检查答案

**小检查 1**

(a) 颈线从 44 到 46，20 根抬高 2，每根 0.1。头在颈线点 1 之后 8 根，那里的颈线是 44 + 0.8 = 44.8，**高度** = 58 - 44.8 = **13.2**。两肩高度差的上限是 13.2 × 30% = **3.96**，实际差 |50 - 51| = 1，满足；两个颈线点差 2，不超过 6.6，满足。时间比例题目没给全，只要在 1/3 到 3 之间就**成立**。

(b) 46.5 - 13.2 = **33.3**。

(c) ZigZag 要等价格从右肩反向走够一个阈值，右肩才被确认。阈值越大，这段反向走得越多，价格就越接近（甚至越过）颈线。极端情况下，阈值大于右肩到颈线的距离，**右肩被确认的那一刻价格已经跌破颈线**，形态「出现」和「成立」发生在同一根。

**小检查 2**

(a) 止损距离 6，目标距离 12，盈亏平衡胜率 = 6 ÷ (6 + 12) = **33.3%**。胜率 40% 时，平均盈亏 = 40% × 2R - 60% × 1R = **+0.2R**。

(b) 第七节两列用的是**同一个入场时刻**（右肩确认时），只是统计范围不同。「只算后来突破的」在入场那一刻不可能知道，所以它的高胜率拿不到。要评价「等突破」，必须像第八节那样**在突破那一刻入场**，那时止损和目标的距离都变了（入场价更低，离止损更远），胜率要和新的盈亏平衡胜率比。第八节的结果是：大多数情况下，突破后入场并没有显著好于普通跌破。

(c) 可能的原因：市场参与者变了（2022 年之后机构、做市商、ETF 占比变化），波动率结构变了（第 15 篇），或者早年的优势本来就是运气。还需要的证据：**逐年的结果是否稳定**（练习 3 (b)）、**扣掉成本之后还剩多少**（练习 3 (c)）、**换一组没看过的参数和数据还在不在**（第 30 篇的样本外检验）。一组 20 次检验里挑出的 2 次显著，而且只在前半段有效，更可能是噪声或者已经过时的规律。
