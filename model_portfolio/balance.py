"""5단계 — 벤치마크 대비 균형.

KOSPI 벤치마크 대비 종목/섹터 액티브 비중(괴리)을 계산하고,
한도를 넘는 항목에 경고를 남겨 포트폴리오 균형을 점검한다.
"""


def check_balance(holdings: list, sector_targets: dict,
                  stock_bm_weights: dict, constraints: dict) -> dict:
    max_stock_active = constraints.get("max_stock_active_pp", 100.0)
    max_sector_active = constraints.get("max_sector_active_pp", 100.0)

    warnings = []
    for h in holdings:
        bm = stock_bm_weights.get(h["code"], 0.0)
        h["benchmark_pct"] = bm
        h["active_pp"] = round(h["weight_pct"] - bm, 2)
        if abs(h["active_pp"]) > max_stock_active:
            warnings.append(
                f"종목 액티브 한도 초과: {h['name']} {h['active_pp']:+.2f}%p "
                f"(한도 ±{max_stock_active}%p)")

    for sector, t in sector_targets.items():
        if abs(t["active_pp"]) > max_sector_active:
            warnings.append(
                f"섹터 액티브 한도 초과: {sector} {t['active_pp']:+.2f}%p "
                f"(한도 ±{max_sector_active}%p)")

    return {"warnings": warnings}
