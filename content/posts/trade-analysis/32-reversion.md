---
title: "第 32 篇：均值回归"
date: 2026-09-17
weight: 32
tags: ["交易技术分析"]
draft: false
summary: "2020 年 2 月 26 日，SPY 连跌五天、收在 20 日均线下方 2.31 个标准差、2 日 RSI 只有 0.65。同一个条件过去出现过七次，五次在五天后是涨的，平均 +1.82%。买不买？揭晓：接下来二十根 **−20.77%**，期间最低 **−28.43%**。但这一篇真正的答案是——**完整的规则在那几天实际只亏了 0.70%**，因为止损连打两次之后，第三次接住了反弹。这一篇把均值回归的每一样东西和第 31 篇的趋势跟随摆在一起：胜率 75.8% 对 32.9%、盈亏比 0.76 对 10.06、凹对凸、怕一路不回头对怕来回震荡。而**同一个数（60 天方差比 0.616 / 0.852 / 1.270）同时决定了两篇的全部结论**。最后把两条腿放进同一个账户：SPY 上夏普从 0.68 和 0.73 升到 **0.98**，最大回撤从 −17% 和 −12% 降到 **−6.30%**。"
showToc: true
tocOpen: false
---

| | |
|---|---|
| **本篇位置** | 第七部分「策略原型」第二篇，也是最后一篇。第 31 篇讲凸的那一半，这一篇讲凹的那一半 |
| **用到的数据** | SPY、AAPL、BTC 日线（全部沿用前面几篇，不需要新下载） |
| **动手** | 新模块 `talab.reversion`：`stretch`、`streak`、`setups`、`edge`、`ReversionPlan` + `reversion`、`worst_trades`、`blend`，附 13 个测试 |
| **读完你能** | 判断一个市场该用趋势跟随还是均值回归，并把两条腿合成一个账户 |

---

## 一、先做一个决定

一个条件：**收盘价连跌五天以上，而且低于 20 日均线 2 个标准差。**

在 SPY 上，这个条件从 2016 年到现在出现过十四次。下面是**其中的前七次**，以及每一次之后发生了什么：

```text
「连跌 5 天以上，而且收盘价低于 20 日均线 2 个标准差」——2020-02-26 之前出现过 7 次：
        时间     收盘    1 根后    5 根后   10 根后   20 根后    期间最低
2018-10-24 265.32  0.0179  0.0200  0.0591 -0.0011 -0.0055
2018-12-19 251.26 -0.0163 -0.0127  0.0045  0.0605 -0.0673
2018-12-20 247.17 -0.0262  0.0023  0.0292  0.0635 -0.0519
2018-12-21 240.70 -0.0264  0.0383  0.0668  0.0943 -0.0264
2018-12-24 234.34  0.0505  0.0676  0.1008  0.1246  0.0421
2019-08-02 292.62 -0.0301 -0.0034 -0.0129 -0.0006 -0.0301
2019-08-05 283.82  0.0140  0.0150  0.0300  0.0244  0.0003

那 7 次：5 根后 5/7 是涨的，平均 +1.82%；20 根后 5/7 是涨的，平均 +5.22%

今天是 2020-02-26：SPY 收在 311.50，连跌 5 天，偏离 20 日均线 -2.31 个标准差，2 日 RSI = 0.65
```

![决策点](/images/trade-analysis/32/decision.png)

**七次里，五次在五天后是涨的，平均 +1.82%；二十天后也是五次涨，平均 +5.22%。**最难看的一次（2019-08-02）五天后也只是 −0.34%。

今天是 2020 年 2 月 26 日。SPY 收在 311.50，连跌五天，偏离 20 日均线 **−2.31** 个标准差，**2 日 RSI 只有 0.65**——几乎是这个指标能到的最低值。

买不买？

---

## 二、揭晓

```text
   1 根之后：-4.49%
   5 根之后：+0.44%
  10 根之后：-11.92%
  20 根之后：-20.77%
  期间最低：-28.43%（2020-03-23 收在 222.95）
```

![揭晓](/images/trade-analysis/32/reveal.png)

**二十根之后 −20.77%，期间最低 −28.43%。**那是 2020 年 3 月。

这一次落在了 14 次里最坏的那一次上，而且坏得不成比例：**前面七次加起来的盈利，抵不上这一次的零头。**

但这不是这一篇的结论。右边那张图才是——它画的是**完整的规则**（带止损、带出场）在同一段时间里实际做的事。我们第八节再回来看。

---

## 三、打个比方：捡硬币

**均值回归就是在压路机前面捡硬币。**

这个比方不太好听，但它每一处都对得上：

| 捡硬币 | 均值回归 |
|---|---|
| 大部分时候都能捡到 | **胜率高**（这一篇实测 70%–76%） |
| 每次只捡到一枚 | 平均每笔只赚 1.7%–4.6% |
| 压路机偶尔会碾过来 | **偶发的大额亏损**（BTC 上最差一笔 −25.10%） |
| 路面越平整越安全 | **方差比越小的市场越适合** |
| 关键不是弯不弯腰，是**什么时候站起来跑** | **生死不在进场，在出场** |

第 31 篇的趋势跟随是它的镜像：十次有七次白跑，但跑对一次抵得上前面十次。**两种策略赚的是同一件事的两面——市场要么延续，要么反转，不可能都不是。**

---

## 四、这个信号到底值多少

先回答一个比「买不买」更前面的问题：**这个条件本身携带信息吗？**

只看「五天后胜率 85.71%」没有意义——如果随便哪一天买入五天后的胜率也有 85%，那这个条件什么都没说。所以要和基准比：

```python
print(pd.DataFrame({f"{k} 根后": RV.edge(table, close, horizon=k) for k in (1, 5, 10, 20)}).round(4).to_string())
```

```text
          1 根后     5 根后    10 根后    20 根后
次数     14.0000  14.0000  14.0000  14.0000
胜率      0.4286   0.8571   0.6429   0.6429
平均     -0.0007   0.0139  -0.0035   0.0050
中位     -0.0034   0.0071   0.0142   0.0322
最差     -0.0449  -0.0127  -0.1660  -0.2077
基准胜率    0.5512   0.6119   0.6503   0.6870
基准平均    0.0006   0.0028   0.0056   0.0113
比基准多赚  -0.0013   0.0111  -0.0091  -0.0063
```

![信号的价值](/images/trade-analysis/32/signal.png)

把四列并排读，一整篇的结论就在里面：

| | 1 根后 | **5 根后** | 10 根后 | 20 根后 |
|---|---|---|---|---|
| 胜率 | 42.86% | **85.71%** | 64.29% | 64.29% |
| 基准胜率 | 55.12% | 61.19% | 65.03% | 68.70% |
| 平均 | −0.07% | **+1.39%** | −0.35% | +0.50% |
| **比基准多赚** | −0.13% | **+1.11%** | −0.91% | −0.63% |
| **最差的那一次** | −4.49% | **−1.27%** | −16.60% | **−20.77%** |

**优势只活在「五根」这个窗口里。**一根太早（那天还在跌，胜率只有 42.86%），十根、二十根太晚（优势变成负的，而最差的那一次从 −1.27% 变成 −20.77%）。

> 这就是凹性最干净的数字版：**你能赚到的那一点，有一个很短的保质期；而你可能亏掉的那一大块，没有。**

### 4.1 换三个标的、换四个条件

```python
rows = []
for name, (frame, periods) in MARKETS.items():
    price = frame["close"]
    stretched, streaks = RV.stretch(price, 20), RV.streak(price)
    for label, flag in [("偏离 ≤ −2", stretched <= -2),
                        ("连跌 ≥ 3 天", streaks <= -3),
                        ("偏离 ≤ −2 且连跌 ≥ 3 天", (stretched <= -2) & (streaks <= -3)),
                        ("2 日 RSI < 5", I.rsi(price, 2) < 5)]:
        stats = RV.edge(RV.setups(price, flag, horizons=(5,)), price, horizon=5)
        rows.append({"标的": name, "条件": label, "次数": int(stats["次数"]), "5 根后胜率": stats["胜率"],
                     "5 根后平均": stats["平均"], "基准胜率": stats["基准胜率"],
                     "基准平均": stats["基准平均"], "比基准多赚": stats["比基准多赚"],
                     "最差一次": stats["最差"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的                条件  次数  5 根后胜率  5 根后平均   基准胜率   基准平均   比基准多赚    最差一次
 SPY           偏离 ≤ −2 115  0.7130  0.0094 0.6119 0.0028  0.0066 -0.1254
 SPY          连跌 ≥ 3 天 211  0.6398  0.0059 0.6119 0.0028  0.0031 -0.1254
 SPY 偏离 ≤ −2 且连跌 ≥ 3 天  60  0.7000  0.0077 0.6119 0.0028  0.0049 -0.1254
 SPY       2 日 RSI < 5 107  0.6262  0.0045 0.6119 0.0028  0.0017 -0.0823
AAPL           偏离 ≤ −2 107  0.4953  0.0085 0.5869 0.0058  0.0027 -0.0793
AAPL          连跌 ≥ 3 天 240  0.5625  0.0083 0.5869 0.0058  0.0025 -0.1090
AAPL 偏离 ≤ −2 且连跌 ≥ 3 天  53  0.6226  0.0160 0.5869 0.0058  0.0102 -0.0793
AAPL       2 日 RSI < 5 133  0.5489  0.0116 0.5869 0.0058  0.0058 -0.0683
 BTC           偏离 ≤ −2 143  0.5734 -0.0019 0.5320 0.0075 -0.0094 -0.2298
 BTC          连跌 ≥ 3 天 334  0.5778  0.0047 0.5320 0.0075 -0.0029 -0.3478
 BTC 偏离 ≤ −2 且连跌 ≥ 3 天  62  0.5484  0.0013 0.5320 0.0075 -0.0063 -0.2298
 BTC       2 日 RSI < 5 189  0.6085  0.0012 0.5320 0.0075 -0.0064 -0.3209
```

只看最后两列（「比基准多赚」和「最差一次」）：

| 标的 | 四个条件的「比基准多赚」 | 结论 |
|---|---|---|
| SPY | +0.66% / +0.31% / +0.49% / +0.17% | **四个全是正的** |
| AAPL | +0.27% / +0.25% / +1.02% / +0.58% | 全是正的，但次数少、波动大 |
| BTC | −0.94% / −0.29% / −0.63% / −0.64% | **四个全是负的** |

**在 BTC 上，「跌得太多」不是买入信号，是反向指标。**这和第 31 篇正好对上：BTC 是三个标的里最适合趋势跟随的（海龟年化 31.60%、夏普 1.367），也是最不适合均值回归的。

---

## 五、同一个数解释两篇

为什么？第 5 篇的**方差比**早就把答案给了：

```python
rows = []
for name, (frame, periods) in MARKETS.items():
    logs = S.log_returns(frame["close"])
    rows.append({"标的": name, **{f"{k} 天方差比": S.variance_ratio(logs, k) for k in (2, 5, 10, 20, 60)},
                 "1 日自相关": float(S.autocorr(logs, lags=(1,)).iloc[0])})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的  2 天方差比  5 天方差比  10 天方差比  20 天方差比  60 天方差比  1 日自相关
 SPY  0.8715  0.8501   0.8253   0.8178   0.6161 -0.1286
AAPL  0.9415  0.9025   0.8750   0.8873   0.8524 -0.0588
 BTC  0.9504  0.9820   1.0237   1.0886   1.2702 -0.0496
```

