"""生成第 8 篇的插图：python 08_figures.py <输出目录>（在 talab 项目根目录运行）。"""
import glob
import itertools
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from talab import data as D, plot as P, structure as X

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
UP, DOWN, BLUE, ORANGE, GRAY = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888"
money = FuncFormatter(lambda v, _: f"{v:,.0f}")
STATE_NAME = {1: "上升", 0: "震荡", -1: "下降"}

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
c = day["close"]
utc = lambda s: pd.Timestamp(s, tz="UTC")
t = utc("2024-10-16")
before = day.loc[:t]


def date_axis(ax, index, n=6):
    step = max(1, len(index) // n)
    ticks = list(range(0, len(index), step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([index[i].strftime("%Y-%m-%d") for i in ticks], fontsize=8)


# 1. 决策点
x = day.loc[utc("2024-03-01"):t]
fig, ax, av = P.plot_candles(x, title="BTCUSDT 日线，2024-03-01 至 2024-10-16")
fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 登山：山峰和山谷、直线距离和实际走的路
rng = np.random.default_rng(5)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4), dpi=150)
xs = np.linspace(0, 10, 400)
ridge = 0.35 * xs + 1.2 * np.sin(xs * 1.9) + 0.18 * np.sin(xs * 11) + 0.08 * np.sin(xs * 37)
a1.fill_between(xs, ridge.min() - 1, ridge, color="#d7ccc8")
a1.plot(xs, ridge, color="#5d4037")
big = X.zigzag(pd.Series(ridge - ridge.min() + 5), 0.20)
for s in big.itertuples():
    a1.plot(xs[s.time], ridge[s.time], "v" if s.kind == 1 else "^", color=DOWN if s.kind == 1 else UP, markersize=9)
a1.set_title("大起伏是山峰和山谷，小起伏只是路上的石头", fontsize=11)
a1.text(0.2, ridge.max() + 0.3, "▼ 山峰（摆动高点）  ▲ 山谷（摆动低点）", fontsize=9)
a1.set_ylim(ridge.min() - 1, ridge.max() + 1)
a1.set_xticks([]); a1.set_yticks([])
straight = np.linspace(0, 6, 21)
winding = np.r_[0, np.cumsum(rng.normal(0.3, 1.3, 20))]
winding = winding - np.linspace(0, winding[-1] - 6, 21)
for path, color, name in [(straight, BLUE, "路线一"), (winding, ORANGE, "路线二")]:
    walked = np.abs(np.diff(path)).sum()
    a2.plot(range(21), path, marker="o", markersize=3, color=color,
            label=f"{name}：直线距离 6，实际走了 {walked:.1f}，效率比 {6 / walked:.2f}")
a2.set_title("同样从 0 走到 6，走的路不一样", fontsize=11)
a2.legend(fontsize=9, loc="upper left"); a2.grid(alpha=0.25); a2.set_xlabel("第几步"); a2.set_ylabel("海拔")
fig.tight_layout(); fig.savefig(out / "hiking.png"); plt.close(fig)

# 3. 分形
x = day.loc[utc("2024-08-01"):t]
fig, ax, av = P.plot_candles(x, title="分形摆动点（2024-08-01 至 2024-10-16）", volume=False, figsize=(11, 5))
pos_x = {ts: i for i, ts in enumerate(x.index)}
for n, dy, size in [(2, 0.012, 7), (5, 0.03, 10)]:
    f = X.fractals(x["high"], x["low"], n, n)
    f = f[f["confirmed_at"] <= t]
    for s in f.itertuples():
        y = s.price * (1 + dy) if s.kind == 1 else s.price * (1 - dy)
        ax.plot(pos_x[s.time], y, "v" if s.kind == 1 else "^", color=DOWN if s.kind == 1 else UP,
                markersize=size, markerfacecolor="none" if n == 5 else None, markeredgewidth=1.3)
ax.plot([], [], "v", color=GRAY, markersize=7, label="左右各 2 根（实心）")
ax.plot([], [], "v", color=GRAY, markersize=10, markerfacecolor="none", label="左右各 5 根（空心）")
ax.legend(fontsize=9, loc="upper left")
lo, hi = ax.get_ylim(); ax.set_ylim(lo * 0.98, hi * 1.02)
fig.savefig(out / "fractals.png"); plt.close(fig)

# 4. 三个阈值的 ZigZag
x = before.loc[utc("2024-03-01"):]
fig, axes = plt.subplots(3, 1, figsize=(11, 9), dpi=150, sharex=True)
for ax, th in zip(axes, [0.05, 0.10, 0.20]):
    z = X.zigzag(before["close"], th)
    state = X.trend_state(z, before["close"], before["close"])["state"].iloc[-1]
    ax.plot(range(len(x)), x["close"], color=GRAY, linewidth=0.9)
    zz = z[z["time"] >= x.index[0]]
    px = [pos_x2 for pos_x2 in [x.index.get_loc(s) for s in zz["time"]]]
    ax.plot(px + [len(x) - 1], zz["price"].tolist() + [x["close"].iloc[-1]], color=BLUE, linewidth=1.4)
    ax.plot([px[-1], len(x) - 1], [zz["price"].iloc[-1], x["close"].iloc[-1]], color="white", linewidth=1.6)
    ax.plot([px[-1], len(x) - 1], [zz["price"].iloc[-1], x["close"].iloc[-1]], color=BLUE, linewidth=1.4, linestyle="--")
    for p, s in zip(px, zz.itertuples()):
        if th == 0.05 and s.time < utc("2024-07-01"):
            continue                                        # 5% 的摆动点太密，只标 7 月以后的
        ax.annotate(f"{s.price:,.0f}", (p, s.price), textcoords="offset points", xytext=(0, 6 if s.kind == 1 else -13),
                    ha="center", fontsize=7.5, color=DOWN if s.kind == 1 else UP)
    ax.set_title(f"ZigZag {th:.0%}：10 月 16 日的状态是「{STATE_NAME[int(state)]}」", fontsize=11, loc="left")
    ax.yaxis.set_major_formatter(money); ax.grid(alpha=0.25)
    lo, hi = ax.get_ylim(); ax.set_ylim(lo - (hi - lo) * 0.08, hi + (hi - lo) * 0.08)
date_axis(axes[-1], x.index)
fig.suptitle("同一段收盘价，三个阈值（虚线是还没有确认的最后一段）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "zigzag-thresholds.png"); plt.close(fig)

# 5. 重绘
x = day.loc[utc("2024-06-15"):utc("2024-08-10")]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150, sharey=True)
for ax, d in zip(axes, ["2024-07-20", "2024-07-29", "2024-08-05"]):
    end = utc(d)
    seen = c.loc[:end]
    z = X.zigzag(seen, 0.10)
    z = z[z["time"] >= utc("2024-05-01")]
    last = z.iloc[-1]
    seg = seen.loc[last["time"]:].iloc[1:]
    tip = seg.idxmin() if last["kind"] == 1 else seg.idxmax()
    part = x.loc[:end]
    ax.plot(x.index, x["close"], color="#dddddd", linewidth=0.9)
    ax.plot(part.index, part["close"], color=GRAY, linewidth=0.9)
    ax.plot(z["time"], z["price"], color=BLUE, linewidth=1.5)
    ax.plot([last["time"], tip], [last["price"], c[tip]], color=ORANGE, linewidth=1.5, linestyle="--")
    ax.plot(tip, c[tip], "o", color=ORANGE)
    ax.text(0.03, 0.95, f"最后一个点：{tip.strftime('%m-%d')} {c[tip]:,.0f}", transform=ax.transAxes,
            va="top", fontsize=9, color=ORANGE)
    ax.axvline(end, color=BLUE, linewidth=0.8, linestyle=":")
    ax.set_title(f"站在 {d} 收盘时看", fontsize=11)
    ax.set_xlim(x.index[0], x.index[-1])
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m-%d"))
    ax.yaxis.set_major_formatter(money); ax.grid(alpha=0.25)
fig.suptitle("10% ZigZag：蓝色实线是已确认的摆动点，橙色虚线是还会变的最后一段（浅灰色是当时还没发生的走势）", fontsize=11)
fig.tight_layout(); fig.savefig(out / "repaint.png"); plt.close(fig)

# 6. 前视偏差
def curve(swings, when):
    signal = pd.Series(np.nan, index=c.index)
    for s in swings.sort_values(when).itertuples():
        signal[getattr(s, when)] = 1.0 if s.kind == -1 else 0.0
    position = signal.ffill().fillna(0)
    return (1 + position.shift(1).fillna(0) * c.pct_change().fillna(0)).cumprod()
z10 = X.zigzag(c, 0.10)
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.plot(c.index, curve(z10, "time"), color=DOWN, label="在摆动点所在的那天买卖（用到了未来）")
ax.plot(c.index, curve(z10, "confirmed_at"), color=BLUE, label="在摆动点确认的那天买卖")
ax.plot(c.index, c / c.iloc[0], color=GRAY, linewidth=1, label="一直持有")
ax.set_yscale("log")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}" if v >= 1 else f"{v:g}"))
ax.legend(fontsize=9); ax.grid(alpha=0.25, which="major"); ax.set_ylabel("1 美元变成多少")
ax.set_title("BTC：10% ZigZag 低点买入、高点卖出")
fig.tight_layout(); fig.savefig(out / "lookahead.png"); plt.close(fig)

