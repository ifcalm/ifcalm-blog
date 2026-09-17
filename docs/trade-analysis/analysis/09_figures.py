"""生成第 9 篇的插图：python 09_figures.py <输出目录>（在 talab 项目根目录运行）。"""
import glob
import sys
from pathlib import Path

import exchange_calendars as xc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from talab import bars as B, data as D, plot as P, structure as X

out = Path(sys.argv[1] if len(sys.argv) > 1 else "figures")
out.mkdir(parents=True, exist_ok=True)
P.use_chinese_font()
UP, DOWN, BLUE, ORANGE, GRAY = "#26a69a", "#ef5350", "#1f77b4", "#ff7f0e", "#888888"
money = FuncFormatter(lambda v, _: f"{v:,.0f}")
pct = FuncFormatter(lambda v, _: f"{v:.0%}")
utc = lambda s: pd.Timestamp(s, tz="UTC")
cols = ["open", "high", "low", "close"]

day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
spy["volume"] = spy["volume"].fillna(0)
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
atr = X.wilder_smooth(X.true_range(day["high"], day["low"], day["close"]), 14)
ZONE_LOW, ZONE_HIGH = 65000.00, 65618.49


def zone(ax, x0, x1, label=True):
    ax.add_patch(Rectangle((x0, ZONE_LOW), x1 - x0, ZONE_HIGH - ZONE_LOW, color=BLUE, alpha=0.18, linewidth=0))
    if label:
        ax.text(x0 + 0.5, ZONE_HIGH, " 65,000 ~ 65,618", color=BLUE, fontsize=9, va="bottom")


# 1. 决策点：日线
x = day.loc[utc("2026-01-20"):utc("2026-06-02")]
fig, ax, av = P.plot_candles(x, title="BTCUSDT 日线，2026-01-20 至 2026-06-02")
zone(ax, -1, len(x))
for d, price in [("2026-02-12", 65118.00), ("2026-03-08", 65618.49), ("2026-03-29", 65000.00)]:
    i = x.index.get_loc(utc(d))
    ax.annotate(f"{d[5:]}\n{price:,.0f}", (i, price), textcoords="offset points", xytext=(0, -34), ha="center",
                fontsize=8.5, arrowprops={"arrowstyle": "->", "color": "#555"})
lo, hi = ax.get_ylim(); ax.set_ylim(lo - (hi - lo) * 0.08, hi)
fig.savefig(out / "decision-daily.png"); plt.close(fig)

# 2. 决策点：1 小时线
hour = B.resample_ohlcv(minute.loc["2026-05-31":"2026-06-03"], "1h")
x = hour.loc[utc("2026-06-01"):utc("2026-06-03 03:00")]
fig, ax, av = P.plot_candles(x, title="BTCUSDT 1 小时线，到 2026-06-03 03:00 这一根（UTC 04:00 收盘）")
zone(ax, -1, len(x))
lo, hi = ax.get_ylim(); ax.set_ylim(min(lo, ZONE_LOW - 500), hi)
fig.savefig(out / "decision-hourly.png"); plt.close(fig)

# 3. 整数关口
hour_all = B.resample_ohlcv(minute, "1h")
def exact_share(p, step):
    p = p[(p >= 10_000) & (p < 130_000)]
    return (np.round(np.mod(p, step), 2) == 0).mean()
series = [("1 分钟收盘价", minute["close"]), ("1 小时最高价", hour_all["high"]), ("1 小时最低价", hour_all["low"]),
          ("日线最高价", day["high"]), ("日线最低价", day["low"])]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), dpi=150)
for ax, step in zip(axes, [1000, 100]):
    values = [exact_share(p, step) for _, p in series]
    bars = ax.bar(range(len(series)), values, color=[GRAY, BLUE, BLUE, ORANGE, ORANGE])
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2%}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(range(len(series))); ax.set_xticklabels([s[0] for s in series], fontsize=9)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1%}"))
    ax.set_title(f"价格正好是 {step:,} 的整数倍的比例（10,000 ~ 130,000 之间）", fontsize=10.5)
    ax.grid(alpha=0.25, axis="y"); ax.set_ylim(0, max(values) * 1.18)
fig.tight_layout(); fig.savefig(out / "round-numbers.png"); plt.close(fig)

