"""talab.report：怎么评价一条策略。第 29 篇。

第 27 篇保证引擎是对的，第 28 篇保证喂进去的数据是干净的。
这个模块回答最后一个问题：**跑出来的这一串数，该怎么读。**

整个模块围绕一件事写：**每一个指标都要带着它的误差一起出现。**
`年化 21%` 是一句话，`年化 21%（90% 区间 3% 到 44%）` 是另一句话，
而它们是同一条资金曲线算出来的。只报前一句不算撒谎，但也不算说清楚。

三组函数：

1. **算指标**：`metrics` 一次给出一页纸上半部分的全部数字
2. **算误差**：`sharpe_se`（解析解）、`bootstrap`（重抽）、`trade_metrics`（交易层面）
3. **排版**：`by_year`、`compare`、`page`
"""
from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from talab.size import drawdown

NORMAL = NormalDist()


# ---------------------------------------------------------------------------
# 一、单个指标
# ---------------------------------------------------------------------------

def to_curve(returns: pd.Series) -> pd.Series:
    """把一串收益率还原成资金曲线，并在**最前面补一个 1**。

    ⚠️ 少补这个 1 是这一篇里最容易犯的小错：`(1 + r).cumprod()` 的第一个点
    已经是「第一根走完之后」了，拿它当期初，整段收益就少算了第一根。
    第一根碰巧是大涨大跌的日子时，年化能差出一个百分点。
    """
    step = returns.index[1] - returns.index[0] if len(returns) > 1 else pd.Timedelta(0)
    head = pd.Series([1.0], index=[returns.index[0] - step])
    return pd.concat([head, (1 + returns).cumprod()])


def annual_return(equity: pd.Series, periods_per_year: int) -> float:
    """复合年化收益率（CAGR）：`(期末 ÷ 期初) ^ (一年几根 ÷ 总共几根) − 1`。

    ⚠️ 这里用**根数**折算而不是用日历天数，所以它衡量的是「每根 K 线平均涨多少」的复利，
    两条起止日期不同的曲线可以这样比；但它对**起止点本身**极其敏感，见第 29 篇。
    """
    n = len(equity) - 1
    if n <= 0:
        raise ValueError("资金曲线至少要有两个点")
    return float(equity.iloc[-1] / equity.iloc[0]) ** (periods_per_year / n) - 1


def annual_vol(returns: pd.Series, periods_per_year: int) -> float:
    """年化波动率：单根 K 线收益率的标准差 × √(一年几根)。"""
    return float(returns.std()) * math.sqrt(periods_per_year)


def excess(returns: pd.Series, periods_per_year: int, rf: float | pd.Series = 0.0) -> pd.Series:
    """超额收益率：每根 K 线的收益率减去同期无风险利率。

    `rf` 是**年化**利率（4.25% 写 0.0425），可以是一个数，也可以是一条随时间变化的序列
    （`data.load_fred_series` 的输出就是）。换算成单根 K 线用复利口径：`(1+rf)^(1/一年几根) − 1`。

    ⚠️ 对齐这一步最容易出事：利率序列只有工作日，而加密的 K 线天天有，还带 UTC 时区。
    直接 `reindex` 会**安安静静地全变成 NaN**，一个报错都不给。所以这里先统一时区，
    再用「并集 + 前向填充」补齐缺的日子。
    """
    if isinstance(rf, pd.Series):
        index, source = returns.index, rf
        if getattr(source.index, "tz", None) != getattr(index, "tz", None):
            source = source.copy()
            source.index = (source.index.tz_localize(None) if index.tz is None
                            else source.index.tz_localize(index.tz) if source.index.tz is None
                            else source.index.tz_convert(index.tz))
        rf = pd.Series(source.reindex(source.index.union(index)).ffill().bfill()
                       .reindex(index).to_numpy(), index=index)
    per_period = (1 + rf) ** (1 / periods_per_year) - 1
    return returns - per_period


