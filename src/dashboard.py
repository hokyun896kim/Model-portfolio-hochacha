"""주간 대시보드 생성 — state/·portfolios/ JSON → reports/dashboard.html.

파생 뷰 렌더링 전용(상태를 만들지 않음). state·ledger 쓰기는 rebalance.py 관할.
실행: python3 -m src.dashboard
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSS = """
:root {
  --paper: #FAF9F7; --card: #FFFFFF; --ink: #201D1E; --muted: #6E6668;
  --line: #E5E0DE; --equity: #C4363C; --bond: #3A5FA8;
  --equity-soft: rgba(196,54,60,.09); --bond-soft: rgba(58,95,168,.09);
  --chip-zero: #EDEAE8; --warn-bg: #FBF3E3; --warn-ink: #7A5A18;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #1C1A1B; --card: #252223; --ink: #ECE7E5; --muted: #A39B9D;
    --line: #3A3536; --equity: #D96A6E; --bond: #6E93D6;
    --equity-soft: rgba(217,106,110,.14); --bond-soft: rgba(110,147,214,.14);
    --chip-zero: #363132; --warn-bg: #3A311C; --warn-ink: #E8C87A;
  }
}
:root[data-theme="dark"] {
  --paper: #1C1A1B; --card: #252223; --ink: #ECE7E5; --muted: #A39B9D;
  --line: #3A3536; --equity: #D96A6E; --bond: #6E93D6;
  --equity-soft: rgba(217,106,110,.14); --bond-soft: rgba(110,147,214,.14);
  --chip-zero: #363132; --warn-bg: #3A311C; --warn-ink: #E8C87A;
}
* { box-sizing: border-box; }
body {
  background: var(--paper); color: var(--ink); margin: 0;
  font-family: Pretendard, "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif;
  line-height: 1.55; font-size: 15px;
}
main { max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }
header.masthead { display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 16px;
  border-bottom: 2px solid var(--ink); padding-bottom: 14px; margin-bottom: 18px; }
.masthead h1 { font-size: 24px; font-weight: 800; letter-spacing: -.02em; margin: 0; }
.masthead .vs { color: var(--muted); font-weight: 600; font-size: 13px;
  text-transform: uppercase; letter-spacing: .08em; }
.masthead .asof { margin-left: auto; color: var(--muted); font-size: 13px;
  font-variant-numeric: tabular-nums; }
.banner { background: var(--warn-bg); color: var(--warn-ink); border-radius: 6px;
  padding: 8px 12px; font-size: 13px; margin: 6px 0; }