> 方差比 = k 天收益率的方差 ÷ (k × 1 天收益率的方差)。等于 1 表示各天互相独立；**大于 1 表示涨跌倾向于延续，小于 1 表示倾向于反转。**

| 标的 | 20 天方差比 | 60 天方差比 | 1 日自相关 | 趋势跟随夏普 | 均值回归夏普 |
|---|---|---|---|---|---|
| SPY | 0.818 | **0.616** | **−0.129** | 0.682 | **0.725** |
| AAPL | 0.887 | 0.852 | −0.059 | **1.260** | 0.527 |
| BTC | 1.089 | **1.270** | −0.050 | **1.367** | 0.193 |

**方差比从 0.616 走到 1.270，两条策略的强弱就跟着掉了个个儿。**SPY 是三个里唯一一个均值回归夏普高于趋势跟随的，它也正是方差比最小的那个；BTC 的趋势跟随夏普是均值回归的**七倍**，它的方差比是唯一大于 1 的。

⚠️ 别把这句话读成「算一下方差比就知道该用哪个」。三个标的算不出一条规律来（第 29 篇：样本量），而且方差比本身在不同年份会变。它是一个**解释**，不是一个**筛选器**。但作为解释它很有力：**这两类策略不是风格偏好，它们在赌同一个统计量的两个方向。**

---

## 六、写成规则

```python
print(RV.ReversionPlan().describe().to_string())
print()
print(RV.ReversionPlan(**CONNORS).describe().to_string())
```

```text
进场         偏离 20 日均线 -2.0 个标准差以下，且连跌 3 天以上
出场一（回归）                       偏离度回到 0.0 以上
出场二（时间）                           最多拿 10 根
出场三（止损）                    进场价下方 3.0 个 ATR
仓位                             一笔冒账户的 2.0%
成交                         下一根开盘（信号用到了收盘价）

进场            2 日 RSI 低于 5
出场一（回归）       偏离度回到 0.0 以上
出场二（时间）           最多拿 10 根
出场三（止损）    进场价下方 3.0 个 ATR
仓位             一笔冒账户的 5.0%
成交         下一根开盘（信号用到了收盘价）
```

两套规则，都不是我调出来的：

- **布林带回归**：偏离 20 日均线 2 个标准差以下、且连跌三天，回到均线就走。教科书写法。
- **RSI(2) < 5**：2 日 RSI 跌破 5 买入，收盘站上 5 日均线卖出。Larry Connors 在 1990 年代就公开了，和第 31 篇那套 1983 年的海龟一样，**参数比这份数据早了二三十年**。

⚠️ 注意最后一行：**成交是下一根开盘。**第 31 篇的通道突破可以「当根成交」，因为通道那条线开盘前就画好了；这一篇不行——偏离度和 RSI 都要用**当根收盘价**才能算出来。判据还是同一句：**这个数，在那一刻能不能算出来。**

### 三个标的上跑一遍

```python
PLANS = {"布林带（偏离 ≤ −2 且连跌 ≥ 3）": RV.ReversionPlan(),
         "RSI(2) < 5（Connors）": RV.ReversionPlan(**CONNORS)}
runs_by_market, rows = {}, []
for name, (frame, periods) in MARKETS.items():
    for label, plan in PLANS.items():
        result = RV.reversion(frame, plan)
        if label.startswith("RSI"):
            runs_by_market[name] = result
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"标的": name, "规则": label, "笔数": len(trades),
                     "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "胜率": float((trades["收益"] > 0).mean()),
                     "中位持仓根数": float(trades["根数"].median()),
                     "在场比例": float(trades["根数"].sum()) / len(curve),
                     "记账误差": result["记账误差"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的                   规则  笔数      年化    最大回撤      夏普     胜率  中位持仓根数   在场比例  记账误差
 SPY 布林带（偏离 ≤ −2 且连跌 ≥ 3）  39  0.0092 -0.0693  0.2626 0.6667     7.0 0.0959   0.0
 SPY  RSI(2) < 5（Connors）  66  0.0415 -0.1163  0.7246 0.7576     2.0 0.0493   0.0
AAPL 布林带（偏离 ≤ −2 且连跌 ≥ 3）  31  0.0025 -0.0494  0.1025 0.5484    10.0 0.1015   0.0
AAPL  RSI(2) < 5（Connors）  69  0.0339 -0.1022  0.5266 0.7246     3.0 0.0765   0.0
 BTC 布林带（偏离 ≤ −2 且连跌 ≥ 3）  43 -0.0022 -0.0859 -0.0563 0.5116     9.0 0.0893   0.0
 BTC  RSI(2) < 5（Connors） 110  0.0127 -0.1254  0.1928 0.7000     2.0 0.0843   0.0
```

| 标的 | 规则 | 年化 | 最大回撤 | 夏普 | 胜率 | 中位持仓 | 在场比例 |
|---|---|---|---|---|---|---|---|
| SPY | RSI(2) | **4.15%** | −11.63% | **0.725** | 75.8% | 2 根 | **4.9%** |
| AAPL | RSI(2) | 3.39% | −10.22% | 0.527 | 72.5% | 3 根 | 7.7% |
| BTC | RSI(2) | 1.27% | −12.54% | 0.193 | 70.0% | 2 根 | 8.4% |

先接受一件事：**这些年化数字很小。**原因不是策略不赚钱，而是**它一年只上场十来天**——在场比例只有 5%–8%。同一条策略如果一直满仓，收益会高得多，风险也一样。

这正是均值回归最真实的性质：**它是一条「偶尔出手」的策略**，单独跑的时候大部分资金在睡觉。它的价值要到第十二节（组合）才完全显出来。

---

## 七、决策点那一天，规则实际做了什么

现在回到 2020 年 2 月。

```python
trades = runs_by_market["SPY"]["交易"]
covid = trades[(trades["进场日"] >= "2020-02-01") & (trades["进场日"] <= "2020-04-30")]
print(covid.assign(进场日=lambda t: t["进场日"].dt.date, 出场日=lambda t: t["出场日"].dt.date)
      [["进场日", "进场价", "出场日", "出场价", "原因", "收益", "根数"]].round(4).to_string(index=False))
print(f"\n同一段时间，买入持有的人从 {close.loc['2020-02-25']:.2f} 拿到 {close.loc[bottom]:.2f}，"
      f"是 {close.loc[bottom] / close.loc['2020-02-25'] - 1:+.2%}")
print(f"这条规则全部 {len(trades)} 笔里最差的五笔：")
print(trades.nsmallest(5, "收益").assign(进场日=lambda t: t["进场日"].dt.date,
                                        出场日=lambda t: t["出场日"].dt.date)
      [["进场日", "出场日", "原因", "收益", "根数"]].round(4).to_string(index=False))
```

```text
       进场日    进场价        出场日      出场价   原因      收益  根数
2020-02-25 323.94 2020-02-25 312.5488   止损 -0.0352   0
2020-02-26 314.18 2020-02-27 300.8339   止损 -0.0425   1
2020-02-28 288.70 2020-03-02 309.0900 回到均线  0.0706   1

同一段时间，买入持有的人从 312.65 拿到 222.95，是 -28.69%
这条规则全部 66 笔里最差的五笔：
       进场日        出场日 原因      收益  根数
2018-12-18 2018-12-21 止损 -0.0618   3
2018-03-20 2018-03-23 止损 -0.0428   3
2020-02-26 2020-02-27 止损 -0.0425   1
2022-01-19 2022-01-21 止损 -0.0412   2
2020-02-25 2020-02-25 止损 -0.0352   0
```

**这条规则在那几天做了三笔：**

| 进场 | 出场 | 原因 | 收益 |
|---|---|---|---|
| 2020-02-25 @ 323.94 | 同一天 @ 312.55 | 止损 | **−3.52%** |
| 2020-02-26 @ 314.18 | 次日 @ 300.83 | 止损 | **−4.25%** |
| 2020-02-28 @ 288.70 | 03-02 @ 309.09 | 回到均线 | **+7.06%** |

**三笔合计 −0.70%。**而同一段时间买入持有的人，从 312.65 拿到 222.95，是 **−28.69%**。

止损连打两次，第三次接住了反弹。**那个「买不买」的问题问错了**——决定生死的不是你那天买没买，是**你买了之后怎么走**。

这也解释了为什么这条策略全部 66 笔里最差的一笔只有 **−6.18%**，而它经历过 2018 年底、2020 年 3 月和 2022 年全年。

> 第 23 篇把出场拆成了四个互相独立的问题：初始止损、跟不跟踪、设不设目标、最多拿多久。在凸性策略上，这四个问题决定你能**带走多少**；在凹性策略上，它们决定你能不能**留在牌桌上**。

---

## 八、收益结构：第 31 篇的镜像

```python
print(pd.DataFrame({name: T.r_profile(result["交易"]["收益"])
                    for name, result in runs_by_market.items()}).round(4).to_string())
```

```text
            SPY     AAPL       BTC
笔数      66.0000  69.0000  110.0000
胜率       0.7576   0.7246    0.7000
平均盈利 R   0.0167   0.0242    0.0462
平均亏损 R   0.0219   0.0254    0.0829
盈亏比      0.7607   0.9534    0.5572
期望 R     0.0073   0.0106    0.0075
中位 R     0.0084   0.0091    0.0204
偏度       1.0093  -0.0536   -0.7728
最大一笔 R   0.1215   0.1222    0.1743
最差一笔 R  -0.0618  -0.0806   -0.2510
合计 R     0.4836   0.7288    0.8213
```

![收益结构](/images/trade-analysis/32/structure.png)

把它和第 31 篇的表放在一起：

| | 趋势跟随（BTC） | 均值回归（BTC） |
|---|---|---|
| 胜率 | **32.9%** | **70.0%** |
| 盈亏比 | **10.06** | **0.56** |
| 中位数一笔 | **−1.00R** | **+2.04%**（正的） |
| 偏度 | **+3.37** | **−0.77** |
| 最大一笔 | **+76.44R** | +17.43% |
| 最差一笔 | −2.61R | **−25.10%** |

**每一行都反过来。**三个标的上均值回归的盈亏比分别是 0.76 / 0.95 / 0.56——**全部小于 1**，也就是说赚的时候赚得比亏的时候少，全靠赢的次数多。

⚠️ 一个诚实的细节：SPY 的偏度是 **+1.01**（正的），不是负的。因为「站上 5 日均线就走」这个出场触发得很快，加上 3 个 ATR 的止损，左尾被截掉了。**凹性不是自动的，它是「不管它」的结果**——第十节会把这笔账算出来。

### 8.1 拿掉最亏的几笔

第 31 篇问的是「拿掉最赚的几笔还剩多少」（答案：什么都不剩）。这一篇要问反过来的那一句：

```python
for name, result in runs_by_market.items():
    print(f"--- {name} ---")
    print(RV.worst_trades(result["交易"]["收益"]).round(4).to_string(index=False))
```

```text
--- BTC ---
 拿掉最亏的几笔   剩下多少  变成原来的   占总笔数
       0 0.8213 1.0000 0.0000
       1 1.0724 1.3056 0.0091
       3 1.3943 1.6976 0.0273
       5 1.6992 2.0688 0.0455
      10 2.3948 2.9157 0.0909
```

