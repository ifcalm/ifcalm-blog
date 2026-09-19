"""talab.backtest 的测试（第 27 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import backtest as BT, indicators as I, rules as R


def series(values, start="2020-01-01"):
    return pd.Series(np.asarray(values, dtype=float),
                     index=pd.date_range(start, periods=len(values), freq="D"))


def flags(n, true_at=(), start="2020-01-01"):
    """长度 n 的布尔序列，只有 true_at 里的位置是 True。"""
    out = np.zeros(n, dtype=bool)
    out[list(true_at)] = True
    return pd.Series(out, index=pd.date_range(start, periods=n, freq="D"))


def bars(close, spread=0.0):
    """一组最简单的 K 线：开盘＝收盘，最高最低按 spread 撑开。"""
    close = series(close)
    return pd.DataFrame({"open": close, "high": close * (1 + spread),
                         "low": close * (1 - spread), "close": close})


def random_walk(n=600, seed=27, scale=0.02):
    rng = np.random.default_rng(seed)
    close = series(100 * np.exp(np.cumsum(rng.standard_normal(n) * scale)))
    return pd.DataFrame({"open": close, "high": close * 1.01, "low": close * 0.99, "close": close})


# ---------------------------------------------------------------------------
# 一、向量化和它的体检
# ---------------------------------------------------------------------------

def test_vectorized_lag_is_the_whole_point():
    """「今天涨了」这个信号，lag=0 时每一根都押中，lag=1 时什么也押不中。"""
    close = series([100, 110, 100, 110, 100, 110, 100])
    up = (close.pct_change() > 0).astype(float)
    assert BT.vectorized(close, up, lag=0).sum() == pytest.approx(up.mul(close.pct_change()).sum())
    assert (BT.vectorized(close, up, lag=0) >= 0).all()          # 偷看未来：一根都不亏
    assert BT.vectorized(close, up, lag=1).min() < 0             # 老老实实：会亏


def test_vectorized_rejects_negative_lag():
    with pytest.raises(ValueError):
        BT.vectorized(series([1.0, 2.0]), series([1.0, 1.0]), lag=-1)


def test_vectorized_charges_the_fee_on_turnover():
    """仓位 0→1→0 收两次费，一直拿着只收进出各一次。"""
    close = series([100.0, 100.0, 100.0, 100.0])
    position = series([1.0, 1.0, 0.0, 0.0])
    charged = -BT.vectorized(close, position, lag=0, fee_rate=0.001).sum()
    assert charged == pytest.approx(0.002)                       # 买一次、卖一次


def test_lag_test_tells_a_peeking_signal_from_a_real_one():
    """偷看未来的信号推迟一根就塌，真信号只是温和变差。"""
    rng = np.random.default_rng(27)
    close = series(100 * np.exp(np.cumsum(rng.standard_normal(800) * 0.01)))
    peeking = (close.pct_change() > 0).astype(float)             # 用当根自己的涨跌当信号
    honest = (close.pct_change().shift(1) > 0).astype(float)     # 用上一根的涨跌当信号
    a = BT.lag_test(close, peeking, lags=(0, 1))
    b = BT.lag_test(close, honest, lags=(0, 1))
    assert a["年化"].iloc[0] > 10 * max(a["年化"].iloc[1], 0.01)  # 塌掉一个数量级
    assert a["持仓根里上涨的比例"].iloc[0] == pytest.approx(1.0)
    assert abs(b["年化"].iloc[0] - b["年化"].iloc[1]) < abs(a["年化"].iloc[0] - a["年化"].iloc[1])


# ---------------------------------------------------------------------------
# 二、盘中路径
# ---------------------------------------------------------------------------

def test_first_touch_is_determined_when_only_one_side_is_hit():
    assert BT.first_touch({"low": 95.0, "high": 101.0}, stop=90.0, target=110.0) == "都没碰到"
    assert BT.first_touch({"low": 89.0, "high": 101.0}, stop=90.0, target=110.0) == "止损"
    assert BT.first_touch({"low": 95.0, "high": 111.0}, stop=90.0, target=110.0) == "止盈"


def test_first_touch_is_an_assumption_when_both_are_hit():
    both = {"low": 89.0, "high": 111.0}
    assert BT.first_touch(both, 90.0, 110.0, "pessimistic") == "止损"
    assert BT.first_touch(both, 90.0, 110.0, "optimistic") == "止盈"
    answers = {BT.first_touch(both, 90.0, 110.0, "coin", np.random.default_rng(seed)) for seed in range(20)}
    assert answers == {"止损", "止盈"}                            # 抛硬币两种都出得来
    with pytest.raises(ValueError):
        BT.first_touch(both, 90.0, 110.0, "coin")                # 没给 rng，结果不可复现
    with pytest.raises(ValueError):
        BT.first_touch(both, 90.0, 110.0, "看心情")


def test_limit_filled_can_require_the_price_to_go_through():
    bar = {"low": 99.9, "high": 100.1}
    assert BT.limit_filled(bar, 100.0, "buy", through=0.0)        # 碰到就算成交
    assert not BT.limit_filled(bar, 100.0, "buy", through=0.005)  # 要穿过 0.5% 才算
    assert BT.limit_filled(bar, 100.0, "sell", through=0.0)
    with pytest.raises(ValueError):
        BT.limit_filled(bar, 100.0, "随便")


# ---------------------------------------------------------------------------
# 三、记账
# ---------------------------------------------------------------------------

def test_account_keeps_cash_plus_position_equal_to_equity():
    account = BT.Account(cash=10_000.0)
    account.buy(price=50.0, shares=100.0)
    assert account.cash == pytest.approx(5_000.0)
    assert account.equity(50.0) == pytest.approx(10_000.0)
    assert account.equity(60.0) == pytest.approx(11_000.0)
    account.sell(price=60.0, shares=100.0)
    assert account.shares == 0.0
    assert account.cash == pytest.approx(11_000.0)


def test_account_fee_eats_into_what_you_can_buy():
    account = BT.Account(cash=10_000.0)
    shares = account.affordable(price=100.0, fee_rate=0.001)
    assert shares == pytest.approx(10_000 / 100.1)                # 不是 100 股
    account.buy(100.0, shares, fee_rate=0.001)
    assert account.cash == pytest.approx(0.0, abs=1e-9)
    assert account.fees == pytest.approx(shares * 100.0 * 0.001)


def test_account_refuses_to_overdraw_or_oversell():
    with pytest.raises(ValueError):
        BT.Account(cash=1_000.0).buy(price=100.0, shares=20.0)
    with pytest.raises(ValueError):
        BT.Account(cash=1_000.0, shares=1.0).sell(price=100.0, shares=2.0)


# ---------------------------------------------------------------------------
# 四、事件驱动
# ---------------------------------------------------------------------------

def test_plan_validates_its_settings():
    entry = flags(2)
    for bad in [dict(fill="随时"), dict(stop="随便"), dict(path="看心情"), dict(sizing="梭哈")]:
        with pytest.raises(ValueError):
            BT.Plan(entry=entry, exit=entry, **bad)
    with pytest.raises(ValueError):
        BT.Plan(entry=entry, exit=entry, stop="none", sizing="risk")
    with pytest.raises(ValueError):
        BT.Plan(entry=entry, exit=entry, trigger="close", target_r=2.0, path="optimistic")
    assert len(BT.Plan(entry=entry, exit=entry).describe()) == 7


def test_run_never_trades_on_the_signal_bar_itself():
    """价格只在第 5 根跳了一下，信号也在第 5 根：正确的引擎一分钱也赚不到。"""
    df = bars([100, 100, 100, 100, 100, 200, 200, 200])
    entry = flags(8, [5])                                         # 跳的那一根收盘才成立
    result = BT.run(df, BT.Plan(entry=entry, exit=flags(8), stop="none"), 1_000.0)
    assert result["资金曲线"].iloc[-1] == pytest.approx(1_000.0)   # 第 6 根开盘买入，价格已经是 200
    assert result["交易"]["买入价"].iloc[0] == pytest.approx(200.0)


def test_run_books_every_bar_exactly():
    df = random_walk()
    entry = (df["close"] >= df["close"].rolling(20).max()).fillna(False)
    exit_ = (df["close"] <= df["close"].rolling(20).min()).fillna(False)
    result = BT.run(df, BT.Plan(entry=entry, exit=exit_, stop="percent", stop_percent=0.10), 100_000.0)
    assert result["记账误差"] == pytest.approx(0.0, abs=1e-9)
    rebuilt = result["现金"] + result["持仓数量"] * df["close"].reindex(result["现金"].index)
    assert (rebuilt - result["资金曲线"]).abs().max() == pytest.approx(0.0, abs=1e-9)


def test_run_agrees_with_the_post21_engine_when_fully_invested():
    """满仓、不收费时，第 27 篇的引擎和第 21 篇的 `rules.run` 必须给出同一条资金曲线。"""
    df = random_walk()
    entry = (df["close"] >= df["close"].rolling(20).max()).fillna(False)
    exit_ = I.cross_below(I.sma(df["close"], 10), I.sma(df["close"], 30)).fillna(False)
    settings = dict(fill="next_open", stop="chandelier", k=3.0, trigger="close")
    old, _, trades = R.run(df, R.Rule(entry=entry, exit=exit_, sizing="full", **settings))
    new = BT.run(df, BT.Plan(entry=entry, exit=exit_, sizing="full", **settings), 1.0)
    assert len(new["交易"]) == len(trades)
    assert ((new["资金曲线"] - (1 + old).cumprod()).abs().max()) < 1e-12


def test_vectorized_and_event_driven_agree_when_there_is_no_stop():
    """没有止损时，仓位就是当根数据的函数，两种写法必须一致。"""
    df = random_walk()
    entry = (df["close"] >= df["close"].rolling(20).max()).fillna(False)
    exit_ = (df["close"] <= df["close"].rolling(20).min()).fillna(False)
    state = pd.Series(np.nan, index=df.index)
    state[entry], state[exit_] = 1.0, 0.0
    vector = (1 + BT.vectorized(df["close"], state.ffill().fillna(0.0), lag=1)).cumprod()
    event = BT.run(df, BT.Plan(entry=entry, exit=exit_, fill="close", stop="none"), 1.0)["资金曲线"]
    assert (event - vector.reindex(event.index)).abs().max() < 1e-12


def test_run_records_the_position_still_open_at_the_end():
    df = bars([100, 101, 102, 103, 104, 105])
    result = BT.run(df, BT.Plan(entry=flags(6, [1]), exit=flags(6), stop="none"), 1_000.0)
    assert result["交易"]["原因"].iloc[-1] == "未平仓"
    assert result["交易"]["卖出日"].iloc[-1] == df.index[-1]


def test_run_fee_only_ever_costs_money():
    df = random_walk()
    entry = (df["close"] >= df["close"].rolling(20).max()).fillna(False)
    exit_ = (df["close"] <= df["close"].rolling(20).min()).fillna(False)
    plan = dict(entry=entry, exit=exit_, stop="percent", stop_percent=0.10)
    curves = [BT.run(df, BT.Plan(fee_rate=fee, **plan), 100_000.0) for fee in [0.0, 0.0005, 0.002]]
    finals = [c["资金曲线"].iloc[-1] for c in curves]
    assert finals[0] > finals[1] > finals[2]
    assert curves[0]["手续费合计"] == 0.0
    assert curves[2]["手续费合计"] > curves[1]["手续费合计"] > 0


def test_run_with_a_coin_path_is_reproducible():
    df = random_walk()
    entry = (df["close"] >= df["close"].rolling(20).max()).fillna(False)
    plan = dict(entry=entry, exit=flags(len(df)), stop="percent", stop_percent=0.005,
                trigger="extreme", target_r=1.0, path="coin")
    first = BT.run(df, BT.Plan(seed=27, **plan), 1.0)["资金曲线"]
    again = BT.run(df, BT.Plan(seed=27, **plan), 1.0)["资金曲线"]
    other = BT.run(df, BT.Plan(seed=99, **plan), 1.0)["资金曲线"]
    assert (first - again).abs().max() == 0.0                     # 同一个种子，同一条曲线
    assert (first - other).abs().max() > 0.0                      # 换个种子就不一样了


def test_optimistic_path_is_never_worse_than_pessimistic():
    df = random_walk()
    entry = (df["close"] >= df["close"].rolling(20).max()).fillna(False)
    plan = dict(entry=entry, exit=flags(len(df)), stop="percent", stop_percent=0.005,
                trigger="extreme", target_r=1.0)
    good = BT.run(df, BT.Plan(path="optimistic", **plan), 1.0)["资金曲线"].iloc[-1]
    bad = BT.run(df, BT.Plan(path="pessimistic", **plan), 1.0)["资金曲线"].iloc[-1]
    assert good > bad


def test_reconcile_reports_zero_for_identical_curves():
    curve = series([1.0, 1.1, 1.05, 1.2])
    table = BT.reconcile({"甲": curve, "乙": curve * 3, "丙": curve * [1, 1, 1, 2]})
    assert table.iloc[0, -1] == pytest.approx(0.0)
    assert table.iloc[1, -1] == pytest.approx(0.0)                # 只差一个倍数，归一之后一样
    assert table.iloc[2, -1] > 0
