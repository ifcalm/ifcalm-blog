"""第 26 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py
和 analysis/19_download_universe.py）。"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from talab import data as D, indicators as I, risk as K, rules as R, screen as SC, size as Z

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(26)
PLAN = K.Exit(stop="atr", k=3.0, trail="chandelier", trail_k=3.0, trigger="close")


def entries(df):
    """主线策略 v3 的入场条件（第 21 篇）：金叉状态 + 收盘创 20 日新高。"""
    close = df["close"]
    return ((I.sma(close, 50) > I.sma(close, 200)) & (close >= close.rolling(20).max())).fillna(False)


def deaths(df):
    """主线策略 v3 的出场信号：死叉。"""
    return I.cross_below(I.sma(df["close"], 50), I.sma(df["close"], 200)).fillna(False)


print("===== 片段 1：主线策略的交易表，先看止损距离 =====")
btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"],
                             D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json"))
MARKETS = {"SPY": (spy, 252), "AAPL": (aapl, 252), "BTC": (btc, 365)}
TRADES = {name: K.run(df, entries(df), PLAN, exits=deaths(df)) for name, (df, _) in MARKETS.items()}
rows = []
for name, table in TRADES.items():
    distance = table["R"] / table["买入价"]
    rows.append({"标的": name, "交易数": len(table), "止损距离中位数": distance.median(),
                 "最小": distance.min(), "最大": distance.max(), "最大÷最小": distance.max() / distance.min(),
                 "1% 风险对应的仓位": 0.01 / distance.median()})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("⚠️ 满仓时，「这一笔最多亏账户的百分之几」= 止损距离，是市场替你定的；BTC 上它在 6.4% 和 26.2% 之间跳")

print("===== 片段 2：决策点 =====")
one = TRADES["BTC"][TRADES["BTC"]["买入日"] == pd.Timestamp("2020-10-10", tz="UTC")].iloc[0]
EQUITY = 100_000.0
distance = Z.stop_distance(one["买入价"], one["初始止损"])
print(f"买入日 {one['买入日'].date()}，开盘价买入 {one['买入价']:,.2f}，初始止损 {one['初始止损']:,.2f}")
print(f"一个 R = {one['R']:.2f}，止损距离 = {distance:.4%}；账户 {EQUITY:,.0f} 美元")
rows = []
for label, notional in [("A 满仓", EQUITY), ("B 固定金额 1 万", 10_000.0),
                        ("C 固定风险 1%", EQUITY * 0.01 / distance),
                        ("D 固定风险 10%", min(EQUITY, EQUITY * 0.10 / distance))]:
    rows.append({"买法": label, "买入金额": notional, "占账户": notional / EQUITY,
                 "数量（BTC）": notional / one["买入价"], "被止损时亏": -notional * distance,
                 "亏掉账户的": -notional * distance / EQUITY})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 3：固定风险的算术 =====")
print(Z.position_size(100_000, distance=0.03, risk_fraction=0.01, price=200.0).to_string())
print("\n同一笔，止损距离换成 8.36%（2020-10-10 那笔）：")
print(Z.position_size(EQUITY, distance, risk_fraction=0.01, price=one["买入价"]).to_string())
print("\n止损距离只有 0.5% 时，1% 的风险要借钱才够——不借钱就封顶，实际风险变成 0.5%：")
print(Z.position_size(EQUITY, 0.005, 0.01).to_string())
atr = I.atr(btc["high"], btc["low"], btc["close"], 14)
value = float(atr.loc[:one["买入日"]].iloc[-2])
print(f"\n按 ATR 的等价写法（进场前一天的 14 日 ATR = {value:.2f}，3 倍 = {3 * value:.2f}）：")
print(Z.size_by_atr(EQUITY, value, one["买入价"], risk_fraction=0.01, k=3.0).to_string())

print("===== 片段 4：同一串交易，四种仓位方法 =====")
rows = []
for name, table in TRADES.items():
    for label, kwargs in [("满仓", dict(method="full")), ("固定金额 1 万", dict(method="amount", amount=10_000.0)),
                          ("固定比例 10%", dict(method="fraction", fraction=0.10)),
                          ("固定风险 1%", dict(method="risk", risk=0.01)),
                          ("固定风险 10%", dict(method="risk", risk=0.10))]:
        path = Z.simulate(table, equity=EQUITY, **kwargs)
        rows.append({"标的": name, "仓位方法": label, "期末账户": path["账户"].iloc[-1],
                     "最差一笔": path["盈亏占账户"].min(), "最好一笔": path["盈亏占账户"].max(),
                     "平均仓位": path["占账户"].mean(), "逐笔最大回撤": Z.drawdown(path["账户"]).min()})
summary = pd.DataFrame(rows)
print(summary.round(4).to_string(index=False))
print("\n⚠️ 「最差一笔」这一列才是仓位方法真正决定的东西：满仓时它由止损距离决定，固定风险时它由你决定")

print("===== 片段 5：把风险预算从 0.25% 调到满仓 =====")
rows = []
for name, (df, ppy) in MARKETS.items():
    entry, leave = entries(df), deaths(df)
    for label, kwargs in ([(f"每笔风险 {x:.2%}", dict(sizing="risk", risk_per_trade=x))
                           for x in [0.0025, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20]] + [("满仓", dict(sizing="full"))]):
        rule = R.Rule(entry=entry, exit=leave, fill="next_open", stop="chandelier", k=3.0,
                      trigger="close", **kwargs)
        returns, held, table = R.run(df, rule)
        equity = (1 + returns).cumprod()
        rows.append({"标的": name, "风险预算": label, "年化": equity.iloc[-1] ** (ppy / len(returns)) - 1,
                     "最大回撤": Z.drawdown(equity).min(), "年化波动": returns.std() * np.sqrt(ppy),
                     "平均仓位": held[held > 0].mean(), "封顶的比例": float((held >= 1.0).sum() / (held > 0).sum())})
budget = pd.DataFrame(rows)
for name in MARKETS:
    print(f"--- {name} ---")
    print(budget[budget["标的"] == name].drop(columns="标的").round(4).to_string(index=False))

print("===== 片段 6：回撤要涨多少才回本 =====")
losses = [0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.832]
print(pd.DataFrame({"回撤": losses, "要涨回来": Z.recovery(losses)}).round(4).to_string(index=False))
rows = []
for name, (df, _) in MARKETS.items():
    table = Z.underwater(df["close"])
    deep = table[table["最深"] < -0.20]
    rows.append({"标的": name, "在水下的时间": float((Z.drawdown(df["close"]) < -1e-12).mean()),
                 "水下段数": len(table), "最长一段（天）": int(table["天数"].max()),
                 "最长那段最深": float(table.loc[table["天数"].idxmax(), "最深"]),
                 "跌超 20% 的段数": len(deep), "这些段恢复天数中位数": float(deep["天数"].median())})
print(pd.DataFrame(rows).round(4).to_string(index=False))
worst = Z.underwater(btc["close"]).sort_values("天数").iloc[-1]
print(f"\nBTC 最长的一段：{worst['开始'].date()} → {worst['结束'].date()}，"
      f"{worst['天数']} 天，最深 {worst['最深']:.1%}，要涨 {worst['要涨回来']:.0%} 才回本")

print("===== 片段 7：凯利公式说下多大注 =====")
rows = []
for name, table in TRADES.items():
    r = table["R 倍数"]
    win_rate = float((r > 0).mean())
    payoff = float(r[r > 0].mean() / -r[r <= 0].mean())
    rows.append({"标的": name, "笔数": len(r), "胜率": win_rate, "平均盈利": r[r > 0].mean(),
                 "平均亏损": -r[r <= 0].mean(), "盈亏比": payoff,
                 "凯利公式 f*": Z.kelly(win_rate, payoff), "网格最优 f*": Z.optimal_f(r.to_numpy())})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("⚠️ 这是「每笔冒账户 27%–32% 的风险」，不是「仓位 27%」——BTC 上它对应的名义仓位早就顶到满仓了")

print("===== 片段 8：凯利的那个 f* 你估不准 =====")
GRID = np.arange(0.005, 1.0, 0.005)
for name, table in TRADES.items():
    r = table["R 倍数"].to_numpy()
    best = Z.optimal_f(r, GRID)
    boots = np.array([Z.optimal_f(rng.choice(r, len(r), replace=True), GRID) for _ in range(2_000)])
    half = len(r) // 2
    front, back = Z.optimal_f(r[:half], GRID), Z.optimal_f(r[half:], GRID)
    print(f"--- {name}（{len(r)} 笔）全样本 f* = {best:.3f}")
    print(f"    重抽 2000 次：中位数 {np.median(boots):.3f}，90% 区间 "
          f"[{np.quantile(boots, .05):.3f}, {np.quantile(boots, .95):.3f}]，"
          f"有 {(boots <= 0.01).mean():.1%} 的重抽说「别下注」")
    print(f"    前半段 f* = {front:.3f}，后半段 f* = {back:.3f}；"
          f"拿前半段的 f* 去跑后半段，每笔对数增长 {Z.growth_rate(r[half:], front):+.4f}，"
          f"后半段自己的最优是 {Z.growth_rate(r[half:], back):+.4f}")
    rows = []
    for label, f in [("全凯利", best), ("半凯利", best / 2), ("四分之一凯利", best / 4),
                     ("双倍凯利", min(2 * best, 0.99)), ("每笔 1%", 0.01), ("每笔 10%", 0.10)]:
        path = np.cumprod(1 + f * r)
        rows.append({"下注比例": label, "f": f, "期末是本金的几倍": path[-1],
                     "每笔对数增长": Z.growth_rate(r, f), "最差一笔": (f * r).min(),
                     "逐笔最大回撤": float(Z.drawdown(pd.Series(path)).min())})
    print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 9：波动率目标仓位 =====")
rows = []
for name, (df, ppy) in MARKETS.items():
    returns = df["close"].pct_change().dropna()
    base = returns.std() * np.sqrt(ppy)
    rows.append({"标的": name, "方法": "买入持有（1 倍）", "年化": (1 + returns).prod() ** (ppy / len(returns)) - 1,
                 "实现波动": base, "最大回撤": Z.drawdown((1 + returns).cumprod()).min(),
                 "平均仓位": 1.0, "仓位换手/年": 0.0,
                 "夏普（无风险 0）": ((1 + returns).prod() ** (ppy / len(returns)) - 1) / base})
    for target, lookback in [(0.15, 20), (0.15, 60), (0.30, 20)]:
        position = Z.vol_target(returns, target, lookback, ppy)
        for label, series in [(f"波动率目标 {target:.0%}，{lookback} 天窗口", position * returns),
                              ("   对照：实现波动一样的恒定杠杆", None)]:
            if series is None:
                leverage = (position * returns).std() / returns.std()
                series = leverage * returns
                label = f"   对照：恒定 {leverage:.2f} 倍买入持有"
            annual = (1 + series).prod() ** (ppy / len(series)) - 1
            volatility = series.std() * np.sqrt(ppy)
            rows.append({"标的": name, "方法": label, "年化": annual, "实现波动": volatility,
                         "最大回撤": Z.drawdown((1 + series).cumprod()).min(),
                         "平均仓位": position.mean() if "对照" not in label else leverage,
                         "仓位换手/年": (position.diff().abs().sum() if "对照" not in label else 0.0) / (len(series) / ppy),
                         "夏普（无风险 0）": annual / volatility})
vol_table = pd.DataFrame(rows)
for name in MARKETS:
    print(f"--- {name} ---")
    print(vol_table[vol_table["标的"] == name].drop(columns="标的").round(4).to_string(index=False))

print("===== 片段 10：为什么股票上有用、BTC 上没用 =====")
print("先确认前提：波动率本身好不好预测（前 20 天的波动 vs 后 20 天的波动，秩相关）")
for name, (df, ppy) in MARKETS.items():
    returns = df["close"].pct_change().dropna()
    past20 = returns.rolling(20).std()
    next20 = past20.shift(-20)
    pair = pd.concat([past20, next20], axis=1).dropna()
    print(f"  {name}：{pair.iloc[:, 0].rank().corr(pair.iloc[:, 1].rank()):.3f}"
          f"（同样算法下，收益的前后秩相关只有 "
          f"{returns.rolling(20).sum().pipe(lambda x: pd.concat([x, x.shift(-20)], axis=1)).dropna().pipe(lambda t: t.iloc[:, 0].rank().corr(t.iloc[:, 1].rank())):.3f}）")
for name, (df, ppy) in MARKETS.items():
    returns = df["close"].pct_change().dropna()
    realized = (returns.rolling(20).std() * np.sqrt(ppy)).shift(1)
    group = pd.qcut(realized.dropna(), 5, labels=["最低 20%", "2", "3", "4", "最高 20%"])
    table = pd.DataFrame({"组": group, "第二天收益": returns.reindex(group.index)})
    stats = table.groupby("组", observed=True)["第二天收益"].agg(["count", "mean", "std"])
    stats["折成年化"] = stats["mean"] * ppy
    stats["年化波动"] = stats["std"] * np.sqrt(ppy)
    stats["收益÷波动"] = stats["折成年化"] / stats["年化波动"]
    print(f"{name}：按前 20 天的波动分五组，之后一天的收益")
    print(stats[["count", "折成年化", "年化波动", "收益÷波动"]].round(4).to_string())
    print(f"   最高波动组的收益是最低组的 {stats['折成年化'].iloc[-1] / stats['折成年化'].iloc[0]:.2f} 倍，"
          f"「收益÷波动」是 {stats['收益÷波动'].iloc[-1] / stats['收益÷波动'].iloc[0]:.2f} 倍")

print("===== 片段 11：风险不能相加 =====")
rows = []
for n in [1, 2, 3, 5, 10]:
    row = {"同时持有几笔": n}
    for corr in [0.0, 0.3, 0.6, 0.9, 1.0]:
        row[f"两两相关 {corr}"] = Z.combined_risk(n, 0.01, corr)
    rows.append(row)
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("每笔都只冒 1% 的风险，五笔同时持有、两两相关 0.6 时，账户一天冒的风险是 4.12%，不是 5%，也不是 1%")
print(f"反过来：想让「同时五笔」合起来只冒 2% 的风险，两两相关 0.6 时每笔只能冒 "
      f"{0.02 / Z.combined_risk(5, 1.0, 0.6):.3%}，相关 0 时可以冒 {0.02 / Z.combined_risk(5, 1.0, 0.0):.3%}")

print("===== 片段 12：有效独立仓位数 =====")
SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
us = {path.name.split("_")[0]: D.load_nasdaq_daily(path) for path in Path("data/universe_us").glob("*_historical.json")}
sector = pd.DataFrame({name: us[name]["close"] for name in SECTORS}).dropna().pct_change().dropna()
frames = {folder.name: D.load_binance_klines(folder.glob("1d/*.zip")) for folder in Path("data/universe/um").iterdir()}
volume = SC.panel(frames, "volume")
close = SC.panel(frames, "close").where(volume > 0)
dollar = pd.DataFrame({name: SC.turnover(df) for name, df in frames.items()}).sort_index(axis=1).where(volume > 0)
PICKED = "2022-12-30"                                       # 名单在这一天定下，相关性在之后的三年半上量
alive = SC.rolling_turnover(dollar, 20).loc[PICKED].where(close.iloc[-1].notna())   # 中途下架/改名的不算
coins = alive.nlargest(10).index.tolist()
crypto = close[coins].loc["2023-01-01":].pct_change().dropna()
print(f"加密成交额前 10（{PICKED} 选的）：{coins}")
for label, table in [("11 个行业 ETF", sector), ("10 个成交额最大的币", crypto)]:
    corr = table.corr().to_numpy()
    off = corr[np.triu_indices(len(corr), 1)]
    weights = np.ones(len(corr)) / len(corr)
    print(f"{label}：{len(table)} 天，两两相关 中位数 {np.median(off):.3f}（{off.min():.3f} 到 {off.max():.3f}），"
          f"有效独立仓位数 {Z.effective_bets(weights, corr):.2f} / {len(corr)}，"
          f"第一主成分解释 {np.linalg.eigvalsh(corr)[-1] / len(corr):.1%}")

print("===== 片段 13：三条策略放进同一个账户 =====")
legs = {}
for name, (df, _) in MARKETS.items():
    rule = R.Rule(entry=entries(df), exit=deaths(df), fill="next_open", stop="chandelier", k=3.0, trigger="close")
    returns, held, _ = R.run(df, rule)
    if returns.index.tz is not None:                        # 美股和加密的日历不一样，先统一成不带时区的日期
        returns.index, held.index = returns.index.tz_localize(None), held.index.tz_localize(None)
    legs[name] = (returns, held)
span = pd.date_range(max(r.index[0] for r, _ in legs.values()), min(r.index[-1] for r, _ in legs.values()), freq="D")
daily = pd.DataFrame({name: r.reindex(span).fillna(0.0) for name, (r, _) in legs.items()})
holding = pd.DataFrame({name: (h > 0).reindex(span).fillna(False) for name, (_, h) in legs.items()})
open_days = legs["SPY"][0].index.intersection(span)         # 只在美股开市日上算相关，周末美股不动会把相关压低
print(f"{span[0].date()} 到 {span[-1].date()}，{len(span)} 个日历日（美股开市 {len(open_days)} 天）")
print("三条策略日收益的相关（美股开市日）：")
print(daily.loc[open_days].corr().round(3).to_string())
print("同时持有几条：", holding.sum(axis=1).value_counts().sort_index().to_dict(),
      f"；三条同时只占 {(holding.sum(axis=1) == 3).mean():.1%} 的日子")
rows = []
for label, weights in [("只做 SPY", [1, 0, 0]), ("只做 AAPL", [0, 1, 0]), ("只做 BTC", [0, 0, 1]),
                       ("三条各 1/3", [1 / 3] * 3), ("三条各满仓（总敞口 300%）", [1, 1, 1])]:
    series = daily @ np.array(weights, dtype=float)
    equity = (1 + series).cumprod()
    annual = equity.iloc[-1] ** (365 / len(series)) - 1
    volatility = series.std() * np.sqrt(365)
    rows.append({"怎么分配": label, "年化": annual, "最大回撤": Z.drawdown(equity).min(),
                 "年化波动": volatility, "夏普（无风险 0）": annual / volatility})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print(f"三条等权的有效独立仓位数：{Z.effective_bets(np.ones(3) / 3, daily.loc[open_days].corr().to_numpy()):.2f} / 3")

print("===== 片段 14：相关性真的会在下跌时上升吗 =====")
market = us["SPY"]["close"].pct_change().reindex(sector.index)


def average_corr(table):
    corr = np.corrcoef(np.asarray(table, dtype=float).T)
    return float(corr[np.triu_indices(len(corr), 1)].mean())


n_down, n_up = int((market < -0.02).sum()), int((market > 0.02).sum())
n_big = int(len(sector) * 0.1)
print(f"真实数据（{len(sector)} 天）：全样本 {average_corr(sector):.4f}")
print(f"  SPY 跌超 2% 的 {n_down} 天：{average_corr(sector[(market < -0.02).fillna(False)]):.4f}")
print(f"  SPY 涨超 2% 的 {n_up} 天：{average_corr(sector[(market > 0.02).fillna(False)]):.4f}")
print(f"  |SPY| 最大的 10%（{n_big} 天）：{average_corr(sector[(market.abs() >= market.abs().quantile(.9)).fillna(False)]):.4f}")
chol = np.linalg.cholesky(sector.corr().to_numpy())
for label, draw in [("正态", lambda: rng.standard_normal((len(sector), len(SECTORS))) @ chol.T),
                    ("t(4)（厚尾）", lambda: (rng.standard_normal((len(sector), len(SECTORS))) @ chol.T)
                     / np.sqrt(rng.chisquare(4, (len(sector), 1)) / 4))]:
    whole, down, up, big = [], [], [], []
    for _ in range(50):                                     # 相关矩阵**恒定不变**的模拟世界，只是照样挑极端日子
        fake = pd.DataFrame(draw(), columns=SECTORS)
        index = fake.mean(axis=1)
        whole.append(average_corr(fake))
        down.append(average_corr(fake.loc[index.nsmallest(n_down).index]))
        up.append(average_corr(fake.loc[index.nlargest(n_up).index]))
        big.append(average_corr(fake.loc[index.abs().nlargest(n_big).index]))
    print(f"对照（{label}，相关矩阵不变）：全样本 {np.mean(whole):.4f}，最差的 {n_down} 天 {np.mean(down):.4f}，"
          f"最好的 {n_up} 天 {np.mean(up):.4f}，|涨跌| 最大的 10% {np.mean(big):.4f}")

print("===== 片段 15：几条策略之间怎么分钱 =====")
LOOKBACK = 365
names = list(daily.columns)
weights_log = {"等权": [], "波动率倒数": [], "按历史夏普": [], "按历史年化": []}
series = {key: [] for key in weights_log}
for i in range(LOOKBACK, len(daily)):
    history = daily.iloc[i - LOOKBACK:i]
    vols = history.std().to_numpy()
    means = history.mean().to_numpy()
    plans = {"等权": np.ones(3) / 3, "波动率倒数": Z.inverse_vol_weights(np.where(vols > 0, vols, np.inf)),
             "按历史夏普": np.clip(means / np.where(vols > 0, vols, np.inf), 0, None),
             "按历史年化": np.clip(means, 0, None)}
    for key, weights in plans.items():
        weights = weights / weights.sum() if weights.sum() > 0 else np.ones(3) / 3
        weights_log[key].append(weights)
        series[key].append(float(daily.iloc[i].to_numpy() @ weights))
rows = []
for key in weights_log:
    path = pd.Series(series[key], index=daily.index[LOOKBACK:])
    equity = (1 + path).cumprod()
    annual = equity.iloc[-1] ** (365 / len(path)) - 1
    volatility = path.std() * np.sqrt(365)
    rows.append({"资金怎么分": key, "年化": annual, "最大回撤": Z.drawdown(equity).min(), "年化波动": volatility,
                 "夏普（无风险 0）": annual / volatility,
                 "平均权重": dict(zip(names, np.round(np.mean(weights_log[key], axis=0), 3)))})
print(f"每天用过去 {LOOKBACK} 天估参数、第二天用，样本外 {len(daily) - LOOKBACK} 天 "
      f"（{daily.index[LOOKBACK].date()} 到 {daily.index[-1].date()}）")
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 16：主线策略 v4 =====")
rows = []
for name, (df, ppy) in MARKETS.items():
    entry, leave = entries(df), deaths(df)
    for label, kwargs in [("v3：满仓", dict(sizing="full")),
                          ("v4：一笔最多亏账户 10%", dict(sizing="risk", risk_per_trade=0.10))]:
        rule = R.Rule(entry=entry, exit=leave, fill="next_open", stop="chandelier", k=3.0,
                      trigger="close", **kwargs)
        returns, held, table = R.run(df, rule)
        equity = (1 + returns).cumprod()
        loss = (table["收益"] * table["仓位"]).min()
        rows.append({"标的": name, "版本": label, "交易数": len(table),
                     "年化": equity.iloc[-1] ** (ppy / len(returns)) - 1, "最大回撤": Z.drawdown(equity).min(),
                     "最差一笔": loss, "平均仓位": held[held > 0].mean(),
                     "缩过仓的交易": float((table["仓位"] < 1.0).mean())})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("\nv4 的六要素（第 21 篇的格子，最后一格终于填上了）：")
print(R.Rule(entry=entries(btc), exit=deaths(btc), fill="next_open", stop="chandelier", k=3.0,
             trigger="close", sizing="risk", risk_per_trade=0.10).describe().to_string())

print("===== 片段 17：揭晓 =====")
print(f"那一笔的结局：{one['卖出日'].date()} 以 {one['卖出价']:,.2f} 止损出场，{one['R 倍数']:.2f}R")
rows = []
for label, notional in [("A 满仓", EQUITY), ("B 固定金额 1 万", 10_000.0),
                        ("C 固定风险 1%", EQUITY * 0.01 / distance),
                        ("D 固定风险 10%", min(EQUITY, EQUITY * 0.10 / distance))]:
    profit = notional * (one["卖出价"] / one["买入价"] - 1)
    rows.append({"买法": label, "这一笔赚": profit, "账户变成": EQUITY + profit,
                 "涨了": profit / EQUITY})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("\n同样四种买法，跑完 BTC 上全部 30 笔交易：")
print(summary[(summary["标的"] == "BTC")].drop(columns="标的").round(4).to_string(index=False))