| 拿掉最亏的几笔 | SPY 变成原来的 | AAPL | BTC |
|---|---|---|---|
| 1 笔 | 1.13 倍 | 1.11 倍 | **1.31 倍** |
| 3 笔 | 1.30 倍 | 1.30 倍 | **1.70 倍** |
| 5 笔 | 1.46 倍 | 1.44 倍 | **2.07 倍** |
| 10 笔（约 9%–15%） | 1.67 倍 | 1.60 倍 | **2.92 倍** |

**在 BTC 上，只要躲开最亏的三笔，九年收益就变成 1.70 倍。**这就是凹性的账：趋势跟随的命门是「错过赢家」，均值回归的命门是「碰上一次没回头的」。

图右边把两条曲线画在了一起——一条从 100% 往下砸穿零轴，一条从 100% 往上爬。**同一个问题的两个方向。**

---

## 九、凹性

```python
for name, (frame, periods) in MARKETS.items():
    strategy = runs_by_market[name]["资金曲线"].pct_change().dropna()
    market = frame["close"].pct_change().reindex(strategy.index)
    print(f"--- {name} ---")
    print(T.convexity(strategy, market, buckets=5, window=20).round(4).to_string())
```

```text
--- SPY ---
 拿掉最亏的几笔   剩下多少  变成原来的   占总笔数
       0 0.4836 1.0000 0.0000
       1 0.5454 1.1279 0.0152
       3 0.6307 1.3042 0.0455
       5 0.7071 1.4622 0.0758
      10 0.8087 1.6723 0.1515
--- AAPL ---
 拿掉最亏的几笔   剩下多少  变成原来的   占总笔数
       0 0.7288 1.0000 0.0000
       1 0.8094 1.1106 0.0145
       3 0.9441 1.2953 0.0435
       5 1.0468 1.4364 0.0725
      10 1.1689 1.6038 0.1449
--- BTC ---
 拿掉最亏的几笔   剩下多少  变成原来的   占总笔数
       0 0.8213 1.0000 0.0000
       1 1.0724 1.3056 0.0091
       3 1.3943 1.6976 0.0273
       5 1.6992 2.0688 0.0455
      10 2.3948 2.9157 0.0909
===== 片段 11：凹性 =====
--- SPY ---
               根数    市场中位    策略中位    策略平均  策略赚钱的比例
按市场 20 根涨跌分组                                      
第 1 组         496 -0.0428  0.0000 -0.0004   0.3468
第 2 组         495 -0.0011  0.0011  0.0063   0.5152
第 3 组         495  0.0176  0.0000  0.0050   0.4242
第 4 组         495  0.0316  0.0000  0.0034   0.2828
第 5 组         496  0.0553  0.0000  0.0024   0.1230
```

![凹性](/images/trade-analysis/32/concavity.png)

⚠️ 这里直接用了第 31 篇的 `trend.convexity`——**同一个函数，画出来的形状正好反过来**，所以不必再写一个。

SPY 上那条蓝线是一条标准的**倒 U**：

| SPY 这 20 根 | −4.28% | −0.11% | +1.76% | +3.16% | +5.53% |
|---|---|---|---|---|---|
| 均值回归平均赚 | **−0.04%** | **+0.63%** | +0.50% | +0.34% | +0.24% |
| 趋势跟随平均赚 | −0.86% | −0.80% | +0.12% | +1.33% | **+2.13%** |

**市场不涨不跌的时候，均值回归赚得最多；市场单边大涨的时候，趋势跟随赚得最多；而市场大跌的时候，两个都不好过**（只是均值回归只亏 0.04%，趋势跟随亏 0.85%——因为后者在大跌之前往往还拿着仓）。

三张图里两条线的**交点**，就是这两类策略的分界：**市场走得越远，越该跟着走；走得越乱，越该反着做。**

---

## 十、止损和时间出场各自在做什么

第 23 篇讲过四类出场。在凹性策略上，它们的作用和在凸性策略上**完全不同**：

```python
rows = []
for label, extra in [("原样（3 ATR 止损 + 10 根时间出场）", {}),
                     ("去掉止损", dict(stop_atr=None, fraction=1.0)),
                     ("去掉时间出场（最多拿 250 根）", dict(max_bars=250)),
                     ("两个都去掉", dict(stop_atr=None, fraction=1.0, max_bars=250))]:
    for name, (frame, periods) in MARKETS.items():
        result = RV.reversion(frame, RV.ReversionPlan(**{**CONNORS, **extra}))
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"设定": label, "标的": name, "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "胜率": float((trades["收益"] > 0).mean()),
                     "最差一笔": float(trades["收益"].min()),
                     "偏度": float(trades["收益"].skew())})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
                     设定   标的     年化    最大回撤     夏普     胜率    最差一笔      偏度
原样（3 ATR 止损 + 10 根时间出场）  SPY 0.0415 -0.1163 0.7246 0.7576 -0.0618  1.0093
原样（3 ATR 止损 + 10 根时间出场） AAPL 0.0339 -0.1022 0.5266 0.7246 -0.0806 -0.0536
原样（3 ATR 止损 + 10 根时间出场）  BTC 0.0127 -0.1254 0.1928 0.7000 -0.2510 -0.7728
                   去掉止损  SPY 0.0385 -0.1502 0.5790 0.7414 -0.0458  1.7861
                   去掉止损 AAPL 0.0809 -0.1632 0.7658 0.7188 -0.1109 -0.0247
                   去掉止损  BTC 0.0102 -0.5986 0.2023 0.7113 -0.3271 -1.6485
      去掉时间出场（最多拿 250 根）  SPY 0.0415 -0.1163 0.7246 0.7576 -0.0618  1.0093
      去掉时间出场（最多拿 250 根） AAPL 0.0339 -0.1022 0.5266 0.7246 -0.0806 -0.0536
      去掉时间出场（最多拿 250 根）  BTC 0.0127 -0.1254 0.1928 0.7000 -0.2510 -0.7728
                  两个都去掉  SPY 0.0385 -0.1502 0.5790 0.7414 -0.0458  1.7861
                  两个都去掉 AAPL 0.0866 -0.1188 0.8085 0.7188 -0.0638  1.0594
                  两个都去掉  BTC 0.0150 -0.5811 0.2178 0.7113 -0.3271 -1.5779
```

| 设定 | SPY 夏普 | AAPL 夏普 | BTC 夏普 | BTC 最大回撤 | BTC 偏度 |
|---|---|---|---|---|---|
| 原样（3 ATR 止损 + 10 根时间出场） | **0.725** | 0.527 | 0.193 | **−12.54%** | −0.77 |
| 去掉止损 | 0.579 | **0.766** | 0.202 | **−59.86%** | **−1.65** |
| 去掉时间出场 | 0.725 | 0.527 | 0.193 | −12.54% | −0.77 |

三件事：

**一，止损在 BTC 上把最大回撤从 −59.86% 压到 −12.54%，偏度从 −1.65 提到 −0.77。**对凹性策略，止损是在**削掉那条长长的左尾**——而它削掉的都是「没回头」的交易，正是这类策略唯一真正的风险。

**二，但在 AAPL 上，加止损让夏普从 0.766 掉到 0.527。**因为 AAPL 的回撤经常又深又快又真的会弹回来，止损正好把这些赢家提前赶下车。**这和趋势跟随正好相反**：那里止损砍掉的是输家，这里砍掉的可能是赢家。

**三，时间出场（10 根 vs 250 根）在这套规则上一点影响都没有**——三个标的的每一个数都一模一样。因为「收盘站上 5 日均线」这个出场本来就触发得比十根快。**它是个摆设。**我本来以为时间出场会是凹性策略的安全带，数据说不是。

---

## 十一、用第六部分的方法检验

### 11.1 参数曲面与 walk-forward

```python
GRID = [(threshold, window) for threshold in [2, 5, 10, 15, 20, 25] for window in [3, 5, 10, 20]]
DEFAULT = (5, 5)
print(f"网格 {len(GRID)} 组（RSI 阈值 × 出场均线长度），默认那一组是 {DEFAULT}")
rows = []
for name, (frame, periods) in MARKETS.items():
    daily = np.array([RV.reversion(frame, RV.ReversionPlan(**{**CONNORS, "entry_rsi": t, "n": w}))
                      ["资金曲线"].pct_change().reindex(frame.index).fillna(0).to_numpy()
                      for t, w in GRID])
    scores = daily.mean(axis=1) / daily.std(axis=1, ddof=1) * np.sqrt(periods)
    face = V.surface(pd.DataFrame({"阈值": [t for t, w in GRID], "出场均线": [w for t, w in GRID],
                                   "夏普": scores}), "阈值", "出场均线", "夏普")
    around = V.neighbourhood(face, DEFAULT)
    splits = V.walk_forward(daily.shape[1], int(periods * 2), periods)
    picked = V.walk_forward_run(daily, splits, names=GRID)
    stitched = V.stitch(daily, splits, [GRID.index(p) for p in picked["选了谁"]])
    rolling = RP.to_curve(pd.Series(stitched, index=pd.RangeIndex(len(stitched))))
    held = daily[GRID.index(DEFAULT), splits[0][1].start:splits[-1][1].stop]
    kept = RP.to_curve(pd.Series(held, index=pd.RangeIndex(len(held))))
    rows.append({"标的": name, "默认 (5,5) 的夏普": scores[GRID.index(DEFAULT)],
                 "排第几": f"{int((scores > scores[GRID.index(DEFAULT)]).sum()) + 1}/{len(GRID)}",
                 "落差": around["落差"], "网格中位": float(np.median(scores)),
                 "亏钱的格子": float((daily.sum(axis=1) < 0).mean()),
                 "白捡的门槛": V.expected_max_sharpe(len(GRID), scores.std()),
                 "PBO": V.pbo(daily, 8)["过拟合概率 PBO"],
                 "每年重挑的年化": RP.annual_return(rolling, periods),
                 "一直用 (5,5) 的年化": RP.annual_return(kept, periods)})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
网格 24 组（RSI 阈值 × 出场均线长度），默认那一组是 (5, 5)
  标的  默认 (5,5) 的夏普  排第几     落差   网格中位  亏钱的格子  白捡的门槛    PBO  每年重挑的年化  一直用 (5,5) 的年化
 SPY        0.7223 3/24 0.5287 0.3911 0.0833 0.5141 0.1286   0.0131         0.0483
AAPL        0.5249 5/24 0.2413 0.3173 0.2083 0.4968 0.4143   0.1154         0.0436
 BTC        0.1923 7/24 0.0637 0.1286 0.2083 0.2501 0.8714   0.0419         0.0158
```

| 标的 | (5,5) 的夏普 | 排第几 | **落差** | 亏钱的格子 | 白捡的门槛 | PBO | 每年重挑 | 一直用 (5,5) |
|---|---|---|---|---|---|---|---|---|
| SPY | 0.722 | 3/24 | **+0.529** | 8.3% | 0.514 | **0.129** | 1.31% | **4.83%** |
| AAPL | 0.525 | 5/24 | +0.241 | 20.8% | 0.497 | 0.414 | **11.54%** | 4.36% |
| BTC | 0.192 | 7/24 | +0.064 | 20.8% | 0.250 | **0.871** | **4.19%** | 1.58% |

