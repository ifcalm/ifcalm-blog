"""talab.patterns 的测试（第 16 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import patterns as Pt, structure as X


def bars(rows):
    """rows 是 (open, high, low, close) 的列表，索引用连续的日期。"""
    index = pd.date_range("2024-01-01", periods=len(rows), freq="D", tz="UTC")
    return pd.DataFrame(rows, columns=Pt.OHLC, index=index, dtype=float)


def mirror(frame):
    """上下翻转：价格取相反数，最高价和最低价互换。看涨形态应该变成看跌形态。"""
    return pd.DataFrame({"open": -frame["open"], "high": -frame["low"],
                         "low": -frame["high"], "close": -frame["close"]})


def test_parts_by_hand():
    p = Pt.parts(bars([(10, 14, 8, 12), (12, 12, 12, 12)]))
    assert p["range_"].iloc[0] == 6 and p["body"].iloc[0] == 2
    assert p["upper"].iloc[0] == 2 and p["lower"].iloc[0] == 2          # 实体 10 到 12，上下各留 2
    assert p["top"].iloc[0] == 12 and p["bottom"].iloc[0] == 10 and bool(p["up"].iloc[0])
    assert np.isnan(p["range_"].iloc[1])                                 # 最高价等于最低价


def test_doji_by_hand():
    x = bars([(100, 110, 90, 101), (100, 110, 90, 105), (100, 100.5, 99.5, 100.04)])
    # 第 1 根实体 1，占整根 20 的 5%：是十字星；第 2 根实体 5，占 25%：不是
    assert Pt.doji(x).tolist() == [True, False, True]
    assert Pt.doji(x, body_max=0.3).tolist() == [True, True, True]


def test_hammer_by_hand():
    x = bars([(108, 110, 90, 109),        # 实体 1（占 10%），下影 18 = 18 倍实体，上影 1（占 5%）：锤子
              (108, 110, 90, 102),        # 实体 6（占 30%），下影 12 = 2 倍实体，上影 2（占 10%）：锤子
              (108, 116, 90, 109),        # 上影 7，占 26%，超过 15%：不是
              (101, 106, 94, 105),        # 实体 4（占 33%），下影 7 < 2 倍实体 8：不是
              (100, 110, 90, 100)])       # 实体 0，下影 10，上影 10 占 50%：不是
    assert Pt.hammer(x).tolist() == [True, True, False, False, False]
    assert Pt.hammer(x, upper_max=0.3).tolist() == [True, True, True, False, False]


def test_inverted_hammer_is_hammer_upside_down():
    rng = np.random.default_rng(16)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 500)))
    x = bars([(c * (1 + rng.normal(0, 0.005)), 0, 0, c) for c in close])
    x["high"] = x[["open", "close"]].max(axis=1) * (1 + rng.uniform(0, 0.02, 500))
    x["low"] = x[["open", "close"]].min(axis=1) * (1 - rng.uniform(0, 0.02, 500))
    assert Pt.hammer(x).sum() > 10 and Pt.inverted_hammer(x).sum() > 10
    pd.testing.assert_series_equal(Pt.inverted_hammer(x), Pt.hammer(mirror(x)), check_names=False)


def test_engulfing_by_hand():
    x = bars([(110, 111, 99, 100),        # 长阴线，实体 10
              (99, 112, 98, 111),         # 阳线，实体 99 到 111，盖住 100 到 110：看涨吞没
              (111, 112, 96, 97),         # 阴线，实体 97 到 111，盖住 99 到 111：看跌吞没
              (97, 113, 96, 112),         # 阳线，实体 97 到 112，盖住 97 到 111（下沿相等也算）：看涨吞没
              (112, 113, 111, 112.05)])   # 实体只占 5%，太小：不算
    assert Pt.engulfing(x).tolist() == [0, 1, -1, 1, 0]


def test_harami_by_hand():
    x = bars([(110, 111, 99, 100),        # 长阴线，实体 10 占整根 12 的 83%
              (102, 106, 101, 105),       # 阳线，实体 102 到 105 包在 100 到 110 里，实体 3 ≤ 一半：看涨孕线
              (104, 107, 103, 103.5),     # 前一根实体占它自己整根的 60%，也算长实体，这一根包在里面：看跌孕线
              (103, 110, 102, 109),       # 阳线，实体比前一根长：不是孕线
              (104, 105, 103, 103.8)])    # 阴线，实体 0.2 包在前一根阳线的实体里：看跌孕线
    assert Pt.harami(x).tolist() == [0, 1, -1, 0, -1]
    thin = bars([(110, 111, 99, 100), (102, 109, 101, 108)])              # 这一根实体 6 > 前一根实体 10 的一半：不算
    assert Pt.harami(thin).tolist() == [0, 0]


def test_star_by_hand():
    morning = bars([(110, 111, 99, 100),      # 长阴线，实体 100 到 110
                    (98, 99, 96, 97),         # 小实体，整个在 100 下方
                    (98, 106, 97, 106)])      # 阳线，收在 105 = 实体中点之上：早晨之星
    assert Pt.star(morning).tolist() == [0, 0, 1]
    late = morning.copy()
    late.iloc[2, late.columns.get_loc("close")] = 104                     # 收在中点 105 之下
    assert Pt.star(late).tolist() == [0, 0, 0]
    pd.testing.assert_series_equal(Pt.star(mirror(morning)), -Pt.star(morning), check_names=False)


def test_scan_columns_and_flat_bars():
    x = bars([(100, 100, 100, 100)] * 5)
    scan = Pt.scan(x)
    assert list(scan.columns) == ["十字星", "锤子形", "倒锤形", "吞没", "孕线", "星形"]
    assert (scan == 0).all().all()                                        # 完全没有波动的 K 线不产生任何形态
    assert scan.dtypes.map(str).eq("int64").all()


def test_scan_never_uses_the_future():
    rng = np.random.default_rng(160)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 400)))
    frame = bars([(c, c, c, c) for c in close])
    frame["open"] = frame["close"].shift(1, fill_value=close[0]) * (1 + rng.normal(0, 0.01, 400))
    frame["high"] = frame[["open", "close"]].max(axis=1) * (1 + rng.uniform(0, 0.015, 400))
    frame["low"] = frame[["open", "close"]].min(axis=1) * (1 - rng.uniform(0, 0.015, 400))
    full = Pt.scan(frame)
    assert (full.abs().sum() > 0).all()
    for k in [50, 200, 399]:
        pd.testing.assert_frame_equal(Pt.scan(frame.iloc[:k]), full.iloc[:k])


# ---------------------------------------------------------------------------
# 图表形态（第 17 篇）
# ---------------------------------------------------------------------------

def toy_path(points, n):
    """按 (根号, 价格) 的折点线性插值出 n 根收盘价。"""
    values = np.interp(np.arange(n), [p[0] for p in points], [p[1] for p in points])
    return pd.Series(values, index=pd.date_range("2024-01-01", periods=n, freq="D"))


def manual_swings(close, rows):
    """rows 是 (根号, 种类) 的列表，价格取收盘价，确认时刻放在下一根。"""
    return pd.DataFrame([(close.index[k], close.iloc[k], kind, close.index[k + 1]) for k, kind in rows],
                        columns=["time", "price", "kind", "confirmed_at"])


def test_head_and_shoulders_by_hand():
    close = toy_path([(0, 100), (10, 110), (16, 102), (28, 120), (36, 104), (44, 112), (60, 96)], 61)
    found = Pt.head_and_shoulders(close, X.zigzag(close, 0.05))
    assert len(found) == 1
    row = found.iloc[0]
    # 颈线过 (16, 102) 和 (36, 104)，每根抬高 0.1；头在第 28 根，颈线 103.2，高度 120 - 103.2 = 16.8
    # 右肩 112 在第 44 根，价格每根跌 1，第 50 根跌到 106，跌够 5%，右肩被确认；那时颈线 105.4，还没跌破
    # 第 51 根收盘 105 低于颈线 105.5：跌破；目标 105.5 - 16.8 = 88.7
    assert row["head"] == close.index[28] and row["confirmed_at"] == close.index[50]
    assert row["neckline"] == pytest.approx(105.4) and row["height"] == pytest.approx(16.8)
    assert row["broken_at"] == close.index[51] and row["target"] == pytest.approx(88.7)


def test_head_and_shoulders_rules_and_bottom_mirror():
    close = toy_path([(0, 100), (10, 110), (16, 102), (28, 120), (36, 104), (44, 119), (60, 96)], 61)
    swings = X.zigzag(close, 0.05)
    assert Pt.head_and_shoulders(close, swings).empty                         # 两肩差 9，超过高度 16.8 的 30%
    assert len(Pt.head_and_shoulders(close, swings, shoulder_tol=0.6)) == 1
    top_close = toy_path([(0, 100), (10, 110), (16, 102), (28, 120), (36, 104), (44, 112), (60, 96)], 61)
    top_swings = X.zigzag(top_close, 0.05)
    flipped = 300 - top_close                                                  # 上下颠倒：头肩顶变成头肩底
    flipped_swings = top_swings.assign(price=300 - top_swings["price"], kind=-top_swings["kind"])
    top, bottom = Pt.head_and_shoulders(top_close, top_swings), Pt.head_and_shoulders(flipped, flipped_swings, "bottom")
    assert list(bottom["head"]) == list(top["head"]) and list(bottom["broken_at"]) == list(top["broken_at"])
    assert bottom["height"].iloc[0] == pytest.approx(top["height"].iloc[0])
    assert bottom["target"].iloc[0] == pytest.approx(300 - top["target"].iloc[0])


def test_double_tops_by_hand():
    close = toy_path([(0, 100), (10, 120), (20, 108), (30, 119), (45, 100)], 46)
    found = Pt.double_tops(close, X.zigzag(close, 0.05))
    assert len(found) == 1
    row = found.iloc[0]
    # 两个顶 120 和 119，中间低点 108：高度 12，两顶差 1 ≤ 1.2；第二个顶之后每根跌 19/15
    # 第 35 根跌到 112.67（跌够 5%）确认；第 39 根收盘 107.6 跌破 108；目标 108 - 12 = 96
    assert row["confirmed_at"] == close.index[35] and row["broken_at"] == close.index[39]
    assert row["neckline"] == 108 and row["height"] == 12 and row["target"] == 96
    assert Pt.double_tops(close, X.zigzag(close, 0.05), tol=0.05).empty      # 两顶差 1 > 12 × 5%


@pytest.mark.parametrize("highs,lows,name", [
    ((110, 108), (100, 102), "对称三角形"), ((110, 110), (100, 104), "上升三角形"), ((110, 106), (100, 100), "下降三角形"),
    ((110, 112), (100, 106), "上升楔形"), ((110, 104), (100, 98), "下降楔形"), ((110, 110), (100, 100), "矩形"),
    ((110, 114), (100, 96), "扩散"), ((110, 114), (100, 104), "通道")])
def test_converging_names_by_hand(highs, lows, name):
    close = pd.Series(105.0, index=pd.date_range("2024-01-01", periods=41, freq="D"))
    for k, price in zip([0, 20, 10, 30], [*highs, *lows]):
        close.iloc[k] = price
    swings = manual_swings(close, [(0, 1), (10, -1), (20, 1), (30, -1)])
    assert Pt.converging(close, swings)["name"].tolist() == [name]


def test_converging_breakout_by_hand():
    close = pd.Series(104.5, index=pd.date_range("2024-01-01", periods=61, freq="D"))
    for k, price in [(0, 110), (10, 100), (20, 108), (30, 102)]:
        close.iloc[k] = price
    close.iloc[36] = 120                                                      # 上轨在第 36 根是 106.4，收盘 120 升破
    found = Pt.converging(close, manual_swings(close, [(0, 1), (10, -1), (20, 1), (30, -1)]))
    assert found["name"].iloc[0] == "对称三角形"
    assert found["broken_at"].iloc[0] == close.index[36] and found["direction"].iloc[0] == 1


def test_chart_patterns_never_use_the_future():
    rng = np.random.default_rng(170)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 1500))),
                      index=pd.date_range("2020-01-01", periods=1500, freq="D"))
    full_swings = X.zigzag(close, 0.03)
    for func, kinds in [(Pt.head_and_shoulders, ["top", "bottom"]), (Pt.double_tops, ["top", "bottom"])]:
        for kind in kinds:
            full = func(close, full_swings, kind)
            assert len(full) > 3
            for k in [600, 1100]:
                cut = close.iloc[:k]
                part = func(cut, X.zigzag(cut, 0.03), kind)
                expected = full[full["confirmed_at"] <= cut.index[-1]].reset_index(drop=True)
                expected["broken_at"] = expected["broken_at"].where(expected["broken_at"] <= cut.index[-1])
                shape = [col for col in part.columns if col not in ("broken_at", "neckline_at_break", "target")]
                pd.testing.assert_frame_equal(part[shape], expected[shape])
                assert part["broken_at"].equals(expected["broken_at"])


# ---------------------------------------------------------------------------
# 斐波那契回撤与扩展（第 18 篇）
# ---------------------------------------------------------------------------

def test_retracement_and_extension_levels_by_hand():
    up = Pt.retracement_levels(100, 200)
    assert up.tolist() == pytest.approx([176.4, 161.8, 150, 138.2, 121.4])
    down = Pt.retracement_levels(200, 100)                                    # 下跌段的回撤位在上方
    assert down.tolist() == pytest.approx([123.6, 138.2, 150, 161.8, 178.6])
    assert Pt.extension_levels(100, 200, 150).tolist() == pytest.approx([277.2, 311.8, 411.8])


def test_swing_ratios_by_hand():
    close = pd.Series([100.0, 200, 150, 300, 225, 240], index=pd.date_range("2024-01-01", periods=6, freq="D"))
    swings = manual_swings(close, [(0, -1), (1, 1), (2, -1), (3, 1), (4, -1)])
    ratios = Pt.swing_ratios(swings)
    # 段长：100、50、150、75。回撤：50/100、150/50、75/150；扩展：150/100、75/50
    assert ratios["retracement"].tolist()[2:] == pytest.approx([0.5, 3.0, 0.5])
    assert ratios["extension"].tolist()[3:] == pytest.approx([1.5, 1.5])
    assert ratios["retracement"].iloc[:2].isna().all() and ratios["extension"].iloc[:3].isna().all()


def retracement_bars(after):
    """0 到 10 根从 100 涨到 200；第 11、12 根回落（第 12 根最低 175），之后按 after 给出的 (最高, 最低, 收盘)。"""
    rows = [(p, p, p) for p in np.linspace(100, 200, 11)] + [(200, 184, 185), (186, 175, 180)] + list(after)
    index = pd.date_range("2024-01-01", periods=len(rows), freq="D")
    frame = pd.DataFrame(rows, columns=["high", "low", "close"], index=index)
    swings = pd.DataFrame([(index[0], 100.0, -1, index[1]), (index[10], 200.0, 1, index[12])], columns=X.SWING_COLUMNS)
    return frame, swings, pd.Series(5.0, index=index)


def test_retracement_tests_by_hand():
    # 23.6% 的价位 176.4 在第 12 根（确认那一根）之前就碰过了，不算；38.2% 的价位 161.8 在第 14 根第一次被碰到
    frame, swings, atr = retracement_bars([(172, 168, 170), (165, 161, 163), (167, 162, 166), (170, 166, 169)])
    found = Pt.retracement_tests(frame["high"], frame["low"], frame["close"], swings, atr, [0.236, 0.382, 0.5])
    assert found["ratio"].tolist() == [0.382]
    assert found["touched_at"].iloc[0] == frame.index[14] and found["level"].iloc[0] == pytest.approx(161.8)
    assert found["held"].iloc[0] == 1.0                                       # 第 15 根最高 167 ≥ 161.8 + 5
    frame, swings, atr = retracement_bars([(172, 168, 170), (165, 161, 163), (164, 156, 158)])
    found = Pt.retracement_tests(frame["high"], frame["low"], frame["close"], swings, atr, [0.382])
    assert found["held"].iloc[0] == 0.0                                       # 第 15 根最低 156 ≤ 161.8 - 5


def test_retracement_tests_down_leg_mirror():
    frame, swings, atr = retracement_bars([(172, 168, 170), (165, 161, 163), (167, 162, 166), (170, 166, 169)])
    flipped = pd.DataFrame({"high": -frame["low"], "low": -frame["high"], "close": -frame["close"]})
    flipped_swings = swings.assign(price=-swings["price"], kind=-swings["kind"])
    up = Pt.retracement_tests(frame["high"], frame["low"], frame["close"], swings, atr, [0.236, 0.382, 0.5])
    down = Pt.retracement_tests(flipped["high"], flipped["low"], flipped["close"], flipped_swings, atr, [0.236, 0.382, 0.5])
    assert down["touched_at"].tolist() == up["touched_at"].tolist() and down["held"].tolist() == up["held"].tolist()
    assert down["level"].tolist() == pytest.approx((-up["level"]).tolist())


def test_retracement_tests_never_use_the_future():
    rng = np.random.default_rng(180)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 1500))), index=pd.date_range("2020-01-01", periods=1500, freq="D"))
    high, low = close * (1 + rng.uniform(0, 0.01, 1500)), close * (1 - rng.uniform(0, 0.01, 1500))
    atr = pd.Series(0.02 * close.to_numpy(), index=close.index)
    ratios = [0.382, 0.5, 0.618]
    full = Pt.retracement_tests(high, low, close, X.zigzag(close, 0.05), atr, ratios)
    assert len(full) > 20
    for k in [700, 1200]:
        part = Pt.retracement_tests(high.iloc[:k], low.iloc[:k], close.iloc[:k], X.zigzag(close.iloc[:k], 0.05), atr.iloc[:k], ratios)
        settled = lambda frame: frame[frame["touched_at"] <= close.index[k - 1 - 20]].reset_index(drop=True)
        pd.testing.assert_frame_equal(settled(part), settled(full))
