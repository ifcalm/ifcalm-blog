---
title: "第 13 篇：MACD"
date: 2026-09-16
weight: 13
tags: ["交易技术分析"]
draft: false
summary: "2025 年 8 月 13 日，BTC 收盘创出 123,306 的新高，MACD 柱的峰值却只有 7 月那一段的一半不到。所有人都在说「顶背离」。这一篇讲清楚 MACD 在算什么：两条 EMA 之差为什么是一个带通滤波器，它对多长周期的波动最敏感（公式和实测正弦波对照）；快线、慢线、柱状图、交叉和零轴在三个标的上的表现；和 TA-Lib 对账时快 EMA 从哪一根开始算这个容易踩的坑。然后把「背离」写成不看未来的算法，在 BTC 日线、4 小时线、1 小时线和 SPY、AAPL 上统计：同样是价格创新高，有背离和没有背离，之后的走势到底有没有不同；以及为什么在图上事后画出来的背离，看起来个个都准。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **本篇位置** | 第三部分「技术指标」的第二篇。MACD 由第 12 篇的 EMA 组合而成，背离要用到第 8 篇的摆动点和第 11 篇的「先碰到哪条线」 |
| **用到的数据** | BTCUSDT 现货日线，以及用 1 分钟线合成的 4 小时线和 1 小时线（2017-08 至 2026-08）；SPY、AAPL 日线（2016-09 至 2026-09） |
| **动手** | `talab.indicators` 第三部分：MACD（和 TA-Lib 一致）、EMA 的频率响应、背离检测，附 10 个测试 |
| **读完你能** | 手算 MACD，说清楚它对哪种周期的波动最敏感；把「顶背离」「底背离」写成一个不偷看未来的算法；知道背离在数据上增加了多少信息 |

---

## 一、先做一个决定

现在是 **2025 年 8 月 13 日 UTC 收盘**。

BTC 今天收在 **123,306.43**，是历史最高收盘价。7 月 22 日那个高点是 119,954.42，今天比它高 2.79%。

可是下方的 MACD 柱，这一段最高只到 **525.5**；7 月那一段的最高是 **1,176.1**。MACD 线也一样：7 月 17 日最高 3,446.6，这一段只到 1,337.4。

![BTCUSDT 日线和 MACD，2025-06 至 2025-08-13](/images/trade-analysis/13/decision.png)

```text
                               high     close    macd  signal   hist
time                                                                
2025-08-08 00:00:00+00:00  117630.0  116674.7   334.0   652.4 -318.4
2025-08-09 00:00:00+00:00  117944.0  116462.2   353.5   592.6 -239.1
2025-08-10 00:00:00+00:00  119311.1  119294.0   590.6   592.2   -1.6
2025-08-11 00:00:00+00:00  122335.2  118686.0   721.1   618.0  103.1
2025-08-12 00:00:00+00:00  120324.4  120134.1   930.7   680.5  250.2
2025-08-13 00:00:00+00:00  123667.8  123306.4  1337.4   811.9  525.5
此前最高收盘：120,134.08（2025-08-12）
6 月 22 日低点之后到 7 月 22 日高点：柱最高 1,176.1（2025-07-14），MACD 线最高 3,446.6（2025-07-17）
8 月 2 日低点之后到 8 月 13 日：柱最高 525.5（2025-08-13），MACD 线最高 1,337.4（2025-08-13）
7 月 22 日收盘 119,954.42，8 月 13 日收盘 123,306.43，高出 2.79%
```

价格创了新高，动能没有跟上。群里、推特上，所有人都在说同一个词：**顶背离**。

你会怎么做？

- A. **卖出或做空**：顶背离，上涨没有力量了
- B. **继续持有**：价格创新高就是强，背离只是指标的滞后
- C. **等确认**：等价格真的掉头、高点被确认之后再说

**先写下你的选择。** 第六节揭晓之后的走势，第八节看背离在全部历史上的表现。

---

## 二、骑车爬一段起伏的山路

### 打个比方

想象你骑自行车，走一段有很多起伏的山路，车上有一个码表。

- **价格是你所在的海拔。** 创新高，就是爬到了比之前所有山头都高的地方。
- **MACD 线像码表上的爬升速度**：你最近一段时间往上爬得有多快。它不是瞬时速度，是平滑过的，路面上的小颠簸不会让它乱跳。
- **柱状图像速度的变化**：还在加速，还是已经在减速。
- **背离**就是：你爬上了第二个山头，它比第一个山头还高，可你爬这个山头时的速度，比爬第一个山头时慢。

骑过车的人都知道，爬坡变慢的原因有很多：可能是累了，快要骑不动了；可能只是这一段坡比较缓；也可能是你在为下一个陡坡省力气。**速度变慢，不等于接下来一定下坡。**

还有一件事：**事后看骑行记录的回放**，你会发现每一个山顶之前速度都变慢了。这是废话，不减速怎么会到顶？可在骑的时候，每一次减速都可能是山顶，也可能不是。第八节会用数据说明这件事。

---

## 三、MACD 是怎么算的

### 定义

MACD 是 Gerald Appel 在 20 世纪 70 年代末提出的，全称是「移动平均线的收敛和发散」（Moving Average Convergence Divergence）。柱状图是 Thomas Aspray 在 1986 年前后加上的。

> MACD 线 = 12 日 EMA - 26 日 EMA
>
> 信号线 = MACD 线的 9 日 EMA
>
> 柱 = MACD 线 - 信号线

三个参数 12、26、9 是默认值，写作 MACD(12, 26, 9)。它们的单位都和价格相同：BTC 的 MACD 是几百几千美元，SPY 的是几块钱，不同标的、同一个标的价格差很多的两个年份之间，数值不能直接比较。

### 手算一遍

用很小的参数 MACD(2, 4, 2) 算 7 个价格：

```python
x = pd.Series([1.0, 2, 4, 8, 6, 5, 7])
small = I.macd(x, fast=2, slow=4, signal=2)
small.insert(0, "价格", x)
small.insert(1, "快 EMA2", I.ema(x.where(np.arange(len(x)) >= 2), 2))
small.insert(2, "慢 EMA4", I.ema(x, 4))
print(small.round(4).to_string())
```

```text
    价格  快 EMA2  慢 EMA4    macd  signal    hist
0  1.0     NaN     NaN     NaN     NaN     NaN
1  2.0     NaN     NaN     NaN     NaN     NaN
2  4.0     NaN     NaN     NaN     NaN     NaN
3  8.0  6.0000   3.750     NaN     NaN     NaN
4  6.0  6.0000   4.650  1.3500  1.8000 -0.4500
5  5.0  5.3333   4.790  0.5433  0.9622 -0.4189
6  7.0  6.4444   5.674  0.7704  0.8344 -0.0639
```

逐步验算：

- **慢 EMA4**（α = 2 ÷ 5 = 0.4）：第一个值在第 3 根，(1 + 2 + 4 + 8) ÷ 4 = 3.75；第 4 根 3.75 + 0.4 × (6 - 3.75) = 4.65。
- **快 EMA2**（α = 2 ÷ 3）：注意它**不是从第 1 根开始算**，而是和慢 EMA 同一根出现，用第 2、3 根的平均 (4 + 8) ÷ 2 = 6 作为初始值（下一小节解释为什么）。第 4 根 6 + ⅔ × (6 - 6) = 6。
- **MACD 线**：第 3 根 6 - 3.75 = 2.25，第 4 根 6 - 4.65 = 1.35。
- **信号线**（α = 2 ÷ 3）：第一个值在第 4 根，(2.25 + 1.35) ÷ 2 = 1.8。
- **柱**：第 4 根 1.35 - 1.8 = **-0.45**。

表里第 3 根的 MACD 线是 NaN，虽然它算得出来（2.25）：**三列要等信号线也有值了，才一起出现**。

### 快 EMA 从哪一根开始

这是和 TA-Lib 对账时最容易踩的坑。

把 MACD 写成 `ema(close, 12) - ema(close, 26)`，看起来天经地义：快 EMA 从第 12 根开始，慢 EMA 从第 26 根开始。但 **TA-Lib 的 MACD 让快 EMA 也从第 26 根开始**，初始值是第 15 到第 26 根的平均。这样两条 EMA 从同一根起步，都「热身」了同样的时间。另外，TA-Lib 让三列输出都从第 34 根（26 + 9 - 1）开始。

两种写法在开头差多少：

