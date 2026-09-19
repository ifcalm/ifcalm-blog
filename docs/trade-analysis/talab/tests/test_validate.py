"""talab.validate 的测试（第 30 篇）。"""
import math

import numpy as np
import pandas as pd
import pytest

from talab import validate as V


def make_surface(values) -> pd.DataFrame:
    frame = pd.DataFrame(values, index=[10, 20, 30], columns=[100, 200, 300])
    frame.index.name, frame.columns.name = "快线", "慢线"
    return frame


def test_surface_spreads_a_long_table_into_two_dimensions():
    table = pd.DataFrame({"快线": [20, 10, 20, 10], "慢线": [200, 200, 100, 100],
                          "年化": [0.4, 0.3, 0.2, 0.1]})
    grid = V.surface(table, "快线", "慢线", "年化")
    assert list(grid.index) == [10, 20] and list(grid.columns) == [100, 200]
    assert grid.loc[20, 200] == 0.4 and grid.loc[10, 100] == 0.1


def test_neighbourhood_is_the_ring_around_one_cell():
    grid = make_surface([[0.1, 0.2, 0.3], [0.4, 1.0, 0.5], [0.6, 0.7, 0.8]])
    out = V.neighbourhood(grid, (20, 200))
    assert out["这一格"] == 1.0 and out["邻居数"] == 8
    assert out["邻居中位"] == pytest.approx(0.45)          # 0.1…0.8 去掉中心的中位数
    assert out["邻居最差"] == pytest.approx(0.1)
    assert out["邻居最好"] == pytest.approx(0.8)
    assert out["落差"] == pytest.approx(0.55)
    corner = V.neighbourhood(grid, (10, 100))              # 角上只有三个邻居
    assert corner["邻居数"] == 3


def test_neighbourhood_counts_steps_on_the_grid_not_parameter_distance():
    """参数网格常常不等距（5、10、20、40、60），「走错一步」指的是换成表里相邻的那个值。"""
    frame = pd.DataFrame([[0.0, 0.0, 0.0], [0.0, 1.0, 0.2], [0.0, 0.0, 0.0]],
                         index=[5, 10, 200], columns=[20, 40, 1000])
    out = V.neighbourhood(frame, (10, 40))
    assert out["邻居数"] == 8                               # 值差 960 的那一列也算邻居
    assert out["邻居最好"] == pytest.approx(0.2)


def test_plateaus_ranks_by_the_neighbourhood_not_by_the_cell():
    """一根针（自己高、周围低）要排在一片高地（自己一般、周围都不错）后面。"""
    grid = make_surface([[0.5, 0.5, 0.0], [0.5, 0.5, 0.0], [0.0, 0.0, 9.0]])
    ranked = V.plateaus(grid)
    top = ranked.iloc[0]
    assert (top["快线"], top["慢线"]) != (30, 300)          # 9.0 那根针不是第一
    needle = ranked[(ranked["快线"] == 30) & (ranked["慢线"] == 300)].iloc[0]
    assert needle["这一格"] == 9.0 and needle["落差"] == pytest.approx(9.0)
    assert ranked["邻域中位"].is_monotonic_decreasing


def test_split_index_cuts_in_time_order():
    inside, outside = V.split_index(100, 0.7)
    assert (inside.start, inside.stop) == (0, 70)
    assert (outside.start, outside.stop) == (70, 100)
    with pytest.raises(ValueError):
        V.split_index(100, 1.0)
    with pytest.raises(ValueError):
        V.split_index(3, 0.01)


def test_walk_forward_windows_do_not_overlap_and_cover_in_order():
    splits = V.walk_forward(1000, train=300, test=100)
    assert len(splits) == 7
    tests = [test for _, test in splits]
    assert tests[0].start == 300 and tests[-1].stop == 1000
    for a, b in zip(tests, tests[1:]):
        assert a.stop == b.start                            # 考卷首尾相接、不重叠
    for train, test in splits:
        assert train.stop == test.start and train.stop - train.start == 300
    with pytest.raises(ValueError):
        V.walk_forward(100, train=300, test=100)


def test_walk_forward_anchored_keeps_growing_the_training_window():
    rolling = V.walk_forward(1000, 300, 100, anchored=False)
    anchored = V.walk_forward(1000, 300, 100, anchored=True)
    assert [t for _, t in rolling] == [t for _, t in anchored]        # 考卷完全一样
    assert all(train.start == 0 for train, _ in anchored)
    lengths = [train.stop - train.start for train, _ in anchored]
    assert lengths == sorted(lengths) and lengths[0] == 300 < lengths[-1]


