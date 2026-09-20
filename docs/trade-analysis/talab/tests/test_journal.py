"""talab.journal 的测试（第 33 篇）。交易序列全部手工构造，每个数都能自己算一遍。"""
import numpy as np
import pandas as pd
import pytest

from talab import journal as J


def frame(rows) -> pd.DataFrame:
    """一张最小的交易表，列名和第 27 篇 `backtest.run` 的输出一致。"""
    return pd.DataFrame(rows, columns=["买入日", "方向", "买入价", "卖出价", "数量", "费用"])


def test_streaks_cuts_a_sequence_into_runs():
    table = J.streaks([1.0, -1, -1, 2, 3, -1])
    assert list(table["方向"]) == ["赚", "亏", "赚", "亏"]
    assert list(table["长度"]) == [1, 2, 2, 1]
    assert list(table["起"]) == [0, 1, 3, 5]
    assert list(table["止"]) == [0, 2, 4, 5]
    assert len(J.streaks([])) == 0


def test_a_breakeven_trade_counts_as_a_loss():
    # 口径和 trend.r_profile 一致：大于 0 才算赚，正好打平算在亏的那一边
    assert J.longest_streak([-1, 0.0, -1, 5]) == 3
    assert J.longest_streak([-1, 0.0, -1, 5], winning=True) == 1
    assert J.longest_streak([1, 2, 3]) == 0                   # 一笔没亏过


def test_expected_longest_matches_the_monte_carlo():
    # 抛 200 次硬币，最长连续正面的期望：公式和一万次模拟应该对得上
    formula = J.expected_longest(200, 0.5)
    simulated = J.streak_distribution(200, 0.5, trials=5000, seed=1)["平均最长连亏"]
    assert abs(formula - simulated) < 0.3
    # 笔数翻一倍，最长连亏只多出 log2(2) = 1 笔左右——**它随笔数增长得很慢，但一定在长**
    assert 0.8 < J.expected_longest(400, 0.5) - formula < 1.2


def test_a_long_losing_streak_is_ordinary_when_the_win_rate_is_low():
    out = J.streak_distribution(70, 0.33, trials=5000, seed=2)
    assert out["平均最长连亏"] > 8                             # 胜率 33% 做 70 笔，期望就有八九笔
    assert out["90% 分位"] >= 11                               # 连亏 11 笔以上也在正常范围里
    assert out["50% 分位"] <= out["95% 分位"]


def test_streak_alarm_tells_you_the_false_alarm_rate():
    table = J.streak_alarm(70, 0.33, thresholds=(4, 8, 15), trials=3000, seed=3)
    probability = table.set_index("门槛（连亏几笔）")["至少响一次的概率"]
    assert probability.loc[4] > 0.98                           # 「连亏 4 笔就停」几乎必然会响
    assert probability.loc[4] > probability.loc[8] > probability.loc[15]
    assert (table["平均响几次"] >= table["至少响一次的概率"]).all()


def test_shuffling_keeps_the_total_and_changes_only_the_path():
    r = pd.Series([3.0, -1, -1, -1, 5, -1, -1, 2, -1, -1])
    table = J.shuffled(r, trials=200, seed=4)
    assert np.allclose(table["合计"], r.sum())                 # 加法可交换：终点永远一样
    assert table["最深回撤"].nunique() > 1                     # 但路径不一样
    assert (table["最深回撤"] <= 0).all()
    assert table["最长连亏"].max() >= 5                        # 六笔亏损挤到一起是可能的
    with pytest.raises(ValueError):
        J.shuffled([1.0])


def test_normal_range_locates_this_run_in_the_distribution():
    r = pd.Series([2.0, -1, -1, -1, -1, 4, -1, -1, 3, -1])
    table = J.normal_range(r, trials=300, seed=5)
    assert list(table.index) == ["最长连亏", "最深回撤", "最长水下（笔）"]
    assert table.loc["最长连亏", "这一次"] == 4
    assert 0 <= table.loc["最深回撤", "比这一次还难看的比例"] <= 1
    # 回撤那一行的分位是反着数的：99% 分位比 50% 分位更深（更负）
    assert table.loc["最深回撤", "99% 分位"] <= table.loc["最深回撤", "50% 分位"]


