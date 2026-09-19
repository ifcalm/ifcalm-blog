"""生成第 31 篇的插图：python 31_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 31_trend.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("31_trend.py").read_text(encoding="utf-8"), ns)
RP, T, V, C, BT, I = ns["RP"], ns["T"], ns["V"], ns["C"], ns["BT"], ns["I"]
btc, spy, aapl, MARKETS = ns["btc"], ns["spy"], ns["aapl"], ns["MARKETS"]
history, window, signal, runs = ns["history"], ns["window"], ns["signal"], ns["runs"]
N_PATHS, GRID, DEFAULT = ns["N_PATHS"], ns["GRID"], ns["DEFAULT"]

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


# 图 1：决策点——过去十次突破
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
price = btc["close"].loc["2022-08-01":"2023-10-16"]
axes[0].plot(price.index, price.to_numpy(), color=GRAY, linewidth=1.3)
channel = T.donchian(btc["high"], btc["low"], 20).reindex(price.index)
axes[0].plot(channel.index, channel["上轨"].to_numpy(), color=BLUE, linewidth=0.9, linestyle="--",
             label="20 日通道上轨")
for _, row in window.iterrows():
    good = row["R"] > 0
    axes[0].scatter([row["进场日"]], [row["第一个单位的价"]], marker="^", s=60,
                    color=UP if good else DOWN, zorder=5)
    axes[0].plot([row["进场日"], row["出场日"]], [row["第一个单位的价"], row["出场价"]],
                 color=UP if good else DOWN, linewidth=1.6, alpha=0.8)
axes[0].axvline(signal["进场日"], color=PURPLE, linewidth=1.6)
axes[0].annotate(f"第 11 次\n{signal['进场日'].date()}\n{signal['第一个单位的价']:,.0f}",
                 (signal["进场日"], float(price.min())), textcoords="offset points",
                 xytext=(-88, 30), fontsize=9, color=PURPLE)
axes[0].set_ylabel("BTC")
axes[0].set_title("十三个月，十次突破：绿色走出去了，红色是假的")
axes[0].legend(fontsize=9, loc="upper left")
axes[0].grid(alpha=0.3)
axes[0].tick_params(axis="x", labelrotation=20)

order = window["R"].sort_values()
axes[1].barh(range(len(order)), order.to_numpy(),
             color=[UP if v > 0 else DOWN for v in order])
axes[1].set_yticks(range(len(order)), [d.strftime("%Y-%m-%d") for d in window.loc[order.index, "进场日"]],
                   fontsize=8)
axes[1].axvline(0, color="black", linewidth=0.8)
for i, v in enumerate(order):
    axes[1].text(v + (0.12 if v > 0 else -0.12), i, f"{v:+.2f}", va="center", fontsize=8,
                 ha="left" if v > 0 else "right")
axes[1].set_xlim(-2.2, 9.5)
axes[1].set_xlabel("R 倍数")
axes[1].set_title(f"十笔合计 {window['R'].sum():+.2f}R")
axes[1].grid(axis="x", alpha=0.3)
save(fig, "decision.png")

# 图 2：揭晓——第 11 次，以及加仓是怎么加的
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
span = btc.loc["2023-09-15":"2024-01-20"]
for ax, units, title in [(axes[0], 1, "第 11 次突破：一个单位"),
                         (axes[1], 4, "同一笔，金字塔加到四个单位")]:
    result = T.turtle(btc, T.TurtlePlan(max_units=units))
    trades = result["交易"]
    row = trades[trades["进场日"] == signal["进场日"]].iloc[0]
    ax.plot(span.index, span["close"].to_numpy(), color=GRAY, linewidth=1.3, label="BTC 收盘")
    band = T.donchian(btc["high"], btc["low"], 10).reindex(span.index)
    ax.plot(band.index, band["下轨"].to_numpy(), color=BLUE, linewidth=0.9, linestyle="--",
            label="10 日通道下轨（出场线）")
    adds = result["加仓"]
    inside = adds[(adds["时间"] >= row["进场日"]) & (adds["时间"] <= row["出场日"])]
    ax.step(inside["时间"], inside["止损移到"], where="post", color=DOWN, linewidth=1.4,
            label="止损（每加一个单位就上移）")
    ax.scatter(inside["时间"], inside["成交价"], marker="^", s=70, color=UP, zorder=5,
               label=f"买入（{len(inside)} 个单位）")
    ax.scatter([row["出场日"]], [row["出场价"]], marker="v", s=90, color=PURPLE, zorder=5,
               label=f"出场 {row['出场价']:,.0f}")
    ax.set_title(f"{title}：R = {row['R']:+.2f}")
    ax.set_ylabel("BTC")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    ax.tick_params(axis="x", labelrotation=20)
save(fig, "reveal.png")

# 图 3：一次突破有多大概率走得出去
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), dpi=150)
names = list(MARKETS)
rates, colors = [], [BLUE, ORANGE, DOWN]
for name, color in zip(names, colors):
    table = T.breakouts(MARKETS[name][0], 20, horizon=20)
    rates.append(T.follow_through(table)["假突破比例"])
    axes[0].hist(table["之后涨幅"].dropna(), bins=40, histtype="step", linewidth=1.8,
                 color=color, density=True, label=f"{name}（{len(table)} 次）")
axes[0].axvline(0, color="black", linewidth=1.0)
axes[0].xaxis.set_major_formatter(percent)
axes[0].set_xlim(-0.35, 0.45)
axes[0].set_xlabel("突破之后 20 根的涨跌")
axes[0].set_title("突破之后会怎样：一个宽得离谱的分布")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

x = np.arange(len(names))
axes[1].bar(x, rates, color=colors, width=0.55)
for i, v in enumerate(rates):
    axes[1].text(i, v + 0.01, f"{v:.1%}", ha="center", fontsize=10)
axes[1].axhline(0.5, color=GRAY, linestyle="--", linewidth=1.2, label="一半一半")
axes[1].set_xticks(x, names)
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_ylim(0, 0.62)
axes[1].set_ylabel("20 根之后仍低于突破价的比例")
axes[1].set_title("假突破比例（最宽松的口径）")
axes[1].legend(fontsize=9)
axes[1].grid(axis="y", alpha=0.3)
save(fig, "breakout.png")

# 图 4：收益结构
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), dpi=150)
values = runs["BTC"]["交易"]["R"]
axes[0].hist(values, bins=40, color=BLUE, alpha=0.85)
axes[0].axvline(0, color="black", linewidth=1.0)
axes[0].axvline(float(values.median()), color=DOWN, linestyle="--", linewidth=1.6,
                label=f"中位数 {values.median():+.2f}R")
axes[0].axvline(float(values.mean()), color=GREEN, linewidth=1.6, label=f"平均 {values.mean():+.2f}R")
axes[0].set_xlabel("每一笔赚了几个 R")
axes[0].set_title(f"BTC 上 {len(values)} 笔：典型的一笔是亏的，平均数全靠尾巴")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3)

for name, color in zip(names, colors):
    table = T.contribution(runs[name]["交易"]["R"], tops=(1, 2, 3, 5, 8, 10, 15))
    axes[1].plot(table["占总笔数"], table["占原来的"], "o-", color=color, linewidth=1.8, label=name)
axes[1].axhline(0, color="black", linewidth=0.8)
axes[1].xaxis.set_major_formatter(percent)
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_xlabel("拿掉最赚的那几笔占全部交易的比例")
axes[1].set_ylabel("剩下的收益占原来的")
axes[1].set_title("拿掉最赚的 15% 的交易，九年收益归零")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.3)
save(fig, "structure.png")

# 图 5：凸性
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.2), dpi=150)
for ax, name in zip(axes, names):
    frame, periods = MARKETS[name]
    for label, plan, color in [("只做多", T.TurtlePlan(), BLUE), ("多空都做", T.TurtlePlan(side="both"), DOWN)]:
        curve = runs[name]["资金曲线"] if label == "只做多" else T.turtle(frame, plan)["资金曲线"]
        strategy = curve.pct_change().dropna()
        market = frame["close"].pct_change().reindex(strategy.index)
        table = T.convexity(strategy, market, buckets=5, window=20)
        ax.plot(table["市场中位"], table["策略中位"], "o-", color=color, linewidth=2.0, label=label)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.xaxis.set_major_formatter(percent)
    ax.yaxis.set_major_formatter(percent)
    ax.set_xlabel(f"{name} 这 20 根涨了多少")
    ax.set_ylabel("策略这 20 根赚了多少")
    ax.set_title(f"{name}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
save(fig, "convexity.png")

# 图 6：蒙特卡洛——把趋势拆掉
fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.2), dpi=150)
for ax, name in zip(axes, names):
    frame, periods = MARKETS[name]
    real = RP.annual_return(runs[name]["资金曲线"], periods)
    fakes = []
    for path in V.synthetic_close(frame["close"], n=N_PATHS, block=20, seed=31):
        scale = path / frame["close"].to_numpy()
        fake = pd.DataFrame({c: frame[c].to_numpy() * scale for c in ["open", "high", "low", "close"]},
                            index=frame.index)
        fakes.append(RP.annual_return(T.turtle(fake, T.TurtlePlan())["资金曲线"], periods))
    fakes = np.array(fakes)
    ax.hist(fakes, bins=30, color=GRAY, alpha=0.85, label=f"把趋势拆掉之后（{N_PATHS} 条）")
    ax.axvline(real, color=DOWN, linestyle="--", linewidth=2.0, label=f"真实数据 {real:.1%}")
    ax.axvline(float(np.median(fakes)), color=BLUE, linewidth=1.5,
               label=f"假数据中位 {np.median(fakes):.1%}")
    ax.xaxis.set_major_formatter(percent)
    ax.set_xlabel("同一套规则跑出来的年化")
    ax.set_title(f"{name}：{int((fakes >= real).sum())}/{N_PATHS} 条假数据比真实的还好")
    ax.legend(fontsize=8.5)
    ax.grid(alpha=0.3)
save(fig, "montecarlo.png")

# 图 7：和主线 v4、买入持有并排
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
btc_cost = C.crypto(1.0, "现货 taker", spread_bp=C.BTC_PERP_SPREAD_BP)["占名义价值"] + 0.00097 / 2
price = btc["close"]
turtle_curve = T.turtle(btc, T.TurtlePlan(fee_rate=btc_cost))["资金曲线"]
plan = BT.Plan(entry=((I.sma(price, 50) > I.sma(price, 200))
                      & (price >= price.rolling(20).max())).fillna(False),
               exit=I.cross_below(I.sma(price, 50), I.sma(price, 200)).fillna(False),
               stop="chandelier", k=3.0, trigger="close", sizing="risk",
               risk_per_trade=0.10, fee_rate=btc_cost)
main_curve = BT.run(btc, plan, 100_000.0)["资金曲线"]
hold = price / price.loc[turtle_curve.index[0]] * 100_000
for curve, label, color in [(turtle_curve, f"海龟（原版）年化 {RP.annual_return(turtle_curve, 365):.1%}", DOWN),
                            (main_curve, f"主线 v4 年化 {RP.annual_return(main_curve, 365):.1%}", BLUE),
                            (hold.loc[turtle_curve.index[0]:], f"买入持有 年化 {RP.annual_return(price, 365):.1%}", GRAY)]:
    axes[0].plot(curve.index, curve.to_numpy(), color=color, linewidth=1.6, label=label)
logy(axes[0], [1e5, 3e5, 1e6, 3e6], ["10 万", "30 万", "100 万", "300 万"])
axes[0].set_ylabel("账户（对数轴）")
axes[0].set_title("BTC，含成本，都从 10 万美元开始")
axes[0].legend(fontsize=9, loc="upper left")
axes[0].grid(alpha=0.3)

labels = ["年化", "|最大回撤|", "夏普", "卡玛"]
series = {"海龟": turtle_curve, "主线 v4": main_curve, "买入持有": price}
y = np.arange(len(labels))
for offset, (name, curve) in enumerate(series.items()):
    daily = curve.pct_change().dropna()
    values = [RP.annual_return(curve, 365), -RP.max_drawdown(curve),
              RP.sharpe(daily, 365), RP.calmar(curve, 365)]
    axes[1].barh(y + (offset - 1) * 0.27, values, height=0.25,
                 color=[DOWN, BLUE, GRAY][offset], label=name)
    for i, v in enumerate(values):
        axes[1].text(v + 0.02, i + (offset - 1) * 0.27, f"{v:.2f}", va="center", fontsize=8)
axes[1].set_yticks(y, labels)
axes[1].invert_yaxis()
axes[1].set_xlim(0, 1.55)
axes[1].set_title("同一段数据，四个指标")
axes[1].legend(fontsize=9, loc="lower right")
axes[1].grid(axis="x", alpha=0.3)
save(fig, "compare.png")
