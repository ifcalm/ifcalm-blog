"""第 7 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
import math

import numpy as np
import pandas as pd
from talab import bars as B, data as D, timeframes as T

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
cols = ["open", "high", "low", "close"]

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
D.download_binance_klines("BTCUSDT", "4h", "2017-08", "2026-08")     # 官方的 4 小时线和周线，只用来核对
D.download_binance_klines("BTCUSDT", "1w", "2017-08", "2026-06")     # 周线的月度文件目前只发布到 2026-06
official_4h = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/4h/*.zip")))
official_1w = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1w/*.zip")))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
print("官方 4 小时线", len(official_4h), "根，官方周线", len(official_1w), "根，最后一周", official_1w.index[-1].date())

print("===== 片段 2：周线从哪天开始 =====")
default = day[cols + ["volume"]].resample("W").agg(B.OHLCV)
weekly = B.resample_ohlcv(day, "W-MON")
print("pandas 默认 \"W\"：", [t.strftime("%Y-%m-%d %a") for t in default.index[:3]])
print("\"W-MON\" + 左闭左标：", [t.strftime("%Y-%m-%d %a") for t in weekly.index[:3]])
print("Binance 官方周线：", [t.strftime("%Y-%m-%d %a") for t in official_1w.index[:3]])
print(pd.concat([official_1w[cols].head(2), default[cols].head(2)], keys=["官方", "默认 W"]))
both = official_1w[cols].join(weekly[cols], rsuffix="_合成", how="inner")
wrong = pd.DataFrame({c: (both[c] - both[c + "_合成"]).abs() > 1e-8 for c in cols}).any(axis=1)
print("W-MON 合成的周线和官方周线：共同的", len(both), "周里对不上", wrong.sum(), "周")
print("floor(\"7D\") 的结果：", [t.strftime("%Y-%m-%d %a") for t in day.index[5:9].floor("7D")])

print("===== 片段 3：1 分钟线合成 4 小时线 =====")
rebuilt = B.resample_ohlcv(minute, "4h", traded_only=True)
both = official_4h[cols].join(rebuilt[cols], rsuffix="_合成", how="outer")
wrong = pd.DataFrame({c: (both[c] - both[c + "_合成"]).abs() > 1e-8 for c in cols}).any(axis=1)
print("官方", len(official_4h), "根，合成", len(rebuilt), "根，对不上", wrong.sum(), "根：", wrong.groupby(both.index.year).sum()[lambda s: s > 0].to_dict())
offset = ((both.index >= "2017-12-04") & (both.index < "2017-12-19")) | ((both.index >= "2018-02-09") & (both.index < "2018-02-11"))
print("其中落在两段时间戳偏移时期的", (wrong & offset).sum(), "根；其余", [t.strftime("%Y-%m-%d %H:%M") for t in both.index[wrong & ~offset]])
four = rebuilt

print("===== 片段 4：美股的一周有几天 =====")
days_per_week = spy["close"].groupby(pd.Grouper(freq="W-MON", label="left", closed="left")).count()
print(days_per_week.value_counts().sort_index().to_dict())
print(days_per_week[days_per_week < 5].tail(3))

print("===== 片段 5：一根周阳线里装着什么 =====")
weekly["green"] = weekly["close"] > weekly["open"]
week_of = pd.Grouper(freq="W-MON", label="left", closed="left")
red_days = (day["close"] < day["open"]).groupby(week_of).sum()
n_days = day["close"].groupby(week_of).count()
full = weekly[n_days == 7]
g = full[full["green"]]
print(f"完整的周阳线 {len(g)} 根：平均含阴线日 {red_days[g.index].mean():.2f} 天；"
      f"至少 3 天阴线 {(red_days[g.index] >= 3).mean():.1%}；一天阴线都没有 {(red_days[g.index] == 0).mean():.1%}")
red_4h = (four["close"] < four["open"]).groupby(week_of).mean()
print(f"周阳线里 4 小时阴线的比例 {red_4h[g.index].mean():.1%}；周阴线里 {red_4h[full[~full['green']].index].mean():.1%}")
dip = g["low"] / g["open"] - 1
print(f"周阳线从开盘向下最深跌了多少：中位数 {dip.median():.2%}，超过 3% 的 {(dip < -0.03).mean():.1%}")

print("===== 片段 6：周线在涨，4 小时线在跌，有多常见 =====")
weekly["sma20"] = weekly["close"].rolling(20).mean()
weekly["up"] = (weekly["close"] > weekly["sma20"]).where(weekly["sma20"].notna())
four = four.copy()
four["sma20"] = four["close"].rolling(20).mean()
four["wk_up"] = T.align_higher(four.index, "4h", weekly[["up"]], "7D")["up"]
known = four.dropna(subset=["sma20", "wk_up"])
table = pd.crosstab(known["wk_up"].astype(bool), known["close"] > known["sma20"], normalize="index")
table.index, table.columns = ["周线在 20 周均线下", "周线在 20 周均线上"], ["4 小时线在 20 根均线下", "4 小时线在 20 根均线上"]
print(table.round(3))

print("===== 片段 7：不同周期的尺度 =====")
for name, df, periods in [("4 小时", four, 6 * 365), ("日线", day, 365), ("周线", weekly, 52)]:
    r = df["close"].pct_change().dropna()
    print(f"{name}：收益率标准差 {r.std():.2%}，年化 {r.std() * math.sqrt(periods):.1%}")

print("===== 片段 8：决策点 =====")
t = pd.Timestamp("2025-10-30 12:00", tz="UTC")
four["low_7d"] = four["low"].rolling(42).min().shift(1)             # 前 42 根（7 天）的最低价
print(four.loc["2025-10-30 04:00":"2025-10-30 12:00", cols + ["low_7d"]].round(2))
print(weekly.loc["2025-10-13":"2025-11-03", cols + ["sma20"]].round(2))

print("===== 片段 9：两种对齐 =====")
def align_wrong(lower_index, higher):
    """错误的对齐：用大 K 线的开始时间去匹配，会用到还没收盘的大 K 线。"""
    return higher.reindex(lower_index, method="ffill")
right = T.align_higher(four.index, "4h", weekly[cols + ["sma20", "up"]], "7D")
bad = align_wrong(four.index, weekly[cols + ["sma20", "up"]])
for name, view in [("正确对齐", right), ("错误对齐", bad)]:
    row = view.loc[t]
    print(f"{name}：周线收盘 {row['close']:,.2f}，20 周均线 {row['sma20']:,.2f}，在均线上方：{bool(row['up'])}")
dev = T.developing(four, "W-MON")
print("正在形成的周线：", dev.loc[t, cols].round(2).to_dict())

print("===== 片段 10：周线向上时，4 小时破位之后发生了什么 =====")
four["break"] = four["close"] < four["low_7d"]
four["event"] = four["break"] & (four["break"].rolling(42).sum().shift(1) == 0)   # 7 天内第一次破位
c = four["close"]
for label, n in [("7 天", 42), ("30 天", 180)]:
    four[label] = c.shift(-n) / c - 1
rows = []
for trend, name in [(True, "周线在均线上"), (False, "周线在均线下")]:
    base = four[four["wk_up"] == trend]
    ev = base[base["event"]]
    for label in ["7 天", "30 天"]:
        e, b = ev[label].dropna(), base[label].dropna()
        t_stat = (e.mean() - b.mean()) / math.sqrt(e.var() / len(e) + b.var() / len(b))
        rows.append({"周线": name, "之后": label, "破位次数": len(e), "破位后平均": e.mean(), "破位后上涨比例": (e > 0).mean(),
                     "所有时刻平均": b.mean(), "所有时刻上涨比例": (b > 0).mean(), "t": t_stat})
print(pd.DataFrame(rows).round(4).to_string(index=False))
depth = (four["low_7d"] - four["close"]) / four["close"]
print(f"破位时收盘价在 7 天最低价下方多少：中位数 {depth[four['event']].median():.2%}")

print("===== 片段 11：揭晓 =====")
for label in ["7 天", "30 天"]:
    print(f"{label}后：{four.loc[t, label]:+.2%}")
print("之后的最低价：", day.loc["2025-10-31":, "low"].min(), day.loc["2025-10-31":, "low"].idxmin().date())

print("===== 片段 12：简化的三重滤网 =====")
def triple_screen(daily, weekly_bars, intraday=None, hold=10):
    wk = weekly_bars.copy()
    wk["sma20"] = wk["close"].rolling(20).mean()
    wk["up"] = (wk["close"] > wk["sma20"]).where(wk["sma20"].notna())
    tide = T.align_higher(daily.index, "1D", wk[["up"]], "7D")["up"]           # 第一层：周线方向
    wave = daily["close"] <= daily["close"].rolling(5).min()                   # 第二层：日线回调到 5 天最低收盘
    trades, busy_until = [], -1
    for i in range(5, len(daily) - hold - 1):
        if not wave.iloc[i] or pd.isna(tide.iloc[i]) or i <= busy_until:
            continue
        trigger = daily["high"].iloc[i]                                        # 第三层：第二天突破信号日最高价才买入
        next_day = daily.index[i + 1]
        if intraday is not None:
            bars = intraday.loc[next_day:next_day + pd.Timedelta("1D") - pd.Timedelta("1s")]
            hit = bars[bars["high"] >= trigger]
            if hit.empty:
                continue
            fill = max(trigger, hit["open"].iloc[0])                            # 跳空越过触发价时，只能按开盘价成交
        else:
            if daily["high"].iloc[i + 1] < trigger:
                continue
            fill = max(trigger, daily["open"].iloc[i + 1])
        exit_price = daily["close"].iloc[i + 1 + hold]
        trades.append({"信号日": daily.index[i], "周线向上": bool(tide.iloc[i]), "收益": exit_price / fill - 1})
        busy_until = i + 1 + hold
    return pd.DataFrame(trades)
for name, daily, intraday in [("BTC", day, four), ("SPY", spy.assign(volume=spy["volume"].fillna(0)), None)]:
    trades = triple_screen(daily, B.resample_ohlcv(daily, "W-MON"), intraday)
    base = (daily["close"].shift(-10) / daily["close"] - 1).dropna()
    print(f"{name}：任意一天买入持有 10 天，平均 {base.mean():+.2%}，上涨比例 {(base > 0).mean():.1%}")
    for label, part in [("全部信号", trades), ("周线向上", trades[trades["周线向上"]]), ("周线向下", trades[~trades["周线向上"]])]:
        r = part["收益"]
        print(f"   {label}：{len(r):3d} 笔，平均 {r.mean():+.2%}，中位数 {r.median():+.2%}，上涨比例 {(r > 0).mean():.1%}")
    up, down = trades.loc[trades["周线向上"], "收益"], trades.loc[~trades["周线向上"], "收益"]
    print(f"   周线向上 vs 向下，平均收益差异的 t = {(up.mean() - down.mean()) / math.sqrt(up.var() / len(up) + down.var() / len(down)):.2f}")

print("===== 片段 13：前视偏差的回测 =====")
def backtest(position, returns, periods_per_year):
    """position 是每根 K 线收盘时决定的仓位（1 持有，0 空仓），从下一根 K 线开始生效。"""
    equity = (1 + position.shift(1).fillna(0) * returns.fillna(0)).cumprod()
    growth = equity.iloc[-1]
    return growth, growth ** (periods_per_year / len(returns)) - 1
weekly["green"] = weekly["close"] > weekly["open"]
default["green"] = default["close"] > default["open"]
r4 = four["close"].pct_change()
tests = {
    "错误对齐（周一标签）": align_wrong(four.index, weekly[["green"]])["green"],
    "错误对齐（pandas 默认 W，周日标签）": align_wrong(four.index, default[["green"]])["green"],
    "正确对齐（上一根已收盘的周线）": T.align_higher(four.index, "4h", weekly[["green"]], "7D")["green"],
    "正在形成的周线": T.developing(four, "W-MON").eval("close > open"),
}
correct = tests["正确对齐（上一根已收盘的周线）"].astype(float).fillna(0)
print("规则：这一周是阳线就持有 BTC，4 小时线")
for name, signal in tests.items():
    pos = signal.astype(float).fillna(0)
    growth, cagr = backtest(pos, r4, 6 * 365)
    print(f"   {name}：×{growth:,.2f}（年化 {cagr:.1%}），和正确对齐不同的 K 线 {int((pos != correct).sum())} 根")
print(f"   一直持有：×{four['close'].iloc[-1] / four['close'].iloc[0]:.2f}")

rd = day["close"].pct_change()
print("规则：周线收盘在 20 周均线上方就持有，日线")
for name, market, bars, ppy in [("BTC", day, weekly, 365), ("SPY", spy, B.resample_ohlcv(spy.assign(volume=spy["volume"].fillna(0)), "W-MON"), 252)]:
    bars = bars.copy()
    bars["sma20"] = bars["close"].rolling(20).mean()
    bars["up"] = (bars["close"] > bars["sma20"]).where(bars["sma20"].notna())
    ret = market["close"].pct_change()
    good = T.align_higher(market.index, "1D", bars[["up"]], "7D")["up"].astype(float).fillna(0)
    leak = align_wrong(market.index, bars[["up"]])["up"].astype(float).fillna(0)
    g1, c1 = backtest(leak, ret, ppy)
    g2, c2 = backtest(good, ret, ppy)
    print(f"   {name}：错误对齐 ×{g1:.2f}（年化 {c1:.1%}）  正确对齐 ×{g2:.2f}（年化 {c2:.1%}）  "
          f"不同的日子 {int((good != leak).sum())} 天  一直持有 ×{market['close'].iloc[-1] / market['close'].iloc[0]:.2f}")
