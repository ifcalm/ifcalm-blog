"""talab.trend：趋势跟随与突破。第 31 篇。

第六部分讲完了怎么检验，这一篇开始讲**被检验的东西**：一类真实存在、公开了四十年、
到现在还有人靠它管钱的策略原型。

趋势跟随的全部内容可以写成一句话：**价格创新高就买，跌破就走。**
它没有预测，没有估值，没有「这次不一样」。它唯一的假设是——

> 大的行情会持续得比大多数人愿意相信的更久，而小的行情会来回震荡。

这个假设**大部分时候是错的**（第 31 篇实测：七成的突破是假的），
但它错的时候亏得少、对的时候赚得多。这个模块就是把这句话拆成可以测量的零件：

1. **通道与突破**：`donchian`、`breakouts`、`follow_through`
2. **海龟系统**：`TurtlePlan` + `turtle`（含 2N 止损、按 N 定仓位、金字塔加仓）
3. **收益结构**：`r_profile`、`contribution`、`convexity`

⚠️ **通道突破是这门课里唯一可以「当根成交」的信号**：通道那条线是用**前面几根**的
最高价算出来的，开盘之前就已经画好了，价格在这一根里碰到它是一件**当时就能看见**的事。
这和第 27 篇「收盘算出来的信号只能下一根成交」不矛盾——那条规矩管的是用到**当根收盘价**
的信号（均线、RSI、收盘价创新高）。判据始终是同一句：**这个数，在那一刻能不能算出来。**
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from talab.backtest import Account

SIDES = ("long", "short", "both")
FILLS = ("touch", "next_open")


# ---------------------------------------------------------------------------
# 一、唐奇安通道与突破
# ---------------------------------------------------------------------------

def donchian(high: pd.Series, low: pd.Series, n: int = 20) -> pd.DataFrame:
    """唐奇安通道：过去 n 根的最高价、最低价，以及两者的中点。

    ⚠️ 两条轨都 `shift(1)`：**第 i 根上用的是第 i−1 根为止的最高价**。
    不推迟的话，「创 20 日新高」这个条件会永远成立（今天的最高价当然是包含今天的最高价之一）。
    """
    return pd.DataFrame({
        "上轨": high.rolling(n).max().shift(1),
        "下轨": low.rolling(n).min().shift(1),
    }).assign(中轨=lambda t: (t["上轨"] + t["下轨"]) / 2)


def breakouts(df: pd.DataFrame, n: int = 20, horizon: int = 20) -> pd.DataFrame:
    """每一次**向上**突破 n 日通道：突破时的价格，以及之后 horizon 根里发生了什么。

    连续多根都在通道上方只算**一次**突破（第一次算，后面的不算），
    否则一段大趋势会被数成几十次「突破」，假突破的比例就被稀释成假的。
    """
    channel = donchian(df["high"], df["low"], n)
    high, low, close = (df[x].to_numpy(float) for x in ["high", "low", "close"])
    upper = channel["上轨"].to_numpy()
    rows, armed = [], True
    for i in range(len(close)):
        if np.isnan(upper[i]):
            continue
        if high[i] > upper[i]:
            if armed:
                ahead = close[i + 1:i + 1 + horizon]
                worst = low[i + 1:i + 1 + horizon]
                rows.append({"时间": df.index[i], "突破价": upper[i], "收盘": close[i],
                             "之后最高收盘": float(ahead.max()) if len(ahead) else np.nan,
                             "之后最低价": float(worst.min()) if len(worst) else np.nan,
                             f"{horizon} 根后": float(ahead[-1]) if len(ahead) == horizon else np.nan})
                armed = False
        elif close[i] < upper[i]:
            armed = True                                  # 回到通道里面，下一次才算新的突破
    out = pd.DataFrame(rows)
    if len(out):
        out["之后涨幅"] = out[f"{horizon} 根后"] / out["突破价"] - 1
        out["最大顺势"] = out["之后最高收盘"] / out["突破价"] - 1
        out["最大逆势"] = out["之后最低价"] / out["突破价"] - 1
    return out


def follow_through(table: pd.DataFrame, threshold: float = 0.0) -> pd.Series:
    """一批突破里，有多少是「走出去了」的，有多少是假的。

    `threshold` 是判定标准（`之后涨幅` 要超过它才算真）。默认 0：**只要没回到突破价以下就算真**——
    这已经是最宽松的口径了，而第 31 篇实测下来仍然只有三成多能过。
    """
    real = table["之后涨幅"] > threshold
    return pd.Series({
        "突破次数": float(len(table)), "走出去的": float(real.sum()),
        "假突破比例": float((~real).mean()),
        "真的那些平均涨": float(table.loc[real, "之后涨幅"].mean()) if real.any() else np.nan,
        "假的那些平均跌": float(table.loc[~real, "之后涨幅"].mean()) if (~real).any() else np.nan,
        "全部平均": float(table["之后涨幅"].mean()),
        "最大顺势中位": float(table["最大顺势"].median()),
        "最大逆势中位": float(table["最大逆势"].median()),
    })


# ---------------------------------------------------------------------------
# 二、海龟系统
# ---------------------------------------------------------------------------

@dataclass
class TurtlePlan:
    """海龟交易法则，1983 年那一版的核心设定。

    原版有两套系统：系统一是 20 日突破进、10 日突破出，系统二是 55 日进、20 日出。
    这里用同一个 dataclass 表示，改两个数字就换系统。
    """
    entry: int = 20                        # 进场：突破几日通道
    exit: int = 10                         # 出场：反向几日通道
    atr_period: int = 20                   # N（原版就叫 N，其实是 20 日 ATR）
    stop_atr: float = 2.0                  # 止损放在进场价外几个 N
    risk: float = 0.01                     # 一个「单位」冒账户的百分之几
    max_units: int = 4                     # 最多加到几个单位
    add_atr: float = 0.5                   # 每走几个 N 加一个单位
    side: str = "long"                     # long / short / both
    fill: str = "touch"                    # touch：碰到通道就成交；next_open：等下一根开盘
    fee_rate: float = 0.0                  # 单边费率（第 28 篇）

    def __post_init__(self):
        if self.side not in SIDES:
            raise ValueError(f"side 只能是 {SIDES} 之一，收到 {self.side!r}")
        if self.fill not in FILLS:
            raise ValueError(f"fill 只能是 {FILLS} 之一，收到 {self.fill!r}")
        if self.entry < 2 or self.exit < 2 or self.atr_period < 2:
            raise ValueError("三个窗口都要至少是 2")
        if self.max_units < 1:
            raise ValueError("至少要允许一个单位")

    def describe(self) -> pd.Series:
        return pd.Series({
            "进场": f"突破 {self.entry} 日通道",
            "出场": f"反向突破 {self.exit} 日通道",
            "N": f"{self.atr_period} 日 ATR",
            "初始止损": f"{self.stop_atr} 个 N",
            "一个单位的风险": f"账户的 {self.risk:.1%}",
            "加仓": f"每走 {self.add_atr} 个 N 加一个单位，最多 {self.max_units} 个",
            "方向": {"long": "只做多", "short": "只做空", "both": "多空都做"}[self.side],
            "成交": {"touch": "碰到通道就成交", "next_open": "等下一根开盘"}[self.fill],
        })


def turtle(df: pd.DataFrame, plan: TurtlePlan | None = None, equity: float = 100_000.0) -> dict:
    """按海龟法则跑一遍历史。

    每一根 K 线上按固定顺序做五件事（和第 27 篇的引擎同一套规矩）：

    0. **补成交**：`fill="next_open"` 时，上一根定下来的动作用这一根的开盘价成交
    1. **出场**：先看止损，再看反向通道；两个都碰到时按**先止损**算（悲观口径）
    2. **加仓**：价格又顺走了 `add_atr` 个 N 就加一个单位，并把**全部**止损上移
    3. **估值**：按收盘价记权益
    4. **进场**：空仓时，价格碰到 `entry` 日通道就进

    通道线来自前面几根，所以 1、2、4 默认在**当根**成交（见模块开头那条 ⚠️）。
    把 `fill` 换成 `"next_open"` 就能量出「当根成交」这个假设值多少钱——
    如果它值很多，那说明这条策略靠的是那一瞬间的价格，不是趋势。
    返回资金曲线、逐笔交易（一整个仓位算一笔，带 R 倍数）、每一次加仓的明细。
    """
    from talab import indicators as I

    plan = plan or TurtlePlan()
    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    n_value = I.atr(df["high"], df["low"], df["close"], plan.atr_period).shift(1).to_numpy()
    enter = donchian(df["high"], df["low"], plan.entry)
    leave = donchian(df["high"], df["low"], plan.exit)
    up_in, down_in = enter["上轨"].to_numpy(), enter["下轨"].to_numpy()
    up_out, down_out = leave["上轨"].to_numpy(), leave["下轨"].to_numpy()

    # ⚠️ 空头的数量只记在 `units` 里，`account.shares` 全程是 0——
    # 所以权益一律用下面的 `position_value` 算，不要用 `account.equity`。
    account = Account(cash=float(equity))
    curve, trades, adds, error = [], [], [], 0.0
    side = 0                                   # +1 做多，−1 做空，0 空仓
    units: list[tuple[float, float]] = []      # 每个单位的（成交价，数量）
    stop = last_price = risk_amount = np.nan
    opened_at = -1

    def position_value(price: float) -> float:
        """权益：做多是「现金 + 持仓市值」，做空是「现金 − 买回来要花的钱」。

        ⚠️ 做空时卖出所得已经记在现金里了，所以**不要再减一次借来的钱**——
        第一版就是这么写的，结果最大回撤算出 −106%（权益跑到 0 以下）。
        「回撤超过 100%」永远是记账错了，不是策略真的这么惨。
        """
        held = sum(q for _, q in units)
        return account.cash + side * held * price

    def close_all(i: int, price: float, reason: str) -> None:
        nonlocal side, units, stop, opened_at
        held = sum(q for _, q in units)
        cost = sum(p * q for p, q in units)
        if side > 0:
            account.sell(price, held, plan.fee_rate)
            profit = price * held - cost - abs(price * held) * plan.fee_rate
        else:
            account.cash -= price * held * (1 + plan.fee_rate)      # 买回来平掉空头
            account.fees += price * held * plan.fee_rate
            profit = cost - price * held - abs(price * held) * plan.fee_rate
        trades.append({"进场日": df.index[opened_at], "方向": "多" if side > 0 else "空",
                       "第一个单位的价": units[0][0], "平均价": cost / held if held else np.nan,
                       "单位数": len(units), "出场日": df.index[i], "出场价": price,
                       "原因": reason, "盈亏": profit, "R": profit / risk_amount,
                       "根数": i - opened_at})
        side, units, stop, opened_at = 0, [], np.nan, -1

    def open_unit(i: int, price: float, direction: int) -> bool:
        nonlocal side, stop, last_price, risk_amount
        step = plan.stop_atr * n_value[i]
        want = position_value(price) * plan.risk / step          # 一个单位：冒账户的 risk
        if direction > 0:
            shares = min(want, account.affordable(price, plan.fee_rate))
        else:
            shares = min(want, position_value(price) / (price * (1 + plan.fee_rate)))
        if shares <= 1e-12:
            return False                                         # 买不起了：别再往下加
        if direction > 0:
            account.buy(price, shares, plan.fee_rate)
        else:
            account.cash += price * shares * (1 - plan.fee_rate)
            account.fees += price * shares * plan.fee_rate
        if not units:
            side = direction
            risk_amount = shares * step                          # 1R = 第一个单位的初始风险
        units.append((price, shares))
        last_price = price
        stop = price - direction * step                          # 加仓之后全部止损跟着走
        adds.append({"时间": df.index[i], "第几个单位": len(units), "成交价": price,
                     "数量": shares, "止损移到": stop})
        return True

    first = int(np.argmax(~np.isnan(n_value) & ~np.isnan(up_in) & ~np.isnan(down_in)))
    pending: tuple | None = None               # fill="next_open" 时挂着的动作
    for i in range(first, len(c)):
        # 第 0 步：上一根定下来的动作，用这一根的开盘价成交
        if pending is not None:
            what, extra = pending
            pending = None
            if what == "close" and side:
                close_all(i, o[i], extra)
            elif what == "add" and side and len(units) < plan.max_units:
                open_unit(i, o[i], side)
            elif what == "open" and not side:
                opened_at = i
                open_unit(i, o[i], extra)

        # 第 1 步：出场
        later = plan.fill == "next_open"
        if side > 0:
            if l[i] <= stop:
                pending = ("close", "止损") if later else pending
                if not later:
                    close_all(i, min(o[i], stop), "止损")
            elif l[i] <= down_out[i]:
                pending = ("close", "通道出场") if later else pending
                if not later:
                    close_all(i, min(o[i], down_out[i]), "通道出场")
        elif side < 0:
            if h[i] >= stop:
                pending = ("close", "止损") if later else pending
                if not later:
                    close_all(i, max(o[i], stop), "止损")
            elif h[i] >= up_out[i]:
                pending = ("close", "通道出场") if later else pending
                if not later:
                    close_all(i, max(o[i], up_out[i]), "通道出场")

        # 第 2 步：加仓
        while side and pending is None and len(units) < plan.max_units:
            level = last_price + side * plan.add_atr * n_value[i]
            if side > 0 and h[i] >= level:
                if later:
                    pending = ("add", None)
                    break
                if not open_unit(i, max(o[i], level), 1):
                    break
            elif side < 0 and l[i] <= level:
                if later:
                    pending = ("add", None)
                    break
                if not open_unit(i, min(o[i], level), -1):
                    break
            else:
                break

        # 第 3 步：估值
        value = position_value(c[i])
        held = sum(q for _, q in units)
        error = max(error, abs(account.cash + side * held * c[i] - value))
        curve.append(value)

        # 第 4 步：进场
        if not side and pending is None and n_value[i] > 0:
            if plan.side in ("long", "both") and h[i] > up_in[i]:
                if later:
                    pending = ("open", 1)
                else:
                    opened_at = i
                    open_unit(i, max(o[i], up_in[i]), 1)
            elif plan.side in ("short", "both") and l[i] < down_in[i]:
                if later:
                    pending = ("open", -1)
                else:
                    opened_at = i
                    open_unit(i, min(o[i], down_in[i]), -1)

    if side:                                                     # 最后一根还拿着
        close_all(len(c) - 1, c[-1], "未平仓")
    index = df.index[first:]
    columns = ["进场日", "方向", "第一个单位的价", "平均价", "单位数", "出场日", "出场价",
               "原因", "盈亏", "R", "根数"]
    return {"资金曲线": pd.Series(curve, index=index, name="权益"),
            "交易": pd.DataFrame(trades, columns=columns),
            "加仓": pd.DataFrame(adds, columns=["时间", "第几个单位", "成交价", "数量", "止损移到"]),
            "手续费合计": account.fees, "记账误差": error,
            "权益最低点": float(min(curve)) if curve else np.nan}


# ---------------------------------------------------------------------------
# 三、收益结构
# ---------------------------------------------------------------------------

def r_profile(r) -> pd.Series:
    """一串 R 倍数的形状：胜率、盈亏比、期望，以及**偏度**。

    趋势跟随的招牌是「胜率低、盈亏比高、偏度为正」。
    第 23 篇的 `risk.expectancy` 给的是前两项，这里补上尾巴那一头——
    **正偏度的意思是「亏损可以预料，盈利不可以」**，而策略的全部收益都藏在那个不可预料的尾巴里。
    """
    r = pd.Series(r).dropna().astype(float)
    wins, losses = r[r > 0], r[r <= 0]
    return pd.Series({
        "笔数": float(len(r)), "胜率": float((r > 0).mean()),
        "平均盈利 R": float(wins.mean()) if len(wins) else 0.0,
        "平均亏损 R": float(-losses.mean()) if len(losses) else 0.0,
        "盈亏比": float(wins.mean() / -losses.mean()) if len(losses) and losses.mean() else np.inf,
        "期望 R": float(r.mean()), "中位 R": float(r.median()),
        "偏度": float(r.skew()), "最大一笔 R": float(r.max()), "最差一笔 R": float(r.min()),
        "合计 R": float(r.sum()),
    })


def contribution(r, tops=(1, 3, 5, 10)) -> pd.DataFrame:
    """把最赚钱的几笔拿掉，还剩多少。

    这张表回答一个很不舒服的问题：**这条策略的收益，有多少集中在极少数几笔上？**
    集中度高不是缺点，是趋势跟随的**定义**——但你必须知道它有多高，
    因为那意味着「错过那几笔」和「策略失效」在账户上是同一件事。
    """
    r = pd.Series(r).dropna().astype(float).sort_values(ascending=False)
    total = r.sum()
    rows = [{"拿掉最赚的几笔": 0, "剩下多少 R": total, "占原来的": 1.0, "占总笔数": 0.0}]
    for n in tops:
        if n >= len(r):
            break
        left = total - r.iloc[:n].sum()
        rows.append({"拿掉最赚的几笔": n, "剩下多少 R": left, "占原来的": left / total if total else np.nan,
                     "占总笔数": n / len(r)})
    return pd.DataFrame(rows)


def convexity(strategy: pd.Series, market: pd.Series, buckets: int = 5,
              window: int = 20) -> pd.DataFrame:
    """凸性表：把市场按 `window` 根的涨跌分成几组，看策略在每一组里赚多少。

    趋势跟随的收益应该是一条**微笑曲线**——市场大涨时赚、市场大跌时也赚（或者至少不怎么亏）、
    市场不涨不跌时小亏。这个形状和「买了一份跨式期权」是一回事，
    小亏就是权利金。第 32 篇的均值回归会给出正好相反的形状（凹性）。
    """
    if not 0 < buckets <= 20:
        raise ValueError("buckets 要在 1 和 20 之间")
    both = pd.concat([strategy.rename("策略"), market.rename("市场")], axis=1).dropna()
    rolled = pd.DataFrame({
        "策略": (1 + both["策略"]).rolling(window).apply(np.prod, raw=True) - 1,
        "市场": (1 + both["市场"]).rolling(window).apply(np.prod, raw=True) - 1,
    }).dropna()
    groups = pd.qcut(rolled["市场"], buckets, labels=False, duplicates="drop")
    out = rolled.groupby(groups).agg(根数=("市场", "size"), 市场中位=("市场", "median"),
                                     策略中位=("策略", "median"), 策略平均=("策略", "mean"),
                                     策略赚钱的比例=("策略", lambda x: float((x > 0).mean())))
    out.index = [f"第 {i + 1} 组" for i in range(len(out))]
    out.index.name = f"按市场 {window} 根涨跌分组"
    return out
