"""生成第 25 篇的插图：python 25_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 25_derivatives.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("25_derivatives.py").read_text(encoding="utf-8"), ns)
close, oi_value, daily_funding = ns["close"], ns["oi_value"], ns["daily_funding"]
funding, premium, metrics, perp = ns["funding"], ns["premium"], ns["metrics"], ns["perp"]
V, DAY, hourly, events = ns["V"], ns["DAY"], ns["hourly"], ns["events"]
oi_hourly, past, low = ns["oi_hourly"], ns["past"], ns["low"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")


def three_panel(window, title, mark=None, extra=None):
    fig, axes = plt.subplots(3, 1, figsize=(11.5, 7.2), dpi=150, sharex=True,
                             gridspec_kw={"height_ratios": [3, 2, 2]})
    n = len(window)
    axes[0].plot(range(n), close.reindex(window).to_numpy(), color="#333333", linewidth=1.4)
    axes[0].set_ylabel("BTCUSDT 永续（美元）")
    axes[0].set_title(title)
    axes[1].plot(range(n), (oi_value.reindex(window) / 1e8).to_numpy(), color=PURPLE, linewidth=1.4)
    axes[1].set_ylabel("持仓价值（亿美元）")
    axes[2].bar(range(n), (daily_funding.reindex(window) * 365).to_numpy(),
                color=[DOWN if v > 0 else UP for v in daily_funding.reindex(window)])
    axes[2].axhline(3 * 0.0001 * 365, color=GRAY, linewidth=1.0, linestyle=":",
                label="0.01%/8 小时的地板（折年化 10.95%）")
    axes[2].set_ylabel("资金费率折年化")
    axes[2].yaxis.set_major_formatter(percent)
    axes[2].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.25)
    if mark is not None:
        k = list(window).index(mark)
        for ax in axes:
            ax.axvline(k, color="black", linewidth=1.0, linestyle="--")
    if extra is not None:
        extra(axes, window, n)
    step = max(1, n // 10)
    axes[2].set_xticks(range(0, n, step))
    axes[2].set_xticklabels([str(d.date())[5:] for d in window[::step]])
    fig.tight_layout()
    return fig


# 1. 决策点
window = close.loc["2021-02-20":"2021-04-13"].index
fig = three_panel(window, "2021-04-13 收盘：价格新高、持仓量新高、资金费率年化 108%")
fig.axes[0].annotate(f"{close[DAY]:,.0f}\n（+6.2%，历史新高）", xy=(len(window) - 1, close[DAY]),
                     xytext=(len(window) - 16, close[DAY] * 0.94), fontsize=10,
                     arrowprops=dict(arrowstyle="->", color="black"))
fig.axes[1].annotate(f"{oi_value[DAY] / 1e8:.1f} 亿", xy=(len(window) - 1, oi_value[DAY] / 1e8),
                     xytext=(len(window) - 14, oi_value[DAY] / 1e8 * 0.86), fontsize=10, color=PURPLE,
                     arrowprops=dict(arrowstyle="->", color=PURPLE))
fig.savefig(out / "decision.png"); plt.close(fig)

# 2. 揭晓
window = close.loc["2021-02-20":"2021-06-30"].index


def mark_crash(axes, window, n):
    crash = pd.Timestamp("2021-04-18", tz="UTC")
    k = list(window).index(crash)
    axes[0].annotate("4/18：单日 -6.6%", xy=(k, close[crash]), xytext=(k + 6, close[crash] * 1.16),
                     fontsize=9.5, color=DOWN, arrowprops=dict(arrowstyle="->", color=DOWN))
    axes[1].annotate("持仓量一天掉 25%", xy=(k, oi_value[crash] / 1e8),
                     xytext=(k + 6, oi_value[crash] / 1e8 * 1.5), fontsize=9.5, color=DOWN,
                     arrowprops=dict(arrowstyle="->", color=DOWN))


fig = three_panel(window, "决策点之后：12 天 -22.9%，到 7 月最低 -53.2%",
                  mark=DAY, extra=mark_crash)
fig.savefig(out / "reveal.png"); plt.close(fig)

# 3. 持仓量不是成交量
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=150)
ax = axes[0]
sub = close.loc["2021-04-12":"2021-04-22"].index
k = np.arange(len(sub))
ax.bar(k - 0.2, (perp["quote_volume"].reindex(sub) / 1e8).to_numpy(), 0.4, color=BLUE, label="当日成交额")
ax.bar(k + 0.2, (oi_value.reindex(sub) / 1e8).to_numpy(), 0.4, color=PURPLE, label="收盘持仓价值")
ax.set_xticks(k)
ax.set_xticklabels([str(d.date())[5:] for d in sub], rotation=45, fontsize=8)
ax.set_ylabel("亿美元")
ax.set_title("2021 年 4 月：成交额翻倍的同一天，持仓量掉了四分之一")
ax.legend(fontsize=9); ax.grid(alpha=0.25, axis="y")
ax = axes[1]
turnover = (perp["quote_volume"] / oi_value).dropna()
ax.plot(turnover.index, turnover.to_numpy(), color=BLUE, linewidth=0.7, alpha=0.8)
ax.axhline(turnover.median(), color=ORANGE, linewidth=1.4, label=f"中位数 {turnover.median():.1f} 倍")
ax.set_yscale("log")
ax.set_yticks([0.5, 1, 2, 5, 10, 20])
ax.set_yticklabels(["0.5", "1", "2", "5", "10", "20"])
ax.set_ylabel("当日成交额 ÷ 收盘持仓价值（倍，对数）")
ax.set_title("整个持仓量每天被换手几遍")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "oi_volume.png"); plt.close(fig)

# 4. 资金费率的公式
average = premium.resample("8h", label="right", closed="right").mean()
average.index = average.index.round("h")
joined = pd.concat([average.rename("premium"), funding.rename("funding")], axis=1).dropna()
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
ax = axes[0]
ax.scatter(joined["premium"] * 100, joined["funding"] * 100, s=5, alpha=0.25, color=BLUE)
grid = np.linspace(-0.4, 0.4, 400)
theory = np.clip(grid / 100 + np.clip(V.INTEREST_RATE - grid / 100, -V.CLAMP, V.CLAMP), -V.CAP, V.CAP) * 100
ax.plot(grid, theory, color=DOWN, linewidth=1.8, label="公式：溢价 + clamp(0.01% - 溢价, ±0.05%)")
ax.axvspan(-0.04, 0.06, color=GREEN, alpha=0.10)
ax.text(0.01, -0.15, "这一段里\n费率恒等于 0.01%", ha="center", fontsize=9, color=GREEN)
ax.set_xlim(-0.4, 0.4); ax.set_ylim(-0.35, 0.35)
ax.set_xlabel("这 8 小时的平均溢价指数（%）")
ax.set_ylabel("官方结算的资金费率（%）")
ax.set_title("资金费率不是「市场情绪」，是一条分段函数")
ax.legend(fontsize=8.5); ax.grid(alpha=0.25)
ax = axes[1]
recomputed = V.funding_from_premium(premium)
checked = pd.concat([funding.rename("a"), recomputed.rename("b")], axis=1).dropna()
error = (checked["b"] - checked["a"]).abs()
simple = np.clip(average + np.clip(V.INTEREST_RATE - average, -V.CLAMP, V.CLAMP), -V.CAP, V.CAP)
plain_error = (simple.reindex(checked.index) - checked["a"]).abs()
bins = np.logspace(-9, -2, 60)
ax.hist(plain_error.clip(1e-9), bins=bins, color=GRAY, alpha=0.7, label=f"简单平均：中位 {plain_error.median():.1e}")
ax.hist(error.clip(1e-9), bins=bins, color=BLUE, alpha=0.8, label=f"时间加权：中位 {error.median():.1e}")
ax.set_xscale("log")
ax.set_xticks([1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3])
ax.set_xticklabels(["完全一致", "1e-8", "1e-7", "1e-6", "1e-5", "1e-4", "1e-3"], fontsize=8.5)
ax.set_xlabel("重算值和官方结算值的差")
ax.set_ylabel("结算次数")
ax.set_title(f"用公开数据重算 {len(checked):,} 次结算，90% 的误差小于 1e-5")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "funding_formula.png"); plt.close(fig)

# 5. 极端资金费率之后
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
ax = axes[0]
forward20 = close.shift(-20) / close - 1
groups = [("资金费率最低 5%", (daily_funding <= daily_funding.quantile(.05)).fillna(False), UP),
          ("资金费率最高 5%", (daily_funding >= daily_funding.quantile(.95)).fillna(False), DOWN),
          ("全部日子", None, GRAY)]
for label, mask, color in groups:
    values = forward20[mask].dropna() if mask is not None else forward20.dropna()
    order = np.sort(values)
    ax.plot(order, np.arange(1, len(order) + 1) / len(order), color=color, linewidth=1.8,
            label=f"{label}：n={len(order)}，平均 {values.mean():+.1%}")
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlim(-0.4, 0.6)
ax.xaxis.set_major_formatter(percent)
ax.yaxis.set_major_formatter(percent)
ax.set_xlabel("之后 20 天的收益")
ax.set_ylabel("累计比例")
ax.set_title("信息全在负费率那一边")
ax.legend(fontsize=9, loc="lower right"); ax.grid(alpha=0.25)
ax = axes[1]
starts = (low & ~low.shift(1, fill_value=False))
table = pd.DataFrame({"年": close.index.year, "r": forward20})[starts.to_numpy()].dropna()
everyone = pd.DataFrame({"年": close.index.year, "r": forward20}).dropna()
years = sorted(table["年"].unique())
width = 0.38
x = np.arange(len(years))
ax.bar(x - width / 2, [table[table["年"] == y]["r"].mean() for y in years], width, color=UP,
       label="负费率段首之后 20 天")
ax.bar(x + width / 2, [everyone[everyone["年"] == y]["r"].mean() for y in years], width, color=GRAY,
       label="同年全样本")
for k, y in enumerate(years):
    ax.text(k - width / 2, 0.005, f"{len(table[table['年'] == y])}", ha="center", fontsize=8, color="white")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(x); ax.set_xticklabels(years)
ax.yaxis.set_major_formatter(percent)
ax.set_ylabel("之后 20 天的平均收益")
ax.set_title("按年拆开：不是只靠 2020–2021")
ax.legend(fontsize=9); ax.grid(alpha=0.25, axis="y")
fig.tight_layout(); fig.savefig(out / "funding_after.png"); plt.close(fig)

# 6. 多空比
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=150)
ax = axes[0]
ratio = V.align(metrics["大户持仓多空比"], close.index)
ax.plot(close.index, ratio.to_numpy(), color=PURPLE, linewidth=0.7, alpha=0.85)
ax.axhline(1, color="black", linewidth=1.0, label="1.0：大户净多净空相等")
ax.axhline(ratio.quantile(.9), color=DOWN, linewidth=1.0, linestyle="--", label=f"最高十分位 {ratio.quantile(.9):.2f}")
ax.axhline(ratio.quantile(.1), color=UP, linewidth=1.0, linestyle="--", label=f"最低十分位 {ratio.quantile(.1):.2f}")
ax.set_ylabel("大户持仓多空比")
ax.set_title("2022 年的数据缺了大半——唯一的熊年")
ax.legend(fontsize=8.5); ax.grid(alpha=0.25)
ax = axes[1]
labels, values, controls = [], [], []
for column in ["大户持仓多空比", "账户数多空比", "主动买卖比"]:
    series = V.align(metrics[column], close.index)
    for name, mask in [("最高十分位", series >= series.quantile(.9)), ("最低十分位", series <= series.quantile(.1))]:
        mask = mask.fillna(False)
        first = mask & ~mask.shift(1, fill_value=False)
        lower, upper = past[mask].quantile(.1), past[mask].quantile(.9)
        control = (past >= lower) & (past <= upper) & ~mask & series.notna()
        labels.append(f"{column}\n{name}")
        values.append(forward20[first].dropna().mean())
        controls.append(forward20[control].dropna().mean())
x = np.arange(len(labels))
ax.bar(x - 0.2, values, 0.4, color=BLUE, label="这一组之后 20 天")
ax.bar(x + 0.2, controls, 0.4, color=GRAY, label="同样涨跌幅的对照组")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5)
ax.yaxis.set_major_formatter(percent)
ax.set_ylabel("之后 20 天的平均收益")
ax.set_title("控制住「之前涨跌了多少」之后，只剩一格还站着")
ax.legend(fontsize=9); ax.grid(alpha=0.25, axis="y")
fig.tight_layout(); fig.savefig(out / "ratios.png"); plt.close(fig)

# 7. 去杠杆事件
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=150)
ax = axes[0]
span = range(-24, 49)
price_path, oi_path = [], []
index = hourly.index
prices, interests = hourly["close"].to_numpy(), oi_hourly.where(oi_hourly > 0).to_numpy()
positions = [index.get_loc(t) for t in index[events]]
for offset in span:
    base = [p for p in positions if 0 <= p + offset < len(index)]
    picked = [p + offset for p in base]
    price_path.append(np.nanmedian(prices[picked] / prices[base] - 1))
    oi_path.append(np.nanmedian(interests[picked] / interests[base] - 1))
ax.plot(list(span), np.array(price_path) * 100, color="#333333", linewidth=1.8, label="价格")
ax.plot(list(span), np.array(oi_path) * 100, color=PURPLE, linewidth=1.8, label="持仓价值")
ax.axvline(0, color=DOWN, linewidth=1.2, linestyle="--")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xlabel("离事件多少小时")
ax.set_ylabel("相对事件时刻的中位变化（%）")
ax.set_title(f"{int(events.sum())} 次去杠杆前后的中位路径")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
ax = axes[1]
forward = hourly["close"].shift(-24 * 7) / hourly["close"] - 1
picked, everyone = forward[events].dropna(), forward.dropna()
bins = np.linspace(-0.3, 0.3, 60)
ax.hist(everyone.clip(-0.3, 0.3), bins=bins, density=True, color=GRAY, alpha=0.6,
        label=f"全样本：平均 {everyone.mean():+.2%}")
ax.hist(picked.clip(-0.3, 0.3), bins=bins, density=True, color=PURPLE, alpha=0.7,
        label=f"去杠杆之后：平均 {picked.mean():+.2%}")
ax.axvline(0, color="black", linewidth=0.8)
ax.xaxis.set_major_formatter(percent)
ax.set_xlabel("之后 7 天的收益")
ax.set_ylabel("密度")
ax.set_title("差别有，但很小")
ax.legend(fontsize=9); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(out / "deleveraging.png"); plt.close(fig)
print("图已写入", out)
