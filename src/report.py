"""주간 배틀 리포트 렌더링 (§9 템플릿) — 순수 함수."""

SCORECARD_LABELS = {
    "exports_yoy": "① 수출증가율 YoY",
    "usdkrw_trend": "② 원/달러 20일 추세",
    "foreign_flow_20d": "③ 외국인 KOSPI 20일 누적 순매수",
    "curve_3_10": "④ 국고 3-10년 스프레드",
    "bok_stance": "⑤ 한은 정책 스탠스",
}

DISCLAIMER = ("※ 본 리포트는 CLD 모델 산출(페이퍼 트랙)이며 실계좌에 대한 "
              "추천이 아닙니다. 모든 정보는 참고용입니다.")


def render_weekly(ctx: dict) -> str:
    saa, taa = ctx["saa"], ctx["taa"]
    lines = []
    add = lines.append

    add(f"# 주간 배틀 리포트 — {ctx['date']}")
    add("")
    if ctx["banners"]:
        add("⚠️ 데이터 경고:")
        for b in ctx["banners"]:
            add(f"- ⚠️ {b}")
        add("")

    per_label = "Fwd PER" if saa["per_kind"] == "fwd" else "트레일링 PER(대체)"
    z = saa["yield_gap_z"] if saa["yield_gap_z"] is not None else "N/A"
    add("## 1. SAA")
    add(f"- {per_label} **{saa['per_value']}배** "
        f"(asof {ctx['per_datum'].asof}, {ctx['per_datum'].source}) | "
        f"국고10Y **{saa['bond10y_pct']}%** "
        f"(asof {ctx['by10'].asof}, {ctx['by10'].source})")
    add(f"- EY {saa['ey_pct']}% | Yield Gap **{saa['yield_gap_pp']:+.2f}%p** (z={z})")
    clip_note = f" (원산출 {saa['raw_equity_pct']}% → 클리핑)" if saa["clipped"] else ""
    add(f"- 기본 주식비중 **{saa['equity_pct']}%**{clip_note}")
    if saa["extreme_per"] and saa["trailing_calc"]:
        t = saa["trailing_calc"]
        add(f"- 극단값 프로토콜: 트레일링 {t['trailing_per']}배 기준 병기 → "
            f"주식비중 {t['clipped_equity_pct']}% (원산출 {t['raw_equity_pct']}%)")
    add("")

    add("## 2. TAA")
    add(f"- 스코어카드 합계 **{taa['score_total']}점** → {taa['tilt_scorecard_pp']:+.1f}%p")
    for key, label in SCORECARD_LABELS.items():
        it = taa["scorecard"][key]
        add(f"  - {label}: **{it['score']:+d}** — {it['basis']} ({it['source']})")
    if taa["override_applied"]:
        add(f"- 재량 오버라이드: **{taa['tilt_final_pp']:+.1f}%p** "
            f"(스코어카드 대비 {taa['discretion_delta_pp']:+.1f}%p)")
        for r in taa["override_reasons"]:
            add(f"  - {r}")
    else:
        add("- 재량 오버라이드: 없음 (스코어카드 채택)")
    bs = ctx["bond_sens"]
    add(f"- **최종 주식 {taa['equity_pct']}% / 국고채 ETF {taa['bond_pct']}%** "
        f"(듀레이션 {bs['duration_years']}년, ±100bp ≈ ∓{bs['pnl_pct_per_100bp']}% 포트 기준)")
    add("")

    add("## 3. 섹터")
    add("")
    add("| 섹터 | 목표(주식 내) | BM | 액티브 |")
    add("|---|---:|---:|---:|")
    for row in ctx["sector"]["table"]:
        bm = f"{row['bm_pct']:.1f}%" if row["bm_pct"] is not None else "N/A"
        act = f"{row['active_pp']:+.1f}%p" if row["active_pp"] is not None else "N/A"
        add(f"| {row['sector']} | {row['target_pct']:.1f}% | {bm} | {act} |")
    add("")
    for sector, r in ctx["sector_rationale"].items():
        add(f"- **{sector}**: {r['basis']} ({r['source']})")
    add("")

    add("## 4. 종목 (선정 카드)")
    add("")
    add("| 종목 | 코드 | 섹터 | 비중 |")
    add("|---|---|---|---:|")
    for s in sorted(ctx["picks"], key=lambda x: -x["weight_pct"]):
        add(f"| {s['name']} | {s['code']} | {s['sector']} | {s['weight_pct']:.1f}% |")
    conc = ctx["screen"]["concentration"]
    add(f"| **주식 합계** | | {conc['names']}종목 | **{taa['equity_pct']:.1f}%** |")
    add("")
    add(f"상위 5종목 합: {conc['top5_pct']}% (한도 {ctx['params']['screen']['top5_max_pct']}%)")
    add("")
    for s in sorted(ctx["picks"], key=lambda x: -x["weight_pct"]):
        c = s["card"]
        add(f"<details><summary>선정 카드 — {s['name']} ({s['weight_pct']:.1f}%)</summary>")
        add("")
        for t in c["thesis"]:
            add(f"- 논리: {t}")
        add(f"- 반대논리: {c['counter']}")
        add(f"- 무효화 조건: {c['invalidation']}")
        add(f"- 편입: {c['entry_date']} / {c['entry_basis']}")
        add("")
        add("</details>")
    add("")

    add("## 5. 리밸런싱")
    led = ctx["ledger"]
    add(f"- 구분: **{led['kind']}** | 체결: {led['execution_basis']} | "
        f"왕복 비용 {led['roundtrip_cost_pct']}%")
    if led["trades"]:
        add("")
        add("| 코드 | 방향 | 현재 | 목표 |")
        add("|---|---|---:|---:|")
        for t in led["trades"]:
            add(f"| {t['code']} | {t['side']} | {t['from_pct']}% | {t['to_pct']}% |")
    else:
        add("- 밴드 이탈 없음 — 매매 없음")
    add("")

    add("## 6. 배틀 현황")
    add("- 첫 주차: 성과 비교는 체결 기준가 확정 후 scoreboard.md에서 개시.")
    add("")

    add("## 7. 다음 주 점검 포인트")
    for w in ctx["next_week_watch"]:
        add(f"- {w}")
    add("")
    add(f"> {DISCLAIMER}")
    add("")
    return "\n".join(lines)


def scoreboard_skeleton(date_str: str, exec_date: str) -> str:
    return f"""# 스코어보드 — CLD vs TDY vs KOSPI vs 복합BM

기준: TR 회계, 체결 = 평가일 익영업일 시가, 왕복 비용 동일 적용.
개시일: {date_str} (첫 체결 기준 {exec_date} 시가 — 기준가 확정 후 수익률 계산 개시)

| 주차 | CLD | TDY | KOSPI | 복합BM | CLD vs TDY | CLD vs KOSPI |
|---|---:|---:|---:|---:|---:|---:|
| {date_str} (개시) | — | — | — | — | — | — |

- 누적: N/A (개시 주)
- MDD / 변동성 / 승률: N/A (개시 주)
- 턴오버·누적 비용: CLD 0.0% / TDY N/A(미입력)
- View 채점: N/A (다음 주부터)
"""
