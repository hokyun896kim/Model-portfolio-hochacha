"""1단계 — 전략적 자산배분 (SAA): Yield Gap 모형.

Earnings Yield = 1 / PER
Yield Gap      = Earnings Yield − 10Y 국채금리
주식 비중       = EY / (EY + 10Y금리)   예) 8.3 / (8.3 + 4.3) = 66%
"""

from dataclasses import dataclass


@dataclass
class SAAResult:
    per: float
    earnings_yield_pct: float
    bond_yield_pct: float
    yield_gap_pp: float
    stock_weight_pct: float
    cash_weight_pct: float


def compute_saa(index_per: float, bond_yield_10y_pct: float) -> SAAResult:
    if index_per <= 0:
        raise ValueError("PER은 양수여야 합니다.")
    if bond_yield_10y_pct <= 0:
        raise ValueError("10Y 금리는 양수여야 합니다.")

    ey = 100.0 / index_per
    stock = 100.0 * ey / (ey + bond_yield_10y_pct)
    return SAAResult(
        per=index_per,
        earnings_yield_pct=round(ey, 2),
        bond_yield_pct=bond_yield_10y_pct,
        yield_gap_pp=round(ey - bond_yield_10y_pct, 2),
        stock_weight_pct=round(stock, 1),
        cash_weight_pct=round(100.0 - stock, 1),
    )
