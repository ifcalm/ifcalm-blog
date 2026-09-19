"""生成第 29 篇的插图：python 29_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 29_evaluation.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("29_evaluation.py").read_text(encoding="utf-8"), ns)
RP, C, rng = ns["RP"], ns["C"], np.random.default_rng(129)
curve_a, curve_b, trades_a, trades_b = ns["curve_a"], ns["curve_b"], ns["trades_a"], ns["trades_b"]
returns_a, returns_b, buy_hold = ns["returns_a"], ns["returns_b"], ns["buy_hold"]
rf, mainline, ONE_WAY, YEARS = ns["rf"], ns["mainline"], ns["ONE_WAY"], ns["YEARS"]
build, by_trade = ns["build"], ns["by_trade"]
d1, h4, position_a, position_b = ns["d1"], ns["h4"], ns["position_a"], ns["position_b"]

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


# 图 1：决策点——两条夏普一样的曲线
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
axes[0].plot(curve_a.index, curve_a.to_numpy(), color=BLUE, linewidth=1.5, label="A 日线唐奇安 40/20（35 笔）")
axes[0].plot(curve_b.index, curve_b.to_numpy(), color=ORANGE, linewidth=1.5, label="B 4 小时突破（1,061 笔）")
logy(axes[0], [1, 10, 100], ["1", "10", "100"])
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title("两条策略，同一个市场，同一段时间")
axes[0].legend(loc="upper left", fontsize=9)
axes[0].grid(alpha=0.3)

labels = ["年化收益", "年化波动", "|最大回撤|", "卡玛比率", "夏普比率"]
pick = lambda curve, series: [RP.annual_return(curve, 365), RP.annual_vol(series, 365),
                              -RP.max_drawdown(curve), RP.calmar(curve, 365), RP.sharpe(series, 365)]
values_a, values_b = pick(curve_a, returns_a), pick(curve_b, returns_b)
y = np.arange(len(labels))
axes[1].barh(y - 0.19, values_a, height=0.36, color=BLUE, label="A")
axes[1].barh(y + 0.19, values_b, height=0.36, color=ORANGE, label="B")
for i, (va, vb) in enumerate(zip(values_a, values_b)):
    axes[1].text(va + 0.03, i - 0.19, f"{va:.4f}", va="center", fontsize=9, color=BLUE)
    axes[1].text(vb + 0.03, i + 0.19, f"{vb:.4f}", va="center", fontsize=9, color=ORANGE)
axes[1].set_yticks(y)
axes[1].set_yticklabels(labels)
axes[1].invert_yaxis()
axes[1].set_xlim(0, 1.78)
axes[1].set_title("夏普比率 1.3086 对 1.3072")
axes[1].legend(fontsize=9, loc="lower right")
axes[1].grid(axis="x", alpha=0.3)
save(fig, "decision.png")

# 图 2：夏普比率的机制（均值 ∝ k、标准差 ∝ √k）与换一个计算周期
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), dpi=150)
ks = np.array([1, 2, 3, 5, 10, 20, 40, 60, 90, 120])
means = np.array([returns_a.rolling(int(k)).sum().dropna().mean() for k in ks])
stds = np.array([returns_a.rolling(int(k)).sum().dropna().std() for k in ks])
axes[0].plot(ks, means / means[0], "o-", color=GREEN, label="合并 k 根之后的均值")
axes[0].plot(ks, stds / stds[0], "o-", color=DOWN, label="合并 k 根之后的标准差")
axes[0].plot(ks, ks, "--", color=GRAY, linewidth=1, label="正比于 k")
axes[0].plot(ks, np.sqrt(ks), ":", color=GRAY, linewidth=1.4, label="正比于 √k")
axes[0].set_xscale("log")
logy(axes[0], [1, 10, 100], ["1 倍", "10 倍", "100 倍"])
axes[0].set_xlabel("把几根 K 线合并成一根（k）")
axes[0].set_title("信噪比按 √k 长大：这就是「年化」的来历")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3, which="both")

names = ["A", "B", "BTC 买入持有"]
series = {"A": curve_a, "B": curve_b, "BTC 买入持有": ns["close_d"]}
x = np.arange(len(names))
for offset, (label, rule, periods, color) in enumerate([("按日线算", None, 365, BLUE),
                                                        ("按周线算", "W", 52, ORANGE),
                                                        ("按月线算", "ME", 12, PURPLE)]):
    values = [RP.sharpe((series[n] if rule is None else series[n].resample(rule).last())
                        .pct_change().dropna(), periods) for n in names]
    axes[1].bar(x + (offset - 1) * 0.27, values, width=0.25, color=color, label=label)
    for i, v in enumerate(values):
        axes[1].text(i + (offset - 1) * 0.27, v + 0.02, f"{v:.3f}", ha="center", fontsize=8)
axes[1].set_xticks(x)
axes[1].set_xticklabels(names)
axes[1].set_ylabel("夏普比率")
axes[1].set_ylim(0, 1.62)
axes[1].set_title("同一条曲线，换一个计算周期，第一名就换人")
axes[1].legend(fontsize=9)
axes[1].grid(axis="y", alpha=0.3)
save(fig, "sharpe.png")

# 图 3：三种骗法——抹平净值、无风险利率、加杠杆
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.2), dpi=150)
smoothed = returns_a.rolling(10).mean().dropna()
raw_window = returns_a.loc["2020-07-01":"2021-06-30"]
smooth_window = smoothed.loc["2020-07-01":"2021-06-30"]
axes[0].plot(raw_window.index, raw_window.to_numpy(), color=GRAY, linewidth=0.9,
             label=f"真实的日收益率（夏普 {RP.sharpe(returns_a, 365):.2f}）")
axes[0].plot(smooth_window.index, smooth_window.to_numpy(), color=DOWN, linewidth=2.0,
             label=f"报告的 10 天平均（夏普 {RP.sharpe(smoothed, 365):.2f}）")
axes[0].axhline(float(returns_a.mean()), color=GREEN, linestyle="--", linewidth=1.2,
                label=f"两条线的均值都是 {returns_a.mean():.4f}")
axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
axes[0].set_title("骗法二：分子没动，分母塌了三分之二")
axes[0].legend(fontsize=8.5)
axes[0].grid(alpha=0.3)
axes[0].tick_params(axis="x", labelrotation=20)

rate = rf.loc["2017-08-17":]
axes[1].fill_between(rate.index, rate.to_numpy(), color=PURPLE, alpha=0.25)
axes[1].plot(rate.index, rate.to_numpy(), color=PURPLE, linewidth=1.4)
axes[1].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
axes[1].set_ylabel("3 个月国库券收益率")
twin = axes[1].twinx()
gaps = pd.Series({year: RP.sharpe(chunk, 365) - RP.sharpe(chunk, 365, rf)
                  for year, chunk in returns_a.groupby(returns_a.index.year)})
twin.bar([pd.Timestamp(f"{y}-07-01", tz="UTC") for y in gaps.index], gaps.to_numpy(),
         width=200, color=ORANGE, alpha=0.75)
twin.set_ylabel("当年夏普被高估了多少")
twin.set_ylim(0, 0.24)
axes[1].set_title("骗法三：无风险利率从 0.00% 涨到 5.36%")
axes[1].grid(alpha=0.3)
axes[1].tick_params(axis="x", labelrotation=20)

for leverage, color in [(1, BLUE), (2, ORANGE), (3, DOWN)]:
    levered = RP.to_curve((leverage * buy_hold).clip(lower=-1.0))
    sharpe_value = RP.sharpe(levered.pct_change().dropna(), 365)
    axes[2].plot(levered.index, levered.clip(lower=1e-4).to_numpy(), color=color, linewidth=1.5,
                 label=f"{leverage} 倍（夏普 {sharpe_value:.4f}）")
logy(axes[2], [1e-4, 1e-2, 1, 1e2], ["归零", "0.01", "1", "100"])
axes[2].set_title("骗法四：3 倍杠杆已经归零，夏普还有 0.52")
axes[2].legend(fontsize=9, loc="lower left")
axes[2].grid(alpha=0.3)
axes[2].tick_params(axis="x", labelrotation=20)
save(fig, "fooled.png")

# 图 4：最大回撤是一个极值，样本越长它越深
mu, sigma = returns_a.mean(), returns_a.std()
year_list = [1, 2, 3, 5, 9, 20]
draws = {}
for years in year_list:
    n = int(365 * years)
    draws[years] = np.array([RP.max_drawdown(RP.to_curve(pd.Series(rng.normal(mu, sigma, n),
                                                                   index=pd.RangeIndex(n))))
                             for _ in range(600)])
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), dpi=150)
axes[0].boxplot([draws[y] for y in year_list], tick_labels=[str(y) for y in year_list],
                showfliers=False, medianprops=dict(color=DOWN, linewidth=1.6))
axes[0].axhline(RP.max_drawdown(curve_a), color=BLUE, linestyle="--", linewidth=1.4,
                label=f"A 真实的最大回撤 {RP.max_drawdown(curve_a):.1%}")
axes[0].yaxis.set_major_formatter(percent)
axes[0].set_xlabel("随机游走跑几年（μ 和 σ 都取自 A）")
axes[0].set_title("同一个过程，样本越长，回撤越深")
axes[0].legend(fontsize=9)
axes[0].grid(axis="y", alpha=0.3)

lengths = list(range(365, len(curve_a), 30))
xs = [n / 365 for n in lengths]
axes[1].plot(xs, [RP.max_drawdown(curve_a.iloc[:n]) for n in lengths],
             color=BLUE, linewidth=1.8, label="A 的最大回撤（左轴）")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_ylim(-0.62, -0.38)
axes[1].set_xlabel("回测只跑到第几年")
calmar_axis = axes[1].twinx()
calmar_axis.plot(xs, [RP.calmar(curve_a.iloc[:n], 365) for n in lengths],
                 color=ORANGE, linewidth=1.8, label="A 的卡玛比率（右轴）")
calmar_axis.set_ylabel("卡玛比率")
calmar_axis.set_ylim(0.8, 3.2)
axes[1].set_title("报告写得越早，这两个数越好看")
handles = axes[1].get_legend_handles_labels()[0] + calmar_axis.get_legend_handles_labels()[0]
axes[1].legend(handles, [h.get_label() for h in handles], fontsize=9, loc="lower left")
axes[1].grid(alpha=0.3)
save(fig, "drawdown.png")

# 图 5：换一个重抽单位
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), dpi=150, sharex=True)
for ax, (name, series, trades, color) in zip(axes, [
        ("A 日线唐奇安 40/20（35 笔）", returns_a, trades_a, BLUE),
        ("B 4 小时突破（1,061 笔）", returns_b, trades_b, ORANGE)]):
    daily = np.array([RP.annual_return(RP.to_curve(pd.Series(
        rng.choice(series.to_numpy(float), size=len(series), replace=True), index=series.index)), 365)
        for _ in range(2000)])
    per_trade = by_trade(trades, n=2000, seed=129)
    bins = np.linspace(0, 1.6, 60)
    ax.hist(daily, bins=bins, color=GRAY, alpha=0.75, label=f"按天重抽（宽 {np.percentile(daily, 95) - np.percentile(daily, 5):.2f}）")
    ax.hist(per_trade, bins=bins, histtype="step", color=color, linewidth=2.0,
            label=f"按交易重抽（宽 {np.percentile(per_trade, 95) - np.percentile(per_trade, 5):.2f}）")
    ax.axvline(RP.annual_return(RP.to_curve(series), 365), color=DOWN, linestyle="--", linewidth=1.4)
    ax.xaxis.set_major_formatter(percent)
    ax.set_xlabel("重抽出来的年化收益")
    ax.set_title(name)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
save(fig, "bootstrap.png")

# 图 6：要跑多少年才能把 t 值攒到 2
fig, ax = plt.subplots(figsize=(9.5, 4.6), dpi=150)
grid = np.linspace(0.2, 3.0, 300)
ax.plot(grid, [RP.years_needed(s, 2.0, 365) for s in grid], color=BLUE, linewidth=2.0)
ax.fill_between(grid, [RP.years_needed(s, 2.0, 365) for s in grid], 200, color=DOWN, alpha=0.08)
ax.fill_between(grid, 0.1, [RP.years_needed(s, 2.0, 365) for s in grid], color=GREEN, alpha=0.08)
points = [("A 和 B（夏普都是 1.31）", RP.sharpe(returns_a, 365), len(curve_a) / 365)]
for name, (result, periods) in mainline.items():
    curve = result["资金曲线"]
    points.append((f"主线 v4 · {name}", RP.sharpe(curve.pct_change().dropna(), periods, rf),
                   len(curve) / periods))
points.sort(key=lambda p: p[1])
for i, (name, value, have) in enumerate(points):
    ax.scatter([value], [have], s=70, color=PURPLE, zorder=5)
    ax.annotate(f"{name}\n手上有 {have:.1f} 年，要 {RP.years_needed(value, 2.0, 365):.0f} 年",
                (value, have), textcoords="offset points", xytext=(-14, 42 + 46 * (i % 2)),
                fontsize=8.5, arrowprops=dict(arrowstyle="-", color=GRAY, linewidth=0.8))
logy(ax, [1, 10, 100], ["1 年", "10 年", "100 年"])
ax.set_xlabel("年化夏普比率")
ax.set_ylabel("要跑多少年，t 值才到 2")
ax.set_title("点在绿区里才算「数据够了」")
ax.set_ylim(0.3, 900)
ax.grid(alpha=0.3, which="both")
save(fig, "significance.png")

# 图 7：揭晓（下）——把成本放回去
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
pairs = [("A 日线唐奇安 40/20", d1, position_a, BLUE), ("B 4 小时突破", h4, position_b, ORANGE)]
bars = []
for name, df, position, color in pairs:
    net = build(df, position, 0.0)[0]
    gross = build(df, position, ONE_WAY)[0]
    axes[0].plot(net.index, net.to_numpy(), color=color, linewidth=1.0, alpha=0.45)
    axes[0].plot(gross.index, gross.to_numpy(), color=color, linewidth=1.8, label=f"{name}（含成本）")
    bars.append((name, RP.sharpe(net.pct_change().dropna(), 365),
                 RP.sharpe(gross.pct_change().dropna(), 365), color))
logy(axes[0], [1, 10, 100], ["1", "10", "100"])
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title("细线是不算成本，粗线是算上成本")
axes[0].legend(fontsize=9, loc="upper left")
axes[0].grid(alpha=0.3)

x = np.arange(len(bars))
axes[1].bar(x - 0.19, [b[1] for b in bars], width=0.36, color=GRAY, label="不算成本")
axes[1].bar(x + 0.19, [b[2] for b in bars], width=0.36, color=[b[3] for b in bars], label="算上成本")
for i, b in enumerate(bars):
    axes[1].text(i - 0.19, b[1] + 0.02, f"{b[1]:.4f}", ha="center", fontsize=9)
    axes[1].text(i + 0.19, b[2] + 0.02, f"{b[2]:.4f}", ha="center", fontsize=9)
    axes[1].annotate("", xy=(i + 0.19, b[2]), xytext=(i - 0.19, b[1]),
                     arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.4))
axes[1].set_xticks(x)
axes[1].set_xticklabels(["A（每年 3.9 笔）", "B（每年 117.4 笔）"])
axes[1].set_ylabel("夏普比率")
axes[1].set_ylim(0, 1.55)
axes[1].set_title("同样的单边成本 0.1002%")
axes[1].legend(fontsize=9)
axes[1].grid(axis="y", alpha=0.3)
save(fig, "reveal.png")
