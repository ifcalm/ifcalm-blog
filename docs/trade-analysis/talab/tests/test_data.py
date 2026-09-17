"""talab.data 的测试。全部使用手工构造的小数据，不需要联网，也不需要下载任何文件。"""
import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from talab import data as D


def make_bars(n=5, start="2024-01-01", freq="1min"):
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC")
    return pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 10.0}, index=idx)


# ---------- 加载 ----------

def write_kline_zip(path, rows):
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, header=False, index=False)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(path.stem + ".csv", buf.getvalue())


def kline_row(open_time):
    return [open_time, "1", "2", "0.5", "1.5", "10", open_time + 59_999, "15", 3, "4", "6", "0"]


def test_load_handles_millisecond_and_microsecond_timestamps(tmp_path):
    ms = 1735689540000          # 2024-12-31 23:59:00 UTC，毫秒
    us = 1735689600000000       # 2025-01-01 00:00:00 UTC，微秒
    write_kline_zip(tmp_path / "a-2024-12.zip", [kline_row(ms)])
    write_kline_zip(tmp_path / "a-2025-01.zip", [kline_row(us)])
    df = D.load_binance_klines(tmp_path.glob("*.zip"))
    assert list(df.index) == [pd.Timestamp("2024-12-31 23:59", tz="UTC"), pd.Timestamp("2025-01-01 00:00", tz="UTC")]


def test_load_raises_when_no_files(tmp_path):
    with pytest.raises(ValueError):
        D.load_binance_klines(tmp_path.glob("*.zip"))


# ---------- 价格调整 ----------

def daily(prices, start="2020-08-26"):
    idx = pd.bdate_range(start, periods=len(prices))
    p = pd.Series(prices, index=idx, dtype=float)
    return pd.DataFrame({"open": p, "high": p, "low": p, "close": p, "volume": 1000.0})


def test_split_roundtrip_restores_original():
    raw = daily([500.0, 510.0, 130.0, 131.0])                 # 第三天起 1 拆 4
    splits = [(raw.index[2].strftime("%Y-%m-%d"), 4)]
    adj = D.adjust_splits(raw, splits)
    assert adj["close"].tolist() == [125.0, 127.5, 130.0, 131.0]
    assert adj["volume"].tolist() == [4000.0, 4000.0, 1000.0, 1000.0]
    pd.testing.assert_frame_equal(D.unadjust_splits(adj, splits), raw)


def test_dividend_factor_matches_hand_calculation():
    # 第 3 篇练习 2：3 月 9 日收盘 100，3 月 10 日除息，每股分红 2
    idx = pd.to_datetime(["2026-03-09", "2026-03-10"])
    close = pd.Series([100.0, 99.0], index=idx)
    f = D.dividend_factor(close, pd.Series([2.0], index=[pd.Timestamp("2026-03-10")]))
    assert f.tolist() == pytest.approx([0.98, 1.0])
    # 调整后的涨跌幅 = 99 / (100 × 0.98) − 1
    assert 99.0 / (100.0 * f.iloc[0]) - 1 == pytest.approx(0.010204, abs=1e-6)


def test_dividend_outside_data_range_is_ignored():
    close = daily([100.0, 101.0])["close"]
    later = pd.Series([1.0], index=[close.index[-1] + pd.Timedelta(days=30)])
    assert (D.dividend_factor(close, later) == 1.0).all()


# ---------- 体检 ----------

def test_health_check_on_clean_data_finds_nothing():
    report = D.health_check(make_bars(10), freq="1min", wick_window=4)
    assert D.summarize(report).sum() == 0


def test_health_check_finds_planted_problems():
    df = make_bars(10)
    df.iloc[2, df.columns.get_loc("high")] = 99.5                        # 最高价低于开盘价
    df.iloc[3, df.columns.get_loc("volume")] = 0.0                        # 零成交量
    df.iloc[4, df.columns.get_loc("close")] = np.nan                      # 空值
    df = df.drop(df.index[6])                                             # 缺一根
    shifted = df.index.tolist()
    shifted[-1] = shifted[-1] + pd.Timedelta(seconds=20)                  # 最后一根时间戳偏移
    df.index = pd.DatetimeIndex(shifted)
    df = pd.concat([df, df.iloc[[0]]]).sort_index()                       # 重复一根

    s = D.summarize(D.health_check(df, freq="1min", wick_window=4))
    assert s["高低价自相矛盾"] == 1
    assert s["成交量为零"] == 1
    assert s["有空值的行"] == 1
    assert s["缺失的 K 线"] == 1
    assert s["时间戳没有对齐"] == 1
    assert s["重复时间戳"] == 1


def test_missing_runs_groups_consecutive_gaps():
    idx = pd.DatetimeIndex(["2024-01-01 00:03", "2024-01-01 00:04", "2024-01-01 00:05", "2024-01-01 00:09"], tz="UTC")
    runs = D.missing_runs(idx, "1min")
    assert runs["缺失根数"].tolist() == [3, 1]


def test_fingerprint():
    fp = D.fingerprint(make_bars(3))
    assert fp["行数"] == 3 and fp["收盘价之和"] == 301.5
