"""番外篇正文里的代码片段（在 talab 项目根目录运行）。

数据：`36_download.py` 下载的 BTCUSDT 永续盘口深度（2023-01-01 起）+ 第 28 篇的
最优买卖报价（只有 2023-05-16 到 2024-03-30）+ 第 22 篇下载的 UM 1 分钟线。
"""
import glob

import numpy as np
import pandas as pd
from talab import book as B, data as D, sessions as SE

pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)
CRASH = pd.Timestamp("2023-08-17 21:44", tz="UTC")
LEVEL = 1.0

depth = D.load_binance_book_depth(sorted(glob.glob("data/binance/um/BTCUSDT/bookDepth-30s/*.csv.gz")))
ticker = D.load_binance_book_ticker(sorted(glob.glob("data/binance/um/BTCUSDT/bookTicker-1m/*.csv.gz")))
um = D.load_binance_klines(sorted(glob.glob("data/binance/um/BTCUSDT/1m/*.zip"))).loc["2023-01-01":"2026-08-31"]
um["主动卖出"] = um["quote_volume"] - um["taker_buy_quote"]
book = B.sides(depth, LEVEL)


def runs(moments: pd.DatetimeIndex, gap: str = "6h") -> np.ndarray:
    """把相邻不超过 `gap` 的时刻并成一段，返回每个时刻属于第几段。

    ⚠️ 合并是第 25 篇定下来的口径：相邻分钟的事件窗口几乎完全重叠，
    不合并的话同一次崩盘会被数很多遍。
    """
    if not len(moments):
        return np.array([], dtype=int)
    # ⚠️ 别用 `np.diff(moments.asi8) > pd.Timedelta(gap).value`：这里的索引是**微秒**精度，
    # 而 `Timedelta.value` 永远是**纳秒**，两边差一千倍，结果是所有事件被并成一段。
    apart = (moments[1:] - moments[:-1]) > pd.Timedelta(gap)
    return np.concatenate([[0], np.cumsum(np.asarray(apart, dtype=int))])


def pick_per_run(moments: pd.DatetimeIndex, weight: np.ndarray | None = None,
                 gap: str = "6h") -> pd.DatetimeIndex:
    """每一段只留一个时刻：`weight` 最小的那个（不给就取段首）。⚠️ 用位置索引，免得丢掉时区。"""
    moments = pd.DatetimeIndex(moments).sort_values()
    if not len(moments):
        return moments
    label = runs(moments, gap)
    keep = []
    for value in np.unique(label):
        inside = np.flatnonzero(label == value)
        keep.append(inside[0] if weight is None else inside[int(np.argmin(weight[inside]))])
    return moments[np.array(keep)]


def events(threshold: float = -0.05, window: int = 60, gap: str = "6h") -> pd.DatetimeIndex:
    """崩盘时刻：`window` 分钟跌幅超过 `threshold`，连着的合并成一段、只取最狠的那一分钟。"""
    drop = um["close"].pct_change(window)
    hit = drop[drop <= threshold]
    return pick_per_run(hit.index, hit.to_numpy(float), gap)


print("===== 片段 1：2023 年 8 月 17 日 21:44 =====")
window = ticker.loc["2023-08-17 21:40":"2023-08-17 21:50"]
print(window[["价差", "最宽价差", "买一量", "卖一量", "中间价"]].round(3).to_string())
same_day = ticker.loc["2023-08-17"]
print(f"\n当天价差中位 {same_day['价差'].median():.4f} 个基点（第 28 篇量到的全样本中位是 0.0328），"
      f"而 21:45 那一分钟最宽到过 {same_day['最宽价差'].max():.2f} 个基点")
print("\n⚠️ 顺带和第 28 篇那个 161.5 对一下账（它是「那一分钟里**最宽的一次报价**」，不是分钟平均）：")
for day in ("2023-08-17", "2023-10-23"):
    one = ticker.loc[day]
    fall = um["close"].pct_change(60).loc[day].min()
    print(f"  {day}：60 分钟最大跌幅 {fall:+.2%}，最宽的一次报价 {one['最宽价差'].max():.2f} 基点，"
          f"而分钟平均价差最大只有 {one['价差'].max():.2f}")
