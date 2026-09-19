"""生成第 17 篇的插图：python 17_figures.py <输出目录>（在 talab 项目根目录运行）。

数据、统计表直接借用 17_chart_patterns.py（完整执行一遍，不打印输出），避免两份代码不一致。
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
source = Path(__file__).with_name("17_chart_patterns.py").read_text(encoding="utf-8")
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(source, ns)
day, Pt, X = ns["day"], ns["Pt"], ns["X"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
money = FuncFormatter(lambda v, _: f"{v:,.0f}")
percent = FuncFormatter(lambda v, _: f"{v:.0%}")


def draw_candles(axis, bars):
    for x, (o, h, l, c) in enumerate(bars[Pt.OHLC].to_numpy()):
        color = UP if c >= o else DOWN
        axis.vlines(x, l, h, color=color, linewidth=0.8)
        axis.add_patch(Rectangle((x - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-9), facecolor=color, edgecolor=color))


def month_ticks(axis, index):
    ticks = [k for k in range(len(index)) if k == 0 or index[k].month != index[k - 1].month]
    axis.set_xticks(ticks)
    axis.set_xticklabels([index[k].strftime("%Y-%m") for k in ticks], fontsize=9)


def draw_head_and_shoulders(axis, bars, row, extend_to, labels=True):
    where = {t: k for k, t in enumerate(bars.index)}
    names = ["左肩", "颈线点", "头", "颈线点", "右肩"]
    times = [row["left"], row["neck_1"], row["head"], row["neck_2"], row["right"]]
    prices = [bars["close"][x] for x in times]
    axis.plot([where[x] for x in times], prices, color=PURPLE, linewidth=1.2, marker="o", markersize=4)
    if labels:
        for x, p, text in zip(times, prices, names):
            axis.annotate(text, (where[x], p), textcoords="offset points", xytext=(0, 9 if text != "颈线点" else -16),
                          ha="center", fontsize=9, color=PURPLE)
    k1, k2 = where[row["neck_1"]], where[row["neck_2"]]
    slope = (prices[3] - prices[1]) / (k2 - k1)
    xs = np.array([k1, where[extend_to]])
    axis.plot(xs, prices[1] + slope * (xs - k1), color=BLUE, linewidth=1.2, linestyle="--", label="颈线（向右延长）")


# 1. 决策点
t = ns["t"]
bars = day.loc[pd.Timestamp("2024-11-01", tz="UTC"):t]
row = ns["row"]
fig, ax = plt.subplots(figsize=(11, 5.4), dpi=150)
draw_candles(ax, bars)
draw_head_and_shoulders(ax, bars, row, t)
ax.annotate(f"1 月 8 日收盘 95,061\n高出颈线 2.2%", (len(bars) - 1, bars["close"].iloc[-1]), textcoords="offset points",
            xytext=(-130, -70), fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
month_ticks(ax, bars.index)
ax.yaxis.set_major_formatter(money); ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="upper left")
ax.set_title("BTCUSDT 日线，2024-11-01 至 2025-01-08；摆动点用收盘价的 ZigZag 5%", fontsize=12)
fig.tight_layout(); fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 规则示意：玩具例子
toy, found = ns["toy"], ns["toy_found"].iloc[0]
fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
ax.plot(np.arange(len(toy)), toy.to_numpy(), color="black", linewidth=1.2, label="收盘价")
where = {x: k for k, x in enumerate(toy.index)}
line = lambda k: 102 + 0.1 * (k - 16)
xs = np.arange(16, 58)
ax.plot(xs, line(xs), color=BLUE, linestyle="--", linewidth=1.2, label="颈线：过两个颈线点，向右延长")
ax.annotate("", (28, 120), (28, line(28)), arrowprops={"arrowstyle": "<->", "color": ORANGE})
ax.text(28.6, (120 + line(28)) / 2, "高度 16.8", color=ORANGE, fontsize=9)
for k, text, dy in [(10, "左肩 110", 8), (16, "颈线点 102", -16), (28, "头 120", 8), (36, "颈线点 104", -16), (44, "右肩 112", 8)]:
    ax.annotate(text, (k, toy.iloc[k]), textcoords="offset points", xytext=(0, dy), ha="center", fontsize=9)
seen, broken = where[found["confirmed_at"]], where[found["broken_at"]]
ax.plot(seen, toy.iloc[seen], "o", color=GRAY); ax.annotate("第 50 根：跌够 5%，右肩被确认\n收盘 106，颈线 105.4", (seen, toy.iloc[seen]),
                                                            textcoords="offset points", xytext=(30, 60), fontsize=9,
                                                            arrowprops={"arrowstyle": "->", "color": "#555"})
ax.plot(broken, toy.iloc[broken], "o", color=DOWN); ax.annotate("第 51 根：收盘 105 跌破颈线", (broken, toy.iloc[broken]),
                                                              textcoords="offset points", xytext=(15, -25), fontsize=9,
                                                              arrowprops={"arrowstyle": "->", "color": "#555"})
ax.axhline(found["target"], color=DOWN, linestyle=":", linewidth=1)
ax.text(1, found["target"] + 0.4, "量度目标 = 跌破时的颈线 105.5 - 高度 16.8 = 88.7", color=DOWN, fontsize=9)
ax.set_ylim(85, 124); ax.set_xlabel("第几根 K 线"); ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="upper right")
ax.set_title("把头肩顶写成规则：五个摆动点、一条颈线、一个高度", fontsize=12)
fig.tight_layout(); fig.savefig(out / "rules.png"); plt.close(fig)

# 3. 调参数：同一段行情，三个阈值
segment = day.loc["2024-10-15":"2025-02-15"]
fig, axes = plt.subplots(3, 1, figsize=(11, 8.4), dpi=150, sharex=True)
for axis, threshold in zip(axes, [0.03, 0.05, 0.08]):
    close = day["close"]
    sw = X.zigzag(close, threshold)
    sw = sw[(sw["time"] >= segment.index[0]) & (sw["time"] <= segment.index[-1])]
    axis.plot(np.arange(len(segment)), segment["close"].to_numpy(), color=GRAY, linewidth=1)
    where = {x: k for k, x in enumerate(segment.index)}
    axis.plot([where[x] for x in sw["time"]], sw["price"], color=BLUE, linewidth=1.2, marker="o", markersize=3.5)
    found = Pt.head_and_shoulders(close, X.zigzag(close, threshold))
    found = found[(found["left"] >= segment.index[0]) & (found["right"] <= segment.index[-1])]
    for r in found.to_dict("records"):
        draw_head_and_shoulders(axis, segment, r, min(r["broken_at"] if pd.notna(r["broken_at"]) else segment.index[-1],
                                                      segment.index[-1]), labels=False)
    axis.set_title(f"ZigZag {threshold:.0%}：{len(sw)} 个摆动点，这一段找到 {len(found)} 个头肩顶", fontsize=11)
    axis.yaxis.set_major_formatter(money); axis.grid(alpha=0.25)
month_ticks(axes[-1], segment.index)
fig.suptitle("同一段 BTC 日线，换一个 ZigZag 阈值，形态就出现或消失", fontsize=12)
fig.tight_layout(); fig.savefig(out / "params.png"); plt.close(fig)

# 4. 揭晓
pattern = ns["pattern"]
bars = day.loc["2024-11-01":"2025-03-15"]
fig, ax = plt.subplots(figsize=(11, 5.6), dpi=150)
draw_candles(ax, bars)
draw_head_and_shoulders(ax, bars, pattern, pd.Timestamp("2025-03-15", tz="UTC"))
where = {x: k for k, x in enumerate(bars.index)}
ax.axhline(pattern["target"], color=DOWN, linestyle=":", linewidth=1)
ax.text(2, pattern["target"] + 600, f"量度目标 {pattern['target']:,.0f}", color=DOWN, fontsize=9)
ax.axhline(pattern["right_price"], color=GRAY, linestyle=":", linewidth=1)
ax.text(2, pattern["right_price"] + 600, f"右肩 {pattern['right_price']:,.0f}（教科书的止损位）", color=GRAY, fontsize=9)
for when, text, dx, dy in [("2025-01-09", "1 月 9 日\n收盘跌破颈线", -40, -60), ("2025-01-20", "1 月 20 日\n盘中 109,588 历史新高", 70, 12),
                           ("2025-03-10", "3 月 10 日\n收盘 78,596 到达目标", -60, -10)]:
    k = where[pd.Timestamp(when, tz="UTC")]
    y = bars["high"].iloc[k] if dy > 0 else bars["low"].iloc[k]
    ax.annotate(text, (k, y), textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=9,
                arrowprops={"arrowstyle": "->", "color": "#555"})
month_ticks(ax, bars.index)
lo, hi = ax.get_ylim(); ax.set_ylim(lo, hi + (hi - lo) * 0.1)
ax.yaxis.set_major_formatter(money); ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="lower left")
ax.set_title("揭晓：BTCUSDT 日线，2024-11-01 至 2025-03-15", fontsize=12)
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 5. 「突破才算成立」让胜率虚高
table = ns["table_a"]
table = table[table["数据"].isin(["BTC 日线", "BTC 4 小时线", "BTC 1 小时线"])]
labels = [f"{r.数据}\n{r.形态}" for r in table.itertuples()]
xs = np.arange(len(table))
fig, ax = plt.subplots(figsize=(12, 4.8), dpi=150)
ax.bar(xs - 0.2, table["决策时刻入场 全部候选"], 0.4, color=BLUE, label="右肩确认时入场：全部候选")
ax.bar(xs + 0.2, table["只算后来突破的"], 0.4, color=ORANGE, label="同样的入场，只统计后来突破了颈线的")
ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=8.5)
ax.yaxis.set_major_formatter(percent); ax.set_ylabel("先碰到量度目标的比例")
ax.set_title("只统计「成立」的形态：同样的交易，胜率凭空高出一截", fontsize=12)
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25, axis="y")
fig.tight_layout(); fig.savefig(out / "conditioning.png"); plt.close(fig)

# 6. 三角形和楔形的突破方向：真实价格和打乱的价格
table = ns["table_c"]
table = table[table["数据"].isin(["BTC 4 小时线", "BTC 1 小时线"]) & table["形态"].isin(
    ["上升三角形", "下降三角形", "对称三角形", "上升楔形", "下降楔形", "通道"])]
labels = [f"{r.数据.replace('BTC ', '')}\n{r.形态}" for r in table.itertuples()]
xs = np.arange(len(table))
fig, ax = plt.subplots(figsize=(12, 4.6), dpi=150)
ax.bar(xs - 0.2, table["向上突破"], 0.4, color=BLUE, label="真实的 BTC")
ax.bar(xs + 0.2, table["打乱后 向上突破"], 0.4, color=GRAY, label="把 K 线顺序打乱之后（10 次平均）")
ax.axhline(0.5, color="black", linewidth=0.8)
ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=8.5)
ax.yaxis.set_major_formatter(percent); ax.set_ylabel("向上突破的比例")
ax.set_title("「楔形反向突破」是真的，但随机价格也一样：方向来自识别规则的几何", fontsize=12)
ax.legend(fontsize=9, loc="upper left"); ax.grid(alpha=0.25, axis="y")
fig.tight_layout(); fig.savefig(out / "triangles.png"); plt.close(fig)
print("ok")
