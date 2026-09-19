"""生成第 14 篇的插图：python 14_figures.py <输出目录>（在 talab 项目根目录运行）。"""
import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from talab import bars as B, data as D, indicators as I, plot as P, structure as X

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
money = FuncFormatter(lambda v, _: f"{v:,.0f}")
five = {"up": "上升", "down": "下降", "range": "震荡", "transition_up": "向上过渡", "transition_down": "向下过渡"}
simple = {"up": "上升", "down": "下降", "range": "震荡", "transition_up": "过渡", "transition_down": "过渡"}

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
c = day["close"]
r = I.rsi(c)
st = I.stochastic(day["high"], day["low"], c)


def candles_with_oscillators(bars, title, marks=()):
    fig, (ax, ar, ak) = plt.subplots(3, 1, figsize=(11, 7.2), dpi=150, sharex=True,
                                     gridspec_kw={"height_ratios": [2.2, 1.1, 1.1]})
    xs = np.arange(len(bars))
    for x, (o, h, l, cl) in zip(xs, bars[["open", "high", "low", "close"]].to_numpy()):
        color = UP if cl >= o else DOWN
        ax.vlines(x, l, h, color=color, linewidth=0.8)
        ax.add_patch(Rectangle((x - 0.35, min(o, cl)), 0.7, max(abs(cl - o), 1e-6), facecolor=color, edgecolor=color))
    rr, ss = r.reindex(bars.index), st.reindex(bars.index)
    ar.plot(xs, rr, color=PURPLE, linewidth=1.3, label="RSI(14)")
    ar.fill_between(xs, 70, rr, where=rr > 70, color=DOWN, alpha=0.25, interpolate=True)
    ar.fill_between(xs, 30, rr, where=rr < 30, color=UP, alpha=0.25, interpolate=True)
    ak.plot(xs, ss["k"], color=BLUE, linewidth=1.2, label="%K(14, 3)")
    ak.plot(xs, ss["d"], color=ORANGE, linewidth=1.2, label="%D(3)")
    for axis, hi_level, lo_level in [(ar, 70, 30), (ak, 80, 20)]:
        axis.axhline(hi_level, color=DOWN, linewidth=0.7, linestyle="--")
        axis.axhline(lo_level, color=UP, linewidth=0.7, linestyle="--")
        axis.set_ylim(0, 100); axis.set_yticks([0, lo_level, 50, hi_level, 100]); axis.grid(alpha=0.25)
        axis.legend(fontsize=8.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False)
    where = {t: k for k, t in enumerate(bars.index)}
    for when, text, dx, dy in marks:
        k = where[pd.Timestamp(when, tz="UTC")]
        ax.annotate(text, (k, bars["high"].iloc[k]), textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=9,
                    arrowprops={"arrowstyle": "->", "color": "#555"})
    ticks = [k for k in range(len(bars)) if k == 0 or bars.index[k].month != bars.index[k - 1].month]
    ak.set_xticks(ticks)
    ak.set_xticklabels([bars.index[k].strftime("%Y-%m") for k in ticks], fontsize=8.5)
    ax.yaxis.set_major_formatter(money)
    ax.set_title(title, fontsize=12); ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig, ax


# 1. 决策点
bars = day.loc["2023-12-01":"2024-02-20"]
fig, ax = candles_with_oscillators(bars, "BTCUSDT 日线，2023-12-01 至 2024-02-20；下方是 RSI(14) 和 Stochastic(14, 3, 3)",
                                   marks=[("2024-01-23", "1 月 23 日\n收盘 39,898", 0, 60), ("2024-02-09", "2 月 9 日\nRSI 升破 70", -40, 25),
                                          ("2024-02-20", "2 月 20 日\n连续第 12 天", -10, 30)])
lo, hi = ax.get_ylim(); ax.set_ylim(lo, hi + (hi - lo) * 0.2)
fig.savefig(out / "decision.png"); plt.close(fig)

# 2. RSI 和「平均涨幅 ÷ 波动」
smooth = lambda s: I.ema(s, 14, alpha=1 / 14)
lr = np.log(c).diff()
ratio = smooth(lr) / np.sqrt(smooth(lr ** 2) - smooth(lr) ** 2)
ok = r.notna() & ratio.notna()
fig, ax = plt.subplots(figsize=(8.5, 5.6), dpi=150)
ax.scatter(ratio[ok], r[ok], s=4, alpha=0.3, color=GRAY, label="BTC 日线，每个点是一天")
grid = np.linspace(-0.8, 0.8, 50)
ax.plot(grid, 50 + 50 / np.sqrt(2 / np.pi) * grid, color=PURPLE, linewidth=2, label="正态分布下的近似：RSI ≈ 50 + 62.7 × 比值")
ax.axhline(70, color=DOWN, linestyle="--", linewidth=0.8); ax.axhline(30, color=UP, linestyle="--", linewidth=0.8)
ax.axvline(0.32, color=DOWN, linestyle=":", linewidth=0.8); ax.axvline(-0.32, color=UP, linestyle=":", linewidth=0.8)
ax.annotate("RSI = 70 ≈ 平均涨幅是波动的 0.32 倍", (0.32, 70), textcoords="offset points", xytext=(10, -40), fontsize=9,
            arrowprops={"arrowstyle": "->", "color": "#555"})
