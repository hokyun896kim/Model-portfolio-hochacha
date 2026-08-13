"""3단계 — 섹터 배분: 벤치마크 비중 + View tilt → 섹터 목표 비중.

섹터·스타일·벤치마크 분석으로 유효한 테마를 선별하고, KOSPI 근사
벤치마크 비중에 ±%p tilt를 더한 뒤 합이 100%가 되도록 정규화한다.
"""


def compute_sector_targets(benchmark: dict, tilts_pp: dict) -> dict:
    """섹터명 -> {benchmark, tilt, target} (%; target은 합 100으로 정규화)."""
    raw = {}
    for sector, bm in benchmark.items():
        tilted = max(0.0, bm + tilts_pp.get(sector, 0.0))
        raw[sector] = tilted
    total = sum(raw.values())
    out = {}
    for sector, bm in benchmark.items():
        target = 100.0 * raw[sector] / total
        out[sector] = {
            "benchmark_pct": bm,
            "tilt_pp": tilts_pp.get(sector, 0.0),
            "target_pct": round(target, 2),
            "active_pp": round(target - bm, 2),
        }
    return out