# 7. 揭晓
x = day.loc[utc("2024-03-01"):utc("2024-12-31")]
fig, (ax, a2) = plt.subplots(2, 1, figsize=(11, 6.5), dpi=150, sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
ax.plot(x.index, x["close"], color="black", linewidth=1)
ax.axvline(t, color=BLUE, linestyle="--"); ax.text(t, x["close"].max(), " 决策点 10-16", color=BLUE, fontsize=9, va="top")
ax.set_yscale("log"); ax.yaxis.set_major_formatter(money); ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
ax.set_yticks([50000, 60000, 70000, 80000, 90000, 100000]); ax.grid(alpha=0.25)
ax.set_title("BTCUSDT 收盘价（对数坐标）和不同定义下的趋势状态", fontsize=12)
rows = []
for th in [0.05, 0.10, 0.20]:
    levels = X.trend_state(X.zigzag(c, th), c, c)
    rows.append((f"{th:.0%} 状态", levels["state"]))
    rows.append((f"{th:.0%} 突破版", X.break_state(levels, c)))
colors = {1: UP, 0: "#bdbdbd", -1: DOWN}
for k, (name, s) in enumerate(rows):
    s = s.reindex(x.index)
    for v in [1, 0, -1]:
        mask = (s == v).to_numpy()
        a2.fill_between(x.index, k - 0.4, k + 0.4, where=mask, color=colors[v], step="mid", linewidth=0)
a2.set_yticks(range(len(rows))); a2.set_yticklabels([r[0] for r in rows], fontsize=8.5); a2.invert_yaxis()
a2.axvline(t, color=BLUE, linestyle="--")
for v, label in [(1, "上升"), (0, "震荡"), (-1, "下降")]:
    a2.fill_between([], [], color=colors[v], label=label)
a2.legend(fontsize=8, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0))
a2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m"))
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 8. 打乱检验
def state_gap(log_returns, threshold, rule, horizon=20):
    close = pd.Series(np.exp(np.cumsum(np.asarray(log_returns))))
    levels = X.trend_state(X.zigzag(close, threshold), close, close)
    state = levels["state"] if rule == "状态" else X.break_state(levels, close)
    forward = close.shift(-horizon) / close - 1
    return forward[state == 1].mean() - forward[state == -1].mean()
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), dpi=150)
for ax, (name, close, th, rule) in zip(axes, [("BTC", c, 0.10, "突破版"), ("SPY", spy["close"], 0.03, "状态")]):
    lr = np.log(close).diff().dropna().to_numpy()
    real = state_gap(lr, th, rule)
    r = np.random.default_rng(0)
    sims = [state_gap(r.permutation(lr), th, rule) for _ in range(1000)]
    ax.hist(sims, bins=40, color="#cfd8dc", edgecolor="white")
    ax.axvline(real, color=DOWN if real < 0 else UP, linewidth=2)
    ax.text(real, ax.get_ylim()[1] * 0.92, f"实际 {real:+.2%} ", color=DOWN if real < 0 else UP, fontsize=10, ha="right")
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.02 if name == "BTC" else 0.01))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_title(f"{name}（阈值 {th:.0%}，{rule}）：上升状态减下降状态，之后 20 天的平均收益", fontsize=10)
    ax.set_xlabel("打乱日子顺序 1,000 次的结果"); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "shuffle.png"); plt.close(fig)

