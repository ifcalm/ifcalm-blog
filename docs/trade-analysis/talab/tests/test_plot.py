"""talab.plot 的测试。"""
import math

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")                 # 不弹出窗口

from talab import plot as P


def test_price_to_y_linear_endpoints_and_middle():
    # 价格区间 100～200，画在从像素 20 开始、高 400 的区域里
    assert P.price_to_y(200, 100, 200, 20, 400) == 20            # 最高价在最上面
    assert P.price_to_y(100, 100, 200, 20, 400) == 420           # 最低价在最下面
    assert P.price_to_y(150, 100, 200, 20, 400) == 220           # 算术中点在正中间


def test_price_to_y_log_puts_geometric_mean_in_the_middle():
    mid = math.sqrt(100 * 200)                                    # 141.42
    assert P.price_to_y(mid, 100, 200, 20, 400, log=True) == pytest.approx(220)


def test_log_scale_gives_equal_ratios_equal_distances():
    d1 = P.price_to_y(10, 10, 1000, 0, 300, log=True) - P.price_to_y(20, 10, 1000, 0, 300, log=True)
    d2 = P.price_to_y(100, 10, 1000, 0, 300, log=True) - P.price_to_y(200, 10, 1000, 0, 300, log=True)
    assert d1 == pytest.approx(d2)


def bars():
    idx = pd.date_range("2024-01-01", periods=3, freq="1D", tz="UTC")
    return pd.DataFrame({"open": [10, 12, 11], "high": [13, 13, 12], "low": [9, 10, 10],
                         "close": [12, 11, 11], "volume": [5, 6, 7]}, index=idx, dtype=float)


def test_candles_svg_draws_one_line_and_one_body_per_bar():
    svg = P.candles_svg(bars())
    assert svg.count("<line") == 3
    assert svg.count("<rect") == 3 + 1                            # 3 个实体 + 1 个白色背景


def test_candles_svg_colors_follow_style():
    svg = P.candles_svg(bars(), style="china")
    # 第一根收盘高于开盘，第三根收盘等于开盘（也按阳线画），每根的影线和实体各用一次颜色
    assert svg.count(P.STYLES["china"]["up"]) == 4
    assert svg.count(P.STYLES["china"]["down"]) == 2


def test_plot_candles_log_axis_and_volume():
    fig, ax, av = P.plot_candles(bars(), log=True)
    assert ax.get_yscale() == "log"
    assert len(ax.patches) == 3 and len(av.patches) == 3
