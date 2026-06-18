#!/usr/bin/env python3
"""Funny J-POP チャンネルのアバター画像を取得して assets/ に保存する。"""
import sys, io, json, urllib.request, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_youtube import load_api_key
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/claude/web_test")
CHANNEL_ID = "UCPZ6Q9Tlp_QGGvcmX8w76tw"

key = load_api_key()
assert key, "no YOUTUBE_API_KEY"
qs = urllib.parse.urlencode({"part": "snippet", "id": CHANNEL_ID, "key": key})
with urllib.request.urlopen("https://www.googleapis.com/youtube/v3/channels?" + qs) as r:
    data = json.load(r)
thumbs = data["items"][0]["snippet"]["thumbnails"]
# pick highest resolution available
best = max(thumbs.values(), key=lambda t: t.get("width", 0))
url = best["url"]
print("avatar:", best.get("width"), "x", best.get("height"), url)

assets = ROOT / "assets"
assets.mkdir(exist_ok=True)
out = assets / "funnyjpop-icon.png"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as r:
    out.write_bytes(r.read())
print("wrote", out, out.stat().st_size, "bytes")
