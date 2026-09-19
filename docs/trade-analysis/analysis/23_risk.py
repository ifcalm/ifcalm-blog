"""第 23 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob

import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, risk as K

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
OHLC = ["open", "high", "low", "close"]

print("===== 片段 1：加载数据，摆出主线策略的信号 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
h4 = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/4h/*.zip"))
h1 = B.resample_ohlcv(D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")), "1h")
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
MARKETS = {"SPY 日线": (spy, 252), "AAPL 日线": (aapl, 252), "BTC 日线": (day, 365),
           "BTC 4 小时": (h4, 365 * 6), "BTC 1 小时": (h1, 365 * 24)}


def entries(df):
    """主线策略 v3 的入场条件（第 21 篇）：金叉状态 + 收盘创 20 日新高。"""
    close = df["close"]
    return ((I.sma(close, 50) > I.sma(close, 200)) & (close >= close.rolling(20).max())).fillna(False)


def deaths(df):
    """主线策略 v3 的出场信号：死叉。"""
    return I.cross_below(I.sma(df["close"], 50), I.sma(df["close"], 200)).fillna(False)


for name, (df, _) in MARKETS.items():
    print(f"{name:10s} {len(df):6d} 根  {str(df.index[0])[:10]}～{str(df.index[-1])[:10]}  入场信号 {int(entries(df).sum()):5d} 根")

print("===== 片段 2：决策点 =====")
CHANDELIER = K.Exit(stop="atr", k=3.0, trail="chandelier", trail_k=3.0, trigger="close")
trades = K.run(day, entries(day), CHANDELIER)
one = trades[trades["买入日"] == pd.Timestamp("2020-10-10", tz="UTC")].iloc[0]
print(f"买入日 {one['买入日'].date()}，开盘价买入 {one['买入价']:.2f}")
print(f"初始止损 {one['初始止损']:.2f}，一个 R = {one['R']:.2f}（占进场价 {one['R'] / one['买入价']:.2%}）")
for x in [1, 2, 3]:
    print(f"  +{x}R = {one['买入价'] + x * one['R']:.2f}")
window = day.loc["2020-10-10":"2020-10-22", OHLC].copy()
window["浮盈 R"] = ((window["close"] - one["买入价"]) / one["R"]).round(2)
print(window.round(2).to_string())

print("===== 片段 3：揭晓 =====")
print(f"这笔交易最后在 {one['卖出日'].date()} 以 {one['卖出价']:.2f} 出场，{one['原因']}，"
      f"{one['R 倍数']:.2f} 个 R，持有 {one['根数']} 根 K 线")
print(f"期间盘中最高到过 {one['最大浮盈']:.2f} 个 R（{day.loc['2020-10-10':'2021-01-12', 'high'].max():.2f}），"
      f"最大浮亏 {one['最大浮亏']:.4f} 个 R（最低 {day.loc['2020-10-10':'2021-01-12', 'low'].min():.2f}，就在买入的那一根上）")
decision = day.loc["2020-10-22", "close"]
r_at_decision = (decision - one["买入价"]) / one["R"]
print(f"\n三种做法在这一笔上的结果（决策点收盘 {decision:.2f}，{r_at_decision:.2f} R）：")
print(pd.Series({"全部离场": r_at_decision, "平一半": (r_at_decision + one["R 倍数"]) / 2,
                 "拿住": one["R 倍数"]}).round(2).to_string())
print("\n同一批交易里，另外三笔也在某一天到过 +2R：")
close = day["close"]
for buy in ["2019-06-16", "2020-07-23", "2021-02-04"]:
    t = trades[trades["买入日"] == pd.Timestamp(buy, tz="UTC")].iloc[0]
    i, j = day.index.get_loc(t["买入日"]), day.index.get_loc(t["卖出日"])
    r = (close.iloc[i:j + 1].to_numpy() - t["买入价"]) / t["R"]
    k = int(np.nonzero(r >= 2)[0][0])
    print(f"  {buy} 买入，{str(day.index[i + k].date())} 收盘 {r[k]:.2f} R，"
          f"最后 {t['R 倍数']:.2f} R（{t['原因']}，又拿了 {j - i - k} 根）")

print("===== 片段 4：R 倍数 =====")
print(f"一个 R = 进场价 − 初始止损价 = {one['买入价']:.2f} − {one['初始止损']:.2f} = {one['R']:.2f}")
for price, label in [(12968.52, "决策点收盘"), (34051.24, "最后出场"), (10126.43, "刚好打到止损")]:
    print(f"  {label:6s} {price:>9.2f} → {K.r_multiple(one['买入价'], one['初始止损'], price):+.2f} R")
print("\n换成别的标的也一样：SPY 2023-11-08 那一笔")
s_trades = K.run(spy, entries(spy), CHANDELIER)
s_one = s_trades[s_trades["买入日"] == pd.Timestamp("2023-11-08")].iloc[0]
print(f"  进场 {s_one['买入价']:.2f}，止损 {s_one['初始止损']:.2f}，一个 R = {s_one['R']:.2f} 美元"
      f"（{s_one['R'] / s_one['买入价']:.2%}）；出场 {s_one['卖出价']:.2f} → {s_one['R 倍数']:+.2f} R")
print(f"  两笔交易的止损距离差 {one['R'] / s_one['R']:.0f} 倍，换成 R 之后才能放在一起比："
      f"BTC 那笔 {one['R 倍数']:.1f} R，SPY 这笔 {s_one['R 倍数']:.1f} R")

print("===== 片段 5：出场的四个问题 =====")
print(CHANDELIER.describe().to_string())
print()
print(K.Exit(stop="structure", lookback=20, buffer=0.5, trail="none", target_r=2.0, max_bars=40).describe().to_string())

print("===== 片段 6：三种初始止损，距离差多少 =====")
METHODS = {"结构：前 20 根低点再往下 0.5 ATR": K.Exit(stop="structure", lookback=20, buffer=0.5),
           "波动率：进场价往下 3 ATR": K.Exit(stop="atr", k=3.0),
           "固定比例：进场价往下 10%": K.Exit(stop="percent", percent=0.10)}
rows = []
for name, (df, _) in MARKETS.items():
    signal = entries(df).to_numpy()
    where = np.flatnonzero(signal[:-1]) + 1                     # 信号的下一根，就是进场的那一根
    where = where[where > 200]
    opens = df["open"].to_numpy()[where]
    atr = I.atr(df["high"], df["low"], df["close"]).to_numpy()   # 算一次，别在循环里反复算
    distances = {label: 1 - np.array([K.initial_stop(df, i, price, plan, atr)
                                      for i, price in zip(where, opens)]) / opens
                 for label, plan in METHODS.items()}
    for label, distance in distances.items():
        rows.append({"标的": name, "初始止损": label, "进场点": len(where), "距离中位数": np.median(distance),
                     "最近": distance.min(), "最远": distance.max(),
                     "比 3 ATR 远的比例": np.mean(distance > distances["波动率：进场价往下 3 ATR"])})
print(pd.DataFrame(rows).round(3).to_string(index=False))
print("\n同一套入场信号，只换初始止损（跟踪、目标、时间都不设，出场信号仍是死叉）：")
rows = []
for name, (df, _) in MARKETS.items():
    for label, plan in METHODS.items():
        t = K.run(df, entries(df), plan, exits=deaths(df))
        rows.append({"标的": name, "初始止损": label, "交易数": len(t), "被止损出场": (t["原因"] == "止损").mean(),
                     "每笔期望 R": t["R 倍数"].mean(), "合计 R": t["R 倍数"].sum()})
print(pd.DataFrame(rows).round(3).to_string(index=False))

print("===== 片段 7：主线策略换四种出场方式 =====")
PLANS = {"A 结构止损，不动": K.Exit(stop="structure", lookback=20, buffer=0.5, trail="none"),
         "B 3 ATR 止损，不动": K.Exit(stop="atr", k=3.0, trail="none"),
         "C 3 ATR 吊灯跟踪": K.Exit(stop="atr", k=3.0, trail="chandelier", trail_k=3.0),
         "D 时间止损：拿满 20 根": K.Exit(stop="atr", k=3.0, trail="none", max_bars=20)}
rng = np.random.default_rng(23)
rows, distributions = [], {}
for name, (df, periods) in MARKETS.items():
    years = len(df) / periods
    for label, plan in PLANS.items():
        t = K.run(df, entries(df), plan, exits=deaths(df))
        r = t["R 倍数"]
        score = K.expectancy(r)
        curve = r.cumsum()
        boot = np.array([rng.choice(r, len(r)).sum() for _ in range(2000)])
        distributions.setdefault(label, []).append(r)
        rows.append({"标的": name, "出场方式": label, "交易数": int(score["交易数"]), "胜率": score["胜率"],
                     "平均盈利": score["平均盈利"], "平均亏损": score["平均亏损"], "盈亏比": score["盈亏比"],
                     "每笔期望 R": score["期望值"], "合计 R": r.sum(),
                     "合计 R 的 95% 区间": f"[{np.percentile(boot, 2.5):.0f}, {np.percentile(boot, 97.5):.0f}]",
                     "最大回撤 R": (curve - curve.cummax()).min(), "在场时间": t["根数"].sum() / len(df),
                     "平均持有根数": t["根数"].mean(), "最大一笔占合计": r.max() / r.sum(),
                     "满仓复利年化": (t["卖出价"] / t["买入价"]).prod() ** (1 / years) - 1})
compare = pd.DataFrame(rows)
for name in MARKETS:
    print(f"\n--- {name} ---")
    print(compare[compare["标的"] == name].drop(columns="标的").round(3).to_string(index=False))
print("\n五个序列的交易合起来：")
print(pd.DataFrame({label: K.expectancy(pd.concat(rs, ignore_index=True))
                    for label, rs in distributions.items()}).round(3).to_string())

print("===== 片段 8：浮盈 2R 的那些交易，后来都怎么样了 =====")
rows = []
for name, (df, _) in MARKETS.items():
    t = K.run(df, entries(df), CHANDELIER, exits=deaths(df))
    close = df["close"]
    for _, x in t.iterrows():
        i, j = df.index.get_loc(x["买入日"]), df.index.get_loc(x["卖出日"])
        r = (close.iloc[i:j + 1].to_numpy() - x["买入价"]) / x["R"]
        hit = np.nonzero(r >= 2.0)[0]
        if len(hit):
            rows.append({"标的": name, "买入日": x["买入日"], "到 2R 那根": df.index[i + hit[0]],
                         "全部离场": r[hit[0]], "拿住": x["R 倍数"], "还要拿几根": j - i - int(hit[0])})
reached = pd.DataFrame(rows)
reached["平一半"] = (reached["全部离场"] + reached["拿住"]) / 2
print(f"五个序列合计 {len(reached)} 笔交易在某一根收盘时浮盈到过 +2R")
print(reached.groupby("标的", sort=False).agg(交易数=("拿住", "size"), 拿住平均=("拿住", "mean"),
                                              拿住中位数=("拿住", "median"), 最好的一笔=("拿住", "max"),
                                              不如直接走=("拿住", lambda s: np.mean(s < reached.loc[s.index, "全部离场"]))).round(3).to_string())
print()
print(pd.DataFrame({"到 2R 就全部离场": K.expectancy(reached["全部离场"]), "平一半": K.expectancy(reached["平一半"]),
                    "拿住": K.expectancy(reached["拿住"])}).round(3).to_string())
print(f"\n拿住比直接走更差的比例：{np.mean(reached['拿住'] < reached['全部离场']):.1%}")
print(f"最终不到 2R 的：{np.mean(reached['拿住'] < 2):.1%}；不到 1R 的：{np.mean(reached['拿住'] < 1):.1%}；"
      f"倒亏的：{np.mean(reached['拿住'] < 0):.1%}")
big = reached["拿住"] >= 4
print(f"最终 ≥ 4R 的只有 {big.mean():.1%}，但它们贡献了「拿住」全部 R 的 {reached.loc[big, '拿住'].sum() / reached['拿住'].sum():.1%}")
print(f"三种做法的标准差：全部离场 {reached['全部离场'].std():.2f}，平一半 {reached['平一半'].std():.2f}，拿住 {reached['拿住'].std():.2f}")

print("===== 片段 9：期望值 =====")
sample = pd.concat(distributions["C 3 ATR 吊灯跟踪"], ignore_index=True)
score = K.expectancy(sample)
print(score.round(3).to_string())
print(f"\n把公式拆开算一遍：{score['胜率']:.4f} × {score['平均盈利']:.4f} − "
      f"{1 - score['胜率']:.4f} × {score['平均亏损']:.4f} = {score['期望值']:.4f}")
print(f"直接对这 {len(sample)} 个 R 取平均：{sample.mean():.4f}（两者相等，期望值就是平均 R）")
print(f"中位数却是 {sample.median():.3f}：一半以上的交易在亏钱，靠的是右边那条尾巴")
print(f"打平需要的胜率 = 平均亏损 ÷（平均亏损 + 平均盈利）= "
      f"{score['平均亏损']:.3f} ÷ ({score['平均亏损']:.3f} + {score['平均盈利']:.3f}) = "
      f"{score['平均亏损'] / (score['平均亏损'] + score['平均盈利']):.1%}，实测胜率 {score['胜率']:.1%}")

print("===== 片段 10：胜率和盈亏比为什么此消彼长 =====")


def race(target, stop=1.0, paths=10000, step=0.05, chunk=1000, seed=23):
    """无漂移随机游走：每步等概率走 ±step 个 R，先碰到 +target 记 target，先碰到 −stop 记 −stop。"""
    rng = np.random.default_rng(seed)
    out, level, alive = np.zeros(paths), np.zeros(paths), np.ones(paths, bool)
    while alive.any():
        idx = np.flatnonzero(alive)
        walk = level[idx, None] + np.cumsum(rng.choice([-step, step], (len(idx), chunk)), axis=1)
        up, down = walk >= target, walk <= -stop
        first_up = np.where(up.any(1), up.argmax(1), chunk)
        first_down = np.where(down.any(1), down.argmax(1), chunk)
        done = np.minimum(first_up, first_down) < chunk
        out[idx[done]] = np.where(first_up < first_down, target, -stop)[done]
        level[idx], alive[idx] = walk[:, -1], ~done
    return out


rows = []
for target in [0.5, 1, 2, 3, 5, 10]:
    r = race(target)
    win = (r > 0).mean()
    rows.append({"目标": f"{target}R", "实测胜率": win, "理论胜率 = 1 ÷ (1 + 目标)": 1 / (1 + target),
                 "盈亏比": target, "胜率 × 盈亏比": win * target, "败率 × 1": 1 - win, "平均 R": r.mean()})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 11：把目标价从 0.5R 挪到 10R =====")


def shuffle_bars(df, rng):
    """打乱 K 线顺序：保留每根 K 线相对前一根收盘价的形状，重新拼成价格（第 9 篇）。"""
    relative = np.log(df[OHLC].div(df["close"].shift(1), axis=0))
    relative = relative.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    previous_close = df["close"].iloc[0] * np.exp(relative["close"].cumsum().shift(1, fill_value=0))
    out = np.exp(relative[OHLC]).mul(previous_close, axis=0)
    out.index = df.index[1:]
    return out


TARGETS = [0.5, 1, 1.5, 2, 3, 4, 6, 8, 10]
COST = 0.001                                                    # 一来一回 0.1%，第 29 篇才认真算成本
scans = {}
rng = np.random.default_rng(23)
for name in ["SPY 日线", "BTC 日线", "BTC 4 小时", "BTC 1 小时"]:
    df = MARKETS[name][0]
    shuffled = [shuffle_bars(df, rng) for _ in range(5)]
    rows = []
    for target in TARGETS:
        plan = K.Exit(stop="atr", k=3.0, trail="none", target_r=target)
        t = K.run(df, entries(df), plan)
        score = K.expectancy(t["R 倍数"])
        cost = (COST / (t["R"] / t["买入价"])).sum()             # 每笔的成本折算成几个 R，再加起来
        fake = [K.expectancy(K.run(s, entries(s), plan)["R 倍数"]) for s in shuffled]
        rows.append({"目标": f"{target}R", "交易数": int(score["交易数"]), "胜率": score["胜率"],
                     "平均盈利": score["平均盈利"], "平均亏损": score["平均亏损"],
                     "打平需要的胜率": score["平均亏损"] / (score["平均亏损"] + score["平均盈利"]),
                     "每笔期望 R": score["期望值"], "合计 R": t["R 倍数"].sum(), "成本合计 R": cost,
                     "扣成本后合计 R": t["R 倍数"].sum() - cost,
                     "打乱后的胜率": np.mean([f["胜率"] for f in fake]),
                     "打乱后的每笔期望 R": np.mean([f["期望值"] for f in fake])})
    scans[name] = pd.DataFrame(rows)
    print(f"\n--- {name} ---")
    print(scans[name].round(3).to_string(index=False))

print("===== 片段 12：时间止损 =====")
for name in ["SPY 日线", "BTC 日线", "BTC 4 小时"]:
    df = MARKETS[name][0]
    rows = []
    for bars in [5, 10, 20, 40, 60, 100, None]:
        t = K.run(df, entries(df), K.Exit(stop="atr", k=3.0, trail="none", max_bars=bars), exits=deaths(df))
        score = K.expectancy(t["R 倍数"])
        rows.append({"最多拿": "不限" if bars is None else f"{bars} 根", "交易数": int(score["交易数"]),
                     "胜率": score["胜率"], "盈亏比": score["盈亏比"], "每笔期望 R": score["期望值"],
                     "合计 R": t["R 倍数"].sum(), "在场时间": t["根数"].sum() / len(df),
                     "被时间赶出来的": (t["原因"] == "时间到").mean()})
    print(f"\n--- {name} ---")
    print(pd.DataFrame(rows).round(3).to_string(index=False))

print("===== 片段 13：最大浮盈和最大浮亏 =====")
pool = []
for name, (df, _) in MARKETS.items():
    t = K.run(df, entries(df), CHANDELIER, exits=deaths(df))
    t["标的"] = name
    pool.append(t)
all_trades = pd.concat(pool, ignore_index=True)
winners = all_trades[all_trades["R 倍数"] > 0]
losers = all_trades[all_trades["R 倍数"] <= 0]
print(f"五个序列合计 {len(all_trades)} 笔：赚钱 {len(winners)} 笔，亏钱 {len(losers)} 笔")
print(pd.DataFrame({"赚钱的交易 · 最大浮亏": winners["最大浮亏"].quantile([.5, .75, .9, .95]),
                    "亏钱的交易 · 最大浮亏": losers["最大浮亏"].quantile([.5, .75, .9, .95]),
                    "亏钱的交易 · 最大浮盈": losers["最大浮盈"].quantile([.5, .75, .9, .95])}).round(2).to_string())
print(f"\n赚钱的交易里，最大浮亏没超过 0.5R 的占 {np.mean(winners['最大浮亏'] > -0.5):.1%}")
print("但把止损收紧，代价是打掉一部分赢家：")
for tight in [0.3, 0.5, 0.7, 1.0]:
    print(f"  止损改放在 −{tight}R（当初距离的 {tight:.0%}），赢家里有 "
          f"{np.mean(winners['最大浮亏'] <= -tight):.1%} 会先被打掉")
print(f"\n亏钱的交易里，浮盈到过 1R 的只有 {np.mean(losers['最大浮盈'] >= 1):.1%}，"
      f"到过 2R 的只有 {np.mean(losers['最大浮盈'] >= 2):.1%}")
print(f"全部交易里最大浮亏跌穿 1R 的有 {np.mean(all_trades['最大浮亏'] < -1):.1%}"
      f"——收盘触发的止损盘中会被穿过去（第 20 篇的选择）")
print("\n跟踪止损注定要还回去一部分：按最大浮盈分组，最后留住了多少")
for low, high in [(0, 1), (1, 2), (2, 3), (3, 5), (5, 1000)]:
    group = all_trades[(all_trades["最大浮盈"] >= low) & (all_trades["最大浮盈"] < high)]
    keep = (group["R 倍数"] / group["最大浮盈"]).median()
    print(f"  最大浮盈 [{low}, {high}) R：{len(group):4d} 笔，最终 R 中位数 {group['R 倍数'].median():6.2f}，"
          + (f"留住比例中位数 {keep:.2f}" if low >= 1 else "（浮盈没到 1R，谈不上留住多少）"))

print("===== 片段 14：成本按 R 折算 =====")
rows = []
for name in ["SPY 日线", "BTC 日线", "BTC 1 小时"]:
    df = MARKETS[name][0]
    for target in [0.5, 2, 10]:
        t = K.run(df, entries(df), K.Exit(stop="atr", k=3.0, trail="none", target_r=target))
        per_trade = COST / (t["R"] / t["买入价"])
        rows.append({"标的": name, "目标": f"{target}R", "交易数": len(t),
                     "止损距离中位数": (t["R"] / t["买入价"]).median(), "每笔成本折合": per_trade.mean(),
                     "合计 R": t["R 倍数"].sum(), "成本合计 R": per_trade.sum(),
                     "成本吃掉": per_trade.sum() / t["R 倍数"].sum()})
print(pd.DataFrame(rows).round(3).to_string(index=False))

print("===== 片段 15：主线策略这一篇不改 =====")
print(compare[compare["出场方式"] == "C 3 ATR 吊灯跟踪"][
    ["标的", "交易数", "胜率", "盈亏比", "每笔期望 R", "合计 R", "合计 R 的 95% 区间", "最大回撤 R"]].round(3).to_string(index=False))
print("\nv3 的出场，四个问题的答案：")
print(CHANDELIER.describe().to_string())
