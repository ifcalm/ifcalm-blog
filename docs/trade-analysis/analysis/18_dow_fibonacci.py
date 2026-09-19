"""第 18 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob

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
thresholds = {"SPY 日线": 0.02, "AAPL 日线": 0.03, "BTC 日线": 0.05, "BTC 4 小时线": 0.02, "BTC 1 小时线": 0.01}   # 和第 17 篇相同

print("===== 片段 2：决策点 =====")
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

print("===== 片段 3：斐波那契比例从哪里来 =====")
fib = [1, 1]
while len(fib) < 16:
    fib.append(fib[-1] + fib[-2])
print("斐波那契数列：", fib)
print("相邻两项之比：", [round(fib[k + 1] / fib[k], 4) for k in range(9, 15)])
phi = (1 + 5 ** 0.5) / 2
print(f"黄金比例 φ = {phi:.6f}；1/φ = {1 / phi:.6f}；1/φ² = {1 / phi ** 2:.6f}；1/φ³ = {1 / phi ** 3:.6f}；"
      f"√(1/φ) = {(1 / phi) ** 0.5:.6f}；φ² = {phi ** 2:.6f}；√φ = {phi ** 0.5:.6f}")

print("===== 片段 4：起点和终点怎么选 =====")
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

print("===== 片段 5：道氏理论：次级回调回撤主要趋势的 1/3 到 2/3？ =====")
rng = np.random.default_rng(0)


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

print("===== 片段 6：揭晓 =====")
after = spy.loc["2025-03-17":"2025-06-30"]
full_levels = Pt.retracement_levels(start, end)
for when in ["2025-03-25", "2025-04-03", "2025-04-08", "2025-04-09", "2025-05-12", "2025-06-27"]:
    close = spy.loc[when, "close"]
    nearest = (full_levels - close).abs().idxmin()
    print(f"{when}：收盘 {close:.2f}，离得最近的回撤位是 {nearest:.1%}（{full_levels[nearest]:.2f}），相差 {close / full_levels[nearest] - 1:+.2%}")
print(f"4 月 8 日收盘 {spy.loc['2025-04-08', 'close']:.2f}，比这一段的起点 {start:.2f} 还低 {spy.loc['2025-04-08', 'close'] / start - 1:.2%}；"
      f"第一次收盘回到 2 月 19 日 {end:.2f} 上方：{after.index[after['close'] > end][0].date()}")

print("===== 片段 7：回撤到斐波那契位和随机比例位 =====")
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

print("===== 片段 8：事后画线 =====")


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
