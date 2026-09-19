"""talab.screen 的测试（第 19 篇）。"""
import json

import numpy as np
import pandas as pd
import pytest

from talab import data as D, screen as S

DAYS = pd.date_range("2024-01-01", periods=8, freq="D", tz="UTC")


def frame(close, volume=None, quote=None):
    """一个标的的 OHLCV 表，长度不足 8 天的用 NaN 补齐（表示还没上市或者已经下架）。"""
    close = list(close) + [np.nan] * (len(DAYS) - len(close))
    df = pd.DataFrame({"close": close}, index=DAYS, dtype=float)
    if volume is not None:
        df["volume"] = list(volume) + [np.nan] * (len(DAYS) - len(volume))
    if quote is not None:
        df["quote_volume"] = list(quote) + [np.nan] * (len(DAYS) - len(quote))
    return df


def test_panel_and_turnover_by_hand():
    frames = {"BBB": frame([10, 11], volume=[3, 3]), "AAA": frame([100, 90], volume=[1, 2], quote=[500, 400])}
    close = S.panel(frames, "close")
    assert list(close.columns) == ["AAA", "BBB"]                      # 列按标的名排序
    assert close["AAA"].iloc[1] == 90 and np.isnan(close["BBB"].iloc[2])
    assert S.turnover(frames["AAA"]).iloc[0] == 500                   # 有成交额就直接用
    assert S.turnover(frames["BBB"]).tolist()[:2] == [30, 33]         # 没有就用收盘价 × 成交量


def test_rolling_turnover_is_the_median():
    dv = pd.DataFrame({"AAA": [10.0, 200.0, 20.0, 30.0]}, index=DAYS[:4])
    out = S.rolling_turnover(dv, n=3)
    assert np.isnan(out["AAA"].iloc[1])                               # 不满 3 天算不出
    assert out["AAA"].iloc[2] == 20 and out["AAA"].iloc[3] == 30      # 中位数不被 200 那天带偏
    assert dv["AAA"].rolling(3).mean().iloc[2] > 76                   # 平均值会被带到 76 以上


def test_cross_rank_by_hand():
    values = pd.DataFrame({"A": [0.5, 0.1], "B": [0.2, np.nan], "C": [0.9, 0.3]}, index=DAYS[:2])
    pct = S.cross_rank(values)
    assert pct.loc[DAYS[0]].tolist() == [2 / 3, 1 / 3, 1.0]           # C 最强
    assert np.isnan(pct.loc[DAYS[1], "B"]) and pct.loc[DAYS[1], "C"] == 1.0
    assert S.cross_rank(values, pct=False).loc[DAYS[0]].tolist() == [2, 3, 1]
    assert S.cross_rank(values, ascending=True, pct=False).loc[DAYS[0]].tolist() == [2, 1, 3]
    mask = pd.DataFrame({"A": [True, True], "B": [True, True], "C": [False, True]}, index=DAYS[:2])
    masked = S.cross_rank(values, mask=mask)                           # C 没进名单，不参加排名
    assert masked.loc[DAYS[0]].tolist()[:2] == [1.0, 0.5] and np.isnan(masked.loc[DAYS[0], "C"])


def test_buckets_and_bucket_returns_by_hand():
    rank = pd.DataFrame({"A": [0.25], "B": [0.5], "C": [0.75], "D": [1.0]}, index=DAYS[:1])
    bucket = S.buckets(rank, k=2)
    assert bucket.iloc[0].tolist() == [1, 1, 2, 2]
    forward = pd.DataFrame({"A": [0.1], "B": [0.3], "C": [-0.2], "D": [0.4]}, index=DAYS[:1])
    out = S.bucket_returns(bucket, forward, k=2)
    assert list(out.columns) == [1, 2]
    assert out.iloc[0].tolist() == [pytest.approx(0.2), pytest.approx(0.1)]


def test_relative_strength_and_momentum_by_hand():
    close = pd.DataFrame({"A": [10.0, 12.0, 12.0], "B": [np.nan, 50.0, 60.0]}, index=DAYS[:3])
    benchmark = pd.Series([100.0, 110.0, 121.0], index=DAYS[:3])
    rs = S.relative_strength(close, benchmark)
    # A 第二天涨 20%、基准涨 10%：相对强度线从 100 升到 (12/110)/(10/100)×100 = 109.09
    assert rs["A"].tolist() == [100, pytest.approx(12 / 110 / 0.1 * 100), pytest.approx(12 / 121 / 0.1 * 100)]
    assert rs["B"].iloc[1] == 100 and rs["B"].iloc[2] == pytest.approx(60 / 121 * 110 / 50 * 100)
    # A 两天涨了 20%，基准涨了 21%，相对强度线走低：涨了也可能跑输
    assert rs["A"].iloc[2] < 100 and close["A"].iloc[2] > close["A"].iloc[0]
    assert S.momentum(close, 2)["A"].iloc[2] == pytest.approx(0.2)
    assert S.momentum(close, 2, skip=1)["A"].iloc[2] == pytest.approx(0.2)   # 跳过最近一天：用 12 比 10