# 4. 四种缺口（示意）
rng = np.random.default_rng(4)
drift = np.r_[np.zeros(25), np.full(35, 0.45), np.full(15, 0.55), np.full(20, -0.5)]
jumps = {12: 2.2, 25: 4.0, 45: 4.0, 60: 4.5, 75: -4.5}
drift[13:17] = -0.6                                        # 普通缺口之后几天回落，把缺口填上
bars_, price, prev_high, prev_low = [], 100.0, 100.5, 99.5
for k in range(len(drift)):
    o = price + jumps.get(k, 0.0)
    if k in jumps:                                         # 跳空：开盘价越过前一根的最高价（或最低价）
        o = max(o, prev_high + 0.8) if jumps[k] > 0 else min(o, prev_low - 0.8)
    c = o + drift[k] + rng.normal(0, 0.5)
    h = max(o, c) + abs(rng.normal(0, 0.3))
    l = min(o, c) - abs(rng.normal(0, 0.3))
    if k in jumps:
        l = max(l, prev_high + 0.3) if jumps[k] > 0 else l
        h = min(h, prev_low - 0.3) if jumps[k] < 0 else h
    bars_.append((o, h, l, c))
    price, prev_high, prev_low = c, h, l
demo = pd.DataFrame(bars_, columns=cols)
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
for i, (o, h, l, c) in enumerate(demo[cols].itertuples(index=False)):
    color = UP if c >= o else DOWN
    ax.vlines(i, l, h, color=color, linewidth=0.8)
    ax.add_patch(Rectangle((i - 0.35, min(o, c)), 0.7, max(abs(c - o), 0.05), facecolor=color))
labels = {12: "普通缺口\n在区间里，几天后被填上", 25: "突破缺口\n离开区间", 45: "中继缺口\n趋势途中",
          60: "竭尽缺口\n趋势末端", 75: "反转之后才知道\n上一个是竭尽缺口"}
for i, text in labels.items():
    y = demo["high"].iloc[i] if jumps[i] > 0 else demo["low"].iloc[i]
    ax.annotate(text, (i, y), textcoords="offset points", xytext=(0, 30 if jumps[i] > 0 else -44), ha="center",
                fontsize=8.5, arrowprops={"arrowstyle": "->", "color": "#555"})
ax.set_title("四种缺口（示意图，不是真实数据）", fontsize=12)
ax.set_xticks([]); ax.yaxis.set_major_formatter(money); ax.grid(alpha=0.2)
lo, hi = ax.get_ylim(); ax.set_ylim(lo - (hi - lo) * 0.2, hi + (hi - lo) * 0.25)
fig.tight_layout(); fig.savefig(out / "gap-types.png"); plt.close(fig)

# 5. 揭晓
x = day.loc[utc("2026-05-15"):utc("2026-08-31")]
fig, ax, av = P.plot_candles(x, title="BTCUSDT 日线，2026-05-15 至 2026-08-31")
zone(ax, -1, len(x))
i = x.index.get_loc(utc("2026-06-03"))
ax.annotate("6 月 3 日\n第四次回来", (i, x["low"].iloc[i]), textcoords="offset points", xytext=(-40, -40), ha="center",
            fontsize=9, arrowprops={"arrowstyle": "->", "color": "#555"})
fig.savefig(out / "reveal.png"); plt.close(fig)

# 6. 一个水平位的一生（65,118）
all_swings = X.fractals(day["high"], day["low"], 5, 5)
life = X.level_tests(day["high"], day["low"], day["close"],
                     all_swings[(all_swings["time"] == utc("2026-02-12")) & (all_swings["kind"] == -1)], atr)
x = day.loc[utc("2026-02-01"):utc("2026-08-31")]
fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
ax.plot(x.index, x["close"], color="black", linewidth=1)
ax.fill_between(x.index, x["low"], x["high"], color=GRAY, alpha=0.25, linewidth=0)
ax.axhline(65118, color=BLUE, linestyle="--", linewidth=1)
ax.fill_between(x.index, 65118 - 1.5 * atr.shift(1).reindex(x.index), 65118 + 1.5 * atr.shift(1).reindex(x.index),
                color=BLUE, alpha=0.08, linewidth=0, label="水平位上下 1.5 个 ATR")
for r in life.itertuples():
    color = UP if r.outcome == "held" else DOWN
    name = "支撑" if r.role == "support" else "阻力"
    word = "守住" if r.outcome == "held" else "突破"
    y = x.loc[r.test_time, "low"] if r.role == "support" else x.loc[r.test_time, "high"]
    ax.plot(r.test_time, y, "o", color=color)
    ax.annotate(f"{name}第 {r.n} 次\n{r.resolved_at:%m-%d} {word}", (r.test_time, y), textcoords="offset points",
                xytext=(-48 if r.outcome == "broken" and r.role == "support" else 0, -32 if r.role == "support" else 14),
                ha="center", fontsize=8.5, color=color)
