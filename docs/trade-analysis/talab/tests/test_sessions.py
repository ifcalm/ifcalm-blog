"""talab.sessions 的测试（第 20 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import sessions as S


def hours(n, start="2024-04-13 00:00", tz="UTC"):
    return pd.date_range(start, periods=n, freq="h", tz=tz)


def test_session_of_by_hand():
    index = hours(24)
    labels = S.session_of(index)
    assert labels.iloc[0] == "亚洲 00-07" and labels.iloc[6] == "亚洲 00-07"
    assert labels.iloc[7] == "欧洲 07-13" and labels.iloc[12] == "欧洲 07-13"
    assert labels.iloc[13] == "美国 13-21" and labels.iloc[20] == "美国 13-21"
    assert labels.iloc[21] == "美股收盘后 21-24" and labels.iloc[23] == "美股收盘后 21-24"
    assert labels.value_counts().sum() == 24                       # 一天正好被切成四段，不重不漏


def test_session_of_converts_time_zones():
    beijing = hours(3, start="2024-04-14 08:00", tz="Asia/Shanghai")   # 北京时间 8 点 = UTC 零点
    assert S.session_of(beijing).tolist() == ["亚洲 00-07"] * 3
    assert S.utc_hour(beijing).tolist() == [0, 1, 2]


def test_is_weekend_by_hand():
    days = pd.date_range("2024-04-12", periods=4, freq="D", tz="UTC")   # 周五、六、日、一
    assert S.is_weekend(days).tolist() == [False, True, True, False]


def test_profile_by_hand():
    index = hours(4)
    bars = pd.DataFrame({"open": [100.0, 100, 100, 100], "high": [110.0, 102, 104, 101],
                         "low": [100.0, 98, 100, 99], "close": [110.0, 98, 104, 100],
                         "quote_volume": [30.0, 10, 50, 10]}, index=index)
    groups = pd.Series(["A", "A", "B", "B"], index=index)
    out = S.profile(bars, groups)
    assert out.loc["A", "K线数"] == 2 and out.loc["B", "K线数"] == 2
    assert out.loc["A", "成交额占比"] == pytest.approx(0.4)          # 40 ÷ 100
    assert out.loc["A", "平均振幅"] == pytest.approx((0.10 + 0.04) / 2)
    assert out.loc["B", "平均涨跌"] == pytest.approx((0.04 + 0.0) / 2)


def test_third_fridays_and_quad_witching_by_hand():
    fridays = S.third_fridays("2024-01-01", "2024-12-31")
    assert len(fridays) == 12
    assert fridays[0] == pd.Timestamp("2024-01-19") and fridays[2] == pd.Timestamp("2024-03-15")
    assert (fridays.dayofweek == 4).all()
    quad = S.third_fridays("2024-01-01", "2024-12-31", months=(3, 6, 9, 12))
    assert quad.tolist() == [pd.Timestamp(d) for d in ["2024-03-15", "2024-06-21", "2024-09-20", "2024-12-20"]]


def test_period_ends_uses_trading_days():
    sessions = pd.DatetimeIndex(["2024-01-30", "2024-01-31", "2024-02-28", "2024-02-29", "2024-03-28"])
    # 2024-03-29 是耶稣受难日，不开市，所以一季度最后一个交易日是 3 月 28 日
    assert S.period_ends(sessions).tolist() == [pd.Timestamp("2024-01-31"), pd.Timestamp("2024-02-29"),
                                               pd.Timestamp("2024-03-28")]
    assert S.period_ends(sessions, freq="QE").tolist() == [pd.Timestamp("2024-03-28")]


def test_parse_fomc_page_by_hand():
    html = ('<a href="/newsevents/pressreleases/monetary20240320a.htm">HTML</a>'
            '<a href="/monetarypolicy/files/monetary20240320a1.pdf">PDF</a>'
            '<a href="/newsevents/pressreleases/monetary20240501a.htm">HTML</a>'
            '<a href="/newsevents/pressreleases/monetary20240320a.htm">重复的链接</a>')
    assert S.parse_fomc_page(html) == ["2024-03-20", "2024-05-01"]     # 去重、排序，PDF 不算


def test_parse_sec_submissions_by_hand():
    payload = {"filings": {"recent": {
        "filingDate": ["2024-05-02", "2024-04-10", "2024-02-01", "2024-01-15"],
        "form": ["8-K", "8-K", "8-K", "10-Q"],
        "items": ["2.02,9.01", "5.02", "2.02,9.01", ""]}}}
    assert S.parse_sec_submissions(payload, item="2.02") == ["2024-02-01", "2024-05-02"]   # 只留业绩公告
    assert len(S.parse_sec_submissions(payload)) == 3                              # 不挑条款就是全部 8-K
    assert S.parse_sec_submissions(payload, form="10-Q") == ["2024-01-15"]


def test_event_window_alignment_by_hand():
    days = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    values = pd.Series(np.arange(10, dtype=float), index=days)
    window = S.event_window(values, ["2024-01-05"], before=2, after=2)
    assert window.columns.tolist() == [-2, -1, 0, 1, 2]
    assert window.iloc[0].tolist() == [2, 3, 4, 5, 6]                  # 事件日的值是 4（1 月 5 日）
    assert S.event_window(values, ["2024-01-05"], 2, 2, offset=1).iloc[0].tolist() == [3, 4, 5, 6, 7]
    assert len(S.event_window(values, ["2024-01-01"], before=2, after=2)) == 0      # 窗口伸出数据范围，丢掉
    # 事件日不在索引里（当天休市）：取之后第一个有数据的位置
    trading = values.drop(days[4])
    assert S.event_window(trading, ["2024-01-05"], 1, 1).iloc[0].tolist() == [3, 5, 6]


def test_event_study_reports_the_baseline():
    days = pd.date_range("2024-01-01", periods=20, freq="D", tz="UTC")
    values = pd.Series([0.0] * 20, index=days)
    values.iloc[10] = 1.0
    out = S.event_study(values, [days[10]], before=1, after=1)
    assert out.loc[0, "平均"] == 1.0 and out.loc[-1, "平均"] == 0.0
    assert out.loc[0, "事件数"] == 1 and out.loc[0, "平常的平均"] == pytest.approx(0.05)
    assert out.loc[0, "平常的中位数"] == 0.0                        # 20 天里只有一天不是 0