```python
naive = I.ema(c, 12) - I.ema(c, 26)
difference = (naive - m["macd"]).abs()
first = m["macd"].first_valid_index()
print(f"第一个 MACD 值（{first.date()}）：TA-Lib 写法 {m['macd'][first]:.4f}，两条 EMA 各自开始 {naive[first]:.4f}")
for k in [60, 100, 200]:
    print(f"第 {k} 根：相差 {difference.iloc[k - 1]:.6f}")
```

```text
第一个 MACD 值（2017-09-19）：TA-Lib 写法 -117.3981，两条 EMA 各自开始 -140.5447
第 60 根：相差 0.300726
第 100 根：相差 0.000377
第 200 根：相差 0.000000
```

BTC 第一个 MACD 值，两种写法差了 23 美元，到第 100 根还差 0.0004，到第 200 根才完全一致。`talab.indicators.macd` 采用 TA-Lib 的写法，第九节的测试会和 TA-Lib 逐个数字对账。

### 直线上的 MACD

价格每根涨 1 的直线上，第 12 篇算过：12 日 EMA 落后 5.5 根，26 日 EMA 落后 12.5 根。两者相差 7 根，所以：

> MACD 线 = 7 × 每根的涨幅
>
> 柱 = 0（MACD 线是常数，信号线等于它）

```python
ramp = pd.Series(np.arange(200, dtype=float))
r = I.macd(ramp)
print(f"MACD 线 最小 {r['macd'].min():.6f} 最大 {r['macd'].max():.6f}；柱 最小 {r['hist'].min():.2e} 最大 {r['hist'].max():.2e}")
```

```text
MACD 线 最小 7.000000 最大 7.000000；柱 最小 0.00e+00 最大 0.00e+00
```

这说明了 MACD 线的本质：**它近似于价格的平滑斜率**，乘以一个固定的倍数 7。价格匀速上涨时，MACD 线是一个正的常数；上涨越快，MACD 线越高。柱衡量的是这个斜率在变大还是变小。回到山路上：MACD 线是爬升速度，柱是在加速还是减速。

### ✋ 小检查 1

(a) 价格每天稳定上涨 3 美元，已经持续了几个月。MACD(12, 26, 9) 的 MACD 线和柱大约是多少？

(b) 换成 MACD(5, 20, 9)，同样每天涨 3 美元，MACD 线是多少？

(c) 价格几个月一直是 100 不动，MACD 线是多少？

答案在文末。

---

## 四、两条 EMA 之差，本质是带通滤波器

### 低通和带通

把价格想象成很多不同周期的波动叠加起来：几天一个来回的小波动、几个月一个来回的中等波动、几年一个来回的大周期。

- **EMA 是低通滤波器**：周期很长的慢变化几乎原样通过，周期很短的快速波动被压扁。
- **两个低通之差是带通滤波器**：12 日 EMA 和 26 日 EMA 对很慢的变化反应差不多，相减之后抵消；对很快的波动都压扁了，相减之后也很小。**只有中间某一段周期的波动，两条 EMA 反应得不一样，差值最大。**

### 算出来

第 12 篇说过 EMA 是递推公式。对一个周期为 T 根 K 线的正弦波，n 日 EMA 的输出也是同一个周期的正弦波，只是振幅和相位变了。放大倍数可以直接算出来：

> α = 2 ÷ (n + 1)，ω = 2π ÷ T
>
> EMA 的响应 = α ÷ (1 - (1 - α) × e^(-iω))，取绝对值就是放大倍数
>
> MACD 线的响应 = EMA12 的响应 - EMA26 的响应
>
> 柱的响应 = MACD 线的响应 × (1 - EMA9 的响应)

`talab.indicators.ema_response` 就是这个公式。用正弦波实测一遍：造一段周期为 T 的正弦波价格，算出 MACD，再用最小二乘拟合出输出的振幅。

```python
def amplitude(y, period):
    """用最小二乘拟合正弦波的振幅（整数个周期）。"""
    tt = np.arange(len(y))
    y = np.asarray(y, dtype=float) - np.mean(y)
    return np.hypot(2 * np.mean(y * np.sin(2 * np.pi * tt / period)), 2 * np.mean(y * np.cos(2 * np.pi * tt / period)))


rows = []
for period in [5, 10, 20, 40, 60, 100, 200, 500]:
    n = 6000 if period != 500 else 10000
    wave = pd.Series(100 + np.sin(2 * np.pi * np.arange(n) / period))
    mm = I.macd(wave)
    keep = slice(n - period * (n // period // 2), n)                  # 后一半、整数个周期
    line_gain = abs(I.ema_response(12, period) - I.ema_response(26, period))
    hist_gain = abs((I.ema_response(12, period) - I.ema_response(26, period)) * (1 - I.ema_response(9, period)))
    rows.append({"周期（根）": period, "MACD 线 公式": line_gain, "MACD 线 实测": amplitude(mm["macd"].iloc[keep], period),
                 "柱 公式": hist_gain, "柱 实测": amplitude(mm["hist"].iloc[keep], period)})
print(pd.DataFrame(rows).round(4).to_string(index=False))
fine = np.arange(2, 3000, 0.1)
for name, gain in [("MACD 线", abs(I.ema_response(12, fine) - I.ema_response(26, fine))),
                   ("柱", abs((I.ema_response(12, fine) - I.ema_response(26, fine)) * (1 - I.ema_response(9, fine))))]:
    band = fine[gain >= gain.max() / np.sqrt(2)]
    print(f"{name}：放大倍数最大 {gain.max():.3f}，在周期 {fine[gain.argmax()]:.0f} 根；"
          f"放大倍数不低于最大值的 1/√2（功率减半）的周期 {band.min():.0f} ~ {band.max():.0f} 根")
```

```text
 周期（根）  MACD 线 公式  MACD 线 实测   柱 公式   柱 实测
     5     0.0757     0.0757 0.0665 0.0665
    10     0.1397     0.1397 0.1175 0.1175
    20     0.2467     0.2467 0.1795 0.1795
    40     0.3528     0.3528 0.1813 0.1813
    60     0.3680     0.3680 0.1395 0.1395
   100     0.3189     0.3189 0.0772 0.0772
   200     0.2001     0.2001 0.0249 0.0249
   500     0.0866     0.0866 0.0043 0.0043
MACD 线：放大倍数最大 0.369，在周期 55 根；放大倍数不低于最大值的 1/√2（功率减半）的周期 22 ~ 141 根
柱：放大倍数最大 0.193，在周期 29 根；放大倍数不低于最大值的 1/√2（功率减半）的周期 12 ~ 61 根
```

![MACD 对不同周期波动的放大倍数](/images/trade-analysis/13/gain.png)

公式和实测到小数点后 4 位完全一致。读这张图：

- **MACD 线对大约 55 根 K 线一个来回的波动最敏感**，放大倍数 0.369；功率减半的范围是 22 到 141 根。日线上，就是一个月到半年一个来回的波动。
- **柱对大约 29 根一个来回的波动最敏感**，范围 12 到 61 根。信号线又减掉了一部分慢变化，柱比 MACD 线更「快」。
- **周期 5 根的波动**，MACD 线只剩 7.6%：几天的噪声基本被过滤掉。
- **周期 500 根的慢波动**，MACD 线只剩 8.7%，柱只剩 0.4%。一轮几年的牛熊周期，在 MACD 线上几乎看不出来。

所以当你说「MACD 柱在变小」的时候，你实际在说的是：**一两个月尺度上的波动正在减弱。** 它对更长的趋势和更短的噪声都不敏感。

---

## 五、快线、慢线、柱状图、交叉和零轴

### 几种常见的用法

MACD 线常被叫作快线，信号线叫作慢线。

- **信号线交叉**：MACD 线上穿信号线（柱由负转正）看涨，下穿看跌。
- **零轴交叉**：MACD 线上穿 0，等于 12 日 EMA 上穿 26 日 EMA，就是一对很快的均线金叉。
- **柱的方向**：柱在 0 上方并且在变长，说明上涨在加速。

### 数据怎么说

