"""第 22 篇正文里的代码片段（在 talab 项目根目录运行）。

需要 U 本位永续合约的三套数据（`22_download.py` 会下载）：
1 分钟最新成交价、1 分钟标记价格、日线。
"""
import glob

import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, orders as O, rules as R

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(0)
OHLC = ["open", "high", "low", "close"]

print("===== 片段 1：三套价格 =====")
last = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/1m/*.zip")))[OHLC + ["volume", "quote_volume"]]
mark = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/markPriceKlines-1m/*.zip")))[OHLC]
day = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/1d/*.zip")))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
print(f"最新成交价 1 分钟线 {len(last):,} 根，标记价格 1 分钟线 {len(mark):,} 根，"
      f"日线 {len(day):,} 根（{day.index[0].date()} 到 {day.index[-1].date()}）")
print("⚠️ 标记价格那份文件里的成交量一栏全是 0：它不是成交出来的价格，是交易所按指数价格加溢价算出来的")

print("===== 片段 2：决策点那一分钟 =====")
window = slice("2024-04-13 20:05", "2024-04-13 20:14")
side_by_side = pd.DataFrame({"最新价最低": last.loc[window, "low"], "最新价收盘": last.loc[window, "close"],
                             "标记价最低": mark.loc[window, "low"], "标记价收盘": mark.loc[window, "close"],
                             "成交额（百万）": last.loc[window, "quote_volume"] / 1e6})
print(side_by_side.round(2).to_string())
stop = 60_000.0
by_last = O.touched(last.loc["2024-04-13":"2024-04-14"], stop, "sell")
by_mark = O.touched(last.loc["2024-04-13":"2024-04-14"], stop, "sell", prices=mark.loc["2024-04-13":"2024-04-14"])
print(f"止损价 {stop:,.0f}：按最新成交价，{by_last} 触发；按标记价格，{by_mark if by_mark else '整天都没触发'}")
print(f"那一分钟：最新价最低 {last.loc['2024-04-13 20:09', 'low']:,.1f}，标记价格最低 {mark.loc['2024-04-13 20:09', 'low']:,.2f}，"
      f"差 {mark.loc['2024-04-13 20:09', 'low'] - last.loc['2024-04-13 20:09', 'low']:,.0f} 美元")
print(f"当天最新价最低 {last.loc['2024-04-13', 'low'].min():,.1f}，标记价格最低 {mark.loc['2024-04-13', 'low'].min():,.2f}")

print("===== 片段 3：两套价格差多少 =====")
both = last.join(mark, rsuffix="_mark", how="inner")
gap = both["low"] / both["low_mark"] - 1
print(f"每分钟「最新价最低 ÷ 标记价最低 - 1」的分布（{len(gap):,} 分钟，单位是百分点，负数 = 最新价更低）：")
print((gap.describe([0.0001, 0.001, 0.01, 0.5, 0.99, 0.999]).drop("count") * 100).round(4).to_string())
print(f"\n偏离超过 0.5% 的分钟：{int((gap <= -0.005).sum()):,} 个（占 {(gap <= -0.005).mean():.3%}）；"
      f"超过 1% 的：{int((gap <= -0.01).sum()):,} 个")
worst = gap.nsmallest(5)
print("最极端的五分钟：")
print(pd.DataFrame({"最新价最低": both["low"][worst.index], "标记价最低": both["low_mark"][worst.index],
                    "偏离": worst}).round(4).to_string())
print("\n按年份，偏离超过 0.5% 的分钟数：", (gap <= -0.005).groupby(gap.index.year).sum().to_dict())

print("===== 片段 4：同一个止损，两种触发价格 =====")
rows = []
for distance in [0.01, 0.03, 0.05]:
    hit_last = hit_mark = only_last = 0
    for date, group in both.groupby(both.index.date):
        level = group["open"].iloc[0] * (1 - distance)                # 每天开盘价下方 distance 的止损
        by_last_hit = bool((group["low"] <= level).any())
        by_mark_hit = bool((group["low_mark"] <= level).any())
        hit_last += by_last_hit
        hit_mark += by_mark_hit
        only_last += by_last_hit and not by_mark_hit
    rows.append({"止损距离": f"-{distance:.0%}", "最新价触发的天数": hit_last, "标记价格触发的天数": hit_mark,
                 "只有最新价触发": only_last, "占最新价触发的": only_last / hit_last})
print(f"把止损放在每天开盘价下方，看这一天会不会被打掉（共 {both.index.normalize().nunique():,} 天）：")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("===== 片段 5：触发 ≠ 成交 =====")
triggers = []
for date, group in both.groupby(both.index.date):
    level = group["open"].iloc[0] * 0.97
    if not (group["low"] <= level).any():
        continue
    fills = {name: O.stop_market_fill(group, level, fill=name)["滑点"] for name in O.FILLS}
    when = O.touched(group, level, "sell")
    position = group.index.get_loc(when)
    later = group["open"].iloc[min(position + 5, len(group) - 1)]
    triggers.append(fills | {"5 分钟后": (level - later) / level, "日期": date})
slippage = pd.DataFrame(triggers).set_index("日期")
print(f"{len(slippage)} 次触发，各种成交口径的滑点（单位是百分点，正数 = 比止损价更不利）：")
print((slippage.describe([0.5, 0.9, 0.99]).drop("count") * 100).round(3).to_string())
print("\n换算成钱：10 万美元的仓位，中位滑点和 99% 分位的滑点各是多少美元")
print((slippage.median() * 100_000).round(0).to_string(), "\n")
print((slippage.quantile(0.99) * 100_000).round(0).to_string())

print("===== 片段 6：止损限价单不成交的风险 =====")
rows = []
for gap_below in [0.0, 0.001, 0.005]:
    filled = {1: 0, 10: 0, 60: 0}
    total = 0
    for date, group in both.groupby(both.index.date):
        level = group["open"].iloc[0] * 0.97
        if not (group["low"] <= level).any():
            continue
        total += 1
        for horizon in filled:
            out = O.stop_limit_fill(group, level, level * (1 - gap_below), expire=horizon)
            filled[horizon] += bool(out["成交"])
    rows.append({"限价放在触发价下方": f"{gap_below:.1%}", "触发次数": total}
                | {f"{h} 分钟内成交": filled[h] / total for h in filled})
print("止损限价单：触发之后价格要回到限价才成交")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

misses = []
for date, group in both.groupby(both.index.date):
    level = group["open"].iloc[0] * 0.97
    if not (group["low"] <= level).any():
        continue
    out = O.stop_limit_fill(group, level, level, expire=60)
    if not out["成交"]:
        after = group.loc[out["触发时间"]:]
        misses.append({"日期": date, "触发价": level, "当天之后最低": after["low"].min(),
                       "又跌了": after["low"].min() / level - 1, "收盘": after["close"].iloc[-1],
                       "收盘时还差": after["close"].iloc[-1] / level - 1})
missed = pd.DataFrame(misses)
print(f"\n一小时内没成交的 {len(missed)} 天：触发之后价格又跌了多少（中位数 {missed['又跌了'].median():.2%}，"
      f"最差 {missed['又跌了'].min():.2%}）")
print(missed.sort_values("又跌了").head(5).to_string(index=False, float_format=lambda v: f"{v:.4f}"))

print("===== 片段 7：括号单：止损和目标在同一根 K 线里 =====")
hour = B.resample_ohlcv(last, "1h", traded_only=True)
rows = []
for name, frame in [("日线", day), ("1 小时线", hour), ("1 分钟线", last)]:
    outcomes = {"先到止损": 0, "先到目标": 0, "同一根": 0, "都没碰到": 0}
    for entry_day in day.index[::5]:                                   # 每 5 天开一次仓，共几百次
        start = entry_day + pd.Timedelta(days=1)
        piece = frame.loc[start:start + pd.Timedelta(days=10)]
        if piece.empty:
            continue
        price = float(piece["open"].iloc[0])
        outcomes[O.oco_first(piece, price * 0.97, price * 1.03)["结果"]] += 1
    total = sum(outcomes.values())
    rows.append({"K 线粒度": name, "样本": total} | {k: v / total for k, v in outcomes.items()})
print("买入之后 10 天内，先碰到 -3% 的止损还是 +3% 的目标（同一段行情，只换 K 线粒度）：")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("===== 片段 8：揭晓 =====")
night = last.loc["2024-04-13 20:00":"2024-04-13 21:00"]
night_mark = mark.loc["2024-04-13 20:00":"2024-04-13 21:00"]
print("同一个 60,000 的止损，四种写法在那一夜的结果：")
rows = []
for label, kwargs in [("止损市价单（标记价格触发）", dict(prices=night_mark)), ("止损市价单（最新价触发）", {})]:
    for fill in ["trigger", "next_open", "worst"]:
        out = O.stop_market_fill(night, stop, fill=fill, **kwargs)
        rows.append({"订单": label, "成交价口径": fill, "触发时间": out["触发时间"], "成交价": out["成交价"],
                     "滑点": out["滑点"]})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print(f"\n⚠️ 1 分钟线看不到那一分钟里价格走过的顺序：20:09 这根从 {last.loc['2024-04-13 20:09', 'open']:,.1f} 开始，"
      f"最低 {last.loc['2024-04-13 20:09', 'low']:,.1f}，收在 {last.loc['2024-04-13 20:09', 'close']:,.1f}。"
      f"止损市价单的真实成交价只能说在最低价和下一根开盘价之间。")
out = O.stop_limit_fill(night, stop, stop)
print(f"止损限价单（最新价触发，限价 {stop:,.0f}）：触发于 {out['触发时间']}，"
      f"按保守口径（从下一根开始算）成交在 {out['成交价']:,.1f}；那一分钟价格已经弹回 "
      f"{last.loc['2024-04-13 20:09', 'close']:,.1f}，所以这一次几乎肯定成交得了。"
      f"真正危险的是价格一路不回头的那些天——第六节数过 {len(missed)} 次。")
print(f"那一夜之后：20:10 收盘 {last.loc['2024-04-13 20:10', 'close']:,.1f}，21:00 收盘 {last.loc['2024-04-13 21:00', 'close']:,.1f}，"
      f"当天收盘 {day.loc['2024-04-13', 'close']:,.1f}")

print("===== 片段 9：日线回测的止损，用分钟线重放 =====")
close = day["close"]
v3 = R.Rule(entry=(I.sma(close, 50) > I.sma(close, 200)) & (close >= close.rolling(20).max()),
            exit=I.cross_below(I.sma(close, 50), I.sma(close, 200)).fillna(False),
            fill="next_open", stop="chandelier", k=3.0, trigger="low")     # 盘中触发，好让止损价可比
returns, held, trades = R.run(day, v3)
stops = trades[trades["原因"] == "止损"]
rows = []
for _, trade in stops.iterrows():
    minutes = last.loc[str(trade["卖出日"].date())]
    level = float(trade["卖出价"])                                       # 回测记的成交价就是止损价
    if minutes.empty or not (minutes["low"] <= level).any():
        continue
    real = O.stop_market_fill(minutes, level, fill="next_open")
    rows.append({"日期": trade["卖出日"].date(), "止损价": level, "分钟线成交价": real["成交价"],
                 "滑点": real["滑点"], "触发时间": real["触发时间"].strftime("%H:%M")})
replay = pd.DataFrame(rows)
print(f"主线 v3 在 BTC 永续合约上共 {len(stops)} 次止损，其中 {len(replay)} 次能在分钟线上重放：")
print(replay.round(4).to_string(index=False))
print(f"\n滑点：中位数 {replay['滑点'].median():.3%}，平均 {replay['滑点'].mean():.3%}，最差 {replay['滑点'].max():.2%}")
print(f"把这些滑点加回去，{len(replay)} 笔止损一共多亏 {replay['滑点'].sum():.2%}（按满仓算），"
      f"年化影响约 {replay['滑点'].sum() / ((day.index[-1] - day.index[0]).days / 365.25):.2%}")

print("===== 片段 10：跳空时的止损 =====")
rows = []
for name, frame in [("SPY", spy), ("AAPL", aapl)]:
    gaps = frame["open"] / frame["close"].shift(1) - 1
    down = gaps[gaps < 0]
    rows.append({"标的": name, "向下跳空的天数": len(down), "跳空中位数": down.median(), "最差的一次": down.min(),
                 "跳空超过 2% 的天数": int((down <= -0.02).sum()),
                 "这些天里开盘价比昨收低的中位数": down[down <= -0.02].median()})
print("止损价在昨天收盘和今天开盘之间时，成交价就是开盘价——跳空有多大，滑点就有多大：")
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.4f}"))
worst_day = (spy["open"] / spy["close"].shift(1) - 1).idxmin()
print(f"SPY 最差的一次：{worst_day.date()} 开盘 {spy.loc[worst_day, 'open']:.2f}，"
      f"前一天收盘 {spy['close'].shift(1)[worst_day]:.2f}（{spy.loc[worst_day, 'open'] / spy['close'].shift(1)[worst_day] - 1:.1%}）")
