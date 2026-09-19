"""talab.structure 的测试。"""
import numpy as np
import pandas as pd
import pytest

from talab import structure as X


def series(values, start="2024-01-01"):
    idx = pd.date_range(start, periods=len(values), freq="1D", tz="UTC")
    return pd.Series(values, index=idx, dtype=float)


def test_fractals_by_hand():
    high = series([10, 11, 13, 12, 11, 12, 12, 11, 10])
    low = series([9, 10, 12, 11, 8, 10, 11, 10, 9])
    f = X.fractals(high, low, left=2, right=2)
    day = high.index
    # 13 是高点，在右边第 2 根（下标 4）确认；8 是低点，在下标 6 确认
    # 下标 5、6 的最高价都是 12，但左边 2 根里都已经有一个 12，不是「严格高于」，所以都不算高点
    assert f.values.tolist() == [[day[2], 13.0, 1, day[4]], [day[4], 8.0, -1, day[6]]]


def test_zigzag_by_hand():
    close = series([100, 105, 112, 108, 100, 95, 104, 110])
    z = X.zigzag(close, 0.10)
    day = close.index
    # 112 比 100 高 12%：确认低点 100（第一根）。跌到 100，比 112 低 10.7%：确认高点 112
    # 95 之后涨到 104 只有 9.5%，还不够；涨到 110（15.8%）才确认低点 95
    assert z.values.tolist() == [[day[0], 100.0, -1, day[2]], [day[2], 112.0, 1, day[4]], [day[5], 95.0, -1, day[7]]]


@pytest.mark.parametrize("finder", ["zigzag", "fractals"])
def test_confirmed_swings_never_repaint(finder):
    rng = np.random.default_rng(8)
    close = series(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 400))))
    high, low = close * 1.01, close * 0.99

    def find(n):
        if finder == "zigzag":
            return X.zigzag(close.iloc[:n], 0.08)
        return X.fractals(high.iloc[:n], low.iloc[:n], 3, 3)

    full = find(400)
    for n in [50, 123, 250, 399]:
        early = find(n)
        known = full[full["confirmed_at"] <= close.index[n - 1]].reset_index(drop=True)
        pd.testing.assert_frame_equal(early, known)       # 截止到第 n 根时已经确认的摆动点，后来一个都没变


def test_trend_state_by_hand():
    close = series([10, 14, 12, 16, 13, 17, 15, 12, 11])
    t = close.index
    swings = pd.DataFrame([
        (t[0], 10.0, -1, t[1]), (t[1], 14.0, 1, t[2]), (t[2], 12.0, -1, t[3]),
        (t[3], 16.0, 1, t[4]), (t[4], 13.0, -1, t[5]), (t[5], 17.0, 1, t[6]),
    ], columns=X.SWING_COLUMNS)
    s = X.trend_state(swings, close, close)
    assert s["state"].iloc[:4].isna().all()          # 下标 4 才有两个高点和两个低点
    assert s["state"].iloc[4] == 1                    # 高点 14 → 16，低点 10 → 12
    assert s["state"].iloc[6] == 1                    # 高点 16 → 17，低点 12 → 13
    # 下标 7：收盘 12，已经低于最近的低点 13。新低点还没确认，但「更低」已经确定：高点抬高、低点降低
    assert s["state"].iloc[7] == 0
    assert s["last_low"].iloc[7] == 13 and s["last_high"].iloc[7] == 17


def test_trend_state_never_uses_the_future():
    rng = np.random.default_rng(1)
    close = series(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 500))))
    full = X.trend_state(X.zigzag(close, 0.08), close, close)
    for n in [100, 333, 499]:
        part = close.iloc[:n]
        early = X.trend_state(X.zigzag(part, 0.08), part, part)
        pd.testing.assert_frame_equal(early, full.iloc[:n])


def test_break_state_by_hand():
    close = series([10, 12, 11, 13, 9])
    levels = pd.DataFrame({"last_high": [np.nan, 11, 11, 12, 12], "last_low": [np.nan, 8, 8, 10, 10]}, index=close.index)
    assert X.break_state(levels, close).tolist()[1:] == [1, 1, 1, -1]


def test_efficiency_ratio_by_hand():
    close = series([100, 102, 101, 104])
    assert X.efficiency_ratio(close, 3).iloc[-1] == pytest.approx(4 / 6)      # 净变化 4，走过的路 2 + 1 + 3
    assert X.efficiency_ratio(series([1, 2, 3, 4, 5]), 4).iloc[-1] == 1


