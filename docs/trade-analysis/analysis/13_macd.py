"""第 13 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob

import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, stats as St, structure as X

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

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
markets = {"SPY": spy, "AAPL": aapl, "BTC": day}
periods_per_year = {"SPY": 252, "AAPL": 252, "BTC": 365}

print("===== 片段 2：决策点 =====")
c = day["close"]
m = I.macd(c)
t = pd.Timestamp("2025-08-13", tz="UTC")
print(pd.concat([day[["high", "close"]], m], axis=1).loc["2025-08-08":"2025-08-13"].round(1).to_string())
print(f"此前最高收盘：{c.loc[:'2025-08-12'].max():,.2f}（{c.loc[:'2025-08-12'].idxmax().date()}）")
july = m.loc["2025-06-23":"2025-07-22"]
august = m.loc["2025-08-03":"2025-08-13"]
print(f"6 月 22 日低点之后到 7 月 22 日高点：柱最高 {july['hist'].max():,.1f}（{july['hist'].idxmax().date()}），"
      f"MACD 线最高 {july['macd'].max():,.1f}（{july['macd'].idxmax().date()}）")
print(f"8 月 2 日低点之后到 8 月 13 日：柱最高 {august['hist'].max():,.1f}（{august['hist'].idxmax().date()}），"
      f"MACD 线最高 {august['macd'].max():,.1f}（{august['macd'].idxmax().date()}）")
print(f"7 月 22 日收盘 {c['2025-07-22']:,.2f}，8 月 13 日收盘 {c[t]:,.2f}，高出 {c[t] / c['2025-07-22'] - 1:.2%}")

print("===== 片段 3：手算 MACD =====")
x = pd.Series([1.0, 2, 4, 8, 6, 5, 7])
small = I.macd(x, fast=2, slow=4, signal=2)
small.insert(0, "价格", x)
small.insert(1, "快 EMA2", I.ema(x.where(np.arange(len(x)) >= 2), 2))
small.insert(2, "慢 EMA4", I.ema(x, 4))
print(small.round(4).to_string())

print("===== 片段 4：快 EMA 从哪一根开始 =====")
naive = I.ema(c, 12) - I.ema(c, 26)
difference = (naive - m["macd"]).abs()
first = m["macd"].first_valid_index()
print(f"第一个 MACD 值（{first.date()}）：TA-Lib 写法 {m['macd'][first]:.4f}，两条 EMA 各自开始 {naive[first]:.4f}")
for k in [60, 100, 200]:
    print(f"第 {k} 根：相差 {difference.iloc[k - 1]:.6f}")

print("===== 片段 5：直线上的 MACD =====")
ramp = pd.Series(np.arange(200, dtype=float))
r = I.macd(ramp)
print(f"MACD 线 最小 {r['macd'].min():.6f} 最大 {r['macd'].max():.6f}；柱 最小 {r['hist'].min():.2e} 最大 {r['hist'].max():.2e}")

print("===== 片段 6：带通滤波器 =====")


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

print("===== 片段 7：交叉和零轴 =====")


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

print("===== 片段 8：揭晓 =====")
i = c.index.get_loc(t)
for n in [7, 14, 30, 60]:
    print(f"{n} 天后（{c.index[i + n].date()}）：{c.iloc[i + n] / c[t] - 1:+.2%}")
before_high = c.loc["2025-08-14":"2025-10-05"]
print(f"8 月 14 日到 10 月 5 日：最低收盘 {before_high.min():,.2f}（{before_high.idxmin().date()}）")
print(f"10 月 6 日收盘 {c['2025-10-06']:,.2f}，比 8 月 13 日 {c['2025-10-06'] / c[t] - 1:+.2%}")
later = c.loc["2025-08-14":"2025-10-31"]
print(f"之后到 10 月底：最低收盘 {later.min():,.2f}（{later.idxmin().date()}），最高收盘 {later.max():,.2f}（{later.idxmax().date()}）")
print(f"2025-10-06 之后到 2026-08-31 的最低收盘：{c.loc['2025-10-07':].min():,.2f}（{c.loc['2025-10-07':].idxmin().date()}）")

print("===== 片段 9：背离，写成算法 =====")
swings = X.zigzag(c, 0.05)
found = I.divergences(swings, m["hist"], "bearish")
recent = found[found["second"] >= "2025-01-01"].copy()
print(recent.round({"first_value": 2, "second_value": 2}).to_string(index=False))
row = found[found["second"] == t].iloc[0]
print(f"8 月 13 日这个高点在 {row['confirmed_at'].date()} 被确认，那天收盘 {c[row['confirmed_at']]:,.2f}，"
      f"相比 8 月 13 日 {c[row['confirmed_at']] / c[t] - 1:+.2%}")

print("===== 片段 10：背离之后的走势 =====")
rng = np.random.default_rng(0)


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

print("===== 片段 11：创新高的那一刻就判断 =====")


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
