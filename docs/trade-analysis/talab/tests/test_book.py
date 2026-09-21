"""talab.book 的测试（番外篇）。深度全部手工构造，每个数都能自己算一遍。"""
import numpy as np
import pandas as pd
import pytest

from talab import book as B


def snapshots(bid_1, ask_1, bid_5=None, ask_5=None) -> pd.DataFrame:
    """一张最小的深度表：只填 ±1% 和 ±5% 两档，列名和 `data.load_binance_book_depth` 一致。"""
    n = len(bid_1)
    index = pd.date_range("2024-01-01", periods=n, freq="30s", tz="UTC")
    data = {"-1%": np.asarray(bid_1, float), "+1%": np.asarray(ask_1, float)}
    if bid_5 is not None:
        data["-5%"] = np.asarray(bid_5, float)
        data["+5%"] = np.asarray(ask_5, float)
    return pd.DataFrame(data, index=index)


def test_sides_splits_the_level_and_knows_which_sign_is_the_bid():
    depth = snapshots([300.0, 100.0], [100.0, 100.0])
    out = B.sides(depth, 1.0)
    assert list(out["买侧"]) == [300.0, 100.0]          # 负号那一侧是买盘
    assert list(out["合计"]) == [400.0, 200.0]
    assert out["不对称"].iloc[0] == pytest.approx(0.5)  # (300-100)/400
    assert out["不对称"].iloc[1] == pytest.approx(0.0)
    with pytest.raises(ValueError, match="0.2"):
        B.sides(depth, 1.5)                             # 不存在的档位
    with pytest.raises(ValueError, match="没有"):
        B.sides(depth, 5.0)                             # 这张表没填 ±5%


def test_imbalance_stays_between_minus_one_and_one():
    depth = snapshots([100.0, 0.0, 50.0], [0.0, 100.0, 50.0])
    out = B.imbalance(depth)
    assert list(out) == [1.0, -1.0, 0.0]
    assert out.name == "不对称（1%）"
    empty = B.imbalance(snapshots([0.0], [0.0]))
    assert np.isnan(empty.iloc[0])                      # 两侧都是 0，除不出来


def test_relative_never_uses_the_current_snapshot():
    """这一篇的时钟规矩：`relative` 的分母只能用**之前**的快照。"""
    values = pd.Series([10.0] * 8 + [1000.0],
                       index=pd.date_range("2024-01-01", periods=9, freq="30s", tz="UTC"))
    out = B.relative(values, window=8)
    # 最后一根暴涨到 1000，分母仍然是前八根的中位数 10 → 100 倍
    assert out.iloc[-1] == pytest.approx(100.0)
    # 把最后一根改成 5，分母一个字不变——说明它没看当根
    changed = values.copy()
    changed.iloc[-1] = 5.0
    assert B.relative(changed, window=8).iloc[-1] == pytest.approx(0.5)
    with pytest.raises(ValueError):
        B.relative(values, window=1)


def test_squeeze_splits_what_vanished_into_eaten_and_gone():
    # 买侧从 1000 掉到 200：少了 800
    bid = [1000.0, 1000.0, 1000.0, 200.0]
    depth = snapshots(bid, [1000.0] * 4)
    sells = pd.Series([0.0, 0.0, 0.0, 100.0], index=depth.index)   # 同期只吃掉 100
    out = B.squeeze(depth, sells, level=1.0, span=3)
    assert out["少掉多少"].iloc[-1] == pytest.approx(800.0)
    assert out["吃掉多少"].iloc[-1] == pytest.approx(100.0)
    # 八百块钱消失，只有一百是被吃掉的——剩下七百自己走了
    assert out["吃掉的占比"].iloc[-1] == pytest.approx(0.125)
    with pytest.raises(ValueError):
        B.squeeze(depth, sells, span=0)


