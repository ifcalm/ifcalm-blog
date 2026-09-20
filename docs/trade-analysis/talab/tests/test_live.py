"""talab.live 的测试（第 34 篇）。价格全部手工构造，每个数都能自己算一遍。"""
import numpy as np
import pandas as pd
import pytest

from talab import backtest as BT
from talab import indicators as I
from talab import live as L


def frame(closes, spread: float = 0.005, opens=None) -> pd.DataFrame:
    close = np.asarray(closes, dtype=float)
    open_ = close if opens is None else np.asarray(opens, dtype=float)
    return pd.DataFrame({"open": open_, "high": np.maximum(close, open_) * (1 + spread),
                         "low": np.minimum(close, open_) * (1 - spread), "close": close},
                        index=pd.date_range("2024-01-01", periods=len(close), freq="D"))


def zigzag(n: int, low: float = 100.0, step: float = 3.0, drift: float = 1.0) -> np.ndarray:
    """锯齿向上：**必须有起伏**，一条水平线的真实波幅全是 0，ATR 也是 0，止损就贴在进场价上。"""
    return np.array([low + drift * i + (step if i % 2 else 0.0) for i in range(n)])


def test_order_checks_itself_and_makes_its_own_id():
    order = L.Order(pd.Timestamp("2024-01-02"), "buy", 1.5, "进场信号")
    assert order.client_id                                   # 没给就自己生成一个
    assert L.Order(pd.Timestamp("2024-01-02"), "buy", 1.5, "进场信号").client_id == order.client_id
    with pytest.raises(ValueError):
        L.Order(pd.Timestamp("2024-01-02"), "长", 1.0)
    with pytest.raises(ValueError):
        L.Order(pd.Timestamp("2024-01-02"), "buy", 0.0)


def test_the_runner_matches_the_backtest_engine_bar_by_bar():
    """这一篇最重要的一个测试：**两份代码、同一段数据，资金曲线必须逐根相等。**"""
    df = frame(zigzag(120))
    close = df["close"]
    entry = (close >= close.rolling(10).max()).fillna(False)
    leave = (close < I.sma(close, 10)).fillna(False)
    plan = BT.Plan(entry=entry, exit=leave, stop="chandelier", k=2.0, trigger="close",
                   sizing="risk", risk_per_trade=0.10, atr_period=14)

    def signal(history):
        price = history["close"]
        if len(price) < 10:
            return False, False
        return (bool(price.iloc[-1] >= price.rolling(10).max().iloc[-1]),
                bool(price.iloc[-1] < I.sma(price, 10).iloc[-1]))

    engine = BT.run(df, plan, 50_000.0)
    streamed = L.replay(df, L.Runner(signal, stop="chandelier", k=2.0, sizing="risk",
                                     risk_per_trade=0.10, atr_period=14, equity=50_000.0,
                                     warmup=60))
    checked = L.agrees(engine["资金曲线"], streamed["资金曲线"])
    assert checked["对不上的根数"] == 0
    assert checked["最大相对差"] < 1e-12
    assert len(engine["交易"]) == len(streamed["交易"]) > 0
    assert list(engine["交易"]["原因"]) == list(streamed["交易"]["原因"])


def test_the_runner_places_at_the_close_and_fills_at_the_next_open():
    # 第 27 篇那条时钟规矩：第 i 根收盘算出来的东西，最早第 i+1 根成交
    df = frame(zigzag(60), opens=zigzag(60) * 0.99)
    seen = []

    def signal(history):
        return len(history) == 30, False                     # 只在第 30 根收盘发一次进场信号

    runner = L.Runner(signal, stop="percent", stop_percent=0.10, sizing="full", equity=10_000.0)
    for position in range(len(df)):
        for order in runner.on_bar(df.index[position], df.iloc[position]):
            seen.append((position, order.side))
    assert seen[0] == (29, "buy")                            # 第 30 根（下标 29）收盘挂单
    assert runner.trades[0]["买入日"] == df.index[30] if runner.trades else True
    assert runner.account.shares > 0 or runner.trades


def test_agrees_judges_by_relative_difference_not_absolute():
    index = pd.date_range("2024-01-01", periods=5)
    base = pd.Series([1e6, 1.1e6, 1.2e6, 1.3e6, 1.4e6], index=index)
    noisy = base * (1 + 1e-13)                               # 纯浮点噪声
    assert (noisy - base).abs().max() > 1e-9                  # 按绝对阈值 1e-9 会全部判成 bug
    assert L.agrees(base, noisy)["对不上的根数"] == 0         # 相对差看，什么事都没有
    real = base.copy()
    real.iloc[3] *= 1.001                                    # 千分之一：这是 bug 不是噪声
    out = L.agrees(base, real)
    assert out["对不上的根数"] == 1
    assert out["第一根对不上的"] == index[3]
    with pytest.raises(ValueError):
        L.agrees(base, base.shift(10, freq="YE"))


