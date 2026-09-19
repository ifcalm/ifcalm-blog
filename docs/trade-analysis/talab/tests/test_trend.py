"""talab.trend 的测试（第 31 篇）。全部用手工构造的价格，每个数都能自己算一遍。"""
import numpy as np
import pandas as pd
import pytest

from talab import trend as T


def frame(closes, spread: float = 0.0) -> pd.DataFrame:
    """把一串收盘价变成 K 线：开盘 = 收盘，最高/最低按 spread 往两边撑开。"""
    close = np.asarray(closes, dtype=float)
    return pd.DataFrame({"open": close, "high": close * (1 + spread),
                         "low": close * (1 - spread), "close": close},
                        index=pd.date_range("2024-01-01", periods=len(close), freq="D"))


def ramp(flat: int = 30, up: int = 40, base: float = 100.0, step: float = 2.0) -> pd.DataFrame:
    """先横盘（锯齿），再一路上涨——足够海龟进场、加满四个单位、再被通道赶出来。"""
    noise = [base + (1 if i % 2 else -1) for i in range(flat)]
    rise = [base + step * (i + 1) for i in range(up)]
    fall = [rise[-1] - step * 3 * (i + 1) for i in range(15)]
    return frame(noise + rise + fall)


def test_donchian_shifts_by_one_bar():
    """不推迟一根，「创 n 日新高」会永远成立——今天的最高价当然是包含今天在内的最高价之一。"""
    bars = frame([1, 2, 3, 4, 5])
    channel = T.donchian(bars["high"], bars["low"], 3)
    assert np.isnan(channel["上轨"].iloc[2])                 # 前三根凑不齐「前 3 根」
    assert channel["上轨"].iloc[3] == 3 and channel["下轨"].iloc[3] == 1
    assert channel["中轨"].iloc[3] == 2
    assert (bars["high"] > channel["上轨"]).iloc[3:].all()   # 一路新高：确实每根都突破
    wrong = bars["high"].rolling(3).max()                    # 忘了 shift 的写法
    assert not (bars["high"] > wrong).iloc[3:].any()         # 永远不成立，信号一个都没有


def test_breakouts_counts_one_per_episode():
    """连着十根都在通道上方只算一次突破，否则一段趋势会被数成十次「突破」。"""
    bars = frame([10] * 5 + [11, 12, 13, 14, 15] + [9] * 5 + [16, 17])
    table = T.breakouts(bars, n=3, horizon=2)
    assert len(table) == 2                                   # 涨那一段一次，最后拉起来又一次
    assert table["时间"].iloc[0] == bars.index[5]
    assert table["突破价"].iloc[0] == 10


def test_breakouts_measures_what_happened_after():
    bars = frame([10] * 5 + [12, 14, 11])
    table = T.breakouts(bars, n=3, horizon=2)
    row = table.iloc[0]
    assert row["突破价"] == 10 and row["收盘"] == 12
    assert row["之后涨幅"] == pytest.approx(11 / 10 - 1)      # 两根之后收在 11
    assert row["最大顺势"] == pytest.approx(14 / 10 - 1)      # 中间最高收到 14
    assert row["最大逆势"] == pytest.approx(11 / 10 - 1)


def test_follow_through_splits_real_from_fake():
    table = pd.DataFrame({"之后涨幅": [0.1, -0.05, 0.2, -0.02],
                          "最大顺势": [0.3, 0.01, 0.25, 0.0],
                          "最大逆势": [-0.01, -0.08, -0.02, -0.05]})
    out = T.follow_through(table)
    assert out["突破次数"] == 4 and out["走出去的"] == 2
    assert out["假突破比例"] == pytest.approx(0.5)
    assert out["真的那些平均涨"] == pytest.approx(0.15)
    assert out["假的那些平均跌"] == pytest.approx(-0.035)
    assert out["全部平均"] == pytest.approx(0.0575)


