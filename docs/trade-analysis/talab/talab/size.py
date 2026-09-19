"""talab.size：仓位。第 26 篇。

第 23 篇把「亏多少算看错」变成了一条止损线，第 24 篇量了杠杆怎么把你赶出场。
夹在它们中间还有一个问题没答：**这一笔，买多少**。

把账户想成家里的配电箱。止损是每条支路上的保险丝：这台电器出事，最多烧掉这一条。
仓位是「这台电器要占多少安培」。两件事必须一起定——保险丝的额定电流再准，
你给一条 16 安的线接上 40 安的电器，跳的就不是支路而是总闸。

模块分四部分：

1. **一笔买多少**：`position_size`、`size_by_atr`、`simulate`——
   把「一笔最多亏账户的百分之几」翻译成金额和数量。
2. **上限在哪**：`kelly`、`growth_rate`、`optimal_f`、`recovery`、`underwater`——
   下注比例再往上加，增长率会掉头向下；回撤要爬回来，需要的涨幅比跌幅大。
3. **按波动调**：`vol_target`——盯住「账户的波动」而不是「持仓的金额」。
4. **组合**：`portfolio_vol`、`effective_bets`、`inverse_vol_weights`、`combined_risk`——
   五条支路接在同一根干线上时，它们其实是一条。

所有函数都不含成本和滑点（成本是第 28 篇）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

METHODS = ("full", "amount", "fraction", "risk")


# ---------------------------------------------------------------------------
# 一、一笔买多少
# ---------------------------------------------------------------------------

def stop_distance(entry_price: float, stop_price: float) -> float:
    """止损距离，按**占进场价的比例**算。

    这是仓位公式里唯一和行情有关的输入：它由第 23 篇的四个出场问题决定，
    不是你随便填的数。入场条件一改（比如要求「收盘创 20 日新高」），它也跟着变。
    """
    if not 0 < stop_price < entry_price:
        raise ValueError(f"止损价要在 0 和进场价之间（进场 {entry_price}，止损 {stop_price}）")
    return (entry_price - stop_price) / entry_price


def position_size(equity: float, distance: float, risk_fraction: float = 0.01,
                  price: float | None = None, max_fraction: float = 1.0) -> pd.Series:
    """一笔最多亏账户的 `risk_fraction`，止损距离 `distance`，该买多少。

    > 仓位金额 = 账户 × 每笔风险比例 ÷ 止损距离

    推导只有一步：仓位金额 × 止损距离 = 这笔被止损时亏的钱，让它等于「账户 × 风险比例」。
    `max_fraction` 是名义敞口的上限，默认 1.0＝不借钱；算出来超过它就封顶，
    这时**实际风险会小于你定的风险比例**，返回的「实际风险」会告诉你小了多少。
    """
    if not 0 < risk_fraction < 1:
        raise ValueError("每笔风险比例要在 0 和 1 之间")
    if distance <= 0:
        raise ValueError("止损距离要大于 0，没有止损就算不出仓位")
    want = equity * risk_fraction / distance
    amount = min(want, equity * max_fraction)
    out = {"仓位金额": amount, "占账户": amount / equity,
           "止损时亏": amount * distance, "实际风险": amount * distance / equity,
           "有没有封顶": want > amount}
    if price is not None:
        out["数量"] = amount / price
    return pd.Series(out)


def size_by_atr(equity: float, atr: float, price: float, risk_fraction: float = 0.01,
                k: float = 3.0, max_fraction: float = 1.0) -> pd.Series:
    """「按 ATR 调整仓位」的写法——它和 `position_size` 是同一个公式。

    止损放在进场价下方 k 倍 ATR 时，止损距离就是 `k × ATR ÷ 价格`，代进去得到

    > 仓位数量 = 账户 × 每笔风险比例 ÷ (k × ATR)

    「波动大就少买」不是另一条规则，是这条公式的自动结果：ATR 翻倍，仓位减半。
    """
    return position_size(equity, k * atr / price, risk_fraction, price, max_fraction)


def simulate(trades: pd.DataFrame, method: str = "risk", equity: float = 100_000.0,
             amount: float = 10_000.0, fraction: float = 0.10, risk: float = 0.01,
             max_fraction: float = 1.0) -> pd.DataFrame:
    """同一串交易，换一种仓位方法，资金曲线长什么样。

    `trades` 要有「买入价」「卖出价」「初始止损」三列（第 23 篇 `risk.run` 的输出就是）。
    四种方法：

    - `full`：满仓，每笔都把账户全押上
    - `amount`：固定金额，每笔都买 `amount` 美元（不随账户变，所以**不复利**）
    - `fraction`：固定比例，每笔都买账户的 `fraction`
    - `risk`：固定风险，每笔都让「被止损时亏掉的钱」等于账户的 `risk`

    ⚠️ 这里假设同一时刻只有一笔仓（主线策略就是这样），所以一笔结束才开下一笔。
    多笔并行的组合风险要用 `combined_risk` 和 `effective_bets` 另算。
    """
    if method not in METHODS:
        raise ValueError(f"method 只能是 {METHODS} 之一，收到 {method!r}")
    rows, account = [], float(equity)
    for _, t in trades.iterrows():
        distance = stop_distance(t["买入价"], t["初始止损"])
        if method == "full":
            notional = account
        elif method == "amount":
            notional = min(amount, account)
        elif method == "fraction":
            notional = account * fraction
        else:
            notional = min(account * risk / distance, account * max_fraction)
        profit = notional * (t["卖出价"] / t["买入价"] - 1)
        account += profit
        rows.append({"买入日": t["买入日"], "卖出日": t["卖出日"], "止损距离": distance,
                     "仓位金额": notional, "占账户": notional / (account - profit),
                     "盈亏": profit, "盈亏占账户": profit / (account - profit), "账户": account})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 二、上限在哪：回撤、凯利
# ---------------------------------------------------------------------------

def recovery(loss) -> float | np.ndarray:
    """亏掉 `loss` 之后，要涨多少才回本：`loss ÷ (1 − loss)`。

    这条式子是整篇的地基。亏 10% 要涨 11.1%，亏 50% 要涨 100%，亏 83% 要涨 488%——
    **亏损和收益不是对称的**，所以「少亏一点」比「多赚一点」在复利上更值钱。
    """
    loss = np.asarray(loss, dtype=float)
    if np.any((loss < 0) | (loss >= 1)):
        raise ValueError("loss 要写成 0 到 1 之间的正数（亏 20% 写 0.2）")
    out = loss / (1 - loss)
    return float(out) if out.ndim == 0 else out


def drawdown(equity: pd.Series) -> pd.Series:
    """每个时点距离历史最高点还差多少（负数）。"""
    return equity / equity.cummax() - 1


def underwater(equity: pd.Series) -> pd.DataFrame:
    """把资金曲线拆成一段段「水下」的日子：从跌破前高到重新创新高。

    最大回撤只说最深有多深，这张表还说**最长有多长**——
    对着账户等三年和亏三成，难受程度完全不是一回事。
    """
    below = drawdown(equity) < -1e-12
    rows, start = [], None
    for time, under in below.items():
        if under and start is None:
            start = time
        elif not under and start is not None:
            rows.append((start, time, float(drawdown(equity).loc[start:time].min())))
            start = None
    if start is not None:                      # 最后一段还没爬回来
        rows.append((start, equity.index[-1], float(drawdown(equity).loc[start:].min())))
    out = pd.DataFrame(rows, columns=["开始", "结束", "最深"])
    out["天数"] = (out["结束"] - out["开始"]).dt.days
    out["要涨回来"] = recovery(-out["最深"].to_numpy())
    return out


def kelly(win_rate: float, payoff: float) -> float:
    """凯利公式的两点版本：赢的概率 `win_rate`，赢时赚 `payoff` 份、输时亏 1 份。

    > f* = 胜率 − 败率 ÷ 盈亏比

    f* 是**每次下注冒的风险占账户的比例**（在交易里就是「一笔最多亏账户的百分之几」）。
    它最大化的是对数收益的期望，也就是长期的复利增长率——不是期望收益，
    期望收益永远是「押得越多越好」。⚠️ 公式里的胜率和盈亏比是**真值**，
    而你只有估计值；`optimal_f` 上的 bootstrap 会告诉你这个估计有多晃。
    """
    if not 0 <= win_rate <= 1:
        raise ValueError("胜率要在 0 和 1 之间")
    if payoff <= 0:
        raise ValueError("盈亏比要大于 0")
    return win_rate - (1 - win_rate) / payoff


def growth_rate(r, f: float) -> float:
    """按比例 `f` 下注一串 R 倍数时，每笔的对数增长率 `mean(log(1 + f·R))`。

    账户是乘起来的，所以要最大化的是对数的平均数，不是收益的平均数。
    下注比例大到某一笔会把账户打到 0 以下时，返回 −inf：那不是「亏得多」，是出局。
    """
    x = 1 + f * np.asarray(r, dtype=float)
    return -np.inf if np.any(x <= 0) else float(np.mean(np.log(x)))


def optimal_f(r, grid=None) -> float:
    """在网格上直接找让 `growth_rate` 最大的下注比例，不假设只有两种结果。

    和 `kelly` 的两点公式对照着看：两者接近，说明那串交易的形状确实像一次赌局；
    差得远，说明分布的尾巴在起作用（第 23 篇：两成的交易贡献一半的 R）。
    """
    grid = np.arange(0.005, 1.0, 0.005) if grid is None else np.asarray(grid, dtype=float)
    values = [growth_rate(r, f) for f in grid]
    return float(grid[int(np.argmax(values))])


# ---------------------------------------------------------------------------
# 三、按波动调：盯住账户的波动
# ---------------------------------------------------------------------------

def vol_target(returns: pd.Series, target: float, lookback: int = 20,
               periods_per_year: int = 252, cap: float = 3.0) -> pd.Series:
    """波动率目标仓位：仓位 = 目标波动 ÷ 最近实际波动。

    固定风险盯的是「一笔亏多少」，波动率目标盯的是「账户每天晃多少」。
    波动率比收益好估得多（第 15 篇：它有聚集性，昨天高今天大概率还高），
    所以这是少数几个「用历史估一个数、拿到未来还能用」的地方。

    ⚠️ 仓位用 `shift(1)`：今天的仓位只能用昨天收盘前算得出来的波动。
    `cap` 是杠杆上限，默认 3 倍；波动特别低的时候公式会要求很大的杠杆。
    """
    realized = returns.rolling(lookback).std() * np.sqrt(periods_per_year)
    return (target / realized).shift(1).clip(upper=cap).fillna(0.0).rename("仓位")


# ---------------------------------------------------------------------------
# 四、组合：几笔交易其实是几笔
# ---------------------------------------------------------------------------

def portfolio_vol(weights, vols, corr) -> float:
    """组合的波动：`sqrt(wᵀ Σ w)`，其中 `Σ` 由波动和相关矩阵拼出来。

    这条式子说的就是那句话：**风险不能相加，只能这样合起来**。
    """
    w, s = np.asarray(weights, dtype=float), np.asarray(vols, dtype=float)
    cov = np.asarray(corr, dtype=float) * np.outer(s, s)
    return float(np.sqrt(w @ cov @ w))


def combined_risk(n: int, per_trade: float, corr: float) -> float:
    """`n` 笔同样大小、两两相关都是 `corr` 的仓位，合起来的风险。

    > 合计 = 单笔 × sqrt(n + n(n−1)ρ)

    ρ=0 时是 `单笔 × sqrt(n)`（教科书上的「风险开根号相加」），
    ρ=1 时是 `单笔 × n`（五笔其实是一笔，只是放大了五倍）。
    真实世界在两者之间，而且离 1 比多数人以为的近。
    """
    if not -1 / max(n - 1, 1) <= corr <= 1:
        raise ValueError(f"{n} 笔仓位的两两相关不可能是 {corr}（相关矩阵会不正定）")
    return per_trade * np.sqrt(n + n * (n - 1) * corr)


def effective_bets(weights, corr) -> float:
    """有效独立仓位数：这一篮子东西，其实相当于几个互不相干的东西。

    > N_eff = (Σw)² ÷ (wᵀ C w)

    全都完全相关时等于 1（买十个等于买一个），互不相关且等权时等于 n。
    它回答的是「我到底分散了没有」，而不是「我持有几个代码」。
    """
    w = np.asarray(weights, dtype=float)
    return float(w.sum() ** 2 / (w @ np.asarray(corr, dtype=float) @ w))


def inverse_vol_weights(vols) -> np.ndarray:
    """按波动率倒数分配资金：波动大的少给，让每份贡献的风险大致相等。

    它只用到波动率，不用到收益率——**波动率估得准，收益率估不准**，
    这就是这个看起来过分简单的做法在样本外往往赢过「按历史收益分配」的原因。
    """
    s = np.asarray(vols, dtype=float)
    if np.any(s <= 0):
        raise ValueError("波动率要大于 0")
    return (1 / s) / (1 / s).sum()
