"""生成第 27 篇的插图：python 27_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 27_backtest.py（整段执行，不打印输出）。
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
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.ticker import FuncFormatter

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(Path(__file__).with_name("27_backtest.py").read_text(encoding="utf-8"), ns)
BT, btc, close, signal = ns["BT"], ns["btc"], ns["close"], ns["signal"]
bracket, frames, fills = ns["bracket"], ns["frames"], ns["fills"]
entry, exit_, mainline, EQUITY = ns["entry"], ns["exit_"], ns["mainline"], ns["EQUITY"]
R, curves = ns["R"], ns["curves"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")


def save(fig, name):
    fig.tight_layout()
    fig.savefig(out / name, bbox_inches="tight")
    plt.close(fig)
    print("写出", out / name)


# 图 1：决策点——一条不回撤的资金曲线
broken = (1 + (signal * close.pct_change()).fillna(0)).cumprod()
fixed = (1 + (signal.shift(1).fillna(False) * close.pct_change()).fillna(0)).cumprod()
fig, axes = plt.subplots(2, 1, figsize=(11.5, 6.6), dpi=150, sharex=True,
                         gridspec_kw={"height_ratios": [3, 2]})
axes[0].plot(broken.index, broken.to_numpy(), color=DOWN, linewidth=1.6, label="错：signal × 当根收益（年化 132.7%）")
axes[0].plot(fixed.index, fixed.to_numpy(), color=BLUE, linewidth=1.6, label="对：signal.shift(1) × 当根收益（年化 14.3%）")
axes[0].plot(close.index, (close / close.iloc[0]).to_numpy(), color=GRAY, linewidth=1.1,
             linestyle=":", label="买入持有")
axes[0].set_yscale("log")
axes[0].set_yticks([1, 10, 100, 1000])
axes[0].set_yticklabels(["1", "10", "100", "1000"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title("同一个信号，差一个 .shift(1)")
axes[0].legend(fontsize=9, loc="upper left")
axes[0].grid(alpha=0.25, which="both")
for series, color, label in [(broken, DOWN, "错"), (fixed, BLUE, "对")]:
    axes[1].plot(series.index, (series / series.cummax() - 1).to_numpy(), color=color, linewidth=1.3, label=label)
axes[1].set_ylabel("距离历史最高点")
axes[1].set_title("破绽在这里：错的那条从来不回撤")
axes[1].yaxis.set_major_formatter(percent)
axes[1].legend(fontsize=9, loc="lower left")
axes[1].grid(alpha=0.25)
save(fig, "decision.png")

# 图 2：把仓位往后推一根
table = BT.lag_test(close, signal.astype(float), lags=(0, 1, 2, 3), periods_per_year=365)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), dpi=150)
positions = np.arange(len(table))
colors = [DOWN] + [BLUE] * (len(table) - 1)
axes[0].bar(positions, table["年化"].to_numpy(), color=colors, alpha=0.9)
for x, value in zip(positions, table["年化"]):
    axes[0].text(x, value + 0.03, f"{value:.1%}", ha="center", fontsize=9)
axes[0].set_xticks(positions)
axes[0].set_xticklabels([f"推迟 {int(v)} 根" for v in table["推迟根数"]])
axes[0].set_ylabel("年化")
axes[0].set_ylim(0, 1.55)
axes[0].yaxis.set_major_formatter(percent)
axes[0].set_title("推迟一根就塌掉，再推迟就不动了")
axes[0].grid(alpha=0.25, axis="y")
axes[1].bar(positions, table["持仓根里上涨的比例"].to_numpy(), color=colors, alpha=0.9)
axes[1].axhline(0.5, color=GRAY, linewidth=1.2, linestyle=":", label="抛硬币的水平")
for x, value in zip(positions, table["持仓根里上涨的比例"]):
    axes[1].text(x, value + 0.02, f"{value:.1%}", ha="center", fontsize=9)
axes[1].set_xticks(positions)
axes[1].set_xticklabels([f"推迟 {int(v)} 根" for v in table["推迟根数"]])
axes[1].set_ylabel("持仓的 K 线里上涨的比例")
axes[1].set_ylim(0, 1.15)
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_title("100% 的胜率不是策略，是漏了一个 shift")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25, axis="y")
save(fig, "lag.png")

# 图 3：一根 K 线上的四步顺序
fig, axes = plt.subplots(1, 2, figsize=(12.5, 3.4), dpi=150, gridspec_kw={"width_ratios": [2, 3]})
ax = axes[0]
ax.plot([1, 1], [96, 108], color="#333333", linewidth=1.4)
ax.add_patch(Rectangle((0.85, 99), 0.3, 6, facecolor=UP, edgecolor="#333333"))
for y, text, when in [(108, "最高价", "收盘才知道"), (105, "收盘价", "收盘才知道"),
                      (99, "开盘价", "一开始就知道"), (96, "最低价", "收盘才知道")]:
    ax.annotate(f"{text}（{when}）", (1.2, y), fontsize=9.5, va="center",
                color=GRAY if when == "一开始就知道" else "#333333")
ax.set_xlim(0.7, 2.6)
ax.set_ylim(94, 110)
ax.set_title("一根 K 线上，只有开盘价是「当时」就有的")
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)
ax = axes[1]
steps = ["1. 成交\n上一根收盘挂出的单", "2. 出场\n止损 / 止盈 / 出场信号",
         "3. 估值\n按收盘价记下权益", "4. 下单\n用这一根的信息，挂下一根的单"]
for i, text in enumerate(steps):
    ax.add_patch(Rectangle((i * 2.4, 0), 2.0, 1.0, facecolor=[BLUE, DOWN, GREEN, PURPLE][i], alpha=0.16,
                           edgecolor=[BLUE, DOWN, GREEN, PURPLE][i]))
    ax.text(i * 2.4 + 1.0, 0.5, text, ha="center", va="center", fontsize=9)
    if i < 3:
        ax.add_patch(FancyArrowPatch((i * 2.4 + 2.0, 0.5), (i * 2.4 + 2.4, 0.5),
                                     arrowstyle="->", mutation_scale=14, color=GRAY))
ax.annotate("第 4 步一定排在第 3 步后面：\n这一根算出来的东西，最早下一根才能成交",
            (4.8, -0.45), ha="center", fontsize=9.5, color=DOWN)
ax.set_xlim(-0.3, 9.9)
ax.set_ylim(-0.9, 1.3)
ax.set_title("每一根 K 线上，引擎按固定顺序做四件事")
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)
save(fig, "clock.png")

# 图 4：同一根的比例
widths = [0.25, 0.5, 1.0]
rates = {name: [bracket(bars, k)[1] / 3281 for k in widths] for name, bars in frames.items()}
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
positions = np.arange(len(widths))
for offset, (name, values) in zip([-1.5, -0.5, 0.5, 1.5], rates.items()):
    bars_ = ax.bar(positions + offset * 0.2, values, width=0.2, label=name)
    for rect, value in zip(bars_, values):
        ax.text(rect.get_x() + rect.get_width() / 2, value + 0.005, f"{value:.2%}",
                ha="center", fontsize=7.5, rotation=90)
ax.set_xticks(positions)
ax.set_xticklabels([f"括号 ±{k} ATR" for k in widths])
ax.set_ylabel("「同一根里两边都碰到」的比例")
ax.set_ylim(0, 0.40)
ax.yaxis.set_major_formatter(percent)
ax.set_title("K 线越粗，越多交易的结果由你的假设决定")
ax.legend(fontsize=9)
ax.grid(alpha=0.25, axis="y")
save(fig, "path_rate.png")

# 图 5：这个假设值多少钱
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
styles = {"乐观：总是止盈先到": (DOWN, "-"), "悲观：总是止损先到": (BLUE, "-"),
          "抛硬币": (ORANGE, "-"), "真相：用 1 分钟线判定": ("#333333", "--")}
for label, path in [("乐观：总是止盈先到", "optimistic"), ("悲观：总是止损先到", "pessimistic"),
                    ("抛硬币", "coin"), ("真相：用 1 分钟线判定", None)]:
    outcome, _ = bracket(btc, 0.25, path=path)
    curve = np.cumprod(1 + 0.01 * outcome)
    color, style = styles[label]
    axes[0].plot(range(len(curve)), np.maximum(curve, 1e-6), color=color, linestyle=style,
                 linewidth=1.5, label=f"{label}（合计 {outcome.sum():+.0f}R）")
axes[0].set_yscale("log")
axes[0].set_yticks([1e-4, 1e-2, 1, 1e2, 1e4])
axes[0].set_yticklabels(["0.0001", "0.01", "1", "100", "10000"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].set_xlabel("第几笔")
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title("日线上 ±0.25 ATR 的括号单，3,281 笔")
axes[0].legend(fontsize=8.5, loc="upper left")
axes[0].grid(alpha=0.25, which="both")
labels, gaps = [], []
for k in widths:
    truth = bracket(btc, k)[0].sum()
    labels.append(f"±{k} ATR")
    gaps.append([bracket(btc, k, path=p)[0].sum() - truth for p in ("optimistic", "pessimistic", "coin")])
gaps = np.array(gaps)
positions = np.arange(len(widths))
for offset, column, color, name in zip([-0.25, 0, 0.25], gaps.T, [DOWN, BLUE, ORANGE],
                                       ["乐观", "悲观", "抛硬币"]):
    axes[1].bar(positions + offset, column, width=0.25, color=color, label=name)
axes[1].axhline(0, color="#333333", linewidth=1.2)
axes[1].set_xticks(positions)
axes[1].set_xticklabels(labels)
axes[1].set_ylabel("比真相多算的 R")
axes[1].set_title("括号越窄，假设越贵；抛硬币一直贴着真相")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25, axis="y")
save(fig, "path_money.png")

# 图 6：限价单「碰到就成交」
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), dpi=150)
groups = fills.groupby("穿过多少", observed=True)
labels = [str(name) for name, _ in groups]
positions = np.arange(len(labels))
axes[0].bar(positions, [group["在限价或更低的分钟数"].median() for _, group in groups], color=BLUE, alpha=0.85)
for x, (_, group) in zip(positions, groups):
    axes[0].text(x, group["在限价或更低的分钟数"].median() + 15, f"{len(group)} 天", ha="center", fontsize=8.5)
axes[0].set_xticks(positions)
axes[0].set_xticklabels(labels, fontsize=8.5, rotation=12)
axes[0].set_ylabel("当天在限价或更低的分钟数（中位数）")
axes[0].set_title("限价挂在开盘价下方 2%，日线判定「成交」的 1,392 天")
axes[0].grid(alpha=0.25, axis="y")
axes[1].bar(positions, [float((group["在限价或更低的分钟数"] <= 1).mean()) for _, group in groups],
            color=DOWN, alpha=0.85, label="只有 1 分钟")
axes[1].bar(positions, [float((group["在限价或更低的分钟数"] <= 5).mean()) for _, group in groups],
            color=DOWN, alpha=0.35, label="不超过 5 分钟")
axes[1].set_xticks(positions)
axes[1].set_xticklabels(labels, fontsize=8.5, rotation=12)
axes[1].set_ylabel("占这一组的比例")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_title("「擦一下」的那 24 天，七成只有一分钟的机会")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25, axis="y")
save(fig, "limit.png")

# 图 7：主线 v4 在新引擎上
result = BT.run(btc, BT.Plan(entry=entry, exit=exit_, sizing="risk", risk_per_trade=0.10, **mainline), EQUITY)
fig, axes = plt.subplots(2, 1, figsize=(11.5, 6.6), dpi=150, sharex=True,
                         gridspec_kw={"height_ratios": [3, 2]})
for (name, curve), color in zip(curves.items(), ["#333333", BLUE, ORANGE]):
    axes[0].plot(curve.index, (curve / curve.iloc[0]).to_numpy(), color=color, linewidth=1.5, label=name)
axes[0].set_yscale("log")
axes[0].set_yticks([1, 2, 5])
axes[0].set_yticklabels(["1", "2", "5"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title("主线策略 v4：三条几乎重合的曲线")
axes[0].legend(fontsize=9, loc="upper left")
axes[0].grid(alpha=0.25, which="both")
position_value = result["持仓数量"] * btc["close"].reindex(result["持仓数量"].index)
axes[1].fill_between(result["现金"].index, 0, (result["现金"] / result["资金曲线"]).to_numpy(),
                     color=GRAY, alpha=0.45, label="现金")
axes[1].fill_between(result["现金"].index, (result["现金"] / result["资金曲线"]).to_numpy(), 1.0,
                     color=GREEN, alpha=0.45, label="持仓市值")
axes[1].set_ylim(0, 1)
axes[1].set_ylabel("占权益")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_title("现金 + 持仓市值 = 权益，每一根都对得上（记账误差 0）")
axes[1].legend(fontsize=9, loc="lower left")
axes[1].grid(alpha=0.25)
save(fig, "engine.png")
