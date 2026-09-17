"""第 5 篇正文里的代码片段（在 talab 项目根目录运行，先运行 scripts/fetch_course_data.py）。"""
import glob
import math

import numpy as np
import pandas as pd
from talab import data as D, stats as S

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

print("===== 片段 1：准备三个标的的收盘价 =====")
btc = D.load_binance_klines(glob.glob("data/binance/spot/BTCUSDT/1d/*.zip"))
spy = D.load_nasdaq_daily("data/nasdaq/SPY_historical.json")
spy = spy.drop(pd.Timestamp("2026-04-20"))              # 第 3 篇体检发现的填充行
aapl = D.load_nasdaq_daily("data/nasdaq/AAPL_historical.json")
divs = D.load_nasdaq_dividends("data/nasdaq/AAPL_dividends.json")
aapl_total = D.adjust_total_return(D.unadjust_splits(aapl, D.SPLITS["AAPL"]), D.SPLITS["AAPL"], divs)
close = {"SPY": spy["close"], "AAPL": aapl_total["close"], "BTC": btc["close"]}
ppy = {"SPY": 252, "AAPL": 252, "BTC": 365}
rets = {k: S.simple_returns(v) for k, v in close.items()}
logs = {k: S.log_returns(v) for k, v in close.items()}
for k, r in rets.items():
    print(k, len(r), "个收益率", r.index[0].date(), "至", r.index[-1].date())

print("===== 片段 2：决策点：正态分布怎么看 −15% =====")
r = rets["BTC"]
past = r.loc[:"2022-06-12"]
last_year = past.iloc[-365:]
mean, std = last_year.mean(), last_year.std()
p = S.NORMAL.cdf((-0.15 - mean) / std)
print(f"过去 365 天：日均 {mean:.4%}，日波动率 {std:.4%}")
print(f"z = {(-0.15 - mean) / std:.2f}，正态概率 {p:.3e}，约 {1 / p / 365:.0f} 年一次")
print("2022-06-12 之前跌幅超过 15% 的日子：")
print(past[past <= -0.15].round(4))

print("===== 片段 3：简单收益率与对数收益率 =====")
c = btc["close"]
print("2022-06-12 收盘", c["2022-06-12"], " 2022-06-13 收盘", c["2022-06-13"])
print(f"简单 {c['2022-06-13'] / c['2022-06-12'] - 1:.4%}  对数 {math.log(c['2022-06-13'] / c['2022-06-12']):.4%}")
two = c.loc["2020-03-11":"2020-03-13"]
print(two)
s2 = two.pct_change().dropna()
l2 = np.log(two).diff().dropna()
print("简单收益率", s2.round(4).tolist(), "相加", round(s2.sum(), 4), "复利", round(S.total_return(s2), 4))
print("对数收益率", l2.round(4).tolist(), "相加", round(l2.sum(), 4), "换回简单", round(math.expm1(l2.sum()), 4))

print("===== 片段 4：组合收益率 =====")
spy_raw, aapl_raw = spy["close"], aapl["close"]
for name, s in [("SPY", spy_raw), ("AAPL", aapl_raw)]:
    print(name, s["2025-04-08"], s["2025-04-09"], f"{s['2025-04-09'] / s['2025-04-08'] - 1:.4%}", f"{math.log(s['2025-04-09'] / s['2025-04-08']):.4%}")

print("===== 片段 5：算术平均 vs 复利 =====")
for k, r in rets.items():
    n = len(r)
    naive = (1 + r.mean()) ** n
    actual = 1 + S.total_return(r)
    print(f"{k:4s} 日均 {r.mean():.4%}  按日均复利 {naive:7.2f} 倍  实际 {actual:6.2f} 倍  "
          f"对数日均 {logs[k].mean():.4%}  日均 − 方差/2 {r.mean() - r.var() / 2:.4%}")

print("===== 片段 6：手算 5 天的波动率 =====")
five = rets["BTC"].loc["2022-06-13":"2022-06-17"]
print((five * 100).round(4))
print("均值", round(five.mean() * 100, 4), "标准差", round(five.std() * 100, 4))

print("===== 片段 7：年化 =====")
for k, r in rets.items():
    wrong = 365 if ppy[k] == 252 else 252               # 故意用错的天数，看看差多少
    print(f"{k:4s} 日波动率 {r.std():.4%}  ×√{ppy[k]} = {S.annualize_vol(r.std(), ppy[k]):.1%}   "
          f"(错用 √{wrong}: {S.annualize_vol(r.std(), wrong):.1%})")

print("===== 片段 8：方差比 =====")
horizons = {"SPY": [5, 21, 63], "AAPL": [5, 21, 63], "BTC": [7, 30, 90]}
for k in rets:
    row = {h: round(S.variance_ratio(logs[k], h), 2) for h in horizons[k]}
    print(k, row)

print("===== 片段 9：波动率本身在变 =====")
table = pd.DataFrame({k: rets[k].groupby(rets[k].index.year).std() * math.sqrt(ppy[k]) for k in rets})
print((table * 100).round(1))
for k in rets:
    w = 30 if k == "BTC" else 21
    rv = S.realized_vol(rets[k], w, ppy[k])
    print(k, f"{w} 天滚动年化波动率：最低 {rv.min():.1%}（{rv.idxmin().date()}），最高 {rv.max():.1%}（{rv.idxmax().date()}），中位数 {rv.median():.1%}")

print("===== 片段 10：肥尾 =====")
for k, r in rets.items():
    print(k)
    print(S.tail_table(r).round({"正态预期天数": 2, "实际 ÷ 预期": 1}))

