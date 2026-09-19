"""第 31 篇正文里的代码片段（在 talab 项目根目录运行，数据沿用第 3、28 篇）。"""
import glob

import numpy as np
import pandas as pd
from talab import (backtest as BT, costs as C, data as D, indicators as I,
                   report as RP, structure as ST, trend as T, validate as V)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
N_PATHS = 100

btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.adjust_total_return(D.unadjust_splits(D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json"),
                                               D.SPLITS["AAPL"]), D.SPLITS["AAPL"],
                             D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json"))
MARKETS = {"SPY": (spy, 252), "AAPL": (aapl, 252), "BTC": (btc, 365)}

print("===== 片段 1：过去十次突破 =====")
plain = T.TurtlePlan(max_units=1)                 # 先不加仓，一次只有一个单位
history = T.turtle(btc, plain)["交易"]
window = history.iloc[34:44]
print(window[["进场日", "第一个单位的价", "出场日", "出场价", "原因", "R", "根数"]]
      .assign(进场日=lambda t: t["进场日"].dt.date, 出场日=lambda t: t["出场日"].dt.date)
      .round(3).to_string(index=False))
wins, losses = window.loc[window["R"] > 0, "R"], window.loc[window["R"] <= 0, "R"]
print(f"\n{window['进场日'].iloc[0].date()} 到 {window['出场日'].iloc[-1].date()}，十三个月，十次突破："
      f"{len(wins)} 次走出去了、{len(losses)} 次是假的")
print(f"合计 {window['R'].sum():+.2f}R —— 赚的三笔 {wins.sum():+.2f}R，亏的七笔 {losses.sum():+.2f}R")
print(f"而这 {window['R'].sum():+.2f}R 里有 {wins.max():+.2f}R 来自 {window.loc[window['R'].idxmax(), '进场日'].date()} "
      f"那一笔；把它拿掉，另外九笔合计 {window['R'].sum() - wins.max():+.2f}R")
signal = history.iloc[44]
print(f"\n现在是 {signal['进场日'].date()}，BTC 又一次碰到 20 日通道上轨 "
      f"{signal['第一个单位的价']:,.2f}。买不买？")

print("===== 片段 2：一次突破，有多大概率走得出去 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    for n in (20, 55):
        table = T.breakouts(frame, n, horizon=20)
        stats = T.follow_through(table)
        rows.append({"标的": name, "通道": f"{n} 日", "突破次数": int(stats["突破次数"]),
                     "假突破比例": stats["假突破比例"], "真的那些平均涨": stats["真的那些平均涨"],
                     "假的那些平均跌": stats["假的那些平均跌"], "全部平均": stats["全部平均"],
                     "最大顺势中位": stats["最大顺势中位"], "最大逆势中位": stats["最大逆势中位"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 3：揭晓 =====")
print(f"{signal['进场日'].date()} 买在 {signal['第一个单位的价']:,.2f}，"
      f"{signal['出场日'].date()} 按 {signal['原因']} 卖在 {signal['出场价']:,.2f}，"
      f"拿了 {int(signal['根数'])} 根 K 线")
print(f"R = {signal['R']:+.2f}，10 万美元的账户上赚了 {signal['盈亏']:,.0f}")
print(f"这一笔在全部 {len(history)} 笔里排第 {int((history['R'] > signal['R']).sum()) + 1}")
print(f"同期 BTC：{btc['close'].loc[signal['进场日']]:,.0f} → {btc['close'].loc[signal['出场日']]:,.0f}")
print(f"如果只有这一笔没做：九年合计从 {history['R'].sum():.1f}R 变成 "
      f"{history['R'].sum() - signal['R']:.1f}R")

print("===== 片段 4：海龟法则 =====")
print(T.TurtlePlan().describe().to_string())
print()
print(T.TurtlePlan(entry=55, exit=20).describe().to_string())

print("===== 片段 5：「当根成交」值多少钱 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    for how in ("touch", "next_open"):
        result = T.turtle(frame, T.TurtlePlan(fill=how))
        curve = result["资金曲线"]
        rows.append({"标的": name, "成交方式": {"touch": "碰到通道就成交", "next_open": "等下一根开盘"}[how],
                     "年化": RP.annual_return(curve, periods),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "最大回撤": RP.max_drawdown(curve), "笔数": len(result["交易"]),
                     "合计 R": result["交易"]["R"].sum(), "记账误差": result["记账误差"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 6：三个标的上跑一遍 =====")
runs, rows = {}, []
for name, (frame, periods) in MARKETS.items():
    result = T.turtle(frame, T.TurtlePlan())
    runs[name] = result
    curve, trades = result["资金曲线"], result["交易"]
    rows.append({"标的": name, "年化": RP.annual_return(curve, periods),
                 "最大回撤": RP.max_drawdown(curve),
                 "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                 "卡玛": RP.calmar(curve, periods), "笔数": len(trades),
                 "在场比例": float(trades["根数"].sum()) / len(curve),
                 "期末": float(curve.iloc[-1]), "记账误差": result["记账误差"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 7：收益结构 =====")
print(pd.DataFrame({name: T.r_profile(result["交易"]["R"]) for name, result in runs.items()}).round(3).to_string())

print("===== 片段 8：收益集中在几笔上 =====")
for name, result in runs.items():
    print(f"--- {name} ---")
    print(T.contribution(result["交易"]["R"]).round(4).to_string(index=False))

print("===== 片段 9：凸性 =====")
for name, (frame, periods) in MARKETS.items():
    for label, plan in [("只做多", T.TurtlePlan()), ("多空都做", T.TurtlePlan(side="both"))]:
        curve = runs[name]["资金曲线"] if label == "只做多" else T.turtle(frame, plan)["资金曲线"]
        strategy = curve.pct_change().dropna()
        market = frame["close"].pct_change().reindex(strategy.index)
        print(f"--- {name}（{label}）---")
        print(T.convexity(strategy, market, buckets=5, window=20).round(4).to_string())

print("===== 片段 10：金字塔加仓值不值 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    for units, risk in [(1, 0.04), (2, 0.02), (4, 0.01)]:
        result = T.turtle(frame, T.TurtlePlan(max_units=units, risk=risk))
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"标的": name, "最多几个单位": units, "每个单位冒的风险": risk,
                     "总风险": units * risk, "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "平均用了几个单位": trades["单位数"].mean(), "最大一笔 R": trades["R"].max()})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 11：什么时候有效 =====")
for name, (frame, periods) in MARKETS.items():
    trades = runs[name]["交易"].copy()
    trades["效率比"] = ST.efficiency_ratio(frame["close"], 20).reindex(trades["进场日"]).to_numpy()
    groups = pd.qcut(trades["效率比"], 3, labels=["低（来回震荡）", "中", "高（一直朝一个方向）"])
    print(f"--- {name} ---")
    print(trades.groupby(groups, observed=True)["R"].agg(
        笔数="size", 胜率=lambda x: float((x > 0).mean()), 平均="mean", 中位="median", 合计="sum"
    ).round(3).to_string())

print("===== 片段 12：做空那一半 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    for side in ("long", "short", "both"):
        result = T.turtle(frame, T.TurtlePlan(side=side, risk=0.025))
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"标的": name, "方向": {"long": "只做多", "short": "只做空", "both": "多空都做"}[side],
                     "年化": RP.annual_return(curve, periods), "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods), "笔数": len(trades),
                     "胜率": float((trades["R"] > 0).mean()), "合计 R": trades["R"].sum()})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 13：参数曲面与 walk-forward =====")
GRID = [(e, x) for e in [10, 15, 20, 30, 40, 55, 80, 100] for x in [5, 10, 15, 20, 30, 40] if x < e]
DEFAULT = (20, 10)
print(f"网格 {len(GRID)} 组（进场 10–100 日 × 出场 5–40 日，出场必须比进场短）")
rows, matrices = [], {}
for name, (frame, periods) in MARKETS.items():
    daily = np.array([T.turtle(frame, T.TurtlePlan(entry=e, exit=x))["资金曲线"]
                      .pct_change().reindex(frame.index).fillna(0).to_numpy() for e, x in GRID])
    matrices[name] = daily
    scores = daily.mean(axis=1) / daily.std(axis=1, ddof=1) * np.sqrt(periods)
    table = pd.DataFrame({"进场": [e for e, x in GRID], "出场": [x for e, x in GRID], "夏普": scores})
    face = V.surface(table, "进场", "出场", "夏普")
    around = V.neighbourhood(face, DEFAULT)
    splits = V.walk_forward(daily.shape[1], int(periods * 2), periods)
    picked = V.walk_forward_run(daily, splits, names=GRID)
    stitched = V.stitch(daily, splits, [GRID.index(p) for p in picked["选了谁"]])
    rolling = RP.to_curve(pd.Series(stitched, index=pd.RangeIndex(len(stitched))))
    held = daily[GRID.index(DEFAULT), splits[0][1].start:splits[-1][1].stop]
    kept = RP.to_curve(pd.Series(held, index=pd.RangeIndex(len(held))))
    rows.append({"标的": name, "1983 年那组 (20,10)": scores[GRID.index(DEFAULT)],
                 "排第几": f"{int((scores > scores[GRID.index(DEFAULT)]).sum()) + 1}/{len(GRID)}",
                 "邻居中位": around["邻居中位"], "落差": around["落差"],
                 "网格最好": scores.max(), "网格中位": float(np.median(scores)),
                 "亏钱的格子": float((daily.sum(axis=1) < 0).mean()),
                 "白捡的门槛": V.expected_max_sharpe(len(GRID), scores.std()),
                 "PBO": V.pbo(daily, 16)["过拟合概率 PBO"],
                 "每年重挑的年化": RP.annual_return(rolling, periods),
                 "一直用 (20,10) 的年化": RP.annual_return(kept, periods)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 14：蒙特卡洛——把趋势拆掉 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    real = runs[name]["资金曲线"]
    real_annual = RP.annual_return(real, periods)
    real_sharpe = RP.sharpe(real.pct_change().dropna(), periods)
    fakes = []
    for path in V.synthetic_close(frame["close"], n=N_PATHS, block=20, seed=31):
        scale = path / frame["close"].to_numpy()          # 四个价按同一个比例缩放，保住 K 线的形状
        fake = pd.DataFrame({c: frame[c].to_numpy() * scale for c in ["open", "high", "low", "close"]},
                            index=frame.index)
        curve = T.turtle(fake, T.TurtlePlan())["资金曲线"]
        fakes.append((RP.annual_return(curve, periods),
                      RP.sharpe(curve.pct_change().dropna(), periods)))
    annuals = np.array([a for a, s in fakes])
    sharpes = np.array([s for a, s in fakes])
    rows.append({"标的": name, "真实年化": real_annual, "假数据年化中位": float(np.median(annuals)),
                 "假数据 95% 分位": float(np.percentile(annuals, 95)),
                 "真实夏普": real_sharpe, "假数据夏普中位": float(np.median(sharpes)),
                 "假的比真的好的比例": float((annuals >= real_annual).mean())})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 15：含成本的成绩单，和主线 v4、买入持有并排 =====")
schedule = pd.Series({"SEC 占卖出金额": 20.60 / 1e6, "TAF 每股": 0.000166, "TAF 每笔上限": 8.30})
us_cost = C.us_stock(100.0, 100.0, "sell", spread_bp=1.0, sec_rate=schedule["SEC 占卖出金额"],
                     taf_per_share=schedule["TAF 每股"], taf_cap=schedule["TAF 每笔上限"])["占名义价值"]
btc_cost = C.crypto(1.0, "现货 taker", spread_bp=C.BTC_PERP_SPREAD_BP)["占名义价值"] + 0.00097 / 2
rows = []
for name, (frame, periods) in MARKETS.items():
    price = frame["close"]
    fee = btc_cost if name == "BTC" else us_cost
    for label, plan in [("海龟（原版：每单位 1%，最多 4 个）", T.TurtlePlan(fee_rate=fee)),
                        ("海龟（和主线同样的风险预算：2.5% × 4）", T.TurtlePlan(risk=0.025, fee_rate=fee))]:
        result = T.turtle(frame, plan)
        curve, trades = result["资金曲线"], result["交易"]
        rows.append({"标的": name, "策略": label, "年化": RP.annual_return(curve, periods),
                     "最大回撤": RP.max_drawdown(curve),
                     "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                     "卡玛": RP.calmar(curve, periods), "笔数": len(trades),
                     "逐笔的 t 值": RP.trade_metrics(trades["R"])["t 值"],
                     "手续费": result["手续费合计"]})
    plan = BT.Plan(entry=((I.sma(price, 50) > I.sma(price, 200))
                          & (price >= price.rolling(20).max())).fillna(False),
                   exit=I.cross_below(I.sma(price, 50), I.sma(price, 200)).fillna(False),
                   stop="chandelier", k=3.0, trigger="close", sizing="risk",
                   risk_per_trade=0.10, fee_rate=fee)
    main = BT.run(frame, plan, 100_000.0)
    curve = main["资金曲线"]
    rows.append({"标的": name, "策略": "主线 v4", "年化": RP.annual_return(curve, periods),
                 "最大回撤": RP.max_drawdown(curve),
                 "夏普": RP.sharpe(curve.pct_change().dropna(), periods),
                 "卡玛": RP.calmar(curve, periods), "笔数": len(main["交易"]),
                 "逐笔的 t 值": RP.trade_metrics(main["交易"]["收益"])["t 值"],
                 "手续费": main["手续费合计"]})
    rows.append({"标的": name, "策略": "买入持有", "年化": RP.annual_return(price, periods),
                 "最大回撤": RP.max_drawdown(price),
                 "夏普": RP.sharpe(price.pct_change().dropna(), periods),
                 "卡玛": RP.calmar(price, periods), "笔数": 1, "逐笔的 t 值": np.nan, "手续费": 0.0})
print(pd.DataFrame(rows).round(4).to_string(index=False))
