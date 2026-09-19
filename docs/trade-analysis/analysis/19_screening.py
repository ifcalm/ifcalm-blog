"""第 19 篇正文里的代码片段（在 talab 项目根目录运行，先运行 analysis/19_download_universe.py）。"""
from pathlib import Path

import numpy as np
import pandas as pd
from talab import data as D, indicators as I, screen as S

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)
rng = np.random.default_rng(0)

print("===== 片段 1：把几百个合约读成宽表 =====")
frames = {folder.name: D.load_binance_klines(folder.glob("1d/*.zip")) for folder in Path("data/universe/um").iterdir()}
volume = S.panel(frames, "volume")
close = S.panel(frames, "close").where(volume > 0)             # ⚠️ 成交量为 0 的是占位 K 线，不是能成交的价格
high, low = S.panel(frames, "high").where(volume > 0), S.panel(frames, "low").where(volume > 0)
dollar = pd.DataFrame({name: S.turnover(df) for name, df in frames.items()}).sort_index(axis=1).where(volume > 0)
print(f"宽表：{close.shape[0]} 行 × {close.shape[1]} 列，{close.index[0].date()} 到 {close.index[-1].date()}")
print(close.loc["2026-08-27":, ["BTCUSDT", "ETHUSDT", "ZECUSDT"]].round(2).to_string())

print("===== 片段 2：名单体检 =====")
trading = close.notna()
first = trading.apply(lambda s: s[s].index[0])
last = trading.apply(lambda s: s[s].index[-1])
stopped = last[last < close.index[-1]]
placeholder = ((volume == 0) & S.panel(frames, "close").notna())
print(f"上过市的 USDT 永续合约：{close.shape[1]} 个；最后一天还在交易的：{int(trading.iloc[-1].sum())} 个；"
      f"中途停止交易的：{len(stopped)} 个")
print("停止交易的按年份：", stopped.dt.year.value_counts().sort_index().to_dict())
print(f"成交量为 0 的占位 K 线：{int(placeholder.to_numpy().sum())} 根，涉及 {int((placeholder.sum() > 0).sum())} 个合约"
      f"（最多的是 {placeholder.sum().idxmax()}，{int(placeholder.sum().max())} 根）")
print("每年最后一天在交易的合约数：", trading.sum(axis=1).resample("YE").last().to_dict())
print("寿命（上市到停止交易）的中位数：", int((last - first).dt.days.median()), "天")
print("名字里带非 ASCII 字符的合约：", [c for c in close.columns if not c.isascii()])
print(f"最后一天「有 K 线」的合约 {int(S.panel(frames, 'close').notna().iloc[-1].sum())} 个，"
      f"其中真的有成交的 {int(trading.iloc[-1].sum())} 个")
print("停止交易之后，K 线还在继续发布（ALPACAUSDT）：")
print(frames["ALPACAUSDT"].loc["2025-04-29":"2025-05-03", ["open", "high", "low", "close", "volume"]].to_string())
print(f"BTCSTUSDT：真正有成交的 {int(trading['BTCSTUSDT'].sum())} 天，之后跟着 {int(placeholder['BTCSTUSDT'].sum())} 根占位 K 线")
for old_name, new_name in [("MATICUSDT", "POLUSDT"), ("RNDRUSDT", "RENDERUSDT")]:
    gone_at, born_at = close[old_name].dropna(), close[new_name].dropna()
    print(f"改名：{old_name} 最后一天 {gone_at.index[-1].date()} 收 {gone_at.iloc[-1]}，"
          f"{new_name} 第一天 {born_at.index[0].date()} 收 {born_at.iloc[0]}")

print("===== 片段 3：三个指标，两道门槛 =====")
natr = pd.DataFrame({name: I.natr(df["high"], df["low"], df["close"]) for name, df in frames.items()}).sort_index(axis=1)
features = {"成交额": S.rolling_turnover(dollar, 20), "涨幅": S.momentum(close, 60),
            "波动率": natr.where(close.notna()), "上市天数": trading.cumsum().where(close.notna())}
