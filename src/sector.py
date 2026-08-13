"""STEP 3 — 섹터 배분 검증 (순수 계산).

BM 대비 액티브 편차 한도: 섹터당 ±active_cap_pp, 단일 섹터 절대 상한.
STEP 5 계산(액티브 셰어, 편차 테이블)도 여기서 제공.
"""


def validate_sector_targets(targets: dict, bm_weights: dict, params: dict) -> dict:
    """targets/bm_weights: {섹터: 주식파트 내 %}. 위반 목록과 편차 테이블 반환."""
    p = params["sector"]
    violations, table = [], []
    total = sum(targets.values())
    if abs(total - 100.0) > 0.5:
        violations.append(f"섹터 목표 합 {total:.1f}% ≠ 100%")

    for sector, tgt in sorted(targets.items(), key=lambda kv: -kv[1]):
        bm = bm_weights.get(sector)
        active = None if bm is None else round(tgt - bm, 2)
        table.append({"sector": sector, "target_pct": round(tgt, 2),
                      "bm_pct": bm, "active_pp": active})
        if tgt > p["single_sector_abs_max_pct"]:
            violations.append(
                f"단일 섹터 절대 상한 초과: {sector} {tgt:.1f}% > {p['single_sector_abs_max_pct']}%")
        if active is not None and abs(active) > p["active_cap_pp"]:
            violations.append(
                f"섹터 액티브 한도 초과: {sector} {active:+.1f}%p (한도 ±{p['active_cap_pp']}%p)")

    return {"table": table, "violations": violations,
            "bm_available": bool(bm_weights)}


def active_share(stock_weights: dict, bm_stock_weights: dict) -> float:
    """액티브 셰어 = 0.5 * Σ|w_i - bm_i| (주식파트 내 % 기준)."""
    codes = set(stock_weights) | set(bm_stock_weights)
    return round(0.5 * sum(abs(stock_weights.get(c, 0.0) - bm_stock_weights.get(c, 0.0))
                           for c in codes), 2)