def test_regression_slope_exact_growth():
    close = series(100 * 1.01 ** np.arange(30))
    r = X.regression_slope(close, 20)
    assert r["slope"].iloc[-1] == pytest.approx(np.log(1.01))
    assert r["r2"].iloc[-1] == pytest.approx(1)
    assert r["slope"].iloc[:19].isna().all()


def test_true_range_and_directional_movement_by_hand():
    high = series([10, 12, 11, 15])
    low = series([8, 9, 7, 12])
    close = series([9, 11, 8, 14])
    assert X.true_range(high, low, close).tolist()[1:] == [3, 4, 7]            # 第三根：11 - 7；第四根：15 - 8
    dm = X.directional_movement(high, low)
    assert dm["plus_dm"].tolist()[1:] == [2, 0, 4]       # 第三根：最高价没涨，最低价跌了 2，只算 -DM
    assert dm["minus_dm"].tolist()[1:] == [0, 2, 0]


def test_adx_of_a_perfect_staircase():
    close = series(np.arange(100, 160, dtype=float))
    a = X.adx(close + 1, close - 1, close, 14)
    assert a["adx"].first_valid_index() == close.index[27]                   # 第一个 ADX 在下标 2n - 1
    assert a["plus_di"].dropna().eq(50).all() and a["minus_di"].dropna().eq(0).all()
    assert a["adx"].dropna().eq(100).all()                                   # 每天都只向上扩展：ADX = 100


# ---------------------------------------------------------------------------
# 第 9 篇：关键位置和缺口
# ---------------------------------------------------------------------------

def test_cluster_levels_by_hand():
    c = X.cluster_levels([65618.49, 60000, 65000, 62510.28, 65118], 0.01)
    # 以 65,000 为基准，不超过 65,650 的都归入一组；60,000 和 62,510.28 各自一组
    assert c["count"].tolist() == [1, 1, 3]
    assert c["low"].iloc[2] == 65000 and c["high"].iloc[2] == 65618.49
    assert c["level"].iloc[2] == pytest.approx((65000 + 65118 + 65618.49) / 3)


def test_level_tests_by_hand():
    #            0    1    2    3    4    5    6    7    8    9   10   11
    close = series([100, 98, 101, 104, 101, 104, 99, 96, 97, 99.5, 96, 104])
    high, low = close + 0.5, close - 0.5
    low.iloc[4] = 100.2                     # 第 4 根回到 100 附近：第 2 次测试
    atr = series([2.0] * 12)                # ATR 固定为 2：离开 = 3，测试区 = 0.5
    t = close.index
    swings = pd.DataFrame([(t[0], 100.0, -1, t[1])], columns=X.SWING_COLUMNS)
    r = X.level_tests(high, low, close, swings, atr)
    # 第 3 根收在 104（离开 3）；第 4 根最低 100.2 进入 100.5 以内：测试；第 5 根收在 104：守住
    # 第 6 根最低 98.5：第 3 次测试；第 7 根收在 96（低于 97）：突破，变成阻力
    # 第 9 根最高 100 进入 99.5 以上：阻力的第 1 次测试；第 10 根收在 96：守住
    # 第 11 根最高 104.5：阻力的第 2 次测试，当根收在 104（高于 103）：突破
    assert r[["role", "flips", "n", "outcome"]].values.tolist() == [
        ["support", 0, 2, "held"], ["support", 0, 3, "broken"],
        ["resistance", 1, 1, "held"], ["resistance", 1, 2, "broken"]]
    assert r["test_time"].tolist() == [t[4], t[6], t[9], t[11]]
    assert r["resolved_at"].tolist() == [t[5], t[7], t[10], t[11]]


def test_level_tests_never_use_the_future():
    rng = np.random.default_rng(9)
    close = series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 600))))
    high, low = close * 1.01, close * 0.99
    atr = X.wilder_smooth(X.true_range(high, low, close), 14)
    swings = X.fractals(high, low, 5, 5)
    full = X.level_tests(high, low, close, swings, atr)
    for n in [150, 400]:
        end = close.index[n - 1]
        early = X.level_tests(high.iloc[:n], low.iloc[:n], close.iloc[:n], swings[swings["confirmed_at"] <= end], atr.iloc[:n])
        done = early[early["outcome"] != "open"].reset_index(drop=True)
        known = full[full["resolved_at"] <= end].reset_index(drop=True)
        pd.testing.assert_frame_equal(done, known)       # 截止到第 n 根已经分出结果的测试，后来一个都没变