def test_turtle_plan_validates_and_describes():
    text = T.TurtlePlan().describe()
    assert text["进场"] == "突破 20 日通道" and text["初始止损"] == "2.0 个 N"
    assert T.TurtlePlan(entry=55, exit=20).describe()["出场"] == "反向突破 20 日通道"
    for bad in [dict(side="随便"), dict(fill="随便"), dict(entry=1), dict(max_units=0)]:
        with pytest.raises(ValueError):
            T.TurtlePlan(**bad)


def test_turtle_books_balance_exactly():
    """现金 + 持仓 × 价格 = 权益，全程误差必须是 0（第 27 篇那条规矩）。"""
    result = T.turtle(ramp(), T.TurtlePlan(atr_period=5, entry=10, exit=5))
    assert result["记账误差"] == 0.0
    assert result["权益最低点"] > 0                          # 权益永远不该跌到 0 以下
    assert len(result["交易"]) >= 1


def test_turtle_enters_at_the_channel_and_stops_two_n_away():
    """止损正好放在 2 个 N 之外，被打掉的那一笔正好是 −1R。

    ⚠️ 横盘那一段要用锯齿而不是一条直线：**真实波幅全是 0 的话 N 也是 0**，
    除不了，海龟一笔都不会开——这是写这类测试时最容易踩的坑。
    """
    zigzag = [100 + (1 if i % 2 else -1) for i in range(14)]
    bars = frame(zigzag + [108, 60])                         # 锯齿 → 跳上去 → 砸下来
    plan = T.TurtlePlan(entry=10, exit=5, atr_period=5, stop_atr=2.0, max_units=1, risk=0.01)
    result = T.turtle(bars, plan)
    trade = result["交易"].iloc[0]
    add = result["加仓"].iloc[0]
    n = (trade["第一个单位的价"] - add["止损移到"]) / plan.stop_atr
    assert trade["第一个单位的价"] == pytest.approx(108)     # 开盘就跳过了通道，只能按开盘价成交
    assert add["止损移到"] == pytest.approx(trade["第一个单位的价"] - 2 * n)
    assert trade["原因"] == "止损"
    assert trade["R"] < -1.0                                 # 跳空跳过了止损：亏得比 1R 还多


def test_turtle_pyramids_and_walks_the_stop_up():
    result = T.turtle(ramp(), T.TurtlePlan(atr_period=5, entry=10, exit=5, max_units=4))
    adds = result["加仓"]
    first = adds[adds["第几个单位"] == 1].index[0]
    block = adds.loc[first:first + 3]
    assert list(block["第几个单位"]) == [1, 2, 3, 4]         # 最多加到四个
    assert block["成交价"].is_monotonic_increasing           # 每一个单位都买得更贵
    assert block["止损移到"].is_monotonic_increasing         # 止损跟着往上走
    assert (adds["第几个单位"] <= 4).all()


def test_turtle_max_units_changes_the_size_not_the_signal():
    """加仓只改仓位大小，不改进场出场的时点——笔数和进场日应该一模一样。"""
    bars = ramp()
    one = T.turtle(bars, T.TurtlePlan(atr_period=5, entry=10, exit=5, max_units=1))["交易"]
    four = T.turtle(bars, T.TurtlePlan(atr_period=5, entry=10, exit=5, max_units=4))["交易"]
    assert list(one["进场日"]) == list(four["进场日"])
    assert (four["单位数"] >= one["单位数"]).all()
    assert four["R"].sum() > one["R"].sum()                  # 涨上去的那一段，加仓赚得更多


