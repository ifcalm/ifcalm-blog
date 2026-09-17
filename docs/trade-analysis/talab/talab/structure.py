"""talab.structure：摆动点、趋势状态和趋势强度（第 8 篇）；关键位置和缺口（第 9 篇）；市场状态、入场和标注比较（第 11 篇）。"""
from __future__ import annotations

import numpy as np
import pandas as pd

SWING_COLUMNS = ["time", "price", "kind", "confirmed_at"]


# ---------------------------------------------------------------------------
# 一、摆动点
# ---------------------------------------------------------------------------

def fractals(high: pd.Series, low: pd.Series, left: int = 2, right: int = 2) -> pd.DataFrame:
    """分形摆动点：一根 K 线的最高价高于左边 left 根、不低于右边 right 根，就是摆动高点（摆动低点反过来）。

    返回的每一行是一个摆动点：
    time:          摆动点所在的 K 线
    price:         摆动点的价格（高点用最高价，低点用最低价）
    kind:          1 表示高点，-1 表示低点
    confirmed_at:  确认的时刻，也就是右边第 right 根 K 线。在这根 K 线收盘之前，这个摆动点还不存在

    左边用「严格高于」、右边用「不低于」：连续几根最高价相同时，只有第一根算高点。
    同一根 K 线可能既是高点又是低点（一根很长的 K 线）。
    """
    h, l, idx = high.to_numpy(float), low.to_numpy(float), high.index
    rows = []
    for i in range(left, len(h) - right):
        if h[i] > h[i - left:i].max() and h[i] >= h[i + 1:i + right + 1].max():
            rows.append((idx[i], h[i], 1, idx[i + right]))
        if l[i] < l[i - left:i].min() and l[i] <= l[i + 1:i + right + 1].min():
            rows.append((idx[i], l[i], -1, idx[i + right]))
    return pd.DataFrame(rows, columns=SWING_COLUMNS)


def zigzag(price: pd.Series, threshold: float) -> pd.DataFrame:
    """ZigZag 摆动点：价格从最近的极值反向走了 threshold（比如 0.1 表示 10%），这个极值才被确认。

    只用一个价格序列（通常是收盘价），这样每一步的先后顺序都是确定的。
    高点和低点一定交替出现。返回的列和 fractals 相同。

    注意两点：
    1. 最后一段还没有反向 threshold，它的极值不在结果里：它随时可能被新的极值替换
    2. 第一个摆动点可能就是序列的第一根 K 线，因为在它之前没有数据
    """
    p, idx = price.to_numpy(float), price.index
    rows = []
    direction = 0                        # 0：还没有确认任何摆动点；1：正在找高点；-1：正在找低点
    hi = lo = p[0]
    hi_i = lo_i = 0
    for i in range(1, len(p)):
        if direction >= 0 and p[i] > hi:
            hi, hi_i = p[i], i
        if direction <= 0 and p[i] < lo:
            lo, lo_i = p[i], i
        if direction == 0:
            if hi_i > lo_i and p[i] >= lo * (1 + threshold):         # 先低后高，涨够了：确认低点
                rows.append((idx[lo_i], lo, -1, idx[i]))
                direction = 1
            elif lo_i > hi_i and p[i] <= hi * (1 - threshold):       # 先高后低，跌够了：确认高点
                rows.append((idx[hi_i], hi, 1, idx[i]))
                direction = -1
        elif direction == 1 and p[i] <= hi * (1 - threshold):        # 从高点回落够了：确认高点，开始找低点
            rows.append((idx[hi_i], hi, 1, idx[i]))
            direction, lo, lo_i = -1, p[i], i
        elif direction == -1 and p[i] >= lo * (1 + threshold):       # 从低点反弹够了：确认低点，开始找高点
            rows.append((idx[lo_i], lo, -1, idx[i]))
            direction, hi, hi_i = 1, p[i], i
    return pd.DataFrame(rows, columns=SWING_COLUMNS)


# ---------------------------------------------------------------------------
# 二、趋势状态
# ---------------------------------------------------------------------------

