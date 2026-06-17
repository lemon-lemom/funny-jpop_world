#!/usr/bin/env python3
"""Funny J-POP 全動画の尺(duration)を YouTube API で取得し、
data_runtime/funnyj_durations.json に {video_id: seconds} で保存する。
videos.list(contentDetails) は 1ユニット/呼び出し・50件/呼び出しなので安価。
"""
import json, sys, io, re, urllib.request, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_youtube import load_api_key
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/claude/web_test")
SRC = Path(r"C:/claude/funnyJ-pop/output/youtube_channel_videos_2026-06-17/funny_jpop_videos.json")

def iso_to_sec(s):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m: return None
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h*3600 + mi*60 + se

key = load_api_key()
assert key, "no YOUTUBE_API_KEY"
ids = [v["video_id"] for v in json.load(open(SRC, encoding="utf-8"))["videos"]]

durations = {}
for i in range(0, len(ids), 50):
    chunk = ids[i:i+50]
    qs = urllib.parse.urlencode({"part": "contentDetails", "id": ",".join(chunk), "key": key})
    with urllib.request.urlopen("https://www.googleapis.com/youtube/v3/videos?" + qs) as r:
        data = json.load(r)
    for it in data.get("items", []):
        durations[it["id"]] = iso_to_sec(it["contentDetails"]["duration"])
    print(f"fetched {len(durations)}/{len(ids)}")

out = ROOT/"data_runtime"/"funnyj_durations.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(durations, ensure_ascii=False, indent=0), encoding="utf-8")
print("wrote", out)

# distribution
secs = sorted(s for s in durations.values() if s is not None)
import bisect
print("min/median/max:", secs[0], secs[len(secs)//2], secs[-1])
for thr in (60, 90, 120, 180):
    print(f"  <= {thr}s : {bisect.bisect_right(secs, thr)} videos")