print("  两天比下来，光看价差连哪一天更糟都排不出来。")
print("\n第 28 篇到这里就没有下文了：价差只是柜台前排队的长度。柜台后面还有多少钱？")

print("===== 片段 2：揭晓 =====")
shown = book.loc[CRASH - pd.Timedelta(minutes=5):CRASH + pd.Timedelta(minutes=2)]
print(shown.assign(买侧=lambda t: t["买侧"].round(0), 卖侧=lambda t: t["卖侧"].round(0),
                   合计=lambda t: t["合计"].round(0)).round(3).to_string())
normal = book.loc[CRASH - pd.Timedelta(hours=24):CRASH - pd.Timedelta(minutes=30), "买侧"].median()
peak = book.loc[CRASH - pd.Timedelta(minutes=5):CRASH, "买侧"].max()
bottom_at = book.loc[CRASH:CRASH + pd.Timedelta(minutes=5), "买侧"].idxmin()
bottom = book.loc[bottom_at, "买侧"]
print(f"\n崩盘前 24 小时，买侧深度中位 {normal:,.0f} 美元")
print(f"21:41 那一张快照 {peak:,.0f}（比平常还厚 {peak / normal - 1:+.0%}）")
print(f"{bottom_at:%H:%M:%S} 只剩 {bottom:,.0f}——{peak - bottom:,.0f} 美元在 "
      f"{(bottom_at - book.loc[:CRASH - pd.Timedelta(minutes=2)].index[-1]).seconds // 60} 分钟里消失了"
      f"（{bottom / peak - 1:+.1%}）")

print("===== 片段 3：那三分钟砸下来多少钱 =====")
flow = um.loc[CRASH - pd.Timedelta(minutes=3):CRASH + pd.Timedelta(minutes=2)]
print(flow[["open", "low", "close", "quote_volume", "taker_buy_quote", "主动卖出"]].round(0).to_string())
three = um.loc[CRASH - pd.Timedelta(minutes=2):CRASH, "主动卖出"].sum()
print(f"\n21:42–21:44 三分钟，主动卖出合计 {three:,.0f} 美元")
print(f"而崩盘前现价下方 1% 以内一共只有 {normal:,.0f}——**{three / normal:.1f} 倍**")
print(f"单是 21:44 这一分钟的 {um.loc[CRASH, '主动卖出']:,.0f}，就已经是它的 "
      f"{um.loc[CRASH, '主动卖出'] / normal:.2f} 倍")

print("===== 片段 4：这份数据能答什么、答不了什么 =====")
print(f"盘口深度快照：{len(depth):,} 张，{depth.index[0].date()} → {depth.index[-1].date()}，"
      f"{len(depth) / B.DAY:.0f} 天")
levels = pd.DataFrame({"有值的快照比例": depth.notna().mean(),
                       "中位金额（美元）": depth.median().round(0)})
print(levels.to_string())
narrow = depth["-0.2%"].notna()
print(f"\n⚠️ ±0.2% 那两档只从 {depth.index[narrow][0].date()} 才开始有值，"
      f"{int(narrow.sum() / B.DAY)} 天——所以全篇用 ±1%。")
print(f"⚠️ 第 28 篇那套价差数据只有 {ticker.index[0].date()} → {ticker.index[-1].date()} 里的 "
      f"{ticker.index.normalize().nunique()} 天（Binance 之后不再公开 bookTicker），"
      f"所以价差和深度**配得上对的只有这几天**。")

print("===== 片段 5：不是一次特例 =====")
crashes = events()
print(f"2023-01-01 起，60 分钟跌幅超过 5% 的崩盘共 {len(crashes)} 次：")
table = pd.DataFrame({
    "时刻": crashes,
    "60 分钟跌幅": [um["close"].pct_change(60).loc[t] for t in crashes],
    "那一分钟主动卖出": [um.loc[t, "主动卖出"] for t in crashes],
})
depth_at = book["买侧"].reindex(crashes, method="nearest")
before = pd.Series([book.loc[t - pd.Timedelta(hours=24):t - pd.Timedelta(minutes=30), "买侧"].median()
                    for t in crashes], index=crashes)