def trend_state(swings: pd.DataFrame, high: pd.Series, low: pd.Series) -> pd.DataFrame:
    """在每一根 K 线收盘时，只用已经确认的摆动点，判断高低点结构。

    state = 1：最近两个高点抬高，最近两个低点也抬高（上升）
    state = -1：最近两个高点降低，最近两个低点也降低（下降）
    state = 0：其他情况（高点和低点方向不一致）
    last_high / last_low：最近一个已确认的高点 / 低点

    「更高」有时不用等确认：最近一个已确认高点之后，价格已经超过了它，
    新高点的具体位置还不知道，但「它比上一个高点高」已经确定了。低点同理。
    high、low 用来计算这种「已经超过」；对收盘价的 ZigZag，两个参数都传收盘价。
    还没有两个高点和两个低点时为 NaN。
    """
    idx = high.index
    h, l = high.to_numpy(float), low.to_numpy(float)
    pos = {t: i for i, t in enumerate(idx)}
    events: dict[int, list] = {}
    for s in swings.sort_values("confirmed_at", kind="stable").itertuples():
        events.setdefault(pos[s.confirmed_at], []).append((pos[s.time], s.price, s.kind))

    highs, lows = [], []
    beyond_high, beyond_low = -np.inf, np.inf     # 最近一个已确认高点之后的最高价 / 低点之后的最低价
    out = np.full((len(idx), 3), np.nan)
    for j in range(len(idx)):
        beyond_high, beyond_low = max(beyond_high, h[j]), min(beyond_low, l[j])
        for i, price, kind in events.get(j, []):
            if kind == 1:
                highs.append(price)
                beyond_high = h[i + 1:j + 1].max() if j > i else -np.inf
            else:
                lows.append(price)
                beyond_low = l[i + 1:j + 1].min() if j > i else np.inf
        if len(highs) < 2 or len(lows) < 2:
            continue
        h0, h1 = (highs[-1], beyond_high) if beyond_high > highs[-1] else (highs[-2], highs[-1])
        l0, l1 = (lows[-1], beyond_low) if beyond_low < lows[-1] else (lows[-2], lows[-1])
        state = 1 if h1 > h0 and l1 > l0 else -1 if h1 < h0 and l1 < l0 else 0
        out[j] = [state, highs[-1], lows[-1]]
    return pd.DataFrame(out, index=idx, columns=["state", "last_high", "last_low"])


def break_state(levels: pd.DataFrame, close: pd.Series) -> pd.Series:
    """突破版的趋势状态：收盘价突破最近一个已确认的高点，变成 1；跌破最近一个已确认的低点，变成 -1；否则保持。

    levels 是 trend_state 的结果（用到 last_high、last_low 两列）。第一次突破之前为 NaN。
    """
    up = close > levels["last_high"]
    down = close < levels["last_low"]
    return pd.Series(np.where(up, 1.0, np.where(down, -1.0, np.nan)), index=close.index).ffill()


# ---------------------------------------------------------------------------
# 三、趋势强度
# ---------------------------------------------------------------------------

def efficiency_ratio(close: pd.Series, n: int = 20) -> pd.Series:
    """效率比（Kaufman）：n 根 K 线的净变化 ÷ 每根变化的绝对值之和。

    1 表示一条直线，接近 0 表示来回走了很多路却没有走远。
    """
    return close.diff(n).abs() / close.diff().abs().rolling(n).sum()


