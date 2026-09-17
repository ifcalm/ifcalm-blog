"""生成第 12 篇的插图：python 12_figures.py <输出目录>（在 talab 项目根目录运行）。"""
import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
from talab import data as D, indicators as I, plot as P

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
money = FuncFormatter(lambda v, _: f"{v:,.0f}")

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
markets = {"SPY": spy, "AAPL": aapl, "BTC": day}
c = spy["close"]
m50, m200 = I.sma(c, 50), I.sma(c, 200)


def mark(ax, df, when, text, dy=-34, price="low", dx=0):
    i = df.index.get_loc(pd.Timestamp(when))
    ax.annotate(text, (i, df[price].iloc[i]), textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=9,
                arrowprops={"arrowstyle": "->", "color": "#555"})


# 1. 决策点
x = spy.loc["2024-07-01":"2025-07-01"]
fig, ax, av = P.plot_candles(x, title="SPY 日线，2024-07-01 至 2025-07-01（价格只按拆股调整）",
                             overlays={"50 日 SMA": m50, "200 日 SMA": m200})
mark(ax, x, "2025-04-08", "4 月 8 日\n最低收盘 496.48", dy=10, dx=-70)
mark(ax, x, "2025-04-14", "4 月 14 日 死叉", dy=48, price="high")
mark(ax, x, "2025-07-01", "7 月 1 日 金叉\n收盘 617.65", dy=-6, dx=-190, price="high")
ax.legend(fontsize=9, loc="upper left")
fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 三种均线的权重
n = 20
alpha = 2 / (n + 1)
lags = np.arange(40)
weights = {"SMA20": np.where(lags < n, 1 / n, 0.0),
           "EMA20": alpha * (1 - alpha) ** lags,
           "WMA20": np.where(lags < n, (n - lags) / (n * (n + 1) / 2), 0.0)}
colors = {"SMA20": BLUE, "EMA20": ORANGE, "WMA20": PURPLE}
fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), dpi=150, sharey=True)
for ax, (name, w) in zip(axes, weights.items()):
    full = w if name != "EMA20" else alpha * (1 - alpha) ** np.arange(5000)
    mean_lag = I.average_lag(full)
    median_lag = int(np.searchsorted(np.cumsum(full) / full.sum(), 0.5 - 1e-9))
    ax.bar(lags, w, color=colors[name], alpha=0.75)
    ax.axvline(mean_lag, color="black", linestyle="--", linewidth=1)
    ax.axvline(median_lag, color=GRAY, linestyle=":", linewidth=1.4)
    ax.text(22, max(w) * 1.25, f"平均滞后（虚线）{mean_lag:.1f}", fontsize=9)
    ax.text(22, max(w) * 1.12, f"权重中位数（点线）{median_lag}", fontsize=9, color="#555")
    ax.set_ylim(0, 0.13)
    ax.set_title(name, fontsize=11)
    ax.set_xlabel("离今天几根（0 是今天）")
    ax.grid(alpha=0.25, axis="y")
axes[0].set_ylabel("权重")
fig.suptitle("三种 20 日均线分给过去每一天的权重", fontsize=12)
fig.tight_layout(); fig.savefig(out / "weights.png"); plt.close(fig)

# 3. 同一段行情上的三种均线（平均滞后相同）
x = spy.loc["2020-01-02":"2020-08-31"]
fig, ax, av = P.plot_candles(x, volume=False, title="SPY 日线，2020 年 1 月至 8 月：平均滞后都是 24.5 根的三条均线",
                             overlays={"SMA50": I.sma(c, 50), "EMA50": I.ema(c, 50), "WMA74": I.wma(c, 74)})
ax.legend(fontsize=9, loc="lower left")
fig.savefig(out / "three-averages.png"); plt.close(fig)