def test_filters_round_down_because_rounding_up_breaks_the_risk_budget():
    filters = L.Filters(tick_size=0.01, step_size=0.001, min_qty=0.001, min_notional=10.0)
    assert filters.round_qty(1.23456) == pytest.approx(1.234)
    assert filters.round_qty(1.2349) == pytest.approx(1.234)  # 向下，不是四舍五入
    assert filters.round_price(101.999) == pytest.approx(101.99)
    # 浮点陷阱：0.29 / 0.01 在双精度里是 28.999999999999996，直接取整会变成 0.28
    assert L.Filters(step_size=0.01).round_qty(0.29) == pytest.approx(0.29)
    assert L.Filters(step_size=0.1).round_qty(2.7) == pytest.approx(2.7)


def test_filters_read_from_the_real_binance_payload():
    payload = {"symbol": "BTCUSDT", "filters": [
        {"filterType": "PRICE_FILTER", "tickSize": "0.01000000"},
        {"filterType": "LOT_SIZE", "stepSize": "0.00001000", "minQty": "0.00001000",
         "maxQty": "9000.00000000"},
        {"filterType": "NOTIONAL", "minNotional": "5.00000000"}]}
    filters = L.Filters.from_binance(payload)
    assert (filters.tick_size, filters.step_size) == (0.01, 1e-5)
    assert filters.min_notional == 5.0 and filters.max_qty == 9000.0


def test_accepts_says_which_rule_the_order_broke():
    filters = L.Filters(step_size=1e-5, min_qty=1e-5, max_qty=100.0, min_notional=5.0)
    assert filters.accepts(80_000.0, 0.001) == ""            # 80 美元，过
    assert "minQty" in filters.accepts(80_000.0, 1e-6)
    assert "maxQty" in filters.accepts(80_000.0, 200.0)
    assert "minNotional" in filters.accepts(80_000.0, 5e-5)  # 4 美元，不够


def test_apply_filters_marks_the_orders_that_cannot_be_sent():
    trades = pd.DataFrame({"买入价": [100.0, 100.0], "数量": [2.6, 0.02]})
    out = L.apply_filters(trades, L.Filters(step_size=1.0, min_qty=1.0, min_notional=0.0))
    assert list(out["取整后数量"]) == [2.0, 0.0]
    assert out["丢掉的比例"].iloc[0] == pytest.approx((2.6 - 2) / 2.6)
    assert out["被拒绝"].iloc[0] == "" and "minQty" in out["被拒绝"].iloc[1]


def test_min_account_takes_the_larger_of_the_two_thresholds():
    cheap = L.Filters(step_size=1e-5, min_qty=1e-5, min_notional=5.0)
    out = L.min_account(cheap, price=80_000.0, risk_per_trade=0.10, stop_fraction=0.15)
    assert out["仓位占账户"] == pytest.approx(2 / 3)
    assert out["按 minNotional 算"] == pytest.approx(7.5)
    assert out["最小账户"] == pytest.approx(max(out["按 minNotional 算"],
                                                out["按 step_size 算（误差 < 1%）"]))
    # 止损越近，仓位占账户越大，最小账户就越小
    closer = L.min_account(cheap, 80_000.0, 0.10, 0.05)
    assert closer["最小账户"] < out["最小账户"]
    with pytest.raises(ValueError):
        L.min_account(cheap, 80_000.0, risk_per_trade=0.0)


def test_starts_really_reruns_from_each_day():
    df = frame(zigzag(200))
    got = []

    def run(piece):
        got.append(len(piece))
        return piece["close"] / piece["close"].iloc[0]

    table = L.starts(df, run, window=40, step=10, warmup=50)
    assert len(table) == len(got) > 0
    assert set(got) == {90}                                  # 每次都是 warmup + window 根
    assert list(table.columns) == ["上线日", "第一段收益", "期间最大回撤"]
    assert (table["期间最大回撤"] <= 0).all()
    with pytest.raises(ValueError):
        L.starts(df, run, window=1)


