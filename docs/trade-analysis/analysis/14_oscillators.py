"""第 14 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
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


def run_length(flag):
    """flag 连续为真的根数：为真的那一根记 1、2、3……，为假记 0。"""
    group = (~flag).cumsum()
    return flag.astype(int).groupby(group).cumsum()


print("===== 片段 2：决策点 =====")
c = day["close"]
r = I.rsi(c)
st = I.stochastic(day["high"], day["low"], c)
t = pd.Timestamp("2024-02-20", tz="UTC")
above = run_length(r > 70)
table = pd.concat([c, r.rename("rsi"), above.rename("连续天数"), st], axis=1)
print(table.loc["2024-02-05":"2024-02-20"].round(1).to_string())
print(f"2024-01-23 最低收盘 {c['2024-01-23']:,.2f}，到 2 月 20 日涨了 {c[t] / c['2024-01-23'] - 1:.2%}")
starts = above[(above == 12)].index
print("此前 BTC 日线 RSI 连续 12 天高于 70 的次数：", int((starts < t).sum()),
      "，最近一次：", starts[starts < t][-1].date())

print("===== 片段 3：手算 RSI =====")
x = pd.Series([10.0, 11, 10, 12, 13, 12, 14])
change = x.diff()
gain, loss = change.clip(lower=0), (-change).clip(lower=0)
small = pd.DataFrame({"收盘价": x, "变化": change, "gain": gain, "loss": loss,
                      "平均 gain": I.ema(gain, 3, alpha=1 / 3), "平均 loss": I.ema(loss, 3, alpha=1 / 3), "RSI(3)": I.rsi(x, 3)})
print(small.round(4).to_string())

print("===== 片段 4：Wilder 平滑和另外两种写法 =====")
d = c.diff()
pandas_style = 100 * d.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean() / d.abs().ewm(alpha=1 / 14, adjust=False).mean()
cutler = 100 * d.clip(lower=0).rolling(14).mean() / d.abs().rolling(14).mean()
first = r.first_valid_index()
k0 = c.index.get_loc(first)
print(f"第一个 RSI（{first.date()}）：Wilder {r[first]:.2f}，pandas ewm 从第一个变化开始 {pandas_style[first]:.2f}，"
      f"Cutler（简单平均）{cutler[first]:.2f}")
for k in [30, 100, 200]:
    i = k0 + k
    print(f"再往后 {k} 根：和 pandas ewm 写法相差 {abs(r.iloc[i] - pandas_style.iloc[i]):.4f}")
gap = (r - cutler).abs()
print(f"和 Cutler 写法：相差的中位数 {gap.median():.2f}，最大 {gap.max():.2f}，"
      f"两者一个高于 70、另一个不高于 70 的天数占 {((r > 70) != (cutler > 70))[r.notna()].mean():.1%}")

print("===== 片段 5：RSI 在量什么 =====")
smooth = lambda s: I.ema(s, 14, alpha=1 / 14)
identity = 50 + 50 * smooth(d) / smooth(d.abs())
print(f"RSI 和 50 + 50 × 平滑的变化 ÷ 平滑的 |变化|：最大差 {(identity - r).abs().max():.1e}")
for name, df in markets.items():
    close = df["close"]
    rr = I.rsi(close)
    lr = np.log(close).diff()
    mean = smooth(lr)
    ratio = mean / np.sqrt(smooth(lr ** 2) - mean ** 2)
    ok = rr.notna() & ratio.notna()
    slope, intercept = np.polyfit(ratio[ok], rr[ok], 1)
    print(f"{name}：RSI ≈ {intercept:.1f} + {slope:.1f} × 平均涨幅/波动，相关系数 {np.corrcoef(ratio[ok], rr[ok])[0, 1]:.3f}；"
          f"RSI > 70 占 {(rr > 70)[ok].mean():.1%}，RSI < 30 占 {(rr < 30)[ok].mean():.1%}")
print(f"正态分布下的斜率 50 ÷ √(2/π) = {50 / np.sqrt(2 / np.pi):.1f}；RSI = 70 对应 平均涨幅/波动 = {20 / (50 / np.sqrt(2 / np.pi)):.2f}")

print("===== 片段 6：钝化 =====")
thresholds = {"SPY": 0.03, "AAPL": 0.05, "BTC": 0.10}
five = {"up": "上升", "down": "下降", "range": "震荡", "transition_up": "向上过渡", "transition_down": "向下过渡"}
rows = []
for name, df in markets.items():
    close = df["close"]
    rr = I.rsi(close)
    swings = X.zigzag(close, thresholds[name])
    state = X.market_state(X.trend_state(swings, close, close), close).map(five)
    for s in ["上升", "向上过渡", "震荡", "向下过渡", "下降"]:
        m = (state == s) & rr.notna()
        rows.append({"标的": name, "状态": s, "K 线": int(m.sum()), "RSI 平均": rr[m].mean(),
                     "RSI > 70": (rr[m] > 70).mean(), "RSI < 30": (rr[m] < 30).mean()})
print(pd.DataFrame(rows).to_string(index=False, formatters={"RSI 平均": "{:.1f}".format,
                                                             "RSI > 70": "{:.1%}".format, "RSI < 30": "{:.1%}".format}))


def streaks(log_returns, k=12):
    """把对数收益率拼回价格，数 RSI 连续高于 70 至少 k 根的段数。"""
    price = pd.Series(np.exp(np.cumsum(np.asarray(log_returns))))
    return float((run_length(I.rsi(price) > 70) == k).sum())


for name, df in markets.items():
    log_returns = np.log(df["close"]).diff().dropna().reset_index(drop=True)
    res = St.shuffle_test(log_returns, streaks, n=500, seed=0)
    print(f"{name}：RSI 连续 12 根以上高于 70 的段数 {res['实际值']:.0f}，打乱后 95% 范围 "
          f"{res['打乱后 2.5% 分位']:.0f} ~ {res['打乱后 97.5% 分位']:.0f}，打乱后不少于实际的比例 {res['比例']:.1%}")

print("===== 片段 7：Stochastic =====")
close = pd.Series([5.0, 6, 7, 6, 8, 9, 7, 6])
high, low = close + 1, close - 1
raw = 100 * (close - low.rolling(3).min()) / (high.rolling(3).max() - low.rolling(3).min())
small = pd.concat([close.rename("收盘价"), high.rolling(3).max().rename("3 根最高"), low.rolling(3).min().rename("3 根最低"),
                   raw.rename("原始 %K"), I.stochastic(high, low, close, k=3, smooth_k=2, d=2)], axis=1)
print(small.round(2).to_string())
for name, df in markets.items():
    s = I.stochastic(df["high"], df["low"], df["close"])
    rr = I.rsi(df["close"])
    ok = s["k"].notna() & rr.notna()
    print(f"{name}：%K 和 RSI 的相关系数 {np.corrcoef(s['k'][ok], rr[ok])[0, 1]:.2f}；%K > 80 占 {(s['k'][ok] > 80).mean():.1%}，"
          f"%K < 20 占 {(s['k'][ok] < 20).mean():.1%}")

print("===== 片段 8：揭晓 =====")
i = c.index.get_loc(t)
for n in [1, 5, 10, 20, 60]:
    print(f"{n} 天后（{c.index[i + n].date()}）：{c.iloc[i + n] / c[t] - 1:+.2%}，RSI {r.iloc[i + n]:.1f}")
exit_c = r.loc["2024-02-21":][r.loc["2024-02-21":] <= 70].index[0]
print(f"选 C：RSI 第一次回到 70 以下是 {exit_c.date()}，收盘 {c[exit_c]:,.2f}（{c[exit_c] / c[t] - 1:+.2%}），RSI {r[exit_c]:.1f}")
peak = c.loc["2024-02-21":"2024-06-30"].idxmax()
low_after = c.loc["2024-02-21":"2024-06-30"].loc[peak:].idxmin()
print(f"之后的最高收盘：{c[peak]:,.2f}（{peak.date()}，{c[peak] / c[t] - 1:+.2%}）；"
      f"到 6 月底的最低收盘 {c[low_after]:,.2f}（{low_after.date()}，{c[low_after] / c[t] - 1:+.2%}）")
events = []
for name, df in markets.items():
    close = df["close"]
    count = run_length(I.rsi(close) > 70)
    later = {n: close.shift(-n) / close - 1 for n in [10, 20, 60]}
    for when in count.index[count == 12]:
        events.append({"标的": name, "第 12 天": when.date(), "RSI": I.rsi(close)[when],
                       "10 根后": later[10][when], "20 根后": later[20][when], "60 根后": later[60][when],
                       "同标的任意一天 20 根后": later[20].mean()})
events = pd.DataFrame(events)
print(events.to_string(index=False, formatters={"RSI": "{:.1f}".format} | {k: "{:+.2%}".format for k in events.columns[3:]}))
print(f"20 根后上涨的次数：{int((events['20 根后'] > 0).sum())} / {events['20 根后'].notna().sum()}")

print("===== 片段 9：同一条规则，按市场状态分开统计 =====")
rng = np.random.default_rng(0)
simple = {"up": "上升", "down": "下降", "range": "震荡", "transition_up": "过渡", "transition_down": "过渡"}


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


def crossed(value, level, downward):
    """value 跌破（downward=True）或升破 level 的那一根。"""
    if downward:
        return (value < level) & (value.shift(1) >= level)
    return (value > level) & (value.shift(1) <= level)


def two_views(df, threshold):
    """实时的市场状态（第 11 篇），和「每个摆动点一出现就知道」的事后状态。"""
    close = df["close"]
    swings = X.zigzag(close, threshold)
    live = X.market_state(X.trend_state(swings, close, close), close).map(simple)
    hindsight_swings = swings.assign(confirmed_at=swings["time"])
    hindsight = X.market_state(X.trend_state(hindsight_swings, close, close), close).map(simple)
    return live, hindsight


def rule_by_state(df, views, flag, direction, which=("实时", "事后")):
    """每一根 K 线都按 direction 入场、看先碰到哪条 2 ATR 线；比较信号 K 线和同状态的全部 K 线。"""
    close = df["close"]
    atr = X.wilder_smooth(X.true_range(df["high"], df["low"], close), 14)
    ok = atr.notna() & views[0].notna() & views[1].notna()
    times = close.index[ok.to_numpy()]
    outcome = pd.Series(X.first_passage(close, df["high"], df["low"], atr, times, [direction] * len(times)), index=times)
    flag = flag.reindex(times).fillna(False).astype(bool)
    rows = []
    for s in ["上升", "震荡", "下降", "过渡"]:
        row = {"状态": s}
        for label, view in zip(("实时", "事后"), views):
            if label not in which:
                continue
            m = (view.reindex(times) == s).to_numpy()
            _, p = label_test(outcome[m], flag[m])
            hit = outcome[m][flag[m]]
            row |= {f"{label} 次数": int(hit.notna().sum()), f"{label} 顺向": hit.mean(),
                    f"{label} 同状态": outcome[m].mean(), f"{label} p": p}
        rows.append(row)
    return pd.DataFrame(rows)


datasets = [("BTC 日线", day, 0.10), ("SPY 日线", spy, 0.03), ("AAPL 日线", aapl, 0.05),
            ("BTC 4 小时线", h4, 0.04), ("BTC 1 小时线", h1, 0.02)]
views = {name: two_views(df, threshold) for name, df, threshold in datasets}
number = lambda v: "" if pd.isna(v) else f"{v:.3f}"


def show(rows):
    table = pd.DataFrame(rows)
    for column in [col for col in table.columns if col.endswith("次数")]:
        table[column] = table[column].astype(int)
    return table.to_string(index=False, float_format=number)


for title, level, downward, direction in [("超卖买入：RSI 跌破 30，做多", 30, True, 1), ("超买卖出：RSI 升破 70，做空", 70, False, -1)]:
    print(title)
    for name, df, threshold in datasets:
        table = rule_by_state(df, views[name], crossed(I.rsi(df["close"]), level, downward), direction)
        table.insert(0, "数据", name)
        print(table.to_string(index=False, float_format=number))

print("===== 片段 10：事后的状态为什么这么准 =====")
close = h1["close"]
atr = X.wilder_smooth(X.true_range(h1["high"], h1["low"], close), 14)
signal = crossed(I.rsi(close), 30, True) & atr.notna()
live, hindsight = (v[signal].rename(k) for k, v in zip(["实时", "事后"], views["BTC 1 小时线"]))
both = pd.concat([live, hindsight], axis=1).dropna()
both["顺向"] = X.first_passage(close, h1["high"], h1["low"], atr, both.index, [1] * len(both))
print("BTC 1 小时线的超卖买入信号：行是实时状态，列是事后状态")
print(pd.crosstab(both["实时"], both["事后"], margins=True, margins_name="合计").to_string())
print("先碰到上方 2 ATR 线的比例：")
print(both.pivot_table(index="实时", columns="事后", values="顺向", aggfunc="mean").to_string(float_format=number))

print("===== 片段 11：趋势里的顺势用法 =====")
rows = []
for name, df, threshold in datasets:
    rr = I.rsi(df["close"])
    for label, flag, direction, state in [("上升状态里 RSI 跌破 40，做多", crossed(rr, 40, True), 1, "上升"),
                                          ("下降状态里 RSI 升破 60，做空", crossed(rr, 60, False), -1, "下降")]:
        table = rule_by_state(df, views[name], flag, direction, which=("实时",)).set_index("状态")
        rows.append({"数据": name, "规则": label} | table.loc[state].to_dict())
print(show(rows))

print("===== 片段 12：BTC 4 小时线和 1 小时线，扣掉同一个月 =====")
for name, df, threshold in datasets[3:]:
    close = df["close"]
    rr = I.rsi(close)
    atr = X.wilder_smooth(X.true_range(df["high"], df["low"], close), 14)
    times = close.index[(atr.notna() & rr.notna()).to_numpy()]
    month = times.tz_localize(None).to_period("M")
    for label, flag, direction in [("超卖买入", crossed(rr, 30, True), 1), ("超买卖出", crossed(rr, 70, False), -1)]:
        outcome = pd.Series(X.first_passage(close, df["high"], df["low"], atr, times, [direction] * len(times)), index=times)
        f = flag.reindex(times).to_numpy()
        _, p = label_test(outcome, f)
        _, p_month = label_test(outcome - outcome.groupby(month).transform("mean"), f)
        month_average = outcome.groupby(month).transform("mean")[f].mean()
        print(f"{name} {label}：{int(outcome[f].notna().sum())} 次，顺向 {outcome[f].mean():.1%}，全部 K 线 {outcome.mean():.1%}（p {p:.3f}）；"
              f"信号所在月份的全部 K 线 {month_average:.1%}，扣掉同月之后 p {p_month:.3f}")

print("===== 片段 13：换成 Stochastic =====")
for title, column, level, downward, direction in [("%K 跌破 20，做多", "k", 20, True, 1), ("%K 升破 80，做空", "k", 80, False, -1)]:
    print(title)
    rows = []
    for name, df, threshold in datasets:
        s = I.stochastic(df["high"], df["low"], df["close"])
        table = rule_by_state(df, views[name], crossed(s[column], level, downward), direction).set_index("状态")
        rows += [{"数据": name, "状态": state} | table.loc[state].to_dict() for state in ["震荡", "上升", "下降"]]
    print(show(rows))