def test_detection_size_grows_with_the_square_of_the_noise():
    small = J.detection_size(mean=0.5, std=3.0)
    assert J.detection_size(mean=0.5, std=6.0) == pytest.approx(small * 4)
    assert J.detection_size(mean=1.0, std=3.0) == pytest.approx(small / 4)
    # 只想认出「掉了一半」，需要的笔数是「掉到 0」的四倍
    assert J.detection_size(0.5, 3.0, drop=0.5) == pytest.approx(small * 4)
    with pytest.raises(ValueError):
        J.detection_size(mean=-0.1, std=1.0)


def test_pause_after_losses_skips_exactly_the_right_trades():
    r = [-1.0, -1, 5, -1, -1, 3, 4, -1]
    taken = J.pause_after_losses(r, after=2, pause=2)
    # 前两笔连亏触发规则 → 跳过第 3、4 笔（其中第 3 笔是 +5R，这就是停手的代价）
    assert list(taken) == [True, True, False, False, True, True, True, True]
    assert list(J.pause_after_losses(r, after=2, pause=0)) == [True] * 8
    with pytest.raises(ValueError):
        J.pause_after_losses(r, after=0)


def test_pause_table_accounts_for_every_trade():
    r = pd.Series([-1.0, -1, 5, -1, -1, 3, 4, -1, -1, -1, 6])
    table = J.pause_table(r, afters=(2, 3), pauses=(1, 2))
    assert table.iloc[0]["合计 R"] == pytest.approx(r.sum())
    # 做了的 + 跳过的 = 全部，一笔都不许丢
    assert np.allclose(table["合计 R"] + table["跳过的那些笔"], r.sum())
    assert (table["做了几笔"] <= len(r)).all()


def test_interfere_only_touches_the_trade_after_the_trigger():
    r = [-2.0, 4, -1, 6]
    assert list(J.interfere(r, "skip_after_loss")) == [-2, 0, -1, 0]
    assert list(J.interfere(r, "double_after_loss")) == [-2, 8, -1, 12]
    assert list(J.interfere(r, "half_after_loss")) == [-2, 2, -1, 3]
    assert list(J.interfere(r, "double_after_win")) == [-2, 4, -2, 6]
    # 第一笔永远不变：它前面没有交易
    assert all(J.interfere(r, kind)[0] == -2 for kind in ("double_after_loss", "double_after_win"))
    with pytest.raises(ValueError):
        J.interfere(r, "去掉最差的那笔")


def test_cap_and_widen_are_both_upper_bounds_on_the_damage():
    r = np.array([-2.0, 4, -1, 6, 0.5])
    assert list(J.interfere(r, "cap", 2.0)) == [-2, 2, -1, 2, 0.5]
    assert list(J.interfere(r, "widen", 2.0)) == [-4, 4, -2, 6, 0.5]   # 赚的那几笔一个字不动
    # 两种改法都只会让每一笔变差或者不变，所以算出来的代价是上界
    assert (J.interfere(r, "cap", 2.0) <= r).all()
    assert (J.interfere(r, "widen", 2.0) <= r).all()


def test_entry_rejects_a_stop_on_the_wrong_side():
    ok = dict(time=pd.Timestamp("2024-01-02"), symbol="BTC", plan_entry=100.0,
              plan_stop=95.0, plan_qty=2.0, plan_exit=110.0)
    assert J.Entry(**ok).pnl(planned=True) == pytest.approx(20.0)
    with pytest.raises(ValueError):
        J.Entry(**{**ok, "plan_stop": 105.0})                  # 做多的止损放到了进场价上面
    with pytest.raises(ValueError):
        J.Entry(**{**ok, "plan_qty": 0.0})
    with pytest.raises(ValueError):
        J.Entry(**{**ok, "side": "两边都做"})
    # 做空：止损在上面才对
    short = J.Entry(**{**ok, "side": "short", "plan_stop": 105.0, "plan_exit": 90.0})
    assert short.pnl(planned=True) == pytest.approx(20.0)


