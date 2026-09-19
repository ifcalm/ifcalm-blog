"""下载第 19 篇用到的「全市场」数据（在 talab 项目根目录运行）：

1. Binance U 本位永续合约：所有上过市的 USDT 交易对的日线，包含已经下架的（不然统计会有幸存者偏差）
2. 美股：Nasdaq 公开筛选接口给出的市值最大的 100 只股票 + 11 只行业 ETF 的日线

⚠️ 美股这一半拿到的是「今天还在上市、今天市值最大」的名单，本身就有幸存者偏差，正文第九节量了它的影响。
"""
from concurrent.futures import ThreadPoolExecutor

from talab import data as D

CRYPTO_END = "2026-08"                                        # 课程数据范围的最后一个月
US_START, US_END = "2016-01-01", "2026-09-15"
SECTOR_ETFS = ["SPY", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]


def one_symbol(symbol: str) -> tuple[str, int]:
    months = [m for m in D.binance_months(symbol, "1d", market="um") if m <= CRYPTO_END]
    if not months:
        return symbol, 0
    paths = D.download_binance_klines(symbol, "1d", months[0], months[-1], market="um",
                                      dest="data/universe", skip_missing=True)
    return symbol, len(paths)


def largest_us_stocks(n: int) -> list[str]:
    """Nasdaq 的股票筛选接口给出的今天全部上市公司，按市值从大到小取前 n 个。"""
    listing = D.load_nasdaq_screener(D.download_nasdaq_screener(dest="data/universe_us"))
    ordinary = listing[listing.index.str.isalpha() & listing["market_cap"].notna()]
    return ordinary["market_cap"].nlargest(n).index.tolist()


def main() -> None:
    symbols = [s for s in D.binance_symbols(market="um") if s.endswith("USDT")]
    print(f"Binance U 本位永续合约里上过市的 USDT 交易对：{len(symbols)} 个", flush=True)
    with ThreadPoolExecutor(max_workers=48) as pool:
        done = list(pool.map(one_symbol, symbols))
    print(f"下载完成：{sum(n for _, n in done)} 个月度文件，{sum(1 for _, n in done if n)} 个交易对", flush=True)

    stocks = largest_us_stocks(100)
    print("美股名单：", " ".join(stocks), flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda symbol: D.download_nasdaq(symbol, "historical", dest="data/universe_us",
                                                       assetclass="etf" if symbol in SECTOR_ETFS else "stocks",
                                                       start=US_START, end=US_END), SECTOR_ETFS + stocks))
    print(f"美股下载完成：{len(SECTOR_ETFS) + len(stocks)} 个", flush=True)


if __name__ == "__main__":
    main()
