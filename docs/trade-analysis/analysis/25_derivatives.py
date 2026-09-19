"""第 25 篇正文里的代码片段（在 talab 项目根目录运行，先运行 25_download.py）。"""
import glob

import numpy as np
import pandas as pd
from talab import bars as B, data as D, derivs as V, indicators as I, risk as K, rules as R

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(25)

print("===== 片段 1：加载数据，先体检 =====")
perp = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/1d/*.zip")))
spot = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
minute = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/1m/*.zip")))
funding = D.load_binance_funding(glob.glob("data/binance/um/BTCUSDT/fundingRate/*.zip"))
premium = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/premiumIndexKlines-1m/*.zip")))["close"]
raw = D.load_binance_metrics(glob.glob("data/binance/um/BTCUSDT/metrics/*.zip"))
print(f"永续日线 {len(perp):,} 根，现货日线 {len(spot):,} 根，1 分钟溢价指数 {len(premium):,} 根，"
      f"资金费率 {len(funding):,} 次")
print(f"持仓量等指标 {len(raw):,} 条（5 分钟一条），{raw.index[0]} 到 {raw.index[-1]}")
print("\n三个数据坑：")
print(f"1. 持仓量为 0 的坏行 {int((raw['持仓量'] == 0).sum())} 条，集中在 "
      f"{sorted({str(d.date()) for d in raw.index[raw['持仓量'] == 0]})[:6]}")
metrics = raw[raw["持仓量"] > 0]
missing = metrics.isna().sum()
print(f"2. 缺失：{missing.to_dict()}")
gap = metrics["大户持仓多空比"]
print(f"   大户持仓多空比缺得最多，按年：{gap[gap.isna()].index.year.value_counts().sort_index().to_dict()}"
      f"——**2022 年（唯一的熊年）缺了大半**")
print("3. 官方文件里每一行都写了两遍，`load_binance_metrics` 里已经去重")

print("===== 片段 2：决策点 =====")
close = perp["close"]
oi_value = V.align(metrics["持仓价值"], close.index)
oi_coins = V.align(metrics["持仓量"], close.index)
daily_funding = funding.resample("1D").sum()
daily_funding.index = daily_funding.index.tz_convert("UTC")
daily_funding = daily_funding.reindex(close.index)
window = pd.DataFrame({"收盘": close, "日涨幅": close.pct_change(),
                       "持仓价值（亿美元）": oi_value / 1e8,
                       "当日资金费（%）": daily_funding * 100,
                       "折成年化": daily_funding * 365}).loc["2021-04-08":"2021-04-13"]
print(window.round(3).to_string())
DAY = pd.Timestamp("2021-04-13", tz="UTC")
print(f"\n2021-04-13：收盘 {close[DAY]:,.2f}（当天 +{close.pct_change()[DAY]:.1%}，历史新高），"
      f"持仓价值 {oi_value[DAY] / 1e8:.2f} 亿美元")
print(f"  持仓价值在此前的历史上排第 {int((oi_value.loc[:DAY] > oi_value[DAY]).sum()) + 1} 高（也就是新高）")
print(f"  当天三次结算的资金费合计 {daily_funding[DAY]:.3%}，折成年化 {daily_funding[DAY] * 365:.0%}，"
      f"在此前的历史上处于 {(daily_funding.loc[:DAY] <= daily_funding[DAY]).mean():.1%} 分位")

print("===== 片段 3：持仓量不是成交量 =====")
compare = pd.DataFrame({"收盘": close, "日涨幅": close.pct_change(),
                        "成交额（亿美元）": perp["quote_volume"] / 1e8,
                        "持仓价值（亿美元）": oi_value / 1e8,
                        "持仓量变化": oi_value.pct_change()}).loc["2021-04-16":"2021-04-20"]
print(compare.round(3).to_string())
big = pd.Timestamp("2021-04-18", tz="UTC")
print(f"\n2021-04-18：成交额 {perp['quote_volume'][big] / 1e8:.0f} 亿美元，是前一天的 "
      f"{perp['quote_volume'][big] / perp['quote_volume'][big - pd.Timedelta('1D')]:.1f} 倍；"
      f"持仓价值却从 {oi_value[big - pd.Timedelta('1D')] / 1e8:.1f} 亿掉到 {oi_value[big] / 1e8:.1f} 亿"
      f"（{oi_value.pct_change()[big]:.1%}）")
print("成交量大＝换手多，持仓量掉＝仓位在成对离场。同一天两件事可以同时发生。")

print("===== 片段 4：价格和持仓量的四种组合 =====")
regime = V.regimes(close, oi_coins)
print(regime.value_counts().to_string())
rows = []
for label in sorted(regime.dropna().unique()):
    mask = (regime == label).fillna(False)
    starts = mask & ~mask.shift(1, fill_value=False)             # 连着的算一段，只取段首
    for horizon in [1, 5, 20]:
        forward = close.shift(-horizon) / close - 1
        picked, everyone = forward[starts].dropna(), forward.dropna()
        boot = np.array([rng.choice(picked, len(picked)).mean() for _ in range(2000)])
        rows.append({"组合": label, "之后": f"{horizon} 天", "段数": len(picked),
                     "平均": picked.mean(), "中位数": picked.median(), "胜率": (picked > 0).mean(),
                     "同期全样本平均": everyone.mean(),
                     "95% 区间": f"[{np.percentile(boot, 2.5):+.3f}, {np.percentile(boot, 97.5):+.3f}]"})
print()
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 5：资金费率是从溢价指数算出来的 =====")
recomputed = V.funding_from_premium(premium)
checked = pd.concat([funding.rename("官方结算"), recomputed.rename("用溢价指数重算")], axis=1).dropna()
error = (checked["用溢价指数重算"] - checked["官方结算"]).abs()
print(f"对上 {len(checked):,} 次结算：中位误差 {error.median():.2e}，90% 分位 {error.quantile(.9):.2e}，"
      f"最大 {error.max():.2e}")
print(f"误差小于 1e-5（0.001 个百分点）的比例：{(error < 1e-5).mean():.1%}")
simple = premium.resample("8h", label="right", closed="right").mean()
simple.index = simple.index.round("h")
plain = simple + np.clip(V.INTEREST_RATE - simple, -V.CLAMP, V.CLAMP)
plain_error = (np.clip(plain, -V.CAP, V.CAP).reindex(checked.index) - checked["官方结算"]).abs()
print(f"改用简单平均（不按时间加权）：中位误差 {plain_error.median():.2e}，差了 "
      f"{plain_error.median() / error.median():.1f} 倍")
print("\n为什么 0.01% 出现得最多：")
average = premium.resample("8h", label="right", closed="right").mean()
inside = ((average >= V.INTEREST_RATE - V.CLAMP) & (average <= V.INTEREST_RATE + V.CLAMP))
print(f"  平均溢价落在 −0.04% 到 +0.06% 之间的比例：{inside.mean():.2%}")
print(f"  官方费率恰好等于 0.01% 的比例：      {(funding.round(6) == V.INTEREST_RATE).mean():.2%}")
print(f"  资金费率的上下限 ±{V.CAP:.1%} = 第一档维持保证金率 0.4% × 0.75（第 24 篇）；"
      f"实际触顶 {int((funding.abs() >= V.CAP - 1e-9).sum())} 次")

print("===== 片段 6：溢价、指数、费率，三个数说的是同一件事 =====")
self_made = V.basis(perp["close"], spot["close"].reindex(perp.index))
premium_day = premium.resample("1D").mean()
three = pd.concat([self_made.rename("自己算的溢价"), premium_day.rename("官方溢价指数"),
                   daily_funding.rename("当日资金费")], axis=1).dropna()
print((three * 100).describe(percentiles=[.01, .5, .99]).round(4).to_string())
print("\n秩相关：")
print(three.rank().corr().round(3).to_string())
print("自己用最新成交价算的溢价和官方溢价指数只有 0.80 的秩相关——因为官方用的是"
      "**一篮子交易所的指数价格**和**冲击价格**，不是 Binance 的最新成交价。")

print("===== 片段 7：极端资金费率之后 =====")


def event_starts(mask: pd.Series) -> pd.Series:
    """连着的日子算一段，只取段首：相邻的窗口重叠得太厉害，不能当成独立样本。"""
    mask = mask.fillna(False)
    return mask & ~mask.shift(1, fill_value=False)


rows = []
for quantile, side in [(0.99, "最高 1%"), (0.95, "最高 5%"), (0.05, "最低 5%"), (0.01, "最低 1%")]:
    level = daily_funding.quantile(quantile)
    mask = (daily_funding >= level) if quantile > 0.5 else (daily_funding <= level)
    starts = event_starts(mask)
    for horizon in [5, 20]:
        forward = close.shift(-horizon) / close - 1
        picked, everyone = forward[starts].dropna(), forward.dropna()
        boot = np.array([rng.choice(picked, len(picked)).mean() for _ in range(2000)])
        rows.append({"阈值": f"{side}（{level:.3%}/天）", "之后": f"{horizon} 天",
                     "天数": int(mask.sum()), "段数": len(picked), "平均": picked.mean(),
                     "中位数": picked.median(), "胜率": (picked > 0).mean(),
                     "同期全样本": everyone.mean(),
                     "95% 区间": f"[{np.percentile(boot, 2.5):+.3f}, {np.percentile(boot, 97.5):+.3f}]"})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("\n负费率是不是只是「跌多了反弹」：找出跌幅相当、但资金费率正常的日子做对照")
past = close / close.shift(20) - 1
low = (daily_funding <= daily_funding.quantile(0.05)).fillna(False)
print(f"  负费率那些天之前 20 天的涨幅中位数 {past[low].median():.1%}，全样本 {past.median():.1%}")
lower, upper = past[low].quantile(.1), past[low].quantile(.9)
control = (past >= lower) & (past <= upper) & ~low & daily_funding.notna()
for horizon in [5, 20]:
    forward = close.shift(-horizon) / close - 1
    a, b = forward[low].dropna(), forward[control].dropna()
    print(f"  之后 {horizon} 天：负费率 {len(a)} 天平均 {a.mean():+.2%}；"
          f"同样跌幅、费率正常 {len(b)} 天平均 {b.mean():+.2%}；差 {a.mean() - b.mean():+.2%}")

print("\n按年拆开（段首、之后 20 天）：")
starts = event_starts(low)
forward20 = close.shift(-20) / close - 1
table = pd.DataFrame({"年": close.index.year, "负费率段首之后": forward20})[starts.to_numpy()].dropna()
everyone = pd.DataFrame({"年": close.index.year, "全样本": forward20}).dropna()
print(pd.concat([table.groupby("年")["负费率段首之后"].agg(["size", "mean"]),
                 everyone.groupby("年")["全样本"].mean()], axis=1).round(4).to_string())

print("===== 片段 8：多空比：先搞清楚它统计的是什么 =====")
print("按**张数**算，多头持仓和空头持仓永远相等——一张合约一个多头一个空头。")
print("所以交易所公布的三个比值统计的都不是「多空持仓量」，而是别的东西：")
print("  大户持仓多空比：大户账户里，净多头仓位之和 ÷ 净空头仓位之和")
print("  账户数多空比：  净多头的账户数 ÷ 净空头的账户数")
print("  主动买卖比：    主动买入成交量 ÷ 主动卖出成交量（这是流量，不是存量）")
rows = []
for column in ["大户持仓多空比", "账户数多空比", "主动买卖比"]:
    series = V.align(metrics[column], close.index)
    for label, mask in [("最高十分位", series >= series.quantile(.9)),
                        ("最低十分位", series <= series.quantile(.1))]:
        starts = event_starts(mask)
        forward = close.shift(-20) / close - 1
        picked = forward[starts].dropna()
        boot = np.array([rng.choice(picked, len(picked)).mean() for _ in range(2000)])
        lower, upper = past[mask.fillna(False)].quantile(.1), past[mask.fillna(False)].quantile(.9)
        control = (past >= lower) & (past <= upper) & ~mask.fillna(False) & series.notna()
        rows.append({"指标": column, "有数据的天数": int(series.notna().sum()), "分组": label,
                     "段数": len(picked), "之前 20 天涨幅中位数": past[mask.fillna(False)].median(),
                     "之后 20 天平均": picked.mean(),
                     "95% 区间": f"[{np.percentile(boot, 2.5):+.3f}, {np.percentile(boot, 97.5):+.3f}]",
                     "同涨幅对照": forward[control].mean(),
                     "差": picked.mean() - forward[control].mean()})
print()
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 9：这两个信号是不是同一件事 =====")
ratio = V.align(metrics["大户持仓多空比"], close.index)
conditions = {"资金费率最低 5%": low,
              "大户持仓多空比最低 10%": (ratio <= ratio.quantile(.1)).fillna(False)}
print(R.overlap(conditions).round(3).to_string())
a, b = conditions["资金费率最低 5%"], conditions["大户持仓多空比最低 10%"]
print(f"\n同时成立 {int((a & b).sum())} 天；只有费率 {int((a & ~b).sum())} 天；"
      f"只有多空比 {int((b & ~a).sum())} 天——重合度很低，是两件事")

print("===== 片段 10：去杠杆：被迫交易者留下的痕迹 =====")
hourly = B.resample_ohlcv(minute, "1h")
oi_hourly = V.align(metrics["持仓价值"], hourly.index)
events = V.deleveraging(oi_hourly, window=12, threshold=0.05)
print(f"持仓量在 12 小时内掉 5% 以上：{int(events.sum())} 次，按年 "
      f"{events[events].index.year.value_counts().sort_index().to_dict()}")
hourly_return = hourly["close"].pct_change()
print(f"事件那一小时的涨跌：中位数 {hourly_return[events].median():+.2%}（全样本 {hourly_return.median():+.2%}）")
print(f"事件前 24 小时的涨跌：中位数 {(hourly['close'] / hourly['close'].shift(24) - 1)[events].median():+.2%}")
rows = []
for horizon in [1, 6, 24, 24 * 7]:
    forward = hourly["close"].shift(-horizon) / hourly["close"] - 1
    picked, everyone = forward[events].dropna(), forward.dropna()
    boot = np.array([rng.choice(picked, len(picked)).mean() for _ in range(2000)])
    rows.append({"之后": f"{horizon} 小时", "次数": len(picked), "平均": picked.mean(),
                 "中位数": picked.median(), "胜率": (picked > 0).mean(), "同期全样本": everyone.mean(),
                 "95% 区间": f"[{np.percentile(boot, 2.5):+.4f}, {np.percentile(boot, 97.5):+.4f}]"})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 11：把资金费率当环境过滤，主线策略会变好吗 =====")


def entries(df):
    price = df["close"]
    return ((I.sma(price, 50) > I.sma(price, 200)) & (price >= price.rolling(20).max())).fillna(False)


def deaths(df):
    return I.cross_below(I.sma(df["close"], 50), I.sma(df["close"], 200)).fillna(False)


spot_funding = daily_funding.reindex(spot.index)
mainline = R.Rule(entry=entries(spot), exit=deaths(spot), fill="next_open",
                  stop="chandelier", k=3.0, trigger="close")
rows = []
for label, environment in [("v3 原样（不过滤）", None),
                           ("资金费率高于 95% 分位时不开新仓", (spot_funding < spot_funding.quantile(.95)).fillna(True)),
                           ("资金费率高于 90% 分位时不开新仓", (spot_funding < spot_funding.quantile(.90)).fillna(True)),
                           ("资金费率为负时不开新仓", (spot_funding >= 0).fillna(True))]:
    returns, held, trades = R.run(spot, R.Rule(**(mainline.__dict__ | {"environment": environment})))
    equity = (1 + returns).cumprod()
    rows.append({"环境过滤": label, "交易数": len(trades), "年化": equity.iloc[-1] ** (365 / len(returns)) - 1,
                 "最大回撤": (equity / equity.cummax() - 1).min(), "在场时间": (held > 0).mean()})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("⚠️ 资金费率从 2020-01 起才有，现货日线从 2017-08 起：2020 年之前的日子过滤不生效（默认放行）")

print("===== 片段 12：揭晓 =====")
after = close.loc[DAY:]
print(pd.DataFrame({"收盘": close, "日涨幅": close.pct_change(),
                    "持仓价值（亿美元）": oi_value / 1e8,
                    "持仓量日变化": oi_value.pct_change(),
                    "当日资金费（%）": daily_funding * 100}).loc["2021-04-14":"2021-04-25"].round(3).to_string())
low_day = close.loc["2021-04-13":"2021-07-31"].idxmin()
print(f"\n从 2021-04-13 收盘 {close[DAY]:,.2f} 算起：")
for horizon, name in [(5, "5 天"), (12, "12 天"), (20, "20 天")]:
    later = close.index[close.index.get_loc(DAY) + horizon]
    print(f"  {name}后（{later.date()}）：{close[later]:,.2f}，{close[later] / close[DAY] - 1:+.1%}")
print(f"  到 2021 年 7 月的最低点 {low_day.date()}：{close[low_day]:,.2f}，{close[low_day] / close[DAY] - 1:+.1%}")
worst = oi_value.pct_change().loc["2021-04-14":"2021-04-25"]
print(f"  持仓价值最大的单日降幅：{worst.min():.1%}（{worst.idxmin().date()}，"
      f"从 {oi_value[worst.idxmin() - pd.Timedelta('1D')] / 1e8:.1f} 亿到 {oi_value[worst.idxmin()] / 1e8:.1f} 亿）")
print(f"  从 4 月 13 日的高点 {oi_value.loc['2021-04-13':'2021-04-25'].max() / 1e8:.1f} 亿，"
      f"到 4 月 19 日的低点 {oi_value.loc['2021-04-13':'2021-04-25'].min() / 1e8:.1f} 亿，六天少了 "
      f"{1 - oi_value.loc['2021-04-13':'2021-04-25'].min() / oi_value.loc['2021-04-13':'2021-04-25'].max():.0%}")
floor = daily_funding.loc["2021-04-14":"2021-04-30"].min()
print(f"  资金费率在 {daily_funding.loc['2021-04-14':'2021-04-30'].idxmin().date()} 掉到 {floor:.3%}/天"
      f"（折年化 {floor * 365:.1%}），也就是 0.01% 的地板")