```python
def backtest_next_open(df, signal):
    """收盘时算出 signal（1 持有、0 空仓），下一根开盘成交（第 12 篇）。"""
    held = signal.shift(1).fillna(0.0)
    before = held.shift(1).fillna(0.0)
    o, close, prev = df["open"], df["close"], df["close"].shift(1)
    r = np.select([(held == 1) & (before == 1), (held == 1) & (before == 0), (held == 0) & (before == 1)],
                  [close / prev - 1, close / o - 1, o / prev - 1], 0.0)
    return pd.Series(r, index=df.index).fillna(0.0)


def state_gap(log_returns, column, horizon):
    p = pd.Series(np.exp(np.cumsum(np.asarray(log_returns))))
    mm = I.macd(p)
    later = np.log(p.shift(-horizon) / p)
    return later[mm[column] > 0].mean() - later[mm[column] < 0].mean()


for name, df in markets.items():
    close = df["close"]
    mm = I.macd(close)
    years = mm["macd"].notna().sum() / periods_per_year[name]
    zero = pd.Series(0.0, index=close.index)
    print(f"{name}：信号线金叉每年 {I.cross_above(mm['macd'], mm['signal']).sum() / years:.1f} 次，"
          f"MACD 线上穿零轴每年 {I.cross_above(mm['macd'], zero).sum() / years:.1f} 次")
    log_returns = np.log(close).diff().dropna().reset_index(drop=True)
    for column, horizon, label in [("hist", 5, "柱在 0 上方减下方，之后 5 天"), ("macd", 20, "MACD 线在 0 上方减下方，之后 20 天")]:
        res = St.shuffle_test(log_returns, lambda v: state_gap(v, column, horizon), n=1000, seed=0)
        print(f"   {label}：{res['实际值']:+.2%}，打乱后 95% 范围 {res['打乱后 2.5% 分位']:+.2%} ~ "
              f"{res['打乱后 97.5% 分位']:+.2%}，打乱后不小于实际的比例 {res['比例']:.1%}")
    start = I.sma(close, 200).first_valid_index()                    # 和第 12 篇的主线策略 v0 同一个起点
    d = df.loc[start:]
    for label, signal in [("买入持有", None), ("主线 v0（SMA50 > SMA200）", (I.sma(close, 50) > I.sma(close, 200)).astype(float)),
                          ("MACD 线 > 0 就持有", (mm["macd"] > 0).astype(float)), ("柱 > 0 就持有", (mm["hist"] > 0).astype(float))]:
        rr = d["close"].pct_change().fillna(0.0) if signal is None else backtest_next_open(d, signal.loc[start:])
        equity = (1 + rr).cumprod()
        buys = "" if signal is None else f"，买入 {int((signal.loc[start:].shift(1).fillna(0).diff() == 1).sum())} 次"
        print(f"   {label}：年化 {equity.iloc[-1] ** (periods_per_year[name] / len(rr)) - 1:.1%}，"
              f"最大回撤 {(equity / equity.cummax() - 1).min():.1%}{buys}")
```

```text
SPY：信号线金叉每年 11.0 次，MACD 线上穿零轴每年 3.4 次
   柱在 0 上方减下方，之后 5 天：-0.01%，打乱后 95% 范围 -0.39% ~ +0.37%，打乱后不小于实际的比例 94.4%
   MACD 线在 0 上方减下方，之后 20 天：-1.00%，打乱后 95% 范围 -1.55% ~ +1.38%，打乱后不小于实际的比例 20.3%
   买入持有：年化 13.2%，最大回撤 -34.1%
   主线 v0（SMA50 > SMA200）：年化 8.5%，最大回撤 -34.1%，买入 5 次
   MACD 线 > 0 就持有：年化 8.3%，最大回撤 -15.7%，买入 32 次
   柱 > 0 就持有：年化 6.8%，最大回撤 -15.1%，买入 103 次
AAPL：信号线金叉每年 9.0 次，MACD 线上穿零轴每年 3.9 次
   柱在 0 上方减下方，之后 5 天：+0.37%，打乱后 95% 范围 -0.62% ~ +0.59%，打乱后不小于实际的比例 25.5%
   MACD 线在 0 上方减下方，之后 20 天：-0.58%，打乱后 95% 范围 -2.31% ~ +2.48%，打乱后不小于实际的比例 64.6%
   买入持有：年化 28.4%，最大回撤 -38.5%
   主线 v0（SMA50 > SMA200）：年化 15.5%，最大回撤 -45.9%，买入 6 次
   MACD 线 > 0 就持有：年化 15.1%，最大回撤 -32.7%，买入 37 次
   柱 > 0 就持有：年化 20.1%，最大回撤 -26.4%，买入 85 次
BTC：信号线金叉每年 13.2 次，MACD 线上穿零轴每年 5.6 次
   柱在 0 上方减下方，之后 5 天：+0.86%，打乱后 95% 范围 -1.02% ~ +1.08%，打乱后不小于实际的比例 12.2%
   MACD 线在 0 上方减下方，之后 20 天：+3.84%，打乱后 95% 范围 -3.91% ~ +3.87%，打乱后不小于实际的比例 5.5%
   买入持有：年化 25.3%，最大回撤 -76.6%
   主线 v0（SMA50 > SMA200）：年化 19.1%，最大回撤 -66.7%，买入 9 次
   MACD 线 > 0 就持有：年化 40.1%，最大回撤 -58.2%，买入 48 次
   柱 > 0 就持有：年化 31.1%，最大回撤 -50.4%，买入 113 次
```

**交叉很频繁。** 信号线金叉每年 9 到 13 次，零轴上穿每年 3 到 6 次。

**状态本身不能预测之后的收益。** 「柱在 0 上方」之后 5 天、「MACD 线在 0 上方」之后 20 天的收益，SPY 和 AAPL 上都在打乱的范围之内。BTC 的 MACD 线状态差距最大，+3.84%，打乱后不小于它的比例是 5.5%，接近但够不上显著。

**把状态当成持有规则回测**（和第 12 篇的主线策略 v0 一样：收盘出信号，下一根开盘成交，**不扣成本**）：

| | SPY 年化 | SPY 回撤 | AAPL 年化 | AAPL 回撤 | BTC 年化 | BTC 回撤 |
|---|---|---|---|---|---|---|
| 买入持有 | 13.2% | -34.1% | 28.4% | -38.5% | 25.3% | -76.6% |
| 主线 v0（SMA50 > SMA200） | 8.5% | -34.1% | 15.5% | -45.9% | 19.1% | -66.7% |
| MACD 线 > 0 就持有 | 8.3% | -15.7% | 15.1% | -32.7% | 40.1% | -58.2% |
| 柱 > 0 就持有 | 6.8% | -15.1% | 20.1% | -26.4% | 31.1% | -50.4% |

两个现象：

1. **MACD 规则的回撤比 v0 小得多。** 它反应快，下跌时出得早。代价是交易次数多了很多：柱 > 0 这条规则，SPY 上买入了 103 次，BTC 上 113 次。
2. **BTC 上「MACD 线 > 0 就持有」年化 40.1%，高于买入持有的 25.3%。** 这很诱人，但先别急：这是 2 条 MACD 规则 × 3 个标的、6 个结果里最好的一个；48 次买卖还没有扣手续费和滑点；9 年只是一段历史。第 12 篇的参数网格里，BTC 上也有好几组均线参数跑赢了买入持有。第 28 篇加成本、第 30 篇做样本外检验之后，才知道它是不是真的。

⚠️ 主线策略这一篇不改。它的下一次升级在第 15 篇。

---

## 六、揭晓

**8 月 13 日之后，BTC 先跌了一段，然后又创了新高，然后才真正崩下去。**

![揭晓：BTCUSDT 日线和 MACD，2025-06 至 2025-11](/images/trade-analysis/13/reveal.png)

```python
i = c.index.get_loc(t)
for n in [7, 14, 30, 60]:
    print(f"{n} 天后（{c.index[i + n].date()}）：{c.iloc[i + n] / c[t] - 1:+.2%}")
before_high = c.loc["2025-08-14":"2025-10-05"]
print(f"8 月 14 日到 10 月 5 日：最低收盘 {before_high.min():,.2f}（{before_high.idxmin().date()}）")
print(f"10 月 6 日收盘 {c['2025-10-06']:,.2f}，比 8 月 13 日 {c['2025-10-06'] / c[t] - 1:+.2%}")
later = c.loc["2025-08-14":"2025-10-31"]
print(f"之后到 10 月底：最低收盘 {later.min():,.2f}（{later.idxmin().date()}），最高收盘 {later.max():,.2f}（{later.idxmax().date()}）")
print(f"2025-10-06 之后到 2026-08-31 的最低收盘：{c.loc['2025-10-07':].min():,.2f}（{c.loc['2025-10-07':].idxmin().date()}）")
```

```text
7 天后（2025-08-20）：-7.33%
14 天后（2025-08-27）：-9.77%
30 天后（2025-09-12）：-5.90%
60 天后（2025-10-12）：-6.77%
8 月 14 日到 10 月 5 日：最低收盘 108,246.35（2025-08-31）
10 月 6 日收盘 124,658.54，比 8 月 13 日 +1.10%
之后到 10 月底：最低收盘 106,431.68（2025-10-17），最高收盘 124,658.54（2025-10-06）
2025-10-06 之后到 2026-08-31 的最低收盘：58,624.71（2026-06-30）
```

