#!/usr/bin/env python3
"""funnyjpop-icon.png(白背景の正方形)を円形に切り抜いて四隅を透過にし、
ファビコン各サイズ(ico + 32/180/192/512 PNG)を再生成する。"""
import sys, io
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

A = Path(r"C:/claude/web_test/assets")
src = Image.open(A/"funnyjpop-icon.png").convert("RGBA")
w, h = src.size

# 非白(=デザイン)領域のバウンディングボックスから円の中心/半径を推定
rgb = src.convert("RGB")
# 白に近い画素を白(255)に、それ以外を黒(0)にした差分マスク
bg = Image.new("RGB", src.size, (253, 253, 253))
diff = ImageChops.difference(rgb, bg).convert("L").point(lambda p: 255 if p > 12 else 0)
bbox = diff.getbbox()
cx = (bbox[0] + bbox[2]) / 2
cy = (bbox[1] + bbox[3]) / 2
r = (((bbox[2]-bbox[0]) + (bbox[3]-bbox[1])) / 4) - 1   # 平均半径(白フチを避け-1)
print(f"bbox={bbox} center=({cx:.0f},{cy:.0f}) r={r:.0f}")

# 4倍解像度で円マスクを描いてダウンスケール(アンチエイリアス)
S = 4
mask = Image.new("L", (w*S, h*S), 0)
ImageDraw.Draw(mask).ellipse(
    [(cx-r)*S, (cy-r)*S, (cx+r)*S, (cy+r)*S], fill=255)
mask = mask.resize((w, h), Image.LANCZOS)

out = src.copy()
out.putalpha(mask)                      # 円外を透過
out.save(A/"funnyjpop-icon.png")        # 元ファイルも透過版に更新
print("updated funnyjpop-icon.png (transparent corners)")

for size in (32, 180, 192, 512):
    out.resize((size, size), Image.LANCZOS).save(A/f"funnyjpop-icon-{size}.png")
    print("wrote", f"funnyjpop-icon-{size}.png")

out.resize((64, 64), Image.LANCZOS).save(A/"favicon.ico", sizes=[(16,16),(32,32),(48,48)])
print("wrote favicon.ico")