和第 31 篇的海龟比，这张表**难看得多**：

- **落差 +0.529**（海龟是 +0.15～+0.20）。均值回归的参数曲面**更像一根针**，尤其在 SPY 上。
- **24 组里有 8%–21% 是亏钱的**（海龟是 0%）。这不是一个「整个参数族都 work」的策略。
- **BTC 的 PBO 是 0.871**——在 BTC 上挑参数比抛硬币还差。
- 每年重挑 vs 固定，三个标的**结论不一致**（SPY 固定好得多、AAPL 和 BTC 重挑更好）。海龟那里是三个标的一致。

### 11.2 蒙特卡洛，以及一条新的方法论

```python


def fake_markets(frame: pd.DataFrame, block: int, n: int = N_PATHS, seed: int = 32):
    """造假数据：四个价按同一个比例缩放，保住 K 线的形状。"""
    for path in V.synthetic_close(frame["close"], n=n, block=block, seed=seed):
        scale = path / frame["close"].to_numpy()
        yield pd.DataFrame({c: frame[c].to_numpy() * scale for c in ["open", "high", "low", "close"]},
                           index=frame.index)


rows = []
for name, (frame, periods) in MARKETS.items():
    real = runs_by_market[name]
    actual = RP.annual_return(real["资金曲线"], periods)
    row = {"标的": name, "真实年化": actual, "中位持仓根数": float(real["交易"]["根数"].median())}
    for block in (1, 2, 5, 20, 60):
        fakes = np.array([RP.annual_return(RV.reversion(fake, RV.ReversionPlan(**CONNORS))["资金曲线"],
                                           periods) for fake in fake_markets(frame, block)])
        row[f"块长 {block} 的 p"] = float((fakes >= actual).mean())
        if block == 1:
            row["块长 1 的假数据中位"] = float(np.median(fakes))
    rows.append(row)
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的   真实年化  中位持仓根数  块长 1 的 p  块长 1 的假数据中位  块长 2 的 p  块长 5 的 p  块长 20 的 p  块长 60 的 p
 SPY 0.0415     2.0      0.01       0.0017      0.01      0.04       0.04       0.05
AAPL 0.0339     3.0      0.13       0.0117      0.16      0.23       0.47       0.59
 BTC 0.0127     2.0      0.40       0.0060      0.43      0.23       0.15       0.11
```

```text
同样两种块长，对第 31 篇那套持仓十几根的海龟：
  标的   真实年化  中位持仓根数  块长 1 的 p  块长 20 的 p
 SPY 0.0468    16.0    0.0167        0.0
AAPL 0.1690    15.0    0.0000        0.0
 BTC 0.3160    12.5    0.0000        0.0
```

![块长](/images/trade-analysis/32/blocks.png)

先看结论：**均值回归只在 SPY 上勉强过关（p = 0.01），AAPL（0.13）和 BTC（0.40）都不过关。**对比海龟：三个标的、两种块长，p 全是 0.00–0.02。

**差距是数量级的。**

但这张表更重要的是它顺带证明的一件事——**对照用的块长，必须比策略的持仓期短：**

| 对照的块长 | 1 | 2 | 5 | 20 | 60 |
|---|---|---|---|---|---|
| SPY 的 p（持仓 2 根） | **0.01** | 0.01 | 0.04 | 0.04 | 0.05 |
| AAPL 的 p（持仓 3 根） | **0.13** | 0.16 | 0.23 | 0.47 | **0.59** |
| 海龟（持仓 12–16 根） | 0.00–0.02 | | | **0.00** | |

第 30 篇说过「做蒙特卡洛对照要用块自助法，打散会低估白捡的部分」。**那句话是对趋势策略说的。**对一条持仓两三根的策略，块长 20 的对照里**原样保留着日间反转**——你把要测的东西留在了对照组里，当然测不出差别（AAPL 上 p 从 0.13 涨到 0.59）。

> **更一般的说法**：对照里保留下来的结构，如果正是策略要利用的那一种，p 值就会被推高。
> ⚠️ 反过来也成立，BTC 那一行就是证据：它的 p 从 0.40 **降到** 0.11，因为长块保留的是 BTC 的**趋势**，而趋势对均值回归是**伤害**，对照反而被削弱了。
> **所以块长不是越长越好也不是越短越好，是要看你想让对照保留什么。**

---

## 十二、把两条腿放进同一个账户

这才是均值回归真正的位置。

```python
rows = []
for name, (frame, periods) in MARKETS.items():
    trend_curve = T.turtle(frame, T.TurtlePlan())["资金曲线"]
    mean_curve = runs_by_market[name]["资金曲线"]
    a, b = trend_curve.pct_change().dropna(), mean_curve.pct_change().dropna()
    shared = a.index.intersection(b.index)
    together = float(((a.reindex(shared) != 0) & (b.reindex(shared) != 0)).mean())
    mixed = RV.blend({"趋势跟随": trend_curve, "均值回归": mean_curve}, [0.5, 0.5])
    for label, curve in [("趋势跟随（第 31 篇）", trend_curve), ("均值回归（这一篇）", mean_curve),
                         ("五五开，每月再平衡", mixed)]:
        daily = curve.pct_change().dropna()
        rows.append({"标的": name, "账户": label, "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve), "夏普": RP.sharpe(daily, periods),
                     "卡玛": RP.calmar(curve, periods),
                     "两条腿的相关": a.reindex(shared).corr(b.reindex(shared)) if label.startswith("五五") else np.nan,
                     "同时在场": together if label.startswith("五五") else np.nan})
print(pd.DataFrame(rows).round(4).to_string(index=False))
```

```text
  标的           账户     年化    最大回撤     夏普     卡玛  两条腿的相关   同时在场
 SPY 趋势跟随（第 31 篇） 0.0468 -0.1711 0.6822 0.2737     NaN    NaN
 SPY    均值回归（这一篇） 0.0415 -0.1163 0.7246 0.3564     NaN    NaN
 SPY    五五开，每月再平衡 0.0451 -0.0630 0.9806 0.7163  0.0025 0.0044
AAPL 趋势跟随（第 31 篇） 0.1690 -0.1187 1.2604 1.4234     NaN    NaN
AAPL    均值回归（这一篇） 0.0339 -0.1022 0.5266 0.3317     NaN    NaN
AAPL    五五开，每月再平衡 0.1026 -0.0972 1.3430 1.0559  0.0160 0.0052
 BTC 趋势跟随（第 31 篇） 0.3160 -0.2156 1.3669 1.4657     NaN    NaN
 BTC    均值回归（这一篇） 0.0127 -0.1254 0.1928 0.1015     NaN    NaN
 BTC    五五开，每月再平衡 0.1659 -0.1330 1.3237 1.2477  0.0019 0.0021
```

![组合](/images/trade-analysis/32/blend.png)

**SPY 上的结果非常干净：**

| SPY | 年化 | 最大回撤 | 夏普 | 卡玛 |
|---|---|---|---|---|
| 趋势跟随（第 31 篇） | 4.68% | −17.11% | 0.682 | 0.274 |
| 均值回归（这一篇） | 4.15% | −11.63% | 0.725 | 0.356 |
| **五五开，每月再平衡** | 4.51% | **−6.30%** | **0.981** | **0.716** |

**年化只是两者的平均（4.51%），但最大回撤只有两条腿的一半多一点（−6.30%），夏普从 0.68 和 0.73 升到 0.98，卡玛从 0.27 和 0.36 升到 0.72。**

为什么能这样？两个数字：

- **两条腿的日收益相关系数是 +0.0025**（AAPL +0.0160、BTC +0.0019）
- **同时在场的日子只占 0.44%**

它们几乎从不同时持仓——一个在「价格创新高」的日子进场，一个在「跌得离谱」的日子进场，**这两件事按定义就不会同时发生**。第 26 篇量过的「有效独立仓位数」，在这里终于出现了一个接近 2 的例子。

⚠️ 但也别把它当成万能：

| | 趋势夏普 | 回归夏普 | 五五开夏普 | 五五开卡玛 |
|---|---|---|---|---|
| SPY | 0.682 | 0.725 | **0.981** | **0.716** |
| AAPL | **1.260** | 0.527 | 1.343 | 1.056（比 1.423 差） |
| BTC | **1.367** | 0.193 | 1.324（更差） | 1.248（比 1.466 差） |

**组合的好处需要两条腿各自都有本事。**BTC 上均值回归的夏普只有 0.193，把它掺进来就是纯稀释。SPY 上两条腿势均力敌（0.682 和 0.725），组合的收益才最大。

> 这条道理第 26 篇已经算过：分散的价值来自**低相关**，但前提是每条腿的期望都为正。**相关系数 0.0025 只保证「能分散」，不保证「值得分散」。**

---

## 十三、动手：`talab.reversion`

```python
"""talab.reversion：均值回归。第 32 篇。

第 31 篇的趋势跟随赌的是「走出去的会接着走」。这一篇赌的正好相反：
**跌得太多的会弹回来。**

两条策略的每一样东西都是镜像：

| | 趋势跟随（第 31 篇） | 均值回归（这一篇） |
|---|---|---|
| 进场 | 价格**创新高** | 价格**跌得离谱** |
| 胜率 | 低（32%–46%） | **高** |
| 单笔盈亏 | 亏小赚大 | **赚小亏大** |
| 形状 | 凸（像买了期权） | **凹（像卖了期权）** |
| 怕什么 | 来回震荡 | **一路不回头** |
| 适合什么市场 | 方差比 > 1 | **方差比 < 1** |

最后那一行是这一篇的骨架：**同一个数（第 5 篇的方差比）同时决定了两篇的结论。**
SPY 的 60 天方差比是 0.616，BTC 是 1.270——所以均值回归在 SPY 上成立、在 BTC 上是反向指标，
而第 31 篇的趋势跟随正好反过来。

⚠️ 这一篇的信号**全部用到当根收盘价**（偏离度、连跌天数、RSI），
所以它**只能下一根开盘成交**——第 31 篇那个「碰到通道就成交」的例外，在这里不成立。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from talab.backtest import Account

SIDES = ("long", "short")
```

### 拉伸、连击与信号评估

