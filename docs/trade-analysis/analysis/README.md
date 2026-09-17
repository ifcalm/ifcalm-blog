# 正文数字的核对脚本

正文里每个统计数字的来源。数据放在 `data/` 下（不入库），从 `data.binance.vision` 下载：

- `data/1d/BTCUSDT-1d-YYYY-MM.zip`：spot/monthly/klines/BTCUSDT/1d，2017-08 至 2026-08
- `data/1m/BTCUSDT-1m-YYYY-MM.zip`：spot/monthly/klines/BTCUSDT/1m，2020-03、2021-02、2021-05、2025-01 至 2025-12
- `data/um1m/BTCUSDT-1m-2021-05.zip`：futures/um/monthly/klines/BTCUSDT/1m

⚠️ Binance 现货数据从 2025-01-01 起时间戳是**微秒**，之前是毫秒。`load.py` 已处理。

第 2 篇额外用到：

- `data/um1m/BTCUSDT-1m-2025-10.zip`：futures/um/monthly/klines/BTCUSDT/1m
- `data/um1d/BTCUSDT-1d-2025-MM.zip`：futures/um/monthly/klines/BTCUSDT/1d，2025 全年
- `data/metrics/BTCUSDT-metrics-2025-10-DD.zip`：futures/um/daily/metrics/BTCUSDT，10-06 至 10-14
- `data/us/spy.json`、`data/us/tsla.json`：`https://api.nasdaq.com/api/quote/{SYM}/historical?assetclass={etf|stocks}&fromdate=2016-01-01&todate=2026-09-15&limit=9999`（需带浏览器 User-Agent；只能回溯约 10 年；价格和成交量已按拆股调整）

⚠️ Stooq 现在有 JS 验证，脚本无法下载；Yahoo 返回 Too Many Requests。美股日线暂用 Nasdaq 接口。

第 3 篇：`03_data.py` 就是正文里的代码片段，依赖 `docs/trade-analysis/talab/talab/data.py`（运行时 `PYTHONPATH=docs/trade-analysis/talab`）。另外用到 Coinbase 公开 K 线接口 `https://api.exchange.coinbase.com/products/{BTC-USD|USDT-USD}/candles?granularity=60&start=…&end=…` 做交叉核对（2025-10-10 20:40–23:00、2021-01-04 10:10–10:30、2019-10-26 00:30–00:55、2019-05-15 02:50–07:00）。`exchange_calendars` 提供纽交所交易日历。

第 4 篇：`04_lab.py` 是正文代码片段，`04_figures.py` 生成 `static/images/trade-analysis/04/` 下的图（`python 04_figures.py <输出目录>`）。两者都在 talab 项目根目录、`pip install -e .` 之后运行。第 4 篇起 talab 是完整项目：`docs/trade-analysis/talab/`（pyproject、requirements、tests、scripts），`pytest -q` 应为 15 passed。

第 5 篇：`05_stats.py` 是正文代码片段（输出与正文逐行核对过），`05_figures.py` 生成 `static/images/trade-analysis/05/` 下的图。新增模块 `talab/stats.py` 和 `tests/test_stats.py`，`pytest -q` 应为 27 passed。不需要新数据。注意：SPY 删除 2026-04-20 填充行；SPY 没有分红数据（Nasdaq 分红接口不支持非 Nasdaq 上市的 ETF），收益率只含拆股调整；AAPL 用拆股 + 分红调整后的收盘价。决策点事件（Celsius 暂停提款）、标准化后最极端的日子（SPY 2018-10-10 / 2024-12-18 / 2025-10-10，AAPL 2017-02-01 / 2024-06-11 / 2018-08-01，BTC 2019-04-02 / 2018-11-14）已查证新闻报道。

第 6 篇：`06_bars.py` 是正文代码片段（输出与正文逐行核对过），`06_figures.py` 生成 `static/images/trade-analysis/06/` 下的图。新增模块 `talab/bars.py` 和 `tests/test_bars.py`，`pytest -q` 应为 37 passed。需要 BTC 全部 1 分钟数据（`fetch_course_data.py` 已包含），加载约 2.4 秒、约 380 MB 内存。SPY、AAPL 用 Nasdaq 拆股调整价（不做分红调整）。决策点两根 K 线：A = 2026-07-01（2026 熊市最低点 57,800.19），B = 2019-07-09。

