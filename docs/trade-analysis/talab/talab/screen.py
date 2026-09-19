"""talab.screen：从几百上千个标的里挑出今天要交易的几个。第 19 篇。

这个模块处理的是「一堆标的」，所以主角是一张**宽表**（panel）：行是时间，列是标的，
还没上市或者已经下架的位置是 NaN。

约定和前面的模块一样：第 k 行的值只用到第 k 行及之前的数据。唯一的例外是 forward_return，
它看的是未来，名字里写明了，只用来做统计，不能用来做交易决定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 一、把很多标的拼成一张宽表
# ---------------------------------------------------------------------------

def panel(frames: dict[str, pd.DataFrame], field: str) -> pd.DataFrame:
    """把 {标的: OHLCV 表} 拼成一张宽表，取每张表的 field 这一列。列按标的名排序。"""
    return pd.DataFrame({name: df[field] for name, df in sorted(frames.items())})


def turnover(df: pd.DataFrame) -> pd.Series:
    """成交额（一天成交了多少钱）。有 quote_volume 就直接用，没有就用收盘价 × 成交量估。

    ⚠️ 成交量（多少股、多少个币）不能跨标的比：1 亿股 5 美元的股票和 100 万股 500 美元的股票，
    成交额一样。能不能进出一个仓位，看的是成交额。
    """
    return df["quote_volume"] if "quote_volume" in df else df["close"] * df["volume"]


def rolling_turnover(dollar_volume: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """最近 n 天成交额的中位数。用中位数而不是平均，是为了不被某一天的暴量带偏。"""
    return dollar_volume.rolling(n, min_periods=n).median()


# ---------------------------------------------------------------------------
# 二、横截面：同一天，标的之间比
# ---------------------------------------------------------------------------

def cross_rank(values: pd.DataFrame, ascending: bool = False, mask: pd.DataFrame | None = None,
               pct: bool = True) -> pd.DataFrame:
    """每一天，在当天有数据的标的之间排名。

    ascending=False（默认）表示值越大排得越前。pct=True 返回 0 到 1 的百分位（1 是最强的那一端），
    pct=False 返回 1、2、3……的名次。mask 给出当天参加排名的标的，没进名单的记 NaN。
    """
    if mask is not None:
        values = values.where(mask)
    if pct:                       # 百分位 = 当天有多少比例的标的排在它后面（含它自己）
        return values.rank(axis=1, ascending=not ascending, pct=True)
    return values.rank(axis=1, ascending=ascending)


def buckets(rank: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """把 0 到 1 的百分位分成 k 组：1 组是排名最靠后的，k 组是最靠前的。"""
    return np.ceil(rank * k)


def bucket_returns(bucket: pd.DataFrame, forward: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """每一天每一组的等权平均未来收益。行是时间，列是组号 1 到 k。"""
    rows = {g: forward.where(bucket == g).mean(axis=1) for g in range(1, k + 1)}
    return pd.DataFrame(rows).reindex(columns=range(1, k + 1))


# ---------------------------------------------------------------------------
# 三、相对强度
# ---------------------------------------------------------------------------

def relative_strength(close: pd.DataFrame | pd.Series, benchmark: pd.Series, base: float = 100.0):
    """相对强度线：标的价格 ÷ 基准价格，第一个能算的位置换算成 base（默认 100）。

    线在涨，说明这段时间跑赢基准，和标的自己是涨是跌无关。
    """
    ratio = close.div(benchmark, axis=0) if isinstance(close, pd.DataFrame) else close / benchmark
    return ratio / ratio.bfill().iloc[0] * base        # bfill().iloc[0] 是每一列第一个能算出来的值


def momentum(close: pd.DataFrame | pd.Series, lookback: int, skip: int = 0):
    """过去 lookback 根 K 线的涨幅；skip 表示跳过最近 skip 根（经典的「12 减 1」动量就是 skip=1 个月）。"""
    recent = close.shift(skip)
    return recent / close.shift(lookback) - 1


# ---------------------------------------------------------------------------
# 四、每日扫描
# ---------------------------------------------------------------------------

def passes(features: dict[str, pd.DataFrame], filters: dict[str, tuple]) -> pd.DataFrame:
    """通过全部硬门槛的位置。filters 是 {指标: (下限, 上限)}，用 None 表示这一端不限。"""
    ok = None
    for name, (low, high) in filters.items():
        values = features[name]
        good = values.notna()
        if low is not None:
            good &= values >= low
        if high is not None:
            good &= values <= high
        ok = good if ok is None else (ok & good)
    return ok


def scan(as_of, features: dict[str, pd.DataFrame], filters: dict[str, tuple],
         rank_by: str, top: int | None = 10) -> pd.DataFrame:
    """某一天的扫描结果：先过硬门槛，再按 rank_by 从大到小排，取前 top 个（top=None 表示全要）。

    返回一张表，每行一个标的，列是各个指标的值，外加 rank_by 在当天候选里的百分位（%）和名次。
    第 k 天的结果只用到第 k 天及之前的数据。
    """
    ok = passes(features, filters)
    table = pd.DataFrame({name: values.loc[as_of] for name, values in features.items()})
    table["名次"] = cross_rank(features[rank_by], mask=ok, pct=False).loc[as_of]
    table["百分位"] = cross_rank(features[rank_by], mask=ok).loc[as_of] * 100
    table = table[ok.loc[as_of]].sort_values("名次")
    return table if top is None else table.head(top)


# ---------------------------------------------------------------------------
# 五、看未来（只用来做统计）
# ---------------------------------------------------------------------------

def forward_return(close: pd.DataFrame, horizon: int, exit_on_delisting: bool = True) -> pd.DataFrame:
    """未来 horizon 根 K 线的收益率。

    ⚠️ exit_on_delisting=True（默认）时，中途下架的标的按下架前最后一个价格算收益；
    直接丢掉这些标的会让统计只剩下活到最后的赢家（幸存者偏差）。
    """
    future = (close.ffill() if exit_on_delisting else close).shift(-horizon)
    return (future / close - 1).where(close.notna())