def sharpe(returns: pd.Series, periods_per_year: int, rf: float | pd.Series = 0.0) -> float:
    """夏普比率：`超额收益的均值 ÷ 超额收益的标准差 × √(一年几根)`。

    它是一个**信噪比**：分子是信号（平均每根赚多少），分母是噪声（这个平均值周围抖多厉害）。
    √(一年几根) 来自「独立的收益率相加时，均值按 n 放大、标准差只按 √n 放大」——
    所以时间拉长对信噪比是有利的，这正是夏普比率能被年化的原因，
    也是它**只有在收益率互相独立时才能这样年化**的原因（第 29 篇量了违反的后果）。

    ⚠️ 曲线一动不动（比如那一年从头到尾空仓）时返回 `NaN` 而不是一个数：
    那种情况下分母是 0，而分子是「−无风险利率」，公式会给出一个绝对值极大的负数——
    它在数学上没错，但把它印在报告上只会误导人。该说的是**「这一年没有可比的夏普比率」**。
    """
    e = excess(returns, periods_per_year, rf)
    if len(e) < 2 or e.std() == 0 or returns.std() == 0:
        return np.nan                                 # 见上面那条 ⚠️
    return float(e.mean() / e.std()) * math.sqrt(periods_per_year)


def sortino(returns: pd.Series, periods_per_year: int, rf: float | pd.Series = 0.0) -> float:
    """索提诺比率：分母只算**下行**的波动，上涨的波动不算在风险里。

    下行标准差 = √(所有超额收益里取 min(x, 0) 的平方平均)——注意分母是**全部**根数，
    不是亏损根数，否则一条「很少亏但亏起来很大」的曲线会被算得比实际好。
    """
    e = excess(returns, periods_per_year, rf)
    downside = np.sqrt((np.minimum(e.to_numpy(float), 0.0) ** 2).mean())
    if downside == 0:                                 # 一次都没亏过：分母是 0
        return np.inf if e.mean() > 0 else np.nan
    return float(e.mean() / downside) * math.sqrt(periods_per_year)


def max_drawdown(equity: pd.Series) -> float:
    """最大回撤（负数）：全程距离历史最高点最远的那一刻，差了多少。"""
    return float(drawdown(equity).min())


def calmar(equity: pd.Series, periods_per_year: int) -> float:
    """卡玛比率：`年化收益 ÷ |最大回撤|`。

    ⚠️ 它的分母是一个**极值**，只由最坏的那一刻决定，样本越长通常越深（第 29 篇量了）。
    所以卡玛比率不能拿来比两条长度不同的曲线。
    """
    mdd = max_drawdown(equity)
    return annual_return(equity, periods_per_year) / abs(mdd) if mdd < 0 else np.inf


def metrics(equity: pd.Series, periods_per_year: int, rf: float | pd.Series = 0.0) -> pd.Series:
    """一页纸的上半部分：一条资金曲线的全部常规指标。"""
    returns = equity.pct_change().dropna()
    below = drawdown(equity) < -1e-12                 # 每一根：在不在水下
    dry = (~below).cumsum()                           # 每创一次新高，这个编号就加一
    return pd.Series({
        "起": equity.index[0], "止": equity.index[-1], "根数": float(len(equity)),
        "累计收益": float(equity.iloc[-1] / equity.iloc[0]) - 1,
        "年化收益": annual_return(equity, periods_per_year),
        "年化波动": annual_vol(returns, periods_per_year),
        "夏普比率": sharpe(returns, periods_per_year, rf),
        "索提诺比率": sortino(returns, periods_per_year, rf),
        "最大回撤": max_drawdown(equity),
        "卡玛比率": calmar(equity, periods_per_year),
        "在水下的比例": float(below.mean()),
        "最长水下根数": float(below.groupby(dry).sum().max()),
        "最好的一根": float(returns.max()), "最差的一根": float(returns.min()),
    })


# ---------------------------------------------------------------------------
# 二、这些数有多准
# ---------------------------------------------------------------------------

def sharpe_se(sharpe_value: float, n: int, periods_per_year: int) -> float:
    """年化夏普比率的标准误（Lo 2002，假设每根收益率互相独立且同分布）：

    > SE(年化夏普) = √(一年几根) × √((1 + 年化夏普² ÷ (2 × 一年几根)) ÷ 根数)

    括号里那一项几乎总是 1 出头（日线上夏普 1.0 时是 1.0014），所以它近似等于
    **√(一年几根 ÷ 根数) = 1 ÷ √年数**：`一条年化夏普 1.0 的策略，跑一年的标准误就是 1.0`。
    """
    if n <= 0:
        raise ValueError("根数要大于 0")
    per_period = sharpe_value / math.sqrt(periods_per_year)
    return math.sqrt(periods_per_year) * math.sqrt((1 + per_period ** 2 / 2) / n)


