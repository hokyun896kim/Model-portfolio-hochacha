"""파이프라인 오케스트레이션: 스냅샷 JSON → 모델 포트폴리오 리포트(MD)."""

import json

from .saa import compute_saa
from .taa import compute_taa
from .sector import compute_sector_targets
from .selection import allocate_stocks
from .balance import check_balance
from .rebalance import describe_rules

DISCLAIMER = ("※ 본 문서의 모든 정보 및 자료는 참고용이며 "
              "법적, 재정적, 투자적 조언으로 간주되지 않습니다.")


def build_portfolio(snapshot_path: str) -> dict:
    with open(snapshot_path, encoding="utf-8") as f:
        snap = json.load(f)

    market = snap["market"]
    saa = compute_saa(market["index_per"], market["bond_yield_10y_pct"])
    taa = compute_taa(saa.stock_weight_pct, snap["view"])
    sectors = compute_sector_targets(snap["sector_benchmark"], snap["sector_tilts_pp"])
    holdings = allocate_stocks(snap["universe"], sectors, taa.stock_weight_pct,
                               snap["constraints"],
                               snap.get("stock_benchmark_weights_pct", {}))
    balance = check_balance(holdings, sectors,
                            snap.get("stock_benchmark_weights_pct", {}),
                            snap["constraints"])
    return {
        "meta": snap["meta"],
        "saa": saa,
        "taa": taa,
        "sectors": sectors,
        "sector_rationale": snap.get("sector_tilt_rationale", {}),
        "holdings": holdings,
        "balance": balance,
        "rebalance_rules": describe_rules(snap["rebalance_rules"]),
    }


def render_markdown(result: dict) -> str:
    meta, saa, taa = result["meta"], result["saa"], result["taa"]
    lines = []
    add = lines.append

    add(f"# 한국주식 모델 포트폴리오 — {meta['as_of']}")
    add("")
    add(f"벤치마크: {meta['benchmark']}")
    add("")

    add("## 1. 전략적 자산배분 (SAA) — Yield Gap 모형")
    add("")
    add("| 항목 | 값 |")
    add("|---|---|")
    add(f"| 지수 PER | {saa.per}배 |")
    add(f"| Earnings Yield (1/PER) | {saa.earnings_yield_pct}% |")
    add(f"| 10Y 국채금리 | {saa.bond_yield_pct}% |")
    add(f"| Yield Gap | {saa.yield_gap_pp:+.2f}%p |")
    add(f"| **SAA 주식 비중** | **{saa.stock_weight_pct}%** "
        f"(= {saa.earnings_yield_pct} / ({saa.earnings_yield_pct} + {saa.bond_yield_pct})) |")
    add(f"| SAA 현금·채권 비중 | {saa.cash_weight_pct}% |")
    add("")

    add("## 2. 전술적 자산배분 (TAA) — SAA ± View")
    add("")
    add(f"- View: **{taa.stance} ({taa.view_tilt_pp:+.1f}%p)**")
    for r in taa.rationale:
        add(f"  - {r}")
    add(f"- **TAA 주식 비중: {taa.stock_weight_pct}% / 현금·채권: {taa.cash_weight_pct}%** "
        f"(= SAA {taa.saa_stock_pct}% {taa.view_tilt_pp:+.1f}%p)")
    add("")

    add("## 3. 섹터 배분")
    add("")
    add("| 섹터 | 벤치마크 | Tilt | 목표(주식 내) | 액티브 |")
    add("|---|---:|---:|---:|---:|")
    for sector, t in sorted(result["sectors"].items(),
                            key=lambda kv: -kv[1]["target_pct"]):
        add(f"| {sector} | {t['benchmark_pct']:.1f}% | {t['tilt_pp']:+.1f}%p "
            f"| {t['target_pct']:.1f}% | {t['active_pp']:+.1f}%p |")
    add("")
    rationale = result["sector_rationale"]
    if rationale:
        add("Tilt 근거:")
        for sector, why in rationale.items():
            add(f"- **{sector}**: {why}")
        add("")

    add("## 4~5. 종목 선정 (Bottom-up) 및 벤치마크 대비 균형")
    add("")
    add("포트폴리오 전체(현금 포함 100%) 기준 비중입니다. "
        "섹터 내 비중은 벤치마크 앵커 + Bottom-up 점수 블렌드로 배분하며, "
        "유니버스에 종목이 없는 섹터(예: 기타)의 예산은 보유 섹터에 비례 재배분됩니다.")
    add("")
    add("| 종목 | 코드 | 섹터 | 점수 | 비중 | BM | 액티브 | 투자 포인트 |")
    add("|---|---|---|---:|---:|---:|---:|---|")
    for h in result["holdings"]:
        add(f"| {h['name']} | {h['code']} | {h['sector']} | {h['score']} "
            f"| {h['weight_pct']:.2f}% | {h.get('benchmark_pct', 0):.1f}% "
            f"| {h.get('active_pp', 0):+.2f}%p | {h['thesis']} |")
    equity = sum(h["weight_pct"] for h in result["holdings"])
    add(f"| **주식 합계** | | | | **{equity:.2f}%** | | | |")
    add(f"| **현금·채권** | | | | **{100 - equity:.2f}%** | | | |")
    add("")
    warnings = result["balance"]["warnings"]
    if warnings:
        add("균형 점검 경고:")
        for w in warnings:
            add(f"- ⚠️ {w}")
    else:
        add("균형 점검: 종목/섹터 액티브 비중 모두 한도 이내입니다. ✅")
    add("")

    add("## 6. 리밸런싱 규칙")
    add("")
    for r in result["rebalance_rules"]:
        add(f"- {r}")
    add("")

    add("## 데이터 출처 및 주의")
    add("")
    for n in meta.get("notes", []):
        add(f"- {n}")
    add("")
    add(f"> {DISCLAIMER}")
    add("")
    return "\n".join(lines)
