"""生成第 10 篇的插图：python 10_figures.py <输出目录>（在 talab 项目根目录运行，先运行 10_volume.py 下载合约数据）。"""
import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from talab import bars as B, data as D, indicators as I, plot as P

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
money = FuncFormatter(lambda v, _: f"{v:,.0f}")
pct = FuncFormatter(lambda v, _: f"{v:.0%}")
utc = lambda s: pd.Timestamp(s, tz="UTC")

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
perp = D.load_binance_klines(glob.glob("data/binance/um/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
spy.loc[pd.Timestamp("2026-04-17"), "volume"] = np.nan
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)

def with_vwap(start, end):
    h = B.resample_ohlcv(minute.loc[start:end], "1h")
    h["vwap"] = I.vwap(h["quote_volume"] / h["volume"], h["volume"], h.index.floor("1D"))
    return h

# 1. 决策点
h = with_vwap("2025-12-17", "2025-12-17 15:59")
fig, ax, av = P.plot_candles(h, title="BTCUSDT 1 小时线，2025-12-17 00:00 至 15:00 这一根（UTC 16:00 收盘）",
                             overlays={"当日 VWAP（UTC 0 点起累计）": h["vwap"]})
fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 揭晓
h = with_vwap("2025-12-17", "2025-12-19 23:59")
fig, ax, av = P.plot_candles(h, title="BTCUSDT 1 小时线，2025-12-17 至 2025-12-19（VWAP 每天 UTC 0 点重新累计）")
xs = np.arange(len(h))
for d in h.index.floor("1D").unique():
    mask = (h.index.floor("1D") == d)
    ax.plot(xs[mask], h["vwap"][mask], color=ORANGE, linewidth=1.4)
ax.plot([], [], color=ORANGE, label="当日 VWAP"); ax.legend(fontsize=9, loc="upper right")
i = h.index.get_loc(utc("2025-12-17 15:00"))
ax.annotate("决策点", (i, h["low"].iloc[i]), textcoords="offset points", xytext=(0, -30), ha="center", fontsize=9,
            arrowprops={"arrowstyle": "->", "color": "#555"})
lo, hi = ax.get_ylim(); ax.set_ylim(lo - (hi - lo) * 0.08, hi)
fig.savefig(out / "reveal.png"); plt.close(fig)

# 3. 成交量的单位和零手续费
fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)
monthly = day[["volume", "quote_volume"]].resample("MS").mean()
ax.plot(monthly.index, monthly["volume"], color=ORANGE, label="平均每天成交多少 BTC（左轴）")
ax2 = ax.twinx()
ax2.plot(monthly.index, monthly["quote_volume"] / 1e8, color=BLUE, label="平均每天成交多少亿 USDT（右轴）")
ax.axvspan(utc("2022-07-08"), utc("2023-03-22"), color=GRAY, alpha=0.2)
ax.text(utc("2022-07-15"), monthly["volume"].max() * 0.55, "BTC 交易对\n零手续费\n2022-07-08\n~2023-03-22", fontsize=8.5, va="top")
ax.yaxis.set_major_formatter(money); ax2.yaxis.set_major_formatter(money)
ax.set_ylabel("BTC"); ax2.set_ylabel("亿 USDT")
lines = ax.get_legend_handles_labels(); lines2 = ax2.get_legend_handles_labels()
ax.legend(lines[0] + lines2[0], lines[1] + lines2[1], fontsize=9, loc="upper left")
ax.grid(alpha=0.25); ax.set_title("Binance BTCUSDT 现货成交量（按月平均）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "volume-units.png"); plt.close(fig)

# 4. 现货和永续合约
both = pd.DataFrame({"现货": day["quote_volume"], "永续合约": perp["quote_volume"]}).dropna().resample("MS").mean() / 1e8
fig, ax = plt.subplots(figsize=(11, 4.2), dpi=150)
ax.plot(both.index, both["永续合约"], color=PURPLE, label="BTCUSDT U 本位永续合约")
ax.plot(both.index, both["现货"], color=BLUE, label="BTCUSDT 现货")
ax.set_yscale("log"); ax.yaxis.set_major_formatter(money); ax.set_ylabel("平均每天成交额（亿 USDT，对数坐标）")
ax.legend(fontsize=9); ax.grid(alpha=0.25, which="both"); ax.set_title("同一个交易所、同一个标的：现货和永续合约的成交额", fontsize=12)
fig.tight_layout(); fig.savefig(out / "spot-perp.png"); plt.close(fig)

# 5. 一天之内的成交量
hour_all = B.resample_ohlcv(minute, "1h")
share = hour_all["volume"].groupby([hour_all.index.year, hour_all.index.hour]).sum()
share = share / share.groupby(level=0).transform("sum")
fig, ax = plt.subplots(figsize=(10, 4.2), dpi=150)
for year, color in [(2019, GRAY), (2022, BLUE), (2025, DOWN)]:
    ax.plot(range(24), share[year].values, "o-", color=color, markersize=3.5, label=str(year))
ax.axvspan(12.5, 15.5, color=ORANGE, alpha=0.12)
ax.text(14, ax.get_ylim()[1] * 0.97, "美股开盘前后\n(UTC 13:30 或 14:30)", ha="center", va="top", fontsize=9)
ax.set_xticks(range(0, 24, 2)); ax.set_xlabel("UTC 小时"); ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1%}"))
ax.set_ylabel("占全天成交量的比例"); ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax.set_title("BTCUSDT 现货：一天中每个小时的成交量占比", fontsize=12)
fig.tight_layout(); fig.savefig(out / "hour-share.png"); plt.close(fig)

