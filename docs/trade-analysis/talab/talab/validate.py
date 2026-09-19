"""talab.validate：过拟合与样本外检验。第 30 篇。

第 27 篇保证引擎对、第 28 篇保证数据干净、第 29 篇保证读数不被自己骗。
这个模块回答最后一个也是最难的问题：**这条策略是学会了，还是把答案背下来了。**

难在哪里：**样本内的成绩永远可以做到任意好。**参数多试几组、规则多加几条，
回测收益一定上升——上升本身不携带任何信息。所以这里的每一个函数都不是在「算成绩」，
而是在**给成绩打折**：

1. **参数曲面**（`surface`、`neighbourhood`、`plateaus`）：这一格好，是因为它周围一片都好，
   还是因为它自己恰好踩中了？后者叫尖峰，它在样本外几乎必然塌。
2. **切分**（`split_index`、`walk_forward`、`walk_forward_run`）：拿一段没看过的数据当考卷。
3. **多重检验**（`expected_max_sharpe`、`deflated_sharpe`）：你试了一万次，
   「最好的那次」本来就该很好看——先把这个白捡的部分减掉。
4. **回测过拟合概率**（`pbo`）：把时间切成块，反复交换样本内外，
   数一数「样本内第一名在样本外落到中位数以下」的比例。
"""
from __future__ import annotations

import itertools
import math
from statistics import NormalDist

import numpy as np
import pandas as pd

NORMAL = NormalDist()
EULER = 0.5772156649015329                       # 欧拉常数，`expected_max_sharpe` 要用


# ---------------------------------------------------------------------------
# 一、参数曲面：平原还是尖峰
# ---------------------------------------------------------------------------

