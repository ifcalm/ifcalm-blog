"""talab.indicators：技术指标。第 10 篇：成交量、VWAP、Volume Profile；第 12 篇：移动平均线；第 13 篇：MACD 和背离。"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 一、成交量
# ---------------------------------------------------------------------------

def relative_volume(volume: pd.Series, n: int = 20, by=None) -> pd.Series:
    """相对成交量：这根 K 线的成交量 ÷ 之前 n 根的平均成交量（不含这一根）。

    by 不为空时，只和同一组的历史比较。比如 by=volume.index.hour，
    就是和之前 n 天「同一个小时」的平均成交量比，去掉一天之内成交量的固定起伏。
    """
    if by is None:
        return volume / volume.rolling(n).mean().shift(1)
    average = volume.groupby(by).transform(lambda s: s.rolling(n).mean().shift(1))
    return volume / average


# ---------------------------------------------------------------------------
# 二、VWAP
# ---------------------------------------------------------------------------

def typical_price(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """典型价格 (最高 + 最低 + 收盘) ÷ 3。没有逐笔成交数据时，用它近似一根 K 线的平均成交价。"""
    return (high + low + close) / 3


def vwap(price: pd.Series, volume: pd.Series, session) -> pd.Series:
    """成交量加权平均价，每个交易时段重新开始累计。

    price:   每根 K 线的成交均价；有逐笔数据时用 成交额 ÷ 成交量，没有时用 typical_price
    session: 和 price 等长的分组键，比如 price.index.floor("1D") 表示按 UTC 自然日重置
    第 k 根 K 线上的值 = 这个时段开始到第 k 根（含）的 Σ(价格 × 成交量) ÷ Σ成交量，只用到当时已经发生的成交。
    """
    amount = (price * volume).groupby(session).cumsum()
    return amount / volume.groupby(session).cumsum()


def anchored_vwap(price: pd.Series, volume: pd.Series, anchor) -> pd.Series:
    """锚定 VWAP：从 anchor 这根 K 线（含）开始累计，之前为 NaN。

    它等于「从锚点开始，所有成交的平均成本」。
    """
    after = price.index >= anchor
    amount = (price * volume).where(after).cumsum()
    return (amount / volume.where(after).cumsum()).where(after)


# ---------------------------------------------------------------------------
# 三、Volume Profile
# ---------------------------------------------------------------------------

def volume_profile(price: pd.Series, volume: pd.Series, bin_size: float) -> pd.Series:
    """按价格分箱统计成交量。每根 K 线的成交量全部记在它的成交均价所在的箱子里。

    返回的索引是每个箱子的下沿（bin_size 的整数倍），从低到高排列，没有成交的箱子补 0。
    分组用整数箱号（价格 ÷ bin_size 向下取整），避免用小数价格做分组键带来的舍入误差。
    """
    number = np.floor(price.to_numpy(dtype=float) / bin_size).astype(np.int64)
    counts = pd.Series(volume.to_numpy(dtype=float)).groupby(number).sum()
    full = np.arange(counts.index.min(), counts.index.max() + 1)
    profile = counts.reindex(full, fill_value=0.0)
    profile.index = full * float(bin_size)
    profile.attrs["bin_size"] = bin_size          # value_area 需要知道格子多宽
    return profile


def value_area(profile: pd.Series, share: float = 0.7) -> dict[str, float]:
    """POC（成交量最大的价格）和价值区间（围绕 POC、包含 share 比例成交量的连续价格区间）。

    从 POC 所在的箱子开始，每次比较上方和下方紧挨着的一个箱子，把成交量大的那个并进来
    （一样大时并上方的），直到累计成交量达到 share。成交量最大的箱子不止一个时，取价格最低的那个。
    返回 poc（POC 箱子的中点）、val（价值区间下沿）、vah（价值区间上沿），都是价格。
    profile 应该是 volume_profile 的结果（格子宽度记在 profile.attrs["bin_size"] 里）。
    """
    volumes = profile.to_numpy(dtype=float)
    size = profile.attrs["bin_size"]
    k = int(np.argmax(volumes))
    low = high = k
    total, covered = volumes.sum(), volumes[k]
    while covered < share * total:
        below = volumes[low - 1] if low > 0 else -1.0
        above = volumes[high + 1] if high < len(volumes) - 1 else -1.0
        if above >= below:
            high += 1
            covered += volumes[high]
        else:
            low -= 1
            covered += volumes[low]
    return {"poc": profile.index[k] + size / 2, "val": profile.index[low], "vah": profile.index[high] + size}


# ---------------------------------------------------------------------------
# 四、移动平均线（第 12 篇）
# ---------------------------------------------------------------------------
#
# 这一部分起，所有指标函数遵守同一套约定：
# 1. 输入一个 Series（通常是收盘价）和参数，返回一个和输入索引完全相同的 Series
# 2. 数据还不够算出第一个值的位置（预热期）返回 NaN，不补 0、不用更短的窗口凑
# 3. 第 k 个值只用到第 k 个及之前的输入：用前 k 个数据算出的结果，和用全部数据算出的前 k 个完全一样
# 4. 结果和 TA-Lib 的同名函数一致（有差异的地方在文档里写明）

def _check_period(n: int) -> None:
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError(f"周期 n 必须是正整数，收到的是 {n!r}")


def sma(x: pd.Series, n: int) -> pd.Series:
    """简单移动平均：最近 n 个值的算术平均。前 n - 1 个为 NaN；窗口里有 NaN 时结果也是 NaN。"""
    _check_period(n)
    return x.rolling(n).mean()


def wma(x: pd.Series, n: int) -> pd.Series:
    """加权移动平均：最近一个值的权重是 n，往前依次是 n - 1、…、1，再除以权重之和 n(n + 1) / 2。"""
    _check_period(n)
    weights = np.arange(1, n + 1, dtype=float)
    return x.rolling(n).apply(lambda w: np.dot(w, weights), raw=True) / weights.sum()


def ema(x: pd.Series, n: int, alpha: float | None = None) -> pd.Series:
    """指数移动平均：新值 = 旧值 + alpha × (今天 - 旧值)，默认 alpha = 2 / (n + 1)。

    第一个值是前 n 个有效值的简单平均（和 TA-Lib 一样），出现在第 n 个有效值的位置，之前为 NaN。
    开头的 NaN 会被跳过，所以可以直接对另一个指标的结果（开头有预热期）再求 EMA。
    alpha = 1 / n 时就是第 8 篇 structure.wilder_smooth 的 Wilder 平滑。
    ⚠️ pandas 的 x.ewm(span=n, adjust=False).mean() 用第一个值做初始值，前面一段和这里不同。
    """
    _check_period(n)
    a = 2 / (n + 1) if alpha is None else alpha
    v = x.to_numpy(dtype=float)
    out = np.full(len(v), np.nan)
    valid = np.flatnonzero(~np.isnan(v))
    if len(valid) >= n:
        start = valid[0] + n - 1
        out[start] = v[valid[0]:start + 1].mean()
        for i in range(start + 1, len(v)):
            out[i] = out[i - 1] + a * (v[i] - out[i - 1])
    return pd.Series(out, index=x.index)


def average_lag(weights) -> float:
    """一组权重的平均滞后：每个值「过去了几根」按权重加权平均。weights[0] 是最新的一根（滞后 0）。

    SMA 是 (n - 1) / 2；WMA 是 (n - 1) / 3；EMA 是 (1 - alpha) / alpha，alpha = 2 / (n + 1) 时正好也是 (n - 1) / 2。
    """
    w = np.asarray(weights, dtype=float)
    return float(np.dot(np.arange(len(w)), w) / w.sum())


def cross_above(a: pd.Series, b: pd.Series) -> pd.Series:
    """a 从不高于 b 变成高于 b 的那一根为 True（上穿）。前一根或这一根有 NaN 时为 False。"""
    return (a > b) & (a.shift(1) <= b.shift(1))


def cross_below(a: pd.Series, b: pd.Series) -> pd.Series:
    """a 从不低于 b 变成低于 b 的那一根为 True（下穿）。"""
    return (a < b) & (a.shift(1) >= b.shift(1))


def bias(close: pd.Series, ma: pd.Series) -> pd.Series:
    """乖离率：收盘价偏离均线的比例，close / ma - 1。"""
    return close / ma - 1


# ---------------------------------------------------------------------------
# 五、MACD（第 13 篇）
# ---------------------------------------------------------------------------

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD（Appel）：快 EMA 减慢 EMA 是 MACD 线，MACD 线的 EMA 是信号线，两者之差是柱（Aspray）。

    和 TA-Lib 的 MACD 一致，有两处细节：
    1. 快 EMA 不从第 fast 根开始，而是和慢 EMA 同一根开始：用第 slow - fast + 1 到第 slow 个有效值的平均做初始值
    2. 三列同时出现，都从第 slow + signal - 1 个有效值开始；在这之前 MACD 线虽然算得出来，也记为 NaN
    返回 macd、signal、hist 三列，单位和价格相同。
    """
    for n in (fast, slow, signal):
        _check_period(n)
    if fast >= slow:
        raise ValueError(f"快线周期 {fast} 必须小于慢线周期 {slow}")
    valid = np.flatnonzero(close.notna().to_numpy())
    if len(valid) == 0:
        return pd.DataFrame({"macd": close * np.nan, "signal": close * np.nan, "hist": close * np.nan})
    position = np.arange(len(close))
    fast_line = ema(close.where(position >= valid[0] + slow - fast), fast)      # 让快 EMA 和慢 EMA 同一根开始
    line = fast_line - ema(close, slow)
    signal_line = ema(line, signal)
    line = line.where(signal_line.notna())
    return pd.DataFrame({"macd": line, "signal": signal_line, "hist": line - signal_line})


