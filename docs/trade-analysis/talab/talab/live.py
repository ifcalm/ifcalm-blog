"""talab.live：从回测走到实盘。第 34 篇。

第 33 篇问「你能不能照着做」。这一篇问更早的一个问题：**你该怎么开始做。**

回测通过了、样本外通过了、正常范围表也算好了——然后呢？把全部资金投进去？

这一篇的答案是「不」，而且理由不是谨慎，是三件可以量出来的事：

| 事 | 用什么量 | 在这里 |
|---|---|---|
| **你上线的那一天是随便抽的** | `starts`、`start_risk` | 第三节 |
| **回测的代码和实盘的代码不是同一份** | `Runner`、`replay`、`agrees` | 第五、六节 |
| **交易所不接受你回测里的那个数量** | `Filters`、`apply_filters`、`min_account` | 第八、九节 |

前两件不解决，第四件就无从谈起：**按台阶一级一级加钱**（`Stage`、`ladder`、`run_ladder`），
每一级的升级条件和降级条件**在上线之前就写死**（`Guard`、`guards_from_range`）。

⚠️ 这一篇里没有任何一个函数在提高策略的收益。它们全都在**减少你把一条对的策略执行坏的概率**。
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from talab.backtest import Account

SIDES = ("buy", "sell")
STOPS = ("none", "chandelier", "percent")
ACTIONS = ("降级", "停用")
COLUMNS = ("open", "high", "low", "close")


# ---------------------------------------------------------------------------
# 一、把回测改成一根一根喂
# ---------------------------------------------------------------------------

@dataclass
class Order:
    """一张要发给交易所的单。

    `client_id` 是**你自己**生成的编号，发单时一起带上。它的唯一用途出现在断线之后：
    重连时用同一个 `client_id` 再发一次，交易所会认出这是同一张单而不是第二张——
    **幂等**。第十三节会说明为什么这是整条流程里最不能省的一个字段。
    """
    time: pd.Timestamp
    side: str
    qty: float
    reason: str = ""
    price: float = np.nan                  # 只是发单那一刻的参考价，市价单不带价格
    client_id: str = ""

    def __post_init__(self):
        if self.side not in SIDES:
            raise ValueError(f"side 只能是 {SIDES} 之一，收到 {self.side!r}")
        if not self.qty > 0:
            raise ValueError("数量要大于 0")
        if not self.client_id:
            self.client_id = f"{pd.Timestamp(self.time).value}-{self.side}-{self.reason}"


class Runner:
    """第 27 篇那个四步循环的**一根一根**版本。

    回测引擎拿到的是整条历史，实盘拿到的是「又收了一根」。两者必须做同一件事，
    但写法完全不同：回测可以先把 ATR 算完再开始循环，实盘只能**每收一根算一次**。

    每收到一根 K 线，`on_bar` 按固定顺序做四件事，和 `backtest.run` 逐字对应：

    1. **成交**：把上一根收盘时挂出的单，按这一根的开盘价成交
    2. **出场**：检查昨天的出场信号和止损
    3. **估值**：按这一根的收盘价记一次权益
    4. **下单**：把这一根收进历史，重算信号，挂出**下一根**的单

    `signal` 是一个函数，收到「到目前为止的全部 K 线」，返回 `(进场, 出场)` 两个布尔值。
    ⚠️ 它拿到的是 `Runner` 自己的缓冲区，而缓冲区只有 `warmup` 根——
    **这正是第七节要量的那件事：上线时你需要带多少根历史。**
    """

    def __init__(self, signal, stop: str = "chandelier", k: float = 3.0,
                 stop_percent: float = 0.10, atr_period: int = 14,
                 sizing: str = "risk", risk_per_trade: float = 0.10,
                 fee_rate: float = 0.0, equity: float = 100_000.0,
                 warmup: int | None = None):
        if stop not in STOPS:
            raise ValueError(f"stop 只能是 {STOPS} 之一，收到 {stop!r}")
        if sizing not in ("full", "risk"):
            raise ValueError("sizing 只能是 full 或 risk")
        if sizing == "risk" and stop == "none":
            raise ValueError('没有止损就算不出每笔的风险，sizing="risk" 需要一个止损')
        self.signal, self.stop, self.k, self.stop_percent = signal, stop, k, stop_percent
        self.atr_period, self.sizing = atr_period, sizing
        self.risk_per_trade, self.fee_rate = risk_per_trade, fee_rate
        self.warmup = warmup
        self.account = Account(cash=float(equity))
        self.bars: deque = deque(maxlen=warmup)
        self.times: deque = deque(maxlen=warmup)
        self.atr = np.nan                  # 算到**上一根**为止的 ATR
        self._tr_sum = self._tr_n = 0
        self.pending = None                # 上一根挂出的单
        self.exit_signal = False           # 上一根收盘时成立的出场信号
        self.entry_price = self.stop_price = self.risk = self.highest = np.nan
        self.entry_time = None
        self.seen = -1                     # 收到的第几根（从 0 开始）
        self.entry_index = -1
        self.last = (None, np.nan)         # 最后一根的时间和收盘价
        self.curve: list = []
        self.trades: list = []
        self.error = 0.0

    # -- 增量指标 ----------------------------------------------------------
    def _push(self, bar: dict):
        """把这一根收进缓冲区，并用 Wilder 平滑把 ATR 往前推一格。

        ⚠️ 这里不能重算整条历史：实盘跑十年，每根都重算一遍是 O(n²)。
        Wilder 平滑本来就是递推的（`新值 = 旧值 + (这一根 − 旧值) / n`），天生适合实盘。
        """
        previous = self.bars[-1]["close"] if self.bars else np.nan
        if not np.isnan(previous):                         # 第一根没有真实波幅（要用前一根收盘）
            true_range = max(bar["high"] - bar["low"], abs(bar["high"] - previous),
                             abs(bar["low"] - previous))
            if self._tr_n < self.atr_period:               # 预热：先攒满 n 根取平均
                self._tr_sum += true_range
                self._tr_n += 1
                if self._tr_n == self.atr_period:
                    self.atr = self._tr_sum / self.atr_period
            else:
                self.atr += (true_range - self.atr) / self.atr_period
        self.bars.append(bar)

    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame(list(self.bars), index=pd.DatetimeIndex(list(self.times)))

    # -- 四步 --------------------------------------------------------------
    def on_bar(self, time, bar) -> list[Order]:
        bar = {name: float(bar[name]) for name in COLUMNS}
        orders: list[Order] = []
        self.seen += 1
        atr = self.atr                                     # 算到上一根为止，这一根还没收进来

        # 第 1 步：成交上一根挂出的单
        if self.pending is not None and self.account.shares == 0:
            price = bar["open"]
            level = (price * (1 - self.stop_percent) if self.stop == "percent"
                     else price - self.k * atr if self.stop == "chandelier" else -np.inf)
            if level < price:
                distance = 1 - level / price
                want = (self.account.equity(price) if self.sizing == "full"
                        else self.account.equity(price)
                        * min(1.0, self.risk_per_trade / max(distance, 1e-9)))
                shares = min(want / price, self.account.affordable(price, self.fee_rate))
                if shares > 0:
                    self.account.buy(price, shares, self.fee_rate)
                    self.entry_price, self.entry_time = price, time
                    self.entry_index = self.seen
                    self.risk, self.highest, self.stop_price = price - level, price, level
            self.pending = None

        # 第 2 步：出场
        if self.account.shares > 0:
            if self.stop == "percent":
                self.stop_price = self.entry_price * (1 - self.stop_percent)
            elif self.stop == "chandelier":
                self.stop_price = max(self.stop_price, self.highest - self.k * atr)
            price = reason = None
            if self.exit_signal and time != self.entry_time:
                price, reason = bar["open"], "出场信号"
            elif self.stop != "none" and bar["close"] <= self.stop_price:
                price, reason = bar["close"], "止损"
            if reason is not None:
                shares = self.account.shares
                self.account.sell(price, shares, self.fee_rate)
                self.trades.append({"买入日": self.entry_time, "买入价": self.entry_price,
                                    "数量": shares, "卖出日": time, "卖出价": price,
                                    "原因": reason, "收益": price / self.entry_price - 1,
                                    "根数": self.seen - self.entry_index})
                orders.append(Order(time, "sell", shares, reason, price))
            else:
                self.highest = max(self.highest, bar["high"])

        # 第 3 步：估值
        value = self.account.equity(bar["close"])
        self.error = max(self.error, abs(self.account.cash
                                         + self.account.shares * bar["close"] - value))
        self.curve.append((time, value))
        self.last = (time, bar["close"])

        # 第 4 步：把这一根收进历史，重算信号，挂出下一根的单
        self.times.append(time)
        self._push(bar)
        entry, self.exit_signal = self.signal(self._frame())
        if self.account.shares == 0 and self.pending is None and entry:
            self.pending = Order(time, "buy", 1.0, "进场信号", bar["close"])
            orders.append(self.pending)
        return orders

    def result(self) -> dict:
        """当前的账本。⚠️ 还拿着的那一笔记成「未平仓」，按最后一根的收盘价估值——
        和 `backtest.run` 同一个口径，**但它是估值不是成交**，明天开盘就不是这个数了。"""
        curve = pd.Series([v for _, v in self.curve],
                          index=pd.DatetimeIndex([t for t, _ in self.curve]), name="权益")
        trades = list(self.trades)
        if self.account.shares > 0:
            time, close = self.last
            trades.append({"买入日": self.entry_time, "买入价": self.entry_price,
                           "数量": self.account.shares, "卖出日": time, "卖出价": close,
                           "原因": "未平仓", "收益": close / self.entry_price - 1,
                           "根数": self.seen - self.entry_index})
        return {"资金曲线": curve,
                "交易": pd.DataFrame(trades, columns=["买入日", "买入价", "数量", "卖出日",
                                                      "卖出价", "原因", "收益", "根数"]),
                "手续费合计": self.account.fees, "记账误差": self.error}


def replay(df: pd.DataFrame, runner: Runner, start: int = 0) -> dict:
    """把一段历史一根一根喂给 `Runner`，就像它是实时到达的一样。

    这是**唯一**能验证实盘代码的办法：让它重放历史，然后和回测引擎逐根对账。
    对不上就是有一边写错了——第 27 篇那句话在这里还成立：**对账是回测唯一能做的自检。**
    """
    for position in range(start, len(df)):
        runner.on_bar(df.index[position], df.iloc[position])
    return runner.result()


def agrees(a: pd.Series, b: pd.Series, tolerance: float = 1e-9) -> pd.Series:
    """两条资金曲线逐根对账：重叠的根数、最大绝对差、最大相对差、第一根对不上的时间。

    ⚠️ 「差不多」不算数。同一套规则、同一段数据，两份代码的资金曲线应该差在浮点误差量级。
    差 0.1% 不是「实现细节不同」，是**其中一份有 bug**，而你还不知道是哪一份。

    ⚠️ 判据用的是**相对**差不是绝对差：绝对差会随账户大小变——
    同样的浮点噪声，10 万美元的账户上是 1e-9，1000 万的账户上就是 1e-7，
    换一个本金就要换一次阈值的判据不是判据。
    """
    common = a.index.intersection(b.index)
    both = pd.DataFrame({"A": a.reindex(common), "B": b.reindex(common)}).dropna()
    if not len(both):
        raise ValueError("两条曲线没有重叠的时间")
    gap = (both["A"] - both["B"]).abs()
    relative = gap / both["B"].abs().clip(lower=1e-12)
    off = both.index[relative > tolerance]
    return pd.Series({"重叠根数": float(len(both)), "最大绝对差": float(gap.max()),
                      "最大相对差": float(relative.max()),
                      "对不上的根数": float(len(off)),
                      "第一根对不上的": off[0] if len(off) else pd.NaT})


# ---------------------------------------------------------------------------
# 二、交易所的硬约束
# ---------------------------------------------------------------------------

@dataclass
class Filters:
    """交易所对一张单的硬性要求。回测里没有这些东西，实盘里每一张单都要过这一关。

    - `tick_size`：价格必须是它的整数倍
    - `step_size`：数量必须是它的整数倍（**向下取整**，因为买多了会超出风险预算）
    - `min_qty` / `max_qty`：单张单的数量上下限
    - `min_notional`：单张单的金额下限——**小账户真正的门槛在这里，不在数量精度上**
    """
    tick_size: float = 0.01
    step_size: float = 1e-5
    min_qty: float = 1e-5
    max_qty: float = np.inf
    min_notional: float = 5.0

    @classmethod
    def from_binance(cls, payload: dict) -> "Filters":
        """从 `api.binance.com/api/v3/exchangeInfo` 的一个 symbol 里读出来（公开接口，不用账号）。"""
        found = {f["filterType"]: f for f in payload["filters"]}
        price, lot = found["PRICE_FILTER"], found["LOT_SIZE"]
        notional = found.get("NOTIONAL", found.get("MIN_NOTIONAL", {}))
        return cls(tick_size=float(price["tickSize"]), step_size=float(lot["stepSize"]),
                   min_qty=float(lot["minQty"]), max_qty=float(lot["maxQty"]),
                   min_notional=float(notional.get("minNotional", 0.0)))

    @staticmethod
    def _floor(value: float, unit: float) -> float:
        if unit <= 0:
            return float(value)
        # 先除再取整会被浮点误差咬：0.29/0.01 在双精度里是 28.999999999999996
        return math.floor(round(value / unit, 9)) * unit

    def round_qty(self, qty: float) -> float:
        """数量向下取到 `step_size` 的整数倍。**向下**不是随手选的：向上取整会让这一笔
        的风险超过你定的预算，而超出的部分正好落在你最不希望它出现的时候。"""
        return self._floor(qty, self.step_size)

    def round_price(self, price: float) -> float:
        return self._floor(price, self.tick_size)

    def accepts(self, price: float, qty: float) -> str:
        """这张单能不能发出去。返回空字符串表示可以，否则是被拒绝的理由。"""
        if qty < self.min_qty:
            return f"数量不足 minQty（{qty:.8f} < {self.min_qty:g}）"
        if qty > self.max_qty:
            return f"数量超过 maxQty（{qty:.8f} > {self.max_qty:g}）"
        if price * qty < self.min_notional:
            return f"金额不足 minNotional（{price * qty:.2f} < {self.min_notional:g}）"
        return ""


def apply_filters(trades: pd.DataFrame, filters: Filters, qty_col: str = "数量",
                  price_col: str = "买入价") -> pd.DataFrame:
    """把一张交易表里的每一笔按交易所的规矩过一遍：取整之后剩多少、有几笔根本发不出去。

    `丢掉的比例` 那一列是取整吃掉的仓位。它在 BTC 上小到可以忽略，
    但**它和账户大小成反比**——同样的 `step_size`，账户越小丢得越多。
    """
    qty = trades[qty_col].astype(float)
    price = trades[price_col].astype(float)
    rounded = qty.map(filters.round_qty)
    rejected = [filters.accepts(p, q) for p, q in zip(price, rounded)]
    return trades.assign(**{"取整后数量": rounded,
                            "丢掉的比例": (qty - rounded) / qty.where(qty != 0),
                            "被拒绝": rejected})


def min_account(filters: Filters, price: float, risk_per_trade: float = 0.10,
                stop_fraction: float = 0.15) -> pd.Series:
    """**这条策略在这个市场上，最少要多大的账户才跑得动。**

    两个门槛，取大的那个：

    - `minNotional`：一笔的金额不能低于它
    - `step_size`：一笔的数量取整之后，误差不能大到把仓位算错

    仓位 = 账户 × 风险预算 ÷ 止损距离（第 26 篇），所以账户 = 仓位金额 × 止损距离 ÷ 风险预算。
    ⚠️ 这个数是**下限不是建议**：刚好够下单，不等于够分散、够扛回撤。
    """
    if not 0 < risk_per_trade <= 1 or not 0 < stop_fraction <= 1:
        raise ValueError("风险预算和止损距离都要在 0 和 1 之间")
    ratio = min(1.0, risk_per_trade / stop_fraction)       # 仓位占账户的比例
    by_notional = filters.min_notional / ratio
    # 让取整误差不超过仓位的 1%：仓位金额至少要是 100 个 step 的钱
    by_step = 100 * filters.step_size * price / ratio
    return pd.Series({"仓位占账户": ratio, "按 minNotional 算": by_notional,
                      "按 step_size 算（误差 < 1%）": by_step,
                      "最小账户": max(by_notional, by_step)})


# ---------------------------------------------------------------------------
# 三、起点风险：你上线的那一天是随便抽的
# ---------------------------------------------------------------------------

def starts(df: pd.DataFrame, run, window: int, step: int = 5,
           warmup: int = 250) -> pd.DataFrame:
    """**从每一个可能的日子开始上线**，各跑 `window` 根，看第一段的成绩。

    `run` 是一个函数，收到一段 K 线、返回一条资金曲线。这里必须**真的重跑引擎**，
    不能拿整条曲线去滚动相除——因为「从今天开始」意味着你此刻是空仓的，
    而连续跑下来的那条曲线在同一时刻多半正拿着一笔仓。

    ⚠️ 这张表回答的问题和「九年年化多少」完全不同：
    **年化是一个九年才收敛的数，而你的第一年只有一次。**
    """
    if window < 2 or step < 1:
        raise ValueError("window 至少是 2，step 至少是 1")
    rows = []
    for begin in range(warmup, len(df) - window, step):
        piece = df.iloc[begin - warmup:begin + window]
        curve = run(piece)
        curve = curve.iloc[-window:] if len(curve) > window else curve
        if len(curve) < 2:
            continue
        peak = curve.cummax()
        rows.append({"上线日": df.index[begin], "第一段收益": float(curve.iloc[-1] / curve.iloc[0] - 1),
                     "期间最大回撤": float((curve / peak - 1).min())})
    return pd.DataFrame(rows)


def start_risk(table: pd.DataFrame, column: str = "第一段收益",
               levels=(0.05, 0.25, 0.5, 0.75, 0.95)) -> pd.Series:
    """把 `starts` 的结果压成一行：赚钱的起点占多少，以及各个分位。"""
    values = table[column].dropna()
    out = {"起点个数": float(len(values)), "赚钱的起点占": float((values > 0).mean()),
           "平均": float(values.mean()), "最差": float(values.min()), "最好": float(values.max())}
    out.update({f"{level:.0%} 分位": float(values.quantile(level)) for level in levels})
    return pd.Series(out)


# ---------------------------------------------------------------------------
# 四、阶梯上线
# ---------------------------------------------------------------------------

@dataclass
class Stage:
    """一级台阶：用多少钱、跑满多少笔才能升级。

    `fraction` 是**这一级实际投入的资金占目标资金的比例**。0 代表模拟盘——
    一分钱不投，但每一笔都照样记账、照样对账。
    """
    name: str
    fraction: float
    trades_to_promote: int

    def __post_init__(self):
        if not 0 <= self.fraction <= 1:
            raise ValueError("fraction 要在 0 和 1 之间")
        if self.trades_to_promote < 1:
            raise ValueError("至少要跑满一笔才能升级")


DEFAULT_LADDER = (Stage("模拟盘", 0.00, 10), Stage("小资金", 0.10, 15),
                  Stage("半仓", 0.35, 20), Stage("目标", 1.00, 1))


def ladder(stages=DEFAULT_LADDER) -> pd.DataFrame:
    """把一条阶梯打印成一张表，贴在上线方案的第一页。"""
    rows = [{"第几级": k + 1, "名字": s.name, "投入比例": s.fraction,
             "跑满几笔升级": s.trades_to_promote} for k, s in enumerate(stages)]
    return pd.DataFrame(rows)


def run_ladder(r, stages=DEFAULT_LADDER, guards=(), start: int = 0) -> dict:
    """按阶梯走一遍：每笔按当前这一级的比例缩放，跑满笔数升一级，触发警戒线降一级。

    ⚠️ 这里有一个**必须**这样写的地方：降级用的警戒线看的是**这一级自己**的成绩，
    不是从头到尾的总成绩。上一级的坑不该算在这一级头上——否则你刚升上去就被降回来。
    """
    r = pd.Series(r).dropna().astype(float).to_numpy()
    level, since, rows = start, [], []
    for i, value in enumerate(r):
        stage = stages[level]
        taken = value * stage.fraction
        since.append(value)
        triggered = [g.name for g in guards if g.fires(np.array(since))]
        note = ""
        if triggered and level > 0:
            level, since, note = level - 1, [], "降级：" + "、".join(triggered)
        elif triggered:
            note = "触发但已在最低一级：" + "、".join(triggered)
        elif len(since) >= stage.trades_to_promote and level < len(stages) - 1:
            level, since, note = level + 1, [], "升级"
        rows.append({"第几笔": i + 1, "这一级": stage.name, "投入比例": stage.fraction,
                     "这一笔的 R": value, "记进账户的": taken, "发生了什么": note})
    table = pd.DataFrame(rows)
    return {"逐笔": table, "合计": float(table["记进账户的"].sum()),
            "一次全投": float(r.sum()), "最后停在": stages[level].name,
            "升级次数": int(table["发生了什么"].eq("升级").sum()),
            "降级次数": int(table["发生了什么"].str.startswith("降级").sum())}


# ---------------------------------------------------------------------------
# 五、警戒线：上线之前就写死
# ---------------------------------------------------------------------------

@dataclass
class Guard:
    """一条**事先写好**的警戒线：看哪个量、超过多少、然后做什么。

    三个字段里最重要的是第三个。一条只说「情况不对」而不说「那就做什么」的规则，
    在情况真的不对的那一天等于没有——**因为那一天你会自己发明一个动作。**
    """
    name: str
    kind: str                              # drawdown / streak
    threshold: float
    action: str = "降级"

    def __post_init__(self):
        if self.kind not in ("drawdown", "streak"):
            raise ValueError("kind 只能是 drawdown 或 streak")
        if self.action not in ACTIONS:
            raise ValueError(f"action 只能是 {ACTIONS} 之一，收到 {self.action!r}")
        if self.kind == "drawdown" and self.threshold >= 0:
            raise ValueError("回撤的阈值要是负数")
        if self.kind == "streak" and self.threshold < 1:
            raise ValueError("连亏的阈值至少是 1 笔")

    def fires(self, r: np.ndarray) -> bool:
        """这一段成绩有没有踩线。⚠️ 传进来的应该是**当前这一级**的成绩。"""
        if not len(r):
            return False
        if self.kind == "streak":
            run = 0
            for value in r:
                run = run + 1 if value <= 0 else 0
            return run >= self.threshold
        curve = np.cumsum(r)
        peak = np.maximum.accumulate(np.concatenate([[0.0], curve]))[1:]
        return bool((curve - peak).min() <= self.threshold)


def stage_range(r, n_trades: int, trials: int = 2000, seed: int = 0,
                levels=(0.5, 0.9, 0.95, 0.99)) -> pd.DataFrame:
    """**按一级台阶实际要跑的笔数**算正常范围，而不是按整段历史。

    第 33 篇那张表是按「九年 70 笔」算出来的，而你在一级台阶上只跑十几笔——
    **十几笔里的正常回撤，比七十笔里的浅得多**（`expected_longest` 说的就是这件事：
    最长连亏随笔数增长）。拿七十笔的阈值去守十五笔的台阶，等于没有阈值。

    做法：从历史的 R 分布里**有放回地**抽 `n_trades` 笔，重复 `trials` 次。
    ⚠️ 有放回是故意的：这里问的是「下一段十五笔可能长什么样」，不是「历史那十五笔怎么排」。
    """
    from talab.journal import longest_streak

    values = pd.Series(r).dropna().astype(float).to_numpy()
    if len(values) < 2 or n_trades < 2:
        raise ValueError("至少要有两笔历史和两笔台阶长度")
    rng = np.random.default_rng(seed)
    picks = rng.choice(values, size=(trials, n_trades), replace=True)
    curve = np.cumsum(picks, axis=1)
    peak = np.maximum.accumulate(np.concatenate([np.zeros((trials, 1)), curve], axis=1), axis=1)[:, 1:]
    deepest = (curve - peak).min(axis=1)
    longest = np.array([longest_streak(row) for row in picks])
    rows = {"最长连亏": longest, "最深回撤": deepest}
    out = []
    for name, sample in rows.items():
        row = {"台阶长度": float(n_trades), "平均": float(sample.mean())}
        for level in levels:
            row[f"{level:.0%} 分位"] = float(np.quantile(sample, 1 - level if "回撤" in name else level))
        out.append(pd.Series(row, name=name))
    return pd.DataFrame(out)


def guards_from_range(table: pd.DataFrame, level: str = "99% 分位",
                      action: str = "降级") -> list[Guard]:
    """**直接把第 33 篇那张正常范围表变成警戒线。**

    这是这一篇和上一篇的接口，也是整条流程里唯一一处「阈值不是拍脑袋定的」：
    回撤线取重抽分布的 99% 分位，连亏线同理。
    ⚠️ 踩线**不等于**策略失效（第 33 篇第六节：那需要几十年的样本），
    它等于「我事先答应过自己，到这里就降一级」。
    """
    if level not in table.columns:
        raise ValueError(f"表里没有 {level!r} 这一列")
    return [Guard(f"回撤超过 {table.loc['最深回撤', level]:.2f}", "drawdown",
                  float(table.loc["最深回撤", level]), action),
            Guard(f"连亏超过 {table.loc['最长连亏', level]:.0f} 笔", "streak",
                  float(table.loc["最长连亏", level]), action)]