第 7 篇：`07_timeframes.py` 是正文代码片段（输出与正文逐行核对过），`07_figures.py` 生成 `static/images/trade-analysis/07/` 下的图。新增模块 `talab/timeframes.py` 和 `tests/test_timeframes.py`，`pytest -q` 应为 43 passed。额外下载官方 BTCUSDT 4h（2017-08 至 2026-08）和 1w（月度文件只发布到 2026-06），只用来核对合成结果。决策点：2025-10-30 12:00 那根 4 小时线收盘跌破 7 天最低价，周线（10-20 这一周）在 20 周均线上方。Elder 三重滤网出处：Futures 杂志 1986 年 4 月。

第 8 篇：`08_structure.py` 是正文代码片段（输出与正文逐行核对过），`08_figures.py` 生成 `static/images/trade-analysis/08/` 下的图。新增模块 `talab/structure.py`（分形、ZigZag、趋势状态、突破版状态、效率比、回归斜率、真实波幅、方向运动、Wilder 平滑、ADX）和 `tests/test_structure.py`，`pytest -q` 应为 54 passed。不需要新数据。打乱检验共约 7,000 次，脚本运行约 20 秒。决策点：2024-10-16 收盘 67,620.01，ZigZag（收盘价）5% 上升、10% 震荡（低点只低 55.84 美元）、20% 下降。ADX 与 TA-Lib 0.8.0 对比过：初始化方式不同，2018-06 起差距小于 1e-7。出处已查证：分形（Bill Williams《Trading Chaos》1995）、效率比（Perry Kaufman《Smarter Trading》1995）、ZigZag 的来源（Arthur Merrill《Filtered Waves》1977）、ADX（Wilder 1978）。

第 9 篇：`09_levels.py` 是正文代码片段（输出与正文逐行核对过，运行约 2 分钟，主要是打乱检验），`09_figures.py` 生成 `static/images/trade-analysis/09/` 下的图。`talab/structure.py` 新增第四、五部分（cluster_levels、level_tests、gaps、first_reach），`tests/test_structure.py` 新增 5 个测试，`pytest -q` 应为 59 passed。不需要新数据（用到 BTC 全部 1 分钟线）。决策点：2026-06-03 03:00 那根 1 小时线最低 65,426.34，第四次进入 65,000～65,618.49（2 月 12 日、3 月 8 日、3 月 29 日三个分形低点）。CME 缺口：用 Binance 现货 1 分钟线代替期货价格，周五 16:00（芝加哥时间）到周日 17:00，周五休市用 `exchange_calendars` 的 CMES 日历找前一个交易日；CME 加密期货自 2026-05-29 起 24/7 交易（CME 新闻稿），所以只算到 2026-05-22 那个周末；CME 比特币期货 2017-12-17 开始交易。出处已查证：Osler 2000（纽约联储 Economic Policy Review）、Osler 2003（Journal of Finance 58(5)）。

第 10 篇：`10_volume.py` 是正文代码片段（输出与正文逐行核对过），`10_figures.py` 生成 `static/images/trade-analysis/10/` 下的图（先运行 `10_volume.py`，它会下载 BTCUSDT U 本位永续合约日线，月度文件从 2020-01 开始）。新增模块 `talab/indicators.py`（relative_volume、typical_price、vwap、anchored_vwap、volume_profile、value_area）和 `tests/test_indicators.py`，`pytest -q` 应为 65 passed。决策点改为 BTC 2025-12-17 15:00 那根 1 小时线（Yahoo 日内接口 429、Nasdaq 只有当天分时，没有免费美股日内历史数据）。SPY 2026-04-17 成交量 9,999,999 设为缺失。出处已查证：Berkowitz、Logue、Noser 1988（Journal of Finance，VWAP 作为执行基准）；Bitwise 2019 年 3 月向 SEC 提交的材料（约 95% 报告成交量虚假）；Bloomberg 报道 2025 年 1 月美股场外成交占 51.8%；Binance BTC 现货交易对零手续费 2022-07-08 至 2023-03-22；Steidlmayer 的 Market Profile 1985 年由 CBOT 推出；Brian Shannon 推广锚定 VWAP。⚠️ 写作时发现 volume_profile 第一版用小数价格做分组键会悄悄丢成交量，已改为整数箱号并核对全部 3,302 天成交量守恒。

