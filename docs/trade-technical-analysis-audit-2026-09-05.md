# 交易技术分析内容审查

审查日期：2026-09-05。审查对象：`content/posts/trade` 中与技术分析、信号、执行和策略验证有关的内容。

**结论：需要实质性修订。主要问题不是少介绍了几个指标，而是把部分经验判断、统计近似和教学类比写成了恒等式或不可能性证明。** 这些错误沿着篇章引用进入了速查表，会影响读者的研究和风控决策。

本次重点阅读第 27、30–41、44、45 篇共 15 篇核心文章；核对第 7、15、26 篇相关论证，以及第 6、19、20、47 篇相关段落和术语表。全目录检索用于检查重复结论和缺漏；不代表已经逐项验证税务、法规、平台规则、链上协议或所有历史事件。没有运行真实行情策略回测，也没有据此认定某个策略有效。本次只新增审查报告，未改文章正文。

## 应当保留的内容

- OHLC 无法完整恢复盘中路径，同根止盈止损存在顺序歧义。
- 区分未完成 K 线与已完成 K 线，强调数据真实可得时点。
- 扣除费用、价差、滑点，检查幸存者偏差与参数搜索。
- 网格必须计入库存浮亏，挂单深度不等于成交承诺。
- 区分描述、交易规则和盈利证据，强调可复现与样本外验证。

以下 P1 表示应优先修正，可能直接改变研究结论或风险判断；P2 表示定义、条件或证据不足。它们是内容修订优先级，不是安全漏洞评级。

## 一、优先修正的明确错误

### 01 · P1：「没有增加原始数据」不等于「没有预测信息」

位置：[32-trading-signals.md:143](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/32-trading-signals.md:143)；同时影响第 27、34、35、37、40、47 篇和术语表。

确定性函数不会增加相对于完整输入的信息，但可以保留输入中与预测目标相关的部分。不能据此把所有纯价格信号直接否决。数据处理不等式是 `I(f(X);Y) ≤ I(X;Y)`，不是 `I(f(X);Y)=0`。如果历史价格本身具有条件预测力，特征提取并不会自动把它清零。

建议改成：**价格指标是历史数据的特征表示；是否具有增量预测价值，要相对于指定基准，在样本外、扣成本后检验。** 本文已引用的时间序列动量研究本身就是历史收益预测未来收益的研究，不能一面援引、一面用“纯价格”否决。[Moskowitz、Ooi、Pedersen 原研究](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum)

### 02 · P1：把 ATR、标准差列为“价格变换的例外”错误

位置：[27-reading-charts.md:350](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/27-reading-charts.md:350)；第 32、34 篇分类表同样受影响。

ATR 和标准差仍然是价格数据的确定性函数。方差可能包含“均值这个单独统计量”没有的信息，却不包含完整价格序列没有的信息。ATR 也不是二阶矩：它是 `max(H−L, |H−C前|, |L−C前|)` 的平滑，量纲是价格；方差才是平方量纲。

建议分开“数据来源”和“用途”，不要按一阶矩/二阶矩划分有无新信息。[Fidelity ATR 定义与算法](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/atr)

### 03 · P1：同源信号不必然高度相关，也不必然信息等价

位置：[27-reading-charts.md:254](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/27-reading-charts.md:254)、[32-trading-signals.md:129](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/32-trading-signals.md:129)；第 15 篇 POC、38 篇策略相关性、39 篇广度也重复此推断。

同一个随机变量的不同函数可以零相关：例如对称分布的 `X` 与 `X²`。不同窗口也可以捕捉不同时间尺度。同源足以提醒“不能默认独立”，不足以推出相关系数接近 1，更不足以推出两个特征等价。

应检验信号相关、持仓相关、收益相关，并做联合模型或过滤器的样本外增量检验；这三种相关性不是同一个量。

### 04 · P1：高低周期是单向聚合，不是信息恒等

位置：[27-reading-charts.md:181](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/27-reading-charts.md:181)、[15-orderflow-data.md:654](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/15-orderflow-data.md:654)。

