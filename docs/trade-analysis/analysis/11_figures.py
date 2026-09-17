"""生成第 11 篇的插图：python 11_figures.py <输出目录>（在 talab 项目根目录运行）。"""
import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter
from talab import bars as B, data as D, plot as P, structure as X

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
UP, DOWN, BLUE, ORANGE, GRAY = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888"
cols = ["open", "high", "low", "close"]
STATE_COLORS = {"up": "#c8ebc8", "down": "#f6c9c9", "range": "#e3e3e3",
                "transition_up": "#e6f5b0", "transition_down": "#fbe0b5", "transition": "#fbe9a8"}
STATE_NAMES = {"up": "上升趋势", "down": "下降趋势", "range": "震荡",
               "transition_up": "过渡（向上）", "transition_down": "过渡（向下）", "transition": "过渡"}

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
h4 = B.resample_ohlcv(minute, "4h", traded_only=True)
h1 = B.resample_ohlcv(minute, "1h", traded_only=True)
del minute
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)


def analyze(df, threshold):
    c = df["close"]
    swings = X.zigzag(c, threshold)
    levels = X.trend_state(swings, c, c)
    state = X.market_state(levels, c)
    atr = X.wilder_smooth(X.true_range(df["high"], df["low"], c), 14)
    return swings, levels, state, atr, X.entries(c, df["high"], df["low"], swings, levels, state)


def candles(ax, bars, scale=1.0):
    for x, (o, h, l, c) in enumerate(bars[cols].to_numpy() * scale):
        color = UP if c >= o else DOWN
        ax.vlines(x, l, h, color=color, linewidth=0.8)
        ax.add_patch(Rectangle((x - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-6), facecolor=color, edgecolor=color))


def ribbon(ax, labels, y0, height):
    """在价格图底部画一条状态色带。"""
    for x, label in enumerate(labels):
        if isinstance(label, str):
            ax.add_patch(Rectangle((x - 0.5, y0), 1, height, facecolor=STATE_COLORS[label], edgecolor="none"))


def date_ticks(ax, index, fmt="%Y-%m"):
    ticks = [i for i in range(len(index)) if i == 0 or index[i].month != index[i - 1].month]
    ax.set_xticks(ticks[::2])
    ax.set_xticklabels([index[i].strftime(fmt) for i in ticks[::2]], fontsize=8.5)


# 1~4. 决策点（匿名）
segment = aapl.loc["2021-08-02":"2022-08-31"]
scale = 100 / segment["close"].iloc[0]
checkpoints = [("决定 1", "2022-01-11"), ("决定 2", "2022-03-29"), ("决定 3", "2022-03-31"), ("决定 4", "2022-06-03")]
lo, hi = segment["low"].min() * scale, segment["high"].max() * scale
for n, (name, t) in enumerate(checkpoints, start=1):
    k = segment.index.get_loc(pd.Timestamp(t)) + 1
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)
    candles(ax, segment.iloc[:k], scale)
    ax.axvspan(k - 0.5, len(segment), color="#f4f4f4")
    ax.text((k + len(segment)) / 2, (lo + hi) / 2, "还没有发生", ha="center", va="center", fontsize=14, color="#aaaaaa")
    ax.annotate(f"第 {k} 根\n收盘 {segment['close'].iloc[k - 1] * scale:.2f}", (k - 1, segment["high"].iloc[k - 1] * scale),
                textcoords="offset points", xytext=(0, 26), ha="center", fontsize=9,
                arrowprops={"arrowstyle": "->", "color": "#555"})
    ax.set_xlim(-2, len(segment) + 1)
    ax.set_ylim(lo * 0.97, hi * 1.05)
    ax.set_xlabel("第几根日线（日期已隐藏）")
    ax.set_title(f"{name}：一段没有日期的日线，价格从 100 开始", fontsize=12)
    ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out / f"decision-{n}.png"); plt.close(fig)

# 5. 状态规则示意
fig, axes = plt.subplots(1, 4, figsize=(13, 3.6), dpi=150)
demos = [
    ("上升趋势\n高点抬高，低点抬高", [0, 1, 2, 3, 4, 5], [100, 110, 104, 116, 109, 113], None, None),
    ("下降趋势\n高点降低，低点降低", [0, 1, 2, 3, 4, 5], [116, 104, 111, 98, 106, 101], None, None),
    ("震荡\n方向不一致，收盘在框里", [0, 1, 2, 3, 4, 5], [100, 116, 98, 112, 103, 108], (3, 112), (4, 103)),
    ("过渡\n收盘越过框，方向变得不一致", [0, 1, 2, 3, 4, 5], [116, 100, 110, 96, 104, 114], (4, 104), (3, 96)),
]
for ax, (title, xs, ys, top, bottom) in zip(axes, demos):
    ax.plot(xs, ys, color="black", linewidth=1.3)
    ax.plot(xs[1:-1], ys[1:-1], "o", color=BLUE, markersize=4)
    if top:
        ax.axhline(top[1], color=BLUE, linestyle="--", linewidth=0.9)
        ax.axhline(bottom[1], color=BLUE, linestyle="--", linewidth=0.9)
        ax.axhspan(bottom[1], top[1], color=BLUE, alpha=0.06)
    ax.plot(xs[-1], ys[-1], "s", color=ORANGE, markersize=6)
    ax.set_title(title, fontsize=10.5)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_ylim(90, 122)
