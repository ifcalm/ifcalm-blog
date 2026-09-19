"""talab.orders：订单类型，以及止损到底成交在哪里。第 22 篇。

回测里写「止损 60000」，默认的意思是「价格碰到 60000，你就以 60000 成交」。真实世界里这句话
拆成三个独立的问题：

1. **用什么价格触发**：最新成交价，还是交易所算出来的标记价格？
2. **触发之后下什么单**：市价单（一定成交，价格不保证）还是限价单（价格保证，成交不保证）？
3. **成交在哪里**：触发那一刻之后的第一笔成交，可能比触发价好，也可能差很多。

这个模块把这三个问题变成参数，好让你量出它们各自值多少钱。所有函数都在一组 K 线上重放，
K 线越细越接近真实（第 22 篇用的是 1 分钟线）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SIDES = ("buy", "sell")
FILLS = ("trigger", "bar_close", "next_open", "worst")


def _check(side: str, allowed=SIDES) -> None:
    if side not in allowed:
        raise ValueError(f"只能是 {allowed} 之一，收到 {side!r}")


def touched(bars: pd.DataFrame, level: float, side: str = "sell",
            prices: pd.DataFrame | None = None) -> pd.Timestamp | None:
    """价格第一次碰到 level 的那根 K 线。

    side="sell"（卖出止损）看最低价跌到 level；side="buy"（买入止损、突破挂单）看最高价涨到 level。
    prices 可以换成另一套价格（比如标记价格）来判断触发，成交仍然发生在 bars 上。
    """
    _check(side)
    source = bars if prices is None else prices
    hit = source["low"] <= level if side == "sell" else source["high"] >= level
    hit = hit.reindex(bars.index).fillna(False)
    return bars.index[hit][0] if hit.any() else None


def market_fill(bars: pd.DataFrame, when, delay: int = 1) -> dict:
    """市价单：在 when 这根 K 线之后 delay 根的开盘价成交（delay=0 表示当根收盘价）。"""
    position = bars.index.get_loc(pd.Timestamp(when)) + delay
    if position >= len(bars):
        return {"成交时间": None, "成交价": np.nan}
    price = bars["open"].iloc[position] if delay > 0 else bars["close"].iloc[position]
    return {"成交时间": bars.index[position], "成交价": float(price)}


def limit_fill(bars: pd.DataFrame, level: float, side: str = "buy", start=None, expire: int | None = None) -> dict:
    """限价单：买单要等价格跌到 level，卖单要等价格涨到 level。expire 是挂单能活多少根 K 线。

    开盘价已经越过限价时按开盘价成交（这是对你有利的一侧），否则按限价成交。
    ⚠️ 这里假设「价格碰到限价就一定成交」。真实的限价单要排队，碰到不等于轮到你。
    """
    _check(side)
    window = bars if start is None else bars.loc[pd.Timestamp(start):]
    if expire is not None:
        window = window.iloc[:expire]
    reached = window["low"] <= level if side == "buy" else window["high"] >= level
    if not reached.any():
        return {"成交时间": None, "成交价": np.nan, "成交": False}
    when = window.index[reached][0]
    open_price = float(window["open"].loc[when])
    better = open_price <= level if side == "buy" else open_price >= level
    return {"成交时间": when, "成交价": open_price if better else float(level), "成交": True}


def stop_market_fill(bars: pd.DataFrame, level: float, side: str = "sell",
                     prices: pd.DataFrame | None = None, fill: str = "next_open") -> dict:
    """止损市价单：触发之后按市价成交，一定成交，价格不保证。

    fill 是成交价的口径，用来量「回测有多乐观」：
      "trigger"   ：成交在止损价（回测最常见的假设）
      "bar_close" ：成交在触发那根 K 线的收盘价
      "next_open" ：成交在下一根 K 线的开盘价（默认）
      "worst"     ：成交在触发那根 K 线最不利的价格（这一根能有多差就有多差）
    滑点为正表示比止损价更不利（卖出成交得更低、买入成交得更高）。
    """
    _check(side)
    _check(fill, FILLS)
    when = touched(bars, level, side, prices)
    if when is None:
        return {"触发时间": None, "成交时间": None, "成交价": np.nan, "滑点": np.nan}
    position = bars.index.get_loc(when)
    if fill == "trigger":
        price, at = float(level), when
    elif fill == "bar_close":
        price, at = float(bars["close"].iloc[position]), when
    elif fill == "worst":
        price, at = float(bars["low"].iloc[position] if side == "sell" else bars["high"].iloc[position]), when
    else:
        nxt = min(position + 1, len(bars) - 1)
        price, at = float(bars["open"].iloc[nxt]), bars.index[nxt]
    slippage = (level - price) / level if side == "sell" else (price - level) / level
    return {"触发时间": when, "成交时间": at, "成交价": price, "滑点": slippage}


def stop_limit_fill(bars: pd.DataFrame, level: float, limit: float, side: str = "sell",
                    prices: pd.DataFrame | None = None, expire: int | None = None) -> dict:
    """止损限价单：触发之后挂一张限价单，价格有保证，成交没保证。

    卖出止损限价单的 limit 通常略低于触发价（给一点余地）。价格一路往下不回头，这张单就挂在那里，
    仓位还在——这正是「止损限价单最危险的地方」。

    ⚠️ 触发发生在那根 K 线中间的某一刻，这根 K 线剩下的部分还能不能成交，从 K 线上看不出来，
    所以这里从**下一根**开始找成交机会。K 线越细，这个保守假设的代价越小。
    """
    _check(side)
    when = touched(bars, level, side, prices)
    if when is None:
        return {"触发时间": None, "成交时间": None, "成交价": np.nan, "成交": False}
    after = bars.iloc[bars.index.get_loc(when) + 1:]
    result = limit_fill(after, limit, "sell" if side == "sell" else "buy", expire=expire)
    return {"触发时间": when} | result


def oco_first(bars: pd.DataFrame, stop: float, target: float, prices: pd.DataFrame | None = None) -> dict:
    """一多一空两个价位，先碰到哪个（括号单 / OCO 的核心问题，做多的口径）。

    同一根 K 线里两个价位都碰到了，就没法从 K 线判断顺序，记成 "同一根"——第 11 篇的 first_passage
    用的是同一条规矩。K 线越细，这类无法判断的次数越少。
    """
    source = bars if prices is None else prices
    down = (source["low"] <= stop).reindex(bars.index).fillna(False)
    up = (source["high"] >= target).reindex(bars.index).fillna(False)
    if not down.any() and not up.any():
        return {"结果": "都没碰到", "时间": None}
    stop_at = bars.index[down][0] if down.any() else None
    target_at = bars.index[up][0] if up.any() else None
    if stop_at is not None and target_at is not None and stop_at == target_at:
        return {"结果": "同一根", "时间": stop_at}
    if target_at is None or (stop_at is not None and stop_at < target_at):
        return {"结果": "先到止损", "时间": stop_at}
    return {"结果": "先到目标", "时间": target_at}
