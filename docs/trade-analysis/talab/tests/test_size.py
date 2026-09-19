"""talab.size 的测试（第 26 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import rules as R, size as Z


def trades(rows):
    """(买入价, 初始止损, 卖出价) 三元组拼成 `risk.run` 那样的交易表。"""
    days = pd.date_range("2020-10-10", periods=len(rows), freq="30D", tz="UTC")
    return pd.DataFrame({"买入日": days, "卖出日": days + pd.Timedelta("20D"),
                         "买入价": [r[0] for r in rows], "初始止损": [r[1] for r in rows],
                         "卖出价": [r[2] for r in rows]})


def test_position_size_loses_exactly_the_risk_budget():
    """账户 10 万、止损距离 3%、一笔最多亏 1%：买 33,333 美元，止损时正好亏 1,000。"""
    plan = Z.position_size(100_000, 0.03, 0.01, price=200.0)
    assert plan["仓位金额"] == pytest.approx(100_000 * 0.01 / 0.03)
    assert plan["止损时亏"] == pytest.approx(1_000.0)
    assert plan["数量"] == pytest.approx(plan["仓位金额"] / 200.0)
    assert not plan["有没有封顶"]


def test_position_size_caps_the_notional_and_says_so():
    """止损距离只有 0.5% 时，1% 的风险要求两倍杠杆；封顶之后实际风险只有一半。"""
    plan = Z.position_size(100_000, 0.005, 0.01)
    assert plan["占账户"] == pytest.approx(1.0)
    assert plan["实际风险"] == pytest.approx(0.005)
    assert plan["有没有封顶"]
    assert Z.position_size(100_000, 0.005, 0.01, max_fraction=3.0)["占账户"] == pytest.approx(2.0)


def test_position_size_rejects_impossible_inputs():
    with pytest.raises(ValueError):
        Z.position_size(100_000, 0.03, risk_fraction=1.5)
    with pytest.raises(ValueError):
        Z.position_size(100_000, distance=0.0)
    with pytest.raises(ValueError):
        Z.stop_distance(100.0, 120.0)                       # 止损价在进场价上方


def test_size_by_atr_is_the_same_formula_as_position_size():
    """3 倍 ATR 的止损，按 ATR 调仓和按止损距离调仓必须给出同一个数。"""
    price, atr = 11_050.64, 308.07
    by_atr = Z.size_by_atr(100_000, atr, price, risk_fraction=0.01, k=3.0)
    by_distance = Z.position_size(100_000, 3 * atr / price, 0.01, price)
    assert by_atr["仓位金额"] == pytest.approx(by_distance["仓位金额"])
    doubled = Z.size_by_atr(100_000, 2 * atr, price, risk_fraction=0.01, k=3.0)
    assert doubled["仓位金额"] == pytest.approx(by_atr["仓位金额"] / 2)      # ATR 翻倍，仓位减半


def test_simulate_fixed_risk_loses_the_same_percentage_every_time():
    """止损距离差三倍的两笔亏损交易，按固定风险下注时亏掉的账户比例一样。"""
    table = Z.simulate(trades([(100.0, 97.0, 97.0), (100.0, 91.0, 91.0)]), "risk", risk=0.01)
    assert list(table["盈亏占账户"].round(10)) == [-0.01, -0.01]
    assert table["占账户"].iloc[0] == pytest.approx(1 / 3)
    assert table["占账户"].iloc[1] == pytest.approx(1 / 9)


def test_simulate_full_lets_the_market_pick_the_loss():
    """同样两笔，满仓时亏掉的是止损距离本身——3% 和 9%，你没有选择权。"""
    table = Z.simulate(trades([(100.0, 97.0, 97.0), (100.0, 91.0, 91.0)]), "full")
    assert list(table["盈亏占账户"].round(10)) == [-0.03, -0.09]


def test_simulate_fixed_amount_does_not_compound():
    """固定金额：账户翻了一倍，下一笔还是买一样多的钱。"""
    table = Z.simulate(trades([(100.0, 90.0, 200.0), (100.0, 90.0, 200.0)]), "amount", amount=10_000.0)
    assert list(table["仓位金额"]) == [10_000.0, 10_000.0]
    assert list(table["账户"]) == [110_000.0, 120_000.0]
    fraction = Z.simulate(trades([(100.0, 90.0, 200.0), (100.0, 90.0, 200.0)]), "fraction", fraction=0.1)
    assert list(fraction["账户"]) == [110_000.0, 121_000.0]        # 固定比例会复利


def test_simulate_rejects_unknown_methods():
    with pytest.raises(ValueError):
        Z.simulate(trades([(100.0, 90.0, 110.0)]), method="拍脑袋")


def test_recovery_is_asymmetric():
    assert Z.recovery(0.5) == pytest.approx(1.0)                   # 亏一半要翻倍
    assert Z.recovery(0.1) == pytest.approx(0.1 / 0.9)
    assert list(np.round(Z.recovery([0.2, 0.8]), 4)) == [0.25, 4.0]
    with pytest.raises(ValueError):
        Z.recovery(1.0)                                            # 亏光了回不来


def test_underwater_finds_the_segments_and_the_last_one_unfinished():
    equity = pd.Series([1.0, 0.8, 0.9, 1.1, 0.9],
                       index=pd.date_range("2020-01-01", periods=5, freq="D"))
    table = Z.underwater(equity)
    assert len(table) == 2
    assert table["最深"].iloc[0] == pytest.approx(-0.2)
    assert table["天数"].iloc[0] == 2                              # 01-02 跌破，01-04 创新高
    assert table["结束"].iloc[-1] == equity.index[-1]              # 最后一段还在水下
    assert table["要涨回来"].iloc[0] == pytest.approx(0.25)


def test_kelly_matches_the_textbook_coin_flip():
    """赔率 2 比 1、胜率 60% 的抛硬币，凯利说押四成。"""
    assert Z.kelly(0.6, 2.0) == pytest.approx(0.6 - 0.4 / 2.0)
    assert Z.kelly(0.5, 1.0) == pytest.approx(0.0)                 # 没有优势就不该下注
    assert Z.kelly(0.4, 1.0) < 0                                   # 负优势：反着下才对
    with pytest.raises(ValueError):
        Z.kelly(1.2, 2.0)


def test_optimal_f_agrees_with_kelly_on_a_two_point_bet():
    """只有两种结果时，网格搜出来的最优下注比例要和公式对得上。"""
    r = np.array([2.0] * 60 + [-1.0] * 40)                         # 胜率 60%，赢 2 份输 1 份
    assert Z.optimal_f(r) == pytest.approx(Z.kelly(0.6, 2.0), abs=0.005)
    assert Z.growth_rate(r, Z.optimal_f(r)) > Z.growth_rate(r, 0.9)


def test_growth_rate_is_minus_infinity_when_a_bet_wipes_you_out():
    assert Z.growth_rate([0.5, -1.0], 1.0) == -np.inf              # 亏满 1 倍＝账户归零
    assert np.isfinite(Z.growth_rate([0.5, -1.0], 0.5))


def test_vol_target_hits_the_target_and_uses_only_the_past():
    rng = np.random.default_rng(26)
    r = pd.Series(rng.standard_normal(3_000) * 0.01,
                  index=pd.date_range("2016-01-01", periods=3_000, freq="D"))
    position = Z.vol_target(r, target=0.15, lookback=60, periods_per_year=365)
    assert (position * r).std() * np.sqrt(365) == pytest.approx(0.15, rel=0.1)
    spike = r.copy()
    spike.iloc[100] = 10.0                                          # 只改第 100 天
    assert Z.vol_target(spike, 0.15, 60, 365).iloc[100] == position.iloc[100]   # 当天的仓位不受影响
    assert Z.vol_target(spike, 0.15, 60, 365).iloc[101] != position.iloc[101]   # 第二天才反应


def test_portfolio_risk_does_not_add_up():
    """五笔各 1%：完全独立时合计 2.24%，两两相关 0.6 时 4.12%，完全一样时 5%。"""
    assert Z.combined_risk(5, 0.01, 0.0) == pytest.approx(0.01 * np.sqrt(5))
    assert Z.combined_risk(5, 0.01, 0.6) == pytest.approx(0.0412, abs=1e-4)
    assert Z.combined_risk(5, 0.01, 1.0) == pytest.approx(0.05)
    with pytest.raises(ValueError):
        Z.combined_risk(5, 0.01, -0.5)
    corr = np.full((5, 5), 0.6) + np.eye(5) * 0.4
    assert Z.portfolio_vol(np.ones(5) * 0.01, np.ones(5), corr) == pytest.approx(Z.combined_risk(5, 0.01, 0.6))


def test_effective_bets_counts_what_you_actually_hold():
    assert Z.effective_bets(np.ones(5) / 5, np.eye(5)) == pytest.approx(5.0)
    assert Z.effective_bets(np.ones(5) / 5, np.ones((5, 5))) == pytest.approx(1.0)
    corr = np.full((5, 5), 0.6) + np.eye(5) * 0.4
    assert Z.effective_bets(np.ones(5) / 5, corr) == pytest.approx(1 / 0.68, abs=1e-6)


def test_inverse_vol_weights_give_each_leg_the_same_risk():
    w = Z.inverse_vol_weights([0.10, 0.20, 0.40])
    assert w.sum() == pytest.approx(1.0)
    contributions = w * np.array([0.10, 0.20, 0.40])
    assert contributions.std() == pytest.approx(0.0, abs=1e-12)     # 每份贡献的风险相等
    with pytest.raises(ValueError):
        Z.inverse_vol_weights([0.1, 0.0])


def test_size_agrees_with_the_mainline_strategy_sizing():
    """和第 21 篇的 `rules.run(sizing="risk")` 对账：同一笔交易算出的仓位必须一样。"""
    rng = np.random.default_rng(26)
    close = pd.Series(100 * np.exp(np.cumsum(rng.standard_normal(600) * 0.02)),
                      index=pd.date_range("2020-01-01", periods=600, freq="D"))
    df = pd.DataFrame({"open": close, "high": close * 1.01, "low": close * 0.99, "close": close})
    entry = pd.Series(False, index=df.index)
    entry.iloc[299] = True
    rule = R.Rule(entry=entry, exit=pd.Series(False, index=df.index), stop="percent",
                  stop_percent=0.08, sizing="risk", risk_per_trade=0.01)
    _, held, table = R.run(df, rule)
    assert held.iloc[300] == pytest.approx(Z.position_size(1.0, 0.08, 0.01)["占账户"])
    assert table["仓位"].iloc[0] == pytest.approx(0.125)
