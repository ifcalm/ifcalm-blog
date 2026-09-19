"""第 24 篇正文里的代码片段（在 talab 项目根目录运行，先运行 24_download.py）。"""
import glob
import json

import numpy as np
import pandas as pd
from talab import bars as B, data as D, indicators as I, risk as K, structure as X

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)

print("===== 片段 1：加载数据 =====")
last = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/1m/*.zip")))
mark = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/markPriceKlines-1m/*.zip")))
um_day = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/1d/*.zip")))
mark_day = B.resample_ohlcv(mark.assign(volume=0.0), "1d")
funding = D.load_binance_funding(glob.glob("data/binance/um/BTCUSDT/fundingRate/*.zip"))
brackets = D.load_binance_brackets("data/binance/brackets.json", "BTCUSDT")
spot = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json").drop(pd.Timestamp("2026-04-20"))
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
MARKETS = {"SPY": (spy, 252), "AAPL": (aapl, 252), "BTC": (spot, 365)}
print(f"永续合约 1 分钟最新价 {len(last):,} 根，标记价格 {len(mark):,} 根，日线 {len(um_day):,} 根")
print(f"资金费率 {len(funding):,} 次结算（{funding.index[0]} 到 {funding.index[-1]}，每 8 小时一次）")
print(f"分层维持保证金表 {len(brackets)} 档，更新时间 {brackets.attrs['updated']}")
missing = um_day.index.difference(mark_day.index)
print(f"⚠️ 标记价格比最新价少 {len(last) - len(mark):,} 分钟，整整缺了 {len(missing)} 天："
      f"{[str(d.date()) for d in missing]}")

print("===== 片段 2：决策点 =====")
ENTRY_TIME = pd.Timestamp("2021-02-08 12:00", tz="UTC")
STOP_TIME = pd.Timestamp("2021-02-08 12:55", tz="UTC")
entry = last.at[ENTRY_TIME, "open"]
now = last.at[STOP_TIME, "close"]
print(f"{ENTRY_TIME}：以开盘价 {entry:,.2f} 开一个 10 倍杠杆的空单（逐仓，名义价值 10 万美元，保证金 1 万）")
window = last.loc["2021-02-08 12:40":"2021-02-08 12:55", ["open", "high", "low", "close"]].round(2)
window["浮亏%"] = ((window["close"] / entry - 1) * 100).round(2)
window["保证金还剩"] = (10_000 * (1 - 10 * (window["close"] / entry - 1))).round(0)
print(window.to_string())
print(f"\n{STOP_TIME} 收盘 {now:,.2f}：价格朝不利方向走了 {now / entry - 1:.2%}，"
      f"1 万保证金只剩 {10_000 * (1 - 10 * (now / entry - 1)):,.0f} 美元")

recent = json.loads(D._fetch("https://data.sec.gov/submissions/CIK0001318605.json"))["filings"]["recent"]
tesla = pd.DataFrame({k: recent[k] for k in ["form", "filingDate", "acceptanceDateTime"]})
ten_k = tesla[(tesla["form"] == "10-K") & (tesla["filingDate"] == "2021-02-08")].iloc[0]
filed = pd.Timestamp(ten_k["acceptanceDateTime"])
moved = pd.Timestamp("2021-02-08 12:43", tz="UTC")
print(f"特斯拉那份 10-K 被 SEC 接收的时间是 {filed}（EDGAR 的记录），"
      f"价格 {moved.strftime('%H:%M')} 才开始动，中间隔了 {int((moved - filed).total_seconds() // 60)} 分钟")

print("===== 片段 3：强平价怎么算 =====")
print(brackets.to_string(index=False))
tier = K.margin_tier(100_000, brackets)
print(f"\n名义价值 10 万美元落在第一档：维持保证金率 {tier['维持保证金率']:.2%}，速算额 {tier['速算额']}，"
      f"最大杠杆 {tier['最大杠杆']}x")
print(f"维持保证金 = 100,000 × {tier['维持保证金率']:.3f} − {tier['速算额']} = "
      f"{K.maintenance_margin(100_000, brackets):,.0f} 美元")
liq = K.liquidation_price(entry, 10, "short", notional=100_000, brackets=brackets)
print(f"\n强平价 = {entry:,.2f} × (−1 − 0.1) ÷ (−1 − {tier['维持保证金率']:.3f}) = {liq:,.2f}"
      f"（比进场价高 {liq / entry - 1:.3%}）")
print("\n三种算法，差多少：")
naive_a = entry * 1.10
naive_b = now * (1 + (1 - 10 * (now / entry - 1)) / 10)
print(pd.Series({
    "天真算法一：10 倍杠杆就是反向 10% 爆仓": naive_a,
    "天真算法二：剩下的保证金比例 ÷ 10，从现在的价格往上量": naive_b,
    "真实强平价": liq}).round(2).to_string())
print(f"从 {now:,.2f} 算起，三种说法分别是还能涨 {naive_a / now - 1:.2%}、{naive_b / now - 1:.2%}、"
      f"{liq / now - 1:.2%}")

print("===== 片段 4：仓位越大，强平价越近 =====")
rows = []
for notional in [100_000, 500_000, 2_000_000, 10_000_000, 50_000_000, 150_000_000]:
    tier = K.margin_tier(notional, brackets)
    leverage = min(10, tier["最大杠杆"])
    level = K.liquidation_price(100.0, leverage, "short", notional=notional, brackets=brackets)
    rows.append({"名义价值": f"{notional:,}", "维持保证金率": tier["维持保证金率"],
                 "这一档允许的最大杠杆": int(tier["最大杠杆"]), "用的杠杆": f"{leverage:g}x",
                 "维持保证金": K.maintenance_margin(notional, brackets),
                 "空单强平价（进场价 100）": level, "要涨多少": level / 100 - 1})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 5：同样的杠杆，空单先爆 =====")
rows = []
for leverage in [1, 2, 3, 5, 10, 20, 25, 50, 100, 125]:
    long_side = K.liquidation_price(100.0, leverage, "long")
    short_side = K.liquidation_price(100.0, leverage, "short")
    rows.append({"杠杆": f"{leverage}x", "多单强平价": long_side, "要跌": 1 - long_side / 100,
                 "空单强平价": short_side, "要涨": short_side / 100 - 1,
                 "空单近多少（个百分点）": (1 - long_side / 100) * 100 - (short_side / 100 - 1) * 100})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 6：做空的收益，上面有一堵墙 =====")
panel = {}
for folder in sorted(glob.glob("data/universe/um/*")):
    files = sorted(glob.glob(f"{folder}/1d/*.zip"))
    if not files:
        continue
    df = D.load_binance_klines(files)
    panel[folder.split("/")[-1]] = df["close"].where(df["volume"] > 0)   # 第 19 篇：成交量 0 的占位 K 线
crypto = pd.DataFrame(panel).sort_index()
stocks = pd.DataFrame({p.split("/")[-1].split("_")[0]: D.load_nasdaq_daily(p)["close"]
                       for p in sorted(glob.glob("data/universe_us/*_historical.json"))}).sort_index()
print(f"加密：{crypto.shape[1]} 个合约 × {crypto.shape[0]} 天；美股：{stocks.shape[1]} 只 × {stocks.shape[0]} 天")
rows = []
for name, table in [("加密永续", crypto), ("美股市值前 100", stocks)]:
    for days in [20, 60, 250]:
        forward = (table.shift(-days) / table - 1).to_numpy().ravel()
        forward = forward[~np.isnan(forward)]
        short = -forward
        rows.append({"市场": name, "持有天数": days, "样本": len(short),
                     "做空最好的一笔": short.max(), "做空最差的一笔": short.min(),
                     "做空中位数": np.median(short), "做空平均": short.mean(),
                     "亏超过本金的比例": (short < -1).mean(), "赚超过本金的比例": (short > 1).mean()})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 7：下跌比上涨快吗 =====")
rows = []
for name, (df, _), threshold in [("SPY", MARKETS["SPY"], 0.08), ("AAPL", MARKETS["AAPL"], 0.12),
                                 ("BTC", MARKETS["BTC"], 0.20)]:
    close = df["close"]
    points = X.zigzag(close, threshold)
    seg = pd.DataFrame({"起价": points["price"][:-1].to_numpy(), "止价": points["price"][1:].to_numpy()})
    seg["根数"] = [close.index.get_loc(b) - close.index.get_loc(a)
                   for a, b in zip(points["time"][:-1], points["time"][1:])]
    seg["幅度"] = seg["止价"] / seg["起价"] - 1
    seg["每根走多少"] = seg["幅度"].abs() / seg["根数"]
    up, down = seg[seg["幅度"] > 0], seg[seg["幅度"] < 0]
    ret = close.pct_change()
    rows.append({"标的": name, "ZigZag 阈值": threshold, "段数": len(seg),
                 "上涨段中位幅度": up["幅度"].median(), "上涨段中位根数": up["根数"].median(),
                 "上涨每根走%": up["每根走多少"].median() * 100, "下跌段中位幅度": down["幅度"].median(),
                 "下跌段中位根数": down["根数"].median(), "下跌每根走%": down["每根走多少"].median() * 100,
                 "下跌快几倍": down["每根走多少"].median() / up["每根走多少"].median(),
                 "最差单日": ret.min(), "最好单日": ret.max(), "偏度": ret.skew()})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 8：美股这边，谁在做空 =====")
listing = D.load_nasdaq_screener("data/universe_us/screener.json")
rows = []
for path in sorted(glob.glob("data/short_interest/*_short-interest.json")):
    symbol = path.split("/")[-1].split("_")[0]
    try:
        table = D.load_nasdaq_short_interest(path)
    except TypeError:                                  # 纽交所上市的，这个接口不给
        continue
    if symbol not in listing.index or listing.loc[symbol, "close"] <= 0:
        continue
    shares = listing.loc[symbol, "market_cap"] / listing.loc[symbol, "close"]
    rows.append({"代码": symbol, "空头股数": table["空头股数"].iloc[-1],
                 "占总股本": table["空头股数"].iloc[-1] / shares, "回补天数": table["回补天数"].iloc[-1]})
short_interest = pd.DataFrame(rows).sort_values("占总股本", ascending=False)
print(f"市值前 100 里有 {len(short_interest)} 只拿到了空头仓位记录（这个接口只覆盖 Nasdaq 上市的股票）")
print(short_interest.head(8).round(4).to_string(index=False))
print(f"...\n中位数：占总股本 {short_interest['占总股本'].median():.2%}，"
      f"回补天数 {short_interest['回补天数'].median():.2f}")
print(short_interest[short_interest["代码"].isin(["AAPL", "TSLA", "NVDA"])].round(4).to_string(index=False))

print("===== 片段 9：卖空占成交的一半，是常态 =====")
files = sorted(glob.glob("data/finra/CNMSshvol*.txt"))
recent = [f for f in files if "CNMSshvol2026" in f]
raw = pd.concat([pd.read_csv(f, sep="|").dropna(subset=["Symbol"]) for f in recent], ignore_index=True)
raw = raw[raw["TotalVolume"] > 0].copy()
raw["卖空占比"] = raw["ShortVolume"] / raw["TotalVolume"]
liquid = raw[raw["TotalVolume"] > 1e6]
print(f"最近 {len(recent)} 个交易日、{len(raw):,} 个「股票 × 日」：卖空占比中位数 {raw['卖空占比'].median():.1%}")
print(f"只看当天成交超过 100 万股的（{len(liquid):,} 个）：中位数 {liquid['卖空占比'].median():.1%}，"
      f"5%–95% 区间 {liquid['卖空占比'].quantile(.05):.1%}–{liquid['卖空占比'].quantile(.95):.1%}")
for symbol in ["AAPL", "SPY", "TSLA", "NVDA", "GME"]:
    s = raw[raw["Symbol"] == symbol]["卖空占比"]
    print(f"  {symbol}: 中位数 {s.median():.1%}，最低 {s.min():.1%}，最高 {s.max():.1%}")

print("===== 片段 10：轧空 =====")
squeeze = [f for f in files if "CNMSshvol2021" in f]
gme_short = pd.concat([pd.read_csv(f, sep="|").dropna(subset=["Symbol"]) for f in squeeze], ignore_index=True)
gme_short = gme_short[gme_short["Symbol"] == "GME"].copy()
gme_short.index = pd.to_datetime(gme_short["Date"].astype(str), format="%Y%m%d")
gme = D.load_nasdaq_daily("data/nasdaq/GME_historical.json")
table = gme.loc["2021-01-12":"2021-02-02", ["open", "high", "low", "close"]].copy()
table["日涨幅"] = table["close"].pct_change()
table["卖空占比"] = gme_short["ShortVolume"] / gme_short["TotalVolume"]
print("⚠️ Nasdaq 的价格按拆股调整过：GME 2022-07-22 一拆四，所以这里的价格是当时的四分之一。")
print(table.round(3).to_string())
start, peak = gme.at[pd.Timestamp("2021-01-12"), "close"], gme.at[pd.Timestamp("2021-01-27"), "close"]
print(f"\n2021-01-12 收盘 {start:.3f}（当时 {start * 4:.2f} 美元）到 2021-01-27 收盘 {peak:.3f}"
      f"（当时 {peak * 4:.2f} 美元）：11 个交易日 {peak / start - 1:+.0%}")
print(f"做空的人：收益 {-(peak / start - 1):.0%}。不是亏了 {1 - start / peak:.0%}"
      f"（那是价格从 {peak:.2f} 跌回 {start:.2f} 要走的幅度），是亏掉本金的 {peak / start - 1:.1f} 倍")
for leverage in [1, 2, 3]:
    level = K.liquidation_price(start, leverage, "short")
    after = gme.loc["2021-01-13":]
    hit = after[after["high"] >= level]
    print(f"  {leverage} 倍空单（强平价 {level:.3f}）：{hit.index[0].date()} 就到了，"
          f"离开仓 {gme.index.get_loc(hit.index[0]) - gme.index.get_loc(pd.Timestamp('2021-01-12'))} 个交易日")

print("===== 片段 11：资金费率是持仓成本（做空这边常常是收入）=====")
print(funding.describe(percentiles=[.01, .05, .5, .95, .99]).round(6).to_string())
yearly = funding.groupby(funding.index.year)
print("\n按年：")
print(pd.DataFrame({"结算次数": yearly.size(), "平均费率": yearly.mean(),
                    "折成年化（×3×365）": yearly.mean() * 3 * 365,
                    "为正的比例": yearly.apply(lambda s: (s > 0).mean()),
                    "最高一次": yearly.max(), "最低一次": yearly.min()}).round(5).to_string())
cumulative = funding.cumsum()
rows = []
for days in [1, 7, 30, 90, 365]:
    step = days * 3
    收 = (cumulative.shift(-step) - cumulative).dropna()          # 费率为正时多头付、空头收
    rows.append({"持有天数": days, "起点数": len(收), "空头收到的中位数": 收.median(), "平均": 收.mean(),
                 "5% 分位": 收.quantile(.05), "95% 分位": 收.quantile(.95),
                 "空头是收钱的比例": (收 > 0).mean()})
print("\n做空持有 N 天，资金费一共收到多少（占名义价值的比例）：")
print(pd.DataFrame(rows).round(4).to_string(index=False))
print(f"\n决策点那一天 16:00 的结算费率是 {funding[pd.Timestamp('2021-02-08 16:00', tz='UTC')]:.5f}，"
      f"历史第 {int((funding > funding[pd.Timestamp('2021-02-08 16:00', tz='UTC')]).sum()) + 1} 高")

print("===== 片段 12：强平价必须在止损价之外 =====")
rows = []
for name, (df, _) in MARKETS.items():
    atr = I.atr(df["high"], df["low"], df["close"])
    distance = (3 * atr / df["close"]).dropna()
    rows.append({"标的": name, "3 ATR 止损距离中位数": distance.median(),
                 "多单最大安全杠杆": K.max_leverage(distance.median(), "long"),
                 "空单最大安全杠杆": K.max_leverage(distance.median(), "short"),
                 "空单·留 2 个点余量": K.max_leverage(distance.median(), "short", cushion=0.02),
                 "止损最宽的 5% 时": distance.quantile(.95),
                 "那时的空单最大杠杆": K.max_leverage(distance.quantile(.95), "short")})
print(pd.DataFrame(rows).round(3).to_string(index=False))
print("\n反过来：选了 L 倍杠杆，止损最远只能放到哪里")
rows = []
for leverage in [2, 3, 5, 10, 20, 25, 50, 100]:
    rows.append({"杠杆": f"{leverage}x",
                 "多单止损最远": 1 - K.liquidation_price(1.0, leverage, "long"),
                 "空单止损最远": K.liquidation_price(1.0, leverage, "short") - 1})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 13：历史重放，多少比例被强平 =====")
hour = B.resample_ohlcv(last, "1h")
mark_hour = B.resample_ohlcv(mark.assign(volume=0.0), "1h")
for label, df, judge, horizons in [("BTC 1 小时线", hour, mark_hour, [24, 24 * 7, 24 * 30]),
                                   ("BTC 日线", um_day, mark_day, [7, 30, 90])]:
    rows = []
    both = df.index.intersection(judge.index)          # 标记价格缺的那些天，两边都去掉
    df, judge = df.loc[both], judge.loc[both]
    keep = df.index[:-(max(horizons))]                 # 所有持有期用同一批起点，才能比
    for leverage in [2, 3, 5, 10, 20, 25, 50, 100]:
        row = {"杠杆": f"{leverage}x"}
        for horizon in horizons:
            for side, word in [("long", "多"), ("short", "空")]:
                hit = K.replay_liquidation(df, leverage, side, horizon=horizon, prices=judge)
                row[f"{horizon} 根内 · {word}"] = hit.reindex(keep).mean()
        rows.append(row)
    print(f"\n--- {label}（{len(keep):,} 个起点）---")
    print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 14：L 倍杠杆不是 L 倍收益 =====")
rows = []
for name, (df, periods) in MARKETS.items():
    ret = df["close"].pct_change().dropna()
    years = len(ret) / periods
    plain = (df["close"].iloc[-1] / df["close"].iloc[0]) ** (1 / years) - 1
    for leverage in [1, 2, 3, 5]:
        daily = 1 + leverage * ret
        if (daily <= 0).any():
            rows.append({"标的": name, "杠杆": f"{leverage}x", "年化": np.nan,
                         "如果杠杆真能放大收益": plain * leverage,
                         "备注": f"有一天就亏光了（{ret.min():.1%} × {leverage}）"})
            continue
        rows.append({"标的": name, "杠杆": f"{leverage}x", "年化": daily.prod() ** (1 / years) - 1,
                     "如果杠杆真能放大收益": plain * leverage, "备注": ""})
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("\n对数收益下，每天再平衡的杠杆仓位年化 ≈ L × μ − L² × σ² ÷ 2，最优杠杆是 μ ÷ σ²：")
for name, (df, periods) in MARKETS.items():
    log_ret = np.log(df["close"]).diff().dropna()
    mu, sigma = log_ret.mean() * periods, log_ret.std() * np.sqrt(periods)
    print(f"  {name}: μ = {mu:.3f}，σ = {sigma:.3f} → μ ÷ σ² = {mu / sigma ** 2:.2f}")

print("===== 片段 15：揭晓 =====")
rows = []
after_mark = mark.loc[ENTRY_TIME:]
for leverage in [1, 2, 3, 5, 10, 20, 25, 50]:
    level = K.liquidation_price(entry, leverage, "short", notional=100_000, brackets=brackets)
    hit = after_mark[after_mark["high"] >= level]
    when = hit.index[0] if len(hit) else None
    rows.append({"杠杆": f"{leverage}x", "强平价": level, "要涨": level / entry - 1,
                 "被强平的时刻": str(when)[:16] if when is not None else "到今天还没有",
                 "撑了多久": str(when - ENTRY_TIME).split(".")[0] if when is not None else ""})
print(pd.DataFrame(rows).round(4).to_string(index=False))
after_last = last.loc[STOP_TIME:]
print(f"\n最新价先越过强平价：{after_last[after_last['high'] >= liq].index[0]}；"
      f"标记价格越过：{after_mark[after_mark['high'] >= liq].index[0]}（强平看的是标记价格，第 22 篇）")
back = last.loc[pd.Timestamp('2021-02-08 12:59', tz='UTC'):]
back = back[back["close"] <= now]
print(f"被强平之后，最新价回到 12:55 那个水平的时间：{back.index[0]}"
      f"（{int((back.index[0] - pd.Timestamp('2021-02-08 12:58', tz='UTC')).total_seconds() // 60)} 分钟后，"
      f"收盘 {back['close'].iloc[0]:,.2f}）")
print(f"但第二天 2021-02-09 标记价格最高 {mark.loc['2021-02-09']['high'].max():,.2f}，"
      f"10 倍空单无论如何都撑不过去")
