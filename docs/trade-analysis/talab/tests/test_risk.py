"""talab.risk 的测试（第 23 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import risk as K, rules as R


def frame(rows):
    """rows 是 (open, high, low, close) 的列表，索引是连续的日期。"""
    index = pd.date_range("2020-01-01", periods=len(rows), freq="D")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=index, dtype=float)


FLAT = [(100, 100, 100, 100)] * 6                       # 0–5：预热用的平盘
BARS = frame(FLAT + [
    (100, 103, 99, 102),      # 6：这一根开盘买入
    (102, 106, 101, 105),     # 7
    (105, 112, 104, 111),     # 8
    (111, 113, 96, 97),       # 9：盘中跌到 96
    (97, 99, 90, 91),         # 10
    (91, 95, 89, 94),         # 11
])
SIGNAL = pd.Series([False] * 5 + [True] + [False] * 6, index=BARS.index)
PERCENT = dict(stop="percent", percent=0.10, atr_period=2)   # 一个 R = 进场价的 10% = 10.0


def test_r_multiple_counts_from_the_initial_stop():
    assert K.r_multiple(100.0, 90.0, 120.0) == pytest.approx(2.0)
    assert K.r_multiple(100.0, 90.0, 90.0) == pytest.approx(-1.0)
    assert K.r_multiple(100.0, 95.0, 120.0) == pytest.approx(4.0)     # 止损放近一倍，同样的价格就是 4 个 R
    with pytest.raises(ValueError):
        K.r_multiple(100.0, 100.0, 120.0)


def test_exit_rejects_impossible_settings():
    for bad in [dict(stop="玄学"), dict(trail="心理价位"), dict(trigger="盘中"),
                dict(partial_fraction=1.0), dict(partial_r=3.0, target_r=2.0)]:
        with pytest.raises(ValueError):
            K.Exit(**bad)


def test_describe_answers_four_questions():
    lines = K.Exit(stop="structure", lookback=20, trail="chandelier", target_r=2.0,
                   partial_r=1.0, max_bars=40).describe()
    assert list(lines.index) == ["一、初始止损", "二、止损跟不跟", "三、目标价", "四、最多拿多久"]
    assert "前 20 根" in lines["一、初始止损"] and "吊灯" in lines["二、止损跟不跟"]
    assert "2.0 个 R" in lines["三、目标价"] and "先平 50%" in lines["三、目标价"]
    assert "40 根" in lines["四、最多拿多久"]


def test_initial_stop_three_methods():
    atr = np.full(len(BARS), 2.0)
    assert K.initial_stop(BARS, 6, 100.0, K.Exit(stop="percent", percent=0.10), atr) == pytest.approx(90.0)
    assert K.initial_stop(BARS, 6, 100.0, K.Exit(stop="atr", k=3.0), atr) == pytest.approx(94.0)
    # 结构止损看前 3 根的最低价（都是 100），再往下 0.5 个 ATR
    plan = K.Exit(stop="structure", lookback=3, buffer=0.5)
    assert K.initial_stop(BARS, 6, 100.0, plan, atr) == pytest.approx(99.0)
    assert K.initial_stop(BARS, 10, 97.0, plan, atr) == pytest.approx(95.0)    # 第 7–9 根最低 96，再减 1


def test_a_structure_stop_above_the_entry_price_skips_the_trade():
    """跳空低开，前几根的低点反而在进场价上方：这笔没法按这条规则做，跳过而不是硬做。"""
    bars = frame(FLAT + [(95, 96, 94, 95), (95, 97, 93, 96)])
    plan = K.Exit(stop="structure", lookback=3, buffer=0.0, atr_period=2)
    trades = K.run(bars, pd.Series([False] * 5 + [True] + [False] * 2, index=bars.index), plan)
    assert len(trades) == 0


def test_a_trade_that_hits_the_stop():
    trades = K.run(BARS, SIGNAL, K.Exit(**PERCENT, trail="none"))
    assert len(trades) == 1
    one = trades.iloc[0]
    assert one["买入日"] == BARS.index[6] and one["买入价"] == pytest.approx(100.0)
    assert one["初始止损"] == pytest.approx(90.0) and one["R"] == pytest.approx(10.0)
    # 第 9 根收盘 97 还在止损上方，第 10 根收盘 91 才跌破 90？没有——91 > 90，第 11 根收盘 94 也没跌破
    assert one["原因"] == "未平仓" and one["卖出日"] == BARS.index[-1]
    assert one["R 倍数"] == pytest.approx((94 - 100) / 10)


def test_stop_fills_at_the_close_that_broke_it():
    bars = frame(FLAT + [(100, 103, 99, 102), (102, 103, 88, 89), (89, 90, 85, 86)])
    trades = K.run(bars, pd.Series([False] * 5 + [True] + [False] * 3, index=bars.index),
                   K.Exit(**PERCENT, trail="none"))
    one = trades.iloc[0]
    assert one["原因"] == "止损" and one["卖出价"] == pytest.approx(89.0)
    assert one["R 倍数"] == pytest.approx(-1.1)                       # 收盘触发会穿过去，亏的比 1R 多
    assert one["最大浮亏"] == pytest.approx(-1.2)                     # 盘中一度到过 88


def test_target_exit():
    trades = K.run(BARS, SIGNAL, K.Exit(**PERCENT, trail="none", target_r=1.0))
    one = trades.iloc[0]
    assert one["原因"] == "止盈" and one["卖出日"] == BARS.index[8]    # 第 8 根收盘 111 ≥ 110
    assert one["R 倍数"] == pytest.approx(1.1)


def test_chandelier_only_moves_up():
    plan = K.Exit(stop="percent", percent=0.10, atr_period=2, trail="chandelier", trail_k=1.0)
    trades = K.run(BARS, SIGNAL, plan)
    one = trades.iloc[0]
    assert one["原因"] == "止损" and one["卖出日"] == BARS.index[9]
    assert one["卖出价"] == pytest.approx(97.0)                        # 第 9 根收盘已经在抬高后的止损下方


def test_time_stop():
    trades = K.run(BARS, SIGNAL, K.Exit(**PERCENT, trail="none", max_bars=3))
    one = trades.iloc[0]
    assert one["原因"] == "时间到" and one["根数"] == 3
    assert one["卖出价"] == pytest.approx(97.0) and one["R 倍数"] == pytest.approx(-0.3)


def test_exit_signal_comes_first():
    leave = pd.Series([False] * 8 + [True] + [False] * 3, index=BARS.index)
    trades = K.run(BARS, SIGNAL, K.Exit(**PERCENT, trail="none"), exits=leave)
    one = trades.iloc[0]
    assert one["原因"] == "出场信号" and one["卖出日"] == BARS.index[9]
    assert one["卖出价"] == pytest.approx(111.0)                       # 第 9 根的开盘价


def test_same_bar_is_counted_as_a_stop():
    plan = K.Exit(**PERCENT, trail="none", target_r=1.0, trigger="extreme")
    bars = frame(FLAT + [(100, 103, 99, 102), (102, 111, 89, 95)])
    trades = K.run(bars, pd.Series([False] * 5 + [True] + [False] * 2, index=bars.index), plan)
    one = trades.iloc[0]
    assert one["原因"] == "同一根"                                     # 110 和 90 在同一根里都碰到了
    assert one["卖出价"] == pytest.approx(90.0)                        # 按止损算，保守的那一边


def test_partial_take_profit_is_a_weighted_average():
    plan = K.Exit(**PERCENT, trail="none", partial_r=1.0, partial_fraction=0.5)
    trades = K.run(BARS, SIGNAL, plan)
    one = trades.iloc[0]
    # 第 8 根收盘 111 先平一半，记 0.5 × 1.1；剩下一半拿到最后一根收盘 94，记 0.5 × (-0.6)
    assert one["R 倍数"] == pytest.approx(0.5 * 1.1 + 0.5 * -0.6)


def test_excursions_and_no_new_trade_while_holding():
    always = pd.Series(True, index=BARS.index)
    trades = K.run(BARS, always, K.Exit(**PERCENT, trail="none"))
    assert len(trades) == 1                                            # 持仓期间的信号全部忽略
    one = trades.iloc[0]
    assert one["最大浮盈"] == pytest.approx((113 - 100) / 10)
    assert one["最大浮亏"] == pytest.approx((89 - 100) / 10)


def test_expectancy_matches_the_plain_average():
    r = pd.Series([2.0, -1.0, -1.0, 3.5, -0.4, 0.8])
    score = K.expectancy(r)
    assert score["交易数"] == 6
    assert score["胜率"] == pytest.approx(3 / 6)
    assert score["平均盈利"] == pytest.approx((2.0 + 3.5 + 0.8) / 3)
    assert score["平均亏损"] == pytest.approx((1.0 + 1.0 + 0.4) / 3)
    assert score["期望值"] == pytest.approx(r.mean())                  # 期望值就是平均 R
    assert score["盈亏比"] == pytest.approx(score["平均盈利"] / score["平均亏损"])


def test_agrees_with_rules_run_on_the_same_setup():
    """同样的入场、同样的 3 ATR 吊灯、同样的收盘触发，两个模块应该给出同一批交易。"""
    rng = np.random.default_rng(23)
    steps = rng.normal(0.0005, 0.02, 600)
    close = pd.Series(100 * np.exp(np.cumsum(steps)),
                      index=pd.date_range("2020-01-01", periods=600, freq="D"))
    df = pd.DataFrame({"open": close.shift(1).bfill(), "high": close * 1.01,
                       "low": close * 0.99, "close": close})
    entry = (close >= close.rolling(20).max()).fillna(False)
    never = pd.Series(False, index=df.index)
    mine = K.run(df, entry, K.Exit(stop="atr", k=3.0, trail="chandelier", trail_k=3.0, trigger="close"))
    theirs = R.run(df, R.Rule(entry=entry, exit=never, fill="next_open",
                              stop="chandelier", k=3.0, trigger="close"))[2]
    assert len(mine) == len(theirs) > 5
    assert list(mine["买入日"]) == list(theirs["买入日"])
    assert mine["卖出价"].to_numpy() == pytest.approx(theirs["卖出价"].to_numpy())


# --- 第 24 篇：杠杆、保证金、强平价 ---

BRACKETS = pd.DataFrame({"下限": [0, 300_000, 800_000], "上限": [300_000, 800_000, 3_000_000],
                         "维持保证金率": [0.004, 0.005, 0.0065], "速算额": [0, 300, 1500],
                         "最大杠杆": [150, 100, 75]})


def test_margin_tier_and_maintenance_margin():
    assert K.margin_tier(10_000, BRACKETS)["维持保证金率"] == pytest.approx(0.004)
    assert K.margin_tier(500_000, BRACKETS)["最大杠杆"] == 100
    assert K.maintenance_margin(10_000, BRACKETS) == pytest.approx(40.0)
    assert K.maintenance_margin(500_000, BRACKETS) == pytest.approx(500_000 * 0.005 - 300)
    # 速算额的作用是让档位之间连续：在 300,000 这个边界上，两档算出来一样
    assert K.maintenance_margin(300_000, BRACKETS) == pytest.approx(1200.0)
    assert K.maintenance_margin(300_001, BRACKETS) == pytest.approx(1200.005)


def test_liquidation_price_matches_the_hand_calculation():
    # 10 倍杠杆、维持保证金率 0.4%：做多 100 × 0.9 ÷ 0.996，做空 100 × 1.1 ÷ 1.004
    assert K.liquidation_price(100.0, 10, "long") == pytest.approx(100 * 0.9 / 0.996)
    assert K.liquidation_price(100.0, 10, "short") == pytest.approx(100 * 1.1 / 1.004)
    # 维持保证金率为 0 时就退化成「反向走 1/L 就爆」
    assert K.liquidation_price(100.0, 10, "long", mmr=0.0) == pytest.approx(90.0)
    assert K.liquidation_price(100.0, 10, "short", mmr=0.0) == pytest.approx(110.0)
    # 手续费和资金费先从保证金里扣，强平价就更近
    assert K.liquidation_price(100.0, 10, "short", mmr=0.0, spent=0.01) == pytest.approx(109.0)
    with pytest.raises(ValueError):
        K.liquidation_price(100.0, 10, "做空")


def test_short_is_liquidated_before_long_at_the_same_leverage():
    """同样的杠杆，空单的强平距离比多单近——名义价值朝着不利方向一起变大。"""
    for leverage in [2, 5, 10, 25]:
        long_gap = 1 - K.liquidation_price(100.0, leverage, "long") / 100
        short_gap = K.liquidation_price(100.0, leverage, "short") / 100 - 1
        assert short_gap < long_gap


def test_liquidation_price_uses_the_bracket_table():
    plain = K.liquidation_price(100.0, 10, "long", mmr=0.005, amount_ratio=300 / 500_000)
    looked_up = K.liquidation_price(100.0, 10, "long", notional=500_000, brackets=BRACKETS)
    assert looked_up == pytest.approx(plain)
    # 仓位大到进了第二档，维持保证金率更高，强平价离进场价更近（多单的强平价更高）
    small = K.liquidation_price(100.0, 10, "long", notional=10_000, brackets=BRACKETS)
    assert 100 - looked_up < 100 - small
    with pytest.raises(ValueError):
        K.liquidation_price(100.0, 10, "long", brackets=BRACKETS)


def test_max_leverage_keeps_the_stop_inside():
    for side, sign in [("long", -1), ("short", 1)]:
        leverage = K.max_leverage(0.10, side)
        stop = 100 * (1 + sign * 0.10)
        level = K.liquidation_price(100.0, leverage, side)
        assert level == pytest.approx(stop)                     # 正好卡在止损价上
        assert abs(K.liquidation_price(100.0, leverage * 1.1, side) - 100) < abs(stop - 100)
    assert K.max_leverage(0.10, "short", cushion=0.05) < K.max_leverage(0.10, "short")


def test_replay_liquidation():
    bars = frame([(100, 106, 99, 105), (105, 112, 104, 111), (111, 113, 96, 97), (97, 99, 90, 91)])
    # 10 倍空单从第 0 根开盘 100 开仓，强平价 109.56；第 1 根最高 112 越过了
    hit = K.replay_liquidation(bars, 10, "short", horizon=2)
    assert hit.iloc[0] == 1.0
    assert np.isnan(hit.iloc[-1])                               # 最后一根没有完整窗口
    # 同样两根里，10 倍多单的强平价是 90.36，没被碰到
    assert K.replay_liquidation(bars, 10, "long", horizon=2).iloc[0] == 0.0
    # 换成标记价格判断：标记价格没有插到 112，就不算强平
    mark = bars.copy()
    mark["high"] = [106, 108, 113, 99]
    assert K.replay_liquidation(bars, 10, "short", horizon=2, prices=mark).iloc[0] == 0.0


def test_funding_cost_sign():
    index = pd.date_range("2021-02-08", periods=6, freq="8h", tz="UTC")
    funding = pd.Series([0.001, 0.001, -0.002, 0.0005, 0.0005, 0.001], index=index)
    start, end = index[0], index[4]
    assert K.funding_cost(funding, start, end, "long") == pytest.approx(0.001 - 0.002 + 0.0005 + 0.0005)
    assert K.funding_cost(funding, start, end, "short") == pytest.approx(-(0.001 - 0.002 + 0.0005 + 0.0005))
    with pytest.raises(ValueError):
        K.funding_cost(funding, start, end, "两边")
