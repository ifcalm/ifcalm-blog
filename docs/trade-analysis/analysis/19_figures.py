"""生成第 19 篇的插图：python 19_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 19_screening.py（整段执行，不打印输出），避免两份代码不一致。
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
from matplotlib.ticker import FuncFormatter

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(Path(__file__).with_name("19_screening.py").read_text(encoding="utf-8"), ns)
close, btc, zec = ns["close"], ns["btc"], ns["zec"]
features, candidates, forward = ns["features"], ns["candidates"], ns["forward"]
decision, table, horizon = ns["decision"], ns["table"], ns["horizon"]

from talab import plot as P, screen as S

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")

# 1. 决策点：ZEC 和 BTC，从 60 天前算起
window = close.loc["2025-08-20":"2025-11-19", ["ZECUSDT", "BTCUSDT"]]
scaled = window / window.loc["2025-09-20"] * 100
fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
ax.plot(scaled.index, scaled["ZECUSDT"], color=PURPLE, linewidth=1.6, label="ZEC 永续合约")
ax.plot(scaled.index, scaled["BTCUSDT"], color=ORANGE, linewidth=1.6, label="BTC 永续合约")
ax.axvline(pd.Timestamp("2025-09-20", tz="UTC"), color=GRAY, linestyle="--", linewidth=1)
ax.annotate("60 天前：两条线都从 100 出发", (pd.Timestamp("2025-09-20", tz="UTC"), 100),
            textcoords="offset points", xytext=(15, 60), fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
ax.annotate(f"决策点 2025-11-19\nZEC {zec.loc[decision]:.0f}（60 天 +1232%）\nBTC {btc.loc[decision]:,.0f}（-21%）",
            (decision, scaled["ZECUSDT"].iloc[-1]), textcoords="offset points", xytext=(-210, -150), fontsize=9,
            arrowprops={"arrowstyle": "->", "color": "#555"})
ax.set_yscale("log")
ax.set_yticks([50, 100, 200, 400, 800, 1600])
ax.get_yaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
ax.set_ylabel("2025-09-20 = 100（对数坐标）")
ax.grid(alpha=0.25)
ax.legend(fontsize=9, loc="upper left")
ax.set_title("决策点：扫描器排第一的 ZEC，和同期的 BTC", fontsize=12)
fig.tight_layout(); fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 揭晓：决策点之后
after = close.loc["2025-08-20":"2026-08-31", ["ZECUSDT", "BTCUSDT"]]
scaled = after / after.loc["2025-09-20"] * 100
fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
ax.plot(scaled.index, scaled["ZECUSDT"], color=PURPLE, linewidth=1.4, label="ZEC 永续合约")
ax.plot(scaled.index, scaled["BTCUSDT"], color=ORANGE, linewidth=1.4, label="BTC 永续合约")
ax.axvspan(decision, decision + pd.Timedelta(days=horizon), color=DOWN, alpha=0.12)
for when, text, dy in [(decision, f"决策点 {zec.loc[decision]:.0f}", 42),
                       (decision + pd.Timedelta(days=horizon), f"20 天后 {zec.loc[decision + pd.Timedelta(days=horizon)]:.0f}\nZEC -36%，BTC +1%", -80),
                       (zec.idxmax(), f"2026-08-23 最高 {zec.max():.0f}", 30)]:
    ax.annotate(text, (when, scaled["ZECUSDT"].loc[when]), textcoords="offset points", xytext=(-30, dy),
                ha="center", fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
ax.set_yscale("log")
ax.set_yticks([50, 100, 200, 400, 800, 1600, 3200])
ax.get_yaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
ax.set_ylabel("2025-09-20 = 100（对数坐标）")
ax.grid(alpha=0.25)
ax.legend(fontsize=9, loc="upper left")
ax.set_title("揭晓：决策点之后的 20 天，以及之后的九个月", fontsize=12)
fig.tight_layout(); fig.savefig(out / "reveal.png"); plt.close(fig)

# 3. 流动性：成交额的分布和集中度
money = features["成交额"].loc["2026-08-31"].dropna().sort_values(ascending=False)
fig, (ax, bx) = plt.subplots(1, 2, figsize=(12, 4.6), dpi=150)
ax.hist(np.log10(money[money > 0]), bins=40, color=BLUE, alpha=0.75)
ax.axvline(7, color=DOWN, linestyle="--", linewidth=1.2)
ax.text(7.1, ax.get_ylim()[1] * 0.78, f"1000 万美元\n右边 {(money >= 1e7).sum()} 个", color=DOWN, fontsize=9)
ax.set_xticks(range(4, 11))
ax.set_xticklabels(["1 万", "10 万", "100 万", "1000 万", "1 亿", "10 亿", "100 亿"], fontsize=9)
ax.set_xlabel("20 天中位成交额（美元，对数坐标）"); ax.set_ylabel("合约数")
ax.set_title(f"{len(money)} 个还在交易的合约", fontsize=11)
bx.plot(range(1, len(money) + 1), money.cumsum() / money.sum(), color=PURPLE, linewidth=1.6)
bx.axhline(money.nlargest(20).sum() / money.sum(), color=GRAY, linestyle="--", linewidth=1)
bx.annotate(f"成交额最大的 20 个合约\n占全市场的 {money.nlargest(20).sum() / money.sum():.0%}", (20, money.nlargest(20).sum() / money.sum()),
            textcoords="offset points", xytext=(60, -45), fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
bx.set_xscale("log")
bx.set_xticks([1, 2, 5, 10, 20, 50, 100, 200, 500])
bx.get_xaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
bx.yaxis.set_major_formatter(percent)
bx.set_xlabel("按成交额从大到小排，前几个"); bx.set_ylabel("占全市场成交额")
bx.set_title("几百个合约，成交额集中在几十个里", fontsize=11)
bx.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "liquidity.png"); plt.close(fig)

# 4. 相对强度线：XLK 和 SPY
sector = ns["window"][["XLK", "SPY"]]
rs = S.relative_strength(sector["XLK"], sector["SPY"])
fig, (ax, bx) = plt.subplots(2, 1, figsize=(11, 6.4), dpi=150, sharex=True, height_ratios=[2, 1])
scaled = sector / sector.iloc[0] * 100
ax.plot(scaled.index, scaled["XLK"], color=BLUE, linewidth=1.5, label="XLK（科技行业 ETF）")
ax.plot(scaled.index, scaled["SPY"], color=GRAY, linewidth=1.5, label="SPY（标普 500）")
ax.set_ylabel("一年前 = 100"); ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="upper left")
ax.set_title("相对强度线：XLK 除以 SPY", fontsize=12)
bx.plot(rs.index, rs, color=PURPLE, linewidth=1.5)
bx.axhline(100, color=GRAY, linestyle="--", linewidth=1)
bx.fill_between(rs.index, 100, rs, where=rs >= 100, color=UP, alpha=0.18)
bx.fill_between(rs.index, 100, rs, where=rs < 100, color=DOWN, alpha=0.18)
bx.set_ylabel("相对强度线"); bx.grid(alpha=0.25)
bx.annotate("线在 100 上方 = 这段时间跑赢 SPY", (rs.index[-60], rs.iloc[-60]), textcoords="offset points",
            xytext=(-250, -40), fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
fig.tight_layout(); fig.savefig(out / "relative-strength.png"); plt.close(fig)

# 5. 横截面动量分组
report = ns["report"]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), dpi=150, sharey=True)
for axis, market in zip(axes, ["BTC 永续合约", "美股 100 只"]):
    rows = report[report["市场"] == market]
    width = 0.8 / len(rows)
    for k, (_, row) in enumerate(rows.iterrows()):
        values = [row[f"第 {g} 组"] for g in range(1, 6)]
        axis.bar(np.arange(5) + k * width - 0.4 + width / 2, values, width, label=f"按过去 {row['回看天数']} 天涨幅排名")
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_xticks(range(5))
    axis.set_xticklabels(["最弱", "2", "3", "4", "最强"])
    axis.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.1%}"))
    axis.set_title(market, fontsize=11)
    axis.grid(alpha=0.25, axis="y")
    axis.legend(fontsize=8)
axes[0].set_ylabel("未来 20 天收益 - 当天全部候选的平均")
fig.suptitle("按相对强度分成五组：哪一组的未来 20 天更好？", fontsize=12)
fig.tight_layout(); fig.savefig(out / "buckets.png"); plt.close(fig)

# 6. 幸存者偏差
alive_today = close.notna().iloc[-1]
days = [d for d in close.index[::horizon] if ns["listed"].loc[d].sum() >= 30]
honest = (1 + forward.where(ns["listed"]).loc[days].mean(axis=1)).cumprod()
survivors = (1 + forward.where(ns["listed"] & alive_today).loc[days].mean(axis=1)).cumprod()
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
ax.plot(honest.index, honest, color=BLUE, linewidth=1.6, label="当时真实的名单（下架的按最后价格离场）")
ax.plot(survivors.index, survivors, color=DOWN, linewidth=1.6, label="只用今天还在交易的名单")
ax.fill_between(honest.index, honest, survivors, color=DOWN, alpha=0.12)
ax.set_yscale("log")
ax.set_ylim(0.45, float(max(honest.max(), survivors.max())) * 1.25)
ax.set_yticks([0.5, 1, 2, 3, 5, 8, 13])
ax.get_yaxis().set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
ax.set_ylabel("等权买入全部候选、每 20 天调一次仓（对数坐标）")
ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="lower left")
ax.set_title("同一个策略，换一份名单：幸存者偏差凭空多出来的收益", fontsize=12)
fig.tight_layout(); fig.savefig(out / "survivorship.png"); plt.close(fig)
print("ok")
