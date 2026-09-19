"""talab.risk：出场。第 23 篇。

入场只有一个决定：买不买。出场有四个，而且它们互相独立：

1. **初始止损放在哪**：跌到哪个价格算这笔交易看错了？（`stop`）
2. **止损要不要跟着走**：赚了之后，那条线往上移吗？怎么移？（`trail`）
3. **有没有目标价**：涨到哪里就收？（`target_r`）
4. **最多拿多久**：一直不涨也不跌，什么时候放弃？（`max_bars`）

把这四个答案填进 `Exit`，`run` 就能按它跑一遍历史。所有结果都用 **R 倍数**记分：
一个 R 就是这笔交易开仓时冒的风险（进场价减初始止损价）。换成 R 之后，
2018 年一笔 2 美元的止损距离和 2021 年一笔 9,000 美元的止损距离才能放在一起比。

这里和第 21 篇的 `rules.run` 分工不同：`rules.run` 关心整条策略的资金曲线，
`risk.run` 只关心**一笔交易怎么结束**，所以它记的是每笔的 R 倍数、最大浮盈和最大浮亏。
两边都不算成本、不算滑点（成本是第 29 篇，滑点是第 22 篇）。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

STOPS = ("atr", "structure", "percent")
TRAILS = ("none", "chandelier", "low", "breakeven")
TRIGGERS = ("close", "extreme")


def r_multiple(entry_price: float, stop_price: float, exit_price: float) -> float:
    """这笔交易赚了（亏了）几个 R。

    R = 进场价 − 初始止损价，是开仓那一刻就定下来的、你打算认输的距离。
    严格按初始止损算：止损后来上移了多少，不改变这笔交易当初冒的风险。
    """
    risk = entry_price - stop_price
    if risk <= 0:
        raise ValueError(f"止损价要在进场价下方（进场 {entry_price}，止损 {stop_price}）")
    return (exit_price - entry_price) / risk


@dataclass
class Exit:
    """一套出场方案：四个问题各一个答案。"""
    stop: str = "atr"                 # 一、初始止损：atr / structure / percent
    k: float = 3.0                    #     atr：进场价往下几个 ATR
    lookback: int = 20                #     structure：往前看几根找最低点
    buffer: float = 0.5               #     structure：在那个最低点再往下几个 ATR
    percent: float = 0.10             #     percent：进场价往下百分之几
    trail: str = "none"               # 二、止损要不要跟着走
    trail_k: float = 3.0              #     chandelier：最高价往下几个 ATR
    trail_bars: int = 20              #     low：跟着前几根的最低点走
    trail_r: float = 1.0              #     breakeven：浮盈几个 R 之后把止损提到成本价
    target_r: float | None = None     # 三、目标价：赚到几个 R 就收（None = 不设目标）
    partial_r: float | None = None    #     浮盈几个 R 时先平掉一部分（None = 不分批）
    partial_fraction: float = 0.5     #     分批平掉多少
    max_bars: int | None = None       # 四、最多拿几根 K 线（None = 不限）
    trigger: str = "close"            # 止损和目标用收盘价触发，还是用盘中最高最低价
    atr_period: int = 14

    def __post_init__(self):
        for name, value, allowed in [("stop", self.stop, STOPS), ("trail", self.trail, TRAILS),
                                     ("trigger", self.trigger, TRIGGERS)]:
            if value not in allowed:
                raise ValueError(f"{name} 只能是 {allowed} 之一，收到 {value!r}")
        if not 0 < self.partial_fraction < 1:
            raise ValueError("partial_fraction 要在 0 和 1 之间")
        if self.partial_r is not None and self.target_r is not None and self.partial_r >= self.target_r:
            raise ValueError("分批止盈的位置要在最终目标下方，否则它永远轮不到")

    def describe(self) -> pd.Series:
        """把四个答案列出来，用来检查「这套出场真的想全了吗」。"""
        first = {"atr": f"进场价下方 {self.k} 倍 ATR",
                 "structure": f"前 {self.lookback} 根的最低点再往下 {self.buffer} 倍 ATR",
                 "percent": f"进场价下方 {self.percent:.0%}"}[self.stop]
        second = {"none": "不动，一直用初始止损",
                  "chandelier": f"吊灯：最高价往下 {self.trail_k} 倍 ATR，只上移",
                  "low": f"跟着前 {self.trail_bars} 根的最低点走，只上移",
                  "breakeven": f"浮盈 {self.trail_r} 个 R 之后提到成本价，再不动"}[self.trail]
        third = "不设目标，让它自己走完" if self.target_r is None else f"赚到 {self.target_r} 个 R 就全部离场"
        if self.partial_r is not None:
            third += f"；浮盈 {self.partial_r} 个 R 时先平 {self.partial_fraction:.0%}"
        fourth = "不限" if self.max_bars is None else f"最多 {self.max_bars} 根 K 线"
        return pd.Series({"一、初始止损": first, "二、止损跟不跟": second,
                          "三、目标价": third, "四、最多拿多久": fourth})


def initial_stop(df: pd.DataFrame, i: int, entry_price: float, plan: Exit,
                 atr: np.ndarray | None = None) -> float:
    """第 i 根 K 线上按 `plan` 算初始止损价。

    只用第 i−1 根及之前的数据：ATR 取前一根的值，结构低点取前 `lookback` 根的最低价，
    都不含第 i 根自己——第 i 根的最低价要等收盘才知道，进场那一刻还没有。
    """
    if plan.stop == "percent":
        return entry_price * (1 - plan.percent)
    if atr is None:
        from talab import indicators as I
        atr = I.atr(df["high"], df["low"], df["close"], plan.atr_period).to_numpy()
    if plan.stop == "atr":
        return entry_price - plan.k * atr[i - 1]
    low = df["low"].to_numpy(float)[max(0, i - plan.lookback):i].min()
    return low - plan.buffer * atr[i - 1]


def run(df: pd.DataFrame, entries: pd.Series, plan: Exit | None = None,
        exits: pd.Series | None = None) -> pd.DataFrame:
    """按一套出场方案跑一遍历史，每笔交易一行。

    `exits` 是策略自己的出场信号（比如主线策略的死叉），它和 `plan` 里的四个答案并存：
    谁先到就听谁的，出场信号排在最前面判断。不给 `exits` 就只靠止损、目标和时间出场。

    约定和第 21 篇一致：信号在收盘时成立，下一根开盘市价成交；持仓期间不接新信号。
    进场的那一根也可能就把你打掉——买在开盘价，这根 K 线剩下的时间照样会走。

    止损和目标同时在一根 K 线里被碰到时（只有 `trigger="extreme"` 才可能发生），
    按**止损**算，并在「原因」里记成「同一根」——K 线看不出谁先到（第 22 篇），
    这里选保守的那一边，并且把它数出来，而不是假装没发生。

    返回的表里，「R 倍数」是这笔交易的最终成绩；分批止盈时它是两段的加权平均。
    「最大浮盈」和「最大浮亏」是持仓期间盘中到过的最好和最差的浮动盈亏（MFE 和 MAE），
    它们回答「这笔交易有没有给过你机会」和「你离被打掉有多近」。进场那一根按整根的
    最高最低价算，所以最大浮亏可能比你实际经历的更难看一点。
    """
    plan = plan or Exit()
    from talab import indicators as I
    atr = I.atr(df["high"], df["low"], df["close"], plan.atr_period).to_numpy()
    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    signal = entries.reindex(df.index).fillna(False).to_numpy(bool)
    leave = (np.zeros(len(c), bool) if exits is None
             else exits.reindex(df.index).fillna(False).to_numpy(bool))
    rows, holding = [], False
    entry_price = entry_i = risk = highest = best = worst = done = left = np.nan
    start = int(np.argmax(~np.isnan(atr))) + 2
    for i in range(start, len(c)):
        if not holding and signal[i - 1]:                             # 昨天收盘的信号，今天开盘成交
            price = o[i]
            level = initial_stop(df, i, price, plan, atr)
            if level < price:                                         # 止损要在进场价下方，否则这笔跳过
                holding, entry_price, entry_i, risk = True, price, i, price - level
                stop_price, highest, done, left, best, worst = level, price, 0.0, 1.0, 0.0, 0.0
        if not holding:
            continue
        if plan.trail == "chandelier":
            stop_price = max(stop_price, highest - plan.trail_k * atr[i - 1])
        elif plan.trail == "low":
            stop_price = max(stop_price, l[max(0, i - plan.trail_bars):i].min())
        elif plan.trail == "breakeven" and highest >= entry_price + plan.trail_r * risk:
            stop_price = max(stop_price, entry_price)
        best = max(best, (h[i] - entry_price) / risk)
        worst = min(worst, (l[i] - entry_price) / risk)
        target = entry_price + plan.target_r * risk if plan.target_r is not None else np.inf
        price = reason = None
        if leave[i - 1] and i > entry_i:                               # 昨天收盘的出场信号，今天开盘执行
            price, reason = o[i], "出场信号"
        elif plan.trigger == "close":
            if c[i] <= stop_price:
                price, reason = c[i], "止损"
            elif c[i] >= target:
                price, reason = c[i], "止盈"
        else:
            hit_stop, hit_target = l[i] <= stop_price, h[i] >= target
            if hit_stop and hit_target:
                price, reason = (o[i] if o[i] <= stop_price else stop_price), "同一根"
            elif hit_stop:
                price, reason = (o[i] if o[i] <= stop_price else stop_price), "止损"
            elif hit_target:
                price, reason = (o[i] if o[i] >= target else target), "止盈"
        if reason is None and plan.max_bars is not None and i - entry_i >= plan.max_bars:
            price, reason = c[i], "时间到"
        if reason is None and i == len(c) - 1:
            price, reason = c[i], "未平仓"
        if reason is None and left == 1.0 and plan.partial_r is not None:   # 先平一部分，剩下的接着走
            level = entry_price + plan.partial_r * risk
            got = c[i] if plan.trigger == "close" and c[i] >= level else (max(o[i], level) if plan.trigger == "extreme" and h[i] >= level else None)
            if got is not None:
                done, left = plan.partial_fraction * (got - entry_price) / risk, 1 - plan.partial_fraction
        highest = max(highest, h[i])
        if reason is None:
            continue
        rows.append({"买入日": df.index[entry_i], "买入价": entry_price, "初始止损": entry_price - risk,
                     "R": risk, "卖出日": df.index[i], "卖出价": price, "原因": reason,
                     "R 倍数": done + left * (price - entry_price) / risk,
                     "最大浮盈": best, "最大浮亏": worst, "根数": i - entry_i})
        holding = False
    return pd.DataFrame(rows, columns=["买入日", "买入价", "初始止损", "R", "卖出日", "卖出价", "原因",
                                       "R 倍数", "最大浮盈", "最大浮亏", "根数"])


def expectancy(r: pd.Series | np.ndarray) -> pd.Series:
    """一串 R 倍数的成绩单。

    期望值 = 胜率 × 平均盈利 − 败率 × 平均亏损，它算出来就是这串 R 的平均数——
    那条公式没有多给出任何信息，它的用处是告诉你**能从哪两头去改**：
    提高胜率，或者提高盈亏比。第 23 篇的数据说明这两头往往是此消彼长的。
    """
    r = pd.Series(r).dropna()
    wins, losses = r[r > 0], r[r <= 0]
    win_rate = len(wins) / len(r) if len(r) else np.nan
    avg_win = wins.mean() if len(wins) else 0.0
    avg_loss = -losses.mean() if len(losses) else 0.0
    return pd.Series({
        "交易数": float(len(r)),
        "胜率": win_rate,
        "平均盈利": avg_win,
        "平均亏损": avg_loss,
        "盈亏比": avg_win / avg_loss if avg_loss else np.inf,
        "期望值": win_rate * avg_win - (1 - win_rate) * avg_loss,
        "中位数": r.median(),
        "最好的一笔": r.max(),
        "最差的一笔": r.min(),
    })


# ---------------------------------------------------------------------------
# 四、杠杆：保证金、强平价、持仓成本（第 24 篇）
# ---------------------------------------------------------------------------

def margin_tier(notional: float, brackets: pd.DataFrame) -> pd.Series:
    """名义价值落在哪一档：返回这一档的维持保证金率、速算额和允许的最大杠杆。

    `brackets` 是 `data.load_binance_brackets` 读出来的表。档位是按**名义价值**分的，
    和你选的杠杆无关：仓位越大，交易所要求的维持保证金率越高。
    """
    row = brackets[(brackets["下限"] < notional) & (notional <= brackets["上限"])]
    if row.empty:
        row = brackets.iloc[[0]] if notional <= brackets["上限"].iloc[0] else brackets.iloc[[-1]]
    return row.iloc[0]


def maintenance_margin(notional: float, brackets: pd.DataFrame) -> float:
    """维持保证金 = 名义价值 × 这一档的维持保证金率 − 这一档的速算额。

    速算额是为了让档位之间连续：跨到下一档时，只有超出的部分按新费率算。
    """
    tier = margin_tier(notional, brackets)
    return notional * tier["维持保证金率"] - tier["速算额"]


def liquidation_price(entry_price: float, leverage: float, side: str = "long",
                      mmr: float = 0.004, amount_ratio: float = 0.0, spent: float = 0.0,
                      notional: float | None = None, brackets: pd.DataFrame | None = None) -> float:
    """逐仓仓位的强平价：价格走到这里，账户权益正好等于维持保证金。

    推导（数量 Q、方向 s = +1 做多 / −1 做空、保证金 WB、名义价值 N = Q × 进场价）：

    > WB + s × Q × (P − 进场价) = Q × P × 维持保证金率 − 速算额

    左边是权益，右边是维持保证金。两边同除以 Q，用 wb = WB ÷ N 表示保证金占名义价值的比例、
    用 amount_ratio = 速算额 ÷ N 表示速算额，解出来就是

    > 强平价 = 进场价 × (s − wb − amount_ratio) ÷ (s − 维持保证金率)

    `spent` 是已经从保证金里扣掉的东西（手续费、累计资金费），按占名义价值的比例给。
    给了 `notional` 和 `brackets` 就自动查档，`mmr` 和 `amount_ratio` 由表决定。

    ⚠️ 档位按名义价值分，而名义价值随价格变化。这里用**开仓时**的档位算，
    仓位在一档之内时是精确的。
    ⚠️ 触发强平的是**标记价格**，不是最新成交价（第 22 篇）。
    """
    if side not in ("long", "short"):
        raise ValueError(f"side 只能是 long 或 short，收到 {side!r}")
    if brackets is not None:
        if notional is None:
            raise ValueError("要查档就得给名义价值 notional")
        tier = margin_tier(notional, brackets)
        mmr, amount_ratio = float(tier["维持保证金率"]), float(tier["速算额"]) / notional
    s = 1.0 if side == "long" else -1.0
    wb = 1.0 / leverage - spent                       # 保证金占名义价值的比例
    return max(entry_price * (s - wb - amount_ratio) / (s - mmr), 0.0)


def max_leverage(stop_distance: float, side: str = "long", mmr: float = 0.004,
                 cushion: float = 0.0) -> float:
    """止损距离是 `stop_distance`（占进场价的比例）时，强平价还在止损价之外的最大杠杆。

    强平价必须在止损价**之外**：止损是你自己认输的地方，强平是交易所替你认输的地方，
    后者先到的话，你的止损就是一句空话（第 23 篇）。`cushion` 是额外留出的余量，
    比如 0.02 表示「强平价还要再远 2 个百分点」，用来盖住滑点和持仓期间的资金费。
    """
    if side not in ("long", "short"):
        raise ValueError(f"side 只能是 long 或 short，收到 {side!r}")
    d = stop_distance + cushion
    gap = 1 - (1 - d) * (1 - mmr) if side == "long" else (1 + d) * (1 + mmr) - 1
    if gap <= 0:
        return np.inf
    return 1 / gap


def replay_liquidation(df: pd.DataFrame, leverage: float, side: str = "long", horizon: int = 30,
                       mmr: float = 0.004, prices: pd.DataFrame | None = None) -> pd.Series:
    """历史重放：每一根 K 线的开盘价开一个 `leverage` 倍的仓，`horizon` 根之内有没有被强平。

    `prices` 给标记价格时用它判断强平（第 22 篇），不给就用 `df` 自己的最高最低价。
    最后 `horizon` 根没有完整的观察窗口，返回 NaN。
    """
    judge = df if prices is None else prices.reindex(df.index)
    entry = df["open"].to_numpy(float)
    level = liquidation_price(1.0, leverage, side, mmr) * entry
    if side == "long":
        worst = judge["low"].rolling(horizon, min_periods=horizon).min().shift(-horizon + 1)
        hit = worst.to_numpy() <= level
    else:
        worst = judge["high"].rolling(horizon, min_periods=horizon).max().shift(-horizon + 1)
        hit = worst.to_numpy() >= level
    out = pd.Series(hit, index=df.index, dtype="float64")
    out.iloc[-(horizon - 1):] = np.nan
    return out


def funding_cost(funding: pd.Series, start, end, side: str = "long") -> float:
    """一段持仓期间的资金费，按占名义价值的比例算，**正数表示你付出去**。

    资金费率为正时多头付给空头，为负时反过来。这里把每次结算的费率直接相加
    （没有按名义价值的变化加权），和交易所实际扣的钱会差一点。
    """
    if side not in ("long", "short"):
        raise ValueError(f"side 只能是 long 或 short，收到 {side!r}")
    window = funding.loc[(funding.index > start) & (funding.index <= end)]
    return float(window.sum()) * (1.0 if side == "long" else -1.0)