```python
def stretch(close: pd.Series, n: int = 20) -> pd.Series:
    """偏离度：收盘价离 n 日均线有几个（n 日）标准差。

    这就是布林带的 %b 换一种写法——`z = −2` 就是「踩在布林下轨上」。
    用标准差而不是百分比，是为了让同一个阈值能跨市场用：
    SPY 的 2 个标准差大约是 3%，BTC 大约是 9%。
    """
    average = close.rolling(n).mean()
    deviation = close.rolling(n).std()
    return ((close - average) / deviation).rename("偏离度")


def streak(close: pd.Series) -> pd.Series:
    """连击：连涨几天记正数，连跌几天记负数，持平记 0。

    它和偏离度量的是**不同的东西**：偏离度看「离得多远」，连击看「连着走了多久」。
    第 32 篇的实测是两个一起用比单用任何一个都好。
    """
    change = close.diff()
    up, down = change > 0, change < 0
    rising = up.groupby((~up).cumsum()).cumsum()
    falling = down.groupby((~down).cumsum()).cumsum()
    return (rising - falling).rename("连击")


def setups(close: pd.Series, condition: pd.Series, horizons=(1, 5, 10, 20)) -> pd.DataFrame:
    """条件成立的每一天，以及之后若干根的涨跌。

    ⚠️ 这不是回测——它没有止损、没有仓位、允许重叠。它回答的是更前面的一个问题：
    **这个条件本身携带信息吗？**答案要和「什么都不做」的基准比（见 `edge`）。
    """
    values = close.to_numpy(float)
    where = np.where(condition.reindex(close.index).fillna(False).to_numpy())[0]
    rows = []
    for i in where:
        row = {"时间": close.index[i], "收盘": values[i]}
        for k in horizons:
            row[f"{k} 根后"] = values[i + k] / values[i] - 1 if i + k < len(values) else np.nan
        tail = values[i + 1:i + 1 + max(horizons)]
        row["期间最低"] = float(tail.min()) / values[i] - 1 if len(tail) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def edge(table: pd.DataFrame, close: pd.Series, horizon: int = 5) -> pd.Series:
    """把 `setups` 的结果和「随便哪一天买入」的基准放在一起比。

    只看「胜率 70%」没有意义——如果随便哪一天买入的胜率也有 68%，那这个条件什么都没说。
    **信号的价值是它比基准好多少，不是它本身多好。**
    """
    column = f"{horizon} 根后"
    hits = table[column].dropna()
    baseline = close.pct_change(horizon).dropna()
    return pd.Series({
        "次数": float(len(hits)), "胜率": float((hits > 0).mean()), "平均": float(hits.mean()),
        "中位": float(hits.median()), "最差": float(hits.min()),
        "基准胜率": float((baseline > 0).mean()), "基准平均": float(baseline.mean()),
        "比基准多赚": float(hits.mean() - baseline.mean()),
    })
```

`edge` 那个函数里藏着这一篇的态度：**信号的价值是它比基准好多少，不是它本身多好。**一个「胜率 85%」的条件，如果基准也有 85%，它就什么都没说。

### 引擎

```python
def reversion(df: pd.DataFrame, plan: ReversionPlan | None = None,
              equity: float = 100_000.0) -> dict:
    """按均值回归的规则跑一遍历史。四步顺序和第 27、31 篇完全一样。

    1. **成交**：上一根收盘定下来的单子，用这一根的开盘价成交
    2. **出场**：止损（盘中触发）→ 回归目标 → 时间到，三者按这个顺序判
    3. **估值**：按收盘价记权益
    4. **下单**：用这一根的收盘价算信号，挂下一根的单

    ⚠️ 第 4 步和第 1 步之间隔着一整根 K 线，这是这一篇和第 31 篇最大的实现差别：
    偏离度要用当根收盘价才能算出来，所以**没有当根成交这一说**。
    """
    from talab import indicators as I

    plan = plan or ReversionPlan()
    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    z = stretch(df["close"], plan.n).to_numpy()
    runs = streak(df["close"]).to_numpy()
    atr = I.atr(df["high"], df["low"], df["close"], plan.atr_period).to_numpy()
    force = (I.rsi(df["close"], plan.rsi_period).to_numpy() if plan.entry_rsi is not None
             else np.full(len(c), np.nan))
    direction = 1 if plan.side == "long" else -1

    account = Account(cash=float(equity))
    curve, trades, error = [], [], 0.0
    pending = False
    entry_price = stop = risk_amount = np.nan
    opened_at = -1
    shares = 0.0

    def value(price: float) -> float:
        return account.cash + direction * shares * price

    def close_out(i: int, price: float, reason: str) -> None:
        nonlocal shares, opened_at, stop
        if direction > 0:
            account.sell(price, shares, plan.fee_rate)
            profit = (price - entry_price) * shares - price * shares * plan.fee_rate
        else:
            account.cash -= price * shares * (1 + plan.fee_rate)
            account.fees += price * shares * plan.fee_rate
            profit = (entry_price - price) * shares - price * shares * plan.fee_rate
        trades.append({"进场日": df.index[opened_at], "进场价": entry_price, "数量": shares,
                       "出场日": df.index[i], "出场价": price, "原因": reason, "盈亏": profit,
                       "R": profit / risk_amount if risk_amount else np.nan,
                       "收益": direction * (price / entry_price - 1), "根数": i - opened_at})
        shares, opened_at, stop = 0.0, -1, np.nan

    ready_at = ~np.isnan(z) & ~np.isnan(atr) & (~np.isnan(force) if plan.entry_rsi is not None else True)
    first = int(np.argmax(ready_at)) + 1
    for i in range(first, len(c)):
        # 第 1 步：成交上一根挂出的单
        if pending and shares == 0:
            price = o[i]
            step = plan.stop_atr * atr[i - 1] if plan.stop_atr else np.nan
            want = (value(price) * plan.risk / step if plan.stop_atr
                    else value(price) * plan.fraction / price)
            size = min(want, value(price) / (price * (1 + plan.fee_rate)))
            if size > 0:
                if direction > 0:
                    account.buy(price, size, plan.fee_rate)
                else:
                    account.cash += price * size * (1 - plan.fee_rate)
                    account.fees += price * size * plan.fee_rate
                shares, entry_price, opened_at = size, price, i
                stop = price - direction * step if plan.stop_atr else -direction * np.inf
                risk_amount = size * step if plan.stop_atr else size * price
            pending = False

        # 第 2 步：出场
        if shares > 0:
            if plan.stop_atr and ((direction > 0 and l[i] <= stop) or (direction < 0 and h[i] >= stop)):
                close_out(i, (min(o[i], stop) if direction > 0 else max(o[i], stop)), "止损")
            elif (direction > 0 and z[i] >= plan.exit_z) or (direction < 0 and z[i] <= -plan.exit_z):
                close_out(i, c[i], "回到均线")
            elif i - opened_at >= plan.max_bars:
                close_out(i, c[i], "时间到")

        # 第 3 步：估值
        current = value(c[i])
        error = max(error, abs(account.cash + direction * shares * c[i] - current))
        curve.append(current)

        # 第 4 步：用这一根的收盘价算信号，挂下一根的单
        if shares == 0 and not pending and atr[i] > 0:
            if plan.entry_rsi is not None:
                ready = (force[i] < plan.entry_rsi if direction > 0
                         else force[i] > 100 - plan.entry_rsi)
            else:
                stretched = z[i] <= plan.entry_z if direction > 0 else z[i] >= -plan.entry_z
                long_enough = (runs[i] <= -plan.entry_streak if direction > 0
                               else runs[i] >= plan.entry_streak)
                ready = stretched and (not plan.entry_streak or long_enough)
            if ready:
                pending = True

    if shares > 0:
        close_out(len(c) - 1, c[-1], "未平仓")
    columns = ["进场日", "进场价", "数量", "出场日", "出场价", "原因", "盈亏", "R", "收益", "根数"]
    return {"资金曲线": pd.Series(curve, index=df.index[first:], name="权益"),
            "交易": pd.DataFrame(trades, columns=columns),
            "手续费合计": account.fees, "记账误差": error}
```

四步顺序和第 27、31 篇一模一样，唯一的差别在第 4 步和第 1 步之间**隔着一整根 K 线**——信号用到当根收盘价，所以只能下一根开盘成交。

### 镜像的两个工具

```python
def worst_trades(returns, tops=(1, 3, 5, 10)) -> pd.DataFrame:
    """把**最亏**的几笔拿掉，还剩多少——第 31 篇 `trend.contribution` 的镜像。

    趋势跟随问的是「拿掉最赚的几笔还剩多少」（答案：什么都不剩）；
    均值回归要问的是反过来的那一句：**如果那几次最深的坑没踩到，成绩会好多少？**
    比值越大，说明这条策略越依赖「那几次没出事」。
    """
    values = pd.Series(returns).dropna().astype(float).sort_values()
    total = values.sum()
    rows = [{"拿掉最亏的几笔": 0, "剩下多少": total, "变成原来的": 1.0, "占总笔数": 0.0}]
    for n in tops:
        if n >= len(values):
            break
        left = total - values.iloc[:n].sum()
        rows.append({"拿掉最亏的几笔": n, "剩下多少": left,
                     "变成原来的": left / total if total else np.nan, "占总笔数": n / len(values)})
    return pd.DataFrame(rows)


def blend(curves: dict[str, pd.Series], weights=None, rebalance: str = "ME") -> pd.Series:
    """把几条资金曲线合成一个账户：按权重分钱，按 `rebalance` 的周期调回目标比例。

    ⚠️ 必须**再平衡**才算一个账户。不再平衡只是把两条曲线加起来，
    赚得多的那条会越占越大，最后你量到的是它一个人的性质（第 26 篇量过资金分配的影响）。
    `rebalance=None` 就是不调，留着做对照。
    """
    frame = pd.concat(curves, axis=1).ffill().dropna()
    if weights is None:
        weights = np.full(frame.shape[1], 1 / frame.shape[1])
    weights = np.asarray(weights, dtype=float)
    if len(weights) != frame.shape[1] or not np.isclose(weights.sum(), 1.0):
        raise ValueError("权重个数要和曲线条数一致，而且加起来等于 1")
    steps = frame.pct_change().fillna(0.0).to_numpy()
    marks = (pd.Series(1, index=frame.index).resample(rebalance).last().index
             if rebalance else pd.DatetimeIndex([]))
    holding, total, out = weights.copy(), 1.0, []
    for k, when in enumerate(frame.index):
        holding = holding * (1 + steps[k])
        total_now = holding.sum()
        out.append(total * total_now)
        holding = holding / total_now
        total = total * total_now
        if rebalance and when in marks:
            holding = weights.copy()
    return pd.Series(out, index=frame.index, name="组合") * float(frame.iloc[0].mean())
```

⚠️ `blend` 里那条注释是重点：**必须再平衡才算一个账户。**不再平衡只是把两条曲线加起来，赚得多的那条会越占越大，最后你量到的是它一个人的性质。测试里专门钉了这一条。

### 测试

十三个测试里最该看的一条，是那个「下一根开盘成交」的规矩：

```python
def test_books_balance_and_fills_happen_on_the_next_open():
    """信号用到当根收盘价，所以**只能下一根开盘成交**——第 31 篇那个例外在这里不成立。"""
    dip = [100.0] * 25 + [97, 94, 91] + [95.0] * 10
    bars = frame(dip, opens=[100.0] * 25 + [99, 96, 93] + [92.0] + [95.0] * 9)
    plan = RV.ReversionPlan(n=20, entry_z=-1.0, entry_streak=3, exit_z=0.0,
                            max_bars=10, stop_atr=None, fraction=1.0)
    result = RV.reversion(bars, plan)
    assert result["记账误差"] == 0.0
    trade = result["交易"].iloc[0]
    assert trade["进场日"] == bars.index[28]                      # 第 27 根收盘才满足条件
    assert trade["进场价"] == pytest.approx(92.0)                 # 成交在第 28 根的**开盘**
```

还有一条把三种出场全部逼出来一遍：

```python
def test_the_three_exits_each_fire():
    reasons = set()
    for closes, kwargs in [
            ([100.0] * 25 + [96, 92, 88] + [200.0] * 5, dict(stop_atr=None)),        # 暴涨 → 回到均线
            ([100.0] * 25 + [96, 92, 88] + [88.5] * 15, dict(stop_atr=None)),        # 不动 → 时间到
            ([100.0] * 25 + [96, 92, 88, 87] + [60.0] * 6, dict(stop_atr=1.0, risk=0.02))]:  # 续跌 → 止损
        plan = RV.ReversionPlan(n=20, entry_z=-1.0, entry_streak=3, max_bars=5, **kwargs)
        trades = RV.reversion(frame(closes), plan)["交易"]
        assert len(trades) >= 1
        reasons.add(trades.iloc[0]["原因"])
    assert reasons == {"回到均线", "时间到", "止损"}
```

