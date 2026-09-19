"""第 21 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
import itertools

import numpy as np
import pandas as pd
from talab import data as D, indicators as I, rules as R, structure as X

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(0)

print("===== 片段 1：加载数据 =====")
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
markets = [("SPY", spy, 252), ("AAPL", aapl, 252), ("BTC", day, 365)]
print(f"SPY {len(spy)} 天，AAPL {len(aapl)} 天，BTC {len(day)} 天")


def crosses(df, fast=50, slow=200):
    """第 12 篇的金叉：快均线上穿慢均线的那一天。"""
    return I.cross_above(I.sma(df["close"], fast), I.sma(df["close"], slow)).fillna(False)


def deaths(df, fast=50, slow=200):
    return I.cross_below(I.sma(df["close"], fast), I.sma(df["close"], slow)).fillna(False)


print("===== 片段 2：决策点 =====")
signal_day = pd.Timestamp("2025-07-01")
print("SPY 十年里的金叉：", [str(d.date()) for d in spy.index[crosses(spy)]])
print("对应的死叉：    ", [str(d.date()) for d in spy.index[deaths(spy)]])
fast, slow = I.sma(spy["close"], 50), I.sma(spy["close"], 200)
print(f"{signal_day.date()} 收盘：SMA50 {fast[signal_day]:.2f} 上穿 SMA200 {slow[signal_day]:.2f}，"
      f"收盘价 {spy.loc[signal_day, 'close']:.2f}，前一个交易日 SMA50 {fast.shift(1)[signal_day]:.2f}")
print(spy.loc["2025-06-27":"2025-07-08", ["open", "high", "low", "close"]].round(2).to_string())
atr = I.atr(spy["high"], spy["low"], spy["close"])
print(f"当天的 ATR {atr[signal_day]:.2f}（{atr[signal_day] / spy.loc[signal_day, 'close']:.2%}）；"
      f"50 日均线 {fast[signal_day]:.2f} 在收盘价下方 {1 - fast[signal_day] / spy.loc[signal_day, 'close']:.1%}")

print("===== 片段 3：六个要素 =====")
entry = (I.sma(spy["close"], 50) > I.sma(spy["close"], 200)) & (spy["close"] >= spy["close"].rolling(20).max())
one = R.Rule(entry=entry, exit=deaths(spy), fill="next_open", stop="chandelier", k=3.0, trigger="close")
print(one.describe().to_string())
returns, held, trades = R.run(spy, one)
print(f"\n这条规则在 SPY 上跑十年：{len(trades)} 笔交易，在场时间 {(held > 0).mean():.1%}，"
      f"年化 {(1 + returns).prod() ** (252 / len(returns)) - 1:.2%}")
print(trades.tail(3).to_string())

print("===== 片段 4：同一个信号，十八种写法 =====")
FILLS = {"当根收盘": dict(fill="close"), "下一根开盘": dict(fill="next_open"), "回调到 50 日均线": dict(fill="pullback")}
STOPS = {"不设止损": dict(stop="none"), "3 ATR 吊灯": dict(stop="chandelier", k=3.0), "进场价 -10%": dict(stop="percent")}
EXITS = {"死叉出场": "death", "跌破 20 日新低": "low20"}


def variant(df, fill_name, stop_name, exit_name):
    """同一个金叉信号，不同的补全方式。"""
    trend = I.sma(df["close"], 50) > I.sma(df["close"], 200)
    signal = trend & (df["close"] >= df["close"].rolling(20).max())
    leave = deaths(df) if EXITS[exit_name] == "death" else (df["close"] <= df["close"].rolling(20).min())
    options = FILLS[fill_name] | STOPS[stop_name]
    if options.get("fill") == "pullback":
        options["pullback_to"] = I.sma(df["close"], 50)
    return R.Rule(entry=signal, exit=leave.fillna(False), **options)


rows = []
for name, df, periods in markets:
    for fill_name, stop_name, exit_name in itertools.product(FILLS, STOPS, EXITS):
        returns, held, trades = R.run(df, variant(df, fill_name, stop_name, exit_name))
        equity = (1 + returns).cumprod()
        rows.append({"标的": name, "入场方式": fill_name, "止损": stop_name, "出场": exit_name,
                     "年化": equity.iloc[-1] ** (periods / len(returns)) - 1,
                     "最大回撤": (equity / equity.cummax() - 1).min(), "交易次数": len(trades),
                     "在场时间": (held > 0).mean(), "最差一笔": trades["收益"].min() if len(trades) else np.nan})
grid = pd.DataFrame(rows)
print(f"每个标的 {len(FILLS)} × {len(STOPS)} × {len(EXITS)} = {len(FILLS) * len(STOPS) * len(EXITS)} 种写法：")
print(grid.groupby("标的")["年化"].agg(["min", "median", "max"]).round(4).to_string())
for name, _, _ in markets:
    sub = grid[grid["标的"] == name].sort_values("年化")
    print(f"\n{name} 最差和最好的三种写法：")
    print(pd.concat([sub.head(3), sub.tail(3)]).drop(columns="标的").to_string(index=False,
                                                                              float_format=lambda v: f"{v:.3f}"))

print("\n按「止损」这一格汇总（每格 6 种写法的平均）：")
print(grid.groupby(["标的", "止损"])[["年化", "最大回撤", "最差一笔", "交易次数"]].mean()
      .to_string(float_format=lambda v: f"{v:.3f}"))

print("===== 片段 5：在一个标的上挑出来的写法，换个标的还灵吗 =====")
wide = grid.pivot_table(index=["入场方式", "止损", "出场"], columns="标的", values="年化")
print(wide.round(4).to_string())
print("\n三个标的之间，写法排名的秩相关：")
print(wide.rank().corr(method="spearman").round(3).to_string())
best = wide["SPY"].idxmax()
print(f"\nSPY 上最好的写法是 {best}：在 AAPL 上排第 {int(wide['AAPL'].rank(ascending=False)[best])}，"
      f"在 BTC 上排第 {int(wide['BTC'].rank(ascending=False)[best])}（共 {len(wide)} 种）")

print("===== 片段 6：条件之间有多重合 =====")


def conditions(df):
    close, high, low = df["close"], df["high"], df["low"]
    return {"金叉状态（50 在 200 上方）": I.sma(close, 50) > I.sma(close, 200),
            "收盘价在 200 日均线上方": close > I.sma(close, 200),
            "收盘创 20 日新高": close >= close.rolling(20).max(),
            "ADX > 20": X.adx(high, low, close)["adx"] > 20,
            "RSI > 50": I.rsi(close) > 50,
            "成交量高于 20 日中位": df["volume"] > df["volume"].rolling(20).median()}


picked = conditions(spy)
print("SPY 上，两两「同时成立」的程度（对角线是各自成立的比例）：")
print(R.overlap(picked).round(3).to_string())
pairs = [("金叉状态（50 在 200 上方）", "收盘价在 200 日均线上方"), ("金叉状态（50 在 200 上方）", "RSI > 50"),
         ("收盘创 20 日新高", "成交量高于 20 日中位")]
for a, b in pairs:
    both = X.agreement(picked[a].astype(float), picked[b].astype(float))
    print(f"{a} 对 {b}：一致 {both['share']:.1%}，kappa {both['kappa']:.3f}")

print("===== 片段 7：条件越多，交易越少，统计越不可靠 =====")
order = list(picked)
print(R.stack(picked, order).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
rows = []
for depth in range(1, len(order) + 1):
    mask = None
    for name in order[:depth]:
        mask = picked[name] if mask is None else (mask & picked[name])
    rule = R.Rule(entry=mask.fillna(False), exit=deaths(spy), stop="chandelier")
    returns, held, trades = R.run(spy, rule)
    profits = trades["收益"].to_numpy()
    if len(profits) >= 2:
        boot = np.array([rng.choice(profits, len(profits), replace=True).mean() for _ in range(2000)])
        low, high = np.percentile(boot, [2.5, 97.5])
    else:
        low = high = np.nan
    rows.append({"条件数": depth, "最后加的": order[depth - 1], "交易次数": len(trades),
                 "每笔平均收益": profits.mean() if len(profits) else np.nan,
                 "95% 区间": f"{low:+.1%} ~ {high:+.1%}", "区间宽度": high - low,
                 "年化": (1 + returns).prod() ** (252 / len(returns)) - 1, "在场时间": (held > 0).mean()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("===== 片段 8：揭晓 =====")
after = spy.loc["2025-07-02":]
print(f"金叉之后 SPY：{signal_day.date()} 收盘 {spy.loc[signal_day, 'close']:.2f} → "
      f"{after.index[-1].date()} 收盘 {after['close'].iloc[-1]:.2f}（{after['close'].iloc[-1] / spy.loc[signal_day, 'close'] - 1:+.1%}）")
drawdown = after["close"] / after["close"].cummax() - 1
print(f"这段里最深的一次回撤 {drawdown.min():.1%}（{drawdown.idxmin().date()}），"
      f"最低收盘 {after['close'].min():.2f}（{after['close'].idxmin().date()}）")
for fill_name, stop_name, exit_name in [("下一根开盘", "不设止损", "死叉出场"), ("下一根开盘", "3 ATR 吊灯", "死叉出场"),
                                        ("回调到 50 日均线", "3 ATR 吊灯", "死叉出场")]:
    returns, _, trades = R.run(spy, variant(spy, fill_name, stop_name, exit_name))
    since = (1 + returns.loc["2025-07-02":]).prod() - 1
    print(f"\n【{fill_name} + {stop_name} + {exit_name}】金叉至今累计 {since:+.1%}（同期买入持有 "
          f"{spy['close'].iloc[-1] / spy.loc[signal_day, 'close'] - 1:+.1%}）")
    this = trades[trades["买入日"] >= "2025-06-01"]
    if len(this) == 0:
        print("  这次金叉之后一直没成交")
        continue
    for _, row in this.iterrows():
        ending = "还拿着（按最后收盘价算）" if row["原因"] == "未平仓" else f"{row['卖出日'].date()} 以 {row['卖出价']:.2f} 出场（{row['原因']}）"
        print(f"  {row['买入日'].date()} 买在 {row['买入价']:.2f}，{ending}，这一笔 {row['收益']:+.1%}")

print("===== 片段 9：主线策略 v3 =====")


def mainline_v3(df):
    """六要素都写出来的主线策略。入场条件把「止损之后要创 20 日新高才买回」这条隐藏规则显式化了。"""
    close = df["close"]
    trend = I.sma(close, 50) > I.sma(close, 200)
    return R.Rule(environment=None,                                  # 一、环境过滤：暂时不加，理由见正文
                  entry=trend & (close >= close.rolling(20).max()),  # 二、入场条件：金叉状态 + 收盘创 20 日新高
                  fill="next_open",                                  # 三、入场方式：下一根开盘市价
                  stop="chandelier", k=3.0, trigger="close",         # 四、初始止损：3 ATR 吊灯，收盘触发（第 20 篇）
                  exit=deaths(df),                                   # 五、出场规则：死叉
                  sizing="full")                                     # 六、仓位：满仓（第 26 篇换成按风险定仓位）


rows = []
for name, df, periods in markets:
    returns, held, trades = R.run(df, mainline_v3(df))
    equity = (1 + returns).cumprod()
    buy_hold = (1 + df["close"].pct_change().fillna(0)).cumprod()
    rows.append({"标的": name, "版本": "v3（六要素）", "年化": equity.iloc[-1] ** (periods / len(returns)) - 1,
                 "最大回撤": (equity / equity.cummax() - 1).min(), "交易次数": len(trades),
                 "在场时间": (held > 0).mean(),
                 "买入持有的年化": buy_hold.iloc[-1] ** (periods / len(buy_hold)) - 1,
                 "买入持有的回撤": (buy_hold / buy_hold.cummax() - 1).min()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
print("\nv3 的六要素：")
print(mainline_v3(spy).describe().to_string())

print("===== 片段 10：每一格换一个选择会怎样 =====")
rows = []
for name, df, periods in markets:
    base = mainline_v3(df)
    close = df["close"]
    changes = {
        "v3 原样": base,
        "三、入场方式改成当根收盘": R.Rule(**(base.__dict__ | {"fill": "close"})),
        "四、止损改成盘中触发": R.Rule(**(base.__dict__ | {"trigger": "low"})),
        "四、止损从 3 ATR 改成 2 ATR": R.Rule(**(base.__dict__ | {"k": 2.0})),
        "四、止损从 3 ATR 改成 5 ATR": R.Rule(**(base.__dict__ | {"k": 5.0})),
        "五、出场改成跌破 20 日新低": R.Rule(**(base.__dict__ | {"exit": (close <= close.rolling(20).min()).fillna(False)})),
        "二、入场去掉「创 20 日新高」": R.Rule(**(base.__dict__ | {"entry": I.sma(close, 50) > I.sma(close, 200)})),
        "一、加上环境过滤 ADX > 20": R.Rule(**(base.__dict__ | {"environment": X.adx(df["high"], df["low"], close)["adx"] > 20})),
    }
    for label, rule in changes.items():
        returns, held, trades = R.run(df, rule)
        equity = (1 + returns).cumprod()
        rows.append({"标的": name, "改动": label, "年化": equity.iloc[-1] ** (periods / len(returns)) - 1,
                     "最大回撤": (equity / equity.cummax() - 1).min(), "交易次数": len(trades)})
sensitivity = pd.DataFrame(rows).pivot_table(index="改动", columns="标的", values=["年化", "交易次数"])
print(sensitivity.round(3).to_string())

print("\n「创 20 日新高」这条入场条件在管什么：止损出场之后，隔多少根 K 线又买回来")
for name, df, periods in markets:
    close = df["close"]
    for label, rule in [("v3（要等 20 日新高）", mainline_v3(df)),
                        ("去掉这一条", R.Rule(**(mainline_v3(df).__dict__ | {"entry": I.sma(close, 50) > I.sma(close, 200)})))]:
        _, _, trades = R.run(df, rule)
        gaps = []
        for k in range(len(trades) - 1):
            if trades["原因"].iloc[k] == "止损":
                gaps.append(df.index.get_loc(trades["买入日"].iloc[k + 1]) - df.index.get_loc(trades["卖出日"].iloc[k]))
        stops = int((trades["原因"] == "止损").sum())
        print(f"  {name} {label}：{stops} 次止损，之后买回的间隔中位数 {np.median(gaps):.0f} 根，"
              f"3 根之内就买回的占 {np.mean(np.array(gaps) <= 3):.0%}")
