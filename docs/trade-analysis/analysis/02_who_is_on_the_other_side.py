"""第 2 篇里全部数字的计算。"""
import glob, zipfile
import numpy as np, pandas as pd
from load import load
from nas import nas

# 三：零优势交易者的成本损耗；2025 年 BTCUSDT 永续成交额与手续费区间
for n in [50, 500, 2000]: print(n, 0.999 ** n - 1)
v = load("data/um1d/*.zip").quote_volume.sum(); print("成交额", v, "手续费", v * 0.0002, v * 0.0007)

# 五-1：第一次穿过前一天高低点 / 对照位置的那一分钟放量倍数（2025 现货 1 分钟）
m = load("data/1m/BTCUSDT-1m-2025-*.zip")
d = m.resample("1D").agg({"high": "max", "low": "min"})
rows = []
for day in d.index[1:]:
    prev = d.shift(1).loc[day]; x = m.loc[day:day + pd.Timedelta("1D") - pd.Timedelta("1min")]; rng = prev.high - prev.low
    for kind, lvl, side in [("prev_low", prev.low, "below"), ("prev_high", prev.high, "above"),
                            ("ctrl_mid", prev.low + 0.5 * rng, None), ("ctrl_37", prev.low + 0.37 * rng, None)]:
        hit = x.index[x.low < lvl] if side == "below" else x.index[x.high > lvl] if side == "above" else x.index[(x.low < lvl) & (x.high > lvl)]
        if len(hit) == 0: continue
        t = hit[0]; pre = m.loc[t - pd.Timedelta("60min"):t - pd.Timedelta("1min")].volume
        if len(pre) < 60: continue
        rows.append((kind, m.loc[t].volume / pre.median()))
r = pd.DataFrame(rows, columns=["kind", "ratio"]); print(r.groupby("kind").ratio.agg(["count", "median", lambda s: (s > 3).mean()]))

# 五-2：2025-10-10 持仓量与成交量
fr = []
for f in sorted(glob.glob("data/metrics/*.zip")):
    with zipfile.ZipFile(f) as z: fr.append(pd.read_csv(z.open(z.namelist()[0])))
oi = pd.concat(fr); oi.index = pd.to_datetime(oi.create_time, utc=True); oi = oi.sort_index().sum_open_interest
print(oi.loc["2025-10-10 20:40":"2025-10-10 22:45"])
u = load("data/um1m/BTCUSDT-1m-2025-10.zip")
print("此前每分钟成交量中位数", u.loc["2025-10-10 00:00":"2025-10-10 20:00"].volume.median())
print(u.loc["2025-10-10 20:52"]); print(u.loc["2025-10-10 21:13":"2025-10-10 21:20"].volume)
print("21:00-21:30", u.loc["2025-10-10 21:00":"2025-10-10 21:29"][["volume", "quote_volume"]].sum())
print("最低", u.loc["2025-10-10"].low.min(), u.loc["2025-10-10"].low.idxmin(), "22:20 收盘", u.loc["2025-10-10 22:20"].close)
print("现货同分钟最低", load("data/1m/BTCUSDT-1m-2025-10.zip").loc["2025-10-10 21:20"].low)

# 五-3：TSLA 纳入标普 500；SPY 季度调整日放量
tsla = nas("data/us/tsla.json"); print((tsla.loc["2020-12-14":"2020-12-22"][["close", "volume"]] * [3, 1 / 3]))
print("20 日中位数", tsla.volume.loc[:"2020-12-17"].tail(20).median() / 3)
spy = nas("data/us/spy.json"); spy["ratio"] = spy.volume / spy.volume.shift(1).rolling(20).median()
i = spy.index; tf = (i.weekday == 4) & (i.day >= 15) & (i.day <= 21); q = i.month.isin([3, 6, 9, 12])
for k, msk in {"季度第三周五": tf & q, "其他第三周五": tf & ~q, "其他周五": (i.weekday == 4) & ~tf, "周一到周四": i.weekday != 4}.items():
    s = spy.ratio[msk].dropna(); print(k, len(s), s.median(), (s > 1.5).mean())

# 五-4：一小时内各分钟的平均成交量
mh = m.volume.groupby(m.index.minute).mean(); print((mh / mh.median()).loc[[0, 1, 2, 30, 59]])
hr = m.volume.groupby([m.index.hour, m.index.minute]).mean()
for H in [0, 8, 16]: print(H, hr.loc[H].iloc[0] / hr.loc[H].median())
