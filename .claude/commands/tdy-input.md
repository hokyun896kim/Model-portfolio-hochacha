# /tdy-input — TDY 변경 수시 입력

운용자가 전달한 TDY(팀더윤쎈 공개 모델포트) 변경 내역을 기록한다.

## 순서 규칙 (HARD 4)
- CLD 평가일 당일에는 해당 주차 CLD ledger 기록이 존재해야만 입력 가능.
- 이 세션에서 `/tdy-input` 실행 후 `/weekly` 연속 실행 금지 (역순은 허용).

## 절차
1. 운용자 입력에서 종목·비중·**change_date**(TDY 실제 변경일)를 파싱한다. change_date 누락 시 요청.
2. `portfolios/tdy.json` 갱신: `{version, asof, weights{}, changes[]}` —
   각 변경에 `change_date`와 `input_date`(오늘)를 분리 저장.
3. 체결 평가는 **change_date의 익영업일 시가** 기준 소급 적용(§3). 동일 비용·TR 회계.
4. 원본 비중과 시스템 평가 비중이 다르면 병기. CHANGELOG.md 기록.
5. CLD 판단에는 이 데이터를 절대 사용하지 않는다.