# 9. 趋势线
x = day.loc[utc("2024-08-01"):t]
fig, ax, av = P.plot_candles(x, title="10 条都「说得过去」的上升趋势线（2024-10-16）", volume=False, figsize=(11, 5.2))
pos_x = {ts: i for i, ts in enumerate(x.index)}
styles = {("最低价", "算术"): (BLUE, "-"), ("最低价", "对数"): (BLUE, "--"), ("收盘价", "算术"): (ORANGE, "-"), ("收盘价", "对数"): (ORANGE, "--")}
for price_type in ["最低价", "收盘价"]:
    series = x["low"] if price_type == "最低价" else x["close"]
    lows = X.fractals(series, series, 2, 2)
    lows = lows[(lows["kind"] == -1) & (lows["confirmed_at"] <= t)]
    for a, b in itertools.combinations(lows.itertuples(), 2):
        if b.price <= a.price:
            continue
        for scale in ["算术", "对数"]:
            f, g = (np.log, np.exp) if scale == "对数" else (lambda v: v, lambda v: v)
            ia, ib = pos_x[a.time], pos_x[b.time]
            steps = np.arange(len(x) - ia)
            line = g(f(a.price) + (f(b.price) - f(a.price)) / (ib - ia) * steps)
            if (series.iloc[ia:].to_numpy() >= line - 1e-6).all():
                color, ls = styles[(price_type, scale)]
                ax.plot(ia + steps, line, color=color, linestyle=ls, linewidth=1)
