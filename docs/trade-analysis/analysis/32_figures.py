"""生成第 32 篇的插图：python 32_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 32_reversion.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("32_reversion.py").read_text(encoding="utf-8"), ns)
RP, RV, T, V, S, I = ns["RP"], ns["RV"], ns["T"], ns["V"], ns["S"], ns["I"]
spy, aapl, btc, MARKETS = ns["spy"], ns["aapl"], ns["btc"], ns["MARKETS"]
close, z, runs, table, before, DAY = ns["close"], ns["z"], ns["runs"], ns["table"], ns["before"], ns["DAY"]
CONNORS, runs_by_market, bottom = ns["CONNORS"], ns["runs_by_market"], ns["bottom"]
fake_markets, N_PATHS = ns["fake_markets"], ns["N_PATHS"]

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


# 图 1：决策点
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
window = close.loc["2018-09-01":DAY]
axes[0].plot(window.index, window.to_numpy(), color=GRAY, linewidth=1.4)
band = close.rolling(20).mean()
axes[0].plot(window.index, band.reindex(window.index).to_numpy(), color=BLUE, linewidth=1.0,
             linestyle="--", label="20 日均线")
lower = (band - 2 * close.rolling(20).std()).reindex(window.index)
axes[0].plot(window.index, lower.to_numpy(), color=PURPLE, linewidth=1.0, linestyle=":",
             label="均线下方 2 个标准差")
earlier = before[before["时间"] >= window.index[0]]
axes[0].scatter(earlier["时间"], earlier["收盘"], marker="v", s=70, color=UP, zorder=5,
                label="之前触发过的日子")
axes[0].scatter([DAY], [close.loc[DAY]], marker="v", s=140, color=DOWN, zorder=6)
axes[0].annotate(f"{DAY.date()}\n{close.loc[DAY]:.2f}\n连跌 5 天、偏离 {z.loc[DAY]:.2f}",
                 (DAY, close.loc[DAY]), textcoords="offset points", xytext=(-108, -58),
                 fontsize=9, color=DOWN,
                 arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.2))
axes[0].set_ylabel("SPY")
axes[0].set_title("买不买？")
axes[0].legend(fontsize=9, loc="lower left")
axes[0].grid(alpha=0.3)
axes[0].tick_params(axis="x", labelrotation=20)

y = np.arange(len(before))
axes[1].barh(y - 0.19, before["5 根后"], height=0.36, color=BLUE, label="5 根后")
axes[1].barh(y + 0.19, before["20 根后"], height=0.36, color=ORANGE, label="20 根后")
axes[1].axvline(0, color="black", linewidth=0.8)
axes[1].set_yticks(y, [d.strftime("%Y-%m-%d") for d in before["时间"]], fontsize=8)
axes[1].invert_yaxis()
axes[1].xaxis.set_major_formatter(percent)
axes[1].set_title(f"之前 {len(before)} 次：5 根后 {int((before['5 根后'] > 0).sum())} 次是涨的")
axes[1].legend(fontsize=9)
axes[1].grid(axis="x", alpha=0.3)
save(fig, "decision.png")

# 图 2：揭晓
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
span = close.loc["2020-01-15":"2020-05-15"]
axes[0].plot(span.index, span.to_numpy(), color=GRAY, linewidth=1.5)
axes[0].scatter([DAY], [close.loc[DAY]], marker="v", s=120, color=DOWN, zorder=5,
                label=f"决策点 {close.loc[DAY]:.2f}")
axes[0].scatter([bottom], [close.loc[bottom]], marker="o", s=90, color=PURPLE, zorder=5,
                label=f"{bottom.date()} 最低 {close.loc[bottom]:.2f}")
axes[0].annotate(f"{close.loc[bottom] / close.loc[DAY] - 1:+.1%}",
                 (bottom, close.loc[bottom]), textcoords="offset points", xytext=(10, -6),
                 fontsize=10, color=PURPLE)
axes[0].set_ylabel("SPY")
row = table[table["时间"] == DAY].iloc[0]
axes[0].set_title(f"揭晓：接下来 20 根 {row['20 根后']:.2%}，期间最低 {row['期间最低']:.2%}")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)
axes[0].tick_params(axis="x", labelrotation=20)

trades = runs_by_market["SPY"]["交易"]
covid = trades[(trades["进场日"] >= "2020-02-01") & (trades["进场日"] <= "2020-04-30")]
axes[1].plot(span.index, span.to_numpy(), color=GRAY, linewidth=1.3)
for _, trade in covid.iterrows():
    good = trade["收益"] > 0
    axes[1].plot([trade["进场日"], trade["出场日"]], [trade["进场价"], trade["出场价"]],
                 color=UP if good else DOWN, linewidth=2.4, marker="o", markersize=5)
    axes[1].annotate(f"{trade['收益']:+.2%}", (trade["出场日"], trade["出场价"]),
                     textcoords="offset points", xytext=(6, 8 if good else -14),
                     fontsize=9, color=UP if good else DOWN)
axes[1].set_ylabel("SPY")
axes[1].set_title(f"完整规则实际做的三笔：合计 {covid['收益'].sum():+.2%}")
axes[1].grid(alpha=0.3)
axes[1].tick_params(axis="x", labelrotation=20)
save(fig, "reveal.png")

# 图 3：信号的价值只存在于很短的窗口 + 方差比解释一切
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), dpi=150)
horizons = (1, 5, 10, 20)
stats = {k: RV.edge(table, close, horizon=k) for k in horizons}
x = np.arange(len(horizons))
axes[0].bar(x - 0.19, [stats[k]["胜率"] for k in horizons], width=0.36, color=BLUE, label="这个条件之后")
axes[0].bar(x + 0.19, [stats[k]["基准胜率"] for k in horizons], width=0.36, color=GRAY, label="随便哪天买")
twin = axes[0].twinx()
twin.plot(x, [stats[k]["最差"] for k in horizons], "o-", color=DOWN, linewidth=2.0, label="最差的那一次")
twin.yaxis.set_major_formatter(percent)
twin.set_ylabel("最差的那一次")
axes[0].set_xticks(x, [f"{k} 根后" for k in horizons])
axes[0].yaxis.set_major_formatter(percent)
axes[0].set_ylim(0, 1.0)
axes[0].set_ylabel("上涨的比例")
axes[0].set_title("优势只活在 5 根这个窗口里")
axes[0].legend(fontsize=9, loc="upper left")
twin.legend(fontsize=9, loc="lower left")
axes[0].grid(axis="y", alpha=0.3)

ratios = [S.variance_ratio(S.log_returns(MARKETS[n][0]["close"]), 60) for n in NAMES]
trend_sharpe = [RP.sharpe(T.turtle(MARKETS[n][0], T.TurtlePlan())["资金曲线"].pct_change().dropna(),
                          MARKETS[n][1]) for n in NAMES]
mean_sharpe = [RP.sharpe(runs_by_market[n]["资金曲线"].pct_change().dropna(), MARKETS[n][1])
               for n in NAMES]
axes[1].plot(ratios, trend_sharpe, "o-", color=DOWN, linewidth=2.0, markersize=9, label="趋势跟随（第 31 篇）")
axes[1].plot(ratios, mean_sharpe, "o-", color=BLUE, linewidth=2.0, markersize=9, label="均值回归（这一篇）")
for k, name in enumerate(NAMES):
    axes[1].annotate(name, (ratios[k], max(trend_sharpe[k], mean_sharpe[k])),
                     textcoords="offset points", xytext=(-10, 12), fontsize=10)
axes[1].axvline(1.0, color=GRAY, linestyle="--", linewidth=1.2)
axes[1].text(1.01, 0.1, "方差比 = 1\n左边反转、右边延续", fontsize=8.5, color=GRAY)
axes[1].set_xlabel("60 天方差比")
axes[1].set_ylabel("夏普比率")
axes[1].set_title("同一个数，解释了两篇的全部结论")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.3)
save(fig, "signal.png")

# 图 4：收益结构的镜像
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), dpi=150)
turtle_r = T.turtle(btc, T.TurtlePlan())["交易"]["R"]
mean_r = runs_by_market["BTC"]["交易"]["收益"]
for ax, values, title, color in [(axes[0], turtle_r / turtle_r.abs().max(), "趋势跟随（第 31 篇，BTC）", DOWN),
                                 (axes[0], mean_r / mean_r.abs().max(), "均值回归（这一篇，BTC）", BLUE)]:
    ax.hist(values, bins=40, histtype="step", linewidth=2.0, color=color, density=True, label=title)
axes[0].axvline(0, color="black", linewidth=0.8)
axes[0].set_xlabel("每一笔的盈亏（各自除以自己最大的那一笔）")
axes[0].set_title("一个右边有长尾，一个左边有长尾")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

best = T.contribution(turtle_r, tops=(1, 2, 3, 5, 8, 10, 15))
worst = RV.worst_trades(mean_r, tops=(1, 2, 3, 5, 8, 10, 15))
axes[1].plot(best["占总笔数"], best["占原来的"], "o-", color=DOWN, linewidth=2.0,
             label="趋势跟随：拿掉最赚的几笔")
axes[1].plot(worst["占总笔数"], worst["变成原来的"], "o-", color=BLUE, linewidth=2.0,
             label="均值回归：拿掉最亏的几笔")
axes[1].axhline(1.0, color=GRAY, linestyle="--", linewidth=1.2)
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].xaxis.set_major_formatter(percent)
axes[1].set_xlabel("拿掉的交易占全部的比例")
axes[1].set_ylabel("剩下的收益变成原来的几倍")
axes[1].set_title("一个靠几笔大赚，一个怕几笔大亏")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.3)
save(fig, "structure.png")

# 图 5：凹性与凸性
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.2), dpi=150)
for ax, name in zip(axes, NAMES):
    frame, periods = MARKETS[name]
    market_returns = frame["close"].pct_change()
    for label, curve, color in [("趋势跟随（凸）", T.turtle(frame, T.TurtlePlan())["资金曲线"], DOWN),
                                ("均值回归（凹）", runs_by_market[name]["资金曲线"], BLUE)]:
        strategy = curve.pct_change().dropna()
        shape = T.convexity(strategy, market_returns.reindex(strategy.index), buckets=5, window=20)
        ax.plot(shape["市场中位"], shape["策略平均"], "o-", color=color, linewidth=2.0, label=label)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.xaxis.set_major_formatter(percent)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1%}"))
    ax.set_xlabel(f"{name} 这 20 根涨了多少")
    ax.set_ylabel("策略这 20 根平均赚多少")
    ax.set_title(name)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
save(fig, "concavity.png")

# 图 6：对照的块长要比持仓期短
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), dpi=150)
blocks = (1, 2, 5, 20, 60)
for ax, (label, runner, plan_of, hold, n_paths) in zip(axes, [
        ("均值回归（中位持仓 2–3 根）", RV.reversion, lambda: RV.ReversionPlan(**CONNORS), 2.5, N_PATHS),
        ("趋势跟随（中位持仓 12–16 根）", T.turtle, lambda: T.TurtlePlan(), 14, 40)]):
    for name, color in zip(NAMES, COLORS):
        frame, periods = MARKETS[name]
        actual = RP.annual_return(runner(frame, plan_of())["资金曲线"], periods)
        values = []
        for block in blocks:
            fakes = np.array([RP.annual_return(runner(fake, plan_of())["资金曲线"], periods)
                              for fake in fake_markets(frame, block, n=n_paths)])
            values.append(float((fakes >= actual).mean()))
        ax.plot(blocks, values, "o-", color=color, linewidth=2.0, label=name)
    ax.axhline(0.05, color=GRAY, linestyle="--", linewidth=1.2, label="5% 那条线")
    ax.axvline(hold, color=PURPLE, linestyle=":", linewidth=1.6)
    ax.text(hold * 1.05, 0.55, "策略的持仓期", fontsize=8.5, color=PURPLE, rotation=90)
    ax.set_xscale("log")
    ax.set_xticks(blocks, [str(b) for b in blocks])
    ax.set_ylim(-0.03, 0.72)
    ax.set_xlabel("对照用的块长（根）")
    ax.set_ylabel("假数据比真实还好的比例（p）")
    ax.set_title(label)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, which="both")
save(fig, "blocks.png")

# 图 7：放进同一个账户
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
trend_curve = T.turtle(spy, T.TurtlePlan())["资金曲线"]
mean_curve = runs_by_market["SPY"]["资金曲线"]
mixed = RV.blend({"趋势跟随": trend_curve, "均值回归": mean_curve}, [0.5, 0.5])
for curve, label, color, width in [(trend_curve, "趋势跟随", DOWN, 1.2),
                                   (mean_curve, "均值回归", BLUE, 1.2),
                                   (mixed, "五五开，每月再平衡", PURPLE, 2.0)]:
    normalised = curve / curve.iloc[0]
    axes[0].plot(normalised.index, normalised.to_numpy(), color=color, linewidth=width,
                 label=f"{label}：夏普 {RP.sharpe(curve.pct_change().dropna(), 252):.3f}")
axes[0].set_ylabel("本金的几倍")
axes[0].set_title("SPY 上的两条腿和它们的组合")
axes[0].legend(fontsize=9, loc="upper left")
axes[0].grid(alpha=0.3)

labels = ["年化", "|最大回撤|", "夏普", "卡玛"]
series = {"趋势跟随": trend_curve, "均值回归": mean_curve, "五五开": mixed}
y = np.arange(len(labels))
for offset, (name, curve) in enumerate(series.items()):
    daily = curve.pct_change().dropna()
    values = [RP.annual_return(curve, 252), -RP.max_drawdown(curve),
              RP.sharpe(daily, 252), RP.calmar(curve, 252)]
    axes[1].barh(y + (offset - 1) * 0.27, values, height=0.25,
                 color=[DOWN, BLUE, PURPLE][offset], label=name)
    for k, value in enumerate(values):
        axes[1].text(value + 0.012, k + (offset - 1) * 0.27, f"{value:.3f}", va="center", fontsize=8)
axes[1].set_yticks(y, labels)
axes[1].invert_yaxis()
axes[1].set_xlim(0, 1.22)
axes[1].set_title("组合把回撤砍掉一半，夏普升到 0.98")
axes[1].legend(fontsize=9, loc="lower right")
axes[1].grid(axis="x", alpha=0.3)
save(fig, "blend.png")
