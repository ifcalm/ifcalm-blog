"""talab.rules 的测试（第 21 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import rules as R


def frame(closes, highs=None, lows=None, opens=None):
    """一串价格做成 OHLC 表；不给高低开就按收盘价填，方便手算。"""
    index = pd.date_range("2024-01-01", periods=len(closes), freq="D", tz="UTC")
    return pd.DataFrame({"open": opens or closes, "high": highs or closes,
                         "low": lows or closes, "close": closes}, index=index, dtype=float)


def flags(index, positions):
    out = pd.Series(False, index=index)
    out.iloc[list(positions)] = True
    return out


def test_rule_checks_its_own_fields():
    index = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    empty = pd.Series(False, index=index)
    with pytest.raises(ValueError, match="fill"):
        R.Rule(entry=empty, exit=empty, fill="随便买")
    with pytest.raises(ValueError, match="pullback"):
        R.Rule(entry=empty, exit=empty, fill="pullback")
    with pytest.raises(ValueError, match="止损"):
        R.Rule(entry=empty, exit=empty, stop="none", sizing="risk")
    described = R.Rule(entry=empty, exit=empty).describe()
    assert len(described) == 6 and described["三、入场方式"] == "下一根开盘价"
    assert described["四、初始止损"] == "3.0 倍 ATR 吊灯（close 触发）"     # 默认值也是选择


def test_next_open_and_close_fills_by_hand():
    df = frame([100, 100, 100, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110],
               opens=[100, 100, 100, 105, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110, 110])
    entry, exit_ = flags(df.index, [2]), flags(df.index, [14])
    _, _, next_open = R.run(df, R.Rule(entry=entry, exit=exit_, stop="none"))
    assert next_open.loc[0, "买入价"] == 105                    # 第 3 根收盘出信号，第 4 根开盘 105 成交
    assert next_open.loc[0, "卖出价"] == 110 and next_open.loc[0, "原因"] == "出场信号"
    _, _, at_close = R.run(df, R.Rule(entry=entry, exit=exit_, fill="close", stop="none"))
    assert at_close.loc[0, "买入价"] == 100                     # 当根收盘就买，便宜 5 块，但假设你能在收盘成交


def test_pullback_fill_waits_and_expires():
    df = frame([100] * 4 + [110, 108, 104, 109] + [110] * 10, lows=[100] * 4 + [110, 106, 100, 109] + [110] * 10)
    entry = flags(df.index, [3])
    limit = pd.Series(103.0, index=df.index)
    _, _, trades = R.run(df, R.Rule(entry=entry, exit=flags(df.index, [15]), fill="pullback",
                                    pullback_to=limit, stop="none"))
    assert trades.loc[0, "买入日"] == df.index[6] and trades.loc[0, "买入价"] == 103   # 第 7 根最低 100，限价成交
    short = R.Rule(entry=entry, exit=flags(df.index, [15]), fill="pullback", pullback_to=limit,
                   pullback_bars=2, stop="none")
    assert len(R.run(df, short)[2]) == 0                        # 只挂两根就过期，没等到回调


def test_percent_stop_by_hand():
    df = frame([100] * 4 + [100, 95, 88, 92] + [100] * 8, lows=[100] * 4 + [100, 89, 86, 92] + [100] * 8)
    rule = R.Rule(entry=flags(df.index, [3]), exit=flags(df.index, [15]), stop="percent", stop_percent=0.10)
    _, _, trades = R.run(df, rule)
    assert trades.loc[0, "买入价"] == 100 and trades.loc[0, "原因"] == "止损"
    assert trades.loc[0, "卖出价"] == 88                        # 收盘 88 跌破 90，按收盘价出场
    intrabar = R.run(df, R.Rule(entry=flags(df.index, [3]), exit=flags(df.index, [15]), stop="percent",
                                stop_percent=0.10, trigger="low"))[2]
    # 第 6 根盘中最低 89 已经跌破 90，盘中触发早一根出场，而且成交在止损价 90 而不是收盘价 88
    assert intrabar.loc[0, "卖出日"] == df.index[5] and intrabar.loc[0, "卖出价"] == 90


def test_risk_sizing_is_capped_by_the_stop_distance():
    df = frame([100] * 20)
    rule = R.Rule(entry=flags(df.index, [3]), exit=flags(df.index, [18]), stop="percent", stop_percent=0.10,
                  sizing="risk", risk_per_trade=0.01)
    _, held, trades = R.run(df, rule)
    assert trades.loc[0, "仓位"] == pytest.approx(0.1)          # 1% 风险 ÷ 10% 止损距离 = 10% 仓位
    assert held.max() == pytest.approx(0.1)
    wide = R.Rule(entry=flags(df.index, [3]), exit=flags(df.index, [18]), stop="percent", stop_percent=0.005,
                  sizing="risk", risk_per_trade=0.01)
    assert R.run(df, wide)[2].loc[0, "仓位"] == 1.0             # 1% ÷ 0.5% = 2 倍，封顶在满仓


def test_environment_filter_blocks_new_trades():
    df = frame([100] * 20)
    entry, exit_ = flags(df.index, [3, 10]), flags(df.index, [6, 15])
    closed = pd.Series(True, index=df.index)
    closed.iloc[3] = False                                      # 第一个信号那天不许开仓
    _, _, trades = R.run(df, R.Rule(entry=entry, exit=exit_, environment=closed, stop="none"))
    assert len(trades) == 1 and trades.loc[0, "买入日"] == df.index[11]


def test_returns_match_the_trades():
    rng = np.random.default_rng(0)
    closes = list(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 60))))
    df = frame(closes, highs=[x * 1.01 for x in closes], lows=[x * 0.99 for x in closes])
    rule = R.Rule(entry=flags(df.index, [20]), exit=flags(df.index, [50]), stop="none")
    returns, held, trades = R.run(df, rule)
    assert len(trades) == 1
    assert (1 + returns).prod() == pytest.approx(1 + trades.loc[0, "收益"])   # 资金曲线和这笔交易对得上
    assert held.sum() == pytest.approx((held > 0).sum())        # 满仓时仓位就是 1


def test_run_never_uses_the_future():
    rng = np.random.default_rng(1)
    closes = list(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 80))))
    df = frame(closes, highs=[x * 1.02 for x in closes], lows=[x * 0.98 for x in closes])
    entry, exit_ = flags(df.index, [30, 60]), flags(df.index, [45, 75])
    rule = lambda frame_: R.Rule(entry=entry.loc[frame_.index], exit=exit_.loc[frame_.index])
    full = R.run(df, rule(df))[0]
    cut = df.iloc[:50]
    pd.testing.assert_series_equal(R.run(cut, rule(cut))[0], full.loc[cut.index[full.index[0] <= cut.index]],
                                   check_freq=False)


def test_open_position_is_reported():
    df = frame([100] * 10 + [120] * 10)
    _, _, trades = R.run(df, R.Rule(entry=flags(df.index, [3]), exit=pd.Series(False, index=df.index), stop="none"))
    assert len(trades) == 1 and trades.loc[0, "原因"] == "未平仓"
    assert trades.loc[0, "卖出日"] == df.index[-1] and trades.loc[0, "卖出价"] == 120      # 按最后的收盘价估值


def test_overlap_and_stack_by_hand():
    index = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    conditions = {"A": flags(index, range(0, 8)), "B": flags(index, range(4, 10)), "C": flags(index, [0, 1])}
    table = R.overlap(conditions)
    assert table.loc["A", "A"] == 0.8 and table.loc["C", "C"] == 0.2
    assert table.loc["A", "B"] == pytest.approx(4 / 10)         # 同时成立 4 根，并集 10 根
    assert table.loc["B", "C"] == 0.0                           # 从不同时成立
    stacked = R.stack(conditions, ["A", "B", "C"])
    assert stacked["还剩的 K 线"].tolist() == [8, 4, 0]         # 每加一条只会更少
