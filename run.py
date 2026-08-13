#!/usr/bin/env python3
"""모델 포트폴리오 리포트 생성 CLI.

사용법:
    python3 run.py [--snapshot data/snapshot_YYYY-MM-DD.json]
"""

import argparse
import glob
import os

from model_portfolio.build import build_portfolio, render_markdown


def latest_snapshot() -> str:
    paths = sorted(glob.glob(os.path.join("data", "snapshot_*.json")))
    if not paths:
        raise SystemExit("data/snapshot_*.json 파일이 없습니다.")
    return paths[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="한국주식 모델 포트폴리오 생성")
    parser.add_argument("--snapshot", default=None,
                        help="시장 스냅샷 JSON 경로 (기본: data/의 최신 파일)")
    args = parser.parse_args()

    snapshot = args.snapshot or latest_snapshot()
    result = build_portfolio(snapshot)
    md = render_markdown(result)

    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output",
                            f"MODEL_PORTFOLIO_{result['meta']['as_of']}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(md)
    print(f"[saved] {out_path}")


if __name__ == "__main__":
    main()
