"""talab.reversion：均值回归。第 32 篇。

第 31 篇的趋势跟随赌的是「走出去的会接着走」。这一篇赌的正好相反：
**跌得太多的会弹回来。**

两条策略的每一样东西都是镜像：

| | 趋势跟随（第 31 篇） | 均值回归（这一篇） |
|---|---|---|
| 进场 | 价格**创新高** | 价格**跌得离谱** |
| 胜率 | 低（32%–46%） | **高** |
| 单笔盈亏 | 亏小赚大 | **赚小亏大** |
| 形状 | 凸（像买了期权） | **凹（像卖了期权）** |
| 怕什么 | 来回震荡 | **一路不回头** |
| 适合什么市场 | 方差比 > 1 | **方差比 < 1** |

最后那一行是这一篇的骨架：**同一个数（第 5 篇的方差比）同时决定了两篇的结论。**
SPY 的 60 天方差比是 0.616，BTC 是 1.270——所以均值回归在 SPY 上成立、在 BTC 上是反向指标，
而第 31 篇的趋势跟随正好反过来。

⚠️ 这一篇的信号**全部用到当根收盘价**（偏离度、连跌天数、RSI），
所以它**只能下一根开盘成交**——第 31 篇那个「碰到通道就成交」的例外，在这里不成立。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from talab.backtest import Account

SIDES = ("long", "short")


# ---------------------------------------------------------------------------
# 一、拉伸与连击：怎么量「跌得太多」
# ---------------------------------------------------------------------------

def stretch(close: pd.Series, n: int = 20) -> pd.Series:
    """偏离度：收盘价离 n 日均线有几个（n 日）标准差。

    这就是布林带的 %b 换一种写法——`z = −2` 就是「踩在布林下轨上」。
    用标准差而不是百分比，是为了让同一个阈值能跨市场用：
    SPY 的 2 个标准差大约是 3%，BTC 大约是 9%。
    """
    average = close.rolling(n).mean()
    deviation = close.rolling(n).std()
    return ((close - average) / deviation).rename("偏离度")


def streak(close: pd.Series) -> pd.Series:
    """连击：连涨几天记正数，连跌几天记负数，持平记 0。

    它和偏离度量的是**不同的东西**：偏离度看「离得多远」，连击看「连着走了多久」。
    第 32 篇的实测是两个一起用比单用任何一个都好。
    """
    change = close.diff()
    up, down = change > 0, change < 0
    rising = up.groupby((~up).cumsum()).cumsum()
    falling = down.groupby((~down).cumsum()).cumsum()
    return (rising - falling).rename("连击")


def setups(close: pd.Series, condition: pd.Series, horizons=(1, 5, 10, 20)) -> pd.DataFrame:
    """条件成立的每一天，以及之后若干根的涨跌。

    ⚠️ 这不是回测——它没有止损、没有仓位、允许重叠。它回答的是更前面的一个问题：
    **这个条件本身携带信息吗？**答案要和「什么都不做」的基准比（见 `edge`）。
    """
    values = close.to_numpy(float)
    where = np.where(condition.reindex(close.index).fillna(False).to_numpy())[0]
    rows = []
    for i in where:
        row = {"时间": close.index[i], "收盘": values[i]}
        for k in horizons:
            row[f"{k} 根后"] = values[i + k] / values[i] - 1 if i + k < len(values) else np.nan
        tail = values[i + 1:i + 1 + max(horizons)]
        row["期间最低"] = float(tail.min()) / values[i] - 1 if len(tail) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def edge(table: pd.DataFrame, close: pd.Series, horizon: int = 5) -> pd.Series:
    """把 `setups` 的结果和「随便哪一天买入」的基准放在一起比。

    只看「胜率 70%」没有意义——如果随便哪一天买入的胜率也有 68%，那这个条件什么都没说。
    **信号的价值是它比基准好多少，不是它本身多好。**
    """
    column = f"{horizon} 根后"
    hits = table[column].dropna()
    baseline = close.pct_change(horizon).dropna()
    return pd.Series({
        "次数": float(len(hits)), "胜率": float((hits > 0).mean()), "平均": float(hits.mean()),
        "中位": float(hits.median()), "最差": float(hits.min()),
        "基准胜率": float((baseline > 0).mean()), "基准平均": float(baseline.mean()),
        "比基准多赚": float(hits.mean() - baseline.mean()),
    })


# ---------------------------------------------------------------------------
# 二、引擎
# ---------------------------------------------------------------------------

@dataclass
class ReversionPlan:
    """一套均值回归的设定。和第 31 篇的 `TurtlePlan` 一一对应，只是每一项都反过来。"""
    entry_z: float = -2.0                  # 进场：偏离度跌到这个数以下
    entry_streak: int = 3                  # 进场：同时要连跌几天（0 = 不要求）
    entry_rsi: float | None = None         # 进场：改用 RSI 低于这个数（None = 用偏离度）
    rsi_period: int = 2
    exit_z: float = 0.0                    # 出场：偏离度回到这个数以上（0 = 回到均线）
    max_bars: int = 10                     # 出场：最多拿几根（时间出场，第 23 篇的第四类）
    stop_atr: float | None = 3.0           # 止损：进场价往下几个 ATR（None = 不设）
    n: int = 20                            # 算偏离度的窗口
    atr_period: int = 14
    risk: float = 0.02                     # 一笔冒账户的百分之几（有止损时）
    fraction: float = 1.0                  # 没有止损时，一笔买账户的百分之几
    side: str = "long"
    fee_rate: float = 0.0

    def __post_init__(self):
        if self.side not in SIDES:
            raise ValueError(f"side 只能是 {SIDES} 之一，收到 {self.side!r}")
        if self.entry_z >= self.exit_z:
            raise ValueError("进场的偏离度要比出场的低，否则进场当天就该出场")
        if self.max_bars < 1 or self.n < 2:
            raise ValueError("max_bars 至少是 1，算偏离度的窗口至少是 2")
        if self.entry_rsi is not None and not 0 < self.entry_rsi < 100:
            raise ValueError("entry_rsi 要在 0 和 100 之间")

    def describe(self) -> pd.Series:
        entry = (f"{self.rsi_period} 日 RSI 低于 {self.entry_rsi:g}" if self.entry_rsi is not None
                 else f"偏离 {self.n} 日均线 {self.entry_z} 个标准差以下"
                      + (f"，且连跌 {self.entry_streak} 天以上" if self.entry_streak else ""))
        return pd.Series({
            "进场": entry,
            "出场一（回归）": f"偏离度回到 {self.exit_z} 以上",
            "出场二（时间）": f"最多拿 {self.max_bars} 根",
            "出场三（止损）": "不设" if self.stop_atr is None else f"进场价下方 {self.stop_atr} 个 ATR",
            "仓位": f"一笔冒账户的 {self.risk:.1%}" if self.stop_atr
                    else f"一笔买账户的 {self.fraction:.0%}",
            "成交": "下一根开盘（信号用到了收盘价）",
        })


def reversion(df: pd.DataFrame, plan: ReversionPlan | None = None,
              equity: float = 100_000.0) -> dict:
    """按均值回归的规则跑一遍历史。四步顺序和第 27、31 篇完全一样。

    1. **成交**：上一根收盘定下来的单子，用这一根的开盘价成交
    2. **出场**：止损（盘中触发）→ 回归目标 → 时间到，三者按这个顺序判
    3. **估值**：按收盘价记权益
    4. **下单**：用这一根的收盘价算信号，挂下一根的单

    ⚠️ 第 4 步和第 1 步之间隔着一整根 K 线，这是这一篇和第 31 篇最大的实现差别：
    偏离度要用当根收盘价才能算出来，所以**没有当根成交这一说**。
    """
    from talab import indicators as I

    plan = plan or ReversionPlan()
    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    z = stretch(df["close"], plan.n).to_numpy()
    runs = streak(df["close"]).to_numpy()
    atr = I.atr(df["high"], df["low"], df["close"], plan.atr_period).to_numpy()
    force = (I.rsi(df["close"], plan.rsi_period).to_numpy() if plan.entry_rsi is not None
             else np.full(len(c), np.nan))
    direction = 1 if plan.side == "long" else -1

    account = Account(cash=float(equity))
    curve, trades, error = [], [], 0.0
    pending = False
    entry_price = stop = risk_amount = np.nan
    opened_at = -1
    shares = 0.0

    def value(price: float) -> float:
        return account.cash + direction * shares * price

    def close_out(i: int, price: float, reason: str) -> None:
        nonlocal shares, opened_at, stop
        if direction > 0:
            account.sell(price, shares, plan.fee_rate)
            profit = (price - entry_price) * shares - price * shares * plan.fee_rate
        else:
            account.cash -= price * shares * (1 + plan.fee_rate)
            account.fees += price * shares * plan.fee_rate
            profit = (entry_price - price) * shares - price * shares * plan.fee_rate
        trades.append({"进场日": df.index[opened_at], "进场价": entry_price, "数量": shares,
                       "出场日": df.index[i], "出场价": price, "原因": reason, "盈亏": profit,
                       "R": profit / risk_amount if risk_amount else np.nan,
                       "收益": direction * (price / entry_price - 1), "根数": i - opened_at})
        shares, opened_at, stop = 0.0, -1, np.nan

    ready_at = ~np.isnan(z) & ~np.isnan(atr) & (~np.isnan(force) if plan.entry_rsi is not None else True)
    first = int(np.argmax(ready_at)) + 1
    for i in range(first, len(c)):
        # 第 1 步：成交上一根挂出的单
        if pending and shares == 0:
            price = o[i]
            step = plan.stop_atr * atr[i - 1] if plan.stop_atr else np.nan
            want = (value(price) * plan.risk / step if plan.stop_atr
                    else value(price) * plan.fraction / price)
            size = min(want, value(price) / (price * (1 + plan.fee_rate)))
            if size > 0:
                if direction > 0:
                    account.buy(price, size, plan.fee_rate)
                else:
                    account.cash += price * size * (1 - plan.fee_rate)
                    account.fees += price * size * plan.fee_rate
                shares, entry_price, opened_at = size, price, i
                stop = price - direction * step if plan.stop_atr else -direction * np.inf
                risk_amount = size * step if plan.stop_atr else size * price
            pending = False

        # 第 2 步：出场
        if shares > 0:
            if plan.stop_atr and ((direction > 0 and l[i] <= stop) or (direction < 0 and h[i] >= stop)):
                close_out(i, (min(o[i], stop) if direction > 0 else max(o[i], stop)), "止损")
            elif (direction > 0 and z[i] >= plan.exit_z) or (direction < 0 and z[i] <= -plan.exit_z):
                close_out(i, c[i], "回到均线")
            elif i - opened_at >= plan.max_bars:
                close_out(i, c[i], "时间到")

        # 第 3 步：估值
        current = value(c[i])
        error = max(error, abs(account.cash + direction * shares * c[i] - current))
        curve.append(current)

        # 第 4 步：用这一根的收盘价算信号，挂下一根的单
        if shares == 0 and not pending and atr[i] > 0:
            if plan.entry_rsi is not None:
                ready = (force[i] < plan.entry_rsi if direction > 0
                         else force[i] > 100 - plan.entry_rsi)
            else:
                stretched = z[i] <= plan.entry_z if direction > 0 else z[i] >= -plan.entry_z
                long_enough = (runs[i] <= -plan.entry_streak if direction > 0
                               else runs[i] >= plan.entry_streak)
                ready = stretched and (not plan.entry_streak or long_enough)
            if ready:
                pending = True

    if shares > 0:
        close_out(len(c) - 1, c[-1], "未平仓")
    columns = ["进场日", "进场价", "数量", "出场日", "出场价", "原因", "盈亏", "R", "收益", "根数"]
    return {"资金曲线": pd.Series(curve, index=df.index[first:], name="权益"),
            "交易": pd.DataFrame(trades, columns=columns),
            "手续费合计": account.fees, "记账误差": error}


# ---------------------------------------------------------------------------
# 三、结构与组合
# ---------------------------------------------------------------------------

def worst_trades(returns, tops=(1, 3, 5, 10)) -> pd.DataFrame:
    """把**最亏**的几笔拿掉，还剩多少——第 31 篇 `trend.contribution` 的镜像。

    趋势跟随问的是「拿掉最赚的几笔还剩多少」（答案：什么都不剩）；
    均值回归要问的是反过来的那一句：**如果那几次最深的坑没踩到，成绩会好多少？**
    比值越大，说明这条策略越依赖「那几次没出事」。
    """
    values = pd.Series(returns).dropna().astype(float).sort_values()
    total = values.sum()
    rows = [{"拿掉最亏的几笔": 0, "剩下多少": total, "变成原来的": 1.0, "占总笔数": 0.0}]
    for n in tops:
        if n >= len(values):
            break
        left = total - values.iloc[:n].sum()
        rows.append({"拿掉最亏的几笔": n, "剩下多少": left,
                     "变成原来的": left / total if total else np.nan, "占总笔数": n / len(values)})
    return pd.DataFrame(rows)


def blend(curves: dict[str, pd.Series], weights=None, rebalance: str = "ME") -> pd.Series:
    """把几条资金曲线合成一个账户：按权重分钱，按 `rebalance` 的周期调回目标比例。

    ⚠️ 必须**再平衡**才算一个账户。不再平衡只是把两条曲线加起来，
    赚得多的那条会越占越大，最后你量到的是它一个人的性质（第 26 篇量过资金分配的影响）。
    `rebalance=None` 就是不调，留着做对照。
    """
    frame = pd.concat(curves, axis=1).ffill().dropna()
    if weights is None:
        weights = np.full(frame.shape[1], 1 / frame.shape[1])
    weights = np.asarray(weights, dtype=float)
    if len(weights) != frame.shape[1] or not np.isclose(weights.sum(), 1.0):
        raise ValueError("权重个数要和曲线条数一致，而且加起来等于 1")
    steps = frame.pct_change().fillna(0.0).to_numpy()
    marks = (pd.Series(1, index=frame.index).resample(rebalance).last().index
             if rebalance else pd.DatetimeIndex([]))
    holding, total, out = weights.copy(), 1.0, []
    for k, when in enumerate(frame.index):
        holding = holding * (1 + steps[k])
        total_now = holding.sum()
        out.append(total * total_now)
        holding = holding / total_now
        total = total * total_now
        if rebalance and when in marks:
            holding = weights.copy()
    return pd.Series(out, index=frame.index, name="组合") * float(frame.iloc[0].mean())
