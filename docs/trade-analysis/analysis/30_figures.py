"""生成第 30 篇的插图：python 30_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 30_overfitting.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("30_overfitting.py").read_text(encoding="utf-8"), ns)
RP, V = ns["RP"], ns["V"]
close, DAILY, DATES, PAIRS, WHERE = ns["close"], ns["DAILY"], ns["DATES"], ns["PAIRS"], ns["WHERE"]
window, annual, sharpe = ns["window"], ns["annual"], ns["sharpe"]
grid, best, train, test = ns["grid"], ns["best"], ns["train"], ns["test"]
in_annual, out_annual, in_sharpe = ns["in_annual"], ns["out_annual"], ns["in_sharpe"]
picked, splits, rolling = ns["picked"], ns["splits"], ns["rolling"]
monte_carlo, surfaces, MAIN = ns["monte_carlo"], ns["surfaces"], ns["MAIN"]
real_annual, real_sharpe, curve = ns["real_annual"], ns["real_sharpe"], ns["curve"]
N_PATHS, grid_returns = ns["N_PATHS"], ns["grid_returns"]

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


def logy(ax, ticks, labels):
    ax.set_yscale("log")
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    ax.yaxis.set_minor_formatter(plt.NullFormatter())


# 图 1：决策点——两年的回测
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
price = close.loc["2021-01-01":"2022-12-31"]
axes[0].plot(curve.index, curve.to_numpy(), color=DOWN, linewidth=1.8,
             label=f"多空均线交叉 (31,36)：年化 {real_annual:.1%}")
axes[0].plot(price.index, (price / price.iloc[0]).to_numpy(), color=GRAY, linewidth=1.4,
             label=f"BTC 买入持有：年化 {RP.annual_return(price, 365):.1%}")
logy(axes[0], [0.5, 1, 2, 4, 8], ["0.5", "1", "2", "4", "8"])
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title("两年：市场跌掉四成，它把本金变成 7.5 倍")
axes[0].legend(loc="upper left", fontsize=9)
axes[0].grid(alpha=0.3)
axes[0].tick_params(axis="x", labelrotation=20)

zoom = grid.loc[29:33, 34:38]
image = axes[1].imshow(zoom.to_numpy(), cmap="RdYlGn", vmin=-0.2, vmax=1.8, aspect="auto")
axes[1].set_xticks(range(len(zoom.columns)), [str(c) for c in zoom.columns])
axes[1].set_yticks(range(len(zoom.index)), [str(i) for i in zoom.index])
for a in range(len(zoom.index)):
    for b in range(len(zoom.columns)):
        value = zoom.iloc[a, b]
        axes[1].text(b, a, f"{value:.0%}", ha="center", va="center", fontsize=9,
                     color="black", fontweight="bold" if (zoom.index[a], zoom.columns[b]) == PAIRS[best] else "normal")
axes[1].set_xlabel("慢线")
axes[1].set_ylabel("快线")
axes[1].set_title("最好那一格和它的邻居（年化）")
fig.colorbar(image, ax=axes[1], format=percent)
save(fig, "decision.png")

# 图 2：一万格的曲面
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
image = axes[0].imshow(grid.to_numpy(), cmap="RdYlGn", vmin=-0.4, vmax=1.2, aspect="auto",
                       extent=[grid.columns[0], grid.columns[-1], grid.index[-1], grid.index[0]])
axes[0].scatter([PAIRS[best][1]], [PAIRS[best][0]], s=90, facecolors="none", edgecolors="black", linewidths=1.8)
axes[0].annotate(f"最好的一格 {PAIRS[best]}\n年化 {real_annual:.0%}", PAIRS[best][::-1],
                 textcoords="offset points", xytext=(25, -8), fontsize=9,
                 arrowprops=dict(arrowstyle="->", color="black", linewidth=1.0))
axes[0].set_xlabel("慢线")
axes[0].set_ylabel("快线")
axes[0].set_title(f"{len(PAIRS):,} 格参数曲面（2021–2022 年化）")
fig.colorbar(image, ax=axes[0], format=percent)

cut = grid.loc[31].dropna()
axes[1].plot(cut.index, cut.to_numpy(), color=BLUE, linewidth=1.2)
axes[1].axhline(np.median(in_annual), color=GRAY, linestyle="--", linewidth=1.2,
                label=f"全网格中位 {np.median(in_annual):.1%}")
axes[1].scatter([36], [cut.loc[36]], s=70, color=DOWN, zorder=5, label=f"(31,36) {cut.loc[36]:.0%}")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_xlabel("慢线（快线固定在 31）")
axes[1].set_title("沿着一条线切一刀：一根针")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.3)
save(fig, "surface.png")

# 图 3：尖峰是样本短的症状
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.3), dpi=150)
nine_values = annual(DAILY)
nine = pd.DataFrame({"快线": [f for f, s in PAIRS], "慢线": [s for f, s in PAIRS], "年化": nine_values})
nine_grid = V.surface(nine, "快线", "慢线", "年化")
nine_best = PAIRS[int(nine_values.argmax())]
for ax, (face, values, top, title, color) in zip(axes[:2], [
        (grid, in_annual, PAIRS[best], "两年（2021–2022）：一根针", DOWN),
        (nine_grid, nine_values, nine_best, "九年（2017–2026）：一片坡", GREEN)]):
    cut = face.loc[top[0]].dropna()
    ax.plot(cut.index, cut.to_numpy(), color=color, linewidth=1.3)
    ax.axhline(np.median(values), color=GRAY, linestyle="--", linewidth=1.2,
               label=f"全网格中位 {np.median(values):.1%}")
    ax.scatter([top[1]], [cut.loc[top[1]]], s=80, color="black", zorder=5,
               label=f"最好的一格 {top} = {cut.loc[top[1]]:.0%}")
    ax.set_ylim(-0.5, 1.9)
    ax.yaxis.set_major_formatter(percent)
    ax.set_xlabel(f"慢线（快线固定在 {top[0]}）")
    ax.set_ylabel("年化")
    ax.set_title(title)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)

years = [1, 2, 3, 5, 9]
gaps = []
for y in years:
    piece = annual(DAILY[:, -int(365 * y):])
    top = int(piece.argmax())
    fast, slow = PAIRS[top]
    ring = [piece[WHERE[(f, s)]] for f in (fast - 1, fast, fast + 1) for s in (slow - 1, slow, slow + 1)
            if (f, s) != (fast, slow) and (f, s) in WHERE]
    gaps.append((piece[top] - np.median(ring)) / piece[top])
axes[2].bar([str(y) for y in years], gaps, color=[DOWN if g > 0.3 else GREEN for g in gaps])
for i, g in enumerate(gaps):
    axes[2].text(i, g + 0.02, f"{g:.0%}", ha="center", fontsize=9)
axes[2].yaxis.set_major_formatter(percent)
axes[2].set_xlabel("回测跑了几年")
axes[2].set_ylabel("落差 ÷ 年化")
axes[2].set_title("样本越短，最好那一格越像一根针")
axes[2].grid(axis="y", alpha=0.3)
save(fig, "plateau.png")

# 图 4：样本内对样本外
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), dpi=150)
axes[0].scatter(in_annual, out_annual, s=3, alpha=0.18, color=GRAY, edgecolors="none")
for label, cell, color in [("这一格最高", PAIRS[best], DOWN),
                           ("邻域中位最高", (32, 34), BLUE),
                           ("课程默认 (50,200)", (50, 200), PURPLE)]:
    k = WHERE[cell]
    axes[0].scatter([in_annual[k]], [out_annual[k]], s=80, color=color, zorder=5,
                    label=f"{label} {cell}")
axes[0].axhline(0, color="black", linewidth=0.8)
axes[0].axhline(np.median(out_annual), color=GREEN, linestyle="--", linewidth=1.2,
                label=f"样本外中位 {np.median(out_annual):.1%}")
axes[0].xaxis.set_major_formatter(percent)
axes[0].yaxis.set_major_formatter(percent)
axes[0].set_xlabel("样本内年化（2021–2022）")
axes[0].set_ylabel("样本外年化（2023-01～2026-08）")
axes[0].set_title(f"秩相关 {pd.Series(in_annual).rank().corr(pd.Series(out_annual).rank()):.3f}")
axes[0].legend(fontsize=8.5, loc="upper right")
axes[0].grid(alpha=0.3)

order = np.argsort(-in_annual)
tops = [10, 50, 100, 500, 1000, 5000, len(PAIRS)]
axes[1].plot([str(n) for n in tops], [np.median(out_annual[order[:n]]) for n in tops],
             "o-", color=BLUE, linewidth=1.8)
axes[1].axhline(np.median(out_annual), color=GREEN, linestyle="--", linewidth=1.2,
                label="全网格样本外中位")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_xlabel("取样本内前几名")
axes[1].set_ylabel("这些格子的样本外年化中位")
axes[1].set_title("样本内排得越靠前，样本外并没有更好")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.3)
save(fig, "oos.png")

# 图 5：walk-forward
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), dpi=150)
x = np.arange(len(picked))
axes[0].bar(x - 0.19, picked["训练期夏普"], width=0.36, color=GRAY, label="训练期夏普")
axes[0].bar(x + 0.19, picked["考卷夏普"], width=0.36,
            color=[GREEN if v > 0 else DOWN for v in picked["考卷夏普"]], label="考卷夏普")
axes[0].axhline(0, color="black", linewidth=0.8)
axes[0].set_xticks(x, [f"第 {k} 段\n{p}" for k, p in zip(picked["第几段"], picked["选了谁"])], fontsize=8)
axes[0].set_ylabel("年化夏普比率")
axes[0].set_title("每一段都在训练期挑第一名，考卷上原形毕露")
axes[0].legend(fontsize=9)
axes[0].grid(axis="y", alpha=0.3)

stitched = V.stitch(rolling, splits, [PAIRS.index(p) for p in picked["选了谁"]])
first = DATES[ns["start"]:][splits[0][1].start]
index = DATES[ns["start"]:][splits[0][1].start:splits[-1][1].stop]
equity = RP.to_curve(pd.Series(stitched, index=index))
axes[1].plot(equity.index, equity.to_numpy(), color=DOWN, linewidth=1.8,
             label=f"walk-forward 拼出来的样本外：年化 {RP.annual_return(equity, 365):.1%}")
tail = close.loc[first:]
axes[1].plot(tail.index, (tail / tail.iloc[0]).to_numpy(), color=GRAY, linewidth=1.4,
             label=f"买入持有：年化 {RP.annual_return(tail, 365):.1%}")
logy(axes[1], [0.5, 1, 2, 5, 10], ["0.5", "1", "2", "5", "10"])
axes[1].set_ylabel("本金的几倍（对数轴）")
axes[1].set_title("每年换一次「当时最好的参数」")
axes[1].legend(fontsize=9, loc="upper left")
axes[1].grid(alpha=0.3)
axes[1].tick_params(axis="x", labelrotation=20)
save(fig, "walkforward.png")

# 图 6：蒙特卡洛
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), dpi=150)
warm = close.loc["2020-11-01":"2022-12-31"]
for ax, (block, label, color) in zip(axes, [(1, "打散（波动率聚集也没了）", GRAY),
                                            (20, "20 天的块（波动率聚集还在）", ORANGE)]):
    tops = np.array([annual(grid_returns(path, PAIRS)[:, -730:]).max()
                     for path in V.synthetic_close(warm, n=N_PATHS, block=block, seed=30)])
    ax.hist(tops, bins=40, color=color, alpha=0.85)
    ax.axvline(real_annual, color=DOWN, linestyle="--", linewidth=1.8,
               label=f"真实数据 {real_annual:.0%}")
    ax.axvline(np.median(tops), color=BLUE, linewidth=1.5, label=f"假数据中位 {np.median(tops):.0%}")
    ax.xaxis.set_major_formatter(percent)
    ax.set_xlabel("「一万组里最好的一组」的年化")
    ax.set_title(f"{label}\n有 {float((tops >= real_annual).mean()):.1%} 的假数据比真实的还好")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
save(fig, "montecarlo.png")

# 图 7：白捡的门槛与主线策略站在哪里
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), dpi=150)
counts = np.unique(np.round(np.logspace(0.31, 4.3, 60)).astype(int))
axes[0].plot(counts, [V.expected_max_sharpe(n, in_sharpe.std()) for n in counts],
             color=BLUE, linewidth=2.0, label="没本事时「最好那次」的期望夏普")
axes[0].axhline(real_sharpe, color=DOWN, linestyle="--", linewidth=1.6,
                label=f"决策点那一组 {real_sharpe:.2f}")
for n, marker, offset in [(2, "说「我就试了两组」", (16, 10)), (len(PAIRS), "说实话：一万组", (-95, 16))]:
    value = V.expected_max_sharpe(n, in_sharpe.std())
    axes[0].scatter([n], [value], s=70, color=PURPLE, zorder=5)
    axes[0].annotate(f"{marker}\n门槛 {value:.2f}", (n, value), textcoords="offset points",
                     xytext=offset, fontsize=8.5)
axes[0].set_ylim(0, 1.95)
axes[0].set_xscale("log")
axes[0].set_xlabel("你试了多少组参数（对数轴）")
axes[0].set_ylabel("年化夏普比率")
axes[0].set_title("同一个 1.75，试得越多越不值钱")
axes[0].legend(fontsize=9, loc="lower right")
axes[0].grid(alpha=0.3, which="both")

face = surfaces["BTC"]
image = axes[1].imshow(face.to_numpy(), cmap="RdYlGn", vmin=0.75, vmax=1.20, aspect="auto")
axes[1].set_xticks(range(len(face.columns)), [str(c) for c in face.columns])
axes[1].set_yticks(range(len(face.index)), [str(i) for i in face.index])
for a in range(len(face.index)):
    for b in range(len(face.columns)):
        default = (face.index[a], face.columns[b]) == (50, 200)
        axes[1].text(b, a, f"{face.iloc[a, b]:.2f}", ha="center", va="center", fontsize=9,
                     fontweight="bold" if default else "normal",
                     color=BLUE if default else "black")
axes[1].set_xlabel("慢线")
axes[1].set_ylabel("快线")
axes[1].set_title("主线 v4 在 BTC 上的夏普曲面（蓝色是从没挑过的 50/200）")
fig.colorbar(image, ax=axes[1])
save(fig, "threshold.png")
