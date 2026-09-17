"""第 1 篇里全部数字的计算。运行：python 01_what_a_chart_records.py（需 pandas、numpy，数据见 README）"""
import numpy as np
from load import load

agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "taker_buy_base": "sum"}

# 一、四、五：2021-02-08 小时线
m = load("data/1m/BTCUSDT-1m-2021-02.zip")
h = m.loc["2021-02-08"].resample("1h").agg(agg)
h["ret"] = h.close / h.open - 1; h["tbr"] = h.taker_buy_base / h.volume
print(h.loc["2021-02-08 12:00":"2021-02-08 13:00"])
print("前 12 小时平均成交量", m.loc["2021-02-08 00:00":"2021-02-08 11:59"].volume.sum() / 12)
print("12:00 成交笔数", m.loc["2021-02-08 12:00":"2021-02-08 12:59"].trades.sum())

# 四：全部日线的主动买入占比
d = load("data/1d/*.zip")
d["ret"] = d.close / d.open - 1; d["buy_ratio"] = d.taker_buy_base / d.volume
up = d[d.ret > 0]; big = d[d.ret > 0.05]
print("上涨日", len(up), (up.buy_ratio < 0.5).sum(), "大涨日", len(big), (big.buy_ratio < 0.5).sum())
print("涨幅排名前五", d.ret.nlargest(5))

# 四：2020-03-13 小时线
h2 = load("data/1m/BTCUSDT-1m-2020-03.zip").loc["2020-03-13"]
print(h2.resample("1h").agg(agg).assign(tbr=lambda x: x.taker_buy_base / x.volume))

# 六：2021-05-19 现货 vs 永续合约
s = load("data/1m/BTCUSDT-1m-2021-05.zip").loc["2021-05-19"]; u = load("data/um1m/BTCUSDT-1m-2021-05.zip").loc["2021-05-19"]
print("13:10 最低", s.loc["2021-05-19 13:10"].low, u.loc["2021-05-19 13:10"].low)
dc = (u.close - s.close).abs(); print("收盘价差最大", dc.max(), dc.idxmax(), "中位数", dc.median())

# 七：方向延续与整数价位
r = d.ret; same = (np.sign(r) == np.sign(r.shift(1))).iloc[1:]
print("次日同向", same.mean(), "大波动后", same[(r.shift(1).abs() > 0.05).iloc[1:]].mean())
for y in ["2018", "2021", "2024", "2025"]:
    rr = r.loc[y]; print(y, (np.sign(rr) == np.sign(rr.shift(1))).iloc[1:].mean())
x = d[d.low >= 10000]
for step in [1000, 100]:
    print(step, len(x), np.isclose(x.low % step, 0).sum(), np.isclose(x.high % step, 0).sum(), len(x) * 0.01 / step)

# 四、九：2025 年各周期
m5 = load("data/1m/BTCUSDT-1m-2025-*.zip")
for tf in ["1min", "5min", "15min", "1h", "4h", "1D"]:
    b = m5.resample(tf).agg(agg).dropna(); ret = b.close / b.open - 1
    above = b.close > b.close.rolling(20).mean()
    print(tf, len(b), ret.abs().median(), (ret.abs() < 0.001).mean(),
          "corr", np.corrcoef(ret, 2 * b.taker_buy_base / b.volume - 1)[0, 1],
          "上穿MA20", (above & ~above.shift(1, fill_value=False)).iloc[20:].sum())
