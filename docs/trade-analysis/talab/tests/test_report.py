"""talab.report 的测试（第 29 篇）。"""
import math

import numpy as np
import pandas as pd
import pytest

from talab import report as RP


def days(n: int, tz=None) -> pd.DatetimeIndex:
    return pd.date_range("2020-01-01", periods=n, freq="D", tz=tz)


def test_to_curve_prepends_one_so_the_first_bar_is_not_lost():
    """少补那个 1，整段收益就少算第一根——这里把两种写法的差摆出来。"""
    r = pd.Series([0.5, 0.1, -0.1], index=days(3))
    curve = RP.to_curve(r)
    assert len(curve) == 4
    assert curve.iloc[0] == 1.0
    assert curve.iloc[-1] == pytest.approx(1.5 * 1.1 * 0.9)
    assert curve.index[0] == r.index[0] - pd.Timedelta(days=1)
    naive = (1 + r).cumprod()                       # 漏掉第一根的写法
    assert float(naive.iloc[-1] / naive.iloc[0]) == pytest.approx(1.1 * 0.9)


def test_annual_return_uses_bar_count_not_calendar():
    """一年 252 根、整段涨一倍，年化就是 100%；跑两年同样涨一倍，年化是 √2 − 1。"""
    one = pd.Series(np.linspace(1, 2, 253), index=days(253))
    assert RP.annual_return(one, 252) == pytest.approx(1.0)
    two = pd.Series(np.linspace(1, 2, 505), index=days(505))
    assert RP.annual_return(two, 252) == pytest.approx(math.sqrt(2) - 1)
    with pytest.raises(ValueError):
        RP.annual_return(pd.Series([1.0], index=days(1)), 252)


def test_annual_vol_scales_with_square_root_of_frequency():
    r = pd.Series([0.01, -0.01] * 50, index=days(100))
    assert RP.annual_vol(r, 252) == pytest.approx(float(r.std()) * math.sqrt(252))
    assert RP.annual_vol(r, 365) / RP.annual_vol(r, 252) == pytest.approx(math.sqrt(365 / 252))


def test_excess_aligns_a_rate_series_across_time_zones_and_weekends():
    """加密 K 线带 UTC 时区、天天都有；利率序列不带时区、只有工作日。

    直接 reindex 会安静地全变成 NaN，这个测试就是为了钉住那个坑。
    """
    r = pd.Series(0.01, index=days(10, tz="UTC"))
    rate = pd.Series([0.05, 0.05], index=pd.to_datetime(["2019-12-31", "2020-01-06"]))
    out = RP.excess(r, 365, rate)
    assert out.notna().all()
    assert out.index.equals(r.index)
    assert out.iloc[0] == pytest.approx(0.01 - (1.05 ** (1 / 365) - 1))
    assert RP.excess(r, 365, 0.0).equals(r)          # rf=0 时原样返回


def test_sharpe_is_mean_over_std_times_root_frequency():
    r = pd.Series([0.02, -0.01, 0.03, 0.00, 0.01], index=days(5))
    assert RP.sharpe(r, 252) == pytest.approx(float(r.mean() / r.std()) * math.sqrt(252))
    rf_only = RP.sharpe(r, 252, 0.10)
    assert rf_only < RP.sharpe(r, 252)               # 扣掉无风险利率只会更低


def test_sharpe_of_a_curve_that_never_moves_is_not_a_number():
    """一年到头空仓：收益率恒等于 0，公式会给出一个绝对值巨大的负数，该给的是 NaN。"""
    flat = pd.Series(0.0, index=days(300, tz="UTC"))
    rate = pd.Series(0.05, index=days(300))
    assert math.isnan(RP.sharpe(flat, 365, rate))
    assert math.isnan(RP.sharpe(flat, 365))


def test_sortino_only_counts_downside_and_divides_by_all_bars():
    r = pd.Series([0.02, -0.01, 0.02, -0.01], index=days(4))
    downside = math.sqrt(((0.01 ** 2) * 2) / 4)      # 分母是 4 根，不是 2 根亏损
    assert RP.sortino(r, 252) == pytest.approx(float(r.mean()) / downside * math.sqrt(252))
    assert RP.sortino(pd.Series([0.01, 0.02], index=days(2)), 252) == np.inf


def test_max_drawdown_and_calmar():
    curve = pd.Series([1.0, 2.0, 1.0, 1.5], index=days(4))
    assert RP.max_drawdown(curve) == pytest.approx(-0.5)
    assert RP.calmar(curve, 252) == pytest.approx(RP.annual_return(curve, 252) / 0.5)
    rising = pd.Series([1.0, 1.1, 1.2], index=days(3))
    assert RP.calmar(rising, 252) == np.inf          # 从没回撤过