ax.axvline(utc("2026-02-17"), color=GRAY, linestyle=":", linewidth=0.8)
ax.text(utc("2026-02-17"), 80500, " 2 月 12 日的低点 65,118\n 在 2 月 17 日确认", fontsize=8.5, va="top")
ax.yaxis.set_major_formatter(money); ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="upper right")
ax.set_ylim(55000, 83000)
ax.set_title("水平位 65,118 的一生：三次守住、一次突破、角色互换", fontsize=12)
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m"))
fig.tight_layout(); fig.savefig(out / "level-life.png"); plt.close(fig)

# 7. 守住比例和打乱后的范围（BTC）
def shuffle_bars(df, rng):
    rel = np.log(df[cols].div(df["close"].shift(1), axis=0))
    rel["volume"] = df["volume"]
    rel = rel.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    prev_close = df["close"].iloc[0] * np.exp(rel["close"].cumsum().shift(1, fill_value=0))
    o = np.exp(rel[cols]).mul(prev_close, axis=0)
    o["volume"] = rel["volume"].to_numpy()
    o.index = df.index[1:]
    return o
def hold_rates(df, distance=1.5):
    a = X.wilder_smooth(X.true_range(df["high"], df["low"], df["close"]), 14)
    t = X.level_tests(df["high"], df["low"], df["close"], X.fractals(df["high"], df["low"], 5, 5), a, distance=distance)
    t = t[t["outcome"] != "open"]
    groups = {}
    for role, name in [("support", "支撑"), ("resistance", "阻力")]:
        first = t[(t["role"] == role) & (t["flips"] == 0)]
        for label, part in [("第 2 次", first[first["n"] == 2]), ("第 3 次", first[first["n"] == 3]),
                            ("第 4 次", first[first["n"] == 4]), ("第 5 次及以上", first[first["n"] >= 5]),
                            ("互换后第 1 次", t[(t["role"] == role) & (t["flips"] == 1) & (t["n"] == 1)])]:
            groups[(name, label)] = ((part["outcome"] == "held").mean(), len(part))
    return groups
rng = np.random.default_rng(0)
real = hold_rates(day)
sims = pd.DataFrame([{k: v[0] for k, v in hold_rates(shuffle_bars(day, rng)).items()} for _ in range(200)])
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), dpi=150, sharey=True)
for ax, role in zip(axes, ["支撑", "阻力"]):
    keys = [k for k in real if k[0] == role]
    xs = np.arange(len(keys))
    lo, hi = sims[keys].quantile(0.025).values, sims[keys].quantile(0.975).values
    ax.bar(xs, hi - lo, bottom=lo, color="#cfd8dc", width=0.55, label="打乱 200 次的 95% 范围")
    ax.plot(xs, [real[k][0] for k in keys], "o", color=DOWN, markersize=8, label="真实数据")
    for xx, k in zip(xs, keys):
        ax.text(xx + 0.3, real[k][0], f"{real[k][0]:.0%}\n({real[k][1]} 次)", fontsize=8, va="center")
    ax.set_xticks(xs); ax.set_xticklabels([k[1] for k in keys], fontsize=9)
    ax.yaxis.set_major_formatter(pct); ax.grid(alpha=0.25, axis="y"); ax.set_ylim(0.2, 0.9)
    ax.set_title(f"BTC {role}：第几次测试时守住的比例", fontsize=11)
axes[0].legend(fontsize=9, loc="lower left")
fig.tight_layout(); fig.savefig(out / "hold-rates.png"); plt.close(fig)