print("===== 片段 11：几年一次 =====")
th = {"SPY": [-0.03, -0.05, -0.07], "AAPL": [-0.05, -0.08, -0.10], "BTC": [-0.10, -0.15, -0.20]}
for k, r in rets.items():
    print(k)
    print(S.threshold_table(r, th[k], ppy[k]).round(2))

print("===== 片段 12：偏度与峰度 =====")
for k, r in rets.items():
    top = r.abs().idxmax()
    print(f"{k:4s} 偏度 {r.skew():.2f}  超额峰度 {r.kurt():.2f}  去掉绝对值最大的一天（{top.date()}，{r[top]:.2%}）后 {r.drop(top).kurt():.2f}")

print("===== 片段 13：按近期波动率标准化 =====")
for k, r in rets.items():
    z = S.standardize(r, 20)
    full = S.tail_table(r, ks=[3, 4])["实际天数"].tolist()
    st = S.tail_table(z, ks=[3, 4])["实际天数"].tolist()
    print(f"{k:4s} 超额峰度 {r.kurt():5.2f} → {z.kurt():5.2f}   超过 3σ/4σ 的天数 {full} → {st}")
    for day in z.abs().nlargest(3).index:
        print(f"     {day.date()}  收益率 {r[day]:7.2%}  前 20 天波动率 {r[:day].iloc[-21:-1].std():.2%}  倍数 {z[day]:6.1f}")

print("===== 片段 14：最差 1% 的日子 =====")
for k, r in rets.items():
    q, es = S.tail_loss(r, 0.01)
    nq, nes = S.normal_tail_loss(r, 0.01)
    q5, _ = S.tail_loss(r, 0.05)
    nq5, _ = S.normal_tail_loss(r, 0.05)
    print(f"{k:4s} 1% 分界线 实际 {q:.2%} 正态 {nq:.2%} | 尾部平均 实际 {es:.2%} 正态 {nes:.2%} | 5% 分界线 实际 {q5:.2%} 正态 {nq5:.2%}")

print("===== 片段 15：自相关 =====")
for k, r in rets.items():
    print(k, "±", round(S.autocorr_band(len(r)), 3))
    print("  收益率    ", S.autocorr(r, [1, 2, 3, 4, 5]).round(3).tolist())
    print("  收益率绝对值", S.autocorr(r.abs(), [1, 5, 20, 60, 120]).round(3).tolist())

print("===== 片段 16：一阶自相关按年拆开 =====")
by_year = pd.DataFrame({k: r.groupby(r.index.year).apply(lambda s: S.autocorr(s, [1]).loc[1]) for k, r in rets.items()})
print(by_year.round(2))
for k, r in rets.items():
    no2020 = r[r.index.year != 2020]
    print(f"{k:4s} 全部 {S.autocorr(r, [1]).loc[1]:.3f}  去掉 2020 年 {S.autocorr(no2020, [1]).loc[1]:.3f}  界限 ±{S.autocorr_band(len(no2020)):.3f}")

print("===== 片段 17：打乱检验 =====")
lag1 = lambda s: S.autocorr(s, [1]).loc[1]
for k, r in rets.items():
    for label, x in [("全部", r), ("去掉 2020", r[r.index.year != 2020])]:
        res = S.shuffle_test(x, lag1, n=1000, seed=0)
        print(f"{k:4s} {label:6s} 实际 {res['实际值']:6.3f}  打乱后 95% 范围 [{res['打乱后 2.5% 分位']:.3f}, {res['打乱后 97.5% 分位']:.3f}]  比例 {res['比例']:.1%}")

print("===== 片段 18：价格不平稳，收益率近似平稳 =====")
b = btc["close"]
yearly = pd.DataFrame({
    "价格均值": b.groupby(b.index.year).mean(),
    "价格标准差": b.groupby(b.index.year).std(),
    "收益率均值%": rets["BTC"].groupby(rets["BTC"].index.year).mean() * 100,
    "收益率标准差%": rets["BTC"].groupby(rets["BTC"].index.year).std() * 100,
})
print(yearly.round(2))

print("===== 片段 19：价格的相关性和收益率的相关性 =====")
btc_day = b.copy()
btc_day.index = btc_day.index.tz_localize(None)            # 用 BTC 在 UTC 零点的收盘价，对齐到美股日期
both = pd.DataFrame({"SPY": spy["close"], "BTC": btc_day}).dropna()
print("共同日期", len(both))
print("价格相关系数", round(both["SPY"].corr(both["BTC"]), 2), " 收益率相关系数", round(both.pct_change()["SPY"].corr(both.pct_change()["BTC"]), 2))
for y in [2025, 2026]:
    part = both[both.index.year == y]
    print(y, "价格", round(part["SPY"].corr(part["BTC"]), 2), "收益率", round(part.pct_change()["SPY"].corr(part.pct_change()["BTC"]), 2))

rng = np.random.default_rng(42)
level_corr, ret_corr = [], []
for _ in range(1000):
    a, bb = rng.normal(0, 0.01, (2, 2500))                 # 两串互相独立的日收益率
    pa, pb = 100 * np.exp(np.cumsum(a)), 100 * np.exp(np.cumsum(bb))
    level_corr.append(np.corrcoef(pa, pb)[0, 1])
    ret_corr.append(np.corrcoef(a, bb)[0, 1])
level_corr, ret_corr = np.abs(level_corr), np.abs(ret_corr)
print(f"1000 对独立随机游走：价格相关系数绝对值 > 0.5 的比例 {np.mean(level_corr > 0.5):.1%}，> 0.8 的比例 {np.mean(level_corr > 0.8):.1%}")
print(f"                     收益率相关系数绝对值最大 {ret_corr.max():.3f}")

print("===== 片段 20：统计档案 =====")
profile = pd.DataFrame({k: S.describe(r, ppy[k]) for k, r in rets.items()})
print(profile.round(4))
