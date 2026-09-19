"""第 20 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob

import exchange_calendars as xcals
import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, sessions as SS

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(0)
OHLC = ["open", "high", "low", "close"]

print("===== 片段 1：加载数据 =====")
minute = D.load_binance_klines(sorted(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip")))
hour = B.resample_ohlcv(minute, "1h", traded_only=True)
day = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
spy.loc[spy["volume"] == 9_999_999, "volume"] = np.nan              # 第 3 篇发现的坏值
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
nyse = xcals.get_calendar("XNYS")
print(f"BTC 1 分钟线 {len(minute):,} 根（{minute.index[0]} 到 {minute.index[-1]}）；1 小时线 {len(hour):,} 根；"
      f"日线 {len(day):,} 根")
print(f"SPY {len(spy)} 天，AAPL {len(aapl)} 天（{spy.index[0].date()} 到 {spy.index[-1].date()}）")

print("===== 片段 2：决策点那一夜 =====")
stop = 62271.550597                                                  # 主线 v1 在 2024-04-13 的止损价，片段 9 会重新算一遍
night = minute.loc["2024-04-13 19:40":"2024-04-13 20:20"].copy()
night["成交均价"] = night["quote_volume"] / night["volume"]
touched = night.index[night["low"] <= stop][0]
print(night.loc["2024-04-13 20:04":"2024-04-13 20:10", OHLC + ["成交均价", "volume", "trades"]].round(2).to_string())
print(f"止损价 {stop:.2f}，第一根跌破它的分钟是 {touched}（北京时间 {touched.tz_convert('Asia/Shanghai'):%m-%d %H:%M}，周日）")
print(f"那一分钟：从 {night.loc[touched, 'open']:.0f} 跌到 {night.loc[touched, 'low']:.0f}，成交 {night.loc[touched, 'trades']:,.0f} 笔，"
      f"成交均价 {night.loc[touched, '成交均价']:.2f}（比止损价高 {night.loc[touched, '成交均价'] / stop - 1:+.2%}）")
low_at = minute.loc["2024-04-13 19:40":"2024-04-13 21:00", "low"].idxmin()
start_at = pd.Timestamp("2024-04-13 19:45", tz="UTC")
start_price, bottom = minute.at[start_at, "open"], minute.at[low_at, "low"]
print(f"19:45 的 {start_price:.0f} 到 {low_at:%H:%M} 的 {bottom:.0f}："
      f"{(low_at - start_at).seconds // 60} 分钟跌了 {bottom / start_price - 1:.1%}")
this_hour = minute.loc["2024-04-13 20:00":"2024-04-13 20:59", "quote_volume"].sum()
last_week = minute.loc["2024-04-06 20:00":"2024-04-06 20:59", "quote_volume"].sum()
print(f"当晚 20 点这一小时成交 {this_hour / 1e6:,.0f} 百万美元；上一个周六同一小时 {last_week / 1e6:,.1f} 百万美元，"
      f"差 {this_hour / last_week:.0f} 倍")

print("===== 片段 3：加密的一天 =====")
hour_of_day = SS.utc_hour(hour.index)
by_hour = pd.DataFrame({"成交额占比": hour.groupby(hour_of_day)["quote_volume"].sum() / hour["quote_volume"].sum(),
                        "平均振幅": ((hour["high"] - hour["low"]) / hour["open"]).groupby(hour_of_day).mean(),
                        "平均笔数": hour.groupby(hour_of_day)["trades"].mean()})
by_hour.index.name = "UTC 小时"
print(by_hour.round(4).to_string())
print("\n按时段：")
print(SS.profile(hour, SS.session_of(hour.index)).round(4).to_string())

print("===== 片段 4：周末 =====")
weekend = SS.is_weekend(hour.index)
print(SS.profile(hour, weekend.map({True: "周六周日", False: "周一到周五"})).round(4).to_string())
impact = (hour["close"] / hour["open"] - 1).abs() / (hour["quote_volume"] / 1e8) * 100   # 每成交 1 亿美元，价格走了百分之几
print("\n价格冲击：这一小时里每成交 1 亿美元，价格平均走了多少（中位数，越大越薄）")
print("  按周末：", impact.groupby(weekend.map({True: "周六周日", False: "周一到周五"}).to_numpy()).median().round(3).to_dict())
print("  按时段：", impact.groupby(SS.session_of(hour.index).to_numpy()).median().round(3).to_dict())
weekend_share = weekend.mean()
print(f"周末占全部小时的 {weekend_share:.1%}，但只占成交额的 {hour.loc[weekend.to_numpy(), 'quote_volume'].sum() / hour['quote_volume'].sum():.1%}")
yearly = hour.groupby([hour.index.year, weekend.to_numpy()])["quote_volume"].sum().unstack()
yearly["周末占比"] = yearly[True] / (yearly[True] + yearly[False])
print("\n每年周末成交额占比：", yearly["周末占比"].round(3).to_dict())

print("===== 片段 5：插针在什么时候发生 =====")
spike = (hour["low"] / hour["open"] - 1 <= -0.03) | (hour["high"] / hour["open"] - 1 >= 0.03)
print(f"一小时内偏离开盘价 3% 以上的小时：{int(spike.sum())} 个，占 {spike.mean():.2%}")
compare = pd.DataFrame({"全部小时": SS.session_of(hour.index).value_counts(normalize=True),
                        "插针小时": SS.session_of(hour.index[spike.to_numpy()]).value_counts(normalize=True)})
compare["插针 ÷ 全部"] = compare["插针小时"] / compare["全部小时"]
print(compare.round(3).to_string())
weekend_spike = SS.is_weekend(hour.index[spike.to_numpy()]).mean()
print(f"插针发生在周末的比例 {weekend_spike:.1%}，周末本身占 {weekend_share:.1%}")
thin = hour["quote_volume"].rolling(24 * 7, min_periods=24).median()
print("插针小时的成交额 ÷ 最近一周中位成交额：", round(float((hour["quote_volume"] / thin)[spike.to_numpy()].median()), 2),
      "；普通小时：", round(float((hour["quote_volume"] / thin)[~spike.to_numpy()].median()), 2))
big = hour["quote_volume"] >= hour["quote_volume"].quantile(0.99)     # 成交额最大的 1% 的小时
print(f"成交额最大的 1% 的小时（{int(big.sum())} 个）里，平均振幅 {((hour['high'] - hour['low']) / hour['open'])[big.to_numpy()].mean():.2%}；"
      f"其中周末的 {((hour['high'] - hour['low']) / hour['open'])[(big & weekend).to_numpy()].mean():.2%}，"
      f"工作日的 {((hour['high'] - hour['low']) / hour['open'])[(big & ~weekend).to_numpy()].mean():.2%}")

print("===== 片段 6：美股的隔夜和日内 =====")
rows = []
for name, df in [("SPY", spy), ("AAPL", aapl)]:
    overnight = df["open"] / df["close"].shift(1) - 1
    intraday = df["close"] / df["open"] - 1
    total = df["close"].iloc[-1] / df["close"].iloc[0] - 1
    rows.append({"标的": name, "总涨幅": total, "只吃隔夜": (1 + overnight).prod() - 1, "只吃日内": (1 + intraday).prod() - 1,
                 "隔夜平均": overnight.mean(), "日内平均": intraday.mean(),
                 "隔夜标准差": overnight.std(), "日内标准差": intraday.std(),
                 "隔夜方差占比": overnight.var() / (overnight.var() + intraday.var())})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.4f}"))

print("===== 片段 7：日历上的日子 =====")
sessions = nyse.sessions_in_range("2016-09-15", "2026-09-15")
expiry = SS.third_fridays("2016-09-15", "2026-09-15")
quad = SS.third_fridays("2016-09-15", "2026-09-15", months=(3, 6, 9, 12))
calendar = {"月度期权到期日（第三个周五）": expiry, "四巫日（3/6/9/12 月第三个周五）": quad,
            "月末最后一个交易日": SS.period_ends(sessions), "季末最后一个交易日": SS.period_ends(sessions, "QE"),
            "提前收盘的半日": pd.DatetimeIndex([d.tz_localize(None) for d in nyse.early_closes])}
rows = []
for name, days in calendar.items():
    for symbol, df in [("SPY", spy), ("AAPL", aapl)]:
        relative_volume = df["volume"] / df["volume"].rolling(20).median().shift(1)
        swing = (df["high"] - df["low"]) / df["open"]
        picked = df.index.intersection(pd.DatetimeIndex(days))
        rows.append({"日子": name, "标的": symbol, "天数": len(picked),
                     "成交量 ÷ 前 20 天中位": relative_volume.loc[picked].median(),
                     "平常": relative_volume.median(), "振幅": swing.loc[picked].median(), "平常振幅": swing.median()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("===== 片段 8：FOMC 和财报 =====")
fomc = SS.fomc_dates(2016, 2026)
earnings = SS.sec_filing_dates(320193)                               # 苹果的 CIK
earnings = earnings[(earnings >= "2016-09-15") & (earnings <= "2026-09-15")]
print(f"FOMC 公布利率的日子 {len(fomc)} 天（{fomc[0].date()} 到 {fomc[-1].date()}）；"
      f"苹果发财报 {len(earnings)} 次（8-K 的 2.02 条款）")
for name, df, events, offset in [("SPY 遇上 FOMC", spy, fomc, 0), ("BTC 遇上 FOMC", day, fomc, 0),
                                 ("AAPL 遇上自己的财报", aapl, earnings, 1)]:
    swing = ((df["high"] - df["low"]) / df["open"]).rename("振幅")
    study = SS.event_study(swing, events, before=3, after=3, offset=offset)
    print(f"\n{name}（振幅 = (最高 - 最低) ÷ 开盘）：")
    print(study.to_string(float_format=lambda v: f"{v:.4f}"))
    jump = (df["open"] / df["close"].shift(1) - 1).abs().rename("隔夜跳空")
    window = SS.event_window(jump, events, before=0, after=1, offset=offset)
    print(f"  事件后第一根的隔夜跳空中位数 {window[0].median():.4f}，平常 {jump.median():.4f}")

print("===== 片段 9：主线策略 v1 是怎么被打掉的 =====")


def mainline(df, k=3.0, n_atr=14, breakout=20, fast=50, slow=200, trigger="low", skip=None):
    """主线策略 v1（第 15 篇）加两个开关。

    trigger="low"：盘中最低价碰到止损价就出场（v1 的做法）；trigger="close"：只有收盘价跌破才出场。
    skip：一个布尔序列，标出「这根 K 线不许触发止损」的日子（比如周末），这些日子只在收盘时判断。
    """
    o, h, l, c = (df[x].to_numpy(float) for x in OHLC)
    atr = I.atr(df["high"], df["low"], df["close"], n_atr).to_numpy()
    trend = (I.sma(df["close"], fast) > I.sma(df["close"], slow)).to_numpy()
    quiet = np.zeros(len(c), bool) if skip is None else np.asarray(skip, bool)
    first = df.index.get_loc(I.sma(df["close"], slow).first_valid_index())
    r, held, trades = np.zeros(len(c)), np.zeros(len(c)), []
    holding = buy = sell = locked = False
    for i in range(first, len(c)):
        if holding:
            stop, base = max(stop, highest - k * atr[i - 1]), c[i - 1]
        elif buy:
            holding, buy, entry, entry_i, highest = True, False, o[i], i, o[i]
            stop, base = o[i] - k * atr[i - 1], o[i]
        if holding:
            held[i] = 1
            intraday = trigger == "low" and not quiet[i]
            exit_price = reason = None
            if sell:
                exit_price, reason = o[i], "趋势"
            elif o[i] <= stop:
                exit_price, reason = o[i], "止损（跳空）"
            elif intraday and l[i] <= stop:
                exit_price, reason = stop, "止损"
            elif not intraday and c[i] <= stop:
                exit_price, reason = c[i], "止损（收盘）"
            if reason is None:
                r[i], highest = c[i] / base - 1, max(highest, h[i])
            else:
                r[i] = exit_price / base - 1
                trades.append((df.index[entry_i], entry, df.index[i], exit_price, reason, stop))
                holding, sell, locked = False, False, reason.startswith("止损")
        if holding:
            sell = not trend[i]
        elif locked:
            if trend[i] and c[i] > c[i - breakout:i].max():
                buy, locked = True, False
        else:
            buy = bool(trend[i])
    index = df.index[first:]
    trades = pd.DataFrame(trades, columns=["买入日", "买入价", "卖出日", "卖出价", "原因", "止损价"])
    trades["收益"] = trades["卖出价"] / trades["买入价"] - 1
    return pd.Series(r[first:], index=index), pd.Series(held[first:], index=index), trades


returns, holding, trades = mainline(day)
hit = trades[trades["卖出日"] == "2024-04-13"].iloc[0]
print("2024 年 4 月那一笔：")
print(hit.to_string())
print(f"止损价 {hit['止损价']:.2f}，那天的收盘价 {day.loc['2024-04-13', 'close']:.2f}，"
      f"收盘比止损价高 {day.loc['2024-04-13', 'close'] / hit['止损价'] - 1:.1%}")
print(f"下一次买回：{trades[trades['买入日'] > hit['卖出日']].iloc[0]['买入日'].date()}，"
      f"买入价 {trades[trades['买入日'] > hit['卖出日']].iloc[0]['买入价']:.2f}")

print("===== 片段 10：揭晓 =====")
after = day.loc["2024-04-14":"2024-06-20", "close"]
print(f"止损之后：4 月 17 日最低收在 {day.loc['2024-04-17', 'close']:.0f}，4 月 19 日盘中最低 {day.loc['2024-04-19', 'low']:.0f}，"
      f"5 月 16 日买回价 66206.51，比止损价高 {66206.51 / hit['止损价'] - 1:.1%}")
for label, when in [("马上买回（4 月 14 日开盘）", "2024-04-14"), ("等规则买回（5 月 16 日）", "2024-05-16")]:
    price = day.loc[when, "open"]
    print(f"{label}：买入价 {price:.2f}，到 6 月 20 日 {day.loc['2024-06-20', 'close']:.2f}，"
          f"{day.loc['2024-06-20', 'close'] / price - 1:+.1%}；期间最低收盘 {day.loc[when:'2024-06-20', 'close'].min():.0f}")

print("===== 片段 11：把止损改成收盘价触发 =====")
rows = []
for name, df, periods in [("SPY", spy, 252), ("AAPL", aapl, 252), ("BTC", day, 365)]:
    for label, kwargs in [("v1：盘中触发", {}), ("v2：收盘触发", {"trigger": "close"}),
                          ("v2w：周末只看收盘", {"skip": SS.is_weekend(df.index)})]:
        r, held, t = mainline(df, **kwargs)
        equity = (1 + r).cumprod()
        stops = t[t["原因"].str.startswith("止损")]
        recovered = (df.loc[stops["卖出日"], "close"].to_numpy() > stops["止损价"].to_numpy()).mean() if len(stops) else np.nan
        rows.append({"标的": name, "版本": label, "年化": equity.iloc[-1] ** (periods / len(r)) - 1,
                     "最大回撤": (equity / equity.cummax() - 1).min(), "交易次数": len(t), "止损次数": len(stops),
                     "止损当天收盘又在止损价上方": recovered, "最差一笔": t["收益"].min()})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("\n止损之后价格又回到止损价上方的比例：")
rows = []
for name, df in [("SPY", spy), ("AAPL", aapl), ("BTC", day)]:
    _, _, t = mainline(df)
    stops = t[t["原因"].str.startswith("止损")]
    back = {}
    for horizon in [0, 5, 20]:
        hits = []
        for when, level in zip(stops["卖出日"], stops["止损价"]):
            position = df.index.get_loc(when)
            window = df["close"].iloc[position: position + horizon + 1]
            hits.append(bool((window > level).any()))
        back[f"{horizon} 天内"] = np.mean(hits)
    rows.append({"标的": name, "止损次数": len(stops)} | back)
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.3f}"))

print("\n同一笔交易，两种触发方式的收益（按买入日配对）：")
for name, df in [("SPY", spy), ("AAPL", aapl), ("BTC", day)]:
    _, _, a = mainline(df)
    _, _, b = mainline(df, trigger="close")
    paired = a.set_index("买入日")["收益"].to_frame("v1").join(b.set_index("买入日")["收益"].to_frame("v2"), how="inner")
    diff = paired["v2"] - paired["v1"]
    boot = np.array([diff.iloc[rng.integers(0, len(diff), len(diff))].mean() for _ in range(2000)])
    print(f"{name}：配对上 {len(paired)} 笔，v2 减 v1 平均 {diff.mean():+.4f}，中位数 {diff.median():+.4f}，"
          f"v2 更好的占 {(diff > 0).mean():.1%}，p = {2 * min((boot <= 0).mean(), (boot >= 0).mean()):.3f}")

print("===== 片段 12：财报前不持仓 =====")
overnight = aapl["open"] / aapl["close"].shift(1) - 1
after_earnings = pd.Series(False, index=aapl.index)
for date in earnings:
    position = aapl.index.searchsorted(date) + 1
    if position < len(aapl):
        after_earnings.iloc[position] = True
print(f"苹果 {len(earnings)} 次财报的第二天：隔夜跳空绝对值中位数 {overnight[after_earnings].abs().median():.2%}，"
      f"平常 {overnight[~after_earnings].abs().median():.2%}")
print(f"  这 {int(after_earnings.sum())} 天贡献了全部隔夜收益的 {overnight[after_earnings].sum() / overnight.sum():.1%}，"
      f"占天数的 {after_earnings.mean():.1%}")
buy_hold = (1 + aapl["close"].pct_change().fillna(0)).cumprod()
skip_days = after_earnings | after_earnings.shift(-1, fill_value=False)      # 财报当天和第二天都空仓
filtered = (1 + aapl["close"].pct_change().fillna(0).where(~skip_days, 0)).cumprod()
years = len(aapl) / 252
print(f"一直持有 AAPL：年化 {buy_hold.iloc[-1] ** (1 / years) - 1:.2%}，最大回撤 {(buy_hold / buy_hold.cummax() - 1).min():.1%}")
print(f"财报当天和第二天空仓：年化 {filtered.iloc[-1] ** (1 / years) - 1:.2%}，"
      f"最大回撤 {(filtered / filtered.cummax() - 1).min():.1%}，少持有 {skip_days.mean():.1%} 的时间")
