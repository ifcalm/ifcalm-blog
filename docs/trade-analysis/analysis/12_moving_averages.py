"""第 12 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob

import numpy as np
import pandas as pd
from talab import data as D, indicators as I, stats as St

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
markets = {"SPY": spy, "AAPL": aapl, "BTC": day}
periods_per_year = {"SPY": 252, "AAPL": 252, "BTC": 365}

print("===== 片段 2：决策点 =====")
c = spy["close"]
t = pd.Timestamp("2025-07-01")
table = pd.DataFrame({"收盘": c, "SMA50": I.sma(c, 50), "SMA200": I.sma(c, 200)})
print(table.loc["2025-06-26":"2025-07-01"].round(2).to_string())
low_day = c.loc["2025-03-01":"2025-06-30"].idxmin()
death = c.index[I.cross_below(table["SMA50"], table["SMA200"])][-1]
print(f"4 月最低收盘：{low_day.date()} {c[low_day]:.2f}，到决策点涨了 {c[t] / c[low_day] - 1:.1%}，"
      f"相隔 {c.index.get_loc(t) - c.index.get_loc(low_day)} 个交易日")
print(f"上一次死叉：{death.date()} 收盘 {c[death]:.2f}，到决策点涨了 {c[t] / c[death] - 1:.1%}")
before = c.loc[:"2025-06-30"]
print(f"决策点之前的最高收盘：{before.max():.2f}（{before.idxmax().date()}），更早的高点 {c.loc[:'2025-04-01'].max():.2f}（{c.loc[:'2025-04-01'].idxmax().date()}）")
for name, n in [("50 日", 50), ("200 日", 200)]:
    above = c.index[I.cross_above(c, I.sma(c, n)) & (c.index > low_day)][0]
    print(f"收盘价第一次站上 {name}均线：{above.date()}")
gap = I.bias(c, table["SMA200"])
print(f"决策点的乖离率（相对 200 日均线）：{gap[t]:+.1%}，在 SPY 全部历史里的分位 {(gap.dropna() <= gap[t]).mean():.0%}")

print("===== 片段 3：手算三种均线 =====")
x = pd.Series([10.0, 11, 12, 11, 13, 16])
print(pd.DataFrame({"价格": x, "SMA3": I.sma(x, 3), "WMA3": I.wma(x, 3), "EMA3": I.ema(x, 3)}).round(4).to_string())

print("===== 片段 4：EMA 的初始值 =====")
ours = I.ema(c, 50)
pandas_style = c.ewm(span=50, adjust=False).mean()
diff = (ours - pandas_style).abs()
print(f"第 50 根（第一个值）：talab {ours.iloc[49]:.2f}，pandas {pandas_style.iloc[49]:.2f}，相差 {diff.iloc[49]:.2f}")
for k in [100, 200, 400]:
    print(f"第 {k} 根：相差 {diff.iloc[k - 1]:.4f}")
print(f"相差第一次小于 0.01：第 {int(np.argmax((diff < 0.01).to_numpy())) + 1} 根")

print("===== 片段 5：未来函数 =====")


def backtest_next_open(df, signal):
    """收盘时算出 signal（1 持有、0 空仓），下一根开盘成交。返回每根 K 线的收益率。"""
    held = signal.shift(1).fillna(0.0)                      # 这一根是否持有
    before = held.shift(1).fillna(0.0)                      # 上一根是否持有
    o, close, prev = df["open"], df["close"], df["close"].shift(1)
    r = np.select([(held == 1) & (before == 1), (held == 1) & (before == 0), (held == 0) & (before == 1)],
                  [close / prev - 1, close / o - 1, o / prev - 1], 0.0)
    return pd.Series(r, index=df.index).fillna(0.0)


def annual(r, n):
    return (1 + r).prod() ** (n / len(r)) - 1


for name, df in markets.items():
    start = I.sma(df["close"], 200).first_valid_index()       # 和后面的主线策略用同一个起点
    d = df.loc[start:]
    for n in [5, 20]:
        signal = (df["close"] > I.sma(df["close"], n)).astype(float).loc[start:]
        right = backtest_next_open(d, signal)
        same_day = (signal * d["close"].pct_change()).fillna(0.0)          # 错误 1：当天收盘才知道的信号，吃了当天的收益
        centered = df["close"].rolling(n, center=True).mean()               # 错误 2：居中的均线，用到了后面 n / 2 天
        rising = (centered.diff() > 0).astype(float).loc[start:]
        peek = (rising.shift(1) * d["close"].pct_change()).fillna(0.0)
        print(f"{name} 收盘价在 {n} 日均线上方就持有：正确 {annual(right, periods_per_year[name]):.1%}，"
              f"当天信号 {annual(same_day, periods_per_year[name]):.1%}，"
              f"居中均线向上就持有 {annual(peek, periods_per_year[name]):.1%}，"
              f"买入 {int((signal.diff() == 1).sum())} 次（年化收益）")

print("===== 片段 6：滞后的公式 =====")
rows = []
for n in [20, 50, 200]:
    alpha = 2 / (n + 1)
    rows.append({"n": n, "SMA": I.average_lag(np.ones(n)), "EMA": I.average_lag((1 - alpha) ** np.arange(5000)),
                 "WMA": I.average_lag(np.arange(n, 0, -1))})
print(pd.DataFrame(rows).round(2).to_string(index=False))
ramp = pd.Series(np.arange(300, dtype=float))
for name, f in [("SMA", I.sma), ("EMA", I.ema), ("WMA", I.wma)]:
    lag = (ramp - f(ramp, 30)).dropna()
    print(f"斜坡上的 {name}30：价格减均线 最小 {lag.min():.4f}，最大 {lag.max():.4f}")

print("===== 片段 7：真实价格上的滞后 =====")


def weight_median(weights):
    """权重从最新往前累加，第一次达到一半的位置。"""
    w = np.asarray(weights, dtype=float)
    return int(np.searchsorted(np.cumsum(w) / w.sum(), 0.5 - 1e-9))          # 减一点点，避免浮点误差让 0.5 被算成不到一半


rows = []
for name, df in markets.items():
    log_price = np.log(df["close"])
    for n in [20, 50, 200]:
        alpha = 2 / (n + 1)
        for kind, ma, weights in [("SMA", I.sma(log_price, n), np.ones(n)),
                                  ("EMA", I.ema(log_price, n), (1 - alpha) ** np.arange(5000)),
                                  ("WMA", I.wma(log_price, n), np.arange(n, 0, -1))]:
            error = {k: ((ma - log_price.shift(k)) ** 2).iloc[400:].mean() for k in range(int(0.8 * n))}
            rows.append({"市场": name, "n": n, "均线": kind, "平均滞后": I.average_lag(weights),
                         "权重中位数": weight_median(weights), "最贴合的平移": min(error, key=error.get)})
print(pd.DataFrame(rows).round(1).to_string(index=False))

print("===== 片段 8：同样的滞后，谁更平滑 =====")
rows = []
for name, df in markets.items():
    log_price = np.log(df["close"])
    step = log_price.diff().std()
    for lag in [9.5, 24.5]:
        n_even, n_wma = int(2 * lag + 1), int(round(3 * lag + 1))          # 平均滞后相同的周期
        a = 2 / (n_even + 1)
        for kind, ma, n, theory in [("SMA", I.sma(log_price, n_even), n_even, 1 / np.sqrt(n_even)),
                                    ("EMA", I.ema(log_price, n_even), n_even, np.sqrt(a / (2 - a))),
                                    ("WMA", I.wma(log_price, n_wma), n_wma,
                                     np.sqrt(2 * (2 * n_wma + 1) / (3 * n_wma * (n_wma + 1))))]:
            move = ma.diff().iloc[250:]
            turns = (np.sign(move) != np.sign(move.shift(1))).iloc[1:].sum()
            rows.append({"市场": name, "平均滞后": lag, "均线": f"{kind}{n}", "实测粗糙度": move.std() / step,
                         "随机游走理论": theory, "每年拐头次数": turns / (len(move) / periods_per_year[name])})
print(pd.DataFrame(rows).round(3).to_string(index=False))

print("===== 片段 9：揭晓 =====")
i = c.index.get_loc(t)
for n in [20, 60, 120, 250]:
    print(f"{n} 个交易日后（{c.index[i + n].date()}）：{c.iloc[i + n] / c[t] - 1:+.2%}")
after = c.iloc[i:]
drawdown = after / after.cummax() - 1
print(f"之后最大回撤 {drawdown.min():.1%}（{drawdown.idxmin().date()}），{c.index[-1].date()} 收盘 {c.iloc[-1]:.2f}，"
      f"比决策点 {c.iloc[-1] / c[t] - 1:+.1%}")
f50, f200 = I.sma(c, 50), I.sma(c, 200)
print("决策点之后的交叉：", list(c.index[(I.cross_above(f50, f200) | I.cross_below(f50, f200)) & (c.index > t)].date))

print("===== 片段 10：交叉、多头排列和乖离率 =====")


def rebuild(log_returns):
    return pd.Series(np.exp(np.cumsum(np.asarray(log_returns))))


def golden_gap(log_returns, horizon=20):
    """50 日均线在 200 日均线上方的日子，减去下方的日子：之后 horizon 天的平均对数收益。"""
    p = rebuild(log_returns)
    fast, slow = I.sma(p, 50), I.sma(p, 200)
    later = np.log(p.shift(-horizon) / p)
    return later[fast > slow].mean() - later[fast < slow].mean()


def stack_gap(log_returns, horizon=20):
    """多头排列（收盘 > 20 日 > 50 日 > 200 日均线）的日子，减去其余有 200 日均线的日子。"""
    p = rebuild(log_returns)
    m20, m50, m200 = I.sma(p, 20), I.sma(p, 50), I.sma(p, 200)
    stacked = (p > m20) & (m20 > m50) & (m50 > m200)
    later = np.log(p.shift(-horizon) / p)
    return later[stacked].mean() - later[~stacked & m200.notna()].mean()


def bias_gap(log_returns, horizon=60):
    """相对 200 日均线的乖离率最高 20% 的日子，减去最低 20% 的日子。"""
    p = rebuild(log_returns)
    rank = I.bias(p, I.sma(p, 200)).rank(pct=True)
    later = np.log(p.shift(-horizon) / p)
    return later[rank > 0.8].mean() - later[rank <= 0.2].mean()


for name, df in markets.items():
    close = df["close"]
    fast, slow = I.sma(close, 50), I.sma(close, 200)
    events = close.index[I.cross_above(fast, slow) | I.cross_below(fast, slow)]
    lasted = np.diff(np.r_[[close.index.get_loc(e) for e in events], len(close) - 1])
    stacked = (close > I.sma(close, 20)) & (I.sma(close, 20) > fast) & (fast > slow)
    print(f"{name}：金叉 {int(I.cross_above(fast, slow).sum())} 次，死叉 {int(I.cross_below(fast, slow).sum())} 次，"
          f"每次交叉之后维持的天数 {lasted.tolist()}")
    print(f"   50 日在 200 日上方的时间 {(fast > slow)[slow.notna()].mean():.1%}，多头排列的时间 {stacked[slow.notna()].mean():.1%}")
    log_returns = np.log(close).diff().dropna().reset_index(drop=True)
    for label, stat in [("50 日在上方减下方，之后 20 天", golden_gap), ("多头排列减其余，之后 20 天", stack_gap),
                        ("乖离率最高 20% 减最低 20%，之后 60 天", bias_gap)]:
        res = St.shuffle_test(log_returns, stat, n=1000, seed=0)
        print(f"   {label}：{res['实际值']:+.2%}，打乱后 95% 范围 {res['打乱后 2.5% 分位']:+.2%} ~ "
              f"{res['打乱后 97.5% 分位']:+.2%}，打乱后不小于实际的比例 {res['比例']:.1%}")

print("===== 片段 11：主线策略 v0 =====")


def mainline_v0(df, fast=50, slow=200):
    """主线策略 v0：快均线在慢均线上方就持有，否则空仓。收盘时判断，下一根开盘成交。没有止损、没有仓位管理、没有成本。"""
    close = df["close"]
    signal = (I.sma(close, fast) > I.sma(close, slow)).astype(float)
    return signal.where(I.sma(close, slow).notna())


def summary(r, n, held=None):
    equity = (1 + r).cumprod()
    out = {"总收益": equity.iloc[-1] - 1, "年化": equity.iloc[-1] ** (n / len(r)) - 1,
           "年化波动": r.std() * np.sqrt(n), "最大回撤": (equity / equity.cummax() - 1).min()}
    if held is not None:
        out["在场时间"] = held.mean()
        out["买入次数"] = int((held.diff() == 1).sum() + (held.iloc[0] == 1))
    return out


results = {}
for name, df in markets.items():
    signal = mainline_v0(df)
    start = signal.first_valid_index()
    d, s = df.loc[start:], signal.loc[start:]
    held = s.shift(1).fillna(0.0)
    r = backtest_next_open(d, s)
    results[name] = r
    rows = {"买入持有": summary(d["close"].pct_change().fillna(0.0), periods_per_year[name]),
            "主线 v0": summary(r, periods_per_year[name], held),
            "主线 v0（未来函数：当天信号）": summary((s * d["close"].pct_change()).fillna(0.0), periods_per_year[name], s)}
    print(f"{name}：{start.date()} 至 {d.index[-1].date()}")
    print(pd.DataFrame(rows).T.to_string(float_format=lambda v: f"{v:.3f}"))
    buys, sells = d.index[held.diff() == 1], d.index[held.diff() == -1]
    print("   买入：", [b.date().isoformat() for b in buys], "卖出：", [e.date().isoformat() for e in sells])

print("===== 片段 12：换一组参数 =====")
fasts, slows = [5, 10, 20, 50, 100], [20, 50, 100, 150, 200, 250]
for name, df in markets.items():
    start = df.index[250]                                     # 所有组合用同一个起点：最长的 250 日均线算出来之后
    d = df.loc[start:]
    hold = summary(d["close"].pct_change().fillna(0.0), periods_per_year[name])
    grid = pd.DataFrame(index=pd.Index(fasts, name="快"), columns=pd.Index(slows, name="慢"), dtype=float)
    for fast in fasts:
        for slow in slows:
            if fast < slow:
                s = mainline_v0(df, fast, slow).loc[start:]
                grid.loc[fast, slow] = summary(backtest_next_open(d, s), periods_per_year[name])["年化"]
    values = grid.stack()
    print(f"{name}（{start.date()} 起）：买入持有年化 {hold['年化']:.1%}；30 组参数年化收益（%）：")
    print((grid * 100).round(1).to_string())
    print(f"   50/200 排第 {int(values.rank(ascending=False)[(50, 200)])} 名；超过买入持有的组合 {int((values > hold['年化']).sum())} 组；"
          f"最好 {int(values.idxmax()[0])}/{int(values.idxmax()[1])} {values.max():.1%}，"
          f"最差 {int(values.idxmin()[0])}/{int(values.idxmin()[1])} {values.min():.1%}")
