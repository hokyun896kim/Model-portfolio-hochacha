"""한국주식 모델 포트폴리오 엔진.

6단계: SAA(Yield Gap) → TAA(± View) → 섹터 배분 → Bottom-up 종목 선정
→ 벤치마크 균형 → 리밸런싱.
"""

from .build import build_portfolio  # noqa: F401
