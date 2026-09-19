"""talab.sessions：交易时段与事件日历。第 20 篇。

两件事：

1. **时段**：一天里的每个小时不一样，一周里的每一天也不一样。加密 24 小时开着，但成交量随
   亚洲、欧洲、美国三个时段起落；周末是一周里最薄的时候。
2. **事件**：有些日子是提前知道的——期权到期、月末、FOMC 公布利率、公司发财报。事件日历
   是一张「哪天会有事」的表，事件研究是「事件前后发生了什么」的统计。

时间一律按 UTC。索引带时区的用它自己的时区换算成 UTC，不带时区的当成 UTC。
"""
from __future__ import annotations

import json
import re
import urllib.request

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 一、时段
# ---------------------------------------------------------------------------

# 三个时段其实是重叠的（伦敦和纽约有三小时重叠），这里按「哪个市场在主导」把一天切成不重叠的四段。
SESSIONS = {"亚洲 00-07": (0, 7), "欧洲 07-13": (7, 13), "美国 13-21": (13, 21), "美股收盘后 21-24": (21, 24)}


def utc_hour(index: pd.DatetimeIndex) -> np.ndarray:
    """每个时间点的 UTC 小时。"""
    index = pd.DatetimeIndex(index)
    return (index.tz_convert("UTC") if index.tz is not None else index).hour.to_numpy()


def session_of(index: pd.DatetimeIndex, sessions: dict = SESSIONS) -> pd.Series:
    """每根 K 线属于哪个时段（按 UTC 小时，左闭右开）。"""
    hour = utc_hour(index)
    out = pd.Series(pd.NA, index=index, dtype="object")
    for name, (start, end) in sessions.items():
        out[(hour >= start) & (hour < end)] = name
    return out


def is_weekend(index: pd.DatetimeIndex) -> pd.Series:
    """是不是周六或周日（按 UTC）。美股周末不开，加密开着但最薄。"""
    index = pd.DatetimeIndex(index)
    weekday = (index.tz_convert("UTC") if index.tz is not None else index).dayofweek
    return pd.Series(weekday >= 5, index=index)


def profile(bars: pd.DataFrame, groups: pd.Series, turnover: pd.Series | None = None) -> pd.DataFrame:
    """按分组统计一组 K 线：占了多少根、成交额占比、平均振幅、平均涨跌和它的标准差。

    振幅 = (最高价 - 最低价) ÷ 开盘价，涨跌 = 收盘价 ÷ 开盘价 - 1，都是这根 K 线自己的口径，
    不跨根，所以可以直接按任意分组求平均。
    """
    money = (turnover if turnover is not None else bars["quote_volume"]).astype(float)
    change = bars["close"] / bars["open"] - 1
    table = pd.DataFrame({"组": groups, "成交额": money, "振幅": (bars["high"] - bars["low"]) / bars["open"],
                          "涨跌": change})
    out = table.groupby("组", observed=True).agg(K线数=("成交额", "size"), 成交额占比=("成交额", "sum"),
                                                 平均振幅=("振幅", "mean"), 平均涨跌=("涨跌", "mean"),
                                                 涨跌标准差=("涨跌", "std"))
    out["成交额占比"] /= money.sum()
    return out


# ---------------------------------------------------------------------------
# 二、事件日历
# ---------------------------------------------------------------------------

def third_fridays(start, end, months: tuple = tuple(range(1, 13))) -> pd.DatetimeIndex:
    """每月第三个周五：美股月度期权到期日。months 只留 3、6、9、12 就是「四巫日」。

    ⚠️ 这是日历上的第三个周五，遇到假日（例如 2020-04-10 耶稣受难日）实际到期日会提前一天，
    用 period_ends 那种「交易日历」口径的函数去对齐。
    """
    days = pd.date_range(start, end, freq="D")
    fridays = days[(days.dayofweek == 4) & days.month.isin(months)]
    order = fridays.to_series().groupby([fridays.year, fridays.month]).cumcount()
    return pd.DatetimeIndex(fridays[order == 2])