# 6. 成交量和涨跌幅
fig, ax = plt.subplots(figsize=(10, 4.2), dpi=150)
for (name, df), color in zip([("BTC", day), ("SPY", spy), ("AAPL", aapl)], [ORANGE, BLUE, GRAY]):
    r = np.log(df["close"]).diff()
    z = (r / r.rolling(20).std().shift(1)).abs()
    rv = I.relative_volume(df["volume"], 20)
    t = pd.DataFrame({"z": z, "rv": rv}).dropna()
    group = pd.cut(t["z"], [0, 0.5, 1, 1.5, 2, 3, np.inf])
    med = t.groupby(group, observed=False)["rv"].median()
    ax.plot(range(len(med)), med.values, "o-", color=color, label=name)
ax.set_xticks(range(6)); ax.set_xticklabels(["0~0.5", "0.5~1", "1~1.5", "1.5~2", "2~3", "3 以上"])
ax.set_xlabel("当天涨跌幅是前 20 天标准差的几倍（不分涨跌）"); ax.set_ylabel("相对成交量的中位数")
ax.axhline(1, color=GRAY, linestyle=":"); ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax.set_title("涨跌越剧烈，成交量越大", fontsize=12)
fig.tight_layout(); fig.savefig(out / "volume-vs-move.png"); plt.close(fig)

# 7. 天量
vol = day["volume"]
record = vol > vol.rolling(250).max().shift(1)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.2), dpi=150, sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
a1.plot(day.index, day["close"], color="black", linewidth=0.9)
ret = day["close"].pct_change()
for t in day.index[record & vol.rolling(250).max().shift(1).notna()]:
    color = UP if ret[t] > 0 else DOWN
    a1.plot(t, day.loc[t, "close"], "o", color=color, markersize=6)
    a2.axvline(t, color=color, linewidth=0.8, alpha=0.7)
a1.set_yscale("log"); a1.yaxis.set_major_formatter(money); a1.grid(alpha=0.25)
a1.set_title("BTCUSDT：成交量创 250 天新高的日子（绿色当天上涨，红色当天下跌）", fontsize=12)
a2.plot(day.index, vol, color=GRAY, linewidth=0.7); a2.yaxis.set_major_formatter(money); a2.set_ylabel("BTC"); a2.grid(alpha=0.25)
a2.axvspan(utc("2022-07-08"), utc("2023-03-22"), color=ORANGE, alpha=0.15)
fig.tight_layout(); fig.savefig(out / "climax.png"); plt.close(fig)

# 8. 锚定 VWAP
daily_price = day["quote_volume"] / day["volume"]
x = day.loc[utc("2025-09-01"):]
fig, ax, av = P.plot_candles(x, title="BTCUSDT 日线和三条锚定 VWAP", volume=False, figsize=(11, 5.2), overlays={
    "从 2025-10-06 历史最高点": I.anchored_vwap(daily_price, day["volume"], utc("2025-10-06")),
    "从 2026-02-06 暴跌低点": I.anchored_vwap(daily_price, day["volume"], utc("2026-02-06")),
    "从 2026-07-01 熊市低点": I.anchored_vwap(daily_price, day["volume"], utc("2026-07-01"))})
