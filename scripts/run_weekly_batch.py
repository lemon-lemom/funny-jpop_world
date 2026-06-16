#!/usr/bin/env python3
"""週次バッチ: 取得 → ランキング生成 → 世代ローテーション → 公開JSON更新。

安全順序(要件 §17.3):
  1. 取得         → data_runtime/staging に新データ
  2. ランキング生成 → build_rankings(current=staging, previous=current)
                     ※ 既存の current(=前回分)を Hot 比較の previous として使う
  3. ローテーション → previous を削除 / current→previous / staging→current
  4. 公開JSON更新 → export_static_json.py

fetch_youtube.py への引数はそのまま渡せる:
  python scripts/run_weekly_batch.py --keywords-per-genre 1 --quota-budget 9000
  python scripts/run_weekly_batch.py --genres guaguanco,reggae --max-results 25
"""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RT = ROOT / "data_runtime"


def run(script, *a):
    print(f"\n=== {script} {' '.join(a)} ===")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *a])
    if r.returncode != 0:
        raise SystemExit(f"{script} failed (exit {r.returncode})")


def main():
    passthrough = sys.argv[1:]  # forwarded to fetch_youtube.py

    # 1. fetch into staging (current = last run, used for Hot tracking)
    run("fetch_youtube.py", "--out", "staging", "--prev", "current", *passthrough)

    stg = RT / "staging"
    if not stg.exists() or not any(stg.glob("*.json")):
        raise SystemExit("no staging output produced; aborting before rotation")

    # 2. rankings comparing staging (new) vs current (previous generation)
    run("build_rankings.py", "--current", "staging", "--previous", "current")

    # 3. rotate generations
    prev, cur = RT / "previous", RT / "current"
    if prev.exists():
        shutil.rmtree(prev)
    if cur.exists():
        cur.rename(prev)
    stg.rename(cur)
    print("\nrotated: current→previous, staging→current")

    # 4. refresh public JSON (places/genres/map_points)
    run("export_static_json.py")
    print("\nweekly batch complete. data/rankings/*.json updated.")


if __name__ == "__main__":
    main()