axes[0].annotate("今天的收盘价", (5, 113), textcoords="offset points", xytext=(-30, 26), fontsize=8.5,
                 arrowprops={"arrowstyle": "->", "color": "#555"})
axes[3].text(0.1, 91.5, "虚线框：最近一个已确认的高点和低点", fontsize=8, color=BLUE)
fig.tight_layout(); fig.savefig(out / "state-rules.png"); plt.close(fig)

# 6. 揭晓：真实日期、状态、信号
swings, levels, state, atr, signals = analyze(aapl, 0.05)
fig, ax = plt.subplots(figsize=(12, 5.4), dpi=150)
candles(ax, segment)
x_of = {t: i for i, t in enumerate(segment.index)}
low_edge = segment["low"].min() * 0.9
ribbon(ax, state.reindex(segment.index).tolist(), low_edge, segment["low"].min() * 0.04)
ax.step(range(len(segment)), levels["last_high"].reindex(segment.index), where="post", color=BLUE, linestyle="--",
        linewidth=0.8, label="最近一个已确认的高点")
ax.step(range(len(segment)), levels["last_low"].reindex(segment.index), where="post", color="black", linestyle=":",
        linewidth=0.9, label="最近一个已确认的低点")
kind_names = {"pullback": "回调", "breakout": "突破", "failed": "失败突破"}
offsets = {"决定 1": (0, 40), "决定 2": (-40, 40), "决定 3": (60, 40), "决定 4": (80, 50)}
for (name, t) in checkpoints:
    t = pd.Timestamp(t)
    row = signals[signals["time"] == t].iloc[0]
    dx, dy = offsets[name]
    y = segment.loc[t, "high"] if dy > 0 else segment.loc[t, "low"]
    ax.annotate(f"{name}\n{t:%m-%d} {kind_names[row.kind]}{'做多' if row.direction == 1 else '做空'}", (x_of[t], y),
                textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=8.5,
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
                arrowprops={"arrowstyle": "->", "color": "#555"})
date_ticks(ax, segment.index)
handles = [Patch(color=STATE_COLORS[k], label=STATE_NAMES[k]) for k in ["up", "down", "range", "transition_up", "transition_down"]]
ax.legend(handles=ax.get_legend_handles_labels()[0] + handles, fontsize=8, loc="upper right", ncol=2)
ax.set_ylim(low_edge * 0.98, segment["high"].max() * 1.08)
ax.set_title("揭晓：AAPL 日线（拆股和分红调整后），2021-08-02 至 2022-08-31；底部色带是 talab 的市场状态（ZigZag 5%）",
             fontsize=11)
ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 7. 状态和事后的行情段
markets = [("BTC", day, 0.10), ("SPY", spy, 0.03), ("AAPL", aapl, 0.05)]
names = ["up", "transition_up", "range", "transition_down", "down"]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), dpi=150, sharey=True)
for ax, (market, df, threshold) in zip(axes, markets):
    sw, lv, st, a, sig = analyze(df, threshold)
    p = pd.Series(np.arange(len(df)), index=df.index)
    leg = pd.Series(np.nan, index=df.index)
    for s0, s1 in zip(sw.itertuples(), sw.iloc[1:].itertuples()):
        leg.iloc[p[s0.time] + 1:p[s1.time] + 1] = 1.0 if s1.kind == 1 else 0.0
    both = pd.concat([st.rename("s"), leg.rename("up")], axis=1).dropna()
    share = both.groupby("s")["up"].mean().reindex(names)
    bars = ax.bar(range(len(names)), share, color=[STATE_COLORS[k] for k in names], edgecolor="#777")
    for b, v in zip(bars, share):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.0%}", ha="center", fontsize=9)
    ax.axhline(both["up"].mean(), color=GRAY, linestyle="--", linewidth=1)
    ax.text(len(names) - 0.5, both["up"].mean() + 0.015, f"全部 K 线 {both['up'].mean():.0%}", ha="right", fontsize=8.5,
            color="#555")
    ax.set_xticks(range(len(names))); ax.set_xticklabels([STATE_NAMES[k] for k in names], fontsize=8.5, rotation=20)
    ax.set_title(f"{market}（ZigZag {threshold:.0%}）", fontsize=11)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_ylim(0, 1.05); ax.grid(alpha=0.25, axis="y")
