"""番外篇的数据：BTCUSDT 永续的盘口深度快照（在 talab 项目根目录运行）。

两样东西：

1. `bookDepth`：每 30 秒一张快照，买卖两侧在 ±0.2/1/2/3/4/5% 上的累计挂单金额。
   **2023-01-01 起**，一天约 550 KB，转成宽表之后更小。
2. `bookTicker`：最优买卖报价，第 28 篇已经下过 8 天，这里补上几个崩盘日。
   ⚠️ 这套数据**只有 2023-05-16 到 2024-03-30**，之后 Binance 不再公开。

所以**只有 2023-05-16 到 2024-03-30 这 320 天，价差和深度才配得上对**；
再往后只有深度。正文第三节会专门交代这件事。
"""
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from talab import data as D

DEPTH_DAYS = [day.strftime("%Y-%m-%d")
              for day in pd.date_range("2023-01-01", "2026-08-31", freq="D")]
# 第 28 篇下过的 8 天，外加价差与深度都有的那几个崩盘日
TICKER_DAYS = ["2023-07-19", "2023-08-12", "2023-08-17", "2023-10-16", "2023-10-23",
               "2023-12-11", "2024-01-03", "2024-01-11", "2024-02-28", "2024-03-05",
               "2024-03-30"]

# 串行一天一天下要十几分钟，用线程池按天并行（和第 19 篇的下载脚本同一个写法）
with ThreadPoolExecutor(max_workers=8) as pool:
    got = list(pool.map(lambda day: D.download_binance_book_depth("BTCUSDT", [day]), DEPTH_DAYS))
depth = [path for batch in got for path in batch]
print(f"bookDepth：{len(depth)} 天（{DEPTH_DAYS[0]} → {DEPTH_DAYS[-1]}）")
ticker = D.download_binance_book_ticker("BTCUSDT", TICKER_DAYS)
have_depth = {path.name.split("-30s-")[-1].split(".")[0] for path in depth}
print(f"bookTicker：{len(ticker)} 天，其中价差与深度都有的 "
      f"{len(set(TICKER_DAYS) & have_depth)} 天")
