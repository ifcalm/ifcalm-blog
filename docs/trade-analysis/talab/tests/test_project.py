"""talab.project 的测试（第 35 篇）。数字全部手工构造，每一个都能自己算一遍。"""
import re

import numpy as np
import pandas as pd
import pytest

from talab import project as PJ
from talab import validate as V

FILLED = dict(name="一句话说清", counterparty="月末被迫调仓的基金", mechanism="第 20 篇的月末效应",
              rules="六要素填满了", control="买入持有", sample="SPY 十年 2,512 根",
              deployment="第 34 篇的阶梯")


def card(annual, drawdown, sharpe, calmar, n_params):
    return {"年化": annual, "最大回撤": drawdown, "夏普": sharpe, "卡玛": calmar,
            "参数个数": float(n_params)}


def test_idea_refuses_an_empty_box():
    assert len(PJ.Idea(**FILLED).describe()) == 7
    with pytest.raises(ValueError, match="谁被迫交易"):
        PJ.Idea(**{**FILLED, "counterparty": "   "})
    # 「不知道」可以，「待定」不行——前者是一个能推进的答案
    assert PJ.Idea(**{**FILLED, "counterparty": "不知道"}).counterparty == "不知道"
    with pytest.raises(ValueError, match="对照组"):
        PJ.Idea(**{**FILLED, "control": "待定"})


def test_the_checklist_puts_the_control_group_near_the_front():
    table = PJ.checklist()
    assert list(table.columns) == ["阶段", "查什么", "判据", "出处"]
    assert set(table["阶段"]) <= set(PJ.STAGES)
    # 对照组排在「想法」这一段，也就是写代码之前——这是整张表的重点
    assert table.loc[table["查什么"] == "对照组", "阶段"].iloc[0] == "想法"
    assert table.index[table["查什么"] == "对照组"][0] < 3


def test_gate_knows_which_direction_is_better():
    assert PJ.Gate("夏普", 1.2, 1.0, "高").passed
    assert not PJ.Gate("夏普", 0.8, 1.0, "高").passed
    assert PJ.Gate("PBO", 0.2, 0.5, "低").passed
    assert not PJ.Gate("PBO", 0.7, 0.5, "低").passed
    assert PJ.Gate("刚好卡线", 1.0, 1.0, "高").passed          # 等于门槛算过
    # 算不出来就是没过，不是「暂且算过」
    assert not PJ.Gate("算不出来", np.nan, 1.0, "高").passed
    with pytest.raises(ValueError):
        PJ.Gate("方向写错", 1.0, 1.0, "越大越好")


def test_audit_turns_gates_into_a_table():
    gates = [PJ.Gate("甲", 2.0, 1.0, "高", "第 1 篇"), PJ.Gate("乙", 2.0, 1.0, "低", "第 2 篇")]
    table = PJ.audit(gates)
    assert list(table["结论"]) == ["过", "没过"]
    assert list(table["出处"]) == ["第 1 篇", "第 2 篇"]
    with pytest.raises(ValueError):
        PJ.audit([])


def test_one_failed_veto_sinks_everything_else():
    passing = [PJ.Gate(f"第 {i} 关", 2.0, 1.0, "高") for i in range(7)]
    assert PJ.verdict(passing)["结论"] == "可以进模拟盘"
    assert PJ.verdict(passing)["过了几关"] == 7
    soft = passing + [PJ.Gate("差一点", 0.5, 1.0, "高")]
    assert PJ.verdict(soft)["结论"] == "补完再说"
    assert PJ.verdict(soft)["踩了几道一票否决"] == 0
    veto = passing + [PJ.Gate("赢过对照组", 0.5, 1.0, "高", must=True)]
    out = PJ.verdict(veto)
    # 七关全过、只踩一道一票否决，结论仍然是不上线——这正是叫它一票否决的原因
    assert out["过了几关"] == 7 and out["踩了几道一票否决"] == 1
    assert out["结论"] == "不上线"
    assert "赢过对照组" in out["没过的"]


def test_against_counts_wins_with_drawdown_as_bigger_is_better():
    candidate = card(0.10, -0.20, 1.0, 0.5, 3)
    controls = {"更差的": card(0.05, -0.30, 0.8, 0.3, 0),
                "零参数对照组": card(0.08, -0.10, 1.1, 0.8, 0)}
    table = PJ.against(candidate, controls)
    assert table.loc["更差的", "候选赢了几项"] == 4.0        # 回撤 -0.20 > -0.30，也算赢
    assert table.loc["零参数对照组", "候选赢了几项"] == 1.0  # 只赢年化
    assert np.isnan(table.loc["候选", "候选赢了几项"])
    assert table.index.name == "策略"
    with pytest.raises(ValueError, match="索提诺"):
        PJ.against(candidate, controls, keys=["索提诺"])


