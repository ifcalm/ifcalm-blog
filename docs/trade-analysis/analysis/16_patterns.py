"""第 16 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
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
datasets = [("SPY 日线", spy, 0.03), ("AAPL 日线", aapl, 0.05), ("BTC 日线", day, 0.10),
            ("BTC 4 小时线", h4, 0.04), ("BTC 1 小时线", h1, 0.02)]

print("===== 片段 2：决策点 =====")
t = pd.Timestamp("2025-01-21")
window = aapl.loc["2025-01-13":"2025-01-21"]
parts = Pt.parts(window)
table = pd.concat([window[["open", "high", "low", "close"]], parts[["body", "upper", "lower", "range_"]],
                   (window["volume"] / 1e6).rename("成交量（百万股）")], axis=1)
table["锤子形"] = Pt.hammer(aapl).loc[window.index]
print(table.round(2).to_string())
close = aapl["close"]
peak = close.loc[:t].idxmax()
atr = I.atr(aapl["high"], aapl["low"], close)
print(f"1 月 21 日收盘 {close[t]:,.2f}，比 {peak.date()} 的最高收盘 {close[peak]:,.2f} 低 {close[t] / close[peak] - 1:.2%}；"
      f"当天 ATR {atr[t]:.2f}，整根 K 线高度是 ATR 的 {(window['high'][t] - window['low'][t]) / atr[t]:.2f} 倍")
print(f"成交量 {window['volume'][t] / 1e6:.1f} 百万股，是前 20 天平均的 {window['volume'][t] / aapl['volume'].loc[:t].iloc[-21:-1].mean():.2f} 倍")
swings = X.zigzag(close, 0.05)
levels = X.trend_state(swings, close, close)
state = X.market_state(levels, close)
print(f"第 11 篇的市场状态：{state[t]}；最近一个已确认的低点 {levels['last_low'][t]:,.2f}，"
      f"这根 K 线的最低价 {window['low'][t]:,.2f}，相差 {abs(window['low'][t] - levels['last_low'][t]) / atr[t]:.2f} 个 ATR")

print("===== 片段 3：把一根 K 线拆开 =====")
example = pd.DataFrame([(10, 14, 8, 12), (12, 12.4, 11.6, 11.9)], columns=Pt.OHLC,
                       index=pd.date_range("2024-01-01", periods=2, freq="D"))
print(pd.concat([example, Pt.parts(example)], axis=1).to_string())

print("===== 片段 4：六个形态的规则 =====")
shapes = pd.DataFrame([(108, 110, 90, 109),      # 锤子形：小实体在上方，长下影
                       (92, 110, 90, 93),        # 倒锤形：小实体在下方，长上影
                       (100, 110, 90, 101),      # 十字星：实体只有整根的 5%
                       (110, 111, 99, 100),      # 长阴线
                       (99, 112, 98, 111),       # 看涨吞没：实体盖住前一根
                       (111, 112, 96, 97),       # 看跌吞没
                       (97, 113, 96, 112),       # 长阳线
                       (110, 111, 108, 109),     # 看跌孕线：小实体包在前一根里
                       (111, 112, 99, 100),      # 长阴线（星形的第 1 根）
                       (98, 99, 96, 97),         # 小实体，整个在前一根实体下方（第 2 根）
                       (98, 107, 97, 106)],      # 阳线，收复第 1 根实体的一半以上：早晨之星
                      columns=Pt.OHLC, index=pd.date_range("2024-02-01", periods=11, freq="D"), dtype=float)
print(pd.concat([shapes, Pt.scan(shapes)], axis=1).to_string())

print("===== 片段 5：形态有多常见 =====")
rows = []
for name, df, threshold in datasets:
    found = Pt.scan(df)
    row = {"数据": name, "K 线": len(df)} | {column: (values != 0).mean() for column, values in found.items()}
    row["锤子形里也是十字星"] = (Pt.doji(df) & Pt.hammer(df)).sum() / Pt.hammer(df).sum()
    row["开盘价 = 前一根收盘价"] = (df["open"] == df["close"].shift(1)).mean()
    rows.append(row)
print(pd.DataFrame(rows).to_string(index=False, formatters={c: "{:.1%}".format for c in
                                                            list(Pt.SHAPES) + list(Pt.COMBINATIONS) + ["锤子形里也是十字星", "开盘价 = 前一根收盘价"]}))

rng = np.random.default_rng(0)


def shuffle_bars(df, rng):
    """打乱 K 线顺序：保留每根 K 线相对前一根收盘价的形状，重新拼成价格（第 9 篇）。"""
    relative = np.log(df[Pt.OHLC].div(df["close"].shift(1), axis=0))
    relative = relative.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    previous_close = df["close"].iloc[0] * np.exp(relative["close"].cumsum().shift(1, fill_value=0))
    out = np.exp(relative[Pt.OHLC]).mul(previous_close, axis=0)
    out.index = df.index[1:]
    return out


rows = []
for name, df, threshold in datasets[:3]:
    real = (Pt.scan(df) != 0).mean()
    shuffled = pd.DataFrame([(Pt.scan(shuffle_bars(df, rng)) != 0).mean() for _ in range(30)]).mean()
    rows.append({"数据": name} | {f"{column}": f"{real[column]:.1%} / {shuffled[column]:.1%}" for column in real.index})
print("真实顺序 / 打乱 K 线顺序 30 次的平均：")
print(pd.DataFrame(rows).to_string(index=False))

print("===== 片段 6：同一个名字，两套定义 =====")
import talib

rows = []
for name, df, threshold in datasets[:3]:
    o, h, l, c = (df[column].to_numpy(float) for column in Pt.OHLC)
    found = Pt.scan(df)
    pairs = [("锤子形", found["锤子形"] > 0, talib.CDLHAMMER(o, h, l, c) > 0),
             ("十字星", found["十字星"] > 0, talib.CDLDOJI(o, h, l, c) > 0),
             ("看涨吞没", found["吞没"] > 0, talib.CDLENGULFING(o, h, l, c) > 0),
             ("看跌吞没", found["吞没"] < 0, talib.CDLENGULFING(o, h, l, c) < 0),
             ("早晨之星", found["星形"] > 0, talib.CDLMORNINGSTAR(o, h, l, c) > 0)]
    for label, ours, theirs in pairs:
        ours, theirs = ours.to_numpy(), np.asarray(theirs)
        rows.append({"数据": name, "形态": label, "talab": int(ours.sum()), "TA-Lib": int(theirs.sum()),
                     "两边都算": int((ours & theirs).sum()), "只有 talab": int((ours & ~theirs).sum()),
                     "只有 TA-Lib": int((~ours & theirs).sum())})
print(pd.DataFrame(rows).to_string(index=False))


def talib_hammer(df):
    """按 TA-Lib 的规则重写锤子线：所有阈值都相对「最近几根 K 线的平均值」，而不是这根 K 线自己的高度。

    实体 < 前 10 根实体的平均；下影线 > 这根的实体；上影线 < 前 10 根整根高度平均的 10%；
    实体下沿 ≤ 前一根的最低价 + 「再往前 5 根整根高度平均」的 20%。
    """
    p = Pt.parts(df)
    height = p["range_"].fillna(0.0)
    return ((p["body"] < p["body"].rolling(10).mean().shift(1))
            & (p["lower"] > p["body"])
            & (p["upper"] < 0.1 * height.rolling(10).mean().shift(1))
            & (p["bottom"] <= df["low"].shift(1) + 0.2 * height.rolling(5).mean().shift(2))).fillna(False)


for name, df, threshold in datasets:
    o, h, l, c = (df[column].to_numpy(float) for column in Pt.OHLC)
    same = (talib_hammer(df).to_numpy() == (talib.CDLHAMMER(o, h, l, c) > 0)).all()
    print(f"{name}：按上面的规则重写，和 talib.CDLHAMMER 完全一致 {same}")

miss = aapl.loc["2025-03-03":"2025-03-05"]
p = Pt.parts(miss)
print("2025-03-05 这根 K 线：talab 判为锤子形，TA-Lib 不判")
print(pd.concat([miss[["open", "high", "low", "close"]], p[["body", "upper", "lower", "range_"]]], axis=1).round(2).to_string())
height = Pt.parts(aapl)["range_"].fillna(0.0)
limit = 0.1 * height.rolling(10).mean().shift(1)
print(f"talab 的上影线上限：整根高度的 15% = {0.15 * p['range_'].iloc[-1]:.2f}；"
      f"TA-Lib 的上限：前 10 根平均高度的 10% = {limit[pd.Timestamp('2025-03-05')]:.2f}；实际上影线 {p['upper'].iloc[-1]:.2f}")

print("===== 片段 7：揭晓 =====")
i = close.index.get_loc(t)
for n in [1, 3, 5, 10, 20, 40, 60]:
    print(f"{n} 天后（{close.index[i + n].date()}）：收盘 {close.iloc[i + n]:,.2f}（{close.iloc[i + n] / close[t] - 1:+.2%}）")
after = close.iloc[i + 1:i + 61]
print(f"之后 60 天：最高收盘 {after.max():,.2f}（{after.idxmax().date()}），最低收盘 {after.min():,.2f}（{after.idxmin().date()}）")
print(f"这根锤子线的最低价 {aapl['low'][t]:,.2f}，之后 60 天里第一次被跌破是 "
      f"{aapl['low'].iloc[i + 1:i + 61][aapl['low'].iloc[i + 1:i + 61] < aapl['low'][t]].index[0].date()}")

print("===== 片段 8：形态之后的走势 =====")


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


def outcomes(df):
    """每根 K 线都按做多、做空各算一次「先碰到哪条 2 ATR 线」（第 11 篇）。"""
    c = df["close"]
    a = I.atr(df["high"], df["low"], c)
    times = c.index[a.notna().to_numpy()]
    return times, {d: pd.Series(X.first_passage(c, df["high"], df["low"], a, times, [d] * len(times)), index=times)
                   for d in (1, -1)}


# 十字星、锤子形没有方向，按教科书最常见的说法（下跌之后看涨）做多打分；倒锤形按「流星」的说法做空
tests = {"十字星": [(1, "全部")], "锤子形": [(1, "全部")], "倒锤形": [(-1, "全部")],
         "吞没": [(1, "看涨"), (-1, "看跌")], "孕线": [(1, "看涨"), (-1, "看跌")], "星形": [(1, "看涨"), (-1, "看跌")]}
rows = []
for name, df, threshold in datasets:
    times, hit = outcomes(df)
    found = Pt.scan(df).reindex(times)
    for column, cases in tests.items():
        for direction, which in cases:
            values = found[column]
            flag = values != 0 if which == "全部" else (values > 0 if which == "看涨" else values < 0)
            _, p = label_test(hit[direction], flag)
            rows.append({"数据": name, "形态": column, "方向": "做多" if direction == 1 else "做空",
                         "次数": int(hit[direction][flag].notna().sum()), "顺向": hit[direction][flag].mean(),
                         "全部 K 线": hit[direction].mean(), "p": p})
table = pd.DataFrame(rows)
print(table.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print(f"一共 {table['p'].notna().sum()} 次检验，p < 0.05 的有 {(table['p'] < 0.05).sum()} 次")

print("===== 片段 9：同样的形态，不同的位置 =====")
simple = {"up": "上升", "down": "下降", "range": "震荡", "transition_up": "过渡", "transition_down": "过渡"}
rows, near_rows = [], []
for name, df, threshold in datasets:
    c = df["close"]
    a = I.atr(df["high"], df["low"], c)
    swings = X.zigzag(c, threshold)
    levels = X.trend_state(swings, c, c)
    state = X.market_state(levels, c).map(simple)
    near_low = (df["low"] - levels["last_low"]).abs() <= 0.5 * a
    ok = a.notna() & state.notna()
    times = c.index[ok.to_numpy()]
    hit = pd.Series(X.first_passage(c, df["high"], df["low"], a, times, [1] * len(times)), index=times)
    found = Pt.scan(df).reindex(times)
    state, near_low = state.reindex(times), near_low.reindex(times).fillna(False)
    for label, flag in [("锤子形", found["锤子形"] > 0), ("看涨吞没", found["吞没"] > 0)]:
        for group in ["下降", "震荡", "上升", "过渡"]:
            inside = (state == group).to_numpy()
            _, p = label_test(hit[inside], flag[inside])
            rows.append({"数据": name, "形态": label, "状态": group, "次数": int(hit[inside][flag[inside]].notna().sum()),
                         "顺向": hit[inside][flag[inside]].mean(), "同状态全部": hit[inside].mean(), "p": p})
        for where, inside in [("前低附近", near_low.to_numpy()), ("其他位置", ~near_low.to_numpy())]:
            _, p = label_test(hit[inside], flag[inside])
            near_rows.append({"数据": name, "形态": label, "位置": where, "次数": int(hit[inside][flag[inside]].notna().sum()),
                              "顺向": hit[inside][flag[inside]].mean(), "同组全部": hit[inside].mean(), "p": p})
by_state = pd.DataFrame(rows)
print("按第 11 篇的实时市场状态分组（都按做多打分）：")
print(by_state.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print(f"一共 {by_state['p'].notna().sum()} 次检验，p < 0.05 的有 {(by_state['p'] < 0.05).sum()} 次")
by_place = pd.DataFrame(near_rows)
print("按「这根 K 线的最低价离最近一个已确认的低点是不是半个 ATR 以内」分组：")
print(by_place.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("===== 片段 10：等确认 =====")
rows = []
for name, df, threshold in datasets:
    times, hit = outcomes(df)
    found = Pt.scan(df)
    long_hit = hit[1]
    confirm = (df["close"] > df["high"].shift(1)).reindex(times).fillna(False)      # 这一根收盘越过前一根的最高价
    after = {label: (signal.shift(1, fill_value=False).reindex(times).fillna(False) & confirm)
             for label, signal in [("锤子形", found["锤子形"] > 0), ("看涨吞没", found["吞没"] > 0)]}
    _, p = label_test(long_hit, confirm)
    rows.append({"数据": name, "组": "任何一根收盘越过前一根最高价", "次数": int(long_hit[confirm].notna().sum()),
                 "顺向": long_hit[confirm].mean(), "对照": long_hit.mean(), "p": p})
    inside = confirm.to_numpy()
    for label, flag in after.items():
        _, p = label_test(long_hit[inside], flag[inside])
        signal = (found["锤子形"] > 0) if label == "锤子形" else (found["吞没"] > 0)
        rows.append({"数据": name, "组": f"{label}之后的确认根", "次数": int(long_hit[flag].notna().sum()),
                     "顺向": long_hit[flag].mean(), "对照": long_hit[confirm].mean(), "p": p,
                     "等到确认的比例": flag.sum() / signal.reindex(times).fillna(False).sum()})
print("「确认」= 形态出现后的下一根收盘越过形态那根的最高价；从确认那一根收盘开始打分：")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