第 11 篇：`11_price_action.py` 是正文代码片段（输出与正文逐行核对过，运行约 3.5 分钟，主要是 4 小时线和 1 小时线的打乱检验），`11_figures.py` 生成 `static/images/trade-analysis/11/` 下的图（约 1 分钟），`11_replay.py` 是给读者练习用的逐根回放工具（交互式，输入 l / s / 回车 / q）。`11_spy_hand_labels.csv` 是实验一的示范手工标注：写作时在运行分类器之前，只看一张没有标记的 SPY 日线图画的，之后没有改过。`talab/structure.py` 新增第六、七部分（market_state、entries、first_passage、agreement、segments_to_labels），`tests/test_structure.py` 新增 7 个测试，`pytest -q` 应为 72 passed。不需要新数据（4 小时线、1 小时线由 1 分钟线合成）。决策点：AAPL 2021-08-02 至 2022-08-31（拆股和分红调整后，第一根收盘换算成 100，系数 0.7056），四个决定在 2022-01-11、03-29、03-31、06-03。⚠️ 写作时发现：突破信号的第一版每次收盘越过都算一次，BTC 日线 3,987.60 在 2019-03-16 至 03-27 被记了 4 次突破、3 次失败突破，已改为每个价位只算第一次。「过渡之后下一段是震荡」92 段里 91 段，例外是 BTC 2022-01-04。

第 12 篇：`12_moving_averages.py` 是正文代码片段（输出与正文逐行核对过，运行约 3 秒），`12_figures.py` 生成 `static/images/trade-analysis/12/` 下的图。`talab/indicators.py` 新增第四部分（sma、wma、ema、average_lag、cross_above、cross_below、bias），`tests/test_indicators.py` 新增 24 个测试（15 个和 TA-Lib 对账），`requirements.txt` 加入 `TA-Lib==0.8.0`（pip 可直接安装，自带 C 库）；`pytest -q` 应为 96 passed，没有 TA-Lib 时 81 passed、15 skipped。与 TA-Lib 对比：SMA/EMA/WMA 各周期绝对误差小于 1e-9，预热期和开头 NaN 的处理一致。不需要新数据。决策点：SPY 最近一次金叉 2025-07-01（SMA50 583.10 上穿 SMA200 582.04），此前 04-08 最低收盘 496.48，04-14 死叉。出处已查证：William Gordon《The Stock Market Indicators》（1968）用道琼斯检验 200 日均线；Richard Donchian 20 世纪 50 年代讨论 5 日和 20 日均线交叉。主线策略 v0（50/200 SMA，下一根开盘成交）年化：SPY 8.5%（买入持有 13.2%）、AAPL 15.5%（28.4%）、BTC 19.1%（25.3%）。

第 13 篇：`13_macd.py` 是正文代码片段（输出与正文逐行核对过，运行约 20 秒），`13_figures.py` 生成 `static/images/trade-analysis/13/` 下的图。`talab/indicators.py` 新增第五部分（macd、ema_response、divergences），`tests/test_indicators.py` 新增 10 个测试，`pytest -q` 应为 106 passed（装了 TA-Lib）。MACD 与 TA-Lib 0.8.0 一致：TA-Lib 让快 EMA 和慢 EMA 同一根开始（初始值用第 slow-fast+1 到 slow 个价格的平均），三列都从第 slow+signal-1 根出现；简单相减的写法在 BTC 日线上开头差 23 美元、200 根才对上。频率响应：MACD 线峰值周期 55 根（功率减半 22–141），柱 29 根（12–61），和正弦波最小二乘实测一致。背离检验（ZigZag 阈值取第 11 篇的一半）：两种写法 × 5 组数据 × 顶底 = 20 次，2 次 p<0.05，都在 BTC 1 小时线。出处已查证：Gerald Appel 20 世纪 70 年代末提出 MACD；Thomas Aspray 1986 年前后加上柱状图。
