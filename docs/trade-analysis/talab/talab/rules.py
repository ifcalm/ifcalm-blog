"""talab.rules：把一个想法写成一条能执行的规则。第 21 篇。

「金叉买入」不是规则，是一个想法。规则要能让另一个人（或者一段程序）在不问你的情况下照做，
它至少要回答六个问题：

1. **环境过滤**（environment）：什么时候允许开新仓？
2. **入场条件**（entry）：什么信号算数？
3. **入场方式**（fill）：用什么价格买？
4. **初始止损**（stop）：跌到哪里认错？
5. **出场规则**（exit）：什么时候正常离场？
6. **仓位**（sizing）：买多少？

`Rule` 把这六个问题写成六组字段，`run` 按它跑一遍历史。这里**不算成本、不算滑点**，
也没有做偏差检查——那是第 27 到 29 篇的事。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

FILLS = ("close", "next_open", "pullback")
STOPS = ("none", "chandelier", "percent")
SIZINGS = ("full", "risk")


@dataclass
class Rule:
    """一条完整的交易规则（只做多）。

    entry / exit / environment 都是逐根 K 线的布尔序列，第 k 个值只能用第 k 根及之前的数据算出来。
    默认值也是选择：不写 stop 不等于「没想过止损」，而是选了「chandelier」。
    """
    entry: pd.Series                                  # 二、入场条件：收盘时信号成立
    exit: pd.Series                                   # 五、出场规则：收盘时该走了（止损之外的出场）
    environment: pd.Series | None = None              # 一、环境过滤：这根 K 线允许开新仓吗
    fill: str = "next_open"                           # 三、入场方式
    pullback_to: pd.Series | None = None              # fill="pullback" 时的限价（比如 50 日均线）
    pullback_bars: int = 10                           # 限价单挂多少根 K 线，过期不候
    stop: str = "chandelier"                          # 四、初始止损
    k: float = 3.0                                    # chandelier：最高价往下几个 ATR
    stop_percent: float = 0.10                        # percent：进场价往下百分之几
    trigger: str = "close"                            # 止损用收盘价还是盘中最低价触发（第 20 篇）
    sizing: str = "full"                              # 六、仓位
    risk_per_trade: float = 0.01                      # sizing="risk"：一笔最多亏账户的百分之几
    atr_period: int = 14

    def __post_init__(self):
        for name, value, allowed in [("fill", self.fill, FILLS), ("stop", self.stop, STOPS),
                                     ("sizing", self.sizing, SIZINGS)]:
            if value not in allowed:
                raise ValueError(f"{name} 只能是 {allowed} 之一，收到 {value!r}")
        if self.fill == "pullback" and self.pullback_to is None:
            raise ValueError("fill=\"pullback\" 要给出挂限价单的价格（pullback_to）")
        if self.sizing == "risk" and self.stop == "none":
            raise ValueError("没有止损就算不出每笔的风险，sizing=\"risk\" 需要一个止损")

    def describe(self) -> pd.Series:
        """把六要素列出来，用来检查「这条规则真的写完了吗」。"""
        return pd.Series({
            "一、环境过滤": "不过滤" if self.environment is None else "有",
            "二、入场条件": "给定的信号序列",
            "三、入场方式": {"close": "当根收盘价", "next_open": "下一根开盘价",
                             "pullback": f"回调到指定价格的限价单，{self.pullback_bars} 根内有效"}[self.fill],
            "四、初始止损": {"none": "没有", "chandelier": f"{self.k} 倍 ATR 吊灯（{self.trigger} 触发）",
                             "percent": f"进场价下方 {self.stop_percent:.0%}（{self.trigger} 触发）"}[self.stop],
            "五、出场规则": "给定的出场信号",
            "六、仓位": "满仓" if self.sizing == "full" else f"每笔风险 {self.risk_per_trade:.0%}",
        })


def _atr(df: pd.DataFrame, n: int) -> np.ndarray:
    from talab import indicators as I
    return I.atr(df["high"], df["low"], df["close"], n).to_numpy()


def run(df: pd.DataFrame, rule: Rule) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    """按规则跑一遍历史，返回（每根 K 线的收益率、是否持仓、每笔交易）。

    约定：信号在收盘时算出来，最快也要等到下一根才能成交（fill="close" 是个例外，它假设
    你能在收盘那一刻成交，第 12 篇量过这个假设有多贵）。没有成本、没有滑点。

    最后一根 K 线还持有的仓位会以「未平仓」的名义记进交易表，按最后的收盘价估值——不这样做的话，
    「每笔交易的平均收益」这类统计会悄悄漏掉还没结束的那一笔。

    仓位是进场时算好的一个比例，每根 K 线的收益率 = 仓位比例 × 价格变化。
    ⚠️ 写成这样等于**每根 K 线都把仓位调回那个比例**：满仓时看不出来，不满仓时会和
    「买进之后数量不变」的真实账户差一点点（第 27 篇的引擎把这笔账对出来了，九年差约 0.5%）。
    真正的仓位管理（加仓、减仓、组合风险）是第 26 篇。
    fill="pullback" 的限价挂在**信号那一天**的 pullback_to 上，挂 pullback_bars 根 K 线，过期作废。
    """
    o, h, l, c = (df[x].to_numpy(float) for x in ["open", "high", "low", "close"])
    atr = _atr(df, rule.atr_period) if rule.stop == "chandelier" else np.full(len(c), np.nan)
    entry = rule.entry.reindex(df.index).fillna(False).to_numpy(bool)
    leave = rule.exit.reindex(df.index).fillna(False).to_numpy(bool)
    allowed = (np.ones(len(c), bool) if rule.environment is None
               else rule.environment.reindex(df.index).fillna(False).to_numpy(bool))
    limit = (np.full(len(c), np.nan) if rule.pullback_to is None
             else rule.pullback_to.reindex(df.index).to_numpy(float))
    first = int(np.argmax(~np.isnan(atr))) + 1 if rule.stop == "chandelier" else 1   # 用不到 ATR 就不用等预热
    returns, held, trades = np.zeros(len(c)), np.zeros(len(c)), []
    holding = False
    waiting = -1                                          # 等着成交的信号出现在第几根，-1 是没有
    size = stop_price = entry_price = highest = np.nan
    entry_i = -1

    def stop_level(i: int, previous: float) -> float:
        """止损价。吊灯只上移不下移，所以要和之前的止损价取大。"""
        if rule.stop == "none":
            return -np.inf
        if rule.stop == "percent":
            return entry_price * (1 - rule.stop_percent)
        return max(previous, highest - rule.k * atr[i - 1])

    for i in range(first, len(c)):
        if not holding and waiting >= 0:                  # 这一根尝试成交
            price = None
            if rule.fill == "next_open":
                price = o[i]
            elif rule.fill == "pullback":
                level = limit[waiting]
                if o[i] <= level:
                    price = o[i]                          # 开盘就在限价下方，按开盘价成交
                elif l[i] <= level:
                    price = level
                elif i - waiting >= rule.pullback_bars:
                    waiting = -1                          # 挂单过期
            if price is not None:
                holding, entry_price, entry_i, highest = True, price, i, price
                stop_price = stop_level(i, -np.inf)
                distance = 1 - stop_price / entry_price
                size = 1.0 if rule.sizing == "full" else min(1.0, rule.risk_per_trade / max(distance, 1e-9))
                waiting = -1
        if holding:
            held[i] = size
            stop_price = stop_level(i, stop_price)
            base = entry_price if i == entry_i else c[i - 1]
            price = reason = None
            if leave[i - 1]:                              # 昨天收盘发出的出场信号，今天开盘执行
                price, reason = o[i], "出场信号"
            elif rule.trigger == "low" and l[i] <= stop_price:
                price, reason = (o[i] if o[i] <= stop_price else stop_price), "止损"
            elif rule.trigger == "close" and c[i] <= stop_price:
                price, reason = c[i], "止损"
            if reason is None:
                returns[i], highest = size * (c[i] / base - 1), max(highest, h[i])
            else:
                returns[i] = size * (price / base - 1)
                trades.append((df.index[entry_i], entry_price, df.index[i], price, reason, size))
                holding = False
        if not holding and waiting < 0 and entry[i] and allowed[i]:
            if rule.fill == "close":                      # 当根收盘就买，下一根开始算收益
                holding, entry_price, entry_i, highest = True, c[i], i, c[i]
                stop_price = stop_level(i, -np.inf)
                distance = 1 - stop_price / entry_price
                size = 1.0 if rule.sizing == "full" else min(1.0, rule.risk_per_trade / max(distance, 1e-9))
            else:
                waiting = i
    if holding:                                           # 最后一根还拿着：记成一笔未平仓的交易，按最后的收盘价估值
        trades.append((df.index[entry_i], entry_price, df.index[-1], c[-1], "未平仓", size))
    index = df.index[first:]
    trades = pd.DataFrame(trades, columns=["买入日", "买入价", "卖出日", "卖出价", "原因", "仓位"])
    trades["收益"] = trades["卖出价"] / trades["买入价"] - 1
    return pd.Series(returns[first:], index=index), pd.Series(held[first:], index=index), trades


# ---------------------------------------------------------------------------
# 二、条件叠加：共振还是冗余
# ---------------------------------------------------------------------------

def overlap(conditions: dict[str, pd.Series]) -> pd.DataFrame:
    """两两之间「同时成立」的程度：对角线是各自成立的比例，上三角是同时成立占其中之一的比例（Jaccard）。

    两个条件几乎总是一起成立，叠加起来就不增加信息，只是让交易次数变少。
    """
    names = list(conditions)
    out = pd.DataFrame(np.nan, index=names, columns=names, dtype=float)
    for a in names:
        left = conditions[a].fillna(False).to_numpy(bool)
        out.loc[a, a] = left.mean()
        for b in names:
            if a == b:
                continue
            right = conditions[b].reindex(conditions[a].index).fillna(False).to_numpy(bool)
            union = (left | right).sum()
            out.loc[a, b] = (left & right).sum() / union if union else np.nan
    return out


def stack(conditions: dict[str, pd.Series], order: list[str] | None = None) -> pd.DataFrame:
    """按顺序一条条加条件，每加一条还剩多少根 K 线成立。"""
    order = order or list(conditions)
    mask, rows = None, []
    for name in order:
        current = conditions[name].fillna(False)
        mask = current if mask is None else (mask & current.reindex(mask.index).fillna(False))
        rows.append({"加上的条件": name, "还剩的 K 线": int(mask.sum()), "占全部": float(mask.mean())})
    return pd.DataFrame(rows)
