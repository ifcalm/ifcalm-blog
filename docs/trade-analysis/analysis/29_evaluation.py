"""第 29 篇正文里的代码片段（在 talab 项目根目录运行，先运行 analysis/29_download.py）。"""
import glob

import numpy as np
import pandas as pd
from talab import (backtest as BT, costs as C, data as D, indicators as I,
                   report as RP, stats as S)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(29)
N_BOOT = 2000

print("===== 片段 1：两条策略的成绩单 =====")
d1 = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
h4 = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/4h/*.zip"))
ONE_WAY = C.crypto(1.0, "现货 taker", spread_bp=C.BTC_PERP_SPREAD_BP)["占名义价值"]


def build(df: pd.DataFrame, position: pd.Series, cost: float = 0.0) -> tuple[pd.Series, pd.DataFrame]:
    """把一条仓位序列跑成「日频资金曲线 + 逐笔交易表」。

    仓位按第 27 篇的时钟规矩推迟一根；换手（`churn`）每变动一次收一次单边成本。
    4 小时线的曲线也换算到日频，这样两条策略的夏普比率才是同一个口径。
    """
    returns = df["close"].pct_change().fillna(0.0)
    held = position.shift(1).fillna(0.0)
    churn = held.diff().abs().fillna(held.iloc[0])
    equity = (1 + held * returns - churn * cost).cumprod()
    trades, start = [], None
    flags, values = held.to_numpy(), equity.to_numpy()
    for i in range(1, len(flags)):
        if flags[i] > 0 and flags[i - 1] == 0:
            start = i
        if flags[i] == 0 and flags[i - 1] > 0 and start is not None:
            trades.append({"买入日": held.index[start], "卖出日": held.index[i],
                           "收益": values[i - 1] / values[start - 1] - 1, "根数": i - start})
            start = None
    if start is not None:                              # 最后一根还拿着
        trades.append({"买入日": held.index[start], "卖出日": held.index[-1],
                       "收益": values[-1] / values[start - 1] - 1, "根数": len(flags) - start})
    return equity.resample("1D").last().ffill(), pd.DataFrame(trades)


close_d, close_h = d1["close"], h4["close"]
state = pd.Series(np.nan, index=close_d.index)
state = state.mask(close_d >= close_d.rolling(40).max(), 1.0).mask(close_d <= close_d.rolling(20).min(), 0.0)
position_a = state.ffill().fillna(0.0)                                      # A：日线唐奇安 40/20
position_b = (close_h >= close_h.rolling(12).max()).rolling(3).max().fillna(0).astype(float)   # B：4 小时突破
curve_a, trades_a = build(d1, position_a)
curve_b, trades_b = build(h4, position_b)
print(RP.compare({"A 日线唐奇安 40/20": curve_a, "B 4 小时创 12 根新高持 3 根": curve_b}, 365).round(4).to_string())
print(f"\nA 一共 {len(trades_a)} 笔，平均持仓 {trades_a['根数'].mean():.1f} 根日线")
print(f"B 一共 {len(trades_b)} 笔，平均持仓 {trades_b['根数'].mean():.1f} 根 4 小时线（{trades_b['根数'].mean() / 6:.1f} 天）")

print("===== 片段 2：年化收益的第一个陷阱：算术平均不是年化收益 =====")
returns_a, returns_b = curve_a.pct_change().dropna(), curve_b.pct_change().dropna()
buy_hold = close_d.pct_change().dropna()
rows = []
for name, series in {"BTC 买入持有": buy_hold, "A": returns_a, "B": returns_b}.items():
    arithmetic = (1 + series.mean()) ** 365 - 1
    geometric = (1 + series).prod() ** (365 / len(series)) - 1
    rows.append({"曲线": name, "日均收益率": series.mean(), "按日均复利": arithmetic,
                 "真实的年化": geometric, "差": arithmetic - geometric,
                 "年化方差的一半": series.var() * 365 / 2})
print(pd.DataFrame(rows).round(6).to_string(index=False))

print("===== 片段 3：年化收益的第二个陷阱：它是两个端点的函数 =====")
shifted = pd.Series({n: RP.annual_return(curve_a.iloc[n:], 365) for n in range(181)})
print(f"起点在最初 180 天里挪一挪：最低 {shifted.min():.2%}（往后挪 {int(shifted.idxmin())} 天）、"
      f"最高 {shifted.max():.2%}（往后挪 {int(shifted.idxmax())} 天）、原样 {shifted.iloc[0]:.2%}")
rows = []
for cut in ["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31", "2026-08-31"]:
    piece = curve_a.loc[:cut]
    rows.append({"报告写到哪天": cut, "年化收益": RP.annual_return(piece, 365),
                 "夏普比率": RP.sharpe(piece.pct_change().dropna(), 365),
                 "最大回撤": RP.max_drawdown(piece), "卡玛比率": RP.calmar(piece, 365)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 4：夏普比率是一个信噪比 =====")
print("分子是「平均每根赚多少」，分母是「这个平均值周围抖多厉害」，比值再按 √(一年几根) 放大。")
rows = []
for k in [1, 5, 10, 20, 60, 120]:
    chunk = returns_a.rolling(k).sum().dropna()
    rows.append({"合并几根": k, "均值": chunk.mean(), "均值 ÷ k": chunk.mean() / k,
                 "标准差": chunk.std(), "标准差 ÷ √k": chunk.std() / np.sqrt(k),
                 "信噪比": chunk.mean() / chunk.std(),
                 "信噪比 ÷ √k": chunk.mean() / chunk.std() / np.sqrt(k)})
print(pd.DataFrame(rows).round(6).to_string(index=False))
print(f"\nA 的日收益率方差比（第 5 篇）：5 天 {S.variance_ratio(np.log1p(returns_a), 5):.3f}、"
      f"20 天 {S.variance_ratio(np.log1p(returns_a), 20):.3f}——不等于 1，所以上面那两列不会严丝合缝")

print("===== 片段 5：骗法一，换一个计算周期，第一名就换人 =====")
rows = []
for name, curve in {"A": curve_a, "B": curve_b, "BTC 买入持有": close_d}.items():
    row = {"曲线": name}
    for label, rule, periods in [("日", None, 365), ("周", "W", 52), ("月", "ME", 12)]:
        series = curve if rule is None else curve.resample(rule).last()
        row[f"{label}线算的夏普"] = RP.sharpe(series.pct_change().dropna(), periods)
    rows.append(row)
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 6：骗法二，把净值抹平一下 =====")
rows = []
for window in [1, 2, 3, 5, 10]:
    smooth = returns_a.rolling(window).mean().dropna()
    rows.append({"报告的净值平滑几天": window, "日均收益率": smooth.mean(),
                 "年化波动": RP.annual_vol(smooth, 365), "夏普比率": RP.sharpe(smooth, 365)})
print(pd.DataFrame(rows).round(6).to_string(index=False))
print("\n分子（日均收益率）几乎没动，分母掉了三分之二——夏普比率就是这样被「抹」出来的。")
print(f"平滑 10 天之后，收益率的一阶自相关从 {S.autocorr(returns_a, lags=(1,)).iloc[0]:.3f} "
      f"变成 {S.autocorr(returns_a.rolling(10).mean().dropna(), lags=(1,)).iloc[0]:.3f}——这是唯一露出来的马脚。")

print("===== 片段 7：骗法三，无风险利率不是 0 =====")
rf = D.load_fred_series("data/fred/DTB3.csv")
print(f"3 个月国库券：{rf.index[0].date()} 到 {rf.index[-1].date()}，"
      f"最低 {rf.min():.2%}（{rf.idxmin().date()}）、最高 {rf.max():.2%}（{rf.idxmax().date()}）")
rows = []
for year, chunk in returns_a.groupby(returns_a.index.year):
    aligned = RP.excess(chunk, 365, rf)
    rows.append({"年": year, "当年平均无风险利率": (chunk - aligned).mean() * 365,
                 "夏普（利率当成 0）": RP.sharpe(chunk, 365),
                 "夏普（用真实利率）": RP.sharpe(chunk, 365, rf)})
table = pd.DataFrame(rows)
table["差"] = table["夏普（利率当成 0）"] - table["夏普（用真实利率）"]
print(table.round(4).to_string(index=False))
print(f"\n全程：{RP.sharpe(returns_a, 365):.4f} → {RP.sharpe(returns_a, 365, rf):.4f}")

print("===== 片段 8：骗法四，夏普比率看不见破产 =====")
rows = []
for leverage in [1, 2, 3, 5]:
    levered = RP.to_curve((leverage * buy_hold).clip(lower=-1.0))
    daily = levered.pct_change().dropna()
    rows.append({"杠杆": f"{leverage} 倍", "年化收益": RP.annual_return(levered, 365),
                 "年化波动": RP.annual_vol(daily, 365), "夏普比率": RP.sharpe(daily, 365),
                 "最大回撤": RP.max_drawdown(levered), "卡玛比率": RP.calmar(levered, 365),
                 "期末还剩": float(levered.iloc[-1])})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 9：最大回撤是一个极值，样本越长它越深 =====")
mu, sigma = returns_a.mean(), returns_a.std()
rows = []
for years in [1, 2, 3, 5, 9, 20]:
    n = int(365 * years)
    draws = np.array([RP.max_drawdown(RP.to_curve(pd.Series(rng.normal(mu, sigma, n),
                                                             index=pd.RangeIndex(n))))
                      for _ in range(N_BOOT)])
    rows.append({"随机游走跑几年": years, "最大回撤中位数": np.median(draws),
                 "5% 分位": np.percentile(draws, 5), "95% 分位": np.percentile(draws, 95)})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print(f"\nA 真实跑了 {len(curve_a) / 365:.1f} 年，最大回撤 {RP.max_drawdown(curve_a):.2%}——"
      "落在「同样波动率的随机游走跑九年」的 90% 区间里面，比那个中位数深 4.60 个百分点。")
rows = []
for years in [1, 2, 3, 5, 9]:
    piece = curve_a.iloc[:int(365 * years) + 1]
    rows.append({"只看前几年": years, "最大回撤": RP.max_drawdown(piece),
                 "年化收益": RP.annual_return(piece, 365), "卡玛比率": RP.calmar(piece, 365)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 10：夏普比率的标准误，和「要跑多少年」 =====")
print(RP.significance_table(periods_per_year=365).round(2).to_string(index=False))
rows = []
for name, (series, trades) in {"A": (returns_a, trades_a), "B": (returns_b, trades_b)}.items():
    value = RP.sharpe(series, 365)
    se = RP.sharpe_se(value, len(series), 365)
    stats = RP.trade_metrics(trades["收益"])
    rows.append({"策略": name, "夏普比率": value, "根数": len(series), "夏普的标准误": se,
                 "夏普的 t 值": value / se, "笔数": int(stats["笔数"]),
                 "平均持仓根数": trades["根数"].mean(), "逐笔的 t 值": stats["t 值"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 11：揭晓（上）——换一个重抽单位，两条策略就分开了 =====")
YEARS = (d1.index[-1] - d1.index[0]).days / 365.25


def by_trade(trades: pd.DataFrame, n: int = N_BOOT, seed: int = 29) -> np.ndarray:
    """按**交易**重抽：有放回地抽同样笔数的交易，复利连乘，再折算成年化。"""
    values = trades["收益"].to_numpy(float)
    generator = np.random.default_rng(seed)
    return np.array([np.prod(1 + generator.choice(values, size=len(values), replace=True))
                     ** (1 / YEARS) - 1 for _ in range(n)])


rows = []
for name, (series, trades) in {"A 日线唐奇安 40/20": (returns_a, trades_a),
                               "B 4 小时创 12 根新高持 3 根": (returns_b, trades_b)}.items():
    actual = RP.annual_return(RP.to_curve(series), 365)
    for label, block in [("按天重抽", 1), ("按 30 天的块重抽", 30), ("按 90 天的块重抽", 90)]:
        band = RP.bootstrap(series, lambda x: RP.annual_return(RP.to_curve(x), 365),
                            n=N_BOOT, block=block, seed=29)
        rows.append({"策略": name, "重抽单位": label, "实际年化": actual,
                     "5% 分位": band["90% 下界"], "95% 分位": band["90% 上界"],
                     "区间宽度": band["90% 上界"] - band["90% 下界"]})
    sims = by_trade(trades)
    rows.append({"策略": name, "重抽单位": f"按交易重抽（{len(trades)} 笔）", "实际年化": actual,
                 "5% 分位": np.percentile(sims, 5), "95% 分位": np.percentile(sims, 95),
                 "区间宽度": np.percentile(sims, 95) - np.percentile(sims, 5)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 12：回撤的区间不能按天重抽 =====")
rows = []
for name, series in {"A": returns_a, "B": returns_b}.items():
    actual = RP.max_drawdown(RP.to_curve(series))
    for block in [1, 20, 120]:
        band = RP.bootstrap(series, lambda x: RP.max_drawdown(RP.to_curve(x)),
                            n=N_BOOT, block=block, seed=29)
        values = series.to_numpy(float)
        generator = np.random.default_rng(29)
        deeper = []
        for _ in range(N_BOOT):
            if block == 1:
                sample = generator.choice(values, size=len(values), replace=True)
            else:
                starts = generator.integers(0, len(values) - block + 1, size=int(np.ceil(len(values) / block)))
                sample = np.concatenate([values[s:s + block] for s in starts])[:len(values)]
            deeper.append(RP.max_drawdown(RP.to_curve(pd.Series(sample, index=series.index))) <= actual)
        rows.append({"策略": name, "块长": block, "实际最大回撤": actual,
                     "重抽的中位数": band["自助法中位数"], "5% 分位": band["90% 下界"],
                     "重抽里比它还深的比例": float(np.mean(deeper))})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 13：揭晓（下）——把成本放回去 =====")
curves = {}
for name, (df, position) in {"A 日线唐奇安 40/20": (d1, position_a),
                             "B 4 小时创 12 根新高持 3 根": (h4, position_b)}.items():
    for label, cost in [("不含成本", 0.0), ("含成本", ONE_WAY)]:
        curves[f"{name}｜{label}"] = build(df, position, cost)[0]
print(f"单边成本 {ONE_WAY:.4%}（现货 taker 0.10% + 半个价差 {C.BTC_PERP_SPREAD_BP / 2:.4f} 基点）")
print(RP.compare(curves, 365).loc[["年化收益", "年化波动", "夏普比率", "最大回撤", "卡玛比率"]].round(4).to_string())
rows = []
for name, (df, position, trades) in {"A": (d1, position_a, trades_a),
                                     "B": (h4, position_b, trades_b)}.items():
    per_year = len(trades) / YEARS
    with_cost = build(df, position, ONE_WAY)[1]       # 同样的交易，逐笔收益扣掉成本
    rows.append({"策略": name, "笔数": len(trades), "每年笔数": per_year,
                 "每年的成本": C.annual_drag(ONE_WAY, per_year),
                 "平均每笔赚": trades["收益"].mean(),
                 "成本占平均每笔": 2 * ONE_WAY / trades["收益"].mean(),
                 "逐笔 t 值（不含成本）": RP.trade_metrics(trades["收益"])["t 值"],
                 "逐笔 t 值（含成本）": RP.trade_metrics(with_cost["收益"])["t 值"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 14：主线策略 v4 的一页纸 =====")
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.adjust_total_return(D.unadjust_splits(D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json"),
                                               D.SPLITS["AAPL"]), D.SPLITS["AAPL"],
                             D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json"))
schedule = pd.Series({"SEC 占卖出金额": 20.60 / 1e6, "TAF 每股": 0.000166, "TAF 每笔上限": 8.30})
us_cost = C.us_stock(100.0, 100.0, "sell", spread_bp=1.0, sec_rate=schedule["SEC 占卖出金额"],
                     taf_per_share=schedule["TAF 每股"], taf_cap=schedule["TAF 每笔上限"])["占名义价值"]
btc_cost = ONE_WAY + 0.00097 / 2                      # 再加第 22 篇量到的止损滑点
mainline, rows = {}, []
for name, (df, periods, fee) in {"SPY": (spy, 252, us_cost), "AAPL": (aapl, 252, us_cost),
                                 "BTC": (d1, 365, btc_cost)}.items():
    c = df["close"]
    plan = BT.Plan(entry=((I.sma(c, 50) > I.sma(c, 200)) & (c >= c.rolling(20).max())).fillna(False),
                   exit=I.cross_below(I.sma(c, 50), I.sma(c, 200)).fillna(False),
                   fill="next_open", stop="chandelier", k=3.0, trigger="close",
                   sizing="risk", risk_per_trade=0.10, fee_rate=fee)
    result = BT.run(df, plan, 100_000.0)
    mainline[name] = (result, periods)
    m = RP.metrics(result["资金曲线"], periods, rf)
    stats = RP.trade_metrics(result["交易"]["收益"])
    se = RP.sharpe_se(m["夏普比率"], len(result["资金曲线"]) - 1, periods)
    rows.append({"标的": name, "年化收益": m["年化收益"], "最大回撤": m["最大回撤"],
                 "夏普比率": m["夏普比率"], "卡玛比率": m["卡玛比率"], "笔数": int(stats["笔数"]),
                 "夏普的 t 值": m["夏普比率"] / se, "逐笔的 t 值": stats["t 值"],
                 "要跑多少年": RP.years_needed(m["夏普比率"], 2.0, periods)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 15：一页纸报告长什么样 =====")
result, periods = mainline["BTC"]
print(RP.page(result["资金曲线"], periods, result["交易"], rf=rf, name="主线策略 v4 · BTC（含成本）",
              n_boot=1000, block=20, seed=29))