---

## 十四、小检查

1. 一个条件之后五天的胜率是 85%。你还需要知道什么，才能判断它值不值钱？
2. 均值回归的盈亏比小于 1（这一篇实测 0.56–0.95），趋势跟随的盈亏比是 10.06。哪一个更好？
3. 同一套止损，在趋势跟随上砍掉的是什么，在均值回归上砍掉的是什么？
4. 第 30 篇说「蒙特卡洛对照要用块自助法」。为什么这一篇说块长 20 对均值回归是错的？
5. 两条策略的相关系数是 0.0025。这是不是意味着把它们组合起来一定更好？

---

## 十五、常见误用

**只看胜率。**第四节：这个条件五天后胜率 85.71%，但基准也有 61.19%；十根、二十根之后胜率还是 64%，而「比基准多赚」已经是负的了。**胜率要和基准一起看，而且要连着窗口一起说。**

**把信号当策略。**第七节：决策点那一天信号确实给对了方向（二十天后 −20.77%），但完整的规则只亏了 0.70%。**信号只说「往哪儿看」，规则才决定你亏多少。**

**在凹性策略上不设止损。**第十节：BTC 上去掉止损，最大回撤从 −12.54% 变成 −59.86%，偏度从 −0.77 跌到 −1.65。**趋势跟随的止损砍的是输家，均值回归的止损砍的是那条要命的左尾**——但也会误伤（AAPL 上夏普从 0.766 掉到 0.527）。

**拿着不放，等它「一定会回来」。**第四节那张表：同样一个条件，五根之后最差 −1.27%，二十根之后最差 −20.77%。**凹性策略的优势有保质期。**

**在方差比大于 1 的市场上做均值回归。**第五节：BTC 的四个条件「比基准多赚」全是负的，而它的 60 天方差比是 1.270。

**用块长大于持仓期的对照做蒙特卡洛。**第 11.2 节：AAPL 上块长 1 给 p = 0.13，块长 60 给 p = 0.59——对照里留着你要测的东西。⚠️ 这条是对第 30 篇那句话的补充，不是推翻：**块长要看你想让对照保留什么。**

**以为低相关就一定值得组合。**第十二节：BTC 上两条腿相关只有 0.0019，但均值回归的夏普只有 0.193，掺进来让组合夏普从 1.367 掉到 1.324。**低相关保证能分散，不保证值得分散。**

**不再平衡就叫「组合」。**`blend` 的默认是每月调回目标比例。不调的话，几年之后你量到的是跑得快那条腿一个人的性质。

---

## 十六、小结

- **均值回归是趋势跟随的镜像**：进场看「跌得离谱」而不是「创新高」，胜率 70.0%–75.8% 而不是 32.9%–45.8%，盈亏比 **0.56–0.95**（全部小于 1）而不是 2.61–10.06，形状是**凹**而不是凸，怕的是**一路不回头**而不是来回震荡。
- **信号的价值有保质期**：SPY 上「连跌五天 + 偏离 −2 个标准差」，五根后胜率 **85.71%**、比基准多赚 **+1.11 个百分点**；到十根、二十根，「比基准多赚」变成 −0.91% 和 −0.63%，而最差的那一次从 −1.27% 变成 **−20.77%**。
- **同一个数解释了两篇**：60 天方差比 SPY **0.616** / AAPL 0.852 / BTC **1.270**；趋势跟随夏普 0.682 / 1.260 / **1.367**，均值回归夏普 **0.725** / 0.527 / 0.193。⚠️ 它是解释，不是筛选器。
- **决策点的答案**：2020-02-26 之后二十根 −20.77%、期间最低 −28.43%，但**完整的规则那几天只亏了 0.70%**（止损连打两次，第三次 +7.06% 接住反弹），同期买入持有是 −28.69%。**生死不在进场，在出场。**
- **拿掉最亏的几笔**：BTC 上拿掉 3 笔收益变成 **1.70 倍**、10 笔变成 **2.92 倍**——和第 31 篇「拿掉最赚的 10 笔归零」正好是镜像。
- **止损的作用相反**：BTC 上止损把回撤从 **−59.86% 压到 −12.54%**，但 AAPL 上让夏普从 0.766 掉到 0.527。时间出场在这套规则里是摆设（三个标的一个数都没变）。
- **检验的结论比第 31 篇难看得多**：落差 +0.529（海龟 +0.15～0.20）、24 组里 8%–21% 亏钱（海龟 0%）、BTC 的 PBO **0.871**；蒙特卡洛只有 SPY 勉强过关（p = 0.01），AAPL 0.13、BTC 0.40。
- **新的方法论**：**对照用的块长必须比策略的持仓期短**，否则对照里原样保留着你要测的那种结构（AAPL 的 p 从 0.13 涨到 0.59）；⚠️ 但方向取决于保留的结构是帮策略还是害策略（BTC 反过来，从 0.40 降到 0.11）。
- **组合是它真正的位置**：SPY 上两条腿相关 **+0.0025**、同时在场只有 **0.44%**，五五开每月再平衡把夏普从 0.682 / 0.725 提到 **0.981**、卡玛从 0.274 / 0.356 提到 **0.716**、最大回撤从 −17.11% / −11.63% 压到 **−6.30%**。⚠️ 但 BTC 上组合更差，因为那条腿本身夏普只有 0.193。
- 新模块 `talab.reversion` 13 个测试，全课共 **335 个**（不装 TA-Lib 时 303 通过 + 32 跳过）。

---

## 十七、完整代码与测试

### `talab/reversion.py`

