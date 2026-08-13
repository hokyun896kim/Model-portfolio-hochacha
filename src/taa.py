"""STEP 2 — TAA: 스코어카드 + Claude 재량 (순수 계산 + 검증).

TAA = SAA ± View. 총 틸트 하드캡 ±tilt_cap_pp, 최종 TAA도 [40, 85] 캡 내.
스코어카드 5항목 각 -1/0/+1 → 합계 → 매핑 틸트.
재량 오버라이드: 사유 3줄 이상 필수, 틸트_스코어카드/틸트_최종 분리 기록.
"""

SCORECARD_KEYS = ["exports_yoy", "usdkrw_trend", "foreign_flow_20d",
                  "curve_3_10", "bok_stance"]


def map_score_to_tilt(total: int, params: dict) -> float:
    for band in params["taa"]["scorecard_mapping"]:
        if band["min"] <= total <= band["max"]:
            return float(band["tilt_pp"])
    raise ValueError(f"스코어 합계 {total}가 매핑 구간 밖")


def compute_taa(saa_equity_pct: float, scorecard: dict, override: dict,
                params: dict) -> dict:
    """scorecard: {key: {"score": -1|0|1, "basis": str, "source": str}}
    override: {"tilt_pp": float|None, "reasons": [str, ...]}  (None이면 스코어카드 채택)
    """
    p = params["taa"]
    for key in SCORECARD_KEYS:
        if key not in scorecard:
            raise ValueError(f"스코어카드 항목 누락: {key}")
        if scorecard[key]["score"] not in (-1, 0, 1):
            raise ValueError(f"스코어 범위 위반: {key}={scorecard[key]['score']}")

    total = sum(scorecard[k]["score"] for k in SCORECARD_KEYS)
    tilt_scorecard = map_score_to_tilt(total, params)

    tilt_final = tilt_scorecard
    override_applied = False
    if override.get("tilt_pp") is not None:
        reasons = [r for r in override.get("reasons", []) if r.strip()]
        if len(reasons) < p["override_min_reason_lines"]:
            raise ValueError(
                f"재량 오버라이드 사유 {p['override_min_reason_lines']}줄 미만 — 거부")
        tilt_final = float(override["tilt_pp"])
        override_applied = True

    cap = p["tilt_cap_pp"]
    tilt_final = max(-cap, min(cap, tilt_final))

    lo, hi = params["saa"]["equity_min_pct"], params["saa"]["equity_max_pct"]
    equity = max(lo, min(hi, saa_equity_pct + tilt_final))

    return {
        "scorecard": scorecard,
        "score_total": total,
        "tilt_scorecard_pp": tilt_scorecard,
        "tilt_final_pp": tilt_final,
        "override_applied": override_applied,
        "override_reasons": override.get("reasons", []),
        "discretion_delta_pp": round(tilt_final - tilt_scorecard, 2),
        "equity_pct": round(equity, 1),
        "bond_pct": round(100.0 - equity, 1),
    }


def bond_sensitivity(bond_pct: float, duration_years: float) -> dict:
    """국고채 ETF 파트의 금리 ±100bp 손익 근사 (포트폴리오 전체 기준 %)."""
    move = duration_years * 1.0
    return {"duration_years": duration_years,
            "pnl_pct_per_100bp": round(move * bond_pct / 100.0, 2)}
