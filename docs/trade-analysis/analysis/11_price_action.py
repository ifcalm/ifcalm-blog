"""第 11 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, structure as X, timeframes as T

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
cols = ["open", "high", "low", "close"]

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
h4 = B.resample_ohlcv(minute, "4h", traded_only=True)
h1 = B.resample_ohlcv(minute, "1h", traded_only=True)
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
print(f"BTC 4 小时线 {len(h4):,} 根，1 小时线 {len(h1):,} 根")


def analyze(df, threshold):
    """一个标的的全套结构：摆动点、高低点状态、市场状态、ATR、三类入场信号。"""
    c = df["close"]
    swings = X.zigzag(c, threshold)
    levels = X.trend_state(swings, c, c)
    state = X.market_state(levels, c)
    atr = X.wilder_smooth(X.true_range(df["high"], df["low"], c), 14)
    signals = X.entries(c, df["high"], df["low"], swings, levels, state)
    return swings, levels, state, atr, signals


print("===== 片段 2：决策点那段行情 =====")
segment = aapl.loc["2021-08-02":"2022-08-31"]
scale = 100 / segment["close"].iloc[0]                       # 第一根收盘价换算成 100
checkpoints = {"决定 1": "2022-01-11", "决定 2": "2022-03-29", "决定 3": "2022-03-31", "决定 4": "2022-06-03"}
print(f"一共 {len(segment)} 根日线，第一根 {segment.index[0].date()}，换算系数 {scale:.4f}")
shown = (segment[cols] * scale).round(2)
shown.insert(0, "第几根", np.arange(1, len(segment) + 1))
for name, t in checkpoints.items():
    k = segment.index.get_loc(pd.Timestamp(t))
    print(f"{name}：")
    print(shown.iloc[k - 1:k + 1].to_string())
seg_swings = X.zigzag(aapl["close"], 0.05)
seg_swings = seg_swings[seg_swings["time"].between(segment.index[0], segment.index[-1])]
print(pd.DataFrame({"第几根": [segment.index.get_loc(t) + 1 for t in seg_swings["time"]],
                    "收盘": (seg_swings["price"] * scale).round(2).to_numpy(),
                    "高 / 低": np.where(seg_swings["kind"] == 1, "高点", "低点"),
                    "第几根确认": [segment.index.get_loc(t) + 1 for t in seg_swings["confirmed_at"]]}).to_string(index=False))
rise = segment["close"].loc["2022-03-14":"2022-03-29"]
print(f"第 156 根到第 167 根：{(rise.diff() > 0).sum()} 天连续收涨")

print("===== 片段 3：每个决策点上，前五篇的工具知道什么 =====")
swings, levels, state, atr, signals = analyze(aapl, 0.05)
anatomy = B.anatomy(aapl)
rvol = I.relative_volume(aapl["volume"], 20)
weekly = aapl.resample("W-MON", label="left", closed="left").agg(
    {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
weekly["ma10"] = weekly["close"].rolling(10).mean()
last_week = T.align_higher(aapl.index, "1D", weekly, "7D")      # 已经收盘的上一周
this_week = T.developing(aapl, "W-MON")                          # 这一周到目前为止
pos = pd.Series(np.arange(len(aapl)), index=aapl.index)
rows = {}
for name, t in checkpoints.items():
    t = pd.Timestamp(t)
    upcoming = swings[swings["confirmed_at"] > t].iloc[0]
    rows[name] = {
        "收盘": f"{aapl.loc[t, 'close'] * scale:.2f}",
        "收盘位置 clv": f"{anatomy.loc[t, 'clv']:.2f}",
        "上周收盘": f"{last_week.loc[t, 'close'] * scale:.2f}",
        "10 周均线": f"{last_week.loc[t, 'ma10'] * scale:.2f}",
        "本周开盘": f"{this_week.loc[t, 'open'] * scale:.2f}",
        "状态": state[t],
        "最近的高点": f"{levels.loc[t, 'last_high'] * scale:.2f}",
        "最近的低点": f"{levels.loc[t, 'last_low'] * scale:.2f}",
        "离高点几个 ATR": f"{(aapl.loc[t, 'close'] - levels.loc[t, 'last_high']) / atr[t]:.2f}",
        "ATR 占价格": f"{atr[t] / aapl.loc[t, 'close']:.2%}",
        "相对成交量": f"{rvol[t]:.2f}",
        "下一个摆动点": f"{upcoming['time'].date()} {'高' if upcoming['kind'] == 1 else '低'}点，"
                     f"{pos[upcoming['confirmed_at']] - pos[t]} 根之后确认",
    }
print(pd.DataFrame(rows).to_string())

print("===== 片段 4：三种状态各占多少时间，一段有多长，之后去哪 =====")
markets = {"BTC": (day, 0.10), "SPY": (spy, 0.03), "AAPL": (aapl, 0.05)}
names = ["up", "down", "range", "transition_up", "transition_down"]
for market, (df, threshold) in markets.items():
    s = analyze(df, threshold)[2].dropna()
    runs = s.groupby((s != s.shift()).cumsum()).agg(["first", "size"])
    table = pd.DataFrame({"时间占比": s.value_counts(normalize=True),
                          "段数": runs["first"].value_counts(),
                          "中位长度": runs.groupby("first")["size"].median()}).reindex(names)
    print(f"{market}（ZigZag {threshold:.0%}）")
    print(table.to_string(formatters={"时间占比": "{:.1%}".format, "中位长度": "{:.1f}".format}))
    moves = pd.crosstab(runs["first"], runs["first"].shift(-1)).reindex(index=names, columns=names, fill_value=0)
    print("下一段是什么（行是这一段，列是下一段）：")
    print(moves.to_string())

for market, (df, threshold) in markets.items():
    sw = analyze(df, threshold)[0]
    p = pd.Series(np.arange(len(df)), index=df.index)
    lag = p[sw["confirmed_at"]].to_numpy() - p[sw["time"]].to_numpy()
    print(f"{market} 摆动点从出现到确认：中位数 {np.median(lag):.0f} 根，平均 {lag.mean():.1f} 根，最长 {lag.max()} 根")

print("===== 片段 5：两个相邻的高点有多接近 =====")
for market, (df, threshold) in markets.items():
    sw = analyze(df, threshold)[0]
    for kind, label in [(1, "高点"), (-1, "低点")]:
        gap = np.abs(np.diff(np.log(sw.loc[sw["kind"] == kind, "price"].to_numpy())))
        print(f"{market} 相邻两个{label}：{len(gap)} 对，相差不到 1% 的 {(gap < 0.01).mean():.1%}，"
              f"不到 2% 的 {(gap < 0.02).mean():.1%}")

print("===== 片段 6：揭晓 =====")
c = aapl["close"]
for (name, t), direction in zip(checkpoints.items(), [1, 1, -1, -1]):
    t = pd.Timestamp(t)
    i = pos[t]
    hit = X.first_passage(c, aapl["high"], aapl["low"], atr, [t], [direction])[0]
    later = {n: c.iloc[i + n] / c.iloc[i] - 1 for n in (5, 10, 20)}
    print(f"{name} {t.date()}：状态 {state[t]}，信号 {signals.loc[signals['time'] == t, 'kind'].tolist()}，"
          f"{'做多' if direction == 1 else '做空'}时先碰到 {'顺向' if hit == 1 else '反向'}的 2 ATR 线；"
          + "，".join(f"{n} 天后 {r:+.2%}" for n, r in later.items())
          + f"；之后 20 天最高 {aapl['high'].iloc[i + 1:i + 21].max() * scale:.2f}，"
          f"最低 {aapl['low'].iloc[i + 1:i + 21].min() * scale:.2f}")
inside = signals[(signals["time"] >= segment.index[0]) & (signals["time"] <= segment.index[-1])].copy()
inside["level"] = (inside["level"] * scale).round(2)
inside["结果"] = X.first_passage(c, aapl["high"], aapl["low"], atr, inside["time"], inside["direction"])
print(inside.to_string(index=False))

print("===== 片段 7：状态和事后看到的行情段 =====")
for market, (df, threshold) in markets.items():
    close = df["close"]
    sw, lv, st, a, sig = analyze(df, threshold)
    p = pd.Series(np.arange(len(close)), index=close.index)
    leg = pd.Series(np.nan, index=close.index, dtype=object)
    for s0, s1 in zip(sw.itertuples(), sw.iloc[1:].itertuples()):
        leg.iloc[p[s0.time] + 1:p[s1.time] + 1] = "上涨段" if s1.kind == 1 else "下跌段"
    both = pd.concat([st.rename("状态"), leg.rename("事后")], axis=1).dropna()
    print(f"{market}：上涨段占全部 K 线的 {(both['事后'] == '上涨段').mean():.1%}")
    share = pd.crosstab(both["状态"], both["事后"], normalize="index").reindex(names)
    share["K 线数"] = both["状态"].value_counts().reindex(names)
    print(share.to_string(formatters={"上涨段": "{:.1%}".format, "下跌段": "{:.1%}".format}))
    done, never, turns = [], 0, 0
    for s0, s1 in zip(sw.itertuples(), sw.iloc[1:].itertuples()):
        want = "up" if s1.kind == 1 else "down"
        if st[s0.time] == want:                       # 这段开始时已经是同方向的趋势：不是转折
            continue
        turns += 1
        part = st.iloc[p[s0.time]:p[s1.time] + 1]
        hit = part.index[part == want]
        if len(hit) == 0:
            never += 1
            continue
        done.append(np.log(close[hit[0]] / s0.price) / np.log(s1.price / s0.price))
    print(f"   开始时不是同方向趋势的行情段 {turns} 段：整段都没有显示成同方向趋势的 {never} 段（{never / turns:.0%}）；"
          f"其余 {len(done)} 段第一次显示时，已经走完 中位数 {np.median(done):.0%}，"
          f"四分位 {np.percentile(done, 25):.0%} ~ {np.percentile(done, 75):.0%}")


print("===== 片段 8：三类入场，日线 =====")
def shuffle_bars(df, rng):
    """打乱 K 线顺序：保留每根 K 线相对前一天收盘价的形状，重新拼成价格。"""
    rel = np.log(df[cols].div(df["close"].shift(1), axis=0))
    rel = rel.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    prev_close = df["close"].iloc[0] * np.exp(rel["close"].cumsum().shift(1, fill_value=0))
    out = np.exp(rel[cols]).mul(prev_close, axis=0)
    out.index = df.index[1:]
    return out


def win_rates(df, threshold, distance=2.0, horizon=20):
    """每类信号「先碰到顺向的线」的比例（没碰到任何一条的不算）。"""
    sw, lv, st, a, sig = analyze(df, threshold)
    sig = sig[a.reindex(sig["time"]).notna().to_numpy()]
    sig = sig.assign(win=X.first_passage(df["close"], df["high"], df["low"], a, sig["time"], sig["direction"],
                                         distance, horizon))
    g = sig.groupby(["kind", "direction"])["win"]
    return pd.DataFrame({"次数": g.count(), "顺向": g.mean()})


def compare(df, threshold, distance=2.0, n=200):
    rng = np.random.default_rng(0)
    real = win_rates(df, threshold, distance)
    sims = pd.concat([win_rates(shuffle_bars(df, rng), threshold, distance)["顺向"] for _ in range(n)], axis=1)
    sims = sims.reindex(real.index)
    real["打乱 2.5%"] = sims.quantile(0.025, axis=1)
    real["打乱平均"] = sims.mean(axis=1)
    real["打乱 97.5%"] = sims.quantile(0.975, axis=1)
    center = sims.mean(axis=1)
    real["p"] = [(np.abs(sims.loc[k] - center[k]) >= abs(real.loc[k, "顺向"] - center[k])).mean() for k in real.index]
    return real


percent = {c: "{:.1%}".format for c in ["顺向", "打乱 2.5%", "打乱平均", "打乱 97.5%"]}
for market, (df, threshold) in markets.items():
    print(f"{market} 日线（ZigZag {threshold:.0%}，2 ATR，20 根）")
    print(compare(df, threshold).to_string(formatters=percent | {"p": "{:.3f}".format}))

print("===== 片段 9：三类入场，BTC 4 小时线和 1 小时线 =====")
for market, df, threshold in [("BTC 4 小时线", h4, 0.04), ("BTC 1 小时线", h1, 0.02)]:
    for distance in [2.0, 1.0, 3.0]:
        print(f"{market}（ZigZag {threshold:.0%}，{distance:.0f} ATR，20 根）")
        print(compare(df, threshold, distance).to_string(formatters=percent | {"p": "{:.3f}".format}))


def month_baseline(df, threshold, distance=2.0):
    """对照：同一个月里每一根 K 线都按同一个方向入场，先碰到顺向线的比例。扣掉「那个月本来就在涨 / 跌」。"""
    sw, lv, st, a, sig = analyze(df, threshold)
    times = df.index[a.notna().to_numpy()]
    month = {}
    for direction in (1, -1):
        hit = X.first_passage(df["close"], df["high"], df["low"], a, times, [direction] * len(times), distance)
        month[direction] = pd.Series(hit, index=times).groupby(times.tz_localize(None).to_period("M")).mean()
    sig = sig[a.reindex(sig["time"]).notna().to_numpy()]
    sig = sig.assign(顺向=X.first_passage(df["close"], df["high"], df["low"], a, sig["time"], sig["direction"], distance))
    sig = sig.dropna(subset=["顺向"])
    sig["同月全部 K 线"] = [month[d][t.tz_localize(None).to_period("M")] for t, d in zip(sig["time"], sig["direction"])]
    return sig.groupby(["kind", "direction"])[["顺向", "同月全部 K 线"]].mean()


for market, df, threshold in [("BTC 4 小时线", h4, 0.04), ("BTC 1 小时线", h1, 0.02)]:
    print(f"{market}（2 ATR）和同一个月的全部 K 线比：")
    print(month_baseline(df, threshold).to_string(float_format="{:.1%}".format))
sw, lv, st, a, sig = analyze(h1, 0.02)
breakouts = sig[sig["kind"] == "breakout"]
print(f"1 小时线突破信号那根 K 线的 ATR 占价格：中位数 {(a / h1['close']).reindex(breakouts['time']).median():.2%}")

print("===== 片段 10：实验一，手工标注和自动标注 =====")
hand_segments = pd.read_csv(Path(__file__).with_name("11_spy_hand_labels.csv"))
window = spy.loc["2018-01-02":"2019-06-28"].index
hand = X.segments_to_labels(hand_segments, window)
simple = {"transition_up": "transition", "transition_down": "transition"}
for threshold in [0.02, 0.03, 0.05, 0.08]:
    auto = analyze(spy, threshold)[2].reindex(window).replace(simple)
    result = X.agreement(hand, auto)
    print(f"ZigZag {threshold:.0%}：相同 {result['share']:.1%}，kappa {result['kappa']:.2f}")
    if threshold == 0.03:
        print(result["table"].rename_axis(index="手工", columns="自动").to_string())
        by_segment = []
        for s in hand_segments.itertuples():
            part = auto.loc[s.start:s.end]
            same = (part == s.label).to_numpy()
            by_segment.append({"开始": s.start, "结束": s.end, "手工": s.label, "根数": len(part),
                               "相同": f"{same.mean():.0%}",
                               "第几根开始相同": int(np.argmax(same)) + 1 if same.any() else "-",
                               "自动标注": "，".join(f"{k} {v}" for k, v in part.value_counts().items())})
        print(pd.DataFrame(by_segment).to_string(index=False))
sw, lv, st, a, sig = analyze(spy, 0.03)
print(sw[(sw["time"] >= "2016-06-01") & (sw["time"] <= "2019-06-30")].round({"price": 2}).to_string(index=False))
print(pd.concat([spy["close"], lv, st], axis=1).loc[["2018-02-02", "2018-02-08", "2018-02-28", "2018-03-01", "2019-02-22",
                                                   "2019-02-25", "2019-04-30", "2019-05-13"]].round(2).to_string())