# 4. 未来函数
start = m200.first_valid_index()
d = spy.loc[start:]
signal = (c > I.sma(c, 5)).astype(float).loc[start:]
held = signal.shift(1).fillna(0.0)
before = held.shift(1).fillna(0.0)
right = pd.Series(np.select([(held == 1) & (before == 1), (held == 1) & (before == 0), (held == 0) & (before == 1)],
                            [d["close"] / d["close"].shift(1) - 1, d["close"] / d["open"] - 1,
                             d["open"] / d["close"].shift(1) - 1], 0.0), index=d.index).fillna(0.0)
same_day = (signal * d["close"].pct_change()).fillna(0.0)
rising = (c.rolling(5, center=True).mean().diff() > 0).astype(float).loc[start:]
peek = (rising.shift(1) * d["close"].pct_change()).fillna(0.0)
fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)
for r, label, color in [(peek, "居中的 5 日均线向上就持有（用到后面 2 天）", PURPLE), (same_day, "当天收盘的信号，吃当天的收益", DOWN),
                        (d["close"].pct_change().fillna(0.0), "买入持有", GRAY), (right, "正确：收盘出信号，下一根开盘成交", BLUE)]:
    ax.plot((1 + r).cumprod(), label=label, color=color, linewidth=1.3)
ax.set_yscale("log")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g} 倍"))
ax.set_title("同一条规则「SPY 收盘价在 5 日均线上方就持有」，三种写法（对数坐标）", fontsize=12)
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "lookahead.png"); plt.close(fig)

# 5. 揭晓
x = spy.loc["2025-04-01":"2026-09-15"]
fig, ax, av = P.plot_candles(x, title="SPY 日线，2025-04-01 至 2026-09-15", overlays={"50 日 SMA": m50, "200 日 SMA": m200})
mark(ax, x, "2025-07-01", "7 月 1 日 金叉", dy=-40)
mark(ax, x, "2026-03-30", "2026 年 3 月 30 日\n比高点回撤 9.1%", dy=-40)
ax.legend(fontsize=9, loc="upper left")
fig.savefig(out / "reveal.png"); plt.close(fig)

# 6. SPY 全部历史上的金叉和死叉
fig, ax = plt.subplots(figsize=(12, 4.8), dpi=150)
ax.plot(c.index, c, color="black", linewidth=0.8, label="收盘价")
ax.plot(m50.index, m50, color=BLUE, linewidth=1.1, label="50 日 SMA")
ax.plot(m200.index, m200, color=ORANGE, linewidth=1.3, label="200 日 SMA")
ax.fill_between(c.index, c.min() * 0.9, c.max() * 1.05, where=(m50 < m200).to_numpy(), color=DOWN, alpha=0.08,
                label="50 日在 200 日下方")
for when in c.index[I.cross_above(m50, m200)]:
    ax.plot(when, m50[when], "^", color=UP, markersize=9)
for when in c.index[I.cross_below(m50, m200)]:
    ax.plot(when, m50[when], "v", color=DOWN, markersize=9)
ax.set_yscale("log")
ax.yaxis.set_major_locator(LogLocator(base=10, subs=(2, 3, 4, 5, 6, 7, 8)))
ax.yaxis.set_major_formatter(money); ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_ylim(c.min() * 0.9, c.max() * 1.05)
ax.set_title("SPY 的 4 次金叉（▲）和 4 次死叉（▼），2016-09 至 2026-09（对数坐标）", fontsize=12)
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "crosses.png"); plt.close(fig)

