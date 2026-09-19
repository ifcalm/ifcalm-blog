"""第 25 篇要用的数据（在 talab 项目根目录运行）。约 8 分钟、250 MB。

1. BTCUSDT 永续合约的持仓量和多空比（`metrics`，5 分钟一条，从 2020-09 起，每天一个文件）
2. 溢价指数 K 线（1 分钟、8 小时、日线）：资金费率就是从 1 分钟的溢价指数平均出来的

资金费率、标记价格、1 分钟 K 线沿用第 22、24 篇下载的。
"""
import glob

import numpy as np
import pandas as pd
from talab import data as D

print("===== 1. 持仓量与多空比 =====")
paths = D.download_binance_metrics("BTCUSDT", "2020-09-01", "2026-09-15")
metrics = D.load_binance_metrics(paths)
print(f"{len(paths)} 个日文件，{len(metrics):,} 条记录，{metrics.index[0]} 到 {metrics.index[-1]}")
print(metrics.describe().round(4).to_string())
gaps = metrics.index.to_series().diff().value_counts().head(5)
print("\n相邻两条的间隔（前五种）：")
print(gaps.to_string())

print("===== 2. 溢价指数 =====")
for interval in ["1m", "8h", "1d"]:
    files = D.download_binance_klines("BTCUSDT", interval, "2020-01", "2026-08",
                                      market="um", kind="premiumIndexKlines")
    premium = D.load_binance_klines(files)
    print(f"{interval}: {len(files)} 个月度文件，{len(premium):,} 根，"
          f"收盘值区间 {premium['close'].min():.5f} 到 {premium['close'].max():.5f}")
