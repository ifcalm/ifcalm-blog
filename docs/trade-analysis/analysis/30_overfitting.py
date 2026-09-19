"""第 30 篇正文里的代码片段（在 talab 项目根目录运行，数据沿用第 3、28 篇）。"""
import glob

import numpy as np
import pandas as pd
from talab import (backtest as BT, costs as C, data as D, indicators as I,
                   report as RP, validate as V)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
N_PATHS = 200

print("===== 片段 1：一条两年的回测 =====")
btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
close = btc["close"]
FASTS, SLOWS = range(5, 51), range(20, 251)
PAIRS = [(f, s) for f in FASTS for s in SLOWS if s > f]


def sma_matrix(values: np.ndarray, windows) -> np.ndarray:
    """一次算出所有窗口长度的简单移动平均，返回 `(窗口个数, 根数)`。"""
    cumulative = np.concatenate([[0.0], np.cumsum(values)])
    out = np.full((len(windows), len(values)), np.nan)
    for k, n in enumerate(windows):
        out[k, n - 1:] = (cumulative[n:] - cumulative[:-n]) / n
    return out


def grid_returns(values: np.ndarray, pairs, chunk: int = 2000) -> np.ndarray:
    """一万组均线参数的每日收益，返回 `(参数组数, 根数 − 1)`。

    快线在慢线上方就做多、下方就做空（±1），按第 27 篇的规矩推迟一根成交。
    ⚠️ 一万次回测不用跑一万遍：均线只有 277 种，先全算出来，剩下的只是比大小。
    """
    windows = sorted({w for pair in pairs for w in pair})
    where = {w: k for k, w in enumerate(windows)}
    averages = sma_matrix(values, windows)
    step = np.diff(values) / values[:-1]
    out = np.empty((len(pairs), len(step)))
    for a in range(0, len(pairs), chunk):
        part = pairs[a:a + chunk]
        fast = [where[f] for f, s in part]
        slow = [where[s] for f, s in part]
        position = (averages[fast] > averages[slow]).astype(float) * 2 - 1
        position[np.isnan(averages[fast]) | np.isnan(averages[slow])] = 0.0
        out[a:a + chunk] = position[:, :-1] * step
    return out


DAILY = grid_returns(close.to_numpy(), PAIRS)
DATES = close.index[1:]
WHERE = {pair: k for k, pair in enumerate(PAIRS)}


def window(low: str, high: str | None = None) -> np.ndarray:
    inside = DATES >= pd.Timestamp(low, tz="UTC")
    return inside & (DATES <= pd.Timestamp(high, tz="UTC")) if high else inside


def annual(rows: np.ndarray) -> np.ndarray:
    return np.prod(1 + rows, axis=1) ** (365 / rows.shape[1]) - 1


def sharpe(rows: np.ndarray, periods_per_year: int = 365) -> np.ndarray:
    return rows.mean(axis=1) / rows.std(axis=1, ddof=1) * np.sqrt(periods_per_year)


INSIDE, OUTSIDE = window("2021-01-01", "2022-12-31"), window("2023-01-01")
train, test = DAILY[:, INSIDE], DAILY[:, OUTSIDE]
in_annual, in_sharpe = annual(train), sharpe(train)
out_annual = annual(test)
best = int(in_annual.argmax())
curve = RP.to_curve(pd.Series(train[best], index=close.index[1:][INSIDE]))
print(f"BTC {close.loc['2021-01-01':'2022-12-31'].index[0].date()} 到 "
      f"{close.loc['2021-01-01':'2022-12-31'].index[-1].date()}："
      f"价格 {close.loc['2021-01-01']:,.0f} → {close.loc['2022-12-31']:,.0f}，"
      f"买入持有年化 {RP.annual_return(close.loc['2021-01-01':'2022-12-31'], 365):.2%}")
print(f"在 {len(PAIRS):,} 组（快线 5–50 × 慢线 20–250）里选年化最高的一组 = {PAIRS[best]}")
print(RP.metrics(curve, 365).drop(["起", "止"]).round(4).to_string())

print("===== 片段 2：第一刀，看一眼邻居 =====")
table = pd.DataFrame({"快线": [f for f, s in PAIRS], "慢线": [s for f, s in PAIRS], "年化": in_annual})
grid = V.surface(table, "快线", "慢线", "年化")
print(grid.loc[29:33, 34:38].round(4).to_string())
print()
print(V.neighbourhood(grid, PAIRS[best]).round(4).to_string())
print(f"\n全网格 {len(PAIRS):,} 格：年化中位 {np.median(in_annual):.2%}，"
      f"90% 分位 {np.percentile(in_annual, 90):.2%}，亏钱的占 {(in_annual < 0).mean():.1%}")

