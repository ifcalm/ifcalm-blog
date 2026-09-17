"""生成第 6 篇的插图：python 06_figures.py <输出目录>（在 talab 项目根目录运行）。"""
import glob
import math
import sys
from pathlib import Path

import matplotlib
import matplotlib.dates
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from talab import bars as B, data as D, plot as P

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
UP, DOWN, BLUE, ORANGE, GRAY = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888"
thousands = FuncFormatter(lambda v, _: f"{v:,.0f}")

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
A, Bday = "2026-07-01", "2019-07-09"


def draw_candle(ax, x, o, h, l, c, width=0.6):
    color = UP if c >= o else DOWN
    ax.vlines(x, l, h, color=color, linewidth=1.5)
    ax.add_patch(Rectangle((x - width / 2, min(o, c)), width, abs(c - o), facecolor=color, edgecolor=color))


# 1. 两根 K 线
fig, ax = plt.subplots(figsize=(6, 4.5), dpi=150)
for x, t, name in [(0, A, "K 线 A"), (1.5, Bday, "K 线 B")]:
    bar = day.loc[t]
    o, h, l, c = (bar[k] / bar["open"] * 100 for k in ["open", "high", "low", "close"])
    draw_candle(ax, x, o, h, l, c)
    ax.text(x, 98.1, name, ha="center", fontsize=11)
ax.set_xlim(-1, 2.5); ax.set_ylim(97.8, 105.2); ax.set_xticks([])
ax.set_ylabel("开盘价记为 100"); ax.grid(alpha=0.25, axis="y")
ax.set_title("两根 BTC 日线（UTC）")
fig.tight_layout(); fig.savefig(out / "two-candles.png"); plt.close(fig)

# 2. 两根 K 线里面的走势
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), dpi=150, sharey=True)
for ax, t, name in [(axes[0], A, "K 线 A"), (axes[1], Bday, "K 线 B")]:
    m = minute.loc[t]
    path = m["close"].resample("5min").last() / day.loc[t, "open"] * 100
    hours = (path.index - path.index[0]).total_seconds() / 3600
    ax.plot(hours, path.values, color=BLUE, linewidth=1)
    for level, label in [(day.loc[t, "high"], "最高"), (day.loc[t, "low"], "最低"), (day.loc[t, "close"], "收盘")]:
        v = level / day.loc[t, "open"] * 100
        ax.axhline(v, color=GRAY, linestyle=":", linewidth=1)
        ax.text(24.2, v, f"{label} {v:.2f}", va="center", fontsize=8, color="#555")
    ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 4)); ax.set_xlabel("UTC 小时")
    ax.set_title(f"{name}：每 5 分钟的收盘价", fontsize=11); ax.grid(alpha=0.25)
axes[0].set_ylabel("开盘价记为 100")
fig.tight_layout(); fig.savefig(out / "two-paths.png"); plt.close(fig)

# 3. 揭晓
for t, fname, lo, hi in [(A, "reveal-a.png", "2026-06-11", "2026-07-11"), (Bday, "reveal-b.png", "2019-06-19", "2019-07-19")]:
    x = day.loc[lo:hi]
    name = "A" if t == A else "B"
    fig, ax, av = P.plot_candles(x, title=f"K 线 {name} 是 {t}：前后各 10 天", marks=[(t, x.loc[t, "low"], f"K 线 {name}")])
    ylo, yhi = ax.get_ylim(); ax.set_ylim(ylo - (yhi - ylo) * 0.15, yhi)
    fig.savefig(out / fname); plt.close(fig)

# 4. 隔夜和日内
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), dpi=150)
for ax, (k, df) in zip(axes, {"SPY": spy, "AAPL": aapl}.items()):
    overnight = (df["open"] / df["close"].shift()).fillna(1).cumprod()
    intraday = (df["close"] / df["open"]).cumprod()
    ax.plot(df.index, overnight, color=BLUE, linewidth=1.2, label="只持有隔夜（收盘买、次日开盘卖）")
    ax.plot(df.index, intraday, color=ORANGE, linewidth=1.2, label="只持有日内（开盘买、当天收盘卖）")
    ax.set_title(f"{k}：1 美元的累计增长", fontsize=11); ax.grid(alpha=0.25); ax.legend(fontsize=8, loc="upper left")
fig.tight_layout(); fig.savefig(out / "overnight-intraday.png"); plt.close(fig)

# 5. 最高价出现在几点
ex = B.intraday_extremes(minute)
theory = [(2 / math.pi) * (math.asin(math.sqrt((h + 1) / 24)) - math.asin(math.sqrt(h / 24))) for h in range(24)]
share = ex["time_of_high"].dt.hour.value_counts(normalize=True).sort_index()
fig, ax = plt.subplots(figsize=(10, 4.2), dpi=150)
ax.bar(share.index, share.values * 100, color=BLUE, alpha=0.7, label="BTC 日线最高价出现的小时（2017-08 至 2026-08）")
ax.plot(range(24), np.array(theory) * 100, color="black", marker="o", markersize=3, label="随机游走的理论比例")
ax.set_xticks(range(24)); ax.set_xlabel("UTC 小时"); ax.set_ylabel("占全部日子的比例（%）")
ax.legend(fontsize=9); ax.grid(alpha=0.25, axis="y")
ax.set_title("最高价最常出现在一天的开头和结尾")
fig.tight_layout(); fig.savefig(out / "high-hours.png"); plt.close(fig)

