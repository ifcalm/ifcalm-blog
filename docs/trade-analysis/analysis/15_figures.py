"""生成第 15 篇的插图：python 15_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和 mainline_v1 等函数直接借用 15_volatility.py（执行到片段 11 的回测循环之前，不打印输出），避免两份代码不一致。
"""
import contextlib
import io
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
source = Path(__file__).with_name("15_volatility.py").read_text(encoding="utf-8")
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(source.split("check = []")[0], ns)
day, spy, aapl, markets, I, X = ns["day"], ns["spy"], ns["aapl"], ns["markets"], ns["I"], ns["X"]
periods_per_year = ns["periods_per_year"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
money = FuncFormatter(lambda v, _: f"{v:,.0f}")
percent = FuncFormatter(lambda v, _: f"{v:.0%}")


def candles_with_bands(bars, title, marks=()):
    b = I.bollinger(day["close"]).reindex(bars.index)
    width_year_low = I.bollinger(day["close"])["bandwidth"].rolling(365).min().reindex(bars.index)
    fig, (ax, aw) = plt.subplots(2, 1, figsize=(11, 6.6), dpi=150, sharex=True, gridspec_kw={"height_ratios": [2.4, 1.1]})
    xs = np.arange(len(bars))
    for x, (o, h, l, cl) in zip(xs, bars[["open", "high", "low", "close"]].to_numpy()):
        color = UP if cl >= o else DOWN
        ax.vlines(x, l, h, color=color, linewidth=0.8)
        ax.add_patch(Rectangle((x - 0.35, min(o, cl)), 0.7, max(abs(cl - o), 1e-6), facecolor=color, edgecolor=color))
    ax.plot(xs, b["middle"], color=BLUE, linewidth=1.0, label="中轨：20 日 SMA")
    ax.plot(xs, b["upper"], color=PURPLE, linewidth=1.0, label="上轨、下轨：± 2 倍标准差")
    ax.plot(xs, b["lower"], color=PURPLE, linewidth=1.0)
    ax.fill_between(xs, b["lower"], b["upper"], color=PURPLE, alpha=0.06)
    aw.plot(xs, b["bandwidth"], color=PURPLE, linewidth=1.3, label="带宽 = (上轨 - 下轨) ÷ 中轨")
    aw.plot(xs, width_year_low, color=GRAY, linewidth=1.0, linestyle="--", label="过去 365 天的最低带宽")
    where = {t: k for k, t in enumerate(bars.index)}
    for when, text, dx, dy in marks:
        k = where[pd.Timestamp(when, tz="UTC")]
        ax.annotate(text, (k, bars["high"].iloc[k]), textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=9,
                    arrowprops={"arrowstyle": "->", "color": "#555"})
    ticks = [k for k in range(len(bars)) if k == 0 or bars.index[k].month != bars.index[k - 1].month]
    aw.set_xticks(ticks)
    aw.set_xticklabels([bars.index[k].strftime("%Y-%m") for k in ticks], fontsize=8.5)
    ax.yaxis.set_major_formatter(money)
    ax.set_title(title, fontsize=12)
    for axis in (ax, aw):
        axis.grid(alpha=0.25)
    ax.legend(fontsize=8.5, loc="upper left")
    aw.legend(fontsize=8.5, loc="upper left")
    fig.tight_layout()
    return fig, ax


# 1. 决策点
bars = day.loc["2023-05-15":"2023-08-14"]
fig, ax = candles_with_bands(bars, "BTCUSDT 日线，2023-05-15 至 2023-08-14，布林带 (20, 2)",
                             marks=[("2023-08-14", "8 月 14 日\n带宽 0.0254", -40, 40)])
fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 波动率聚集：真实的 NATR 和打乱顺序之后的 NATR
rng = np.random.default_rng(0)
fig, axes = plt.subplots(2, 2, figsize=(12, 5.8), dpi=150, sharey="row")
for row, (name, df) in enumerate([("SPY", spy), ("BTC", day)]):
    shuffled = ns["shuffle_bars"](df, rng)
    for col, (label, data) in enumerate([("真实顺序", df), ("把 K 线顺序随机打乱", shuffled)]):
        n = I.natr(data["high"], data["low"], data["close"])
        axis = axes[row, col]
        axis.plot(n.index, n, color=BLUE if col == 0 else GRAY, linewidth=0.8)
        axis.set_title(f"{name} 日线 NATR(14)：{label}", fontsize=11)
        axis.grid(alpha=0.25)
        axis.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
fig.suptitle("波动率聚集：高低波动成片出现；打乱顺序之后，同样的 K 线只剩下随机的起伏", fontsize=12)
fig.tight_layout(); fig.savefig(out / "clustering.png"); plt.close(fig)

# 3. 揭晓
bars = day.loc["2023-05-15":"2023-10-15"]
fig, ax = candles_with_bands(bars, "揭晓：BTCUSDT 日线，2023-05-15 至 2023-10-15",
                             marks=[("2023-08-14", "8 月 14 日\n决策点", -50, 40), ("2023-08-17", "8 月 17 日\n收盘 26,623", 80, 10)])
fig.savefig(out / "reveal.png"); plt.close(fig)

# 4. 止损被打掉的比例
groups = ["最低 20%", "20-40%", "40-60%", "60-80%", "最高 20%"]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150, sharey=True)
for axis, (name, df) in zip(axes, markets.items()):
    close = df["close"]
    a = I.atr(df["high"], df["low"], close)
    pct = float((3 * a / close).median())
    rank = (a / close).rolling(periods_per_year[name]).rank(pct=True)
    frame = pd.DataFrame({"组": pd.cut(rank, [0, 0.2, 0.4, 0.6, 0.8, 1.0], labels=groups),
                          "fixed": ns["stop_hit"](df, close * pct), "atr": ns["stop_hit"](df, 3 * a)}).dropna()
    table = frame.groupby("组", observed=True).mean()
    xs = np.arange(len(groups))
    axis.bar(xs - 0.2, table["fixed"], 0.4, color=GRAY, label=f"固定 {pct:.2%}")
    axis.bar(xs + 0.2, table["atr"], 0.4, color=BLUE, label="3 ATR")
    axis.set_xticks(xs); axis.set_xticklabels(groups, fontsize=8.5)
    axis.set_title(f"{name} 日线", fontsize=11); axis.grid(alpha=0.25, axis="y"); axis.yaxis.set_major_formatter(percent)
    axis.set_xlabel("现在的 NATR 在过去一年里的排位")
    axis.legend(fontsize=9, loc="upper left")
