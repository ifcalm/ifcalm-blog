"""talab.indicators 的测试。"""
import numpy as np
import pandas as pd
import pytest

from talab import indicators as I, structure as X


def hourly(values, start="2024-01-01 22:00"):
    idx = pd.date_range(start, periods=len(values), freq="1h", tz="UTC")
    return pd.Series(values, index=idx, dtype=float)


def test_relative_volume_by_hand():
    volume = hourly([10, 20, 30, 60])
    rv = I.relative_volume(volume, n=3)
    assert rv.iloc[:3].isna().all()
    assert rv.iloc[3] == pytest.approx(60 / 20)          # 前 3 根的平均是 20


def test_relative_volume_same_hour():
    idx = pd.date_range("2024-01-01", periods=6, freq="12h", tz="UTC")   # 0 点、12 点交替
    volume = pd.Series([10, 100, 20, 200, 30, 600], index=idx, dtype=float)
    rv = I.relative_volume(volume, n=2, by=idx.hour)
    # 最后一根是 12 点：之前两个 12 点是 100 和 200，平均 150；如果不分组，会和 20、200 的平均比
    assert rv.iloc[5] == pytest.approx(600 / 150)
    assert rv.iloc[4] == pytest.approx(30 / 15)


def test_vwap_by_hand_and_resets_each_session():
    price = hourly([100, 102, 104, 50])                   # 22:00、23:00 是第一天，0:00 起是第二天
    volume = hourly([1, 3, 2, 5])
    session = price.index.floor("1D")
    v = I.vwap(price, volume, session)
    assert v.iloc[0] == 100
    assert v.iloc[1] == pytest.approx((100 * 1 + 102 * 3) / 4)       # 101.5
    assert v.iloc[2] == 104                                             # 新的一天，重新累计
    assert v.iloc[3] == pytest.approx((104 * 2 + 50 * 5) / 7)


def test_anchored_vwap_by_hand():
    price = hourly([100, 90, 110, 120])
    volume = hourly([5, 1, 1, 2])
    a = I.anchored_vwap(price, volume, price.index[1])
    assert np.isnan(a.iloc[0])
    assert a.iloc[1] == 90
    assert a.iloc[3] == pytest.approx((90 * 1 + 110 * 1 + 120 * 2) / 4)   # 110


def test_volume_profile_by_hand():
    price = pd.Series([100.2, 100.7, 101.9, 103.1, 100.4])
    volume = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    p = I.volume_profile(price, volume, 1.0)
    # 100.2、100.7、100.4 在 [100, 101)；101.9 在 [101, 102)；[102, 103) 没有成交；103.1 在 [103, 104)
    assert p.index.tolist() == [100.0, 101.0, 102.0, 103.0]
    assert p.tolist() == [8.0, 3.0, 0.0, 4.0]
    assert I.value_area(I.volume_profile(pd.Series([100.2]), pd.Series([1.0]), 1.0)) == {"poc": 100.5, "val": 100.0, "vah": 101.0}


