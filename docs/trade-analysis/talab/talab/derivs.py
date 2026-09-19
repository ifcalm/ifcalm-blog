"""talab.derivs：永续合约的衍生品数据。第 25 篇。

现货只有一个数：价格。永续合约还有三个公开的数，它们说的是同一件事的不同侧面：

- **持仓量**：还没有平掉的合约有多少张。每一张合约都有一个多头和一个空头，
  所以它不是「有多少人看多」，是「有多少对人正在对赌」。
- **资金费率**：每 8 小时多空之间互相付的钱。它由**溢价指数**算出来，
  而溢价指数就是永续价格偏离现货指数的程度。
- **多空比**：交易所按账户数或按持仓量统计的比例。
  ⚠️ 按**张数**算的多空持仓量永远相等（一张合约两个人），所以这些比值统计的一定是别的东西。

这个模块把这几个数对齐到 K 线上，并且把资金费率的公式实现一遍——
能用公开数据重算出交易所的结算值，才算真的懂它是怎么来的。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

INTEREST_RATE = 0.0001        # 每 8 小时 0.01%，Binance 的默认利率
CLAMP = 0.0005                # 夹住 ±0.05%
CAP = 0.003                   # 上下限 ±0.3%，等于第一档维持保证金率 0.4% 的 0.75 倍（第 24 篇）


def align(series: pd.Series, index: pd.DatetimeIndex, how: str = "last") -> pd.Series:
    """把细粒度的序列（比如 5 分钟一条的持仓量）对齐到 K 线的索引上。

    默认取每根 K 线**区间内最后一个**值：持仓量是存量，K 线收盘那一刻的存量才和收盘价配对。
    `how="mean"` 取区间平均，用在流量型的数据上。
    ⚠️ 只用区间内的数据，不往后借（那是前视偏差，第 7 篇）。
    """
    if how not in ("last", "mean", "max", "min"):
        raise ValueError(f"how 只能是 last / mean / max / min，收到 {how!r}")
    bucket = pd.cut(series.index, bins=index.append(index[-1:] + (index[1] - index[0])),
                    right=False, labels=index)
    out = series.groupby(bucket, observed=False).agg(how)
    out.index = index
    return out


def funding_from_premium(premium: pd.Series, interval: str = "8h",
                         interest_rate: float = INTEREST_RATE, clamp: float = CLAMP,
                         cap: float = CAP) -> pd.Series:
    """用 1 分钟的溢价指数重算资金费率，交易所的公式是：

    > 资金费率 = 平均溢价指数 + clamp(利率 − 平均溢价指数, −0.05%, +0.05%)

    所以**只要平均溢价落在 −0.04% 到 +0.06% 之间，费率就精确等于利率 0.01%**——
    这就是为什么 0.01% 是出现最多的那个值。超出这个范围，费率才跟着溢价走。
    最后再用 ±0.3% 的上下限夹一次（这个上下限是第一档维持保证金率的 0.75 倍，第 24 篇）。

    「平均溢价指数」是**时间加权**的：越靠近结算时刻的那一分钟，权重越大（线性递增）。
    用简单平均也能算个大概，但和官方结算值的误差会大四倍。
    """
    def weighted(values: np.ndarray) -> float:
        w = np.arange(1, len(values) + 1)
        return float(np.dot(values, w) / w.sum())

    average = premium.resample(interval, label="right", closed="right").apply(
        lambda x: weighted(x.to_numpy()) if len(x) else np.nan)
    average.index = average.index.round("h")
    rate = average + np.clip(interest_rate - average, -clamp, clamp)
    return np.clip(rate, -cap, cap).rename("funding")


def annualize(funding: pd.Series, hours: float = 8.0) -> pd.Series:
    """把「每 8 小时」的费率折成年化，方便和借券费、利率放在一起看。

    用的是单利（× 一年结算多少次），不是复利：资金费按名义价值收，不会自动滚进本金。
    """
    return funding * (365 * 24 / hours)


def basis(perp: pd.Series, spot: pd.Series) -> pd.Series:
    """永续合约相对现货的溢价（正数＝合约比现货贵）。两边先按时间对齐。"""
    joined = pd.concat([perp.rename("perp"), spot.rename("spot")], axis=1).dropna()
    return (joined["perp"] / joined["spot"] - 1).rename("basis")


REGIMES = {(True, True): "价涨 + 仓涨：新多进场",
           (True, False): "价涨 + 仓跌：空头平仓",
           (False, True): "价跌 + 仓涨：新空进场",
           (False, False): "价跌 + 仓跌：多头平仓"}


def regimes(close: pd.Series, open_interest: pd.Series) -> pd.Series:
    """价格和持仓量的四种组合，教科书上的那张表。

    背后的算术只有一句话：**持仓量要涨，必须同时有一个新的多头和一个新的空头**；
    要跌，必须有一对老仓位同时离场。所以这四格说的是「这根 K 线上，
    动的主要是新开的仓还是平掉的仓」。

    ⚠️ 这只是记账恒等式给出的一种读法，不是预测。第 25 篇把四格之后的收益都统计了一遍。
    """
    price_up = close.diff() > 0
    oi_up = open_interest.reindex(close.index).diff() > 0
    valid = close.diff().notna() & open_interest.reindex(close.index).diff().notna()
    labels = [REGIMES[(bool(p), bool(o))] for p, o in zip(price_up, oi_up)]
    return pd.Series(labels, index=close.index).where(valid).rename("组合")


def deleveraging(open_interest: pd.Series, window: int = 12, threshold: float = 0.05) -> pd.Series:
    """去杠杆事件：持仓量在 `window` 根之内掉了 `threshold` 以上。

    Binance 从 2024 年起不再公开强平明细，所以这里用持仓量的骤降做代理：
    **一串仓位被强制平掉，持仓量一定会掉**，而且掉得比正常平仓快得多。
    返回的是布尔序列，True 表示这一根是事件发生的那一根（事件连成一片时只标第一根）。
    """
    drop = open_interest / open_interest.rolling(window).max() - 1
    hit = (drop <= -threshold).fillna(False)
    return (hit & ~hit.shift(1, fill_value=False)).rename("去杠杆")
