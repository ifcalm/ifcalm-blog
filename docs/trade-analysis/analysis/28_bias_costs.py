"""第 28 篇正文里的代码片段（在 talab 项目根目录运行，先运行 analysis/28_download.py）。"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from talab import (backtest as BT, costs as C, data as D, indicators as I,
                   rules as R, screen as SC, structure as ST)

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(28)
START = "2020-01-01"
OHLC = ["open", "high", "low", "close"]

print("===== 片段 1：一条很好看的资金曲线 =====")
frames = {folder.name: D.load_binance_klines(folder.glob("1d/*.zip"))
          for folder in Path("data/universe/um").iterdir()}
volume = SC.panel(frames, "volume")
close = SC.panel(frames, "close").where(volume > 0)
dollar = pd.DataFrame({name: SC.turnover(df) for name, df in frames.items()}).sort_index(axis=1).where(volume > 0)
turnover = SC.rolling_turnover(dollar, 20)
returns = close.pct_change()
today_top = pd.DataFrame(False, index=close.index, columns=close.columns)
today_top[turnover.iloc[-1].nlargest(20).index] = True          # 名单：**今天**成交额最大的 20 个
gate_full = turnover >= turnover.stack().median()               # 门槛：**全样本**成交额中位数


def basket(universe, high_window, low_window, gate, cost=0.0, lag=1):
    """等权持有「创 high_window 日新高」的合约，跌破 low_window 日新低就卖。

    `lag=1` 是第 27 篇的时钟规矩：收盘算出来的仓位，下一根才生效。
    """
    state = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    state = state.mask(close >= close.rolling(high_window).max(), 1.0)
    state = state.mask(close <= close.rolling(low_window).min(), 0.0)
    position = state.ffill().fillna(0.0).where(universe & gate & close.notna(), 0.0)
    held = position.shift(lag).fillna(0.0)
    count = held.sum(axis=1)
    churn = held.diff().abs().sum(axis=1)
    daily = (((held * returns).sum(axis=1)) - churn * cost) / count.replace(0, np.nan)
    daily = daily.fillna(0.0).loc[START:]
    equity = (1 + daily).cumprod()
    return {"年化": equity.iloc[-1] ** (365 / len(daily)) - 1,
            "最大回撤": float((equity / equity.cummax() - 1).min()),
            "平均持仓": count.loc[START:].mean(), "每年换手": churn.loc[START:].sum() / (len(daily) / 365),
            "持仓日上涨的比例": float((daily[count.loc[START:] > 0] > 0).mean()),
            "资金曲线": equity, "每日收益": daily}


GRID = [(n, m) for n in [20, 40, 60, 90, 120] for m in [10, 20, 40, 60]]
scan = {p: basket(today_top, p[0], p[1], gate_full)["年化"] for p in GRID}
best = max(scan, key=scan.get)
original = basket(today_top, best[0], best[1], gate_full)
yearly = (1 + original["每日收益"]).groupby(original["每日收益"].index.year).prod() - 1
print(f"标的：今天成交额最大的 20 个永续合约；门槛：20 日成交额高于全样本中位数 "
      f"{turnover.stack().median() / 1e6:.1f} 百万美元")
print(f"参数：在 {len(GRID)} 组（新高 20–120 日 × 新低 10–60 日）里选年化最高的一组 = {best}")
print(f"{START} 到 {close.index[-1].date()}，年化 {original['年化']:.2%}，最大回撤 {original['最大回撤']:.2%}，"
      f"期末是本金的 {original['资金曲线'].iloc[-1]:,.0f} 倍")
print(f"平均同时持有 {original['平均持仓']:.1f} 个，每年换手 {original['每年换手']:.0f} 次")
print("按年：", {k: f"{v:.1%}" for k, v in yearly.round(4).items()}, f"——七年里 {(yearly > 0).sum()} 年赚钱")

print("===== 片段 2：第 27 篇的体检过不了关 =====")
rows = []
for extra in [0, 1, 2]:
    result = basket(today_top, best[0], best[1], gate_full, lag=1 + extra)
    rows.append({"再往后推几根": extra, "年化": result["年化"], "最大回撤": result["最大回撤"],
                 "持仓日上涨的比例": result["持仓日上涨的比例"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("三项体检全过：回撤不是 0，持仓日上涨的比例在五成出头，再往后推一根也只是温和地变差。")
print("**第 27 篇的体检对这条曲线里的问题一个都查不出来**——它们查的是事件顺序，")
print("而这条策略的事件顺序是对的。错的是数据本身，以及挑数据、挑参数的方式。")

print("===== 片段 3：偏差一，前视不只是少写一个 shift =====")
btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
price = btc["close"]
# 最常见的一种写法：把价格缩放到 0 和 1 之间。⚠️ 这两个最值要等最后一天才知道。
scaled = (price - price.min()) / (price.max() - price.min())
print(f"全样本归一化：最低 {price.min():,.0f}（{price.idxmin().date()}）、"
      f"最高 {price.max():,.0f}（{price.idxmax().date()}）；"
      f"2017 年最后一天的归一化值是 {scaled.loc['2017-12-31']:.3f}")
rows = []
for label, low, high in [("全样本的最低价和最高价（偷看未来）", price.min(), price.max()),
                         ("只用到今天为止的最低价和最高价", price.cummin(), price.cummax())]:
    scaled = (price - low) / (high - low)
    state = pd.Series(np.nan, index=price.index)
    state[scaled < 0.25] = 1.0                                  # 归一化后低于 0.25 就买
    state[scaled > 0.75] = 0.0                                  # 高于 0.75 就卖
    position = state.ffill().fillna(0.0)
    equity = (1 + BT.vectorized(price, position, lag=1)).cumprod()
    rows.append({"归一化用的最值": label, "在场比例": float((position.shift(1) > 0).mean()),
                 "年化": equity.iloc[-1] ** (365 / len(equity)) - 1,
                 "最大回撤": float((equity / equity.cummax() - 1).min()),
                 "期末倍数": float(equity.iloc[-1])})
rows.append({"归一化用的最值": "买入持有（对照）", "在场比例": 1.0,
             "年化": (price.iloc[-1] / price.iloc[0]) ** (365 / len(price)) - 1,
             "最大回撤": float((price / price.cummax() - 1).min()), "期末倍数": float(price.iloc[-1] / price.iloc[0])})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("⚠️ 偷看版本「跑赢了买入持有」，老实版本跑输——而两者只差一件事：")
print("   那个最高价是 2025 年才出现的，2017 年的你不可能拿它做归一化。")

print("===== 片段 4：偏差二，幸存者 =====")
alive = close.iloc[-1].notna()
print(f"上过市的合约 {close.shape[1]} 个，最后一天还在交易 {int(alive.sum())} 个，中途停止交易 {int((~alive).sum())} 个")
liquid = turnover >= 1e7
state = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
state = state.mask((close >= close.rolling(60).max()) & liquid, 1.0)
state = state.mask(close <= close.rolling(20).min(), 0.0)
position = state.ffill().fillna(0.0).where(close.notna(), 0.0)
held_all = position.shift(1).fillna(0.0)
rows = []
for label, columns in [("只用今天还在交易的 704 个", close.columns[alive]),
                       ("全部上过市的 864 个", close.columns)]:
    held, part = held_all[columns], returns[columns]
    count = held.sum(axis=1)
    daily = ((held * part).sum(axis=1) / count.replace(0, np.nan)).fillna(0.0).loc[START:]
    equity = (1 + daily).cumprod()
    rows.append({"标的池": label, "个数": len(columns), "年化": equity.iloc[-1] ** (365 / len(daily)) - 1,
                 "最大回撤": float((equity / equity.cummax() - 1).min()), "平均持仓": count.loc[START:].mean()})
print(pd.DataFrame(rows).round(4).to_string(index=False))
legs = [close[c].dropna().iloc[-1] / close[c].dropna().iloc[-61] - 1
        for c in close.columns[~alive] if close[c].notna().sum() > 60]
print(f"停止交易的合约在最后 60 天里：中位数 {np.median(legs):.1%}，平均 {np.mean(legs):.1%}——"
      f"**它们不是安静地消失，是先跌掉一半再消失**")

print("===== 片段 5：偏差三，数据窥探 =====")


def show(params):
    """把参数元组打印成人看的样子（pandas 会把它们变成 numpy 标量）。"""
    return "(%d, %d, %d, %g)" % tuple(params)


def mainline(df, fast, slow, window, k, periods_per_year=365):
    """主线策略的四个参数：快慢均线、创新高的窗口、吊灯止损的 ATR 倍数。"""
    c = df["close"]
    entry = ((I.sma(c, fast) > I.sma(c, slow)) & (c >= c.rolling(window).max())).fillna(False)
    exit_ = I.cross_below(I.sma(c, fast), I.sma(c, slow)).fillna(False)
    series, _, _ = R.run(df, R.Rule(entry=entry, exit=exit_, fill="next_open", stop="chandelier",
                                    k=k, trigger="close", sizing="risk", risk_per_trade=0.10))
    equity = (1 + series).cumprod()
    return equity.iloc[-1] ** (periods_per_year / len(series)) - 1


PARAMS = [(f, s, w, k) for f in [20, 30, 50, 80, 120] for s in [100, 150, 200, 250]
          for w in [10, 20, 40, 60] for k in [2.0, 3.0, 4.0] if f < s]
real = pd.Series({p: mainline(btc, *p) for p in PARAMS})
DEFAULT = (50, 200, 20, 3.0)
print(f"{len(PARAMS)} 组参数跑在 BTC 日线上：")
print(f"  默认参数 {show(DEFAULT)}（主线 v4）年化 {real[DEFAULT]:.2%}，排第 {int((real > real[DEFAULT]).sum()) + 1}")
print(f"  最好的一组 {show(real.idxmax())} 年化 {real.max():.2%}")
print(f"  全部 {len(PARAMS)} 组：中位数 {real.median():.2%}，四分位 {real.quantile(.25):.2%}–{real.quantile(.75):.2%}，"
      f"最差 {real.min():.2%}，亏钱的组 {(real < 0).mean():.1%}")


def shuffle_bars(df, rng):
    """打乱 K 线顺序：保留每根相对前一根收盘价的形状，重新拼成价格（第 9、23 篇）。"""
    relative = np.log(df[OHLC].div(df["close"].shift(1), axis=0))
    relative = relative.dropna().iloc[rng.permutation(len(df) - 1)].reset_index(drop=True)
    previous = df["close"].iloc[0] * np.exp(relative["close"].cumsum().shift(1, fill_value=0))
    out = np.exp(relative[OHLC]).mul(previous, axis=0)
    out.index = df.index[1:]
    return out


fake_max, fake_median = [], []
for _ in range(100):                                            # 打乱之后价格里没有任何趋势
    fake = shuffle_bars(btc, rng)
    values = pd.Series({p: mainline(fake, *p) for p in PARAMS})
    fake_max.append(values.max())
    fake_median.append(values.median())
fake_max, fake_median = pd.Series(fake_max), pd.Series(fake_median)
print(f"\n把 K 线打乱 100 次，每次重扫同样 {len(PARAMS)} 组：")
print(f"  打乱后「最好的一组」的年化：中位 {fake_max.median():.2%}，"
      f"90% 区间 [{fake_max.quantile(.05):.2%}, {fake_max.quantile(.95):.2%}]")
print(f"  打乱后全部组的中位数：{fake_median.median():.2%}（真实数据是 {real.median():.2%}）")
print(f"  打乱之后「最好的一组」超过真实数据最好那组（{real.max():.2%}）的比例：{(fake_max >= real.max()).mean():.1%}")

print("===== 片段 6：同一件事的另一种看法，样本内和样本外 =====")
cut = int(len(btc) * 2 / 3)
inside, outside = btc.iloc[:cut], btc.iloc[cut - 250:]          # 样本外留 250 根给均线预热
values_in = pd.Series({p: mainline(inside, *p) for p in PARAMS})
values_out = pd.Series({p: mainline(outside, *p) for p in PARAMS})
best_in, best_out = values_in.idxmax(), values_out.idxmax()
print(f"样本内 {inside.index[0].date()}～{inside.index[-1].date()}，"
      f"样本外 {outside.index[250].date()}～{outside.index[-1].date()}")
print(pd.DataFrame([
    {"这一组参数": f"样本内最优 {show(best_in)}", "样本内年化": values_in[best_in], "样本外年化": values_out[best_in]},
    {"这一组参数": f"样本外最优 {show(best_out)}", "样本内年化": values_in[best_out], "样本外年化": values_out[best_out]},
    {"这一组参数": f"默认 {show(DEFAULT)}", "样本内年化": values_in[DEFAULT], "样本外年化": values_out[DEFAULT]},
]).round(4).to_string(index=False))
print(f"样本内最优的那一组，在样本外排第 {int((values_out > values_out[best_in]).sum()) + 1} / {len(PARAMS)}")
print(f"样本内排名和样本外排名的秩相关 {values_in.rank().corr(values_out.rank()):.3f}——**不是 0，但也远不是 1**")
print(f"样本内前 10 名在样本外的中位数 {values_out[values_in.nlargest(10).index].median():.2%}，"
      f"全部 {len(PARAMS)} 组在样本外的中位数 {values_out.median():.2%}")

print("===== 片段 7：偏差四，复权 =====")
nasdaq = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
dividends = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
unadjusted = D.unadjust_splits(nasdaq, D.SPLITS["AAPL"])
total_return = D.adjust_total_return(unadjusted, D.SPLITS["AAPL"], dividends)
rows = []
for label, df in [("未复权（当时屏幕上的价格）", unadjusted), ("只按拆股复权", nasdaq),
                  ("拆股 + 分红（全收益）", total_return)]:
    c = df["close"]
    entry = ((I.sma(c, 50) > I.sma(c, 200)) & (c >= c.rolling(20).max())).fillna(False)
    exit_ = I.cross_below(I.sma(c, 50), I.sma(c, 200)).fillna(False)
    series, _, trades = R.run(df, R.Rule(entry=entry, exit=exit_, fill="next_open", stop="chandelier",
                                         k=3.0, trigger="close", sizing="risk", risk_per_trade=0.10))
    equity = (1 + series).cumprod()
    rows.append({"价格序列": label, "年化": equity.iloc[-1] ** (252 / len(series)) - 1,
                 "最大回撤": float((equity / equity.cummax() - 1).min()), "交易数": len(trades),
                 "最差一笔": float((trades["收益"] * trades["仓位"]).min())})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("\n2020-08-31 苹果四拆一，未复权的价格序列上那一天长这样：")
print(unadjusted.loc["2020-08-27":"2020-09-01", OHLC].round(2).to_string())
split_day = unadjusted["close"].pct_change().loc["2020-08-31"]
print(f"回测看到的是「一天跌了 {split_day:.2%}」，而实际上股价一分钱没跌")
print(f"分红：{len(dividends)} 次，合计每股 {dividends.sum():.2f} 美元；"
      f"十年累计 只按拆股复权 {nasdaq['close'].iloc[-1] / nasdaq['close'].iloc[0] - 1:.1%}，"
      f"全收益 {total_return['close'].iloc[-1] / total_return['close'].iloc[0] - 1:.1%}")
print("⚠️ 加密没有拆股也没有分红，所以这一种偏差在加密上不存在——它是股票独有的")

print("===== 片段 8：偏差五，重绘 =====")
swings = ST.zigzag(price, 0.15)
lows = swings[swings["kind"] == -1]
delay = (lows["confirmed_at"] - lows["time"]).dt.days
ahead = [price.loc[when] / value - 1 for when, value in zip(lows["confirmed_at"], lows["price"])]
print(f"15% 的 ZigZag 在 BTC 日线上给出 {len(swings)} 个摆动点，其中低点 {len(lows)} 个")
print(f"一个低点从**发生**到被**确认**：中位 {delay.median():.0f} 天，平均 {delay.mean():.1f} 天，最长 {delay.max()} 天")
print(f"确认那天的价格，已经比那个低点高了：中位 {np.median(ahead):.2%}，平均 {np.mean(ahead):.2%}")
rows = []
for label, column in [("在摆动点当天成交（重绘版）", "time"), ("在摆动点被确认之后成交（老实版）", "confirmed_at")]:
    state = pd.Series(np.nan, index=price.index)
    for _, row in swings.iterrows():
        if row[column] in state.index:
            state[row[column]] = 1.0 if row["kind"] == -1 else 0.0
    position = state.ffill().fillna(0.0)
    equity = (1 + BT.vectorized(price, position, lag=1)).cumprod()
    rows.append({"什么时候成交": label, "在场比例": float((position.shift(1) > 0).mean()),
                 "年化": equity.iloc[-1] ** (365 / len(equity)) - 1,
                 "最大回撤": float((equity / equity.cummax() - 1).min()),
                 "期末是本金的几倍": float(equity.iloc[-1])})
rows.append({"什么时候成交": "买入持有（对照）", "在场比例": 1.0,
             "年化": (price.iloc[-1] / price.iloc[0]) ** (365 / len(price)) - 1,
             "最大回撤": float((price / price.cummax() - 1).min()),
             "期末是本金的几倍": float(price.iloc[-1] / price.iloc[0])})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 9：成本一，真实的买卖价差 =====")
book = D.load_binance_book_ticker(glob.glob("data/binance/um/BTCUSDT/bookTicker-1m/*.csv.gz"))
perp = D.load_binance_klines(glob.glob("data/binance/um/BTCUSDT/1d/*.zip"))
by_day = book.groupby(book.index.floor("D"))
table = by_day.agg(分钟数=("价差", "size"), 平均价差=("价差", "mean"), 中位价差=("价差", "median"),
                   最宽的一分钟=("最宽价差", "max"), 买一量=("买一量", "median"), 中间价=("中间价", "mean"),
                   盘口更新=("更新次数", "sum"))
table["当天振幅"] = ((perp["high"] - perp["low"]) / perp["open"]).reindex(table.index)
table["买一金额（万美元）"] = table["买一量"] * table["中间价"] / 1e4
print("8 天的公开盘口（价差的单位是基点，万分之一）：")
print(table[["平均价差", "中位价差", "最宽的一分钟", "买一金额（万美元）", "盘口更新", "当天振幅"]].round(4).to_string())
tick = 0.1 / book["中间价"].mean() * 1e4
print(f"\n全部 {len(book):,} 分钟：中位 {book['价差'].median():.4f} 基点，平均 {book['价差'].mean():.4f}，"
      f"95% 分位 {book['价差'].quantile(.95):.4f}，最宽的一分钟 {book['价差'].max():.2f}")
print(f"最小变动价位 0.1 美元在平均价 {book['中间价'].mean():,.0f} 上就是 {tick:.4f} 基点——"
      f"**价差基本上就是一跳**")
taker = C.BINANCE_FEES["永续 taker"] * 1e4
print(f"而永续合约的 taker 手续费是 {taker:.0f} 基点，是中位价差的 {taker / book['价差'].median():.0f} 倍")

print("===== 片段 10：成本二，没有盘口数据的市场怎么办 =====")
truth = by_day["价差"].median()
estimate = C.corwin_schultz(perp["high"], perp["low"]) * 1e4
check = pd.DataFrame({"真实中位价差": truth, "高低价估计": estimate.reindex(truth.index)})
check["高估倍数"] = check["高低价估计"] / check["真实中位价差"]
print("在**有真相**的市场上检验高低价价差估计量（单位：基点）：")
print(check.round(3).to_string())
window = estimate.loc["2023-05-16":"2024-03-30"]
print(f"\n同一段 {int(window.notna().sum())} 天：估计值中位 {window.median():.2f} 基点，"
      f"真实 {book['价差'].median():.4f} 基点——**高估约 {window.median() / book['价差'].median():.0f} 倍**，"
      f"而且 {(window < 0).mean():.1%} 的日子估出负数")
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = total_return                                             # 主线一直用的是全收益序列（第 23 篇）
for name, df in [("SPY", spy), ("AAPL", aapl), ("BTC 永续", perp)]:
    values = C.corwin_schultz(df["high"], df["low"]) * 1e4
    print(f"  {name:8s} 估计值中位 {values.median():7.2f} 基点，负数占 {(values < 0).mean():.1%}，"
          f"日均振幅 {((df['high'] - df['low']) / df['open']).median():.2%}")
print("**一半的日子估出负数，说明它在这里就是噪声。** 有真相的市场用来检验方法，")
print("没有真相的市场不要硬估——所以美股的价差这一篇不估，改做敏感性分析（片段 12）。")

print("===== 片段 11：成本三，美股的费率是现抓的 =====")
schedule = D.us_fee_schedule()
print(schedule.to_string())
print(f"\n买入 500 股、200 美元一股（10 万美元），假设价差 1 个基点：")
for side in ["buy", "sell"]:
    one = C.us_stock(200.0, 500.0, side, spread_bp=1.0, sec_rate=schedule["SEC 占卖出金额"],
                     taf_per_share=schedule["TAF 每股"], taf_cap=schedule["TAF 每笔上限"])
    print(f"  {'买入' if side == 'buy' else '卖出'}：" + "，".join(
        f"{k} {v:,.2f}" for k, v in one.drop(["名义价值", "占名义价值"]).items())
        + f"，占名义价值 {one['占名义价值']:.4%}")
print("⚠️ 两项监管费只在卖出时收，加起来 2.06 + 0.08 = 2.14 美元，不到万分之零点三；")
print("   而 1 个基点的价差就是 5 美元。**零佣金不是没有成本，是把成本挪进了价差。**")

print("===== 片段 12：成本四，拆开看，以及频率 =====")
rows = []
for venue in ["永续 maker", "永续 taker", "现货 taker"]:
    one = C.crypto(100_000, venue, spread_bp=float(book["价差"].median()))
    rows.append({"怎么成交": venue, **one.drop("名义价值").to_dict()})
print(pd.DataFrame(rows).round(4).to_string(index=False))
one_way = C.crypto(1.0, "现货 taker", spread_bp=float(book["价差"].median()))["占名义价值"]
print(f"\n主线策略在 BTC 现货上，单边成本 {one_way:.4%}（taker 手续费 + 半个价差）")
print(C.frequency_table(one_way).assign(每年的成本=lambda t: t["每年的成本"].map("{:.2%}".format)).to_string(index=False))
distances = [0.005, 0.02, 0.05, 0.108, 0.20]
print("\n同样的成本，折算成 R（第 23 篇：成本 ÷ 止损距离）：")
print(pd.DataFrame({"止损距离": [f"{d:.1%}" for d in distances],
                    "一来一回占几个 R": [C.cost_in_r(one_way, d) for d in distances]}).round(4).to_string(index=False))

print("===== 片段 13：揭晓，四个问题一个一个修 =====")
rolling_top = turnover.rank(axis=1, ascending=False) <= 20      # 名单：**当时**成交额最大的 20 个
gate_rolling = turnover.ge(turnover.median(axis=1).expanding().median(), axis=0)
ONE_WAY = C.crypto(1.0, "永续 taker", spread_bp=float(book["价差"].median()))["占名义价值"]
steps = [("原样：四个问题都在", today_top, best, gate_full, 0.0),
         ("① 不挑参数，固定 60 日新高 / 20 日新低", today_top, (60, 20), gate_full, 0.0),
         ("② 门槛改成当时算得出来的", today_top, (60, 20), gate_rolling, 0.0),
         ("③ 名单改成当时成交额最大的 20 个", rolling_top, (60, 20), gate_rolling, 0.0),
         ("④ 加上成本", rolling_top, (60, 20), gate_rolling, ONE_WAY)]
rows, previous = [], None
for label, universe, params, gate, cost in steps:
    result = basket(universe, params[0], params[1], gate, cost)
    every_year = (1 + result["每日收益"]).groupby(result["每日收益"].index.year).prod() - 1
    rows.append({"修到哪一步": label, "年化": result["年化"], "最大回撤": result["最大回撤"],
                 "平均持仓": result["平均持仓"], "每年换手": result["每年换手"],
                 "赚钱的年份": f"{int((every_year > 0).sum())}/{len(every_year)}",
                 "比上一步掉了": np.nan if previous is None else previous - result["年化"]})
    previous = result["年化"]
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 14：主线策略 v4 换成含成本的成绩单 =====")
MARKETS = {"SPY": (spy, 252, 0.0), "AAPL": (aapl, 252, 0.0), "BTC": (btc, 365, one_way)}
rows = []
for name, (df, periods, crypto_cost) in MARKETS.items():
    c = df["close"]
    entry = ((I.sma(c, 50) > I.sma(c, 200)) & (c >= c.rolling(20).max())).fillna(False)
    exit_ = I.cross_below(I.sma(c, 50), I.sma(c, 200)).fillna(False)
    plan = dict(entry=entry, exit=exit_, fill="next_open", stop="chandelier", k=3.0,
                trigger="close", sizing="risk", risk_per_trade=0.10)
    if name == "BTC":
        costs = [("不算成本", 0.0), ("现货 taker + 半个价差", crypto_cost),
                 ("再加第 22 篇量到的止损滑点", crypto_cost + 0.00097 / 2)]
    else:
        us = C.us_stock(float(c.iloc[-1]), 100.0, "sell", spread_bp=1.0,
                        sec_rate=schedule["SEC 占卖出金额"], taf_per_share=schedule["TAF 每股"],
                        taf_cap=schedule["TAF 每笔上限"])["占名义价值"]
        costs = [("不算成本", 0.0), ("监管费 + 1 个基点的价差", us),
                 ("价差按 5 个基点算", us + 2 * 1.0 / 10_000)]
    for label, fee in costs:
        result = BT.run(df, BT.Plan(fee_rate=fee, **plan), 100_000.0)
        curve = result["资金曲线"]
        rows.append({"标的": name, "成本": label, "单边费率": fee,
                     "年化": (curve.iloc[-1] / 100_000) ** (periods / len(curve)) - 1,
                     "最大回撤": float((curve / curve.cummax() - 1).min()),
                     "交易数": len(result["交易"]), "手续费合计": result["手续费合计"]})
print(pd.DataFrame(rows).round(4).to_string(index=False))
