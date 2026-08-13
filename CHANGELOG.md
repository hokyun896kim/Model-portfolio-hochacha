# CHANGELOG

## 2026-08-13 — 첫 /weekly 실행

- 데이터 수집 검증 리포트 발행(`reports/setup-validation-2026-08-13.md`) — 클라우드 환경
  KRX/ECOS/DART/FnGuide 전부 차단 확인, 수기 폴백 경로로 첫 사이클 진행.
- CLD 첫 산출: SAA 80.2%(Fwd PER 5.7배·국고10Y 4.33%, 극단값 프로토콜 발동 — 트레일링 병기 55.7%),
  스코어카드 +1점→+2.5%p, 재량 오버라이드 0%p(사유 3줄 기록), 최종 주식 80.2%/국고채 ETF 19.8%.
- 20종목 initial 편입 + KOSEF 국고채10년(148070). ledger/2026-08-13.json 기록,
  체결 기준 2026-08-14 시가. scoreboard.md 골격 생성.

## 2026-08-13 — v0.4.1 초기 셋업 (§10 시행)

- CLAUDE.md v0.4-draft를 SSOT로 편입, 배틀판 구조로 저장소 전면 개편.
- 구 프로토타입(`model_portfolio/`, `run.py`, `output/`, `data/snapshot_*.json`) 제거 —
  파라미터 하드코딩(HARD 7 위반 구조)으로 신규 체계와 병존 불가. git 이력에 보존.
- `config/params.yaml` 신설 — CLAUDE.md의 [ ] 예시 기본값을 확정치로 등재.
- `src/` 구현: datafeed / saa / taa / sector / screen / rebalance / report.
- `.claude/commands/` 7종: weekly, tdy-input, score, yieldgap, macro, screen, audit.
- **§4 표 갱신 (Fwd PER 소스 확정)**: 1순위 = FnGuide(comp.fnguide.com) 크롤 — 단,
  현 클라우드 실행 환경에서는 KRX·ECOS·FnGuide 전부 이그레스 차단 확인(셋업 검증 리포트 참조).
  클라우드 세션의 작동 경로는 웹검색 → `data/manual/<날짜>.json` 수기 기록(출처+asof 병기).
  로컬 실행 시 pykrx·ECOS 1순위 경로 활성화(코드 구현 완료, .env 키 필요).
- CLAUDE.md 버전 표기는 v0.4-draft 유지(문서 본문 개정은 운용자 승인 사항) —
  params.yaml version=0.4.1로 셋업 이력 관리.