section { margin-top: 28px; }
h2 { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .09em;
  color: var(--muted); margin: 0 0 10px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
.tile { background: var(--card); border: 1px solid var(--line); border-radius: 8px;
  padding: 14px 16px; }
.tile .k { font-size: 12px; color: var(--muted); letter-spacing: .04em; }
.tile .v { font-size: 26px; font-weight: 800; letter-spacing: -.01em;
  font-variant-numeric: tabular-nums; margin-top: 2px; }
.tile .s { font-size: 12px; color: var(--muted); margin-top: 4px; }
.tile .v .unit { font-size: 15px; font-weight: 600; color: var(--muted); }
.allocbar { display: flex; gap: 2px; height: 40px; border-radius: 6px; overflow: hidden; }
.allocbar > div { display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 14px; font-variant-numeric: tabular-nums; }
.alloc-eq { background: var(--equity); }
.alloc-bd { background: var(--bond); }
.legend { display: flex; gap: 18px; margin-top: 8px; font-size: 13px; color: var(--muted); }
.legend .sw { display: inline-block; width: 10px; height: 10px; border-radius: 3px;
  margin-right: 6px; vertical-align: baseline; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 720px) { .cols { grid-template-columns: 1fr; } }
.scorerow { display: flex; align-items: center; gap: 10px; padding: 8px 0;
  border-bottom: 1px solid var(--line); font-size: 13.5px; }
.scorerow:last-child { border-bottom: 0; }
.scorerow .chip { flex: 0 0 44px; text-align: center; border-radius: 999px;
  font-weight: 800; font-size: 13px; padding: 3px 0; font-variant-numeric: tabular-nums; }
.chip.pos { background: var(--equity-soft); color: var(--equity); }
.chip.neg { background: var(--bond-soft); color: var(--bond); }
.chip.zer { background: var(--chip-zero); color: var(--muted); }
.scorerow .why { color: var(--muted); font-size: 12.5px; }
.sectorrow { display: grid; grid-template-columns: 128px 1fr 52px; align-items: center;
  gap: 10px; padding: 5px 0; font-size: 13.5px; }
.sectorrow .bar { height: 14px; border-radius: 0 4px 4px 0; background: var(--equity);
  opacity: .78; min-width: 2px; }
.sectorrow:hover .bar { opacity: 1; }
.sectorrow .val { text-align: right; font-variant-numeric: tabular-nums; color: var(--muted); }
.tablewrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th { text-align: left; font-size: 11.5px; text-transform: uppercase; letter-spacing: .07em;
  color: var(--muted); font-weight: 700; padding: 8px 10px; border-bottom: 1px solid var(--ink); }
td { padding: 7px 10px; border-bottom: 1px solid var(--line);
  font-variant-numeric: tabular-nums; }
td.num { text-align: right; }
.wbar { display: inline-block; height: 10px; border-radius: 0 3px 3px 0;
  background: var(--equity); opacity: .78; vertical-align: middle; }
tr.bondrow .wbar { background: var(--bond); }
details.card { margin: 0; }
details.card summary { cursor: pointer; list-style: none; color: var(--ink); font-weight: 600; }
details.card summary::after { content: " ▾"; color: var(--muted); font-size: 11px; }
details.card[open] summary::after { content: " ▴"; }
details.card .cardbody { margin: 8px 0 4px; padding: 10px 12px; background: var(--card);
  border: 1px solid var(--line); border-radius: 6px; font-size: 12.5px; color: var(--muted); }
details.card .cardbody b { color: var(--ink); }
.battle { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.battle .tile .v { font-size: 22px; }
.note { font-size: 12.5px; color: var(--muted); margin-top: 10px; }
footer { margin-top: 40px; border-top: 1px solid var(--line); padding-top: 14px;
  font-size: 12px; color: var(--muted); }
.reasons { margin: 6px 0 0; padding-left: 18px; font-size: 12.5px; color: var(--muted); }
.reasons li { margin: 3px 0; }
"""


def _load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def _chip(score):
    cls = "pos" if score > 0 else ("neg" if score < 0 else "zer")
    return f'<span class="chip {cls}">{score:+d}</span>'


SCORE_LABELS = {"exports_yoy": "수출 YoY", "usdkrw_trend": "원/달러 추세",
                "foreign_flow_20d": "외국인 수급", "curve_3_10": "커브 3-10년",
                "bok_stance": "한은 스탠스"}


def render() -> str:
    saa, taa = _load("state/saa.json"), _load("state/taa.json")
    sector, picks = _load("state/sector.json"), _load("state/picks.json")
    cld = _load("portfolios/cld.json")
    led = _load(f"ledger/{cld['last_rebalance']}.json")

    h = []
    add = h.append
    add(f"<title>K-포트 배틀 대시보드</title>\n<style>{CSS}</style>\n<main>")

    add('<header class="masthead"><h1>K-MODEL PORTFOLIO 배틀판</h1>'
        '<span class="vs">CLD vs TDY</span>'
        f'<span class="asof">asof {saa["date"]} · params {cld["params_hash"]}</span></header>')

    if saa.get("yield_gap_z") is None:
        add('<div class="banner">⚠️ Yield Gap z-score N/A — 5년 시계열 이력 축적 중</div>')
    if not any(r.get("bm_pct") is not None for r in sector["table"]):
        add('<div class="banner">⚠️ KOSPI 섹터 BM 시총 비중 N/A — 섹터 액티브 한도·액티브 셰어 검증 불가 (수기 확보 필요)</div>')
    per_kind = "Fwd" if saa["per_kind"] == "fwd" else "트레일링(대체)"
    if saa.get("extreme_per"):
        t = saa.get("trailing_calc") or {}
        add(f'<div class="banner">⚠️ 극단값 프로토콜 발동 — {per_kind} PER {saa["per_value"]}배. '
            f'트레일링 {t.get("trailing_per", "N/A")}배 기준 병기 산출: 주식 {t.get("clipped_equity_pct", "N/A")}%</div>')

    # ---- 스탯 타일
    add('<section><div class="tiles">')
    add(f'<div class="tile"><div class="k">최종 배분 (TAA)</div>'
        f'<div class="v">{taa["equity_pct"]}<span class="unit">%</span> <span class="unit">주식</span></div>'
        f'<div class="s">국고채 ETF {taa["bond_pct"]}% · 듀레이션 {taa["bond_sens"]["duration_years"]}년</div></div>')
    add(f'<div class="tile"><div class="k">Yield Gap ({per_kind} PER {saa["per_value"]}배)</div>'
        f'<div class="v">{saa["yield_gap_pp"]:+.2f}<span class="unit">%p</span></div>'
        f'<div class="s">EY {saa["ey_pct"]}% − 국고10Y {saa["bond10y_pct"]}% → SAA {saa["equity_pct"]}%</div></div>')
    add(f'<div class="tile"><div class="k">스코어카드</div>'
        f'<div class="v">{taa["score_total"]:+d}<span class="unit">점</span></div>'
        f'<div class="s">매핑 틸트 {taa["tilt_scorecard_pp"]:+.1f}%p</div></div>')
    add(f'<div class="tile"><div class="k">재량 오버라이드</div>'
        f'<div class="v">{taa["tilt_final_pp"]:+.1f}<span class="unit">%p</span></div>'
        f'<div class="s">스코어카드 대비 {taa["discretion_delta_pp"]:+.1f}%p — 재량 기여도로 추적</div></div>')
    add('</div></section>')

    # ---- 자산배분 바
    add('<section><h2>자산배분</h2><div class="allocbar">')
    add(f'<div class="alloc-eq" style="width:{taa["equity_pct"]}%" '
        f'title="주식 {taa["equity_pct"]}%">주식 {taa["equity_pct"]}%</div>')
    add(f'<div class="alloc-bd" style="width:{taa["bond_pct"]}%" '
        f'title="국고채 ETF {taa["bond_pct"]}%">{taa["bond_pct"]}%</div>')
    add('</div><div class="legend">'
        '<span><span class="sw" style="background:var(--equity)"></span>주식 (20종목)</span>'
        '<span><span class="sw" style="background:var(--bond)"></span>KOSEF 국고채10년 — '
        f'±100bp ≈ ∓{taa["bond_sens"]["pnl_pct_per_100bp"]}% (포트 기준)</span></div></section>')

    # ---- 스코어카드 + 섹터
    add('<section class="cols"><div><h2>TAA 스코어카드</h2>')
    for key, label in SCORE_LABELS.items():
        it = taa["scorecard"][key]
        add(f'<div class="scorerow">{_chip(it["score"])}<div><b>{label}</b> '
            f'<span class="why">{it["basis"]}</span></div></div>')
    if taa["override_applied"]:
        add('<div class="note"><b>재량 사유</b><ul class="reasons">')
        for r in taa["override_reasons"]:
            add(f"<li>{r}</li>")
        add("</ul></div>")
    add('</div><div><h2>섹터 목표 (주식 내)</h2>')
    max_t = max(r["target_pct"] for r in sector["table"])
    for r in sector["table"]:
        why = sector.get("rationale", {}).get(r["sector"], {}).get("basis", "")
        add(f'<div class="sectorrow" title="{why}"><span>{r["sector"]}</span>'
            f'<div class="bar" style="width:{r["target_pct"] / max_t * 100:.0f}%"></div>'
            f'<span class="val">{r["target_pct"]:.1f}%</span></div>')
    add("</div></section>")

    # ---- 종목 테이블
    conc = picks["concentration"]
    add(f'<section><h2>보유 종목 — {conc["names"]}종목 · 상위5 {conc["top5_pct"]}%</h2>'
        '<div class="tablewrap"><table>')
    add("<tr><th>종목 (선정 카드)</th><th>코드</th><th>섹터</th><th style='text-align:right'>비중</th><th></th></tr>")
    for s in sorted(picks["picks"], key=lambda x: -x["weight_pct"]):
        c = s["card"]
        thesis = "".join(f"<li>{t}</li>" for t in c["thesis"])
        add(f'<tr><td><details class="card"><summary>{s["name"]}</summary>'
            f'<div class="cardbody"><ul class="reasons">{thesis}</ul>'
            f'<b>반대논리</b> {c["counter"]}<br><b>무효화</b> {c["invalidation"]}<br>'
            f'<b>편입</b> {c["entry_date"]} · {c["entry_basis"]}</div></details></td>'
            f'<td>{s["code"]}</td><td>{s["sector"]}</td>'
            f'<td class="num">{s["weight_pct"]:.1f}%</td>'
            f'<td style="width:120px"><span class="wbar" style="width:{s["weight_pct"] * 10:.0f}px" '
            f'title="{s["name"]} {s["weight_pct"]:.1f}%"></span></td></tr>')
    bond_w = cld["weights"].get("148070", 0)
    add(f'<tr class="bondrow"><td><b>KOSEF 국고채10년</b></td><td>148070</td><td>국고채 ETF</td>'
        f'<td class="num">{bond_w:.1f}%</td>'
        f'<td style="width:120px"><span class="wbar" style="width:{bond_w * 5:.0f}px"></span></td></tr>')
    add("</table></div></section>")

    # ---- 배틀 현황
    add('<section><h2>배틀 현황</h2><div class="battle">')
    for name, note in [("CLD", f'{led["execution_basis"]} 대기'), ("TDY", "/tdy-input 대기"),
                       ("KOSPI", "기준가 확정 대기"), ("복합BM", "기준가 확정 대기")]:
        add(f'<div class="tile"><div class="k">{name}</div><div class="v">—</div>'
            f'<div class="s">{note}</div></div>')
    add(f'</div><div class="note">개시 {cld["asof"]} · 체결 {led["execution_basis"]} · '
        f'왕복 비용 {led["roundtrip_cost_pct"]}% · TR 회계 동일 적용 — '
        '기준가 확정 후 /score로 수익률 추적 개시</div></section>')

    add('<footer>출처: PER — ' + saa["per_source"]["source"] +
        f' (asof {saa["per_source"]["asof"]}) · 국고10Y — {saa["bond10y_source"]["source"]}'
        f' (asof {saa["bond10y_source"]["asof"]})<br>'
        '주간 평가·±2%p 밴드 리밸런싱 · Yield Gap ±0.5%p 변동 시 SAA 재산출<br>'
        '※ 본 대시보드는 CLD 모델 산출(페이퍼 트랙)이며 실계좌에 대한 추천이 아닙니다.</footer>')
    add("</main>")
    return "\n".join(h)


def main() -> None:
    out = os.path.join(ROOT, "reports", "dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render())
    print(f"[saved] {out}")


if __name__ == "__main__":
    main()