- **选 A（卖出或做空）的，头两周是对的**：7 天后 -7.33%，14 天后 -9.77%。到 10 月 5 日为止，最低收盘价是 8 月 31 日的 108,246.35。
- **可是 10 月 6 日，BTC 收在 124,658.54，又创了新高**，比 8 月 13 日还高 1.1%。如果你在 8 月 13 日做空并且一直拿着，到这天是亏的。
- **之后才是真正的大跌**：10 月 10 日起急跌，到 2026 年 6 月 30 日最低收盘 58,624.71。

选 B 持有的，经历了一次 12% 的回撤，又在 10 月看到了新高，再经历了一次腰斩。选 C 等确认的，第七节会告诉你「确认」发生在哪一天、那时价格在哪里。

所以这一次的顶背离，说对了一半：**它之后确实跌了，但不是顶。** 真正的顶在两个月之后，而且那一次（10 月 6 日相对 9 月 18 日）的背离算法并没有给出顶背离信号：那一段的柱比前一段更高。

---

## 七、背离：写成算法

### 「背离」这个词里藏着多少选择

「价格创新高，指标没有创新高」，听起来很清楚。可一旦要写成程序，至少要回答五个问题：

1. **「高点」是什么？** 用哪种摆动点算法、多大的阈值？（第 8 篇）
2. **「指标的高点」取在哪？** 就取价格高点那一根的指标值，还是这一段上涨里指标的最大值？柱的峰值常常比价格的高点早好几根。
3. **两个高点隔多远才算？** 隔两年的两个高点之间，还算背离吗？
4. **指标的值要不要在 0 上方？** 前一个高点时柱本来就是负的，谈不上「动能减弱」。
5. **什么时候才知道？** 第二个高点要被确认，才知道它是高点。

### `talab` 的定义

| 选择 | 这一篇的做法 |
|---|---|
| 摆动点 | ZigZag（收盘价）。BTC 日线 5%、4 小时线 2%、1 小时线 1%，SPY 1.5%，AAPL 2.5%，都是第 11 篇阈值的一半：背离看的是比趋势状态更小一级的起伏 |
| 指标 | MACD 柱 |
| 每个高点对应的指标值 | 从前一个摆动低点之后（不含）到这个高点（含）这一段里，柱的**最大值** |
| 顶背离 | 相邻两个摆动高点，后一个价格更高、柱的最大值更低，而且前一个的最大值大于 0 |
| 距离 | 两个高点相隔 5 到 60 根 K 线 |
| 知道的时刻 | **第二个高点被确认的那一根**（`confirmed_at`） |
| 底背离 | 以上全部反过来 |

`divergences` 返回每一对「价格创新高（新低）」的相邻摆动点，并标明是不是背离。**不是背离的那些也保留**，这是下一节做对照要用的：同样是价格创了新高，有背离和没有背离，之后有没有区别。

### 在决策点上

```python
swings = X.zigzag(c, 0.05)
found = I.divergences(swings, m["hist"], "bearish")
recent = found[found["second"] >= "2025-01-01"].copy()
print(recent.round({"first_value": 2, "second_value": 2}).to_string(index=False))
row = found[found["second"] == t].iloc[0]
print(f"8 月 13 日这个高点在 {row['confirmed_at'].date()} 被确认，那天收盘 {c[row['confirmed_at']]:,.2f}，"
      f"相比 8 月 13 日 {c[row['confirmed_at']] / c[t] - 1:+.2%}")
```

```text
                    first                    second  first_price  second_price  first_value  second_value              confirmed_at  divergence
2025-01-06 00:00:00+00:00 2025-01-21 00:00:00+00:00    102235.60     106143.82       425.53        974.89 2025-02-01 00:00:00+00:00       False
2025-03-24 00:00:00+00:00 2025-05-22 00:00:00+00:00     87498.16     111696.21       810.61       1374.70 2025-05-29 00:00:00+00:00       False
2025-06-10 00:00:00+00:00 2025-07-22 00:00:00+00:00    110274.39     119954.42        26.63       1176.09 2025-08-01 00:00:00+00:00       False
2025-07-22 00:00:00+00:00 2025-08-13 00:00:00+00:00    119954.42     123306.43      1176.09        525.47 2025-08-18 00:00:00+00:00        True
2025-09-18 00:00:00+00:00 2025-10-06 00:00:00+00:00    117073.53     124658.54       835.97       1287.94 2025-10-10 00:00:00+00:00       False
2025-11-27 00:00:00+00:00 2025-12-03 00:00:00+00:00     91333.95      93429.95       336.11       1030.76 2025-12-14 00:00:00+00:00       False
2025-12-03 00:00:00+00:00 2026-01-14 00:00:00+00:00     93429.95      96951.78      1030.76        871.18 2026-01-20 00:00:00+00:00        True
2026-02-14 00:00:00+00:00 2026-03-04 00:00:00+00:00     69822.95      72666.77       -85.65       1141.47 2026-03-06 00:00:00+00:00       False
2026-03-04 00:00:00+00:00 2026-03-16 00:00:00+00:00     72666.77      74884.67      1141.47        943.82 2026-03-19 00:00:00+00:00        True
2026-03-25 00:00:00+00:00 2026-05-10 00:00:00+00:00     71336.53      82210.07        28.15        717.57 2026-05-17 00:00:00+00:00       False
2026-06-15 00:00:00+00:00 2026-07-21 00:00:00+00:00     66328.74      66556.16       514.13        729.07 2026-07-31 00:00:00+00:00       False
8 月 13 日这个高点在 2025-08-18 被确认，那天收盘 116,227.05，相比 8 月 13 日 -5.74%
```

2025 年以来，算法找到了 11 对「创新高」的相邻高点，其中 3 对是顶背离，8 月 13 日这一对就是其中之一。

**但算法要到 8 月 18 日才能说出「8 月 13 日是一个高点，而且和 7 月 22 日构成顶背离」**：那一天收盘价比 8 月 13 日的高点回落了 5%，ZigZag 才确认这个高点。那时 BTC 收在 116,227.05，已经比 8 月 13 日低了 5.74%。

这就是选 C「等确认」的代价：等你确认了顶背离，已经跌掉了一截。而 8 月 18 日之后，BTC 又跌了约 7% 到 8 月 31 日的低点，然后反弹到 10 月的新高。

也看一下 10 月 6 日那个真正的顶：它和 9 月 18 日的高点相比，柱的最大值是 1,287.94，比前一段的 835.97 **更高**。按定义，这不是背离。

### 事后在图上看

![BTCUSDT 日线 2024–2026：算法找到的全部背离](/images/trade-analysis/13/divergences-on-chart.png)

把两年多里找到的背离全部画在图上，红色的顶背离大多出现在一段上涨的末端，绿色的底背离大多在一段下跌的末端。**看起来很准。**

但图上每一个标记都画在第二个摆动点上，也就是事后才知道的高点或低点。竖线才是算法真正知道的那一天。下一节用数据说明，为什么这张图会让人高估背离。

### ✋ 小检查 2

一段行情里，ZigZag 找到的摆动点依次是：第 12 根低点 90；第 20 根高点 100；第 28 根低点 93；第 40 根高点 104，在第 45 根被确认。MACD 柱在第 13 到 20 根之间最大是 8（在第 17 根），在第 29 到 40 根之间最大是 5（在第 35 根），第 41 根是 6。

(a) 按 `talab` 的定义，第 20 根和第 40 根这两个高点构成顶背离吗？

(b) 最早在第几根，算法能报告这个背离？

(c) 第 41 根的柱是 6，比 5 大。它会不会改变 (a) 的结论？

(d) 如果第 13 到 20 根之间柱的最大值是 -2，结论是什么？

答案在文末。

---

## 八、背离之后的走势

### 和什么比

要回答「背离有没有用」，关键是**对照组选什么**。

错误的对照是「所有日子」。顶背离一定出现在价格创新高的时候，而创新高之后的走势本来就和普通日子不一样。

这一节的对照是：**同样是相邻两个高点、后一个价格更高，而且同样在第二个高点被确认的那一刻，没有背离的那些。** 两组唯一的区别就是柱有没有跟着创新高。

打分用第 11 篇的方法：从确认那一根的收盘价出发，上下各放一条 2 倍 ATR 的线，20 根以内先碰到**顺着背离方向**的那一条（顶背离是下面那条，底背离是上面那条）记 1。检验用第 10 篇的**打乱标签**：保持每一对的结果不变，把「背离 / 不背离」的标签随机重排 2000 次，看实际差距有多常见。

