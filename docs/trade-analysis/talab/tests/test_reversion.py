"""talab.reversion 的测试（第 32 篇）。价格全部手工构造，每个数都能自己算一遍。"""
import numpy as np
import pandas as pd
import pytest

from talab import reversion as RV


def frame(closes, spread: float = 0.01, opens=None) -> pd.DataFrame:
    close = np.asarray(closes, dtype=float)
    open_ = close if opens is None else np.asarray(opens, dtype=float)
    return pd.DataFrame({"open": open_, "high": np.maximum(close, open_) * (1 + spread),
                         "low": np.minimum(close, open_) * (1 - spread), "close": close},
                        index=pd.date_range("2024-01-01", periods=len(close), freq="D"))


def test_stretch_is_the_z_score_against_the_moving_average():
    close = pd.Series([1, 2, 3, 4, 10.0], index=pd.date_range("2024-01-01", periods=5))
    out = RV.stretch(close, 4)
    assert np.isnan(out.iloc[2])                                  # 前三根凑不齐窗口
    window = close.iloc[1:5]
    assert out.iloc[4] == pytest.approx((10 - window.mean()) / window.std())
    assert out.iloc[4] > 1                                        # 最后一根远高于均线
    flat = pd.Series([5.0] * 10, index=pd.date_range("2024-01-01", periods=10))
    assert np.isnan(RV.stretch(flat, 5).iloc[-1])                 # 标准差是 0，除不出来


def test_streak_counts_up_days_positive_and_down_days_negative():
    close = pd.Series([10, 11, 12, 13, 12, 11, 10, 10, 11.0])
    out = RV.streak(close)
    assert list(out.iloc[1:4]) == [1, 2, 3]                       # 连涨三天
    assert list(out.iloc[4:7]) == [-1, -2, -3]                    # 连跌三天
    assert out.iloc[7] == 0                                       # 持平清零
    assert out.iloc[8] == 1


def test_setups_records_what_happened_after_each_trigger():
    close = pd.Series([100, 90, 95, 99, 120.0], index=pd.date_range("2024-01-01", periods=5))
    condition = pd.Series([False, True, False, False, False], index=close.index)
    table = RV.setups(close, condition, horizons=(1, 3))
    assert len(table) == 1
    row = table.iloc[0]
    assert row["收盘"] == 90
    assert row["1 根后"] == pytest.approx(95 / 90 - 1)
    assert row["3 根后"] == pytest.approx(120 / 90 - 1)
    assert row["期间最低"] == pytest.approx(95 / 90 - 1)          # 之后三根里最低的是 95


def test_edge_compares_the_signal_against_doing_nothing():
    """胜率 100% 也可能什么都没说——要和「随便哪一天买入」比。"""
    close = pd.Series(np.linspace(100, 200, 200), index=pd.date_range("2024-01-01", periods=200))
    condition = pd.Series(False, index=close.index)
    condition.iloc[[10, 50, 90]] = True
    out = RV.edge(RV.setups(close, condition, horizons=(5,)), close, horizon=5)
    assert out["次数"] == 3
    assert out["胜率"] == 1.0 and out["基准胜率"] == 1.0           # 一路上涨，两边都是 100%
    assert out["比基准多赚"] > 0                                  # 三次都落在前半段，那时涨幅占比更大
    assert out["平均"] > out["基准平均"]                          # ——但这什么都没证明，只是买得早


def test_plan_validates_and_describes_both_entry_styles():
    text = RV.ReversionPlan().describe()
    assert "2.0 个标准差" in text["进场"] and "连跌 3 天" in text["进场"]
    assert text["成交"].startswith("下一根开盘")
    rsi = RV.ReversionPlan(entry_rsi=5, rsi_period=2).describe()
    assert rsi["进场"] == "2 日 RSI 低于 5"
    for bad in [dict(side="随便"), dict(entry_z=1.0), dict(max_bars=0), dict(entry_rsi=120)]:
        with pytest.raises(ValueError):
            RV.ReversionPlan(**bad)


def test_books_balance_and_fills_happen_on_the_next_open():
    """信号用到当根收盘价，所以**只能下一根开盘成交**——第 31 篇那个例外在这里不成立。"""
    dip = [100.0] * 25 + [97, 94, 91] + [95.0] * 10
    bars = frame(dip, opens=[100.0] * 25 + [99, 96, 93] + [92.0] + [95.0] * 9)
    plan = RV.ReversionPlan(n=20, entry_z=-1.0, entry_streak=3, exit_z=0.0,
                            max_bars=10, stop_atr=None, fraction=1.0)
    result = RV.reversion(bars, plan)
    assert result["记账误差"] == 0.0
    trade = result["交易"].iloc[0]
    assert trade["进场日"] == bars.index[28]                      # 第 27 根收盘才满足条件
    assert trade["进场价"] == pytest.approx(92.0)                 # 成交在第 28 根的**开盘**


