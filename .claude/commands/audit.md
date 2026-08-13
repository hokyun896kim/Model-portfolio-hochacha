# /audit — 월 1회 정합성 감사

1. **4자 대조**: state/ ↔ reports/ ↔ CHANGELOG.md ↔ ledger/ 의 날짜·수치 일치 여부.
2. portfolios/*.json의 params_hash가 현재 config/params.yaml 해시와 일치하는지.
3. ledger append-only 확인: git 이력에서 기존 ledger 파일 수정 여부 점검.
4. **오염 규칙(HARD 4) 점검**: CLD 평가일에 tdy 입력이 선행된 기록이 없는지,
   판단 로그에 팀더윤쎈 참조 흔적이 없는지.
5. 발견된 규칙–실무 괴리는 목록화하고, 둘 중 무엇을 고칠지 명시 제안(CHANGELOG 초안 포함).
