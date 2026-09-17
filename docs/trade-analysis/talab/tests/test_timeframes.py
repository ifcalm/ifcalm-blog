"""talab.timeframes 的测试。"""
import numpy as np
import pandas as pd
import pytest

from talab import bars as B
from talab import timeframes as T


def daily(n=21, start="2024-01-01"):
    """从 2024-01-01（周一）开始的日线，收盘价依次是 1, 2, 3, ……"""
    idx = pd.date_range(start, periods=n, freq="1D", tz="UTC")
    close = np.arange(1, n + 1, dtype=float)
    return pd.DataFrame({"open": close - 0.5, "high": close + 1, "low": close - 1,
                         "close": close, "volume": 1.0}, index=idx)


def test_weekly_bars_start_on_monday():
    weeks = B.resample_ohlcv(daily(), "W-MON")
    assert (weeks.index.dayofweek == 0).all()
    assert weeks["close"].tolist() == [7, 14, 21]        # 每周最后一天（周日）的收盘价


def test_align_higher_by_hand():
    d = daily()
    weeks = B.resample_ohlcv(d, "W-MON")
    aligned = T.align_higher(d.index, "1D", weeks, "7D")
    # 第一周（1 月 1 日到 7 日）在 1 月 8 日 0 点收盘。1 月 7 日（周日）收盘的时刻正好是 1 月 8 日 0 点，可以用
    assert aligned["close"].iloc[:6].isna().all()          # 1 月 1 日到 6 日：还没有任何一周收盘
    assert aligned.loc["2024-01-07", "close"] == 7
    assert aligned.loc["2024-01-10", "close"] == 7          # 周三只能看到上一周
    assert aligned.loc["2024-01-14", "close"] == 14


def test_align_higher_never_uses_the_future():
    d = daily(60)
    weeks = B.resample_ohlcv(d, "W-MON")
    before = T.align_higher(d.index, "1D", weeks, "7D")
    changed = weeks.copy()
    cutoff = pd.Timestamp("2024-01-29", tz="UTC")            # 修改从这一周开始的所有周线
    changed.loc[changed.index >= cutoff, "close"] = -999
    after = T.align_higher(d.index, "1D", changed, "7D")
    # 在修改的那一周收盘（2 月 5 日 0 点）之前做的决定，都不应该受影响
    safe = d.index + pd.Timedelta("1D") < cutoff + pd.Timedelta("7D")
    pd.testing.assert_series_equal(before.loc[safe, "close"], after.loc[safe, "close"])
    assert (after.loc[~safe, "close"] == -999).any()


def test_align_4h_to_daily():
    idx = pd.date_range("2024-01-01", periods=12, freq="4h", tz="UTC")     # 两天，每天 6 根
    four = pd.DataFrame({"close": np.arange(12.0)}, index=idx)
    days = pd.DataFrame({"close": [100.0, 200.0]},
                        index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"], tz="UTC"))
    aligned = T.align_higher(four.index, "4h", days, "1D")
    assert aligned["close"].iloc[:5].isna().all()            # 第一天 0 点到 20 点开始的前 5 根：日线还没收盘
    assert aligned["close"].iloc[5] == 100                   # 20:00 这根在 24:00 收盘，正好等于日线收盘时刻
    assert aligned["close"].iloc[11] == 200


def test_developing_ends_equal_to_finished_bar():
    d = daily(21)
    dev = T.developing(d, "W-MON")
    weeks = B.resample_ohlcv(d, "W-MON")
    last_of_week = dev.groupby(pd.Grouper(freq="W-MON", label="left", closed="left")).tail(1)
    assert last_of_week[["open", "high", "low", "close", "volume"]].values.tolist() == \
        weeks[["open", "high", "low", "close", "volume"]].values.tolist()
    # 周三（第 3 天）：开盘是周一的开盘价，最高是前三天的最高价，收盘是周三的收盘价
    wed = dev.loc["2024-01-03"]
    assert wed.tolist() == [0.5, 4.0, 0.0, 3.0, 3.0]


def test_developing_only_uses_the_past():
    d = daily(21)
    before = T.developing(d, "W-MON")
    changed = d.copy()
    changed.loc["2024-01-05":, ["high", "close"]] = 999          # 修改周五及以后
    after = T.developing(changed, "W-MON")
    pd.testing.assert_frame_equal(before.loc[:"2024-01-04"], after.loc[:"2024-01-04"])
