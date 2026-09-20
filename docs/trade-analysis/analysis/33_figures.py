"""生成第 33 篇的插图：python 33_figures.py <输出目录>（在 talab 项目根目录运行）。

数据和统计结果直接借用 33_journal.py（整段执行，不打印输出）。
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
    exec(Path(__file__).with_name("33_journal.py").read_text(encoding="utf-8"), ns)
JN, RP, T, btc, MARKETS = ns["JN"], ns["RP"], ns["T"], ns["btc"], ns["MARKETS"]
turtles, mains, account_returns = ns["turtles"], ns["mains"], ns["account_returns"]
trades, curve, worst = ns["trades"], ns["curve"], ns["worst"]
first, seventh, gap, TRIALS = ns["first"], ns["seventh"], ns["gap"], ns["TRIALS"]

from talab import plot as P

P.use_chinese_font()
plt.rcParams["axes.unicode_minus"] = False
UP, DOWN, BLUE, ORANGE, GRAY, PURPLE, GREEN = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888", "#7b1fa2", "#2e7d32"
percent = FuncFormatter(lambda v, _: f"{v:.0%}")
money = FuncFormatter(lambda v, _: f"{v / 1000:,.0f}k")
NAMES = list(MARKETS)
COLORS = [BLUE, ORANGE, DOWN]
LAST = int(worst["止"])


def save(fig, name):
    fig.tight_layout()
    fig.savefig(out / name, bbox_inches="tight")
    plt.close(fig)
    print("写出", out / name)


def losing_panel(ax_price, ax_equity, stop_at: int, mark_winner: bool):
    """画同一段行情：上面是价格和每一笔的进出场，下面是账户。"""
    left = pd.Timestamp("2021-09-01", tz="UTC")
    right = trades["出场日"].iloc[stop_at] + pd.Timedelta(days=12)
    price = btc["close"].loc[left:right]
    ax_price.plot(price.index, price.to_numpy(), color=GRAY, linewidth=1.3)
    for i in range(first, stop_at + 1):
        row = trades.iloc[i]
        won = row["R"] > 0
        colour = UP if won else DOWN
        ax_price.plot([row["进场日"], row["出场日"]], [row["平均价"], row["出场价"]],
                      color=colour, linewidth=2.6 if won else 1.6, zorder=4)
        ax_price.scatter([row["进场日"]], [row["平均价"]], marker="^", s=34, color=colour, zorder=5)
        ax_price.scatter([row["出场日"]], [row["出场价"]], marker="x", s=34, color=colour, zorder=5)
    if mark_winner:
        row = trades.iloc[LAST + 1]
        ax_price.annotate(f"{row['进场日'].date()} 买入 {row['第一个单位的价']:,.0f}\n"
                          f"{row['出场日'].date()} 卖出 {row['出场价']:,.0f}\n"
                          f"{row['R']:+.2f}R，{row['盈亏']:+,.0f} 美元",
                          (row["出场日"], row["出场价"]), textcoords="offset points",
                          xytext=(-150, 34), fontsize=9, color=GREEN,
                          arrowprops=dict(arrowstyle="->", color=GREEN, linewidth=1.1))
    ax_price.set_ylabel("BTC 收盘价（美元）")
    ax_price.yaxis.set_major_formatter(money)
    ax_price.grid(alpha=0.25)
    equity = curve.loc[left:right]
    ax_equity.plot(equity.index, equity.to_numpy(), color=PURPLE, linewidth=1.5)
    ax_equity.fill_between(equity.index, equity.to_numpy(), equity.max(),
                           where=equity.to_numpy() < equity.max(), color=DOWN, alpha=0.10)
    ax_equity.set_ylabel("账户权益（美元）")
    ax_equity.yaxis.set_major_formatter(money)
    ax_equity.grid(alpha=0.25)
    return right


# 图 1：决策点——连亏 7 笔，停在这里
fig, axes = plt.subplots(2, 1, figsize=(12.0, 6.4), dpi=150, sharex=True,
                         gridspec_kw={"height_ratios": [2, 1]})
right = losing_panel(axes[0], axes[1], seventh, mark_winner=False)
shown = trades.iloc[first:seventh + 1]
axes[0].set_title(f"海龟法则在 BTC 上连着亏了 7 笔："
                  f"{trades['进场日'].iloc[first].date()} 到 {trades['出场日'].iloc[seventh].date()}，"
                  f"合计 {shown['R'].sum():.2f}R")
peak = curve.loc[:trades["出场日"].iloc[seventh]].max()
now = curve.loc[trades["出场日"].iloc[seventh]]
axes[1].annotate(f"峰值 {peak:,.0f}\n现在 {now:,.0f}（{now / peak - 1:.1%}）",
                 (trades["出场日"].iloc[seventh], now), textcoords="offset points",
                 xytext=(-136, 16), fontsize=9, color=DOWN,
                 arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
axes[1].set_xlim(pd.Timestamp("2021-09-01", tz="UTC"), right)
save(fig, "decision.png")

# 图 2：揭晓——还要再亏 5 笔，然后是那一笔
fig, axes = plt.subplots(2, 1, figsize=(12.0, 6.4), dpi=150, sharex=True,
                         gridspec_kw={"height_ratios": [2, 1]})
right = losing_panel(axes[0], axes[1], LAST + 1, mark_winner=True)
whole = trades.iloc[first:LAST + 1]
axes[0].axvline(trades["出场日"].iloc[seventh], color=GRAY, linestyle="--", linewidth=1.0)
axes[0].annotate("上一张图停在这里", (trades["出场日"].iloc[seventh], price_top := btc["close"].loc[
    pd.Timestamp("2021-09-01", tz="UTC"):right].max()), textcoords="offset points",
    xytext=(-104, -14), fontsize=9, color=GRAY)
axes[0].set_title(f"连亏一共 {int(worst['长度'])} 笔（{whole['R'].sum():.2f}R），"
                  f"紧接着的第 {LAST + 2} 笔是 {trades['R'].iloc[LAST + 1]:+.2f}R")
axes[1].set_xlim(pd.Timestamp("2021-09-01", tz="UTC"), right)
save(fig, "reveal.png")

# 图 3：连亏 12 笔算不算离谱
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.3), dpi=150)
win_rate = float((trades["R"] > 0).mean())
rng = np.random.default_rng(33)
wins = rng.random((TRIALS, len(trades))) < win_rate
longest = np.zeros(TRIALS, dtype=int)
current = np.zeros(TRIALS, dtype=int)
for k in range(len(trades)):
    current = np.where(wins[:, k], 0, current + 1)
    longest = np.maximum(longest, current)
bins = np.arange(longest.min() - 0.5, longest.max() + 1.5)
axes[0].hist(longest, bins=bins, color=BLUE, alpha=0.75, edgecolor="white")
real = JN.longest_streak(trades["R"])
for value, colour, label in [
        (JN.expected_longest(len(trades), 1 - win_rate), ORANGE, "公式给的期望"),
        (float(np.quantile(longest, 0.95)), GRAY, "95% 分位"),
        (real, DOWN, f"真实这一次：{real} 笔")]:
    axes[0].axvline(value, color=colour, linestyle="--", linewidth=1.5, label=f"{label} {value:.1f}"
                    if colour is not DOWN else label)
axes[0].set_xlabel("九年里最长的一段连亏有几笔")
axes[0].set_ylabel(f"{TRIALS:,} 次模拟中的次数")
axes[0].set_title(f"胜率 {win_rate:.1%} 的策略做 {len(trades)} 笔，最长连亏的分布")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.25)

alarm = JN.streak_alarm(len(trades), win_rate, thresholds=tuple(range(2, 21)),
                        trials=TRIALS, seed=33)
axes[1].plot(alarm["门槛（连亏几笔）"], alarm["至少响一次的概率"], color=DOWN, marker="o",
             markersize=3.5, linewidth=1.6)
axes[1].axhline(0.5, color=GRAY, linestyle=":", linewidth=1.0)
hit = alarm.set_index("门槛（连亏几笔）")["至少响一次的概率"]
axes[1].annotate(f"「连亏 7 笔就停」\n在策略完全正常时\n也有 {hit.loc[7]:.0%} 的概率会响",
                 (7, hit.loc[7]), textcoords="offset points", xytext=(20, -12), fontsize=9,
                 color=DOWN, arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
axes[1].set_xlabel("停用规则的门槛（连亏几笔）")
axes[1].set_ylabel("九年里至少响一次的概率")
axes[1].set_title("每一条「连亏几笔就停」规则的误报率")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_xticks(range(2, 21, 2))
axes[1].grid(alpha=0.25)
save(fig, "streaks.png")

# 图 4：正常范围——把同一批交易重排一遍
fig, axes = plt.subplots(2, 3, figsize=(13.0, 6.6), dpi=150)
for column, name in enumerate(NAMES):
    for row, (label, values, unit) in enumerate([
            ("海龟", turtles[name]["交易"]["R"], "R"),
            ("主线 v4", account_returns(mains[name]) * 100, "账户百分点")]):
        ax = axes[row][column]
        sample = JN.shuffled(values, trials=TRIALS, seed=33)["最深回撤"]
        ax.hist(sample, bins=45, color=COLORS[column], alpha=0.65, edgecolor="white")
        actual = JN.normal_range(values, trials=2, seed=33).loc["最深回撤", "这一次"]
        low = float(np.quantile(sample, 0.05))
        ax.axvline(actual, color=DOWN, linewidth=2.0,
                   label=f"真实这一次 {actual:.1f}（比它难看的占 {(sample <= actual).mean():.0%}）")
        ax.axvline(low, color=GRAY, linestyle="--", linewidth=1.3, label=f"95% 分位 {low:.1f}")
        ax.set_title(f"{name}：{label}（{len(pd.Series(values).dropna())} 笔）", fontsize=11)
        ax.set_xlabel(f"重排之后的最深回撤（{unit}）")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
fig.suptitle("同一批交易，换一个发生顺序：你会看到多深的回撤", fontsize=12)
save(fig, "normal.png")

# 图 5：停手规则跳过了什么
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150, gridspec_kw={"width_ratios": [3, 2]})
r = trades["R"].to_numpy(float)
axes[0].plot(range(1, len(r) + 1), np.cumsum(r), color=GRAY, linewidth=2.0,
             label=f"一笔不落：{r.sum():.0f}R")
for (after, pausing), colour in zip([(3, 3), (4, 3)], [BLUE, ORANGE]):
    taken = JN.pause_after_losses(r, after, pausing)
    kept = r * taken
    axes[0].plot(range(1, len(r) + 1), np.cumsum(kept), color=colour, linewidth=1.5,
                 label=f"连亏 {after} 笔停 {pausing} 笔：{kept.sum():.0f}R")
taken = JN.pause_after_losses(r, 4, 3)
skipped = np.flatnonzero(~taken)
big = [i for i in skipped if r[i] > 10]
axes[0].scatter(np.array(big) + 1, np.cumsum(r * taken)[big], marker="v", s=70, color=DOWN, zorder=5)
axes[0].annotate("被规则挡在门外的三笔\n" + "、".join(f"{r[i]:+.0f}R" for i in big),
                 (big[-1] + 1, np.cumsum(r * taken)[big[-1]]), textcoords="offset points",
                 xytext=(-160, 24), fontsize=9, color=DOWN,
                 arrowprops=dict(arrowstyle="->", color=DOWN, linewidth=1.1))
axes[0].set_xlabel("第几笔交易")
axes[0].set_ylabel("累计 R")
axes[0].set_title("BTC 海龟：连亏之后停手，停掉的是什么")
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.25)

rows = []
for name in NAMES:
    values = turtles[name]["交易"]["R"]
    full = float(values.sum())
    rows.append([float(values.to_numpy()[JN.pause_after_losses(values, a, p)].sum()) / full - 1
                 for a, p in [(2, 3), (3, 3), (4, 3), (3, 5)]])
labels = ["连亏 2\n停 3", "连亏 3\n停 3", "连亏 4\n停 3", "连亏 3\n停 5"]
width, spots = 0.26, np.arange(len(labels))
for k, (name, values) in enumerate(zip(NAMES, rows)):
    axes[1].bar(spots + (k - 1) * width, values, width, color=COLORS[k], label=name)
axes[1].axhline(0, color="black", linewidth=0.9)
axes[1].set_xticks(spots)
axes[1].set_xticklabels(labels, fontsize=9)
axes[1].set_ylabel("合计 R 比「一笔不落」差多少")
axes[1].yaxis.set_major_formatter(percent)
axes[1].set_title("三个标的 × 四条规则，十二组里十一组是亏的")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25, axis="y")
save(fig, "pause.png")

# 图 6：手动调整的代价
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), dpi=150)
styles = [("一个字不改", None, 0.0, GRAY, 2.2), ("亏了之后不敢做", "skip_after_loss", 0.0, BLUE, 1.4),
          ("亏了之后加倍", "double_after_loss", 0.0, PURPLE, 1.4),
          ("赚了之后加倍", "double_after_win", 0.0, ORANGE, 1.4),
          ("浮盈 2R 就走", "cap", 2.0, GREEN, 1.4),
          ("要止损了把止损挪远", "widen", 2.0, DOWN, 1.4)]
for label, kind, level, colour, lw in styles:
    changed = r if kind is None else JN.interfere(r, kind, level)
    axes[0].plot(range(1, len(r) + 1), np.cumsum(changed), color=colour, linewidth=lw,
                 label=f"{label}：{changed.sum():.0f}R")
axes[0].set_xlabel("第几笔交易")
axes[0].set_ylabel("累计 R")
axes[0].set_title("BTC 海龟：六种「手动调整」之后的资金曲线")
axes[0].legend(fontsize=8.5)
axes[0].grid(alpha=0.25)

kinds = [(label, kind, level) for label, kind, level, _, _ in styles if kind]
spots = np.arange(len(kinds))
for k, name in enumerate(NAMES):
    values = turtles[name]["交易"]["R"]
    base = float(values.sum())
    heights = [float(JN.interfere(values, kind, level).sum()) / base - 1 for _, kind, level in kinds]
    axes[1].barh(spots + (k - 1) * 0.26, heights, 0.26, color=COLORS[k], label=name)
axes[1].axvline(0, color="black", linewidth=0.9)
axes[1].set_yticks(spots)
axes[1].set_yticklabels([label for label, _, _ in kinds], fontsize=9)
axes[1].invert_yaxis()
axes[1].set_xlabel("合计 R 比「一个字不改」差多少")
axes[1].xaxis.set_major_formatter(percent)
axes[1].set_title("三个标的：只有「加倍」是赚的，代价是回撤翻倍")
axes[1].legend(fontsize=9)
axes[1].grid(alpha=0.25, axis="x")
save(fig, "interference.png")

# 图 7：把差额拆开
fig, ax = plt.subplots(figsize=(11.5, 4.6), dpi=150)
parts = gap["归因"].drop(["合计", "实盘 − 回测", "差额核对"])
bottom, spots = 0.0, np.arange(len(parts) + 1)
span = max(abs(parts).max(), abs(parts.cumsum()).max())
for k, (label, value) in enumerate(parts.items()):
    colour = DOWN if value < 0 else UP
    ax.bar(k, value, 0.62, bottom=bottom, color=colour, alpha=0.85)
    if abs(value) > span * 0.12:                      # 柱子够高，标签放里面
        ax.annotate(f"{value:+,.0f}", (k, bottom + value / 2), ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
    else:                                             # 柱子太矮，标签放下面
        ax.annotate(f"{value:+,.0f}", (k, bottom + min(value, 0.0)), ha="center", va="top",
                    textcoords="offset points", xytext=(0, -5), fontsize=9, color=colour)
    if k:
        ax.plot([k - 0.69, k - 0.31], [bottom, bottom], color=GRAY, linewidth=0.9, linestyle=":")
    bottom += value
ax.bar(len(parts), bottom, 0.62, color=PURPLE, alpha=0.85)
ax.annotate(f"{bottom:+,.0f}", (len(parts), bottom / 2), ha="center", va="center",
            fontsize=9, color="white", fontweight="bold")
ax.axhline(0, color="black", linewidth=0.9)
ax.set_xticks(spots)
ax.set_xticklabels(list(parts.index) + ["实盘 - 回测"], fontsize=9.5)
ax.set_ylabel("美元")
ax.yaxis.set_major_formatter(money)
ax.set_title("九年下来，实盘和回测差的那一截是从哪来的（BTC 海龟）")
ax.grid(alpha=0.25, axis="y")
save(fig, "reconcile.png")
