# K-MODEL PORTFOLIO 배틀판 (TDY vs CLD)

같은 방법론, 다른 두뇌. 팀더윤쎈 6단계 방법론의 '판단'을 Claude가 독립 수행하는
모델 포트폴리오(**CLD**)를 운용하고, TDY·KOSPI·복합BM과 성과를 비교한다.

- **단일 규범(SSOT): [`CLAUDE.md`](CLAUDE.md)** — 모든 규칙은 이 문서가 우선한다.
- 파라미터: `config/params.yaml` (모든 숫자의 유일한 서식지)
- 실행: `.claude/commands/` — `/weekly` `/tdy-input` `/score` `/yieldgap` `/macro` `/screen` `/audit`
- 계산 엔진: `src/` — 데이터 수집(datafeed) + 순수 계산(saa/taa/sector/screen) +
  부수효과는 rebalance에만, 리포트는 report.
- 기록: `state/` `portfolios/` `ledger/`(append-only) `reports/` `scoreboard.md`

> ※ 본 저장소의 모든 산출은 CLD 모델 산출(페이퍼 트랙)이며 실계좌에 대한 추천이 아닙니다.
