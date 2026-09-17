"""第 8 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
import itertools
import math

import numpy as np
import pandas as pd
from talab import data as D, stats as St, structure as X

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
cols = ["open", "high", "low", "close"]

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
t = pd.Timestamp("2024-10-16", tz="UTC")                      # 决策点
print(day.loc["2024-10-14":"2024-10-16", cols])
before = day.loc[:t]
print("3 月以来最高价", before.loc["2024-03-01":, "high"].max(), before.loc["2024-03-01":, "high"].idxmax().date(),
      "最低价", before.loc["2024-03-01":, "low"].min(), before.loc["2024-03-01":, "low"].idxmin().date())

print("===== 片段 2：分形 =====")
f2 = X.fractals(before["high"], before["low"], 2, 2)
print(f2[f2["time"] >= "2024-09-01"].to_string(index=False))
for n in [2, 5, 10]:
    f = X.fractals(day["high"], day["low"], n, n)
    kinds = f["kind"].to_numpy()
    repeats = int((kinds[1:] == kinds[:-1]).sum())
    print(f"左右各 {n} 根：{len(f)} 个摆动点（高点 {(f['kind'] == 1).sum()}，低点 {(f['kind'] == -1).sum()}），"
          f"相邻两个是同一种的 {repeats} 次")

print("===== 片段 3：ZigZag 用最高最低价时的先后问题 =====")
def zigzag_high_low(high, low, threshold):
    """用最高价和最低价的 ZigZag，只用来数「同一根 K 线里分不清先后」的次数。"""
    h, l = high.to_numpy(float), low.to_numpy(float)
    direction, hi, lo, found, unclear = 0, h[0], l[0], 0, 0
    hi_i = lo_i = 0
    for i in range(1, len(h)):
        new_high = direction >= 0 and h[i] > hi
        new_low = direction <= 0 and l[i] < lo
        if new_high:
            hi, hi_i = h[i], i
        if new_low:
            lo, lo_i = l[i], i
        if direction == 0:
            if hi_i > lo_i and hi >= lo * (1 + threshold):
                direction, found = 1, found + 1
            elif lo_i > hi_i and lo <= hi * (1 - threshold):
                direction, found = -1, found + 1
        elif direction == 1 and l[i] <= hi * (1 - threshold):
            unclear += new_high                              # 同一根 K 线创了新高，又比新高低了 threshold
            direction, found, lo, lo_i = -1, found + 1, l[i], i
        elif direction == -1 and h[i] >= lo * (1 + threshold):
            unclear += new_low
            direction, found, hi, hi_i = 1, found + 1, h[i], i
    return found, unclear
for th in [0.05, 0.10, 0.20]:
    found, unclear = zigzag_high_low(day["high"], day["low"], th)
    print(f"阈值 {th:.0%}：{found} 个摆动点，其中 {unclear} 个在同一根 K 线里分不清先后（{unclear / found:.1%}）")

print("===== 片段 4：ZigZag =====")
z10 = X.zigzag(before["close"], 0.10)
print(z10.tail(6).to_string(index=False))
pos = pd.Series(np.arange(len(day)), index=day.index)
for th in [0.05, 0.10, 0.20, 0.30]:
    z = X.zigzag(day["close"], th)
    lag = pos[z["confirmed_at"]].to_numpy() - pos[z["time"]].to_numpy()
    print(f"阈值 {th:.0%}：{len(z)} 个摆动点，平均 {len(day) / len(z):.1f} 天一个；"
          f"确认滞后 中位数 {np.median(lag):.0f} 天，平均 {lag.mean():.1f} 天，最长 {lag.max()} 天")

print("===== 片段 5：最后一个点 =====")
def last_point(close, swings, day_i):
    """图上最后一个点：最近一个已确认摆动点之后的最低价（上一个是高点时）或最高价（上一个是低点时）。"""
    done = swings[pos[swings["confirmed_at"]].to_numpy() <= day_i]
    prev = done.iloc[-1]
    seg = close.iloc[pos[prev["time"]] + 1:day_i + 1]
    return seg.idxmin() if prev["kind"] == 1 else seg.idxmax()
for th in [0.10, 0.20]:
    z = X.zigzag(day["close"], th)
    first = pos[z["confirmed_at"].iloc[0]]
    points = [last_point(day["close"], z, i) for i in range(first, len(day))]
    replaced = np.mean([p not in set(z["time"]) for p in points])
    distance = (day["close"][z["confirmed_at"]].to_numpy() / z["price"].to_numpy() - 1)
    print(f"阈值 {th:.0%}：图上最后一个点后来没有成为摆动点的天数占 {replaced:.1%}；"
          f"确认那天的收盘价离摆动点 平均 {np.abs(distance).mean():.2%}")
for d in ["2024-07-20", "2024-07-29", "2024-08-05"]:
    i = pos[pd.Timestamp(d, tz="UTC")]
    p = last_point(day["close"], X.zigzag(day["close"].iloc[:i + 1], 0.10), i)
    print(f"{d} 收盘时，10% ZigZag 的最后一个点：{p.date()} {day['close'][p]:,.2f}")

print("===== 片段 6：按摆动点的时间回测 =====")
def swing_backtest(close, swings, when):
    """摆动低点买入、摆动高点卖出。when 选择用摆动点所在的时间，还是确认的时间。"""
    signal = pd.Series(np.nan, index=close.index)
    for s in swings.sort_values(when).itertuples():
        signal[getattr(s, when)] = 1.0 if s.kind == -1 else 0.0
    position = signal.ffill().fillna(0)
    return (1 + position.shift(1).fillna(0) * close.pct_change().fillna(0)).prod()
for name, swings in [("ZigZag 10%", X.zigzag(day["close"], 0.10)), ("分形 2/2", X.fractals(day["high"], day["low"], 2, 2))]:
    print(f"{name}：按摆动点所在的时间 ×{swing_backtest(day['close'], swings, 'time'):,.0f}，"
          f"按确认的时间 ×{swing_backtest(day['close'], swings, 'confirmed_at'):.2f}")
print(f"一直持有：×{day['close'].iloc[-1] / day['close'].iloc[0]:.2f}")

print("===== 片段 7：决策点的趋势状态 =====")
rows = {}
for th in [0.05, 0.10, 0.20]:
    z = X.zigzag(before["close"], th)
    levels = X.trend_state(z, before["close"], before["close"])
    highs, lows = z[z["kind"] == 1]["price"].tail(2).tolist(), z[z["kind"] == -1]["price"].tail(2).tolist()
    rows[f"ZigZag {th:.0%}"] = {"最近两个高点": highs, "最近两个低点": lows,
                                "状态": levels["state"].iloc[-1], "突破版": X.break_state(levels, before["close"]).iloc[-1]}
for n in [2, 5]:
    f = X.fractals(before["high"], before["low"], n, n)
    levels = X.trend_state(f, before["high"], before["low"])
    rows[f"分形 {n}/{n}"] = {"最近两个高点": f[f["kind"] == 1]["price"].tail(2).tolist(),
                           "最近两个低点": f[f["kind"] == -1]["price"].tail(2).tolist(),
                           "状态": levels["state"].iloc[-1], "突破版": X.break_state(levels, before["close"]).iloc[-1]}
print(pd.DataFrame(rows).T.to_string())
print("10 月 16 日之前的最高收盘价（8 月 25 日之后）：", before.loc["2024-08-26":, "close"].max())
for th in [0.10, 0.20]:
    levels = X.trend_state(X.zigzag(before["close"], th), before["close"], before["close"])
    b = X.break_state(levels, before["close"])
    since = b.index[b.index.get_loc(b[b != b.iloc[-1]].index[-1]) + 1]
    print(f"ZigZag {th:.0%} 突破版：从 {since.date()} 起一直是 {int(b.iloc[-1])}，那天收盘 {before['close'][since]:,.2f}，"
          f"最近的高点 {levels['last_high'][since]:,.2f}，最近的低点 {levels['last_low'][since]:,.2f}")

print("===== 片段 8：揭晓 =====")
c = day["close"]
for n in [7, 30, 60]:
    print(f"{n} 天后（{day.index[pos[t] + n].date()}）：{c.iloc[pos[t] + n] / c[t] - 1:+.2%}")
after = day.loc["2024-10-17":"2024-12-31"]
print("之后 30 天最低价", day.loc["2024-10-17":"2024-11-15", "low"].min(), "；年底前最高价", after["high"].max(), after["high"].idxmax().date())
for th in [0.05, 0.10, 0.20]:
    levels = X.trend_state(X.zigzag(c, th), c, c)
    for name, s in [("状态", levels["state"]), ("突破版", X.break_state(levels, c))]:
        part = s.loc["2024-10-16":"2025-01-31"]
        changes = part[part.diff() != 0]
        print(f"ZigZag {th:.0%} {name}：", {k.date().isoformat(): int(v) for k, v in changes.items()})

print("===== 片段 9：状态之后的 20 天 =====")
def state_gap(log_returns, threshold, rule, horizon=20):
    """用对数收益率重建价格，计算「上升状态」和「下降状态」之后 horizon 天平均收益的差。"""
    close = pd.Series(np.exp(np.cumsum(np.asarray(log_returns))))
    levels = X.trend_state(X.zigzag(close, threshold), close, close)
    state = levels["state"] if rule == "状态" else X.break_state(levels, close)
    forward = close.shift(-horizon) / close - 1
    return forward[state == 1].mean() - forward[state == -1].mean()
markets = [("BTC", day["close"], 0.10), ("SPY", spy["close"], 0.03), ("AAPL", aapl["close"], 0.05)]
for name, close, th in markets:
    lr = np.log(close).diff().dropna().reset_index(drop=True)
    levels = X.trend_state(X.zigzag(close, th), close, close)
    share = levels["state"].dropna().value_counts(normalize=True)
    print(f"{name}（阈值 {th:.0%}）：上升 {share[1]:.1%}，震荡 {share[0]:.1%}，下降 {share[-1]:.1%}")
    for rule in ["状态", "突破版"]:
        res = St.shuffle_test(lr, lambda x: state_gap(x, th, rule), n=1000, seed=0)
        print(f"   {rule}：上升减下降 {res['实际值']:+.2%}，打乱后 95% 范围 {res['打乱后 2.5% 分位']:+.2%} ~ "
              f"{res['打乱后 97.5% 分位']:+.2%}，打乱后差距不小于实际的比例 {res['比例']:.1%}")

print("按年份拆开：上升减下降（只列两边都有样本的年份）")
for name, close, th, rule in [("BTC", day["close"], 0.10, "突破版"), ("SPY", spy["close"], 0.03, "状态")]:
    levels = X.trend_state(X.zigzag(close, th), close, close)
    state = levels["state"] if rule == "状态" else X.break_state(levels, close)
    forward = close.shift(-20) / close - 1
    by_year = forward.groupby([close.index.year, state]).mean().unstack()
    gap = (by_year[1.0] - by_year[-1.0]).dropna()
    print(f"   {name} {rule}：", {int(y): f"{g:+.1%}" for y, g in gap.items()})

print("===== 片段 10：打乱之后还有没有结构 =====")
rng = np.random.default_rng(0)
for name, close, th in markets:
    lr = np.log(close).diff().dropna().to_numpy()
    sims = []
    for _ in range(1000):
        fake = pd.Series(np.exp(np.cumsum(rng.permutation(lr))))
        z = X.zigzag(fake, th)
        s = X.trend_state(z, fake, fake)["state"].dropna()
        sims.append([len(z), (s == 1).mean(), (s == -1).mean()])
    sims = np.array(sims)
    lo, hi = np.percentile(sims, [2.5, 97.5], axis=0)
    real = X.trend_state(X.zigzag(close, th), close, close)["state"].dropna()
    print(f"{name}：摆动点 {len(X.zigzag(close, th))}（打乱后 {lo[0]:.0f}~{hi[0]:.0f}），"
          f"上升 {(real == 1).mean():.1%}（{lo[1]:.1%}~{hi[1]:.1%}），下降 {(real == -1).mean():.1%}（{lo[2]:.1%}~{hi[2]:.1%}）")

print("===== 片段 11：趋势线 =====")
window = day.loc[pd.Timestamp("2024-08-01", tz="UTC"):t]
lines = []
for price_type in ["最低价", "收盘价"]:
    lows_series = window["low"] if price_type == "最低价" else window["close"]
    swings = X.fractals(lows_series, lows_series, 2, 2)
    swings = swings[(swings["kind"] == -1) & (swings["confirmed_at"] <= t)]
    for a, b in itertools.combinations(swings.itertuples(), 2):
        for scale in ["算术", "对数"]:
            f, g = (np.log, np.exp) if scale == "对数" else (lambda v: v, lambda v: v)
            ia, ib, it = pos[a.time], pos[b.time], pos[t]
            slope = (f(b.price) - f(a.price)) / (ib - ia)
            line = g(f(a.price) + slope * np.arange(it - ia + 1))
            touched = lows_series.iloc[ia - pos[window.index[0]]:].to_numpy()
            lines.append({"价格": price_type, "坐标": scale, "起点": a.time.date(), "起点价": a.price,
                          "终点": b.time.date(), "终点价": b.price, "向上": b.price > a.price,
                          "没有被穿过": bool((touched >= line - 1e-6).all()), "今天的位置": line[-1]})
lines = pd.DataFrame(lines)
valid = lines[lines["向上"] & lines["没有被穿过"]]
print(f"两两连接的候选线 {len(lines)} 条，向上且中间没有价格跌破的 {len(valid)} 条")
print(valid.drop(columns=["向上", "没有被穿过"]).round(2).to_string(index=False))
print(f"10 月 16 日的位置：{valid['今天的位置'].min():,.2f} ~ {valid['今天的位置'].max():,.2f}，收盘价 {c[t]:,.2f}")

print("===== 片段 12：趋势强度 =====")
er = X.efficiency_ratio(c, 20)
reg = X.regression_slope(c, 20)
dmi = X.adx(day["high"], day["low"], c, 14)
strength = pd.concat([er.rename("er"), reg, dmi], axis=1)
print(strength.loc[["2024-10-16", "2024-11-15", "2024-11-22"]].round(3))
print(strength[["er", "r2", "adx"]].corr(method="spearman").round(2))

print("===== 片段 13：随机数据里的「趋势强度」 =====")
def strength_summary(bars):
    e = X.efficiency_ratio(bars["close"], 20)
    r2 = X.regression_slope(bars["close"], 20)["r2"]
    t_value = np.sqrt(r2 * 18 / (1 - r2))                     # 20 个点的回归，斜率的 t 值
    a = X.adx(bars["high"], bars["low"], bars["close"], 14)["adx"]
    return [e.mean(), (t_value > 2.10).mean(), (a > 25).mean()]
relative = np.log(day[cols].div(c.shift(1), axis=0)).dropna()  # 每根 K 线相对前一天收盘价的位置
sims = []
for _ in range(1000):
    shuffled = relative.iloc[rng.permutation(len(relative))].reset_index(drop=True)
    prev_close = c.iloc[0] * np.exp(shuffled["close"].cumsum().shift(1, fill_value=0))
    sims.append(strength_summary(shuffled.apply(np.exp).mul(prev_close, axis=0)))
lo, hi = np.percentile(np.array(sims), [2.5, 97.5], axis=0)
real = strength_summary(day)
for k, label in enumerate(["20 天效率比的平均值", "20 天回归斜率 |t| > 2.10 的比例", "ADX > 25 的比例"]):
    fmt = "{:.3f}" if k == 0 else "{:.1%}"
    print(f"{label}：实际 {fmt.format(real[k])}，打乱后 {fmt.format(lo[k])} ~ {fmt.format(hi[k])}")
print(f"随机游走的效率比约等于 1/√20 = {1 / math.sqrt(20):.3f}")

print("===== 片段 14：ADX 确认趋势时，行情走了多少 =====")
z20 = X.zigzag(c, 0.20)
done, never = [], 0
for s0, s1 in zip(z20.itertuples(), z20.iloc[1:].itertuples()):
    leg = dmi.iloc[pos[s0.time]:pos[s1.time] + 1]
    same_way = leg["plus_di"] > leg["minus_di"] if s1.kind == 1 else leg["minus_di"] > leg["plus_di"]
    hit = leg.index[(leg["adx"] > 25) & same_way]
    if len(hit) == 0:
        never += 1
        continue
    done.append(math.log(c[hit[0]] / s0.price) / math.log(s1.price / s0.price))
print(f"20% ZigZag 的 {len(z20) - 1} 段行情：ADX 从来没有同方向超过 25 的 {never} 段；"
      f"其余第一次超过 25 时，已经走完的比例 中位数 {np.median(done):.1%}，四分位 {np.percentile(done, 25):.1%} ~ {np.percentile(done, 75):.1%}")
