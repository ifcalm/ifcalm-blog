"""生成第 28 篇的插图：python 28_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 28_bias_costs.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("28_bias_costs.py").read_text(encoding="utf-8"), ns)
BT, C, D, I, R, ST = ns["BT"], ns["C"], ns["D"], ns["I"], ns["R"], ns["ST"]
basket, original, best, steps = ns["basket"], ns["original"], ns["best"], ns["steps"]
close, returns, turnover, alive = ns["close"], ns["returns"], ns["turnover"], ns["alive"]
held_all, START = ns["held_all"], ns["START"]
real, fake_max, PARAMS, DEFAULT = ns["real"], ns["fake_max"], ns["PARAMS"], ns["DEFAULT"]
values_in, values_out = ns["values_in"], ns["values_out"]
price, swings, lows, book, by_day = ns["price"], ns["swings"], ns["lows"], ns["book"], ns["by_day"]
unadjusted, nasdaq, total_return = ns["unadjusted"], ns["nasdaq"], ns["total_return"]

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


# 图 1：决策点
curve = original["资金曲线"]
yearly = (1 + original["每日收益"]).groupby(original["每日收益"].index.year).prod() - 1
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
axes[0].plot(curve.index, curve.to_numpy(), color=DOWN, linewidth=1.6)
axes[0].set_yscale("log")
axes[0].set_yticks([1, 10, 100])
axes[0].set_yticklabels(["1", "10", "100"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title(f"年化 {original['年化']:.1%}，最大回撤 {original['最大回撤']:.1%}，期末 {curve.iloc[-1]:,.0f} 倍")
axes[0].grid(alpha=0.25, which="both")
axes[1].bar(yearly.index.astype(str), yearly.to_numpy(),
            color=[UP if v > 0 else DOWN for v in yearly])
for x, value in zip(range(len(yearly)), yearly):
    axes[1].text(x, value + (0.3 if value > 0 else -0.6), f"{value:.0%}", ha="center", fontsize=8.5)
axes[1].axhline(0, color="#333333", linewidth=1.0)
axes[1].set_ylabel("当年收益")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_title("七年里六年赚钱")
axes[1].grid(alpha=0.25, axis="y")
save(fig, "decision.png")

# 图 2：四步瀑布
results = [basket(universe, params[0], params[1], gate, cost)
           for _, universe, params, gate, cost in steps]
labels = [label for label, *_ in steps]
values = [r["年化"] for r in results]
fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.6), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
positions = np.arange(len(values))
axes[0].bar(positions, values, color=[DOWN] + [BLUE] * 2 + [PURPLE] + [ORANGE], alpha=0.9)
for x, value in zip(positions, values):
    axes[0].text(x, value + (0.05 if value > 0 else 0.04), f"{value:.1%}", ha="center", fontsize=9.5,
                 va="bottom" if value > 0 else "bottom")
axes[0].axhline(0, color="#333333", linewidth=1.0)
axes[0].set_xticks(positions)
axes[0].set_xticklabels(["原样", "① 不挑\n参数", "② 门槛\n老实", "③ 名单\n老实", "④ 加上\n成本"], fontsize=9)
axes[0].set_ylabel("年化")
axes[0].yaxis.set_major_formatter(percent)
axes[0].set_title("一个一个修：123.5% 是怎么变成负数的")
axes[0].grid(alpha=0.25, axis="y")
for result, label, color in zip(results, ["原样（四个问题都在）", "① 不挑参数", "② 门槛老实",
                                          "③ 名单老实", "④ 加上成本"],
                                [DOWN, BLUE, "#6baed6", PURPLE, ORANGE]):
    axes[1].plot(result["资金曲线"].index, result["资金曲线"].clip(lower=1e-3).to_numpy(),
                 color=color, linewidth=1.4, label=label)
axes[1].set_yscale("log")
axes[1].set_yticks([1e-2, 1, 1e2])
axes[1].set_yticklabels(["0.01", "1", "100"])
axes[1].yaxis.set_minor_formatter(plt.NullFormatter())
axes[1].set_ylabel("本金的几倍（对数轴）")
axes[1].legend(fontsize=8)
axes[1].set_title("同一条策略的五条资金曲线")
axes[1].grid(alpha=0.25, which="both")
save(fig, "waterfall.png")

# 图 3：数据窥探
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
axes[0].hist(real.to_numpy(), bins=np.arange(0, 0.40, 0.01), color=BLUE, alpha=0.75,
             label=f"真实数据的 {len(PARAMS)} 组")
axes[0].hist(fake_max.to_numpy(), bins=np.arange(0, 0.40, 0.01), color=DOWN, alpha=0.55,
             label="打乱 100 次，每次「最好的一组」")
axes[0].axvline(real[DEFAULT], color="#333333", linewidth=1.4, linestyle="--",
                label=f"默认参数 {real[DEFAULT]:.1%}")
axes[0].axvline(real.max(), color=GREEN, linewidth=1.4, label=f"真实数据里最好的一组 {real.max():.1%}")
axes[0].set_xlabel("年化")
axes[0].set_ylabel("组数 / 次数")
axes[0].xaxis.set_major_formatter(percent)
axes[0].set_title("在没有趋势的数据上挑最好，也能挑出两成年化")
axes[0].legend(fontsize=8)
axes[0].grid(alpha=0.25)
axes[1].scatter(values_in.to_numpy(), values_out.to_numpy(), s=12, color=BLUE, alpha=0.55)
axes[1].scatter([values_in[values_in.idxmax()]], [values_out[values_in.idxmax()]], s=70,
                color=DOWN, marker="*", label="样本内最优")
axes[1].scatter([values_in[DEFAULT]], [values_out[DEFAULT]], s=50, color=GREEN, marker="D",
                label="默认参数")
axes[1].axhline(values_out.median(), color=GRAY, linewidth=1.0, linestyle=":",
                label=f"样本外中位数 {values_out.median():.1%}")
axes[1].set_xlabel("样本内年化（前三分之二）")
axes[1].set_ylabel("样本外年化（后三分之一）")
axes[1].xaxis.set_major_formatter(percent)
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_title(f"样本内排名和样本外排名的秩相关 {values_in.rank().corr(values_out.rank()):.2f}")
axes[1].legend(fontsize=8)
axes[1].grid(alpha=0.25)
save(fig, "snooping.png")

# 图 4：幸存者
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
for label, columns, color in [("只用今天还在交易的 704 个", close.columns[alive], DOWN),
                              ("全部上过市的 864 个", close.columns, BLUE)]:
    held, part = held_all[columns], returns[columns]
    count = held.sum(axis=1)
    daily = ((held * part).sum(axis=1) / count.replace(0, np.nan)).fillna(0.0).loc[START:]
    equity = (1 + daily).cumprod()
    axes[0].plot(equity.index, equity.to_numpy(), color=color, linewidth=1.5,
                 label=f"{label}（年化 {equity.iloc[-1] ** (365 / len(daily)) - 1:.1%}）")
axes[0].set_yscale("log")
axes[0].set_yticks([1, 10, 100])
axes[0].set_yticklabels(["1", "10", "100"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title("同一条策略，只换标的池")
axes[0].legend(fontsize=8.5)
axes[0].grid(alpha=0.25, which="both")
legs = [close[c].dropna().iloc[-1] / close[c].dropna().iloc[-61] - 1
        for c in close.columns[~alive] if close[c].notna().sum() > 60]
axes[1].hist(np.clip(legs, -1, 2), bins=np.arange(-1, 2.05, 0.1), color=PURPLE, alpha=0.8)
axes[1].axvline(np.median(legs), color="#333333", linewidth=1.4, linestyle="--",
                label=f"中位数 {np.median(legs):.1%}")
axes[1].axvline(0, color=GRAY, linewidth=1.0)
axes[1].set_xlabel("停止交易前 60 天的涨跌幅")
axes[1].set_ylabel("合约数")
axes[1].xaxis.set_major_formatter(percent)
axes[1].set_title(f"{len(legs)} 个停止交易的合约：它们不是安静地消失")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25)
save(fig, "survivorship.png")

# 图 5：重绘
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
for label, column, color in [("在摆动点当天成交（重绘版）", "time", DOWN),
                             ("在摆动点被确认之后成交", "confirmed_at", BLUE)]:
    state = pd.Series(np.nan, index=price.index)
    for _, row in swings.iterrows():
        if row[column] in state.index:
            state[row[column]] = 1.0 if row["kind"] == -1 else 0.0
    equity = (1 + BT.vectorized(price, state.ffill().fillna(0.0), lag=1)).cumprod()
    axes[0].plot(equity.index, equity.to_numpy(), color=color, linewidth=1.5,
                 label=f"{label}（年化 {equity.iloc[-1] ** (365 / len(equity)) - 1:.0%}）")
axes[0].plot(price.index, (price / price.iloc[0]).to_numpy(), color=GRAY, linewidth=1.1,
             linestyle=":", label="买入持有")
axes[0].set_yscale("log")
axes[0].set_yticks([1, 1e2, 1e4, 1e6, 1e8])
axes[0].set_yticklabels(["1", "100", "1万", "100万", "1亿"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].set_ylabel("本金的几倍（对数轴）")
axes[0].set_title("同一个 ZigZag，差的只是「你什么时候知道它」")
axes[0].legend(fontsize=8.5, loc="upper left")
axes[0].grid(alpha=0.25, which="both")
slow = lows.loc[(lows["confirmed_at"] - lows["time"]).idxmax()]      # 确认得最慢的那个低点
window = price.loc[slow["time"] - pd.Timedelta(days=25): slow["confirmed_at"] + pd.Timedelta(days=25)]
axes[1].plot(range(len(window)), window.to_numpy(), color="#333333", linewidth=1.4)
inside = lows[(lows["time"] >= window.index[0]) & (lows["time"] <= window.index[-1])]
for _, row in inside.iterrows():
    a = list(window.index).index(row["time"])
    axes[1].plot([a], [row["price"]], marker="o", color=DOWN, markersize=8)
    if row["confirmed_at"] in window.index:
        b = list(window.index).index(row["confirmed_at"])
        axes[1].plot([b], [window.iloc[b]], marker="^", color=BLUE, markersize=9)
        axes[1].annotate("", xy=(b, window.iloc[b]), xytext=(a, row["price"]),
                         arrowprops=dict(arrowstyle="->", color=GRAY, linewidth=1.2))
        axes[1].text(a + 2, row["price"] * 1.02,
                     f"{(row['confirmed_at'] - row['time']).days} 天之后才确认，"
                     f"那时价格已经高了 {window.iloc[b] / row['price'] - 1:.0%}", fontsize=9)
axes[1].set_ylabel("BTCUSDT（美元）")
axes[1].set_title("圆点＝低点发生，三角＝你真正知道它的那天")
step = max(1, len(window) // 6)
axes[1].set_xticks(range(0, len(window), step))
axes[1].set_xticklabels([str(d.date())[5:] for d in window.index[::step]], fontsize=8)
axes[1].grid(alpha=0.25)
save(fig, "repaint.png")

# 图 6：价差
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
for day, group in book.groupby(book.index.floor("D")):
    axes[0].plot(range(len(group)), group["价差"].to_numpy(), linewidth=0.8,
                 label=str(day.date()))
axes[0].set_yscale("log")
axes[0].set_yticks([0.01, 0.1, 1, 10])
axes[0].set_yticklabels(["0.01", "0.1", "1", "10"])
axes[0].yaxis.set_minor_formatter(plt.NullFormatter())
axes[0].set_xlabel("这一天的第几分钟")
axes[0].set_ylabel("买卖价差（基点，对数轴）")
axes[0].set_title("八天、每分钟的真实价差")
axes[0].legend(fontsize=7, ncol=2)
axes[0].grid(alpha=0.25, which="both")
items = [("中位价差", float(book["价差"].median()), GREEN),
         ("95% 分位", float(book["价差"].quantile(.95)), GREEN),
         ("最宽的一分钟", float(book["价差"].max()), ORANGE),
         ("永续 maker 手续费", C.BINANCE_FEES["永续 maker"] * 1e4, BLUE),
         ("永续 taker 手续费", C.BINANCE_FEES["永续 taker"] * 1e4, BLUE),
         ("现货 taker 手续费", C.BINANCE_FEES["现货 taker"] * 1e4, DOWN)]
positions = np.arange(len(items))
axes[1].barh(positions, [v for _, v, _ in items], color=[c for _, _, c in items], alpha=0.85)
for y, (_, value, _) in zip(positions, items):
    axes[1].text(value * 1.25, y, f"{value:.3g} 基点", va="center", fontsize=9)
axes[1].set_yticks(positions)
axes[1].set_yticklabels([name for name, _, _ in items], fontsize=9)
axes[1].invert_yaxis()
axes[1].set_xscale("log")
axes[1].set_xlim(0.02, 200)
axes[1].set_xticks([0.1, 1, 10, 100])
axes[1].set_xticklabels(["0.1", "1", "10", "100"])
axes[1].xaxis.set_minor_formatter(plt.NullFormatter())
axes[1].set_xlabel("基点（对数轴）")
axes[1].set_title("价差 vs 手续费：差了两个数量级")
axes[1].grid(alpha=0.25, axis="x", which="both")
save(fig, "spread.png")

# 图 7：复权
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
for label, df, color in [("未复权（当时屏幕上的价格）", unadjusted, DOWN),
                         ("只按拆股复权", nasdaq, BLUE), ("拆股 + 分红（全收益）", total_return, GREEN)]:
    c = df["close"]
    entry = ((I.sma(c, 50) > I.sma(c, 200)) & (c >= c.rolling(20).max())).fillna(False)
    exit_ = I.cross_below(I.sma(c, 50), I.sma(c, 200)).fillna(False)
    series, _, _ = R.run(df, R.Rule(entry=entry, exit=exit_, fill="next_open", stop="chandelier",
                                    k=3.0, trigger="close", sizing="risk", risk_per_trade=0.10))
    equity = (1 + series).cumprod()
    axes[0].plot(equity.index, equity.to_numpy(), color=color, linewidth=1.5,
                 label=f"{label}（年化 {equity.iloc[-1] ** (252 / len(series)) - 1:.2%}）")
axes[0].set_ylabel("本金的几倍")
axes[0].set_title("苹果，同一条策略，三种价格序列")
axes[0].legend(fontsize=8.5)
axes[0].grid(alpha=0.25)
window = unadjusted.loc["2020-08-10":"2020-09-15", "close"]
axes[1].plot(range(len(window)), window.to_numpy(), color=DOWN, linewidth=1.6, label="未复权")
split = list(window.index).index(pd.Timestamp("2020-08-31"))
axes[1].axvline(split, color=GRAY, linewidth=1.0, linestyle="--")
axes[1].annotate(f"回测看到「一天跌了 74%」\n实际上股价一分钱没跌", (split + 1, 300), fontsize=9.5)
axes[1].plot(range(len(window)), (nasdaq.loc[window.index, "close"] * 4).to_numpy(),
             color=BLUE, linewidth=1.4, linestyle=":", label="只按拆股复权（还原成拆股前的口径）")
axes[1].set_ylabel("AAPL（美元）")
axes[1].set_title("2020-08-31，苹果四拆一")
step = max(1, len(window) // 6)
axes[1].set_xticks(range(0, len(window), step))
axes[1].set_xticklabels([str(d.date())[5:] for d in window.index[::step]], fontsize=8)
axes[1].legend(fontsize=8.5)
axes[1].grid(alpha=0.25)
save(fig, "adjust.png")
