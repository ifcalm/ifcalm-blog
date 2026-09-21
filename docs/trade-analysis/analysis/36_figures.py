"""生成番外篇的插图：python 36_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 36_book.py（整段执行，不打印输出）。⚠️ 读 1,300 多个盘口文件约两分钟。
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
from matplotlib.ticker import FuncFormatter

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(Path(__file__).with_name("36_book.py").read_text(encoding="utf-8"), ns)
B, SE = ns["B"], ns["SE"]
depth, ticker, um, book = ns["depth"], ns["ticker"], ns["um"], ns["book"]
CRASH, crashes, quiet = ns["CRASH"], ns["crashes"], ns["quiet"]
level_after, WINDOWS, tilt_power = ns["level_after"], ns["WINDOWS"], ns["tilt_power"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")
million = FuncFormatter(lambda v, _: f"{v / 1e6:,.0f}M")
LEFT = CRASH - pd.Timedelta(minutes=25)
RIGHT = CRASH + pd.Timedelta(minutes=25)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(out / name, bbox_inches="tight")
    plt.close(fig)
    print("写出", out / name)


def price_panel(ax):
    window = um.loc[LEFT:RIGHT, "close"]
    ax.plot(window.index, window.to_numpy(), color=GRAY, linewidth=1.5)
    ax.axvline(CRASH, color=DOWN, linestyle="--", linewidth=1.1)
    ax.set_ylabel("BTC 永续（美元）")
    ax.grid(alpha=0.25)


# 图 1：决策点——第 28 篇量到的那一半
fig, axes = plt.subplots(2, 1, figsize=(12.0, 6.2), dpi=150, sharex=True,
                         gridspec_kw={"height_ratios": [2, 1]})
price_panel(axes[0])
low = um.loc[LEFT:RIGHT, "low"].min()
axes[0].annotate(f"{CRASH:%H:%M} 那一分钟\n收在 {um.loc[CRASH, 'close']:,.0f}，最低 {um.loc[CRASH, 'low']:,.0f}",
                 (CRASH, um.loc[CRASH, "close"]), textcoords="offset points", xytext=(-176, 30),
                 fontsize=9.5, color=DOWN, arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
axes[0].set_title(f"{CRASH:%Y-%m-%d} 21:44 UTC：BTC 永续 60 分钟跌 "
                  f"{abs(um['close'].pct_change(60).loc[CRASH]):.2%}")
spread = ticker.loc[LEFT:RIGHT]
axes[1].plot(spread.index, spread["最宽价差"].to_numpy(), color=ORANGE, linewidth=1.4,
             label="那一分钟最宽的价差")
axes[1].plot(spread.index, spread["价差"].to_numpy(), color=BLUE, linewidth=1.4, label="分钟平均价差")
axes[1].set_yscale("log")
axes[1].set_yticks([0.01, 0.1, 1, 10, 100])
axes[1].set_yticklabels(["0.01", "0.1", "1", "10", "100"])
axes[1].yaxis.set_minor_formatter(plt.NullFormatter())
axes[1].axvline(CRASH, color=DOWN, linestyle="--", linewidth=1.1)
axes[1].set_ylabel("买卖价差（基点，对数）")
axes[1].set_title(f"第 28 篇量到的那一半：最宽到过 {spread['最宽价差'].max():.0f} 个基点，"
                  f"而当天中位只有 {ticker.loc['2023-08-17', '价差'].median():.4f}")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25, which="both")
save(fig, "decision.png")

# 图 2：揭晓——柜台后面还有多少钱
fig, axes = plt.subplots(2, 1, figsize=(12.0, 6.6), dpi=150, sharex=True,
                         gridspec_kw={"height_ratios": [1, 2]})
price_panel(axes[0])
axes[0].set_title("同一段时间，加上盘口深度")
piece = book.loc[LEFT:RIGHT]
axes[1].plot(piece.index, piece["买侧"].to_numpy(), color=UP, linewidth=1.8, label="买侧（现价下方 1% 以内）")
axes[1].plot(piece.index, piece["卖侧"].to_numpy(), color=DOWN, linewidth=1.4, label="卖侧（上方 1% 以内）")
normal = book.loc[CRASH - pd.Timedelta(hours=24):CRASH - pd.Timedelta(minutes=30), "买侧"].median()
axes[1].axhline(normal, color=GRAY, linestyle=":", linewidth=1.4)
axes[1].annotate(f"崩盘前 24 小时的中位 {normal / 1e6:,.0f}M", (piece.index[3], normal),
                 textcoords="offset points", xytext=(6, 8), fontsize=9, color=GRAY)
peak_at = piece.loc[CRASH - pd.Timedelta(minutes=5):CRASH, "买侧"].idxmax()
bottom_at = piece.loc[CRASH:CRASH + pd.Timedelta(minutes=5), "买侧"].idxmin()
for spot, colour, text in [(peak_at, PURPLE, f"{peak_at:%H:%M}：{piece.loc[peak_at, '买侧'] / 1e6:,.0f}M\n"
                            f"比平常还厚 {piece.loc[peak_at, '买侧'] / normal - 1:+.0%}"),
                           (bottom_at, DOWN, f"{bottom_at:%H:%M:%S}：只剩 {piece.loc[bottom_at, '买侧'] / 1e6:,.1f}M\n"
                            f"（{piece.loc[bottom_at, '买侧'] / piece.loc[peak_at, '买侧'] - 1:+.1%}）")]:
    axes[1].scatter([spot], [piece.loc[spot, "买侧"]], s=95, color=colour, zorder=5)
    axes[1].annotate(text, (spot, piece.loc[spot, "买侧"]), textcoords="offset points",
                     xytext=(-150, 22) if colour is PURPLE else (28, 40), fontsize=9.5, color=colour,
                     arrowprops=dict(arrowstyle="->", color=colour, linewidth=1.1))
axes[1].yaxis.set_major_formatter(million)
axes[1].set_ylabel("挂单金额（美元）")
axes[1].set_title("三分钟里，现价下方 1% 以内的钱少了九成五")
axes[1].legend(fontsize=9, loc="upper right")
axes[1].grid(alpha=0.25)
save(fig, "reveal.png")

# 图 3：砸下来的钱，和接得住的钱
fig, ax = plt.subplots(figsize=(11.5, 4.6), dpi=150)
flow = um.loc[CRASH - pd.Timedelta(minutes=6):CRASH + pd.Timedelta(minutes=4)]
spots = np.arange(len(flow))
ax.bar(spots, flow["主动卖出"].to_numpy(), 0.62, color=DOWN, alpha=0.85, label="那一分钟的主动卖出")
ax.axhline(normal, color=UP, linewidth=2.0, linestyle="--",
           label=f"崩盘前现价下方 1% 以内的全部承接力（{normal / 1e6:,.0f}M）")
worst = int(np.argmax(flow["主动卖出"].to_numpy()))
ax.annotate(f"{flow.index[worst]:%H:%M} 一分钟砸下 {flow['主动卖出'].iloc[worst] / 1e6:,.0f}M\n"
            f"是全部承接力的 {flow['主动卖出'].iloc[worst] / normal:.1f} 倍",
            (worst, flow["主动卖出"].iloc[worst]), textcoords="offset points", xytext=(-40, -46),
            fontsize=9.5, color=DOWN, arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
ax.set_xticks(spots)
ax.set_xticklabels([f"{t:%H:%M}" for t in flow.index], fontsize=8.5, rotation=45)
ax.yaxis.set_major_formatter(million)
ax.set_ylabel("美元")
ax.set_title("那三分钟：主动卖出 vs 盘口接得住的钱")
ax.legend(fontsize=9)
ax.grid(alpha=0.25, axis="y")
save(fig, "flow.png")

# 图 4：22 次崩盘，和对照组
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.5), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
drops, controls = [], []
for moments, bucket in [(crashes, drops), (quiet, controls)]:
    for moment in moments:
        base = book.loc[moment - pd.Timedelta(hours=24):moment - pd.Timedelta(minutes=30), "买侧"].median()
        bottom = book.loc[moment:moment + pd.Timedelta(minutes=10), "买侧"].min()
        if base and base > 0:
            bucket.append(bottom / base - 1)
order = np.argsort(drops)
axes[0].barh(np.arange(len(drops)), np.array(drops)[order], 0.7, color=DOWN, alpha=0.85)
axes[0].set_yticks(np.arange(len(drops)))
axes[0].set_yticklabels([f"{crashes[i]:%Y-%m-%d}" for i in order], fontsize=8)
axes[0].xaxis.set_major_formatter(percent)
axes[0].set_xlabel("崩盘后十分钟，买侧深度掉了多少")
axes[0].set_title(f"2023 年起 {len(drops)} 次崩盘（60 分钟跌超 5%）")
axes[0].grid(alpha=0.25, axis="x")

axes[1].hist(controls, bins=30, color=BLUE, alpha=0.65, edgecolor="white", density=True,
             label=f"对照：同样大的卖单但价格没崩（{len(controls)} 次）")
axes[1].hist(drops, bins=12, color=DOWN, alpha=0.6, edgecolor="white", density=True,
             label=f"崩盘（{len(drops)} 次）")
for values, colour in [(controls, BLUE), (drops, DOWN)]:
    axes[1].axvline(np.median(values), color=colour, linestyle="--", linewidth=1.8)
axes[1].annotate(f"中位 {np.median(controls):.1%}", (np.median(controls), 3.2),
                 fontsize=9, color=BLUE, ha="center")
axes[1].annotate(f"中位 {np.median(drops):.1%}", (np.median(drops), 2.4),
                 fontsize=9, color=DOWN, ha="center")
axes[1].xaxis.set_major_formatter(percent)
axes[1].set_xlabel("买侧深度掉了多少")
axes[1].set_title("和「同样大的卖单，但价格没崩」比")
axes[1].legend(fontsize=8)
axes[1].grid(alpha=0.25)
save(fig, "events.png")

# 图 5：恢复
fig, ax = plt.subplots(figsize=(10.5, 4.8), dpi=150)
minutes = [5, 10, 20, 30, 60, 120, 240, 480, 1440]
line = [level_after(book["买侧"], crashes, m) for m in minutes]
both_sides = [level_after(book["合计"], crashes, m) for m in minutes]
spread_events = [t for t in crashes if t in ticker.index]
spread_line = [level_after(ticker["价差"], spread_events, m) for m in minutes]
ax.semilogx(minutes, line, color=UP, marker="o", markersize=5, linewidth=2.0, label="买侧深度（22 次）")
ax.semilogx(minutes, both_sides, color=GREEN, marker="s", markersize=4, linewidth=1.4,
            label="两侧合计（22 次）")
ax.semilogx(minutes, spread_line, color=ORANGE, marker="^", markersize=5, linewidth=1.6,
            label="价差（只有 6 次有数据）")
ax.axhline(1.0, color=GRAY, linestyle="--", linewidth=1.4)
ax.annotate("崩盘前的水平", (5.4, 1.02), fontsize=9, color=GRAY)
ax.set_xticks(minutes)
ax.set_xticklabels([f"{m}" for m in minutes])
ax.xaxis.set_minor_formatter(plt.NullFormatter())
ax.yaxis.set_major_formatter(percent)
ax.set_xlabel("崩盘之后多少分钟（对数）")
ax.set_ylabel("相对崩盘前的水平")
ax.set_title("深度少掉一半要一个小时才补到八成；价差一小时就回去了")
ax.legend(fontsize=9)
ax.grid(alpha=0.25, which="both")
save(fig, "recovery.png")

# 图 6：崩盘前的盘口长什么样
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.5), dpi=150)
tilt = B.imbalance(depth, 1.0)
study = SE.event_study(tilt, crashes, before=20, after=20)
axes[0].plot(study.index / 2, study["中位数"].to_numpy(), color=PURPLE, linewidth=2.0, marker="o",
             markersize=3.5)
axes[0].axhline(float(study["平常的中位数"].iloc[0]), color=GRAY, linestyle="--", linewidth=1.4)
axes[0].annotate(f"平常的中位 {study['平常的中位数'].iloc[0]:+.4f}",
                 (-9.5, float(study["平常的中位数"].iloc[0])), textcoords="offset points",
                 xytext=(0, 8), fontsize=9, color=GRAY)
axes[0].axvline(0, color=DOWN, linestyle=":", linewidth=1.4)
peak = float(study["中位数"].loc[0:2].max())
axes[0].annotate(f"崩盘那一刻 {peak:+.3f}\n买盘看上去比平常厚十倍", (0.5, peak),
                 textcoords="offset points", xytext=(18, 16), fontsize=9.5, color=DOWN,
                 arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
axes[0].axhline(0, color="black", linewidth=0.8)
axes[0].set_xlabel("离崩盘多少分钟")
axes[0].set_ylabel("买卖不对称（正 = 买盘更厚）")
axes[0].set_title(f"{len(crashes)} 次崩盘前后的盘口")
axes[0].grid(alpha=0.25)

horizons = list(tilt_power["往后看几分钟"])
real = list(tilt_power["秩相关"])
noise = list(tilt_power["打乱 200 次的 95% 分位"])
spots = np.arange(len(horizons))
axes[1].bar(spots - 0.2, real, 0.4, color=PURPLE, label="真实秩相关")
axes[1].bar(spots + 0.2, noise, 0.4, color=GRAY, label="打乱 200 次的 95% 分位")
for k, value in enumerate(real):
    axes[1].annotate(f"{value:.3f}", (k - 0.2, value), textcoords="offset points", xytext=(0, 3),
                     ha="center", fontsize=9)
axes[1].set_xticks(spots)
axes[1].set_xticklabels([f"{h} 分钟" for h in horizons])
axes[1].set_ylabel("和之后涨跌的秩相关")
axes[1].set_title(f"四个窗口全部显著，但平方之后不到 {tilt_power['秩相关的平方'].max():.4f}")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25, axis="y")
save(fig, "tilt.png")

# 图 7：你的单子有多大
fig, ax = plt.subplots(figsize=(10.5, 4.8), dpi=150)
sizes = np.array([1e5, 3e5, 1e6, 3e6, 1e7, 3e7, 1e8])
usual = book["买侧"].median()
in_crash = float(np.median([book.loc[t:t + pd.Timedelta(minutes=10), "买侧"].min() for t in crashes]))
ax.loglog(sizes, sizes / usual, color=UP, marker="o", markersize=5, linewidth=2.0,
          label=f"平常（买侧中位 {usual / 1e6:,.0f}M）")
ax.loglog(sizes, sizes / in_crash, color=DOWN, marker="s", markersize=5, linewidth=2.0,
          label=f"崩盘那十分钟（中位 {in_crash / 1e6:,.0f}M）")
ax.axhline(1.0, color=GRAY, linestyle="--", linewidth=1.6)
ax.annotate("一张单吃光现价下方 1% 的全部挂单", (1.1e5, 1.15), fontsize=9, color=GRAY)
ax.set_xticks(sizes)
ax.set_xticklabels(["10 万", "30 万", "100 万", "300 万", "1000 万", "3000 万", "1 亿"], fontsize=9)
ax.set_yticks([0.001, 0.01, 0.1, 1, 10])
ax.set_yticklabels(["0.1%", "1%", "10%", "100%", "1000%"])
for which in (ax.xaxis, ax.yaxis):
    which.set_minor_formatter(plt.NullFormatter())
ax.set_xlabel("一张市价卖单多大（美元）")
ax.set_ylabel("占现价下方 1% 承接力的比例")
ax.set_title("同一张单，平常和崩盘时不是一回事")
ax.legend(fontsize=9)
ax.grid(alpha=0.25, which="both")
save(fig, "size.png")
