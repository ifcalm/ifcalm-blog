"""生成第 26 篇的插图：python 26_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 26_sizing.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("26_sizing.py").read_text(encoding="utf-8"), ns)
Z, I, K, R = ns["Z"], ns["I"], ns["K"], ns["R"]
btc, one, distance, EQUITY = ns["btc"], ns["one"], ns["distance"], ns["EQUITY"]
TRADES, MARKETS, budget, vol_table = ns["TRADES"], ns["MARKETS"], ns["budget"], ns["vol_table"]
sector, market, SECTORS, crypto = ns["sector"], ns["market"], ns["SECTORS"], ns["crypto"]
daily, open_days, rng = ns["daily"], ns["open_days"], ns["rng"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")
BUYS = [("A 满仓", EQUITY, "#333333"), ("B 固定金额 1 万", 10_000.0, ORANGE),
        ("C 固定风险 1%", EQUITY * 0.01 / distance, BLUE), ("D 固定风险 10%", min(EQUITY, EQUITY * 0.10 / distance), GREEN)]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(out / name, bbox_inches="tight")
    plt.close(fig)
    print("写出", out / name)


# 图 1：决策点——同一笔交易，四种买法
window = btc.loc["2020-08-26":"2020-10-10"]   # ⚠️ 停在决策点当天，后面的走势不画
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
axes[0].plot(range(len(window)), window["close"].to_numpy(), color="#333333", linewidth=1.4)
mark = list(window.index).index(one["买入日"])
axes[0].axvline(mark, color="black", linewidth=1.0, linestyle="--")
axes[0].axhline(one["买入价"], color=BLUE, linewidth=1.2, label=f"买入 {one['买入价']:,.0f}")
axes[0].axhline(one["初始止损"], color=DOWN, linewidth=1.2, linestyle=":",
                label=f"初始止损 {one['初始止损']:,.0f}（-{distance:.2%}）")
axes[0].set_title("2020-10-10：主线策略在 BTC 上发出买入信号")
axes[0].set_ylabel("BTCUSDT（美元）")
axes[0].legend(fontsize=9, loc="upper left")
axes[0].grid(alpha=0.25)
step = max(1, len(window) // 8)
axes[0].set_xticks(range(0, len(window), step))
axes[0].set_xticklabels([str(d.date())[5:] for d in window.index[::step]], fontsize=8)
labels = [name for name, _, _ in BUYS]
positions = np.arange(len(BUYS))
axes[1].barh(positions, [notional / EQUITY for _, notional, _ in BUYS],
             color=[color for _, _, color in BUYS], alpha=0.85)
for y, (name, notional, _) in zip(positions, BUYS):
    axes[1].text(notional / EQUITY + 0.02, y, f"买 {notional:,.0f} 美元，被止损亏 {notional * distance:,.0f}",
                 va="center", fontsize=8.5)
axes[1].set_yticks(positions)
axes[1].set_yticklabels(labels, fontsize=9)
axes[1].invert_yaxis()
axes[1].set_xlim(0, 1.65)
axes[1].xaxis.set_major_formatter(percent)
axes[1].set_xlabel("买入金额占账户")
axes[1].set_title("账户 10 万美元，该买多少？")
axes[1].grid(alpha=0.25, axis="x")
save(fig, "decision.png")

# 图 2：揭晓——同一笔交易走完，四条账户曲线
held = btc.loc[one["买入日"]:one["卖出日"]]
atr = I.atr(btc["high"], btc["low"], btc["close"], 14).reindex(held.index)
chandelier = (held["high"].cummax() - 3 * atr.shift(1)).cummax().clip(lower=one["初始止损"])
fig, axes = plt.subplots(2, 1, figsize=(11.5, 6.4), dpi=150, sharex=True, gridspec_kw={"height_ratios": [3, 2]})
axes[0].plot(range(len(held)), held["close"].to_numpy(), color="#333333", linewidth=1.4, label="收盘价")
axes[0].plot(range(len(held)), chandelier.to_numpy(), color=DOWN, linewidth=1.1, linestyle="--", label="3 ATR 吊灯止损")
axes[0].set_ylabel("BTCUSDT（美元）")
axes[0].set_title(f"2020-10-10 → 2021-01-12：{one['R 倍数']:.2f}R")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.25)
for name, notional, color in BUYS:
    path = EQUITY + notional * (held["close"] / one["买入价"] - 1)
    dashed = name.startswith("D")                       # D 和 A 在这一笔上完全重合，画成虚线才看得见
    axes[1].plot(range(len(held)), path.to_numpy() / 1e4, color=color, linewidth=1.4,
                 linestyle="--" if dashed else "-", label=name + ("（和 A 重合）" if dashed else ""))
axes[1].axhline(EQUITY / 1e4, color=GRAY, linewidth=1.0, linestyle=":")
axes[1].set_ylabel("账户（万美元）")
axes[1].legend(fontsize=8.5, ncol=2)
axes[1].grid(alpha=0.25)
step = max(1, len(held) // 9)
axes[1].set_xticks(range(0, len(held), step))
axes[1].set_xticklabels([str(d.date()) for d in held.index[::step]], fontsize=8)
save(fig, "reveal.png")

# 图 3：同一串交易（BTC 30 笔），四种仓位方法的资金曲线
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=150)
paths = {"满仓": dict(method="full"), "固定金额 1 万": dict(method="amount", amount=10_000.0),
         "固定风险 1%": dict(method="risk", risk=0.01), "固定风险 10%": dict(method="risk", risk=0.10)}
colors = {"满仓": "#333333", "固定金额 1 万": ORANGE, "固定风险 1%": BLUE, "固定风险 10%": GREEN}
for label, kwargs in paths.items():
    path = Z.simulate(TRADES["BTC"], equity=EQUITY, **kwargs)
    axes[0].plot(range(len(path) + 1), np.r_[EQUITY, path["账户"].to_numpy()] / 1e4, color=colors[label],
                 linewidth=1.5, marker="o", markersize=2.5, label=label)
    axes[1].plot(range(1, len(path) + 1), (path["占账户"] * path["止损距离"]).to_numpy(), color=colors[label],
                 linewidth=1.2, marker="o", markersize=2.5, label=label)
axes[0].set_yscale("log")
axes[0].set_yticks([10, 20, 50, 100])
axes[0].set_yticklabels(["10", "20", "50", "100"])
axes[0].set_xlabel("第几笔交易")
axes[0].set_ylabel("账户（万美元，对数轴）")
axes[0].set_title("BTC 上的 30 笔交易，四种仓位方法")
axes[0].legend(fontsize=8.5)
axes[0].grid(alpha=0.25, which="both")
axes[1].set_xlabel("第几笔交易")
axes[1].set_ylabel("被止损时会亏掉账户的")
axes[1].set_title("仓位方法决定的是这张图：进场那一刻就知道的数")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_ylim(0, 0.30)
axes[1].legend(fontsize=8.5)
axes[1].grid(alpha=0.25)
save(fig, "methods.png")

# 图 4：风险预算怎么调
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150, sharex=True)
for ax, name in zip(axes, MARKETS):
    rows = budget[(budget["标的"] == name) & (budget["风险预算"] != "满仓")].copy()
    x = [float(s.split()[-1].rstrip("%")) / 100 for s in rows["风险预算"]]
    ax.plot(x, rows["年化"].to_numpy(), color=GREEN, marker="o", markersize=4, linewidth=1.6, label="年化")
    ax.plot(x, -rows["最大回撤"].to_numpy(), color=DOWN, marker="s", markersize=4, linewidth=1.6, label="最大回撤（取正）")
    full = budget[(budget["标的"] == name) & (budget["风险预算"] == "满仓")].iloc[0]
    ax.axhline(full["年化"], color=GREEN, linewidth=1.0, linestyle=":")
    ax.axhline(-full["最大回撤"], color=DOWN, linewidth=1.0, linestyle=":")
    ax.set_xscale("log")
    ax.set_xticks([0.0025, 0.01, 0.05, 0.20])
    ax.set_xticklabels(["0.25%", "1%", "5%", "20%"])
    ax.set_xlabel("每笔风险预算")
    ax.set_title(f"{name}（虚线＝满仓）")
    ax.yaxis.set_major_formatter(percent)
    ax.grid(alpha=0.25)
axes[0].set_ylabel("年化 / 最大回撤")
axes[0].legend(fontsize=8.5)
save(fig, "budget.png")

# 图 5：凯利曲线和它的误差
GRID = np.arange(0.005, 0.80, 0.005)
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=150)
for name, color in zip(MARKETS, [BLUE, ORANGE, PURPLE]):
    r = TRADES[name]["R 倍数"].to_numpy()
    curve = [Z.growth_rate(r, f) for f in GRID]
    best = Z.optimal_f(r, GRID)
    axes[0].plot(GRID, curve, color=color, linewidth=1.6, label=f"{name}（f* = {best:.2f}）")
    axes[0].plot([best], [Z.growth_rate(r, best)], marker="o", color=color, markersize=5)
    axes[0].plot([best / 2], [Z.growth_rate(r, best / 2)], marker="s", color=color, markersize=5)
axes[0].axhline(0, color=GRAY, linewidth=1.0)
axes[0].set_xlabel("每笔下注的风险占账户的比例 f")
axes[0].set_ylabel("每笔的对数增长率")
axes[0].set_title("圆点＝全凯利，方块＝半凯利")
axes[0].set_ylim(-0.12, 0.12)
axes[0].legend(fontsize=8.5)
axes[0].grid(alpha=0.25)
r = TRADES["BTC"]["R 倍数"].to_numpy()
boots = np.array([Z.optimal_f(rng.choice(r, len(r), replace=True), GRID) for _ in range(2_000)])
axes[1].hist(boots, bins=np.arange(0, 0.82, 0.02), color=PURPLE, alpha=0.75)
axes[1].axvline(Z.optimal_f(r, GRID), color="black", linewidth=1.4, linestyle="--",
                label=f"全样本 f* = {Z.optimal_f(r, GRID):.2f}")
axes[1].axvline(np.quantile(boots, .05), color=GRAY, linewidth=1.0, linestyle=":")
axes[1].axvline(np.quantile(boots, .95), color=GRAY, linewidth=1.0, linestyle=":",
                label=f"90% 区间 [{np.quantile(boots, .05):.2f}, {np.quantile(boots, .95):.2f}]")
axes[1].set_xlabel("把这 30 笔重抽一遍，算出来的 f*")
axes[1].set_ylabel("次数")
axes[1].set_title("BTC：同样 30 笔交易，重抽 2000 次的最优下注比例")
axes[1].legend(fontsize=8.5)
axes[1].grid(alpha=0.25)
save(fig, "kelly.png")

# 图 6：回撤要爬多久
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
losses = np.arange(0.01, 0.90, 0.01)
axes[0].plot(losses, Z.recovery(losses), color=DOWN, linewidth=1.8)
axes[0].plot(losses, losses, color=GRAY, linewidth=1.2, linestyle=":", label="如果是对称的")
for level in [0.2, 0.5, 0.83]:
    axes[0].plot([level], [Z.recovery(level)], marker="o", color="black", markersize=5)
    axes[0].annotate(f"亏 {level:.0%} 要涨 {Z.recovery(level):.0%}", (level, Z.recovery(level)),
                     textcoords="offset points", xytext=(-105, 6), fontsize=8.5)
axes[0].set_xlabel("回撤")
axes[0].set_ylabel("回本需要的涨幅")
axes[0].set_title("亏损和收益不对称")
axes[0].xaxis.set_major_formatter(percent)
axes[0].yaxis.set_major_formatter(percent)
axes[0].set_ylim(0, 5.2)
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.25)
for name, color in zip(MARKETS, [BLUE, ORANGE, PURPLE]):
    series = Z.drawdown(MARKETS[name][0]["close"])
    index = series.index.tz_localize(None) if series.index.tz is not None else series.index
    axes[1].plot(index, series.to_numpy(), color=color, linewidth=1.1, label=f"{name} 买入持有")
axes[1].fill_between(pd.to_datetime(["2017-12-17", "2020-11-24"]), -0.9, 0, color=PURPLE, alpha=0.10)
axes[1].annotate("BTC：1073 天在水下，最深 -83%", (pd.Timestamp("2021-01-15"), -0.80), fontsize=8.5)
axes[1].set_ylabel("距离历史最高点")
axes[1].set_title("水下曲线：绝大多数日子你都在回撤里")
axes[1].yaxis.set_major_formatter(percent)
axes[1].legend(fontsize=8.5, loc="lower left")
axes[1].grid(alpha=0.25)
save(fig, "recovery.png")

# 图 7：分散到底分散了没有
fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.6), dpi=150)
groups = [("11 个行业 ETF", sector, PURPLE), ("10 个成交额最大的币", crypto, ORANGE),
          ("主线策略的三个标的", daily.loc[open_days], BLUE)]
names, values, totals = [], [], []
for label, table, color in groups:
    corr = table.corr().to_numpy()
    names.append(label)
    values.append(Z.effective_bets(np.ones(len(corr)) / len(corr), corr))
    totals.append(len(corr))
positions = np.arange(len(names))
axes[0].barh(positions, totals, color=GRAY, alpha=0.35, label="你持有的个数")
axes[0].barh(positions, values, color=[c for _, _, c in groups], height=0.55, label="有效独立仓位数")
for y, (value, total) in enumerate(zip(values, totals)):
    axes[0].text(value + 0.15, y, f"{value:.2f} / {total}", va="center", fontsize=9)
axes[0].set_yticks(positions)
axes[0].set_yticklabels(names, fontsize=9)
axes[0].invert_yaxis()
axes[0].set_xlim(0, 13)
axes[0].set_xlabel("个数")
axes[0].set_title("等权持有时，实际上相当于几个独立的东西")
axes[0].legend(fontsize=8.5, loc="lower right")
axes[0].grid(alpha=0.25, axis="x")


def average_corr(table):
    corr = np.corrcoef(np.asarray(table, dtype=float).T)
    return float(corr[np.triu_indices(len(corr), 1)].mean())


n_down, n_up = int((market < -0.02).sum()), int((market > 0.02).sum())
n_big = int(len(sector) * 0.1)
chol = np.linalg.cholesky(sector.corr().to_numpy())
fake_rows = []
for _ in range(50):
    fake = pd.DataFrame(rng.standard_normal((len(sector), len(SECTORS))) @ chol.T, columns=SECTORS)
    index = fake.mean(axis=1)
    fake_rows.append([average_corr(fake), average_corr(fake.loc[index.nsmallest(n_down).index]),
                      average_corr(fake.loc[index.nlargest(n_up).index]),
                      average_corr(fake.loc[index.abs().nlargest(n_big).index])])
real = [average_corr(sector), average_corr(sector[(market < -0.02).fillna(False)]),
        average_corr(sector[(market > 0.02).fillna(False)]),
        average_corr(sector[(market.abs() >= market.abs().quantile(.9)).fillna(False)])]
labels = ["全部日子", f"跌超 2%\n（{n_down} 天）", f"涨超 2%\n（{n_up} 天）", f"|涨跌| 最大 10%\n（{n_big} 天）"]
positions = np.arange(len(labels))
axes[1].bar(positions - 0.2, real, width=0.4, color=DOWN, label="真实数据")
axes[1].bar(positions + 0.2, np.mean(fake_rows, axis=0), width=0.4, color=GRAY, alpha=0.7,
            label="对照：相关矩阵恒定不变的模拟世界")
axes[1].set_xticks(positions)
axes[1].set_xticklabels(labels, fontsize=8.5)
axes[1].set_ylabel("11 个行业 ETF 的平均两两相关")
axes[1].set_title("「危机时相关性上升」有多少是挑出来的")
axes[1].legend(fontsize=8.5, loc="upper left")
axes[1].grid(alpha=0.25, axis="y")
save(fig, "correlation.png")