```python
def label_test(values, flag, n=2000):
    """flag 为真的组减去其余的平均值；把标签随机打乱 n 次，看差距不小于实际的比例（第 10 篇）。"""
    v, f = np.asarray(values, float), np.asarray(flag, bool)
    ok = ~np.isnan(v)
    v, f = v[ok], f[ok]
    observed = v[f].mean() - v[~f].mean()
    sims = np.array([v[p].mean() - v[~p].mean() for p in (rng.permutation(f) for _ in range(n))])
    return observed, (np.abs(sims) >= abs(observed)).mean()


datasets = [("BTC 日线", day, 0.05), ("BTC 4 小时线", h4, 0.02), ("BTC 1 小时线", h1, 0.01),
            ("SPY 日线", spy, 0.015), ("AAPL 日线", aapl, 0.025)]
results = []
for name, df, threshold in datasets:
    close = df["close"]
    mm = I.macd(close)
    sw = X.zigzag(close, threshold)
    atr = X.wilder_smooth(X.true_range(df["high"], df["low"], close), 14)
    where = pd.Series(np.arange(len(close)), index=close.index)
    for kind, direction in [("bearish", -1), ("bullish", 1)]:
        pairs = I.divergences(sw, mm["hist"], kind)
        pairs = pairs[atr.reindex(pairs["confirmed_at"]).notna().to_numpy()]
        pairs["顺向"] = X.first_passage(close, df["high"], df["low"], atr, pairs["confirmed_at"],
                                      [direction] * len(pairs))
        for label, column in [("从确认时", "confirmed_at"), ("从摆动点", "second")]:
            a = where[pairs[column]].to_numpy()
            b = np.minimum(a + 20, len(close) - 1)
            pairs[label] = np.log(close.to_numpy()[b] / close.to_numpy()[a]) * direction
        gap, p = label_test(pairs["顺向"], pairs["divergence"])                # 20 根以内两条线都没碰到的不计入
        yes, no = pairs[pairs["divergence"]], pairs[~pairs["divergence"]]
        results.append({"数据": name, "方向": "顶背离" if kind == "bearish" else "底背离",
                        "背离": int(yes["顺向"].notna().sum()), "不背离": int(no["顺向"].notna().sum()),
                        "顺向 背离": yes["顺向"].mean(), "顺向 不背离": no["顺向"].mean(), "差": gap, "p": p,
                        "20 根收益 从确认时 背离": yes["从确认时"].mean(), "从确认时 不背离": no["从确认时"].mean(),
                        "从摆动点 背离": yes["从摆动点"].mean(), "从摆动点 不背离": no["从摆动点"].mean()})
table = pd.DataFrame(results)
print(table.iloc[:, :8].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print(table[["数据", "方向"] + list(table.columns[8:])].to_string(index=False, float_format=lambda v: f"{v:+.2%}"))
```

```text
       数据  方向  背离  不背离  顺向 背离  顺向 不背离      差     p
   BTC 日线 顶背离  24   43  0.542   0.488  0.053 0.802
   BTC 日线 底背离  25   36  0.640   0.500  0.140 0.324
BTC 4 小时线 顶背离  99  224  0.465   0.504 -0.040 0.560
BTC 4 小时线 底背离 107  210  0.561   0.452  0.108 0.081
BTC 1 小时线 顶背离 424  865  0.517   0.473  0.044 0.141
BTC 1 小时线 底背离 399  819  0.549   0.475  0.074 0.013
   SPY 日线 顶背离  28   45  0.321   0.378 -0.056 0.802
   SPY 日线 底背离  15   26  0.667   0.462  0.205 0.346
  AAPL 日线 顶背离  19   51  0.421   0.392  0.029 1.000
  AAPL 日线 底背离  13   34  0.462   0.500 -0.038 1.000
       数据  方向  20 根收益 从确认时 背离  从确认时 不背离  从摆动点 背离  从摆动点 不背离
   BTC 日线 顶背离          +1.49%    +2.30%   +8.18%    +8.94%
   BTC 日线 底背离          +2.10%    +0.82%   +8.53%    +7.27%
BTC 4 小时线 顶背离          +0.35%    -0.03%   +3.04%    +3.07%
BTC 4 小时线 底背离          +0.28%    +0.51%   +3.43%    +3.17%
BTC 1 小时线 顶背离          -0.12%    -0.09%   +1.42%    +1.44%
BTC 1 小时线 底背离          +0.32%    +0.04%   +1.91%    +1.51%
   SPY 日线 顶背离          -1.30%    -0.90%   +0.84%    +1.39%
   SPY 日线 底背离          +3.03%    +0.87%   +4.75%    +2.61%
  AAPL 日线 顶背离          -2.82%    -1.95%   +2.00%    +2.04%
  AAPL 日线 底背离          +1.99%    +0.30%   +4.38%    +3.67%
```

### 读这个结果

**第一张表：有背离和没有背离，差别很小，而且方向不一致。**

- 顶背离之后先碰到下面那条线的比例，BTC 日线是 54.2%，没有背离的是 48.8%；4 小时线反过来，46.5% 对 50.4%；SPY 也反过来。
- 底背离看起来稍好一些，10 个结果里 BTC 三个周期和 SPY 都是背离组更高，但只有 **BTC 1 小时线**（54.9% 对 47.5%，p = 0.013）够得上显著。
- 10 次检验里 1 次 p 小于 0.05，全是随机的话平均也会有 0.5 次。

**第二张表：事后看图的错觉，可以量化。**

表的右半边，是把起点从「确认的那一根」换成「摆动点那一根」（也就是图上画标记的地方），之后 20 根的顺向收益。

- BTC 日线的顶背离，从确认时算，之后 20 天顺向（下跌）只有 +1.49%；**从高点那一根算，是 +8.18%**。
- 可**没有背离的高点**，从高点那一根算也是 +8.94%，比有背离的还多。

原因很简单：**从一个事后确认的高点往后看，价格当然是跌的**，不管有没有背离。你在图上看到「顶背离之后大跌」，大跌的主要原因是你把标记画在了顶上，而不是背离。回到山路上：看回放的时候，每个山顶之后都是下坡，这和你爬那个山顶时的速度快慢没有关系。

### 在创新高的那一刻就判断

也许背离的价值不在确认之后，而在创新高的那一刻，就像决策点那天所有人做的那样。那就换一种写法：**收盘价第一次越过上一个已确认的高点时**，比较这一段和上一段柱的峰值。这一段只用到当时已经确认的低点，同样不看未来。

```python
def divergence_at_break(close, swings, indicator, kind="bearish", max_bars=60):
    """收盘价第一次越过上一个已确认的高点（低点）时，比较这一段和上一段指标的峰值。

    这一段从最近一个已确认的反向摆动点之后算起，到越过的这一根为止，全部是当时已经知道的数据。
    """
    want = 1 if kind == "bearish" else -1
    price, values, idx = close.to_numpy(float), indicator.to_numpy(float), close.index
    where = {tt: k for k, tt in enumerate(idx)}
    sw = swings.sort_values("confirmed_at").reset_index(drop=True)
    same, other = sw[sw["kind"] == want], sw[sw["kind"] == -want]
    rows = []
    for s in same.itertuples():
        before = other[other["time"] < s.time]
        leg = values[(where[before["time"].iloc[-1]] + 1 if len(before) else 0):where[s.time] + 1]
        if np.isnan(leg).all():
            continue
        old_peak = np.nanmax(leg) if want == 1 else np.nanmin(leg)
        following = same[same["confirmed_at"] > s.confirmed_at]
        stop = min(where[following["confirmed_at"].iloc[0]] if len(following) else len(price), where[s.time] + max_bars + 1)
        for j in range(where[s.confirmed_at] + 1, stop):
            if (price[j] - s.price) * want > 0:
                known = other[other["confirmed_at"] <= idx[j]]
                now = values[(where[known["time"].iloc[-1]] + 1 if len(known) else 0):j + 1]
                new_peak = np.nanmax(now) if want == 1 else np.nanmin(now)
                weaker = (new_peak - old_peak) * want < 0 and old_peak * want > 0
                rows.append((idx[j], s.time, old_peak, new_peak, bool(weaker)))
                break
    return pd.DataFrame(rows, columns=["time", "previous_swing", "previous_value", "value", "divergence"])


early = divergence_at_break(c, swings, m["hist"])
print(early[early["time"] >= "2025-07-01"].head(3).round({"previous_value": 1, "value": 1}).to_string(index=False))
results = []
for name, df, threshold in datasets:
    close = df["close"]
    mm = I.macd(close)
    sw = X.zigzag(close, threshold)
    atr = X.wilder_smooth(X.true_range(df["high"], df["low"], close), 14)
    for kind, direction in [("bearish", -1), ("bullish", 1)]:
        e = divergence_at_break(close, sw, mm["hist"], kind)
        e = e[atr.reindex(e["time"]).notna().to_numpy()]
        e["顺向"] = X.first_passage(close, df["high"], df["low"], atr, e["time"], [direction] * len(e))
        gap, p = label_test(e["顺向"], e["divergence"])
        results.append({"数据": name, "方向": "顶背离" if kind == "bearish" else "底背离",
                        "背离": int(e.loc[e["divergence"], "顺向"].notna().sum()),
                        "不背离": int(e.loc[~e["divergence"], "顺向"].notna().sum()),
                        "顺向 背离": e.loc[e["divergence"], "顺向"].mean(), "顺向 不背离": e.loc[~e["divergence"], "顺向"].mean(),
                        "差": gap, "p": p})
print(pd.DataFrame(results).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
```

