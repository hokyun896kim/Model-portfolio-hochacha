"""4단계 — 종목 선정 (Bottom-up).

섹터 목표 비중(주식 부분)을 섹터 내 종목에 배분한다.

- 유니버스에 종목이 없는 섹터의 예산은 보유 섹터에 비례 재배분해
  TAA 주식 비중이 전부 집행되도록 한다.
- 섹터 내 비중 = 벤치마크 앵커(시총 비중 셰어)와 Bottom-up 점수 셰어의
  블렌드. 순수 점수 비례는 초대형주(예: 삼성전자)의 벤치마크 대비
  언더웨이트를 과도하게 키우므로, 벤치마크에 앵커링한 뒤 점수로
  기울인다. 블렌드 비율은 constraints["bm_anchor_alpha"] (기본 0.5).
- 점수는 실적 모멘텀·밸류에이션·퀄리티에 대한 1~5점 정성 평가.
"""


def allocate_stocks(universe: list, sector_targets: dict, equity_pct: float,
                    constraints: dict, stock_bm_weights: dict = None) -> list:
    """포트폴리오 전체 기준 종목별 비중(%) 리스트를 반환한다."""
    stock_bm_weights = stock_bm_weights or {}
    max_w = constraints.get("max_stock_weight_pct", 100.0)
    min_w = constraints.get("min_stock_weight_pct", 0.0)
    alpha = constraints.get("bm_anchor_alpha", 0.5)

    by_sector = {}
    for stock in universe:
        by_sector.setdefault(stock["sector"], []).append(stock)

    # 보유 섹터의 목표 비중 합으로 재정규화 (미보유 섹터 예산 재배분)
    covered_total = sum(t["target_pct"] for s, t in sector_targets.items()
                        if s in by_sector)

    holdings = []
    for sector, stocks in by_sector.items():
        target = sector_targets.get(sector, {}).get("target_pct", 0.0)
        sector_budget = equity_pct * target / covered_total
        score_sum = sum(s["score"] for s in stocks)
        bm_sum = sum(stock_bm_weights.get(s["code"], 0.0) for s in stocks)
        for s in stocks:
            score_share = s["score"] / score_sum
            bm_share = (stock_bm_weights.get(s["code"], 0.0) / bm_sum
                        if bm_sum > 0 else score_share)
            share = alpha * bm_share + (1.0 - alpha) * score_share
            holdings.append({**s, "weight_pct": sector_budget * share})

    # 최대 비중 제약 적용 후, 잘린 만큼을 여유 종목에 점수 비례 재배분
    capped = sum(max(0.0, h["weight_pct"] - max_w) for h in holdings)
    for h in holdings:
        h["weight_pct"] = min(h["weight_pct"], max_w)
    if capped > 0:
        room = [h for h in holdings if h["weight_pct"] < max_w]
        score_sum = sum(h["score"] for h in room)
        for h in room:
            h["weight_pct"] = min(max_w, h["weight_pct"] + capped * h["score"] / score_sum)

    holdings = [h for h in holdings if h["weight_pct"] >= min_w]
    holdings.sort(key=lambda h: -h["weight_pct"])
    for h in holdings:
        h["weight_pct"] = round(h["weight_pct"], 2)
    return holdings
