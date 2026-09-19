"""talab.orders 的测试（第 22 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import orders as O


def bars(rows):
    """rows 是 (open, high, low, close) 的列表，索引是连续的分钟。"""
    index = pd.date_range("2024-04-13 20:00", periods=len(rows), freq="min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=index, dtype=float)


PATH = bars([(100, 101, 99.5, 100.5),        # 0
             (100.5, 100.8, 97.0, 98.0),     # 1：跌破 99
             (98.0, 98.5, 94.0, 94.5),       # 2：继续跌
             (94.5, 99.5, 94.0, 99.0),       # 3：反弹回 99.5
             (99.0, 103.0, 98.5, 102.0)])    # 4


def test_touched_uses_the_right_side():
    assert O.touched(PATH, 99.0, "sell") == PATH.index[1]
    assert O.touched(PATH, 102.5, "buy") == PATH.index[4]
    assert O.touched(PATH, 50.0, "sell") is None                    # 从没碰到
    with pytest.raises(ValueError):
        O.touched(PATH, 99.0, "做多")


def test_touched_can_use_another_price_series():
    mark = PATH.copy()
    mark["low"] = [99.5, 99.2, 95.0, 95.0, 99.0]                    # 标记价格没跌到 99
    assert O.touched(PATH, 99.0, "sell") == PATH.index[1]           # 最新价第 2 根就触发
    assert O.touched(PATH, 99.0, "sell", prices=mark) == PATH.index[2]   # 标记价格晚一根


def test_stop_market_fill_prices_by_hand():
    at_trigger = O.stop_market_fill(PATH, 99.0, fill="trigger")
    assert at_trigger["成交价"] == 99.0 and at_trigger["滑点"] == 0    # 回测的乐观假设
    at_close = O.stop_market_fill(PATH, 99.0, fill="bar_close")
    assert at_close["成交价"] == 98.0 and at_close["滑点"] == pytest.approx((99 - 98) / 99)
    worst = O.stop_market_fill(PATH, 99.0, fill="worst")
    assert worst["成交价"] == 97.0                                   # 触发那根的最低价
    next_open = O.stop_market_fill(PATH, 99.0)                       # 默认口径：下一根开盘
    assert next_open["成交价"] == 98.0 and next_open["成交时间"] == PATH.index[2]


def test_stop_market_fill_for_buy_side():
    out = O.stop_market_fill(PATH, 102.5, side="buy", fill="worst")
    assert out["触发时间"] == PATH.index[4] and out["成交价"] == 103.0
    assert out["滑点"] == pytest.approx((103 - 102.5) / 102.5)       # 买入止损成交得更高才算不利


def test_limit_fill_can_miss():
    filled = O.limit_fill(PATH, 95.0, side="buy")
    assert filled["成交"] and filled["成交时间"] == PATH.index[2] and filled["成交价"] == 95.0
    assert not O.limit_fill(PATH, 90.0, side="buy")["成交"]          # 价格没跌到，这张单一直挂着
    assert not O.limit_fill(PATH, 95.0, side="buy", expire=2)["成交"]   # 只挂两根就撤了
    gapped = bars([(100, 100, 100, 100), (94, 95, 93, 94)])
    assert O.limit_fill(gapped, 95.0, side="buy")["成交价"] == 94.0  # 开盘就在限价下方，按开盘价成交


def test_stop_limit_may_never_fill():
    ok = O.stop_limit_fill(PATH, 99.0, 98.5)                         # 第 2 根触发，从第 3 根开始找成交机会
    assert ok["成交"] and ok["成交时间"] == PATH.index[2]            # 第 3 根最高 98.5，正好够到限价
    assert ok["成交价"] == 98.5
    missed = O.stop_limit_fill(bars([(100, 101, 99.5, 100.5), (99.4, 99.4, 90.0, 90.5),
                                     (90.5, 91.0, 85.0, 85.5)]), 99.0, 98.5)
    assert missed["触发时间"] is not None and not missed["成交"]     # 触发了，但价格再没回到 98.5
    assert np.isnan(missed["成交价"])                                 # 仓位还在，这才是止损限价单的风险


def test_oco_first_by_hand():
    assert O.oco_first(PATH, 95.0, 103.0)["结果"] == "先到止损"
    assert O.oco_first(PATH, 90.0, 103.0)["结果"] == "先到目标"
    assert O.oco_first(PATH, 90.0, 110.0)["结果"] == "都没碰到"
    assert O.oco_first(PATH, 99.5, 100.8)["结果"] == "同一根"        # 第 2 根里两个价位都碰到了
    mark = PATH.copy()
    mark["low"] = [99.5, 99.2, 95.5, 95.5, 99.0]
    assert O.oco_first(PATH, 95.0, 103.0, prices=mark)["结果"] == "先到目标"   # 换标记价格，结论反过来