def test_metrics_reports_the_longest_underwater_stretch_in_bars():
    curve = pd.Series([1.0, 0.9, 0.8, 1.1, 1.0, 1.2], index=days(6))
    m = RP.metrics(curve, 252)
    assert m["在水下的比例"] == pytest.approx(3 / 6)        # 第 2、3、5 根在水下
    assert m["最长水下根数"] == 2                            # 最长的一段是第 2、3 根
    assert m["最大回撤"] == pytest.approx(-0.2)
    assert m["累计收益"] == pytest.approx(0.2)


def test_sharpe_se_is_about_one_over_root_years():
    """夏普 1.0 跑一年，标准误就是 1.0——所以一年的数据什么都证明不了。"""
    assert RP.sharpe_se(1.0, 252, 252) == pytest.approx(1.0, rel=0.01)
    assert RP.sharpe_se(1.0, 252 * 4, 252) == pytest.approx(0.5, rel=0.01)
    assert RP.sharpe_se(1.0, 252 * 4, 252) < RP.sharpe_se(1.0, 252, 252)
    with pytest.raises(ValueError):
        RP.sharpe_se(1.0, 0, 252)


def test_years_needed_is_t_over_sharpe_squared():
    assert RP.years_needed(2.0, 2.0, 252) == pytest.approx(1.0, rel=0.01)
    assert RP.years_needed(0.5, 2.0, 252) == pytest.approx(16.0, rel=0.02)
    assert RP.years_needed(-0.3) == np.inf
    table = RP.significance_table(periods_per_year=252)
    assert table["要跑多少年"].is_monotonic_decreasing


def test_bootstrap_is_reproducible_and_blocks_keep_the_length():
    r = pd.Series(np.random.default_rng(0).normal(0.001, 0.02, 500), index=days(500))
    stat = lambda x: RP.sharpe(x, 252)
    a = RP.bootstrap(r, stat, n=200, block=1, seed=7)
    b = RP.bootstrap(r, stat, n=200, block=1, seed=7)
    assert a.equals(b)                                      # 同一个 seed 必须给同一个答案
    assert a["90% 下界"] < a["实际值"] < a["90% 上界"]
    block = RP.bootstrap(r, lambda x: float(len(x)), n=5, block=37, seed=1)
    assert block["实际值"] == 500 and block["自助法中位数"] == 500
    with pytest.raises(ValueError):
        RP.bootstrap(r, stat, block=0)
    with pytest.raises(ValueError):
        RP.bootstrap(r, stat, block=501)


def test_trade_metrics_t_value_and_longest_losing_streak():
    r = pd.Series([0.2, -0.1, -0.1, -0.05, 0.3, -0.02])
    out = RP.trade_metrics(r)
    assert out["笔数"] == 6
    assert out["t 值"] == pytest.approx(float(r.mean()) / (float(r.std(ddof=1)) / math.sqrt(6)))
    assert out["最长连亏笔数"] == 3                          # 第 2、3、4 笔
    assert out["连亏最多亏掉"] == pytest.approx(-0.25)
    with pytest.raises(ValueError):
        RP.trade_metrics([0.1])


def test_more_trades_shrink_the_interval_at_the_same_average():
    """同一串交易重复十遍：平均每笔一点没变，区间宽度缩到 2/7。

    直觉上应该缩到 1/√10 = 0.316，实际是 2/7 = 0.286：差在 ddof=1 的自由度修正上
    （5 笔时平方和除以 4，50 笔时除以 49）。笔数少的时候这个修正一点都不小。
    """
    few = pd.Series([0.2, -0.1, 0.15, -0.08, 0.05])
    many = pd.Series(list(few) * 10)
    a, b = RP.trade_metrics(few), RP.trade_metrics(many)
    assert b["平均每笔"] == pytest.approx(a["平均每笔"])
    width = lambda x: x["95% 上界"] - x["95% 下界"]
    assert width(b) / width(a) == pytest.approx(math.sqrt(20 / 245))
    assert width(b) / width(a) == pytest.approx(2 / 7)


def test_by_year_and_compare_and_page_line_up():
    r = pd.Series(np.random.default_rng(29).normal(0.001, 0.02, 800), index=days(800))
    curve = RP.to_curve(r)
    years = RP.by_year(curve, 365)
    assert list(years.index) == [2020, 2021, 2022]
    assert years["根数"].sum() == 800
    side = RP.compare({"甲": curve, "乙": curve * 2}, 365)
    assert list(side.columns) == ["甲", "乙"]
    assert side.loc["夏普比率", "甲"] == pytest.approx(side.loc["夏普比率", "乙"])   # 放大不改信噪比
    text = RP.page(curve, 365, n_boot=50, block=20, name="测试")
    assert "【一】指标" in text and "【三】分年" in text
    assert "【四】交易" not in text                            # 没给交易表就不印第四段
