"""下载第 22 篇用到的合约数据（在 talab 项目根目录运行，约 10 分钟、300 MB）：

1. BTCUSDT U 本位永续合约的 1 分钟**最新成交价**（klines）
2. 同一个合约的 1 分钟**标记价格**（markPriceKlines）——交易所算出来的公允价，止损默认看它
3. 同一个合约的日线

⚠️ 标记价格的文件里成交量一栏全是 0：它不是成交出来的价格。
"""
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from talab import data as D

START, END = "2020-01", "2026-08"                      # U 本位永续合约的数据从 2020-01 开始


def main() -> None:
    months = [str(m) for m in pd.period_range(START, END, freq="M")]
    jobs = [(kind, interval, month) for kind, interval in
            [("klines", "1m"), ("markPriceKlines", "1m"), ("klines", "1d")] for month in months]
    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(lambda job: D.download_binance_klines("BTCUSDT", job[1], job[2], job[2],
                                                            market="um", kind=job[0]), jobs))
    print(f"下载完成：{len(jobs)} 个月度文件")


if __name__ == "__main__":
    main()
