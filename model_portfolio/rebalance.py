"""6단계 — 리밸런싱: 주간 평가 기준과 트리거를 명문화한다.

- 주간 단위로 포트폴리오를 평가한다.
- 종목 비중이 목표 대비 밴드(절대 %p 또는 상대 %)를 이탈하면 리밸런싱.
- Yield Gap이 기준치 이상 움직이면 SAA 자체를 재평가.
"""


def describe_rules(rules: dict) -> list:
    return [
        f"평가 주기: {rules.get('review_frequency', 'weekly')} (주간 평가·리밸런싱)",
        (f"종목 드리프트 밴드: 목표 대비 절대 ±{rules.get('drift_band_abs_pp', 2.0)}%p "
         f"또는 상대 ±{rules.get('drift_band_rel_pct', 20.0)}% 이탈 시 리밸런싱"),
        (f"SAA 재평가: Yield Gap이 ±{rules.get('saa_reeval_yieldgap_move_pp', 0.5)}%p "
         "이상 변하면 1단계부터 재산출"),
        "Bottom-up 점수와 섹터 View는 주간 평가에서 재검토",
    ]


def drift_check(holdings: list, current_weights: dict, rules: dict) -> list:
    """실측 비중(dict: code -> %)을 받아 밴드 이탈 종목 목록을 반환한다."""
    abs_band = rules.get("drift_band_abs_pp", 2.0)
    rel_band = rules.get("drift_band_rel_pct", 20.0)
    out = []
    for h in holdings:
        cur = current_weights.get(h["code"])
        if cur is None:
            continue
        drift = cur - h["weight_pct"]
        rel = 100.0 * abs(drift) / h["weight_pct"] if h["weight_pct"] else 0.0
        if abs(drift) > abs_band or rel > rel_band:
            out.append({"name": h["name"], "code": h["code"],
                        "target_pct": h["weight_pct"], "current_pct": cur,
                        "drift_pp": round(drift, 2)})
    return out
