"""talab.patterns：K 线组合形态（第 16 篇）；图表形态（第 17 篇）；斐波那契回撤与扩展（第 18 篇）。

所有函数只看形状，不看位置：同样一根长下影线的 K 线，出现在下跌之后叫锤子线，出现在上涨之后叫上吊线，
形状函数不区分这两个名字。位置用 talab.structure 的市场状态、摆动点来判断（第 8、9、11 篇）。

约定和 talab.indicators 相同：输入是一个 OHLC 的 DataFrame，返回同索引的 Series；
数据不够的位置返回 False 或 0；第 k 个值只用到第 k 根及之前的 K 线。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

OHLC = ["open", "high", "low", "close"]


def parts(bars: pd.DataFrame) -> pd.DataFrame:
    """把每根 K 线拆成四个部分，单位都是价格。

    range_:  最高价 - 最低价，整根 K 线的高度
    body:    |收盘价 - 开盘价|，实体的高度
    upper:   最高价 - 实体上沿，上影线
    lower:   实体下沿 - 最低价，下影线
    top / bottom: 实体的上沿和下沿；up: 收盘价是否不低于开盘价
    最高价等于最低价（完全没有波动）时，range_ 记为 NaN，所有比例都无法计算，形态一律不成立。
    """
    o, h, l, c = (bars[name].astype(float) for name in OHLC)
    top, bottom = np.maximum(o, c), np.minimum(o, c)
    return pd.DataFrame({"range_": (h - l).where(h > l), "body": (c - o).abs(), "upper": h - top,
                         "lower": bottom - l, "top": top, "bottom": bottom, "up": c >= o})


# ---------------------------------------------------------------------------
# 一、单根 K 线的形状
# ---------------------------------------------------------------------------

def doji(bars: pd.DataFrame, body_max: float = 0.1) -> pd.Series:
    """十字星：实体不超过整根 K 线高度的 body_max（默认 10%）。开盘和收盘几乎相同。"""
    p = parts(bars)
    return (p["body"] <= body_max * p["range_"]).fillna(False)


def hammer(bars: pd.DataFrame, body_max: float = 0.34, shadow_min: float = 2.0, upper_max: float = 0.15) -> pd.Series:
    """锤子形：小实体在上方，长下影线，几乎没有上影线。

    实体不超过整根高度的 body_max，下影线至少是实体的 shadow_min 倍，上影线不超过整根高度的 upper_max。
    ⚠️ 这是形状，不是名字。下跌之后出现叫锤子线（看涨），上涨之后出现叫上吊线（看跌），形状完全一样。
    实体非常小时，它同时也是十字星（蜻蜓十字）。
    """
    p = parts(bars)
    return ((p["body"] <= body_max * p["range_"]) & (p["lower"] >= shadow_min * p["body"])
            & (p["upper"] <= upper_max * p["range_"])).fillna(False)


def inverted_hammer(bars: pd.DataFrame, body_max: float = 0.34, shadow_min: float = 2.0,
                    lower_max: float = 0.15) -> pd.Series:
    """倒锤形：小实体在下方，长上影线，几乎没有下影线。锤子形上下颠倒。

    ⚠️ 下跌之后出现叫倒锤线（看涨），上涨之后出现叫流星线（看跌）。
    """
    p = parts(bars)
    return ((p["body"] <= body_max * p["range_"]) & (p["upper"] >= shadow_min * p["body"])
            & (p["lower"] <= lower_max * p["range_"])).fillna(False)


# ---------------------------------------------------------------------------
# 二、两根、三根 K 线的组合
# ---------------------------------------------------------------------------

def engulfing(bars: pd.DataFrame, body_min: float = 0.1) -> pd.Series:
    """吞没：这一根的实体完全盖住前一根的实体，而且颜色相反。返回 1（看涨吞没）、-1（看跌吞没）、0。

    看涨吞没：前一根收阴，这一根收阳，这一根的实体下沿不高于前一根的实体下沿、上沿不低于前一根的实体上沿。
    两根的实体都要至少占各自整根高度的 body_min，避免把十字星也算成吞没。
    """
    p = parts(bars)
    before, before_up = p.drop(columns="up").shift(1), p["up"].shift(1, fill_value=False)
    real = (p["body"] >= body_min * p["range_"]) & (before["body"] >= body_min * before["range_"])
    covers = (p["bottom"] <= before["bottom"]) & (p["top"] >= before["top"])
    both = (real & covers).fillna(False)
    return ((both & p["up"] & ~before_up).astype(int) - (both & ~p["up"] & before_up).astype(int)).astype(int)


def harami(bars: pd.DataFrame, body_min: float = 0.6, body_max: float = 0.5) -> pd.Series:
    """孕线：前一根是长实体，这一根的实体完全包在里面，而且颜色相反。返回 1（看涨孕线）、-1（看跌孕线）、0。

    前一根的实体至少占它整根高度的 body_min，这一根的实体不超过前一根实体的 body_max。
    看涨孕线：前一根收阴，这一根收阳。
    """
    p = parts(bars)
    before, before_up = p.drop(columns="up").shift(1), p["up"].shift(1, fill_value=False)
    inside = ((before["body"] >= body_min * before["range_"]) & (p["body"] <= body_max * before["body"])
              & (p["bottom"] >= before["bottom"]) & (p["top"] <= before["top"])).fillna(False)
    return ((inside & p["up"] & ~before_up).astype(int) - (inside & ~p["up"] & before_up).astype(int)).astype(int)


def star(bars: pd.DataFrame, body_min: float = 0.5, small_max: float = 0.3, recover: float = 0.5) -> pd.Series:
    """三根 K 线的星形。返回 1（早晨之星，看涨）、-1（黄昏之星，看跌）、0。

    早晨之星：
    第 1 根：长阴线，实体至少占整根高度的 body_min
    第 2 根：小实体，不超过第 1 根实体的 small_max，而且整个实体低于第 1 根的实体下沿
    第 3 根：阳线，收盘价至少收复第 1 根实体的 recover（默认一半）
    黄昏之星上下颠倒。传统定义要求第 2 根跳空，这里改成「实体完全在外侧」，因为加密货币几乎没有跳空。
    """
    p = parts(bars)
    numbers = p.drop(columns="up")
    one, two = numbers.shift(2), numbers.shift(1)
    one_up = p["up"].shift(2, fill_value=False)
    shape = ((one["body"] >= body_min * one["range_"]) & (two["body"] <= small_max * one["body"])).fillna(False)
    morning = (shape & ~one_up & (two["top"] < one["bottom"]).fillna(False) & p["up"]
               & (bars["close"] >= one["bottom"] + recover * one["body"]).fillna(False))
    evening = (shape & one_up & (two["bottom"] > one["top"]).fillna(False) & ~p["up"]
               & (bars["close"] <= one["top"] - recover * one["body"]).fillna(False))
    return (morning.astype(int) - evening.astype(int)).astype(int)


# ---------------------------------------------------------------------------
# 三、扫描器
# ---------------------------------------------------------------------------

SHAPES = {"十字星": doji, "锤子形": hammer, "倒锤形": inverted_hammer}
COMBINATIONS = {"吞没": engulfing, "孕线": harami, "星形": star}


def scan(bars: pd.DataFrame) -> pd.DataFrame:
    """把六种形态一次扫出来。

    十字星、锤子形、倒锤形只有形状，出现记 1；吞没、孕线、星形分方向，看涨记 1、看跌记 -1。
    返回的每一列都和输入同索引，第 k 行只用到第 k 根及之前的 K 线。
    """
    columns = {name: func(bars).astype(int) for name, func in SHAPES.items()}
    columns |= {name: func(bars) for name, func in COMBINATIONS.items()}
    return pd.DataFrame(columns, index=bars.index)


# ---------------------------------------------------------------------------
# 四、图表形态（第 17 篇）
# ---------------------------------------------------------------------------
#
# 图表形态由摆动点（structure.zigzag 或 structure.fractals）连成。每个函数返回全部「候选形态」：
# 最后一个摆动点被确认的那一刻（confirmed_at），形状条件已经满足，就记一行，不管之后有没有突破。
# broken_at 是之后第一次收盘越过颈线（或趋势线）的时刻，等不到就是 NaT。
# 这样既能统计「成立的形态」，也能统计「当时看得到、后来没有成立的形态」。

def _runs(swings: pd.DataFrame, kinds: list[int]) -> list[pd.DataFrame]:
    """按时间排序，找出种类依次等于 kinds 的每一组相邻摆动点。"""
    ordered = swings.sort_values("time").reset_index(drop=True)
    k = ordered["kind"].to_numpy()
    n = len(kinds)
    return [ordered.iloc[i:i + n] for i in range(len(ordered) - n + 1) if list(k[i:i + n]) == kinds]


def _first_close_beyond(close: np.ndarray, start: int, stop: int, line, sign: int):
    """从第 start 根到第 stop 根（不含），第一次 sign × (收盘价 - line(根号)) < 0 的根号；没有返回 None。"""
    for j in range(start, min(stop, len(close))):
        if sign * (close[j] - line(j)) < 0:
            return j
    return None


def head_and_shoulders(close: pd.Series, swings: pd.DataFrame, kind: str = "top", shoulder_tol: float = 0.3,
                       neck_tol: float = 0.5, time_ratio: float = 3.0, wait: int | None = None) -> pd.DataFrame:
    """头肩顶（kind="top"）或头肩底（kind="bottom"）的全部候选。

    头肩顶是五个相邻的摆动点：左肩（高）、颈线点 1（低）、头（高）、颈线点 2（低）、右肩（高）。
    颈线：连接两个颈线点的直线，向右延长。高度：头的价格减去头所在位置的颈线值。
    形状条件：
    1. 头比两个肩都高
    2. 两个肩的高度差不超过高度的 shoulder_tol
    3. 两个颈线点的高度差不超过高度的 neck_tol（颈线不能太斜）
    4. 头到右肩的根数 ÷ 左肩到头的根数，在 1 / time_ratio 到 time_ratio 之间
    confirmed_at：右肩被确认的时刻。在这之前，右肩还不存在，形态也就还不存在。
    broken_at：从 confirmed_at 这一根起，wait 根以内（默认等于左肩到右肩的根数），第一次收盘价低于颈线。
    target：跌破时的颈线值减去高度，也就是经典的「量度目标」；没有跌破为 NaN。
    头肩底把高低全部颠倒：颈线在上方，向上突破，目标在上方。返回的价格都是原始价格，height 总是正数。
    """
    if kind not in ("top", "bottom"):
        raise ValueError('kind 只能是 "top" 或 "bottom"')
    sign = 1 if kind == "top" else -1
    c = close.to_numpy(float)
    pos = {t: i for i, t in enumerate(close.index)}
    rows = []
    for run in _runs(swings, [sign, -sign, sign, -sign, sign]):
        left, neck_1, head, neck_2, right = (sign * run["price"].to_numpy())
        t = [pos[x] for x in run["time"]]
        slope = (neck_2 - neck_1) / (t[3] - t[1])
        line = lambda j, a=neck_1, b=t[1], m=slope: sign * (a + m * (j - b))           # 原始价格上的颈线
        height = head - (neck_1 + slope * (t[2] - t[1]))
        if not (head > left and head > right and height > 0):
            continue
        if abs(left - right) > shoulder_tol * height or abs(neck_2 - neck_1) > neck_tol * height:
            continue
        if not 1 / time_ratio <= (t[4] - t[2]) / (t[2] - t[0]) <= time_ratio:
            continue
        seen = pos[run["confirmed_at"].iloc[4]]
        limit = t[4] + (wait if wait is not None else t[4] - t[0]) + 1
        j = _first_close_beyond(c, seen, limit, line, sign)
        rows.append((*run["time"], run["confirmed_at"].iloc[4], sign * left, sign * head, sign * right,
                     line(seen), height, close.index[j] if j is not None else pd.NaT,
                     line(j) if j is not None else np.nan, line(j) - sign * height if j is not None else np.nan))
    return pd.DataFrame(rows, columns=["left", "neck_1", "head", "neck_2", "right", "confirmed_at", "left_price",
                                       "head_price", "right_price", "neckline", "height", "broken_at",
                                       "neckline_at_break", "target"])


def double_tops(close: pd.Series, swings: pd.DataFrame, kind: str = "top", tol: float = 0.1,
                wait: int | None = None) -> pd.DataFrame:
    """双顶（kind="top"）或双底（kind="bottom"）的全部候选。

    双顶是三个相邻的摆动点：第一个顶（高）、中间的低点、第二个顶（高）。
    颈线：中间低点的价格（水平线）。高度：两个顶中较高的那个减去颈线。
    形状条件：两个顶的高度差不超过高度的 tol。
    confirmed_at：第二个顶被确认的时刻。
    broken_at：从 confirmed_at 起，wait 根以内（默认等于两个顶之间的根数），第一次收盘价低于颈线。
    target：颈线减去高度（双底是加上高度），不管有没有跌破都给出。双底上下颠倒，height 总是正数。
    """
    if kind not in ("top", "bottom"):
        raise ValueError('kind 只能是 "top" 或 "bottom"')
    sign = 1 if kind == "top" else -1
    c = close.to_numpy(float)
    pos = {t: i for i, t in enumerate(close.index)}
    rows = []
    for run in _runs(swings, [sign, -sign, sign]):
        first, middle, second = sign * run["price"].to_numpy()
        t = [pos[x] for x in run["time"]]
        height = max(first, second) - middle
        if height <= 0 or abs(first - second) > tol * height:
            continue
        seen = pos[run["confirmed_at"].iloc[2]]
        limit = t[2] + (wait if wait is not None else t[2] - t[0]) + 1
        j = _first_close_beyond(c, seen, limit, lambda _, m=sign * middle: m, sign)
        rows.append((*run["time"], run["confirmed_at"].iloc[2], sign * first, sign * second, sign * middle,
                     height, close.index[j] if j is not None else pd.NaT, sign * (middle - height)))
    return pd.DataFrame(rows, columns=["first", "middle", "second", "confirmed_at", "first_price", "second_price",
                                       "neckline", "height", "broken_at", "target"])


def converging(close: pd.Series, swings: pd.DataFrame, flat: float = 0.2, wait: int | None = None) -> pd.DataFrame:
    """用最近两个摆动高点连上轨、两个摆动低点连下轨，按两条线的方向给形态命名。

    四个相邻的摆动点（两高两低，高低交替）决定两条线。设第一个点的位置两线之间的宽度为 W，
    四个点从头到尾的根数为 T，每条线在 T 根里的变化 ÷ W 叫这条线的「斜度」，绝对值不超过 flat 算水平。
    上轨水平、下轨向上：上升三角形；上轨向下、下轨水平：下降三角形；上轨向下、下轨向上：对称三角形
    两条线都向上且下轨更陡（在收窄）：上升楔形；都向下且上轨更陡：下降楔形
    两条线都水平：矩形；上轨向上、下轨向下：扩散；其余同方向而不收窄的：通道
    confirmed_at：第四个摆动点被确认的时刻。
    broken_at / direction：从 confirmed_at 起，wait 根以内（默认 T），第一次收盘价在上轨上方（1）或下轨下方（-1）。
    """
    c = close.to_numpy(float)
    pos = {t: i for i, t in enumerate(close.index)}
    rows = []
    ordered = swings.sort_values("time").reset_index(drop=True)
    for i in range(len(ordered) - 3):
        run = ordered.iloc[i:i + 4]
        kinds = run["kind"].to_numpy()
        if not all(kinds[1:] == -kinds[:-1]):
            continue
        t = np.array([pos[x] for x in run["time"]])
        price = run["price"].to_numpy(float)
        highs, lows = np.flatnonzero(kinds == 1), np.flatnonzero(kinds == -1)
        slope_up = (price[highs[1]] - price[highs[0]]) / (t[highs[1]] - t[highs[0]])
        slope_down = (price[lows[1]] - price[lows[0]]) / (t[lows[1]] - t[lows[0]])
        upper = lambda j, a=price[highs[0]], b=t[highs[0]], m=slope_up: a + m * (j - b)
        lower = lambda j, a=price[lows[0]], b=t[lows[0]], m=slope_down: a + m * (j - b)
        width, span = upper(t[0]) - lower(t[0]), t[3] - t[0]
        if width <= 0:
            continue
        du, dl = slope_up * span / width, slope_down * span / width
        up_flat, down_flat = abs(du) <= flat, abs(dl) <= flat
        if up_flat and down_flat:
            name = "矩形"
        elif up_flat and dl > 0:
            name = "上升三角形"
        elif down_flat and du < 0:
            name = "下降三角形"
        elif du < 0 < dl:
            name = "对称三角形"
        elif du > 0 and dl > du:
            name = "上升楔形"
        elif dl < 0 and du < dl:
            name = "下降楔形"
        elif du > 0 > dl:
            name = "扩散"
        else:
            name = "通道"
        seen = pos[run["confirmed_at"].iloc[3]]
        stop = t[3] + (wait if wait is not None else span) + 1
        j, direction = None, 0
        for k in range(seen, min(stop, len(c))):
            if c[k] > upper(k) or c[k] < lower(k):
                j, direction = k, 1 if c[k] > upper(k) else -1
                break
        rows.append((run["time"].iloc[0], run["time"].iloc[3], run["confirmed_at"].iloc[3], name, du, dl,
                     upper(seen), lower(seen), close.index[j] if j is not None else pd.NaT, direction))
    return pd.DataFrame(rows, columns=["start", "end", "confirmed_at", "name", "upper_slope", "lower_slope",
                                       "upper", "lower", "broken_at", "direction"])


# ---------------------------------------------------------------------------
# 五、斐波那契回撤与扩展（第 18 篇）
# ---------------------------------------------------------------------------

FIB_RETRACEMENTS = (0.236, 0.382, 0.5, 0.618, 0.786)
FIB_EXTENSIONS = (1.272, 1.618, 2.618)


def retracement_levels(start: float, end: float, ratios=FIB_RETRACEMENTS) -> pd.Series:
    """一段行情从 start 走到 end，回撤 ratio 的价位 = end - ratio × (end - start)。

    上涨段（end > start）的回撤位在 end 下方，下跌段在 end 上方，公式相同。返回以 ratio 为索引的价位。
    """
    ratios = np.asarray(ratios, dtype=float)
    return pd.Series(end - ratios * (end - start), index=ratios, name="level")


def extension_levels(a: float, b: float, c: float, ratios=FIB_EXTENSIONS) -> pd.Series:
    """A 走到 B、回撤到 C 之后，下一段的扩展目标 = C + ratio × (B - A)。返回以 ratio 为索引的价位。"""
    ratios = np.asarray(ratios, dtype=float)
    return pd.Series(c + ratios * (b - a), index=ratios, name="level")


def swing_ratios(swings: pd.DataFrame) -> pd.DataFrame:
    """每个摆动点结束的那一段，相对前面几段的比例。

    retracement：这一段的长度 ÷ 前一段的长度（前一段被回撤了多少，1 表示回撤到起点）
    extension：这一段的长度 ÷ 前面隔一段的那一段的长度（A→B、B→C、C→D 里的 CD ÷ AB）
    比例都用摆动点的价格算，第一、二个摆动点没有前一段，为 NaN。
    """
    ordered = swings.sort_values("time").reset_index(drop=True)
    p = ordered["price"].to_numpy(dtype=float)
    leg = np.abs(np.diff(p, prepend=np.nan))                 # 第 n 个摆动点结束的那一段的长度
    retracement = leg / np.roll(leg, 1)
    extension = leg / np.roll(leg, 2)
    retracement[:2], extension[:3] = np.nan, np.nan
    return pd.DataFrame({"time": ordered["time"], "kind": ordered["kind"], "retracement": retracement,
                         "extension": extension})


def retracement_tests(high: pd.Series, low: pd.Series, close: pd.Series, swings: pd.DataFrame, atr: pd.Series,
                      ratios, distance: float = 1.0, horizon: int = 20) -> pd.DataFrame:
    """实时地检验回撤位：每一段 A→B 被确认之后，价格第一次回撤到某个比例的价位时，看它是「停住」还是「穿过」。

    对每两个相邻的摆动点 A、B（B 在 confirmed_at 被确认）：
    1. 各个比例的价位 = B - ratio × (B - A)
    2. 从 B 到 confirmed_at 之间已经碰过的价位不算：那时还不知道这一段存在
    3. 从 confirmed_at 的下一根开始往后看，收盘价越过 B（新高，上涨段）或越过 A（整段被吃掉）就停止
    4. 某个价位第一次被碰到（上涨段看最低价 ≤ 价位）的那一根，记为 touched_at
    5. 从这个价位出发，上下各放 distance 个 ATR（用 confirmed_at 那一根的 ATR）。
       之后 horizon 根里，先朝原来方向走出 distance 个 ATR 记 1（停住了），先反向走出记 0（穿过了），都没有记 NaN。
       碰到价位的那一根自己就走过了反向的线，记 0
    返回每一次「碰到」一行：start、end、confirmed_at、ratio、level、touched_at、held。
    """
    h, l, c, a = (s.to_numpy(dtype=float) for s in (high, low, close, atr))
    pos = {t: i for i, t in enumerate(close.index)}
    ordered = swings.sort_values("time").reset_index(drop=True)
    ratios = np.asarray(ratios, dtype=float)
    rows = []
    for n in range(1, len(ordered)):
        start, end = ordered["price"].iloc[n - 1], ordered["price"].iloc[n]
        sign = 1 if end > start else -1                        # 1：上涨段，回撤向下
        seen = pos[ordered["confirmed_at"].iloc[n]]
        if np.isnan(a[seen]):
            continue
        levels = end - ratios * (end - start)
        width = distance * a[seen]
        k0 = pos[ordered["time"].iloc[n]]
        reached = (l[k0:seen + 1].min() if sign == 1 else h[k0:seen + 1].max())
        done = sign * (reached - levels) <= 0
        for j in range(seen + 1, len(c)):
            if sign * (c[j] - end) > 0 or sign * (c[j] - start) < 0 or done.all():
                break
            extreme = l[j] if sign == 1 else h[j]
            hit = ~done & (sign * (extreme - levels) <= 0)
            for g in np.flatnonzero(hit):
                level, held = levels[g], np.nan
                if sign * (extreme - (level - sign * width)) <= 0:
                    held = 0.0
                else:
                    for m in range(j + 1, min(j + 1 + horizon, len(c))):
                        if sign * ((l[m] if sign == 1 else h[m]) - (level - sign * width)) <= 0:
                            held = 0.0
                            break
                        if sign * ((h[m] if sign == 1 else l[m]) - (level + sign * width)) >= 0:
                            held = 1.0
                            break
                rows.append((ordered["time"].iloc[n - 1], ordered["time"].iloc[n], ordered["confirmed_at"].iloc[n],
                             ratios[g], level, close.index[j], held))
            done |= hit
    return pd.DataFrame(rows, columns=["start", "end", "confirmed_at", "ratio", "level", "touched_at", "held"])
