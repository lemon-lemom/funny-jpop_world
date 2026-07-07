# -*- coding: utf-8 -*-
"""Generate OGP share images + share stub pages for the Soul Rhythm Check (shindan.html).

Outputs:
  assets/shindan-og/og-<id>.png   (1200x630, one per type)
  assets/shindan-og/og-shindan.png (generic, for shindan.html itself)
  share/shindan-<id>.html          (OGP stub that redirects to ../shindan.html)

Run:  .\\.venv\\Scripts\\python.exe scripts\\generate_shindan_og.py
NOTE: TYPES below must stay in sync with RESULTS in shindan.html.
"""
import os
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

# (id, nameJa, nameEn, typeName, labelText)
TYPES = [
    ("samba", "サンバ", "SAMBA", "太陽のカーニバル魂", "SAMBA"),
    ("salsa_ny", "サルサ", "SALSA (NY)", "眠らない街のダンサー", "SALSA"),
    ("balkan_brass", "バルカン・ブラス", "BALKAN BRASS", "愛すべきカオスの指揮者", "BALKAN"),
    ("afrobeat", "アフロビート", "AFROBEAT", "不屈のグルーヴ・エンジン", "AFROBEAT"),
    ("gospel", "ゴスペル", "GOSPEL", "魂を持ち上げる合唱隊長", "GOSPEL"),
    ("flamenco", "フラメンコ", "FLAMENCO", "情熱と哀愁の求道者", "FLAMENCO"),
    ("tango", "タンゴ", "TANGO", "夜のドラマの主役", "TANGO"),
    ("filmi", "フィルミー", "FILMI (BOLLYWOOD)", "感情ジェットコースターの主演", "FILMI"),
    ("reggae", "レゲエ", "REGGAE", "動じないレイドバック賢者", "REGGAE"),
    ("son_cubano", "ソン・クバーノ", "SON CUBANO", "夕暮れの人たらし", "SON"),
    ("irish_folk", "アイリッシュ・フォーク", "IRISH FOLK", "酒場の吟遊詩人", "IRISH"),
    ("city_pop", "シティ・ポップ", "CITY POP", "真夜中のシティ・クルーザー", "CITY POP"),
    ("bossa_nova", "ボサノヴァ", "BOSSA NOVA", "囁きの美学者", "BOSSA"),
    ("fado", "ファド", "FADO", "運命を歌う夜の詩人", "FADO"),
    ("desert_blues", "デザート・ブルース", "DESERT BLUES", "地平線をゆく孤高の旅人", "DESERT"),
    ("gamelan", "ガムラン", "GAMELAN", "異世界の周波数の持ち主", "GAMELAN"),
]

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
    d.text((80, 556), "▶ あなたのリズムも、6つの質問・30秒で見つかる", font=load_font(24), fill=CREAM + (150,))


def type_image(t):
    gid, name_ja, name_en, type_name, label = t
    img = base_canvas()
    draw_vinyl(img, 930, 320, 240, label)
    d = ImageDraw.Draw(img)
    header(d)
    d.text((80, 196), "私の魂のリズムは", font=load_font(34), fill=CREAM)
    name = f"『{name_ja}』"
    f_name = fit_font(d, name, 590, 92)
    # orange offset shadow, then cream text (site's h1 style)
    ny = 250
    d.text((84, ny + 4), name, font=f_name, fill=ACC1 + (150,))
    d.text((80, ny), name, font=f_name, fill=CREAM)
    ny2 = ny + f_name.size + 26
    d.text((88, ny2), name_en, font=load_font(28), fill=ACC2)
    badge(d, 84, ny2 + 52, type_name, load_font(32))
    footer(d)
    return img.convert("RGB")


def generic_image():
    img = base_canvas()
    draw_vinyl(img, 930, 320, 240, "?")
    d = ImageDraw.Draw(img)
    header(d)
    d.text((80, 208), "あなたの魂は、", font=load_font(56), fill=CREAM)
    d.text((84, 292), "どのリズムで打っている?", font=load_font(56), fill=ACC1 + (150,))
    d.text((80, 288), "どのリズムで打っている?", font=load_font(56), fill=CREAM)
    badge(d, 84, 396, "全16タイプ × 聴けるJ-POPアレンジ付き", load_font(30))
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
<meta property="og:title" content="私の魂のリズムは『{name_ja}』({type_name})">
<meta property="og:description" content="知ってる歌が、知らない国のリズムで鳴る。6つの質問・全16タイプの「魂のリズム診断」— Funny J-POP">
<meta property="og:url" content="{base}/share/shindan-{gid}.html">
<meta property="og:image" content="{base}/assets/shindan-og/og-{gid}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="私の魂のリズムは『{name_ja}』({type_name})">
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
    for t in TYPES:
        gid, name_ja, _, type_name, _ = t
        type_image(t).save(os.path.join(OG_DIR, f"og-{gid}.png"), optimize=True)
        stub = STUB_TEMPLATE.format(gid=gid, name_ja=name_ja, type_name=type_name, base=BASE_URL)
        with open(os.path.join(SHARE_DIR, f"shindan-{gid}.html"), "w", encoding="utf-8") as fp:
            fp.write(stub)
        print(f"og-{gid}.png + share/shindan-{gid}.html")
    print("done.")


if __name__ == "__main__":
    main()