def test_journal_counts_the_rows_you_did_not_follow():
    book = J.Journal()
    common = dict(symbol="SPY", plan_entry=100.0, plan_stop=95.0, plan_qty=10.0, plan_exit=110.0)
    book.add(J.Entry(time=pd.Timestamp("2024-01-02"), **common))                    # 完全照做
    book.add(J.Entry(time=pd.Timestamp("2024-02-02"), fill_entry=101.0, **common))  # 买贵了
    book.add(J.Entry(time=pd.Timestamp("2024-03-02"), fill_qty=0.0,
                     basis="我觉得", note="连亏三笔，这次不敢做", **common))          # 干脆没做
    out = book.summary()
    assert out["记了几笔"] == 3 and out["没做"] == 1
    assert out["成交价和计划不一样"] == 1 and out["依据不是规则"] == 1
    assert out["计划盈亏合计"] == pytest.approx(300.0)
    assert out["实际盈亏合计"] == pytest.approx(100.0 + 90.0 + 0.0)
    assert out["差额"] == pytest.approx(-110.0)
    assert list(book.frame().columns)[:3] == ["时间", "标的", "方向"]


def test_reconcile_splits_the_gap_into_pieces_that_add_up_exactly():
    planned = frame([
        [pd.Timestamp("2024-01-01"), "多", 100.0, 110.0, 10.0, 1.0],    # +99
        [pd.Timestamp("2024-02-01"), "空", 200.0, 190.0, 5.0, 2.0],     # +48
        [pd.Timestamp("2024-03-01"), "多", 100.0, 90.0, 4.0, 0.0],      # −40，实盘没做
    ])
    actual = frame([
        [pd.Timestamp("2024-01-01"), "多", 101.0, 109.0, 12.0, 2.0],    # 买贵、走早、做大
        [pd.Timestamp("2024-02-01"), "空", 201.0, 191.0, 5.0, 2.0],
        [pd.Timestamp("2024-04-01"), "多", 100.0, 105.0, 3.0, 0.0],     # 计划里没有
    ])
    out = J.reconcile(planned, actual)
    parts = out["归因"]
    assert parts["实盘 − 回测"] == pytest.approx(50.0)
    assert parts["差额核对"] == pytest.approx(0.0, abs=1e-9)             # 拆得干干净净
    assert parts["漏做"] == pytest.approx(40.0)                          # 躲过一笔亏损，反而是加分项
    assert parts["多做"] == pytest.approx(15.0)
    assert parts["进场滑点"] == pytest.approx(-5.0)
    assert parts["出场滑点"] == pytest.approx(-15.0)
    assert parts["仓位差"] == pytest.approx(16.0)
    assert parts["费用差"] == pytest.approx(-1.0)
    assert len(out["漏做的"]) == 1 and len(out["多做的"]) == 1
    assert out["逐笔"]["这一笔差多少"].sum() == pytest.approx(-5.0)      # 两笔共同的交易差了多少


def test_reconcile_is_exact_on_random_tables():
    # 随机造两张表，六块之和必须永远等于总差额——这是代数恒等式，不是近似
    rng = np.random.default_rng(33)
    days = pd.date_range("2024-01-01", periods=40, freq="D")
    def build(pick):
        return frame([[days[i], "多" if i % 3 else "空", 100 + rng.normal(),
                       100 + rng.normal(0, 5), 1 + rng.random() * 9, rng.random()]
                      for i in pick])
    planned, actual = build(range(0, 30)), build(range(10, 40))
    parts = J.reconcile(planned, actual)["归因"]
    assert parts["差额核对"] == pytest.approx(0.0, abs=1e-9)
    assert parts["合计"] == pytest.approx(parts["实盘 − 回测"])
