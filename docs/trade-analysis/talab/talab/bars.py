"""talab.bars：K 线的构造与拆解。第 6 篇。"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

OHLCV = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
SUMMABLE = ["quote_volume", "trades", "taker_buy_base", "taker_buy_quote"]


# ---------------------------------------------------------------------------
# 一、合成：小周期 → 大周期
# ---------------------------------------------------------------------------

def resample_ohlcv(df: pd.DataFrame, rule: str, traded_only: bool = False) -> pd.DataFrame:
    """把小周期 K 线合成大周期 K 线。

    开盘取第一根的开盘价，最高取最大值，最低取最小值，收盘取最后一根的收盘价，量类字段求和。
    每根大 K 线的时间戳是它的开始时间，包含开始时刻、不包含结束时刻。
    traded_only=True 时先去掉成交量为 0 的占位 K 线，否则占位 K 线的价格会被当成真实成交价。
    一根成交也没有的时间段不会出现在结果里。
    """
    src = df[df["volume"] > 0] if traded_only else df
    rules = dict(OHLCV)
    rules.update({c: "sum" for c in SUMMABLE if c in src.columns})
    out = src.resample(rule, label="left", closed="left").agg(rules)
    return out.dropna(subset=["open"])


# ---------------------------------------------------------------------------
# 二、拆解：实体和影线
# ---------------------------------------------------------------------------

def anatomy(df: pd.DataFrame) -> pd.DataFrame:
    """每根 K 线的各个部分。

    body          实体：收盘 − 开盘（带符号，正数是阳线）
    upper_shadow  上影线：最高 − max(开盘, 收盘)
    lower_shadow  下影线：min(开盘, 收盘) − 最低
    range         全长：最高 − 最低
    body_ratio    实体占全长的比例，0～1
    clv           收盘位置：(收盘 − 最低) ÷ 全长，0 表示收在最低，1 表示收在最高
    """
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    rng = h - l
    safe = rng.where(rng > 0)                                 # 全长为 0 时比例没有意义，记为 NaN
    return pd.DataFrame({
        "body": c - o,
        "upper_shadow": h - np.maximum(o, c),
        "lower_shadow": np.minimum(o, c) - l,
        "range": rng,
        "body_ratio": (c - o).abs() / safe,
        "clv": (c - l) / safe,
    }, index=df.index)


# ---------------------------------------------------------------------------
# 三、K 线丢掉的路径：用小周期找回来
# ---------------------------------------------------------------------------

def intraday_extremes(minute: pd.DataFrame, rule: str = "1D") -> pd.DataFrame:
    """每个大周期里，最高价和最低价分别出现在哪根小 K 线。

    同一个最高价出现多次时取第一次。high_first 为 True 表示最高价先于最低价出现；
    两者出现在同一根小 K 线里时，小 K 线本身也分不清先后，记为 NA。
    """
    period = minute.index.floor(rule)
    t_high = minute["high"].groupby(period).idxmax()
    t_low = minute["low"].groupby(period).idxmin()
    out = pd.DataFrame({"time_of_high": t_high, "time_of_low": t_low})
    out["high_first"] = (out["time_of_high"] < out["time_of_low"]).astype("boolean")
    out.loc[out["time_of_high"] == out["time_of_low"], "high_first"] = pd.NA
    return out


def first_touch(minute: pd.DataFrame, up: float, down: float, rule: str = "1D") -> pd.Series:
    """以每个大周期的开盘价为基准，价格先碰到 +up 还是 −down（都是比例，比如 0.03）。

    返回每个周期的结果："up" 先碰到上方，"down" 先碰到下方，"none" 两边都没碰到，
    "same_bar" 两边在同一根小 K 线里都碰到了（小 K 线也分不清先后）。
    """
    period = minute.index.floor(rule)
    base = minute["open"].groupby(period).transform("first")          # 每个周期的开盘价
    hit_up = minute["high"] >= base * (1 + up)
    hit_down = minute["low"] <= base * (1 - down)
    times = minute.index.to_series(index=minute.index)
    first_up = times[hit_up].groupby(period[hit_up.to_numpy()]).first()      # 第一次碰到上方的时间
    first_down = times[hit_down].groupby(period[hit_down.to_numpy()]).first()
    days = pd.Index(period.unique())
    fu, fd = first_up.reindex(days), first_down.reindex(days)
    result = pd.Series("none", index=days, dtype=object)
    result[fu.notna() & (fd.isna() | (fu < fd))] = "up"
    result[fd.notna() & (fu.isna() | (fd < fu))] = "down"
    result[fu.notna() & fd.notna() & (fu == fd)] = "same_bar"
    return result


# ---------------------------------------------------------------------------
# 四、Heikin-Ashi：平均出来的 K 线
# ---------------------------------------------------------------------------

def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    """Heikin-Ashi K 线。

    HA 收盘 = (开 + 高 + 低 + 收) ÷ 4
    HA 开盘 = (前一根 HA 开盘 + 前一根 HA 收盘) ÷ 2；第一根用 (开 + 收) ÷ 2
    HA 最高 = max(最高, HA 开盘, HA 收盘)
    HA 最低 = min(最低, HA 开盘, HA 收盘)
    ⚠️ 这些价格大多不是真实成交过的价格。
    """
    o, h, l, c = (df[k].to_numpy(dtype=float) for k in ["open", "high", "low", "close"])
    ha_close = (o + h + l + c) / 4
    ha_open = np.empty(len(df))
    ha_open[0] = (o[0] + c[0]) / 2
    for i in range(1, len(df)):
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2
    return pd.DataFrame({
        "open": ha_open,
        "high": np.maximum.reduce([h, ha_open, ha_close]),
        "low": np.minimum.reduce([l, ha_open, ha_close]),
        "close": ha_close,
    }, index=df.index)


# ---------------------------------------------------------------------------
# 五、Renko：去掉时间轴的砖块图
# ---------------------------------------------------------------------------

def renko(close: pd.Series, brick: float, log: bool = False) -> pd.DataFrame:
    """用收盘价构造 Renko 砖块。

    brick: 砖块大小。log=False 时是价格单位（比如 1000 美元）；
           log=True 时是比例（比如 0.05 表示每块 5%），砖块在对数坐标上等高。
    规则：第一个价格是起点。顺着当前方向，每走满一块砖就画一块；
         要反向，价格必须越过当前这块砖的另一端再走满一块砖（也就是离最后一块砖的收盘两块砖远）。
    返回每块砖：formed_at（形成这块砖的那根 K 线的时间）、open、close、direction（+1 或 −1）。
    """
    step = math.log(1 + brick) if log else brick
    xs = np.log(close.to_numpy(dtype=float)) if log else close.to_numpy(dtype=float)
    rows = []
    lo = hi = xs[0]                  # 最后一块砖的下沿和上沿；还没有砖时两者都是起点
    for t, x in zip(close.index, xs):
        # 价格比最后一块砖的上沿高出一块砖：画一块向上的砖。
        # 如果最后一块砖是向下的，它的上沿就是它的开盘价，所以这正好是「离收盘两块砖」的反向条件
        while x >= hi + step:
            rows.append((t, hi, hi + step, 1))
            lo, hi = hi, hi + step
        # 价格比最后一块砖的下沿低出一块砖：画一块向下的砖（道理同上）
        while x <= lo - step:
            rows.append((t, lo, lo - step, -1))
            lo, hi = lo - step, lo
    out = pd.DataFrame(rows, columns=["formed_at", "open", "close", "direction"])
    if log:
        out[["open", "close"]] = np.exp(out[["open", "close"]])
    return out
