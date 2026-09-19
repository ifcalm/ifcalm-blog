"""生成第 23 篇的插图：python 23_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 23_risk.py（整段执行，不打印输出）。
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
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(Path(__file__).with_name("23_risk.py").read_text(encoding="utf-8"), ns)
day, one, MARKETS, K = ns["day"], ns["one"], ns["MARKETS"], ns["K"]
entries, deaths, CHANDELIER = ns["entries"], ns["deaths"], ns["CHANDELIER"]
reached, all_trades, distributions, scans = ns["reached"], ns["all_trades"], ns["distributions"], ns["scans"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")


def candles(ax, bars, width=0.35, alpha=1.0):
    for x, (o, h, l, c) in enumerate(bars[["open", "high", "low", "close"]].to_numpy()):
        color = UP if c >= o else DOWN
        ax.vlines(x, l, h, color=color, linewidth=0.9, alpha=alpha)
        ax.add_patch(Rectangle((x - width, min(o, c)), 2 * width, max(abs(c - o), 1e-9),
                               facecolor=color, edgecolor=color, alpha=alpha))


entry, risk = one["买入价"], one["R"]

# 1. 决策点：停在 2020-10-22
window = day.loc["2020-09-25":"2020-10-22"]
fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=150)
candles(ax, window)
n = len(window)
buy = window.index.get_loc(one["买入日"])
ax.axhline(entry, color=BLUE, linewidth=1.3, label=f"进场 {entry:,.0f}")
ax.axhline(entry - risk, color=DOWN, linewidth=1.3, linestyle="--", label=f"初始止损 {entry - risk:,.0f}（-1R）")
for x in [1, 2]:
    ax.axhline(entry + x * risk, color=GRAY, linewidth=1.0, linestyle=":")
    ax.text(0.6, entry + x * risk, f"+{x}R", va="bottom", fontsize=9, color=GRAY)
ax.annotate("买入", xy=(buy, window["low"].iloc[buy]), xytext=(buy - 3.2, entry - 0.8 * risk),
            fontsize=10, color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE))
ax.annotate(f"今天收盘 {window['close'].iloc[-1]:,.0f}\n浮盈 +2.08R", xy=(n - 1.6, window["close"].iloc[-1]),
            xytext=(n - 13, entry + 1.35 * risk), fontsize=11,
            arrowprops=dict(arrowstyle="->", color="black"))
ax.set_xticks(range(0, n, 4))
ax.set_xticklabels([str(d.date())[5:] for d in window.index[::4]])
ax.set_ylabel("BTCUSDT 现货（美元）")
ax.set_title("2020-10-22 收盘：仓位浮盈 2R，拿住、平一半，还是全部离场？")
ax.legend(loc="upper left", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 揭晓：一直到 2021-01-12
window = day.loc["2020-09-25":"2021-01-20"]
trail = []
highest, stop = entry, entry - risk
from talab import indicators as I
atr = I.atr(day["high"], day["low"], day["close"])
for ts, bar in window.iterrows():
    if ts < one["买入日"]:
        trail.append(np.nan); continue
    stop = max(stop, highest - 3 * atr.shift(1)[ts])
    trail.append(stop if ts <= one["卖出日"] else np.nan)
    highest = max(highest, bar["high"])
fig, ax = plt.subplots(figsize=(11.5, 6.0), dpi=150)
n = len(window)
ax.plot(range(n), window["close"].to_numpy(), color="#333333", linewidth=1.2, label="收盘价")
ax.plot(range(n), trail, color=DOWN, linewidth=1.4, linestyle="--", label="3 ATR 吊灯止损（只上移）")
ax.axhline(entry, color=BLUE, linewidth=1.0)
right = ax.twinx()
right.set_ylim(((np.array(ax.get_ylim()) - entry) / risk))
right.set_ylabel("浮盈（R 倍数）")
mark = window.index.get_loc(pd.Timestamp("2020-10-22", tz="UTC"))
sell = window.index.get_loc(one["卖出日"])
top = window["high"].idxmax()
ax.scatter([mark], [window["close"].iloc[mark]], color="black", zorder=5, s=36)
ax.annotate("决策点 +2.08R", xy=(mark, window["close"].iloc[mark]), xytext=(mark - 2, entry * 2.1),
            fontsize=10, arrowprops=dict(arrowstyle="->", color="black"))
ax.scatter([sell], [one["卖出价"]], color=DOWN, zorder=5, s=44)
ax.annotate(f"止损出场 {one['卖出价']:,.0f}\n+24.89R", xy=(sell, one["卖出价"]),
            xytext=(sell - 24, one["卖出价"] * 1.05), fontsize=10,
            arrowprops=dict(arrowstyle="->", color=DOWN))
ax.annotate(f"最高 {window['high'].max():,.0f}（+33.4R）", xy=(window.index.get_loc(top), window["high"].max()),
            xytext=(window.index.get_loc(top) - 46, window["high"].max() * 0.93), fontsize=9, color=GRAY,
            arrowprops=dict(arrowstyle="->", color=GRAY))
ax.set_xticks(range(0, n, 10))
ax.set_xticklabels([str(d.date())[5:] for d in window.index[::10]])
ax.set_ylabel("BTCUSDT 现货（美元）")
ax.set_title("同一笔交易，后面还有 82 根 K 线")
ax.legend(loc="upper left", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 3. 浮盈到过 2R 的 205 笔，最后落在哪里
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=150)
ax = axes[0]
bins = np.arange(-1, 12.5, 0.5)
ax.hist(np.clip(reached["拿住"], -1, 12), bins=bins, color=BLUE, alpha=0.85)
ax.axvline(2, color=DOWN, linewidth=1.4, linestyle="--", label="决策点 +2R")
ax.axvline(reached["拿住"].mean(), color=ORANGE, linewidth=1.4, label=f"平均 {reached['拿住'].mean():.2f}R")
ax.axvline(reached["拿住"].median(), color=GREEN, linewidth=1.4, label=f"中位数 {reached['拿住'].median():.2f}R")
ax.set_xlabel("拿住的最终 R 倍数（12R 以上并入最右边一格）")
ax.set_ylabel("交易笔数")
ax.set_title(f"到过 +2R 的 {len(reached)} 笔，后来怎么收场")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax = axes[1]
for label, color in [("全部离场", GRAY), ("平一半", GREEN), ("拿住", BLUE)]:
    values = np.sort(reached[label])
    ax.plot(values, np.arange(1, len(values) + 1) / len(values), color=color, linewidth=1.6,
            label=f"{label}：平均 {values.mean():.2f}R，标准差 {values.std():.2f}")
ax.set_xlim(0.5, 9)
ax.set_xlabel("最终 R 倍数")
ax.set_ylabel("累计比例")
ax.yaxis.set_major_formatter(percent)
ax.set_title("三种做法的分布")
ax.legend(fontsize=9, loc="lower right"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "twor.png"); plt.close(fig)

# 4. 四种出场方式的 R 分布
fig, axes = plt.subplots(1, 4, figsize=(12.5, 4.2), dpi=150, sharey=True)
bins = np.arange(-2, 8.25, 0.5)
for ax, (label, series) in zip(axes, distributions.items()):
    r = pd.concat(series, ignore_index=True)
    ax.hist(np.clip(r, -2, 8), bins=bins, color=BLUE, alpha=0.85)
    score = K.expectancy(r)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.axvline(score["期望值"], color=ORANGE, linewidth=1.4)
    ax.set_title(f"{label}\n胜率 {score['胜率']:.0%} · 盈亏比 {score['盈亏比']:.1f}\n"
                 f"平均 {score['期望值']:.2f}R · 中位数 {score['中位数']:.2f}R", fontsize=9.5)
    ax.set_xlabel("R 倍数（8R 以上并入最右边一格）")
    ax.grid(alpha=0.25)
axes[0].set_ylabel("交易笔数（五个序列合计）")
fig.tight_layout(); fig.savefig(out / "styles.png"); plt.close(fig)

# 5. 胜率和盈亏比：打平那条曲线
fig, ax = plt.subplots(figsize=(8.2, 5.6), dpi=150)
ratio = np.linspace(0.3, 12, 300)
ax.plot(ratio, 1 / (1 + ratio), color="black", linewidth=1.5, label="打平线：胜率 = 1 ÷ (1 + 盈亏比)")
ax.fill_between(ratio, 1 / (1 + ratio), 1, color=GREEN, alpha=0.08)
ax.fill_between(ratio, 0, 1 / (1 + ratio), color=DOWN, alpha=0.08)
markers = {"SPY 日线": "o", "AAPL 日线": "s", "BTC 日线": "^", "BTC 4 小时": "D", "BTC 1 小时": "v"}
colors = {"A 结构止损，不动": PURPLE, "B 3 ATR 止损，不动": ORANGE,
          "C 3 ATR 吊灯跟踪": BLUE, "D 时间止损：拿满 20 根": GREEN}
for label, series in distributions.items():
    for (name, _), r in zip(MARKETS.items(), series):
        score = K.expectancy(r)
        ax.scatter(score["盈亏比"], score["胜率"], marker=markers[name], color=colors[label], s=52, alpha=0.9)
for label, color in colors.items():
    ax.scatter([], [], color=color, s=52, label=label)
for name, marker in markers.items():
    ax.scatter([], [], color=GRAY, marker=marker, s=52, label=name)
ax.set_xscale("log")
ax.set_xticks([0.5, 1, 2, 3, 5, 10])
ax.set_xticklabels(["0.5", "1", "2", "3", "5", "10"])
ax.set_xlabel("盈亏比（平均盈利 ÷ 平均亏损）")
ax.set_ylabel("胜率")
ax.yaxis.set_major_formatter(percent)
ax.set_title("四种出场方式 × 五个序列：都在打平线上方，位置各不相同")
ax.legend(fontsize=8, ncol=2, loc="upper right")
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "tradeoff.png"); plt.close(fig)

# 6. 目标价扫描
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
targets = [float(t[:-1]) for t in scans["BTC 4 小时"]["目标"]]
ax = axes[0]
for name, color in [("BTC 4 小时", BLUE), ("BTC 1 小时", ORANGE), ("SPY 日线", GREEN)]:
    table = scans[name]
    ax.plot(targets, table["胜率"], color=color, marker="o", markersize=4, linewidth=1.6, label=f"{name}：实测")
    ax.plot(targets, table["打乱后的胜率"], color=color, linestyle="--", linewidth=1.2, alpha=0.8,
            label=f"{name}：打乱后")
ax.plot(targets, scans["BTC 4 小时"]["打平需要的胜率"], color="black", linewidth=1.4, linestyle=":",
        label="打平需要的胜率（BTC 4 小时）")
ax.set_xlabel("止盈目标（R 倍数）")
ax.set_ylabel("胜率")
ax.yaxis.set_major_formatter(percent)
ax.set_title("目标越远，胜率越低——打乱之后一模一样")
ax.legend(fontsize=8); ax.grid(alpha=0.25)
ax = axes[1]
table = scans["BTC 1 小时"]
width = 0.38
x = np.arange(len(targets))
ax.bar(x - width / 2, table["合计 R"], width, color=BLUE, label="不扣成本")
ax.bar(x + width / 2, table["扣成本后合计 R"], width, color=ORANGE, label="扣掉一来一回 0.1%")
for k, trades in enumerate(table["交易数"]):
    ax.text(k - width / 2, 4, f"{trades} 笔", ha="center", va="bottom", fontsize=8,
            color="white", rotation=90)
ax.set_xticks(x)
ax.set_xticklabels(table["目标"])
ax.set_xlabel("止盈目标")
ax.set_ylabel("九年合计 R")
ax.set_title("BTC 1 小时：小目标的合计 R 被成本吃掉大半")
ax.legend(fontsize=9); ax.grid(alpha=0.25, axis="y")
fig.tight_layout(); fig.savefig(out / "targets.png"); plt.close(fig)

# 7. 最大浮亏和最大浮盈
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
winners = all_trades[all_trades["R 倍数"] > 0]
losers = all_trades[all_trades["R 倍数"] <= 0]
ax = axes[0]
ax.scatter(np.clip(losers["最大浮亏"], -2.2, 0), np.clip(losers["最大浮盈"], 0, 8),
           s=9, alpha=0.35, color=DOWN, label=f"亏钱的 {len(losers)} 笔")
ax.scatter(np.clip(winners["最大浮亏"], -2.2, 0), np.clip(winners["最大浮盈"], 0, 8),
           s=9, alpha=0.5, color=UP, label=f"赚钱的 {len(winners)} 笔")
ax.axvline(-1, color="black", linewidth=1.0, linestyle="--")
ax.text(-1.03, 7.5, "初始止损 -1R", ha="right", fontsize=9)
ax.axhline(2, color=GRAY, linewidth=1.0, linestyle=":")
ax.text(-2.15, 2.12, "浮盈 +2R", fontsize=9, color=GRAY)
ax.set_xlabel("最大浮亏 MAE（R，-2.2 以下并入最左边）")
ax.set_ylabel("最大浮盈 MFE（R）")
ax.set_title("每笔交易走过的最好和最坏时刻")
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)
ax = axes[1]
grid = np.linspace(0.05, 1.5, 60)
ax.plot(grid, [np.mean(winners["最大浮亏"] <= -q) for q in grid], color=UP, linewidth=1.8, label="赚钱的交易")
ax.plot(grid, [np.mean(losers["最大浮亏"] <= -q) for q in grid], color=DOWN, linewidth=1.8, label="亏钱的交易")
for q in [0.3, 0.5, 0.7]:
    ax.axvline(q, color=GRAY, linewidth=0.8, linestyle=":")
    ax.text(q, 0.02, f"{np.mean(winners['最大浮亏'] <= -q):.0%}", fontsize=8, color=UP, ha="center")
ax.set_xlabel("把止损收紧到当初距离的多少（R）")
ax.set_ylabel("会先被打掉的比例")
ax.yaxis.set_major_formatter(percent)
ax.set_title("收紧止损，先打掉的是谁")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "excursion.png"); plt.close(fig)
print("图已写入", out)