def test_value_area_by_hand():
    profile = pd.Series([2.0, 5.0, 10.0, 6.0, 5.0, 1.0, 1.0], index=[10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
    profile.attrs["bin_size"] = 1.0
    va = I.value_area(profile, 0.7)
    # 总量 30，目标 21。从 POC（12~13，10）开始：上方 6 > 下方 5，并入 13（16）；
    # 上方 5 = 下方 5，并入上方 14（21），达到 21
    assert va == {"poc": 12.5, "val": 12.0, "vah": 15.0}
    # 目标改成 27：接着比较上方 15（1）和下方 11（5），并入 11（26）；再比较 15（1）和 10（2），并入 10（28）
    assert I.value_area(profile, 0.9) == {"poc": 12.5, "val": 10.0, "vah": 15.0}


# ---------------------------------------------------------------------------
# 第 12 篇：移动平均线
# ---------------------------------------------------------------------------

def test_moving_averages_by_hand():
    x = hourly([2, 4, 6, 8, 4])
    assert I.sma(x, 3).iloc[2:].tolist() == pytest.approx([4, 6, 6])
    # 权重 1、2、3：(2 + 8 + 18) / 6，(4 + 12 + 24) / 6，(6 + 16 + 12) / 6
    assert I.wma(x, 3).iloc[2:].tolist() == pytest.approx([28 / 6, 40 / 6, 34 / 6])
    # alpha = 2 / 4 = 0.5；第一个值是前 3 个的平均 4，然后 4 + 0.5 × (8 - 4) = 6，6 + 0.5 × (4 - 6) = 5
    assert I.ema(x, 3).iloc[2:].tolist() == pytest.approx([4, 6, 5])
    for f in (I.sma, I.wma, I.ema):
        assert f(x, 3).iloc[:2].isna().all()                        # 预热期是 NaN，不是 0


def test_average_lag_formulas():
    n = 20
    assert I.average_lag(np.ones(n)) == pytest.approx((n - 1) / 2)
    assert I.average_lag(np.arange(n, 0, -1)) == pytest.approx((n - 1) / 3)
    alpha = 2 / (n + 1)
    assert I.average_lag((1 - alpha) ** np.arange(2000)) == pytest.approx((n - 1) / 2)


def test_moving_averages_lag_exactly_on_a_ramp():
    ramp = hourly(np.arange(300))
    n = 30
    assert (ramp - I.sma(ramp, n)).dropna().to_numpy() == pytest.approx((n - 1) / 2)
    assert (ramp - I.wma(ramp, n)).dropna().to_numpy() == pytest.approx((n - 1) / 3)
    assert (ramp - I.ema(ramp, n)).dropna().to_numpy() == pytest.approx((n - 1) / 2)


def test_ema_skips_leading_nan_and_matches_wilder_smooth():
    x = hourly([np.nan, np.nan, 1, 2, 3, 4])
    assert I.ema(x, 2).iloc[3:].tolist() == pytest.approx([1.5, 2.5, 3.5])
    rng = np.random.default_rng(12)
    y = hourly(100 + np.cumsum(rng.normal(0, 1, 200)))
    pd.testing.assert_series_equal(I.ema(y, 14, alpha=1 / 14), X.wilder_smooth(y, 14))


def test_cross_and_bias_by_hand():
    a = hourly([1, 2, 3, 2, 2, 1])
    b = hourly([2, 2, 2, 2, 2, 2])
    # 2 → 3 是从「等于」变成「高于」，算上穿；3 → 2 → 1 是从「高于」到「等于」再到「低于」，在最后一根算下穿
    assert I.cross_above(a, b).tolist() == [False, False, True, False, False, False]
    assert I.cross_below(a, b).tolist() == [False, False, False, False, False, True]
    assert I.bias(hourly([110, 90]), hourly([100, 100])).tolist() == pytest.approx([0.10, -0.10])


def test_period_must_be_a_positive_integer():
    for bad in (0, -3, 2.5):
        with pytest.raises(ValueError):
            I.sma(hourly([1, 2, 3]), bad)


@pytest.mark.parametrize("name", ["sma", "ema", "wma"])
def test_moving_averages_never_use_the_future(name):
    rng = np.random.default_rng(3)
    x = hourly(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 400))))
    f = getattr(I, name)
    full = f(x, 50)
    for k in [60, 177, 399]:
        pd.testing.assert_series_equal(f(x.iloc[:k], 50), full.iloc[:k])


@pytest.mark.parametrize("name", ["SMA", "EMA", "WMA"])
@pytest.mark.parametrize("n", [1, 2, 9, 50, 200])
def test_moving_averages_match_talib(name, n):
    talib = pytest.importorskip("talib")
    rng = np.random.default_rng(n)
    x = hourly(50_000 * np.exp(np.cumsum(rng.normal(0, 0.03, 3000))))
    ours = getattr(I, name.lower())(x, n).to_numpy()
    theirs = getattr(talib, name)(x.to_numpy(), timeperiod=n)
    assert (np.isnan(ours) == np.isnan(theirs)).all()                 # 预热期一样长
    np.testing.assert_allclose(ours, theirs, rtol=1e-12, atol=1e-8)


# ---------------------------------------------------------------------------
# 第 13 篇：MACD 和背离
# ---------------------------------------------------------------------------

def test_macd_by_hand():
    x = hourly([1, 2, 4, 8, 6, 5, 7])
    m = I.macd(x, fast=2, slow=4, signal=2)
    # 慢 EMA（alpha 0.4）：第 3 根 (1+2+4+8)/4 = 3.75，然后 4.65、4.79、5.674
    # 快 EMA（alpha 2/3）从第 2 根开始：第 3 根 (4+8)/2 = 6，然后 6、5.3333、6.4444
    # MACD 线：2.25、1.35、0.5433、0.7704；信号线（alpha 2/3）第 4 根 (2.25+1.35)/2 = 1.8，然后 0.9622、0.8344
    assert m["macd"].iloc[:4].isna().all() and m["signal"].iloc[:4].isna().all()   # 三列同时从第 slow + signal - 2 根开始
    assert m["macd"].iloc[4:].tolist() == pytest.approx([1.35, 0.54333333, 0.77044444])
    assert m["signal"].iloc[4:].tolist() == pytest.approx([1.8, 0.96222222, 0.83437037])
    assert m["hist"].iloc[4] == pytest.approx(1.35 - 1.8)


