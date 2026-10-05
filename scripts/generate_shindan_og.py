# -*- coding: utf-8 -*-
"""Generate OGP share images + share stub pages for the Soul Rhythm Check (shindan.html).

Outputs:
  assets/shindan-og/og-<id>.png   (1200x630, one per type)
  assets/shindan-og/og-shindan.png (generic, for shindan.html itself)
  share/shindan-<id>.html          (OGP stub that redirects to ../shindan.html)

Run:  .\\.venv\\Scripts\\python.exe scripts\\generate_shindan_og.py
Types, names and rarity come from data/shindan64.json (built by build_shindan64.py).
"""
import json
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OG_DIR = os.path.join(ROOT, "assets", "shindan-og")
SHARE_DIR = os.path.join(ROOT, "share")
BASE_URL = "https://lemon-lemom.github.io/funny-jpop_world"

BG = (42, 20, 14)
BG2 = (58, 29, 18)
ACC1 = (255, 107, 53)
ACC2 = (245, 192, 78)
CREAM = (246, 232, 213)
INK = (28, 13, 8)
GROOVE = (36, 21, 17)
VINYL = (18, 10, 7)

DATA = json.load(open(os.path.join(ROOT, "data", "shindan64.json"), encoding="utf-8"))


def stars(n):
    return "？？？" if n > 5 else "★" * n + "☆" * (5 - n)


def load_types():
    """One dict per shareable result (64 types + the secret), with display fields."""
    tribes = {t["id"]: t for t in DATA["tribes"]}
    lins = {l["id"]: l for l in DATA["lineages"]}
    out = []
    for t in DATA["types"] + [DATA["secret"]]:
        if t is DATA["secret"]:
            where = "？？族・こだまの系譜"
        else:
            lin = lins[t["lineage"]]
            where = f"{tribes[lin['tribe']]['nameJa']}・{lin['nameJa']}"
        en = re.sub(r"\s*\(.*\)", "", t["nameEn"])
        one_in = int(DATA["totalPatterns"] / t["count"] + 0.5)  # same rounding as Math.round in shindan.html
        out.append(dict(
            gid=t["id"], name_ja=t["nameJa"], type_name=t["name"],
            label=en if len(en) <= 10 else en.split()[0], where=where,
            stars=stars(t["stars"]), rank=t["rank"],
            rarity=f"{stars(t['stars'])} {t['rank']}  ・  約{one_in:,}人に1人",
        ))
    return out

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\meiryob.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise FileNotFoundError("No suitable Japanese font found: " + ", ".join(FONT_CANDIDATES))


def fit_font(draw, text, max_width, start_size, min_size=40):
    size = start_size
    while size > min_size:
        f = load_font(size)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 4
    return load_font(min_size)


def draw_vinyl(img, cx, cy, r, label_text):
    d = ImageDraw.Draw(img)
    # shadow
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([cx - r, cy - r + 14, cx + r, cy + r + 14], fill=(0, 0, 0, 130))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(sh)
    d = ImageDraw.Draw(img)
    # disc + grooves
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=VINYL)
    for gr in range(int(r * 0.42), r - 8, 9):
        d.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], outline=GROOVE, width=2)
    # sheen (two soft arcs)
    sheen = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.pieslice([cx - r, cy - r, cx + r, cy + r], 200, 235, fill=(255, 255, 255, 16))
    sd.pieslice([cx - r, cy - r, cx + r, cy + r], 20, 55, fill=(255, 255, 255, 12))
    sheen = sheen.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(sheen)
    d = ImageDraw.Draw(img)
    # label (text above the spindle hole, like a real vinyl label)
    lr = int(r * 0.36)
    d.ellipse([cx - lr, cy - lr, cx + lr, cy + lr], fill=ACC1, outline=INK, width=6)
    if label_text == "?":
        d.text((cx, cy), label_text, font=load_font(96), fill=INK, anchor="mm")
    else:
        f = fit_font(d, label_text, lr * 2 - 44, 36, 18)
        d.text((cx, cy - int(lr * 0.42)), label_text, font=f, fill=INK, anchor="mm")
        d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=INK)