filters = {"成交额": (1e7, None), "上市天数": (120, None), "涨幅": (None, None), "波动率": (None, None)}
candidates = S.passes(features, filters)
print("每年最后一天通过门槛的合约数：", candidates.sum(axis=1).resample("YE").last().to_dict())
for day in ["2023-12-31", "2024-12-31", "2025-12-31", "2026-08-31"]:
    row = features["成交额"].loc[day].dropna()
    print(f"{day}：在交易 {int(close.loc[day].notna().sum()):>3} 个，全市场 20 天中位成交额合计 {row.sum() / 1e8:>5.0f} 亿美元，"
          f"其中成交额前 20 个占 {row.nlargest(20).sum() / row.sum():.1%}")

print("===== 片段 4：决策点 =====")
decision = pd.Timestamp("2025-11-19", tz="UTC")
table = S.scan(decision, features, filters, rank_by="涨幅", top=10)
table["成交额"] = (table["成交额"] / 1e6).round(0)                 # 换成百万美元
print(f"{decision.date()} 通过门槛的合约：{int(candidates.loc[decision].sum())} 个；前十名：")
print(table.round(3).to_string())
money = features["成交额"].loc[decision]
print(f"ZEC 的 20 天中位成交额，在当天有成交额的 {int(money.notna().sum())} 个合约里排第 {int((money > money['ZECUSDT']).sum()) + 1}："
      f"只低于 {', '.join(money.nlargest(3).index)}")
zec, btc = close["ZECUSDT"], close["BTCUSDT"]
print(f"ZEC：60 天前 {zec.loc['2025-09-20']:.2f} → 决策日 {zec.loc[decision]:.2f}，涨了 {zec.loc[decision] / zec.loc['2025-09-20'] - 1:.1%}；"
      f"同期 BTC {btc.loc['2025-09-20']:.0f} → {btc.loc[decision]:.0f}，{btc.loc[decision] / btc.loc['2025-09-20'] - 1:+.1%}")

print("===== 片段 5：流动性：几百个标的，实际能交易的有几个 =====")
recent = features["成交额"].loc["2026-08-31"].dropna()
print(f"2026-08-31 有 20 天成交额的合约：{len(recent)} 个")
print("分位数（百万美元）：", (recent.quantile([0.1, 0.25, 0.5, 0.75, 0.9]) / 1e6).round(2).to_dict())
for line in [1e6, 1e7, 1e8, 1e9]:
    passing = recent[recent >= line]
    print(f"  20 天中位成交额 ≥ {line / 1e6:>5.0f} 百万美元：{len(passing):>3} 个，占全市场成交额 {passing.sum() / recent.sum():.1%}")
print("成交额前十（百万美元）：", (recent.nlargest(10) / 1e6).round(0).to_dict())
listing = D.load_nasdaq_screener("data/universe_us/screener.json")
us_turnover = (listing["close"] * listing["volume"]).dropna()
print(f"美股：Nasdaq 的筛选接口列出 {len(listing)} 只股票，当天成交额 ≥ 1000 万美元的 {int((us_turnover >= 1e7).sum())} 只，"
      f"中位数 {us_turnover.median() / 1e4:.0f} 万美元，前 100 只占全部成交额的 {us_turnover.nlargest(100).sum() / us_turnover.sum():.1%}")

print("===== 片段 6：波动率：一个仓位有多大 =====")
risk, stop_atr, share = 0.01, 3, 0.01          # 一笔最多亏账户的 1%；止损放 3 个 ATR；仓位不超过日成交额的 1%
rows = []
for name in ["BTCUSDT", "SOLUSDT", "ZECUSDT", "MERLUSDT", "ALCHUSDT"]:
    rate, money = natr.loc["2026-08-31", name] / 100, features["成交额"].loc["2026-08-31", name]
    rows.append({"合约": name, "收盘价": close.loc["2026-08-31", name], "NATR": rate,
                 "3 ATR 止损距离": stop_atr * rate, "20 天中位成交额": money,
                 "10 万账户的仓位": risk * 100_000 / (stop_atr * rate),     # 仓位金额 = 能亏的钱 ÷ 止损距离
                 "1000 万账户的仓位": risk * 10_000_000 / (stop_atr * rate),
                 "成交额的 1%": share * money})