def test_turtle_next_open_fills_one_bar_later():
    zigzag = frame([100 + (1 if i % 2 else -1) for i in range(14)], spread=0.02)
    assert float(zigzag["high"].iloc[4:14].max()) == pytest.approx(103.02)   # 10 日通道上轨
    # 第 15 根：开在通道下方 102，盘中穿上去；第 16 根直接开在 107
    extra = pd.DataFrame({"open": [102.0, 107.0, 110.0], "high": [106.0, 111.0, 114.0],
                          "low": [101.0, 106.0, 109.0], "close": [105.0, 110.0, 113.0]},
                         index=pd.date_range(zigzag.index[-1] + pd.Timedelta(days=1), periods=3))
    bars = pd.concat([zigzag, extra])
    common = dict(entry=10, exit=5, atr_period=5, max_units=1)
    touch = T.turtle(bars, T.TurtlePlan(fill="touch", **common))["交易"].iloc[0]
    later = T.turtle(bars, T.TurtlePlan(fill="next_open", **common))["交易"].iloc[0]
    assert touch["第一个单位的价"] == pytest.approx(103.02)       # 就在通道那条线上成交
    assert later["进场日"] == touch["进场日"] + pd.Timedelta(days=1)
    assert later["第一个单位的价"] == pytest.approx(107.0)        # 等一根，开盘已经 107 了


def test_turtle_short_side_is_the_mirror_image():
    falling = ramp()
    mirrored = falling.copy()
    top = float(falling["high"].max()) + 10
    mirrored["open"], mirrored["close"] = top - falling["open"], top - falling["close"]
    mirrored["high"], mirrored["low"] = top - falling["low"], top - falling["high"]
    plan = dict(atr_period=5, entry=10, exit=5)
    up = T.turtle(falling, T.TurtlePlan(side="long", **plan))
    down = T.turtle(mirrored, T.TurtlePlan(side="short", **plan))
    assert len(down["交易"]) == len(up["交易"])
    assert down["记账误差"] == 0.0
    assert down["交易"]["R"].sum() > 0                       # 镜像的下跌里，做空同样赚钱


def test_r_profile_matches_hand_arithmetic():
    out = T.r_profile([-1, -1, -1, 3, 5])
    assert out["笔数"] == 5 and out["胜率"] == pytest.approx(0.4)
    assert out["平均盈利 R"] == pytest.approx(4.0)
    assert out["平均亏损 R"] == pytest.approx(1.0)
    assert out["盈亏比"] == pytest.approx(4.0)
    assert out["期望 R"] == pytest.approx(1.0)
    assert out["中位 R"] == pytest.approx(-1.0)              # 典型的一笔是亏的
    assert out["合计 R"] == pytest.approx(5.0)
    assert out["偏度"] > 0                                   # 正偏：亏损可预料，盈利不可


def test_contribution_shows_how_concentrated_the_profit_is():
    out = T.contribution([-1, -1, -1, -1, 10], tops=(1, 2))
    assert out.loc[0, "剩下多少 R"] == pytest.approx(6.0)
    assert out.loc[1, "拿掉最赚的几笔"] == 1
    assert out.loc[1, "剩下多少 R"] == pytest.approx(-4.0)   # 拿掉那一笔就亏钱了
    assert out.loc[1, "占原来的"] < 0
    assert out.loc[1, "占总笔数"] == pytest.approx(0.2)


def test_convexity_finds_the_smile():
    """造一个真的趋势跟随者：顺着最近 20 根的方向做。它该在两头赚、中间亏。"""
    rng = np.random.default_rng(31)
    drift = np.concatenate([[0.005] * 200, [-0.005] * 200,
                            [0.005 if i % 2 else -0.005 for i in range(200)]])
    market = pd.Series(drift + rng.normal(0, 0.004, 600),   # 加一点噪声，免得分位数挤在一起
                       index=pd.date_range("2022-01-01", periods=600))
    direction = np.sign(market.rolling(20).sum().shift(1)).fillna(0.0)
    strategy = market * direction - 0.0005                   # 顺势做，外加一点点摩擦
    out = T.convexity(strategy, market, buckets=5, window=20)
    assert len(out) == 5 and out["根数"].sum() == 600 - 19
    assert out["市场中位"].is_monotonic_increasing           # 分组本身按市场涨跌排好了
    assert out["策略中位"].iloc[0] > out["策略中位"].iloc[2]  # 市场大跌那一组：做空赚钱
    assert out["策略中位"].iloc[-1] > out["策略中位"].iloc[2]  # 市场大涨那一组：做多赚钱
    with pytest.raises(ValueError):
        T.convexity(strategy, market, buckets=0)