after = pd.Series([book.loc[t:t + pd.Timedelta(minutes=10), "买侧"].min() for t in crashes], index=crashes)
table["崩盘前 24 小时买侧"] = before.to_numpy()
table["崩盘后 10 分钟最低"] = after.to_numpy()
table["掉了多少"] = (after / before - 1).to_numpy()
print(table.assign(时刻=lambda t: t["时刻"].dt.strftime("%Y-%m-%d %H:%M")).round(4).to_string(index=False))
print(f"\n{len(table)} 次里，买侧深度掉幅的中位数是 {table['掉了多少'].median():.1%}，"
      f"最狠 {table['掉了多少'].min():.1%}，最轻 {table['掉了多少'].max():.1%}")

print("===== 片段 6：和什么比 =====")
sells = um["主动卖出"]
drop60 = um["close"].pct_change(60)
quiet = pick_per_run(um.index[(drop60.abs() < 0.01) & (sells >= sells.quantile(0.999))])
print(f"对照组：主动卖出额同样在最大的 0.1% 里，但 60 分钟涨跌幅在 ±1% 以内的时刻，共 {len(quiet)} 个")
rows = []
for label, moments in [("崩盘", crashes), ("对照：同样大的卖单，但价格没崩", quiet)]:
    base = pd.Series([book.loc[t - pd.Timedelta(hours=24):t - pd.Timedelta(minutes=30), "买侧"].median()
                      for t in moments], index=moments)
    low = pd.Series([book.loc[t:t + pd.Timedelta(minutes=10), "买侧"].min() for t in moments], index=moments)
    rows.append({"哪一组": label, "个数": len(moments),
                 "那一分钟主动卖出（中位）": float(sells.reindex(moments).median()),
                 "买侧深度掉幅（中位）": float((low / base - 1).median()),
                 "买侧深度掉幅（最狠）": float((low / base - 1).min())})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 7：价差和深度，恢复得一样快吗 =====")
WINDOWS = [(10, "10 分钟后"), (60, "1 小时后"), (240, "4 小时后"), (1440, "24 小时后")]


def level_after(values: pd.Series, moments, minutes: int, before: int = 60) -> float:
    """事件之后第 `minutes` 分钟前后那一段，相对事件**前** `before` 分钟的中位水平是几成。

    ⚠️ 用「那一段的中位水平」而不是「第一次碰到九成是什么时候」：深度抖得厉害，
    碰一下就记成恢复，会把一条一直趴在地上的曲线记成「三分钟就回来了」。
    """
    ratios = []
    for moment in moments:
        base = values.loc[moment - pd.Timedelta(minutes=before):moment].median()
        chunk = values.loc[moment + pd.Timedelta(minutes=minutes * 0.8):
                           moment + pd.Timedelta(minutes=minutes)].median()
        if base and base > 0 and not np.isnan(chunk):
            ratios.append(chunk / base)
    return float(np.median(ratios)) if ratios else np.nan


spread_events = [t for t in crashes if t in ticker.index]
print(f"价差和深度都有数据的崩盘：{len(spread_events)} 次（bookTicker 只覆盖 11 天）")
rows = []
for minutes, label in WINDOWS:
    rows.append({
        "什么时候": label,
        "价差（越小越好，1 = 回到崩盘前）": level_after(ticker["价差"], spread_events, minutes),
        "买侧深度（越大越好，1 = 回到崩盘前）": level_after(book["买侧"], spread_events, minutes),
    })
print(pd.DataFrame(rows).round(3).to_string(index=False))
print("\n同样这几次崩盘、同样的口径：价差十分钟后还宽着，一小时基本回到崩盘前；"
      "买侧深度十分钟后只剩四分之三，一小时补到九成。")