sizing = pd.DataFrame(rows).set_index("合约")
print("仓位金额 = 账户 × 1% ÷ 止损距离；最后一列是「不超过日成交额 1%」这条上限：")
print(sizing.to_string(float_format=lambda v: f"{v:,.4f}" if v < 1 else f"{v:,.0f}"))
day = pd.Timestamp("2026-08-31", tz="UTC")
sizes = risk / (stop_atr * natr.loc[day] / 100)                    # 每 1 美元账户对应的仓位
for account in [100_000, 1_000_000, 10_000_000, 100_000_000]:
    fits = candidates.loc[day] & (sizes * account <= share * features["成交额"].loc[day])
    print(f"账户 {account:>11,} 美元：通过门槛、且仓位不超过日成交额 1% 的合约 {int(fits.sum()):>3} 个")

print("===== 片段 7：相对强度线 =====")
us = {path.name.split("_")[0]: D.load_nasdaq_daily(path) for path in Path("data/universe_us").glob("*_historical.json")}
sectors = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
us_close = S.panel(us, "close")
window = us_close.loc["2025-09-15":"2026-09-15"]
rs = S.relative_strength(window[sectors], window["SPY"])
summary = pd.DataFrame({"一年涨幅": window[sectors].iloc[-1] / window[sectors].iloc[0] - 1,
                        "相对强度线": rs.iloc[-1].round(1)}).sort_values("相对强度线", ascending=False)
print(f"SPY 这一年：{window['SPY'].iloc[0]:.2f} → {window['SPY'].iloc[-1]:.2f}，{window['SPY'].iloc[-1] / window['SPY'].iloc[0] - 1:+.1%}")
print(summary.round(3).to_string())
own = S.momentum(close, 60)
against_btc = (close / close.shift(60)).div(btc / btc.shift(60), axis=0) - 1
by_gain, by_strength = S.cross_rank(own, mask=candidates), S.cross_rank(against_btc, mask=candidates)
print("按自己的涨幅排名，和按「相对 BTC 的涨幅」排名，最大差别：", float((by_gain - by_strength).abs().max().max()))
hand = window[["XLK", "SPY"]].loc[["2025-09-15", "2026-03-16", "2026-09-15"]]
hand["XLK ÷ SPY"] = hand["XLK"] / hand["SPY"]
hand["相对强度线"] = hand["XLK ÷ SPY"] / hand["XLK ÷ SPY"].iloc[0] * 100
print(hand.round(4).to_string())

print("===== 片段 8：揭晓 =====")
horizon = 20
forward = S.forward_return(close, horizon)
after = table.index
print(f"{decision.date()} 之后 {horizon} 天：")
print(pd.DataFrame({"决策日收盘": close.loc[decision, after], "20 天后": close.loc[decision + pd.Timedelta(days=horizon), after],
                    "收益": forward.loc[decision, after]}).round(3).to_string())
print(f"前十等权 {forward.loc[decision, after].mean():+.1%}，BTC {forward.loc[decision, 'BTCUSDT']:+.1%}，"
      f"当天通过门槛的全部合约等权 {forward.loc[decision].where(candidates.loc[decision]).mean():+.1%}")
earlier = pd.Timestamp("2025-10-15", tz="UTC")
earlier_list = S.scan(earlier, features, filters, rank_by="涨幅", top=10).index
print(f"一个月前的 {earlier.date()}：第一名也是 {earlier_list[0]}，之后 20 天 {forward.loc[earlier, earlier_list[0]]:+.1%}，"
      f"前十等权 {forward.loc[earlier, earlier_list].mean():+.1%}，BTC {forward.loc[earlier, 'BTCUSDT']:+.1%}")
print(f"ZEC 后来：2025-12-09 最低收在 {zec.loc['2025-12-09']:.2f}，2026-08-23 最高收在 {zec.max():.2f}，"
      f"2026-08-31 收在 {zec.iloc[-1]:.2f}（比决策日 {zec.iloc[-1] / zec.loc[decision] - 1:+.1%}）")

print("===== 片段 9：把「买最强的」做成统计 =====")


