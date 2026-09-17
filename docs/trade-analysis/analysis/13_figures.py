"""生成第 13 篇的插图：python 13_figures.py <输出目录>（在 talab 项目根目录运行）。"""
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

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
c = day["close"]
m = I.macd(c)


def candles_with_macd(bars, title, marks=(), hist_marks=()):
    fig, (ax, am) = plt.subplots(2, 1, figsize=(11, 6.4), dpi=150, sharex=True, gridspec_kw={"height_ratios": [2.2, 1.3]})
    xs = np.arange(len(bars))
    for x, (o, h, l, cl) in zip(xs, bars[["open", "high", "low", "close"]].to_numpy()):
        color = UP if cl >= o else DOWN
        ax.vlines(x, l, h, color=color, linewidth=0.8)
        ax.add_patch(Rectangle((x - 0.35, min(o, cl)), 0.7, max(abs(cl - o), 1e-6), facecolor=color, edgecolor=color))
    mm = m.reindex(bars.index)
    am.bar(xs, mm["hist"], color=np.where(mm["hist"] >= 0, UP, DOWN), width=0.8, alpha=0.7, label="柱")
    am.plot(xs, mm["macd"], color=BLUE, linewidth=1.2, label="MACD 线")
    am.plot(xs, mm["signal"], color=ORANGE, linewidth=1.2, label="信号线")
    am.axhline(0, color="black", linewidth=0.6)
    where = {t: k for k, t in enumerate(bars.index)}
    for when, text, dx, dy in marks:
        k = where[pd.Timestamp(when, tz="UTC")]
        ax.annotate(text, (k, bars["high"].iloc[k]), textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=9,
                    arrowprops={"arrowstyle": "->", "color": "#555"})
    for when, text in hist_marks:
        k = where[pd.Timestamp(when, tz="UTC")]
        am.annotate(text, (k, mm["hist"].iloc[k]), textcoords="offset points", xytext=(0, 18), ha="center", fontsize=8.5,
                    arrowprops={"arrowstyle": "->", "color": "#555"})
    ticks = [k for k in range(len(bars)) if k == 0 or bars.index[k].month != bars.index[k - 1].month]
    am.set_xticks(ticks)
    am.set_xticklabels([bars.index[k].strftime("%Y-%m") for k in ticks], fontsize=8.5)
    ax.yaxis.set_major_formatter(money); am.yaxis.set_major_formatter(money)
    ax.set_title(title, fontsize=12); ax.grid(alpha=0.25); am.grid(alpha=0.25)
    am.legend(fontsize=8.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, frameon=False)
    fig.tight_layout()
    return fig, ax, am


# 1. 决策点
bars = day.loc["2025-06-01":"2025-08-13"]
fig, ax, am = candles_with_macd(bars, "BTCUSDT 日线，2025-06-01 至 2025-08-13；下方是 MACD(12, 26, 9)",
                                marks=[("2025-07-22", "7 月 22 日收盘\n119,954", 0, 30), ("2025-08-13", "8 月 13 日收盘\n123,306 新高", -60, 20)],
                                hist_marks=[("2025-07-14", "柱 1,176"), ("2025-08-13", "柱 526")])
lo, hi = ax.get_ylim(); ax.set_ylim(lo, hi + (hi - lo) * 0.18)
fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 放大倍数和周期
periods = np.logspace(np.log10(2), np.log10(2000), 600)
line = np.abs(I.ema_response(12, periods) - I.ema_response(26, periods))
hist = np.abs((I.ema_response(12, periods) - I.ema_response(26, periods)) * (1 - I.ema_response(9, periods)))
fig, ax = plt.subplots(figsize=(11, 4.4), dpi=150)
ax.plot(periods, np.abs(I.ema_response(12, periods)), color=GRAY, linestyle=":", label="EMA12（低通：周期越长越接近 1）")
ax.plot(periods, np.abs(I.ema_response(26, periods)), color=GRAY, linestyle="--", label="EMA26")
ax.plot(periods, line, color=BLUE, linewidth=2, label="MACD 线 = EMA12 - EMA26（带通）")
ax.plot(periods, hist, color=PURPLE, linewidth=2, label="柱 = MACD 线 - 信号线")
for g, color in [(line, BLUE), (hist, PURPLE)]:
    k = g.argmax()
    ax.plot(periods[k], g[k], "o", color=color)
    ax.annotate(f"最大：周期 {periods[k]:.0f} 根", (periods[k], g[k]), textcoords="offset points", xytext=(8, 8), fontsize=9, color=color)
ax.set_xscale("log")
ax.set_xticks([2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]); ax.set_xticklabels([2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000])
ax.set_xlabel("正弦波的周期（多少根 K 线一个来回，对数坐标）"); ax.set_ylabel("输出振幅 ÷ 输入振幅")
ax.set_title("MACD 对不同周期波动的放大倍数", fontsize=12)
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "gain.png"); plt.close(fig)

# 3. 揭晓
bars = day.loc["2025-06-01":"2025-11-30"]
fig, ax, am = candles_with_macd(bars, "揭晓：BTCUSDT 日线，2025-06-01 至 2025-11-30",
                                marks=[("2025-08-13", "8 月 13 日\n决策点", -45, 25), ("2025-08-18", "8 月 18 日\n高点被确认", 45, 40),
                                       ("2025-10-06", "10 月 6 日\n新高 124,659", -55, 15)])
lo, hi = ax.get_ylim(); ax.set_ylim(lo, hi + (hi - lo) * 0.25)
fig.savefig(out / "reveal.png"); plt.close(fig)

# 4. 事后在图上找背离
bars = day.loc["2024-01-01":"2026-08-31"]
sw = X.zigzag(c, 0.05)
fig, ax = plt.subplots(figsize=(12, 4.8), dpi=150)
ax.plot(bars.index, bars["close"], color="black", linewidth=0.9)
for kind, color, marker in [("bearish", DOWN, "v"), ("bullish", UP, "^")]:
    d = I.divergences(sw, m["hist"], kind)
    d = d[(d["divergence"]) & (d["second"] >= bars.index[0])]
    for r in d.itertuples():
        ax.plot([r.first, r.second], [r.first_price, r.second_price], color=color, linewidth=1.6)
        ax.plot(r.second, r.second_price, marker, color=color, markersize=8)
        ax.axvline(r.confirmed_at, color=color, alpha=0.25, linewidth=0.8)
ax.plot([], [], color=DOWN, marker="v", label="顶背离（画在第二个高点上）")
ax.plot([], [], color=UP, marker="^", label="底背离")
ax.plot([], [], color=GRAY, alpha=0.5, label="竖线：第二个摆动点被确认的那一天")
ax.set_yscale("log"); ax.set_yticks([40000, 60000, 80000, 100000, 120000]); ax.yaxis.set_major_formatter(money)
ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
ax.set_title("BTCUSDT 日线 2024–2026：算法找到的全部背离（ZigZag 5%，MACD 柱）", fontsize=12)
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "divergences-on-chart.png"); plt.close(fig)
print("ok")