print("⚠️ 只有 6 次事件，这张表的每个数都很吵（4 小时那一行价差反而比崩盘前还窄）——"
      "它只够说明「两者的时间常数不一样」，不够说明差多少。下一节用全部 22 次重做。")

print("===== 片段 8：22 次崩盘，深度多久才补回来 =====")
rows = []
for minutes, label in WINDOWS:
    rows.append({"什么时候": label,
                 "买侧深度占崩盘前": level_after(book["买侧"], crashes, minutes),
                 "两侧合计占崩盘前": level_after(book["合计"], crashes, minutes),
                 "期间主动卖出（中位，美元）": float(np.median(
                     [um.loc[t:t + pd.Timedelta(minutes=minutes), "主动卖出"].sum() for t in crashes]))})
print(pd.DataFrame(rows).round(4).to_string(index=False))
first = B.recovery(book["买侧"], crashes, horizon=B.DAY * 2, fraction=0.9,
                   before=120, trough_within=120)
print(f"\n⚠️ 换成「第一次碰到崩盘前的九成是什么时候」，中位只有 "
      f"{first['几分钟后回来'].median():.0f} 分钟，{int(first['几分钟后回来'].isna().sum())} 次两天都没碰到——"
      "但那只是碰一下。深度抖得厉害，碰一下不等于补回来了，上面那张表才是持续水平。")
print(f"最低点中位只剩崩盘前的 {first['最低点占事件前'].median():.1%}，"
      f"最低点出现在崩盘后 {first['最低点在几分钟后'].median():.1f} 分钟")
print("\n所以第 28 篇那句话的深度版本是：**形状一样，幅度大得多、窗口长得多**。"
      "价差在分钟平均上只放大到一两倍、一小时就回去了；"
      "深度直接少掉一半，要一个小时才补到八成。")

print("===== 片段 9：崩盘时盘口变陡了还是变平了 =====")
KEEP = [-20, -10, -5, -2, -1, 0, 1, 2, 5, 10, 20, 40]
steep = B.slope(depth, near=1.0, far=5.0)
print("（一行是一个偏移，单位是 30 秒快照；0 就是崩盘那一刻）")
print(SE.event_study(steep, crashes, before=20, after=40).loc[KEEP].round(3).to_string())

print("===== 片段 10：「买盘厚所以会涨」 =====")
tilt = B.imbalance(depth, LEVEL)
print("崩盘之前那几张快照，盘口是什么样的：")
print(SE.event_study(tilt, crashes, before=20, after=20).loc[[k for k in KEEP if abs(k) <= 20]]
      .round(4).to_string())
print(f"\n⚠️ 决策点那一天，21:41 的不对称是 "
      f"{tilt.loc[CRASH - pd.Timedelta(minutes=3):CRASH - pd.Timedelta(minutes=2)].max():+.3f}"
      f"——买盘比卖盘厚一半还多，三分钟之后价格跌了 10%")

print("===== 片段 11：不对称到底能不能预测 =====")
minutes = book["买侧"].resample("1min").last().reindex(um.index)
tilt_min = tilt.resample("1min").last().reindex(um.index).shift(1)   # 只用上一分钟收盘时的盘口
rows = []
rng = np.random.default_rng(36)


def standardized_ranks(values: pd.Series) -> np.ndarray:
    """先把秩标准化，之后打乱只要乘一遍加一遍——秩相关就是标准化秩的内积平均。"""
    ranked = values.rank().to_numpy(float)
    return (ranked - ranked.mean()) / ranked.std()


for horizon in (1, 5, 30, 240):
    forward = um["close"].pct_change(horizon).shift(-horizon)
    both = pd.DataFrame({"不对称": tilt_min, "之后": forward}).dropna()
    left, right = standardized_ranks(both["不对称"]), standardized_ranks(both["之后"])
    real = float((left * right).mean())
    shuffled = np.array([float((rng.permutation(left) * right).mean()) for _ in range(200)])
    cutoff = float(np.quantile(np.abs(shuffled), 0.95))
    rows.append({"往后看几分钟": horizon, "样本量": len(both), "秩相关": real,
                 "打乱 200 次的 95% 分位": cutoff, "比打乱的极端吗": abs(real) > cutoff,
                 "秩相关的平方": real ** 2})