def test_gaps_by_hand():
    open_ = series([10, 12, 11.5, 9, 9])
    high = series([11, 13, 12, 10, 10])
    low = series([9, 11.5, 11, 8, 8.5])
    close = series([11, 12, 11, 9, 9.5])
    g = X.gaps(open_, high, low, close)
    # 第 1 根：12 高于前一根最高 11，完整缺口；第 2 根：11.5 低于前收 12 但不低于前最低 11.5，不完整
    # 第 3 根：9 低于前最低 11，完整缺口；第 4 根：开盘 9 等于前收 9，不是缺口
    assert g.index.tolist() == close.index[1:4].tolist()
    assert g["direction"].tolist() == [1, -1, -1]
    assert g["full"].tolist() == [True, False, True]
    assert g["size"].iloc[0] == pytest.approx(12 / 11 - 1)


def test_first_reach_by_hand():
    high = series([12, 13, 12.5, 11.8, 12])
    low = series([11, 11.6, 11.4, 10.9, 11.5])
    t = high.index
    assert X.first_reach(high, low, t[1], 11.0, from_above=True) == t[3]      # 第 3 根最低 10.9，回补到 11
    assert X.first_reach(high, low, t[1], 13.0, from_above=False) == t[1]     # 当根就到了
    assert pd.isna(X.first_reach(high, low, t[2], 13.0, from_above=False))


# ---------------------------------------------------------------------------
# 第 11 篇：市场状态、入场和标注比较
# ---------------------------------------------------------------------------

def test_market_state_by_hand():
    close = series([100, 104, 112, 95, 88, 100])
    levels = pd.DataFrame({"state": [np.nan, 1, 0, 0, 0, -1],
                           "last_high": [np.nan, 110, 110, 110, 110, 110],
                           "last_low": [np.nan, 90, 90, 90, 90, 90]}, index=close.index)
    # 结构不一致时看收盘价在框里还是框外：112 在 110 上方，95 在框里，88 在 90 下方
    state = X.market_state(levels, close)
    assert pd.isna(state.iloc[0])
    assert state.iloc[1:].tolist() == ["up", "transition_up", "range", "transition_down", "down"]


def test_entries_breakout_and_failed_by_hand():
    close = series([100, 105, 100, 104, 112, 111, 108, 95, 89, 113])
    t = close.index
    levels = pd.DataFrame({"state": 0.0, "last_high": 110.0, "last_low": 90.0}, index=t)
    state = pd.Series(["range"] * 4 + ["transition_up", "transition_up", "range", "range", "transition_down", "range"], index=t)
    swings = pd.DataFrame(columns=X.SWING_COLUMNS)
    e = X.entries(close, close + 1, close - 1, swings, levels, state)
    # 112 第一次收在 110 上方：突破做多；两根之后 108 收回 110 下方：失败突破，做空
    # 89 第一次收在 90 下方：突破做空
    # 最后 113 收回 90 上方：跌破失败，做多。113 也在 110 上方，但 110 已经被越过一次了，不再算突破
    assert e.values.tolist() == [[t[4], "breakout", 1, 110.0], [t[6], "failed", -1, 110.0],
                                 [t[8], "breakout", -1, 90.0], [t[9], "failed", 1, 90.0]]


def test_entries_breakout_needs_a_state_other_than_the_same_trend():
    close = series([100, 112, 100, 88])
    t = close.index
    levels = pd.DataFrame({"state": 1.0, "last_high": 110.0, "last_low": 90.0}, index=t)
    state = pd.Series(["up", "up", "range", "transition_down"], index=t)
    e = X.entries(close, close, close, pd.DataFrame(columns=X.SWING_COLUMNS), levels, state)
    # 112 越过 110 时前一根已经是上升趋势：只是创新高，不算突破；88 跌破 90 时前一根是震荡：算
    assert e.values.tolist() == [[t[3], "breakout", -1, 90.0]]


def test_entries_pullback_by_hand():
    close = series([110, 120, 107, 105, 108, 104, 109, 111])
    t = close.index
    swings = pd.DataFrame([(t[1], 120.0, 1, t[2]), (t[5], 104.0, -1, t[6])], columns=X.SWING_COLUMNS)
    levels = pd.DataFrame({"state": 1.0, "last_high": np.nan, "last_low": np.nan}, index=t)
    state = pd.Series(["up"] * 8, index=t)
    e = X.entries(close, close + 1, close - 1, swings, levels, state)
    # 高点 120 在下标 2 确认；下标 3 的 105 没有高于前一根最高价 108；下标 4 的 108 高于 106：回调做多
    # 低点 104 在下标 6 确认，但状态是上升趋势，不是下降趋势，不产生做空的回调
    assert e.values.tolist() == [[t[4], "pullback", 1, 120.0]]


