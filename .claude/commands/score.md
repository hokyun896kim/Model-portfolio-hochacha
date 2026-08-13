# /score — 스코어보드 갱신

CLD vs TDY vs KOSPI vs 복합BM 성과를 갱신해 `scoreboard.md`에 기록한다.

1. 각 트랙의 체결 기준가(익영업일 시가)와 현재가를 수집(출처+asof 병기, 실패 시 N/A).
2. TR 회계·왕복 비용 동일 적용(HARD 5). 트랙별 턴오버·누적 비용 병기.
3. 주간·누적 수익률, MDD, 변동성, 승률(vs TDY / vs KOSPI) 계산.
4. View 채점: 지난주 틸트 방향 적중 여부 1줄 (스코어카드 vs 재량 각각).
5. 월 1회 기여도 분해: SAA / 틸트(스코어카드) / 재량 / 섹터 / 종목 / 채권.
6. scoreboard.md는 append 방식으로 주차 행 추가 — 과거 행 수정 금지(HARD 8).