# 6. 真实 K 线 vs HA
x = spy.loc["2025-03-10":"2025-05-09"]
ha = B.heikin_ashi(spy).loc[x.index]
fig, axes = plt.subplots(2, 1, figsize=(10, 7), dpi=150, sharex=True)
for ax, df, title in [(axes[0], x, "SPY 真实 K 线"), (axes[1], ha, "SPY Heikin-Ashi")]:
    for i, (o, h, l, c) in enumerate(df[["open", "high", "low", "close"]].itertuples(index=False)):
        draw_candle(ax, i, o, h, l, c, width=0.7)
    ax.set_title(title, fontsize=11); ax.grid(alpha=0.25); ax.autoscale_view()
i9 = list(x.index).index(pd.Timestamp("2025-04-09"))
axes[1].plot(i9, spy.loc["2025-04-09", "close"], marker="x", color="black", markersize=8)
axes[1].annotate("4 月 9 日真实收盘 548.62\nHA 收盘只有 520.93", (i9, spy.loc["2025-04-09", "close"]), xytext=(i9 + 3, 555), fontsize=9,
                 arrowprops={"arrowstyle": "->", "color": "#555"})
ticks = list(range(0, len(x), 8))
axes[1].set_xticks(ticks); axes[1].set_xticklabels([x.index[i].strftime("%m-%d") for i in ticks])
fig.tight_layout(); fig.savefig(out / "ha-vs-real.png"); plt.close(fig)

# 7. HA 回测：假的成交价
h = B.heikin_ashi(day)
green = (h["close"] > h["open"]).astype(int)
held = green.shift(1).fillna(0)                                   # 今天收盘决定，持有到明天收盘
real = (1 + held * day["close"].pct_change().fillna(0)).cumprod()
fake = (1 + held * h["close"].pct_change().fillna(0)).cumprod()
hold = day["close"] / day["close"].iloc[0]
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.plot(day.index, fake, color=DOWN, linewidth=1.2, label="按 HA 收盘价计算（不可能成交的价格）")
ax.plot(day.index, real, color=BLUE, linewidth=1.2, label="按真实收盘价计算")
ax.plot(day.index, hold, color=GRAY, linewidth=1, label="一直持有")
ax.set_yscale("log"); ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}" if v >= 1 else f"{v:g}"))
ax.set_ylabel("1 美元变成多少"); ax.legend(fontsize=9); ax.grid(alpha=0.25, which="both")
ax.set_title("BTC：HA 变绿持有、变红空仓")
fig.tight_layout(); fig.savefig(out / "ha-backtest.png"); plt.close(fig)

# 8. Renko 手算
closes = day["close"].loc["2026-06-24":"2026-07-12"]
bricks = B.renko(closes, 1000)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150, sharey=True, gridspec_kw={"width_ratios": [3, 2]})
a1.plot(closes.index.tz_localize(None), closes.values, color=BLUE, marker="o", markersize=4, linewidth=1)
for k in range(-3, 4):
    a1.axhline(61077.99 + 1000 * k, color=GRAY, linestyle=":", linewidth=0.8)
a1.set_title("日线收盘价，虚线间隔 1,000 美元（从 6 月 24 日收盘价起算）", fontsize=10)
a1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m-%d")); a1.tick_params(axis="x", labelsize=8)
a1.grid(alpha=0.2); a1.yaxis.set_major_formatter(thousands)
for i, b in bricks.iterrows():
    color = UP if b["direction"] > 0 else DOWN
    a2.add_patch(Rectangle((i, min(b["open"], b["close"])), 0.9, 1000, facecolor=color, edgecolor="white"))
    a2.text(i + 0.45, min(b["open"], b["close"]) - 250, b["formed_at"].strftime("%m-%d"), ha="center", fontsize=7)
a2.set_xlim(-0.5, len(bricks) + 0.5); a2.set_ylim(57500, 65000); a2.set_xticks([])
a2.set_title("Renko，每块 1,000 美元（砖下方是形成日期）", fontsize=10)
fig.tight_layout(); fig.savefig(out / "renko-hand.png"); plt.close(fig)

# 9. Renko 全历史
bricks = B.renko(day["close"], 0.05, log=True)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7.5), dpi=150)
a1.plot(day.index, day["close"], color=BLUE, linewidth=0.8)
a1.set_yscale("log"); a1.yaxis.set_major_formatter(thousands); a1.set_title("BTC 日线收盘价（对数坐标）", fontsize=11); a1.grid(alpha=0.25)
for i, b in bricks.iterrows():
    color = UP if b["direction"] > 0 else DOWN
    lo, hi = sorted([b["open"], b["close"]])
    a2.add_patch(Rectangle((i, lo), 1, hi - lo, facecolor=color, edgecolor=color))
a2.set_xlim(0, len(bricks)); a2.set_yscale("log"); a2.set_ylim(day["close"].min() * 0.8, day["close"].max() * 1.2)
a2.yaxis.set_major_formatter(thousands)
years = bricks.groupby(bricks["formed_at"].dt.year).head(1)
a2.set_xticks(years.index); a2.set_xticklabels(years["formed_at"].dt.year, fontsize=8)
a2.set_title(f"Renko，每块 5%，共 {len(bricks)} 块（横轴是砖块序号，刻度标出每年第一块砖）", fontsize=11); a2.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "renko-btc.png"); plt.close(fig)
print("done")
