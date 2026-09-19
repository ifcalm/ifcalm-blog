"""生成第 24 篇的插图：python 24_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 24_leverage.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("24_leverage.py").read_text(encoding="utf-8"), ns)
last, mark, K, brackets = ns["last"], ns["mark"], ns["K"], ns["brackets"]
entry, now, liq = ns["entry"], ns["now"], ns["liq"]
crypto, stocks, gme, gme_short = ns["crypto"], ns["stocks"], ns["gme"], ns["gme_short"]
short_interest, raw, funding = ns["short_interest"], ns["raw"], ns["funding"]
MARKETS, hour, mark_hour = ns["MARKETS"], ns["hour"], ns["mark_hour"]
um_day, mark_day = ns["um_day"], ns["mark_day"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")


def candles(ax, bars, width=0.35):
    for x, (o, h, l, c) in enumerate(bars[["open", "high", "low", "close"]].to_numpy()):
        color = UP if c >= o else DOWN
        ax.vlines(x, l, h, color=color, linewidth=0.9)
        ax.add_patch(Rectangle((x - width, min(o, c)), 2 * width, max(abs(c - o), 1e-9),
                               facecolor=color, edgecolor=color))


# 1. 决策点：停在 12:55
window = last.loc["2021-02-08 11:30":"2021-02-08 12:55"]
fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=150)
candles(ax, window)
n = len(window)
ax.axhline(entry, color=BLUE, linewidth=1.3, label=f"做空进场 {entry:,.0f}")
ax.axhline(liq, color=DOWN, linewidth=1.5, linestyle="--", label=f"10 倍空单的强平价 {liq:,.0f}")
ax.axhline(entry * 1.10, color=GRAY, linewidth=1.0, linestyle=":",
           label=f"「反向 10% 就爆仓」的说法 {entry * 1.1:,.0f}")
ax.annotate(f"现在 {window['close'].iloc[-1]:,.0f}\n浮亏 7.94%\n1 万保证金只剩 2,059",
            xy=(n - 1.5, window["close"].iloc[-1]), xytext=(n - 26, entry * 1.055), fontsize=10.5,
            arrowprops=dict(arrowstyle="->", color="black"))
ax.set_ylim(top=entry * 1.118)
ax.set_xticks(range(0, n, 10))
ax.set_xticklabels([str(t)[11:16] for t in window.index[::10]])
ax.set_xlabel("2021-02-08 UTC")
ax.set_ylabel("BTCUSDT 永续合约（美元）")
ax.set_title("10 倍杠杆做空，价格朝不利方向走了 7.9%：离强平价还有多远？")
ax.legend(loc="upper left", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 揭晓：强平之后价格还回来了
window = last.loc["2021-02-08 12:30":"2021-02-08 14:00"]
marks = mark.loc[window.index[0]:window.index[-1]]
fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=150)
n = len(window)
ax.plot(range(n), window["close"].to_numpy(), color="#333333", linewidth=1.2, label="最新成交价")
ax.plot(range(n), marks["close"].reindex(window.index).to_numpy(), color=PURPLE, linewidth=1.2,
        alpha=0.85, label="标记价格（强平看这个）")
ax.axhline(entry, color=BLUE, linewidth=1.1, label=f"进场 {entry:,.0f}")
ax.axhline(liq, color=DOWN, linewidth=1.5, linestyle="--", label=f"强平价 {liq:,.0f}")
for stamp, text, color, offset in [("2021-02-08 12:55", "决策点", "black", (-17, 0.978)),
                                   ("2021-02-08 12:58", "标记价格越过强平价，仓位被平掉", DOWN, (-25, 1.016)),
                                   ("2021-02-08 13:10", "12 分钟后价格回到决策点的水平", GREEN, (2, 0.955))]:
    k = window.index.get_loc(pd.Timestamp(stamp, tz="UTC"))
    ax.scatter([k], [window["close"].iloc[k]], color=color, s=40, zorder=5)
    ax.annotate(text, xy=(k, window["close"].iloc[k]),
                xytext=(k + offset[0], window["close"].iloc[k] * offset[1]),
                fontsize=9.5, color=color, arrowprops=dict(arrowstyle="->", color=color))
ax.set_xticks(range(0, n, 10))
ax.set_xticklabels([str(t)[11:16] for t in window.index[::10]])
ax.set_xlabel("2021-02-08 UTC")
ax.set_ylabel("BTCUSDT 永续合约（美元）")
ax.set_title("58 分钟：从开仓到被强平")
ax.legend(loc="lower right", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 3. 做空的不对称
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
ax = axes[0]
forward = (crypto.shift(-60) / crypto - 1).to_numpy().ravel()
forward = -forward[~np.isnan(forward)]
bins = np.linspace(-3, 1.2, 90)
ax.hist(np.clip(forward, -3, 1.2), bins=bins, color=BLUE, alpha=0.85)
ax.axvline(1, color=DOWN, linewidth=1.6, linestyle="--")
ax.text(0.95, 1.6e3, "+100% 这堵墙\n（价格跌到 0）", ha="right", fontsize=9.5, color=DOWN)
ax.axvline(np.median(forward), color=ORANGE, linewidth=1.4, label=f"中位数 {np.median(forward):+.1%}")
ax.axvline(forward.mean(), color=GREEN, linewidth=1.4, label=f"平均 {forward.mean():+.1%}")
ax.set_yscale("log")
ax.set_xlabel("做空 60 天的收益（-3 以下并入最左边）")
ax.set_ylabel("样本数（对数刻度）")
ax.set_title(f"864 个永续合约、{len(forward):,} 个样本\n右边有墙，左边没有")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax = axes[1]
for name, table, color in [("加密永续（864 个合约）", crypto, ORANGE), ("美股（市值前 100）", stocks, BLUE)]:
    for days, style in [(20, ":"), (60, "--"), (250, "-")]:
        loss = -(table.shift(-days) / table - 1).to_numpy().ravel()
        loss = loss[~np.isnan(loss)]
        grid = np.linspace(0.2, 3.0, 60)
        ax.plot(grid, [(loss < -g).mean() for g in grid], color=color, linestyle=style, linewidth=1.5,
                label=f"{name} · {days} 天")
ax.axvline(1, color=DOWN, linewidth=1.6)
ax.text(1.04, 0.3, "做多最多亏到这里\n（本金的 100%）", fontsize=9.5, color=DOWN)
ax.set_yscale("log")
ax.set_yticks([1, 1e-1, 1e-2, 1e-3, 1e-4, 1e-5])
ax.set_yticklabels(["100%", "10%", "1%", "0.1%", "0.01%", "0.001%"])
ax.set_xlabel("做空一笔亏掉本金的几倍")
ax.set_ylabel("出现的概率（对数刻度）")
ax.set_title("做空亏损超过本金 N 倍的概率")
ax.legend(fontsize=8); ax.grid(alpha=0.25, which="both")
fig.tight_layout(); fig.savefig(out / "asymmetry.png"); plt.close(fig)

# 4. 美股这边
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
ax = axes[0]
top = short_interest.head(15).iloc[::-1]
ax.barh(top["代码"], top["占总股本"], color=BLUE, alpha=0.85)
for y, (value, days) in enumerate(zip(top["占总股本"], top["回补天数"])):
    ax.text(value + 0.0012, y, f"{days:.1f} 天", va="center", fontsize=8, color=GRAY)
ax.axvline(short_interest["占总股本"].median(), color=ORANGE, linewidth=1.4,
           label=f"40 只的中位数 {short_interest['占总股本'].median():.2%}")
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_xlabel("空头仓位占总股本（右边标的是回补天数）")
ax.set_title("市值前 100 里空头仓位最高的 15 只")
ax.legend(fontsize=9); ax.grid(alpha=0.25, axis="x")
ax = axes[1]
liquid = raw[raw["TotalVolume"] > 1e6]["卖空占比"]
ax.hist(liquid, bins=60, color=BLUE, alpha=0.85)
ax.axvline(liquid.median(), color=ORANGE, linewidth=1.6, label=f"中位数 {liquid.median():.1%}")
ax.axvline(0.5, color="black", linewidth=1.0, linestyle=":")
for symbol, color in [("AAPL", GREEN), ("NVDA", PURPLE), ("SPY", DOWN)]:
    value = raw[raw["Symbol"] == symbol]["卖空占比"].median()
    ax.axvline(value, color=color, linewidth=1.3, linestyle="--", label=f"{symbol} {value:.1%}")
ax.xaxis.set_major_formatter(percent)
ax.set_xlabel("当天成交里卖空占的比例（成交超过 100 万股的股票-日）")
ax.set_ylabel("样本数")
ax.set_title("卖空占成交的一半是常态，不是看空信号")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "us_short.png"); plt.close(fig)

# 5. 轧空
window = gme.loc["2020-12-01":"2021-03-01"]
fig, axes = plt.subplots(2, 1, figsize=(11.5, 6.4), dpi=150, sharex=True,
                         gridspec_kw={"height_ratios": [3, 1]})
ax = axes[0]
n = len(window)
ax.plot(range(n), window["close"].to_numpy(), color="#333333", linewidth=1.3, label="收盘价（按拆股调整）")
start = gme.at[pd.Timestamp("2021-01-12"), "close"]
k0 = window.index.get_loc(pd.Timestamp("2021-01-12"))
ax.scatter([k0], [start], color=BLUE, s=44, zorder=5)
ax.annotate(f"这里做空 {start:.2f}", xy=(k0, start), xytext=(k0 - 20, start * 3.0), fontsize=10,
            color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE))
for leverage, color in [(1, GREEN), (2, ORANGE), (3, DOWN)]:
    level = K.liquidation_price(start, leverage, "short")
    ax.axhline(level, color=color, linewidth=1.1, linestyle="--",
               label=f"{leverage} 倍空单的强平价 {level:.2f}")
ax.set_yscale("log")
ax.set_yticks([4, 10, 20, 40, 80])
ax.set_yticklabels(["4", "10", "20", "40", "80"])
ax.set_ylabel("GME（美元，对数刻度）")
ax.set_title("2021 年 1 月：11 个交易日 +1,642%，1 倍空单两天就被强平")
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25)
ax = axes[1]
share = (gme_short["ShortVolume"] / gme_short["TotalVolume"]).reindex(window.index)
ax.bar(range(n), share.to_numpy(), color=PURPLE, alpha=0.8)
ax.axhline(0.5, color="black", linewidth=0.8, linestyle=":")
ax.set_ylim(0, 0.8)
ax.yaxis.set_major_formatter(percent)
ax.set_ylabel("卖空占比")
ax.set_xticks(range(0, n, 10))
ax.set_xticklabels([str(d.date())[5:] for d in window.index[::10]])
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "gme.png"); plt.close(fig)

# 6. 资金费率
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=150)
ax = axes[0]
ax.plot(funding.index, funding.to_numpy() * 100, color=BLUE, linewidth=0.5, alpha=0.7)
ax.axhline(0, color="black", linewidth=0.8)
ax.axhline(0.01, color=GRAY, linewidth=0.9, linestyle=":", label="0.01%＝最常见的那一档")
ax.set_ylabel("每 8 小时的资金费率（%）")
ax.set_title(f"{len(funding):,} 次结算，{(funding > 0).mean():.0%} 的时候是多头付钱")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax = axes[1]
ax.plot(funding.index, funding.cumsum().to_numpy() * 100, color=GREEN, linewidth=1.5)
ax.set_ylabel("做空一直持有，累计收到的资金费（%）")
ax.set_title("2020 年以来累计：空头收到名义价值的 "
             f"{funding.sum():.0%}")
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "funding.png"); plt.close(fig)

# 7. 爆仓概率与波动拖累
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
ax = axes[0]
both = um_day.index.intersection(mark_day.index)
day, judge = um_day.loc[both], mark_day.loc[both]
keep = day.index[:-90]
levers = [2, 3, 5, 10, 20, 25, 50, 100]
for horizon, style in [(7, ":"), (30, "--"), (90, "-")]:
    for side, color, word in [("long", UP, "多"), ("short", DOWN, "空")]:
        rate = [K.replay_liquidation(day, L, side, horizon=horizon, prices=judge).reindex(keep).mean()
                for L in levers]
        ax.plot(levers, rate, color=color, linestyle=style, marker="o", markersize=3,
                label=f"{word}单 · {horizon} 天")
ax.set_xscale("log")
ax.set_xticks(levers); ax.set_xticklabels([f"{L}x" for L in levers])
ax.yaxis.set_major_formatter(percent)
ax.set_xlabel("杠杆")
ax.set_ylabel("被强平的比例")
ax.set_title(f"BTC 日线 {len(keep):,} 个起点：开仓之后被强平的比例")
ax.legend(fontsize=8, ncol=2); ax.grid(alpha=0.25, which="both")
ax = axes[1]
for name, color in [("SPY", GREEN), ("AAPL", BLUE), ("BTC", ORANGE)]:
    df, periods = MARKETS[name]
    ret = df["close"].pct_change().dropna()
    years = len(ret) / periods
    grid = np.linspace(0.25, 4.0, 40)
    values = []
    for L in grid:
        daily = 1 + L * ret
        values.append(daily.prod() ** (1 / years) - 1 if (daily > 0).all() else np.nan)
    ax.plot(grid, values, color=color, linewidth=1.8, label=name)
    plain = (df["close"].iloc[-1] / df["close"].iloc[0]) ** (1 / years) - 1
    ax.plot(grid, plain * grid, color=color, linewidth=0.9, linestyle=":", alpha=0.7)
ax.axvline(1, color="black", linewidth=0.8)
ax.yaxis.set_major_formatter(percent)
ax.set_xlabel("杠杆（每天再平衡）")
ax.set_ylabel("年化收益")
ax.set_title("虚线是「杠杆真能放大收益」，实线是实际\n（BTC 超过 2.5 倍就会有一天亏光）")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "leverage.png"); plt.close(fig)
print("图已写入", out)
