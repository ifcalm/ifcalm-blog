"""生成第 20 篇的插图：python 20_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 20_sessions.py（整段执行，不打印输出），避免两份代码不一致。
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
    exec(Path(__file__).with_name("20_sessions.py").read_text(encoding="utf-8"), ns)
minute, hour, day, spy, aapl = ns["minute"], ns["hour"], ns["day"], ns["spy"], ns["aapl"]
stop, mainline, SS = ns["stop"], ns["mainline"], ns["SS"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")

# 1. 决策点：那一夜的分钟线
window = minute.loc["2024-04-13 19:30":"2024-04-13 21:00"]
fig, (ax, bx) = plt.subplots(2, 1, figsize=(11.5, 6.4), dpi=150, sharex=True, height_ratios=[3, 1])
for x, (o, h, l, c) in enumerate(window[["open", "high", "low", "close"]].to_numpy()):
    color = UP if c >= o else DOWN
    ax.vlines(x, l, h, color=color, linewidth=0.8)
    ax.add_patch(Rectangle((x - 0.4, min(o, c)), 0.8, max(abs(c - o), 1e-9), facecolor=color, edgecolor=color))
ax.axhline(stop, color=PURPLE, linestyle="--", linewidth=1.4)
ax.text(1, stop, f" 主线 v1 的止损价 {stop:,.0f}", color=PURPLE, fontsize=9, va="bottom")
touched = list(window.index).index(pd.Timestamp("2024-04-13 20:07", tz="UTC"))
ax.annotate(f"20:07 UTC（北京时间周日 04:07）\n这一分钟从 63,476 跌到 62,000\n成交 39,578 笔",
            (touched, stop), textcoords="offset points", xytext=(-250, 60), fontsize=9,
            arrowprops={"arrowstyle": "->", "color": "#555"})
ax.annotate(f"最低 {window['low'].min():,.0f}", (int(np.argmin(window["low"].to_numpy())), window["low"].min()),
            textcoords="offset points", xytext=(70, 20), fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
ax.grid(alpha=0.25)
ax.set_ylabel("BTCUSDT")
ax.set_title("2024-04-13 周六晚上（UTC），伊朗向以色列发射无人机的消息传出后的 90 分钟", fontsize=12)
bx.bar(range(len(window)), window["quote_volume"] / 1e6, color=GRAY)
bx.set_ylabel("成交额\n（百万美元 / 分钟）", fontsize=9)
ticks = [k for k in range(len(window)) if window.index[k].minute % 10 == 0]
bx.set_xticks(ticks)
bx.set_xticklabels([window.index[k].strftime("%H:%M") for k in ticks], fontsize=9)
bx.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 揭晓：日线
bars = day.loc["2024-03-01":"2024-06-30"]
where = {x: k for k, x in enumerate(bars.index)}
fig, ax = plt.subplots(figsize=(11.5, 5.4), dpi=150)
for x, (o, h, l, c) in enumerate(bars[["open", "high", "low", "close"]].to_numpy()):
    color = UP if c >= o else DOWN
    ax.vlines(x, l, h, color=color, linewidth=0.9)
    ax.add_patch(Rectangle((x - 0.35, min(o, c)), 0.7, max(abs(c - o), 1e-9), facecolor=color, edgecolor=color))
ax.hlines(stop, where[pd.Timestamp("2024-04-09", tz="UTC")], len(bars) - 1, color=PURPLE, linestyle="--", linewidth=1.2)
for when, text, dx, dy in [("2024-04-09", "买入 71,620", -30, 40), ("2024-04-13", "周末插针\n止损 62,272", -70, -70),
                           ("2024-04-17", "4 月 17 日\n收盘 61,277", 10, -60), ("2024-05-16", "规则买回\n66,207", -10, 55)]:
    k = where[pd.Timestamp(when, tz="UTC")]
    y = bars["high"].iloc[k] if dy > 0 else bars["low"].iloc[k]
    ax.annotate(text, (k, y), textcoords="offset points", xytext=(dx, dy), ha="center", fontsize=9,
                arrowprops={"arrowstyle": "->", "color": "#555"})
ticks = [k for k, x in enumerate(bars.index) if x.day in (1, 15)]
ax.set_xticks(ticks)
ax.set_xticklabels([bars.index[k].strftime("%m-%d") for k in ticks], fontsize=9)
ax.grid(alpha=0.25)
ax.set_title("揭晓：止损之后的两个月（BTC 日线）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 3. 一天里的每个小时
by_hour = ns["by_hour"]
fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.5, 4.6), dpi=150)
colors = [BLUE if h < 7 else UP if h < 13 else ORANGE if h < 21 else GRAY for h in by_hour.index]
ax.bar(by_hour.index, by_hour["成交额占比"], color=colors)
ax.axhline(1 / 24, color="black", linewidth=1, linestyle="--")
ax.text(0.2, 1 / 24 * 1.03, "平均水平 1/24", fontsize=9)
ax.set_xticks(range(0, 24, 2))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1%}"))
ax.set_xlabel("UTC 小时（蓝=亚洲，绿=欧洲，橙=美国，灰=美股收盘后）"); ax.set_ylabel("占全天成交额")
ax.set_title("BTC 一天的成交额分布", fontsize=11)
ax.grid(alpha=0.25, axis="y")
bx.plot(by_hour.index, by_hour["平均振幅"], color=PURPLE, marker="o", markersize=4)
bx.axvspan(13, 21, color=ORANGE, alpha=0.12)
bx.text(17, by_hour["平均振幅"].min(), "美股交易时段", ha="center", fontsize=9, color="#b35c00")
bx.set_xticks(range(0, 24, 2))
bx.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.2%}"))
bx.set_xlabel("UTC 小时"); bx.set_ylabel("平均振幅 (高-低)÷开盘")
bx.set_title("波动也跟着时段走", fontsize=11)
bx.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "hourly.png"); plt.close(fig)

# 4. 美股：隔夜和日内
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), dpi=150)
for axis, (name, df) in zip(axes, [("SPY", spy), ("AAPL", aapl)]):
    overnight = (1 + (df["open"] / df["close"].shift(1) - 1).fillna(0)).cumprod()
    intraday = (1 + (df["close"] / df["open"] - 1).fillna(0)).cumprod()
    total = df["close"] / df["close"].iloc[0]
    axis.plot(df.index, total, color="black", linewidth=1.4, label="一直持有")
    axis.plot(df.index, overnight, color=BLUE, linewidth=1.4, label="只吃隔夜（收盘买、开盘卖）")
    axis.plot(df.index, intraday, color=ORANGE, linewidth=1.4, label="只吃日内（开盘买、收盘卖）")
    axis.set_yscale("log")
    axis.get_yaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}×"))
    axis.set_title(name, fontsize=11)
    axis.grid(alpha=0.25)
    axis.legend(fontsize=8, loc="upper left")
fig.suptitle("把十年的涨幅拆成「隔夜」和「日内」两半（不算成本）", fontsize=12)
fig.tight_layout(); fig.savefig(out / "overnight.png"); plt.close(fig)

# 5. 事件前后
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
for (name, df, events, offset), color in zip(
        [("SPY 遇上 FOMC", spy, ns["fomc"], 0), ("BTC 遇上 FOMC", day, ns["fomc"], 0),
         ("AAPL 遇上自己的财报", aapl, ns["earnings"], 1)], [BLUE, ORANGE, PURPLE]):
    swing = (df["high"] - df["low"]) / df["open"]
    study = SS.event_study(swing, events, before=3, after=3, offset=offset)
    ax.plot(study.index, study["中位数"] / swing.median(), color=color, marker="o", markersize=5,
            label=f"{name}（{int(study['事件数'].iloc[0])} 次）")
ax.axhline(1, color="black", linewidth=1, linestyle="--")
ax.text(-3, 1.02, "平常日子的水平", fontsize=9)
ax.set_xticks(range(-3, 4))
ax.set_xlabel("离事件几个交易日（0 = 公布当天；财报是盘后公布，0 指的是第二天）")
ax.set_ylabel("当天振幅 ÷ 平常的中位振幅")
ax.set_title("事件前后，一天能走多远", fontsize=12)
ax.grid(alpha=0.25); ax.legend(fontsize=9)
fig.tight_layout(); fig.savefig(out / "events.png"); plt.close(fig)

# 6. 止损：插针打掉的那些
fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=150)
labels, width = ["当天收盘", "5 天内", "20 天内"], 0.25
for k, (name, df, color) in enumerate([("SPY", spy, BLUE), ("AAPL", aapl, ORANGE), ("BTC", day, PURPLE)]):
    _, _, trades = mainline(df)
    stops = trades[trades["原因"].str.startswith("止损")]
    shares = []
    for horizon in [0, 5, 20]:
        hits = [bool((df["close"].iloc[df.index.get_loc(when): df.index.get_loc(when) + horizon + 1] > level).any())
                for when, level in zip(stops["卖出日"], stops["止损价"])]
        shares.append(np.mean(hits))
    ax.bar(np.arange(3) + k * width - width, shares, width, color=color, label=f"{name}（{len(stops)} 次止损）")
ax.set_xticks(range(3)); ax.set_xticklabels(labels)
ax.yaxis.set_major_formatter(percent)
ax.set_ylim(0, 1.05)
ax.set_ylabel("价格回到止损价上方的比例")
ax.set_title("止损之后，价格多久会回到止损价上方", fontsize=11)
ax.grid(alpha=0.25, axis="y"); ax.legend(fontsize=9, loc="lower right")
fig.tight_layout(); fig.savefig(out / "stops.png"); plt.close(fig)

# 7. 同一笔交易，两种触发方式的差
fig, bx = plt.subplots(figsize=(7.5, 4.6), dpi=150)
for name, df, color in [("SPY", spy, BLUE), ("AAPL", aapl, ORANGE), ("BTC", day, PURPLE)]:
    _, _, a = mainline(df)
    _, _, b = mainline(df, trigger="close")
    paired = a.set_index("买入日")["收益"].to_frame("v1").join(b.set_index("买入日")["收益"].to_frame("v2"), how="inner")
    diff = (paired["v2"] - paired["v1"]).sort_values().to_numpy()
    bx.plot(np.linspace(0, 1, len(diff)), diff, marker="o", markersize=3, color=color, label=name)
bx.axhline(0, color="black", linewidth=1)
bx.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0%}"))
bx.set_xlabel("按差值从小到大排的分位")
bx.set_ylabel("收盘触发 - 盘中触发（同一笔交易）")
bx.set_title("多数交易上收盘触发略差，少数几笔大幅更好", fontsize=11)
bx.xaxis.set_major_formatter(percent)
bx.grid(alpha=0.25); bx.legend(fontsize=9, loc="upper left")
fig.tight_layout(); fig.savefig(out / "stop-trigger.png"); plt.close(fig)
print("ok")
