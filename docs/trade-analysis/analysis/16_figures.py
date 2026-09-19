"""生成第 16 篇的插图：python 16_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计表直接借用 16_patterns.py（执行到片段 9 之前，不打印输出），避免两份代码不一致。
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
source = Path(__file__).with_name("16_patterns.py").read_text(encoding="utf-8")
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(source.split('print("===== 片段 9')[0], ns)
aapl, shapes, outcome = ns["aapl"], ns["shapes"], ns["table"]
Pt = ns["Pt"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
money = FuncFormatter(lambda v, _: f"{v:,.0f}")


def draw_candles(axis, bars, width=0.7):
    for x, (o, h, l, c) in enumerate(bars[Pt.OHLC].to_numpy()):
        color = UP if c >= o else DOWN
        axis.vlines(x, l, h, color=color, linewidth=1.0)
        axis.add_patch(Rectangle((x - width / 2, min(o, c)), width, max(abs(c - o), 1e-9), facecolor=color, edgecolor=color))


def candles_with_volume(bars, title, marks=()):
    fig, (ax, av) = plt.subplots(2, 1, figsize=(11, 6.2), dpi=150, sharex=True, gridspec_kw={"height_ratios": [2.6, 1]})
    draw_candles(ax, bars)
    colors = np.where(bars["close"].to_numpy() >= bars["open"].to_numpy(), UP, DOWN)
    av.bar(np.arange(len(bars)), bars["volume"] / 1e6, color=colors, width=0.7, alpha=0.8)
    av.set_ylabel("成交量（百万股）", fontsize=9)
    where = {t: k for k, t in enumerate(bars.index)}
    for when, text, dx, dy in marks:
        k = where[pd.Timestamp(when)]
        ax.annotate(text, (k, bars["low"].iloc[k]), textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=9,
                    arrowprops={"arrowstyle": "->", "color": "#555"})
    ticks = [k for k in range(len(bars)) if k == 0 or bars.index[k].month != bars.index[k - 1].month]
    av.set_xticks(ticks)
    av.set_xticklabels([bars.index[k].strftime("%Y-%m") for k in ticks], fontsize=9)
    ax.yaxis.set_major_formatter(money)
    ax.set_title(title, fontsize=12)
    for axis in (ax, av):
        axis.grid(alpha=0.25)
    fig.tight_layout()
    return fig, ax


# 1. 决策点
bars = aapl.loc["2024-11-15":"2025-01-21"]
fig, ax = candles_with_volume(bars, "AAPL 日线，2024-11-15 至 2025-01-21（已按拆股和分红调整）",
                              marks=[("2025-01-21", "1 月 21 日\n锤子线\n收盘 221.04", -70, -30)])
lo, hi = ax.get_ylim()
ax.set_ylim(lo - (hi - lo) * 0.12, hi)
fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 一根 K 线的四个部分，和六个形态
fig = plt.figure(figsize=(12, 6.4), dpi=150)
grid = fig.add_gridspec(2, 4, height_ratios=[1.15, 1])
ax = fig.add_subplot(grid[0, 0])
single = pd.DataFrame([(10, 14, 8, 12)], columns=Pt.OHLC, dtype=float)
draw_candles(ax, single, width=0.5)
for y0, y1, text, color in [(12, 14, "上影线 2", PURPLE), (10, 12, "实体 2", BLUE), (8, 10, "下影线 2", ORANGE)]:
    ax.annotate("", (0.42, y0), (0.42, y1), arrowprops={"arrowstyle": "<->", "color": color})
    ax.text(0.5, (y0 + y1) / 2, text, fontsize=9, color=color, va="center")
ax.annotate("", (-0.42, 8), (-0.42, 14), arrowprops={"arrowstyle": "<->", "color": GRAY})
ax.text(-0.5, 11, "整根高度 6", fontsize=9, color=GRAY, va="center", ha="right", rotation=90)
ax.set_xlim(-1.3, 1.6); ax.set_ylim(7, 15); ax.set_xticks([])
ax.set_title("开 10、高 14、低 8、收 12", fontsize=11)
ax.grid(alpha=0.2)

pieces = {"十字星": [2], "锤子形": [0], "倒锤形": [1], "看涨吞没": [3, 4], "看跌孕线": [6, 7], "早晨之星": [8, 9, 10]}
for k, (name, rows) in enumerate(pieces.items()):
    axis = fig.add_subplot(grid[(k + 1) // 4, (k + 1) % 4])
    draw_candles(axis, shapes.iloc[rows], width=0.55)
    axis.set_title(name, fontsize=11)
    axis.set_xticks([]); axis.set_xlim(-0.8, max(len(rows) - 0.2, 1.2)); axis.grid(alpha=0.2)
fig.suptitle("一根 K 线的四个部分，和这一篇的六个形态（都是按 talab 的规则画的例子）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "anatomy.png"); plt.close(fig)

# 3. 揭晓
bars = aapl.loc["2024-11-15":"2025-04-30"]
fig, ax = candles_with_volume(bars, "揭晓：AAPL 日线，2024-11-15 至 2025-04-30",
                              marks=[("2025-01-21", "1 月 21 日\n锤子线", -20, -50), ("2025-02-24", "2 月 24 日\n收盘 245.59", 0, 40),
                                     ("2025-04-08", "4 月 8 日\n收盘 171.37", 25, -30)])
lo, hi = ax.get_ylim()
ax.set_ylim(lo - (hi - lo) * 0.12, hi + (hi - lo) * 0.08)
fig.savefig(out / "reveal.png"); plt.close(fig)

# 4. 形态之后的胜率减去基准
outcome = outcome.copy()
outcome["差"] = outcome["顺向"] - outcome["全部 K 线"]
labels = [f"{row.形态}（{row.方向}）" for row in outcome.drop_duplicates(["形态", "方向"]).itertuples()]
markets = list(dict.fromkeys(outcome["数据"]))
colors = {name: color for name, color in zip(markets, [BLUE, ORANGE, PURPLE, UP, GRAY])}
fig, ax = plt.subplots(figsize=(11, 5.4), dpi=150)
for k, label in enumerate(labels):
    part = outcome[[f"{row.形态}（{row.方向}）" == label for row in outcome.itertuples()]]
    for row in part.itertuples():
        ax.scatter(row.差, k, s=20 + 40 * np.log10(max(row.次数, 2)), color=colors[row.数据], alpha=0.75,
                   label=row.数据 if k == 0 else None)
ax.axvline(0, color="black", linewidth=1)
ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=10)
ax.set_xlabel("形态出现后「先碰到顺向 2 ATR」的比例 减去 同一组全部 K 线的比例")
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0%}"))
ax.set_title("六个形态在五组数据上的表现：点越靠右越好，圆点大小表示样本数", fontsize=12)
ax.legend(fontsize=9, loc="lower right"); ax.grid(alpha=0.25, axis="x")
ax.invert_yaxis()
fig.tight_layout(); fig.savefig(out / "outcome.png"); plt.close(fig)
print("ok")
