"""生成第 21 篇的插图：python 21_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 21_rules.py（整段执行，不打印输出），避免两份代码不一致。
"""
import contextlib
import io
import itertools
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
    exec(Path(__file__).with_name("21_rules.py").read_text(encoding="utf-8"), ns)
spy, aapl, day, R, I = ns["spy"], ns["aapl"], ns["day"], ns["R"], ns["I"]
variant, mainline_v3, signal_day = ns["variant"], ns["mainline_v3"], ns["signal_day"]
FILLS, STOPS, EXITS = ns["FILLS"], ns["STOPS"], ns["EXITS"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")

# 1. 决策点：金叉那一天
bars = spy.loc["2024-11-01":"2025-07-01"]
fast, slow = I.sma(spy["close"], 50).loc[bars.index], I.sma(spy["close"], 200).loc[bars.index]
fig, ax = plt.subplots(figsize=(11.5, 5.4), dpi=150)
for x, (o, h, l, c) in enumerate(bars[["open", "high", "low", "close"]].to_numpy()):
    color = UP if c >= o else DOWN
    ax.vlines(x, l, h, color=color, linewidth=0.8)
    ax.add_patch(Rectangle((x - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-9), facecolor=color, edgecolor=color))
ax.plot(range(len(bars)), fast.to_numpy(), color=BLUE, linewidth=1.4, label="50 日均线")
ax.plot(range(len(bars)), slow.to_numpy(), color=PURPLE, linewidth=1.4, label="200 日均线")
ax.annotate(f"2025-07-01 金叉\nSMA50 583.10 上穿 SMA200 582.04\n收盘 617.65（在均线上方 5.6%）",
            (len(bars) - 1, float(fast.iloc[-1])), textcoords="offset points", xytext=(-235, 35), fontsize=9,
            arrowprops={"arrowstyle": "->", "color": "#555"})
ticks = [k for k, x in enumerate(bars.index) if x.day <= 3 and (k == 0 or bars.index[k - 1].month != x.month)]
ax.set_xticks(ticks)
ax.set_xticklabels([bars.index[k].strftime("%Y-%m") for k in ticks], fontsize=9)
ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="upper left")
ax.set_title("决策点：SPY 十年里的第四次金叉", fontsize=12)
fig.tight_layout(); fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 揭晓：三种写法在同一段行情上的进出场
window = spy.loc["2025-06-15":]
fig, ax = plt.subplots(figsize=(11.5, 5.6), dpi=150)
ax.plot(window.index, window["close"], color="black", linewidth=1.2, label="SPY 收盘价")
styles = [("下一根开盘 + 不设止损 + 死叉出场", ("下一根开盘", "不设止损", "死叉出场"), BLUE, 1.0),
          ("下一根开盘 + 3 ATR 吊灯 + 死叉出场", ("下一根开盘", "3 ATR 吊灯", "死叉出场"), ORANGE, 0.985),
          ("回调到 50 日均线 + 3 ATR 吊灯 + 死叉出场", ("回调到 50 日均线", "3 ATR 吊灯", "死叉出场"), PURPLE, 0.97)]
for label, combo, color, offset in styles:
    returns, _, trades = R.run(spy, variant(spy, *combo))
    since = (1 + returns.loc["2025-07-02":]).prod() - 1
    picked = trades[trades["买入日"] >= "2025-06-01"]
    ax.scatter(picked["买入日"], picked["买入价"] * offset, marker="^", s=70, color=color, zorder=3,
               label=f"{label}：{since:+.1%}")
    closed = picked[picked["原因"] != "未平仓"]
    ax.scatter(closed["卖出日"], closed["卖出价"] * offset, marker="v", s=70, color=color, zorder=3,
               facecolors="none", linewidths=1.5)
ax.axvline(signal_day, color=GRAY, linestyle="--", linewidth=1)
ax.text(signal_day, window["close"].min(), " 金叉", fontsize=9, color="#555")
ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="upper left")
ax.set_title("同一个金叉，三种写法：▲ 买入，▽ 卖出（同期买入持有 +22.6%）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 3. 十八条资金曲线
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), dpi=150)
for axis, (name, df) in zip(axes, [("SPY", spy), ("BTC", day)]):
    for fill_name, stop_name, exit_name in itertools.product(FILLS, STOPS, EXITS):
        returns, _, _ = R.run(df, variant(df, fill_name, stop_name, exit_name))
        equity = (1 + returns).cumprod()
        axis.plot(equity.index, equity, color=GRAY, linewidth=0.9, alpha=0.6)
    returns, _, _ = R.run(df, mainline_v3(df))
    equity = (1 + returns).cumprod()
    axis.plot(equity.index, equity, color=PURPLE, linewidth=2.0, label="主线 v3")
    hold = (1 + df["close"].pct_change().fillna(0)).cumprod().loc[equity.index]
    axis.plot(hold.index, hold / hold.iloc[0], color=BLUE, linewidth=1.6, linestyle="--", label="买入持有")
    axis.set_yscale("log")
    axis.get_yaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}×"))
    axis.set_title(f"{name}：同一个信号的 18 种写法（灰线）", fontsize=11)
    axis.grid(alpha=0.25); axis.legend(fontsize=9, loc="upper left")