def test_entries_and_market_state_never_use_the_future():
    rng = np.random.default_rng(11)
    close = series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 500))))
    high, low = close * 1.01, close * 0.99

    def run(n):
        c, h, l = close.iloc[:n], high.iloc[:n], low.iloc[:n]
        swings = X.zigzag(c, 0.05)
        levels = X.trend_state(swings, c, c)
        state = X.market_state(levels, c)
        return state, X.entries(c, h, l, swings, levels, state)

    full_state, full_entries = run(500)
    assert full_entries["kind"].nunique() == 3                     # 三类信号都出现过，这个测试才有意义
    for n in [80, 191, 333, 499]:
        state, e = run(n)
        pd.testing.assert_series_equal(state, full_state.iloc[:n])
        known = full_entries[full_entries["time"] <= close.index[n - 1]].reset_index(drop=True)
        pd.testing.assert_frame_equal(e, known)


def test_first_passage_by_hand():
    close = series([100, 100, 100, 100])
    high = series([100, 105, 111, 112])
    low = series([100, 95, 96, 88])
    atr = series([5, 5, 5, 5])
    t = close.index
    # 上下两条线都是 100 ± 2 × 5 = 110 / 90
    out = X.first_passage(close, high, low, atr, [t[0], t[1], t[2], t[3]], [1, -1, 1, 1])
    # t0 做多：下标 2 先碰到 110，记 1；t1 做空：同样先碰到 110，记 0
    # t2：下标 3 同时碰到 112 和 88，分不清先后，记 0；t3：后面没有 K 线，记 NaN
    assert out[:3].tolist() == [1.0, 0.0, 0.0] and np.isnan(out[3])
    assert np.isnan(X.first_passage(close, high, low, atr, [t[0]], [1], horizon=1)[0])   # 只看 1 根，没碰到


def test_agreement_and_segments_by_hand():
    idx = pd.date_range("2024-01-01", periods=6, freq="1D", tz="UTC")
    segments = pd.DataFrame({"start": ["2024-01-01", "2024-01-05"], "end": ["2024-01-03", "2024-01-05"],
                             "label": ["up", "range"]})
    a = X.segments_to_labels(segments, idx)
    assert a.iloc[[0, 1, 2, 4]].tolist() == ["up", "up", "up", "range"] and a.iloc[[3, 5]].isna().all()
    a = pd.Series(["up", "up", "up", "range", "range", None], index=idx)
    b = pd.Series(["up", "up", "range", "range", "up", "up"], index=idx)
    result = X.agreement(a, b)
    # 两边都有标签的 5 根里 3 根相同：0.6。两边都是 up 占 0.6、range 占 0.4，随便贴碰上的概率 0.36 + 0.16 = 0.52
    assert result["share"] == pytest.approx(0.6)
    assert result["kappa"] == pytest.approx((0.6 - 0.52) / (1 - 0.52))
    assert result["table"].loc["up", "range"] == 1 and result["table"].loc["range", "up"] == 1


def test_adx_converges_to_talib():
    """talab 的 Wilder 平滑用前 n 个值的平均做初始值；TA-Lib 的 +DM、-DM、TR 只用前 n - 1 个（第 15 篇实验二）。
    两者的差每根乘以 (n - 1) / n，开头最多差零点几，几百根之后一致。"""
    talib = pytest.importorskip("talib")
    rng = np.random.default_rng(8)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 1000))))
    high, low = close * (1 + rng.uniform(0, 0.02, 1000)), close * (1 - rng.uniform(0, 0.02, 1000))
    ours = X.adx(high, low, close)
    H, L, C = high.to_numpy(), low.to_numpy(), close.to_numpy()
    for column, theirs in [("plus_di", talib.PLUS_DI(H, L, C, 14)), ("minus_di", talib.MINUS_DI(H, L, C, 14)),
                           ("adx", talib.ADX(H, L, C, 14))]:
        assert (ours[column].isna().to_numpy() == np.isnan(theirs)).all()
        assert np.nanmax(np.abs(ours[column].to_numpy() - theirs)) > 1e-3             # 开头确实不一样
        np.testing.assert_allclose(ours[column].to_numpy()[500:], theirs[500:], rtol=1e-8)

