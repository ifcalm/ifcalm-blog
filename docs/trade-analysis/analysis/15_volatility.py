"""第 15 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob

import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, structure as X

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
cols = ["open", "high", "low", "close"]

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
band = I.bollinger(c)
year_low = band["bandwidth"].rolling(365).min()
t = pd.Timestamp("2023-08-14", tz="UTC")
table = pd.concat([day[["high", "low", "close"]], I.atr(day["high"], day["low"], c).rename("atr"),
                   I.natr(day["high"], day["low"], c).rename("natr"), band[["upper", "lower", "bandwidth"]],
                   year_low.rename("365 天最低带宽")], axis=1)
print(table.loc["2023-08-01":"2023-08-14"].round({"high": 0, "low": 0, "close": 0, "atr": 0, "natr": 2, "upper": 0, "lower": 0,
                                                  "bandwidth": 4, "365 天最低带宽": 4}).to_string())
natr = I.natr(day["high"], day["low"], c)
before = natr.loc[:"2023-08-11"]
print(f"8 月 14 日 NATR {natr[t]:.2f}%，上一次不高于它是 {before[before <= natr[t]].index[-1].date()}；"
      f"带宽 {band['bandwidth'][t]:.4f}，8 月 11 日之前 365 天里最窄的是 {band['bandwidth'].loc[:'2023-08-11'].iloc[-365:].idxmin().date()}"
      f"（{band['bandwidth'].loc[:'2023-08-11'].iloc[-365:].min():.4f}）；2017 年 8 月以来最窄的是 "
      f"{band['bandwidth'].loc[:'2023-08-11'].idxmin().date()}（{band['bandwidth'].loc[:'2023-08-11'].min():.4f}）")
print(f"过去 20 天收盘价最高 {c.loc[:t].iloc[-20:].max():,.2f}，最低 {c.loc[:t].iloc[-20:].min():,.2f}，"
      f"相差 {c.loc[:t].iloc[-20:].max() / c.loc[:t].iloc[-20:].min() - 1:.2%}")

print("===== 片段 3：真实波幅和跳空 =====")
small = pd.DataFrame({"open": [100.0, 104, 97, 99], "high": [102.0, 106, 98, 101], "low": [99.0, 103, 94, 98],
                      "close": [101.0, 105, 95, 100]})
small["最高 - 最低"] = small["high"] - small["low"]
small["|最高 - 昨收|"] = (small["high"] - small["close"].shift(1)).abs()
small["|最低 - 昨收|"] = (small["low"] - small["close"].shift(1)).abs()
small["真实波幅"] = X.true_range(small["high"], small["low"], small["close"])
small["ATR(2)"] = I.atr(small["high"], small["low"], small["close"], 2)
print(small.to_string())
for name, df in markets.items():
    tr = X.true_range(df["high"], df["low"], df["close"])
    gap = (tr - (df["high"] - df["low"]))[tr.notna()]
    share = gap / tr[tr.notna()]
    print(f"{name}：真实波幅大于「最高 - 最低」的日子占 {(gap > 1e-9).mean():.1%}，跳空部分占全部真实波幅的 {gap.sum() / tr.sum():.1%}；"
          f"跳空占比最大的三天 " + "、".join(f"{d.date()}（{v:.0%}）" for d, v in share.nlargest(3).items()))

print("===== 片段 4：ATR 和标准差 =====")
print(f"没有跳空的连续随机游走：一天的 最高 - 最低 平均是标准差的 2√(2/π) = {2 * np.sqrt(2 / np.pi):.3f} 倍")
for name, df in markets.items():
    close = df["close"]
    sd = np.log(close).diff().rolling(20).std()
    hl = ((df["high"] - df["low"]) / close).rolling(20).mean()
    ratio = (I.natr(df["high"], df["low"], close) / 100 / sd).dropna()
    print(f"{name}：NATR ÷ 20 天收益率标准差 中位数 {ratio.median():.2f}（25% ~ 75%：{ratio.quantile(0.25):.2f} ~ {ratio.quantile(0.75):.2f}）；"
          f"不含跳空的 (最高 - 最低)/收盘 ÷ 标准差 中位数 {(hl / sd).median():.2f}")

print("===== 片段 5：布林带 =====")
x = pd.Series([10.0, 11, 12, 11, 13, 14])
small = I.bollinger(x, n=4, k=2)
small.insert(0, "收盘价", x)
small.insert(2, "总体标准差", x.rolling(4).std(ddof=0))
print(small.round(4).to_string())
wrong = c.rolling(20).mean() + 2 * c.rolling(20).std()
print(f"BTC 日线：用 pandas 默认的 rolling().std()（除以 n - 1），上轨最多高出 {(wrong - band['upper']).max():,.2f}，"
      f"带宽平均宽了 {((wrong - c.rolling(20).mean()) / (band['upper'] - band['middle'])).mean() - 1:.2%}")
for name, df in markets.items():
    close = df["close"]
    b = I.bollinger(close)
    ok = b["upper"].notna()
    identity = (b["percent_b"] - 0.5) * b["bandwidth"] - I.bias(close, b["middle"])
    print(f"{name}：收盘价在上轨上方 {(close > b['upper'])[ok].mean():.1%}，在下轨下方 {(close < b['lower'])[ok].mean():.1%}"
          f"（正态分布的说法是各 2.3%）；乖离率 = (%b - 0.5) × 带宽 的最大误差 {identity.abs().max():.1e}")

walk = pd.Series(100 * np.exp(np.cumsum(np.random.default_rng(5).normal(0, 0.01, 200_000))))
b = I.bollinger(walk)
print(f"正态随机游走（20 万步）：收盘价在上轨上方 {(walk > b['upper'])[b['upper'].notna()].mean():.1%}，"
      f"在下轨下方 {(walk < b['lower'])[b['upper'].notna()].mean():.1%}")

print("===== 片段 6：波动率聚集 =====")
rng = np.random.default_rng(0)


def shuffle_bars(df, rng):
    """打乱 K 线顺序：保留每根 K 线相对前一根收盘价的形状，重新拼成价格（第 9 篇）。"""
    rel = np.log(df[cols].div(df["close"].shift(1), axis=0))
    rel = rel.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    prev_close = df["close"].iloc[0] * np.exp(rel["close"].cumsum().shift(1, fill_value=0))
    out = np.exp(rel[cols]).mul(prev_close, axis=0)
    out.index = df.index[1:]
    return out


def future_mean(x, n=20):
    """之后 n 根（不含这一根）的平均值。"""
    return x[::-1].rolling(n).mean()[::-1].shift(-1)


def forecast_power(df):
    """这一根的 NATR 和之后 20 根的平均真实波幅（占前一根收盘价的比例），两者取对数后的相关系数。"""
    tr_pct = X.true_range(df["high"], df["low"], df["close"]) / df["close"].shift(1)
    now, later = np.log(I.natr(df["high"], df["low"], df["close"])), np.log(future_mean(tr_pct))
    ok = now.notna() & later.notna()
    return np.corrcoef(now[ok], later[ok])[0, 1]


datasets = [("SPY 日线", spy), ("AAPL 日线", aapl), ("BTC 日线", day), ("BTC 4 小时线", h4), ("BTC 1 小时线", h1)]
for name, df in datasets:
    sims = np.array([forecast_power(shuffle_bars(df, rng)) for _ in range(100)])
    print(f"{name}：现在的 NATR 和之后 20 根的平均真实波幅，相关系数 {forecast_power(df):.2f}；"
          f"打乱 K 线顺序 100 次：平均 {sims.mean():+.2f}，最大 {sims.max():+.2f}")

rows = []
for name, df in markets.items():
    close = df["close"]
    look = periods_per_year[name]
    n = I.natr(df["high"], df["low"], close)
    rank = n.rolling(look).rank(pct=True)                        # 在过去一年里排第几（只用到这一根为止）
    tr_pct = 100 * X.true_range(df["high"], df["low"], close) / close.shift(1)
    later = pd.DataFrame({"组": pd.cut(rank, [0, 0.2, 0.4, 0.6, 0.8, 1.0], labels=["最低 20%", "20-40%", "40-60%", "60-80%", "最高 20%"]),
                          "现在 NATR": n, "之后 20 根平均真实波幅": future_mean(tr_pct),
                          "之后 20 根收益": close.shift(-20) / close - 1}).dropna()
    later["之后 ÷ 现在"] = later["之后 20 根平均真实波幅"] / later["现在 NATR"]
    g = later.groupby("组", observed=True)
    rows.append(pd.DataFrame({"标的": name, "K 线": g.size(), "现在 NATR": g["现在 NATR"].mean(),
                              "之后 20 根平均真实波幅": g["之后 20 根平均真实波幅"].mean(),
                              "之后 ÷ 现在": g["之后 ÷ 现在"].mean(), "之后 20 根收益": g["之后 20 根收益"].mean(),
                              "上涨比例": g["之后 20 根收益"].apply(lambda v: (v > 0).mean())}).reset_index())
print("按「现在的 NATR 在过去一年里的排位」分成五组：")
print(pd.concat(rows).to_string(index=False, formatters={"现在 NATR": "{:.2f}".format, "之后 20 根平均真实波幅": "{:.2f}".format,
                                                          "之后 ÷ 现在": "{:.2f}".format, "之后 20 根收益": "{:+.2%}".format,
                                                          "上涨比例": "{:.1%}".format}))

print("===== 片段 7：揭晓 =====")
i = c.index.get_loc(t)
for n in [1, 2, 3, 5, 10, 20]:
    print(f"{n} 天后（{c.index[i + n].date()}）：收盘 {c.iloc[i + n]:,.2f}（{c.iloc[i + n] / c[t] - 1:+.2%}），"
          f"带宽 {band['bandwidth'].iloc[i + n]:.4f}，NATR {natr.iloc[i + n]:.2f}")
crash = pd.Timestamp("2023-08-17", tz="UTC")
row = day.loc[crash]
print(f"8 月 17 日：开盘 {row['open']:,.2f}，最低 {row['low']:,.2f}（{row['low'] / row['open'] - 1:+.2%}），收盘 {row['close']:,.2f}，"
      f"真实波幅是 8 月 16 日 ATR 的 {X.true_range(day['high'], day['low'], c)[crash] / I.atr(day['high'], day['low'], c).iloc[i + 2]:.1f} 倍")
after = c.iloc[i + 1:i + 61]
print(f"之后 60 天：最高收盘 {after.max():,.2f}（{after.idxmax().date()}），最低收盘 {after.min():,.2f}（{after.idxmin().date()}）")

print("===== 片段 8：收口之后 =====")


def label_test(values, flag, n=2000):
    """flag 为真的组减去其余的平均值；把标签随机打乱 n 次，看差距不小于实际的比例（第 10 篇）。"""
    v, f = np.asarray(values, float), np.asarray(flag, bool)
    ok = ~np.isnan(v)
    v, f = v[ok], f[ok]
    observed = v[f].mean() - v[~f].mean()
    sims = np.array([v[p].mean() - v[~p].mean() for p in (rng.permutation(f) for _ in range(n))])
    return observed, (np.abs(sims) >= abs(observed)).mean()


def squeeze_study(df, look):
    """带宽创出 look 根新低的第一根（收口），和带宽排在过去 look 根最低 10% 的全部 K 线、全部 K 线比较。"""
    close = df["close"]
    b = I.bollinger(close)
    a = I.atr(df["high"], df["low"], close)
    tr = X.true_range(df["high"], df["low"], close)
    lowest = b["bandwidth"].rolling(look).min()
    new_low = (b["bandwidth"] <= lowest) & lowest.notna()
    squeeze = new_low & ~new_low.shift(1, fill_value=False)
    rank = b["bandwidth"].rolling(look).rank(pct=True)
    high_later = df["high"][::-1].rolling(20).max()[::-1].shift(-1)
    low_later = df["low"][::-1].rolling(20).min()[::-1].shift(-1)
    frame = pd.DataFrame({"收口": squeeze, "最低 10%": rank <= 0.1, "之后 ÷ 现在 ATR": future_mean(tr) / a,
                          "之后 20 根高低点距离（ATR）": (high_later - low_later) / a,
                          "之后 20 根平均真实波幅（%）": 100 * future_mean(tr) / close,
                          "之后 20 根上涨": (close.shift(-20) > close).astype(float)}).loc[rank.notna() & high_later.notna()]
    return frame, b, a


rows = []
for (name, df), look in zip(datasets, [252, 252, 365, 365 * 6, 365 * 24]):
    frame, b, a = squeeze_study(df, look)
    low = frame[frame["最低 10%"]]
    _, p = label_test(low["之后 ÷ 现在 ATR"], low["收口"])
    for label, part in [("收口", frame[frame["收口"]]), ("带宽最低 10%", low), ("全部", frame)]:
        rows.append({"数据": name, "组": label, "K 线": len(part)} | part.iloc[:, 2:].mean().to_dict()
                    | {"p（收口 vs 最低 10%）": p if label == "收口" else np.nan})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: "" if pd.isna(v) else f"{v:.2f}"))

print("同样的计算放在打乱 K 线顺序的价格上（没有波动率聚集），各打乱 20 次取平均：")
rows = []
for (name, df), look in list(zip(datasets, [252, 252, 365, 365 * 6]))[:4]:
    sims = []
    for _ in range(20):
        frame, _, _ = squeeze_study(shuffle_bars(df, rng), look)
        sims.append({"收口 次数": frame["收口"].sum(), "收口": frame.loc[frame["收口"], "之后 ÷ 现在 ATR"].mean(),
                     "带宽最低 10%": frame.loc[frame["最低 10%"], "之后 ÷ 现在 ATR"].mean(), "全部": frame["之后 ÷ 现在 ATR"].mean()})
    rows.append({"数据": name} | pd.DataFrame(sims).mean().to_dict())
print("之后 20 根平均真实波幅 ÷ 现在的 ATR：")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.2f}"))

print("突破方向：收口之后 20 根以内，收盘价第一次越过上轨（做多）或下轨（做空）；对照是所有「前一根还在带内、这一根收在带外」的 K 线")
rows = []
for (name, df), look in zip(datasets, [252, 252, 365, 365 * 6, 365 * 24]):
    frame, b, a = squeeze_study(df, look)
    close = df["close"]
    side = np.sign((close > b["upper"]).astype(int) - (close < b["lower"]).astype(int))
    breakout = (side != 0) & (side.shift(1) == 0) & a.notna()
    after_squeeze = pd.Series(False, index=close.index)
    for when in frame.index[frame["收口"]]:
        k = close.index.get_loc(when)
        later = breakout.iloc[k + 1:k + 21]
        if later.any():
            after_squeeze[later.idxmax()] = True
    times = close.index[breakout]
    hit = pd.Series(X.first_passage(close, df["high"], df["low"], a, times, side[times].to_numpy()), index=times)
    _, p = label_test(hit, after_squeeze[times])
    rows.append({"数据": name, "收口后的突破": int(hit[after_squeeze[times]].notna().sum()),
                 "顺向": hit[after_squeeze[times]].mean(), "全部突破": int(hit.notna().sum()), "全部突破 顺向": hit.mean(), "p": p})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("===== 片段 9：用途一：定止损 =====")


def stop_hit(df, distance, horizon=20):
    """在每根 K 线收盘价买入，止损放在收盘价下方 distance（价格单位），之后 horizon 根里最低价碰到算被打掉。"""
    close, low, dist = df["close"].to_numpy(), df["low"].to_numpy(), distance.to_numpy()
    out = np.full(len(close), np.nan)
    for k in range(len(close) - horizon):
        if not np.isnan(dist[k]):
            out[k] = float((low[k + 1:k + 1 + horizon] <= close[k] - dist[k]).any())
    return pd.Series(out, index=df.index)


rows = []
for name, df in markets.items():
    close = df["close"]
    a = I.atr(df["high"], df["low"], close)
    percent = float((3 * a / close).median())                     # 固定百分比取 3 ATR 的历史中位数，两种止损平均距离相同
    rank = (a / close).rolling(periods_per_year[name]).rank(pct=True)
    frame = pd.DataFrame({"组": pd.cut(rank, [0, 0.2, 0.4, 0.6, 0.8, 1.0], labels=["最低 20%", "20-40%", "40-60%", "60-80%", "最高 20%"]),
                          f"固定 {percent:.2%}": stop_hit(df, close * percent), "3 ATR": stop_hit(df, 3 * a)}).dropna()
    table = frame.groupby("组", observed=True).mean().T
    table.insert(0, "标的", name)
    rows.append(table)
print("20 根以内被打掉的比例，按「现在的 NATR 在过去一年里的排位」分组：")
print(pd.concat(rows).to_string(float_format=lambda v: f"{v:.1%}"))

print("===== 片段 10：用途二：定仓位 =====")
rows = []
for name, df in markets.items():
    close = df["close"]
    r = close.pct_change()
    n = I.natr(df["high"], df["low"], close)
    weight = (1.0 / n.shift(1)).clip(upper=4.0 / n.median())       # 前一根的 NATR 越大，这一根拿得越少；最多 4 倍
    weight = weight / weight.mean()                                 # 平均仓位和固定仓位一样
    scaled = (weight * r).dropna()
    fixed = r.loc[scaled.index]
    by_year = pd.DataFrame({"固定金额": fixed, "按 ATR 调整": scaled}).groupby(scaled.index.year).std() * np.sqrt(periods_per_year[name])
    rows.append({"标的": name, "固定金额 最低年份波动": by_year["固定金额"].min(), "最高": by_year["固定金额"].max(),
                 "最高 ÷ 最低": by_year["固定金额"].max() / by_year["固定金额"].min(),
                 "按 ATR 调整 最低": by_year["按 ATR 调整"].min(), "最高 ": by_year["按 ATR 调整"].max(),
                 "最高 ÷ 最低 ": by_year["按 ATR 调整"].max() / by_year["按 ATR 调整"].min()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.2f}"))

print("===== 片段 11：主线策略 v1 =====")


def backtest_next_open(df, signal):
    """收盘时算出 signal（1 持有、0 空仓），下一根开盘成交（第 12 篇）。"""
    held = signal.shift(1).fillna(0.0)
    before = held.shift(1).fillna(0.0)
    o, close, prev = df["open"], df["close"], df["close"].shift(1)
    r = np.select([(held == 1) & (before == 1), (held == 1) & (before == 0), (held == 0) & (before == 1)],
                  [close / prev - 1, close / o - 1, o / prev - 1], 0.0)
    return pd.Series(r, index=df.index).fillna(0.0)


def mainline_v0(df, fast=50, slow=200):
    """主线策略 v0（第 12 篇）：快均线在慢均线上方就持有。"""
    close = df["close"]
    signal = (I.sma(close, fast) > I.sma(close, slow)).astype(float)
    return signal.where(I.sma(close, slow).notna())


def mainline_v1(df, k=3.0, n_atr=14, breakout=20, fast=50, slow=200):
    """主线策略 v1：v0 加上 ATR 吊灯止损。没有仓位管理、没有成本。

    入场：收盘时快均线在慢均线上方，下一根开盘买入（和 v0 相同）。
    止损：买入那一根的止损价 = 开盘价 - k × 前一根的 ATR。之后每一根开盘前更新：
          止损价 = max(原来的止损价, 买入以来的最高价 - k × 前一根的 ATR)，只上移、不下移。
          开盘价已经不高于止损价，按开盘价卖出（跳空击穿）；否则最低价碰到止损价，按止损价卖出。
    趋势出场：收盘时快均线不在慢均线上方，下一根开盘卖出（和 v0 相同）。
    止损之后：趋势还在，也不马上买回。要等收盘价高于之前 breakout 根的最高收盘价（创新高），下一根开盘再买。
    返回每根 K 线的收益率、是否持有，以及每笔交易。
    """
    o, h, l, c = (df[x].to_numpy(float) for x in cols)
    a = I.atr(df["high"], df["low"], df["close"], n_atr).to_numpy()
    trend = (I.sma(df["close"], fast) > I.sma(df["close"], slow)).to_numpy()
    first = df.index.get_loc(I.sma(df["close"], slow).first_valid_index())
    r, held, trades = np.zeros(len(c)), np.zeros(len(c)), []
    holding = buy = sell = locked = False
    for i in range(first, len(c)):
        if holding:
            stop, base = max(stop, highest - k * a[i - 1]), c[i - 1]
        elif buy:
            holding, buy, entry, entry_i, highest = True, False, o[i], i, o[i]
            stop, base = o[i] - k * a[i - 1], o[i]
        if holding:
            held[i] = 1
            exit_price = reason = None
            if sell:
                exit_price, reason = o[i], "趋势"
            elif o[i] <= stop:
                exit_price, reason = o[i], "止损（跳空）"
            elif l[i] <= stop:
                exit_price, reason = stop, "止损"
            if reason is None:
                r[i], highest = c[i] / base - 1, max(highest, h[i])
            else:
                r[i] = exit_price / base - 1
                trades.append((df.index[entry_i], entry, df.index[i], exit_price, reason))
                holding, sell, locked = False, False, reason.startswith("止损")
        if holding:                                                   # 收盘时决定下一根做什么
            sell = not trend[i]
        elif locked:
            if trend[i] and c[i] > c[i - breakout:i].max():
                buy, locked = True, False
        else:
            buy = bool(trend[i])
    index = df.index[first:]
    trades = pd.DataFrame(trades, columns=["买入日", "买入价", "卖出日", "卖出价", "原因"])
    trades["收益"] = trades["卖出价"] / trades["买入价"] - 1
    return pd.Series(r[first:], index=index), pd.Series(held[first:], index=index), trades


def summary(r, n, held=None, trades=None):
    equity = (1 + r).cumprod()
    out = {"年化": equity.iloc[-1] ** (n / len(r)) - 1, "年化波动": r.std() * np.sqrt(n),
           "最大回撤": (equity / equity.cummax() - 1).min()}
    out["年化 ÷ 波动"] = out["年化"] / out["年化波动"]
    out["年化 ÷ 回撤"] = out["年化"] / -out["最大回撤"]
    if held is not None:
        out["在场时间"] = held.mean()
    if trades is not None:
        out |= {"交易次数": len(trades), "止损出场": int(trades["原因"].str.startswith("止损").sum()),
                "最差一笔": trades["收益"].min()}
    return out


check = []
for name, df in markets.items():
    signal = mainline_v0(df)
    start = signal.first_valid_index()
    d = df.loc[start:]
    v0 = backtest_next_open(d, signal.loc[start:])
    r, held, trades = mainline_v1(df, k=1e12)
    check.append(f"{name} {np.abs(r - v0).max():.1e}")
    rows = {"买入持有": summary(d["close"].pct_change().fillna(0.0), periods_per_year[name]),
            "主线 v0": summary(v0, periods_per_year[name], signal.loc[start:].shift(1).fillna(0.0))}
    for k in [3.0, 2.0, 4.0, 5.0]:
        r, held, trades = mainline_v1(df, k=k)
        rows[f"主线 v1（{k:.0f} ATR）"] = summary(r, periods_per_year[name], held, trades)
        if k == 3.0:
            example = trades
    print(f"{name}：{start.date()} 至 {d.index[-1].date()}")
    count = lambda v: "" if pd.isna(v) else f"{v:.0f}"
    print(pd.DataFrame(rows).T.to_string(float_format=lambda v: "" if pd.isna(v) else f"{v:.3f}",
                                         formatters={"交易次数": count, "止损出场": count}))
    if name == "SPY":
        print("SPY 主线 v1（3 ATR）2020 年和 2025 年的交易：")
        print(example[example["买入日"].dt.year.isin([2020, 2025])].round({"买入价": 2, "卖出价": 2, "收益": 4}).to_string(index=False))
print("止损距离设成无穷大时，v1 和 v0 每根 K 线收益率的最大差：", "，".join(check))

print("===== 片段 12：实验二：和 TA-Lib 对账 =====")
import talib

rows = []
for name, df in [("BTC 日线", day), ("SPY 日线", spy), ("BTC 1 小时线", h1)]:
    high, low, close = df["high"], df["low"], df["close"]
    H, L, C = (s.to_numpy(float) for s in (high, low, close))
    stoch, band, m = I.stochastic(high, low, close), I.bollinger(close), I.macd(close)
    upper, middle, lower = talib.BBANDS(C, 20, 2, 2, 0)
    pairs = [("SMA(20)", I.sma(close, 20), talib.SMA(C, 20)), ("EMA(20)", I.ema(close, 20), talib.EMA(C, 20)),
             ("WMA(20)", I.wma(close, 20), talib.WMA(C, 20)), ("MACD 线", m["macd"], talib.MACD(C)[0]),
             ("MACD 信号线", m["signal"], talib.MACD(C)[1]), ("MACD 柱", m["hist"], talib.MACD(C)[2]),
             ("RSI(14)", I.rsi(close), talib.RSI(C, 14)), ("Stochastic %K", stoch["k"], talib.STOCH(H, L, C, 14, 3, 0, 3, 0)[0]),
             ("Stochastic %D", stoch["d"], talib.STOCH(H, L, C, 14, 3, 0, 3, 0)[1]),
             ("真实波幅", X.true_range(high, low, close), talib.TRANGE(H, L, C)), ("ATR(14)", I.atr(high, low, close), talib.ATR(H, L, C, 14)),
             ("NATR(14)", I.natr(high, low, close), talib.NATR(H, L, C, 14)),
             ("布林上轨", band["upper"], upper), ("布林中轨", band["middle"], middle), ("布林下轨", band["lower"], lower),
             ("+DI(14)", X.adx(high, low, close)["plus_di"], talib.PLUS_DI(H, L, C, 14)),
             ("-DI(14)", X.adx(high, low, close)["minus_di"], talib.MINUS_DI(H, L, C, 14)),
             ("ADX(14)", X.adx(high, low, close)["adx"], talib.ADX(H, L, C, 14))]
    for label, ours, theirs in pairs:
        ours = ours.to_numpy(float)
        both = ~np.isnan(ours) & ~np.isnan(theirs)
        error = np.abs(ours[both] - theirs[both])
        rows.append({"数据": name, "指标": label, "NaN 位置一致": bool((np.isnan(ours) == np.isnan(theirs)).all()),
                     "最大绝对误差": error.max(), "最大相对误差": (error / np.maximum(np.abs(theirs[both]), 1e-12)).max()})
table = pd.DataFrame(rows)
table["通过（相对误差 ≤ 1e-8）"] = table["NaN 位置一致"] & (table["最大相对误差"] <= 1e-8)
print(table.to_string(index=False, formatters={"最大绝对误差": "{:.1e}".format, "最大相对误差": "{:.1e}".format}))

print("===== 片段 13：实验二：ADX 差在哪里 =====")
high, low, close = day["high"], day["low"], day["close"]
H, L, C = (s.to_numpy(float) for s in (high, low, close))
plus_dm = X.directional_movement(high, low)["plus_dm"].to_numpy()
n = 14
running = np.nansum(plus_dm[1:n])                                  # TA-Lib：先把前 n - 1 个 +DM 加起来
talib_style = np.full(len(plus_dm), np.nan)
for k in range(n, len(plus_dm)):
    running = running - running / n + plus_dm[k]
    talib_style[k] = running
tr = X.true_range(high, low, close).to_numpy()
running = np.nansum(tr[1:n])
talib_tr = np.full(len(tr), np.nan)
for k in range(n, len(tr)):
    running = running - running / n + tr[k]
    talib_tr[k] = running
print(f"按 TA-Lib 的初始值重算 +DI，和 talib.PLUS_DI 的最大差：{np.nanmax(np.abs(100 * talib_style / talib_tr - talib.PLUS_DI(H, L, C, 14))):.1e}")
ours = X.adx(high, low, close)
gap = pd.DataFrame({"+DI": (ours["plus_di"] - talib.PLUS_DI(H, L, C, 14)).abs(), "ADX": (ours["adx"] - talib.ADX(H, L, C, 14)).abs()})
start = gap["+DI"].first_valid_index()
k0 = day.index.get_loc(start)
print(pd.DataFrame({f"第 {k} 根": gap.iloc[k0 + k] for k in [0, 14, 50, 100, 200, 300, 400]}).T
      .to_string(formatters={"+DI": "{:.1e}".format, "ADX": "{:.1e}".format}))
print(f"(13/14)^300 = {(13 / 14) ** 300:.1e}")

print("===== 片段 14：实验二：指标相关性矩阵 =====")


def indicator_panel(df):
    """同一组 K 线上的 14 个指标读数，每一列都是「这根 K 线收盘时」的值。"""
    close, high, low = df["close"], df["high"], df["low"]
    m, band, stoch, dmi = I.macd(close), I.bollinger(close), I.stochastic(high, low, close), X.adx(high, low, close)
    change = close.diff()
    return pd.DataFrame({
        "RSI": I.rsi(close), "%K": stoch["k"], "%b": band["percent_b"], "乖离率": I.bias(close, I.sma(close, 20)),
        "20 日涨幅": close.pct_change(20), "效率比": change.rolling(20).sum() / change.abs().rolling(20).sum(),
        "+DI 减 -DI": dmi["plus_di"] - dmi["minus_di"], "MACD 线": m["macd"] / close, "MACD 柱": m["hist"] / close,
        "ADX": dmi["adx"], "NATR": I.natr(high, low, close), "带宽": band["bandwidth"],
        "20 日波动": np.log(close).diff().rolling(20).std(), "相对成交量": I.relative_volume(df["volume"], 20)}).dropna()


for name, df in [("BTC 日线", day), ("SPY 日线", spy)]:
    panel = indicator_panel(df)
    corr = panel.corr(method="spearman")
    print(f"{name}（{len(panel)} 根，Spearman 秩相关）：")
    print(corr.round(2).to_string())
    linked = corr.abs() >= 0.8
    seen, groups = set(), []
    for column in corr.columns:
        if column in seen:
            continue
        group, todo = [], [column]
        while todo:
            item = todo.pop()
            if item not in seen:
                seen.add(item)
                group.append(item)
                todo += [other for other in corr.columns if linked.loc[item, other] and other not in seen]
        groups.append(group)
    print("   |相关系数| ≥ 0.8 连在一起的组：", " ｜ ".join("、".join(g) for g in groups))