for (price_type, scale), (color, ls) in styles.items():
    ax.plot([], [], color=color, linestyle=ls, label=f"连接{price_type}，{scale}坐标")
ax.legend(fontsize=9, loc="upper left")
fig.savefig(out / "trendlines.png"); plt.close(fig)

# 10. 趋势强度
x = day.loc[utc("2024-03-01"):utc("2024-12-31")]
er = X.efficiency_ratio(c, 20)
reg = X.regression_slope(c, 20)
dmi = X.adx(day["high"], day["low"], c, 14)
fig, axes = plt.subplots(4, 1, figsize=(11, 9), dpi=150, sharex=True, gridspec_kw={"height_ratios": [2, 1, 1, 1.3]})
axes[0].plot(x.index, x["close"], color="black", linewidth=1); axes[0].yaxis.set_major_formatter(money)
axes[0].set_title("BTCUSDT 收盘价和三种趋势强度（都用最近 20 天或 14 天计算）", fontsize=12)
axes[1].plot(x.index, er.reindex(x.index), color=BLUE); axes[1].set_ylabel("效率比"); axes[1].set_ylim(0, 1)
axes[2].plot(x.index, reg["r2"].reindex(x.index), color=ORANGE); axes[2].set_ylabel("回归 R 平方"); axes[2].set_ylim(0, 1)
axes[3].plot(x.index, dmi["adx"].reindex(x.index), color="black", label="ADX")
axes[3].plot(x.index, dmi["plus_di"].reindex(x.index), color=UP, linewidth=0.9, label="+DI")
axes[3].plot(x.index, dmi["minus_di"].reindex(x.index), color=DOWN, linewidth=0.9, label="-DI")
axes[3].axhline(25, color=GRAY, linestyle=":"); axes[3].legend(fontsize=8, ncol=3, loc="upper left"); axes[3].set_ylabel("ADX / DI")
for a in axes:
    a.axvline(t, color=BLUE, linestyle="--", linewidth=0.9); a.grid(alpha=0.25)
axes[3].xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m"))
fig.tight_layout(); fig.savefig(out / "strength.png"); plt.close(fig)
print("done")
