"""talab.stats 的测试。"""
import math

import numpy as np
import pandas as pd
import pytest

from talab import stats as S


def prices(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="1D", tz="UTC")
    return pd.Series(values, index=idx, dtype=float)


def test_simple_and_log_returns_by_hand():
    close = prices([100, 110, 99])
    assert S.simple_returns(close).tolist() == pytest.approx([0.10, -0.10])
    assert S.log_returns(close).tolist() == pytest.approx([math.log(1.1), math.log(0.9)])


def test_log_returns_add_up_but_simple_returns_do_not():
    close = prices([100, 150, 75])                                # 先涨 50%，再跌 50%
    assert S.simple_returns(close).sum() == pytest.approx(0.0)    # 简单收益率相加是 0
    assert S.total_return(S.simple_returns(close)) == pytest.approx(-0.25)   # 实际亏了 25%
    assert S.log_returns(close).sum() == pytest.approx(math.log(75 / 100))   # 对数收益率相加正好是总收益


def test_annualized_return_of_constant_growth():
    # 每天涨 0.1%，252 天复利下来的年化收益就是 1.001 ** 252 − 1
    r = prices([0.001] * 504)
    assert S.annualized_return(r, 252) == pytest.approx(1.001 ** 252 - 1)


def test_annualize_vol_uses_square_root_of_time():
    assert S.annualize_vol(0.01, 252) == pytest.approx(0.01 * math.sqrt(252))
    assert S.annualize_vol(0.02, 365) == pytest.approx(0.02 * math.sqrt(365))


def test_variance_ratio_extremes():
    alternating = prices([0.01, -0.01] * 50)                       # 涨跌严格交替：两天加起来总是 0
    assert S.variance_ratio(alternating, 2) == pytest.approx(0.0)
    rng = np.random.default_rng(1)
    independent = pd.Series(rng.normal(0, 0.01, 200_000))          # 互相独立的收益率
    assert S.variance_ratio(independent, 5) == pytest.approx(1.0, abs=0.02)


def test_standardize_only_uses_past_days():
    r = prices([0.01, -0.01, 0.01, -0.01, 0.10])
    z = S.standardize(r, window=4)
    trailing = pd.Series([0.01, -0.01, 0.01, -0.01]).std()        # 只用前 4 天
    assert len(z) == 1
    assert z.iloc[0] == pytest.approx(0.10 / trailing)


def test_autocorr_by_hand():
    x = pd.Series([1.0, -1.0] * 5)                                  # 均值 0，严格交替
    # 分子是 9 个相邻乘积（每个 −1），分母是 10 个平方（每个 1）
    assert S.autocorr(x, lags=[1]).loc[1] == pytest.approx(-0.9)
    assert S.autocorr(x, lags=[2]).loc[2] == pytest.approx(0.8)


def test_autocorr_band():
    assert S.autocorr_band(2500) == pytest.approx(1.96 / 50)


def test_tail_table_expected_counts_match_normal_distribution():
    r = pd.Series(np.random.default_rng(2).normal(0, 1, 1000))
    table = S.tail_table(r, ks=[3])
    assert table.loc[3, "正态预期天数"] == pytest.approx(1000 * 0.0026998, rel=1e-3)


def test_threshold_table_counts_and_normal_period():
    r = pd.Series([-0.20, 0.0, 0.0, 0.0] * 91 + [0.0])             # 365 天里有 91 天跌 20%
    table = S.threshold_table(r, [-0.15], periods_per_year=365)
    assert table.loc[-0.15, "实际次数"] == 91
    assert table.loc[-0.15, "实际每年次数"] == pytest.approx(91)
    p = S.NORMAL.cdf((-0.15 - r.mean()) / r.std())
    assert table.loc[-0.15, "正态下几年一次"] == pytest.approx(1 / p / 365)


def test_tail_loss_by_hand():
    r = pd.Series([-0.05, -0.03, -0.01] + [0.01] * 97)             # 100 天
    cutoff, avg = S.tail_loss(r, level=0.01)
    assert cutoff == pytest.approx(-0.0302)                         # 第 1% 分位，在 −5% 和 −3% 之间插值
    assert avg == pytest.approx(-0.05)                              # 只有 −5% 那一天在分界线之下


def test_shuffle_test_detects_strong_order():
    x = pd.Series([1.0, -1.0] * 200)
    result = S.shuffle_test(x, lambda s: S.autocorr(s, [1]).loc[1], n=200, seed=0)
    assert result["实际值"] < result["打乱后 2.5% 分位"]
    assert result["比例"] == 0.0
