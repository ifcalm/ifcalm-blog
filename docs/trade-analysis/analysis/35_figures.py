"""生成第 35 篇的插图：python 35_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 35_project.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("35_project.py").read_text(encoding="utf-8"), ns)
PJ, RP, RV, T = ns["PJ"], ns["RP"], ns["RV"], ns["T"]
MARKETS, legs, switches, card = ns["MARKETS"], ns["legs"], ns["switches"], ns["card"]
BEST, LABEL, SPLIT = ns["BEST"], ns["LABEL"], ns["SPLIT"]
grid, sharpes, inside, outside = ns["grid"], ns["sharpes"], ns["inside"], ns["outside"]
best_curve, spy_trend, spy_mean, spy_blend = ns["best_curve"], ns["spy_trend"], ns["spy_mean"], ns["spy_blend"]
luck, gates, versions, CHANGES = ns["luck"], ns["gates"], ns["versions"], ns["CHANGES"]
blend_in, blend_out = ns["blend_in"], ns["blend_out"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")
NAMES = list(MARKETS)
COLORS = [BLUE, ORANGE, DOWN]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(out / name, bbox_inches="tight")
    plt.close(fig)
    print("写出", out / name)


def curves(ax, with_blend: bool):
    for label, curve, colour, width in [("只做趋势跟随（第 31 篇）", spy_trend, GRAY, 1.2),
                                        ("只做均值回归（第 32 篇）", spy_mean, ORANGE, 1.2),
                                        (f"按方差比切换（{LABEL}）", best_curve, PURPLE, 2.0)]:
        normalized = curve / curve.iloc[0]
        ax.plot(normalized.index, normalized.to_numpy(), color=colour, linewidth=width, label=label)
    if with_blend:
        normalized = spy_blend / spy_blend.iloc[0]
        ax.plot(normalized.index, normalized.to_numpy(), color=GREEN, linewidth=2.0,
                linestyle="--", label="五五开每月再平衡（第 32 篇，零参数）")
    ax.set_ylabel("本金的几倍")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=9, loc="upper left")


def scorecard(ax, with_blend: bool):
    rows = {"按方差比切换": card(best_curve, 252, 3), "只做趋势跟随": card(spy_trend, 252, 0),
            "只做均值回归": card(spy_mean, 252, 0)}
    if with_blend:
        rows["五五开每月再平衡"] = card(spy_blend, 252, 0)
    keys = ["夏普", "卡玛"]
    spots = np.arange(len(keys))
    width = 0.8 / len(rows)
    colours = [PURPLE, GRAY, ORANGE, GREEN]
    for k, (name, values) in enumerate(rows.items()):
        heights = [values[key] for key in keys]
        bars = ax.bar(spots + (k - (len(rows) - 1) / 2) * width, heights, width,
                      color=colours[k], label=name)
        for bar, height in zip(bars, heights):
            ax.annotate(f"{height:.3f}", (bar.get_x() + bar.get_width() / 2, height),
                        textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8)
    ax.set_xticks(spots)
    ax.set_xticklabels(keys)
    ax.set_ylim(0, 1.25)
    ax.grid(alpha=0.25, axis="y")
    ax.legend(fontsize=8.5)


# 图 1：决策点——只和两条单腿比
fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.6), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
curves(axes[0], with_blend=False)
axes[0].set_title("SPY：切换策略和两条单腿")
scorecard(axes[1], with_blend=False)
axes[1].set_title("四项指标，候选 4 比 0 全赢")
save(fig, "decision.png")

# 图 2：揭晓——加上那条零参数的对照组
fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.6), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
curves(axes[0], with_blend=True)
axes[0].set_title("同一张图，加上第 32 篇那条零参数的五五开")
scorecard(axes[1], with_blend=True)
axes[1].set_title("加上对照组之后：夏普赢一点，卡玛输")
save(fig, "control.png")

# 图 3：优势，和白捡的量
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
axes[0].hist(sharpes.to_numpy(), bins=30, color=BLUE, alpha=0.7, edgecolor="white")
control = RP.sharpe(spy_blend.pct_change().dropna(), 252)
for value, colour, label in [(sharpes.median(), GRAY, f"网格中位 {sharpes.median():.3f}"),
                             (control, GREEN, f"零参数五五开 {control:.3f}"),
                             (sharpes.max(), PURPLE, f"网格最好 {sharpes.max():.3f}")]:
    axes[0].axvline(value, color=colour, linestyle="--", linewidth=1.8, label=label)
axes[0].set_xlabel("夏普比率")
axes[0].set_ylabel(f"{len(sharpes)} 格中的个数")
axes[0].set_title(f"试了 {len(sharpes)} 格，只有 {int((sharpes > control).sum())} 格超过零参数的对照组")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.25)

bars = axes[1].bar(["候选比对照组\n多出来的", f"试 {len(sharpes)} 次\n白捡的门槛"],
                   [luck["优势"], luck["白捡的门槛"]], 0.55, color=[PURPLE, DOWN])
for bar, value in zip(bars, [luck["优势"], luck["白捡的门槛"]]):
    axes[1].annotate(f"{value:+.4f}", (bar.get_x() + bar.get_width() / 2, value),
                     textcoords="offset points", xytext=(0, 4), ha="center", fontsize=11)
axes[1].set_ylim(0, luck["白捡的门槛"] * 1.25)
axes[1].set_ylabel("夏普")
axes[1].set_title(f"优势只有门槛的 {luck['优势是门槛的几成']:.1%}")
axes[1].grid(alpha=0.25, axis="y")
save(fig, "luck.png")

# 图 4：样本内外
fig, ax = plt.subplots(figsize=(8.2, 6.2), dpi=150)
ax.scatter(inside.to_numpy(), outside.to_numpy(), s=26, color=BLUE, alpha=0.6, label=f"{len(grid)} 格")
picked = inside.idxmax()
ax.scatter([inside[picked]], [outside[picked]], s=150, color=PURPLE, zorder=5,
           label="样本内挑出来的那一格")
ax.axvline(blend_in, color=GREEN, linestyle="--", linewidth=1.8)
ax.axhline(blend_out, color=GREEN, linestyle="--", linewidth=1.8)
ax.annotate(f"零参数五五开：样本内 {blend_in:.3f}", (blend_in, ax.get_ylim()[1]),
            textcoords="offset points", xytext=(-8, -8), fontsize=9, color=GREEN,
            rotation=90, va="top", ha="right")
ax.annotate(f"零参数五五开：样本外 {blend_out:.3f}", (ax.get_xlim()[0], blend_out),
            textcoords="offset points", xytext=(10, 6), fontsize=9, color=GREEN)
ax.set_xlabel(f"样本内夏普（到 {SPLIT.date()}）")
ax.set_ylabel("样本外夏普")
ax.set_title(f"挑参数的那一段里，{len(grid)} 格没有一格越过那条竖线")
ax.legend(fontsize=9, loc="lower right")
ax.grid(alpha=0.25)
save(fig, "insample.png")

# 图 5：换两个市场
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
spots = np.arange(len(NAMES))
switch_sharpe, blend_sharpe, on_trend = [], [], []
for name in NAMES:
    _, _, blended, _, periods = legs(name)
    series, share = switches(name)[BEST]
    switch_sharpe.append(RP.sharpe(series, periods))
    blend_sharpe.append(RP.sharpe(blended.pct_change().dropna(), periods))
    on_trend.append(share)
axes[0].bar(spots - 0.2, switch_sharpe, 0.4, color=PURPLE, label="SPY 挑出来的那一格")
axes[0].bar(spots + 0.2, blend_sharpe, 0.4, color=GREEN, label="五五开（零参数）")
for k, (a, b) in enumerate(zip(switch_sharpe, blend_sharpe)):
    axes[0].annotate(f"{a:.3f}", (k - 0.2, a), textcoords="offset points", xytext=(0, 3),
                     ha="center", fontsize=8.5)
    axes[0].annotate(f"{b:.3f}", (k + 0.2, b), textcoords="offset points", xytext=(0, 3),
                     ha="center", fontsize=8.5)
axes[0].set_xticks(spots)
axes[0].set_xticklabels(NAMES)
axes[0].set_ylabel("夏普比率")
axes[0].set_title("换两个市场，三个全输")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.25, axis="y")

axes[1].bar(spots, on_trend, 0.5, color=COLORS)
for k, share in enumerate(on_trend):
    axes[1].annotate(f"{share:.1%}", (k, share), textcoords="offset points", xytext=(0, 4),
                     ha="center", fontsize=10)
axes[1].axhline(0.5, color=GRAY, linestyle=":", linewidth=1.2)
axes[1].set_xticks(spots)
axes[1].set_xticklabels(NAMES)
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_ylim(0, 0.75)
axes[1].set_ylabel("在趋势腿上的天数")
axes[1].set_title("同一组参数，在三个市场上是三条不同的策略")
axes[1].grid(alpha=0.25, axis="y")
save(fig, "markets.png")

# 图 6：主线 v0 → v4
fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.6), dpi=150)
labels = list(CHANGES)
short = [name.split("（")[0] for name in labels]
spots = np.arange(len(labels))
for k, name in enumerate(NAMES):
    axes[0].plot(spots, [versions[v][f"{name} 年化"] for v in labels], color=COLORS[k],
                 marker="o", markersize=5, linewidth=1.8, label=name)
    axes[1].plot(spots, [versions[v][f"{name} 回撤"] for v in labels], color=COLORS[k],
                 marker="o", markersize=5, linewidth=1.8, label=name)
for ax, title, formatter in [(axes[0], "年化", percent), (axes[1], "最大回撤", percent)]:
    ax.set_xticks(spots)
    ax.set_xticklabels(short)
    ax.yaxis.set_major_formatter(formatter)
    ax.set_title(f"主线策略 v0 → v4：{title}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
axes[0].annotate("加止损，三个标的的\n年化都掉了一截", (1, versions[labels[1]]["SPY 年化"]),
                 textcoords="offset points", xytext=(34, 34), fontsize=9, color=GRAY,
                 arrowprops=dict(arrowstyle="->", color=GRAY, linewidth=1.0))
axes[1].annotate("加「收盘创 20 日新高」\n三条线在这里一起抬起来",
                 (3, versions[labels[3]]["BTC 回撤"]), textcoords="offset points",
                 xytext=(-150, -34), fontsize=9, color=GRAY,
                 arrowprops=dict(arrowstyle="->", color=GRAY, linewidth=1.0))
save(fig, "evolution.png")

# 图 7：体检表
fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=150)
table = PJ.audit(gates)
spots = np.arange(len(table))[::-1]
for spot, (_, row) in zip(spots, table.iterrows()):
    passed = row["结论"] == "过"
    colour = GREEN if passed else DOWN
    ax.scatter([1 if passed else 0], [spot], s=190, color=colour, zorder=5,
               marker="o" if passed else "X")
    ax.plot([0, 1], [spot, spot], color=GRAY, linewidth=0.7, linestyle=":", zorder=1)
    ax.annotate(row["出处"], (1.08, spot), fontsize=8.5, color=GRAY, va="center")
    if row["一票否决"]:
        ax.annotate("一票否决", (-0.13, spot), fontsize=8.5, color=DOWN, va="center", ha="right")
ax.set_yticks(spots)
ax.set_yticklabels(table["这一关"], fontsize=9.5)
ax.set_xticks([0, 1])
ax.set_xticklabels(["没过", "过"], fontsize=11)
ax.set_xlim(-0.55, 1.35)
result = PJ.verdict(gates)
ax.set_title(f"体检表：{int(result['一共几关'])} 关过了 {int(result['过了几关'])} 关，"
             f"踩了 {int(result['踩了几道一票否决'])} 道一票否决 → {result['结论']}")
ax.grid(alpha=0.25, axis="x")
save(fig, "audit.png")