axes[0].set_ylabel("事后看，处在上涨段里的比例")
fig.suptitle("实时状态说的，和事后看到的行情段：趋势状态里有不少 K 线其实已经在反方向的行情段里", fontsize=11.5)
fig.tight_layout(); fig.savefig(out / "state-vs-legs.png"); plt.close(fig)


# 8. 三类入场：BTC 4 小时线和 1 小时线
def shuffle_bars(df, rng):
    rel = np.log(df[cols].div(df["close"].shift(1), axis=0))
    rel = rel.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    prev_close = df["close"].iloc[0] * np.exp(rel["close"].cumsum().shift(1, fill_value=0))
    frame = np.exp(rel[cols]).mul(prev_close, axis=0)
    frame.index = df.index[1:]
    return frame


def win_rates(df, threshold):
    sw, lv, st, a, sig = analyze(df, threshold)
    sig = sig[a.reindex(sig["time"]).notna().to_numpy()]
    sig = sig.assign(win=X.first_passage(df["close"], df["high"], df["low"], a, sig["time"], sig["direction"]))
    return sig.groupby(["kind", "direction"])["win"].mean()


order = [("breakout", 1), ("breakout", -1), ("failed", 1), ("failed", -1), ("pullback", 1), ("pullback", -1)]
labels = ["突破做多", "突破做空", "失败突破\n做多", "失败突破\n做空", "回调做多", "回调做空"]
fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), dpi=150, sharey=True)
for ax, (market, df, threshold) in zip(axes, [("BTC 4 小时线（ZigZag 4%）", h4, 0.04), ("BTC 1 小时线（ZigZag 2%）", h1, 0.02)]):
    rng = np.random.default_rng(0)
    real = win_rates(df, threshold).reindex(order)
    sims = pd.concat([win_rates(shuffle_bars(df, rng), threshold) for _ in range(200)], axis=1).reindex(order)
    lo_, hi_ = sims.quantile(0.025, axis=1), sims.quantile(0.975, axis=1)
    xs = np.arange(len(order))
    ax.vlines(xs, lo_, hi_, color=GRAY, linewidth=6, alpha=0.45, label="打乱 200 次的 95% 范围")
    ax.plot(xs, real, "o", color=[BLUE][0], markersize=8, label="真实数据")
    for x, v in zip(xs, real):
        ax.text(x + 0.12, v, f"{v:.1%}", fontsize=8.5, va="center")
    ax.axhline(0.5, color="black", linewidth=0.6, linestyle=":")
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=8.5)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_title(market, fontsize=11); ax.grid(alpha=0.25, axis="y"); ax.set_xlim(-0.5, len(order) - 0.2)
axes[0].set_ylabel("先碰到顺向 2 ATR 线的比例")
axes[0].legend(fontsize=8.5, loc="lower left")
fig.suptitle("三类入场之后，先碰到顺向还是反向的 2 ATR 线（20 根以内）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "entries.png"); plt.close(fig)

# 9. 实验一：手工标注和自动标注
hand_segments = pd.read_csv(Path(__file__).with_name("11_spy_hand_labels.csv"))
window = spy.loc["2018-01-02":"2019-06-28"]
hand = X.segments_to_labels(hand_segments, window.index)
simple = {"transition_up": "transition", "transition_down": "transition"}
fig, ax = plt.subplots(figsize=(12, 5.4), dpi=150)
candles(ax, window)
low = window["low"].min()
height = (window["high"].max() - low) * 0.05
ribbon(ax, hand.tolist(), low - 2.3 * height, height)
for threshold, k in [(0.03, 3.6), (0.02, 4.9)]:
    auto = analyze(spy, threshold)[2].reindex(window.index).replace(simple)
    ribbon(ax, auto.tolist(), low - k * height, height)
for y, text in [(1.8, "手工"), (3.1, "自动 3%"), (4.4, "自动 2%")]:
    ax.text(-2, low - y * height, text, ha="right", va="center", fontsize=9)
date_ticks(ax, window.index)
handles = [Patch(color=STATE_COLORS[k], label=STATE_NAMES[k]) for k in ["up", "down", "range", "transition"]]
ax.legend(handles=handles, fontsize=8.5, loc="upper left", ncol=4)
ax.set_xlim(-24, len(window) + 1)
ax.set_ylim(low - 5.2 * height, window["high"].max() * 1.03)
ax.set_yticks([v for v in range(230, 305, 10) if v >= low])
ax.set_title("实验一：SPY 日线 2018-01 至 2019-06，手工标注和 talab 自动标注（过渡不分方向）", fontsize=11.5)
ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig(out / "lab.png"); plt.close(fig)
print("ok")
