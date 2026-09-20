"""第 32 篇正文里的代码片段（在 talab 项目根目录运行，数据沿用第 3、28 篇）。"""
import glob

import numpy as np
import pandas as pd
from talab import (data as D, indicators as I, report as RP, reversion as RV,
                   stats as S, trend as T, validate as V)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
N_PATHS = 100

btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.adjust_total_return(D.unadjust_splits(D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json"),
                                               D.SPLITS["AAPL"]), D.SPLITS["AAPL"],
                             D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json"))
MARKETS = {"SPY": (spy, 252), "AAPL": (aapl, 252), "BTC": (btc, 365)}
# Connors 的 RSI(2) 规则：2 日 RSI 跌破 5 买入，收盘站上 5 日均线卖出。1990 年代就公开了。
CONNORS = dict(entry_rsi=5, rsi_period=2, n=5, exit_z=0.0, max_bars=10, stop_atr=3.0, risk=0.05)

print("===== 片段 1：2020 年 2 月 26 日 =====")
close = spy["close"]
z = RV.stretch(close, 20)
runs = RV.streak(close)
condition = (z <= -2) & (runs <= -5)
table = RV.setups(close, condition, horizons=(1, 5, 10, 20))
DAY = pd.Timestamp("2020-02-26")
before = table[table["时间"] < DAY]
print(f"「连跌 5 天以上，而且收盘价低于 20 日均线 2 个标准差」——{DAY.date()} 之前出现过 {len(before)} 次：")
print(before.assign(时间=lambda t: t["时间"].dt.date).round(4).to_string(index=False))
print(f"\n那 {len(before)} 次：5 根后 {int((before['5 根后'] > 0).sum())}/{len(before)} 是涨的，"
      f"平均 {before['5 根后'].mean():+.2%}；20 根后 {int((before['20 根后'] > 0).sum())}/{len(before)} 是涨的，"
      f"平均 {before['20 根后'].mean():+.2%}")
print(f"\n今天是 {DAY.date()}：SPY 收在 {close.loc[DAY]:.2f}，连跌 {int(-runs.loc[DAY])} 天，"
      f"偏离 20 日均线 {z.loc[DAY]:.2f} 个标准差，2 日 RSI = {I.rsi(close, 2).loc[DAY]:.2f}")

print("===== 片段 2：揭晓 =====")
row = table[table["时间"] == DAY].iloc[0]
for k in (1, 5, 10, 20):
    print(f"  {k:>2} 根之后：{row[f'{k} 根后']:+.2%}")
bottom = close.loc["2020-02-26":"2020-04-30"].idxmin()
print(f"  期间最低：{row['期间最低']:+.2%}（{bottom.date()} 收在 {close.loc[bottom]:.2f}）")

print("===== 片段 3：短窗口是优势，长窗口是灾难 =====")
print(pd.DataFrame({f"{k} 根后": RV.edge(table, close, horizon=k) for k in (1, 5, 10, 20)}).round(4).to_string())

print("===== 片段 4：这个信号在三个标的上值多少 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    price = frame["close"]
    stretched, streaks = RV.stretch(price, 20), RV.streak(price)
    for label, flag in [("偏离 ≤ −2", stretched <= -2),
                        ("连跌 ≥ 3 天", streaks <= -3),
                        ("偏离 ≤ −2 且连跌 ≥ 3 天", (stretched <= -2) & (streaks <= -3)),
                        ("2 日 RSI < 5", I.rsi(price, 2) < 5)]:
        stats = RV.edge(RV.setups(price, flag, horizons=(5,)), price, horizon=5)
        rows.append({"标的": name, "条件": label, "次数": int(stats["次数"]), "5 根后胜率": stats["胜率"],
                     "5 根后平均": stats["平均"], "基准胜率": stats["基准胜率"],
                     "基准平均": stats["基准平均"], "比基准多赚": stats["比基准多赚"],
                     "最差一次": stats["最差"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 5：方差比解释了两篇的全部结论 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    logs = S.log_returns(frame["close"])
    rows.append({"标的": name, **{f"{k} 天方差比": S.variance_ratio(logs, k) for k in (2, 5, 10, 20, 60)},
                 "1 日自相关": float(S.autocorr(logs, lags=(1,)).iloc[0])})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 6：写成规则 =====")
print(RV.ReversionPlan().describe().to_string())
print()
print(RV.ReversionPlan(**CONNORS).describe().to_string())

print("===== 片段 7：三个标的上跑一遍 =====")
PLANS = {"布林带（偏离 ≤ −2 且连跌 ≥ 3）": RV.ReversionPlan(),
         "RSI(2) < 5（Connors）": RV.ReversionPlan(**CONNORS)}
runs_by_market, rows = {}, []
for name, (frame, periods) in MARKETS.items():
    for label, plan in PLANS.items():
        result = RV.reversion(frame, plan)
        if label.startswith("RSI"):
            runs_by_market[name] = result
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"标的": name, "规则": label, "笔数": len(trades),
                     "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "胜率": float((trades["收益"] > 0).mean()),
                     "中位持仓根数": float(trades["根数"].median()),
                     "在场比例": float(trades["根数"].sum()) / len(curve),
                     "记账误差": result["记账误差"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 8：决策点那一天，规则实际上做了什么 =====")
trades = runs_by_market["SPY"]["交易"]
covid = trades[(trades["进场日"] >= "2020-02-01") & (trades["进场日"] <= "2020-04-30")]
print(covid.assign(进场日=lambda t: t["进场日"].dt.date, 出场日=lambda t: t["出场日"].dt.date)
      [["进场日", "进场价", "出场日", "出场价", "原因", "收益", "根数"]].round(4).to_string(index=False))
print(f"\n同一段时间，买入持有的人从 {close.loc['2020-02-25']:.2f} 拿到 {close.loc[bottom]:.2f}，"
      f"是 {close.loc[bottom] / close.loc['2020-02-25'] - 1:+.2%}")
print(f"这条规则全部 {len(trades)} 笔里最差的五笔：")
print(trades.nsmallest(5, "收益").assign(进场日=lambda t: t["进场日"].dt.date,
                                        出场日=lambda t: t["出场日"].dt.date)
      [["进场日", "出场日", "原因", "收益", "根数"]].round(4).to_string(index=False))

print("===== 片段 9：收益结构，和第 31 篇正好反过来 =====")
print(pd.DataFrame({name: T.r_profile(result["交易"]["收益"])
                    for name, result in runs_by_market.items()}).round(4).to_string())
print("\n⚠️ 这里的「R」列装的是**收益率**不是 R 倍数（表头是 r_profile 的固定写法）。")

print("===== 片段 10：把最亏的几笔拿掉 =====")
for name, result in runs_by_market.items():
    print(f"--- {name} ---")
    print(RV.worst_trades(result["交易"]["收益"]).round(4).to_string(index=False))

print("===== 片段 11：凹性 =====")
for name, (frame, periods) in MARKETS.items():
    strategy = runs_by_market[name]["资金曲线"].pct_change().dropna()
    market = frame["close"].pct_change().reindex(strategy.index)
    print(f"--- {name} ---")
    print(T.convexity(strategy, market, buckets=5, window=20).round(4).to_string())

print("===== 片段 12：止损和时间出场各自在做什么 =====")
rows = []
for label, extra in [("原样（3 ATR 止损 + 10 根时间出场）", {}),
                     ("去掉止损", dict(stop_atr=None, fraction=1.0)),
                     ("去掉时间出场（最多拿 250 根）", dict(max_bars=250)),
                     ("两个都去掉", dict(stop_atr=None, fraction=1.0, max_bars=250))]:
    for name, (frame, periods) in MARKETS.items():
        result = RV.reversion(frame, RV.ReversionPlan(**{**CONNORS, **extra}))
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"设定": label, "标的": name, "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "胜率": float((trades["收益"] > 0).mean()),
                     "最差一笔": float(trades["收益"].min()),
                     "偏度": float(trades["收益"].skew())})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 13：参数曲面、walk-forward 与 PBO =====")
GRID = [(threshold, window) for threshold in [2, 5, 10, 15, 20, 25] for window in [3, 5, 10, 20]]
DEFAULT = (5, 5)
print(f"网格 {len(GRID)} 组（RSI 阈值 × 出场均线长度），默认那一组是 {DEFAULT}")
rows = []
for name, (frame, periods) in MARKETS.items():
    daily = np.array([RV.reversion(frame, RV.ReversionPlan(**{**CONNORS, "entry_rsi": t, "n": w}))
                      ["资金曲线"].pct_change().reindex(frame.index).fillna(0).to_numpy()
                      for t, w in GRID])
    scores = daily.mean(axis=1) / daily.std(axis=1, ddof=1) * np.sqrt(periods)
    face = V.surface(pd.DataFrame({"阈值": [t for t, w in GRID], "出场均线": [w for t, w in GRID],
                                   "夏普": scores}), "阈值", "出场均线", "夏普")
    around = V.neighbourhood(face, DEFAULT)
    splits = V.walk_forward(daily.shape[1], int(periods * 2), periods)
    picked = V.walk_forward_run(daily, splits, names=GRID)
    stitched = V.stitch(daily, splits, [GRID.index(p) for p in picked["选了谁"]])
    rolling = RP.to_curve(pd.Series(stitched, index=pd.RangeIndex(len(stitched))))
    held = daily[GRID.index(DEFAULT), splits[0][1].start:splits[-1][1].stop]
    kept = RP.to_curve(pd.Series(held, index=pd.RangeIndex(len(held))))
    rows.append({"标的": name, "默认 (5,5) 的夏普": scores[GRID.index(DEFAULT)],
                 "排第几": f"{int((scores > scores[GRID.index(DEFAULT)]).sum()) + 1}/{len(GRID)}",
                 "落差": around["落差"], "网格中位": float(np.median(scores)),
                 "亏钱的格子": float((daily.sum(axis=1) < 0).mean()),
                 "白捡的门槛": V.expected_max_sharpe(len(GRID), scores.std()),
                 "PBO": V.pbo(daily, 8)["过拟合概率 PBO"],
                 "每年重挑的年化": RP.annual_return(rolling, periods),
                 "一直用 (5,5) 的年化": RP.annual_return(kept, periods)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 14：蒙特卡洛，以及对照的块长该取多少 =====")


def fake_markets(frame: pd.DataFrame, block: int, n: int = N_PATHS, seed: int = 32):
    """造假数据：四个价按同一个比例缩放，保住 K 线的形状。"""
    for path in V.synthetic_close(frame["close"], n=n, block=block, seed=seed):
        scale = path / frame["close"].to_numpy()
        yield pd.DataFrame({c: frame[c].to_numpy() * scale for c in ["open", "high", "low", "close"]},
                           index=frame.index)


rows = []
for name, (frame, periods) in MARKETS.items():
    real = runs_by_market[name]
    actual = RP.annual_return(real["资金曲线"], periods)
    row = {"标的": name, "真实年化": actual, "中位持仓根数": float(real["交易"]["根数"].median())}
    for block in (1, 2, 5, 20, 60):
        fakes = np.array([RP.annual_return(RV.reversion(fake, RV.ReversionPlan(**CONNORS))["资金曲线"],
                                           periods) for fake in fake_markets(frame, block)])
        row[f"块长 {block} 的 p"] = float((fakes >= actual).mean())
        if block == 1:
            row["块长 1 的假数据中位"] = float(np.median(fakes))
    rows.append(row)
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("\n同样两种块长，对第 31 篇那套持仓十几根的海龟：")
rows = []
for name, (frame, periods) in MARKETS.items():
    real = T.turtle(frame, T.TurtlePlan())
    actual = RP.annual_return(real["资金曲线"], periods)
    row = {"标的": name, "真实年化": actual, "中位持仓根数": float(real["交易"]["根数"].median())}
    for block in (1, 20):
        fakes = np.array([RP.annual_return(T.turtle(fake, T.TurtlePlan())["资金曲线"], periods)
                          for fake in fake_markets(frame, block, n=60)])
        row[f"块长 {block} 的 p"] = float((fakes >= actual).mean())
    rows.append(row)
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 15：和趋势跟随放进同一个账户 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    trend_curve = T.turtle(frame, T.TurtlePlan())["资金曲线"]
    mean_curve = runs_by_market[name]["资金曲线"]
    a, b = trend_curve.pct_change().dropna(), mean_curve.pct_change().dropna()
    shared = a.index.intersection(b.index)
    together = float(((a.reindex(shared) != 0) & (b.reindex(shared) != 0)).mean())
    mixed = RV.blend({"趋势跟随": trend_curve, "均值回归": mean_curve}, [0.5, 0.5])
    for label, curve in [("趋势跟随（第 31 篇）", trend_curve), ("均值回归（这一篇）", mean_curve),
                         ("五五开，每月再平衡", mixed)]:
        daily = curve.pct_change().dropna()
        rows.append({"标的": name, "账户": label, "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve), "夏普": RP.sharpe(daily, periods),
                     "卡玛": RP.calmar(curve, periods),
                     "两条腿的相关": a.reindex(shared).corr(b.reindex(shared)) if label.startswith("五五") else np.nan,
                     "同时在场": together if label.startswith("五五") else np.nan})
print(pd.DataFrame(rows).round(4).to_string(index=False))
