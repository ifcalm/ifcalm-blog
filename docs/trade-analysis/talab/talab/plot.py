"""talab.plot：K 线绘图。第 4 篇。"""
from __future__ import annotations

import math

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter, LogLocator

# 涨跌颜色。国际惯例：涨绿跌红；中国大陆惯例：涨红跌绿
STYLES = {
    "international": {"up": "#26a69a", "down": "#ef5350"},
    "china": {"up": "#ef5350", "down": "#26a69a"},
}


# ---------------------------------------------------------------------------
# 一、价格 → 像素：一切 K 线图的核心
# ---------------------------------------------------------------------------

def price_to_y(price: float, lo: float, hi: float, top: float, height: float, log: bool = False) -> float:
    """把价格换算成图上的纵坐标（像素）。屏幕坐标向下增大，所以最高价在最上面。

    算术坐标：按价格的「差」等比例分配高度
    对数坐标：按价格的「比」等比例分配高度
    """
    if log:
        frac = (math.log(hi) - math.log(price)) / (math.log(hi) - math.log(lo))
    else:
        frac = (hi - price) / (hi - lo)
    return top + frac * height


def candles_svg(df: pd.DataFrame, width: int = 800, height: int = 400, log: bool = False,
                style: str = "international", pad: int = 20) -> str:
    """不用任何绘图库，直接生成一张 K 线图的 SVG 文本。"""
    colors = STYLES[style]
    lo, hi = df["low"].min(), df["high"].max()
    n = len(df)
    slot = (width - 2 * pad) / n                 # 每根 K 线占的水平宽度
    body_w = slot * 0.7                          # 实体宽度，留 30% 做间隔
    y = lambda p: price_to_y(p, lo, hi, pad, height - 2 * pad, log)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
             f'<rect width="{width}" height="{height}" fill="white"/>']
    for i, (o, h, l, c) in enumerate(df[["open", "high", "low", "close"]].itertuples(index=False)):
        color = colors["up"] if c >= o else colors["down"]
        x_mid = pad + slot * (i + 0.5)
        # 影线：从最高价画到最低价的一条竖线
        parts.append(f'<line x1="{x_mid:.2f}" y1="{y(h):.2f}" x2="{x_mid:.2f}" y2="{y(l):.2f}" stroke="{color}" stroke-width="1"/>')
        # 实体：开盘价和收盘价之间的矩形；开盘等于收盘时至少画 1 像素高
        top, bottom = y(max(o, c)), y(min(o, c))
        parts.append(f'<rect x="{x_mid - body_w / 2:.2f}" y="{top:.2f}" width="{body_w:.2f}" '
                     f'height="{max(bottom - top, 1):.2f}" fill="{color}"/>')
    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 二、实际使用的绘图函数
# ---------------------------------------------------------------------------

def plot_candles(df: pd.DataFrame, *, title: str | None = None, volume: bool = True, log: bool = False,
                 time_axis: str = "bars", style: str = "international",
                 overlays: dict[str, pd.Series] | None = None,
                 hlines: dict[str, float] | None = None,
                 marks: list[tuple] | None = None,
                 figsize=(10, 6), dpi: int = 150):
    """画 K 线图，返回 (fig, 价格子图, 成交量子图或 None)。

    time_axis: "bars" 每根 K 线等距排列（休市时段不留空白）；"real" 按真实时间排列
    overlays:  叠加在价格上的曲线，比如均线 {"MA20": series}
    hlines:    水平线 {"说明": 价格}
    marks:     标注点 [(时间, 价格, "文字"), ...]
    """
    colors = STYLES[style]
    if volume:
        fig, (ax, av) = plt.subplots(2, 1, figsize=figsize, dpi=dpi, sharex=True,
                                     gridspec_kw={"height_ratios": [3, 1]})
    else:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        av = None

    if time_axis == "bars":
        xs = list(range(len(df)))
        width = 0.7
    elif time_axis == "real":
        xs = list(df.index)
        step = pd.Series(df.index).diff().median()      # 相邻两根 K 线通常相隔多久
        width = step * 0.7
    else:
        raise ValueError('time_axis 只能是 "bars" 或 "real"')
    x_of = dict(zip(df.index, xs))

    for x, (o, h, l, c, v) in zip(xs, df[["open", "high", "low", "close", "volume"]].itertuples(index=False)):
        color = colors["up"] if c >= o else colors["down"]
        ax.vlines(x, l, h, color=color, linewidth=0.8)
        ax.add_patch(Rectangle((x - width / 2, min(o, c)),
                               width, abs(c - o), facecolor=color, edgecolor=color, linewidth=0.5))
        if av is not None:
            av.bar(x, v, width=width, color=color)

    for name, series in (overlays or {}).items():
        s = series.reindex(df.index)
        ax.plot(xs, s.values, linewidth=1.2, label=name)
    for name, price in (hlines or {}).items():
        ax.axhline(price, linestyle=":", linewidth=1.2, color="#1f77b4")
        ax.annotate(name, (xs[0], price), textcoords="offset points", xytext=(2, 3), fontsize=9, color="#1f77b4")
    for t, price, text in (marks or []):
        # 文字放在点的下方，箭头向上指着这个价格
        ax.annotate(text, (x_of[pd.Timestamp(t, tz=df.index.tz) if df.index.tz else pd.Timestamp(t)], price),
                    textcoords="offset points", xytext=(0, -32), ha="center", fontsize=9,
                    arrowprops={"arrowstyle": "->", "color": "#555"})

    ax.autoscale_view()
    if log:
        ax.set_yscale("log")
        lo, hi = ax.get_ylim()
        # 价格跨度超过 20 倍时，刻度只放在 1、2、5 的倍数上；跨度小时放在 1～9 的倍数上，否则刻度太少
        subs = (1.0, 2.0, 5.0) if hi / lo > 20 else tuple(range(1, 10))
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=subs))
        ax.yaxis.set_minor_locator(LogLocator(base=10, subs=()))
    # 刻度显示成带千位分隔的普通数字，不用 10 的几次方
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}" if v >= 100 else f"{v:g}"))
    if time_axis == "bars":
        ticks = _date_ticks(df.index)
        (av or ax).set_xticks(ticks)
        (av or ax).set_xticklabels([df.index[i].strftime("%Y-%m-%d") for i in ticks], fontsize=8)
        ax.set_xlim(-1, len(df))
    else:
        locator = mdates.AutoDateLocator(maxticks=8)
        (av or ax).xaxis.set_major_locator(locator)
        (av or ax).xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    if overlays:
        ax.legend(fontsize=9, loc="upper left")
    if title:
        ax.set_title(title, fontsize=12)
    ax.set_ylabel("价格")
    if av is not None:
        av.set_ylabel("成交量")
        av.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for a in (ax, av):
        if a is not None:
            a.grid(alpha=0.25)
    fig.tight_layout()
    return fig, ax, av


def _date_ticks(index: pd.DatetimeIndex, n: int = 6) -> list[int]:
    """在等距排列的 K 线里，挑出大约 n 个位置放日期标签。"""
    step = max(1, len(index) // n)
    return list(range(0, len(index), step))


def use_chinese_font(path: str = "/System/Library/Fonts/Hiragino Sans GB.ttc") -> None:
    """让 matplotlib 能显示中文。默认路径是 macOS 自带字体；Windows 可以用 C:/Windows/Fonts/msyh.ttc。"""
    from matplotlib import font_manager
    font_manager.fontManager.addfont(path)
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=path).get_name()
    plt.rcParams["axes.unicode_minus"] = False
