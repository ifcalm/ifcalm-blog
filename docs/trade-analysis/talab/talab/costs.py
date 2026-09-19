"""talab.costs：成本。第 28 篇。

第 27 篇的引擎里留了一个 `fee_rate`，这个模块负责把它算出来。

一笔交易的成本有四项，它们的可见度差别很大：

| 这一项 | 加密 | 美股 |
|---|---|---|
| **手续费** | 交易所公开费率表，精确 | 主流券商 0 佣金 |
| **监管费** | 没有 | SEC 的 Section 31 费 + FINRA 的 TAF，只在**卖出**时收，费率公开 |
| **买卖价差** | 公开的盘口数据可以量（第 28 篇量了 8 天） | **没有公开的历史报价**，量不了 |
| **滑点** | 用分钟线重放可以量（第 22 篇） | 日线上量不了 |

于是整篇的结论已经写在这张表里：**能精确算的那几项都很小，算不准的那几项才是大头。**
零佣金不是没有成本，它只是把成本从「看得见的佣金」挪到了「看不见的价差」。

所有函数都返回一个**拆开的**成本表，而不是一个总数——你要知道钱花在哪一项上，
才知道该换券商、换订单类型，还是干脆少交易。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Binance 公开费率表里的 VIP 0 档（现货和 U 本位永续），单位是占成交名义价值的比例。
# ⚠️ 这是**今天**的费率：档位和优惠会变，拿它去算几年前的交易，算的是「按今天的费率会怎样」。
BINANCE_FEES = {"现货 taker": 0.0010, "现货 maker": 0.0010,
                "永续 taker": 0.0005, "永续 maker": 0.0002}

# 第 28 篇用 8 天的公开盘口量出来的 BTCUSDT 永续价差中位数，单位是基点（万分之一）。
BTC_PERP_SPREAD_BP = 0.033


def corwin_schultz(high: pd.Series, low: pd.Series) -> pd.Series:
    """Corwin–Schultz (2012) 的高低价价差估计量：只用最高价和最低价估买卖价差。

    想法是：连续两根 K 线的**单根**高低幅里既有波动也有价差，**两根合起来**的高低幅里
    波动被放大而价差没有，两者相减就能把价差解出来。

    ⚠️ 第 28 篇在 BTC 上用真实盘口检验过它：**高估约两千倍，而且四分之一的日子估出负数**；
    在 SPY 和 AAPL 上一半的日子是负数。**它在这三个市场上都是噪声。**
    这个函数留在这里，是为了让你自己能重做那次检验——
    **有真相的市场用来检验方法，没有真相的市场不要硬估。**
    """
    beta = (np.log(high / low) ** 2).rolling(2).sum()
    high2 = pd.concat([high, high.shift(1)], axis=1).max(axis=1)
    low2 = pd.concat([low, low.shift(1)], axis=1).min(axis=1)
    gamma = np.log(high2 / low2) ** 2
    k = 3 - 2 * np.sqrt(2)
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    return (2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))).rename("价差估计")


def crypto(notional: float, venue: str = "永续 taker", spread_bp: float = BTC_PERP_SPREAD_BP,
           slippage_bp: float = 0.0) -> pd.Series:
    """加密交易所单边的成本拆解（做多的口径，买卖对称）。

    价差只算**一半**：报价的中间价才是「公允价」，你吃掉的是从中间价到卖一的那一半。
    """
    if venue not in BINANCE_FEES:
        raise ValueError(f"venue 只能是 {tuple(BINANCE_FEES)} 之一，收到 {venue!r}")
    fee = notional * BINANCE_FEES[venue]
    spread = notional * spread_bp / 2 / 10_000
    slippage = notional * slippage_bp / 10_000
    total = fee + spread + slippage
    return pd.Series({"名义价值": notional, "手续费": fee, "半个价差": spread, "滑点": slippage,
                      "合计": total, "占名义价值": total / notional})


def us_stock(price: float, shares: float, side: str = "buy", spread_bp: float = 1.0,
             sec_rate: float = 0.0, taf_per_share: float = 0.0, taf_cap: float = np.inf) -> pd.Series:
    """美股单边的成本拆解。费率用 `data.us_fee_schedule()` 现抓，别写死。

    ⚠️ **SEC 的 Section 31 费和 FINRA 的 TAF 只在卖出时收**，买入这两项都是 0。
    佣金按主流零佣金券商算成 0——但那不等于免费：券商把订单卖给做市商（订单流付费，PFOF），
    做市商的钱从价差里赚。所以 `spread_bp` 这一项才是美股真正的成本，而它**没有公开的历史数据**。
    """
    if side not in ("buy", "sell"):
        raise ValueError(f"side 只能是 buy 或 sell，收到 {side!r}")
    notional = price * shares
    commission = 0.0
    sec = notional * sec_rate if side == "sell" else 0.0
    taf = min(shares * taf_per_share, taf_cap) if side == "sell" else 0.0
    spread = notional * spread_bp / 2 / 10_000
    total = commission + sec + taf + spread
    return pd.Series({"名义价值": notional, "佣金": commission, "SEC 费": sec, "FINRA TAF": taf,
                      "半个价差": spread, "合计": total, "占名义价值": total / notional})


def cost_in_r(one_way: float, stop_distance: float) -> float:
    """把成本折算成 R 倍数（第 23 篇）：一来一回的成本 ÷ 止损距离。

    > 一笔交易的成本 = 2 × 单边成本 ÷ 止损距离（单位：R）

    这条式子说明**成本贵不贵取决于止损放得多远**：同样 0.1% 的来回成本，
    止损放 10% 时只占 0.01R，止损放 0.5% 时就占 0.2R——日内策略死在这里。
    """
    if stop_distance <= 0:
        raise ValueError("止损距离要大于 0")
    return 2 * one_way / stop_distance


def annual_drag(one_way: float, trades_per_year: float) -> float:
    """成本每年吃掉多少：`2 × 单边成本 × 每年交易笔数`（一笔进出算两次）。

    这是个近似（没算复利），但它足够回答那个最重要的问题：
    **你的策略一年要跑赢这个数，才刚够把成本挣回来。**
    """
    return 2 * one_way * trades_per_year


def frequency_table(one_way: float, trades_per_year=(2, 6, 12, 52, 250, 1000)) -> pd.DataFrame:
    """同样的单边成本，不同交易频率下每年被吃掉多少。

    成本和频率是**线性**关系，而策略的收益不是——这就是为什么高频信号在成本面前先死一次。
    """
    rows = [{"每年交易笔数": n, "每年的成本": annual_drag(one_way, n)} for n in trades_per_year]
    return pd.DataFrame(rows)