def bucket_test(close_panel, mask, lookback, horizon=20, k=5, n=2000):
    """按过去 lookback 天的涨幅分成 k 组，每 horizon 天调一次仓，看各组未来 horizon 天的等权收益。"""
    forward = S.forward_return(close_panel, horizon)
    bucket = S.buckets(S.cross_rank(S.momentum(close_panel, lookback), mask=mask), k)
    grouped = S.bucket_returns(bucket, forward, k)
    universe = forward.where(mask).mean(axis=1)
    days = [d for d in close_panel.index[::horizon] if mask.loc[d].sum() >= 50 and grouped.loc[d].notna().all()]
    rows, excess = grouped.loc[days], grouped.loc[days].sub(universe.loc[days], axis=0)
    spread = rows[k] - rows[1]
    boot = np.array([spread.iloc[rng.integers(0, len(spread), len(spread))].mean() for _ in range(n)])
    return {"回看天数": lookback, "调仓次数": len(days)} | {f"第 {g} 组": excess[g].mean() for g in range(1, k + 1)} \
        | {"最强减最弱": spread.mean(), "95% 区间": f"{np.percentile(boot, 2.5):+.3f} ~ {np.percentile(boot, 97.5):+.3f}",
           "p": 2 * min((boot <= 0).mean(), (boot >= 0).mean())}


us_volume, us_trading = S.panel(us, "volume"), us_close.notna()
us_candidates = S.passes({"成交额": S.rolling_turnover(us_close * us_volume, 20),
                          "上市天数": us_trading.cumsum().where(us_close.notna())}, {"成交额": (1e7, None), "上市天数": (120, None)})
stocks = [name for name in us_close.columns if name not in sectors and name != "SPY"]
print("各组的数字是「该组的平均未来 20 天收益 - 当天全部候选的平均」：")
crypto_rows = [bucket_test(close, candidates, lookback) for lookback in [20, 60, 120]]
us_rows = [bucket_test(us_close[stocks], us_candidates[stocks], lookback) for lookback in [20, 60, 120, 250]]
report = pd.DataFrame([{"市场": "BTC 永续合约"} | row for row in crypto_rows]
                      + [{"市场": "美股 100 只"} | row for row in us_rows])
print(report.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

print("===== 片段 10：相对强度线创新高 =====")
excess = forward.sub(forward.where(candidates).mean(axis=1), axis=0)
strength = close.div(btc, axis=0)
price_high, strength_high = close >= close.rolling(60).max(), strength >= strength.rolling(60).max()
days = close.index[::horizon]
rows = []
for name, condition in [("价格创 60 天新高", price_high), ("相对 BTC 的强度线创 60 天新高", strength_high),
                        ("强度线新高、价格没新高", strength_high & ~price_high),
                        ("价格新高、强度线没新高", price_high & ~strength_high)]:
    picked = excess.loc[days].where((condition & candidates).loc[days]).stack().dropna()
    boot = np.array([picked.iloc[rng.integers(0, len(picked), len(picked))].mean() for _ in range(2000)])
    rows.append({"条件": name, "次数": len(picked), "超额收益": picked.mean(), "中位数": picked.median(),
                 "p": 2 * min((boot <= 0).mean(), (boot >= 0).mean())})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.4f}"))

print("===== 片段 11：成交额小的涨得多？ =====")
listed = S.passes(features, {"上市天数": (120, None), "成交额": (0, None)})
liquidity_bucket = S.buckets(S.cross_rank(features["成交额"], mask=listed), 5)
days = [d for d in close.index[::horizon] if listed.loc[d].sum() >= 50]
volatility_bucket = S.buckets(S.cross_rank(features["波动率"], mask=listed), 5)
for title, bucket, column in [("按 20 天中位成交额分 5 组（第 5 组成交额最大）", liquidity_bucket, "成交额"),
                              ("按 NATR 分 5 组（第 5 组波动最大）", volatility_bucket, "波动率")]:
    rows = []
    for group in range(1, 6):
        picked = forward.loc[days].where((bucket == group).loc[days]).stack().dropna()
        level = features[column].where(bucket == group).loc[days].median().median()
        rows.append({"组": group, f"{column}中位数": level / 1e6 if column == "成交额" else level,
                     "未来 20 天平均": picked.mean(), "未来 20 天中位数": picked.median(),
                     "涨超过 50% 的比例": (picked > 0.5).mean(), "跌超过 30% 的比例": (picked < -0.3).mean()})
    print(f"{title}：")
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.4f}"))
young = pd.DataFrame([{"上市 30 天": (s := close[name].dropna()).iloc[30] / s.iloc[0] - 1,
                       "上市 90 天": s.iloc[90] / s.iloc[0] - 1, "上市 120 天": s.iloc[120] / s.iloc[0] - 1}
                      for name in close.columns if close[name].count() > 130])