def test_edge_vs_luck_compares_the_edge_to_the_free_lunch():
    out = PJ.edge_vs_luck(candidate_sharpe=1.05, control_sharpe=1.00,
                          n_trials=200, sharpe_std=0.10)
    assert out["优势"] == pytest.approx(0.05)
    assert out["白捡的门槛"] == pytest.approx(V.expected_max_sharpe(200, 0.10))
    assert out["优势是门槛的几成"] == pytest.approx(0.05 / out["白捡的门槛"])
    assert out["结论"].startswith("优势小于")
    # 试的次数越少，白捡的门槛越低，同样的优势就越站得住
    few = PJ.edge_vs_luck(1.05, 1.00, n_trials=2, sharpe_std=0.10)
    assert few["白捡的门槛"] < out["白捡的门槛"]
    assert PJ.edge_vs_luck(1.60, 1.00, 200, 0.10)["结论"].startswith("优势大于")
    with pytest.raises(ValueError):
        PJ.edge_vs_luck(1.0, 0.9, n_trials=1, sharpe_std=0.1)
    with pytest.raises(ValueError):
        PJ.edge_vs_luck(1.0, 0.9, n_trials=100, sharpe_std=0.0)


def test_evolution_keeps_one_row_per_version():
    table = PJ.evolution({"v0": {"改了什么": "第一版", "年化": 0.08},
                          "v1": {"改了什么": "加止损", "年化": 0.05}})
    assert list(table.index) == ["v0", "v1"]
    assert table.index.name == "版本"
    assert table.loc["v1", "年化"] == 0.05


def test_markdown_escapes_pipes_and_shows_missing_values():
    table = pd.DataFrame({"名字": ["带 | 竖线的"], "数": [np.nan]})
    text = PJ._markdown(table)
    assert text.splitlines()[1] == "|---|---|"
    assert r"\|" in text                                      # 竖线被转义了
    assert "—" in text                                        # 缺失值不写成 nan
    # 数「没被转义的竖线」：表头和数据行必须一样多，否则那一行会被劈成多一列
    bars = lambda line: len(re.findall(r"(?<!\\)\|", line))
    assert bars(text.splitlines()[0]) == bars(text.splitlines()[2]) == 3


def test_one_pager_carries_the_six_boxes_and_the_verdict():
    idea = PJ.Idea(**FILLED)
    gates = [PJ.Gate("过了的", 2.0, 1.0, "高", "第 1 篇"),
             PJ.Gate("赢过对照组", 0.5, 1.0, "高", "第 35 篇", must=True)]
    comparison = PJ.against(card(0.10, -0.20, 1.0, 0.5, 3),
                            {"买入持有": card(0.12, -0.15, 1.2, 0.9, 0)})
    luck = PJ.edge_vs_luck(1.0, 1.2, 100, 0.1)
    text = PJ.one_pager(idea, gates, comparison, luck)
    for label in PJ.Idea.FIELDS.values():
        if label != "一句话":
            assert label in text
    assert "结论：不上线" in text
    assert "买入持有" in text and "白捡的门槛" in text
    assert PJ.one_pager(idea, gates, comparison).count("白捡的门槛") == 0


def test_a_report_that_only_beats_worse_things_still_fails():
    """这一篇的主张：只和更差的东西比出来的报告，每个数字都对，整份报告没有意义。"""
    candidate = card(0.0643, -0.1006, 1.0176, 0.6392, 3)
    legs = {"只做趋势跟随": card(0.0468, -0.1711, 0.6822, 0.2737, 0),
            "只做均值回归": card(0.0415, -0.1163, 0.7246, 0.3564, 0)}
    blend = {"五五开（零参数）": card(0.0451, -0.0630, 0.9806, 0.7163, 0)}
    only_legs = PJ.against(candidate, legs)
    assert (only_legs["候选赢了几项"].dropna() == 4.0).all()   # 两条单腿，四项全赢
    full = PJ.against(candidate, {**legs, **blend})
    assert full.loc["五五开（零参数）", "候选赢了几项"] == 2.0  # 加上对照组只赢两项
    luck = PJ.edge_vs_luck(1.0176, 0.9806, 180, 0.0889)
    assert luck["优势是门槛的几成"] < 0.2
    gates = [PJ.Gate("赢过对照组的项数", 2.0, 4.0, "高", must=True),
             PJ.Gate("优势 ÷ 白捡的门槛", luck["优势是门槛的几成"], 1.0, "高", must=True)]
    assert PJ.verdict(gates)["结论"] == "不上线"
