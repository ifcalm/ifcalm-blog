"""talab.stats：收益率、波动率与分布。第 5 篇。"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Callable

import numpy as np
import pandas as pd

NORMAL = NormalDist()

# 一年有多少根日线：美股一年约 252 个交易日，加密市场全年无休
PERIODS_PER_YEAR = {"us_stock": 252, "crypto": 365}


# ---------------------------------------------------------------------------
# 一、收益率
# ---------------------------------------------------------------------------

def simple_returns(close: pd.Series) -> pd.Series:
    """简单收益率：今天收盘 ÷ 昨天收盘 − 1。第一天没有「昨天」，去掉。"""
    return close.pct_change().dropna()


def log_returns(close: pd.Series) -> pd.Series:
    """对数收益率：ln(今天收盘 ÷ 昨天收盘)。"""
    return np.log(close).diff().dropna()


def total_return(returns: pd.Series) -> float:
    """把一串简单收益率复利连乘，得到整段时间的总收益率。"""
    return float((1 + returns).prod() - 1)


def annualized_return(returns: pd.Series, periods_per_year: int) -> float:
    """复合年化收益率（CAGR）：假设每年都按同一个比例增长，这个比例是多少。"""
    growth = 1 + total_return(returns)
    return growth ** (periods_per_year / len(returns)) - 1


# ---------------------------------------------------------------------------
# 二、波动率
# ---------------------------------------------------------------------------

def annualize_vol(vol: float | pd.Series, periods_per_year: int) -> float | pd.Series:
    """把单根 K 线的波动率换算成年化波动率：乘以一年 K 线根数的平方根。"""
    return vol * math.sqrt(periods_per_year)


def realized_vol(returns: pd.Series, window: int, periods_per_year: int) -> pd.Series:
    """滚动的已实现波动率（年化）：每一天用截至当天（含当天）的最近 window 天计算。"""
    return annualize_vol(returns.rolling(window).std(), periods_per_year)


def variance_ratio(log_rets: pd.Series, k: int) -> float:
    """方差比：k 天收益率的方差 ÷ (k × 1 天收益率的方差)。

    每天的收益率互相独立时，方差比等于 1，「波动率按时间的平方根放大」成立；
    大于 1 说明涨跌倾向于延续，小于 1 说明涨跌倾向于反转。
    k 天收益率用相邻 k 天对数收益率之和（重叠窗口）计算。
    """
    k_day = log_rets.rolling(k).sum().dropna()
    return float(k_day.var() / (k * log_rets.var()))


def standardize(returns: pd.Series, window: int) -> pd.Series:
    """把每天的收益率除以「前 window 天」的波动率，得到当天是几倍的近期波动。

    用 shift(1) 保证只用到当天之前的数据，当天的收益率不参与计算自己的标尺。
    """
    trailing = returns.rolling(window).std().shift(1)
    return (returns / trailing).dropna()


# ---------------------------------------------------------------------------
# 三、分布与尾部
# ---------------------------------------------------------------------------

def describe(returns: pd.Series, periods_per_year: int) -> pd.Series:
    """一个标的收益率的统计档案。"""
    return pd.Series({
        "天数": len(returns),
        "日均收益率": returns.mean(),
        "日波动率": returns.std(),
        "年化波动率": annualize_vol(returns.std(), periods_per_year),
        "复合年化收益率": annualized_return(returns, periods_per_year),
        "偏度": returns.skew(),
        "超额峰度": returns.kurt(),
        "最大单日涨幅": returns.max(),
        "最大单日跌幅": returns.min(),
    })


def tail_table(returns: pd.Series, ks=(1, 2, 3, 4, 5, 6)) -> pd.DataFrame:
    """距离均值超过 k 个标准差的天数：实际有多少天，正态分布下预期有多少天。"""
    z = (returns - returns.mean()) / returns.std()
    rows = []
    for k in ks:
        actual = int((z.abs() > k).sum())
        expected = len(z) * 2 * NORMAL.cdf(-k)
        rows.append({"k": k, "实际天数": actual, "正态预期天数": expected,
                     "实际 ÷ 预期": actual / expected})
    return pd.DataFrame(rows).set_index("k")


def threshold_table(returns: pd.Series, thresholds, periods_per_year: int) -> pd.DataFrame:
    """单日跌幅超过某个阈值的日子：实际每年几次，正态分布认为几年才有一次。

    正态分布的均值和标准差用同一段样本估计。
    """
    years = len(returns) / periods_per_year
    mean, std = returns.mean(), returns.std()
    rows = []
    for t in thresholds:
        actual = int((returns <= t).sum())
        p = NORMAL.cdf((t - mean) / std)                  # 正态分布下，某一天跌幅超过 t 的概率
        rows.append({"阈值": t, "实际次数": actual, "实际每年次数": actual / years,
                     "正态下几年一次": 1 / p / periods_per_year})
    return pd.DataFrame(rows).set_index("阈值")


def tail_loss(returns: pd.Series, level: float = 0.01) -> tuple[float, float]:
    """最差 level 比例的日子：返回（分界线，这些日子的平均收益率）。

    分界线就是历史 VaR，平均值就是历史 ES（expected shortfall）。
    """
    cutoff = float(returns.quantile(level))
    return cutoff, float(returns[returns <= cutoff].mean())


def normal_tail_loss(returns: pd.Series, level: float = 0.01) -> tuple[float, float]:
    """假设收益率服从正态分布时的分界线和尾部平均值，用来和 tail_loss 对比。"""
    mean, std = returns.mean(), returns.std()
    z = NORMAL.inv_cdf(level)
    return mean + std * z, mean - std * NORMAL.pdf(z) / level


# ---------------------------------------------------------------------------
# 四、自相关
# ---------------------------------------------------------------------------

def autocorr(x: pd.Series, lags=(1, 2, 3, 4, 5)) -> pd.Series:
    """自相关系数：ρ_k = Σ (x_t − x̄)(x_{t−k} − x̄) ÷ Σ (x_t − x̄)²。"""
    d = x.to_numpy(dtype=float) - x.mean()
    denom = (d ** 2).sum()
    return pd.Series({k: (d[k:] * d[:-k]).sum() / denom for k in lags}, name="自相关")


def autocorr_band(n: int) -> float:
    """没有自相关时，样本自相关系数大约 95% 落在 ±1.96/√n 之内。"""
    return 1.96 / math.sqrt(n)


def shuffle_test(x: pd.Series, stat: Callable[[pd.Series], float],
                 n: int = 1000, seed: int = 0) -> dict[str, float]:
    """打乱检验：把日子的顺序随机打乱 n 次，看统计量在「顺序无关」时通常落在什么范围。

    打乱保留了每一天的收益率本身（包括肥尾），只破坏了先后顺序。
    返回实际值、打乱后 95% 的范围，以及打乱后的绝对值不小于实际值的比例。
    """
    rng = np.random.default_rng(seed)
    observed = stat(x)
    values = x.to_numpy(dtype=float).copy()
    sims = np.empty(n)
    for i in range(n):
        rng.shuffle(values)
        sims[i] = stat(pd.Series(values))
    lo, hi = np.percentile(sims, [2.5, 97.5])
    return {"实际值": observed, "打乱后 2.5% 分位": lo, "打乱后 97.5% 分位": hi,
            "比例": float((np.abs(sims) >= abs(observed)).mean())}