fig.suptitle("「金叉买入」不是一条规则：补全方式不同，结果差得很远", fontsize=12)
fig.tight_layout(); fig.savefig(out / "spaghetti.png"); plt.close(fig)

# 4. 条件之间的重合
table = R.overlap(ns["conditions"](spy))
fig, ax = plt.subplots(figsize=(8.2, 6.4), dpi=150)
image = ax.imshow(table.to_numpy(), cmap="YlOrRd", vmin=0, vmax=1)
ax.set_xticks(range(len(table))); ax.set_yticks(range(len(table)))
ax.set_xticklabels(table.columns, rotation=30, ha="right", fontsize=9)
ax.set_yticklabels(table.index, fontsize=9)
for i in range(len(table)):
    for j in range(len(table)):
        value = table.to_numpy()[i, j]
        ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=9,
                color="white" if value > 0.6 else "black")
ax.set_title("SPY：两个条件「同时成立」的程度\n（对角线是各自成立的比例，其余是同时成立 ÷ 至少一个成立）", fontsize=11)
fig.colorbar(image, ax=ax, shrink=0.8)
fig.tight_layout(); fig.savefig(out / "overlap.png"); plt.close(fig)

# 5. 条件越多，交易越少
stacked = ns["rows"] if isinstance(ns.get("rows"), list) else None
depths, trades_count, widths, annual = [], [], [], []
picked = ns["conditions"](spy)
order = list(picked)
for depth in range(1, len(order) + 1):
    mask = None
    for name in order[:depth]:
        mask = picked[name] if mask is None else (mask & picked[name])
    returns, _, trades = R.run(spy, R.Rule(entry=mask.fillna(False), exit=ns["deaths"](spy), stop="chandelier"))
    profits = trades["收益"].to_numpy()
    boot = np.array([np.random.default_rng(k).choice(profits, len(profits), replace=True).mean() for k in range(2000)])
    depths.append(depth); trades_count.append(len(trades))
    widths.append(np.percentile(boot, 97.5) - np.percentile(boot, 2.5))
    annual.append((1 + returns).prod() ** (252 / len(returns)) - 1)
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
ax.bar(depths, trades_count, color=BLUE, alpha=0.7, label="交易次数（左轴）")
ax.set_xlabel("叠加了几个条件"); ax.set_ylabel("交易次数")
ax.set_xticks(depths)
ax.set_xticklabels([f"{d}\n{order[d - 1][:8]}" for d in depths], fontsize=8)
bx = ax.twinx()
bx.plot(depths, widths, color=DOWN, marker="o", linewidth=1.6, label="每笔平均收益的 95% 区间宽度（右轴）")
bx.plot(depths, annual, color=PURPLE, marker="s", linewidth=1.6, label="年化（右轴）")
bx.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1%}"))
bx.set_ylabel("区间宽度 / 年化")
lines = ax.get_legend_handles_labels()[0] + bx.get_legend_handles_labels()[0]
labels = ax.get_legend_handles_labels()[1] + bx.get_legend_handles_labels()[1]
ax.legend(lines, labels, fontsize=9, loc="upper center")
ax.grid(alpha=0.25, axis="y")
ax.set_title("SPY：条件越多，交易越少，结论越不可靠", fontsize=12)
fig.tight_layout(); fig.savefig(out / "stacking.png"); plt.close(fig)

# 6. 每一格换一个选择
sensitivity = ns["sensitivity"]["年化"]
fig, ax = plt.subplots(figsize=(11.5, 5), dpi=150)
labels = list(sensitivity.index)
width = 0.26
for k, (name, color) in enumerate([("SPY", BLUE), ("AAPL", ORANGE), ("BTC", PURPLE)]):
    ax.barh(np.arange(len(labels)) + k * width - width, sensitivity[name].to_numpy(), width, color=color, label=name)
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels, fontsize=9)
ax.axvline(0, color="black", linewidth=0.8)
ax.xaxis.set_major_formatter(percent)
ax.set_xlabel("年化")
ax.grid(alpha=0.25, axis="x"); ax.legend(fontsize=9)
ax.set_title("六要素里每一格换一个选择，年化会变成什么样", fontsize=12)
fig.tight_layout(); fig.savefig(out / "sensitivity.png"); plt.close(fig)
print("ok")
