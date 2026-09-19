"""第 27 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob

import numpy as np
import pandas as pd
from talab import backtest as BT, bars as B, data as D, indicators as I, rules as R

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(27)
EQUITY = 100_000.0

print("===== 片段 1：一段看起来很好的回测 =====")
btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
close = btc["close"]
signal = ((I.sma(close, 50) > I.sma(close, 200)) & (close >= close.rolling(20).max())).fillna(False)
# ← 这一行
returns = signal * close.pct_change()
equity = (1 + returns.fillna(0)).cumprod()
print(f"{len(btc)} 根日线，{btc.index[0].date()} 到 {btc.index[-1].date()}，持仓 {signal.mean():.1%} 的日子")
print(f"年化 {equity.iloc[-1] ** (365 / len(equity)) - 1:.2%}")
print(f"最大回撤 {(equity / equity.cummax() - 1).min():.2%}")
print(f"期末是本金的 {equity.iloc[-1]:,.1f} 倍")
held = returns[signal]
print(f"持仓的 {len(held)} 根 K 线里，上涨的有 {(held > 0).mean():.2%}")

print("===== 片段 2：不用看代码的三项体检 =====")
print(BT.lag_test(close, signal.astype(float), lags=(0, 1, 2, 3), periods_per_year=365).round(4).to_string(index=False))
print("\n推迟一根就从 132.69% 塌到 14.26%，而推迟两根、三根都在同一个量级——")
print("真策略赚的是「信号之后价格接着走」，推迟一根只会温和地变差；")
print("这里塌掉的那一截，是**信号当根自己的涨幅**，而那一根正是算出信号的原料。")

print("===== 片段 3：一根 K 线上，什么时候才知道什么 =====")
timeline = pd.DataFrame([
    {"这一根上的数": "开盘价 open", "什么时候知道": "这一根刚开始", "能用来下这一根的单吗": "能"},
    {"这一根上的数": "最高价 high", "什么时候知道": "这一根结束", "能用来下这一根的单吗": "不能"},
    {"这一根上的数": "最低价 low", "什么时候知道": "这一根结束", "能用来下这一根的单吗": "不能"},
    {"这一根上的数": "收盘价 close", "什么时候知道": "这一根结束", "能用来下这一根的单吗": "不能"},
    {"这一根上的数": "均线、ATR、RSI…", "什么时候知道": "这一根结束（它们都用到收盘价）", "能用来下这一根的单吗": "不能"},
])
print(timeline.to_string(index=False))
print("\n所以那条时钟规矩只有一句话：**第 i 根收盘时算出来的东西，最早只能在第 i+1 根上成交。**")

print("===== 片段 4：把 signal 换成仓位，再跑一遍 =====")
for lag in [0, 1]:
    series = BT.vectorized(close, signal.astype(float), lag=lag)
    curve = (1 + series).cumprod()
    print(f"lag={lag}：年化 {curve.iloc[-1] ** (365 / len(curve)) - 1:8.2%}  "
          f"最大回撤 {(curve / curve.cummax() - 1).min():8.2%}  期末 {curve.iloc[-1]:10,.2f} 倍")

print("===== 片段 5：向量化能表达的，和不能表达的 =====")
leave = I.cross_below(I.sma(close, 50), I.sma(close, 200)).fillna(False)
state = pd.Series(np.nan, index=btc.index)
state[signal] = 1.0                                       # 信号成立：目标仓位 1
state[leave] = 0.0                                        # 死叉：目标仓位 0
position = state.ffill().fillna(0.0)                      # 中间的日子沿用上一个状态
vector = (1 + BT.vectorized(close, position, lag=1)).cumprod()
event = BT.run(btc, BT.Plan(entry=signal, exit=leave, fill="close", stop="none", sizing="full"), EQUITY)
event_curve = event["资金曲线"] / EQUITY
print(f"向量化：终值 {vector.iloc[-1]:.6f} 倍，在场 {(position.shift(1) > 0).mean():.2%}")
print(f"事件驱动：终值 {event_curve.iloc[-1]:.6f} 倍，{len(event['交易'])} 笔交易，记账误差 {event['记账误差']:.1e}")
print(f"两条曲线的最大差额：{(event_curve - vector.reindex(event_curve.index)).abs().max():.3e}")
print("\n⚠️ 加上止损，这个写法就塌了：止损价要从**进场那一根**往后推，")
print("而进场在哪一根又取决于上一次出场在哪一根——仓位不再是「当根数据的函数」，")
print("它是一个状态机。向量化不是错的，它只是**只能表达一类策略**。")

print("===== 片段 6：记账 =====")
account = BT.Account(cash=EQUITY)
print(f"开局：现金 {account.cash:,.2f}，持仓 {account.shares}，权益 {account.equity(100.0):,.2f}")
account.buy(price=100.0, shares=account.affordable(100.0, fee_rate=0.001), fee_rate=0.001)
print(f"以 100 买入（单边费率 0.1%）：现金 {account.cash:,.6f}，持仓 {account.shares:,.4f} 股，"
      f"权益 {account.equity(100.0):,.2f}，已付手续费 {account.fees:,.2f}")
account.sell(price=110.0, shares=account.shares, fee_rate=0.001)
print(f"以 110 全部卖出：现金 {account.cash:,.2f}，权益 {account.equity(110.0):,.2f}，"
      f"手续费合计 {account.fees:,.2f}")
print(f"价格涨了 10%，账户只涨了 {account.cash / EQUITY - 1:.4%}——差的就是两次手续费")
try:
    BT.Account(cash=1_000.0).buy(price=100.0, shares=20.0)
except ValueError as error:
    print(f"买超过现金会直接报错：{error}")

print("===== 片段 7：四步顺序，和第 21 篇的引擎对账 =====")
mainline = dict(fill="next_open", stop="chandelier", k=3.0, trigger="close")
rows = []
for name, (df, ppy) in {"SPY": (D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20")), 252),
                        "BTC": (btc, 365)}.items():
    price = df["close"]
    entry = ((I.sma(price, 50) > I.sma(price, 200)) & (price >= price.rolling(20).max())).fillna(False)
    exit_ = I.cross_below(I.sma(price, 50), I.sma(price, 200)).fillna(False)
    for sizing, label in [("full", "满仓"), ("risk", "每笔风险 10%")]:
        series, _, table = R.run(df, R.Rule(entry=entry, exit=exit_, sizing=sizing,
                                            risk_per_trade=0.10, **mainline))
        old = (1 + series).cumprod()
        result = BT.run(df, BT.Plan(entry=entry, exit=exit_, sizing=sizing,
                                    risk_per_trade=0.10, **mainline), EQUITY)
        new = result["资金曲线"] / EQUITY
        rows.append({"标的": name, "仓位": label, "rules.run 交易数": len(table),
                     "backtest.run 交易数": len(result["交易"]),
                     "rules.run 终值": old.iloc[-1], "backtest.run 终值": new.iloc[-1],
                     "两条曲线最大差额": float((new - old).abs().max()),
                     "记账误差": result["记账误差"]})
print(pd.DataFrame(rows).round(6).to_string(index=False))

print("===== 片段 8：对不上的那两行，是谁错了 =====")
price = btc["close"]
entry = ((I.sma(price, 50) > I.sma(price, 200)) & (price >= price.rolling(20).max())).fillna(False)
exit_ = I.cross_below(I.sma(price, 50), I.sma(price, 200)).fillna(False)
series, held_size, _ = R.run(btc, R.Rule(entry=entry, exit=exit_, sizing="risk", risk_per_trade=0.10, **mainline))
result = BT.run(btc, BT.Plan(entry=entry, exit=exit_, sizing="risk", risk_per_trade=0.10, **mainline), EQUITY)
one = result["交易"].set_index("买入日").loc[pd.Timestamp("2021-02-04", tz="UTC")]
window = slice(pd.Timestamp("2021-02-04", tz="UTC"), one["卖出日"] - pd.Timedelta(days=1))
value = result["持仓数量"][window] * btc["close"][window]
fraction = value / result["资金曲线"][window]
planned = one["数量"] * one["买入价"] / (result["资金曲线"][window].iloc[0] - value.iloc[0] + one["数量"] * one["买入价"])
print(f"挑一笔仓位没顶到满仓的：{window.start.date()} 以 {one['买入价']:,.2f} 买入，持有 {one['根数']} 根，涨了 {one['收益']:.2%}")
print(f"  按计划，这笔的仓位占权益 {held_size[window.start]:.2%}（= min(1, 10% ÷ 止损距离)）")
print(f"  出场前一根，数量一股没动，但仓位占权益变成了 {fraction.iloc[-1]:.2%}——是价格涨上去的")
print(f"  `rules.run` 里这个比例始终是 {held_size[window].iloc[0]:.2%}：它每根 K 线都把仓位调回目标比例")
print(f"\n九年下来的差额：rules.run 终值 {(1 + series).cumprod().iloc[-1]:.4f} 倍，"
      f"backtest.run {result['资金曲线'].iloc[-1] / EQUITY:.4f} 倍，差 "
      f"{result['资金曲线'].iloc[-1] / EQUITY / (1 + series).cumprod().iloc[-1] - 1:.2%}")
print("两个引擎都能自圆其说，但只有一个对得上真实账户：**你不会每天把仓位调回 39%。**")

print("===== 片段 9：同一根 K 线里，止损和止盈都碰到了 =====")
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
frames = {"日线": btc, "4 小时": B.resample_ohlcv(minute, "4h"),
          "1 小时": B.resample_ohlcv(minute, "1h"), "1 分钟": minute}
atr = I.atr(btc["high"], btc["low"], btc["close"], 14).to_numpy()
opens = btc["open"].to_numpy(float)


def bracket(bars, k, horizon=20, path=None):
    """每天开盘挂一个 ±k·ATR 的括号单，最多等 horizon 天。path=None 表示用 1 分钟线定真相。"""
    low, high, index = bars["low"].to_numpy(float), bars["high"].to_numpy(float), bars.index
    coin = np.random.default_rng(27)                              # 每次调用都从同一个种子开始，结果可复现
    step = index[1] - index[0]
    fine_low, fine_high, fine_index = (minute["low"].to_numpy(float), minute["high"].to_numpy(float), minute.index)
    results, ambiguous = [], 0
    for i in range(20, len(btc) - 1):
        if np.isnan(atr[i - 1]):
            continue
        entry_price = opens[i]
        stop, target = entry_price - k * atr[i - 1], entry_price + k * atr[i - 1]
        begin = index.searchsorted(btc.index[i])
        end = index.searchsorted(btc.index[i] + pd.Timedelta(days=horizon), side="right")
        answer = None
        for j in range(begin, end):
            hit_stop, hit_target = low[j] <= stop, high[j] >= target
            if hit_stop and hit_target:                           # 两个都碰到，K 线上看不出顺序
                ambiguous += 1
                if path is not None:
                    answer = BT.first_touch({"low": low[j], "high": high[j]}, stop, target, path, coin)
                else:                                             # 拆到 1 分钟线上看真相
                    a = fine_index.searchsorted(index[j])
                    b = fine_index.searchsorted(index[j] + step)
                    down = np.flatnonzero(fine_low[a:b] <= stop)
                    up = np.flatnonzero(fine_high[a:b] >= target)
                    answer = "止损" if len(up) == 0 or (len(down) > 0 and down[0] <= up[0]) else "止盈"
            elif hit_stop:
                answer = "止损"
            elif hit_target:
                answer = "止盈"
            if answer:
                break
        if answer:
            results.append(1.0 if answer == "止盈" else -1.0)
    return np.array(results), ambiguous


rows = []
for name, bars in frames.items():
    for k in [0.25, 0.5, 1.0]:
        _, ambiguous = bracket(bars, k)
        rows.append({"K 线": name, "括号宽度": f"±{k} ATR", "同一根的笔数": ambiguous,
                     "占全部": ambiguous / 3281})
print(pd.DataFrame(rows).pivot(index="K 线", columns="括号宽度", values="占全部")
      .reindex(list(frames)).map(lambda v: f"{v:.2%}").to_string())
print("⚠️ K 线越细，这件事越少，但压不到 0：只要还是 K 线，就还有这一根内部")

print("===== 片段 10：这个假设值多少钱 =====")
for k in [0.25, 0.5, 1.0]:
    rows = []
    for label, path in [("乐观：总是止盈先到", "optimistic"), ("悲观：总是止损先到", "pessimistic"),
                        ("抛硬币", "coin"), ("真相：用 1 分钟线判定", None)]:
        outcome, ambiguous = bracket(btc, k, path=path)
        curve = np.cumprod(1 + 0.01 * outcome)            # 每笔冒 1% 的风险（第 26 篇）
        rows.append({"同一根里听谁的": label, "笔数": len(outcome), "同一根": ambiguous,
                     "胜率": float((outcome > 0).mean()), "合计 R": float(outcome.sum()),
                     "期末是本金的几倍": float(curve[-1])})
    table = pd.DataFrame(rows)
    table["比真相多算的 R"] = table["合计 R"] - table["合计 R"].iloc[-1]
    print(f"--- 日线，括号 ±{k} ATR ---")
    print(table.round(4).to_string(index=False))

print("===== 片段 11：限价单「碰到就成交」有多真 =====")
level = btc["open"] * (1 - 0.02)
touched = (btc["low"] <= level).fillna(False)
rows = []
for when in btc.index[touched]:
    fine = minute.loc[when: when + pd.Timedelta("1D") - pd.Timedelta("1min")]
    if len(fine) == 0:
        continue
    at = fine["low"] <= level[when]
    rows.append({"日期": when, "价格穿过限价的幅度": (level[when] - btc["low"][when]) / level[when],
                 "在限价或更低的分钟数": int(at.sum()),
                 "这些分钟的成交额占当天": float(fine.loc[at, "quote_volume"].sum() / fine["quote_volume"].sum())})
fills = pd.DataFrame(rows)
fills["穿过多少"] = pd.cut(fills["价格穿过限价的幅度"], [-1e-9, 0.0005, 0.002, 0.01, 0.03, 1],
                           labels=["≤0.05%（擦一下）", "0.05%–0.2%", "0.2%–1%", "1%–3%", "大于 3%"])
summary = fills.groupby("穿过多少", observed=True).agg(
    天数=("在限价或更低的分钟数", "size"),
    分钟数中位=("在限价或更低的分钟数", "median"),
    只有1分钟的比例=("在限价或更低的分钟数", lambda s: float((s <= 1).mean())),
    不超过5分钟=("在限价或更低的分钟数", lambda s: float((s <= 5).mean())),
    成交额占比中位=("这些分钟的成交额占当天", "median"))
print(f"限价挂在开盘价下方 2%，日线判定「成交」的 {len(fills)} 天（占全部 {touched.mean():.1%}）：")
print(summary.round(4).to_string())
print("\n`limit_filled` 里的 through 参数就是用来量这个假设的：")
for through in [0.0, 0.0005, 0.002]:
    hit = sum(BT.limit_filled({"low": btc["low"][d], "high": btc["high"][d]}, level[d], "buy", through)
              for d in btc.index[touched])
    print(f"  要求价格穿过限价 {through:.2%} 才算成交：{hit} 天成交（原来 {int(touched.sum())} 天），"
          f"少了 {int(touched.sum()) - hit} 天")

print("===== 片段 12：成本的接口 =====")
rows = []
for fee in [0.0, 0.0002, 0.0005, 0.001, 0.002]:
    result = BT.run(btc, BT.Plan(entry=entry, exit=exit_, sizing="risk", risk_per_trade=0.10,
                                 fee_rate=fee, **mainline), EQUITY)
    curve = result["资金曲线"]
    rows.append({"单边费率": f"{fee:.2%}", "交易数": len(result["交易"]),
                 "年化": (curve.iloc[-1] / EQUITY) ** (365 / len(curve)) - 1,
                 "期末账户": curve.iloc[-1], "手续费合计": result["手续费合计"],
                 "手续费占期末账户": result["手续费合计"] / curve.iloc[-1]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("⚠️ 真实的费率、滑点、买卖价差是第 28 篇的事，这里只是把口子留出来")

print("===== 片段 13：主线策略 v4 在新引擎上 =====")
plan = BT.Plan(entry=entry, exit=exit_, sizing="risk", risk_per_trade=0.10, **mainline)
print(plan.describe().to_string())
result = BT.run(btc, plan, EQUITY)
series, _, table = R.run(btc, R.Rule(entry=entry, exit=exit_, sizing="risk", risk_per_trade=0.10, **mainline))
curves = {"第 21 篇的 rules.run": (1 + series).cumprod() * EQUITY,
          "第 27 篇的 backtest.run": result["资金曲线"],
          "加上 0.05% 单边费率": BT.run(btc, BT.Plan(entry=entry, exit=exit_, sizing="risk",
                                                    risk_per_trade=0.10, fee_rate=0.0005, **mainline),
                                       EQUITY)["资金曲线"]}
print()
print(BT.reconcile(curves).round(6).to_string(index=False))
for name, curve in curves.items():
    annual = (curve.iloc[-1] / curve.iloc[0]) ** (365 / len(curve)) - 1
    print(f"{name}：年化 {annual:.2%}，最大回撤 {(curve / curve.cummax() - 1).min():.2%}")
print(f"\n记账误差 {result['记账误差']:.1e}；最后一根上 现金 {result['现金'].iloc[-1]:,.2f} + "
      f"持仓 {result['持仓数量'].iloc[-1]:.6f} × {btc['close'].iloc[-1]:,.2f} = {result['资金曲线'].iloc[-1]:,.2f}")

print("===== 片段 14：揭晓 =====")
print("错的那一行是：returns = signal * close.pct_change()")
print("改对只要一个 .shift(1)：returns = signal.shift(1) * close.pct_change()")
returns = signal.shift(1) * close.pct_change()
fixed = (1 + returns.fillna(0)).cumprod()
broken = (1 + (signal * close.pct_change()).fillna(0)).cumprod()
print(pd.DataFrame([
    {"版本": "错：signal * ret", "年化": broken.iloc[-1] ** (365 / len(broken)) - 1,
     "最大回撤": float((broken / broken.cummax() - 1).min()), "期末倍数": float(broken.iloc[-1])},
    {"版本": "对：signal.shift(1) * ret", "年化": fixed.iloc[-1] ** (365 / len(fixed)) - 1,
     "最大回撤": float((fixed / fixed.cummax() - 1).min()), "期末倍数": float(fixed.iloc[-1])},
]).round(4).to_string(index=False))