print(f"\n{len(young)} 个上市满 130 天的合约，从上市第一天收盘算起：")
print(young.agg(["mean", "median"]).to_string(float_format=lambda v: f"{v:.3f}"))
beaten = [close[name].dropna().iloc[90] / close[name].dropna().iloc[0] < btc.reindex(close[name].dropna().index[:91]).ffill().iloc[-1]
          / btc.reindex(close[name].dropna().index[:91]).ffill().iloc[0] for name in close.columns
          if close[name].count() > 91 and name != "BTCUSDT"]
print(f"其中上市 90 天跑输 BTC 的：{np.mean(beaten):.1%}（{len(beaten)} 个合约）")

print("===== 片段 12：幸存者偏差 =====")
alive_today = trading.iloc[-1]
for label, mask in [("全部合约（只要上市满 120 天）", listed), ("通过流动性门槛的合约", candidates)]:
    days = [d for d in close.index[::horizon] if mask.loc[d].sum() >= 30]
    years = (days[-1] - days[0]).days / 365.25
    honest = forward.where(mask).loc[days].mean(axis=1)
    survivors = forward.where(mask & alive_today).loc[days].mean(axis=1)
    annual = lambda r: (1 + r).prod() ** (1 / years) - 1
    print(f"{label}：平均每期 {mask.loc[days].sum(axis=1).mean():.0f} 个标的，{len(days)} 期")
    print(f"    当时真实的名单：年化 {annual(honest):+.2%}；只用今天还在交易的名单：年化 {annual(survivors):+.2%}"
          f"（凭空多出 {annual(survivors) - annual(honest):.2%}）")
final = pd.DataFrame([{"合约": name, "最后 20 天": (s := close[name].dropna()).iloc[-1] / s.iloc[-21] - 1,
                       "最后 60 天": s.iloc[-1] / s.iloc[-61] - 1} for name in stopped.index if close[name].count() > 61])
print(f"\n{len(final)} 个停止交易的合约，停之前的表现：")
print(final[["最后 20 天", "最后 60 天"]].agg(["mean", "median"]).to_string(float_format=lambda v: f"{v:.3f}"))

print("===== 片段 13：名单每天换多少 =====")
order = S.cross_rank(features["涨幅"], mask=candidates, pct=False)
top_ten = order <= 10
days = close.index[close.index >= "2021-01-01"]
lists = {day: set(top_ten.columns[top_ten.loc[day]]) for day in days}
overnight = np.mean([len(lists[days[k]] & lists[days[k - 1]]) / 10 for k in range(1, len(days))])
monthly = np.mean([len(lists[days[k]] & lists[days[k - 20]]) / 10 for k in range(20, len(days))])
fee = 0.0005
print(f"前十名单：隔一天还剩 {overnight:.1%}，隔 20 天还剩 {monthly:.1%}")
print(f"每天调一次仓：一天换掉 {10 * (1 - overnight):.1f} 个，按每边 {fee:.2%} 手续费，一年光手续费 {2 * fee * (1 - overnight) * 365:.1%}")
print(f"每 20 天调一次仓：一次换掉 {10 * (1 - monthly):.1f} 个，一年 {2 * fee * (1 - monthly) * 365 / 20:.1%}")
daily = np.log(close).diff()


def average_correlation(names, day):
    recent = daily.loc[:day].tail(60)[list(names)].dropna(axis=1, how="any")
    matrix = recent.corr().to_numpy()
    return float(matrix[np.triu_indices_from(matrix, 1)].mean())


sample = days[::20]
picked = [average_correlation(lists[day], day) for day in sample]
random_ten = [average_correlation(rng.choice(list(candidates.columns[candidates.loc[day]]), 10, replace=False), day)
              for day in sample]
print(f"\n前十之间 60 天日收益的平均相关系数 {np.nanmean(picked):.3f}；同一天随机挑十个 {np.nanmean(random_ten):.3f}"
      f"（{len(sample)} 个取样日）")
privacy = ["ZECUSDT", "DASHUSDT", "ZENUSDT"]
print(f"决策日前十里的三个隐私币 {privacy}：彼此平均相关 {average_correlation(privacy, decision):.3f}，"
      f"之后 20 天 {forward.loc[decision, privacy].round(3).to_dict()}")
