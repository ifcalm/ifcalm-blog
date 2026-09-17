"""第 4 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd
from talab import data as D, plot as P

print("===== 片段 1：价格换算成像素 =====")
btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
march = btc.loc["2020-03-01":"2020-03-31"]
lo, hi = march["low"].min(), march["high"].max()
print("最低价", lo, "最高价", hi, "K 线根数", len(march))
bar = march.loc["2020-03-13"]
for name in ["high", "close", "open", "low"]:
    y_lin = P.price_to_y(bar[name], lo, hi, top=20, height=360)
    y_log = P.price_to_y(bar[name], lo, hi, top=20, height=360, log=True)
    print(f"{name:>5} {bar[name]:>9.2f}  算术坐标 y = {y_lin:6.2f}  对数坐标 y = {y_log:6.2f}")

print("===== 片段 2：手画 SVG =====")
Path("figures").mkdir(exist_ok=True)
svg = P.candles_svg(march)
Path("figures/hand-drawn.svg").write_text(svg)
lines = svg.splitlines()
print(len(lines), "行")
print(lines[26])          # 3 月 13 日的影线
print(lines[27])          # 3 月 13 日的实体

print("===== 片段 3：talab.plot =====")
P.use_chinese_font()
fig, ax, av = P.plot_candles(march, title="BTCUSDT 日线（2020 年 3 月），用 talab.plot 画")
fig.savefig("figures/talab-plot.png")

print("===== 片段 4：对数坐标里，相同的倍数是相同的距离 =====")
for a, b in [(10, 20), (100, 200), (1000, 2000)]:
    d_lin = P.price_to_y(a, 10, 2000, 0, 300) - P.price_to_y(b, 10, 2000, 0, 300)
    d_log = P.price_to_y(a, 10, 2000, 0, 300, log=True) - P.price_to_y(b, 10, 2000, 0, 300, log=True)
    print(f"{a:>5} → {b:<5} 算术坐标上相距 {d_lin:6.2f} 像素，对数坐标上相距 {d_log:6.2f} 像素")

print("===== 片段 5：同一条趋势线，两种坐标 =====")
x = btc.loc["2025-09-01":"2026-05-15"]
t1, p1 = pd.Timestamp("2025-10-06", tz="UTC"), btc.loc["2025-10-06", "high"]
t2, p2 = pd.Timestamp("2026-01-14", tz="UTC"), btc.loc["2026-01-14", "high"]
a = (x.index - t1) / (t2 - t1)                   # 第一个高点记为 0，第二个高点记为 1
linear = pd.Series(p1 + (p2 - p1) * a, index=x.index)
logline = pd.Series(np.exp(np.log(p1) + (np.log(p2) - np.log(p1)) * a), index=x.index)
after = x.index > t2
first_lin = x.index[after & (x["close"] > linear)][0]
first_log = x.index[after & (x["close"] > logline)][0]
print("两个高点：", p1, p2)
for day in [first_lin, first_log]:
    print(day.date(), "收盘", x.loc[day, "close"], " 算术直线", round(linear[day], 2), " 对数直线", round(logline[day], 2))
zero_day = t1 + (t2 - t1) * (p1 / (p1 - p2))
print("算术直线降到 0 的日期：", zero_day.date())