def ema_response(n: int, period) -> np.ndarray:
    """n 日 EMA 对「周期为 period 根 K 线的正弦波」的复数响应：绝对值是振幅放大倍数，辐角是相位。

    alpha = 2 / (n + 1)，响应 = alpha / (1 - (1 - alpha) × e^(-iω))，ω = 2π / period。
    MACD 线的响应是 ema_response(fast) - ema_response(slow)；柱再乘以 1 - ema_response(signal)。
    """
    alpha = 2 / (n + 1)
    omega = 2 * np.pi / np.asarray(period, dtype=float)
    return alpha / (1 - (1 - alpha) * np.exp(-1j * omega))


def divergences(swings: pd.DataFrame, indicator: pd.Series, kind: str = "bearish",
                min_bars: int = 5, max_bars: int = 60) -> pd.DataFrame:
    """找出相邻两个同类摆动点之间的背离。

    swings 是 structure.zigzag 或 fractals 的结果；indicator 通常是 MACD 柱，索引和价格相同。
    kind="bearish"（顶背离）：相邻两个摆动高点，后一个价格更高，相隔 min_bars 到 max_bars 根。
        每个高点对应的指标值，取「前一个摆动低点之后（不含）到这个高点（含）」这一段里指标的最大值，
        因为柱的峰值常常比价格的高点早出现几根。
        后一段的最大值更低、而且前一段的最大值大于 0，就是背离。
    kind="bullish"（底背离）：高低、大小全部反过来。
    返回每一对「价格创新高（新低）」的摆动点，divergence 列标明是不是背离；不是背离的也保留，方便做对照。
    confirmed_at 是第二个摆动点被确认的时刻：在这之前，第二个高点还不存在，背离也就还不存在。
    """
    if kind not in ("bearish", "bullish"):
        raise ValueError('kind 只能是 "bearish" 或 "bullish"')
    want = 1 if kind == "bearish" else -1
    values = indicator.to_numpy(dtype=float)
    pos = {t: i for i, t in enumerate(indicator.index)}
    ordered = swings.sort_values("time").reset_index(drop=True)
    rows, previous, leg_start = [], None, 0
    for s in ordered.itertuples():
        if s.kind != want:
            leg_start = pos[s.time] + 1                      # 反向的摆动点之后，开始新的一段
            continue
        leg = values[leg_start:pos[s.time] + 1]
        leg = leg[~np.isnan(leg)]
        extreme = (leg.max() if want == 1 else leg.min()) if len(leg) else np.nan
        if previous is not None and not np.isnan(extreme) and not np.isnan(previous[1]):
            first, first_value = previous
            gap = pos[s.time] - pos[first.time]
            further = (s.price - first.price) * want > 0
            if min_bars <= gap <= max_bars and further:
                weaker = (extreme - first_value) * want < 0
                same_side = first_value * want > 0
                rows.append((first.time, s.time, first.price, s.price, first_value, extreme, s.confirmed_at,
                             bool(weaker and same_side)))
        previous = (s, extreme)
    return pd.DataFrame(rows, columns=["first", "second", "first_price", "second_price",
                                       "first_value", "second_value", "confirmed_at", "divergence"])