def surface(table: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    """把「一行一组参数」的长表摊成二维曲面，行列都是参数值。

    摊成二维之后才能问「这一格的邻居怎么样」——而那正是这一篇的核心问题。
    """
    return table.pivot(index=index, columns=columns, values=values).sort_index().sort_index(axis=1)


def neighbourhood(grid: pd.DataFrame, cell: tuple, radius: int = 1) -> pd.Series:
    """一格和它周围一圈的成绩：本格、邻居的中位数 / 最差 / 最好，以及落差。

    `落差` = 本格 − 邻居中位数。它是这一篇最省事的过拟合警报：
    **落差越大，说明这一格越像是踩中的，而不是踩在一片实地上。**

    ⚠️ 邻居按**网格上的位置**算，不按参数值相差多少。参数网格常常不是等距的
    （5、10、20、40、60 这种），这时候「走错一步」的正确含义是「换成表里相邻的那个值」，
    不是「加一减一」。
    """
    row, column = cell
    i, j = grid.index.get_loc(row), grid.columns.get_loc(column)
    block = grid.iloc[max(i - radius, 0):i + radius + 1, max(j - radius, 0):j + radius + 1]
    here = float(grid.iloc[i, j])
    others = block.to_numpy(float).ravel()
    others = np.delete(others, list(block.index).index(row) * block.shape[1]
                       + list(block.columns).index(column))
    others = others[~np.isnan(others)]
    if not len(others):
        raise ValueError("这一格周围没有有效的邻居")
    return pd.Series({"这一格": here, "邻居数": float(len(others)),
                      "邻居中位": float(np.median(others)), "邻居最差": float(others.min()),
                      "邻居最好": float(others.max()), "落差": here - float(np.median(others))})


def plateaus(grid: pd.DataFrame, radius: int = 1) -> pd.DataFrame:
    """给每一格配上它邻域的中位数，按**邻域中位数**从高到低排序。

    这是「不挑尖峰」的选参数方法：不要问「哪一格最高」，要问
    **「哪一片地最高」**——站在一片高地上，走错一步还在高地上。
    """
    rows = []
    for row in grid.index:
        for column in grid.columns:
            if np.isnan(grid.loc[row, column]):
                continue
            stats = neighbourhood(grid, (row, column), radius)
            rows.append({grid.index.name or "行": row, grid.columns.name or "列": column,
                         "这一格": stats["这一格"], "邻域中位": stats["邻居中位"],
                         "落差": stats["落差"]})
    return pd.DataFrame(rows).sort_values("邻域中位", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 二、切分：样本内、样本外、walk-forward
# ---------------------------------------------------------------------------

def split_index(n: int, fraction: float = 0.5) -> tuple[slice, slice]:
    """把 n 根 K 线按时间顺序切成前后两段：前面选参数，后面当考卷。

    ⚠️ 只能按**时间顺序**切。随机抽一半当样本外是错的——
    相邻两天的行情高度相关，随机抽等于让考卷和复习资料互相抄。
    """
    if not 0 < fraction < 1:
        raise ValueError("fraction 要在 0 和 1 之间")
    cut = int(n * fraction)
    if cut < 1 or cut >= n:
        raise ValueError("切出来的两段都要至少有一根")
    return slice(0, cut), slice(cut, n)


def walk_forward(n: int, train: int, test: int, anchored: bool = False) -> list[tuple[slice, slice]]:
    """滚动检验的切分：每一段用前 `train` 根挑参数，紧接着的 `test` 根拿来考试。

    - `anchored=False`（默认）：训练窗口长度固定，整段往前滚
    - `anchored=True`：训练窗口从第一根开始，越考越长（更像真实的积累过程）

    各段的考卷首尾相接、互不重叠，把它们拼起来就是一条**每一根都没被看过**的资金曲线。
    """
    if train < 1 or test < 1:
        raise ValueError("train 和 test 都要至少是 1")
    out, start = [], 0
    while start + train + test <= n:
        out.append((slice(0 if anchored else start, start + train),
                    slice(start + train, start + train + test)))
        start += test
    if not out:
        raise ValueError(f"{n} 根放不下一次 {train}+{test} 的切分")
    return out


def walk_forward_run(returns: np.ndarray, splits, names=None, min_bars: int = 2) -> pd.DataFrame:
    """在每一段上选出训练期里夏普最高的那一列，记下它在考卷上的表现。

    `returns` 是 `(试验数, 根数)` 的每根收益矩阵——一行一组参数。
    返回一张表：每一段选了谁、训练期分数、考卷分数，以及**这一段的考卷收益**。
    """
    rows = []
    for k, (train, test) in enumerate(splits):
        inside, outside = returns[:, train], returns[:, test]
        if inside.shape[1] < min_bars or outside.shape[1] < min_bars:
            raise ValueError("某一段太短，算不出标准差")
        score = inside.mean(axis=1) / np.where(inside.std(axis=1) > 0, inside.std(axis=1), np.nan)
        pick = int(np.nanargmax(score))
        rows.append({"第几段": k + 1, "选了谁": names[pick] if names is not None else pick,
                     "训练期夏普": float(score[pick]),
                     "考卷夏普": float(outside[pick].mean() / outside[pick].std()),
                     "考卷收益": float(np.prod(1 + outside[pick]) - 1),
                     "训练根数": inside.shape[1], "考卷根数": outside.shape[1]})
    return pd.DataFrame(rows)


def stitch(returns: np.ndarray, splits, picks) -> np.ndarray:
    """把各段考卷上被选中那一列的收益首尾接起来，得到一条完整的样本外收益序列。"""
    return np.concatenate([returns[int(p), test] for (_, test), p in zip(splits, picks)])


# ---------------------------------------------------------------------------
# 三、多重检验：你试了多少次
# ---------------------------------------------------------------------------

def expected_max_sharpe(n_trials: int, sharpe_std: float) -> float:
    """**完全没有本事**的情况下，试 `n_trials` 次，「最好的那次」夏普期望是多少
    （Bailey & López de Prado 2014）：

    > E[最大值] ≈ 标准差 × [(1 − γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e))]

    γ 是欧拉常数 0.5772。`sharpe_std` 是这一万次试验的夏普比率**彼此之间**的标准差。
    直觉：N 越大，最大值越往右跑——**「我试了一万组，最好的那组夏普 1.5」这句话里，
    「一万组」和「1.5」一样重要。**
    """
    if n_trials < 2:
        raise ValueError("至少要有两次试验")
    high = NORMAL.inv_cdf(1 - 1 / n_trials)
    low = NORMAL.inv_cdf(1 - 1 / (n_trials * math.e))
    return sharpe_std * ((1 - EULER) * high + EULER * low)


def deflated_sharpe(sharpe: float, n_trials: int, n_obs: int, sharpe_std: float,
                    skew: float = 0.0, kurtosis: float = 3.0,
                    periods_per_year: int = 252) -> pd.Series:
    """打过折的夏普比率（DSR）：把「试了很多次」和「收益率不是正态」都扣掉之后，
    这条策略的夏普**真的大于 0** 的概率。

    两步：先用 `expected_max_sharpe` 算出「没本事时白捡的那一截」当作门槛，
    再问「观察到的夏普超过这个门槛」有多显著：

    > DSR = Φ( (夏普 − 门槛) × √(根数 − 1) ÷ √(1 − 偏度×夏普 + (峰度−1)/4 × 夏普²) )

    式子里的夏普都是**单根**的（不年化）。`kurtosis` 传的是原始峰度（正态是 3），
    不是超额峰度。DSR 低于 0.95 就该当成「还没排除运气」。
    """
    per_period = sharpe / math.sqrt(periods_per_year)
    threshold = expected_max_sharpe(n_trials, sharpe_std / math.sqrt(periods_per_year))
    spread = math.sqrt(max(1 - skew * per_period + (kurtosis - 1) / 4 * per_period ** 2, 1e-12))
    z = (per_period - threshold) * math.sqrt(max(n_obs - 1, 1)) / spread
    return pd.Series({"年化夏普": sharpe, "试验次数": float(n_trials),
                      "白捡的门槛（年化）": threshold * math.sqrt(periods_per_year),
                      "超过门槛多少": sharpe - threshold * math.sqrt(periods_per_year),
                      "t 值": z, "打过折的夏普 DSR": NORMAL.cdf(z)})


# ---------------------------------------------------------------------------
# 四、回测过拟合概率（CSCV）
# ---------------------------------------------------------------------------

def pbo(returns: np.ndarray, n_chunks: int = 8) -> pd.Series:
    """回测过拟合概率（Bailey 等 2017 的 CSCV）。

    做法：把时间切成 `n_chunks` 块，穷举所有「一半当样本内、另一半当样本外」的分法；
    每一种分法里选出样本内夏普最高的那一列，看它**在样本外排第几**。
    如果这个第一名在样本外经常掉到中位数以下，说明「挑第一名」这个动作本身就是在挑噪声。

    > PBO = 样本内第一名在样本外掉到中位数以下的分法比例

    ⚠️ 它衡量的是**挑选流程**，不是某一组参数。PBO 高不代表这些参数都没用，
    代表「用样本内最优去选参数」这件事在这批数据上不管用。
    n_chunks 要是偶数；16 块有 12,870 种分法，8 块只有 70 种，慢和稳之间自己选。
    """
    if n_chunks % 2 or n_chunks < 4:
        raise ValueError("n_chunks 要是不小于 4 的偶数")
    n_trials, n_bars = returns.shape
    if n_trials < 2:
        raise ValueError("至少要有两列试验")
    edges = np.linspace(0, n_bars, n_chunks + 1).astype(int)
    counts = np.diff(edges).astype(float)
    total = np.array([returns[:, edges[i]:edges[i + 1]].sum(axis=1) for i in range(n_chunks)])
    square = np.array([(returns[:, edges[i]:edges[i + 1]] ** 2).sum(axis=1) for i in range(n_chunks)])

    def score(keys) -> np.ndarray:                 # 任意几块合起来的夏普，O(试验数)
        n = counts[list(keys)].sum()
        mean = total[list(keys)].sum(axis=0) / n
        var = square[list(keys)].sum(axis=0) / n - mean ** 2
        return mean / np.sqrt(np.maximum(var, 1e-300))

    logits, ranks = [], []
    everything = range(n_chunks)
    for inside in itertools.combinations(everything, n_chunks // 2):
        outside = tuple(k for k in everything if k not in inside)
        best = int(np.argmax(score(inside)))
        outside_score = score(outside)
        rank = int((outside_score < outside_score[best]).sum()) + 1      # 1 最差，n_trials 最好
        omega = rank / (n_trials + 1)
        ranks.append(omega)
        logits.append(math.log(omega / (1 - omega)))
    logits = np.array(logits)
    return pd.Series({"试验次数": float(n_trials), "切成几块": float(n_chunks),
                      "一共几种分法": float(len(logits)),
                      "样本外分位中位数": float(np.median(ranks)),
                      "过拟合概率 PBO": float((logits <= 0).mean()),
                      "logit 中位数": float(np.median(logits))})


# ---------------------------------------------------------------------------
# 五、蒙特卡洛：如果这个市场本来就没有规律
# ---------------------------------------------------------------------------

def synthetic_close(close: pd.Series, n: int = 100, block: int = 1, seed: int = 0) -> np.ndarray:
    """造 n 条「和原序列同分布、但没有原来那段走势」的假价格，返回 `(n, 根数)`。

    `block=1` 是把日收益率完全打散（波动率聚集也一起没了）；
    `block > 1` 用块自助法，保留每一小段内部的顺序，**波动率聚集还在，趋势没了**。
    拿这些假价格重跑一遍同样的参数扫描，就知道「最好的一组」里有多少是白捡的。
    """
    values = close.pct_change().dropna().to_numpy(float)
    m = len(values)
    if block < 1 or block > m:
        raise ValueError("block 要在 1 和样本长度之间")
    rng = np.random.default_rng(seed)
    out = np.empty((n, m + 1))
    for i in range(n):
        if block == 1:
            sample = rng.choice(values, size=m, replace=True)
        else:
            starts = rng.integers(0, m - block + 1, size=int(np.ceil(m / block)))
            sample = np.concatenate([values[s:s + block] for s in starts])[:m]
        out[i] = float(close.iloc[0]) * np.concatenate([[1.0], np.cumprod(1 + sample)])
    return out
