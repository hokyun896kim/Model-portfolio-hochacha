"""2단계 — 전술적 자산배분 (TAA): TAA = SAA ± View.

사전 균형비중(Prior, = SAA Yield Gap 비중)에 매크로·투자전략 관점의
정성적 View(±%p)를 더해 사후비중을 만드는 Black-Litterman식 구조.
"""

from dataclasses import dataclass

# View 가감폭 한도: 정성 판단이 모형을 압도하지 않도록 ±10%p로 제한
MAX_VIEW_TILT_PP = 10.0


@dataclass
class TAAResult:
    saa_stock_pct: float
    view_tilt_pp: float
    stance: str
    rationale: list
    stock_weight_pct: float
    cash_weight_pct: float


def compute_taa(saa_stock_pct: float, view: dict) -> TAAResult:
    tilt = float(view.get("tilt_pp", 0.0))
    tilt = max(-MAX_VIEW_TILT_PP, min(MAX_VIEW_TILT_PP, tilt))
    stock = max(0.0, min(100.0, saa_stock_pct + tilt))
    return TAAResult(
        saa_stock_pct=saa_stock_pct,
        view_tilt_pp=tilt,
        stance=view.get("stance", "Neutral"),
        rationale=list(view.get("rationale", [])),
        stock_weight_pct=round(stock, 1),
        cash_weight_pct=round(100.0 - stock, 1),
    )
