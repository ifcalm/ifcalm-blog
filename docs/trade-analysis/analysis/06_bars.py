"""第 6 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
import math

import numpy as np
import pandas as pd
from talab import bars as B, data as D

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
print("BTC 日线", len(day), "根，1 分钟线", len(minute), "根")

print("===== 片段 2：两根 K 线 =====")
A, Bday = "2026-07-01", "2019-07-09"
for name, t in [("A", A), ("B", Bday)]:
    bar = day.loc[t]
    scaled = (bar[["open", "high", "low", "close"]] / bar["open"] * 100).round(2)
    print(name, t, bar[["open", "high", "low", "close"]].tolist(), "→ 开盘记为 100：", scaled.tolist())

print("===== 片段 3：手动合成一根 5 分钟 K 线 =====")
five = minute.loc["2026-07-01 22:20":"2026-07-01 22:24", ["open", "high", "low", "close", "volume"]]
print(five)
print(B.resample_ohlcv(five, "5min"))

print("===== 片段 4：用 1 分钟线合成日线，和官方日线对比 =====")
cols = ["open", "high", "low", "close"]
for traded_only in [False, True]:
    rebuilt = B.resample_ohlcv(minute, "1D", traded_only=traded_only)
    both = day[cols].join(rebuilt[cols], rsuffix="_合成")
    wrong = pd.DataFrame({c: (both[c] - both[c + "_合成"]).abs() > 1e-8 for c in cols})
    bad = wrong.any(axis=1)
    print(f"traded_only={traded_only}：价格对不上的日子 {bad.sum()} 天，按字段 {wrong.sum().to_dict()}")
    print("   按年：", bad.groupby(both.index.year).sum()[lambda s: s > 0].to_dict())
print(minute.loc["2017-08-20 00:04":"2017-08-20 00:07", ["open", "high", "low", "close", "volume"]])
print("官方日线 2017-08-20 开盘：", day.loc["2017-08-20", "open"])
bad_days = both.index[bad]
print("剩下的日子：", bad_days[0].date(), "至", bad_days[13].date(), "共 14 天；", [d.date() for d in bad_days[14:]])
rebuilt = B.resample_ohlcv(minute, "1D", traded_only=True)
vol_diff = (day["volume"] / rebuilt["volume"] - 1).abs()
print(f"成交量相差超过百万分之一的日子 {(vol_diff > 1e-6).sum()} 天，其中相差的中位数 {vol_diff[vol_diff > 1e-6].median():.4%}，"
      f"最大 {vol_diff.max():.2%}（{vol_diff.idxmax().date()}）")

print("===== 片段 5：实体和影线 =====")
for name, t in [("A", A), ("B", Bday)]:
    print(name, B.anatomy(day.loc[[t]]).round(4).iloc[0].to_dict())
rows = {}
for k, df in {"SPY": spy, "AAPL": aapl, "BTC": day}.items():
    a = B.anatomy(df)
    rows[k] = {"实体占比中位数": a["body_ratio"].median(), "十字星(实体<10%)": (a["body_ratio"] < 0.1).mean(),
               "光头光脚(实体>90%)": (a["body_ratio"] > 0.9).mean(), "收盘位置中位数": a["clv"].median()}
print(pd.DataFrame(rows).round(3))

print("===== 片段 6：K 线颜色和当天涨跌 =====")
for k, df in {"SPY": spy, "AAPL": aapl, "BTC": day}.items():
    ret = df["close"].pct_change()
    green_down = ((df["close"] > df["open"]) & (ret < 0)).sum()
    red_up = ((df["close"] < df["open"]) & (ret > 0)).sum()
    gap = df["open"] / df["close"].shift() - 1
    print(f"{k:4s} 阳线但下跌 {green_down} 天，阴线但上涨 {red_up} 天，占 {(green_down + red_up) / (len(df) - 1):.1%}；"
          f"跳空超过 0.5% 的日子 {(gap.abs() > 0.005).mean():.1%}")
print(spy.loc["2025-04-04":"2025-04-07"])

print("===== 片段 7：隔夜和日内 =====")
for k, df in {"SPY": spy, "AAPL": aapl, "BTC": day}.items():
    overnight = np.log(df["open"] / df["close"].shift()).dropna()        # 昨天收盘 → 今天开盘
    intraday = np.log(df["close"] / df["open"]).iloc[1:]                 # 今天开盘 → 今天收盘
    print(f"{k:4s} 隔夜累计 ×{math.exp(overnight.sum()):.2f}   日内累计 ×{math.exp(intraday.sum()):.2f}   "
          f"合计 ×{math.exp(overnight.sum() + intraday.sum()):.2f}")

print("===== 片段 8：最高价和最低价谁先出现 =====")
ex = B.intraday_extremes(minute)
print(ex.loc[[A, Bday]])
d = day.join(ex)
up, down = d["close"] > d["open"], d["close"] < d["open"]
print(f"全部日子：最高价先出现 {d['high_first'].mean():.1%}")
print(f"阳线：最高价先出现 {d.loc[up, 'high_first'].mean():.1%}，最低价先出现 {1 - d.loc[up, 'high_first'].mean():.1%}")
print(f"阴线：最高价先出现 {d.loc[down, 'high_first'].mean():.1%}")

print("===== 片段 9：最高价出现在哪个小时 =====")
theory = [(2 / math.pi) * (math.asin(math.sqrt((h + 1) / 24)) - math.asin(math.sqrt(h / 24))) for h in range(24)]
hours = pd.DataFrame({
    "最高价": ex["time_of_high"].dt.hour.value_counts(normalize=True).sort_index(),
    "最低价": ex["time_of_low"].dt.hour.value_counts(normalize=True).sort_index(),
    "随机游走理论": theory,
})
print((hours * 100).round(1).T.to_string())
share = minute["quote_volume"].groupby(minute.index.hour).sum()
print("成交额占比%：", (share / share.sum() * 100).round(1).tolist())

print("===== 片段 10：止损和止盈都在一根日线里 =====")
for k in [0.02, 0.03, 0.05]:
    truth = B.first_touch(minute, k, k)
    hit_up = day["high"] >= day["open"] * (1 + k)
    hit_down = day["low"] <= day["open"] * (1 - k)
    ambiguous = hit_up & hit_down
    only_up, only_down, neither = hit_up & ~hit_down, hit_down & ~hit_up, ~hit_up & ~hit_down
    base = k * only_up.sum() - k * only_down.sum() + (day["close"] / day["open"] - 1)[neither].sum()
    t = truth[ambiguous]
    guess = np.where(day.loc[ambiguous, "close"] >= day.loc[ambiguous, "open"], "down", "up")   # 阳线假设先低后高
    n = ambiguous.sum()
    print(f"±{k:.0%}：{len(day)} 天里，只碰到止盈 {only_up.sum()} 天，只碰到止损 {only_down.sum()} 天，都没碰到 {neither.sum()} 天，两个都碰到 {n} 天")
    print(f"   两个都碰到的 {n} 天里，1 分钟数据显示先碰到止盈 {(t == 'up').sum()} 天，先碰到止损 {(t == 'down').sum()} 天，同一分钟 {(t == 'same_bar').sum()} 天")
    print(f"   收益率之和：假设先止盈 {(base + k * n):+.1%}   假设先止损 {(base - k * n):+.1%}   "
          f"按阴阳线猜 {(base + k * (guess == 'up').sum() - k * (guess == 'down').sum()):+.1%}（猜对 {(guess == t.values).mean():.1%}）   "
          f"真实 {(base + k * (t == 'up').sum() - k * (t == 'down').sum()):+.1%}")

print("===== 片段 11：路径能预测第二天吗 =====")
d["next"] = d["close"].pct_change().shift(-1)
for name, mask in [("阳线", up), ("阴线", down)]:
    a = d.loc[mask & (d["high_first"] == True), "next"].dropna()
    b = d.loc[mask & (d["high_first"] == False), "next"].dropna()
    t_stat = (a.mean() - b.mean()) / math.sqrt(a.var() / len(a) + b.var() / len(b))
    print(f"{name}：先高后低 {len(a)} 天，次日平均 {a.mean():+.3%}；先低后高 {len(b)} 天，次日平均 {b.mean():+.3%}；t = {t_stat:.2f}")
before_22 = minute["close"][minute.index.hour < 22].resample("1D").last()
last2h = (day["close"] / before_22 - 1).rename("last2h")
x = pd.DataFrame({"last2h": last2h, "next": d["next"]}).dropna()
print(f"最后两小时涨跌 vs 次日涨跌：相关系数 {x['last2h'].corr(x['next']):.3f}，界限 ±{1.96 / math.sqrt(len(x)):.3f}")
for a_, b_ in [("2017", "2019"), ("2020", "2020"), ("2021", "2023"), ("2024", "2026")]:
    y = x.loc[a_:b_]
    print(f"   {a_}–{b_}：{y['last2h'].corr(y['next']):+.3f}（{len(y)} 天）")
no2020 = x[x.index.year != 2020]
print(f"   去掉 2020 年：{no2020['last2h'].corr(no2020['next']):+.3f}")

print("===== 片段 12：揭晓 =====")
for name, t in [("A", A), ("B", Bday)]:
    t0 = pd.Timestamp(t, tz="UTC")
    c0 = day.loc[t0, "close"]
    later = {k: day.loc[t0 + pd.Timedelta(days=k), "close"] / c0 - 1 for k in [1, 3, 7, 10]}
    print(name, t, {f"{k} 天后": f"{v:+.2%}" for k, v in later.items()})

for name, t in [("A", A), ("B", Bday)]:
    m = minute.loc[t]
    print(name, {f"±{k:.0%}": B.first_touch(m, k, k).iloc[0] for k in [0.01, 0.03]})

print("===== 片段 13：Heikin-Ashi =====")
ha = B.heikin_ashi(spy)
print(pd.concat([spy[cols], ha.add_prefix("ha_")], axis=1).loc["2025-04-02":"2025-04-10"].round(4))

print("===== 片段 14：HA 的价格有多少是真的 =====")
def runs(sign):
    s = sign[sign != 0]
    return s.groupby((s != s.shift()).cumsum()).size()
for k, df in {"SPY": spy, "AAPL": aapl, "BTC": day}.items():
    h = B.heikin_ashi(df)
    outside = ((h["open"] > df["high"]) | (h["open"] < df["low"])).mean()
    close_gap = (h["close"] / df["close"] - 1).abs()
    print(f"{k:4s} HA 开盘在真实最高最低之外 {outside:.1%}；HA 收盘偏离真实收盘 中位数 {close_gap.median():.2%} 最大 {close_gap.max():.1%}；"
          f"同色连续根数 平均 真实 {runs(np.sign(df['close'] - df['open'])).mean():.2f} / HA {runs(np.sign(h['close'] - h['open'])).mean():.2f}")
h1 = B.heikin_ashi(day)
h2 = B.heikin_ashi(day.loc["2020-01-01":])
diff = (h1["open"].loc["2020-01-01":] / h2["open"] - 1).abs()
print("从不同的起点开始算，HA 开盘的差距：", [f"{v:.4%}" for v in diff.head(8)])

print("===== 片段 15：用 HA 价格回测 =====")
def ha_backtest(df, years):
    h = B.heikin_ashi(df)
    green = (h["close"] > h["open"]).to_numpy()
    trades, start = [], None
    for i, g in enumerate(green):
        if g and start is None:
            start = i
        elif not g and start is not None:
            trades.append((start, i))
            start = None
    if start is not None:
        trades.append((start, len(df) - 1))
    hc, c, o = h["close"].to_numpy(), df["close"].to_numpy(), df["open"].to_numpy()
    fake = np.prod([hc[j] / hc[i] for i, j in trades])                          # 按 HA 收盘价成交
    at_close = np.prod([c[j] / c[i] for i, j in trades])                       # 按真实收盘价成交
    next_open = np.prod([o[min(j + 1, len(o) - 1)] / o[i + 1] for i, j in trades if i + 1 < len(o)])   # 次日开盘成交
    cagr = lambda g: g ** (1 / years) - 1
    return len(trades), fake, cagr(fake), at_close, cagr(at_close), next_open, cagr(next_open), c[-1] / c[0]
for k, df in {"SPY": spy, "AAPL": aapl, "BTC": day}.items():
    years = len(df) / (365 if k == "BTC" else 252)
    n, f, fc, r, rc, no, noc, bh = ha_backtest(df, years)
    print(f"{k:4s} {n} 笔：按 HA 收盘价 ×{f:,.2f}（年化 {fc:.1%}）  按真实收盘价 ×{r:.2f}（{rc:.1%}）  "
          f"按次日开盘价 ×{no:.2f}（{noc:.1%}）  一直持有 ×{bh:.2f}")

print("===== 片段 16：用 HA 价格算风险 =====")
x = spy.loc["2025-04-09"]
h = ha.loc["2025-04-09"]
print(f"真实收盘 {x['close']}  HA 收盘 {h['close']:.4f}  止损放在 HA 最低 {h['low']}")
print(f"以为的风险 {h['close'] - h['low']:.4f}（{(h['close'] - h['low']) / h['close']:.2%}）  实际的风险 {x['close'] - h['low']:.4f}（{(x['close'] - h['low']) / x['close']:.2%}）")
for k, df in {"SPY": spy, "AAPL": aapl, "BTC": day}.items():
    h = B.heikin_ashi(df)
    planned, actual = h["close"] - h["low"], df["close"] - h["low"]
    ratio = (actual / planned)[planned > 0]
    print(f"{k:4s} 实际风险 ÷ 以为的风险：大于 1.5 倍 {(ratio > 1.5).mean():.1%}，小于 1/1.5 {(ratio < 1 / 1.5).mean():.1%}")

print("===== 片段 17：Renko 手算 =====")
closes = day["close"].loc["2026-06-24":"2026-07-12"]
print(closes)
print(B.renko(closes, 1000))

print("===== 片段 18：Renko，每块 5% =====")
daily_bricks = B.renko(day["close"], 0.05, log=True)
minute_bricks = B.renko(minute["close"], 0.05, log=True)
for name, bricks in [("日线收盘价", daily_bricks), ("1 分钟收盘价", minute_bricks)]:
    reversals = (bricks["direction"] != bricks["direction"].shift()).sum() - 1
    print(f"用 {name}：{len(bricks)} 块砖，{reversals} 次反向")
per_year = pd.DataFrame({"日线": daily_bricks.groupby(daily_bricks["formed_at"].dt.year).size(),
                         "1 分钟": minute_bricks.groupby(minute_bricks["formed_at"].dt.year).size()})
print(per_year.T)
wait = daily_bricks["formed_at"].diff()
i = wait.idxmax()
print("两块砖之间最长隔了", wait[i].days, "天：", daily_bricks.loc[i - 1, "formed_at"].date(), "→", daily_bricks.loc[i, "formed_at"].date())
per_day = daily_bricks["formed_at"].value_counts()
print("一天里最多画了", per_day.max(), "块砖：", per_day.idxmax().date())
shifted = B.renko(day["close"].iloc[1:], 0.05, log=True)
print("起点从 2017-08-17 换成 2017-08-18：", len(daily_bricks), "块 →", len(shifted), "块")

print("===== 片段 19：砖块价格不是成交价 =====")
last = daily_bricks.groupby("formed_at").last()
beyond = (day.loc[last.index, "close"] / last["close"] - 1) * last["direction"]
print(f"形成砖块的那天，真实收盘价比最后一块砖的收盘价多走了：中位数 {beyond.median():.2%}，最大 {beyond.max():.2%}")
flips = last["direction"][last["direction"] != last["direction"].shift()]
entries, exits = [], []
for t, direction in flips.items():
    if direction == 1:
        entries.append(t)
    elif entries and len(exits) < len(entries):
        exits.append(t)
def brick_price(t, direction):
    return daily_bricks[(daily_bricks["formed_at"] == t) & (daily_bricks["direction"] == direction)].iloc[0]["close"]
fake = real = 1.0
for i, t in enumerate(entries):
    if i < len(exits):
        fake *= brick_price(exits[i], -1) / brick_price(t, 1)
        real *= day.loc[exits[i], "close"] / day.loc[t, "close"]
    else:
        fake *= day["close"].iloc[-1] / brick_price(t, 1)
        real *= day["close"].iloc[-1] / day.loc[t, "close"]
years = len(day) / 365
print(f"砖块转为向上就买、转为向下就卖（只做多），{len(entries)} 笔：按砖块价格 ×{fake:.2f}（年化 {fake ** (1 / years) - 1:.1%}）  "
      f"按真实收盘价 ×{real:.2f}（年化 {real ** (1 / years) - 1:.1%}）")
