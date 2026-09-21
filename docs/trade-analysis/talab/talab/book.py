"""talab.book：盘口深度。番外篇——补第 28 篇留下的那个洞。

第 28 篇量了**价差**：BTC 永续平时的真实买卖价差中位数只有 0.0328 个基点，
基本就是一个最小变动价位；但振幅 20.4% 那天，有一分钟飙到 **161.5 个基点**。

那一篇留了半个问题没答：**价差只是柜台前排队的长度，柜台后面还有多少钱，它没量。**

这一篇用银行挤兑做比方：

| 挤兑 | 盘口 |
|---|---|
| 柜台前排多长的队 | 买卖价差 |
| **金库里还有多少现金** | **深度** |
| 「我随时能取钱」 | 「我随时能卖掉」 |
| 钱不是被取光的，是**被搬走藏起来的** | 深度不是被吃掉的，是**被撤走的** |

⚠️ **先说清楚这份数据不是什么。**Binance 公开的 `bookDepth` 是**每 30 秒一张快照**，
每张只有 12 个数：买卖两侧在 ±0.2%、1%、2%、3%、4%、5% 六个距离上的**累计**挂单金额。
它不是逐笔订单流，也不是完整的 L2 盘口。所以：

- **能答**：现价上下 1% 以内还剩多少钱、两侧对不对称、崩盘时掉多少、多久回来
- **答不了**：大单墙在哪一档、有没有撤单动作、是不是冰山单——
  这些要逐笔订单流，公开数据站没有，只能自己开 WebSocket 录，而且录的是未来

⚠️ 还有两条边界，正文第三节会展开：这份数据**只有 BTC 永续、只从 2023-01-01 开始**，
而第 28 篇那套价差数据**只有 2023-05-16 到 2024-03-30**——
**两者配得上对的只有 320 天。**
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LEVELS = (0.2, 1.0, 2.0, 3.0, 4.0, 5.0)
DAY = 2 * 60 * 24                      # 一天有多少张 30 秒快照


def _columns(level: float) -> tuple[str, str]:
    if level not in LEVELS:
        raise ValueError(f"只有 {LEVELS} 这几档，收到 {level}")
    return f"{-level:+g}%", f"{level:+g}%"


def sides(depth: pd.DataFrame, level: float = 1.0) -> pd.DataFrame:
    """把某一档拆成买侧、卖侧、合计和不对称。

    ⚠️ 负号那一侧是**买盘**（挂在中间价下方）。「买侧深度」回答的是
    **「现价下方 1% 以内，一共还有多少钱在等着接」**——这正是你想卖出时唯一关心的数。
    """
    bid, ask = _columns(level)
    if bid not in depth or ask not in depth:
        raise ValueError(f"表里没有 {bid} 或 {ask} 这两列")
    out = pd.DataFrame({"买侧": depth[bid], "卖侧": depth[ask]})
    out["合计"] = out["买侧"] + out["卖侧"]
    out["不对称"] = (out["买侧"] - out["卖侧"]) / out["合计"].where(out["合计"] > 0)
    return out


def imbalance(depth: pd.DataFrame, level: float = 1.0) -> pd.Series:
    """买卖不对称：(买 − 卖) ÷ (买 + 卖)，范围 −1 到 +1。

    正数表示买盘比卖盘厚。⚠️ 「买盘厚所以会涨」是盘口里最流行的说法之一，
    正文第七节会把它和打乱后的对照组放在一起量——**先别信它**。
    """
    return sides(depth, level)["不对称"].rename(f"不对称（{level:g}%）")


def relative(values: pd.Series, window: int = DAY) -> pd.Series:
    """相对「最近 `window` 张快照的中位数」是几倍。

    深度的绝对金额在三年里长了好几倍（市场变深了），直接比 2023 年和 2026 年的美元数没有意义。
    ⚠️ 这里用的是**滚动中位数**而不是全样本中位数，也不分 UTC 小时——
    第 20 篇量过 BTC 有明显的小时效应，正文第五节会检查它够不够小。
    """
    if window < 2:
        raise ValueError("窗口至少是 2")
    base = values.rolling(window, min_periods=window // 4).median().shift(1)
    return (values / base.where(base > 0)).rename("相对平常")


def squeeze(depth: pd.DataFrame, taker_sell: pd.Series, level: float = 1.0,
            span: int = 30) -> pd.DataFrame:
    """**深度少掉的那些钱，有多少能被成交解释。**这是这一篇的核心计算。

    每个时刻回看 `span` 张快照（默认 30 张 = 15 分钟）：

    - `少掉多少`：买侧深度从那时到现在减少了多少美元
    - `吃掉多少`：同一段时间里主动卖出的成交额（taker 卖单打在买盘上）
    - `吃掉的占比`：后者 ÷ 前者

    占比接近 1，说明买盘是**被吃掉**的；占比很小，说明那些钱**自己走了**——
    要么撤单，要么挂到更远的地方去了。⚠️ 对一个想卖出的人来说这两件事没有区别：
    **它不在现价下方 1% 以内了。**

    ⚠️ 这个比值是一个**下界**：深度只统计 ±1% 以内，而成交可能发生在更远的地方，
    所以「吃掉多少」会被高估一点点。结论是「撤走的比吃掉的多得多」时，这个方向的误差不影响结论。
    """
    if span < 1:
        raise ValueError("回看的快照数至少是 1")
    bid = sides(depth, level)["买侧"]
    lost = (bid.shift(span) - bid).rename("少掉多少")
    eaten = taker_sell.reindex(bid.index).fillna(0.0).rolling(span).sum().rename("吃掉多少")
    share = (eaten / lost.where(lost > 0)).rename("吃掉的占比")
    return pd.concat([bid.rename("买侧深度"), lost, eaten, share], axis=1)


def recovery(values: pd.Series, events, horizon: int = DAY, fraction: float = 0.9,
             before: int = 60, trough_within: int | None = None) -> pd.DataFrame:
    """事件之后，多久回到事件**前**水平的 `fraction`。

    「事件前水平」取事件前 `before` 张快照的中位数。

    ⚠️ 计时从**最低点**算起，不是从事件那一刻算起。崩盘那一分钟深度往往还没来得及掉，
    从事件时刻起算会把一大半事件记成「0 分钟就回来了」——**那不是恢复快，是还没开始跌**。

    ⚠️ 而最低点只在事件后 `trough_within` 张快照里找（默认 120 张 = 一小时，不超过 `horizon`）。
    `horizon` 动辄两天，在两天里找最低点，找到的多半是**下一次崩盘**，不是这一次的谷底。

    回不到就记 NaN——别把回不到的那些当成 0，也别把它们悄悄丢掉：
    **它们才是最该看的那几次。**
    """
    if not 0 < fraction <= 1:
        raise ValueError("fraction 要在 0 和 1 之间")
    trough_within = min(120, horizon) if trough_within is None else trough_within
    if trough_within < 1 or trough_within > horizon:
        raise ValueError("找谷底的窗口要在 1 和 horizon 之间")
    index, array = values.index, values.to_numpy(float)
    rows = []
    for event in pd.DatetimeIndex(events):
        when = event.tz_localize(index.tz) if index.tz is not None and event.tz is None else event
        position = int(index.searchsorted(when))
        if position - before < 0 or position + 1 >= len(array):
            continue
        base = float(np.nanmedian(array[position - before:position]))
        after = array[position:position + horizon]
        if not len(after) or np.all(np.isnan(after)):
            continue
        trough = int(np.nanargmin(after[:trough_within]))
        back = np.flatnonzero(after[trough:] >= base * fraction)
        rows.append({"事件": index[position], "事件前水平": base,
                     "最低点": float(after[trough]),
                     "最低点占事件前": (float(after[trough]) / base) if base > 0 else np.nan,
                     "最低点在几分钟后": trough / 2,
                     "几张快照后回来": float(back[0]) if len(back) else np.nan,
                     "几分钟后回来": float(back[0]) / 2 if len(back) else np.nan})
    return pd.DataFrame(rows)


def slope(depth: pd.DataFrame, near: float = 1.0, far: float = 5.0) -> pd.Series:
    """盘口的陡峭程度：远档深度 ÷ 近档深度（两侧合计）。

    这个比值越大，说明钱越集中在**远处**——近处很薄，稍微一卖价格就往下走一截。
    崩盘的时候它会怎么变，正文第六节会量。
    """
    if not near < far:
        raise ValueError("near 要小于 far")
    close_in = sides(depth, near)["合计"]
    far_out = sides(depth, far)["合计"]
    return (far_out / close_in.where(close_in > 0)).rename(f"{far:g}% ÷ {near:g}%")