def badge(d, x, y, text, font, pad_x=22, pad_y=12):
    w = d.textlength(text, font=font)
    h = font.size
    box = [x, y, x + w + pad_x * 2, y + h + pad_y * 2]
    # hard shadow like the site's buttons
    d.rounded_rectangle([box[0], box[1] + 5, box[2], box[3] + 5], radius=(h + pad_y * 2) // 2, fill=INK)
    d.rounded_rectangle(box, radius=(h + pad_y * 2) // 2, fill=ACC2, outline=INK, width=4)
    d.text((x + pad_x, y + pad_y - 2), text, font=font, fill=INK)
    return box


def base_canvas():
    img = Image.new("RGBA", (1200, 630), BG + (255,))
    # warm glow top-right
    glow = Image.new("RGBA", (1200, 630), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([600, -320, 1500, 380], fill=BG2 + (255,))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img.alpha_composite(glow)
    return img


def header(d):
    d.text((80, 58), "FUNNY J-POP PRESENTS", font=load_font(26), fill=ACC2)
    d.text((80, 100), "魂のリズム診断  —  SOUL RHYTHM CHECK", font=load_font(30), fill=CREAM + (210,))
    d.line([80, 152, 620, 152], fill=CREAM + (60,), width=2)


def footer(d):
    d.text((80, 556), "▶ あなたのリズムも、12の質問で見つかる(全64タイプ+隠し1)", font=load_font(24), fill=CREAM + (150,))


def type_image(t):
    img = base_canvas()
    draw_vinyl(img, 930, 320, 240, t["label"])
    d = ImageDraw.Draw(img)
    header(d)
    d.text((80, 186), "私の魂のリズムは", font=load_font(32), fill=CREAM)
    d.text((80, 230), t["where"], font=fit_font(d, t["where"], 590, 26, 18), fill=ACC2)
    name = f"『{t['name_ja']}』"
    f_name = fit_font(d, name, 590, 84)
    # orange offset shadow, then cream text (site's h1 style)
    ny = 268
    d.text((84, ny + 4), name, font=f_name, fill=ACC1 + (150,))
    d.text((80, ny), name, font=f_name, fill=CREAM)
    ny2 = ny + f_name.size + 20
    badge(d, 84, ny2, t["type_name"], fit_font(d, t["type_name"], 540, 30, 20))
    d.text((88, ny2 + 72), t["rarity"], font=load_font(24), fill=ACC2)
    footer(d)
    return img.convert("RGB")


def generic_image():
    img = base_canvas()
    draw_vinyl(img, 930, 320, 240, "?")
    d = ImageDraw.Draw(img)
    header(d)
    d.text((80, 208), "あなたのリズムは、", font=load_font(56), fill=CREAM)
    d.text((84, 292), "体のどこで鳴っている?", font=load_font(56), fill=ACC1 + (150,))
    d.text((80, 288), "体のどこで鳴っている?", font=load_font(56), fill=CREAM)
    badge(d, 84, 396, "全64タイプ+隠し1 ・ レア度つき", load_font(30))
    footer(d)
    return img.convert("RGB")


STUB_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>私の魂のリズムは『{name_ja}』でした — 魂のリズム診断 | Funny J-POP</title>
<meta name="robots" content="noindex">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Funny J-POP">
<meta property="og:locale" content="ja_JP">
<meta property="og:title" content="私の魂のリズムは『{name_ja}』({type_name}) {stars} {rank}">
<meta property="og:description" content="知ってる歌が、知らない国のリズムで鳴る。12の質問・全64タイプ+隠し1の「魂のリズム診断」— Funny J-POP">
<meta property="og:url" content="{base}/share/shindan-{gid}.html">
<meta property="og:image" content="{base}/assets/shindan-og/og-{gid}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="私の魂のリズムは『{name_ja}』({type_name}) {stars} {rank}">
<meta name="twitter:description" content="知ってる歌が、知らない国のリズムで鳴る。魂のリズム診断 — Funny J-POP">
<meta name="twitter:image" content="{base}/assets/shindan-og/og-{gid}.png">
<meta http-equiv="refresh" content="0; url=../shindan.html">
<link rel="canonical" href="{base}/shindan.html">
</head>
<body style="font-family:sans-serif;background:#2a140e;color:#f6e8d5;display:grid;place-items:center;min-height:100vh;margin:0">
<p>診断ページへ移動しています… <a href="../shindan.html" style="color:#f5c04e">開かない場合はこちら</a></p>
</body>
</html>
"""


def main():
    os.makedirs(OG_DIR, exist_ok=True)
    os.makedirs(SHARE_DIR, exist_ok=True)
    generic_image().save(os.path.join(OG_DIR, "og-shindan.png"), optimize=True)
    print("og-shindan.png")
    for t in load_types():
        gid = t["gid"]
        type_image(t).save(os.path.join(OG_DIR, f"og-{gid}.png"), optimize=True)
        stub = STUB_TEMPLATE.format(base=BASE_URL, **t)
        with open(os.path.join(SHARE_DIR, f"shindan-{gid}.html"), "w", encoding="utf-8") as fp:
            fp.write(stub)
        print(f"og-{gid}.png + share/shindan-{gid}.html")
    print("done.")


if __name__ == "__main__":
    main()
