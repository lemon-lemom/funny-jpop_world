#!/usr/bin/env python3
"""YouTube Data API でジャンル別に動画を取得し data_runtime/<out>/{genre_id}.json に保存する。

quota の目安: search.list = 100 units / 回、videos.list = 1 unit / 回(最大50 id)。
無料枠は 1 日 10,000 units。168ジャンル × 2キーワードを一度に回すと約 33,600 units で
枠を超えるため、既定でキーワード数を絞り、予算ガード(--quota-budget)で安全に止める。

使い方の例:
  # 動作確認(1ジャンル・1キーワード・25件)
  python scripts/fetch_youtube.py --genres guaguanco --keywords-per-genre 1 --max-results 25
  # 予算内で回せるだけ回す
  python scripts/fetch_youtube.py --keywords-per-genre 1 --quota-budget 9000
"""
import argparse, csv, json, os, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data_master"


def load_api_key():
    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        return key
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        key = os.environ.get("YOUTUBE_API_KEY")
    except Exception:
        pass
    if not key:  # manual fallback if python-dotenv is missing
        envf = ROOT / ".env"
        if envf.exists():
            for line in envf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("YOUTUBE_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key


def read_csv(name):
    with open(MASTER / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_genre_keywords(only=None, kw_per_genre=2):
    genres = [g for g in read_csv("genres.csv") if g.get("is_active", "1") == "1"]
    if only:
        only = set(only)
        genres = [g for g in genres if g["genre_id"] in only]
    by_genre = {}
    for k in read_csv("genre_keywords.csv"):
        if k.get("is_active", "1") != "1":
            continue
        by_genre.setdefault(k["genre_id"], []).append((int(k.get("priority") or 99), k["keyword"]))
    work = []
    for g in genres:
        kws = [kw for _, kw in sorted(by_genre.get(g["genre_id"], []))][:kw_per_genre]
        if kws:
            work.append((g["genre_id"], kws))
    return work


class Quota:
    def __init__(self, budget):
        self.used, self.budget = 0, budget

    def charge(self, n):
        if self.used + n > self.budget:
            raise RuntimeError(f"quota budget reached ({self.used}+{n} > {self.budget})")
        self.used += n


def build_client(key):
    from googleapiclient.discovery import build
    return build("youtube", "v3", developerKey=key, cache_discovery=False)


def search_video_ids(yt, q, quota, max_results, order):
    quota.charge(100)
    resp = yt.search().list(q=q, part="snippet", type="video",
                            maxResults=min(max_results, 50), order=order).execute()
    return [it["id"]["videoId"] for it in resp.get("items", []) if it.get("id", {}).get("videoId")]


def fetch_details(yt, ids, quota):
    out = []
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        quota.charge(1)
        resp = yt.videos().list(part="snippet,statistics,contentDetails",
                                id=",".join(chunk), maxResults=50).execute()
        for it in resp.get("items", []):
            sn, st = it.get("snippet", {}), it.get("statistics", {})
            thumbs = sn.get("thumbnails", {})
            thumb = (thumbs.get("medium") or thumbs.get("high") or thumbs.get("default") or {}).get("url", "")
            out.append({
                "videoId": it["id"],
                "title": sn.get("title", ""),
                "channelId": sn.get("channelId", ""),
                "channelTitle": sn.get("channelTitle", ""),
                "publishedAt": sn.get("publishedAt", ""),
                "thumbnailUrl": thumb,
                "url": "https://www.youtube.com/watch?v=" + it["id"],
                "viewCount": int(st["viewCount"]) if "viewCount" in st else None,
                "likeCount": int(st["likeCount"]) if "likeCount" in st else None,
                "commentCount": int(st["commentCount"]) if "commentCount" in st else None,
            })
    return out


def previous_ids(genre_id, prev_dir):
    p = prev_dir / f"{genre_id}.json"
    if p.exists():
        try:
            return [v["videoId"] for v in json.loads(p.read_text(encoding="utf-8")).get("videos", [])]
        except Exception:
            return []
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genres", help="comma-separated genre_ids (default: all active)")
    ap.add_argument("--max-genres", type=int, default=0, help="limit number of genres (0 = no limit)")
    ap.add_argument("--keywords-per-genre", type=int, default=2)
    ap.add_argument("--max-results", type=int, default=50, help="search results per keyword (max 50)")
    ap.add_argument("--order", default="relevance", choices=["relevance", "viewCount", "date"])
    ap.add_argument("--quota-budget", type=int, default=9000)
    ap.add_argument("--out", default="staging", help="output dir under data_runtime/")
    ap.add_argument("--prev", default="current", help="dir under data_runtime/ to also refresh for Hot tracking")
    ap.add_argument("--skip-existing", action="store_true",
                    help="skip genres already present in --out (for multi-day backfill)")
    args = ap.parse_args()

    key = load_api_key()
    if not key:
        sys.exit("ERROR: YOUTUBE_API_KEY not found (set it in .env)")

    only = [s.strip() for s in args.genres.split(",")] if args.genres else None
    work = load_genre_keywords(only, args.keywords_per_genre)
    if args.max_genres:
        work = work[:args.max_genres]
    if not work:
        sys.exit("no genres matched")

    out_dir = ROOT / "data_runtime" / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    prev_dir = ROOT / "data_runtime" / args.prev

    if args.skip_existing:
        before = len(work)
        work = [(gid, kws) for gid, kws in work if not (out_dir / f"{gid}.json").exists()]
        print(f"skip-existing: {before - len(work)} already in {out_dir.name}/, {len(work)} remaining")
        if not work:
            sys.exit("nothing left to fetch (all genres already exist)")

    yt = build_client(key)
    quota = Quota(args.quota_budget)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    from googleapiclient.errors import HttpError

    done = skipped = 0
    for gid, kws in work:
        try:
            ids, matched = [], {}
            for kw in kws:
                for v in search_video_ids(yt, kw, quota, args.max_results, args.order):
                    matched.setdefault(v, set()).add(kw)
                    ids.append(v)
            for v in previous_ids(gid, prev_dir):   # keep tracking last run's videos for Hot
                matched.setdefault(v, set())
                ids.append(v)
            ids = list(dict.fromkeys(ids))           # dedupe, preserve order
            videos = fetch_details(yt, ids, quota)
            for v in videos:
                v["matchedKeywords"] = sorted(matched.get(v["videoId"], []))
            payload = {"genreId": gid, "capturedAt": now, "keywords": kws, "videos": videos}
            (out_dir / f"{gid}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            done += 1
            print(f"[{done}/{len(work)}] {gid}: {len(videos)} videos  (quota used {quota.used})")
        except RuntimeError as e:
            print(f"STOP: {e}")
            break
        except HttpError as e:
            status = getattr(getattr(e, "resp", None), "status", None)
            print(f"WARN {gid}: HttpError {status}: {e}")
            if status in (403, 400):
                print("Key/quota/API problem — stopping. Check the key and that YouTube Data API v3 is enabled.")
                break
            skipped += 1
            continue

    print(f"\ndone={done} skipped={skipped} quota_used={quota.used} -> data_runtime/{args.out}/")


if __name__ == "__main__":
    main()