def test_walk_forward_run_picks_the_best_of_the_training_window():
    rng = np.random.default_rng(0)
    returns = rng.normal(0, 0.01, (4, 400))
    returns[1, :200] += 0.05                                # 第 1 列只在前半段好
    returns[2, 200:] += 0.05                                # 第 2 列只在后半段好
    splits = V.walk_forward(400, 200, 200)
    out = V.walk_forward_run(returns, splits, names=list("甲乙丙丁"))
    assert len(out) == 1 and out.loc[0, "选了谁"] == "乙"      # 训练期挑的是乙
    assert out.loc[0, "训练期夏普"] > out.loc[0, "考卷夏普"]    # 考卷上乙已经不行了


def test_stitch_joins_the_test_windows_end_to_end():
    returns = np.arange(30, dtype=float).reshape(3, 10)
    splits = V.walk_forward(10, 4, 3)
    joined = V.stitch(returns, splits, [0, 2])
    assert len(joined) == sum(test.stop - test.start for _, test in splits)
    assert joined[0] == returns[0, splits[0][1].start]
    assert joined[-1] == returns[2, splits[1][1].stop - 1]


def test_expected_max_sharpe_matches_a_simulation():
    """这是整个模块最该钉住的一条：公式算出来的「白捡的最大值」要对得上真的抽一万次。"""
    rng = np.random.default_rng(30)
    for n_trials in (50, 1000, 10_000):
        draws = rng.normal(0.0, 0.3, size=(400, n_trials)).max(axis=1)
        assert V.expected_max_sharpe(n_trials, 0.3) == pytest.approx(draws.mean(), rel=0.05)


def test_expected_max_sharpe_grows_with_trials_and_scales_with_spread():
    assert V.expected_max_sharpe(10, 1.0) < V.expected_max_sharpe(1000, 1.0)
    assert V.expected_max_sharpe(1000, 2.0) == pytest.approx(2 * V.expected_max_sharpe(1000, 1.0))
    with pytest.raises(ValueError):
        V.expected_max_sharpe(1, 1.0)


def test_deflated_sharpe_falls_as_you_admit_more_trials():
    same = dict(sharpe=1.5, n_obs=1000, sharpe_std=0.4, periods_per_year=252)
    few = V.deflated_sharpe(n_trials=2, **same)
    many = V.deflated_sharpe(n_trials=10_000, **same)
    assert few["年化夏普"] == many["年化夏普"] == 1.5          # 夏普一个字没变
    assert few["白捡的门槛（年化）"] < many["白捡的门槛（年化）"]
    assert few["打过折的夏普 DSR"] > many["打过折的夏普 DSR"]
    assert 0 <= many["打过折的夏普 DSR"] <= 1


def test_pbo_is_a_coin_flip_on_pure_noise():
    """一堆互相没区别的随机策略，样本内第一名在样本外就是随机的——PBO 该在 0.5 附近。"""
    returns = np.random.default_rng(1).normal(0.0, 0.01, (100, 800))
    out = V.pbo(returns, 8)
    assert out["一共几种分法"] == 70
    assert out["过拟合概率 PBO"] == pytest.approx(0.5, abs=0.2)


def test_pbo_is_near_zero_when_one_strategy_is_genuinely_better():
    returns = np.random.default_rng(2).normal(0.0, 0.01, (40, 800))
    returns[7] += 0.01                                      # 第 7 列全程真的更好
    out = V.pbo(returns, 8)
    assert out["过拟合概率 PBO"] < 0.05
    assert out["样本外分位中位数"] > 0.9
    with pytest.raises(ValueError):
        V.pbo(returns, 7)                                   # 块数要是偶数


def test_synthetic_close_keeps_the_length_and_the_starting_price():
    close = pd.Series(np.cumprod(1 + np.random.default_rng(3).normal(0, 0.02, 500)) * 100,
                      index=pd.date_range("2020-01-01", periods=500, freq="D"))
    paths = V.synthetic_close(close, n=5, block=20, seed=3)
    assert paths.shape == (5, len(close))
    assert np.allclose(paths[:, 0], float(close.iloc[0]))
    assert not np.allclose(paths[0], close.to_numpy())       # 是新造的，不是原样抄回来
    fast = V.synthetic_close(close, n=3, block=1, seed=3)
    assert fast.shape == (3, len(close))
    with pytest.raises(ValueError):
        V.synthetic_close(close, block=10_000)
