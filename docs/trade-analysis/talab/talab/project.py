"""talab.project：把前面三十四篇串成一条流水线。第 35 篇（毕业项目）。

这个模块里没有一个函数在计算收益。它们全都在回答同一个问题：

> **这条想法，凭什么值得你把钱放进去。**

在法庭上，举证责任在原告。你的策略就是原告：它要证明自己比「什么都不做」和
「一个更简单的做法」更好——**而不是等着别人来证明它不行**。

| 这里的东西 | 对应法庭上的 |
|---|---|
| `Idea` 六格登记表 | 起诉状：告谁、凭什么、要什么 |
| `checklist` | 证据规则：哪些证据算数 |
| `Gate` / `audit` | 一条一条过证据 |
| **`against`** | **被告的抗辩：「同样的结果，不用你也能得到」** |
| `edge_vs_luck` | 「这点差别，随便试试也能试出来」 |
| `one_pager` | 判决书 |

⚠️ 整条流水线里最容易被跳过、而且一跳过就全白做的是 `against` 那一格：
**你和什么比。**一份把候选和「更差的东西」比出来的报告，每一个数字都可以是对的，
而整份报告没有任何意义。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from talab.validate import expected_max_sharpe

BETTER = ("高", "低")
STAGES = ("想法", "结构", "规则", "回测", "评估", "检验", "上线")


# ---------------------------------------------------------------------------
# 一、想法登记表：六格，一格都不能空
# ---------------------------------------------------------------------------

@dataclass
class Idea:
    """一条想法在开始写代码之前必须填完的六格。

    六格的顺序就是这门课的顺序，而且**是有依赖的**：
    没有第一格就写不出第三格（不知道谁在被迫交易，就不知道该在哪一根进场），
    没有第四格，后面所有的数字都失去意义。

    ⚠️ 允许填「不知道」，但**不允许留空，也不允许写「待定」**——
    「不知道」是一个可以推进的答案（去查），「待定」不是。
    """
    name: str                              # 一句话说清这条想法
    counterparty: str                      # 谁被迫交易，为什么（第 2 篇）
    mechanism: str                         # 这件事凭什么会发生（第 8–20 篇）
    rules: str                             # 六要素（第 21 篇）
    control: str                           # 对照组：它要打败谁（这一篇）
    sample: str                            # 多少笔、多长、哪些市场（第 29 篇）
    deployment: str                        # 上线方案（第 34 篇）

    FIELDS = {"name": "一句话", "counterparty": "谁被迫交易", "mechanism": "机制",
              "rules": "规则（六要素）", "control": "对照组", "sample": "样本",
              "deployment": "上线方案"}

    def __post_init__(self):
        for key in self.FIELDS:
            value = str(getattr(self, key)).strip()
            if not value:
                raise ValueError(f"「{self.FIELDS[key]}」这一格不能空")
            if value in ("待定", "TBD", "?", "略"):
                raise ValueError(f"「{self.FIELDS[key]}」写的是 {value!r}——"
                                 "不知道就写「不知道」，那是一个可以推进的答案")

    def describe(self) -> pd.Series:
        return pd.Series({label: getattr(self, key) for key, label in self.FIELDS.items()})


def checklist() -> pd.DataFrame:
    """全课的检查单：每一关查什么、判据是什么、出自第几篇。

    ⚠️ 这张表的顺序是有讲究的：**越靠前的关，越便宜、越致命**。
    对照组选错了，后面十关全部白查；而「夏普够不够高」排在很后面，
    因为它是这张表里**最不重要**的一个数。
    """
    rows = [
        ("想法", "谁被迫交易", "说得出具体是谁、为什么非交易不可", "第 2 篇"),
        ("想法", "对照组", "说得出「不用这条想法的更简单做法」是什么", "第 35 篇"),
        ("结构", "这个数在那一刻算得出来吗", "所有输入只用到当根及之前的数据", "第 27、28 篇"),
        ("结构", "指标能不能增量算", "实盘每收一根算一次，不是重算整条历史", "第 34 篇"),
        ("规则", "六要素填满了吗", "环境、入场、成交、止损、出场、仓位，一格不空", "第 21 篇"),
        ("回测", "引擎对账", "和另一份实现逐根相对差 < 1e-9", "第 27、34 篇"),
        ("回测", "记账自洽", "现金 + 持仓市值 = 权益，误差 0", "第 27 篇"),
        ("回测", "推迟一根塌不塌", "lag 0→1 只温和变差，不塌陷", "第 27 篇"),
        ("回测", "成本算进去了吗", "手续费 + 价差 + 滑点，按 R 折算", "第 28 篇"),
        ("评估", "笔数够不够", "样本量看**笔数**不看根数", "第 29 篇"),
        ("评估", "逐笔 t 值", "大于 2", "第 29、31 篇"),
        ("检验", "曲面是高地还是针", "落差占年化的比例越小越好", "第 30 篇"),
        ("检验", "样本外", "样本内挑的那一格，样本外排名不塌", "第 30 篇"),
        ("检验", "多重检验", "扣掉「试了几次」白捡的那一截还剩多少", "第 30、35 篇"),
        ("检验", "打乱对照", "块自助法造的假数据里，多少比真实的好", "第 30、32 篇"),
        ("检验", "赢过对照组了吗", "**和对照组比，不是和更差的东西比**", "第 35 篇"),
        ("上线", "正常范围表", "连亏、回撤、水下时间的分位数算好了", "第 33 篇"),
        ("上线", "预热要几根", "窗口型看硬门槛，递推型带周期的五倍", "第 34 篇"),
        ("上线", "交易所收不收这张单", "tickSize / stepSize / minNotional 过了", "第 34 篇"),
        ("上线", "警戒线和动作", "阈值按台阶笔数算，动作写死", "第 33、34 篇"),
    ]
    return pd.DataFrame(rows, columns=["阶段", "查什么", "判据", "出处"])


# ---------------------------------------------------------------------------
# 二、一道一道过关
# ---------------------------------------------------------------------------

@dataclass
class Gate:
    """一道关：看哪个数、门槛多少、谁大谁好、出自第几篇。

    `must=True` 是**一票否决**：这一道没过，前面过了多少道都不算数。
    整条流水线上只有很少几道该是一票否决的，而它们几乎都不是「收益够不够」。
    """
    name: str
    value: float
    threshold: float
    better: str = "高"
    source: str = ""
    must: bool = False

    def __post_init__(self):
        if self.better not in BETTER:
            raise ValueError(f"better 只能是 {BETTER} 之一，收到 {self.better!r}")

    @property
    def passed(self) -> bool:
        if np.isnan(self.value):
            return False                   # 算不出来就是没过，不是「暂且算过」
        return self.value >= self.threshold if self.better == "高" else self.value <= self.threshold

    def row(self) -> dict:
        return {"这一关": self.name, "量到的": self.value, "门槛": self.threshold,
                "谁大谁好": self.better, "一票否决": self.must,
                "结论": "过" if self.passed else "没过", "出处": self.source}


def audit(gates) -> pd.DataFrame:
    """把若干道关摆成一张表。"""
    gates = list(gates)
    if not gates:
        raise ValueError("至少要有一道关")
    return pd.DataFrame([gate.row() for gate in gates])


def verdict(gates) -> pd.Series:
    """几道过、几道没过，以及**一票否决有没有被踩**。

    ⚠️ 结论不是「过了几道」的加权平均。一票否决踩了一道，结论就是不上线——
    **这正是把它叫做一票否决的原因**。
    """
    gates = list(gates)
    failed = [g for g in gates if not g.passed]
    blocked = [g for g in failed if g.must]
    return pd.Series({
        "一共几关": float(len(gates)), "过了几关": float(len(gates) - len(failed)),
        "没过几关": float(len(failed)), "踩了几道一票否决": float(len(blocked)),
        "没过的": "、".join(g.name for g in failed) or "（没有）",
        "结论": "不上线" if blocked else ("可以进模拟盘" if not failed else "补完再说"),
    })


# ---------------------------------------------------------------------------
# 三、对照组：这一篇的主角
# ---------------------------------------------------------------------------

def against(candidate: dict, controls: dict[str, dict], keys=None) -> pd.DataFrame:
    """把候选和对照组**并排**放，并数清楚它赢了几项。

    每一个字典是一条策略的成绩单（`report.metrics` 的输出就能直接用），
    外加一个 `参数个数`——**这一列是整张表里最容易被省掉、也最要命的一列**：
    一条零参数的对照组和一条三参数的候选比，候选必须赢**得够多**才算赢
    （多出来的那一截该有多大，交给 `edge_vs_luck`）。

    ⚠️ 默认比的四项全是**越大越好**：最大回撤是负数，所以「大」就是「浅」。
    `参数个数` 这一列不参与比较，它只是摆在那里提醒你两边不是同一个起跑线。
    """
    keys = [key for key in (keys or ["年化", "最大回撤", "夏普", "卡玛"])]
    table = pd.DataFrame({name: pd.Series(values) for name, values in
                          {"候选": candidate, **controls}.items()}).T
    missing = [key for key in keys if key not in table.columns]
    if missing:
        raise ValueError(f"成绩单里没有这几项：{missing}")
    wins = [np.nan if name == "候选"
            else float(sum(table.loc["候选", key] > table.loc[name, key] for key in keys))
            for name in table.index]
    table["候选赢了几项"] = wins
    table["一共几项"] = [np.nan if name == "候选" else float(len(keys)) for name in table.index]
    table.index.name = "策略"
    return table


def edge_vs_luck(candidate_sharpe: float, control_sharpe: float, n_trials: int,
                 sharpe_std: float) -> pd.Series:
    """候选比对照组多出来的那一截，和**「试了 n_trials 次白捡的那一截」**比。

    第 30 篇算过：完全没有本事的情况下试 N 次，「最好的那次」的夏普期望
    就已经是一个正数（`expected_max_sharpe`）。所以「候选比对照组高 0.04」
    这句话本身不携带信息——**要看它高出来的量，和白捡的量，哪个大**。

    ⚠️ 对照组的参数个数如果是 0，它一次都没试过，这个门槛全算在候选头上。
    """
    if n_trials < 2 or sharpe_std <= 0:
        raise ValueError("试验次数至少是 2，夏普标准差要大于 0")
    threshold = expected_max_sharpe(n_trials, sharpe_std)
    edge = candidate_sharpe - control_sharpe
    return pd.Series({
        "候选夏普": candidate_sharpe, "对照组夏普": control_sharpe, "优势": edge,
        "试了几次": float(n_trials), "这些试验的夏普标准差": sharpe_std,
        "白捡的门槛": threshold, "优势是门槛的几成": edge / threshold,
        "结论": "优势大于白捡的量" if edge > threshold else "优势小于白捡的量，不算数",
    })


# ---------------------------------------------------------------------------
# 四、回顾与交付
# ---------------------------------------------------------------------------

def evolution(versions: dict[str, dict]) -> pd.DataFrame:
    """把一条策略每一版的成绩摆在一起，并标出**每一版只改了哪一件事**。

    ⚠️ 一次只改一件事，否则你分不清是哪一改起的作用——
    这和第 21 篇「六要素是咬合的，不能一格一格单独优化」不矛盾：
    那里说的是**别单独最优化**，这里说的是**别一次改两件**。
    """
    table = pd.DataFrame(versions).T
    table.index.name = "版本"
    return table


def _markdown(table: pd.DataFrame, index: bool = False) -> str:
    """把一张表写成 Markdown。自己写是为了不引入 `tabulate` 这个依赖。

    ⚠️ 单元格里的竖线要转义，否则它会把一列劈成两列（这门课的正文里踩过）。
    """
    frame = table.reset_index() if index else table
    def cell(value):
        if isinstance(value, float):
            return "—" if np.isnan(value) else f"{value:.4f}"
        return str(value).replace("|", "\\|")

    text = frame.astype(object).map(cell)
    header = "| " + " | ".join(str(name).replace("|", "\\|") for name in text.columns) + " |"
    rule = "|" + "---|" * len(text.columns)
    body = ["| " + " | ".join(row) + " |" for row in text.to_numpy()]
    return "\n".join([header, rule] + body)


def one_pager(idea: Idea, gates, comparison: pd.DataFrame,
              luck: pd.Series | None = None) -> str:
    """实验四的产出：一页纸策略报告（Markdown 文本）。

    这份报告刻意做得很短。它不是用来说服别人的，是用来**在半年之后说服你自己**：
    半年后你会忘记当时为什么这么定，而这页纸上每一行都能一句话答上来。
    """
    table = audit(gates)
    result = verdict(gates)
    lines = [f"# 策略报告：{idea.name}", ""]
    lines.append("## 一、登记表")
    lines.append("")
    lines.append("| 格 | 填的什么 |")
    lines.append("|---|---|")
    for key, label in idea.FIELDS.items():
        if key == "name":
            continue
        lines.append(f"| {label} | {getattr(idea, key)} |")
    lines.append("")
    lines.append("## 二、和对照组并排")
    lines.append("")
    lines.append(_markdown(comparison, index=True))
    if luck is not None:
        lines.append("")
        lines.append(f"> 优势 {luck['优势']:+.4f}，而试 {int(luck['试了几次'])} 次白捡的门槛是 "
                     f"{luck['白捡的门槛']:.4f}——**{luck['结论']}**")
    lines.append("")
    lines.append("## 三、过关情况")
    lines.append("")
    lines.append(_markdown(table[["这一关", "量到的", "门槛", "结论", "出处"]]))
    lines.append("")
    lines.append("## 四、结论")
    lines.append("")
    lines.append(f"- 一共 {int(result['一共几关'])} 关，过了 {int(result['过了几关'])} 关，"
                 f"没过 {int(result['没过几关'])} 关")
    lines.append(f"- 踩了 {int(result['踩了几道一票否决'])} 道一票否决")
    lines.append(f"- 没过的是：{result['没过的']}")
    lines.append(f"- **结论：{result['结论']}**")
    return "\n".join(lines)
