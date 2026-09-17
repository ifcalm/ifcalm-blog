"""生成第 7 篇的插图：python 07_figures.py <输出目录>（在 talab 项目根目录运行）。"""
import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.ticker import FuncFormatter
from talab import bars as B, data as D, plot as P, timeframes as T

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
UP, DOWN, BLUE, ORANGE, GRAY = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888"

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
four = B.resample_ohlcv(minute, "4h", traded_only=True)
weekly = B.resample_ohlcv(day, "W-MON")
weekly["sma20"] = weekly["close"].rolling(20).mean()
four["low_7d"] = four["low"].rolling(42).min().shift(1)
t = pd.Timestamp("2025-10-30 12:00", tz="UTC")

# 1. 决策点：周线
w = weekly.loc["2025-03-03":"2025-10-20"]
fig, ax, av = P.plot_candles(w, title="BTCUSDT 周线，到 2025-10-20 这一周（最后一根已收盘的周线）",
                             overlays={"20 周均线": weekly["sma20"]})
fig.savefig(out / "decision-weekly.png"); plt.close(fig)

# 2. 决策点：4 小时线
x = four.loc[pd.Timestamp("2025-10-20", tz="UTC"):t]
fig, ax, av = P.plot_candles(x, title="BTCUSDT 4 小时线，到 2025-10-30 12:00 这一根（UTC 16:00 收盘）")
ax.axhline(four.loc[t, "low_7d"], linestyle=":", linewidth=1.2, color=BLUE)
ax.annotate(f"前 7 天最低价 {four.loc[t, 'low_7d']:,.2f}", (30, four.loc[t, "low_7d"]), textcoords="offset points",
            xytext=(0, 4), fontsize=9, color=BLUE)
fig.savefig(out / "decision-4h.png"); plt.close(fig)

# 3. 一根周阳线里面
wk = pd.Timestamp("2025-10-20", tz="UTC")
inside = four.loc[wk:wk + pd.Timedelta("7D") - pd.Timedelta("1s")]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6), dpi=150, gridspec_kw={"width_ratios": [1, 6]}, sharey=True)
bar = weekly.loc[wk]
color = UP if bar["close"] >= bar["open"] else DOWN
a1.vlines(0, bar["low"], bar["high"], color=color, linewidth=1.5)
a1.add_patch(Rectangle((-0.3, min(bar["open"], bar["close"])), 0.6, abs(bar["close"] - bar["open"]), facecolor=color))
a1.set_xlim(-1, 1); a1.set_xticks([]); a1.set_title("一根周线", fontsize=11)
a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
for i, (o, h, l, c) in enumerate(inside[["open", "high", "low", "close"]].itertuples(index=False)):
    col = UP if c >= o else DOWN
    a2.vlines(i, l, h, color=col, linewidth=0.8)
    a2.add_patch(Rectangle((i - 0.35, min(o, c)), 0.7, max(abs(c - o), 1), facecolor=col))
red = (inside["close"] < inside["open"]).sum()
a2.set_title(f"同一周的 42 根 4 小时线：{42 - red} 根阳线，{red} 根阴线", fontsize=11)
ticks = list(range(0, 42, 6))
a2.set_xticks(ticks); a2.set_xticklabels([inside.index[i].strftime("%m-%d") for i in ticks])
for a in (a1, a2):
    a.grid(alpha=0.25)
fig.suptitle("2025-10-20 这一周（周一 00:00 至下周一 00:00，UTC）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "week-inside.png"); plt.close(fig)

# 4. 时间线：正确对齐和错误对齐
fig, ax = plt.subplots(figsize=(12, 3.8), dpi=150)
weeks = [("10-20 这一周", pd.Timestamp("2025-10-20"), "收盘 114,559.40\n在均线上方"),
         ("10-27 这一周", pd.Timestamp("2025-10-27"), "收盘 110,540.68\n在均线下方")]
base = pd.Timestamp("2025-10-20")
days = lambda ts: (ts - base) / pd.Timedelta("1D")
for i, (name, start, note) in enumerate(weeks):
    ax.add_patch(Rectangle((days(start), 1.0), 7, 0.8, facecolor=["#e0f2f1", "#fde0dc"][i], edgecolor=GRAY))
    ax.text(days(start) + 2.3, 1.55, name, ha="center", fontsize=10)
    ax.text(days(start) + 2.3, 1.2, note, ha="center", fontsize=9)
    ax.plot(days(start) + 7, 1.0, marker="^", color="black")
    ax.text(days(start) + 7, 0.78, f"{(start + pd.Timedelta('7D')).strftime('%m-%d')} 00:00\n这一周收盘", ha="center", va="top", fontsize=8)
now = days(pd.Timestamp("2025-10-30 16:00"))
ax.axvline(now, color=BLUE, linestyle="--")
ax.text(now + 0.15, 2.3, "决策时刻：2025-10-30 16:00\n（12:00 这根 4 小时线收盘）", ha="left", fontsize=9, color=BLUE)
ax.add_artist(FancyArrowPatch((now - 0.1, 0.35), (7.05, 0.35), arrowstyle="->", mutation_scale=15, color=UP))
ax.text((now + 7) / 2, 0.15, "正确：只看已经收盘的周线", ha="center", fontsize=9, color=UP)
ax.add_artist(FancyArrowPatch((now + 0.1, 0.35), (13.95, 0.35), arrowstyle="->", mutation_scale=15, color=DOWN, linestyle="--"))
ax.text((now + 14) / 2 + 0.3, 0.15, "错误：看到了还要 3 天多才收盘的周线", ha="center", fontsize=9, color=DOWN)
ax.set_xlim(-0.5, 14.8); ax.set_ylim(-0.1, 2.8); ax.axis("off")
fig.tight_layout(); fig.savefig(out / "alignment-timeline.png"); plt.close(fig)

# 5. 前视偏差的资金曲线
weekly["up"] = (weekly["close"] > weekly["sma20"]).where(weekly["sma20"].notna())
ret = day["close"].pct_change().fillna(0)
good = T.align_higher(day.index, "1D", weekly[["up"]], "7D")["up"].astype(float).fillna(0)
leak = weekly[["up"]].reindex(day.index, method="ffill")["up"].astype(float).fillna(0)
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.plot(day.index, (1 + leak.shift(1).fillna(0) * ret).cumprod(), color=DOWN, label="错误对齐（用到了还没收盘的周线）")
ax.plot(day.index, (1 + good.shift(1).fillna(0) * ret).cumprod(), color=BLUE, label="正确对齐")
ax.plot(day.index, day["close"] / day["close"].iloc[0], color=GRAY, linewidth=1, label="一直持有")
ax.set_yscale("log"); ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}" if v >= 1 else f"{v:g}"))
ax.legend(fontsize=9); ax.grid(alpha=0.25, which="both"); ax.set_ylabel("1 美元变成多少")
ax.set_title("BTC：周线收盘在 20 周均线上方就持有")
fig.tight_layout(); fig.savefig(out / "leak-equity.png"); plt.close(fig)

# 6. 揭晓
x = day.loc["2025-09-15":"2025-12-15"]
fig, ax, av = P.plot_candles(x, title="BTCUSDT 日线，2025-09-15 至 2025-12-15",
                             marks=[("2025-10-30", x.loc["2025-10-30", "low"], "决策点")])
ylo, yhi = ax.get_ylim(); ax.set_ylim(ylo - (yhi - ylo) * 0.12, yhi)
fig.savefig(out / "reveal.png"); plt.close(fig)
print("done")