def test_forward_return_counts_delisting_as_an_exit():
    close = pd.DataFrame({"A": [10.0, 11.0, 12.0, 13.0], "B": [10.0, 8.0, np.nan, np.nan]}, index=DAYS[:4])
    out = S.forward_return(close, 2)
    assert out["A"].iloc[0] == pytest.approx(0.2)
    assert out["B"].iloc[0] == pytest.approx(-0.2)          # 第 3 天下架，按下架前最后的 8 算
    assert np.isnan(out["B"].iloc[2])                       # 已经下架的日子不参加统计
    dropped = S.forward_return(close, 2, exit_on_delisting=False)
    assert np.isnan(dropped["B"].iloc[0])                   # 直接丢掉的话，B 的这笔亏损不会进统计


def test_passes_and_scan_by_hand():
    features = {"成交额": pd.DataFrame({"A": [100.0, 100.0], "B": [10.0, 300.0], "C": [500.0, 500.0]}, index=DAYS[:2]),
                "涨幅": pd.DataFrame({"A": [0.1, 0.1], "B": [0.9, 0.9], "C": [0.5, np.nan]}, index=DAYS[:2])}
    filters = {"成交额": (50, None), "涨幅": (None, None)}
    ok = S.passes(features, filters)
    assert ok.loc[DAYS[0]].tolist() == [True, False, True]           # B 第一天成交额不够
    assert ok.loc[DAYS[1]].tolist() == [True, True, False]           # C 第二天涨幅是 NaN
    table = S.scan(DAYS[0], features, filters, rank_by="涨幅")
    assert table.index.tolist() == ["C", "A"]                        # B 没进名单，C 涨得多排前面
    assert table["名次"].tolist() == [1, 2] and table["百分位"].tolist() == [100.0, 50.0]
    assert S.scan(DAYS[0], features, filters, rank_by="涨幅", top=1).index.tolist() == ["C"]


def test_scan_never_uses_the_future():
    rng = np.random.default_rng(0)
    close = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.02, (8, 4)), axis=0)),
                         index=DAYS, columns=list("ABCD"))
    dv = pd.DataFrame(rng.uniform(1e6, 1e8, (8, 4)), index=DAYS, columns=list("ABCD"))
    features = {"成交额": S.rolling_turnover(dv, n=3), "涨幅": S.momentum(close, 3)}
    filters = {"成交额": (2e6, None), "涨幅": (None, None)}
    full = S.scan(DAYS[5], features, filters, rank_by="涨幅", top=None)
    cut = {name: values.loc[:DAYS[5]] for name, values in
           {"成交额": S.rolling_turnover(dv.loc[:DAYS[5]], n=3), "涨幅": S.momentum(close.loc[:DAYS[5]], 3)}.items()}
    pd.testing.assert_frame_equal(full, S.scan(DAYS[5], cut, filters, rank_by="涨幅", top=None))


def test_load_nasdaq_screener_by_hand(tmp_path):
    raw = {"data": {"rows": [
        {"symbol": "AAA", "name": "A Inc.", "lastsale": "$12.50", "volume": "1,000", "marketCap": "1,234,000.00",
         "sector": "Technology", "country": "United States", "ipoyear": "1999"},
        {"symbol": "BBB", "name": "B Inc.", "lastsale": "$3.00", "volume": "", "marketCap": "",
         "sector": "", "country": "", "ipoyear": ""}]}}
    path = tmp_path / "screener.json"
    path.write_text(json.dumps(raw))
    listing = D.load_nasdaq_screener(path)
    assert listing.index.tolist() == ["AAA", "BBB"]
    assert listing.loc["AAA", "market_cap"] == 1_234_000 and listing.loc["AAA", "close"] == 12.5
    assert np.isnan(listing.loc["BBB", "market_cap"])            # 没有市值的（ETF、优先股）记 NaN


def test_parse_s3_listing_by_hand():
    xml = ("<ListBucketResult><Prefix>data/futures/um/monthly/klines/</Prefix>"
           "<IsTruncated>false</IsTruncated>"
           "<CommonPrefixes><Prefix>data/futures/um/monthly/klines/BTCUSDT/</Prefix></CommonPrefixes>"
           "<CommonPrefixes><Prefix>data/futures/um/monthly/klines/LUNAUSDT/</Prefix></CommonPrefixes>"
           "</ListBucketResult>")
    names, marker = D.parse_s3_listing(xml, "data/futures/um/monthly/klines/")
    assert names == ["BTCUSDT", "LUNAUSDT"] and marker is None        # 已经下架的 LUNAUSDT 也在名单里
    truncated = xml.replace("<IsTruncated>false", "<IsTruncated>true")
    assert D.parse_s3_listing(truncated, "data/futures/um/monthly/klines/")[1].endswith("LUNAUSDT")
