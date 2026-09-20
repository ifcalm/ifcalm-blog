"""生成第 34 篇的插图：python 34_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 34_live.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("34_live.py").read_text(encoding="utf-8"), ns)
L, T, I, BT, D = ns["L"], ns["T"], ns["I"], ns["BT"], ns["D"]
LADDERS, WINDOW = ns["LADDERS"], ns["WINDOW"]
btc, spy, aapl, MARKETS, DAY = ns["btc"], ns["spy"], ns["aapl"], ns["MARKETS"], ns["DAY"]
table, book, guards, r = ns["table"], ns["book"], ns["guards"], ns["r"]
mainline_plan = ns["mainline_plan"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")
NAMES = list(MARKETS)
COLORS = [BLUE, ORANGE, DOWN]
WHOLE = L.Filters(tick_size=0.01, step_size=1.0, min_qty=1.0, min_notional=0.0)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(out / name, bbox_inches="tight")
    plt.close(fig)
    print("写出", out / name)


before = btc.loc[:"2021-11-07"]
done = T.turtle(before, T.TurtlePlan())
ahead = pd.concat([btc.loc[:DAY].iloc[-250:-1], btc.loc[DAY:].iloc[:365]])
after = T.turtle(ahead, T.TurtlePlan())["资金曲线"].iloc[-365:]

# 图 1：决策点——手上的回测
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
curve = done["资金曲线"] / done["资金曲线"].iloc[0]
axes[0].semilogy(curve.index, curve.to_numpy(), color=PURPLE, linewidth=1.6, label="海龟")
hold = before["close"] / before["close"].iloc[0]
axes[0].semilogy(hold.index, hold.to_numpy(), color=GRAY, linewidth=1.1, label="买入持有")
axes[0].set_yticks([1, 2, 5, 10, 20])
axes[0].set_yticklabels(["1", "2", "5", "10", "20"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].set_ylabel("本金的几倍（对数）")
axes[0].set_title(f"上线之前手上的回测：{before.index[0].date()} 到 {before.index[-1].date()}")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.25, which="both")
labels = ["年化", "夏普", "卡玛", "逐笔 t 值"]
values = [0.5018, 1.6900, 2.7359, 2.3025]
bars = axes[1].barh(labels[::-1], values[::-1], 0.55, color=[GREEN, GREEN, GREEN, GREEN])
for bar, value in zip(bars, values[::-1]):
    axes[1].annotate(f"{value:.2f}" if value < 1.9 else f"{value:.0%}",
                     (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                     textcoords="offset points", xytext=(6, 0), va="center", fontsize=10)
axes[1].set_xlim(0, 3.4)
axes[1].set_title(f"{len(done['交易'])} 笔交易，每一项都通过了")
axes[1].grid(alpha=0.25, axis="x")
save(fig, "decision.png")

# 图 2：揭晓
fig, ax = plt.subplots(figsize=(12.0, 4.6), dpi=150)
whole = pd.concat([curve, (after / after.iloc[0]) * curve.iloc[-1]])
ax.semilogy(curve.index, curve.to_numpy(), color=PURPLE, linewidth=1.6, label="上线之前（回测）")
tail = (after / after.iloc[0]) * curve.iloc[-1]
ax.semilogy(tail.index, tail.to_numpy(), color=DOWN, linewidth=1.8, label="上线之后（真金白银）")
ax.axvline(DAY, color=GRAY, linestyle="--", linewidth=1.1)
ax.annotate(f"{DAY.date()} 上线\n第一年 {after.iloc[-1] / after.iloc[0] - 1:+.2%}",
            (tail.index[-1], tail.iloc[-1]), textcoords="offset points", xytext=(-150, 26),
            fontsize=10, color=DOWN, arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.2))
ax.set_ylim(0.9, 9.0)
ax.set_yticks([1, 2, 3, 5, 8])
ax.set_yticklabels(["1", "2", "3", "5", "8"])
ax.yaxis.set_minor_formatter(plt.NullFormatter())
ax.set_ylabel("本金的几倍（对数）")
ax.set_title("同一条策略，同一个参数：上线之后的第一年")
ax.legend(fontsize=9, loc="lower right")
ax.grid(alpha=0.25, which="both")
save(fig, "reveal.png")

# 图 3：起点风险
fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.4), dpi=150, gridspec_kw={"width_ratios": [2, 3]})
values = table["第一段收益"].to_numpy()
axes[0].hist(values, bins=40, color=BLUE, alpha=0.7, edgecolor="white")
here = -0.1397
for value, colour, label in [(np.median(values), GRAY, f"中位 {np.median(values):+.1%}"),
                             (np.quantile(values, 0.05), ORANGE,
                              f"5% 分位 {np.quantile(values, 0.05):+.1%}"),
                             (here, DOWN, f"2021-11-08 上线 {here:+.1%}")]:
    axes[0].axvline(value, color=colour, linestyle="--", linewidth=1.6, label=label)
axes[0].xaxis.set_major_formatter(percent)
axes[0].set_xlabel("上线之后第一年的收益")
axes[0].set_ylabel(f"{len(values)} 个上线日中的个数")
axes[0].set_title("从每一天开始上线，第一年赚多少")
axes[0].legend(fontsize=8.5)
axes[0].grid(alpha=0.25)

axes[1].plot(table["上线日"], table["第一段收益"], color=BLUE, linewidth=1.3)
axes[1].fill_between(table["上线日"], table["第一段收益"], 0,
                     where=table["第一段收益"].to_numpy() < 0, color=DOWN, alpha=0.25)
axes[1].axhline(0, color="black", linewidth=0.9)
axes[1].scatter([DAY], [here], marker="v", s=110, color=DOWN, zorder=5)
axes[1].annotate(f"{DAY.date()}\n第 1.7 个百分位", (DAY, here), textcoords="offset points",
                 xytext=(-30, 46), fontsize=9, color=DOWN, ha="center",
                 arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_ylabel("上线后第一年的收益")
axes[1].set_title(f"同一条策略，{len(values)} 个上线日：{(values > 0).mean():.1%} 赚钱，"
                  f"最差 {values.min():+.1%}")
axes[1].grid(alpha=0.25)
save(fig, "starts.png")

# 图 4：预热
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
GO = 2500
warmups = np.arange(30, 1700, 10)
for name, make, colour in [("ATR(14)", lambda d: I.atr(d["high"], d["low"], d["close"], 14), BLUE),
                           ("ATR(20)", lambda d: I.atr(d["high"], d["low"], d["close"], 20), GREEN),
                           ("EMA(50)", lambda d: I.ema(d["close"], 50), ORANGE),
                           ("EMA(200)", lambda d: I.ema(d["close"], 200), DOWN)]:
    whole_value = make(btc).loc[btc.index[GO]]
    errors = []
    for warmup in warmups:
        value = make(btc.iloc[GO - warmup:]).loc[btc.index[GO]]
        errors.append(abs(value - whole_value) / abs(whole_value) if not np.isnan(value) else np.nan)
    axes[0].semilogy(warmups, np.maximum(errors, 1e-16), color=colour, linewidth=1.6, label=name)
axes[0].set_ylim(1e-17, 3.0)
axes[0].set_yticks([1e-16, 1e-13, 1e-10, 1e-7, 1e-4, 1e-1])
axes[0].set_yticklabels(["1e-16", "1e-13", "1e-10", "1e-7", "1e-4", "0.1"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].axhline(1e-6, color=GRAY, linestyle=":", linewidth=1.2)
axes[0].annotate("百万分之一", (1500, 1.4e-6), fontsize=8.5, color=GRAY, ha="right")
axes[0].set_xlabel("上线时带了多少根历史")
axes[0].set_ylabel("和「用全部历史」算出来的相对误差")
axes[0].set_title("递推型指标：预热是渐近的，周期越长要得越多")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.25, which="both")

entry = ((I.sma(btc["close"], 50) > I.sma(btc["close"], 200))
         & (btc["close"] >= btc["close"].rolling(20).max())).fillna(False).to_numpy()
picks = np.arange(20, 205, 5)
chances = []
for warmup in picks:
    blind = max(0, 200 - warmup)
    chances.append(np.mean([entry[i:i + blind].any() for i in range(200, len(entry) - blind)])
                   if blind else 0.0)
axes[1].plot(picks, chances, color=PURPLE, marker="o", markersize=3, linewidth=1.6)
axes[1].axvline(200, color=DOWN, linestyle="--", linewidth=1.5)
axes[1].annotate("200 根：硬门槛\n少一根就完全算不出", (200, 0.06), textcoords="offset points",
                 xytext=(-150, 62), fontsize=9, color=DOWN,
                 arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_xlabel("上线时带了多少根历史")
axes[1].set_ylabel("瞎的那段里至少漏掉一个进场信号的概率")
axes[1].set_title("窗口型指标（SMA 200）：不是渐近，是有和没有")
axes[1].grid(alpha=0.25)
save(fig, "warmup.png")

# 图 5：交易所的规矩
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
step_money = book["一个 step 值多少钱"].to_numpy()
axes[0].hist(np.log10(np.maximum(step_money, 1e-7)), bins=45, color=GREEN, alpha=0.7,
             edgecolor="white")
for value, colour, label in [(np.median(step_money), GRAY, f"中位 {np.median(step_money):.3f} 美元"),
                             (np.quantile(step_money, 0.99), ORANGE,
                              f"99% 分位 {np.quantile(step_money, 0.99):.2f} 美元"),
                             (step_money.max(), DOWN, f"最粗的一个 {step_money.max():.2f} 美元")]:
    axes[0].axvline(np.log10(value), color=colour, linestyle="--", linewidth=1.5, label=label)
axes[0].set_xticks([-6, -4, -2, 0])
axes[0].set_xticklabels(["0.000001", "0.0001", "0.01", "1"])
axes[0].set_xlabel("一个 stepSize 值多少钱（对数刻度）")
axes[0].set_ylabel(f"{len(book)} 个 USDT 交易对中的个数")
axes[0].set_title("加密这边：下单精度细到可以忽略")
axes[0].legend(fontsize=8.5)
axes[0].grid(alpha=0.25)

equities = np.array([1_000, 3_000, 10_000, 30_000, 100_000, 300_000, 1_000_000])
for name, frame, colour in [("SPY", spy, BLUE), ("AAPL", aapl, ORANGE)]:
    losses = []
    for equity in equities:
        trades = BT.run(frame, mainline_plan(frame), float(equity))["交易"]
        losses.append(L.apply_filters(trades, WHOLE)["丢掉的比例"].median())
    axes[1].loglog(equities, np.maximum(losses, 1e-6), color=colour, marker="o",
                   markersize=4, linewidth=1.6, label=name)
axes[1].set_xticks([1e3, 1e4, 1e5, 1e6])
axes[1].set_xticklabels(["1 千", "1 万", "10 万", "100 万"])
axes[1].set_yticks([1e-4, 1e-3, 1e-2, 1e-1])
axes[1].set_yticklabels(["0.01%", "0.1%", "1%", "10%"])
for which in (axes[1].xaxis, axes[1].yaxis):
    which.set_minor_formatter(plt.NullFormatter())
axes[1].axhline(0.01, color=GRAY, linestyle=":", linewidth=1.2)
axes[1].set_xlabel("本金（美元）")
axes[1].set_ylabel("整股取整丢掉的仓位（中位）")
axes[1].set_title("美股这边：只能买整股，小账户直接被吃掉两成")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25, which="both")
save(fig, "filters.png")

# 图 6：走一遍阶梯
fig, ax = plt.subplots(figsize=(12.0, 5.0), dpi=150)
values = r.to_numpy(float)
plain = L.run_ladder(values, L.DEFAULT_LADDER)
walked = L.run_ladder(values, L.DEFAULT_LADDER, guards)
spots = np.arange(1, len(values) + 1)
ax.plot(spots, np.cumsum(values), color=GRAY, linewidth=2.2, label=f"一次全投：{values.sum():.0f}R")
ax.plot(spots, np.cumsum(plain["逐笔"]["记进账户的"]), color=BLUE, linewidth=1.6,
        label=f"阶梯（只升不降）：{plain['合计']:.1f}R")
ax.plot(spots, np.cumsum(walked["逐笔"]["记进账户的"]), color=DOWN, linewidth=1.6,
        label=f"阶梯 + 警戒线：{walked['合计']:.1f}R")
biggest = int(np.argmax(values))
ax.scatter([biggest + 1], [np.cumsum(values)[biggest]], marker="v", s=90, color=PURPLE, zorder=5)
ax.annotate(f"第 {biggest + 1} 笔 {values[biggest]:+.0f}R\n还在模拟盘上，一分钱没赚到",
            (biggest + 1, np.cumsum(values)[biggest]), textcoords="offset points",
            xytext=(26, 26), fontsize=9, color=PURPLE,
            arrowprops=dict(arrowstyle="->", color=PURPLE, linewidth=1.1))
steps = walked["逐笔"]
down = steps.index[steps["发生了什么"].str.startswith("降级")]
for spot in down:
    ax.axvline(spot + 1, color=DOWN, linestyle="--", linewidth=1.2)
best_after = int(np.argmax(values[down[0] + 1:down[0] + 3])) + down[0] + 1
ax.annotate(f"第 {down[0] + 1} 笔触发警戒线降级\n紧接着的第 {best_after + 1} 笔是 {values[best_after]:+.0f}R",
            (down[0] + 1, np.cumsum(values)[down[0]]), textcoords="offset points",
            xytext=(-210, 34), fontsize=9, color=DOWN,
            arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
ax.set_xlabel("第几笔交易")
ax.set_ylabel("累计 R")
ax.set_title("BTC 海龟九年：一次全投、阶梯上线、阶梯加警戒线")
ax.legend(fontsize=9.5, loc="upper left")
ax.grid(alpha=0.25)
save(fig, "ladder.png")

# 图 7：阶梯到底买到了什么
fig, ax = plt.subplots(figsize=(9.2, 6.4), dpi=150)
pieces = [values[begin:begin + WINDOW] for begin in range(0, len(values) - WINDOW + 1)]
full_mean = np.mean([piece.sum() for piece in pieces])
full_worst = min(piece.sum() for piece in pieces)
line = np.linspace(0.0, 1.0, 50)
ax.plot(line, line, color=GRAY, linewidth=1.8, linestyle="--",
        label="一直用同样大小的仓位（参照线）")
ax.fill_between(line, line, 4.2, color=DOWN, alpha=0.06)
ax.fill_between(line, 0.0, line, color=GREEN, alpha=0.08)
colours = [DOWN, ORANGE, PURPLE, BLUE, GREEN]
offsets = [(14, 8), (14, 8), (14, 8), (-14, 12), (14, -22)]
for (label, stages), colour, offset in zip(LADDERS, colours, offsets):
    got = np.array([L.run_ladder(piece, stages, guards)["合计"] for piece in pieces])
    x, y = got.mean() / full_mean, got.min() / full_worst
    ax.scatter([x], [y], s=140, color=colour, zorder=5)
    ax.annotate(f"{label}\n({x:.0%}, {y:.0%})", (x, y), textcoords="offset points",
                xytext=offset, fontsize=9, color=colour,
                ha="right" if offset[0] < 0 else "left")
ax.set_xlim(0, 1.02)
ax.set_ylim(0, 4.2)
ax.xaxis.set_major_formatter(percent)
ax.yaxis.set_major_formatter(percent)
ax.set_xlabel("平均收益是「一次全投」的百分之几  →  越右越好")
ax.set_ylabel("最差的那一段是「一次全投」的百分之几  →  越下越好")
ax.set_title(f"头 {WINDOW} 笔，{len(pieces)} 个起点：五条阶梯全部落在参照线的坏的一侧")
ax.legend(fontsize=9, loc="upper left")
ax.grid(alpha=0.25)
save(fig, "tradeoff.png")
