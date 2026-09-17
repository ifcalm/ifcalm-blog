"""一根一根地看：从 BTC 日线里随机挑一段，隐藏日期、价格换算成从 100 开始，每次多露出一根 K 线，让你做决定。

在 talab 项目根目录运行：python 11_replay.py [种子] [先露出几根] [一共做几次决定]
每一步把图存成 replay.png（用会自动刷新的看图软件打开），然后在终端输入：
    l 做多    s 做空    直接回车 不动    q 提前结束
结束后揭晓这段行情的日期，按第 11 篇的方法给每个做多、做空的决定打分，并列出同一段时间里 talab 的状态和信号。
"""
import glob
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from talab import data as D, plot as P, structure as X

defaults = [0, 120, 40]
seed, shown, steps = [int(v) for v in sys.argv[1:4]] + defaults[len(sys.argv[1:4]):]
cols = ["open", "high", "low", "close"]
P.use_chinese_font()
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
rng = np.random.default_rng(seed)
start = int(rng.integers(100, len(day) - shown - steps - 20))   # 前面留 100 根算结构，后面留 20 根打分
segment = day.iloc[start:start + shown + steps]
scale = 100 / segment["close"].iloc[0]


def draw(bars, path="replay.png"):
    """只画已经收盘的 K 线，横轴是第几根，不显示日期。"""
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    for x, (o, h, l, c) in enumerate(bars[cols].to_numpy() * scale):
        color = "#26a69a" if c >= o else "#ef5350"
        ax.vlines(x, l, h, color=color, linewidth=0.8)
        ax.add_patch(plt.Rectangle((x - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-6), color=color))
    ax.set_xlim(-1, shown + steps + 1)
    ax.autoscale(axis="y")
    ax.set_title(f"第 {len(bars)} 根收盘：{bars['close'].iloc[-1] * scale:.2f}")
    ax.grid(alpha=0.3)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


decisions = []
for k in range(shown, shown + steps):
    draw(segment.iloc[:k])
    answer = input(f"第 {k} 根收盘 {segment['close'].iloc[k - 1] * scale:.2f}，l 做多 / s 做空 / 回车不动 / q 结束：")
    if answer.strip() == "q":
        break
    if answer.strip() in ("l", "s"):
        decisions.append((segment.index[k - 1], 1 if answer.strip() == "l" else -1))

c = day["close"]
swings = X.zigzag(c, 0.10)
levels = X.trend_state(swings, c, c)
state = X.market_state(levels, c)
atr = X.wilder_smooth(X.true_range(day["high"], day["low"], c), 14)
signals = X.entries(c, day["high"], day["low"], swings, levels, state)

first, last = segment.index[shown - 1], segment.index[shown + steps - 1]
print(f"\n这段行情是 {segment.index[0].date()} 到 {last.date()}，你从 {first.date()} 那根开始做决定")
if decisions:
    times, directions = zip(*decisions)
    result = pd.DataFrame({"time": times, "方向": ["做多" if d == 1 else "做空" for d in directions],
                           "状态": state.reindex(list(times)).to_numpy(),
                           "先碰到顺向的 2 ATR 线": X.first_passage(c, day["high"], day["low"], atr, times, directions)})
    print(result.to_string(index=False))
    print(f"打分的 {result.iloc[:, 3].notna().sum()} 次里，顺向 {result.iloc[:, 3].mean():.0%}（没碰到任何一条线的不算）")
inside = signals[(signals["time"] >= first) & (signals["time"] <= last)]
print("同一段时间里 talab 的信号：")
print(inside.assign(level=(inside["level"] * scale).round(2)).to_string(index=False) if len(inside) else "（没有）")
print("状态的变化：")
part = state.loc[first:last]
print(part[part != part.shift()].to_string())