```python
"""talab.reversion：均值回归。第 32 篇。

第 31 篇的趋势跟随赌的是「走出去的会接着走」。这一篇赌的正好相反：
**跌得太多的会弹回来。**

两条策略的每一样东西都是镜像：

| | 趋势跟随（第 31 篇） | 均值回归（这一篇） |
|---|---|---|
| 进场 | 价格**创新高** | 价格**跌得离谱** |
| 胜率 | 低（32%–46%） | **高** |
| 单笔盈亏 | 亏小赚大 | **赚小亏大** |
| 形状 | 凸（像买了期权） | **凹（像卖了期权）** |
| 怕什么 | 来回震荡 | **一路不回头** |
| 适合什么市场 | 方差比 > 1 | **方差比 < 1** |

最后那一行是这一篇的骨架：**同一个数（第 5 篇的方差比）同时决定了两篇的结论。**
SPY 的 60 天方差比是 0.616，BTC 是 1.270——所以均值回归在 SPY 上成立、在 BTC 上是反向指标，
而第 31 篇的趋势跟随正好反过来。

⚠️ 这一篇的信号**全部用到当根收盘价**（偏离度、连跌天数、RSI），
所以它**只能下一根开盘成交**——第 31 篇那个「碰到通道就成交」的例外，在这里不成立。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from talab.backtest import Account

SIDES = ("long", "short")


# ---------------------------------------------------------------------------
# 一、拉伸与连击：怎么量「跌得太多」
# ---------------------------------------------------------------------------

def stretch(close: pd.Series, n: int = 20) -> pd.Series:
    """偏离度：收盘价离 n 日均线有几个（n 日）标准差。

    这就是布林带的 %b 换一种写法——`z = −2` 就是「踩在布林下轨上」。
    用标准差而不是百分比，是为了让同一个阈值能跨市场用：
    SPY 的 2 个标准差大约是 3%，BTC 大约是 9%。
    """
    average = close.rolling(n).mean()
    deviation = close.rolling(n).std()
    return ((close - average) / deviation).rename("偏离度")


def streak(close: pd.Series) -> pd.Series:
    """连击：连涨几天记正数，连跌几天记负数，持平记 0。

    它和偏离度量的是**不同的东西**：偏离度看「离得多远」，连击看「连着走了多久」。
    第 32 篇的实测是两个一起用比单用任何一个都好。
    """
    change = close.diff()
    up, down = change > 0, change < 0
    rising = up.groupby((~up).cumsum()).cumsum()
    falling = down.groupby((~down).cumsum()).cumsum()
    return (rising - falling).rename("连击")


def setups(close: pd.Series, condition: pd.Series, horizons=(1, 5, 10, 20)) -> pd.DataFrame:
    """条件成立的每一天，以及之后若干根的涨跌。

    ⚠️ 这不是回测——它没有止损、没有仓位、允许重叠。它回答的是更前面的一个问题：
    **这个条件本身携带信息吗？**答案要和「什么都不做」的基准比（见 `edge`）。
    """
    values = close.to_numpy(float)
    where = np.where(condition.reindex(close.index).fillna(False).to_numpy())[0]
    rows = []
    for i in where:
        row = {"时间": close.index[i], "收盘": values[i]}
        for k in horizons:
            row[f"{k} 根后"] = values[i + k] / values[i] - 1 if i + k < len(values) else np.nan
        tail = values[i + 1:i + 1 + max(horizons)]
        row["期间最低"] = float(tail.min()) / values[i] - 1 if len(tail) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def edge(table: pd.DataFrame, close: pd.Series, horizon: int = 5) -> pd.Series:
    """把 `setups` 的结果和「随便哪一天买入」的基准放在一起比。

    只看「胜率 70%」没有意义——如果随便哪一天买入的胜率也有 68%，那这个条件什么都没说。
    **信号的价值是它比基准好多少，不是它本身多好。**
    """
    column = f"{horizon} 根后"
    hits = table[column].dropna()
    baseline = close.pct_change(horizon).dropna()
    return pd.Series({
        "次数": float(len(hits)), "胜率": float((hits > 0).mean()), "平均": float(hits.mean()),
        "中位": float(hits.median()), "最差": float(hits.min()),
        "基准胜率": float((baseline > 0).mean()), "基准平均": float(baseline.mean()),
        "比基准多赚": float(hits.mean() - baseline.mean()),
    })


# ---------------------------------------------------------------------------
# 二、引擎
# ---------------------------------------------------------------------------

@dataclass
class ReversionPlan:
    """一套均值回归的设定。和第 31 篇的 `TurtlePlan` 一一对应，只是每一项都反过来。"""
    entry_z: float = -2.0                  # 进场：偏离度跌到这个数以下
    entry_streak: int = 3                  # 进场：同时要连跌几天（0 = 不要求）
    entry_rsi: float | None = None         # 进场：改用 RSI 低于这个数（None = 用偏离度）
    rsi_period: int = 2
    exit_z: float = 0.0                    # 出场：偏离度回到这个数以上（0 = 回到均线）
    max_bars: int = 10                     # 出场：最多拿几根（时间出场，第 23 篇的第四类）
    stop_atr: float | None = 3.0           # 止损：进场价往下几个 ATR（None = 不设）
    n: int = 20                            # 算偏离度的窗口
    atr_period: int = 14
    risk: float = 0.02                     # 一笔冒账户的百分之几（有止损时）
    fraction: float = 1.0                  # 没有止损时，一笔买账户的百分之几
    side: str = "long"
    fee_rate: float = 0.0

    def __post_init__(self):
        if self.side not in SIDES:
            raise ValueError(f"side 只能是 {SIDES} 之一，收到 {self.side!r}")
        if self.entry_z >= self.exit_z:
            raise ValueError("进场的偏离度要比出场的低，否则进场当天就该出场")
        if self.max_bars < 1 or self.n < 2:
            raise ValueError("max_bars 至少是 1，算偏离度的窗口至少是 2")
        if self.entry_rsi is not None and not 0 < self.entry_rsi < 100:
            raise ValueError("entry_rsi 要在 0 和 100 之间")

    def describe(self) -> pd.Series:
        entry = (f"{self.rsi_period} 日 RSI 低于 {self.entry_rsi:g}" if self.entry_rsi is not None
                 else f"偏离 {self.n} 日均线 {self.entry_z} 个标准差以下"
                      + (f"，且连跌 {self.entry_streak} 天以上" if self.entry_streak else ""))
        return pd.Series({
            "进场": entry,
            "出场一（回归）": f"偏离度回到 {self.exit_z} 以上",
            "出场二（时间）": f"最多拿 {self.max_bars} 根",
            "出场三（止损）": "不设" if self.stop_atr is None else f"进场价下方 {self.stop_atr} 个 ATR",
            "仓位": f"一笔冒账户的 {self.risk:.1%}" if self.stop_atr
                    else f"一笔买账户的 {self.fraction:.0%}",
            "成交": "下一根开盘（信号用到了收盘价）",
        })


def reversion(df: pd.DataFrame, plan: ReversionPlan | None = None,
              equity: float = 100_000.0) -> dict:
    """按均值回归的规则跑一遍历史。四步顺序和第 27、31 篇完全一样。

    1. **成交**：上一根收盘定下来的单子，用这一根的开盘价成交
    2. **出场**：止损（盘中触发）→ 回归目标 → 时间到，三者按这个顺序判
    3. **估值**：按收盘价记权益
    4. **下单**：用这一根的收盘价算信号，挂下一根的单

    ⚠️ 第 4 步和第 1 步之间隔着一整根 K 线，这是这一篇和第 31 篇最大的实现差别：
    偏离度要用当根收盘价才能算出来，所以**没有当根成交这一说**。
    """
    from talab import indicators as I

    plan = plan or ReversionPlan()
    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    z = stretch(df["close"], plan.n).to_numpy()
    runs = streak(df["close"]).to_numpy()
    atr = I.atr(df["high"], df["low"], df["close"], plan.atr_period).to_numpy()
    force = (I.rsi(df["close"], plan.rsi_period).to_numpy() if plan.entry_rsi is not None
             else np.full(len(c), np.nan))
    direction = 1 if plan.side == "long" else -1

    account = Account(cash=float(equity))
    curve, trades, error = [], [], 0.0
    pending = False
    entry_price = stop = risk_amount = np.nan
    opened_at = -1
    shares = 0.0

    def value(price: float) -> float:
        return account.cash + direction * shares * price

    def close_out(i: int, price: float, reason: str) -> None:
        nonlocal shares, opened_at, stop
        if direction > 0:
            account.sell(price, shares, plan.fee_rate)
            profit = (price - entry_price) * shares - price * shares * plan.fee_rate
        else:
            account.cash -= price * shares * (1 + plan.fee_rate)
            account.fees += price * shares * plan.fee_rate
            profit = (entry_price - price) * shares - price * shares * plan.fee_rate
        trades.append({"进场日": df.index[opened_at], "进场价": entry_price, "数量": shares,
                       "出场日": df.index[i], "出场价": price, "原因": reason, "盈亏": profit,
                       "R": profit / risk_amount if risk_amount else np.nan,
                       "收益": direction * (price / entry_price - 1), "根数": i - opened_at})
        shares, opened_at, stop = 0.0, -1, np.nan

    ready_at = ~np.isnan(z) & ~np.isnan(atr) & (~np.isnan(force) if plan.entry_rsi is not None else True)
    first = int(np.argmax(ready_at)) + 1
    for i in range(first, len(c)):
        # 第 1 步：成交上一根挂出的单
        if pending and shares == 0:
            price = o[i]
            step = plan.stop_atr * atr[i - 1] if plan.stop_atr else np.nan
            want = (value(price) * plan.risk / step if plan.stop_atr
                    else value(price) * plan.fraction / price)
            size = min(want, value(price) / (price * (1 + plan.fee_rate)))
            if size > 0:
                if direction > 0:
                    account.buy(price, size, plan.fee_rate)
                else:
                    account.cash += price * size * (1 - plan.fee_rate)
                    account.fees += price * size * plan.fee_rate
                shares, entry_price, opened_at = size, price, i
                stop = price - direction * step if plan.stop_atr else -direction * np.inf
                risk_amount = size * step if plan.stop_atr else size * price
            pending = False

        # 第 2 步：出场
        if shares > 0:
            if plan.stop_atr and ((direction > 0 and l[i] <= stop) or (direction < 0 and h[i] >= stop)):
                close_out(i, (min(o[i], stop) if direction > 0 else max(o[i], stop)), "止损")
            elif (direction > 0 and z[i] >= plan.exit_z) or (direction < 0 and z[i] <= -plan.exit_z):
                close_out(i, c[i], "回到均线")
            elif i - opened_at >= plan.max_bars:
                close_out(i, c[i], "时间到")

        # 第 3 步：估值
        current = value(c[i])
        error = max(error, abs(account.cash + direction * shares * c[i] - current))
        curve.append(current)

        # 第 4 步：用这一根的收盘价算信号，挂下一根的单
        if shares == 0 and not pending and atr[i] > 0:
            if plan.entry_rsi is not None:
                ready = (force[i] < plan.entry_rsi if direction > 0
                         else force[i] > 100 - plan.entry_rsi)
            else:
                stretched = z[i] <= plan.entry_z if direction > 0 else z[i] >= -plan.entry_z
                long_enough = (runs[i] <= -plan.entry_streak if direction > 0
                               else runs[i] >= plan.entry_streak)
                ready = stretched and (not plan.entry_streak or long_enough)
            if ready:
                pending = True

    if shares > 0:
        close_out(len(c) - 1, c[-1], "未平仓")
    columns = ["进场日", "进场价", "数量", "出场日", "出场价", "原因", "盈亏", "R", "收益", "根数"]
    return {"资金曲线": pd.Series(curve, index=df.index[first:], name="权益"),
            "交易": pd.DataFrame(trades, columns=columns),
            "手续费合计": account.fees, "记账误差": error}


# ---------------------------------------------------------------------------
# 三、结构与组合
# ---------------------------------------------------------------------------

def worst_trades(returns, tops=(1, 3, 5, 10)) -> pd.DataFrame:
    """把**最亏**的几笔拿掉，还剩多少——第 31 篇 `trend.contribution` 的镜像。

    趋势跟随问的是「拿掉最赚的几笔还剩多少」（答案：什么都不剩）；
    均值回归要问的是反过来的那一句：**如果那几次最深的坑没踩到，成绩会好多少？**
    比值越大，说明这条策略越依赖「那几次没出事」。
    """
    values = pd.Series(returns).dropna().astype(float).sort_values()
    total = values.sum()
    rows = [{"拿掉最亏的几笔": 0, "剩下多少": total, "变成原来的": 1.0, "占总笔数": 0.0}]
    for n in tops:
        if n >= len(values):
            break
        left = total - values.iloc[:n].sum()
        rows.append({"拿掉最亏的几笔": n, "剩下多少": left,
                     "变成原来的": left / total if total else np.nan, "占总笔数": n / len(values)})
    return pd.DataFrame(rows)


def blend(curves: dict[str, pd.Series], weights=None, rebalance: str = "ME") -> pd.Series:
    """把几条资金曲线合成一个账户：按权重分钱，按 `rebalance` 的周期调回目标比例。

    ⚠️ 必须**再平衡**才算一个账户。不再平衡只是把两条曲线加起来，
    赚得多的那条会越占越大，最后你量到的是它一个人的性质（第 26 篇量过资金分配的影响）。
    `rebalance=None` 就是不调，留着做对照。
    """
    frame = pd.concat(curves, axis=1).ffill().dropna()
    if weights is None:
        weights = np.full(frame.shape[1], 1 / frame.shape[1])
    weights = np.asarray(weights, dtype=float)
    if len(weights) != frame.shape[1] or not np.isclose(weights.sum(), 1.0):
        raise ValueError("权重个数要和曲线条数一致，而且加起来等于 1")
    steps = frame.pct_change().fillna(0.0).to_numpy()
    marks = (pd.Series(1, index=frame.index).resample(rebalance).last().index
             if rebalance else pd.DatetimeIndex([]))
    holding, total, out = weights.copy(), 1.0, []
    for k, when in enumerate(frame.index):
        holding = holding * (1 + steps[k])
        total_now = holding.sum()
        out.append(total * total_now)
        holding = holding / total_now
        total = total * total_now
        if rebalance and when in marks:
            holding = weights.copy()
    return pd.Series(out, index=frame.index, name="组合") * float(frame.iloc[0].mean())
```

### `talab/tests/test_reversion.py`