```text
                     time            previous_swing  previous_value  value  divergence
2025-07-09 00:00:00+00:00 2025-06-10 00:00:00+00:00            26.6  343.4       False
2025-08-12 00:00:00+00:00 2025-07-22 00:00:00+00:00          1176.1  250.2        True
2025-10-01 00:00:00+00:00 2025-09-18 00:00:00+00:00           836.0  322.5        True
       数据  方向  背离  不背离  顺向 背离  顺向 不背离      差     p
   BTC 日线 顶背离  40   37  0.500   0.514 -0.014 1.000
   BTC 日线 底背离  28   36  0.643   0.500  0.143 0.315
BTC 4 小时线 顶背离 177  195  0.492   0.441  0.050 0.353
BTC 4 小时线 底背离 183  181  0.459   0.486 -0.027 0.671
BTC 1 小时线 顶背离 682  730  0.513   0.453  0.060 0.025
BTC 1 小时线 底背离 725  756  0.506   0.471  0.035 0.164
   SPY 日线 顶背离  43   32  0.349   0.312  0.036 0.797
   SPY 日线 底背离  24   29  0.583   0.586 -0.003 1.000
  AAPL 日线 顶背离  39   37  0.359   0.405 -0.046 0.802
  AAPL 日线 底背离  20   38  0.500   0.500  0.000 1.000
```

这个写法在 8 月 12 日（第一次收在 7 月 22 日高点上方的那天）就报告了背离。

**结果和确认版差不多：** 10 个结果里，只有 BTC 1 小时线的顶背离够得上显著（先碰到下面那条线 51.3% 对 45.3%，p = 0.025）。日线上三个标的都看不出区别。这里的「顺向」是指朝背离预示的方向：顶背离时向下。换句话说，**价格突破前高时，柱没有跟着创新高的那些，并没有比柱跟着创新高的更容易掉头**，只有 BTC 1 小时线上差了 6 个百分点。

这和第 11 篇的发现也对得上：在 BTC 上，突破前高之后价格倾向于继续走，有没有 MACD 的配合，差别不大。

### 结论

把两种写法、5 组数据、顶底两个方向合在一起，一共 20 次检验，2 次 p 小于 0.05，都在 BTC 1 小时线上，幅度是 6 到 7 个百分点；全是随机的话平均会有 1 次。

- **日线上，MACD 背离在这三个标的上没有增加可测量的信息。**
- **BTC 1 小时线上有一点迹象**，但两种写法里显著的方向不同（一个是底背离，一个是顶背离），很难说是稳定的规律。
- **事后在图上看到的「背离很准」，主要来自把标记画在了事后才知道的高低点上。**

---

## 九、talab.indicators：第三部分

### 新增了什么

| 函数 | 作用 |
|---|---|
| `macd` | MACD 线、信号线、柱，和 TA-Lib 的 MACD 一致 |
| `ema_response` | n 日 EMA 对某个周期正弦波的复数响应（放大倍数和相位） |
| `divergences` | 相邻两个同类摆动点之间的背离，同时保留不是背离的对照 |

`divergence_at_break`、`label_test` 这些只在这一篇分析用的函数**不放进模块**，只在 `docs/trade-analysis/analysis/13_macd.py` 里。

### 代码

```python
# ---------------------------------------------------------------------------
# 五、MACD（第 13 篇）
# ---------------------------------------------------------------------------

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD（Appel）：快 EMA 减慢 EMA 是 MACD 线，MACD 线的 EMA 是信号线，两者之差是柱（Aspray）。

    和 TA-Lib 的 MACD 一致，有两处细节：
    1. 快 EMA 不从第 fast 根开始，而是和慢 EMA 同一根开始：用第 slow - fast + 1 到第 slow 个有效值的平均做初始值
    2. 三列同时出现，都从第 slow + signal - 1 个有效值开始；在这之前 MACD 线虽然算得出来，也记为 NaN
    返回 macd、signal、hist 三列，单位和价格相同。
    """
    for n in (fast, slow, signal):
        _check_period(n)
    if fast >= slow:
        raise ValueError(f"快线周期 {fast} 必须小于慢线周期 {slow}")
    valid = np.flatnonzero(close.notna().to_numpy())
    if len(valid) == 0:
        return pd.DataFrame({"macd": close * np.nan, "signal": close * np.nan, "hist": close * np.nan})
    position = np.arange(len(close))
    fast_line = ema(close.where(position >= valid[0] + slow - fast), fast)      # 让快 EMA 和慢 EMA 同一根开始
    line = fast_line - ema(close, slow)
    signal_line = ema(line, signal)
    line = line.where(signal_line.notna())
    return pd.DataFrame({"macd": line, "signal": signal_line, "hist": line - signal_line})


def ema_response(n: int, period) -> np.ndarray:
    """n 日 EMA 对「周期为 period 根 K 线的正弦波」的复数响应：绝对值是振幅放大倍数，辐角是相位。

    alpha = 2 / (n + 1)，响应 = alpha / (1 - (1 - alpha) × e^(-iω))，ω = 2π / period。
    MACD 线的响应是 ema_response(fast) - ema_response(slow)；柱再乘以 1 - ema_response(signal)。
    """
    alpha = 2 / (n + 1)
    omega = 2 * np.pi / np.asarray(period, dtype=float)
    return alpha / (1 - (1 - alpha) * np.exp(-1j * omega))


def divergences(swings: pd.DataFrame, indicator: pd.Series, kind: str = "bearish",
                min_bars: int = 5, max_bars: int = 60) -> pd.DataFrame:
    """找出相邻两个同类摆动点之间的背离。

    swings 是 structure.zigzag 或 fractals 的结果；indicator 通常是 MACD 柱，索引和价格相同。
    kind="bearish"（顶背离）：相邻两个摆动高点，后一个价格更高，相隔 min_bars 到 max_bars 根。
        每个高点对应的指标值，取「前一个摆动低点之后（不含）到这个高点（含）」这一段里指标的最大值，
        因为柱的峰值常常比价格的高点早出现几根。
        后一段的最大值更低、而且前一段的最大值大于 0，就是背离。
    kind="bullish"（底背离）：高低、大小全部反过来。
    返回每一对「价格创新高（新低）」的摆动点，divergence 列标明是不是背离；不是背离的也保留，方便做对照。
    confirmed_at 是第二个摆动点被确认的时刻：在这之前，第二个高点还不存在，背离也就还不存在。
    """
    if kind not in ("bearish", "bullish"):
        raise ValueError('kind 只能是 "bearish" 或 "bullish"')
    want = 1 if kind == "bearish" else -1
    values = indicator.to_numpy(dtype=float)
    pos = {t: i for i, t in enumerate(indicator.index)}
    ordered = swings.sort_values("time").reset_index(drop=True)
    rows, previous, leg_start = [], None, 0
    for s in ordered.itertuples():
        if s.kind != want:
            leg_start = pos[s.time] + 1                      # 反向的摆动点之后，开始新的一段
            continue
        leg = values[leg_start:pos[s.time] + 1]
        leg = leg[~np.isnan(leg)]
        extreme = (leg.max() if want == 1 else leg.min()) if len(leg) else np.nan
        if previous is not None and not np.isnan(extreme) and not np.isnan(previous[1]):
            first, first_value = previous
            gap = pos[s.time] - pos[first.time]
            further = (s.price - first.price) * want > 0
            if min_bars <= gap <= max_bars and further:
                weaker = (extreme - first_value) * want < 0
                same_side = first_value * want > 0
                rows.append((first.time, s.time, first.price, s.price, first_value, extreme, s.confirmed_at,
                             bool(weaker and same_side)))
        previous = (s, extreme)
    return pd.DataFrame(rows, columns=["first", "second", "first_price", "second_price",
                                       "first_value", "second_value", "confirmed_at", "divergence"])
```