12 根 5 分钟线可以在同源、同口径、对齐时聚合成 1 根小时线；小时线不能反推出这 12 根线。应该写“可聚合”，不应使用表示等价的符号论证信息相同。多个窗口方向可能冲突；联合事件概率既不能直接乘成 `0.05³`，也不能无依据指定为约 `0.05`。

保留“不应重复计算独立证据”的提醒；允许长周期条件与短周期触发产生可检验的增量价值。

### 05 · P1：均线平均滞后不能当作金叉延迟

位置：[27-reading-charts.md:291](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/27-reading-charts.md:291)。

SMA 的权重重心 `(n−1)/2` 与标准 EMA 的低频极限延迟相等，这个限定下的计算成立。但交叉时间是价格路径和两条滤波曲线共同决定的，不能说 20/60 金叉固定或平均迟到 29.5 根。

本次用同样的 100 根线性下跌前史，接斜率为 0.25、1、4 的上涨，SMA20/60 首次上穿分别在谷底后 **38、25、16 根**。这是反例校验，不是市场回测。应删除金叉固定延迟及下游“可事前算出入场晚多少”的推论。标题中的“EMA 更快是错的”也须保留“低频平均延迟”限定。

### 06 · P2：KDJ 范围和 RSI 的推理错误

位置：[27-reading-charts.md:306](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/27-reading-charts.md:306)。

常用 KDJ 中 K、D 通常在 0–100，**J=3K−2D 可以超界**。正文列的 KDJ 式子也只是 RSV 的核心比例，缺少 ×100、K/D 平滑、J 线和初始化。

