"""talab.derivs 的测试（第 25 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import derivs as V


def minutes(values, start="2021-04-13 16:01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="min", tz="UTC"),
                     dtype=float)


def test_align_takes_the_last_value_inside_each_bar():
    fine = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                     index=pd.date_range("2021-04-13", periods=6, freq="10min", tz="UTC"))
    bars = pd.date_range("2021-04-13", periods=2, freq="30min", tz="UTC")
    assert list(V.align(fine, bars)) == [3.0, 6.0]                 # 每根 K 线区间内的最后一个
    assert list(V.align(fine, bars, how="mean")) == [2.0, 5.0]
    with pytest.raises(ValueError):
        V.align(fine, bars, how="随便")


def test_align_does_not_borrow_from_the_future():
    """第二根 K 线的值只能用第二根区间里的数据，不能把第三根的第一条算进来。"""
    fine = pd.Series([1.0, 9.0], index=pd.to_datetime(["2021-04-13 00:29", "2021-04-13 00:30"], utc=True))
    bars = pd.date_range("2021-04-13", periods=2, freq="30min", tz="UTC")
    assert list(V.align(fine, bars)) == [1.0, 9.0]


def test_funding_equals_the_interest_rate_inside_the_clamp():
    """平均溢价落在 −0.04% 到 +0.06% 之间时，费率精确等于 0.01%。"""
    for level in [-0.0004, 0.0, 0.0003, 0.0006]:
        rate = V.funding_from_premium(minutes([level] * 480))
        assert rate.iloc[0] == pytest.approx(V.INTEREST_RATE)


def test_funding_follows_the_premium_outside_the_clamp():
    high = V.funding_from_premium(minutes([0.0020] * 480))
    low = V.funding_from_premium(minutes([-0.0020] * 480))
    assert high.iloc[0] == pytest.approx(0.0020 - V.CLAMP)          # 溢价高于 0.06%：减掉 0.05%
    assert low.iloc[0] == pytest.approx(-0.0020 + V.CLAMP)          # 溢价低于 −0.04%：加上 0.05%


def test_funding_is_capped():
    assert V.funding_from_premium(minutes([0.05] * 480)).iloc[0] == pytest.approx(V.CAP)
    assert V.funding_from_premium(minutes([-0.05] * 480)).iloc[0] == pytest.approx(-V.CAP)


def test_funding_weights_the_later_minutes_more():
    """前一半 0、后一半 0.2% 的溢价，时间加权的结果要比简单平均（0.1%）更靠近后一半。"""
    premium = minutes([0.0] * 240 + [0.002] * 240)
    weighted = V.funding_from_premium(premium).iloc[0] + V.CLAMP    # 反解出加权平均
    assert weighted > 0.001
    assert weighted == pytest.approx(0.002 * (sum(range(241, 481)) / sum(range(1, 481))))


def test_annualize():
    funding = pd.Series([0.0001, -0.0003])
    assert V.annualize(funding).iloc[0] == pytest.approx(0.0001 * 1095)
    assert V.annualize(funding, hours=4).iloc[1] == pytest.approx(-0.0003 * 2190)


def test_basis():
    index = pd.date_range("2021-04-13", periods=3, freq="D", tz="UTC")
    perp = pd.Series([101.0, 100.0, 99.0], index=index)
    spot = pd.Series([100.0, 100.0, 100.0], index=index)
    assert list(V.basis(perp, spot).round(4)) == [0.01, 0.0, -0.01]


def test_regimes_covers_the_four_boxes():
    index = pd.date_range("2021-04-13", periods=5, freq="D", tz="UTC")
    close = pd.Series([100.0, 101.0, 102.0, 101.0, 100.0], index=index)
    oi = pd.Series([10.0, 11.0, 10.0, 11.0, 10.0], index=index)
    labels = V.regimes(close, oi)
    assert pd.isna(labels.iloc[0])                                  # 第一根没有前一根
    assert labels.iloc[1] == "价涨 + 仓涨：新多进场"
    assert labels.iloc[2] == "价涨 + 仓跌：空头平仓"
    assert labels.iloc[3] == "价跌 + 仓涨：新空进场"
    assert labels.iloc[4] == "价跌 + 仓跌：多头平仓"


def test_deleveraging_marks_only_the_first_bar_of_an_episode():
    index = pd.date_range("2021-04-13", periods=8, freq="h", tz="UTC")
    oi = pd.Series([100.0, 100.0, 100.0, 94.0, 93.0, 92.0, 100.0, 100.0], index=index)
    events = V.deleveraging(oi, window=3, threshold=0.05)
    assert list(events) == [False, False, False, True, False, False, False, False]
    assert V.deleveraging(oi, window=3, threshold=0.20).sum() == 0   # 阈值调高就没有事件了
