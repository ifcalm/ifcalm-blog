"""第 34 篇的数据：Binance 的两个公开接口（不需要账号）。在 talab 项目根目录运行。

- `exchangeInfo`：每个交易对的下单规矩（tickSize、stepSize、minQty、minNotional、maxQty）
- `ticker/price`：现在的价格，用来把 stepSize 换算成钱

⚠️ 两个文件都是**今天**的快照。交易所随时会改这些数，所以它们要和回测结果一起存档。
"""
from talab import data as D

for endpoint, name in [("exchangeInfo", "exchange_info"), ("ticker/price", "ticker_price")]:
    path = D.download_binance_public(endpoint, name)
    print(f"{endpoint:>14} → {path}（{path.stat().st_size / 1024:.0f} KB）")
