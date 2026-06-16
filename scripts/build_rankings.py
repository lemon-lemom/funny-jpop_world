#!/usr/bin/env python3
"""data_runtime/<current> と <previous> を比較して Classic/Fresh/Hot を生成し、
data/rankings/{genre_id}.json を書き出す(フロントの world-music-map.html が読む形)。

  Classic … 累計再生数の多い順 Top10
  Fresh   … 直近90日に投稿された動画の再生数順 Top10
  Hot     … previous からの再生数増加(weekly_growth>0)の多い順 Top10(2回目以降)
"""
import argparse, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRESH_DAYS = 90
TOP_N = 10


def load_dir(d):
    out = {}
    if d.exists():
        for p in d.glob("*.json"):
            try:
                out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return out


def parse_dt(s):
    try:
        return datetime.datetime.fromisoformat((s or "").replace("Z", "+00:00"))
    except Exception:
        return None


def card(v, rank, growth=None):
    return {
        "rank": rank, "videoId": v["videoId"], "title": v.get("title", ""),
        "channelTitle": v.get("channelTitle", ""), "publishedAt": v.get("publishedAt", ""),
        "views": v.get("viewCount"), "weeklyGrowth": growth,
        "thumbnailUrl": v.get("thumbnailUrl", ""), "url": v.get("url", ""),
    }


def build(curr, prev):
    videos = [v for v in curr.get("videos", []) if v.get("viewCount") is not None]

    classic = sorted(videos, key=lambda v: v["viewCount"], reverse=True)[:TOP_N]

    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=FRESH_DAYS)
    fresh = [v for v in videos if (parse_dt(v.get("publishedAt")) or cutoff.replace(year=1)) >= cutoff]
    fresh = sorted(fresh, key=lambda v: v["viewCount"], reverse=True)[:TOP_N]

    prev_map = {v["videoId"]: v for v in (prev.get("videos", []) if prev else [])}
    hot = []
    for v in videos:
        pv = prev_map.get(v["videoId"])
        if pv and pv.get("viewCount") is not None:
            g = v["viewCount"] - pv["viewCount"]
            if g > 0:
                hot.append((g, v))
    hot = sorted(hot, key=lambda x: x[0], reverse=True)[:TOP_N]

    return {
        "genreId": curr["genreId"],
        "updatedAt": curr.get("capturedAt"),
        "rankings": {
            "classic": [card(v, i + 1) for i, v in enumerate(classic)],
            "fresh": [card(v, i + 1) for i, v in enumerate(fresh)],
            "hot": [card(v, i + 1, g) for i, (g, v) in enumerate(hot)],
        },
        "note": "このランキングはYouTube公式ランキングではなく、独自に設定した検索キーワードに基づく集計です。",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", default="current", help="dir under data_runtime/")
    ap.add_argument("--previous", default="previous", help="dir under data_runtime/")
    args = ap.parse_args()

    cur = load_dir(ROOT / "data_runtime" / args.current)
    prev = load_dir(ROOT / "data_runtime" / args.previous)
    out = ROOT / "data" / "rankings"
    out.mkdir(parents=True, exist_ok=True)

    n = hot_total = 0
    for gid, c in cur.items():
        r = build(c, prev.get(gid))
        (out / f"{gid}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
        hot_total += len(r["rankings"]["hot"])
    print(f"wrote {n} ranking files to data/rankings/ (hot entries: {hot_total})")


if __name__ == "__main__":
    main()