ax.set_xlim(-0.8, 0.8); ax.set_ylim(0, 100)
ax.set_xlabel("最近一段（Wilder 平滑）的 平均对数收益 ÷ 收益的标准差"); ax.set_ylabel("RSI(14)")
ax.set_title("RSI 几乎就是「最近涨得稳不稳」：平均涨幅相对波动的比值", fontsize=12)
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "rsi-vs-trend.png"); plt.close(fig)

# 3. 揭晓
bars = day.loc["2023-12-01":"2024-05-31"]
fig, ax = candles_with_oscillators(bars, "揭晓：BTCUSDT 日线，2023-12-01 至 2024-05-31",
                                   marks=[("2024-02-20", "2 月 20 日\n决策点", -45, 45), ("2024-02-22", "2 月 22 日\nRSI 回到 70 以下", 95, -50),
                                          ("2024-03-13", "3 月 13 日\n收盘 73,072", 55, 5)])
lo, hi = ax.get_ylim(); ax.set_ylim(lo, hi + (hi - lo) * 0.2)
fig.savefig(out / "reveal.png"); plt.close(fig)

# 4. 不同市场状态里 RSI 的位置
thresholds = {"SPY": (spy, 0.03), "AAPL": (aapl, 0.05), "BTC": (day, 0.10)}
states = ["上升", "向上过渡", "震荡", "向下过渡", "下降"]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150, sharey=True)
for axis, (name, (df, threshold)) in zip(axes, thresholds.items()):
    close = df["close"]
    rr = I.rsi(close)
    state = X.market_state(X.trend_state(X.zigzag(close, threshold), close, close), close).map(five)
    high_share = [(rr[(state == s) & rr.notna()] > 70).mean() for s in states]
    low_share = [(rr[(state == s) & rr.notna()] < 30).mean() for s in states]
    xs = np.arange(len(states))
    axis.bar(xs - 0.2, high_share, 0.4, color=DOWN, alpha=0.8, label="RSI > 70 的 K 线占比")
    axis.bar(xs + 0.2, low_share, 0.4, color=UP, alpha=0.8, label="RSI < 30 的 K 线占比")
    axis.set_xticks(xs); axis.set_xticklabels(states, fontsize=9)
    axis.set_title(f"{name} 日线（ZigZag {threshold:.0%}）", fontsize=11); axis.grid(alpha=0.25, axis="y")
    axis.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
axes[0].legend(fontsize=9, loc="upper right")
fig.suptitle("实时市场状态（第 11 篇）里，RSI 的极端值出现在哪里", fontsize=12)
fig.tight_layout(); fig.savefig(out / "state-share.png"); plt.close(fig)

# 5. 实时状态和事后状态：BTC 1 小时线的一个超卖信号
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
h1 = B.resample_ohlcv(minute, "1h", traded_only=True)
del minute
close = h1["close"]
swings = X.zigzag(close, 0.02)
live = X.trend_state(swings, close, close)
hindsight = X.trend_state(swings.assign(confirmed_at=swings["time"]), close, close)
live_state = X.market_state(live, close).map(simple)
hindsight_state = X.market_state(hindsight, close).map(simple)
signal = (I.rsi(close) < 30) & (I.rsi(close).shift(1) >= 30)
candidates = signal[signal & (live_state == "过渡") & (hindsight_state == "震荡")].index
when = candidates[candidates >= "2025-01-01"][0]
k = close.index.get_loc(when)
window = slice(k - 60, k + 41)
seg = close.iloc[window]
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
ax.plot(seg.index, seg, color="black", linewidth=1.0, label="收盘价（1 小时）")
ax.step(seg.index, live["last_low"].iloc[window], where="post", color=BLUE, linewidth=1.4, label=f"实时：最近一个已确认的低点（状态「{live_state[when]}」）")
ax.step(seg.index, hindsight["last_low"].iloc[window], where="post", color=ORANGE, linewidth=1.4, linestyle="--",
        label=f"事后：低点一出现就算数（状态「{hindsight_state[when]}」）")
ax.plot(when, close[when], "o", color=UP, markersize=8)
ax.annotate(f"RSI 跌破 30\n{when.strftime('%Y-%m-%d %H:%M')} UTC", (when, close[when]), textcoords="offset points", xytext=(-330, 40),
            fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
ax.yaxis.set_major_formatter(money)
ax.set_title("同一个超卖信号：实时看是「跌破了前低」，事后看是「前低守住了」", fontsize=12)
ax.legend(fontsize=9, loc="upper right"); ax.grid(alpha=0.25)
fig.autofmt_xdate()
fig.tight_layout(); fig.savefig(out / "live-vs-hindsight.png"); plt.close(fig)
print("示例信号：", when)
print("ok")
