#!/usr/bin/env python3
"""実データの世界地図ベースのSNS宣伝画像を生成。
   CARTO dark タイル(サイトと同じ)をstitch → 121都市を実緯度経度でピン表示 → ブランド合成。"""
import sys, io, math, urllib.request, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

A = Path(r"C:/claude/web_test/assets")
GOLD=(245,192,78); CREAM=(243,234,217); LIME=(158,240,26); TEAL=(45,212,191); PINK=(255,77,109); SUB=(214,203,184)
F="C:/Windows/Fonts/"
def af(s): return ImageFont.truetype(F+"arialbd.ttf", s)
def ar(s): return ImageFont.truetype(F+"arial.ttf", s)
def jp(s): return ImageFont.truetype(F+"YuGothB.ttc", s)

Z = 2; TS = 512  # @2x tiles -> world 2048
N = 2**Z
WORLD = N*TS
def fetch_world():
    base = Image.new("RGB",(WORLD,WORLD),(11,17,23))
    subs="abcd"
    for tx in range(N):
        for ty in range(N):
            url=f"https://{subs[(tx+ty)%4]}.basemaps.cartocdn.com/dark_all/{Z}/{tx}/{ty}@2x.png"
            req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                t=Image.open(io.BytesIO(r.read())).convert("RGB")
            base.paste(t,(tx*TS,ty*TS))
    return base

def merc(lat,lon):
    x=(lon+180)/360*WORLD
    s=math.sin(math.radians(lat)); s=max(min(s,0.9999),-0.9999)
    y=(0.5 - math.log((1+s)/(1-s))/(4*math.pi))*WORLD
    return x,y

places=json.load(open(r"C:/claude/web_test/data/places.json",encoding="utf-8"))
icon=Image.open(A/"funnyjpop-icon.png").convert("RGBA")
world=fetch_world()
print("world tiles fetched", world.size)

def build(out, W, H, title_lines, tsz, lh, tagjp, layout):
    # scale world square to width W, crop vertically to H (poles are empty ocean)
    sc = W/WORLD
    sw = world.resize((W, W), Image.LANCZOS)
    top = (W-H)//2
    img = sw.crop((0, top, W, top+H)).convert("RGB")
    # darken a touch for contrast
    img = Image.blend(img, Image.new("RGB",(W,H),(8,12,17)), 0.18)
    glow = Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    cols=[TEAL,PINK,LIME,GOLD]
    for i,p in enumerate(places):
        x,y = merc(p["lat"],p["lon"]); x*=sc; y=y*sc-top
        if not(-10<=y<=H+10): continue
        c=cols[i%4]
        gd.ellipse([x-9,y-9,x+9,y+9], fill=c+(70,))
        gd.ellipse([x-3.2,y-3.2,x+3.2,y+3.2], fill=c+(255,))
    glow=glow.filter(ImageFilter.GaussianBlur(0.6))
    img=Image.alpha_composite(img.convert("RGBA"), glow)
    d=ImageDraw.Draw(img)
    # bottom scrim for legibility
    scrim=Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(scrim)
    for yy in range(H):
        a=int(max(0,(yy-(H*0.42))/(H*0.58))*210)
        sd.line([(0,yy),(W,yy)],fill=(6,9,13,a))
    img=Image.alpha_composite(img,scrim); d=ImageDraw.Draw(img)
    # brand icon + text bottom-left
    isz= int(H*0.20); ic=icon.resize((isz,isz),Image.LANCZOS)
    pad=int(W*0.045); by=H-pad-isz
    img.alpha_composite(ic,(pad,by))
    tx=pad+isz+int(W*0.025)
    ty=by + (isz - (lh*len(title_lines)+10+tsz+8+30))//2
    for ln in title_lines: d.text((tx,ty),ln,font=af(tsz),fill=GOLD); ty+=lh
    ty+=8; d.text((tx,ty),tagjp,font=jp(int(tsz*0.42)),fill=CREAM)
    # top-right stat chip
    chip="190 GENRES · 121 CITIES · 74 COUNTRIES"
    cf=af(int(H*0.030)); cw=d.textlength(chip,font=cf)
    d.text((W-pad-cw, pad), chip, font=cf, fill=LIME)
    # map attribution (CARTO/OSM terms)
    at="© OpenStreetMap  © CARTO"; afnt=ar(13); aw=d.textlength(at,font=afnt)
    d.text((W-aw-10, H-22), at, font=afnt, fill=(150,160,168))
    img.convert("RGB").save(out, quality=92); print("wrote",out,img.size)

build(A/"promo-map-16x9.png", 1280,720, ["WORLD MUSIC MAP"], 60, 66, "世界の音楽を、地図で掘る。", "wide")
build(A/"promo-map-1x1.png", 1080,1080, ["WORLD","MUSIC MAP"], 78, 86, "世界の音楽を、地図で掘る。", "square")