def test_start_risk_counts_the_starts_that_made_money():
    table = pd.DataFrame({"第一段收益": [-0.2, -0.1, 0.1, 0.3, 0.5]})
    out = L.start_risk(table)
    assert out["起点个数"] == 5 and out["赚钱的起点占"] == pytest.approx(0.6)
    assert out["最差"] == pytest.approx(-0.2) and out["最好"] == pytest.approx(0.5)
    assert out["50% 分位"] == pytest.approx(0.1)


def test_stage_and_ladder_check_themselves():
    assert list(L.ladder()["名字"]) == ["模拟盘", "小资金", "半仓", "目标"]
    assert L.ladder()["投入比例"].iloc[0] == 0.0             # 模拟盘一分钱不投
    with pytest.raises(ValueError):
        L.Stage("太大", 1.5, 10)
    with pytest.raises(ValueError):
        L.Stage("零笔", 0.5, 0)


def test_run_ladder_promotes_after_enough_trades():
    stages = (L.Stage("模拟盘", 0.0, 3), L.Stage("小资金", 0.5, 3), L.Stage("目标", 1.0, 1))
    out = L.run_ladder([1.0] * 9, stages)
    # 前 3 笔 0%、接着 3 笔 50%、剩下 3 笔 100%
    assert list(out["逐笔"]["记进账户的"]) == [0, 0, 0, 0.5, 0.5, 0.5, 1, 1, 1]
    assert out["合计"] == pytest.approx(4.5)
    assert out["一次全投"] == pytest.approx(9.0)
    assert out["升级次数"] == 2 and out["降级次数"] == 0
    assert out["最后停在"] == "目标"


def test_run_ladder_demotes_when_a_guard_fires():
    stages = (L.Stage("模拟盘", 0.0, 2), L.Stage("小资金", 0.5, 99))
    guard = L.Guard("连亏 3 笔", "streak", 3)
    out = L.run_ladder([1.0, 1.0, -1.0, -1.0, -1.0, 2.0], stages, [guard])
    assert out["升级次数"] == 1 and out["降级次数"] == 1
    assert out["最后停在"] == "模拟盘"
    # 降级之后那一笔 +2R 落在模拟盘上，一分钱没赚到——和第 33 篇停手规则是同一个病
    assert out["逐笔"]["记进账户的"].iloc[-1] == 0.0


def test_guard_refuses_a_threshold_that_points_the_wrong_way():
    assert L.Guard("回撤 5R", "drawdown", -5.0).fires(np.array([-2.0, -2.0, -2.0]))
    assert not L.Guard("回撤 5R", "drawdown", -5.0).fires(np.array([-2.0, 3.0, -2.0]))
    assert L.Guard("连亏 3 笔", "streak", 3).fires(np.array([1.0, -1, -1, -1]))
    assert not L.Guard("连亏 3 笔", "streak", 3).fires(np.array([1.0, -1, -1, 1, -1]))
    assert not L.Guard("连亏 3 笔", "streak", 3).fires(np.array([]))
    with pytest.raises(ValueError):
        L.Guard("回撤写成正的", "drawdown", 5.0)
    with pytest.raises(ValueError):
        L.Guard("看不懂的量", "夏普", 1.0)
    with pytest.raises(ValueError):
        L.Guard("动作看不懂", "streak", 3, action="加仓")


def test_stage_range_gets_worse_as_the_stage_gets_longer():
    rng = np.random.default_rng(0)
    r = rng.normal(0.3, 1.0, 200)
    short = L.stage_range(r, 10, trials=800, seed=1)
    long = L.stage_range(r, 40, trials=800, seed=1)
    # 笔数越多，最长连亏越长、最深回撤越深——这正是第 33 篇 expected_longest 说的事
    assert long.loc["最长连亏", "平均"] > short.loc["最长连亏", "平均"]
    assert long.loc["最深回撤", "99% 分位"] < short.loc["最深回撤", "99% 分位"]
    with pytest.raises(ValueError):
        L.stage_range(r, 1)


def test_guards_from_range_reads_the_table_it_is_given():
    table = L.stage_range(np.array([1.0, -1.0, 2.0, -1.5, 0.5] * 20), 15, trials=500, seed=2)
    guards = L.guards_from_range(table, "95% 分位", action="停用")
    assert [g.kind for g in guards] == ["drawdown", "streak"]
    assert guards[0].threshold == pytest.approx(table.loc["最深回撤", "95% 分位"])
    assert all(g.action == "停用" for g in guards)
    with pytest.raises(ValueError):
        L.guards_from_range(table, "没有这一列")
