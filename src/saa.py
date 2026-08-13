"""STEP 1 — SAA: Yield Gap 모형 (순수 계산).

EY = 1 / Fwd PER, BY = 국고10년, 기본 주식비중 = EY / (EY + BY).
클리핑 [equity_min, equity_max], 원산출값 병기.
극단값 프로토콜: Fwd PER가 [7, 16] 밖이면 트레일링 기준 산출 병기 요구.
"""


def compute_saa(per_value: float, per_kind: str, bond10y_pct: float,
                params: dict, trailing_per: float = None,
                yieldgap_history: list = None) -> dict:
    """순수 함수. per_kind: 'fwd' | 'trailing'(폴백 시)."""
    p = params["saa"]
    ey = 100.0 / per_value
    gap = ey - bond10y_pct
    raw = 100.0 * ey / (ey + bond10y_pct)
    clipped = max(p["equity_min_pct"], min(p["equity_max_pct"], raw))

    z = None
    if yieldgap_history and len(yieldgap_history) >= 30:
        mean = sum(yieldgap_history) / len(yieldgap_history)
        var = sum((g - mean) ** 2 for g in yieldgap_history) / len(yieldgap_history)
        z = (gap - mean) / (var ** 0.5) if var > 0 else None

    extreme = per_value < p["fwd_per_extreme_low"] or per_value > p["fwd_per_extreme_high"]
    trailing_calc = None
    if extreme and trailing_per:
        tey = 100.0 / trailing_per
        traw = 100.0 * tey / (tey + bond10y_pct)
        trailing_calc = {
            "trailing_per": trailing_per,
            "ey_pct": round(tey, 2),
            "raw_equity_pct": round(traw, 1),
            "clipped_equity_pct": round(
                max(p["equity_min_pct"], min(p["equity_max_pct"], traw)), 1),
        }

    return {
        "per_value": per_value,
        "per_kind": per_kind,
        "ey_pct": round(ey, 2),
        "bond10y_pct": bond10y_pct,
        "yield_gap_pp": round(gap, 2),
        "yield_gap_z": round(z, 2) if z is not None else None,
        "raw_equity_pct": round(raw, 1),
        "equity_pct": round(clipped, 1),
        "clipped": abs(clipped - raw) > 1e-9,
        "extreme_per": extreme,
        "trailing_calc": trailing_calc,
        "bond_pct": round(100.0 - clipped, 1),
    }