def years_needed(sharpe_value: float, t: float = 2.0, periods_per_year: int = 252) -> float:
    """要让「这条策略不是运气」的 t 值达到 `t`，需要跑多少年：

    > 年数 = (t ÷ 年化夏普)² × (1 + 年化夏普² ÷ (2 × 一年几根))

    近似就是 **(t ÷ 夏普)²**：夏普 2.0 要 1 年，夏普 1.0 要 4 年，夏普 0.5 要 16 年。
    所以「夏普 0.5 但我只有两年数据」这句话本身就已经说完了——那两年什么都证明不了。
    """
    if sharpe_value <= 0:
        return np.inf
    return (t / sharpe_value) ** 2 * (1 + sharpe_value ** 2 / (2 * periods_per_year))


def significance_table(sharpes=(0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0), t: float = 2.0,
                       periods_per_year: int = 252) -> pd.DataFrame:
    """不同夏普比率下，要多少年才能把 t 值攒到 `t`。"""
    rows = [{"年化夏普": s, "要跑多少年": years_needed(s, t, periods_per_year),
             "要多少根 K 线": years_needed(s, t, periods_per_year) * periods_per_year}
            for s in sharpes]
    return pd.DataFrame(rows)


def bootstrap(returns: pd.Series, stat, n: int = 2000, block: int = 1, seed: int = 0,
              level: float = 0.90) -> pd.Series:
    """块自助法：把收益率切成长度 `block` 的小段，有放回地抽回原来的长度，重算 `stat`。

    `stat` 接收一条收益率序列，返回一个数（`lambda r: sharpe(r, 365)` 这样）。

    - `block=1` 就是普通的 i.i.d. 自助法：它假设**先后顺序无关紧要**。
      算均值、夏普比率时这个假设还行；算**最大回撤**时它是错的——
      回撤衡量的恰恰是「坏日子会不会连在一起」，而打散重抽把这件事抹掉了（第 29 篇量了差多少）。
    - `block > 1` 保留每一小段内部的顺序，是回撤类指标该用的口径。
    """
    if block < 1 or block > len(returns):
        raise ValueError("block 要在 1 和样本长度之间")
    values = returns.to_numpy(dtype=float)
    m = len(values)
    rng = np.random.default_rng(seed)
    sims = np.empty(n)
    for i in range(n):
        if block == 1:
            sample = rng.choice(values, size=m, replace=True)
        else:
            starts = rng.integers(0, m - block + 1, size=int(np.ceil(m / block)))
            sample = np.concatenate([values[s:s + block] for s in starts])[:m]
        sims[i] = stat(pd.Series(sample, index=returns.index))
    lo, hi = np.percentile(sims, [(1 - level) * 50, 100 - (1 - level) * 50])
    return pd.Series({"实际值": float(stat(returns)), "自助法中位数": float(np.median(sims)),
                      f"{level:.0%} 下界": float(lo), f"{level:.0%} 上界": float(hi),
                      "标准误": float(sims.std(ddof=1)), "小于 0 的比例": float((sims < 0).mean())})


def trade_metrics(trade_returns, level: float = 0.95) -> pd.Series:
    """交易层面的统计：**样本量是交易笔数，不是 K 线根数**。

    一条持仓 1,377 天的策略如果只进出了 35 次，它就只下了 35 次注；
    那 1,377 个日收益率不是 1,377 个独立样本，它们被绑成了 35 串。
    夏普比率的标准误按「根数」算，所以它在这种策略上**系统性地偏小**（第 29 篇量了）。

    `t 值` = 平均每笔 ÷ 平均值的标准误。经验上 |t| < 2 就是「这串数和 0 分不开」。
    ⚠️ 区间用的是正态近似，笔数少的时候它偏窄，该以 `bootstrap` 为准。
    """
    r = pd.Series(trade_returns).dropna().astype(float)
    n = len(r)
    if n < 2:
        raise ValueError("至少要有两笔交易")
    se = float(r.std(ddof=1)) / math.sqrt(n)
    z = NORMAL.inv_cdf(0.5 + level / 2)
    streak = longest = 0
    worst = current = 0.0
    for x in r:
        if x <= 0:
            streak += 1
            current += x
            longest, worst = max(longest, streak), min(worst, current)
        else:
            streak, current = 0, 0.0
    return pd.Series({
        "笔数": float(n), "平均每笔": float(r.mean()), "每笔的标准差": float(r.std(ddof=1)),
        "平均值的标准误": se, "t 值": float(r.mean()) / se,
        f"{level:.0%} 下界": float(r.mean()) - z * se, f"{level:.0%} 上界": float(r.mean()) + z * se,
        "最长连亏笔数": float(longest), "连亏最多亏掉": worst,
    })


# ---------------------------------------------------------------------------
# 三、排版
# ---------------------------------------------------------------------------