“RSI 可以高位钝化”正确；“有界量不能表达无界过程，所以必然做反”不是有效证明，有界变换也可以表示无界变量。应区分 RSI 趋势过滤与超买反转两类规则，分别检验。[富途 KDJ 算法](https://www.futuhk.com/cn/en/support/topic1_149)

### 07 · P1：趋势和均值回归的偏度写反

位置：[30-trend-following.md:244](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/30-trend-following.md:244)、[36-left-right-side.md:81](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/36-left-right-side.md:81)；第 31 篇也写趋势收益左偏。

在文中所描述的分布下，平时小亏、偶尔巨赚是**右偏/正偏**；平时小赚、偶尔巨亏是**左偏/负偏**。第 10、20 篇部分表述反而是正确的，形成内部冲突。修正时应说明：这是典型形态，不是所有趋势或均值回归系统必然具有的偏度。

### 08 · P1：止损不保证凸性，也不保证损失硬下界

位置：[30-trend-following.md:68](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/30-trend-following.md:68)；传播到第 7、36、37、41 篇和术语表。

下有界、上无界不能推出函数凸；凸性也必须说明自变量、持有期和交易路径。带止损策略具有路径依赖，同一终点价格可以对应不同损益。跳空和滑点还可能突破预设损失。

Fung–Hsieh 用回望跨式期权**建模**趋势策略，不是证明每个止损策略等价于期权多头。高波动震荡同样可能令趋势策略亏损，不能从类比推出统一正 vega。入场也会影响收益分布，胜率并非只能由出场决定。[Fung–Hsieh 原研究](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=250542)

### 09 · P1：OI×价格四象限不是恒等关系

位置：[33-price-levels.md:249](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/33-price-levels.md:249)；第 34、44 篇援引。

双方开仓使 OI 增加，意味着同时新增多头和空头；双方平仓使 OI 减少。仅凭价格上涨/下跌不能唯一确定“新多主导”“新空主导”或“轧空”。美元名义 OI 还可能只因价格上涨而上升。

保留双方开平仓对 OI 的记账表；把四象限降级为**常见解释假说**，补主动方向、强平记录、单位和多空配对限制。[CME OI 统计口径](https://www.cmegroup.com/trading/about-volume.html)

### 10 · P1：形态确认不是无法修复的选择偏差

位置：[40-chart-patterns.md:163](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/40-chart-patterns.md:163)。

若在 t 时刻用已发生的颈线破位确认形态，在 t 之后交易，统计之后的全部收益，包括假突破亏损，**这可以检验**。错误的是把确认前的跌幅计入可交易收益，或事后只挑继续下跌的案例。不存在“必须把形态定义移到确认前”的普遍要求。

原文第三节承认机械识别可检验，第四节却否定确认后检验，二者冲突。建议分别写清：候选形态、确认时刻、首次可成交时刻、未来评价区间。[Lo、Mamaysky、Wang 原研究](https://www.nber.org/papers/w7613)

### 11 · P1：连续参数或多个参数不等于不可证伪

位置：[34-technical-analysis-map.md:209](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/34-technical-analysis-map.md:209)；第 37、40、47 篇重复。

普通线性回归的实数参数空间同样不可数，仍然可检验。必须区分参数个数、实际尝试次数、有效模型复杂度和没有固定规则的事后解释。ATR 也有窗口和平滑参数，深度也有价格带参数，并非“假设空间=1”。

应改为：自由选择增加过拟合风险，需要预先约定、正则化、搜索记录和独立验证；**不是逻辑上无法检验**。

第 32 篇“输出必须离散，否则不可检验”同样应修正。概率、预期收益或标准化分数都可以作为连续信号，按事先定义的目标评价；要形成完整策略，再补信号到仓位和退出的映射。信号预测评估不必强行先指定交易止损，策略损益评估则必须有完整交易规则。

### 12 · P1：过滤器判据漏掉标准差变化

位置：[32-trading-signals.md:198](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/32-trading-signals.md:198)；术语表同步。

在均值为正且使用同一简化 t 统计量时，保持 t 不降需要：

`μ后/μ前 ≥ (σ后/σ前) × √(N前/N后)`。

原文只在 `σ后=σ前` 时成立。例如样本减半、均值不变、标准差也减半，t 反而提高 √2。不能直接判定“平均收益没提高 1.41 倍就是证据变弱”。且 t 的提升不是唯一策略目标，过滤器可能改善尾部风险或容量。

### 13 · P1：均值回归半衰期公式是近似，判定条件不足

位置：[35-market-regime.md:147](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/35-market-regime.md:147)；第 41 篇、术语表同步。

对 `Δp_t=a+b p_(t−1)+ε_t`，离散 AR(1) 系数为 `φ=1+b`。当 `0<φ<1` 时：

`h=−ln(2)/ln(1+b)`；只有 b 接近 0 才近似 `−ln(2)/b`。

例如 b=−0.2，精确值约 **3.106 根**，原文近似为 3.466 根。`b<0` 本身不充分：平稳条件是 `|1+b|<1`，负 φ 对应交替衰减，不能直接套单调回归解释。估计到负 b 也不能证明平稳，需要检验与区间。配对价差、跨期价差没有普遍“必须归零”的机制。[Penn State AR(1) 课程](https://online.stat.psu.edu/stat510/Lesson01)

### 14 · P1：网格 0.5%−0.2% 的正负判断错误

位置：[41-grid-trading.md:195](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/41-grid-trading.md:195)。

按文中同基数简化口径，完成一轮的净收益是 **+0.3%**，不是“每格负期望”。这不证明整个网格正期望，因为未闭合库存、路径风险和其他成本仍要计入。

同篇 `毛收益≈N×(g−c)` 实为扣所列成本后的结果；还缺每格数量/名义本金。N 应数**完整买卖配对**，不能把单向穿越次数都当盈利回合。收盘价路程与百分比间距量纲不一致，且分钟收盘路径会漏掉盘内往返，所以所写 `R/g` 也不能无条件作为真实成交次数上界。

### 15 · P1：网格杠杆容忍跌幅混淆收益率分母

位置：[41-grid-trading.md:234](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/41-grid-trading.md:234)。

等量持仓、均价约 `P0(1−d/2)` 时，从均价跌到下界的亏损率是 `d/(2−d)`，不是 d/2。若 L 定义为总建仓成本/初始权益，忽略维持保证金和成本，解 `L d/(2−d)=1` 得 **d=2/(L+1)**；L=10 时约 18.18%，不是 20%。若 L 是现价名义杠杆或券商杠杆档，需另建模型，不能混用。

“越跌越加大数量必然缩短可承受距离”也要区分固定总预算重新分配与额外加仓。后者可能显著增风险；前者平均成本下降，不支持原文无条件结论。建议改为逐笔余额、权益、维持保证金模拟。

### 16 · P1：随机进出回测没有文中声称的确定答案

位置：[38-validation.md:367](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/38-validation.md:367)；术语表、第 44 篇同步。

随机时点做多上涨资产可能赚钱；即便方向对称、期望毛收益为零，单次样本也可能赚钱。因此不能以“接近零或赚钱”直接判定引擎 bug。

应使用人工固定价格路径和手算账本做确定性测试：固定价加费用、已知两笔交易、空头、跳空、同时触及止盈止损、部分成交。随机测试只能在明确零假设下看多次模拟分布。

### 17 · P2：交易频率与时间单位算错

位置：[31-short-term-trading.md:189](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/31-short-term-trading.md:189)。

400 笔/每日 250 次=1.6 **天**，不是年；400 笔/每月 12 次≈33.3 **个月**，不是年。若本意是每年 250 次、每年 12 次，应更改频率标签。`400×0.1%=40%` 还须说明按什么名义本金收费，不能直接当账户必然损耗。

### 18 · P2：52 周新低不会在暴跌满一年后自动归零

位置：[39-market-breadth.md:71](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/39-market-breadth.md:71)。

滚动最低价旧值退出窗口会改变比较基准，但当日是否创新低仍由当前价和剩余历史决定，不会机械归零；移除更低的旧低点，甚至可能让后续创新低更容易。应改为“窗口换样影响阈值”，并给具体序列示例。

### 19 · P1：环境指标正常不能排除策略失效和随机亏损

位置：[35-market-regime.md:255](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/35-market-regime.md:255)。

ATR、效率比正常不代表策略期望保持不变，也不排除抽样噪声。`实际结果=策略期望值+执行偏差+成本` 不是完整随机损益分解，成本若按正数记还应减去。

建议写为 `实际损益=条件期望损益+随机偏差+执行差异−成本`，并注明分解需统一基准、避免重复扣费。不能用两个环境读数把亏损全部归到执行问题。

### 20 · P2：期权价差并不必然同时增加 call 和 put OI

位置：[45-option-chain.md:233](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/45-option-chain.md:233)。

Bull call spread 两条腿都是 call；put vertical 两条腿都是 put。开平仓及对手方状态共同决定 OI 变化。应改成“多腿交易会影响多个合约，单腿聚合数据不能直接还原组合意图”。[OIC 牛市看涨价差定义](https://www.optionseducation.org/strategies/all-strategies/bull-call-spread-debit-call-spread)

## 二、应补条件或降低结论强度

| 编号 / 级别 | 定位 | 问题与建议 |
|---|---|---|
| 21 · P1 | [26-screening.md:160](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/26-screening.md:160)；第 31、35、37 篇 | √T 是特定模型下的尺度近似，不是条件交易利润的上界；ATR 也不等于收益标准差。平均单根振幅不能证明 3–5 分钟交易数学不可能，信号周期也不等于持仓期。把比值 5/10、捕获 1/3 标为作者的经验筛选假设，实际用信号条件下的净收益、成交率检验。 |
| 22 · P2 | [31-short-term-trading.md:108](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/31-short-term-trading.md:108) | 被动限价入场也可以服务方向策略；maker 不自动等于做市。比较手续费时要包含未成交机会、逆向选择和出场方式。 |
| 23 · P1 | [30-trend-following.md:306](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/30-trend-following.md:306) | 没有证据证明多品种趋势基金主要为凑样本而非分散；同一宏观冲击的交易不能当独立样本。删除“单一两个品种不可能有统计证据”和“短线几个月一定验证”的断言。 |
| 24 · P1 | [20-performance-and-retirement.md:93](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/20-performance-and-retirement.md:93)；第 7、30、31、38 篇 | `N=4σ²/μ²` 仅是简化效应量达到 t≈2 的规模标尺，不是有充分检验功效的最低样本数。在独立正态近似、双侧 5%、80% 功效、μ/σ=0.1 时约需 785 笔，而非 400。补依赖性、HAC/分块方法、功效和多重检验；“未显著”不能改写成“没有任何信息”。 |
| 25 · P2 | [38-validation.md:288](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/38-validation.md:288)；术语表 | 表中最好夏普需要独立/有效独立尝试、近似分布等条件。术语表写 `√(2lnN)/√T` 却在 N=1000、T=5 时给 1.46；该式实际是约 1.662。1.46 可接近更精细的有限样本极值近似，但不能混作同一公式结果。 |
| 26 · P2 | [38-validation.md:304](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/38-validation.md:304) | DSR 不是简单“观察夏普减去运气水平”，它是相对调整后基准的概率统计量，还考虑样本长度、偏度、峰度等。第八节的等风险等权组合有效数也不能直接拿来替代多重检验有效试验数。 |
| 27 · P2 | [38-validation.md:195](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/38-validation.md:195) | 对选好策略的收益做 bootstrap 不自动恢复被搜索选择遗漏的坏路径，也不保证 MDD 中位数更大。区分参数估计区间与路径风险分布，补未经历的尾部压力情景。固定“至少 10 段”、各段都赚钱、参数一致也都不是普适通过标准。 |
| 28 · P2 | [38-validation.md:90](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/38-validation.md:90) | 用历史零成本回测估 g 当然使用数据；根据 g 选模型也会消耗验证信息。可说“不动最终留出集”，不能说“纯算术无数据消耗”。同理，切点测试若用于调规则也属于搜索。 |
| 29 · P1 | [33-price-levels.md:135](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/33-price-levels.md:135)；第 45 篇 | OI 集中是观察，必然 pinning 是推断。是否吸附/放大取决于净 gamma、距离行权价、期限、对冲行为及其他头寸。IV/Gamma 也依赖模型、利率、分红和报价选择，不是完全无假设。“GEX 数值精确、只有符号不确定”过强，净头寸假设同时影响大小。 |
| 30 · P2 | [45-option-chain.md:229](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/45-option-chain.md:229) | 合法使用昨日已发布 OI 没有前视偏差；它是滞后数据。将未来更新值回填到过去才是前视。应保留实际发布时间，区分数据新鲜度和信息泄漏。 |
| 31 · P2 | [45-option-chain.md:211](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/45-option-chain.md:211) | 每天更新的 Max Pain 仍可在固定时点存档，对固定到期目标检验；动态更新不等于不可证伪。应批评缺乏样本外证据、事后换版本、成本与机制假设。不能笼统说每周只有一个样本，需按产品到期频率和相关性计数。 |
| 32 · P1 | [33-price-levels.md:421](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/33-price-levels.md:421)；第 27 篇止损建议 | K 线不能直接看见真实止损库存，止损触发后的市价单通常消耗挂单流动性。订单聚集不自动推出价格被吸引，也不能统一要求“前低下方不能止损”。区分可观测挂单、推测触发单、风险预算。 |
| 33 · P2 | [15-orderflow-data.md:510](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/15-orderflow-data.md:510)；第 33 篇 | 深度、成交、OI 可在单位、币种、时间和合约口径统一后聚合。执行深度还受账户资金、访问权限、延迟与路由限制。不能说聚合完全没意义，也不能把全市场聚合直接当一个账户可立即成交的深度。 |
| 34 · P2 | [15-orderflow-data.md:221](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/15-orderflow-data.md:221) | 自身成交测量较直接，但仍受延迟、基准选择、成交路径乃至不利执行影响；它不是“不可操纵”。深度也可能被诱导挂单污染。成交量、价差、深度、恢复速度应结合，不宜全面否决成交额。 |
| 35 · P2 | [15-orderflow-data.md:374](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/15-orderflow-data.md:374) | Value Area 算法随平台不同，常见实现比较上下候选桶的量，而不是简单交替。应指明实现、并列桶处理、70% 阈值和越界约定，免得自建指标与平台不一致。 |
| 36 · P2 | [27-reading-charts.md:82](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/27-reading-charts.md:82) | 更细数据有帮助但没有通用“十倍”保证；更细 K 线仍可能双触。可用逐笔/报价、保守路径上下界与敏感性分析。HA 开盘递归本身可分析延迟；不能说完全不可算。非时间图可保留时间戳，需区分显示轴与底层数据。 |
| 37 · P1 | [36-left-right-side.md:65](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/36-left-right-side.md:65) | 确认窗口缩短不自动把确认后入场变成转折前入场；左侧不必摊平、不必无止损，右侧也不必低胜率。该篇第二节导语还与紧接的胜率表相反。建议重写成入场时点、退出规则、仓位规则三个独立维度。 |
| 38 · P2 | [39-market-breadth.md:178](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/39-market-breadth.md:178) | 广度差与持仓权重集中不是算术等价：等权组合也可能只有少数股上涨。`1/Σw²` 是权重集中度，不是实际独立风险数；负相关资产也使所谓“必然上界”不成立。等权/市值加权比值受规模风格、再平衡、分红和费用影响，成分变化也不会因使用比值而消失。 |
| 39 · P2 | [45-option-chain.md:99](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/45-option-chain.md:99)；第 39 篇 | IV 包含风险中性定价与风险溢价，不是现实概率下未来波动的无偏预测。区分隐含方差与未来实现方差、事前溢价与事后差值、年化与期限一致。倒挂可能来自短期压力而非已知日历事件，不能当作事件存在的证明。 |
| 40 · P2 | [47-ai-in-trading.md:157](/Users/lishuaishuai/Projects/ifcalm/ifcalm-blog/content/posts/trade/47-ai-in-trading.md:157) | 混淆模型参数与超参数；并非所有 ML 模型参数都比样本多。黑箱不等于不可检验，可固定模型版本并记录时间戳输出做前向评估。“代码出错一定崩溃、AI 校验通过就安全”也应删除，数值逻辑错误同样可静默发生。 |

补充来源：DSR 的定义与统计条件见 [Bailey–López de Prado 原论文](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)（25–26）；Value Area 见 [TradingView 算法](https://www.tradingview.com/support/solutions/43000502040-volume-profile-indicators-basic-concepts/)（35）；流动性多指标口径见 [CME 教育说明](https://www.cmegroup.com/education/articles-and-reports/how-traders-measure-liquidity)（34）；VIX 见 [Cboe 方法文件](https://cdn.cboe.com/api/global/us_indices/governance/VIX_Methodology.pdf)（39）。

关于止损聚集，纽约联储研究提供的是特定外汇市场中止损触发与价格级联的证据，不能外推成所有前高前低均有已知库存，或价格必然被吸引过去。[Osler 原研究](https://www.newyorkfed.org/research/staff_reports/sr150.html)（32）。

另需统一检查所有“唯一”“必然”“无解”“完全不可能”“可靠性差一个数量级”等表述。例如“空仓是正期望”应改为在指定反事实下避免交易成本，空仓本身不是普遍正收益来源；“用默认参数多重检验负担为零”也忽略了指标、标的、周期和出场选择。第 37 篇关于缠论原作者观点、定义及重言式判断，应补原课文出处和版本，不能仅凭本手册的改述证明原体系性质。

## 三、缺少或展开不足的教学内容

这里的“缺少”指未找到独立、可复现的展开，不代表一个词也没提过。

| 优先级 | 建议补充 | 最少应包含什么 | 建议位置 |
|---|---|---|---|
| 高 | 核心指标的算法与适用条件 | SMA/EMA/Wilder 平滑差异；MACD 信号线与柱体平台倍数；RSI 初始化与零分母；KDJ 完整公式；ATR 与收益标准差区别；ADX 无方向；布林带不是自动 95% 概率区间；Donchian 突破需排除当前柱。配短数据手算表。 | 27、34、术语表 |
| 高 | 结构分析的可计算定义 | HH/HL/LH/LL、摆动点、区间、突破、回踩、假突破、背离。明确确认窗口、容差、失效条件和时间范围，不把术语本身当盈利证据。 | 33、37、40 |
| 高 | 重绘与信号可得时点专题 | Pivot/ZigZag/分型被画回过去但当时不可知；需要右侧 k 根确认；高周期未收盘数据；中心化平滑/负位移；可见区间 VP 起点变化。区分事件时间、确认时间、下单时间。 | 27、37、44 |
| 高 | 一个端到端、可复现的教学策略 | 固定一套公开规则，含数据版本、信号、仓位、下一时点执行、费用、退出、失败案例、留出集。提供基准与消融比较；明确仅教学，不承诺获利。当前文章多教否决，却缺少从定义到验证的完整实例。 | 32、38 或新附录 |
| 高 | 依赖样本的统计检验 | HAC/Newey–West、按日期同步分块、重叠持仓、purging/必要间隔、多个品种共同冲击、检验功效、置信区间、固定停止规则。不是简单“多几笔就显著”。 | 38 |
| 高 | 风险与净值记账规范 | 线性多空仓位公式中的绝对价差/乘数/币种；价格止损与风险预算止损；跳空风险；MAE/MFE；未平仓 mark-to-market；单笔 R 和账户收益区别；容量与资金占用。已有风险章节，可在此补完整算例。 | 6、18、20、41 |
| 中 | VWAP 与成交分布的完整用法 | Session VWAP、Anchored VWAP 的锚点选择；TPO Market Profile 与 Volume Profile 不同；逐笔真实 Delta 与低周期近似 Delta；数据源覆盖差异。 | 15、33 |
| 中 | 实时判定市场状态与验证状态切换 | 历史状态不等于未来持续；训练时定阈值，验证时固定；状态滞后、来回切换、误判成本。均值回归须含单位根/协整与结构突变，不要求任意配对价差“必然收敛”。 | 35 |
| 中 | 数据规范与工程边界 | 复权用于指标、可成交价用于撮合；期货连续合约换月；空 bar/零成交量；tick/lot 舍入；指标 warm-up；交易所字段与时间戳；行情修订；原始数据版本。现有第 44 篇方向正确，但不足以复现指标。 | 44 |
| 中 | 原始证据表和维护规则 | 每项主张给来源、市场、样本期、持有期、是否扣成本、效应大小、不确定性、复现状态。把“无证据”“证据混杂”“已证明无效”严格区分。经验阈值标记为假设。 | 7、34、38 |

重绘专题可参照 [TradingView 官方说明](https://www.tradingview.com/pine-script-docs/concepts/repainting/)：重点是历史显示与实时可得信息不同，而不是笼统宣布所有重绘指标不可用。止损是否改善策略也需要条件检验，[Kaminski–Lo 研究](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=968338)明确分析了增加和减少价值的条件。

不建议为了“全面”直接增加江恩、更多波浪或更多神奇参数。先补公式、可用时点、失败样本和验证方法，比扩展指标数量更有价值。

## 四、建议的修订顺序与验收

1. **修框架**：27、32、34、40，去掉“无新数据所以无预测力”“不可数所以不可证伪”等错误门槛。
2. **修数学和记账**：30、31、33、35、36、38、41、45，先修偏度、OI、过滤器、半衰期、网格和随机测试。
3. **同步传播点**：术语表、索引、summary、结论段，以及 7、15、19、20、26、37、39、44、47 篇相关引用，避免正文修了速查表仍错。
4. **补最小教学闭环**：一张算法表、一组人工可手算数据、一套完整教学策略和一份失败/样本外报告。

验收时应检查：每个数学式都有变量、单位和假设；每个信号都有最早可得时点；每个强结论有原始证据或可复现推导；策略类比明确不是恒等关系；所有金额案例手算复核；最后运行 Hugo 检查引用和构建。

本次复算只用于检查文中算术与提供反例，没有使用实时行情来推断盈利能力。以上发现应作为修订清单，而不是相反方向的交易推荐。