```python
"""talab.reversion 的测试（第 32 篇）。价格全部手工构造，每个数都能自己算一遍。"""
import numpy as np
import pandas as pd
import pytest

from talab import reversion as RV


def frame(closes, spread: float = 0.01, opens=None) -> pd.DataFrame:
    close = np.asarray(closes, dtype=float)
    open_ = close if opens is None else np.asarray(opens, dtype=float)
    return pd.DataFrame({"open": open_, "high": np.maximum(close, open_) * (1 + spread),
                         "low": np.minimum(close, open_) * (1 - spread), "close": close},
                        index=pd.date_range("2024-01-01", periods=len(close), freq="D"))


def test_stretch_is_the_z_score_against_the_moving_average():
    close = pd.Series([1, 2, 3, 4, 10.0], index=pd.date_range("2024-01-01", periods=5))
    out = RV.stretch(close, 4)
    assert np.isnan(out.iloc[2])                                  # 前三根凑不齐窗口
    window = close.iloc[1:5]
    assert out.iloc[4] == pytest.approx((10 - window.mean()) / window.std())
    assert out.iloc[4] > 1                                        # 最后一根远高于均线
    flat = pd.Series([5.0] * 10, index=pd.date_range("2024-01-01", periods=10))
    assert np.isnan(RV.stretch(flat, 5).iloc[-1])                 # 标准差是 0，除不出来


def test_streak_counts_up_days_positive_and_down_days_negative():
    close = pd.Series([10, 11, 12, 13, 12, 11, 10, 10, 11.0])
    out = RV.streak(close)
    assert list(out.iloc[1:4]) == [1, 2, 3]                       # 连涨三天
    assert list(out.iloc[4:7]) == [-1, -2, -3]                    # 连跌三天
    assert out.iloc[7] == 0                                       # 持平清零
    assert out.iloc[8] == 1


def test_setups_records_what_happened_after_each_trigger():
    close = pd.Series([100, 90, 95, 99, 120.0], index=pd.date_range("2024-01-01", periods=5))
    condition = pd.Series([False, True, False, False, False], index=close.index)
    table = RV.setups(close, condition, horizons=(1, 3))
    assert len(table) == 1
    row = table.iloc[0]
    assert row["收盘"] == 90
    assert row["1 根后"] == pytest.approx(95 / 90 - 1)
    assert row["3 根后"] == pytest.approx(120 / 90 - 1)
    assert row["期间最低"] == pytest.approx(95 / 90 - 1)          # 之后三根里最低的是 95


def test_edge_compares_the_signal_against_doing_nothing():
    """胜率 100% 也可能什么都没说——要和「随便哪一天买入」比。"""
    close = pd.Series(np.linspace(100, 200, 200), index=pd.date_range("2024-01-01", periods=200))
    condition = pd.Series(False, index=close.index)
    condition.iloc[[10, 50, 90]] = True
    out = RV.edge(RV.setups(close, condition, horizons=(5,)), close, horizon=5)
    assert out["次数"] == 3
    assert out["胜率"] == 1.0 and out["基准胜率"] == 1.0           # 一路上涨，两边都是 100%
    assert out["比基准多赚"] > 0                                  # 三次都落在前半段，那时涨幅占比更大
    assert out["平均"] > out["基准平均"]                          # ——但这什么都没证明，只是买得早


def test_plan_validates_and_describes_both_entry_styles():
    text = RV.ReversionPlan().describe()
    assert "2.0 个标准差" in text["进场"] and "连跌 3 天" in text["进场"]
    assert text["成交"].startswith("下一根开盘")
    rsi = RV.ReversionPlan(entry_rsi=5, rsi_period=2).describe()
    assert rsi["进场"] == "2 日 RSI 低于 5"
    for bad in [dict(side="随便"), dict(entry_z=1.0), dict(max_bars=0), dict(entry_rsi=120)]:
        with pytest.raises(ValueError):
            RV.ReversionPlan(**bad)


def test_books_balance_and_fills_happen_on_the_next_open():
    """信号用到当根收盘价，所以**只能下一根开盘成交**——第 31 篇那个例外在这里不成立。"""
    dip = [100.0] * 25 + [97, 94, 91] + [95.0] * 10
    bars = frame(dip, opens=[100.0] * 25 + [99, 96, 93] + [92.0] + [95.0] * 9)
    plan = RV.ReversionPlan(n=20, entry_z=-1.0, entry_streak=3, exit_z=0.0,
                            max_bars=10, stop_atr=None, fraction=1.0)
    result = RV.reversion(bars, plan)
    assert result["记账误差"] == 0.0
    trade = result["交易"].iloc[0]
    assert trade["进场日"] == bars.index[28]                      # 第 27 根收盘才满足条件
    assert trade["进场价"] == pytest.approx(92.0)                 # 成交在第 28 根的**开盘**


def test_the_three_exits_each_fire():
    reasons = set()
    for closes, kwargs in [
            ([100.0] * 25 + [96, 92, 88] + [200.0] * 5, dict(stop_atr=None)),        # 暴涨 → 回到均线
            ([100.0] * 25 + [96, 92, 88] + [88.5] * 15, dict(stop_atr=None)),        # 不动 → 时间到
            ([100.0] * 25 + [96, 92, 88, 87] + [60.0] * 6, dict(stop_atr=1.0, risk=0.02))]:  # 续跌 → 止损
        plan = RV.ReversionPlan(n=20, entry_z=-1.0, entry_streak=3, max_bars=5, **kwargs)
        trades = RV.reversion(frame(closes), plan)["交易"]
        assert len(trades) >= 1
        reasons.add(trades.iloc[0]["原因"])
    assert reasons == {"回到均线", "时间到", "止损"}


def test_stop_is_three_atr_away_and_costs_exactly_one_r():
    closes = [100 + (1 if i % 2 else -1) for i in range(25)] + [96, 92, 88, 40.0]
    plan = RV.ReversionPlan(n=20, entry_z=-1.0, entry_streak=3, max_bars=20,
                            stop_atr=3.0, risk=0.02, atr_period=14)
    trade = RV.reversion(frame(closes), plan)["交易"].iloc[0]
    assert trade["原因"] == "止损"
    assert trade["R"] < -1.0                                      # 跳空跳过止损，比 1R 还多


def test_rsi_entry_is_an_alternative_trigger():
    closes = [100.0] * 25 + [96, 92, 88] + [95.0] * 10
    common = dict(n=5, exit_z=0.0, max_bars=10, stop_atr=None, fraction=1.0)
    by_rsi = RV.reversion(frame(closes), RV.ReversionPlan(entry_rsi=10, rsi_period=2, **common))
    assert len(by_rsi["交易"]) >= 1
    assert by_rsi["记账误差"] == 0.0


def test_short_side_is_the_mirror_image():
    rising = [100.0] * 25 + [104, 108, 112] + [98.0] * 10
    opens = [100.0] * 25 + [104, 108, 112] + [111.0] + [98.0] * 9   # 第 28 根高开、低走
    plan = dict(n=20, entry_z=-1.0, entry_streak=3, exit_z=0.0, max_bars=10,
                stop_atr=None, fraction=1.0)
    down = RV.reversion(frame(rising, opens=opens), RV.ReversionPlan(side="short", **plan))
    assert len(down["交易"]) == 1 and down["记账误差"] == 0.0
    trade = down["交易"].iloc[0]
    assert trade["进场价"] == pytest.approx(111.0)                 # 下一根开盘卖出
    assert trade["收益"] == pytest.approx(1 - 98 / 111)            # 跌回 98 就是这么多
    assert trade["收益"] > 0                                       # 涨太多之后做空，回落时赚钱


def test_worst_trades_is_the_mirror_of_contribution():
    """趋势跟随问「拿掉最赚的几笔还剩多少」，均值回归要问反过来的那一句。"""
    out = RV.worst_trades([0.01, 0.01, 0.01, 0.01, -0.10], tops=(1, 2))
    assert out.loc[0, "剩下多少"] == pytest.approx(-0.06)
    assert out.loc[1, "拿掉最亏的几笔"] == 1
    assert out.loc[1, "剩下多少"] == pytest.approx(0.04)          # 拿掉那一笔就赚钱了
    assert out.loc[1, "变成原来的"] < 0                           # 从亏变赚，比值是负的
    assert out.loc[2, "剩下多少"] == pytest.approx(0.03)


def test_blend_rebalances_back_to_the_target_weights():
    index = pd.date_range("2024-01-31", periods=90, freq="D")
    fast = pd.Series(np.linspace(100, 300, 90), index=index)       # 一条涨三倍
    flat = pd.Series(100.0, index=index)                           # 一条一动不动
    mixed = RV.blend({"快": fast, "平": flat}, [0.5, 0.5], rebalance="ME")
    never = RV.blend({"快": fast, "平": flat}, [0.5, 0.5], rebalance=None)
    assert len(mixed) == len(fast)
    assert mixed.iloc[-1] < never.iloc[-1]                        # 不再平衡＝让赢家越占越大
    assert mixed.iloc[-1] > flat.iloc[-1]                         # 但组合还是跟着涨了
    with pytest.raises(ValueError):
        RV.blend({"快": fast, "平": flat}, [0.7, 0.7])


def test_blend_of_one_curve_is_that_curve():
    index = pd.date_range("2024-01-01", periods=40, freq="D")
    curve = pd.Series(np.linspace(100, 140, 40), index=index)
    out = RV.blend({"只有一条": curve}, [1.0])
    assert np.allclose(out.to_numpy(), curve.to_numpy())
```

### 两个 venv 的测试结果

```text
335 passed in 1.18s
303 passed, 32 skipped in 1.17s
```

---

## 练习

1. 第四节只量了「之后 N 根的涨跌」。加一列「之后 N 根里的最大回撤」，同样按 1/5/10/20 根看——凹性在这一列上会比在收益那一列上更明显吗？
2. `ReversionPlan` 现在只有偏离度和 RSI 两种进场。加第三种：**布林带下轨被跌穿之后又收回来**（第 15 篇的带宽和第 9 篇的假突破合在一起）。它的胜率和最差一笔比现在好还是差？
3. 第十节发现时间出场在这套规则上是摆设。把出场条件换成「回到 20 日均线」（慢得多），时间出场会不会重新变得有用？
4. 做空那一半：把 `side="short"` 的结果量一遍。在长期向上的标的上做空「涨得太多」，结果会比第 31 篇做空趋势更差还是更好？
5. 第 11.2 节的结论是「块长要比持仓期短」。写一个函数，给定一条策略自动挑块长：先跑一遍拿到中位持仓期，再取它的一半。在这一篇和第 31 篇的四条策略上验证它给出的 p 值是否稳定。
6. `blend` 现在按固定权重再平衡。改成第 26 篇的**波动率倒数**权重（每月按过去 60 天的波动率重新分配），SPY 上的夏普还能再高吗？
7. 把第 31 篇的海龟和这一篇的均值回归同时跑在 SPY、AAPL、BTC 三个标的上（六条腿），按第 26 篇的 `effective_bets` 算一下这个组合的有效独立仓位数。它离 6 有多远？

---

## 小检查答案

1. **至少三件事。**一，**基准是多少**——第四节里基准五天后的胜率就有 61.19%，85% 里有六成是白送的；二，**平均赚多少**（胜率高但每次只赚一点点，可能还不够付成本，第 28 篇）；三，**最差的一次是多少**——这个条件五根后最差 −1.27%，二十根后最差 −20.77%，同一个信号换个窗口就是两种风险。
2. **都不更好，它们是同一枚硬币的两面。**盈亏比 10.06 配的是 32.9% 的胜率，盈亏比 0.56 配的是 70.0% 的胜率，两条的期望值都是正的。真正该比的是第 29 篇那几个数：**含成本的夏普、逐笔的 t 值、以及你能不能坐得住**（趋势跟随最长连亏多少笔，均值回归最差一笔亏多少）。
3. **在趋势跟随上砍掉的是输家**——那些突破之后不走的，止损把它们钉在 1R，代价是也会打掉一些最终会走出去的（第 31 篇：止损把假突破比例从四成推到近七成）。**在均值回归上砍掉的是那条左尾**——那些跌下去不回头的，这是凹性策略唯一真正的风险（BTC 上回撤 −59.86% → −12.54%）。⚠️ 但它也会误伤真正会弹回来的（AAPL 上夏普 0.766 → 0.527）。
4. 因为**块长 20 的对照里，原样保留着日间反转**。均值回归的中位持仓只有 2–3 根，它要利用的结构完全落在一个 20 根的块内部；块自助法打乱的是块与块之间的顺序，块内部一个字没动。于是对照组也会均值回归，你就测不出差别了（AAPL 的 p 从 0.13 涨到 0.59）。**规则是：块长要比持仓期短。**第 30 篇那句话没错，它针对的是持仓十几根的趋势策略。
5. **不一定。**低相关只保证「分散能降低波动」，不保证「组合更好」——那还需要**每条腿自己的期望都为正且量级相当**。第十二节：BTC 上两条腿相关只有 0.0019，但均值回归的夏普是 0.193、趋势跟随是 1.367，五五开之后夏普反而从 1.367 掉到 1.324。**SPY 上组合效果最好，恰恰因为两条腿势均力敌（0.682 和 0.725）。**

---

第七部分到此结束。第 33 篇开始**第八部分：实盘**，讲从回测走到真实账户的那一步：怎么下单、怎么记录、怎么在连亏的时候分清「正常波动」和「策略失效」。动手是 `talab.journal`——一本能和回测对账的交易日志。