def by_year(equity: pd.Series, periods_per_year: int, rf: float | pd.Series = 0.0) -> pd.DataFrame:
    """按自然年拆开：每一年的收益、回撤、夏普各是多少。

    单独一年的夏普比率基本没有统计意义（见 `years_needed`），列在这里是为了看**稳不稳**，
    不是为了挑出最好的那一年。
    """
    returns = equity.pct_change().dropna()
    rows = []
    for year, chunk in returns.groupby(returns.index.year):
        curve = to_curve(chunk)
        rows.append({"年": year, "根数": len(chunk), "收益": float(curve.iloc[-1]) - 1,
                     "最大回撤": max_drawdown(curve),
                     "夏普": sharpe(chunk, periods_per_year, rf) if len(chunk) > 1 else np.nan})
    return pd.DataFrame(rows).set_index("年")


def compare(curves: dict[str, pd.Series], periods_per_year: int,
            rf: float | pd.Series = 0.0) -> pd.DataFrame:
    """把几条资金曲线的指标并排放：每一列一条曲线。

    ⚠️ 只有起止时间和 K 线频率都一样的曲线才能这样比。不一样时先各自换算到同一个频率
    （`equity.resample("1D").last()`），再比。
    """
    return pd.DataFrame({name: metrics(curve, periods_per_year, rf)
                         for name, curve in curves.items()})


def page(equity: pd.Series, periods_per_year: int, trades: pd.DataFrame | None = None,
         rf: float | pd.Series = 0.0, name: str = "策略", n_boot: int = 1000,
         block: int = 20, seed: int = 29) -> str:
    """一页纸的回测报告：指标、误差、分年、交易统计，全部折算成能一眼看完的文本。

    三段里最重要的是**中间那段**：同样一条曲线，把它的夏普比率和最大回撤重抽一千次，
    看它们能落在多宽的范围里。上面那段的数字只有配上中间那段才算读得懂。
    """
    returns = equity.pct_change().dropna()
    m = metrics(equity, periods_per_year, rf)
    lines = [f"{'=' * 62}", f"  {name}   {m['起'].date()} → {m['止'].date()}   {int(m['根数'])} 根",
             f"{'=' * 62}", "【一】指标"]
    for key in ["累计收益", "年化收益", "年化波动", "夏普比率", "索提诺比率",
                "最大回撤", "卡玛比率", "在水下的比例"]:
        lines.append(f"  {key:<8}{m[key]:>12.4f}")
    lines.append(f"  {'最长水下':<8}{int(m['最长水下根数']):>12d} 根")

    lines.append("【二】这些数有多准（重抽 %d 次，块长 %d 根）" % (n_boot, block))
    solved = sharpe_se(m["夏普比率"], len(returns), periods_per_year)
    lines.append(f"  夏普比率的标准误（解析解）{solved:>10.4f}   "
                 f"t 值 {m['夏普比率'] / solved:>6.2f}   "
                 f"要攒到 t=2 得跑 {years_needed(m['夏普比率'], 2.0, periods_per_year):.1f} 年")
    for label, stat, use_block in [
            ("夏普比率", lambda r: sharpe(r, periods_per_year, rf), 1),
            ("年化收益", lambda r: annual_return(to_curve(r), periods_per_year), 1),
            ("最大回撤", lambda r: max_drawdown(to_curve(r)), block)]:
        b = bootstrap(returns, stat, n=n_boot, block=use_block, seed=seed)
        lines.append(f"  {label:<8}{b['实际值']:>10.4f}   90% 区间 "
                     f"[{b['90% 下界']:.4f}, {b['90% 上界']:.4f}]   块长 {use_block}")

    lines.append("【三】分年")
    lines.append("  " + by_year(equity, periods_per_year, rf).round(4).to_string().replace("\n", "\n  "))

    if trades is not None and len(trades) >= 2:
        t = trade_metrics(trades["收益"])
        lines.append("【四】交易（样本量 = 笔数，不是根数）")
        lines.append(f"  笔数 {int(t['笔数'])}   平均每笔 {t['平均每笔']:.4f}   "
                     f"t 值 {t['t 值']:.2f}   最长连亏 {int(t['最长连亏笔数'])} 笔")
        lines.append(f"  95% 区间 [{t['95% 下界']:.4f}, {t['95% 上界']:.4f}]   "
                     f"连亏最多亏掉 {t['连亏最多亏掉']:.4f}")
    lines.append("=" * 62)
    return "\n".join(lines)
