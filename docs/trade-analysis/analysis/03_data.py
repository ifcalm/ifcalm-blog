"""第 3 篇正文里的全部代码片段，按出现顺序。在 talab 项目根目录运行（需要能访问 data.binance.vision 和 api.nasdaq.com）。"""
import glob
import numpy as np
import pandas as pd
import exchange_calendars as xc
from talab import data as D

pd.set_option("display.width", 120)

print("===== 片段 1：AAPL 三种价格 =====")
D.download_nasdaq("AAPL", "historical", start="2016-01-01", end="2026-09-15")
D.download_nasdaq("AAPL", "dividends")
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")        # 拆股调整后的价格
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")     # 分红记录
raw = D.unadjust_splits(aapl, D.SPLITS["AAPL"])                       # 还原成当时的真实价格
total = D.adjust_total_return(raw, D.SPLITS["AAPL"], divs)            # 拆股 + 分红调整
table = pd.DataFrame({
    "真实成交价": raw["close"],
    "拆股调整": aapl["close"],
    "拆股+分红调整": total["close"],
})
print(table.loc["2020-08-26":"2020-09-01"].round(2))

print("===== 片段 2：分红调整会回溯变化 =====")
for cutoff in ["2021-09-15", "2023-09-15", "2025-09-15", "2026-09-15"]:
    part = raw.loc[:cutoff]
    adj = D.adjust_total_return(part, D.SPLITS["AAPL"], divs[divs.index <= cutoff])
    print(cutoff, "下载时，2020-08-28 的调整后收盘价 =", round(adj.loc["2020-08-28", "close"], 2))

print("===== 片段 3：SPY 体检 =====")
D.download_nasdaq("SPY", "historical", assetclass="etf", start="2016-01-01", end="2026-09-15")
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json")
sessions = xc.get_calendar("XNYS").sessions_in_range("2016-09-15", "2026-09-15")
report = D.health_check(spy, sessions=sessions, wick_k=8, wick_window=250, low_volume_ratio=0.3)
print(D.summarize(report))
print(spy.loc["2026-04-15":"2026-04-22"])

print("===== 片段 4：BTC 1 分钟全历史 =====")
D.download_binance_klines("BTCUSDT", "1m", "2017-08", "2026-08")
btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1m/*.zip"))
print(D.fingerprint(btc))
report = D.health_check(btc, freq="1min")
print(D.summarize(report))

print("===== 片段 5：缺口 =====")
runs = D.missing_runs(report["缺失的 K 线"], "1min")
print("一共", len(runs), "段缺口，", runs["缺失根数"].sum(), "根 K 线")
print(runs.sort_values("缺失根数", ascending=False).head(6).to_string(index=False))

print("===== 片段 6：时间戳没对齐 =====")
print(btc.loc["2017-12-04 05:58":"2017-12-04 06:02", ["open", "close", "volume"]])

print("===== 片段 7：UTC 日线 vs 北京时间日线 =====")
bars = btc.copy()
bars.index = bars.index.floor("1min")                     # 先把没对齐的时间戳对齐
bars = bars[~bars.index.duplicated(keep="last")]
agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
utc_day = bars.loc["2018-01-02":"2026-08-31"].resample("1D").agg(agg)
bj_day = bars.tz_convert("Asia/Shanghai").resample("1D").agg(agg).loc["2018-01-02":"2026-08-31"]
utc_day.index = utc_day.index.date
bj_day.index = bj_day.index.date
days = utc_day.join(bj_day, lsuffix="_utc", rsuffix="_bj", how="inner")
up_utc = days["close_utc"] > days["open_utc"]
up_bj = days["close_bj"] > days["open_bj"]
print("天数：", len(days), " 阴阳不同的天数：", (up_utc != up_bj).sum(), f"（{(up_utc != up_bj).mean():.1%}）")
print(days.loc[[pd.Timestamp("2020-03-13").date()]].T)

print("===== 附：交叉核对与其他数字（正文表格来源） =====")
print("可疑插针按年份", report["可疑插针"].index.year.value_counts().sort_index().to_dict())
z = btc[(btc.volume == 0) & (btc.index.year >= 2018)]
print("2018 年以后零成交量", z.index.to_series().dt.date.value_counts().sort_index().to_dict())
print(btc.loc["2023-03-24 12:38":"2023-03-24 14:01", ["open", "close", "volume"]])
print("2019-01-03", raw.loc["2019-01-02":"2019-01-03"])
e = pd.Timestamp("2020-08-07"); p = pd.Timestamp("2020-08-06")
print("除息", raw.close[p], raw.close[e], divs[e], total.close[e] / total.close[p] - 1, (raw.close[e] + divs[e]) / raw.close[p] - 1)
print("十年增长", aapl.close.iloc[-1] / aapl.close.iloc[0], total.close.iloc[-1] / total.close.iloc[0], len(divs[(divs.index > aapl.index[0])]))
