"""生成第 22 篇的插图：python 22_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 22_orders.py（整段执行，不打印输出）。
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
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(Path(__file__).with_name("22_orders.py").read_text(encoding="utf-8"), ns)
last, mark, day, O = ns["last"], ns["mark"], ns["day"], ns["O"]
gap, slippage, missed, replay = ns["gap"], ns["slippage"], ns["missed"], ns["replay"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")

# 1. 决策点：那一分钟的两套价格
window = slice("2024-04-13 19:55", "2024-04-13 20:25")
bars, marks = last.loc[window], mark.loc[window]
fig, ax = plt.subplots(figsize=(11.5, 5.6), dpi=150)
for x, (o, h, l, c) in enumerate(bars[["open", "high", "low", "close"]].to_numpy()):
    color = UP if c >= o else DOWN
    ax.vlines(x, l, h, color=color, linewidth=0.9)
    ax.add_patch(Rectangle((x - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-9), facecolor=color, edgecolor=color))
ax.plot(range(len(marks)), marks["low"].to_numpy(), color=PURPLE, linewidth=1.6, label="标记价格的最低价")
ax.axhline(60_000, color="black", linestyle="--", linewidth=1.3)
ax.text(0.3, 60_000, " 止损价 60,000", fontsize=9, va="bottom")
k = list(bars.index).index(pd.Timestamp("2024-04-13 20:09", tz="UTC"))
ax.annotate(f"20:09 UTC\n最新价最低 59,652.5（跌破）\n标记价格最低 60,475.7（没跌破）",
            (k, 59_652.5), textcoords="offset points", xytext=(90, 60), fontsize=9,
            arrowprops={"arrowstyle": "->", "color": "#555"})
ticks = [i for i in range(len(bars)) if bars.index[i].minute % 5 == 0]
ax.set_xticks(ticks)
ax.set_xticklabels([bars.index[i].strftime("%H:%M") for i in ticks], fontsize=9)
ax.set_ylabel("BTCUSDT 永续合约"); ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="upper left")
ax.set_title("2024-04-13 20:09 UTC：最新成交价插到 59,652.5，标记价格最低只有 60,475.7", fontsize=12)
fig.tight_layout(); fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 两套价格的偏离
fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=150)
ax.hist(gap * 100, bins=np.linspace(-1.5, 1.5, 121), color=BLUE)
ax.set_yscale("log")
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("最新价最低 ÷ 标记价最低 - 1（百分点）"); ax.set_ylabel("分钟数（对数）")
ax.set_title(f"平时几乎重合：中位数只差 {gap.median() * 100:.3f} 个百分点", fontsize=11)
ax.grid(alpha=0.25)
yearly = (gap <= -0.005).groupby(gap.index.year).sum()
bx.bar(yearly.index, yearly.to_numpy(), color=DOWN)
for x, y in zip(yearly.index, yearly.to_numpy()):
    bx.text(x, y, f"{int(y)}", ha="center", va="bottom", fontsize=9)
bx.set_xlabel("年份"); bx.set_ylabel("分钟数")
bx.set_title("最新价比标记价格低 0.5% 以上的分钟数：越来越少", fontsize=11)
bx.grid(alpha=0.25, axis="y")
fig.tight_layout(); fig.savefig(out / "gap.png"); plt.close(fig)

# 3. 滑点的分布
fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
labels = {"trigger": "回测的假设：成交在止损价", "next_open": "下一分钟开盘价",
          "worst": "这一分钟最差的价格", "5 分钟后": "5 分钟后的价格"}
data = [slippage[name].to_numpy() * 100 for name in labels]
parts = ax.boxplot(data, orientation="horizontal", widths=0.6, showfliers=False, patch_artist=True,
                   tick_labels=list(labels.values()))
for patch, color in zip(parts["boxes"], [GRAY, BLUE, DOWN, ORANGE]):
    patch.set_facecolor(color); patch.set_alpha(0.65)
for k, name in enumerate(labels):
    values = slippage[name] * 100
    ax.scatter([values.quantile(0.99)], [k + 1], marker="|", s=200, color="black", zorder=3)
    ax.text(values.quantile(0.99), k + 1.28, f"99% 分位 {values.quantile(0.99):.2f}", fontsize=8, ha="center")
ax.axvline(0, color="black", linewidth=1)
ax.set_xlabel("滑点（百分点，正数 = 比止损价更不利）")
ax.set_xlim(-1.2, 2.2)
ax.grid(alpha=0.25, axis="x")
ax.set_title(f"{len(slippage)} 次止损触发：成交价口径不同，结果差多少", fontsize=12)
fig.tight_layout(); fig.savefig(out / "slippage.png"); plt.close(fig)

# 4. 止损限价单没成交的那些天
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
ordered = missed.sort_values("又跌了")
positions = range(len(ordered))
ax.bar(positions, ordered["又跌了"] * 100, color=DOWN, alpha=0.8)
ax.bar(positions, ordered["收盘时还差"] * 100, color=GRAY, alpha=0.9, width=0.4, label="当天收盘时离触发价还差多少")
ax.set_xticks(list(positions))
ax.set_xticklabels([str(d) for d in ordered["日期"]], rotation=60, ha="right", fontsize=8)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_ylabel("触发之后价格又跌了多少")
ax.grid(alpha=0.25, axis="y"); ax.legend(fontsize=9, loc="lower right")
ax.set_title(f"止损限价单一小时内没成交的 {len(missed)} 天：仓位还在，价格继续跌", fontsize=12)
fig.tight_layout(); fig.savefig(out / "stoplimit.png"); plt.close(fig)

# 5. 日线回测的止损 vs 分钟线重放
fig, ax = plt.subplots(figsize=(11.5, 4.8), dpi=150)
colors = [DOWN if value > 0 else UP for value in replay["滑点"]]
ax.bar(range(len(replay)), replay["滑点"] * 100, color=colors)
ax.axhline(0, color="black", linewidth=0.8)
ax.axhline(replay["滑点"].median() * 100, color=PURPLE, linestyle="--", linewidth=1.2,
           label=f"中位数 {replay['滑点'].median():.2%}")
ax.set_xticks(range(len(replay)))
ax.set_xticklabels([f"{d}" for d in replay["日期"]], rotation=75, ha="right", fontsize=7)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.1f}%"))
ax.set_ylabel("分钟线成交价相对止损价的滑点")
ax.grid(alpha=0.25, axis="y"); ax.legend(fontsize=9)
ax.set_title(f"主线 v3 的 {len(replay)} 次止损：日线回测假设成交在止损价，分钟线说实际成交在哪", fontsize=12)
fig.tight_layout(); fig.savefig(out / "replay.png"); plt.close(fig)
print("ok")
