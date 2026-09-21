"""talab.data：下载、加载、体检、价格调整。第 3 篇。"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 一、下载
# ---------------------------------------------------------------------------

BINANCE_BASE = "https://data.binance.vision/data"
BINANCE_LIST = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"        # 列目录用的 S3 接口
BINANCE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
]
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


REGULATOR_AGENT = "talab-course research@example.com"   # SEC / FINRA 要求 UA 写成「名字 邮箱」的样子


def _fetch(url: str, retries: int = 3, agent: str | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": agent or USER_AGENT})
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:                       # 文件不存在，重试也没用
                raise
            if i == retries - 1:
                raise
            time.sleep(2 ** i)
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2 ** i)


def download_binance_klines(symbol: str, interval: str, start: str, end: str,
                            market: str = "spot", dest: str = "data/binance",
                            skip_missing: bool = False, kind: str = "klines") -> list[Path]:
    """按月下载 Binance 公开 K 线压缩包，并用官方 .CHECKSUM 文件校验。

    market: "spot"（现货）或 "um"（U 本位永续合约）
    kind: "klines"（最新成交价）、"markPriceKlines"（标记价格）、"indexPriceKlines"（指数价格）等，
          只有合约有后面几种（第 22 篇）
    start / end: "YYYY-MM"，包含两端
    skip_missing: 这个月没有文件（上市之前、下架之后）时跳过，而不是报错
    """
    prefix = "spot" if market == "spot" else "futures/um"
    folder = Path(dest) / market / symbol / (interval if kind == "klines" else f"{kind}-{interval}")
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for month in pd.period_range(start, end, freq="M"):
        name = f"{symbol}-{interval}-{month}.zip"
        path = folder / name
        url = f"{BINANCE_BASE}/{prefix}/monthly/{kind}/{quote(symbol)}/{interval}/{quote(name)}"
        try:
            expected = _fetch(url + ".CHECKSUM").decode().split()[0]
        except urllib.error.HTTPError as e:
            if skip_missing and e.code == 404:
                continue
            raise
        if not (path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected):
            content = _fetch(url)
            actual = hashlib.sha256(content).hexdigest()
            if actual != expected:
                raise ValueError(f"{name} 校验失败：期望 {expected}，实际 {actual}")
            path.write_bytes(content)
        paths.append(path)
    return paths


def parse_s3_listing(xml: str, prefix: str) -> tuple[list[str], str | None]:
    """从 S3 列目录返回的 XML 里取出 prefix 下一层的名字，以及下一页的起点（没有下一页时是 None）。"""
    names = re.findall(r"<(?:Prefix|Key)>" + re.escape(prefix) + r"([^<]+?)/?</(?:Prefix|Key)>", xml)
    names = [n for n in names if n]
    if "<IsTruncated>true</IsTruncated>" not in xml:
        return names, None
    marker = re.search(r"<NextMarker>([^<]+)</NextMarker>", xml)
    return names, marker.group(1) if marker else prefix + names[-1]


def list_binance(prefix: str, folders: bool = True) -> list[str]:
    """列出 data.binance.vision 上某个目录下一层的名字（folders=True 列子目录，False 列文件）。"""
    names, marker = [], ""
    while True:
        url = f"{BINANCE_LIST}?prefix={quote(prefix)}&max-keys=1000" + ("&delimiter=/" if folders else "")
        page, marker = parse_s3_listing(_fetch(url + (f"&marker={quote(marker)}" if marker else "")).decode(), prefix)
        names += page
        if marker is None:
            return names


def binance_symbols(market: str = "spot") -> list[str]:
    """所有上过市的交易对，包含已经下架的。⚠️ 只看今天还在交易的那些，统计会有幸存者偏差。"""
    prefix = "spot" if market == "spot" else "futures/um"
    return list_binance(f"data/{prefix}/monthly/klines/")


def binance_months(symbol: str, interval: str, market: str = "spot", kind: str = "klines") -> list[str]:
    """某个交易对有哪些月份的 K 线文件（"YYYY-MM"），从上市月到下架月。"""
    prefix = "spot" if market == "spot" else "futures/um"
    names = list_binance(f"data/{prefix}/monthly/{kind}/{symbol}/{interval}/", folders=False)
    return sorted(n[-11:-4] for n in names if n.endswith(".zip"))


def download_binance_funding(symbol: str, start: str, end: str, market: str = "um",
                             dest: str = "data/binance") -> list[Path]:
    """按月下载资金费率的历史结算记录（第 24 篇），并用官方 .CHECKSUM 校验。

    文件里一行是一次结算：结算时刻、结算间隔（小时）、这一次的费率。
    """
    folder = Path(dest) / market / symbol / "fundingRate"
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for month in pd.period_range(start, end, freq="M"):
        name = f"{symbol}-fundingRate-{month}.zip"
        path = folder / name
        url = f"{BINANCE_BASE}/futures/{market}/monthly/fundingRate/{quote(symbol)}/{quote(name)}"
        expected = _fetch(url + ".CHECKSUM").decode().split()[0]
        if not (path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected):
            content = _fetch(url)
            actual = hashlib.sha256(content).hexdigest()
            if actual != expected:
                raise ValueError(f"{name} 校验失败：期望 {expected}，实际 {actual}")
            path.write_bytes(content)
        paths.append(path)
    return paths


def download_binance_metrics(symbol: str, start: str, end: str, market: str = "um",
                             dest: str = "data/binance", workers: int = 32) -> list[Path]:
    """按天下载合约的持仓量和多空比（第 25 篇），5 分钟一条，从 2020-09 起才有。

    每天一个文件，两千多天，所以并发下载并用官方 .CHECKSUM 校验。上市之前的日子没有文件，跳过。
    """
    folder = Path(dest) / market / symbol / "metrics"
    folder.mkdir(parents=True, exist_ok=True)

    def one(day) -> Path | None:
        name = f"{symbol}-metrics-{day:%Y-%m-%d}.zip"
        path = folder / name
        url = f"{BINANCE_BASE}/futures/{market}/daily/metrics/{quote(symbol)}/{quote(name)}"
        try:
            expected = _fetch(url + ".CHECKSUM").decode().split()[0]
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        if not (path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected):
            content = _fetch(url)
            actual = hashlib.sha256(content).hexdigest()
            if actual != expected:
                raise ValueError(f"{name} 校验失败：期望 {expected}，实际 {actual}")
            path.write_bytes(content)
        return path

    with ThreadPoolExecutor(max_workers=workers) as pool:
        got = list(pool.map(one, pd.date_range(start, end, freq="D")))
    return [p for p in got if p is not None]


def download_binance_book_ticker(symbol: str, days, market: str = "um",
                                dest: str = "data/binance") -> list[Path]:
    """下载最优买卖报价（第 28 篇），**下载完立刻聚合成 1 分钟，再把原始文件删掉**。

    原始文件一天 70–300 MB、几百万到几千万行（盘口每变一次就写一行）。留着它没有意义：
    这一篇要回答的是「价差有多宽、买一卖一有多厚」，1 分钟的汇总（一天 1,440 行）就够了。
    想重算别的统计量，重新下载就是了——这里保存的是**结论的原料**，不是原始数据的副本。

    ⚠️ 这套数据只有 **2023-05-16 到 2024-03-30**（320 天）。之前和之后 Binance 都没有公开，
    所以这一篇量到的价差是这 11 个月的事实，不能直接外推到 2017 年或 2026 年。
    """
    folder = Path(dest) / market / symbol / "bookTicker-1m"
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for day in days:
        target = folder / f"{symbol}-bookTicker-1m-{day}.csv.gz"
        if not target.exists():
            name = f"{symbol}-bookTicker-{day}.zip"
            url = f"{BINANCE_BASE}/futures/{market}/daily/bookTicker/{quote(symbol)}/{quote(name)}"
            try:
                raw = _fetch(url)
            except urllib.error.HTTPError as e:
                if e.code == 404:                   # 这一天没有公开数据
                    continue
                raise
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                frame = pd.read_csv(z.open(z.namelist()[0]),
                                    usecols=["best_bid_price", "best_bid_qty", "best_ask_price",
                                             "best_ask_qty", "transaction_time"])
            mid = (frame["best_bid_price"] + frame["best_ask_price"]) / 2
            frame["价差"] = (frame["best_ask_price"] - frame["best_bid_price"]) / mid * 10_000
            frame["中间价"] = mid
            frame["time"] = pd.to_datetime(frame["transaction_time"], unit="ms", utc=True).dt.floor("min")
            minute = frame.groupby("time").agg(
                更新次数=("价差", "size"), 价差=("价差", "mean"), 最宽价差=("价差", "max"),
                买一量=("best_bid_qty", "mean"), 卖一量=("best_ask_qty", "mean"),
                中间价=("中间价", "mean"))
            minute.to_csv(target)
        paths.append(target)
    return paths


BOOK_DEPTH_LEVELS = (-5.0, -4.0, -3.0, -2.0, -1.0, -0.2, 0.2, 1.0, 2.0, 3.0, 4.0, 5.0)


def download_binance_book_depth(symbol: str, days, market: str = "um",
                                dest: str = "data/binance") -> list[Path]:
    """下载盘口深度快照（番外篇），**下载完立刻转成宽表、金额取整到美元，再把原始文件删掉**。

    ⚠️ 先说清楚这份数据**不是**什么：它不是逐笔订单流，也不是完整的 L2 盘口。
    Binance 公开的是**每 30 秒一张快照**，每张快照只有 12 个数——买卖两侧在
    ±0.2%、1%、2%、3%、4%、5% 这六个距离上的**累计**挂单金额。

    所以「大单墙在哪一档」「有没有撤单」「是不是冰山单」这类问题，**用这份数据一个都答不了**，
    要答只能自己开 WebSocket 录，而且录的是未来。这一篇只回答它能回答的那个问题：
    **崩盘的时候，盘口上的钱还在不在。**

    ⚠️ 覆盖范围是 **2023-01-01 起**，之前没有公开数据。
    """
    folder = Path(dest) / market / symbol / "bookDepth-30s"
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for day in days:
        target = folder / f"{symbol}-bookDepth-30s-{day}.csv.gz"
        if not target.exists():
            name = f"{symbol}-bookDepth-{day}.zip"
            url = f"{BINANCE_BASE}/futures/{market}/daily/bookDepth/{quote(symbol)}/{quote(name)}"
            try:
                raw = _fetch(url)
            except urllib.error.HTTPError as e:
                if e.code == 404:                   # 这一天没有公开数据
                    continue
                raise
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                frame = pd.read_csv(z.open(z.namelist()[0]))
            wide = frame.pivot_table(index="timestamp", columns="percentage",
                                     values="notional", aggfunc="last")
            wide = wide.reindex(columns=list(BOOK_DEPTH_LEVELS)).round(0)
            wide.columns = [f"{level:+g}%" for level in wide.columns]
            wide.index.name = "time"
            wide.to_csv(target)
        paths.append(target)
    return paths


def load_binance_book_depth(paths) -> pd.DataFrame:
    """读回 `download_binance_book_depth` 转好的宽表。

    每行一张快照（30 秒一张），列是 `-5%`…`+5%` 十二档的**累计挂单金额（美元）**。
    ⚠️ 负号那一侧是**买盘**（价格比中间价低），正号是卖盘。
    """
    frames = [pd.read_csv(path, parse_dates=["time"]) for path in sorted(map(str, paths))]
    out = pd.concat(frames, ignore_index=True).set_index("time").sort_index()
    out.index = out.index.tz_localize("UTC") if out.index.tz is None else out.index.tz_convert("UTC")
    return out


def load_binance_book_ticker(paths) -> pd.DataFrame:
    """读回 `download_binance_book_ticker` 聚合好的 1 分钟盘口。价差的单位是**基点**（万分之一）。"""
    frames = [pd.read_csv(path, parse_dates=["time"]) for path in sorted(map(str, paths))]
    out = pd.concat(frames, ignore_index=True).set_index("time").sort_index()
    out.index = out.index.tz_convert("UTC") if out.index.tz is not None else out.index.tz_localize("UTC")
    return out


SEC_FEE_ADVISORIES = "https://www.sec.gov/rules-regulations/fee-rate-advisories"
FINRA_FEE_RULES = ("https://www.finra.org/rules-guidance/rulebooks/"
                   "corporate-organization/section-1-member-regulatory-fees")


def _plain(page: str) -> str:
    """把一页 HTML 压成一行纯文本，方便用正则找数字。"""
    body = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", body)))


def parse_sec_fee_advisory(page: str) -> pd.Series:
    """从 SEC 的「Section 31 Transaction Fee Rate Advisory」里取出费率和生效日（第 28 篇）。

    这笔钱**只在卖出时收**，按成交金额算，买入不收。费率每年随国会拨款调整，
    所以要现抓而不是写死——写死的费率过两年就是错的。
    """
    text = _plain(page)
    rate = re.search(r"will be set at \$([\d.]+) per million", text)
    when = re.search(r"starting on ([A-Z][a-z]+ \d{1,2}, \d{4})", text)
    year = re.search(r"Fiscal Year (\d{4})", text)
    if not (rate and when):
        raise ValueError("没在这一页里找到 Section 31 的费率")
    value = float(rate.group(1)) / 1e6
    return pd.Series({"财年": int(year.group(1)) if year else None,
                      "每百万美元": float(rate.group(1)),
                      "占卖出金额": value,
                      "生效日": pd.Timestamp(when.group(1))})


def parse_finra_taf(page: str) -> pd.Series:
    """从 FINRA 的费用规则页里取出交易活动费（TAF）：**按股数**收，也只在卖出时收。"""
    text = _plain(page)
    per_share = re.search(r"\$?([\d.]+) per share for each sale of a covered equity security", text)
    cap = re.search(r"maximum charge of \$([\d.]+)", text)
    if not (per_share and cap):
        raise ValueError("没在这一页里找到 TAF 的费率")
    return pd.Series({"每股": float("0." + per_share.group(1).split(".")[-1]),
                      "每笔上限": float(cap.group(1))})


def us_fee_schedule() -> pd.Series:
    """现抓美股的两项监管费（第 28 篇）：SEC 的 Section 31 费和 FINRA 的 TAF。

    ⚠️ 两项都**只在卖出时收**。它们加起来通常只有成交金额的万分之几，
    真正贵的是买卖价差——而价差没有公开的历史数据。
    """
    links = re.findall(r'href="([^"]*fee-rate-advisories/\d{4}-\d)"',
                       _fetch(SEC_FEE_ADVISORIES, agent=REGULATOR_AGENT).decode())
    for link in links:                                  # 找最近一条 Section 31 的公告
        url = link if link.startswith("http") else "https://www.sec.gov" + link
        page = _fetch(url, agent=REGULATOR_AGENT).decode()
        if "Section 31 Transaction Fee Rate Advisory" in page:
            sec = parse_sec_fee_advisory(page)
            break
    else:
        raise ValueError("没找到 Section 31 的公告")
    finra = parse_finra_taf(_fetch(FINRA_FEE_RULES, agent=REGULATOR_AGENT).decode())
    return pd.concat([sec.rename(lambda k: f"SEC {k}"), finra.rename(lambda k: f"TAF {k}")])


def download_binance_brackets(dest: str = "data/binance") -> Path:
    """下载 U 本位合约的分层维持保证金表（第 24 篇），原样保存 JSON。

    这是**今天**的表：档位的名义价值上限、维持保证金率和最大杠杆都会被交易所调整，
    拿它去算几年前的某一笔仓位，算的是「按今天的规则会怎样」。
    """
    path = Path(dest) / "brackets.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fetch("https://www.binance.com/bapi/futures/v1/friendly/future/common/brackets"))
    return path


BINANCE_API = "https://api.binance.com/api/v3/"
BINANCE_API_AGENT = "talab-course/1.0"


def download_binance_public(endpoint: str, name: str, dest: str = "data/binance") -> Path:
    """下载 Binance 的一个**公开**接口（不需要账号、不需要密钥），原样保存 JSON。第 34 篇。

    这一篇只用两个：

    - `exchangeInfo`：每个交易对的下单规矩（tickSize、stepSize、minNotional……）
    - `ticker/price`：现在的价格，用来把 stepSize 换算成钱

    ⚠️ 和 `download_binance_brackets` 一样，拿到的是**今天**的规矩。交易所随时会改，
    所以这个文件要和回测结果一起存档——不然过两个月你复现不出自己的数。
    """
    path = Path(dest) / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fetch(BINANCE_API + endpoint, agent=BINANCE_API_AGENT))
    return path


def load_json(path) -> dict | list:
    """把 `download_binance_public` 存下来的文件读回来。"""
    return json.loads(Path(path).read_text())


def download_finra_short_volume(days: list[str], dest: str = "data/finra") -> list[Path]:
    """下载 FINRA 每日卖空成交量文件（第 24 篇），days 是 "YYYY-MM-DD" 的列表。

    ⚠️ 这是 FINRA 三个交易报告设施（TRF）上的成交，不含交易所撮合的部分，
    所以「卖空占比」是这部分成交里的占比，不是全市场的占比。周末和假日没有文件。
    ⚠️ 市场休市那天没有文件，FINRA 对不存在的文件返回 **403 而不是 404**
    （2026-06-19 Juneteenth 就是这样），所以两个状态码都当成「这天没有」。
    """
    folder = Path(dest)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for day in days:
        stamp = day.replace("-", "")
        path = folder / f"CNMSshvol{stamp}.txt"
        if not path.exists():
            try:
                path.write_bytes(_fetch(f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{stamp}.txt"))
            except urllib.error.HTTPError as e:
                if e.code in (403, 404):            # 周末、假日：没有这个文件
                    continue
                raise
            time.sleep(0.5)                         # 对公开服务器客气一点
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


def download_nasdaq_screener(dest: str = "data/nasdaq") -> Path:
    """今天在 NASDAQ、NYSE、AMEX 上市的全部股票（代码、名称、市值、当天成交量、行业），原样保存 JSON。

    ⚠️ 这是**今天**的名单：退市、被收购的公司不在里面。拿它回测历史会有幸存者偏差（第 19 篇）。
    """
    path = Path(dest) / "screener.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fetch("https://api.nasdaq.com/api/screener/stocks?tableonly=true&download=true"))
    return path


FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd={start}"
FRED_AGENT = "talab-course/1.0"     # ⚠️ FRED 会把浏览器的 UA 晾着不回应，报个老实的名字反而秒回

# 无风险利率常用的两个序列（都是年化百分数，不是小数）
FRED_SERIES = {"3 个月国库券": "DTB3", "联邦基金有效利率": "DFF"}


def download_fred_series(series: str = "DTB3", start: str = "2016-01-01",
                         dest: str = "data/fred") -> Path:
    """下载圣路易斯联储 FRED 上的一条日频序列，原样保存 CSV（公开接口，不需要注册）。

    默认的 `DTB3` 是 3 个月国库券的二级市场收益率，算夏普比率时最常用的无风险利率。
    """
    path = Path(dest) / f"{series}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fetch(FRED_CSV.format(series=series, start=start), agent=FRED_AGENT))
    return path


def load_fred_series(path) -> pd.Series:
    """读取 FRED 的 CSV，返回**小数形式**的年化利率（4.25% 读成 0.0425）。

    ⚠️ FRED 的利率列写的是百分数，这里除以 100；假日那天是 "."，转成 NaN 之后前向填充。
    """
    df = pd.read_csv(path, parse_dates=[0], index_col=0)
    s = pd.to_numeric(df.iloc[:, 0], errors="coerce") / 100
    s.index.name = "date"
    return s.ffill().rename(df.columns[0])


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


def load_binance_funding(paths) -> pd.Series:
    """把一组资金费率压缩包读成一条 Series，索引是结算时刻（UTC），值是这一次结算的费率。

    正数＝多头付给空头，负数＝空头付给多头（第 24 篇）。
    """
    paths = sorted(Path(p) for p in paths)
    if not paths:
        raise ValueError("没有找到任何资金费率文件，检查一下路径")
    frames = []
    for path in paths:
        with zipfile.ZipFile(path) as z:
            frames.append(pd.read_csv(z.open(z.namelist()[0])))
    df = pd.concat(frames, ignore_index=True)
    df.index = pd.to_datetime(df["calc_time"].astype("int64"), unit="ms", utc=True).dt.round("h")
    df.index.name = "time"
    rate = df["last_funding_rate"].astype(float).sort_index()
    rate.name = "funding"
    return rate[~rate.index.duplicated()]


def load_binance_metrics(paths) -> pd.DataFrame:
    """把一组持仓量文件读成一张表，索引是 UTC 时间（5 分钟一条）。

    列：持仓量（币）、持仓价值（USDT）、大户账户数多空比、大户持仓量多空比、
    全部账户数多空比、主动买卖量比。
    """
    paths = sorted(Path(p) for p in paths)
    if not paths:
        raise ValueError("没有找到任何持仓量文件，检查一下路径")
    frames = []
    for path in paths:
        with zipfile.ZipFile(path) as z:
            frames.append(pd.read_csv(z.open(z.namelist()[0])))
    df = pd.concat(frames, ignore_index=True)
    df.index = pd.to_datetime(df.pop("create_time"), format="%Y-%m-%d %H:%M:%S", utc=True)
    df.index.name = "time"
    df = df.drop(columns=["symbol"]).astype(float).sort_index()
    df.columns = ["持仓量", "持仓价值", "大户账户数多空比", "大户持仓多空比", "账户数多空比", "主动买卖比"]
    return df[~df.index.duplicated()]                 # ⚠️ 官方文件里每一行都重复了一遍


def load_binance_brackets(path, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """读取一个合约的分层维持保证金表：每一档的名义价值区间、维持保证金率、速算额、最大杠杆。"""
    data = json.loads(Path(path).read_text())["data"]["brackets"]
    rows = [b for b in data if b["symbol"] == symbol]
    if not rows:
        raise KeyError(f"表里没有 {symbol}")
    df = pd.DataFrame(rows[0]["riskBrackets"])
    df = df.rename(columns={"bracketNotionalFloor": "下限", "bracketNotionalCap": "上限",
                            "bracketMaintenanceMarginRate": "维持保证金率",
                            "cumFastMaintenanceAmount": "速算额", "maxOpenPosLeverage": "最大杠杆"})
    df.attrs["updated"] = pd.Timestamp(rows[0]["updateTime"], unit="ms", tz="UTC")
    return df[["下限", "上限", "维持保证金率", "速算额", "最大杠杆"]].sort_values("下限").reset_index(drop=True)


def load_finra_short_volume(paths, symbols=None) -> pd.DataFrame:
    """读取 FINRA 每日卖空成交量：索引是日期，列是股票代码，值是卖空量占这部分成交量的比例。"""
    frames = []
    for path in sorted(Path(p) for p in paths):
        df = pd.read_csv(path, sep="|").dropna(subset=["Symbol"])
        if symbols is not None:
            df = df[df["Symbol"].isin(symbols)]
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["Date"].astype("int64").astype(str), format="%Y%m%d")
    df["share"] = df["ShortVolume"] / df["TotalVolume"]
    return df.pivot_table(index="date", columns="Symbol", values="share")


def load_nasdaq_short_interest(path) -> pd.DataFrame:
    """读取 Nasdaq 的空头仓位记录：每半个月一行，空头股数、日均成交量、回补天数。"""
    rows = json.loads(Path(path).read_text())["data"]["shortInterestTable"]["rows"]
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.pop("settlementDate"), format="%m/%d/%Y")
    df.index.name = "date"
    df["空头股数"] = pd.to_numeric(df.pop("interest").str.replace(",", ""))
    df["日均成交量"] = pd.to_numeric(df.pop("avgDailyShareVolume").str.replace(",", ""))
    df["回补天数"] = pd.to_numeric(df.pop("daysToCover"))
    return df.sort_index()


def load_nasdaq_daily(path) -> pd.DataFrame:
    """读取 Nasdaq 日线。⚠️ 这个接口给出的价格和成交量已经按拆股调整过，但没有按分红调整。"""
    rows = json.loads(Path(path).read_text())["data"]["tradesTable"]["rows"]
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.pop("date"), format="%m/%d/%Y")
    df.index.name = "date"
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c].str.replace(r"[$,]", "", regex=True), errors="coerce")  # "N/A" → NaN
    return df[["open", "high", "low", "close", "volume"]].sort_index()


def load_nasdaq_screener(path) -> pd.DataFrame:
    """读取股票名单：索引是股票代码，列有名称、市值（美元）、当天成交量、当天价格、行业。"""
    rows = json.loads(Path(path).read_text())["data"]["rows"]
    df = pd.DataFrame(rows).set_index("symbol")
    for name, source in [("market_cap", "marketCap"), ("volume", "volume")]:
        df[name] = pd.to_numeric(df[source].str.replace(",", ""), errors="coerce")
    df["close"] = pd.to_numeric(df["lastsale"].str.lstrip("$"), errors="coerce")
    return df[["name", "close", "volume", "market_cap", "sector", "country", "ipoyear"]]


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