def period_ends(sessions: pd.DatetimeIndex, freq: str = "ME") -> pd.DatetimeIndex:
    """每个月（freq="ME"）或每个季度（freq="QE"）的最后一个交易日。"""
    sessions = pd.DatetimeIndex(sessions)
    return pd.DatetimeIndex(pd.Series(sessions, index=sessions).resample(freq).last().dropna())


def parse_fomc_page(html: str) -> list[str]:
    """从美联储的会议日历页面里取出所有货币政策声明的日期（YYYY-MM-DD）。

    声明的链接形如 /newsevents/pressreleases/monetary20240320a.htm，日期就是会议最后一天，
    也就是利率公布的那一天。
    """
    found = re.findall(r"/newsevents/pressreleases/monetary(\d{8})a\.htm", html)
    return sorted({f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in found})


def fomc_dates(start_year: int = 2016, end_year: int = 2026) -> pd.DatetimeIndex:
    """FOMC 公布利率的日期。近几年在 fomccalendars.htm，更早的在每年一张的历史页面上。"""
    pages = ["https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"]
    pages += [f"https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm"
              for year in range(start_year, min(end_year, 2021))]
    dates = {d for page in pages for d in parse_fomc_page(_get(page))}
    picked = pd.DatetimeIndex(sorted(dates))
    return picked[(picked.year >= start_year) & (picked.year <= end_year)]


def parse_sec_submissions(payload: dict, form: str = "8-K", item: str | None = None) -> list[str]:
    """从 SEC EDGAR 的备案清单里取出日期。item="2.02" 是「业绩公告」，也就是财报发布日。"""
    filings = payload["filings"]["recent"] if "filings" in payload else payload
    rows = zip(filings["filingDate"], filings["form"], filings.get("items", [""] * len(filings["form"])))
    return sorted({date for date, kind, items in rows if kind == form and (item is None or item in items)})


def sec_filing_dates(cik: int, form: str = "8-K", item: str | None = "2.02") -> pd.DatetimeIndex:
    """一家公司向 SEC 提交某类文件的日期。默认取 8-K 的 2.02 条款：公布季度业绩。

    ⚠️ 备案日是公司发布的那一天。苹果在美股收盘后发财报，所以价格反应在**第二天**。
    """
    base = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    payload = json.loads(_get(base))
    dates = set(parse_sec_submissions(payload, form, item))
    for older in payload["filings"].get("files", []):
        dates |= set(parse_sec_submissions(json.loads(_get(f"https://data.sec.gov/submissions/{older['name']}")),
                                           form, item))
    return pd.DatetimeIndex(sorted(dates))


def _get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "talab course (contact: reader@example.com)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# 三、事件研究
# ---------------------------------------------------------------------------

def event_window(values: pd.Series, events, before: int = 5, after: int = 5, offset: int = 0) -> pd.DataFrame:
    """把每个事件对齐到同一张表：每行一个事件，列是 -before 到 +after 根 K 线。

    事件日不在索引里（休市、或者 values 是别的市场）时，取它之后第一个有数据的位置。
    offset 用来处理「盘后公布」：offset=1 表示把第 0 根算作事件日的下一根。
    窗口伸出数据范围的事件直接丢掉。
    """
    index = values.index
    rows, kept = [], []
    for event in pd.DatetimeIndex(events):
        when = event.tz_localize(index.tz) if index.tz is not None and event.tz is None else event
        position = index.searchsorted(when) + offset
        if position - before < 0 or position + after >= len(index):
            continue
        rows.append(values.to_numpy()[position - before: position + after + 1])
        kept.append(event)
    return pd.DataFrame(rows, index=pd.DatetimeIndex(kept), columns=range(-before, after + 1))


def event_study(values: pd.Series, events, before: int = 5, after: int = 5, offset: int = 0) -> pd.DataFrame:
    """事件窗口的平均值、中位数和事件数；最后两列是「所有日子」的平均和中位数，用来当基准。"""
    window = event_window(values, events, before, after, offset)
    return pd.DataFrame({"平均": window.mean(), "中位数": window.median(), "事件数": window.count(),
                         "平常的平均": values.mean(), "平常的中位数": values.median()})
