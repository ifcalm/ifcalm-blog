"""第 33 篇正文里的代码片段（在 talab 项目根目录运行，数据沿用第 3 篇）。"""
import glob

import numpy as np
import pandas as pd
from talab import (backtest as BT, costs as C, data as D, indicators as I,
                   journal as JN, report as RP, size as SZ, trend as T)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
TRIALS = 5000

btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.adjust_total_return(D.unadjust_splits(D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json"),
                                               D.SPLITS["AAPL"]), D.SPLITS["AAPL"],
                             D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json"))
MARKETS = {"SPY": (spy, 252), "AAPL": (aapl, 252), "BTC": (btc, 365)}

turtles = {name: T.turtle(frame, T.TurtlePlan()) for name, (frame, _) in MARKETS.items()}


def mainline(frame, fee=0.0):
    """第 26 篇定下来的主线 v4，一个字没改。"""
    price = frame["close"]
    plan = BT.Plan(entry=((I.sma(price, 50) > I.sma(price, 200))
                          & (price >= price.rolling(20).max())).fillna(False),
                   exit=I.cross_below(I.sma(price, 50), I.sma(price, 200)).fillna(False),
                   stop="chandelier", k=3.0, trigger="close", sizing="risk",
                   risk_per_trade=0.10, fee_rate=fee)
    return BT.run(frame, plan, 100_000.0)


def account_returns(result) -> pd.Series:
    """每一笔在**账户层面**赚亏了百分之几：进场那一根的前一根收盘 → 出场那一根收盘。

    只有一笔仓、空仓时拿现金，所以这段权益变化就是这一笔的全部损益（含手续费）。
    """
    curve, trades = result["资金曲线"], result["交易"]
    values = curve.to_numpy()
    before = values[np.maximum(curve.index.get_indexer(trades["买入日"]) - 1, 0)]
    after = values[curve.index.get_indexer(trades["卖出日"])]
    return pd.Series(after / before - 1, name="每笔账户收益率")


print("===== 片段 1：2022 年 7 月 26 日 =====")
res = turtles["BTC"]
trades, curve = res["交易"], res["资金曲线"]
runs = JN.streaks(trades["R"])
worst = runs[runs["方向"] == "亏"].sort_values("长度").iloc[-1]
first, seventh = int(worst["起"]), int(worst["起"]) + 6
shown = trades.iloc[first:seventh + 1]
print(shown[["进场日", "出场日", "单位数", "原因", "盈亏", "R"]]
      .assign(进场日=lambda t: t["进场日"].dt.date, 出场日=lambda t: t["出场日"].dt.date)
      .round(2).to_string(index=False))
peak = curve.loc[:trades["出场日"].iloc[seventh]].max()
now = curve.loc[trades["出场日"].iloc[seventh]]
print(f"\n这 7 笔：合计 {shown['R'].sum():.2f}R，合计 {shown['盈亏'].sum():,.0f} 美元，"
      f"历时 {(trades['出场日'].iloc[seventh] - trades['进场日'].iloc[first]).days} 天")
print(f"账户：峰值 {peak:,.0f} → 现在 {now:,.0f}，回撤 {now / peak - 1:.2%}")
print(f"这条策略九年 {len(trades)} 笔，胜率 {(trades['R'] > 0).mean():.1%}，"
      f"到今天为止合计 {trades['R'].iloc[:seventh + 1].sum():.2f}R")

print("===== 片段 2：先别急着揭晓——连亏 7 笔，概率是多少 =====")
win_rate = float((trades["R"] > 0).mean())
print(f"公式给的期望（{len(trades)} 笔、胜率 {win_rate:.1%}）：最长连亏 "
      f"{JN.expected_longest(len(trades), 1 - win_rate):.2f} 笔")
print(JN.streak_distribution(len(trades), win_rate, trials=TRIALS, seed=33).round(3).to_string())
print()
print(JN.streak_alarm(len(trades), win_rate, trials=TRIALS, seed=33).round(4).to_string(index=False))

print("===== 片段 3：揭晓 =====")
tail = trades.iloc[seventh + 1:int(worst["止"]) + 2]
print(tail[["进场日", "出场日", "单位数", "原因", "盈亏", "R"]]
      .assign(进场日=lambda t: t["进场日"].dt.date, 出场日=lambda t: t["出场日"].dt.date)
      .round(2).to_string(index=False))
whole = trades.iloc[first:int(worst["止"]) + 1]
end = trades["出场日"].iloc[int(worst["止"])]
print(f"\n连亏没有在第 7 笔停下：一共 {int(worst['长度'])} 笔，合计 {whole['R'].sum():.2f}R、"
      f"{whole['盈亏'].sum():,.0f} 美元，从 {trades['进场日'].iloc[first].date()} 一直亏到 {end.date()}，"
      f"{(end - trades['进场日'].iloc[first]).days} 天")
print(f"账户 {peak:,.0f} → {curve.loc[end]:,.0f}，回撤 {curve.loc[end] / peak - 1:.2%}")
nxt = trades.iloc[int(worst["止"]) + 1]
print(f"\n然后是第 {int(worst['止']) + 2} 笔：{nxt['进场日'].date()} 进场 {nxt['第一个单位的价']:,.2f}，"
      f"{nxt['出场日'].date()} 以 {nxt['出场价']:,.2f} {nxt['原因']}，"
      f"{nxt['R']:+.2f}R、{nxt['盈亏']:+,.0f} 美元")
print(f"这一笔一个人赚回了前面 {int(worst['长度'])} 笔亏掉的 {-whole['盈亏'].sum():,.0f} 美元，还多出 "
      f"{nxt['盈亏'] + whole['盈亏'].sum():,.0f}；它在九年 {len(trades)} 笔里排第 "
      f"{int((trades['R'] > nxt['R']).sum()) + 1}")

print("===== 片段 4：正常范围表 =====")
for name in MARKETS:
    print(f"—— {name}（海龟，{len(turtles[name]['交易'])} 笔，单位是 R）")
    print(JN.normal_range(turtles[name]["交易"]["R"], trials=TRIALS, seed=33).round(3).to_string())

print("===== 片段 5：主线策略 v4 的正常范围 =====")
mains = {name: mainline(frame) for name, (frame, _) in MARKETS.items()}
for name in MARKETS:
    r = account_returns(mains[name]) * 100          # 换成百分点，方便读
    print(f"—— {name}（主线 v4，{len(r)} 笔，单位是账户的百分点）")
    print(JN.normal_range(r, trials=TRIALS, seed=33).round(2).to_string())

print("===== 片段 6：要多少笔，才能认出策略真的坏了 =====")
rows = []
for name in MARKETS:
    for label, values in [("海龟（R）", turtles[name]["交易"]["R"]),
                          ("主线 v4（账户 %）", account_returns(mains[name]) * 100)]:
        values = pd.Series(values).dropna()
        mean, std = float(values.mean()), float(values.std())
        rows.append({"标的": name, "策略": label, "笔数": len(values), "每笔期望": mean,
                     "每笔标准差": std, "标准差是期望的几倍": std / mean,
                     "认出「掉到 0」要几笔": JN.detection_size(mean, std),
                     "认出「掉一半」要几笔": JN.detection_size(mean, std, drop=0.5),
                     "按历史速度要跑几年": JN.detection_size(mean, std) / (len(values) / 9.0)})
print(pd.DataFrame(rows).round(2).to_string(index=False))

print("===== 片段 7：连亏之后停手，在 BTC 上值多少钱 =====")
pause = JN.pause_table(trades["R"])
base = pause.iloc[0]["合计 R"]
pause = pause.round(2)
pause["比一笔不落差多少"] = (pause["合计 R"] - base).round(2)
print(pause.to_string(index=False))

print("===== 片段 8：六条停手规则 × 三个标的 × 两条策略 =====")
rows = []
for name in MARKETS:
    for label, values in [("海龟（R）", turtles[name]["交易"]["R"]),
                          ("主线 v4（账户 %）", account_returns(mains[name]) * 100)]:
        values = pd.Series(values).dropna()
        full = float(values.sum())
        row = {"标的": name, "策略": label, "一笔不落": full}
        for after, pause in [(2, 3), (3, 3), (4, 3), (3, 5)]:
            taken = JN.pause_after_losses(values, after, pause)
            row[f"连亏 {after} 停 {pause}"] = float(values.to_numpy()[taken].sum()) - full
        rows.append(row)
print(pd.DataFrame(rows).round(2).to_string(index=False))

print()
rows = []
for name, (frame, periods) in MARKETS.items():
    curve = turtles[name]["资金曲线"]
    daily = curve.pct_change().fillna(0.0).to_numpy()
    rows.append({"标的": name, "单日亏多少就停": "不停", "停几天": 0, "被触发几次": 0,
                 "真正被砍掉的天数": 0, "年化": RP.annual_return(curve, periods),
                 "最大回撤": RP.max_drawdown(curve)})
    for limit in (0.03, 0.05):
        for days in (5, 20):
            kept, cool, hits = daily.copy(), 0, 0
            for i in range(len(daily)):
                if cool > 0:
                    kept[i], cool = 0.0, cool - 1
                elif daily[i] < -limit:
                    cool, hits = days, hits + 1
            stopped = RP.to_curve(pd.Series(kept[1:], index=curve.index[1:])) * curve.iloc[0]
            rows.append({"标的": name, "单日亏多少就停": f"{limit:.0%}", "停几天": days,
                         "被触发几次": hits, "真正被砍掉的天数": int((kept == 0).sum() - (daily == 0).sum()),
                         "年化": RP.annual_return(stopped, periods),
                         "最大回撤": RP.max_drawdown(stopped)})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 9：连亏之后的下一笔，有什么不一样吗 =====")
rows = []
for name in MARKETS:
    r = turtles[name]["交易"]["R"].to_numpy(float)
    previous = np.concatenate([[np.nan], r[:-1]])
    losing_run = np.zeros(len(r), dtype=int)
    for i in range(1, len(r)):
        losing_run[i] = losing_run[i - 1] + 1 if r[i - 1] <= 0 else 0
    for label, mask in [("全部", np.ones(len(r), bool)), ("前一笔是亏的", previous <= 0),
                        ("前面连亏 ≥ 3 笔", losing_run >= 3), ("前面连亏 ≥ 5 笔", losing_run >= 5)]:
        picked = r[mask]
        rows.append({"标的": name, "这一笔的处境": label, "笔数": len(picked),
                     "平均 R": picked.mean() if len(picked) else np.nan,
                     "胜率": (picked > 0).mean() if len(picked) else np.nan,
                     "最大一笔 R": picked.max() if len(picked) else np.nan})
    top = np.argsort(r)[-10:]
    rows.append({"标的": name, "这一笔的处境": "最赚的 10 笔，前一笔是亏的占",
                 "笔数": 10, "平均 R": r[top].mean(),
                 "胜率": float(np.mean(previous[top] <= 0)), "最大一笔 R": r[top].max()})
print(pd.DataFrame(rows).round(3).to_string(index=False))

print("===== 片段 10：手动调整的代价 =====")
for name in MARKETS:
    print(f"—— {name}（海龟）")
    out = JN.interference_table(turtles[name]["交易"]["R"]).round(2)
    out["按每笔冒 1% 折算"] = (out["差多少 R"] / 100).map("{:+.1%}".format)
    print(out.to_string(index=False))

print("===== 片段 11：「一开始就放远」和「临时挪远」是两件事 =====")
rows = []
for name, (frame, periods) in MARKETS.items():
    for stop_atr in (2.0, 3.0, 4.0):
        result = T.turtle(frame, T.TurtlePlan(stop_atr=stop_atr))
        rows.append({"标的": name, "止损": f"{stop_atr:g}N（一开始就定好）",
                     "笔数": len(result["交易"]),
                     "年化": RP.annual_return(result["资金曲线"], periods),
                     "最大回撤": RP.max_drawdown(result["资金曲线"]),
                     "合计 R": float(result["交易"]["R"].sum())})
    r = turtles[name]["交易"]["R"]
    for k in (1.5, 2.0):
        changed = JN.interfere(r, "widen", k)
        rows.append({"标的": name, "止损": f"临时挪远（亏的 ×{k:g}，上界）",
                     "笔数": len(r), "年化": np.nan, "最大回撤": np.nan,
                     "合计 R": float(changed.sum())})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 12：日志里的一行长什么样 =====")
book = JN.Journal()
# 就用决策点之后那三笔真实交易：数量从「盈亏 ÷ 价差」精确反推（费率是 0）
after = trades.iloc[int(worst["止"]) + 1:int(worst["止"]) + 4]
quantities = after["盈亏"] / (after["出场价"] - after["平均价"])
n_value = I.atr(btc["high"], btc["low"], btc["close"], 20).shift(1)      # 海龟的 N
plans = [dict(time=row["进场日"], symbol="BTC", plan_entry=row["平均价"],
              plan_stop=row["平均价"] - 2 * n_value.loc[row["进场日"]],
              plan_qty=float(q), plan_exit=row["出场价"], exit_time=row["出场日"])
         for (_, row), q in zip(after.iterrows(), quantities)]
book.add(JN.Entry(**plans[0]))                                             # 完全照做
book.add(JN.Entry(**{**plans[1], "fill_entry": plans[1]["plan_entry"] + 13.4,
                     "fill_exit": plans[1]["plan_exit"] - 15.98,
                     "fee": 44.0, "note": "进场晚了 13 美元，出场滑了 16 美元"}))
book.add(JN.Entry(**{**plans[2], "fill_qty": 0.0, "basis": "我觉得",
                     "note": "刚被止损两次，这次不敢做"}))
shown = book.frame()
for column in ("时间", "出场时间"):
    shown[column] = shown[column].map(lambda t: "" if pd.isna(t) else str(t.date()))
shown[shown.select_dtypes("number").columns] = shown.select_dtypes("number").round(2)
print(shown.to_string(index=False))
print()
print(book.summary().round(2).to_string())

print("===== 片段 13：把九年实盘和回测的差额拆开 =====")
SLIP_BP, FEE_BP = 5e-4, 1e-3


def as_table(trades: pd.DataFrame) -> pd.DataFrame:
    """把海龟的交易表整理成 `reconcile` 认识的样子（费率是 0，所以数量能精确反推）。"""
    sign = np.where(trades["方向"] == "多", 1.0, -1.0)
    qty = trades["盈亏"].to_numpy() / (sign * (trades["出场价"] - trades["平均价"]).to_numpy())
    return trades.assign(数量=qty, 费用=0.0)[["进场日", "方向", "平均价", "出场价", "数量", "费用"]]


planned = as_table(trades)
sign = np.where(planned["方向"] == "多", 1.0, -1.0)
rng = np.random.default_rng(33)
live = planned.assign(
    平均价=planned["平均价"] * (1 + sign * SLIP_BP),            # 买的时候买贵一点
    出场价=planned["出场价"] * (1 - sign * SLIP_BP),            # 卖的时候卖便宜一点
    数量=planned["数量"] * (1 + rng.normal(0, 0.10, len(planned))),
)
live["费用"] = live["数量"] * (live["平均价"] + live["出场价"]) * FEE_BP
taken = JN.pause_after_losses(trades["R"], after=4, pause=3)    # 决策点那个人的行为
live = live[taken]
print(f"「实盘」的三处不一样：单边 {SLIP_BP:.2%} 滑点、数量随机差 ±10%、单边 {FEE_BP:.2%} 手续费，"
      f"外加「连亏 4 笔就停 3 笔」跳过了 {int((~taken).sum())} 笔")
gap = JN.reconcile(planned, live, key="进场日", entry_col="平均价", exit_col="出场价")
print()
print(gap["归因"].map("{:+,.0f}".format).to_string())
print(f"\n跳过的那 {int((~taken).sum())} 笔：")
print(trades[~taken][["进场日", "出场日", "原因", "盈亏", "R"]]
      .assign(进场日=lambda t: t["进场日"].dt.date, 出场日=lambda t: t["出场日"].dt.date)
      .round(2).to_string(index=False))

print("===== 片段 14：漏做一笔，相当于多少滑点 =====")
rows = []
for name in MARKETS:
    table = as_table(turtles[name]["交易"])
    sign = np.where(table["方向"] == "多", 1.0, -1.0)
    notional = float((table["数量"] * (table["平均价"] + table["出场价"])).sum())
    profit = turtles[name]["交易"]["盈亏"]
    biggest = float(profit.max())
    total = float((sign * table["数量"] * (table["出场价"] - table["平均价"])).sum())
    rows.append({"标的": name, "九年成交名义金额": notional, "九年总盈亏": total,
                 "单边 1 个基点滑点": -notional * 1e-4, "漏做赚得最多的那一笔": -biggest,
                 "一笔顶多少个基点的滑点": biggest / (notional * 1e-4)})
print(pd.DataFrame(rows).round(1).to_string(index=False))

print("===== 片段 15：对账能查出来的，和查不出来的 =====")
rows = []
for name in MARKETS:
    table = as_table(turtles[name]["交易"])
    sign = np.where(table["方向"] == "多", 1.0, -1.0)
    base = float((sign * table["数量"] * (table["出场价"] - table["平均价"])).sum())
    for label, build in [
        ("只有滑点（单边 5 个基点）",
         lambda t, s: t.assign(平均价=t["平均价"] * (1 + s * SLIP_BP),
                               出场价=t["出场价"] * (1 - s * SLIP_BP))),
        ("只有仓位差（每笔 ±10%）",
         lambda t, s: t.assign(数量=t["数量"] * (1 + np.random.default_rng(1).normal(0, 0.10, len(t))))),
        ("只漏做赚得最多的那一笔",
         lambda t, s: t.drop(t.index[int(turtles[name]["交易"]["盈亏"].argmax())])),
        ("只跳过「连亏 4 笔」之后的三笔",
         lambda t, s: t[JN.pause_after_losses(turtles[name]["交易"]["R"], 4, 3)]),
    ]:
        parts = JN.reconcile(table, build(table, sign), key="进场日",
                             entry_col="平均价", exit_col="出场价")["归因"]
        rows.append({"标的": name, "实盘和回测哪里不一样": label,
                     "差额": parts["实盘 − 回测"], "占九年总盈亏": parts["实盘 − 回测"] / base,
                     "拆出来对不对得上": parts["差额核对"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