### 读一遍代码

**`macd`** 的关键是 `close.where(position >= valid[0] + slow - fast)`：把第 slow - fast 个有效值之前的价格暂时变成 NaN，再交给第 12 篇的 `ema`。`ema` 会跳过开头的 NaN，于是快 EMA 恰好和慢 EMA 在同一根出现，初始值是那 fast 个价格的平均。这样不用复制一遍 EMA 的递推代码，就得到了 TA-Lib 的写法。最后 `line.where(signal_line.notna())` 让三列同时出现。

**`ema_response`** 直接写出公式。它接受一个数组，所以可以一次算出几千个周期的放大倍数，画出第四节那张图。

**`divergences`** 按时间遍历摆动点，`leg_start` 记录「这一段」从哪里开始：每遇到一个反向的摆动点，就把起点挪到它的下一根。遇到同向的摆动点时，取这一段指标的最大值（或最小值），和上一个同向摆动点比较。

两个细节：

- `leg[~np.isnan(leg)]`：一段全是预热期的 NaN 时，这个摆动点没有指标值，不参与比较，也不会触发 numpy 的「全是 NaN」警告。
- `weaker and same_side`：柱更低，并且前一段的最大值在 0 上方，才算顶背离。不满足的也作为一行返回，`divergence` 是 False。

### 测试

```python
def test_macd_by_hand():
    x = hourly([1, 2, 4, 8, 6, 5, 7])
    m = I.macd(x, fast=2, slow=4, signal=2)
    # 慢 EMA（alpha 0.4）：第 3 根 (1+2+4+8)/4 = 3.75，然后 4.65、4.79、5.674
    # 快 EMA（alpha 2/3）从第 2 根开始：第 3 根 (4+8)/2 = 6，然后 6、5.3333、6.4444
    # MACD 线：2.25、1.35、0.5433、0.7704；信号线（alpha 2/3）第 4 根 (2.25+1.35)/2 = 1.8，然后 0.9622、0.8344
    assert m["macd"].iloc[:4].isna().all() and m["signal"].iloc[:4].isna().all()   # 三列同时从第 slow + signal - 2 根开始
    assert m["macd"].iloc[4:].tolist() == pytest.approx([1.35, 0.54333333, 0.77044444])
    assert m["signal"].iloc[4:].tolist() == pytest.approx([1.8, 0.96222222, 0.83437037])
    assert m["hist"].iloc[4] == pytest.approx(1.35 - 1.8)


def test_macd_on_a_ramp():
    ramp = hourly(np.arange(200))
    m = I.macd(ramp)
    assert m["macd"].first_valid_index() == ramp.index[33]
    # 两条 EMA 在直线上分别落后 (26-1)/2 = 12.5 和 (12-1)/2 = 5.5 根，差 7 根，每根涨 1：MACD 线恒等于 7，柱恒等于 0
    assert m["macd"].dropna().to_numpy() == pytest.approx(7)
    assert m["hist"].dropna().to_numpy() == pytest.approx(0, abs=1e-9)


def test_macd_rejects_bad_periods():
    with pytest.raises(ValueError):
        I.macd(hourly(np.arange(50)), fast=26, slow=12)


def test_macd_never_uses_the_future():
    rng = np.random.default_rng(13)
    x = hourly(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 300))))
    full = I.macd(x)
    for k in [40, 150, 299]:
        pd.testing.assert_frame_equal(I.macd(x.iloc[:k]), full.iloc[:k])


@pytest.mark.parametrize("fast,slow,signal", [(12, 26, 9), (5, 35, 5), (3, 10, 16)])
def test_macd_matches_talib(fast, slow, signal):
    talib = pytest.importorskip("talib")
    rng = np.random.default_rng(fast)
    x = hourly(50_000 * np.exp(np.cumsum(rng.normal(0, 0.03, 2000))))
    ours = I.macd(x, fast, slow, signal)
    for column, theirs in zip(["macd", "signal", "hist"], talib.MACD(x.to_numpy(), fast, slow, signal)):
        assert (ours[column].isna().to_numpy() == np.isnan(theirs)).all()
        np.testing.assert_allclose(ours[column].to_numpy(), theirs, rtol=1e-12, atol=1e-8)


def amplitude(y, period):
    """用最小二乘拟合正弦波的振幅（取整数个周期），不受采样点有没有落在波峰上的影响。"""
    t = np.arange(len(y))
    y = np.asarray(y, dtype=float) - np.mean(y)
    return np.hypot(2 * np.mean(y * np.sin(2 * np.pi * t / period)), 2 * np.mean(y * np.cos(2 * np.pi * t / period)))


def test_ema_response_matches_a_sine_wave():
    period = 40
    t = np.arange(4000)
    wave = hourly(100 + np.sin(2 * np.pi * t / period))
    steady = I.ema(wave, 20).iloc[2000:]                                   # 跳过开头，只看稳定之后的 50 个周期
    assert amplitude(steady, period) == pytest.approx(abs(I.ema_response(20, period)), rel=1e-6)
    assert abs(I.ema_response(20, 1e9)) == pytest.approx(1)              # 周期无限长（不变的价格）时原样通过
    line = I.macd(wave)["macd"].iloc[2000:]
    gain = abs(I.ema_response(12, period) - I.ema_response(26, period))
    assert amplitude(line, period) == pytest.approx(gain, rel=1e-6)


def make_swings(index, rows):
    return pd.DataFrame([(index[i], price, kind, index[c]) for i, price, kind, c in rows], columns=X.SWING_COLUMNS)


def test_divergences_by_hand():
    idx = pd.date_range("2024-01-01", periods=40, freq="1D", tz="UTC")
    swings = make_swings(idx, [(0, 90, -1, 3), (10, 100, 1, 13), (15, 95, -1, 18), (25, 105, 1, 28), (30, 96, -1, 33)])
    hist = pd.Series(0.0, index=idx)
    hist.iloc[8], hist.iloc[22] = 5.0, 3.0            # 第一段（1~10）最大 5，第二段（16~25）最大 3
    d = I.divergences(swings, hist, "bearish")
    assert d[["first", "second", "first_value", "second_value", "confirmed_at", "divergence"]].values.tolist() == \
        [[idx[10], idx[25], 5.0, 3.0, idx[28], True]]
    hist.iloc[22] = 6.0                                # 第二段更强：价格和指标一起创新高，不是背离
    assert not I.divergences(swings, hist, "bearish")["divergence"].iloc[0]
    hist.iloc[8], hist.iloc[22] = -1.0, -2.0           # 前一段的峰值在 0 下方：不算顶背离
    assert not I.divergences(swings, hist, "bearish")["divergence"].iloc[0]
    assert len(I.divergences(swings, hist, "bearish", max_bars=10)) == 0      # 两个高点相隔 15 根，超过上限


def test_divergences_bullish_mirror():
    idx = pd.date_range("2024-01-01", periods=40, freq="1D", tz="UTC")
    swings = make_swings(idx, [(0, 110, 1, 3), (10, 100, -1, 13), (15, 104, 1, 18), (25, 95, -1, 28)])
    hist = pd.Series(0.0, index=idx)
    hist.iloc[9], hist.iloc[20] = -5.0, -2.0
    d = I.divergences(swings, hist, "bullish")
    assert d["divergence"].tolist() == [True] and d["second_price"].iloc[0] == 95
```

- `test_macd_by_hand`：第三节的手算，包括三列同时出现。
- `test_macd_on_a_ramp`：直线上 MACD 线恒等于 7、柱恒等于 0，第一个值在第 34 根。
- `test_macd_rejects_bad_periods`：快线周期不小于慢线周期时报错。
- `test_macd_never_uses_the_future`：截断 3 次，前 k 行必须和全部数据算出的一致。
- `test_macd_matches_talib`：3 组参数，三列都要和 TA-Lib 一致，包括 NaN 的位置。
- `test_ema_response_matches_a_sine_wave`：EMA 和 MACD 线在正弦波上的实测振幅，和公式的相对误差小于百万分之一。`amplitude` 用最小二乘拟合振幅，而不是取最高点和最低点，因为一个周期只有 40 个采样点时，采样点不一定正好落在波峰上，那样会低估约 0.3%。
- `test_divergences_by_hand` 和 `test_divergences_bullish_mirror`：小检查 2 那样的构造，覆盖「柱更高不算」「前一段在 0 下方不算」「超过距离上限不算」和底背离。

