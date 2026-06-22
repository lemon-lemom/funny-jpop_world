#!/usr/bin/env python3
"""OGPカード画像(1200x630)を生成: assets/og-home.png / assets/og-map.png。"""
import sys, io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

A = Path(r"C:/claude/web_test/assets")
W, H = 1200, 630
GOLD=(245,192,78); CREAM=(243,234,217); LIME=(158,240,26); SUB=(208,196,176)
F = "C:/Windows/Fonts/"
def af(sz): return ImageFont.truetype(F+"arialbd.ttf", sz)   # Arial Bold
def ar(sz): return ImageFont.truetype(F+"arial.ttf", sz)     # Arial
def jp(sz): return ImageFont.truetype(F+"YuGothB.ttc", sz)   # 游ゴシック Bold

icon = Image.open(A/"funnyjpop-icon.png").convert("RGBA")

def bg():
    img = Image.new("RGB", (W, H), (20,11,8))
    top, bot = (44,21,16), (16,9,6)
    for y in range(H):
        f = y/H
        img.paste(tuple(int(top[i]+(bot[i]-top[i])*f) for i in range(3)), (0,y,W,y+1))
    return img

def card(out, big_lines, jp_line, en_line, accent, icon_size=430):
    img = bg(); d = ImageDraw.Draw(img)
    ic = icon.resize((icon_size, icon_size), Image.LANCZOS)
    iy = (H - icon_size)//2
    img.paste(ic, (70, iy), ic)
    x = 70 + icon_size + 48
    # measure total text height to vertically center
    big_f = af(76); jp_f = jp(34); en_f = ar(30); ac_f = af(26)
    lh_big = 86
    total = lh_big*len(big_lines) + 18 + 46 + 40 + 22 + 40
    y = (H - total)//2
    for ln in big_lines:
        d.text((x, y), ln, font=big_f, fill=GOLD); y += lh_big
    y += 18
    d.text((x, y), jp_line, font=jp_f, fill=CREAM); y += 46
    d.text((x, y), en_line, font=en_f, fill=SUB); y += 40
    y += 22
    d.text((x, y), accent, font=ac_f, fill=LIME)
    img.save(out, quality=92)
    print("wrote", out)

card(A/"og-home.png",
     ["FUNNY J-POP"],
     "日本のメロディを、世界のリズムで。",
     "Japanese melodies, global grooves.",
     "JUKEBOX STUDIO   ·   WORLD MUSIC MAP")

card(A/"og-map.png",
     ["WORLD", "MUSIC MAP"],
     "世界の音楽を、地図で掘る。",
     "190 genres · 121 cities · 74 countries",
     "FUNNY J-POP   ·   powered by YouTube   ·   JA / EN")