def test_squeeze_leaves_the_ratio_undefined_when_depth_grew():
    depth = snapshots([100.0, 100.0, 500.0], [100.0] * 3)
    sells = pd.Series([10.0] * 3, index=depth.index)
    out = B.squeeze(depth, sells, span=2)
    assert out["少掉多少"].iloc[-1] < 0                  # 深度反而变厚了
    assert np.isnan(out["吃掉的占比"].iloc[-1])          # 这时候「占比」没有意义


def test_recovery_finds_when_it_came_back_and_admits_when_it_did_not():
    base = [100.0] * 10
    back = pd.Series(base + [20.0, 30.0, 60.0, 95.0, 100.0],
                     index=pd.date_range("2024-01-01", periods=15, freq="30s", tz="UTC"))
    event = back.index[10]
    out = B.recovery(back, [event], horizon=10, fraction=0.9, before=10)
    assert out["事件前水平"].iloc[0] == pytest.approx(100.0)
    assert out["最低点"].iloc[0] == pytest.approx(20.0)
    assert out["最低点占事件前"].iloc[0] == pytest.approx(0.2)
    assert out["最低点在几分钟后"].iloc[0] == pytest.approx(0.0)   # 事件那一张就是谷底
    assert out["几张快照后回来"].iloc[0] == 3            # ⚠️ 从**谷底**往后数第 3 张（95 ≥ 90）
    assert out["几分钟后回来"].iloc[0] == pytest.approx(1.5)
    # 一直没回来的那几次记 NaN，不能当成 0，也不能悄悄丢掉
    never = pd.Series(base + [20.0] * 5, index=back.index)
    assert np.isnan(B.recovery(never, [event], horizon=10, before=10)["几张快照后回来"].iloc[0])
    # ⚠️ 崩盘那一刻还没跌的那些：从事件时刻起算会记成「0 分钟就回来了」，从谷底起算才对
    late = pd.Series(base + [100.0, 100.0, 20.0, 95.0, 100.0], index=back.index)
    slow = B.recovery(late, [event], horizon=10, fraction=0.9, before=10)
    assert slow["最低点在几分钟后"].iloc[0] == pytest.approx(1.0)
    assert slow["几张快照后回来"].iloc[0] == 1
    # ⚠️ 谷底只在 `trough_within` 之内找：把窗口收到 2 张，就看不到第 3 张那个 20
    near = B.recovery(late, [event], horizon=10, fraction=0.9, before=10, trough_within=2)
    assert near["最低点"].iloc[0] == pytest.approx(100.0)
    with pytest.raises(ValueError):
        B.recovery(late, [event], horizon=10, before=10, trough_within=99)
    assert len(B.recovery(back, [back.index[2]], before=10)) == 0   # 窗口伸出数据范围，丢掉
    with pytest.raises(ValueError):
        B.recovery(back, [event], fraction=1.5)


def test_slope_says_where_the_money_sits():
    # 近档薄、远档厚 → 比值大 → 稍微一卖价格就往下走一截
    thin = snapshots([10.0], [10.0], bid_5=[500.0], ask_5=[500.0])
    fat = snapshots([200.0], [200.0], bid_5=[500.0], ask_5=[500.0])
    assert B.slope(thin).iloc[0] == pytest.approx(50.0)
    assert B.slope(fat).iloc[0] == pytest.approx(2.5)
    assert B.slope(thin).name == "5% ÷ 1%"
    with pytest.raises(ValueError):
        B.slope(thin, near=5.0, far=1.0)


def test_the_levels_binance_publishes_are_the_only_ones_that_exist():
    assert B.LEVELS == (0.2, 1.0, 2.0, 3.0, 4.0, 5.0)
    assert B.DAY == 2880                                 # 30 秒一张，一天 2,880 张
    depth = snapshots([1.0], [1.0])
    for level in (0.5, 1.5, 10.0):
        with pytest.raises(ValueError, match="只有"):
            B.sides(depth, level)
