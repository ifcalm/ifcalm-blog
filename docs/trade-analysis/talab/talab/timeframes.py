"""talab.timeframes：多周期对齐。第 7 篇。"""
from __future__ import annotations

import pandas as pd


def align_higher(lower_index: pd.DatetimeIndex, lower_period: str,
                 higher: pd.DataFrame, higher_period: str) -> pd.DataFrame:
    """把大周期的数据对齐到小周期的每一根 K 线上，只使用当时已经收盘的大周期 K 线。

    lower_index:   小周期 K 线的时间戳（开始时间）
    lower_period:  小周期的长度，比如 "4h"、"1D"
    higher:        大周期的数据，索引是每根大 K 线的开始时间
    higher_period: 大周期的长度，比如 "1D"、"7D"

    规则：小周期 K 线在它收盘的那一刻做决定；这一刻之前（含这一刻）已经收盘的大周期 K 线才能使用。
    大 K 线的收盘时间 = 开始时间 + higher_period；小 K 线的收盘时间 = 开始时间 + lower_period。
    返回的表和 lower_index 一一对应；还没有任何大 K 线收盘时为 NaN。
    """
    available = higher.copy()
    available.index = higher.index + pd.Timedelta(higher_period)          # 每根大 K 线从收盘那一刻起才可用
    decide_at = lower_index + pd.Timedelta(lower_period)                   # 每根小 K 线收盘、做决定的时刻
    out = available.reindex(decide_at, method="ffill")                     # 取这一刻之前最近一根已收盘的大 K 线
    out.index = lower_index
    return out


def developing(lower: pd.DataFrame, rule: str) -> pd.DataFrame:
    """正在形成的大周期 K 线：在每一根小 K 线收盘时，这根大 K 线「到目前为止」的样子。

    开盘 = 这个大周期第一根小 K 线的开盘价（固定不变）
    最高 / 最低 = 到目前为止的最高 / 最低
    收盘 = 当前这根小 K 线的收盘价（还会继续变）
    成交量 = 到目前为止的累计
    每个大周期最后一根小 K 线上的值，就等于这根大 K 线收盘后的最终值。
    rule 和 resample 的写法一样，比如 "1D"、"W-MON"（周一开始的一周）。
    """
    groups = pd.Grouper(freq=rule, label="left", closed="left")
    return pd.DataFrame({
        "open": lower["open"].groupby(groups).transform("first"),
        "high": lower["high"].groupby(groups).cummax(),
        "low": lower["low"].groupby(groups).cummin(),
        "close": lower["close"],
        "volume": lower["volume"].groupby(groups).cumsum(),
    }, index=lower.index)