# 8. 美股跳空：回补和对照
def gap_table(df):
    g = X.gaps(df["open"], df["high"], df["low"], df["close"])
    sigma = np.log(df["close"]).diff().rolling(20).std().shift(1)
    g = g[sigma[g.index].notna()].copy()
    g["标准差倍数"] = np.abs(np.log1p(g["size"])) / sigma[g.index]
    days = pd.Series(np.arange(len(df)), index=df.index)
    fill, mirror = [], []
    for t, row in g.iterrows():
        up = row["direction"] == 1
        f = X.first_reach(df["high"], df["low"], t, row["prev_close"], from_above=up)
        m = X.first_reach(df["high"], df["low"], t, row["open"] * row["open"] / row["prev_close"], from_above=not up)
        fill.append(days[f] - days[t] if pd.notna(f) else np.nan)
        mirror.append(days[m] - days[t] if pd.notna(m) else np.nan)
    g["回补"], g["对照"] = fill, mirror
    return g
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), dpi=150, sharey=True)
labels = ["0~0.25", "0.25~0.5", "0.5~1", "1~2", "2 以上"]
for ax, (name, df) in zip(axes, [("SPY", spy), ("AAPL", aapl)]):
    g = gap_table(df)
    size = pd.cut(g["标准差倍数"], [0, 0.25, 0.5, 1, 2, np.inf], labels=labels)
    grouped = g.groupby(size, observed=False)
    xs = np.arange(len(labels))
    for col, color, text in [("回补", BLUE, "回到前一天收盘价"), ("对照", ORANGE, "到达开盘价另一侧同样距离")]:
        ax.plot(xs, grouped[col].apply(lambda s: (s == 0).mean()).values, "o-", color=color, label=f"当天：{text}")
        ax.plot(xs, grouped[col].apply(lambda s: (s <= 5).mean()).values, "s--", color=color, label=f"5 天内：{text}")
    ax.set_xticks(xs); ax.set_xticklabels(labels); ax.set_xlabel("跳空大小（前 20 天日收益率标准差的几倍）")
    ax.yaxis.set_major_formatter(pct); ax.grid(alpha=0.25); ax.set_title(f"{name}：隔夜跳空之后", fontsize=11)
axes[0].legend(fontsize=8, loc="lower left")
fig.tight_layout(); fig.savefig(out / "us-gaps.png"); plt.close(fig)

# 9. CME 缺口
CT = "America/Chicago"
cme = xc.get_calendar("CMES", start="2017-12-01", end="2026-06-30")
open_days = set(cme.sessions.date)
rows = []
for friday in pd.date_range("2017-12-22", "2026-05-22", freq="W-FRI"):
    last = friday
    while last.date() not in open_days:
        last -= pd.Timedelta("1D")
    close_at = pd.Timestamp(f"{last.date()} 16:00", tz=CT).tz_convert("UTC")
    open_at = pd.Timestamp(f"{(friday + pd.Timedelta('2D')).date()} 17:00", tz=CT).tz_convert("UTC")
    rows.append({"开盘时刻": open_at, "收盘价": minute["close"].get(close_at - pd.Timedelta("1min")), "开盘价": minute["open"].get(open_at)})
weekend = pd.DataFrame(rows).dropna()
up = weekend["开盘价"] > weekend["收盘价"]
def hours_to(start, level, from_above):
    hit = X.first_reach(minute["high"], minute["low"], start, level, from_above)
    return (hit - start) / pd.Timedelta("1h") if pd.notna(hit) else np.inf
fill = np.array([hours_to(r["开盘时刻"], r["收盘价"], u) for (_, r), u in zip(weekend.iterrows(), up)])
mirror = np.array([hours_to(r["开盘时刻"], r["开盘价"] ** 2 / r["收盘价"], not u) for (_, r), u in zip(weekend.iterrows(), up)])
grid = np.logspace(-1, np.log10(24 * 365 * 3), 300)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4), dpi=150)
gap_sizes = (weekend["开盘价"] / weekend["收盘价"] - 1).clip(-0.1, 0.1)
a1.hist(gap_sizes, bins=60, color="#90a4ae")
a1.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}")); a1.grid(alpha=0.25)
a1.set_title(f"{len(weekend)} 个周末缺口的大小（超过 ±10% 的归入两端）", fontsize=11)
a2.plot(grid, [(fill <= g).mean() for g in grid], color=BLUE, label="回到周五收盘价（回补缺口）")
a2.plot(grid, [(mirror <= g).mean() for g in grid], color=ORANGE, label="到达开盘价另一侧同样距离")
a2.set_xscale("log")
for h, text in [(24, "1 天"), (168, "1 周"), (720, "30 天"), (8760, "1 年")]:
    a2.axvline(h, color=GRAY, linestyle=":", linewidth=0.8); a2.text(h, 0.03, text, fontsize=8)
a2.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
a2.set_xlabel("周日开盘之后的小时数（对数坐标）"); a2.yaxis.set_major_formatter(pct); a2.grid(alpha=0.25)
a2.legend(fontsize=9, loc="upper left"); a2.set_title("已经到达的比例", fontsize=11)
fig.tight_layout(); fig.savefig(out / "cme-gaps.png"); plt.close(fig)
print("done")
