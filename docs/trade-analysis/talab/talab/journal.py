"""talab.journal：执行纪律与交易日志。第 33 篇。

前面三十二篇在回答同一个问题：**这条规则值不值得做。**
这一篇换一个问题：**规则已经定好了，你能不能照着做。**

两个问题的难点完全不同。前一个难在统计，后一个难在——你会想改。
而「想改」几乎总是发生在同一个时刻：**连着亏了几笔之后。**

所以这一篇的第一件事，是把「连着亏几笔」从一种感受变成一个可以算的数：

| 你想知道的 | 这里用什么算 |
|---|---|
| 连亏 7 笔正常吗 | `expected_longest`、`streak_distribution` |
| 回撤 20% 正常吗 | `shuffled`、`normal_range` |
| 连亏几笔才算策略坏了 | `streak_alarm`（先看这条规则会误报多少次）、`detection_size` |
| 连亏之后停手划不划算 | `pause_after_losses`、`pause_table` |
| 我那几次「手动调整」花了多少钱 | `interfere`、`interference_table` |
| 实盘和回测差的那一截是从哪来的 | `Entry`、`Journal`、`reconcile` |

最后一行是这一篇真正的落点。**回测和实盘的差额可以被完整地拆开**——
拆成成交价、仓位、漏做、多做、费用五块，五块之和**恰好**等于总差额，一分钱不剩。
拆不开的差额不存在；拆开之后你会发现，最大的一块通常不是滑点。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np
import pandas as pd

NORMAL = NormalDist()
EULER = 0.5772156649015329
SIDES = {"long": 1, "short": -1, "多": 1, "空": -1}
KINDS = ("skip_after_loss", "double_after_loss", "half_after_loss",
         "double_after_win", "cap", "widen")


# ---------------------------------------------------------------------------
# 一、连亏：正常范围是算出来的，不是感觉出来的
# ---------------------------------------------------------------------------

def streaks(results) -> pd.DataFrame:
    """把一串交易结果切成连胜段和连亏段。

    `results` 可以是收益、R 倍数或者 True/False，**大于 0 算赚**（和 `trend.r_profile` 同一个口径，
    所以正好打平的那一笔算在亏的那一边）。返回每一段的方向、起止序号和长度。
    """
    wins = pd.Series(results).to_numpy()
    wins = wins if wins.dtype == bool else wins > 0
    if len(wins) == 0:
        return pd.DataFrame(columns=["方向", "起", "止", "长度"])
    edges = np.flatnonzero(np.diff(wins)) + 1
    starts = np.concatenate([[0], edges])
    ends = np.concatenate([edges - 1, [len(wins) - 1]])
    return pd.DataFrame({"方向": np.where(wins[starts], "赚", "亏"),
                         "起": starts, "止": ends, "长度": ends - starts + 1})


def longest_streak(results, winning: bool = False) -> int:
    """最长的一段连亏（`winning=True` 时是最长连胜）有多少笔。没有这样的段就是 0。"""
    table = streaks(results)
    picked = table[table["方向"] == ("赚" if winning else "亏")]
    return int(picked["长度"].max()) if len(picked) else 0


def expected_longest(n: int, p: float) -> float:
    """`n` 次独立的下注里，概率为 `p` 的那一面**最长连续出现多少次**（Schilling 1990 的近似）：

    > E[最长连击] ≈ log(n·(1−p)) ÷ log(1/p) + γ ÷ ln(1/p) − 1/2

    γ 是欧拉常数 0.5772。这个式子说的事情很朴素：**笔数越多，最长连亏越长，而且是必然变长。**
    一条胜率 33% 的策略做 70 笔，最长连亏的期望接近 9——
    **你以为的「不正常」，只是笔数攒够了。**
    """
    if not 0 < p < 1:
        raise ValueError("p 要在 0 和 1 之间")
    if n < 1:
        raise ValueError("至少要有一次下注")
    log_inv = math.log(1 / p)
    return math.log(max(n * (1 - p), 1e-12)) / log_inv + EULER / log_inv - 0.5


def streak_distribution(n: int, win_rate: float, trials: int = 10_000, seed: int = 0,
                        levels=(0.5, 0.75, 0.9, 0.95, 0.99)) -> pd.Series:
    """蒙特卡洛：胜率 `win_rate` 的策略做 `n` 笔，**最长连亏**的分布。

    `expected_longest` 给的是期望，这里给的是整条分布——
    因为你关心的从来不是「平均会连亏几笔」，而是**「我这次碰上的这个数，算不算离谱」**。
    """
    rng = np.random.default_rng(seed)
    wins = rng.random((trials, n)) < win_rate
    # 逐行求最长的一段 False：把连续的 False 累加，遇到 True 清零，取每行最大值
    longest = np.zeros(trials, dtype=int)
    current = np.zeros(trials, dtype=int)
    for k in range(n):
        current = np.where(wins[:, k], 0, current + 1)
        longest = np.maximum(longest, current)
    out = {"笔数": float(n), "胜率": float(win_rate), "平均最长连亏": float(longest.mean()),
           "公式给的期望": expected_longest(n, 1 - win_rate)}
    out.update({f"{level:.0%} 分位": float(np.quantile(longest, level)) for level in levels})
    return pd.Series(out)


def streak_alarm(n: int, win_rate: float, thresholds=(3, 4, 5, 6, 7, 8, 10, 12),
                 trials: int = 10_000, seed: int = 0) -> pd.DataFrame:
    """「连亏 k 笔就认定策略坏了」——**这条规则在策略完全正常的时候，会误报多少次。**

    这是判断任何停用规则的第一步，也是唯一一步：先问它的误报率。
    一条误报率 90% 的规则不是谨慎，它只是**保证你会在某个时刻停手**。
    """
    rng = np.random.default_rng(seed)
    wins = rng.random((trials, n)) < win_rate
    rows = []
    for k in thresholds:
        current = np.zeros(trials, dtype=int)
        hits = np.zeros(trials, dtype=int)
        for j in range(n):
            current = np.where(wins[:, j], 0, current + 1)
            hits += (current == k)                      # 只在刚好凑满 k 笔那一下记一次
        rows.append({"门槛（连亏几笔）": k, "至少响一次的概率": float((hits > 0).mean()),
                     "平均响几次": float(hits.mean())})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 二、回撤：把交易的顺序重抽一遍
# ---------------------------------------------------------------------------

def shuffled(r, trials: int = 2000, seed: int = 0) -> pd.DataFrame:
    """把同一批交易**重新排一遍顺序**，看每一种顺序下的连亏、回撤和水下时间。

    这是第 29 篇自助法的一个特例，但问的问题不一样：那里问「这条策略的夏普可信吗」，
    这里问「**同样这批交易，换个顺序发生，我会看到多难看的一段**」。

    合计和顺序无关（加法可交换），所以每一次重抽的终点都一样——
    **变的只有路径。而你会不会中途停手，只取决于路径。**

    ⚠️ 这里**一律用加法**：曲线就是每笔结果的累加，相当于「每笔都按初始本金的固定比例下注」。
    喂 R 倍数进去，回撤的单位就是 R；喂每笔的账户收益率进去，单位就是百分点。
    不用复利是故意的——要看的是顺序效应，复利会把顺序效应和「越赚越大」搅在一起。
    """
    r = pd.Series(r).dropna().astype(float).to_numpy()
    if len(r) < 2:
        raise ValueError("至少要有两笔交易")
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(trials):
        path = rng.permutation(r)
        curve = np.cumsum(path)
        peak = np.maximum.accumulate(np.concatenate([[0.0], curve]))[1:]
        under = curve < peak
        rows.append({"最长连亏": longest_streak(path), "最深回撤": float((curve - peak).min()),
                     "最长水下（笔）": int(_longest_true(under)), "合计": float(curve[-1])})
    return pd.DataFrame(rows)


def _longest_true(flags: np.ndarray) -> int:
    longest = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest


def normal_range(r, trials: int = 2000, seed: int = 0,
                 levels=(0.5, 0.9, 0.95, 0.99)) -> pd.DataFrame:
    """一张「正常范围」表：真实这一次的连亏、回撤、水下时间，各自落在重抽分布的第几分位。

    这张表是这一篇唯一的可执行结论：**上线之前把它打印出来贴在屏幕上。**
    在范围内的难看是设计的一部分，超出范围才值得重新检查——
    ⚠️ 而且「超出范围」也只是**你事先约好的降级线**，不等于统计上证明了策略失效
    （要多少笔才能证明，看 `detection_size`）。
    """
    r = pd.Series(r).dropna().astype(float)
    table = shuffled(r, trials=trials, seed=seed)
    curve = r.cumsum().to_numpy()
    peak = np.maximum.accumulate(np.concatenate([[0.0], curve]))[1:]
    real = {"最长连亏": longest_streak(r), "最深回撤": float((curve - peak).min()),
            "最长水下（笔）": int(_longest_true(curve < peak))}
    rows = []
    for name, value in real.items():
        column = table[name]
        # 回撤是负数：越小越难看，所以分位要反过来数
        worse = (column <= value).mean() if "回撤" in name else (column >= value).mean()
        row = {"这一次": value, "重抽平均": float(column.mean()),
               "比这一次还难看的比例": float(worse)}
        for level in levels:
            q = 1 - level if "回撤" in name else level
            row[f"{level:.0%} 分位"] = float(np.quantile(column, q))
        rows.append(pd.Series(row, name=name))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 三、这是正常波动，还是策略真的坏了
# ---------------------------------------------------------------------------

def detection_size(mean: float, std: float, drop: float = 1.0,
                   alpha: float = 0.05, power: float = 0.8) -> float:
    """要**多少笔**交易，才能以 `power` 的把握、在 `alpha` 的水平上，
    认出「每笔的期望值掉了 `drop` 倍」（`drop=1.0` 就是掉到 0）：

    > 笔数 ≈ [ (z₁₋α + z_power) × 标准差 ÷ (期望 × drop) ]²

    这是第 29 篇「要跑多少年」的交易版本，结论也一样难看：
    **单笔收益的标准差通常是期望的好几倍，于是分母被平方一次，笔数就上了三位数。**
    连亏 7 笔提供的信息量，和这个数字比起来约等于 0。
    """
    if mean <= 0 or std <= 0 or drop <= 0:
        raise ValueError("期望、标准差、drop 都要是正数")
    z = NORMAL.inv_cdf(1 - alpha) + NORMAL.inv_cdf(power)
    return (z * std / (mean * drop)) ** 2


# ---------------------------------------------------------------------------
# 四、执行规则：连亏之后停手，值多少钱
# ---------------------------------------------------------------------------

def pause_after_losses(r, after: int = 3, pause: int = 3) -> np.ndarray:
    """「连亏 `after` 笔就停 `pause` 笔」这条规则，实际会跳过哪几笔。

    返回一串 True/False：True = 这一笔做了，False = 被规则拦下了。
    ⚠️ 被拦下的那几笔的**结果照样要记**——不然你永远不知道停手是赚了还是亏了。
    """
    r = pd.Series(r).dropna().astype(float).to_numpy()
    if after < 1 or pause < 0:
        raise ValueError("after 至少是 1，pause 不能是负数")
    taken = np.ones(len(r), dtype=bool)
    losses = skip = 0
    for i, value in enumerate(r):
        if skip > 0:
            taken[i] = False
            skip -= 1
            continue
        losses = losses + 1 if value <= 0 else 0
        if losses >= after:
            skip, losses = pause, 0
    return taken


def pause_table(r, afters=(2, 3, 4, 5), pauses=(1, 3, 5)) -> pd.DataFrame:
    """把「连亏几笔停几笔」的各种组合摆在一起，和「一笔不落地做」比。

    `跳过的那些笔` 这一列是全表最值得看的一列：它是**你停手的那段时间里，市场发给别人的钱**。
    """
    r = pd.Series(r).dropna().astype(float)
    total = float(r.sum())
    rows = [{"连亏几笔": 0, "停几笔": 0, "做了几笔": len(r), "合计 R": total,
             "跳过的那些笔": 0.0, "最深回撤": _depth(r.to_numpy())}]
    for after in afters:
        for pause in pauses:
            taken = pause_after_losses(r, after, pause)
            kept = r.to_numpy() * taken
            rows.append({"连亏几笔": after, "停几笔": pause, "做了几笔": int(taken.sum()),
                         "合计 R": float(kept.sum()),
                         "跳过的那些笔": float(r.to_numpy()[~taken].sum()),
                         "最深回撤": _depth(kept)})
    return pd.DataFrame(rows)


def _depth(r: np.ndarray) -> float:
    curve = np.cumsum(r)
    peak = np.maximum.accumulate(np.concatenate([[0.0], curve]))[1:]
    return float((curve - peak).min()) if len(curve) else 0.0


# ---------------------------------------------------------------------------
# 五、手动调整的代价
# ---------------------------------------------------------------------------

def interfere(r, kind: str, level: float = 2.0) -> np.ndarray:
    """在一串 R 倍数上施加一次常见的「手动调整」，返回调整之后的 R。

    前四种只动**仓位**或者**做不做**，所以是精确的：

    - `skip_after_loss`：亏一笔之后，下一笔不敢做了
    - `double_after_loss`：亏一笔之后，下一笔加倍下注（想一把捞回来）
    - `half_after_loss`：亏一笔之后，下一笔只做一半（怯场）
    - `double_after_win`：赚一笔之后，下一笔加倍下注（觉得手感来了）

    后两种动的是**出场**，只能给一个方向确定的估计：

    - `cap`：浮盈到 `level` 个 R 就提前走人 → `min(r, level)`。
      ⚠️ 这是**代价的上界**：真实的提前止盈还会把一部分最终亏损的交易救成小赚，
      所以真实代价比这里算出来的小。
    - `widen`：眼看要止损，把止损往外挪，最后照样止损 → 亏的那些乘以 `level`。
      ⚠️ 这也是**上界**：挪远之后会有一部分活过来变成盈利。
      想要不含上界的那个数，就直接改引擎里的止损参数重跑一遍——两个数一夹，真相在中间。
    """
    r = pd.Series(r).dropna().astype(float).to_numpy()
    if kind not in KINDS:
        raise ValueError(f"kind 只能是 {KINDS} 之一，收到 {kind!r}")
    if kind == "cap":
        return np.minimum(r, level)
    if kind == "widen":
        return np.where(r <= 0, r * level, r)
    previous = np.concatenate([[np.nan], r[:-1]])
    after_loss, after_win = previous <= 0, previous > 0
    scale = np.ones(len(r))
    if kind == "skip_after_loss":
        scale[after_loss] = 0.0
    elif kind == "double_after_loss":
        scale[after_loss] = 2.0
    elif kind == "half_after_loss":
        scale[after_loss] = 0.5
    else:
        scale[after_win] = 2.0
    return r * scale


def interference_table(r, cap: float = 2.0, widen: float = 2.0) -> pd.DataFrame:
    """把几种手动调整一次算完：合计 R、最深回撤、以及**和「一个字不改」差了多少**。

    这张表的用法是把最后一列读成钱：每笔冒账户 1%，差 10R 就是差 10 个百分点。
    """
    r = pd.Series(r).dropna().astype(float)
    base = float(r.sum())
    names = {"skip_after_loss": "亏了之后不敢做", "double_after_loss": "亏了之后加倍",
             "half_after_loss": "亏了之后减半", "double_after_win": "赚了之后加倍",
             "cap": f"浮盈 {cap:g}R 就走", "widen": f"要止损了把止损挪远（亏的 ×{widen:g}）"}
    rows = [{"怎么改的": "一个字不改", "合计 R": base, "最深回撤": _depth(r.to_numpy()),
             "差多少 R": 0.0}]
    for kind, label in names.items():
        changed = interfere(r, kind, cap if kind == "cap" else widen)
        rows.append({"怎么改的": label, "合计 R": float(changed.sum()),
                     "最深回撤": _depth(changed), "差多少 R": float(changed.sum() - base)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 六、交易日志：一行记两遍
# ---------------------------------------------------------------------------

@dataclass
class Entry:
    """日志里的一行。核心是一件事：**计划和实际并排放。**

    只记实际成交价的日志没有用——它能告诉你赚了多少，不能告诉你**为什么和回测不一样**。
    `reconcile` 要拆的那几块，全都藏在「计划」和「实际」的差里。

    `fill_*` 留空表示「和计划完全一样」。`qty` 为 0 的一行表示**这笔计划里的交易你没做**，
    照样要记——第四节的 `pause_table` 已经说明了为什么。
    """
    time: pd.Timestamp                    # 计划进场的那一根
    symbol: str                           # 标的
    plan_entry: float                     # 计划进场价
    plan_stop: float                      # 计划止损价
    plan_qty: float                       # 计划数量
    side: str = "long"
    plan_exit: float = np.nan             # 计划出场价（回测给的）
    fill_entry: float | None = None       # 实际成交价
    fill_qty: float | None = None         # 实际数量（0 = 没做）
    fill_exit: float | None = None
    exit_time: pd.Timestamp | None = None
    fee: float = 0.0                      # 实际付出的手续费
    plan_fee: float = 0.0
    basis: str = "规则"                   # 依据：规则 / 我觉得 / 别人说的
    note: str = ""                        # 偏离计划的原因，一句话

    def __post_init__(self):
        if self.side not in SIDES:
            raise ValueError(f"side 只能是 {tuple(SIDES)} 之一，收到 {self.side!r}")
        if not self.plan_qty > 0:
            raise ValueError("计划数量要大于 0")
        if SIDES[self.side] * (self.plan_stop - self.plan_entry) >= 0:
            raise ValueError("止损放错了方向：做多的止损要低于进场价，做空的要高于")
        if self.fill_qty is not None and self.fill_qty < 0:
            raise ValueError("实际数量不能是负数")

    def actual(self, name: str):
        """实际值；没填就是和计划一样。"""
        filled = getattr(self, f"fill_{name}")
        return getattr(self, f"plan_{name}") if filled is None else filled

    def pnl(self, planned: bool = False) -> float:
        """这一行的盈亏。`planned=True` 给的是回测里那一笔。"""
        sign = SIDES[self.side]
        if planned:
            return sign * self.plan_qty * (self.plan_exit - self.plan_entry) - self.plan_fee
        return sign * self.actual("qty") * (self.actual("exit") - self.actual("entry")) - self.fee

    def row(self) -> dict:
        return {"时间": self.time, "标的": self.symbol,
                "方向": "多" if SIDES[self.side] > 0 else "空",
                "计划进场价": self.plan_entry, "实际进场价": self.actual("entry"),
                "计划止损价": self.plan_stop,
                "计划数量": self.plan_qty, "实际数量": self.actual("qty"),
                "计划出场价": self.plan_exit, "实际出场价": self.actual("exit"),
                "出场时间": self.exit_time, "计划费用": self.plan_fee, "费用": self.fee,
                "计划盈亏": self.pnl(planned=True), "实际盈亏": self.pnl(),
                "依据": self.basis, "备注": self.note}


@dataclass
class Journal:
    """一本日志：`Entry` 的列表，加上一张能直接喂给 `reconcile` 的表。"""
    entries: list = field(default_factory=list)

    def add(self, entry: Entry) -> "Journal":
        self.entries.append(entry)
        return self

    def frame(self) -> pd.DataFrame:
        columns = ["时间", "标的", "方向", "计划进场价", "实际进场价", "计划止损价",
                   "计划数量", "实际数量", "计划出场价", "实际出场价", "出场时间",
                   "计划费用", "费用", "计划盈亏", "实际盈亏", "依据", "备注"]
        return pd.DataFrame([e.row() for e in self.entries], columns=columns)

    def summary(self) -> pd.Series:
        """日志自己的体检：有多少笔没按计划走，以及**有多少笔的依据不是「规则」**。

        最后那个数是这本日志唯一不能从券商对账单里算出来的东西，
        也是记日志的全部理由——**「我觉得」这一类，只有你自己记才数得出来。**
        """
        table = self.frame()
        if not len(table):
            return pd.Series(dtype=float)
        skipped = table["实际数量"] == 0
        off_price = table["实际进场价"] != table["计划进场价"]
        off_qty = (table["实际数量"] != table["计划数量"]) & ~skipped
        return pd.Series({
            "记了几笔": float(len(table)), "没做": float(skipped.sum()),
            "成交价和计划不一样": float(off_price.sum()),
            "数量和计划不一样": float(off_qty.sum()),
            "依据不是规则": float((table["依据"] != "规则").sum()),
            "计划盈亏合计": float(table["计划盈亏"].sum()),
            "实际盈亏合计": float(table["实际盈亏"].sum()),
            "差额": float(table["实际盈亏"].sum() - table["计划盈亏"].sum()),
        })


# ---------------------------------------------------------------------------
# 七、对账：把差额拆干净
# ---------------------------------------------------------------------------

def reconcile(planned: pd.DataFrame, actual: pd.DataFrame, key: str = "买入日",
              entry_col: str = "买入价", exit_col: str = "卖出价", qty_col: str = "数量",
              fee_col: str = "费用", side_col: str = "方向") -> dict:
    """实盘和回测差的那一截，是从哪来的。

    两张表按 `key`（默认进场日）对齐，把总差额拆成五块：

    | 这一块 | 怎么算 | 说的是 |
    |---|---|---|
    | 漏做 | −Σ 回测那笔的盈亏 | 计划里有、你没做 |
    | 多做 | +Σ 实盘那笔的盈亏 | 计划里没有、你做了 |
    | 进场滑点 | Σ 方向 × 计划量 ×（计划进场价 − 实际进场价） | 买贵了 / 卖便宜了 |
    | 出场滑点 | Σ 方向 × 计划量 ×（实际出场价 − 计划出场价） | 走早了 / 走晚了 |
    | 仓位差 | Σ 方向 ×（实际量 − 计划量）×（实际出场价 − 实际进场价） | 做大了 / 做小了 |
    | 费用差 | −Σ（实际费用 − 计划费用） | 手续费和回测里假设的不一样 |

    这不是近似：**六块之和恒等于「实盘合计 − 回测合计」**（`差额核对` 那一项就是用来看这个的，
    正常应该是 0）。代数上它是把 q(x−e) 的差分三步展开，每一步只动一个量。

    ⚠️ **拆开之后最该看的是「漏做」那一格。** 滑点是几个基点的事，
    漏做一笔是整整一笔的事——而第 31 篇已经量过，一笔可以占九年收益的 14%。
    """
    def prep(table: pd.DataFrame) -> pd.DataFrame:
        out = table.copy()
        if fee_col not in out:
            out[fee_col] = 0.0
        out["_side"] = (out[side_col].map(SIDES).astype(float) if side_col in out else 1.0)
        out["_pnl"] = out["_side"] * out[qty_col] * (out[exit_col] - out[entry_col]) - out[fee_col]
        return out.set_index(key)

    left, right = prep(planned), prep(actual)
    both = left.index.intersection(right.index)
    missing, extra = left.drop(both), right.drop(both)
    p, a = left.loc[both], right.loc[both]

    sign, q_p, q_a = p["_side"], p[qty_col], a[qty_col]
    slip_in = sign * q_p * (p[entry_col] - a[entry_col])
    slip_out = sign * q_p * (a[exit_col] - p[exit_col])
    size_gap = sign * (q_a - q_p) * (a[exit_col] - a[entry_col])
    fee_gap = -(a[fee_col] - p[fee_col])
    parts = pd.Series({
        "漏做": -float(missing["_pnl"].sum()), "多做": float(extra["_pnl"].sum()),
        "进场滑点": float(slip_in.sum()), "出场滑点": float(slip_out.sum()),
        "仓位差": float(size_gap.sum()), "费用差": float(fee_gap.sum()),
    })
    total = float(right["_pnl"].sum() - left["_pnl"].sum())
    parts["合计"] = float(parts.sum())
    parts["实盘 − 回测"] = total
    parts["差额核对"] = parts["合计"] - total
    by_trade = pd.DataFrame({"进场滑点": slip_in, "出场滑点": slip_out,
                             "仓位差": size_gap, "费用差": fee_gap,
                             "这一笔差多少": a["_pnl"] - p["_pnl"]})
    return {"归因": parts, "逐笔": by_trade.sort_index(),
            "漏做的": missing.drop(columns=["_side"]), "多做的": extra.drop(columns=["_side"])}
