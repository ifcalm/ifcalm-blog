"""第 9 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob

import exchange_calendars as xc
import numpy as np
import pandas as pd
from talab import bars as B, data as D, structure as X

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
cols = ["open", "high", "low", "close"]

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
spy["volume"] = spy["volume"].fillna(0)
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
markets = {"BTC": day, "SPY": spy, "AAPL": aapl}
atr = {name: X.wilder_smooth(X.true_range(df["high"], df["low"], df["close"]), 14) for name, df in markets.items()}
swings = {name: X.fractals(df["high"], df["low"], 5, 5) for name, df in markets.items()}

print("===== 片段 2：决策点 =====")
hour = B.resample_ohlcv(minute.loc["2026-06-02":"2026-06-03"], "1h")
print(hour.loc["2026-06-03 00:00":"2026-06-03 03:00", cols])
decision = pd.Timestamp("2026-06-03 04:00", tz="UTC")                   # 03:00 这根 1 小时线收盘
known = swings["BTC"][swings["BTC"]["confirmed_at"] < decision.floor("1D")]
lows = known[(known["kind"] == -1) & (known["time"] >= "2026-01-01")]
print(lows.to_string(index=False))
print(X.cluster_levels(lows["price"], 0.01).round(2).to_string(index=False))
print(f"前一天的 ATR：{atr['BTC']['2026-06-02']:,.2f}")

print("===== 片段 3：整数关口 =====")
hour_all = B.resample_ohlcv(minute, "1h")
def round_stats(prices, step):
    p = prices[(prices >= 10_000) & (prices < 130_000)]
    r = np.round(np.mod(p, step), 2)
    return {"样本": len(p), "正好整数": (r == 0).mean(), "整数下方 50 以内": ((r >= step - 50) & (r > 0)).mean(),
            "整数上方 50 以内": ((r > 0) & (r <= 50)).mean()}
for step in [1000, 100]:
    table = pd.DataFrame({name: round_stats(p, step) for name, p in [
        ("1 分钟收盘价", minute["close"]), ("1 小时最高价", hour_all["high"]), ("1 小时最低价", hour_all["low"]),
        ("日线最高价", day["high"]), ("日线最低价", day["low"])]}).T
    print(f"{step} 的整数倍：")
    print(table.to_string(formatters={"样本": "{:,.0f}".format, "正好整数": "{:.2%}".format,
                                      "整数下方 50 以内": "{:.2%}".format, "整数上方 50 以内": "{:.2%}".format}))

print("===== 片段 4：65,000 附近这三个水平位的一生 =====")
zone_swings = swings["BTC"][(swings["BTC"]["kind"] == -1) & swings["BTC"]["price"].between(65000, 65618.49)
                            & (swings["BTC"]["time"] < "2026-06-01")]
life = X.level_tests(day["high"], day["low"], day["close"], zone_swings, atr["BTC"])
print(life.assign(level_time=life["level_time"].dt.date, test_time=life["test_time"].dt.date,
                  resolved_at=life["resolved_at"].dt.date).to_string(index=False))

print("===== 片段 5：揭晓 =====")
c = day["close"]
print(f"6 月 3 日收盘 {c['2026-06-03']:,.2f}；6 月 5 日最低 {day.loc['2026-06-05', 'low']:,.2f}；"
      f"7 月 1 日最低 {day.loc['2026-07-01', 'low']:,.2f}")
for n in [7, 30, 60]:
    later = day.index[day.index.get_loc(pd.Timestamp("2026-06-03", tz="UTC")) + n]
    print(f"6 月 3 日收盘之后 {n} 天（{later.date()}）：{c[later] / c['2026-06-03'] - 1:+.2%}")
summer = day.loc["2026-06-06":"2026-08-16"]
print(f"6 月 6 日到 8 月 16 日：最高价 {summer['high'].max():,.2f}（{summer['high'].idxmax().date()}），"
      f"收盘价最高 {summer['close'].max():,.2f}，收盘在 65,618.49 上方的天数 {(summer['close'] > 65618.49).sum()} / {len(summer)}")
print(f"8 月 17 日到 8 月 31 日：最高价 {day.loc['2026-08-17':, 'high'].max():,.2f}，8 月 31 日收盘 {c.iloc[-1]:,.2f}")

print("===== 片段 6：第几次测试，守住的比例 =====")
def shuffle_bars(df, rng):
    """打乱 K 线顺序：保留每根 K 线相对前一天收盘价的形状和成交量，重新拼成价格。"""
    rel = np.log(df[cols].div(df["close"].shift(1), axis=0))
    rel["volume"] = df["volume"]
    rel = rel.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    prev_close = df["close"].iloc[0] * np.exp(rel["close"].cumsum().shift(1, fill_value=0))
    out = np.exp(rel[cols]).mul(prev_close, axis=0)
    out["volume"] = rel["volume"].to_numpy()
    out.index = df.index[1:]
    return out
def hold_rates(df, distance=1.5):
    a = X.wilder_smooth(X.true_range(df["high"], df["low"], df["close"]), 14)
    t = X.level_tests(df["high"], df["low"], df["close"], X.fractals(df["high"], df["low"], 5, 5), a, distance=distance)
    t = t[t["outcome"] != "open"]
    groups = {}
    for role, name in [("support", "支撑"), ("resistance", "阻力")]:
        first = t[(t["role"] == role) & (t["flips"] == 0)]
        for label, part in [("第 2 次", first[first["n"] == 2]), ("第 3 次", first[first["n"] == 3]),
                            ("第 4 次", first[first["n"] == 4]), ("第 5 次及以上", first[first["n"] >= 5]),
                            ("互换后第 1 次", t[(t["role"] == role) & (t["flips"] == 1) & (t["n"] == 1)])]:
            groups[(name, label)] = ((part["outcome"] == "held").mean(), len(part))
    return groups
rng = np.random.default_rng(0)
for name, df in markets.items():
    real = hold_rates(df)
    sims = pd.DataFrame([{k: v[0] for k, v in hold_rates(shuffle_bars(df, rng)).items()} for _ in range(200)])
    table = pd.DataFrame({"次数": [v[1] for v in real.values()], "守住": [v[0] for v in real.values()],
                          "打乱后 2.5%": sims.quantile(0.025).values, "打乱后平均": sims.mean().values,
                          "打乱后 97.5%": sims.quantile(0.975).values}, index=pd.MultiIndex.from_tuples(real.keys()))
    print(name)
    print(table.round(3).to_string())
print("BTC 支撑第 2 次测试，换不同的「离开 / 守住 / 突破」距离：")
for distance in [1.0, 2.0]:
    real = hold_rates(day, distance)[("支撑", "第 2 次")]
    sims = [hold_rates(shuffle_bars(day, rng), distance)[("支撑", "第 2 次")][0] for _ in range(200)]
    print(f"   {distance} 个 ATR：守住 {real[0]:.1%}（{real[1]} 次），打乱后 {np.percentile(sims, 2.5):.1%} ~ {np.percentile(sims, 97.5):.1%}")

print("===== 片段 7：跌破之后，多少是假跌破 =====")
def breakdowns(df, horizon=10, distance=1.5):
    """支撑第一次被收盘跌破（之前价格已经离开过），之后 horizon 天内先收回支撑上方，算假跌破。"""
    a = X.wilder_smooth(X.true_range(df["high"], df["low"], df["close"]), 14).to_numpy()
    h, l, c, v = (df[k].to_numpy(float) for k in ["high", "low", "close", "volume"])
    v20 = df["volume"].rolling(20).mean().shift(1).to_numpy()
    pos = {t: i for i, t in enumerate(df.index)}
    rows = []
    sw = X.fractals(df["high"], df["low"], 5, 5)
    for s in sw[sw["kind"] == -1].itertuples():
        level, armed, pierced = s.price, False, False
        for j in range(pos[s.confirmed_at] + 1, len(c) - horizon):
            unit = a[j - 1]
            if np.isnan(unit):
                continue
            if not armed:
                if c[j] >= level + distance * unit:
                    armed = True
                elif c[j] < level:
                    break
                continue
            if l[j] < level <= c[j] and not pierced:              # 盘中跌破、收盘收回
                pierced = True
                rows.append(("只是盘中跌破", (level - l[j]) / unit, v[j] / v20[j], bool((c[j + 1:j + 1 + horizon] < level).any())))
            if c[j] < level:
                later = c[j + 1:j + 1 + horizon]
                back, deep = np.flatnonzero(later >= level), np.flatnonzero(later <= level - distance * unit)
                fake = len(back) > 0 and (len(deep) == 0 or back[0] < deep[0])
                rows.append(("收盘跌破", (level - c[j]) / unit, v[j] / v20[j], fake))
                break
    return pd.DataFrame(rows, columns=["类型", "深度", "量比", "结果"])
def breakdown_table(df):
    b = breakdowns(df)
    close_breaks = b[b["类型"] == "收盘跌破"]
    rows = {("全部收盘跌破", ""): close_breaks["结果"]}
    depth = pd.cut(close_breaks["深度"], [0, 0.25, 0.5, 1, np.inf], labels=["0~0.25", "0.25~0.5", "0.5~1", "1 以上"])
    for label, part in close_breaks.groupby(depth, observed=False):
        rows[("收盘价在支撑下方几个 ATR", label)] = part["结果"]
    volume = pd.cut(close_breaks["量比"], [0, 1, 1.5, np.inf], labels=["1 倍以下", "1~1.5 倍", "1.5 倍以上"])
    for label, part in close_breaks.groupby(volume, observed=False):
        rows[("成交量是 20 日平均的", label)] = part["结果"]
    rows[("只是盘中跌破：之后 10 天内收盘跌破", "")] = b.loc[b["类型"] == "只是盘中跌破", "结果"]
    return {k: (v.astype(float).mean(), len(v)) for k, v in rows.items()}
for name in ["BTC", "SPY"]:
    real = breakdown_table(markets[name])
    sims = pd.DataFrame([{k: v[0] for k, v in breakdown_table(shuffle_bars(markets[name], rng)).items()} for _ in range(200)])
    table = pd.DataFrame({"次数": [v[1] for v in real.values()], "比例": [v[0] for v in real.values()],
                          "打乱后平均次数": [np.nan] * len(real), "打乱后 2.5%": sims.quantile(0.025).values,
                          "打乱后 97.5%": sims.quantile(0.975).values}, index=pd.MultiIndex.from_tuples(real.keys()))
    counts = pd.DataFrame([{k: v[1] for k, v in breakdown_table(shuffle_bars(markets[name], rng)).items()} for _ in range(50)])
    table["打乱后平均次数"] = counts.mean().values
    print(name)
    print(table.round(3).to_string())

print("===== 片段 8：美股的隔夜跳空 =====")
def gap_table(df):
    g = X.gaps(df["open"], df["high"], df["low"], df["close"])
    sigma = np.log(df["close"]).diff().rolling(20).std().shift(1)
    g = g[sigma[g.index].notna()].copy()
    g["标准差倍数"] = np.abs(np.log1p(g["size"])) / sigma[g.index]
    high20 = df["high"].rolling(20).max().shift(1)
    low20 = df["low"].rolling(20).min().shift(1)
    g["突破型"] = np.where(g["direction"] == 1, g["open"] > high20[g.index], g["open"] < low20[g.index])
    fill, mirror = [], []
    days = pd.Series(np.arange(len(df)), index=df.index)
    for t, row in g.iterrows():
        up = row["direction"] == 1
        fill.append(X.first_reach(df["high"], df["low"], t, row["prev_close"], from_above=up))
        other_side = row["open"] * row["open"] / row["prev_close"]           # 开盘价另一侧、同样距离的价格
        mirror.append(X.first_reach(df["high"], df["low"], t, other_side, from_above=not up))
    g["回补"] = [days[f] - days[t] if pd.notna(f) else np.nan for f, t in zip(fill, g.index)]
    g["对照"] = [days[f] - days[t] if pd.notna(f) else np.nan for f, t in zip(mirror, g.index)]
    return g
def fill_summary(part):
    return pd.Series({"次数": len(part), "当天回补": (part["回补"] == 0).mean(), "5 天内": (part["回补"] <= 5).mean(),
                      "20 天内": (part["回补"] <= 20).mean(), "对照 当天": (part["对照"] == 0).mean(),
                      "对照 5 天内": (part["对照"] <= 5).mean(), "对照 20 天内": (part["对照"] <= 20).mean()})
for name in ["SPY", "AAPL"]:
    g = gap_table(markets[name])
    print(f"{name}：{len(g)} 个交易日有跳空，其中向上 {(g['direction'] == 1).mean():.1%}，完整缺口 {g['full'].sum()} 个")
    size = pd.cut(g["标准差倍数"], [0, 0.25, 0.5, 1, 2, np.inf], labels=["0~0.25", "0.25~0.5", "0.5~1", "1~2", "2 以上"])
    print(g.groupby(size, observed=False).apply(fill_summary).round(3).to_string())
    big = g[g["标准差倍数"] > 1]
    print("超过 1 倍标准差的跳空，按是否突破 20 日区间：")
    print(big.groupby(big["突破型"].map({True: "突破型", False: "普通"})).apply(fill_summary).round(3).to_string())

print("===== 片段 9：BTC 的 CME 缺口 =====")
CT = "America/Chicago"
cme = xc.get_calendar("CMES", start="2017-12-01", end="2026-06-30")
open_days = set(cme.sessions.date)
rows = []
for friday in pd.date_range("2017-12-22", "2026-05-22", freq="W-FRI"):
    last = friday
    while last.date() not in open_days:                   # 周五休市（比如耶稣受难日），用前一个交易日
        last -= pd.Timedelta("1D")
    close_at = pd.Timestamp(f"{last.date()} 16:00", tz=CT).tz_convert("UTC")
    open_at = pd.Timestamp(f"{(friday + pd.Timedelta('2D')).date()} 17:00", tz=CT).tz_convert("UTC")
    rows.append({"周五": friday.date(), "收盘时刻": close_at, "开盘时刻": open_at,
                 "收盘价": minute["close"].get(close_at - pd.Timedelta("1min")), "开盘价": minute["open"].get(open_at)})
weekend = pd.DataFrame(rows).dropna()
weekend["缺口"] = weekend["开盘价"] / weekend["收盘价"] - 1
print(f"{len(weekend)} 个周末，其中周五休市、改用周四收盘的 {(pd.to_datetime(weekend['收盘时刻']).dt.tz_convert(CT).dt.dayofweek != 4).sum()} 个；"
      f"缺口绝对值中位数 {weekend['缺口'].abs().median():.2%}，超过 1% 的 {(weekend['缺口'].abs() > 0.01).mean():.1%}")
print(weekend.tail(3).to_string(index=False))
def hours_to(start, level, from_above):
    hit = X.first_reach(minute["high"], minute["low"], start, level, from_above)
    return (hit - start) / pd.Timedelta("1h") if pd.notna(hit) else np.nan
weekend["回补小时"] = [hours_to(r["开盘时刻"], r["收盘价"], r["缺口"] > 0) for _, r in weekend.iterrows()]
weekend["对照小时"] = [hours_to(r["开盘时刻"], r["开盘价"] ** 2 / r["收盘价"], r["缺口"] < 0) for _, r in weekend.iterrows()]
def cme_summary(part):
    return pd.Series({"个数": len(part), "24 小时内": (part["回补小时"] <= 24).mean(), "1 周内": (part["回补小时"] <= 168).mean(),
                      "30 天内": (part["回补小时"] <= 720).mean(), "到 8 月底": part["回补小时"].notna().mean(),
                      "对照 24 小时": (part["对照小时"] <= 24).mean(), "对照 1 周": (part["对照小时"] <= 168).mean(),
                      "对照 30 天": (part["对照小时"] <= 720).mean(), "对照 到 8 月底": part["对照小时"].notna().mean()})
size = pd.cut(weekend["缺口"].abs(), [0, 0.005, 0.01, 0.02, 0.05, 1], labels=["0~0.5%", "0.5%~1%", "1%~2%", "2%~5%", "5% 以上"])
print(weekend.groupby(size, observed=False).apply(cme_summary).round(3).to_string())
print(cme_summary(weekend).round(3).to_frame("全部").T.to_string())
print("到 2026-08-31 还没有回补的：")
print(weekend[weekend["回补小时"].isna()][["周五", "收盘价", "开盘价", "缺口"]].round(4).to_string(index=False))
