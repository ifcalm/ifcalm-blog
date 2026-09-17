"""下载这门课用到的全部基础数据，并打印复现指纹。

在项目根目录运行：python scripts/fetch_course_data.py
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from talab import data as D

CRYPTO_START, CRYPTO_END = "2017-08", "2026-08"          # 加密数据：按月，包含两端
US_START, US_END = "2016-01-01", "2026-09-15"            # 美股数据：Nasdaq 接口最多回溯约 10 年
US_SYMBOLS = {"SPY": "etf", "AAPL": "stocks", "TSLA": "stocks"}


def fetch_binance(interval: str) -> None:
    months = [str(m) for m in pd.period_range(CRYPTO_START, CRYPTO_END, freq="M")]
    # 按月并行下载；每个月都会校验官方 SHA-256，已经下载且校验通过的会跳过
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda m: D.download_binance_klines("BTCUSDT", interval, m, m), months))


def main() -> None:
    for interval in ["1d", "1m"]:
        print(f"下载 BTCUSDT {interval} ……", flush=True)
        fetch_binance(interval)
    for symbol, assetclass in US_SYMBOLS.items():
        print(f"下载 {symbol} 日线 ……", flush=True)
        D.download_nasdaq(symbol, "historical", assetclass=assetclass, start=US_START, end=US_END)
    D.download_nasdaq("AAPL", "dividends")

    print("\n复现指纹：")
    for interval in ["1d", "1m"]:
        df = D.load_binance_klines(Path("data/binance/spot/BTCUSDT", interval).glob("*.zip"))
        print(f"BTCUSDT {interval}:", D.fingerprint(df))
    for symbol in US_SYMBOLS:
        df = D.load_nasdaq_daily(f"data/nasdaq/{symbol}_historical.json")
        print(f"{symbol}:", D.fingerprint(df))


if __name__ == "__main__":
    main()
