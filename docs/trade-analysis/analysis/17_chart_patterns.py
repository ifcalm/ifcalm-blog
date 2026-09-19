"""第 17 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
import math

import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, patterns as Pt, structure as X

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
h4 = B.resample_ohlcv(minute, "4h", traded_only=True)
h1 = B.resample_ohlcv(minute, "1h", traded_only=True)
del minute
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
datasets = [("SPY 日线", spy), ("AAPL 日线", aapl), ("BTC 日线", day), ("BTC 4 小时线", h4), ("BTC 1 小时线", h1)]
for name, df in datasets:
    print(f"{name}：NATR 中位数 {I.natr(df['high'], df['low'], df['close']).median():.2f}%")
thresholds = {"SPY 日线": 0.02, "AAPL 日线": 0.03, "BTC 日线": 0.05, "BTC 4 小时线": 0.02, "BTC 1 小时线": 0.01}

print("===== 片段 2：决策点 =====")
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

print("===== 片段 3：把头肩顶写成规则 =====")
points = [(0, 100), (10, 110), (16, 102), (28, 120), (36, 104), (44, 112), (60, 96)]
path = np.interp(np.arange(61), [p[0] for p in points], [p[1] for p in points])
toy = pd.Series(path, index=pd.date_range("2024-01-01", periods=61, freq="D"))
toy_swings = X.zigzag(toy, 0.05)
print(toy_swings.to_string(index=False))
toy_found = Pt.head_and_shoulders(toy, toy_swings)
print(toy_found.drop(columns=["left", "neck_1", "neck_2"]).round(2).T.to_string())

print("===== 片段 4：调参数，识别结果怎么变 =====")
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

print("===== 片段 5：揭晓 =====")
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

print("===== 片段 6：「突破颈线才算成立」 =====")
rng = np.random.default_rng(0)


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

print("===== 片段 7：三角形、楔形、通道 =====")


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
