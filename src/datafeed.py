"""데이터 수집 계층.

규칙 (CLAUDE.md §8): 모든 데이터 함수는 값 + asof + source를 반환한다.
실패는 N/A Datum(사유 포함)으로 반환하며 report.py가 배너로 승격한다.

소스 우선순위 (§4): pykrx/ECOS → 수기 폴백(data/manual/<날짜>.json) → N/A.
캐싱: data/cache/YYYYMMDD/ 원본 저장, 당일 중복 호출 금지.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "data", "cache")
MANUAL_DIR = os.path.join(ROOT, "data", "manual")


@dataclass
class Datum:
    value: Optional[float]
    asof: str
    source: str
    ok: bool = True
    note: str = ""

    @staticmethod
    def na(reason: str) -> "Datum":
        return Datum(value=None, asof="N/A", source="N/A", ok=False, note=reason)

    def to_dict(self) -> dict:
        return asdict(self)


def _cache_path(date_str: str, name: str) -> str:
    d = os.path.join(CACHE_DIR, date_str.replace("-", ""))
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{name}.json")


def cache_get(date_str: str, name: str):
    path = _cache_path(date_str, name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def cache_put(date_str: str, name: str, payload) -> None:
    with open(_cache_path(date_str, name), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_manual(date_str: str) -> dict:
    """수기 폴백 파일. 항목별 {value, asof, source, note?} 스키마."""
    path = os.path.join(MANUAL_DIR, f"{date_str}.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _manual_datum(manual: dict, key: str) -> Optional[Datum]:
    if key in manual:
        m = manual[key]
        return Datum(value=m.get("value"), asof=m.get("asof", "N/A"),
                     source=m.get("source", "수기"), ok=m.get("value") is not None,
                     note=m.get("note", "수기 폴백"))
    return None


# ---------- pykrx / ECOS 1순위 경로 ----------

def _try_pykrx_index_per(date_str: str) -> Optional[Datum]:
    """KOSPI 트레일링 PER (pykrx). 실패 시 None."""
    try:
        from pykrx import stock
        ymd = date_str.replace("-", "")
        df = stock.get_index_fundamental(ymd, ymd, "1001")
        if df is None or df.empty:
            return None
        per = float(df["PER"].iloc[-1])
        cache_put(date_str, "pykrx_index_fundamental", {"per": per})
        return Datum(value=per, asof=date_str, source="pykrx(KRX) KOSPI 트레일링 PER")
    except Exception:
        return None


def _try_ecos_bond10y(date_str: str) -> Optional[Datum]:
    """국고채 10년 (ECOS Open API). API 키는 .env의 ECOS_API_KEY. 실패 시 None."""
    key = os.environ.get("ECOS_API_KEY")
    if not key:
        return None
    try:
        import urllib.request
        ymd = date_str.replace("-", "")
        url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/1/10/"
               f"817Y002/D/{ymd}/{ymd}/010200000")
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode())
        rows = data.get("StatisticSearch", {}).get("row", [])
        if not rows:
            return None
        val = float(rows[-1]["DATA_VALUE"])
        cache_put(date_str, "ecos_bond10y", data)
        return Datum(value=val, asof=date_str, source="ECOS 817Y002 국고채(10년)")
    except Exception:
        return None


# ---------- 공개 API: 항목별 수집 (1순위 → 수기 → N/A) ----------

def get_fwd_per(date_str: str) -> Datum:
    """KOSPI 12M Fwd PER. 크롤 소스(§4) 실패 시 수기 → N/A."""
    d = _manual_datum(load_manual(date_str), "fwd_per")
    if d:
        return d
    return Datum.na("Fwd PER 크롤 소스 접근 불가, 수기 입력 없음")


def get_trailing_per(date_str: str) -> Datum:
    d = _try_pykrx_index_per(date_str)
    if d:
        return d
    d = _manual_datum(load_manual(date_str), "trailing_per")
    if d:
        return d
    return Datum.na("pykrx 실패, 수기 입력 없음")


def get_bond10y(date_str: str) -> Datum:
    d = _try_ecos_bond10y(date_str)
    if d:
        return d
    d = _manual_datum(load_manual(date_str), "bond10y")
    if d:
        return d
    return Datum.na("ECOS 실패(키 미설정 또는 차단), 수기 입력 없음")


def get_bond3y(date_str: str) -> Datum:
    d = _manual_datum(load_manual(date_str), "bond3y")
    if d:
        return d
    return Datum.na("국고3년 수기 입력 없음")


def get_kospi_close(date_str: str) -> Datum:
    try:
        from pykrx import stock
        ymd = date_str.replace("-", "")
        df = stock.get_index_ohlcv(ymd, ymd, "1001")
        if df is not None and not df.empty:
            val = float(df["종가"].iloc[-1])
            cache_put(date_str, "pykrx_kospi_close", {"close": val})
            return Datum(value=val, asof=date_str, source="pykrx(KRX) KOSPI 종가")
    except Exception:
        pass
    d = _manual_datum(load_manual(date_str), "kospi_close")
    if d:
        return d
    return Datum.na("pykrx 실패, 수기 입력 없음")


def get_scorecard_input(date_str: str, key: str) -> Datum:
    """스코어카드 원천 데이터(수출YoY/환율추세/외국인수급/커브/한은).

    1순위 자동수집은 항목별 API 확정 후 구현. 현재는 수기 폴백만.
    key: exports_yoy | usdkrw_trend | foreign_flow_20d | curve_3_10 | bok_stance
    """
    d = _manual_datum(load_manual(date_str), key)
    if d:
        return d
    return Datum.na(f"{key} 수기 입력 없음")


def get_sector_bm_weights(date_str: str) -> dict:
    """KOSPI 섹터 시총 비중. 반환: {"weights": {섹터: %}, "datum": Datum}."""
    manual = load_manual(date_str)
    if "sector_bm_weights" in manual:
        m = manual["sector_bm_weights"]
        return {"weights": m.get("value", {}),
                "datum": Datum(value=None, asof=m.get("asof", "N/A"),
                               source=m.get("source", "수기"), ok=True,
                               note=m.get("note", "수기 폴백"))}
    return {"weights": {}, "datum": Datum.na("pykrx 섹터 시총 실패, 수기 입력 없음")}


def get_bond_etf_price(date_str: str, ticker: str) -> Datum:
    try:
        from pykrx import stock
        ymd = date_str.replace("-", "")
        df = stock.get_market_ohlcv(ymd, ymd, ticker)
        if df is not None and not df.empty:
            val = float(df["종가"].iloc[-1])
            cache_put(date_str, f"pykrx_etf_{ticker}", {"close": val})
            return Datum(value=val, asof=date_str, source=f"pykrx(KRX) {ticker} 종가")
    except Exception:
        pass
    d = _manual_datum(load_manual(date_str), f"etf_{ticker}_close")
    if d:
        return d
    return Datum.na(f"ETF {ticker} 시세 실패, 수기 입력 없음")