axes[0].set_ylabel("20 根以内被打掉的比例")
fig.suptitle("两种止损，平均距离相同，按当时的波动率在过去一年里的排位分组", fontsize=12)
fig.tight_layout(); fig.savefig(out / "stops.png"); plt.close(fig)

# 5. 主线策略 v1
fig, axes = plt.subplots(2, 3, figsize=(13, 6.4), dpi=150, sharex="col", gridspec_kw={"height_ratios": [2, 1]})
for col, (name, df) in enumerate(markets.items()):
    signal = ns["mainline_v0"](df)
    start = signal.first_valid_index()
    d = df.loc[start:]
    curves = {"买入持有": d["close"].pct_change().fillna(0.0), "主线 v0": ns["backtest_next_open"](d, signal.loc[start:]),
              "主线 v1（3 ATR 止损）": ns["mainline_v1"](df, k=3.0)[0]}
    for (label, r), color in zip(curves.items(), [GRAY, BLUE, ORANGE]):
        equity = (1 + r).cumprod()
        axes[0, col].plot(equity.index, equity, color=color, linewidth=1.2, label=label)
        axes[1, col].plot(equity.index, equity / equity.cummax() - 1, color=color, linewidth=1.0)
    axes[0, col].set_yscale("log"); axes[0, col].set_title(f"{name}：资金曲线（对数坐标，起点 1）", fontsize=11)
    axes[0, col].set_yticks([0.5, 1, 2, 3, 5, 10])
    axes[0, col].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    axes[0, col].yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    axes[1, col].set_title("回撤", fontsize=10); axes[1, col].yaxis.set_major_formatter(percent)
    for axis in axes[:, col]:
        axis.grid(alpha=0.25)
        axis.xaxis.set_major_locator(matplotlib.dates.YearLocator(2))
        axis.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
axes[0, 0].legend(fontsize=9, loc="upper left")
fig.tight_layout(); fig.savefig(out / "mainline-v1.png"); plt.close(fig)

# 6. 实验二：ADX 的差距如何消失
import talib

high, low, close = day["high"], day["low"], day["close"]
H, L, C = (s.to_numpy(float) for s in (high, low, close))
ours = X.adx(high, low, close)
fig, ax = plt.subplots(figsize=(9, 4.4), dpi=150)
for column, func, color in [("plus_di", talib.PLUS_DI, BLUE), ("adx", talib.ADX, ORANGE)]:
    gap = pd.Series(np.abs(ours[column].to_numpy() - func(H, L, C, 14))).dropna().reset_index(drop=True)
    ax.plot(gap.index, gap.clip(lower=1e-16), color=color, linewidth=1.2, label={"plus_di": "+DI", "adx": "ADX"}[column])
k = np.arange(0, 600)
ax.plot(k, 0.12 * (13 / 14) ** k, color=GRAY, linestyle="--", linewidth=1.0, label="0.12 × (13/14)^根数")
ax.axhline(1e-8, color=DOWN, linewidth=0.8, linestyle=":", label="1e-8")
ax.set_yscale("log"); ax.set_xlim(0, 600); ax.set_ylim(1e-16, 1)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"1e{np.log10(v):.0f}"))
ax.set_xlabel("从第一个值算起的根数"); ax.set_ylabel("|talab - TA-Lib|")
ax.set_title("BTC 日线：talab 和 TA-Lib 的 ADX、+DI，差距每根缩小到 13/14", fontsize=12)
ax.legend(fontsize=9); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "lab-adx.png"); plt.close(fig)

# 7. 实验二：相关性矩阵
exec(source.split("print(\"===== 片段 14：实验二：指标相关性矩阵 =====\")")[1].split("for name, df in")[0], ns)
corr = ns["indicator_panel"](day).corr(method="spearman")
fig, ax = plt.subplots(figsize=(9.5, 8), dpi=150)
image = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=60, ha="right", fontsize=9)
ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.columns, fontsize=9)
for i in range(len(corr)):
    for j in range(len(corr)):
        value = corr.iloc[i, j]
        ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7, color="white" if abs(value) > 0.6 else "black")
fig.colorbar(image, ax=ax, shrink=0.8)
ax.set_title("BTC 日线：14 个指标读数的秩相关系数", fontsize=12)
fig.tight_layout(); fig.savefig(out / "correlation.png"); plt.close(fig)
print("ok")