ax.legend(fontsize=9, loc="upper right")
fig.savefig(out / "avwap.png"); plt.close(fig)

# 9. Volume Profile
segment = minute.loc["2026-02-06":"2026-05-31"]
segment = segment[segment["volume"] > 0]
profile = I.volume_profile(segment["quote_volume"] / segment["volume"], segment["volume"], 250)
area = I.value_area(profile, 0.7)
seg_day = day.loc[utc("2026-02-06"):utc("2026-05-31")]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.4), dpi=150, sharey=True, gridspec_kw={"width_ratios": [3, 1.2]})
a1.plot(seg_day.index, seg_day["close"], color="black", linewidth=1)
a1.fill_between(seg_day.index, seg_day["low"], seg_day["high"], color=GRAY, alpha=0.25, linewidth=0)
colors = [BLUE if area["val"] <= p < area["vah"] else "#b0bec5" for p in profile.index]
a2.barh(profile.index + 125, profile.values, height=240, color=colors)
for a in (a1, a2):
    a.axhline(area["poc"], color=DOWN, linewidth=1.2)
    a.axhspan(65000, 65618.49, color=ORANGE, alpha=0.25)
    a.grid(alpha=0.25)
a1.text(seg_day.index[-1], area["poc"] + 300, f"POC {area['poc']:,.0f}", color=DOWN, ha="right", fontsize=9)
a2.text(profile.max() * 0.98, area["vah"] + 300, f"价值区间上沿 {area['vah']:,.0f}", color=BLUE, ha="right", fontsize=9)
a2.text(profile.max() * 0.98, area["val"] - 900, f"价值区间下沿 {area['val']:,.0f}", color=BLUE, ha="right", fontsize=9)
a1.text(seg_day.index[3], 64200, "第 9 篇的 65,000 ~ 65,618", color=ORANGE, fontsize=9)
a1.yaxis.set_major_formatter(money); a1.set_title("BTCUSDT 日线，2026-02-06 至 2026-05-31", fontsize=11)
a1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m-%d"))
a2.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3)); a2.xaxis.set_major_formatter(money); a2.set_xlabel("成交量（BTC）"); a2.set_title("每 250 美元一格的成交量", fontsize=11)
fig.tight_layout(); fig.savefig(out / "profile.png"); plt.close(fig)

# 10. 前一天的 POC
m = minute[minute["volume"] > 0]
avg = m["quote_volume"] / m["volume"]
width = avg.groupby(m.index.floor("1D")).transform("first") * 0.001
poc = {}
for d, idx in m.groupby(m.index.floor("1D")).groups.items():
    poc[d] = I.value_area(I.volume_profile(avg[idx], m["volume"][idx], width[idx[0]]))["poc"]
poc = pd.Series(poc).reindex(day.index)
references = {"前一天 POC": poc.shift(1), "前一天 VWAP": daily_price.shift(1), "前一天最高最低价中点": ((day["high"] + day["low"]) / 2).shift(1)}
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150, sharey=True)
labels = ["0.5%~1%", "1%~2%", "2%~5%"]
for ax, (name, level) in zip(axes, references.items()):
    distance = np.log(day["open"] / level)
    mirror = day["open"] ** 2 / level
    hit = np.where(distance > 0, day["low"] <= level, day["high"] >= level)
    mirror_hit = np.where(distance > 0, day["high"] >= mirror, day["low"] <= mirror)
    t = pd.DataFrame({"距离": distance.abs(), "碰到": hit, "对照": mirror_hit}).dropna()
    group = pd.cut(t["距离"], [0.005, 0.01, 0.02, 0.05], labels=labels)
    s = t.groupby(group, observed=False)[["碰到", "对照"]].mean()
    xs = np.arange(len(labels))
    ax.bar(xs - 0.18, s["碰到"], width=0.36, color=BLUE, label="当天碰到它")
    ax.bar(xs + 0.18, s["对照"], width=0.36, color="#b0bec5", label="当天碰到对照价格")
    ax.set_xticks(xs); ax.set_xticklabels(labels); ax.set_xlabel("开盘价离它多远")
    ax.set_title(name, fontsize=11); ax.yaxis.set_major_formatter(pct); ax.grid(alpha=0.25, axis="y")
axes[0].legend(fontsize=9)
fig.tight_layout(); fig.savefig(out / "poc-magnet.png"); plt.close(fig)
print("done")
