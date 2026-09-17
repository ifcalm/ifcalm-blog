"""生成第 5 篇的插图：python 05_figures.py <输出目录>（在 talab 项目根目录运行）。"""
import glob
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from talab import data as D, plot as P, stats as S

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
GREEN, RED, BLUE, GRAY = "#26a69a", "#ef5350", "#1f77b4", "#888888"

btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl_total = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
rets = {"SPY": S.simple_returns(spy["close"]), "AAPL": S.simple_returns(aapl_total["close"]),
        "BTC": S.simple_returns(btc["close"])}
colors = {"SPY": BLUE, "AAPL": "#ff7f0e", "BTC": "#9467bd"}


def normal_pdf(x, m, s):
    return np.exp(-0.5 * ((x - m) / s) ** 2) / (s * math.sqrt(2 * math.pi))


# 1. 决策点
fig, ax, av = P.plot_candles(btc.loc["2022-04-01":"2022-06-12"], title="BTCUSDT 日线，2022-04-01 至 2022-06-12（停在这里）")
fig.savefig(out / "decision-point.png"); plt.close(fig)

# 2. 你手里的正态模型
r = rets["BTC"]
last_year = r.loc[:"2022-06-12"].iloc[-365:]
m, s = last_year.mean(), last_year.std()
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.hist(last_year * 100, bins=60, density=True, color=GRAY, alpha=0.6, label="过去 365 天的日收益率")
xs = np.linspace(-18, 12, 600)
ax.plot(xs, normal_pdf(xs, m * 100, s * 100), color=BLUE, linewidth=2, label=f"正态分布（均值 {m:.2%}，标准差 {s:.2%}）")
ax.axvline(-15, color=RED, linestyle="--")
ax.annotate("跌 15%：正态分布认为约 208 年一次", (-15, 0.02), xytext=(-14.6, 0.06), color=RED, fontsize=10,
            arrowprops={"arrowstyle": "->", "color": RED})
ax.set_xlabel("日收益率（%）"); ax.set_ylabel("密度"); ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax.set_title("2021-06-13 至 2022-06-12，BTC 日收益率的分布")
fig.tight_layout(); fig.savefig(out / "normal-model.png"); plt.close(fig)

# 3. 揭晓
x = btc.loc["2022-04-01":"2022-07-15"]
fig, ax, av = P.plot_candles(x, title="BTCUSDT 日线，2022-04-01 至 2022-07-15",
                             marks=[("2022-06-13", x.loc["2022-06-13", "low"], "6-13 收盘跌 15.4%"),
                                    ("2022-06-18", x.loc["2022-06-18", "low"], "6-18 最低 17,622")])
ax.axvline(list(x.index).index(pd.Timestamp("2022-06-12", tz="UTC")) + 0.5, color=GRAY, linestyle=":")
ax.set_ylim(12000, 49000)
fig.savefig(out / "reveal.png"); plt.close(fig)

# 4. 平方根法则：抛硬币
fig, axes = plt.subplots(1, 4, figsize=(12, 3.4), dpi=150, sharey=False)
for a, n in zip(axes, [1, 4, 16, 64]):
    k = np.arange(n + 1)
    pos = 2 * k - n                                          # 涨 k 天、跌 n−k 天，累计 2k−n 个百分点
    prob = np.array([math.comb(n, i) for i in k]) / 2 ** n
    a.bar(pos, prob, width=1.6, color=BLUE)
    a.set_xlim(-20, 20)
    a.set_title(f"{n} 天：标准差 {math.sqrt(n):.0f}%", fontsize=11)
    a.set_xlabel("累计涨跌（%）")
    a.grid(alpha=0.25)
axes[0].set_ylabel("概率")
fig.suptitle("每天等可能涨 1% 或跌 1%：天数变成 4 倍，宽度只变成 2 倍", fontsize=12)
fig.tight_layout(); fig.savefig(out / "sqrt-time.png"); plt.close(fig)

# 5. 波动率本身在变
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
for k in ["BTC", "AAPL", "SPY"]:
    w = 30 if k == "BTC" else 21
    rv = S.realized_vol(rets[k], w, 365 if k == "BTC" else 252)
    rv.index = rv.index.tz_localize(None) if rv.index.tz is not None else rv.index
    ax.plot(rv.index, rv * 100, color=colors[k], linewidth=1, label=f"{k}（{w} 天滚动）")
ax.set_ylabel("年化波动率（%）"); ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax.set_title("滚动年化波动率：平静和剧烈的时期成片出现")
fig.tight_layout(); fig.savefig(out / "rolling-vol.png"); plt.close(fig)

