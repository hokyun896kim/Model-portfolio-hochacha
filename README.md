# Model Portfolio Hochacha — 한국주식 모델 포트폴리오

Yield Gap 기반 자산배분 → 매크로 View → 섹터 배분 → Bottom-up 종목 선정 → 벤치마크 균형 → 주간 리밸런싱의
6단계 방법론을 코드로 구현한 한국주식(KOSPI) 모델 포트폴리오 엔진입니다.

> ※ 본 저장소의 모든 정보 및 산출물은 참고용이며 법적·재정적·투자적 조언으로 간주되지 않습니다.

## 구성 방법론 (6단계)

| 단계 | 이름 | 내용 | 구현 |
|---|---|---|---|
| 1 | 전략적 자산배분 (SAA) | Yield Gap 모형으로 주식/현금(채권) 비중의 기준을 설정 | `model_portfolio/saa.py` |
| 2 | 전술적 자산배분 (TAA) | 매크로 분석·투자전략 관점의 정성적 View로 비중 확대/축소 (`TAA = SAA ± View`) | `model_portfolio/taa.py` |
| 3 | 섹터 배분 | 섹터·스타일·벤치마크 분석으로 유효한 테마를 선별, 벤치마크 대비 오버/언더웨이트 | `model_portfolio/sector.py` |
| 4 | 종목 선정 (Bottom-up) | 섹터 내에서 Bottom-up 점수(실적 모멘텀·밸류에이션·퀄리티)로 개별 종목 발굴 | `model_portfolio/selection.py` |
| 5 | 벤치마크 대비 균형 | KOSPI 대비 종목/섹터 액티브 비중 한도를 점검해 포트폴리오 균형 조정 | `model_portfolio/balance.py` |
| 6 | 리밸런싱 | 주간 단위 평가, 밴드 이탈 시 리밸런싱 또는 재평가 실행 | `model_portfolio/rebalance.py` |

### 1. SAA — Yield Gap 모형

```
Earnings Yield = 1 / PER
Yield Gap      = Earnings Yield − 10Y 국채금리
주식 비중       = EY / (EY + 10Y금리)      # 예: 8.3 / (8.3 + 4.3) = 66%
```

"지금 주식 투자를 한다면 얼마나 할 때인가?"에 대한 기본 원칙입니다.
Earnings Yield가 금리 대비 얼마나 매력적인지를 기준으로 판단하며,
이해하기 쉬우면서 저가 매수·고가 매도를 기계적으로 반복하게 해 줍니다.

### 2. TAA — SAA ± View

Black-Litterman 류 자산배분 모형처럼 **사전 균형비중(Prior, = SAA) + View 반영 → 사후비중** 구조입니다.
매크로 분석으로 현재가 투자에 유리한 국면인지 판단하고, Yield Gap상 기준 비중 대비 ±가감합니다
(예: Favorable 판단 시 +5%p).

### 3~5. 섹터 배분 · 종목 선정 · 벤치마크 균형

- 섹터별 벤치마크(KOSPI 근사) 비중에 View 기반 tilt(±%p)를 더해 섹터 목표 비중을 만듭니다.
- 섹터 내에서는 Bottom-up 점수 비례로 종목 비중을 배분합니다.
- 종목/섹터 액티브 비중(벤치마크 대비 괴리)이 한도를 넘으면 경고를 출력해 균형을 조정합니다.

### 6. 리밸런싱

주간 평가를 기본으로, 종목 비중이 목표 대비 밴드(절대 ±2%p 또는 상대 ±20%)를 이탈하면 리밸런싱,
Yield Gap이 크게 움직이면(±0.5%p) SAA 자체를 재평가합니다.

## 사용법

```bash
python3 run.py                          # 최신 스냅샷으로 리포트 생성
python3 run.py --snapshot data/snapshot_2026-08-13.json
```

산출물은 `output/MODEL_PORTFOLIO_<날짜>.md`로 저장됩니다.

## 데이터 갱신

시장 입력값(지수 PER, 10Y 금리, 섹터 벤치마크 비중, 종목 유니버스와 Bottom-up 점수)은 전부
`data/snapshot_*.json` 한 파일에 들어 있습니다. 주간 리밸런싱 때 이 파일만 새 날짜로 복사해
값을 갱신하고 다시 실행하면 됩니다. 스냅샷의 출처와 근사치 여부는 파일 안 `meta.notes`에 기록합니다.
