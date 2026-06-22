#!/usr/bin/env python3
"""World Music Map のSNS宣伝画像を生成 (16:9 と 正方形)。"""
import sys, io, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

A = Path(r"C:/claude/web_test/assets")
GOLD=(245,192,78); CREAM=(243,234,217); LIME=(158,240,26); TEAL=(45,212,191); PINK=(255,77,109); SUB=(208,196,176)
F="C:/Windows/Fonts/"
def af(s): return ImageFont.truetype(F+"arialbd.ttf", s)
def ar(s): return ImageFont.truetype(F+"arial.ttf", s)
def jp(s): return ImageFont.truetype(F+"YuGothB.ttc", s)
icon = Image.open(A/"funnyjpop-icon.png").convert("RGBA")

def gradient(w,h):
    img=Image.new("RGB",(w,h),(18,10,7)); top,bot=(40,20,15),(12,7,5)
    for y in range(h):
        f=y/h; img.paste(tuple(int(top[i]+(bot[i]-top[i])*f) for i in range(3)),(0,y,w,y+1))
    return img

def pins(d, w, h, n, seed=7):
    """地図感を出す装飾ピン(リング付きの点)"""
    random.seed(seed)
    cols=[TEAL,LIME,PINK,GOLD]
    for _ in range(n):
        x=random.randint(int(w*0.04), int(w*0.96)); y=random.randint(int(h*0.06), int(h*0.94))
        r=random.choice([3,4,5,6]); c=random.choice(cols)
        d.ellipse([x-r*3,y-r*3,x+r*3,y+r*3], outline=c+(0,) if False else c, width=1)
        d.ellipse([x-r,y-r,x+r,y+r], fill=c)

def make(out, w, h, icon_size, title_lines, title_sz, lh, tagjp, tagjp_sz, stats, stats_sz, brand, brand_sz, layout):
    img=gradient(w,h); d=ImageDraw.Draw(img)
    # decorative dotted grid + pins (behind)
    for gx in range(0,w,46): d.line([(gx,0),(gx,h)], fill=(255,255,255,8))
    pins(d,w,h, 26 if layout=="wide" else 22)
    ic=icon.resize((icon_size,icon_size), Image.LANCZOS)
    if layout=="wide":
        iy=(h-icon_size)//2; img.paste(ic,(64,iy),ic)
        x=64+icon_size+44; tot=lh*len(title_lines)+20+tagjp_sz+18+stats_sz+24+brand_sz
        y=(h-tot)//2
        for ln in title_lines: d.text((x,y),ln,font=af(title_sz),fill=GOLD); y+=lh
        y+=20; d.text((x,y),tagjp,font=jp(tagjp_sz),fill=CREAM); y+=tagjp_sz+18
        d.text((x,y),stats,font=ar(stats_sz),fill=SUB); y+=stats_sz+24
        d.text((x,y),brand,font=af(brand_sz),fill=LIME)
    else: # square: icon top-center, text below
        ix=(w-icon_size)//2; img.paste(ic,(ix,70),ic)
        y=70+icon_size+40
        for ln in title_lines:
            tw=d.textlength(ln,font=af(title_sz)); d.text(((w-tw)/2,y),ln,font=af(title_sz),fill=GOLD); y+=lh
        y+=14; tw=d.textlength(tagjp,font=jp(tagjp_sz)); d.text(((w-tw)/2,y),tagjp,font=jp(tagjp_sz),fill=CREAM); y+=tagjp_sz+16
        tw=d.textlength(stats,font=ar(stats_sz)); d.text(((w-tw)/2,y),stats,font=ar(stats_sz),fill=SUB); y+=stats_sz+22
        tw=d.textlength(brand,font=af(brand_sz)); d.text(((w-tw)/2,y),brand,font=af(brand_sz),fill=LIME)
    img.save(out, quality=92); print("wrote", out, img.size)

make(A/"promo-map-16x9.png", 1280,720, 470,
     ["WORLD","MUSIC MAP"], 92, 104, "世界の音楽を、地図で掘る。", 38,
     "190 genres · 121 cities · 74 countries", 30, "FUNNY J-POP  ·  YouTube-linked  ·  JA / EN", 26, "wide")

make(A/"promo-map-1x1.png", 1080,1080, 520,
     ["WORLD MUSIC MAP"], 70, 84, "世界の音楽を、地図で掘る。", 40,
     "190 genres · 121 cities · 74 countries", 32, "FUNNY J-POP  ·  JA / EN", 28, "square")
