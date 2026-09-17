"""第 10 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, structure as X

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
cols = ["open", "high", "low", "close"]

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
months = [str(m) for m in pd.period_range("2020-01", "2026-08", freq="M")]     # U 本位永续合约的月度文件从 2020-01 开始
with ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(lambda m: D.download_binance_klines("BTCUSDT", "1d", m, m, market="um"), months))
perp = D.load_binance_klines(glob.glob("data/binance/um/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
spy.loc[pd.Timestamp("2026-04-17"), "volume"] = np.nan                      # 第 3 篇：这一天的成交量 9,999,999 是错误值
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
markets = {"BTC": day, "SPY": spy, "AAPL": aapl}
print(f"永续合约日线 {len(perp)} 根：{perp.index[0].date()} 至 {perp.index[-1].date()}")

print("===== 片段 2：决策点 =====")
hour = B.resample_ohlcv(minute.loc["2025-11-01":"2025-12-17"], "1h")
hour["均价"] = hour["quote_volume"] / hour["volume"]
hour["vwap"] = I.vwap(hour["均价"], hour["volume"], hour.index.floor("1D"))
hour["相对 24 小时"] = I.relative_volume(hour["volume"], 24)
hour["相对同一小时"] = I.relative_volume(hour["volume"], 20, by=hour.index.hour)
print(hour.loc["2025-12-17 12:00":"2025-12-17 15:00", cols + ["volume", "vwap", "相对 24 小时", "相对同一小时"]].round(2))

print("===== 片段 3：成交量的单位 =====")
yearly = day.groupby(day.index.year)[["volume", "quote_volume"]].mean()
yearly.columns = ["平均每天成交 BTC", "平均每天成交 USDT（亿）"]
yearly["平均每天成交 USDT（亿）"] /= 1e8
print(yearly.round({"平均每天成交 BTC": 0, "平均每天成交 USDT（亿）": 1}).to_string())

print("===== 片段 4：零手续费活动 =====")
v = day["volume"]
for label, before, after in [("2022-07-08 开始", ("2022-06-08", "2022-07-07"), ("2022-07-08", "2022-08-07")),
                             ("2023-03-22 结束", ("2023-02-20", "2023-03-21"), ("2023-03-22", "2023-04-21"))]:
    b, a = v[before[0]:before[1]].mean(), v[after[0]:after[1]].mean()
    print(f"{label}：之前 30 天平均 {b:,.0f} BTC，之后 30 天平均 {a:,.0f} BTC，变化 {a / b - 1:+.0%}")

print("===== 片段 5：现货和永续合约 =====")
both = pd.DataFrame({"现货": day["quote_volume"], "永续合约": perp["quote_volume"]}).dropna()
table = both.groupby(both.index.year).mean() / 1e8
table["合约 ÷ 现货"] = table["永续合约"] / table["现货"]
print(table.round(1).to_string())

print("===== 片段 6：一天之内的成交量 =====")
hour_all = B.resample_ohlcv(minute, "1h")
share = hour_all["volume"].groupby([hour_all.index.year, hour_all.index.hour]).sum()
share = share / share.groupby(level=0).transform("sum")
print((share.unstack(0)[[2019, 2022, 2025]] * 100).round(2).T.to_string())
print({year: f"{share[year].loc[13:15].sum():.1%}" for year in [2019, 2022, 2025]})

print("===== 片段 7：成交量和涨跌幅 =====")
rng = np.random.default_rng(0)
def label_test(values, flag, n=2000):
    """flag 为真的组减去其余的平均值；把标签随机打乱 n 次，看差距不小于实际的比例。"""
    x, f = np.asarray(values, float), np.asarray(flag, bool)
    observed = x[f].mean() - x[~f].mean()
    sims = np.array([x[p].mean() - x[~p].mean() for p in (rng.permutation(f) for _ in range(n))])
    return observed, (np.abs(sims) >= abs(observed)).mean()
for name, df in markets.items():
    r = np.log(df["close"]).diff()
    rv = I.relative_volume(df["volume"], 20)
    z = (r / r.rolling(20).std().shift(1)).abs()
    t = pd.DataFrame({"r": r, "rv": rv, "z": z, "次日": r.shift(-1), "5 天": np.log(df["close"].shift(-5) / df["close"])}).dropna()
    print(f"{name}：相对成交量和「涨跌幅是几倍标准差」的秩相关 {t['rv'].rank().corr(t['z'].rank()):.2f}")
    t["组合"] = np.where(t["r"] > 0, "涨", "跌") + np.where(t["rv"] > 1, "放量", "缩量")
    print(t.groupby("组合").agg(天数=("次日", "size"), 次日平均=("次日", "mean"), 五天平均=("5 天", "mean"),
                              五天上涨比例=("5 天", lambda s: (s > 0).mean())).round(4).to_string())
    for side in ["涨", "跌"]:
        part = t[t["组合"].str.startswith(side)]
        gap, p = label_test(part["5 天"], part["rv"] > 1)
        print(f"   {side}的日子：放量减缩量，之后 5 天 {gap:+.2%}，打乱标签后差距不小于它的比例 {p:.1%}")

print("===== 片段 8：放量突破、缩量回调、天量 =====")
for name, df in markets.items():
    c, rv = df["close"], I.relative_volume(df["volume"], 20)
    high20 = df["high"].rolling(20).max().shift(1)
    breakout = (c > high20) & (c.shift(1) <= high20.shift(1))
    fell_back = pd.concat([c.shift(-k) for k in range(1, 11)], axis=1).min(axis=1) < high20
    t = pd.DataFrame({"rv": rv, "20 天": c.shift(-20) / c - 1, "10 天内跌回": fell_back})[breakout].dropna()
    group = pd.cut(t["rv"], [0, 1, 2, np.inf], labels=["1 倍以下", "1~2 倍", "2 倍以上"])
    print(f"{name} 收盘突破 20 日最高价 {len(t)} 次（任意一天之后 20 天平均 {(c.shift(-20) / c - 1).mean():+.2%}）：")
    print(t.groupby(group, observed=False).agg(次数=("20 天", "size"), 之后20天平均=("20 天", "mean"),
                                              上涨比例=("20 天", lambda s: (s > 0).mean()), 跌回比例=("10 天内跌回", "mean")).round(3).to_string())
    gap, p = label_test(t["10 天内跌回"].astype(float), t["rv"] > 2)
    print(f"   2 倍以上放量减其余，跌回比例 {gap:+.1%}，打乱标签后 {p:.1%}")
    down3 = (c < c.shift(1)) & (c.shift(1) < c.shift(2)) & (c.shift(2) < c.shift(3))
    pullback_volume = df["volume"].rolling(3).mean() / df["volume"].rolling(20).mean().shift(3)
    t = pd.DataFrame({"量": pullback_volume, "10 天": c.shift(-10) / c - 1})[down3 & (c > c.rolling(50).mean())].dropna()
    gap, p = label_test(t["10 天"], t["量"] < 1)
    print(f"   50 日均线上方连跌 3 天 {len(t)} 次：缩量 {(t['量'] < 1).sum()} 次，之后 10 天平均 {t.loc[t['量'] < 1, '10 天'].mean():+.2%}；"
          f"放量 {(t['量'] >= 1).sum()} 次，{t.loc[t['量'] >= 1, '10 天'].mean():+.2%}；缩量减放量 {gap:+.2%}，打乱标签后 {p:.1%}")
for name in ["BTC", "AAPL"]:
    df = markets[name]
    c, vol = df["close"], df["volume"]
    record = vol > vol.rolling(250).max().shift(1)
    rows = []
    for t in df.index[record & vol.rolling(250).max().shift(1).notna()]:
        i = df.index.get_loc(t)
        if i + 60 >= len(df):
            continue
        later = df.iloc[i + 1:i + 61]
        third_friday = t.dayofweek == 4 and 15 <= t.day <= 21 and t.month in (3, 6, 9, 12)
        rows.append({"日期": t.date(), "当天涨跌": c.iloc[i] / c.iloc[i - 1] - 1, "当天最高价是之后 60 天最高": df["high"].iloc[i] >= later["high"].max(),
                     "当天最低价是之后 60 天最低": df["low"].iloc[i] <= later["low"].min(), "之后 60 天": c.iloc[i + 60] / c.iloc[i] - 1,
                     "季度第三个周五": third_friday})
    print(f"{name}：成交量创 250 天新高的日子")
    print(pd.DataFrame(rows).to_string(index=False, formatters={"当天涨跌": "{:+.1%}".format, "之后 60 天": "{:+.1%}".format}))

print("===== 片段 9：VWAP 算得有多准 =====")
m = minute[minute["volume"] > 0]
session = m.index.floor("1D")
exact = I.vwap(m["quote_volume"] / m["volume"], m["volume"], session)
approx = I.vwap(I.typical_price(m["high"], m["low"], m["close"]), m["volume"], session)
end = exact.groupby(session).tail(1).index
error = (approx[end] / exact[end] - 1).abs()
print(f"1 分钟线的典型价格算出的全天 VWAP：误差中位数 {error.median():.4%}，99% 分位 {error.quantile(0.99):.4%}，最大 {error.max():.4%}")
daily_exact = day["quote_volume"] / day["volume"]
error = (I.typical_price(day["high"], day["low"], day["close"]) / daily_exact - 1).abs()
print(f"只用日线的 (最高 + 最低 + 收盘) ÷ 3：误差中位数 {error.median():.2%}，90% 分位 {error.quantile(0.9):.2%}，"
      f"最大 {error.max():.2%}（{error.idxmax().date()}）")

print("===== 片段 10：揭晓 =====")
after = B.resample_ohlcv(minute.loc["2025-12-17 16:00":"2025-12-24 16:00"], "1h")
decision_price = hour.loc["2025-12-17 15:00", "close"]
rest = after.loc[:"2025-12-17 23:00"]
print(f"决策价 {decision_price:,.2f}；当天收盘 {rest['close'].iloc[-1]:,.2f}（{rest['close'].iloc[-1] / decision_price - 1:+.2%}），"
      f"当天剩余时间最低 {rest['low'].min():,.2f}，最高 {rest['high'].max():,.2f}")
for label, t in [("24 小时后", "2025-12-18 15:00"), ("3 天后", "2025-12-20 15:00"), ("7 天后", "2025-12-24 15:00")]:
    print(f"{label}：{after.loc[t, 'close'] / decision_price - 1:+.2%}")
print(f"12 月 18 日全天 VWAP {(lambda d: d['quote_volume'].sum() / d['volume'].sum())(after.loc['2025-12-18']):,.2f}")

print("===== 片段 11：放量跌破 VWAP 之后 =====")
h = hour_all.copy()
h["均价"] = h["quote_volume"] / h["volume"]
h = h[h["volume"] > 0]
h["vwap"] = I.vwap(h["均价"], h["volume"], h.index.floor("1D"))
h["相对 24 小时"] = I.relative_volume(h["volume"], 24)
h["相对同一小时"] = I.relative_volume(h["volume"], 20, by=h.index.hour)
h["到收盘"] = np.log(h["close"].groupby(h.index.floor("1D")).transform("last") / h["close"])
h["24 小时"] = np.log(h["close"].shift(-24) / h["close"])
below = h["close"] < h["vwap"]
cross = below & ~below.shift(1, fill_value=False) & (h.index.hour >= 4) & (h.index.hour <= 20)
events = h[cross].dropna(subset=["相对 24 小时", "相对同一小时", "24 小时"])
print(f"收盘从 VWAP 上方跌到下方的 1 小时线（4:00 到 20:00 之间）：{len(events)} 次")
for col in ["相对 24 小时", "相对同一小时"]:
    group = pd.cut(events[col], [0, 1, 2, 3, np.inf], labels=["1 倍以下", "1~2 倍", "2~3 倍", "3 倍以上"])
    print(f"按{col}分组：")
    print(events.groupby(group, observed=False).agg(次数=("到收盘", "size"), 到当天收盘平均=("到收盘", "mean"),
                                                   之后24小时平均=("24 小时", "mean"), 之后24小时下跌比例=("24 小时", lambda s: (s < 0).mean())).round(4).to_string())
    strong = events[events[col] >= 2]
    print(f"   {col} 2 倍以上的事件里，发生在 UTC 13:00~15:00 的占 {strong.index.hour.isin([13, 14, 15]).mean():.1%}"
          f"（全部事件里是 {events.index.hour.isin([13, 14, 15]).mean():.1%}）")
gap, p = label_test(events["24 小时"], events["相对同一小时"] >= 2)
print(f"同一小时 2 倍以上放量减其余，之后 24 小时 {gap:+.2%}，打乱标签后 {p:.1%}")

print("===== 片段 12：锚定 VWAP =====")
daily_price = day["quote_volume"] / day["volume"]
anchors = {"2025-10-06 历史最高": "2025-10-06", "2026-02-06 暴跌低点": "2026-02-06", "2026-07-01 熊市低点": "2026-07-01"}
lines = pd.DataFrame({name: I.anchored_vwap(daily_price, day["volume"], pd.Timestamp(t, tz="UTC")) for name, t in anchors.items()})
print(lines.loc[["2026-06-03", "2026-08-18", "2026-08-31"]].round(2).to_string())
print("收盘价：", day["close"].loc[["2026-06-03", "2026-08-18", "2026-08-31"]].round(2).tolist())

def line_tests(df, price, weighted, kind, distance=1.5, zone=0.25, horizon=250):
    """从每个摆动点开始画一条线（VWAP 或不加权的平均价），像第 9 篇一样统计回到线附近之后守住的比例。"""
    a = X.wilder_smooth(X.true_range(df["high"], df["low"], df["close"]), 14).to_numpy()
    p, v = price.to_numpy(float), df["volume"].to_numpy(float)
    h_, l_, c_ = (df[k].to_numpy(float) for k in ["high", "low", "close"])
    sw = X.fractals(df["high"], df["low"], 5, 5)
    pos = {t: i for i, t in enumerate(df.index)}
    results = []
    for s in sw[sw["kind"] == kind].itertuples():
        start, end, side = pos[s.time], min(len(c_), pos[s.time] + horizon), (1 if kind == -1 else -1)
        seg_p, seg_v = p[start:end], v[start:end]
        line = np.cumsum(seg_p * seg_v) / np.cumsum(seg_v) if weighted else np.cumsum(seg_p) / np.arange(1, len(seg_p) + 1)
        j, armed = pos[s.confirmed_at] + 1, False                 # 摆动点确认之后才开始用这条线
        while j < end:
            unit, away = a[j - 1], (c_[j] - line[j - start]) * side
            if not armed:
                if away >= distance * unit:
                    armed = True
                elif away <= -distance * unit:
                    break
                j += 1
                continue
            if not (l_[j] <= line[j - start] + zone * unit if side == 1 else h_[j] >= line[j - start] - zone * unit):
                j += 1
                continue
            k, outcome = j, None
            while k < end:
                away = (c_[k] - line[k - start]) * side
                if abs(away) >= distance * unit:
                    outcome = "held" if away > 0 else "broken"
                    break
                k += 1
            if outcome is None:
                break
            results.append(outcome == "held")
            if outcome == "broken":
                break
            j = k + 1
    return len(results), np.mean(results)
for kind, role in [(-1, "从摆动低点开始（支撑）"), (1, "从摆动高点开始（阻力）")]:
    for weighted, name in [(True, "锚定 VWAP"), (False, "不加权的平均价")]:
        n, rate = line_tests(day, daily_price, weighted, kind)
        print(f"{role} {name}：测试 {n} 次，守住 {rate:.1%}")

print("===== 片段 13：Volume Profile =====")
segment = minute.loc["2026-02-06":"2026-05-31"]
segment = segment[segment["volume"] > 0]
profile = I.volume_profile(segment["quote_volume"] / segment["volume"], segment["volume"], 250)
area = I.value_area(profile, 0.7)
print(f"2026-02-06 至 2026-05-31，每 250 美元一格，共 {len(profile)} 格")
print({k: f"{v:,.2f}" for k, v in area.items()})
print(profile.sort_values(ascending=False).head(5).round(0).to_string())
print(f"这段时间成交量在价值区间里的比例 {profile.loc[area['val']:area['vah'] - 1].sum() / profile.sum():.1%}")

print("===== 片段 14：前一天的 POC =====")
m = minute[minute["volume"] > 0]
avg = m["quote_volume"] / m["volume"]
width = avg.groupby(m.index.floor("1D")).transform("first") * 0.001            # 每天的格子宽度 = 当天第一笔均价的 0.1%
poc = {}
for d, idx in m.groupby(m.index.floor("1D")).groups.items():
    poc[d] = I.value_area(I.volume_profile(avg[idx], m["volume"][idx], width[idx[0]]))["poc"]
poc = pd.Series(poc).reindex(day.index)
references = {"前一天 POC": poc.shift(1), "前一天 VWAP": daily_price.shift(1), "前一天最高最低价中点": ((day["high"] + day["low"]) / 2).shift(1)}
for name, level in references.items():
    distance = np.log(day["open"] / level)
    mirror = day["open"] ** 2 / level
    hit = np.where(distance > 0, day["low"] <= level, day["high"] >= level)
    mirror_hit = np.where(distance > 0, day["high"] >= mirror, day["low"] <= mirror)
    t = pd.DataFrame({"距离": distance.abs(), "碰到": hit, "对照": mirror_hit}).dropna()
    t = t[t["距离"] > 0.005]
    group = pd.cut(t["距离"], [0.005, 0.01, 0.02, 0.05, 1], labels=["0.5%~1%", "1%~2%", "2%~5%", "5% 以上"])
    summary = t.groupby(group, observed=False).agg(天数=("碰到", "size"), 当天碰到=("碰到", "mean"), 对照=("对照", "mean"))
    only_level, only_mirror = int((t["碰到"] & ~t["对照"]).sum()), int((~t["碰到"] & t["对照"]).sum())
    z = (only_level - only_mirror) / np.sqrt(only_level + only_mirror)
    print(f"{name}（开盘价离它 0.5% 以上）：只碰到它 {only_level} 天，只碰到对照 {only_mirror} 天，z = {z:.2f}")
    print(summary.round(3).to_string())