# 7. 主线策略 v0
fig, axes = plt.subplots(2, 3, figsize=(14, 6.4), dpi=150, sharex="col", gridspec_kw={"height_ratios": [2.2, 1]})
for k, (name, df) in enumerate(markets.items()):
    close = df["close"]
    sig = (I.sma(close, 50) > I.sma(close, 200)).astype(float).where(I.sma(close, 200).notna())
    begin = sig.first_valid_index()
    dd_, s = df.loc[begin:], sig.loc[begin:]
    h = s.shift(1).fillna(0.0)
    b = h.shift(1).fillna(0.0)
    r = pd.Series(np.select([(h == 1) & (b == 1), (h == 1) & (b == 0), (h == 0) & (b == 1)],
                            [dd_["close"] / dd_["close"].shift(1) - 1, dd_["close"] / dd_["open"] - 1,
                             dd_["open"] / dd_["close"].shift(1) - 1], 0.0), index=dd_.index).fillna(0.0)
    hold = dd_["close"].pct_change().fillna(0.0)
    for series, label, color in [(hold, "买入持有", GRAY), (r, "主线 v0（50/200 SMA）", BLUE)]:
        eq = (1 + series).cumprod()
        axes[0, k].plot(eq, label=label, color=color, linewidth=1.2)
        axes[1, k].plot(eq / eq.cummax() - 1, color=color, linewidth=1)
    axes[0, k].set_yscale("log")
    axes[0, k].yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    axes[0, k].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    axes[0, k].yaxis.set_minor_formatter(NullFormatter())
    axes[1, k].xaxis.set_major_locator(mdates.YearLocator(2))
    axes[1, k].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[0, k].set_title(f"{name}（1 = 起点）", fontsize=11)
    axes[1, k].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    axes[0, k].grid(alpha=0.25); axes[1, k].grid(alpha=0.25)
axes[0, 0].legend(fontsize=9, loc="upper left")
axes[1, 0].set_ylabel("回撤")
fig.suptitle("主线策略 v0 和买入持有：资金曲线（上，对数坐标）和回撤（下），没有扣成本", fontsize=12)
fig.tight_layout(); fig.savefig(out / "mainline-v0.png"); plt.close(fig)

# 8. 参数网格
fasts, slows = [5, 10, 20, 50, 100], [20, 50, 100, 150, 200, 250]
fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), dpi=150)
for ax, (name, df) in zip(axes, markets.items()):
    close = df["close"]
    begin = df.index[250]
    dd_ = df.loc[begin:]
    years = 252 if name != "BTC" else 365
    hold = (1 + dd_["close"].pct_change().fillna(0.0)).prod() ** (years / len(dd_)) - 1
    grid = np.full((len(fasts), len(slows)), np.nan)
    for a, fast in enumerate(fasts):
        for bb, slow in enumerate(slows):
            if fast >= slow:
                continue
            s = (I.sma(close, fast) > I.sma(close, slow)).astype(float).loc[begin:]
            h = s.shift(1).fillna(0.0)
            b = h.shift(1).fillna(0.0)
            r = pd.Series(np.select([(h == 1) & (b == 1), (h == 1) & (b == 0), (h == 0) & (b == 1)],
                                    [dd_["close"] / dd_["close"].shift(1) - 1, dd_["close"] / dd_["open"] - 1,
                                     dd_["open"] / dd_["close"].shift(1) - 1], 0.0), index=dd_.index).fillna(0.0)
            grid[a, bb] = ((1 + r).prod() ** (years / len(r)) - 1 - hold) * 100
    limit = np.nanmax(np.abs(grid))
    im = ax.imshow(grid, cmap="RdYlGn", vmin=-limit, vmax=limit)
    for a in range(len(fasts)):
        for bb in range(len(slows)):
            if not np.isnan(grid[a, bb]):
                weight = "bold" if (fasts[a], slows[bb]) == (50, 200) else "normal"
                ax.text(bb, a, f"{grid[a, bb]:+.1f}", ha="center", va="center", fontsize=8.5, fontweight=weight)
    ax.set_xticks(range(len(slows))); ax.set_xticklabels(slows)
    ax.set_yticks(range(len(fasts))); ax.set_yticklabels(fasts)
    ax.set_xlabel("慢均线"); ax.set_ylabel("快均线")
    ax.set_title(f"{name}：年化收益减买入持有（{hold:.1%}），百分点", fontsize=10.5)
fig.suptitle("30 组快慢均线的年化收益，和买入持有相比（加粗的是 50/200；没有扣成本）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "grid.png"); plt.close(fig)
print("ok")
