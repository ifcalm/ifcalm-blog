"""talab.bars 的测试。"""
import numpy as np
import pandas as pd
import pytest

from talab import bars as B


def minutes(rows, start="2024-01-01 00:00"):
    idx = pd.date_range(start, periods=len(rows), freq="1min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx, dtype=float)


def test_resample_ohlcv_by_hand():
    m = minutes([
        [10, 12, 9, 11, 1],       # 00:00
        [11, 15, 11, 14, 2],      # 00:01  最高价 15
        [14, 14, 8, 9, 3],        # 00:02  最低价 8
        [9, 10, 9, 10, 4],        # 00:03
        [10, 11, 10, 11, 5],      # 00:04  收盘 11
        [11, 13, 11, 12, 6],      # 00:05  属于下一根 5 分钟 K 线
    ])
    out = B.resample_ohlcv(m, "5min")
    assert len(out) == 2
    assert out.iloc[0].tolist() == [10, 15, 8, 11, 15]
    assert out.index[1] == pd.Timestamp("2024-01-01 00:05", tz="UTC")   # 时间戳是开始时间


def test_resample_traded_only_ignores_placeholder_bars():
    m = minutes([
        [100, 100, 100, 100, 0],  # 没有成交的占位 K 线，价格沿用上一分钟的收盘价
        [98, 101, 97, 99, 2],     # 第一笔真实成交在这里
    ])
    assert B.resample_ohlcv(m, "1D").iloc[0]["open"] == 100
    assert B.resample_ohlcv(m, "1D", traded_only=True).iloc[0]["open"] == 98


def test_anatomy_by_hand():
    df = minutes([[100, 110, 95, 104, 1], [50, 50, 50, 50, 1]])
    a = B.anatomy(df)
    first = a.iloc[0]
    assert first["body"] == 4
    assert first["upper_shadow"] == 6            # 110 − 104
    assert first["lower_shadow"] == 5            # 100 − 95
    assert first["range"] == 15
    assert first["body_ratio"] == pytest.approx(4 / 15)
    assert first["clv"] == pytest.approx(9 / 15)
    assert np.isnan(a.iloc[1]["clv"])            # 四价相同，全长为 0


def test_intraday_extremes_order():
    day1 = [[10, 10, 9, 9, 1], [9, 9, 5, 6, 1], [6, 12, 6, 12, 1]]        # 先低后高
    day2 = [[10, 20, 10, 18, 1], [18, 18, 3, 4, 1], [4, 6, 4, 5, 1]]      # 先高后低
    day3 = [[10, 30, 1, 10, 1], [10, 11, 9, 10, 1], [10, 11, 9, 10, 1]]   # 高低在同一分钟
    m = pd.concat([minutes(day1, "2024-01-01"), minutes(day2, "2024-01-02"), minutes(day3, "2024-01-03")])
    ex = B.intraday_extremes(m)
    assert ex["high_first"].iloc[0] == False
    assert ex["high_first"].iloc[1] == True
    assert pd.isna(ex["high_first"].iloc[2])
    assert ex["time_of_low"].iloc[0] == pd.Timestamp("2024-01-01 00:01", tz="UTC")


def test_first_touch_all_outcomes():
    up = [[100, 101, 99, 100, 1], [100, 104, 100, 102, 1], [102, 102, 96, 97, 1]]    # 先 +3%，后 −3%
    down = [[100, 100, 96, 97, 1], [97, 104, 97, 103, 1], [103, 103, 103, 103, 1]]  # 先 −3%，后 +3%
    none = [[100, 102, 98, 100, 1]] * 3
    both = [[100, 104, 96, 100, 1]] * 3                                             # 同一分钟两边都碰到
    m = pd.concat([minutes(up, "2024-01-01"), minutes(down, "2024-01-02"),
                   minutes(none, "2024-01-03"), minutes(both, "2024-01-04")])
    assert B.first_touch(m, 0.03, 0.03).tolist() == ["up", "down", "none", "same_bar"]


def test_heikin_ashi_by_hand():
    df = minutes([[10, 14, 8, 12, 1], [12, 16, 11, 15, 1], [15, 15, 9, 10, 1]])
    ha = B.heikin_ashi(df)
    # 第一根：HA 开盘 = (10 + 12) ÷ 2 = 11，HA 收盘 = (10 + 14 + 8 + 12) ÷ 4 = 11
    assert ha.iloc[0].tolist() == [11, 14, 8, 11]
    # 第二根：HA 开盘 = (11 + 11) ÷ 2 = 11，HA 收盘 = (12 + 16 + 11 + 15) ÷ 4 = 13.5
    assert ha.iloc[1].tolist() == [11, 16, 11, 13.5]
    # 第三根：HA 开盘 = (11 + 13.5) ÷ 2 = 12.25，HA 收盘 = (15 + 15 + 9 + 10) ÷ 4 = 12.25
    assert ha.iloc[2].tolist() == [12.25, 15, 9, 12.25]


def test_heikin_ashi_range_always_covers_real_range():
    rng = np.random.default_rng(3)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 500)))
    open_ = np.r_[100, close[:-1]]
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.01, 500))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.01, 500))
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})
    ha = B.heikin_ashi(df)
    assert (ha["high"] >= df["high"]).all() and (ha["low"] <= df["low"]).all()


def test_renko_by_hand():
    close = pd.Series([100, 105, 111, 121, 115, 99, 100], dtype=float)
    bricks = B.renko(close, 10)
    # 111 → 画 100～110；121 → 画 110～120；115 不够；99 跌破 110 − 10 = 100，反向画 110～100
    assert bricks[["open", "close", "direction"]].values.tolist() == [[100, 110, 1], [110, 120, 1], [110, 100, -1]]
    assert bricks["formed_at"].tolist() == [2, 3, 5]


def test_renko_needs_two_bricks_to_reverse():
    close = pd.Series([100, 110, 101, 100.5, 90], dtype=float)
    bricks = B.renko(close, 10)
    # 110 画出 100～110 的砖。跌到 101、100.5 都不反向：反向要跌到 110 − 2 × 10 = 90
    assert bricks["direction"].tolist() == [1, -1]
    assert bricks["formed_at"].tolist() == [1, 4]


def test_renko_log_bricks_are_equal_ratios():
    close = pd.Series([100, 122, 99], dtype=float)
    bricks = B.renko(close, 0.10, log=True)
    assert bricks["close"].iloc[0] == pytest.approx(110)
    assert bricks["close"].iloc[1] == pytest.approx(121)
    assert bricks["direction"].tolist() == [1, 1, -1]          # 跌到 99，低于 110 ÷ 1.1 = 100，反向一块