def regression_slope(close: pd.Series, n: int = 20) -> pd.DataFrame:
    """对最近 n 根 K 线的对数价格做直线回归。

    slope: 每根 K 线的对数斜率，exp(slope) - 1 约等于每根 K 线的平均涨幅
    r2:    直线能解释多少价格变化（0 到 1），越接近 1，价格越贴着直线走
    """
    y = np.log(close)
    t = pd.Series(np.arange(len(y), dtype=float), index=close.index)
    return pd.DataFrame({
        "slope": y.rolling(n).cov(t) / t.rolling(n).var(),
        "r2": y.rolling(n).corr(t) ** 2,
    })


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """真实波幅：今天的最高最低，连同昨天收盘到今天的跳空，一起算进波动。第一根为 NaN。"""
    prev = close.shift(1)
    tr = pd.concat([high - low, (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return tr.where(prev.notna())


def directional_movement(high: pd.Series, low: pd.Series) -> pd.DataFrame:
    """方向运动：今天向上扩展了多少（+DM）、向下扩展了多少（-DM），只保留较大的一边。第一根为 NaN。"""
    up = high.diff()
    down = -low.diff()
    plus = up.where((up > down) & (up > 0), 0.0).where(up.notna())
    minus = down.where((down > up) & (down > 0), 0.0).where(down.notna())
    return pd.DataFrame({"plus_dm": plus, "minus_dm": minus})


def wilder_smooth(x: pd.Series, n: int) -> pd.Series:
    """Wilder 平滑：第一个值是前 n 个有效值的平均，之后每次 新值 = 旧值 + (今天 - 旧值) ÷ n。"""
    v = x.to_numpy(float)
    out = np.full(len(v), np.nan)
    valid = np.flatnonzero(~np.isnan(v))
    if len(valid) >= n:
        start = valid[0] + n - 1
        out[start] = v[valid[0]:start + 1].mean()
        for i in range(start + 1, len(v)):
            out[i] = out[i - 1] + (v[i] - out[i - 1]) / n
    return pd.Series(out, index=x.index)


def adx(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.DataFrame:
    """Wilder 的 +DI、-DI 和 ADX。

    +DI / -DI：平滑后的 +DM / -DM 占平滑后真实波幅的百分比
    DX：两者之差占两者之和的百分比，只看差距，不看方向
    ADX：DX 再做一次 Wilder 平滑。第一个 ADX 出现在第 2n 根 K 线（下标 2n - 1）
    """
    atr = wilder_smooth(true_range(high, low, close), n)
    dm = directional_movement(high, low)
    plus_di = 100 * wilder_smooth(dm["plus_dm"], n) / atr
    minus_di = 100 * wilder_smooth(dm["minus_dm"], n) / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return pd.DataFrame({"plus_di": plus_di, "minus_di": minus_di, "adx": wilder_smooth(dx, n)})


# ---------------------------------------------------------------------------
# 四、关键位置（第 9 篇）
# ---------------------------------------------------------------------------

def cluster_levels(prices, tolerance: float) -> pd.DataFrame:
    """把相近的价格归成一个水平位。

    从小到大排序，以每一组最小的价格为基准，不超过它 (1 + tolerance) 倍的价格都归入这一组。
    返回每一组的平均价格（level）、最低（low）、最高（high）和个数（count）。
    """
    p = np.sort(np.asarray(prices, dtype=float))
    rows = []
    i = 0
    while i < len(p):
        j = i
        while j + 1 < len(p) and p[j + 1] <= p[i] * (1 + tolerance):
            j += 1
        rows.append((p[i:j + 1].mean(), p[i], p[j], j - i + 1))
        i = j + 1
    return pd.DataFrame(rows, columns=["level", "low", "high", "count"])


def level_tests(high: pd.Series, low: pd.Series, close: pd.Series, swings: pd.DataFrame, atr: pd.Series,
                zone: float = 0.25, distance: float = 1.5, max_flips: int = 1) -> pd.DataFrame:
    """跟踪每一个摆动点价格（水平位）的一生：被测试了几次，每次守住还是被突破，突破之后角色是否互换。

    摆动低点从支撑开始，摆动高点从阻力开始。距离都以 ATR 为单位，用前一根 K 线的 ATR（当时已知）：
    离开：收盘价在正确的一侧、离水平位至少 distance 个 ATR，之后再回来才算一次测试
    测试：支撑是最低价进入水平位上方 zone 个 ATR 以内；阻力是最高价进入下方 zone 个 ATR 以内
    结果：从测试那根 K 线起，先出现「收盘价离开 distance 个 ATR」算守住（held），
         先出现「收盘价穿到另一侧 distance 个 ATR」算突破（broken），数据结束还没分出来算 open
    突破之后，支撑变成阻力（或反过来），flips 加 1，测试次数重新计数；超过 max_flips 就不再跟踪。
    摆动点本身算原角色的第 1 次测试，所以第一行测试的 n 是 2。
    """
    h, l, c = high.to_numpy(float), low.to_numpy(float), close.to_numpy(float)
    a, idx = atr.to_numpy(float), close.index
    pos = {t: i for i, t in enumerate(idx)}
    rows = []
    for s in swings.itertuples():
        level, side = s.price, (1 if s.kind == -1 else -1)       # 1：支撑（价格在上方）；-1：阻力（价格在下方）
        flips, n, armed = 0, 1, False
        j = pos[s.confirmed_at] + 1
        while j < len(c):
            unit = a[j - 1]
            if np.isnan(unit):
                j += 1
                continue
            if not armed:
                away = (c[j] - level) * side
                if away >= distance * unit:
                    armed = True
                elif away <= -distance * unit:                   # 还没离开就被突破：直接换角色
                    flips, side, n, armed = flips + 1, -side, 0, True
                    if flips > max_flips:
                        break
                j += 1
                continue
            touched = l[j] <= level + zone * unit if side == 1 else h[j] >= level - zone * unit
            if not touched:
                j += 1
                continue
            n += 1
            k, outcome = j, "open"
            while k < len(c):
                away = (c[k] - level) * side
                if away >= distance * unit:
                    outcome = "held"
                    break
                if away <= -distance * unit:
                    outcome = "broken"
                    break
                k += 1
            rows.append((s.time, level, "support" if side == 1 else "resistance", flips, n, idx[j], outcome,
                         idx[k] if k < len(c) else pd.NaT))
            if outcome == "open":
                break
            if outcome == "broken":
                flips, side, n = flips + 1, -side, 0
                if flips > max_flips:
                    break
            j = k + 1
    return pd.DataFrame(rows, columns=["level_time", "level", "role", "flips", "n", "test_time", "outcome", "resolved_at"])


# ---------------------------------------------------------------------------
# 五、缺口（第 9 篇）
# ---------------------------------------------------------------------------

def gaps(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
    """开盘价和前一根收盘价不相等的每一根 K 线。

    direction: 1 向上跳空，-1 向下跳空
    size:      开盘价 ÷ 前收盘价 - 1
    full:      完整缺口：向上时开盘价高于前一根最高价，向下时低于前一根最低价（K 线图上看得见空白）
    """
    prev_close, prev_high, prev_low = close.shift(1), high.shift(1), low.shift(1)
    size = open_ / prev_close - 1
    out = pd.DataFrame({"prev_close": prev_close, "open": open_, "size": size,
                        "direction": np.sign(size),
                        "full": (open_ > prev_high) | (open_ < prev_low)})
    return out[(size != 0) & size.notna()].astype({"direction": int})


def first_reach(high: pd.Series, low: pd.Series, start, level: float, from_above: bool):
    """从 start 这根 K 线（含）开始，价格第一次到达 level 的时间；一直没到达返回 NaT。

    from_above=True：价格原本在 level 上方，看最低价什么时候不高于 level（比如向上跳空的回补）。
    from_above=False：反过来，看最高价什么时候不低于 level。
    """
    part = low.loc[start:] <= level if from_above else high.loc[start:] >= level
    hit = part.index[part.to_numpy()]
    return hit[0] if len(hit) else pd.NaT


# ---------------------------------------------------------------------------
# 六、市场状态和三类入场（第 11 篇）
# ---------------------------------------------------------------------------

def market_state(levels: pd.DataFrame, close: pd.Series) -> pd.Series:
    """在每一根 K 线收盘时，把市场分成三种状态（趋势分上下，过渡分方向，一共五个标签）。

    levels 是 trend_state 的结果（用到 state、last_high、last_low 三列）：
    up / down：                       高点和低点同时抬高 / 同时降低（trend_state 的 1 / -1）
    range（震荡）：                   高点和低点方向不一致，收盘价还在最近一个已确认的高点和低点之间
    transition_up / transition_down： 高点和低点方向不一致，收盘价已经越过了最近一个已确认的高点 / 低点
    还没有两个高点和两个低点时为缺失值（NaN）。
    """
    state = levels["state"]
    labels = np.select([state == 1, state == -1, close > levels["last_high"], close < levels["last_low"]],
                       ["up", "down", "transition_up", "transition_down"], "range").astype(object)
    labels[state.isna().to_numpy()] = np.nan
    return pd.Series(labels, index=close.index, name="market_state")


def entries(close: pd.Series, high: pd.Series, low: pd.Series, swings: pd.DataFrame, levels: pd.DataFrame,
            state: pd.Series, failed_within: int = 5) -> pd.DataFrame:
    """三类入场信号，每个信号都在那根 K 线收盘时就能知道。

    pullback（回调）：上升趋势里，一个摆动高点刚被确认（价格已经从高点回落了一个阈值），
        之后第一根收盘价高于前一根最高价的 K 线，做多。下降趋势反过来，做空。
        等到信号之前状态已经不是同方向的趋势，这次回调作废。
    breakout（突破）：收盘价第一次越过最近一个已确认的高点，而且前一根 K 线不在上升趋势里，做多。
        低点反过来，做空。每个高点 / 低点只算第一次被收盘越过（不管那一次是不是信号）。
    failed（失败突破）：突破之后 failed_within 根 K 线以内，收盘价回到被突破的价位另一侧，反方向入场。

    返回每个信号的 time、kind、direction（1 做多、-1 做空）、level（回调是那个摆动点的价格，
    突破和失败突破是被突破的价位）。
    """
    c, h, l = close.to_numpy(float), high.to_numpy(float), low.to_numpy(float)
    idx, st = close.index, state.to_numpy(object)
    last_high, last_low = levels["last_high"].to_numpy(float), levels["last_low"].to_numpy(float)
    pos = {t: i for i, t in enumerate(idx)}
    rows = []

    confirmed = sorted((pos[s.confirmed_at], s.kind, s.price) for s in swings.itertuples())
    for k, (j0, kind, price) in enumerate(confirmed):
        trend = "up" if kind == 1 else "down"            # 高点确认 = 上升趋势里的回调开始了
        end = confirmed[k + 1][0] if k + 1 < len(confirmed) else len(c)
        for j in range(j0 + 1, end):
            if st[j] != trend:
                break
            if (kind == 1 and c[j] > h[j - 1]) or (kind == -1 and c[j] < l[j - 1]):
                rows.append((idx[j], "pullback", kind, price))
                break

    broken_high = broken_low = np.nan                     # 已经被收盘越过的高点 / 低点
    for j in range(1, len(c)):
        direction = 0
        if c[j] > last_high[j - 1] and last_high[j - 1] != broken_high:
            broken_high, level = last_high[j - 1], last_high[j - 1]
            direction = 1 if st[j - 1] != "up" else 0
        elif c[j] < last_low[j - 1] and last_low[j - 1] != broken_low:
            broken_low, level = last_low[j - 1], last_low[j - 1]
            direction = -1 if st[j - 1] != "down" else 0
        if direction == 0:
            continue
        rows.append((idx[j], "breakout", direction, level))
        for k in range(j + 1, min(j + 1 + failed_within, len(c))):
            if (c[k] - level) * direction < 0:
                rows.append((idx[k], "failed", -direction, level))
                break
    out = pd.DataFrame(rows, columns=["time", "kind", "direction", "level"])
    return out.sort_values("time", kind="stable").reset_index(drop=True)


def first_passage(close: pd.Series, high: pd.Series, low: pd.Series, atr: pd.Series, times, directions,
                  distance: float = 2.0, horizon: int = 20) -> np.ndarray:
    """从每个信号 K 线的收盘价出发，上下各放一条 distance 个 ATR 的线，看之后 horizon 根 K 线里先碰到哪一条。

    顺着 direction 的那条先碰到记 1，反方向的先碰到记 0，都没碰到记 NaN。
    同一根 K 线两条都碰到时，分不清先后，记 0（按对入场者不利的情况算）。
    价格随机游走、没有漂移时，两条线距离相同，记 1 的比例约为 50%。
    """
    c, h, l, a = (s.to_numpy(float) for s in (close, high, low, atr))
    pos = {t: i for i, t in enumerate(close.index)}
    out = np.full(len(times), np.nan)
    for n, (t, direction) in enumerate(zip(times, directions)):
        i = pos[t]
        upper, lower = c[i] + distance * a[i], c[i] - distance * a[i]
        for j in range(i + 1, min(i + 1 + horizon, len(c))):
            hit_up, hit_down = h[j] >= upper, l[j] <= lower
            if hit_up and hit_down:
                out[n] = 0.0
            elif hit_up or hit_down:
                out[n] = float(hit_up == (direction == 1))
            else:
                continue
            break
    return out


# ---------------------------------------------------------------------------
# 七、两份标注的比较（第 11 篇，实验一）
# ---------------------------------------------------------------------------

def agreement(a: pd.Series, b: pd.Series) -> dict:
    """比较两份逐根 K 线的标注，只看两边都有标签的 K 线。

    share: 标签相同的比例
    kappa: Cohen's kappa，扣掉「两边各自按自己的比例随便贴标签也会碰上」的那部分之后的一致程度。
           1 是完全一致，0 是和随便贴一样，负数是比随便贴还差
    table: 交叉表，行是 a 的标签，列是 b 的标签
    """
    both = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    share = float((both["a"] == both["b"]).mean())
    pa, pb = both["a"].value_counts(normalize=True), both["b"].value_counts(normalize=True)
    chance = float((pa * pb.reindex(pa.index, fill_value=0)).sum())
    kappa = (share - chance) / (1 - chance) if chance < 1 else float("nan")
    return {"share": share, "kappa": kappa, "table": pd.crosstab(both["a"], both["b"])}


def segments_to_labels(segments: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    """把手工标注的区间（start、end、label 三列，含两端）展开成逐根 K 线的标签，没标到的 K 线为缺失值。"""
    labels = pd.Series(np.nan, index=index, dtype=object)
    for s in segments.itertuples():
        labels[(index >= pd.Timestamp(s.start, tz=index.tz)) & (index <= pd.Timestamp(s.end, tz=index.tz))] = s.label
    return labels
