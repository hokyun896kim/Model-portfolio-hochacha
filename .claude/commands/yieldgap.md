# /yieldgap — STEP 1 단독 갱신

1. Fwd PER(폴백: 트레일링, 명시)·국고10년을 수집한다. 출처+asof 병기, 실패 시 N/A(HARD 1).
2. `python3 -c` 또는 스크립트로 `src.saa.compute_saa` 실행, 결과를 보고한다.
3. 극단값 프로토콜(Fwd PER <7 또는 >16) 해당 시 트레일링 병기 산출 포함.
4. state를 갱신하려면 /weekly 전체 실행을 사용한다 (단독 갱신은 보고만).
