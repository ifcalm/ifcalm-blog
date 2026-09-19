"""talab.backtest：回测引擎。第 27 篇。

回测是一台飞行模拟器：它要在地面上把飞行重演一遍，重演得越像，你在上面练出来的东西才越有用。
模拟器最容易出的毛病不是「不够精细」，是**它偷偷告诉了你未来**——提前三秒提示下沉气流，
你当然飞得又稳又好，但那不是飞行。

所以这个模块的第一条规矩不是关于收益的，是关于时钟的：

> **第 i 根 K 线收盘时算出来的东西，最早只能在第 i+1 根上成交。**

围绕这条规矩，模块分四部分：

1. **向量化**：`vectorized` 和 `lag_test`——一行代码就能写完的回测，以及怎么检查它有没有偷看。
2. **盘中路径**：`first_touch`——同一根 K 线里止损和止盈都被碰到，先算哪个？
   K 线只有四个数，这件事**从数据上无法判断**，所以它是一个假设，必须显式写出来。
3. **记账**：`Account`——现金、持仓、权益三个数必须时时自洽，手续费从现金里扣。
   `rules.run`（第 21 篇）只算收益率，算不出「这笔钱够不够买」。
4. **事件驱动**：`Plan` 和 `run`——一根一根推进，每一根上按固定顺序做四件事。

⚠️ 这个模块只负责**把重演做对**。偏差（幸存者、数据窥探、复权）和真实成本是第 28 篇，
怎么评价跑出来的结果是第 29 篇。`fee_rate` 这个口子留在这里，数字由第 28 篇填。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

PATHS = ("pessimistic", "optimistic", "coin")
FILLS = ("next_open", "close")
STOPS = ("none", "chandelier", "percent")
SIZINGS = ("full", "risk")


# ---------------------------------------------------------------------------
# 一、向量化：一行代码的回测，和它的体检
# ---------------------------------------------------------------------------

def vectorized(close: pd.Series, position: pd.Series, lag: int = 1, fee_rate: float = 0.0) -> pd.Series:
    """向量化回测：仓位乘以收益，一行就算完。

    `position` 是**收盘时算出来的目标仓位**（0 到 1）。`lag=1` 表示它最早在下一根生效——
    这是本模块的时钟规矩。写 `lag=0` 就是声称「今天收盘才算得出来的仓位，今天一整天都拿着」，
    也就是第 27 篇决策点里那一行错误代码。

    手续费按仓位变化收：仓位从 0 变 1 收一次，从 1 变 0 再收一次。
    """
    if lag < 0:
        raise ValueError("lag 不能是负数（那是明目张胆地用未来）")
    held = position.reindex(close.index).fillna(0.0).shift(lag).fillna(0.0)
    turnover = held.diff().abs().fillna(held.abs())
    return (held * close.pct_change().fillna(0.0) - turnover * fee_rate).rename("收益")


def lag_test(close: pd.Series, position: pd.Series, lags=(0, 1, 2, 3),
             periods_per_year: int = 365) -> pd.DataFrame:
    """把仓位依次往后推一根，看结果掉得有多快——查「有没有偷看未来」的通用体检。

    一条真策略的收益来自「信号之后价格继续走」，推迟一根只会让它**温和地**变差。
    推迟一根就塌掉，说明原来那个版本赚的是**信号当根自己的涨幅**，
    而那一根的涨幅正是算出信号的原料。
    """
    rows = []
    for lag in lags:
        returns = vectorized(close, position, lag)
        equity = (1 + returns).cumprod()
        in_market = vectorized(close, position, lag) != 0
        rows.append({"推迟根数": lag,
                     "年化": equity.iloc[-1] ** (periods_per_year / len(returns)) - 1,
                     "最大回撤": float((equity / equity.cummax() - 1).min()),
                     "持仓根里上涨的比例": float((returns[in_market] > 0).mean()) if in_market.any() else np.nan})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 二、盘中路径：K 线里面发生了什么，数据没说
# ---------------------------------------------------------------------------

def first_touch(bar, stop: float, target: float, path: str = "pessimistic",
                rng: np.random.Generator | None = None) -> str:
    """一根 K 线上，止损和止盈谁先到（做多的口径）。

    只碰到一个，答案是确定的。**两个都碰到，K 线上就看不出顺序了**——
    开盘、最高、最低、收盘四个数里没有时间。这时按 `path` 给出的假设回答：

    - `"pessimistic"`：算止损先到（回测该用的默认值：宁可低估自己）
    - `"optimistic"`：算止盈先到（回测最常见、也最贵的那个错误）
    - `"coin"`：抛硬币（需要 `rng`；它比前两个都接近真相，但每跑一次结果都不一样）

    ⚠️ 换成更细的 K 线能把「两个都碰到」的比例压下去，但压不到 0：
    只要还是 K 线，就还有这一根内部。
    """
    if path not in PATHS:
        raise ValueError(f"path 只能是 {PATHS} 之一，收到 {path!r}")
    hit_stop, hit_target = bar["low"] <= stop, bar["high"] >= target
    if not hit_stop and not hit_target:
        return "都没碰到"
    if hit_stop and not hit_target:
        return "止损"
    if hit_target and not hit_stop:
        return "止盈"
    if path == "pessimistic":
        return "止损"
    if path == "optimistic":
        return "止盈"
    if rng is None:
        raise ValueError('path="coin" 要给一个 numpy 的随机数发生器，好让结果可复现')
    return "止盈" if rng.random() < 0.5 else "止损"


def limit_filled(bar, level: float, side: str = "buy", through: float = 0.0) -> bool:
    """限价单在这根 K 线上算不算成交。

    `through=0` 就是回测默认的「碰到就成交」。真实的限价单要排队，**碰到不等于轮到你**：
    价格只是擦了一下限价就掉头，那一分钟的成交量可能根本轮不到你的单子。
    `through=0.001` 表示「价格要穿过限价 0.1% 才算我成交」，用来量这个假设值多少钱。
    """
    if side not in ("buy", "sell"):
        raise ValueError(f"side 只能是 buy 或 sell，收到 {side!r}")
    return bool(bar["low"] <= level * (1 - through) if side == "buy"
                else bar["high"] >= level * (1 + through))


# ---------------------------------------------------------------------------
# 三、记账：现金、持仓、权益
# ---------------------------------------------------------------------------

@dataclass
class Account:
    """一个自洽的账本：任何时刻 **现金 + 持仓数量 × 价格 = 权益**。

    `rules.run` 只算收益率，永远「买得起」。真实账户不是：手续费从现金里扣，
    扣完之后能买的数量就少了一点点，这一点点会随着交易次数复利。
    """
    cash: float
    shares: float = 0.0
    fees: float = 0.0

    def equity(self, price: float) -> float:
        return self.cash + self.shares * price

    def affordable(self, price: float, fee_rate: float = 0.0) -> float:
        """现金最多买得起多少（把手续费也算进去）。"""
        return self.cash / (price * (1 + fee_rate))

    def buy(self, price: float, shares: float, fee_rate: float = 0.0) -> float:
        cost = shares * price
        fee = cost * fee_rate
        if cost + fee > self.cash + 1e-9:
            raise ValueError(f"现金不够：要 {cost + fee:.2f}，只有 {self.cash:.2f}")
        self.cash -= cost + fee
        self.shares += shares
        self.fees += fee
        return fee

    def sell(self, price: float, shares: float, fee_rate: float = 0.0) -> float:
        if shares > self.shares + 1e-9:
            raise ValueError(f"持仓不够：要卖 {shares}，只有 {self.shares}")
        proceeds = shares * price
        fee = proceeds * fee_rate
        self.cash += proceeds - fee
        self.shares -= shares
        self.fees += fee
        return fee


# ---------------------------------------------------------------------------
# 四、事件驱动：一根一根推进
# ---------------------------------------------------------------------------

@dataclass
class Plan:
    """一次回测的全部设定。前五项和第 21 篇的 `Rule` 一一对应，后面几项是这一篇新加的。"""
    entry: pd.Series                       # 收盘时成立的入场信号
    exit: pd.Series                        # 收盘时成立的出场信号
    fill: str = "next_open"                # 下一根开盘成交，还是当根收盘成交
    stop: str = "chandelier"               # none / chandelier / percent
    k: float = 3.0                         # chandelier：最高价往下几个 ATR
    stop_percent: float = 0.10
    trigger: str = "close"                 # 止损用收盘价还是盘中最低价触发（第 20 篇）
    target_r: float | None = None          # 止盈目标，按 R 算（第 23 篇）
    path: str = "pessimistic"              # 同一根里止损和止盈都碰到时听谁的
    sizing: str = "full"                   # full / risk（第 26 篇）
    risk_per_trade: float = 0.10
    fee_rate: float = 0.0                  # 单边费率，数字留给第 28 篇
    atr_period: int = 14
    seed: int = 27                         # path="coin" 时的随机种子

    def __post_init__(self):
        for name, value, allowed in [("fill", self.fill, FILLS), ("stop", self.stop, STOPS),
                                     ("path", self.path, PATHS), ("sizing", self.sizing, SIZINGS)]:
            if value not in allowed:
                raise ValueError(f"{name} 只能是 {allowed} 之一，收到 {value!r}")
        if self.target_r is not None and self.trigger == "close" and self.path != "pessimistic":
            raise ValueError("收盘价触发时一根 K 线只有一个收盘价，不存在先后问题，path 没有意义")
        if self.sizing == "risk" and self.stop == "none":
            raise ValueError('没有止损就算不出每笔的风险，sizing="risk" 需要一个止损')

    def describe(self) -> pd.Series:
        return pd.Series({
            "入场方式": {"close": "当根收盘价", "next_open": "下一根开盘价"}[self.fill],
            "初始止损": {"none": "没有", "chandelier": f"{self.k} 倍 ATR 吊灯",
                         "percent": f"进场价下方 {self.stop_percent:.0%}"}[self.stop],
            "止损触发": {"close": "收盘价", "extreme": "盘中最低价"}[self.trigger],
            "止盈目标": "不设" if self.target_r is None else f"{self.target_r} 个 R",
            "同一根里的顺序": {"pessimistic": "算止损先到", "optimistic": "算止盈先到",
                               "coin": "抛硬币"}[self.path],
            "仓位": "满仓" if self.sizing == "full" else f"每笔风险 {self.risk_per_trade:.0%}",
            "单边费率": f"{self.fee_rate:.4%}",
        })


def run(df: pd.DataFrame, plan: Plan, equity: float = 100_000.0) -> dict:
    """事件驱动回测：一根一根推进，每一根上按**固定顺序**做四件事。

    1. **成交**：用上一根收盘时挂出的订单，在这一根上成交（开盘市价单）
    2. **出场**：检查止损、止盈；两个都碰到时按 `plan.path` 决定顺序
    3. **估值**：按这一根的收盘价给账户估值，记下权益
    4. **下单**：用截至这一根的数据算信号，挂出**下一根**的订单

    第 4 步必须排在第 3 步后面，这就是那条时钟规矩。把 3 和 4 调个个儿，
    或者把第 4 步算出来的信号拿到第 2 步去用，回测立刻变成印钞机。

    返回一个字典：资金曲线、现金、持仓数量、交易表、以及**记账误差**——
    每一根上「现金 + 持仓市值」和权益的最大差额，正常应该是 0。
    """
    from talab import indicators as I

    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    atr = (I.atr(df["high"], df["low"], df["close"], plan.atr_period).to_numpy()
           if plan.stop == "chandelier" else np.full(len(c), np.nan))
    signal = plan.entry.reindex(df.index).fillna(False).to_numpy(bool)
    leave = plan.exit.reindex(df.index).fillna(False).to_numpy(bool)
    rng = np.random.default_rng(plan.seed)
    account = Account(cash=float(equity))
    first = int(np.argmax(~np.isnan(atr))) + 1 if plan.stop == "chandelier" else 1

    curve, cash_path, share_path, trades, error = [], [], [], [], 0.0
    pending = False                                   # 上一根收盘挂出的买单还在不在
    entry_price = stop_price = risk = highest = np.nan
    entry_i = -1

    def stop_level(i: int, previous: float) -> float:
        if plan.stop == "none":
            return -np.inf
        if plan.stop == "percent":
            return entry_price * (1 - plan.stop_percent)
        return max(previous, highest - plan.k * atr[i - 1])   # 吊灯只上移

    for i in range(first, len(c)):
        # 第 1 步：成交上一根挂出的单
        if pending and account.shares == 0:
            price = o[i] if plan.fill == "next_open" else c[i - 1]
            level = (price * (1 - plan.stop_percent) if plan.stop == "percent"
                     else price - plan.k * atr[i - 1] if plan.stop == "chandelier" else -np.inf)
            if level < price:
                distance = 1 - level / price
                want = (account.equity(price) if plan.sizing == "full"
                        else account.equity(price) * min(1.0, plan.risk_per_trade / max(distance, 1e-9)))
                shares = min(want / price, account.affordable(price, plan.fee_rate))
                if shares > 0:
                    account.buy(price, shares, plan.fee_rate)
                    entry_price, entry_i, risk = price, i, price - level
                    highest, stop_price = price, level
            pending = False

        # 第 2 步：出场
        if account.shares > 0:
            stop_price = stop_level(i, stop_price)
            target = entry_price + plan.target_r * risk if plan.target_r is not None else np.inf
            price = reason = None
            if leave[i - 1] and i > entry_i:                      # 昨天收盘的出场信号，今天成交
                price, reason = (o[i] if plan.fill == "next_open" else c[i - 1]), "出场信号"
            elif plan.trigger == "close":
                if c[i] <= stop_price:
                    price, reason = c[i], "止损"
                elif c[i] >= target:
                    price, reason = c[i], "止盈"
            else:
                bar = {"low": l[i], "high": h[i]}
                touched = first_touch(bar, stop_price, target, plan.path, rng)
                if touched == "止损":
                    price, reason = min(o[i], stop_price), "止损"
                elif touched == "止盈":
                    price, reason = max(o[i], target), "止盈"
            if reason is not None:
                shares = account.shares
                account.sell(price, shares, plan.fee_rate)
                trades.append({"买入日": df.index[entry_i], "买入价": entry_price, "数量": shares,
                               "卖出日": df.index[i], "卖出价": price, "原因": reason,
                               "收益": price / entry_price - 1, "根数": i - entry_i})
            else:
                highest = max(highest, h[i])

        # 第 3 步：估值
        value = account.equity(c[i])
        error = max(error, abs(account.cash + account.shares * c[i] - value))
        curve.append(value)
        cash_path.append(account.cash)
        share_path.append(account.shares)

        # 第 4 步：用这一根收盘的信息下单，最早下一根成交
        if account.shares == 0 and not pending and signal[i]:
            pending = True

    if account.shares > 0:                            # 最后一根还拿着：记成「未平仓」，按收盘价估值
        trades.append({"买入日": df.index[entry_i], "买入价": entry_price, "数量": account.shares,
                       "卖出日": df.index[-1], "卖出价": c[-1], "原因": "未平仓",
                       "收益": c[-1] / entry_price - 1, "根数": len(c) - 1 - entry_i})
    index = df.index[first:]
    table = pd.DataFrame(trades, columns=["买入日", "买入价", "数量", "卖出日", "卖出价", "原因", "收益", "根数"])
    return {"资金曲线": pd.Series(curve, index=index, name="权益"),
            "现金": pd.Series(cash_path, index=index, name="现金"),
            "持仓数量": pd.Series(share_path, index=index, name="持仓"),
            "交易": table, "手续费合计": account.fees, "记账误差": error}


def reconcile(curves: dict[str, pd.Series]) -> pd.DataFrame:
    """把几条资金曲线摆在一起对账：终值、年化、最大回撤，以及和第一条的最大差额。

    两个引擎在同样的设定下跑出不同的曲线，一定有一个写错了。**对账是回测唯一能做的自检。**
    """
    names = list(curves)
    base = curves[names[0]] / curves[names[0]].iloc[0]
    rows = []
    for name in names:
        series = curves[name] / curves[name].iloc[0]
        aligned = series.reindex(base.index)
        rows.append({"名字": name, "终值（本金的几倍）": float(series.iloc[-1]),
                     "最大回撤": float((series / series.cummax() - 1).min()),
                     f"和「{names[0]}」的最大差额": float((aligned - base).abs().max())})
    return pd.DataFrame(rows)