print("===== 片段 3：尖峰是样本短的症状 =====")
rows = []
for years in [1, 2, 3, 5, 9]:
    piece = DAILY[:, -int(365 * years):]
    values = annual(piece)
    top = int(values.argmax())
    fast, slow = PAIRS[top]
    neighbours = [values[WHERE[(f, s)]] for f in (fast - 1, fast, fast + 1)
                  for s in (slow - 1, slow, slow + 1) if (f, s) != (fast, slow) and (f, s) in WHERE]
    rows.append({"回测几年": years, "最好的一格": f"({fast},{slow})", "年化": values[top],
                 "邻居中位": np.median(neighbours), "落差": values[top] - np.median(neighbours),
                 "落差占年化": (values[top] - np.median(neighbours)) / values[top],
                 "全网格中位": np.median(values)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 4：第二刀，样本外 =====")
plateau = V.plateaus(grid)
rows = []
for label, cell in [("按「这一格最高」挑", PAIRS[best]),
                    ("按「邻域中位最高」挑", (int(plateau.iloc[0]["快线"]), int(plateau.iloc[0]["慢线"]))),
                    ("课程默认（第 12 篇的 50/200，没挑过）", (50, 200))]:
    k = WHERE[cell]
    rows.append({"挑法": label, "参数": f"({cell[0]},{cell[1]})", "样本内年化": in_annual[k],
                 "样本外年化": out_annual[k], "样本外排名": int((out_annual > out_annual[k]).sum()) + 1})
rows.append({"挑法": "全网格中位（什么都不挑）", "参数": f"{len(PAIRS):,} 格",
             "样本内年化": np.median(in_annual), "样本外年化": np.median(out_annual),
             "样本外排名": len(PAIRS) // 2})
print(pd.DataFrame(rows).round(4).to_string(index=False))
order = np.argsort(-in_annual)
ladder = [{"样本内前几名": n, "样本外年化中位": np.median(out_annual[order[:n]])}
          for n in [10, 50, 100, 500, 1000, 5000]]
ladder.append({"样本内前几名": len(PAIRS), "样本外年化中位": np.median(out_annual)})
print(pd.DataFrame(ladder).round(4).to_string(index=False))
print(f"\n样本内排名和样本外排名的秩相关："
      f"{pd.Series(in_annual).rank().corr(pd.Series(out_annual).rank()):.4f}")

print("===== 片段 5：第三刀，walk-forward =====")
start = int(np.argmax(DATES >= pd.Timestamp("2018-01-01", tz="UTC")))   # 前 250 根留给均线预热
rolling = DAILY[:, start:]
rows = []
for anchored in (False, True):
    for train_bars, test_bars in [(365, 182), (730, 365), (1095, 365)]:
        splits = V.walk_forward(rolling.shape[1], train_bars, test_bars, anchored=anchored)
        picked = V.walk_forward_run(rolling, splits, names=PAIRS)
        stitched = V.stitch(rolling, splits, [PAIRS.index(p) for p in picked["选了谁"]])
        equity = RP.to_curve(pd.Series(stitched, index=pd.RangeIndex(len(stitched))))
        rows.append({"训练窗口": "锚定（越考越长）" if anchored else "滚动（固定长度）",
                     "训练根数": train_bars, "考卷根数": test_bars, "几段": len(splits),
                     "训练期夏普中位": picked["训练期夏普"].median() * np.sqrt(365),
                     "考卷夏普中位": picked["考卷夏普"].median() * np.sqrt(365),
                     "样本外年化": RP.annual_return(equity, 365),
                     "样本外最大回撤": RP.max_drawdown(equity)})
print(pd.DataFrame(rows).round(4).to_string(index=False))
splits = V.walk_forward(rolling.shape[1], 730, 365, anchored=False)
picked = V.walk_forward_run(rolling, splits, names=PAIRS)
picked["训练期夏普"] *= np.sqrt(365)
picked["考卷夏普"] *= np.sqrt(365)
print()
print(picked.round(4).to_string(index=False))
first_test = DATES[start:][splits[0][1].start]
tail = window(str(first_test.date()))
print(f"\n同一段（{first_test.date()} 起）的对照：")
for label, pair in [("课程默认 (50,200)", (50, 200)), ("九年全样本最好的 (8,43)（这是作弊）", (8, 43)),
                    ("决策点那一组 (31,36)", (31, 36))]:
    piece = DAILY[WHERE[pair], tail]
    equity = RP.to_curve(pd.Series(piece, index=pd.RangeIndex(len(piece))))
    print(f"  {label:<34} 年化 {RP.annual_return(equity, 365):>8.2%}   "
          f"夏普 {RP.sharpe(equity.pct_change().dropna(), 365):.4f}")
print(f"  {'买入持有':<34} 年化 {RP.annual_return(close.loc[first_test:], 365):>8.2%}   "
      f"夏普 {RP.sharpe(close.loc[first_test:].pct_change().dropna(), 365):.4f}")

print("===== 片段 6：第四刀，蒙特卡洛 =====")
warm = close.loc["2020-11-01":"2022-12-31"]          # 多留 250 根给均线预热
real_annual, real_sharpe = in_annual[best], in_sharpe[best]
rows = []
for block, label in [(1, "打散（连波动率聚集也没了）"), (20, "20 天的块（波动率聚集还在）")]:
    tops_annual, tops_sharpe = [], []
    for path in V.synthetic_close(warm, n=N_PATHS, block=block, seed=30):
        piece = grid_returns(path, PAIRS)[:, -730:]
        tops_annual.append(annual(piece).max())
        tops_sharpe.append(sharpe(piece).max())
    tops_annual, tops_sharpe = np.array(tops_annual), np.array(tops_sharpe)
    beaten = float((tops_annual >= real_annual).mean())
    rows.append({"假数据怎么造的": label, "「最好一组」年化中位": np.median(tops_annual),
                 "90% 分位": np.percentile(tops_annual, 90), "最大": tops_annual.max(),
                 "比真实还好的比例": beaten, "夏普中位": np.median(tops_sharpe),
                 "夏普比真实还好的比例": float((tops_sharpe >= real_sharpe).mean())})
print(f"真实数据上「最好的一组」：年化 {real_annual:.2%}，夏普 {real_sharpe:.4f}")
monte_carlo = pd.DataFrame(rows)
print(monte_carlo.round(4).to_string(index=False))

print("===== 片段 7：第五刀，多重检验 =====")
print(f"{len(PAIRS):,} 组参数的夏普比率：中位 {np.median(in_sharpe):.4f}，"
      f"标准差 {in_sharpe.std():.4f}，最大 {in_sharpe.max():.4f}")
print(f"完全没本事时，试 {len(PAIRS):,} 次「最好的那次」期望是 "
      f"{V.expected_max_sharpe(len(PAIRS), in_sharpe.std()):.4f}")
rows = [V.deflated_sharpe(real_sharpe, n, train.shape[1], in_sharpe.std(),
                          skew=float(pd.Series(train[best]).skew()),
                          kurtosis=float(pd.Series(train[best]).kurt()) + 3,
                          periods_per_year=365).rename(f"试了 {n:,} 次")
        for n in [2, 100, 1000, len(PAIRS)]]
print(pd.concat(rows, axis=1).round(4).to_string())

print("===== 片段 8：第六刀，回测过拟合概率 =====")
rows = [V.pbo(train, chunks).rename(f"切成 {chunks} 块") for chunks in (8, 12, 16)]
print(pd.concat(rows, axis=1).round(4).to_string())

print("===== 片段 9：六刀砍完，还剩什么 =====")
verdict = pd.DataFrame([
    {"检查": "① 邻居（落差 ÷ 年化）", "这条策略": f"{V.neighbourhood(grid, PAIRS[best])['落差'] / real_annual:.1%}",
     "该是多少": "越接近 0 越好", "过了吗": "否"},
    {"检查": "② 样本外年化", "这条策略": f"{out_annual[best]:.2%}",
     "该是多少": f"网格中位 {np.median(out_annual):.2%}", "过了吗": "否"},
    {"检查": "③ walk-forward 考卷夏普中位", "这条策略": f"{picked['考卷夏普'].median():.4f}",
     "该是多少": f"训练期是 {picked['训练期夏普'].median():.4f}", "过了吗": "否"},
    {"检查": "④ 蒙特卡洛：没有趋势的假数据也能做到",
     "这条策略": f"{monte_carlo['比真实还好的比例'].max():.1%}", "该是多少": "低于 5%", "过了吗": "否"},
    {"检查": "⑤ 多重检验：白捡的门槛（年化夏普）",
     "这条策略": f"{real_sharpe:.4f}", "该是多少": f"门槛 {V.expected_max_sharpe(len(PAIRS), in_sharpe.std()):.4f}",
     "过了吗": "勉强"},
    {"检查": "⑥ 回测过拟合概率 PBO", "这条策略": f"{V.pbo(train, 16)['过拟合概率 PBO']:.4f}",
     "该是多少": "低于 0.5 才有意义", "过了吗": "否"},
])
print(verdict.to_string(index=False))

print("===== 片段 10：主线策略 v4 走一遍 =====")
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.adjust_total_return(D.unadjust_splits(D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json"),
                                               D.SPLITS["AAPL"]), D.SPLITS["AAPL"],
                             D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json"))
MAIN = [(f, s, b, k) for f in [20, 30, 40, 50, 60, 80] for s in [100, 150, 200, 250, 300]
        for b in [5, 10, 20, 40, 60] for k in [2.0, 2.5, 3.0, 3.5, 4.0]]
DEFAULT = (50, 200, 20, 3.0)
print(f"主线网格 {len(MAIN)} 组（快线 × 慢线 × 突破窗口 × 吊灯倍数），默认那一组是 {DEFAULT}")
rows, surfaces = [], {}
for name, frame, periods in [("SPY", spy, 252), ("AAPL", aapl, 252), ("BTC", btc, 365)]:
    price = frame["close"]
    curves = []
    for fast, slow, breakout, k in MAIN:
        plan = BT.Plan(entry=((I.sma(price, fast) > I.sma(price, slow))
                              & (price >= price.rolling(breakout).max())).fillna(False),
                       exit=I.cross_below(I.sma(price, fast), I.sma(price, slow)).fillna(False),
                       stop="chandelier", k=k, trigger="close", sizing="risk", risk_per_trade=0.10)
        curves.append(BT.run(frame, plan, 100_000.0)["资金曲线"].pct_change().fillna(0).to_numpy())
    matrix = np.array(curves)
    scores = sharpe(matrix, periods)
    here = MAIN.index(DEFAULT)
    slice_table = pd.DataFrame([{"快线": f, "慢线": s, "夏普": scores[k]}
                                for k, (f, s, b, kk) in enumerate(MAIN)
                                if (b, kk) == (DEFAULT[2], DEFAULT[3])])
    face = V.surface(slice_table, "快线", "慢线", "夏普")
    surfaces[name] = face
    around = V.neighbourhood(face, (DEFAULT[0], DEFAULT[1]))
    rows.append({"标的": name, "默认那一组的夏普": scores[here],
                 "排第几": f"{int((scores > scores[here]).sum()) + 1}/{len(MAIN)}",
                 "邻居中位": around["邻居中位"], "落差": around["落差"],
                 "网格最好": scores.max(), "白捡的门槛": V.expected_max_sharpe(len(MAIN), scores.std()),
                 "最好的 DSR": V.deflated_sharpe(scores.max(), len(MAIN), matrix.shape[1],
                                               scores.std(), periods_per_year=periods)["打过折的夏普 DSR"],
                 "PBO": V.pbo(matrix, 16)["过拟合概率 PBO"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("\nBTC 上固定「突破 20 日新高、吊灯 3 ATR」时的夏普曲面（行是快线，列是慢线）：")
print(surfaces["BTC"].round(3).to_string())

print("===== 片段 11：实验三，一份交上来的策略 =====")
FAST3 = [10, 20, 30, 40, 50, 60, 80, 100]
SLOW3 = [100, 120, 150, 180, 200, 220, 250, 300]
COMBOS = [(f, s, h, l) for f in FAST3 for s in SLOW3 if s > f
          for h in [10, 20, 40, 60, 90] for l in [10, 20, 40, 60, 90]]
values = close.to_numpy()
averages = {n: close.rolling(n).mean().to_numpy() for n in set(FAST3) | set(SLOW3)}
highs = {n: close.rolling(n).max().to_numpy() for n in [10, 20, 40, 60, 90]}
lows = {n: close.rolling(n).min().to_numpy() for n in [10, 20, 40, 60, 90]}
step = np.diff(values) / values[:-1]
EXP3 = np.empty((len(COMBOS), len(step)))
for k, (fast, slow, high, low) in enumerate(COMBOS):
    state = np.full(len(values), np.nan)
    state[values >= highs[high]] = 1.0                 # 创新高就进
    state[values <= lows[low]] = 0.0                   # 破新低就走
    holding = pd.Series(state).ffill().fillna(0.0).to_numpy() * (averages[fast] > averages[slow])
    holding[np.isnan(averages[fast]) | np.isnan(averages[slow])] = 0.0
    EXP3[k] = holding[:-1] * step
LOW3, HIGH3 = "2018-01-01", "2021-12-31"
inside3, outside3 = window(LOW3, HIGH3), window("2022-01-01")
train3, test3 = EXP3[:, inside3], EXP3[:, outside3]
scores3, annual3, out3 = sharpe(train3), annual(train3), annual(test3)
pick = int(scores3.argmax())
curve3 = RP.to_curve(pd.Series(train3[pick], index=close.index[1:][inside3]))
print("「我做了一条 BTC 日线策略：快线在慢线上方（大方向向上）、收盘创 N 日新高就买入，")
print(f"  跌破 M 日新低就卖出。四个参数在 {len(COMBOS):,} 组里选夏普最高的一组 = {COMBOS[pick]}，")
print(f"  {LOW3} 到 {HIGH3} 的成绩是这样，你看有没有问题？」")
print(RP.metrics(curve3, 365).drop(["起", "止"]).round(4).to_string())
print(f"\n同期买入持有：年化 {RP.annual_return(close.loc[LOW3:HIGH3], 365):.2%}、"
      f"夏普 {RP.sharpe(close.loc[LOW3:HIGH3].pct_change().dropna(), 365):.4f}、"
      f"最大回撤 {RP.max_drawdown(close.loc[LOW3:HIGH3]):.2%}")

print("===== 片段 12：实验三的体检 =====")
holding3 = (train3[pick] != 0).astype(int)
edges = np.diff(np.concatenate([[0], holding3]))
opens, closes = np.where(edges == 1)[0], np.where(edges == -1)[0]
if len(closes) < len(opens):
    closes = np.append(closes, len(holding3))
path = curve3.to_numpy()
trades = pd.Series([path[b] / path[a] - 1 for a, b in zip(opens, closes)])
slice3 = pd.DataFrame([{"快线": f, "慢线": s, "夏普": scores3[k]} for k, (f, s, h, l) in enumerate(COMBOS)
                       if (h, l) == (COMBOS[pick][2], COMBOS[pick][3])])
face3 = V.surface(slice3, "快线", "慢线", "夏普")
checks = pd.DataFrame([
    {"查什么": "第 27 篇：最大回撤是不是 0", "结果": f"{RP.max_drawdown(curve3):.2%}", "判定": "过"},
    {"查什么": "第 27 篇：持仓日上涨的比例",
     "结果": f"{float((train3[pick][train3[pick] != 0] > 0).mean()):.2%}", "判定": "过"},
    {"查什么": "① 参数曲面的落差",
     "结果": f"{V.neighbourhood(face3, COMBOS[pick][:2])['落差']:.4f}（邻居中位 "
             f"{V.neighbourhood(face3, COMBOS[pick][:2])['邻居中位']:.4f}）", "判定": "过（是平原）"},
    {"查什么": "② 多重检验：白捡的门槛",
     "结果": f"夏普 {scores3[pick]:.4f} vs 门槛 "
             f"{V.expected_max_sharpe(len(COMBOS), scores3.std()):.4f}，"
             f"DSR {V.deflated_sharpe(scores3[pick], len(COMBOS), train3.shape[1], scores3.std(), periods_per_year=365)['打过折的夏普 DSR']:.4f}",
     "判定": "过（勉强）"},
    {"查什么": "③ 回测过拟合概率 PBO",
     "结果": f"{V.pbo(train3, 16)['过拟合概率 PBO']:.4f}", "判定": "过"},
    {"查什么": "④ 整个网格的成绩",
     "结果": f"{len(COMBOS):,} 组里夏普大于 1 的占 {(scores3 > 1).mean():.1%}，亏钱的占 {(annual3 < 0).mean():.1%}",
     "判定": "不过"},
    {"查什么": "⑤ 第 29 篇：逐笔的 t 值",
     "结果": f"{len(trades)} 笔，平均每笔 {trades.mean():.2%}，t 值 "
             f"{RP.trade_metrics(trades)['t 值']:.4f}，95% 区间下界 {RP.trade_metrics(trades)['95% 下界']:.2%}",
     "判定": "不过"},
    {"查什么": "⑥ 样本外（2022-01 到 2026-08）",
     "结果": f"年化 {out3[pick]:.2%}，排 {int((out3 > out3[pick]).sum()) + 1}/{len(COMBOS):,}，"
             f"网格中位 {np.median(out3):.2%}，买入持有 {RP.annual_return(close.loc['2022-01-01':], 365):.2%}",
     "判定": "不过"},
])
print(checks.to_string(index=False))
print("\n截止日挪一挪，同一组参数：")
for cut in ["2020-12-31", "2021-06-30", "2021-12-31", "2022-06-30", "2022-12-31"]:
    piece = EXP3[pick, window(LOW3, cut)]
    equity = RP.to_curve(pd.Series(piece, index=pd.RangeIndex(len(piece))))
    print(f"  截到 {cut}：年化 {RP.annual_return(equity, 365):>7.2%}，"
          f"夏普 {RP.sharpe(equity.pct_change().dropna(), 365):.4f}")