```bash
pytest -q
```

```text
........................................................................ [ 67%]
..................................                                       [100%]
106 passed in 0.49s
```

---

## 十、常见误用

**1. 把背离画在事后才知道的高点上，再说「背离之后大跌」。**
BTC 日线上，从高点那一根算，没有背离的高点之后 20 天也跌了 8.94%，比有背离的还多。

**2. 以为背离出现在创新高的那一刻。**
按摆动点定义的背离，要等第二个高点被确认才存在。8 月 13 日的背离，8 月 18 日才确认，那时价格已经跌了 5.74%。

**3. 用「所有日子」做对照。**
背离只出现在创新高（新低）的时候。要回答背离有没有用，对照组应该是同样创新高、但没有背离的那些。

**4. 跨越很长时间比较 MACD 的数值。**
MACD 的单位是价格。BTC 从 4,000 涨到 120,000，同样的波动幅度，MACD 的数值会大 30 倍。

**5. 用 `ema(close, 12) - ema(close, 26)` 去和 TA-Lib、交易软件对账。**
快 EMA 的起点不同，BTC 上开头差了 23 美元，要 200 根才完全一致。

**6. 以为 MACD 柱反映的是整个趋势的强弱。**
柱对 12 到 61 根一个来回的波动最敏感，对几百根的长期趋势几乎没有反应。

**7. 从几条 MACD 规则、几个标的里挑出最好的一个，当作发现。**
BTC 上「MACD 线 > 0 就持有」年化 40.1%，是 6 个结果里最好的一个，而且没扣成本。

---

## 十一、这一篇能回答什么，不能回答什么

| 这一篇**能**帮你回答 | 这一篇**不能**回答 |
|---|---|
| MACD 的每个数字是怎么算出来的，和 TA-Lib 是否一致 | MACD(12, 26, 9) 是不是最好的参数 |
| MACD 线和柱对哪些周期的波动敏感 | 市场里此刻主导的是哪个周期的波动 |
| 某一对高点（低点）之间有没有背离，最早什么时候能知道 | 这一次背离之后会不会见顶 |
| 在这三个标的、这几个周期上，背离有没有增加信息 | 换一个标的、一个指标（比如 RSI）、一种摆动点算法，结论是否一样（练习 4、5） |
| 事后看图时，背离的效果被高估了多少 | 实时交易中你会不会被同样的错觉影响 |

---

## 十二、小结

1. **MACD 线 = 12 日 EMA - 26 日 EMA，信号线是它的 9 日 EMA，柱是两者之差。** 单位和价格相同，不同价位之间不能直接比较。

2. **和 TA-Lib 对账要注意快 EMA 的起点。** TA-Lib 让快 EMA 和慢 EMA 同一根开始，三列从第 34 根一起出现。简单相减的写法在 BTC 上要 200 根才对上。

3. **直线上 MACD 线恒等于 7 倍斜率、柱等于 0。** MACD 线是平滑后的「速度」，柱是速度的变化。

4. **两条 EMA 之差是带通滤波器。** MACD 线对约 55 根一个来回的波动最敏感（22 到 141 根），柱对约 29 根（12 到 61 根）。公式和正弦波实测完全一致。

5. **交叉和零轴状态本身，在三个标的上都不能预测之后的收益。** 当作持有规则，MACD 的回撤比主线 v0 小、交易多得多；BTC 上「MACD 线 > 0」年化 40.1%，但这是挑出来的、没扣成本的结果。

6. **背离写成算法，要回答五个问题**：用什么摆动点、指标值取在哪、隔多远、要不要在 0 的同一侧、什么时候知道。`talab` 的背离在第二个摆动点被确认时才存在。

7. **同样是价格创新高（新低），有背离和没有背离，之后的走势在日线上没有可测量的区别。** 两种写法、5 组数据、20 次检验，2 次显著，都在 BTC 1 小时线上，方向还不一致。

8. **事后在图上看到的「背离很准」，来自把标记画在了事后才知道的高低点上。** 从高点往后看，没有背离的高点跌得一样多。

9. **决策点那次顶背离说对了一半**：两周内跌了 9.8%，但 10 月 6 日又创了新高，真正的顶没有背离。

最后回到山路上。码表告诉你这一段爬得比上一段慢，这是真的（第三、四节）。可爬坡变慢的原因有很多，下一段是下坡还是更陡的上坡，码表不知道（第八节）。至于看回放时觉得「每次减速之后都到顶了」，那是因为回放里你只注意到了那些真正到顶的减速（第七、八节）。

下一篇是第 14 篇：**振荡器：RSI 与 Stochastic**。RSI 已经连续 12 天高于 70，「超买」了。在强趋势里，超买超卖为什么会失效？同一条「超卖买入」的规则，在震荡段和趋势段表现有多不同？

---

## 练习

**练习 1（手算）**
价格依次是 10、12、11、14、13、15、18、16，用 MACD(2, 4, 2)。

- (a) 按 TA-Lib 的写法，算出快 EMA、慢 EMA、MACD 线、信号线和柱。第一个完整的值在第几根？
- (b) 如果快 EMA 从第 2 根就开始算（简单相减的写法），最后一根的 MACD 线差多少？

**练习 2（推导）**
第四节给出了 EMA 的响应公式。

- (a) 从递推公式 EMAₜ = EMAₜ₋₁ + α(Pₜ - EMAₜ₋₁) 出发，代入 Pₜ = e^(iωt)，推出这个公式。
- (b) 算出 MACD(12, 26, 9) 的 MACD 线对周期 55 根的正弦波，相位是超前还是落后？落后（超前）多少根？
- (c) 用 `ema_response` 画出 MACD(5, 35, 5) 的放大倍数曲线。它对哪个周期最敏感？

**练习 3（编程）**
第三节说 MACD 的单位是价格。

- (a) 写一个 `ppo(close, fast, slow, signal)`：MACD 线除以慢 EMA 再乘以 100，信号线和柱照此计算。
- (b) 用 PPO 的柱重新做第八节的背离检验（BTC 日线和 1 小时线）。结论变不变？

**练习 4（数据）**
第七节的定义有很多选择。

- (a) 把「每个高点对应的指标值」从「这一段的最大值」改成「高点那一根的值」，重做 BTC 日线的检验。
- (b) 把摆动点从 ZigZag 换成第 8 篇的分形（左右各 5 根），重做一遍。
- (c) 在 (a)(b) 的所有组合里，你找到的最小 p 值是多少？用第十节误用 7 的思路解释它。

**练习 5（数据）**
把指标从 MACD 柱换成第 12 篇的乖离率（收盘价相对 50 日 SMA），重做第八节的两种检验。背离的结论和指标有关吗？

**练习 6（思考）**
第八节的第二张表显示，从摆动点那一根算，没有背离的高点之后也跌了 8.94%。

- (a) 用第 8 篇 ZigZag 的定义解释：为什么从一个 5% ZigZag 高点往后 20 天，平均一定是跌的？
- (b) 在网上找一篇「MACD 背离准确率」的文章，看看它的统计起点是哪一根。

---

## 小检查答案

**小检查 1**

(a) MACD 线 = 7 × 3 = **21** 美元。柱 = **0**：MACD 线不变，信号线也收敛到 21。

(b) 5 日 EMA 落后 (5 - 1) ÷ 2 = 2 根，20 日 EMA 落后 (20 - 1) ÷ 2 = 9.5 根，相差 7.5 根。MACD 线 = 7.5 × 3 = **22.5**。

(c) 两条 EMA 都等于 100，MACD 线 = **0**，柱也是 0。

**小检查 2**

(a) **构成顶背离。** 第二个高点 104 高于第一个 100，相隔 20 根（在 5 到 60 之内）；第一段（第 13 到 20 根）柱最大 8，第二段（第 29 到 40 根）最大 5，更低；第一段的 8 大于 0。

(b) **第 45 根。** 在第 40 根被确认为高点之前，算法不知道第 40 根是高点，也就没有「第二个高点」。

(c) **不会。** 这一段的范围是从前一个低点之后到这个高点为止（第 29 到 40 根），第 41 根在高点之后，不属于这一段。

(d) **不算顶背离。** 前一段柱的最大值在 0 下方，谈不上「上一段的动能」，`same_side` 不成立。算法仍会返回这一对高点，`divergence` 是 False。
