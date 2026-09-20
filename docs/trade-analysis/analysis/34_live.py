"""第 34 篇正文里的代码片段（在 talab 项目根目录运行）。

数据沿用第 3 篇，外加 `34_download.py` 下载的两个 Binance 公开接口快照。
"""
import glob

import numpy as np
import pandas as pd
from talab import (backtest as BT, data as D, indicators as I, journal as JN,
                   live as L, report as RP, trend as T)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
TRIALS = 4000
DAY = pd.Timestamp("2021-11-08", tz="UTC")

btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.adjust_total_return(D.unadjust_splits(D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json"),
                                               D.SPLITS["AAPL"]), D.SPLITS["AAPL"],
                             D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json"))
MARKETS = {"SPY": (spy, 252), "AAPL": (aapl, 252), "BTC": (btc, 365)}


def mainline_plan(frame, fee_rate: float = 0.0) -> BT.Plan:
    """第 26 篇定下来的主线 v4，一个字没改。"""
    price = frame["close"]
    return BT.Plan(entry=((I.sma(price, 50) > I.sma(price, 200))
                          & (price >= price.rolling(20).max())).fillna(False),
                   exit=I.cross_below(I.sma(price, 50), I.sma(price, 200)).fillna(False),
                   stop="chandelier", k=3.0, trigger="close", sizing="risk",
                   risk_per_trade=0.10, fee_rate=fee_rate)


def account_returns(result) -> pd.Series:
    """每一笔在**账户层面**赚亏了百分之几（第 33 篇那个口径，原样搬过来）。"""
    curve, trades = result["资金曲线"], result["交易"]
    values = curve.to_numpy()
    before = values[np.maximum(curve.index.get_indexer(trades["买入日"]) - 1, 0)]
    after = values[curve.index.get_indexer(trades["卖出日"])]
    return pd.Series(after / before - 1, name="每笔账户收益率")


def mainline_signal(history: pd.DataFrame):
    """同一套规则的**实盘**写法：只看得到「到目前为止」的 K 线，每根重算一次。"""
    close = history["close"]
    if len(close) < 200:
        return False, False                       # 200 日均线还算不出来：这一根什么都不做
    fast, slow = I.sma(close, 50), I.sma(close, 200)
    enter = bool(fast.iloc[-1] > slow.iloc[-1] and close.iloc[-1] >= close.rolling(20).max().iloc[-1])
    leave = bool(I.cross_below(fast, slow).iloc[-1]) if len(close) >= 201 else False
    return enter, leave


print("===== 片段 1：2021 年 11 月 8 日 =====")
before = btc.loc[:"2021-11-07"]
done = T.turtle(before, T.TurtlePlan())
curve = done["资金曲线"]
print(f"手上的回测：BTC 日线 {before.index[0].date()} → {before.index[-1].date()}，{len(before)} 根")
print(pd.Series({"年化": RP.annual_return(curve, 365), "最大回撤": RP.max_drawdown(curve),
                 "夏普": RP.sharpe(curve.pct_change().dropna(), 365),
                 "卡玛": RP.calmar(curve, 365), "笔数": float(len(done["交易"])),
                 "胜率": float((done["交易"]["R"] > 0).mean()),
                 "逐笔的 t 值": RP.trade_metrics(done["交易"]["R"])["t 值"]}).round(4).to_string())
print("\n前面几篇的检验也都过了：第 30 篇的曲面落差 +0.15～+0.20（高地不是针）、"
      "每年重挑参数跑不赢固定参数、蒙特卡洛 300 条假数据 0 条比真实的好；")
print("第 33 篇的正常范围表也算好了。账户 10 万美元。全投吗？")

print("===== 片段 2：揭晓 =====")
for window, label in [(365, "第一年"), (403, "头 403 天")]:
    piece = pd.concat([btc.loc[:DAY].iloc[-250:-1], btc.loc[DAY:].iloc[:window]])
    after = T.turtle(piece, T.TurtlePlan())["资金曲线"].iloc[-window:]
    print(f"  上线之后{label}：{after.iloc[-1] / after.iloc[0] - 1:+.2%}，"
          f"期间最深 {(after / after.cummax() - 1).min():+.2%}")
print("\n策略一个字没错——这正是第 33 篇那段十二连亏，它从 2021-11-08 开始。")

print("===== 片段 3：你上线的那一天是随便抽的 =====")
table = L.starts(btc, lambda piece: T.turtle(piece, T.TurtlePlan())["资金曲线"],
                 window=365, step=5, warmup=250)
print(L.start_risk(table).round(4).to_string())
print("\n第一年的最大回撤（⚠️ 回撤全是负数，这里只看分位）：")
print(L.start_risk(table, "期间最大回撤").drop("赚钱的起点占").round(4).to_string())
worst = table.nsmallest(5, "第一段收益")
print(f"\n最差的 5 个上线日（共 {len(table)} 个）：")
print(worst.assign(上线日=lambda t: t["上线日"].dt.date).round(4).to_string(index=False))
print(f"\n2021-11-08 落在第 {100 * (table['第一段收益'] <= -0.1397).mean():.1f} 个百分位——"
      f"{len(table)} 个起点里最差的那一撮。")

print("===== 片段 4：把回测改成一根一根喂，然后逐根对账 =====")
plan = mainline_plan(btc)
engine = BT.run(btc, plan, 100_000.0)
runner = L.Runner(mainline_signal, stop="chandelier", k=3.0, sizing="risk",
                  risk_per_trade=0.10, equity=100_000.0, warmup=400)
streamed = L.replay(btc, runner)
print(L.agrees(engine["资金曲线"], streamed["资金曲线"]).to_string())
print(f"\n回测 {len(engine['交易'])} 笔，实盘 {len(streamed['交易'])} 笔；"
      f"两张交易表完全一样：{engine['交易'][['买入日', '卖出日', '原因']].reset_index(drop=True).equals(streamed['交易'][['买入日', '卖出日', '原因']].reset_index(drop=True))}")
print(f"记账误差：回测 {engine['记账误差']:.2e}，实盘 {streamed['记账误差']:.2e}")

print("===== 片段 5：递推型指标的记忆有多长 =====")
GO = 2500
rows = []
for name, make, decay in [("ATR(14)", lambda d: I.atr(d["high"], d["low"], d["close"], 14), 13 / 14),
                          ("ATR(20)", lambda d: I.atr(d["high"], d["low"], d["close"], 20), 19 / 20),
                          ("EMA(50)", lambda d: I.ema(d["close"], 50), 1 - 2 / 51),
                          ("EMA(200)", lambda d: I.ema(d["close"], 200), 1 - 2 / 201)]:
    whole = make(btc)
    row = {"指标": name, "每多带一根，误差乘": decay}
    for warmup in (50, 100, 200, 400, 800, 1600):
        part = make(btc.iloc[GO - warmup:])
        here, there = part.loc[btc.index[GO]], whole.loc[btc.index[GO]]
        row[f"带 {warmup} 根"] = abs(here - there) / abs(there) if not np.isnan(here) else np.nan
    rows.append(row)
print(pd.DataFrame(rows).to_string(index=False))

print("===== 片段 6：窗口型指标是硬门槛 =====")
entry = ((I.sma(btc["close"], 50) > I.sma(btc["close"], 200))
         & (btc["close"] >= btc["close"].rolling(20).max())).fillna(False)
print(f"主线 v4 的进场信号在九年 {len(entry)} 根里出现 {int(entry.sum())} 次（{entry.mean():.1%} 的日子）")
flags = entry.to_numpy()
for warmup in (60, 100, 150, 199, 200, 250):
    blind = max(0, 200 - warmup)
    if blind == 0:
        print(f"  带 {warmup:>3} 根历史上线：一根都不瞎")
        continue
    chance = np.mean([flags[i:i + blind].any() for i in range(200, len(flags) - blind)])
    print(f"  带 {warmup:>3} 根历史上线：瞎 {blind:>3} 根，"
          f"随便挑一天上线，瞎的那段里至少漏掉一个进场信号的概率 {chance:.1%}")

print("===== 片段 7：交易所的下单规矩 =====")
info = D.load_json("data/binance/exchange_info.json")
prices = {row["symbol"]: float(row["price"]) for row in D.load_json("data/binance/ticker_price.json")}
rows = []
for symbol in info["symbols"]:
    if symbol["quoteAsset"] != "USDT" or symbol["status"] != "TRADING":
        continue
    if symbol["symbol"] not in prices:
        continue
    filters, price = L.Filters.from_binance(symbol), prices[symbol["symbol"]]
    rows.append({"交易对": symbol["symbol"], "价格": price, "tickSize": filters.tick_size,
                 "stepSize": filters.step_size, "minNotional": filters.min_notional,
                 "一个 step 值多少钱": filters.step_size * price})
book = pd.DataFrame(rows)
print(f"全市场 {len(info['symbols'])} 个交易对，其中还在交易的 USDT 交易对 {len(book)} 个")
print(book[["交易对", "价格", "tickSize", "stepSize", "minNotional", "一个 step 值多少钱"]]
      .set_index("交易对").loc[["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]].to_string())
print("\nminNotional 的取值：")
print(book["minNotional"].value_counts().to_string())
print("\nstepSize 的取值：")
print(book["stepSize"].value_counts().sort_index().to_string())

print("===== 片段 8：取整的代价，和拒单的代价 =====")
print(book["一个 step 值多少钱"].describe(percentiles=[0.5, 0.9, 0.99]).round(4).to_string())
for threshold in (0.1, 1.0, 10.0):
    hit = (book["一个 step 值多少钱"] > threshold)
    print(f"  一个 step 超过 {threshold:g} 美元的交易对：{int(hit.sum())} 个（{hit.mean():.1%}）")
worst_pair = book.nlargest(1, "一个 step 值多少钱").iloc[0]
print(f"  最粗的一个是 {worst_pair['交易对']}：一个 step 值 {worst_pair['一个 step 值多少钱']:.2f} 美元，"
      f"落在 1,000 美元的仓位上是 {worst_pair['一个 step 值多少钱'] / 2 / 1000:.3%} 的误差")
btc_filters = L.Filters.from_binance(next(s for s in info["symbols"] if s["symbol"] == "BTCUSDT"))
print(f"\nBTCUSDT：{btc_filters}")
print("一张单发出去之前要过的三关（拿一笔 0.123456789 BTC 的单试）：")
raw = 0.123456789
print(f"  原始数量 {raw}  →  取整后 {btc_filters.round_qty(raw)}  →  "
      f"{btc_filters.accepts(prices['BTCUSDT'], btc_filters.round_qty(raw)) or '可以发出去'}")
tiny = 0.00005
print(f"  原始数量 {tiny}  →  取整后 {btc_filters.round_qty(tiny)}  →  "
      f"{btc_filters.accepts(prices['BTCUSDT'], btc_filters.round_qty(tiny)) or '可以发出去'}")
print(f"  不取整直接发 {raw} → 交易所按 LOT_SIZE 拒单，这一笔就**没有了**")

print("===== 片段 9：美股这边，整股是真的会咬人 =====")
whole_share = L.Filters(tick_size=0.01, step_size=1.0, min_qty=1.0, min_notional=0.0)
rows = []
for name, frame in [("SPY", spy), ("AAPL", aapl)]:
    for equity in (1_000, 10_000, 100_000, 1_000_000):
        trades = BT.run(frame, mainline_plan(frame), float(equity))["交易"]
        checked = L.apply_filters(trades, whole_share)
        rows.append({"标的": name, "本金": equity, "笔数": len(trades),
                     "平均每笔几股": float(trades["数量"].mean()),
                     "取整丢掉的仓位（中位）": float(checked["丢掉的比例"].median()),
                     "取整丢掉的仓位（最大）": float(checked["丢掉的比例"].max()),
                     "发不出去的单": int((checked["被拒绝"] != "").sum())})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 10：最小账户和最大账户 =====")
print(L.min_account(btc_filters, prices["BTCUSDT"], risk_per_trade=0.10, stop_fraction=0.15)
      .round(2).to_string())
market_lot = next(f for f in next(s for s in info["symbols"] if s["symbol"] == "BTCUSDT")["filters"]
                  if f["filterType"] == "MARKET_LOT_SIZE")
ratio = min(1.0, 0.10 / 0.15)
cap = float(market_lot["maxQty"]) * prices["BTCUSDT"]
print(f"\n另一头：MARKET_LOT_SIZE 的 maxQty = {float(market_lot['maxQty']):.2f} BTC"
      f" = {cap / 1e6:.2f} 百万美元")
print(f"主线 v4 的仓位占账户 {ratio:.2%}，所以账户超过 {cap / ratio / 1e6:.1f} 百万美元时，"
      f"一张市价单发不完，必须拆单")

print("===== 片段 11：把第 33 篇的正常范围表变成警戒线 =====")
r = T.turtle(btc, T.TurtlePlan())["交易"]["R"]
for n in (10, 15, 20, len(r)):
    print(f"—— 台阶长度 {n} 笔")
    print(L.stage_range(r, n, trials=TRIALS, seed=34).round(2).to_string())
guards = L.guards_from_range(L.stage_range(r, 15, trials=TRIALS, seed=34))
print("\n按「一级台阶十五笔」定出来的警戒线：")
for guard in guards:
    print(f"  {guard.name}（{guard.kind}，阈值 {guard.threshold:.2f}，{guard.action}）")
print("\n⚠️ 如果拿整段历史（70 笔）的 99% 分位去守一级十五笔的台阶，阈值会松成这样：")
for guard in L.guards_from_range(L.stage_range(r, len(r), trials=TRIALS, seed=34)):
    print(f"  {guard.name}")

print("===== 片段 12：走一遍阶梯 =====")
print(L.ladder().to_string(index=False))
plain = L.run_ladder(r, L.DEFAULT_LADDER)                 # 只升不降，用来单独算警戒线的代价
walked = L.run_ladder(r, L.DEFAULT_LADDER, guards)
print("\n" + pd.Series({k: v for k, v in walked.items() if k != "逐笔"}).to_string())
print(f"\n同一条阶梯，如果不挂警戒线：合计 {plain['合计']:.2f}R（挂了是 {walked['合计']:.2f}R）"
      f"——一次降级花掉 {plain['合计'] - walked['合计']:.2f}R")
steps = walked["逐笔"]
print("\n发生过事情的那几笔：")
print(steps[steps["发生了什么"] != ""].round(2).to_string(index=False))
print(f"\n⚠️ 第 10 笔那一行：{steps.iloc[9]['这一笔的 R']:+.2f}R 落在模拟盘阶段，"
      f"投入比例 {steps.iloc[9]['投入比例']:.0%}，记进账户的是 {steps.iloc[9]['记进账户的']:.2f}R")

print("===== 片段 13：阶梯值多少钱 =====")
FAST = (L.Stage("模拟盘", 0.00, 5), L.Stage("小资金", 0.10, 8),
        L.Stage("半仓", 0.35, 10), L.Stage("目标", 1.00, 1))
FASTER = (L.Stage("模拟盘", 0.00, 3), L.Stage("小资金", 0.10, 5),
          L.Stage("半仓", 0.35, 6), L.Stage("目标", 1.00, 1))
WATCH5 = (L.Stage("模拟盘", 0.00, 5), L.Stage("目标", 1.00, 1))
WATCH10 = (L.Stage("模拟盘", 0.00, 10), L.Stage("目标", 1.00, 1))
LADDERS = [("教科书阶梯 10/15/20", L.DEFAULT_LADDER), ("快阶梯 5/8/10", FAST),
           ("更快 3/5/6", FASTER), ("先观望 5 笔再全投", WATCH5),
           ("先观望 10 笔再全投", WATCH10)]
values = r.to_numpy(float)
WINDOW = 15
pieces = [values[begin:begin + WINDOW] for begin in range(0, len(values) - WINDOW + 1)]
full_mean = float(np.mean([piece.sum() for piece in pieces]))
full_worst = float(min(piece.sum() for piece in pieces))
rows = [{"怎么上线": "一次全投", "平均仓位": 1.0, "平均收益 R": full_mean, "最差 R": full_worst,
         "平均是全投的": 1.0, "最差是全投的": 1.0}]
for label, stages in LADDERS:
    walks = [L.run_ladder(piece, stages, guards) for piece in pieces]
    got = np.array([walk["合计"] for walk in walks])
    rows.append({"怎么上线": label,
                 "平均仓位": float(np.mean([w["逐笔"]["投入比例"].mean() for w in walks])),
                 "平均收益 R": float(got.mean()), "最差 R": float(got.min()),
                 "平均是全投的": float(got.mean() / full_mean),
                 "最差是全投的": float(got.min() / full_worst)})
print(f"头 {WINDOW} 笔，{len(pieces)} 个起点（⚠️「最差是全投的」这一列越小越好，超过 100% 表示"
      f"比一次全投还难看）：")
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 14：和「一直用小仓位」比 =====")
walks = [L.run_ladder(piece, L.DEFAULT_LADDER, guards) for piece in pieces]
got = np.array([walk["合计"] for walk in walks])
exposure = float(np.mean([walk["逐笔"]["投入比例"].mean() for walk in walks]))
print(f"教科书阶梯在头 {WINDOW} 笔里的平均仓位是 {exposure:.2%}。")
print("拿同样仓位「一直不动」做对照（R 是加法，固定仓位就是整条分布乘一个数）：")
print(pd.DataFrame([
    {"怎么上线": "一次全投", "平均 R": full_mean, "最差 R": full_worst},
    {"怎么上线": f"一直用 {exposure:.2%} 仓位", "平均 R": full_mean * exposure,
     "最差 R": full_worst * exposure},
    {"怎么上线": "教科书阶梯", "平均 R": float(got.mean()), "最差 R": float(got.min())},
]).round(4).to_string(index=False))
print(f"\n阶梯 vs 同样仓位一直不动：平均少赚 {1 - got.mean() / (full_mean * exposure):.1%}，"
      f"最差还难看 {got.min() / (full_worst * exposure) - 1:+.1%}")
biggest = int(np.argmax(values))
print(f"原因和第 33 篇那条停手规则一模一样：九年最大的一笔 {values[biggest]:+.2f}R 是第 "
      f"{biggest + 1} 笔，而教科书阶梯的前 {L.DEFAULT_LADDER[0].trades_to_promote} 笔在模拟盘上")
print("\n换几个窗口长度再看一遍，每条阶梯都和「同样的平均仓位一直不动」比：")
rows = []
for window in (10, 15, 25, 40):
    cut = [values[begin:begin + window] for begin in range(0, len(values) - window + 1)]
    mean_full = float(np.mean([piece.sum() for piece in cut]))
    worst_full = float(min(piece.sum() for piece in cut))
    for label, stages in LADDERS[:3]:
        walks = [L.run_ladder(piece, stages, guards) for piece in cut]
        got = np.array([walk["合计"] for walk in walks])
        flat = float(np.mean([walk["逐笔"]["投入比例"].mean() for walk in walks]))
        if flat <= 0:                       # 整个窗口都在模拟盘上，没有可比的固定仓位
            continue
        rows.append({"窗口（笔）": window, "起点个数": len(cut), "阶梯": label,
                     "平均仓位": flat, "阶梯平均 R": float(got.mean()),
                     "同仓位不动 平均 R": mean_full * flat,
                     "阶梯最差 R": float(got.min()),
                     "同仓位不动 最差 R": worst_full * flat})
check = pd.DataFrame(rows)
check["阶梯平均更低"] = check["阶梯平均 R"] < check["同仓位不动 平均 R"]
check["阶梯最差更难看"] = check["阶梯最差 R"] < check["同仓位不动 最差 R"]
print(check.round(3).to_string(index=False))
print(f"\n{len(check)} 组对照里：阶梯的平均更低的有 {int(check['阶梯平均更低'].sum())} 组，"
      f"阶梯的最差更难看的有 {int(check['阶梯最差更难看'].sum())} 组")

print("===== 片段 15：三个标的的上线方案 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    plan = mainline_plan(frame)
    engine = BT.run(frame, plan, 100_000.0)
    runner = L.Runner(mainline_signal, stop="chandelier", k=3.0, sizing="risk",
                      risk_per_trade=0.10, equity=100_000.0, warmup=400)
    checked = L.agrees(engine["资金曲线"], L.replay(frame, runner)["资金曲线"])
    per_trade = account_returns(engine) * 100          # 账户百分点，不是持仓的涨跌幅
    ranges = L.stage_range(per_trade, 15, trials=TRIALS, seed=34)
    guard = L.guards_from_range(ranges)
    trades_per_year = len(engine["交易"]) / (len(frame) / periods)
    rows.append({"标的": name, "逐根对账（最大相对差）": f"{checked['最大相对差']:.1e}",
                 "预热硬门槛": 200, "九年笔数": len(engine["交易"]),
                 "一年几笔": trades_per_year,
                 "走完教科书阶梯要几年": sum(s.trades_to_promote for s in L.DEFAULT_LADDER[:-1]) / trades_per_year,
                 "台阶警戒线·回撤（账户百分点）": guard[0].threshold,
                 "台阶警戒线·连亏（笔）": guard[1].threshold})
print(pd.DataFrame(rows).round(3).to_string(index=False))
