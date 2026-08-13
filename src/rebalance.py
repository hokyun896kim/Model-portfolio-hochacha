"""STEP 6 — 리밸런싱 + 오케스트레이션 (부수효과 허용 유일 모듈, §8).

실행: python3 -m src.rebalance --date YYYY-MM-DD
입력:
  data/manual/<date>.json          — 수기 시장 데이터 (datafeed 폴백)
  state/inputs/<date>/judgments.json — Claude 판단 (STEP 2~4)
출력(모두 이 모듈에서만 쓰기):
  state/{saa,taa,sector,picks}.json, portfolios/cld.json,
  ledger/<date>.json (append-only, 기존 파일 존재 시 거부),
  reports/<date>.md, scoreboard.md(없으면 골격 생성)

HARD 6: 가드레일 위반 시 포트폴리오를 쓰지 않고 위반 목록만 출력 후 종료.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import date as _date, timedelta

import yaml

from . import datafeed, saa as saa_mod, taa as taa_mod
from . import sector as sector_mod, screen as screen_mod, report as report_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_params() -> tuple:
    path = os.path.join(ROOT, "config", "params.yaml")
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    return yaml.safe_load(raw), hashlib.sha256(raw.encode()).hexdigest()[:12]


def next_business_day(date_str: str) -> str:
    d = _date.fromisoformat(date_str) + timedelta(days=1)
    while d.weekday() >= 5:  # 공휴일은 미반영 — 체결 시 수동 확인
        d += timedelta(days=1)
    return d.isoformat()


def _write_json(rel_path: str, payload: dict) -> None:
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def band_trades(prev_weights: dict, target_weights: dict, band_pp: float) -> list:
    """±밴드 이탈 항목만 매매. 초기 편입(prev 없음)은 전량 매수."""
    trades = []
    for code, tgt in target_weights.items():
        cur = prev_weights.get(code, 0.0)
        if abs(tgt - cur) > band_pp or (cur == 0.0 and tgt > 0):
            trades.append({"code": code, "from_pct": round(cur, 2),
                           "to_pct": round(tgt, 2),
                           "side": "BUY" if tgt > cur else "SELL"})
    for code, cur in prev_weights.items():
        if code not in target_weights and cur > 0:
            trades.append({"code": code, "from_pct": round(cur, 2),
                           "to_pct": 0.0, "side": "SELL"})
    return trades


def run_weekly(date_str: str) -> int:
    params, params_hash = load_params()
    banners = []

    # ---------- 데이터 수집 (STEP 1 입력) ----------
    fwd = datafeed.get_fwd_per(date_str)
    trailing = datafeed.get_trailing_per(date_str)
    by10 = datafeed.get_bond10y(date_str)

    if fwd.ok:
        per_value, per_kind, per_datum = fwd.value, "fwd", fwd
    elif trailing.ok:
        per_value, per_kind, per_datum = trailing.value, "trailing", trailing
        banners.append("Fwd PER 확보 실패 → 트레일링 PER 대체 (§4 폴백)")
    else:
        print("⛔ PER 확보 불가 — 중단"); print(fwd.note, "/", trailing.note)
        return 1
    if not by10.ok:
        print("⛔ 국고10년 확보 불가 — 중단:", by10.note)
        return 1

    saa = saa_mod.compute_saa(per_value, per_kind, by10.value, params,
                              trailing_per=trailing.value if trailing.ok else None)
    if saa["yield_gap_z"] is None:
        banners.append("Yield Gap z-score N/A (5년 시계열 미확보 — 이력 축적 중)")

    # ---------- Claude 판단 로드 (STEP 2~4) ----------
    jpath = os.path.join(ROOT, "state", "inputs", date_str, "judgments.json")
    if not os.path.exists(jpath):
        print(f"⛔ 판단 파일 없음: {jpath}")
        return 1
    with open(jpath, encoding="utf-8") as f:
        judg = json.load(f)

    taa = taa_mod.compute_taa(saa["equity_pct"], judg["scorecard"],
                              judg.get("override", {}), params)
    bond_sens = taa_mod.bond_sensitivity(taa["bond_pct"],
                                         params["saa"]["bond_duration_years"])

    sector_bm = datafeed.get_sector_bm_weights(date_str)
    if not sector_bm["weights"]:
        banners.append("KOSPI 섹터 BM 시총 비중 N/A — 섹터 액티브 한도·액티브 셰어 검증 불가"
                       " (pykrx 차단, 수기 입력 없음)")
    sector_res = sector_mod.validate_sector_targets(
        judg["sector_targets"], sector_bm["weights"], params)

    screen_res = screen_mod.validate_picks(judg["picks"], taa["equity_pct"], params)

    # ---------- HARD 6: 가드레일 ----------
    violations = sector_res["violations"] + screen_res["violations"]
    if violations:
        print("⛔ 가드레일 위반 — 포트폴리오 출력 중단 (HARD 6)")
        for v in violations:
            print(" -", v)
        return 2

    # ---------- 목표 비중 확정 ----------
    bond_ticker = params["saa"]["bond_etf_ticker"]
    target_weights = {s["code"]: s["weight_pct"] for s in judg["picks"]}
    target_weights[bond_ticker] = taa["bond_pct"]

    prev_weights, prev_asof = {}, None
    cld_path = os.path.join(ROOT, "portfolios", "cld.json")
    if os.path.exists(cld_path):
        with open(cld_path, encoding="utf-8") as f:
            prev = json.load(f)
        prev_weights, prev_asof = prev.get("weights", {}), prev.get("asof")
        if prev.get("params_hash") != params_hash:
            banners.append(f"params_hash 변경 감지: {prev.get('params_hash')} → {params_hash}")

    trades = band_trades(prev_weights, target_weights, params["rebalance"]["band_pp"])
    exec_date = next_business_day(date_str)

    # ---------- ledger (append-only) ----------
    ledger_path = os.path.join(ROOT, "ledger", f"{date_str}.json")
    if os.path.exists(ledger_path):
        print(f"⛔ ledger 이미 존재 — append-only 위반 방지 중단: {ledger_path}")
        return 3
    ledger = {
        "date": date_str,
        "kind": "initial" if not prev_weights else "weekly",
        "trades": trades,
        "execution_basis": f"{exec_date} 시가 (평가일 익영업일)",
        "roundtrip_cost_pct": params["rebalance"]["roundtrip_cost_pct"],
        "params_hash": params_hash,
    }

    # ---------- 쓰기 ----------
    _write_json("state/saa.json", {"date": date_str, **saa,
                                   "per_source": per_datum.to_dict(),
                                   "bond10y_source": by10.to_dict()})
    _write_json("state/taa.json", {"date": date_str, **taa, "bond_sens": bond_sens})
    _write_json("state/sector.json", {"date": date_str, **sector_res,
                                      "rationale": judg.get("sector_rationale", {}),
                                      "bm_source": sector_bm["datum"].to_dict()})
    _write_json("state/picks.json", {"date": date_str, "picks": judg["picks"],
                                     "concentration": screen_res["concentration"]})
    _write_json("portfolios/cld.json", {"version": params["version"],
                                        "asof": date_str,
                                        "weights": target_weights,
                                        "params_hash": params_hash,
                                        "last_rebalance": date_str})
    _write_json(f"ledger/{date_str}.json", ledger)

    ctx = {"date": date_str, "banners": banners, "saa": saa,
           "per_datum": per_datum, "by10": by10, "taa": taa,
           "bond_sens": bond_sens, "sector": sector_res,
           "sector_rationale": judg.get("sector_rationale", {}),
           "picks": judg["picks"], "screen": screen_res, "ledger": ledger,
           "params": params, "next_week_watch": judg.get("next_week_watch", [])}
    md = report_mod.render_weekly(ctx)
    rpath = os.path.join(ROOT, "reports", f"{date_str}.md")
    os.makedirs(os.path.dirname(rpath), exist_ok=True)
    with open(rpath, "w", encoding="utf-8") as f:
        f.write(md)

    sb_path = os.path.join(ROOT, "scoreboard.md")
    if not os.path.exists(sb_path):
        with open(sb_path, "w", encoding="utf-8") as f:
            f.write(report_mod.scoreboard_skeleton(date_str, exec_date))

    print(md)
    print(f"[saved] reports/{date_str}.md, ledger/{date_str}.json, portfolios/cld.json")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    sys.exit(run_weekly(args.date))


if __name__ == "__main__":
    main()