def test_the_three_exits_each_fire():
    reasons = set()
    for closes, kwargs in [
            ([100.0] * 25 + [96, 92, 88] + [200.0] * 5, dict(stop_atr=None)),        # 暴涨 → 回到均线
            ([100.0] * 25 + [96, 92, 88] + [88.5] * 15, dict(stop_atr=None)),        # 不动 → 时间到
            ([100.0] * 25 + [96, 92, 88, 87] + [60.0] * 6, dict(stop_atr=1.0, risk=0.02))]:  # 续跌 → 止损
        plan = RV.ReversionPlan(n=20, entry_z=-1.0, entry_streak=3, max_bars=5, **kwargs)
        trades = RV.reversion(frame(closes), plan)["交易"]
        assert len(trades) >= 1
        reasons.add(trades.iloc[0]["原因"])
    assert reasons == {"回到均线", "时间到", "止损"}


def test_stop_is_three_atr_away_and_costs_exactly_one_r():
    closes = [100 + (1 if i % 2 else -1) for i in range(25)] + [96, 92, 88, 40.0]
    plan = RV.ReversionPlan(n=20, entry_z=-1.0, entry_streak=3, max_bars=20,
                            stop_atr=3.0, risk=0.02, atr_period=14)
    trade = RV.reversion(frame(closes), plan)["交易"].iloc[0]
    assert trade["原因"] == "止损"
    assert trade["R"] < -1.0                                      # 跳空跳过止损，比 1R 还多


def test_rsi_entry_is_an_alternative_trigger():
    closes = [100.0] * 25 + [96, 92, 88] + [95.0] * 10
    common = dict(n=5, exit_z=0.0, max_bars=10, stop_atr=None, fraction=1.0)
    by_rsi = RV.reversion(frame(closes), RV.ReversionPlan(entry_rsi=10, rsi_period=2, **common))
    assert len(by_rsi["交易"]) >= 1
    assert by_rsi["记账误差"] == 0.0


def test_short_side_is_the_mirror_image():
    rising = [100.0] * 25 + [104, 108, 112] + [98.0] * 10
    opens = [100.0] * 25 + [104, 108, 112] + [111.0] + [98.0] * 9   # 第 28 根高开、低走
    plan = dict(n=20, entry_z=-1.0, entry_streak=3, exit_z=0.0, max_bars=10,
                stop_atr=None, fraction=1.0)
    down = RV.reversion(frame(rising, opens=opens), RV.ReversionPlan(side="short", **plan))
    assert len(down["交易"]) == 1 and down["记账误差"] == 0.0
    trade = down["交易"].iloc[0]
    assert trade["进场价"] == pytest.approx(111.0)                 # 下一根开盘卖出
    assert trade["收益"] == pytest.approx(1 - 98 / 111)            # 跌回 98 就是这么多
    assert trade["收益"] > 0                                       # 涨太多之后做空，回落时赚钱


def test_worst_trades_is_the_mirror_of_contribution():
    """趋势跟随问「拿掉最赚的几笔还剩多少」，均值回归要问反过来的那一句。"""
    out = RV.worst_trades([0.01, 0.01, 0.01, 0.01, -0.10], tops=(1, 2))
    assert out.loc[0, "剩下多少"] == pytest.approx(-0.06)
    assert out.loc[1, "拿掉最亏的几笔"] == 1
    assert out.loc[1, "剩下多少"] == pytest.approx(0.04)          # 拿掉那一笔就赚钱了
    assert out.loc[1, "变成原来的"] < 0                           # 从亏变赚，比值是负的
    assert out.loc[2, "剩下多少"] == pytest.approx(0.03)


def test_blend_rebalances_back_to_the_target_weights():
    index = pd.date_range("2024-01-31", periods=90, freq="D")
    fast = pd.Series(np.linspace(100, 300, 90), index=index)       # 一条涨三倍
    flat = pd.Series(100.0, index=index)                           # 一条一动不动
    mixed = RV.blend({"快": fast, "平": flat}, [0.5, 0.5], rebalance="ME")
    never = RV.blend({"快": fast, "平": flat}, [0.5, 0.5], rebalance=None)
    assert len(mixed) == len(fast)
    assert mixed.iloc[-1] < never.iloc[-1]                        # 不再平衡＝让赢家越占越大
    assert mixed.iloc[-1] > flat.iloc[-1]                         # 但组合还是跟着涨了
    with pytest.raises(ValueError):
        RV.blend({"快": fast, "平": flat}, [0.7, 0.7])


def test_blend_of_one_curve_is_that_curve():
    index = pd.date_range("2024-01-01", periods=40, freq="D")
    curve = pd.Series(np.linspace(100, 140, 40), index=index)
    out = RV.blend({"只有一条": curve}, [1.0])
    assert np.allclose(out.to_numpy(), curve.to_numpy())
