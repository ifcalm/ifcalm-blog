"""第 35 篇（毕业项目）正文里的代码片段（在 talab 项目根目录运行，数据沿用第 3、28 篇）。"""
import glob
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from talab import (backtest as BT, costs as C, data as D, indicators as I,
                   project as PJ, report as RP, reversion as RV, trend as T,
                   validate as V)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)

btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.adjust_total_return(D.unadjust_splits(D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json"),
                                               D.SPLITS["AAPL"]), D.SPLITS["AAPL"],
                             D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json"))
MARKETS = {"SPY": (spy, 252), "AAPL": (aapl, 252), "BTC": (btc, 365)}
CONNORS = dict(entry_rsi=5, rsi_period=2, n=5, exit_z=0.0, max_bars=10, stop_atr=3.0, risk=0.05)
WINDOWS, KS, THRESHOLDS = [125, 250, 375, 500, 625, 750], [10, 20, 40, 60, 90, 120], [0.8, 0.9, 1.0, 1.1, 1.2]
SPLIT = pd.Timestamp("2021-09-15")


def rolling_variance_ratio(close: pd.Series, window: int, k: int) -> pd.Series:
    """滚动方差比：第 5 篇那个 `stats.variance_ratio` 的滚动版本。

    ⚠️ 最后那个 `shift(1)` 是这一篇全部数字的前提：方差比用到当根收盘价，
    所以它最早只能在**下一根**上用来做决定（第 27 篇的时钟规矩）。
    """
    log_returns = np.log(close).diff()
    k_day = log_returns.rolling(k).sum()
    return (k_day.rolling(window).var() / (k * log_returns.rolling(window).var())).shift(1)


def legs(name: str):
    """两条腿（第 31、32 篇）和它们的五五开组合（零参数的对照组）。"""
    frame, periods = MARKETS[name]
    trend = T.turtle(frame, T.TurtlePlan())["资金曲线"]
    mean = RV.reversion(frame, RV.ReversionPlan(**CONNORS))["资金曲线"]
    blended = RV.blend({"趋势跟随": trend, "均值回归": mean}, [0.5, 0.5])
    return trend, mean, blended, frame, periods


def switches(name: str) -> dict:
    """整个参数网格：每一格是一条「按方差比在两条腿之间切换」的日收益率。"""
    trend, mean, _, frame, _ = legs(name)
    trend_returns, mean_returns = trend.pct_change().fillna(0.0), mean.pct_change().fillna(0.0)
    index = trend_returns.index.intersection(mean_returns.index)
    out = {}
    for window, k in itertools.product(WINDOWS, KS):
        ratio = rolling_variance_ratio(frame["close"], window, k).reindex(index)
        for threshold in THRESHOLDS:
            on_trend = (ratio > threshold).fillna(False)
            out[(window, k, threshold)] = (
                pd.Series(np.where(on_trend, trend_returns.reindex(index),
                                   mean_returns.reindex(index)), index=index),
                float(on_trend.mean()))
    return out


def card(curve: pd.Series, periods: int, n_params: int) -> dict:
    daily = curve.pct_change().dropna()
    return {"年化": RP.annual_return(curve, periods), "最大回撤": RP.max_drawdown(curve),
            "夏普": RP.sharpe(daily, periods), "卡玛": RP.calmar(curve, periods),
            "参数个数": float(n_params)}


print("===== 片段 1：一份看起来无懈可击的报告 =====")
spy_trend, spy_mean, spy_blend, _, _ = legs("SPY")
grid = switches("SPY")
sharpes = pd.Series({key: RP.sharpe(value[0], 252) for key, value in grid.items()})
BEST = tuple(float(x) if isinstance(x, float) else int(x) for x in sharpes.idxmax())
BEST = (int(BEST[0]), int(BEST[1]), float(BEST[2]))
LABEL = f"window={BEST[0]}, k={BEST[1]}, 阈值={BEST[2]:g}"
best_curve = RP.to_curve(grid[BEST][0])
rows = [{"策略": f"按方差比切换（{LABEL}）", **card(best_curve, 252, 3)},
        {"策略": "只做趋势跟随（第 31 篇）", **card(spy_trend, 252, 0)},
        {"策略": "只做均值回归（第 32 篇）", **card(spy_mean, 252, 0)}]
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("\n第 30 篇的检验：")
surface = pd.DataFrame([{"window": w, "k": k, "夏普": sharpes[(w, k, BEST[2])]}
                        for w, k in itertools.product(WINDOWS, KS)]).pivot(
    index="window", columns="k", values="夏普")
neighbours = V.neighbourhood(surface, (BEST[0], BEST[1]), radius=1)
inside = pd.Series({key: RP.sharpe(value[0].loc[:SPLIT], 252) for key, value in grid.items()})
outside = pd.Series({key: RP.sharpe(value[0].loc[SPLIT:], 252) for key, value in grid.items()})
picked = inside.idxmax()
annual = pd.Series({key: RP.annual_return(RP.to_curve(value[0]), 252) for key, value in grid.items()})
matrix = np.column_stack([value[0].to_numpy() for value in grid.values()])
checks = pd.Series({
    "网格一共几格": float(len(grid)),
    "亏钱的格子": float((annual < 0).sum()),
    "最好的一格夏普": sharpes.max(),
    "邻域中位": float(neighbours.median()),
    "落差": sharpes.max() - float(neighbours.median()),
    "落差占最好那格的": (sharpes.max() - float(neighbours.median())) / sharpes.max(),
    "样本内挑的那格·样本内夏普": inside[picked],
    "样本内挑的那格·样本外夏普": outside[picked],
    "它在样本外排第几": float((outside > outside[picked]).sum() + 1),
    "样本内外秩相关": inside.rank().corr(outside.rank()),
    "PBO": V.pbo(matrix, n_chunks=8)["过拟合概率 PBO"],
})
print(checks.round(4).to_string())

print("===== 片段 2：报告里少了一行 =====")
comparison = PJ.against(card(best_curve, 252, 3),
                        {"只做趋势跟随": card(spy_trend, 252, 0),
                         "只做均值回归": card(spy_mean, 252, 0),
                         "五五开每月再平衡（第 32 篇）": card(spy_blend, 252, 0)})
print(comparison.round(4).to_string())

print("===== 片段 3：优势，和「试了 180 次白捡的量」 =====")
luck = PJ.edge_vs_luck(candidate_sharpe=sharpes.max(),
                       control_sharpe=RP.sharpe(spy_blend.pct_change().dropna(), 252),
                       n_trials=len(grid), sharpe_std=float(sharpes.std()))
print(luck.drop("结论").round(4).to_string())
print("结论：" + luck["结论"])

print("===== 片段 4：样本内那一段，一格都没赢过 =====")
blend_returns = spy_blend.pct_change().dropna()
blend_in, blend_out = RP.sharpe(blend_returns.loc[:SPLIT], 252), RP.sharpe(blend_returns.loc[SPLIT:], 252)
print(pd.Series({
    "样本内（挑参数那一段）·网格最好": inside.max(),
    "样本内·网格中位": inside.median(),
    "样本内·零参数五五开": blend_in,
    "样本内超过五五开的格子": float((inside > blend_in).sum()),
    "全样本·网格最好": sharpes.max(),
    "全样本·零参数五五开": RP.sharpe(blend_returns, 252),
    "全样本超过五五开的格子": float((sharpes > RP.sharpe(blend_returns, 252)).sum()),
}).round(4).to_string())
print(f"\n⚠️ 挑参数的那一段（到 {SPLIT.date()} 为止），{len(grid)} 格里超过零参数对照组的有 "
      f"{int((inside > blend_in).sum())} 格。")

print("===== 片段 5：换两个市场 =====")
rows = []
for name in MARKETS:
    trend, mean, blended, _, periods = legs(name)
    series, on_trend = switches(name)[BEST]
    rows.append({"标的": name, "策略": f"SPY 挑出来的那一格（{LABEL}）", "在趋势腿上的天数": on_trend,
                 **card(RP.to_curve(series), periods, 3)})
    rows.append({"标的": name, "策略": "五五开每月再平衡（零参数）", "在趋势腿上的天数": np.nan,
                 **card(blended, periods, 0)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 6：它到底在做什么 =====")
rows = []
for name in MARKETS:
    trend, mean, _, _, periods = legs(name)
    series, on_trend = switches(name)[BEST]
    trend_returns, mean_returns = trend.pct_change().fillna(0.0), mean.pct_change().fillna(0.0)
    index = series.index
    rows.append({"标的": name, "在趋势腿上的天数": on_trend,
                 "和趋势腿的相关": float(series.corr(trend_returns.reindex(index))),
                 "和均值回归腿的相关": float(series.corr(mean_returns.reindex(index))),
                 "一年切换几次": float((series.index.to_series().notna()
                                        & pd.Series(np.diff((rolling_variance_ratio(
                                            MARKETS[name][0]["close"], BEST[0], BEST[1])
                                            .reindex(index) > BEST[2]).fillna(False).astype(int),
                                            prepend=0) != 0, index=index)).sum()) / (len(index) / periods)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 7：六格登记表 =====")
idea = PJ.Idea(
    name="用滚动方差比，在趋势跟随和均值回归之间切换",
    counterparty="不知道。第 31、32 篇说清楚了两条腿各自的对手（被迫平仓的趋势者 / 被迫止损的散户），"
                 "但说不出「方差比变了」这件事本身对应谁在被迫交易",
    mechanism="第 32 篇量到 60 天方差比 0.616 / 0.852 / 1.270 和两条腿的强弱一一对应，"
              "⚠️ 但那一篇明确写了「三个标的算不出规律，它是解释不是筛选器」",
    rules="每根收盘算滚动方差比（window, k），高于阈值则下一根用海龟的仓位，否则用 RSI(2) 的仓位",
    control="第 32 篇的五五开每月再平衡——**零参数**，而且已经在同样的数据上量过",
    sample="SPY / AAPL / BTC 日线，约 2,500–3,300 根，两条腿合计约 300 笔",
    deployment="第 34 篇的阶梯；警戒线按台阶笔数用第 33 篇的正常范围表算",
)
print(idea.describe().to_string())

print("===== 片段 8：全课的检查单 =====")
print(PJ.checklist().to_string(index=False))

print("===== 片段 9：这条想法的体检表 =====")
best_annual = RP.annual_return(best_curve, 252)
gates = [
    PJ.Gate("说得出谁被迫交易", 0.0, 1.0, "高", "第 2 篇", must=True),
    PJ.Gate("网格里亏钱的格子占", float((annual < 0).mean()), 0.10, "低", "第 31 篇"),
    PJ.Gate("曲面落差占最好那格的", checks["落差占最好那格的"], 0.30, "低", "第 30 篇"),
    PJ.Gate("样本外排名（越小越好）", checks["它在样本外排第几"], len(grid) * 0.5, "低", "第 30 篇"),
    PJ.Gate("PBO", checks["PBO"], 0.50, "低", "第 30 篇"),
    PJ.Gate("夏普优势 ÷ 白捡的门槛", luck["优势是门槛的几成"], 1.0, "高", "第 30、35 篇", must=True),
    PJ.Gate("赢过对照组的项数（共 4 项）", float(comparison.loc["五五开每月再平衡（第 32 篇）", "候选赢了几项"]),
            4.0, "高", "第 35 篇", must=True),
    PJ.Gate("换市场还成立吗（三个标的里赢过对照组的个数）", 0.0, 2.0, "高", "第 31 篇"),
]
print(PJ.audit(gates).round(4).to_string(index=False))
print()
print(PJ.verdict(gates).to_string())

print("===== 片段 10：实验四，一页纸策略报告 =====")
print(PJ.one_pager(idea, gates, comparison, luck))

print("===== 片段 11：主线策略 v0 → v4 =====")
def mainline(frame, version: str, fee_rate: float = 0.0):
    price = frame["close"]
    cross = (I.sma(price, 50) > I.sma(price, 200)).fillna(False)
    high20 = (price >= price.rolling(20).max()).fillna(False)
    exit_signal = I.cross_below(I.sma(price, 50), I.sma(price, 200)).fillna(False)
    settings = {
        "v0（第 12 篇）": dict(entry=cross, stop="none", sizing="full"),
        "v1（第 15 篇）": dict(entry=cross, stop="chandelier", trigger="extreme", sizing="full"),
        "v2（第 20 篇）": dict(entry=cross, stop="chandelier", trigger="close", sizing="full"),
        "v3（第 21 篇）": dict(entry=cross & high20, stop="chandelier", trigger="close", sizing="full"),
        "v4（第 26 篇）": dict(entry=cross & high20, stop="chandelier", trigger="close",
                              sizing="risk", risk_per_trade=0.10),
    }[version]
    return BT.run(frame, BT.Plan(exit=exit_signal, k=3.0, fee_rate=fee_rate, **settings), 100_000.0)


CHANGES = {"v0（第 12 篇）": "50/200 均线金叉持有、死叉出场，满仓，没有止损",
           "v1（第 15 篇）": "＋ 3 ATR 吊灯止损（盘中最低价触发）",
           "v2（第 20 篇）": "止损改成收盘价触发",
           "v3（第 21 篇）": "入场加一条：收盘要创 20 日新高",
           "v4（第 26 篇）": "仓位改成「一笔最多亏账户 10%」"}
schedule = pd.Series({"SEC 占卖出金额": 20.60 / 1e6, "TAF 每股": 0.000166, "TAF 每笔上限": 8.30})
us_cost = C.us_stock(100.0, 100.0, "sell", spread_bp=1.0, sec_rate=schedule["SEC 占卖出金额"],
                     taf_per_share=schedule["TAF 每股"], taf_cap=schedule["TAF 每笔上限"])["占名义价值"]
btc_cost = C.crypto(1.0, "现货 taker", spread_bp=C.BTC_PERP_SPREAD_BP)["占名义价值"] + 0.00097 / 2
versions = {}
for version, change in CHANGES.items():
    row = {"这一版改了什么": change}
    for name, (frame, periods) in MARKETS.items():
        result = mainline(frame, version)
        row[f"{name} 年化"] = RP.annual_return(result["资金曲线"], periods)
        row[f"{name} 回撤"] = RP.max_drawdown(result["资金曲线"])
    versions[version] = row
print(PJ.evolution(versions).round(4).to_string())
print("\n⚠️ 和当年那几篇报的数字核对一下（SPY 年化）：")
recorded = {"v0（第 12 篇）": 0.085, "v1（第 15 篇）": 0.029, "v2（第 20 篇）": 0.039,
            "v3（第 21 篇）": 0.030, "v4（第 26 篇）": 0.030}
print(pd.DataFrame([{"版本": version, "当年报的": recorded[version],
                     "这张表重算的": versions[version]["SPY 年化"],
                     "差多少个百分点": 100 * (versions[version]["SPY 年化"] - recorded[version])}
                    for version in CHANGES]).round(4).to_string(index=False))

print("\n加上第 28 篇的成本之后（v4）：")
rows = []
for name, (frame, periods) in MARKETS.items():
    fee = btc_cost if name == "BTC" else us_cost
    plain = mainline(frame, "v4（第 26 篇）")["资金曲线"]
    costed = mainline(frame, "v4（第 26 篇）", fee_rate=fee)["资金曲线"]
    rows.append({"标的": name, "单边费率": fee, "不含成本年化": RP.annual_return(plain, periods),
                 "含成本年化": RP.annual_return(costed, periods),
                 "差多少个百分点": 100 * (RP.annual_return(plain, periods)
                                          - RP.annual_return(costed, periods))})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 12：主线 v4 走一遍同一条流水线 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    fee = btc_cost if name == "BTC" else us_cost
    result = mainline(frame, "v4（第 26 篇）", fee_rate=fee)
    curve, trades = result["资金曲线"], result["交易"]
    hold = frame["close"].loc[curve.index[0]:]
    rows.append({"标的": name, **card(curve, periods, 4),
                 "笔数": float(len(trades)),
                 "逐笔 t 值": RP.trade_metrics(trades["收益"])["t 值"],
                 "买入持有·年化": RP.annual_return(hold, periods),
                 "买入持有·夏普": RP.sharpe(hold.pct_change().dropna(), periods),
                 "赢过买入持有的项数": float(sum([
                     RP.annual_return(curve, periods) > RP.annual_return(hold, periods),
                     RP.max_drawdown(curve) > RP.max_drawdown(hold),
                     RP.sharpe(curve.pct_change().dropna(), periods) > RP.sharpe(hold.pct_change().dropna(), periods),
                     RP.calmar(curve, periods) > RP.calmar(hold, periods)]))})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 13：那要是真想改进那条零参数的对照组呢 =====")
rows = []
for name in MARKETS:
    trend, mean, _, _, periods = legs(name)
    for weight in (0.3, 0.5, 0.7):
        for rebalance in ("W", "ME", "QE"):
            mixed = RV.blend({"趋势跟随": trend, "均值回归": mean}, [weight, 1 - weight], rebalance)
            rows.append({"标的": name, "趋势腿权重": weight, "再平衡": rebalance,
                         "夏普": RP.sharpe(mixed.pct_change().dropna(), periods),
                         "卡玛": RP.calmar(mixed, periods)})
table = pd.DataFrame(rows)
print(table.pivot_table(index=["标的", "趋势腿权重"], columns="再平衡", values="夏普").round(4).to_string())
base = table[(table["趋势腿权重"] == 0.5) & (table["再平衡"] == "ME")].set_index("标的")["夏普"]
better = table.merge(base.rename("五五开每月"), on="标的")
better = better[better["夏普"] > better["五五开每月"]]
print(f"\n{len(table)} 组里夏普超过「五五开 + 每月再平衡」的有 {len(better)} 组：")
print(better.round(4).to_string(index=False))

print("===== 片段 14：这门课造出来的东西 =====")
root = Path("talab")
rows = []
for path in sorted(root.glob("*.py")):
    if path.name == "__init__.py":
        continue
    text = path.read_text(encoding="utf-8")
    rows.append({"模块": path.stem, "行数": len(text.splitlines()),
                 "函数": text.count("\ndef "), "类": text.count("\nclass ")})
modules = pd.DataFrame(rows)
print(modules.to_string(index=False))
tests = sorted(Path("tests").glob("test_*.py"))
total_tests = sum(path.read_text(encoding="utf-8").count("\ndef test_") for path in tests)
print(f"\n合计：{len(modules)} 个模块、{modules['行数'].sum():,} 行、"
      f"{modules['函数'].sum()} 个函数、{modules['类'].sum()} 个类；"
      f"{len(tests)} 个测试文件、{total_tests} 个测试函数"
      f"（其中 {sum(path.read_text(encoding='utf-8').count('parametrize') for path in tests)} 处 "
      f"parametrize，所以 pytest 数出来的用例比函数多）")

print("===== 片段 15：这门课用过的数据 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    rows.append({"标的": name, "K 线根数": float(len(frame)),
                 "从": str(frame.index[0].date()), "到": str(frame.index[-1].date()),
                 "年数": len(frame) / periods})
print(pd.DataFrame(rows).round(2).to_string(index=False))
minutes = len(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip"))
universe = len(glob.glob("data/universe/um/*"))
print(f"\n另外：BTC 1 分钟线 {minutes} 个月度文件；第 19、28 篇的全市场名单 {universe} 个合约；"
      f"第 34 篇的 exchangeInfo 快照 {len(D.load_json('data/binance/exchange_info.json')['symbols']):,} 个交易对")
