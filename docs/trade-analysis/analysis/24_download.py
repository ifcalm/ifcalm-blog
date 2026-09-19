"""第 24 篇要用的数据（在 talab 项目根目录运行）。约 2 分钟、60 MB。

1. BTCUSDT U 本位永续合约的资金费率历史（2020-01 至 2026-08，每 8 小时一条）
2. Binance U 本位合约的分层维持保证金表（今天的表，公开接口）
3. FINRA 每日卖空成交量：最近三个月 + 2021 年 1 月那一轮轧空前后
4. Nasdaq 的空头仓位记录（市值前 100 里在 Nasdaq 上市的那些）和 GME 的日线

1 分钟 K 线和标记价格 K 线沿用第 22 篇下载的（`22_download.py`）。
"""
import time
import urllib.error

import numpy as np
import pandas as pd
from talab import data as D

print("===== 1. 资金费率 =====")
paths = D.download_binance_funding("BTCUSDT", "2020-01", "2026-08")
funding = D.load_binance_funding(paths)
print(f"{len(paths)} 个月度文件，{len(funding)} 次结算，{funding.index[0]} 到 {funding.index[-1]}")
print(f"费率区间 {funding.min():.6f} 到 {funding.max():.6f}，中位数 {funding.median():.6f}")

print("===== 2. 分层维持保证金表 =====")
path = D.download_binance_brackets()
brackets = D.load_binance_brackets(path, "BTCUSDT")
print(f"BTCUSDT 共 {len(brackets)} 档，表的更新时间 {brackets.attrs['updated']}")
print(brackets.to_string(index=False))

print("===== 3. FINRA 每日卖空成交量 =====")
recent = pd.bdate_range("2026-06-15", "2026-09-15").strftime("%Y-%m-%d").tolist()
squeeze = pd.bdate_range("2021-01-04", "2021-02-12").strftime("%Y-%m-%d").tolist()
files = D.download_finra_short_volume(recent + squeeze)
print(f"{len(files)} 个交易日的文件（申请 {len(recent) + len(squeeze)} 天，周末假日没有文件）")

print("===== 4. Nasdaq 空头仓位 =====")
listing = D.load_nasdaq_screener(D.download_nasdaq_screener(dest="data/universe_us"))
top = listing.sort_values("market_cap", ascending=False).head(100).index.tolist()
ok, missing = [], []
for symbol in top:
    try:
        path = D.download_nasdaq(symbol, "short-interest", dest="data/short_interest")
        D.load_nasdaq_short_interest(path)
        ok.append(symbol)
    except (TypeError, urllib.error.HTTPError):   # data 是 null 或者 404：接口不覆盖这只
        missing.append(symbol)
    time.sleep(0.3)
print(f"市值前 100 里，{len(ok)} 只拿到了空头仓位记录，{len(missing)} 只没有"
      f"（这个接口只覆盖 Nasdaq 上市的股票，纽交所的不给）")
print("没有的前十个：", missing[:10])
table = D.load_nasdaq_short_interest("data/short_interest/AAPL_short-interest.json")
print(f"AAPL：{len(table)} 期，{table.index[0].date()} 到 {table.index[-1].date()}")
print(table.tail(3).to_string())

print("===== 5. GME 日线（2021 年 1 月那一轮轧空）=====")
D.download_nasdaq("GME", "historical", start="2019-01-01")
gme = D.load_nasdaq_daily("data/nasdaq/GME_historical.json")
print(f"GME 日线 {len(gme)} 根，{gme.index[0].date()} 到 {gme.index[-1].date()}，"
      f"最高收盘 {gme['close'].max():.2f}（{gme['close'].idxmax().date()}）")
print("⚠️ GME 在纽交所上市，Nasdaq 的空头仓位接口不覆盖它（返回「只支持 Nasdaq 上市的股票」），")
print("   所以这一篇讲轧空时用的是 FINRA 的每日卖空成交占比，不是两周一次的空头仓位。")
