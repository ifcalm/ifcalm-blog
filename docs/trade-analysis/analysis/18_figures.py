"""生成第 18 篇的插图：python 18_figures.py <输出目录>（在 talab 项目根目录运行）。

数据、统计结果直接借用 18_dow_fibonacci.py（执行到片段 8 之前，不打印输出），避免两份代码不一致。
"""
import contextlib
import io
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
source = Path(__file__).with_name("18_dow_fibonacci.py").read_text(encoding="utf-8")
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(source.split('print("===== 片段 8')[0], ns)
spy, h1, Pt, X = ns["spy"], ns["h1"], ns["Pt"], ns["X"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")


def draw_candles(axis, bars):
    for x, (o, h, l, c) in enumerate(bars[Pt.OHLC].to_numpy()):
        color = UP if c >= o else DOWN
        axis.vlines(x, l, h, color=color, linewidth=0.8)
        axis.add_patch(Rectangle((x - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-9), facecolor=color, edgecolor=color))


def month_ticks(axis, index):
    ticks = [k for k in range(len(index)) if k == 0 or index[k].month != index[k - 1].month]
    axis.set_xticks(ticks)
    axis.set_xticklabels([index[k].strftime("%Y-%m") for k in ticks], fontsize=9)


def draw_levels(axis, levels, x0, x1):
    for ratio, price in levels.items():
        color = DOWN if ratio == 0.618 else GRAY
        axis.hlines(price, x0, x1, color=color, linewidth=1.2 if ratio == 0.618 else 0.8, linestyle="--")
        axis.text(x1 + 1, price, f"{ratio:.1%}  {price:.2f}", color=color, fontsize=8.5, va="center")


start, end = ns["start"], ns["end"]
levels = Pt.retracement_levels(start, end)

# 1. 决策点
bars = spy.loc["2024-07-15":"2025-03-14"]
where = {x: k for k, x in enumerate(bars.index)}
fig, ax = plt.subplots(figsize=(11.5, 5.6), dpi=150)
draw_candles(ax, bars)
k0, k1 = where[pd.Timestamp("2024-08-05")], where[pd.Timestamp("2025-02-19")]
ax.plot([k0, k1], [start, end], color=BLUE, linewidth=1.2)
draw_levels(ax, levels, k0, len(bars) + 2)
ax.annotate("2024-08-05\n收盘 517.38", (k0, start), textcoords="offset points", xytext=(0, -35), ha="center", fontsize=9)
ax.annotate("2025-02-19\n收盘 612.93", (k1, end), textcoords="offset points", xytext=(-75, -5), ha="center", fontsize=9)
ax.annotate("3 月 11 日、13 日\n最低价碰到 61.8%\n3 月 14 日收盘 562.81", (where[pd.Timestamp("2025-03-13")], bars["low"]["2025-03-13"]),
            textcoords="offset points", xytext=(-240, -25), fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
ax.set_xlim(-2, len(bars) + 22)
month_ticks(ax, bars.index)
ax.grid(alpha=0.25)
ax.set_title("SPY 日线，2024-07-15 至 2025-03-14；斐波那契回撤位按收盘价 ZigZag 5% 的一段画", fontsize=12)
fig.tight_layout(); fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 揭晓
bars = spy.loc["2024-07-15":"2025-07-15"]
where = {x: k for k, x in enumerate(bars.index)}
fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=150)
draw_candles(ax, bars)
k0, k1 = where[pd.Timestamp("2024-08-05")], where[pd.Timestamp("2025-02-19")]
ax.plot([k0, k1], [start, end], color=BLUE, linewidth=1.2)
draw_levels(ax, levels, k0, len(bars) + 2)
for when, text, dx, dy in [("2025-03-14", "决策点", -70, 70), ("2025-03-25", "3 月 25 日\n收盘 575.46", 10, 45),
                           ("2025-04-03", "4 月 3 日\n收盘 536.70", -60, -30), ("2025-04-08", "4 月 8 日\n收盘 496.48", 40, -25),
                           ("2025-06-27", "6 月 27 日\n收盘 614.91", -20, 30)]:
    k = where[pd.Timestamp(when)]
    y = bars["high"].iloc[k] if dy > 0 else bars["low"].iloc[k]
    ax.annotate(text, (k, y), textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=9,
                arrowprops={"arrowstyle": "->", "color": "#555"})
ax.set_xlim(-2, len(bars) + 30)
month_ticks(ax, bars.index)
ax.grid(alpha=0.25)
ax.set_title("揭晓：SPY 日线，2024-07-15 至 2025-07-15", fontsize=12)
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 3. 回撤比例的分布：BTC 1 小时线，真实和打乱
rng = np.random.default_rng(1)
real = Pt.swing_ratios(X.zigzag(h1["close"], 0.01))["retracement"].dropna()
shuffled = pd.concat([Pt.swing_ratios(X.zigzag(ns["shuffle_bars"](h1, rng)["close"], 0.01))["retracement"].dropna()
                      for _ in range(5)])
bins = np.arange(0, 1.0001, 0.02)
fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)
ax.hist(real[real < 1], bins=bins, density=True, color=BLUE, alpha=0.6, label=f"真实的 BTC 1 小时线（{(real < 1).sum()} 段）")
ax.hist(shuffled[shuffled < 1], bins=bins, density=True, histtype="step", color="black", linewidth=1.3,
        label="把 K 线顺序打乱之后（5 次合在一起）")
top = ax.get_ylim()[1]
ax.set_ylim(0, top * 1.18)
for f in Pt.FIB_RETRACEMENTS:
    ax.axvline(f, color=DOWN, linestyle="--", linewidth=1)
    ax.text(f, top * 1.08, f"{f:.1%}", color=DOWN, ha="center", fontsize=9, backgroundcolor="white")
ax.set_xlabel("回撤比例 = 这一段的长度 ÷ 前一段的长度（只看小于 1 的）"); ax.set_ylabel("密度")
ax.set_title("回撤比例的分布：斐波那契比例的位置上没有尖峰", fontsize=12)
ax.legend(fontsize=9, loc="lower right"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "ratio-histogram.png"); plt.close(fig)

# 4. 「停住」的比例随回撤比例的变化（不平滑；圆点是斐波那契比例本身）
curves = ns["curves"]
fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
for name, color in zip(["BTC 日线", "BTC 4 小时线", "BTC 1 小时线"], [PURPLE, UP, GRAY]):
    curve = curves[name]
    on_grid = curve[np.isclose(curve.index * 100, np.round(curve.index * 100))]
    ax.plot(on_grid.index, on_grid, color=color, linewidth=1.1, label=f"{name}：每 0.01 一个比例")
    ax.plot(list(Pt.FIB_RETRACEMENTS), curve.reindex(Pt.FIB_RETRACEMENTS), "o", color=color, markersize=7,
            markeredgecolor="black")
for f in Pt.FIB_RETRACEMENTS:
    ax.axvline(f, color=DOWN, linestyle="--", linewidth=0.8)
ax.set_xlim(0.14, 0.86)
ax.yaxis.set_major_formatter(percent)
ax.set_xlabel("回撤比例"); ax.set_ylabel("碰到之后「停住」的比例")
ax.set_title("回撤到各个比例之后停住的比例：斐波那契比例（圆点）落在曲线的起伏之中，没有突出", fontsize=12)
ax.legend(fontsize=9, loc="upper right"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "held-curve.png"); plt.close(fig)
print("ok")
