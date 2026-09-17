"""talab.data：下载、加载、体检、价格调整。第 3 篇。"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 一、下载
# ---------------------------------------------------------------------------

BINANCE_BASE = "https://data.binance.vision/data"
BINANCE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
]
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def _fetch(url: str, retries: int = 3) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2 ** i)


def download_binance_klines(symbol: str, interval: str, start: str, end: str,
                            market: str = "spot", dest: str = "data/binance") -> list[Path]:
    """按月下载 Binance 公开 K 线压缩包，并用官方 .CHECKSUM 文件校验。

    market: "spot"（现货）或 "um"（U 本位永续合约）
    start / end: "YYYY-MM"，包含两端
    """
    prefix = "spot" if market == "spot" else "futures/um"
    folder = Path(dest) / market / symbol / interval
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for month in pd.period_range(start, end, freq="M"):
        name = f"{symbol}-{interval}-{month}.zip"
        path = folder / name
        url = f"{BINANCE_BASE}/{prefix}/monthly/klines/{symbol}/{interval}/{name}"
        expected = _fetch(url + ".CHECKSUM").decode().split()[0]
        if not (path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected):
            content = _fetch(url)
            actual = hashlib.sha256(content).hexdigest()
            if actual != expected:
                raise ValueError(f"{name} 校验失败：期望 {expected}，实际 {actual}")
            path.write_bytes(content)
        paths.append(path)
    return paths


def download_nasdaq(symbol: str, kind: str, dest: str = "data/nasdaq",
                    assetclass: str = "stocks", start: str = "2016-01-01", end: str | None = None) -> Path:
    """从 Nasdaq 公开接口下载日线（kind="historical"）或分红记录（kind="dividends"），原样保存 JSON。"""
    end = end or pd.Timestamp.today().strftime("%Y-%m-%d")
    base = f"https://api.nasdaq.com/api/quote/{symbol}/{kind}?assetclass={assetclass}"
    url = base + (f"&fromdate={start}&todate={end}&limit=9999" if kind == "historical" else "")
    path = Path(dest) / f"{symbol}_{kind}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fetch(url))
    return path


# ---------------------------------------------------------------------------
# 二、加载
# ---------------------------------------------------------------------------

def load_binance_klines(paths) -> pd.DataFrame:
    """把一组 Binance K 线压缩包读成一张表，索引是 UTC 时间（K 线开始的时刻）。"""
    paths = sorted(Path(p) for p in paths)
    if not paths:
        raise ValueError("没有找到任何 K 线文件，检查一下路径")
    frames = []
    for path in paths:
        with zipfile.ZipFile(path) as z:
            df = pd.read_csv(z.open(z.namelist()[0]), header=None)
        if not str(df.iloc[0, 0]).isdigit():        # 部分文件第一行是表头
            df = df.iloc[1:]
        df.columns = BINANCE_COLUMNS
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    t = df["open_time"].astype("int64")
    # ⚠️ 现货数据从 2025-01-01 起时间戳是微秒（16 位），之前是毫秒（13 位）
    t = np.where(t > 10**14, t // 1000, t)
    df.index = pd.to_datetime(t, unit="ms", utc=True)
    df.index.name = "time"
    num = ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base", "taker_buy_quote"]
    df[num] = df[num].astype(float)
    df["trades"] = df["trades"].astype("int64")
    return df.drop(columns=["open_time", "close_time", "ignore"])


def load_nasdaq_daily(path) -> pd.DataFrame:
    """读取 Nasdaq 日线。⚠️ 这个接口给出的价格和成交量已经按拆股调整过，但没有按分红调整。"""
    rows = json.loads(Path(path).read_text())["data"]["tradesTable"]["rows"]
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.pop("date"), format="%m/%d/%Y")
    df.index.name = "date"
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c].str.replace(r"[$,]", "", regex=True), errors="coerce")  # "N/A" → NaN
    return df[["open", "high", "low", "close", "volume"]].sort_index()


def load_nasdaq_dividends(path) -> pd.Series:
    """读取现金分红记录：索引是除息日，值是每股分红（当时的原始金额，没有按之后的拆股调整）。"""
    rows = json.loads(Path(path).read_text())["data"]["dividends"]["rows"]
    df = pd.DataFrame(rows)
    df = df[df["type"] == "Cash"]
    s = pd.Series(pd.to_numeric(df["amount"].str.replace("$", ""), errors="coerce").values,
                  index=pd.to_datetime(df["exOrEffDate"], format="%m/%d/%Y"), name="dividend")
    return s.sort_index()


# ---------------------------------------------------------------------------
# 三、价格调整
# ---------------------------------------------------------------------------

# 拆股记录：（拆股后第一个交易日，1 股变成几股）
SPLITS = {
    "AAPL": [("1987-06-16", 2), ("2000-06-21", 2), ("2005-02-28", 2), ("2014-06-09", 7), ("2020-08-31", 4)],
    "TSLA": [("2020-08-31", 5), ("2022-08-25", 3)],
    "SPY": [],
}

PRICE_COLS = ["open", "high", "low", "close"]


def split_factor(index: pd.DatetimeIndex, splits) -> pd.Series:
    """每一天的「拆股系数」：这一天之后一共拆了多少倍。拆股后第一天及以后为 1。"""
    f = pd.Series(1.0, index=index)
    for day, ratio in splits:
        f[index < pd.Timestamp(day)] *= ratio
    return f


def unadjust_splits(df: pd.DataFrame, splits) -> pd.DataFrame:
    """把按拆股调整过的价格还原成当时真实成交的价格。"""
    f = split_factor(df.index, splits)
    raw = df.copy()
    raw[PRICE_COLS] = df[PRICE_COLS].mul(f, axis=0)
    raw["volume"] = df["volume"] / f
    return raw


def adjust_splits(raw: pd.DataFrame, splits) -> pd.DataFrame:
    """把真实成交价格按拆股调整：拆股之前的价格除以之后累计的拆股倍数。"""
    f = split_factor(raw.index, splits)
    adj = raw.copy()
    adj[PRICE_COLS] = raw[PRICE_COLS].div(f, axis=0)
    adj["volume"] = raw["volume"] * f
    return adj


def dividend_factor(raw_close: pd.Series, dividends: pd.Series) -> pd.Series:
    """每一天的「分红系数」。

    对每个除息日 e，分红 D，除息日前一个交易日的真实收盘价 P：
        这次分红的系数 = 1 - D / P
    除息日之前的每一天，都要乘上这个系数；多次分红的系数连乘。
    """
    f = pd.Series(1.0, index=raw_close.index)
    for ex_date, amount in dividends.items():
        before = raw_close.index[raw_close.index < ex_date]
        if len(before) == 0 or ex_date > raw_close.index[-1]:
            continue                                   # 数据范围之外的分红
        prev_close = raw_close[before[-1]]
        f[raw_close.index < ex_date] *= 1 - amount / prev_close
    return f


def adjust_total_return(raw: pd.DataFrame, splits, dividends: pd.Series) -> pd.DataFrame:
    """同时按拆股和分红调整。调整后，相邻两天价格之比 = 持有者真实的总收益（含分红再投资）。"""
    adj = adjust_splits(raw, splits)
    f = dividend_factor(raw["close"], dividends)
    adj[PRICE_COLS] = adj[PRICE_COLS].mul(f, axis=0)
    return adj


# ---------------------------------------------------------------------------
# 四、体检
# ---------------------------------------------------------------------------

def health_check(df: pd.DataFrame, freq: str | None = None, sessions: pd.DatetimeIndex | None = None,
                 wick_k: float = 20.0, wick_window: int = 1440,
                 low_volume_ratio: float | None = None, volume_window: int = 20) -> dict[str, pd.DataFrame | pd.Index]:
    """检查一张 OHLCV 表的常见问题，返回每类问题对应的行。

    freq:      固定周期（如 "1min"、"1D"），用来找缺失的 K 线（适合 24 小时交易的市场）
    sessions:  交易日历（适合有休市的市场），用来找缺失和多出来的交易日
    wick_k:    影线长度超过「过去 wick_window 根 K 线典型波幅」的多少倍，算作可疑插针
    low_volume_ratio: 成交量低于「过去 volume_window 根 K 线中位数」的这个比例，算作可疑（适合日线）
    """
    report = {}
    report["重复时间戳"] = df.index[df.index.duplicated()]
    report["时间没有按顺序排列"] = df.index[1:][df.index[1:] <= df.index[:-1]]
    report["有空值的行"] = df[df[PRICE_COLS + ["volume"]].isna().any(axis=1)]
    body_hi = df[["open", "close"]].max(axis=1)
    body_lo = df[["open", "close"]].min(axis=1)
    report["高低价自相矛盾"] = df[(df["high"] < body_hi) | (df["low"] > body_lo) | (df["low"] > df["high"])]
    report["价格不为正"] = df[(df[PRICE_COLS] <= 0).any(axis=1)]
    report["成交量为零"] = df[df["volume"] == 0]
    report["四价相同"] = df[(df["open"] == df["high"]) & (df["high"] == df["low"]) & (df["low"] == df["close"])]

    if freq is not None:
        report["时间戳没有对齐"] = df.index[df.index != df.index.floor(freq)]
        full = pd.date_range(df.index[0].floor(freq), df.index[-1], freq=freq)
        report["缺失的 K 线"] = full.difference(df.index.floor(freq))
    if sessions is not None:
        report["缺失的交易日"] = sessions.difference(df.index)
        report["日历之外多出来的日子"] = df.index.difference(sessions)

    # 可疑插针：影线远远长于最近的典型波幅
    typical = ((df["high"] - df["low"]) / df["close"]).rolling(wick_window, min_periods=wick_window // 2).median().shift(1)
    upper = (df["high"] - body_hi) / df["close"]
    lower = (body_lo - df["low"]) / df["close"]
    report["可疑插针"] = df[(upper > wick_k * typical) | (lower > wick_k * typical)]

    if low_volume_ratio is not None:
        usual = df["volume"].rolling(volume_window, min_periods=volume_window // 2).median().shift(1)
        report["成交量异常偏低"] = df[df["volume"] < low_volume_ratio * usual]
    return report


def summarize(report: dict) -> pd.Series:
    """把体检报告压缩成「每类问题有多少条」。"""
    return pd.Series({k: len(v) for k, v in report.items()}, name="数量")


def missing_runs(missing: pd.DatetimeIndex, freq: str) -> pd.DataFrame:
    """把一个个缺失的时间点，合并成一段段连续的缺口。"""
    if len(missing) == 0:
        return pd.DataFrame(columns=["开始", "结束", "缺失根数"])
    step = pd.Timedelta(freq)
    s = pd.Series(missing)
    group = (s.diff() != step).cumsum()
    runs = s.groupby(group).agg(["first", "last", "count"])
    runs.columns = ["开始", "结束", "缺失根数"]
    return runs.reset_index(drop=True)


def fingerprint(df: pd.DataFrame) -> dict:
    """复现指纹：你算出来的这几个数和正文一致，说明数据一致。"""
    return {
        "行数": len(df),
        "起点": str(df.index[0]),
        "终点": str(df.index[-1]),
        "收盘价之和": round(float(df["close"].sum()), 2),
    }
