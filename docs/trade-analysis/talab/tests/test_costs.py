"""talab.costs 的测试（第 28 篇）。"""
import numpy as np
import pandas as pd
import pytest

from talab import costs as C, data as D


def test_crypto_cost_splits_into_fee_half_spread_and_slippage():
    """10 万美元的永续 taker 单：手续费 50、半个价差 0.165、滑点 0。"""
    out = C.crypto(100_000, "永续 taker", spread_bp=0.033)
    assert out["手续费"] == pytest.approx(50.0)
    assert out["半个价差"] == pytest.approx(100_000 * 0.033 / 2 / 10_000)
    assert out["滑点"] == 0.0
    assert out["占名义价值"] == pytest.approx(out["合计"] / 100_000)
    assert out["手续费"] / out["半个价差"] == pytest.approx(0.0005 / (0.033 / 2 / 10_000))


def test_crypto_maker_is_cheaper_than_taker_and_spot_is_dearest():
    cheap = C.crypto(100_000, "永续 maker")["占名义价值"]
    dear = C.crypto(100_000, "永续 taker")["占名义价值"]
    spot = C.crypto(100_000, "现货 taker")["占名义价值"]
    assert cheap < dear < spot
    with pytest.raises(ValueError):
        C.crypto(100_000, "场外找人私聊")


def test_us_regulatory_fees_are_charged_on_sales_only():
    """SEC 费和 TAF 只在卖出时收，买入这两项都是 0。"""
    kwargs = dict(price=200.0, shares=500.0, spread_bp=1.0, sec_rate=20.6e-6,
                  taf_per_share=0.000166, taf_cap=8.30)
    buy, sell = C.us_stock(side="buy", **kwargs), C.us_stock(side="sell", **kwargs)
    assert buy["SEC 费"] == 0.0 and buy["FINRA TAF"] == 0.0
    assert sell["SEC 费"] == pytest.approx(100_000 * 20.6e-6)
    assert sell["FINRA TAF"] == pytest.approx(500 * 0.000166)
    assert buy["半个价差"] == sell["半个价差"] == pytest.approx(100_000 * 1.0 / 2 / 10_000)
    assert sell["合计"] > buy["合计"]
    with pytest.raises(ValueError):
        C.us_stock(200.0, 500.0, side="随便")


def test_us_taf_is_capped_per_transaction():
    big = C.us_stock(price=1.0, shares=1_000_000, side="sell", spread_bp=0.0,
                     taf_per_share=0.000166, taf_cap=8.30)
    assert big["FINRA TAF"] == pytest.approx(8.30)          # 不封顶的话是 166 美元


def test_us_zero_commission_is_not_zero_cost():
    """佣金 0，但价差还在：1 个基点的价差在 10 万美元上是 5 美元，比两项监管费加起来还多。"""
    out = C.us_stock(200.0, 500.0, "sell", spread_bp=1.0, sec_rate=20.6e-6, taf_per_share=0.000166)
    assert out["佣金"] == 0.0
    assert out["半个价差"] > out["SEC 费"] + out["FINRA TAF"]


def test_cost_in_r_depends_on_where_the_stop_is():
    """同样 0.05% 的单边成本，止损放 10% 只占 0.01R，放 0.5% 就占 0.2R。"""
    assert C.cost_in_r(0.0005, 0.10) == pytest.approx(0.01)
    assert C.cost_in_r(0.0005, 0.005) == pytest.approx(0.20)
    with pytest.raises(ValueError):
        C.cost_in_r(0.0005, 0.0)


def test_annual_drag_is_linear_in_frequency():
    assert C.annual_drag(0.0005, 30) == pytest.approx(0.03)
    assert C.annual_drag(0.0005, 300) == pytest.approx(0.30)   # 频率翻十倍，成本也翻十倍
    table = C.frequency_table(0.0005)
    assert list(table.columns) == ["每年交易笔数", "每年的成本"]
    assert table["每年的成本"].is_monotonic_increasing


def test_corwin_schultz_is_exact_when_there_is_no_volatility():
    """价格不动、只有一个固定的价差时，这个估计量应该精确地把价差还原出来。"""
    for spread in [0.001, 0.005, 0.02]:
        price = pd.Series([100.0] * 10)
        high, low = price * (1 + spread / 2), price * (1 - spread / 2)
        estimate = C.corwin_schultz(high, low).dropna()
        assert estimate.to_numpy() == pytest.approx(spread, rel=1e-9)


def test_corwin_schultz_falls_apart_when_volatility_dominates():
    """真实市场上波动远大于价差，估计量会满地负数——第 28 篇量到 SPY 有一半的日子是负的。"""
    rng = np.random.default_rng(28)
    close = pd.Series(100 * np.exp(np.cumsum(rng.standard_normal(2_000) * 0.02)))
    noise = np.abs(rng.standard_normal(2_000)) * 0.02
    estimate = C.corwin_schultz(close * (1 + noise), close * (1 - noise)).dropna()
    assert (estimate < 0).mean() > 0.2                      # 大量负数＝它在这里是噪声


# ---------------------------------------------------------------------------
# 费率的解析（data 模块）
# ---------------------------------------------------------------------------

SEC_PAGE = """<p>Section 31 Transaction Fee Rate Advisory for Fiscal Year 2026.
Feb. 27, 2026 &mdash; The Securities and Exchange Commission today announced that
starting on April 4, 2026, the fee rates applicable to most securities transactions
will be set at $20.60 per million dollars.</p>"""

FINRA_PAGE = """<div>(3) Fee Rates (A) Each member shall pay to FINRA a fee per share
for each sale of a covered equity security of $0.000166 per share for each sale of a
covered equity security, with a maximum charge of $8.30 per transaction.</div>"""


def test_parse_sec_fee_advisory():
    out = D.parse_sec_fee_advisory(SEC_PAGE)
    assert out["财年"] == 2026
    assert out["每百万美元"] == pytest.approx(20.60)
    assert out["占卖出金额"] == pytest.approx(20.60 / 1e6)
    assert out["生效日"] == pd.Timestamp("2026-04-04")
    with pytest.raises(ValueError):
        D.parse_sec_fee_advisory("<p>今天天气不错</p>")


def test_parse_finra_taf():
    out = D.parse_finra_taf(FINRA_PAGE)
    assert out["每股"] == pytest.approx(0.000166)
    assert out["每笔上限"] == pytest.approx(8.30)
    with pytest.raises(ValueError):
        D.parse_finra_taf("<p>今天天气也不错</p>")


def test_load_binance_book_ticker_round_trip(tmp_path):
    frame = pd.DataFrame({"time": pd.date_range("2024-01-11", periods=3, freq="min", tz="UTC"),
                          "更新次数": [10, 20, 30], "价差": [0.03, 0.04, 0.05],
                          "最宽价差": [0.1, 0.2, 0.3], "买一量": [1.0, 2.0, 3.0],
                          "卖一量": [1.5, 2.5, 3.5], "中间价": [46000.0, 46010.0, 46020.0]})
    path = tmp_path / "BTCUSDT-bookTicker-1m-2024-01-11.csv.gz"
    frame.to_csv(path, index=False)
    out = D.load_binance_book_ticker([path])
    assert len(out) == 3
    assert str(out.index.tz) == "UTC"
    assert out["价差"].median() == pytest.approx(0.04)