def test_macd_on_a_ramp():
    ramp = hourly(np.arange(200))
    m = I.macd(ramp)
    assert m["macd"].first_valid_index() == ramp.index[33]
    # 两条 EMA 在直线上分别落后 (26-1)/2 = 12.5 和 (12-1)/2 = 5.5 根，差 7 根，每根涨 1：MACD 线恒等于 7，柱恒等于 0
    assert m["macd"].dropna().to_numpy() == pytest.approx(7)
    assert m["hist"].dropna().to_numpy() == pytest.approx(0, abs=1e-9)


def test_macd_rejects_bad_periods():
    with pytest.raises(ValueError):
        I.macd(hourly(np.arange(50)), fast=26, slow=12)


def test_macd_never_uses_the_future():
    rng = np.random.default_rng(13)
    x = hourly(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 300))))
    full = I.macd(x)
    for k in [40, 150, 299]:
        pd.testing.assert_frame_equal(I.macd(x.iloc[:k]), full.iloc[:k])


@pytest.mark.parametrize("fast,slow,signal", [(12, 26, 9), (5, 35, 5), (3, 10, 16)])
def test_macd_matches_talib(fast, slow, signal):
    talib = pytest.importorskip("talib")
    rng = np.random.default_rng(fast)
    x = hourly(50_000 * np.exp(np.cumsum(rng.normal(0, 0.03, 2000))))
    ours = I.macd(x, fast, slow, signal)
    for column, theirs in zip(["macd", "signal", "hist"], talib.MACD(x.to_numpy(), fast, slow, signal)):
        assert (ours[column].isna().to_numpy() == np.isnan(theirs)).all()
        np.testing.assert_allclose(ours[column].to_numpy(), theirs, rtol=1e-12, atol=1e-8)


def amplitude(y, period):
    """用最小二乘拟合正弦波的振幅（取整数个周期），不受采样点有没有落在波峰上的影响。"""
    t = np.arange(len(y))
    y = np.asarray(y, dtype=float) - np.mean(y)
    return np.hypot(2 * np.mean(y * np.sin(2 * np.pi * t / period)), 2 * np.mean(y * np.cos(2 * np.pi * t / period)))


def test_ema_response_matches_a_sine_wave():
    period = 40
    t = np.arange(4000)
    wave = hourly(100 + np.sin(2 * np.pi * t / period))
    steady = I.ema(wave, 20).iloc[2000:]                                   # 跳过开头，只看稳定之后的 50 个周期
    assert amplitude(steady, period) == pytest.approx(abs(I.ema_response(20, period)), rel=1e-6)
    assert abs(I.ema_response(20, 1e9)) == pytest.approx(1)              # 周期无限长（不变的价格）时原样通过
    line = I.macd(wave)["macd"].iloc[2000:]
    gain = abs(I.ema_response(12, period) - I.ema_response(26, period))
    assert amplitude(line, period) == pytest.approx(gain, rel=1e-6)


def make_swings(index, rows):
    return pd.DataFrame([(index[i], price, kind, index[c]) for i, price, kind, c in rows], columns=X.SWING_COLUMNS)


def test_divergences_by_hand():
    idx = pd.date_range("2024-01-01", periods=40, freq="1D", tz="UTC")
    swings = make_swings(idx, [(0, 90, -1, 3), (10, 100, 1, 13), (15, 95, -1, 18), (25, 105, 1, 28), (30, 96, -1, 33)])
    hist = pd.Series(0.0, index=idx)
    hist.iloc[8], hist.iloc[22] = 5.0, 3.0            # 第一段（1~10）最大 5，第二段（16~25）最大 3
    d = I.divergences(swings, hist, "bearish")
    assert d[["first", "second", "first_value", "second_value", "confirmed_at", "divergence"]].values.tolist() == \
        [[idx[10], idx[25], 5.0, 3.0, idx[28], True]]
    hist.iloc[22] = 6.0                                # 第二段更强：价格和指标一起创新高，不是背离
    assert not I.divergences(swings, hist, "bearish")["divergence"].iloc[0]
    hist.iloc[8], hist.iloc[22] = -1.0, -2.0           # 前一段的峰值在 0 下方：不算顶背离
    assert not I.divergences(swings, hist, "bearish")["divergence"].iloc[0]
    assert len(I.divergences(swings, hist, "bearish", max_bars=10)) == 0      # 两个高点相隔 15 根，超过上限


def test_divergences_bullish_mirror():
    idx = pd.date_range("2024-01-01", periods=40, freq="1D", tz="UTC")
    swings = make_swings(idx, [(0, 110, 1, 3), (10, 100, -1, 13), (15, 104, 1, 18), (25, 95, -1, 28)])
    hist = pd.Series(0.0, index=idx)
    hist.iloc[9], hist.iloc[20] = -5.0, -2.0
    d = I.divergences(swings, hist, "bullish")
    assert d["divergence"].tolist() == [True] and d["second_price"].iloc[0] == 95
