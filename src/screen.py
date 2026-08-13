"""STEP 4 — 종목 선정 검증 (순수 계산).

한도: 종목 수 [min, max], 종목당 상한, 최소 편입, 상위 5종목 합.
선정 카드 필수 필드: thesis(3줄) / counter(1줄) / invalidation / entry_date, entry_basis.
가드레일 위반 포트폴리오는 출력 금지(HARD 6) — 위반 목록을 반환해 호출자가 중단.
"""

CARD_FIELDS = ["thesis", "counter", "invalidation", "entry_date", "entry_basis"]


def validate_picks(picks: list, equity_pct: float, params: dict) -> dict:
    """picks: [{name, code, sector, weight_pct(포트 전체 기준), card{...}}]"""
    p = params["screen"]
    violations = []

    n = len(picks)
    if not (p["min_names"] <= n <= p["max_names"]):
        violations.append(f"종목 수 {n}개 — 허용 [{p['min_names']}, {p['max_names']}]")

    total = sum(s["weight_pct"] for s in picks)
    if abs(total - equity_pct) > 0.5:
        violations.append(f"종목 비중 합 {total:.1f}% ≠ 주식 비중 {equity_pct:.1f}%")

    for s in picks:
        if s["weight_pct"] > p["stock_max_pct"]:
            violations.append(f"종목 상한 초과: {s['name']} {s['weight_pct']:.1f}% > {p['stock_max_pct']}%")
        if s["weight_pct"] < p["stock_min_pct"]:
            violations.append(f"최소 편입 미달: {s['name']} {s['weight_pct']:.1f}% < {p['stock_min_pct']}%")
        card = s.get("card", {})
        missing = [f for f in CARD_FIELDS if not card.get(f)]
        if missing:
            violations.append(f"선정 카드 필드 누락: {s['name']} {missing}")
        thesis = card.get("thesis", [])
        if isinstance(thesis, list) and len(thesis) < 3:
            violations.append(f"투자논리 3줄 미만: {s['name']}")

    top5 = sum(sorted((s["weight_pct"] for s in picks), reverse=True)[:5])
    if top5 > p["top5_max_pct"]:
        violations.append(f"상위 5종목 합 {top5:.1f}% > {p['top5_max_pct']}%")

    concentration = {
        "top5_pct": round(top5, 2),
        "names": n,
    }
    return {"violations": violations, "concentration": concentration}