# 6. BTC 收益率直方图 vs 正态
z = (r - r.mean()) / r.std()
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.hist(z.clip(-8, 8), bins=np.arange(-8, 8.25, 0.25), density=True, color=GRAY, alpha=0.6, label="BTC 全部日收益率（按标准差换算）")
xs = np.linspace(-8, 8, 600)
ax.plot(xs, normal_pdf(xs, 0, 1), color=BLUE, linewidth=2, label="标准正态分布")
ax.set_xlabel("距离均值几个标准差（超过 8 的并入两端）"); ax.set_ylabel("密度")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax.set_title("中间更尖、两肩更瘦、两端更长")
fig.tight_layout(); fig.savefig(out / "btc-histogram.png"); plt.close(fig)

# 7. 尾部概率（对数纵轴）
ks = np.linspace(0, 10, 201)
fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
for k in ["SPY", "AAPL", "BTC"]:
    zz = ((rets[k] - rets[k].mean()) / rets[k].std()).abs().to_numpy()
    frac = np.array([(zz > t).mean() for t in ks])
    ax.step(ks, np.where(frac > 0, frac, np.nan), where="post", color=colors[k], label=k)
ax.plot(ks, [2 * S.NORMAL.cdf(-t) for t in ks], color="black", linestyle="--", label="正态分布")
ax.set_yscale("log"); ax.set_ylim(1e-6, 1.2); ax.set_xlim(0, 10)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: "1" if v >= 1 else f"1/{round(1 / v):,}"))
ax.set_xlabel("k（个标准差）"); ax.set_ylabel("单日涨跌幅超过 k 个标准差的比例")
ax.legend(fontsize=9); ax.grid(alpha=0.25, which="both")
ax.set_title("尾部：k 越大，实际比例和正态分布差得越远")
fig.tight_layout(); fig.savefig(out / "tails-log.png"); plt.close(fig)

# 8. 自相关
fig, axes = plt.subplots(2, 3, figsize=(12, 6), dpi=150)
for j, k in enumerate(["SPY", "AAPL", "BTC"]):
    band = S.autocorr_band(len(rets[k]))
    for i, (series, lags, name) in enumerate([(rets[k], range(1, 21), "收益率"),
                                              (rets[k].abs(), range(1, 121), "收益率的绝对值")]):
        a = axes[i, j]
        ac = S.autocorr(series, list(lags))
        a.bar(ac.index, ac.values, color=colors[k], width=0.8)
        a.axhspan(-band, band, color=GRAY, alpha=0.2)
        a.axhline(0, color="black", linewidth=0.6)
        a.set_title(f"{k}：{name}", fontsize=11)
        a.set_ylim(-0.2, 0.45)
        a.grid(alpha=0.25)
    axes[1, j].set_xlabel("滞后天数")
axes[0, 0].set_ylabel("自相关系数"); axes[1, 0].set_ylabel("自相关系数")
fig.suptitle("灰色带：没有自相关时 95% 的样本落在这个范围里", fontsize=12)
fig.tight_layout(); fig.savefig(out / "acf.png"); plt.close(fig)

# 9. 价格 vs 收益率
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6), dpi=150, sharex=True)
idx = btc.index.tz_localize(None)
a1.plot(idx, btc["close"], color=BLUE, linewidth=1)
a1.set_ylabel("收盘价"); a1.set_title("BTC：价格（上）和日收益率（下）")
a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
a2.plot(r.index.tz_localize(None), r * 100, color=GRAY, linewidth=0.6)
a2.set_ylabel("日收益率（%）")
for a in (a1, a2):
    a.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "price-vs-returns.png"); plt.close(fig)

# 10. 两条独立的随机游走
rng = np.random.default_rng(42)
for _ in range(1000):
    a, b = rng.normal(0, 0.01, (2, 2500))
    pa, pb = 100 * np.exp(np.cumsum(a)), 100 * np.exp(np.cumsum(b))
    if np.corrcoef(pa, pb)[0, 1] > 0.85:
        break
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2), dpi=150)
a1.plot(pa, color=BLUE, linewidth=1, label="价格 A")
a1.plot(pb, color="#ff7f0e", linewidth=1, label="价格 B")
a1.set_title(f"两串互相独立的随机收益率累积出来的价格：相关系数 {np.corrcoef(pa, pb)[0, 1]:.2f}", fontsize=10)
a1.set_xlabel("天"); a1.legend(fontsize=9); a1.grid(alpha=0.25)
a2.scatter(a * 100, b * 100, s=3, color=GRAY)
a2.set_title(f"它们每天的收益率：相关系数 {np.corrcoef(a, b)[0, 1]:.2f}", fontsize=10)
a2.set_xlabel("A 的日收益率（%）"); a2.set_ylabel("B 的日收益率（%）"); a2.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "random-walks.png"); plt.close(fig)
print("done", np.corrcoef(pa, pb)[0, 1], np.corrcoef(a, b)[0, 1])