tilt_power = pd.DataFrame(rows)
print(tilt_power.round(5).to_string(index=False))
print("\n⚠️ 四个窗口全部「比打乱的极端」——但样本有 190 万分钟，"
      f"秩相关 {tilt_power['秩相关'].max():.3f} 的平方只有 {tilt_power['秩相关的平方'].max():.5f}。"
      "**显著和有用是两件事**（第 19 篇量过同一件事的另一面：不显著也不等于没有）。")

print("===== 片段 12：价差和深度，哪个更像「流动性」 =====")
# ⚠️ 三个索引的时间精度不一样，直接 concat 会触发 pandas 的排序警告；先对齐到分钟线的索引
grid_index = um.index
paired = pd.DataFrame({"价差": ticker["价差"].reindex(grid_index),
                       "买侧深度": book["买侧"].resample("1min").last().reindex(grid_index),
                       "两侧合计": book["合计"].resample("1min").last().reindex(grid_index),
                       "主动卖出": um["主动卖出"]}).dropna()
print(f"两套数据都有的分钟：{len(paired):,}")
print(paired.corr(method="spearman").round(3).to_string())
print(f"\n价差中位 {paired['价差'].median():.4f} 基点、99% 分位 {paired['价差'].quantile(0.99):.3f}、"
      f"最大 {paired['价差'].max():.1f}")
print(f"深度中位 {paired['买侧深度'].median():,.0f} 美元、1% 分位 {paired['买侧深度'].quantile(0.01):,.0f}、"
      f"最小 {paired['买侧深度'].min():,.0f}")
print(f"价差从中位到最大放大了 {paired['价差'].max() / paired['价差'].median():,.0f} 倍，"
      f"深度从中位到最小缩小到 {paired['买侧深度'].min() / paired['买侧深度'].median():.3%}")

print("===== 片段 13：这对第 22 篇的止损意味着什么 =====")
rows = []
for size in (100_000, 1_000_000, 10_000_000, 50_000_000):
    share = size / book["买侧"]
    rows.append({"一张市价卖单（美元）": size,
                 "占现价下方 1% 承接力的比例（平常中位）": float(share.median()),
                 "崩盘那十分钟的中位": float(pd.Series(
                     [size / book.loc[t:t + pd.Timedelta(minutes=10), "买侧"].min() for t in crashes]).median()),
                 "平常打穿 1% 的比例": float((share > 1).mean())})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 14：这对第 34 篇的拆单意味着什么 =====")
rows = []
for risk in (0.10,):
    for equity in (1e5, 1e6, 1e7, 1e8):
        position = equity * min(1.0, risk / 0.15)          # 第 34 篇那条主线 v4 的仓位
        rows.append({"账户（美元）": equity, "一笔仓位": position,
                     "占平常 1% 承接力": float(position / book["买侧"].median()),
                     "占崩盘时 1% 承接力（中位）": float(position / pd.Series(
                         [book.loc[t:t + pd.Timedelta(minutes=10), "买侧"].min() for t in crashes]).median())})
print(pd.DataFrame(rows).round(4).to_string(index=False))

print("===== 片段 15：三年下来，市场变深了吗 =====")
yearly = book.resample("YE").median()
yearly["合计（百万美元）"] = (yearly["合计"] / 1e6).round(1)
print(yearly[["买侧", "卖侧", "合计（百万美元）"]].assign(
    买侧=lambda t: t["买侧"].round(0), 卖侧=lambda t: t["卖侧"].round(0)).to_string())
crash_by_year = pd.Series([len(pd.DatetimeIndex([t for t in crashes if t.year == year]))
                           for year in sorted(um.index.year.unique())],
                          index=sorted(um.index.year.unique()), name="崩盘次数")
print()
print(crash_by_year.to_string())
