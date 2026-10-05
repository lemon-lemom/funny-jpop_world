# -*- coding: utf-8 -*-
"""Soul Rhythm Check 64 — design spec (questions / tribes / lineages / types).

Edit this file, then run scripts/build_shindan64.py to re-tune rarity and
regenerate data/shindan64.json (the file shindan.html reads).

Scoring model
-------------
Every option adds a delta to 8 axes:
  body axes  F 足 / W 腰 / C 胸 / M 頭   -> tribe = argmax(body + tribe bias)
  modifiers  H 熱(+)静(-) / B 陽(+)哀(-) / S みんな(+)ひとり(-) / E 土着(+)都会(-)
             -> type = nearest target in the tribe (squared distance + per-type bias)
Body questions (even Q) mainly move F/W/C/M; flavor questions (odd Q) are a 2x2
on one modifier pair, and every pair appears exactly once.
Options flagged y=True are the hidden-type triggers: pick all of them -> yodel.
"""

AXES = ["F", "W", "C", "M", "H", "B", "S", "E"]


def opt(t, y=False, **d):
    return {"t": t, "d": [d.get(a, 0) for a in AXES], "y": y}


QUESTIONS = [
    {"emoji": "🌅", "text": "理想の週末、その始まりは?", "opts": [
        opt("フェスやイベントへ、朝から友達と出発!", H=2, S=2, F=1),
        opt("早起きして、ひとりで山に登る", y=True, H=2, S=-2, M=1),
        opt("友達と、のんびり遅めのブランチ", H=-2, S=2, W=1),
        opt("目覚ましなしで、昼までひとりの時間", H=-2, S=-2, C=1),
    ]},
    {"emoji": "🏞", "text": "いちばん心が動く風景は?", "opts": [
        opt("人と音であふれかえる、祭りの広場", F=3, S=1, B=1),
        opt("ネオンがにじむ、真夜中の都会", W=3, E=-1),
        opt("夕暮れどきの、誰もいない海辺", C=3, B=-1, S=-1),
        opt("雲の上にそびえる、雪の峰々", y=True, M=3, E=1),
    ]},
    {"emoji": "🍽", "text": "旅先でいちばん楽しみな食事は?", "opts": [
        opt("話題のレストランで、みんなで乾杯", B=2, E=-2),
        opt("山小屋で、とろけるチーズとあったかいスープ", y=True, B=2, E=2),
        opt("夜景の見えるバーで、静かに一杯", B=-2, E=-2, W=1),
        opt("何百年も続く老舗で、土地の料理をしみじみ", B=-2, E=2, M=1),
    ]},
    {"emoji": "🎤", "text": "カラオケでのあなたの役回りは?", "opts": [
        opt("マイクを離さない、盛り上げ隊長", F=3, H=1, S=1),
        opt("タンバリンと合いの手で、場を温める職人", W=3, S=1, B=1),
        opt("しっとりバラードで、空気を一変させる", C=3, B=-1),
        opt("誰も知らないマニアックな曲を入れて満足", M=3, S=-1),
    ]},
    {"emoji": "🧳", "text": "あなたの旅のスタイルは?", "opts": [
        opt("話題のスポットを、計画びっしりで完全制覇", H=2, E=-2),
        opt("現地の祭りに飛び込んで、一緒に踊る", H=2, E=2, F=1),
        opt("高級ホテルで、何もしない贅沢", H=-2, E=-2, W=1),
        opt("ガイドブックにない山あいの村で、何日もぼんやり", y=True, H=-2, E=2, M=1),
    ]},
    {"emoji": "☔", "text": "落ち込んだ日の処方箋は?", "opts": [
        opt("爆音で音楽をかけて、踊って忘れる", F=3, H=1),
        opt("お風呂とお菓子で、とことんダラダラ", W=3, H=-1),
        opt("悲しい曲で、とことん泣ききる", C=3, B=-1),
        opt("散歩や瞑想で、頭を空っぽにする", M=3),
    ]},
    {"emoji": "🎂", "text": "誕生日、理想の過ごし方は?", "opts": [
        opt("サプライズパーティーで大騒ぎ", B=2, S=2, F=1),
        opt("好きなものだけ詰め込んだ、ひとりご褒美デー", B=2, S=-2, W=1),
        opt("気心の知れた数人と、しみじみ語り明かす", B=-2, S=2, C=1),
        opt("静かに過ごして、この1年を振り返る", B=-2, S=-2, M=1),
    ]},
    {"emoji": "🎧", "text": "イヤホンから流れてきた曲。最初に反応するのは?", "opts": [
        opt("つま先が、勝手にリズムを刻みだす", F=3),
        opt("首と肩が、じわっと揺れはじめる", W=3),
        opt("歌詞と声が刺さって、ちょっと泣きそう", C=3),
        opt("「今の何拍子?」が気になって止まらない", M=3),
    ]},
    {"emoji": "🌦", "text": "いちばん好きな空は?", "opts": [
        opt("雲ひとつない、真夏の快晴", H=2, B=2),
        opt("嵐の前の、ざわつく空", H=2, B=-2),
        opt("高原の、澄みきった朝の空", y=True, H=-2, B=2),
        opt("しとしと雨が降る、夜の空", H=-2, B=-2),
    ]},
    {"emoji": "🌃", "text": "パーティーの夜。気づけばあなたはどこにいる?", "opts": [
        opt("ダンスフロアのど真ん中", F=3, S=1),
        opt("バーカウンターで、揺れながらおしゃべり", W=3),
        opt("ベランダで、誰かと人生の話", C=3),
        opt("本棚を見つけて、ひとり読みふける", M=3, S=-1),
    ]},
    {"emoji": "🕰", "text": "タイムスリップできるなら、どこへ行く?", "opts": [
        opt("千年前の村祭りに、飛び入り参加", S=2, E=2),
        opt("1970年代NYのディスコで、朝まで", S=2, E=-2, F=1),
        opt("古代の神殿で、ひとり儀式を見届ける", S=-2, E=2, M=1),
        opt("1980年代の東京、真夜中の首都高をドライブ", S=-2, E=-2, W=1),
    ]},
    {"emoji": "🎬", "text": "人生という映画。エンドロールに流したいのは?", "opts": [
        opt("出演者全員で踊りまくる、大団円のフィナーレ", F=3, S=1, B=1),
        opt("ゆるいグルーヴにのせた、笑えるNG集", W=3, B=1),
        opt("静かなピアノと、こらえきれない涙", C=3, H=-1),
        opt("謎を残したまま、神秘的に幕を閉じる", M=3, E=1),
    ]},
]

# Target share of all non-secret results per tribe.
TRIBES = [
    {"id": "foot",  "nameJa": "足族", "nameEn": "FOOT",  "emoji": "🦶", "catch": "体が勝手に踊り出す", "target": 0.30},
    {"id": "hip",   "nameJa": "腰族", "nameEn": "HIPS",  "emoji": "🌀", "catch": "揺れて、うねって、乗る", "target": 0.30},
    {"id": "heart", "nameJa": "胸族", "nameEn": "HEART", "emoji": "❤️", "catch": "歌と感情で震える", "target": 0.25},
    {"id": "head",  "nameJa": "頭族", "nameEn": "HEAD",  "emoji": "🧠", "catch": "構造とトランスにハマる", "target": 0.15},
]

LINEAGES = [
    {"id": "drum_festival",     "tribe": "foot",  "emoji": "🥁", "nameJa": "太鼓の祭り系", "catch": "打楽器で街ごと揺らす"},
    {"id": "salsa_night",       "tribe": "foot",  "emoji": "💃", "nameJa": "サルサの夜系", "catch": "ペアで踊る夜に生きる"},
    {"id": "showtime",          "tribe": "foot",  "emoji": "🪩", "nameJa": "ショータイム系", "catch": "派手に盛ってこそ人生"},
    {"id": "stomp_folk",        "tribe": "foot",  "emoji": "🎻", "nameJa": "足踏みフォーク系", "catch": "床を踏み鳴らす素朴な熱"},
    {"id": "funk_engine",       "tribe": "hip",   "emoji": "🔥", "nameJa": "ファンク・エンジン系", "catch": "グルーヴで押し切る推進力"},
    {"id": "caribbean_offbeat", "tribe": "hip",   "emoji": "🌴", "nameJa": "カリブのオフビート系", "catch": "裏拍でゆるく跳ねる"},
    {"id": "soul",              "tribe": "hip",   "emoji": "🎙", "nameJa": "ソウル系", "catch": "心の声で揺れる"},
    {"id": "slow_sway",         "tribe": "hip",   "emoji": "🌙", "nameJa": "スロー・スウェイ系", "catch": "甘く、ゆっくり、とろける"},
    {"id": "saudade",           "tribe": "heart", "emoji": "🌊", "nameJa": "サウダージ系", "catch": "戻らないものを愛おしむ"},
    {"id": "passion",           "tribe": "heart", "emoji": "🌹", "nameJa": "激情系", "catch": "情熱と痛みを燃やす"},
    {"id": "voices",            "tribe": "heart", "emoji": "🙌", "nameJa": "声を重ねる系", "catch": "声を重ねてひとつになる"},
    {"id": "nostalgia",         "tribe": "heart", "emoji": "🎞", "nameJa": "ノスタルジー系", "catch": "行ったことのない場所が懐かしい"},
    {"id": "ancient_classics",  "tribe": "head",  "emoji": "🏯", "nameJa": "悠久の古典系", "catch": "千年単位の時間を生きる"},
    {"id": "modal_trance",      "tribe": "head",  "emoji": "🕌", "nameJa": "旋法の陶酔系", "catch": "旋律の渦に溺れる"},
    {"id": "jazz_labyrinth",    "tribe": "head",  "emoji": "🎷", "nameJa": "ジャズの迷宮系", "catch": "複雑さこそ快感"},
    {"id": "otherworld",        "tribe": "head",  "emoji": "🛸", "nameJa": "異界の周波数系", "catch": "この世の外側の響き"},
]

# Familiarity tier -> relative appearance weight inside the tribe.
# S = everyone knows it ... L = legend-class deep cut. Rarer result = bigger discovery.
TIER_WEIGHT = {"S": 8.0, "A": 5.0, "B": 3.0, "C": 1.8, "D": 1.0, "L": 0.4}

# (genreId, lineage, H, B, S, E, tier) — H/B/S/E on a -2..+2 semantic scale.
TYPES = [
    ("samba",              "drum_festival",      2,  2,  2,  1, "S"),
    ("rumba_cubana",       "drum_festival",      1, -1,  2,  2, "C"),
    ("mbalax",             "drum_festival",      2,  1,  1,  2, "D"),
    ("juju",               "drum_festival",      0,  2,  2,  2, "D"),
    ("salsa_ny",           "salsa_night",        2, -1,  0, -2, "A"),
    ("salsa_cubana",       "salsa_night",        2,  1,  1, -1, "B"),
    ("salsa_calena",       "salsa_night",        2,  1, -1, -1, "C"),
    ("chacha",             "salsa_night",       -1,  1,  0, -2, "B"),
    ("disco",              "showtime",           1,  2,  2, -2, "S"),
    ("filmi",              "showtime",           1,  0,  2,  0, "B"),
    ("swing_big_band",     "showtime",           0,  2,  1, -1, "A"),
    ("balkan_brass",       "showtime",           2, -1,  2,  1, "C"),
    ("irish_folk",         "stomp_folk",         0,  0,  1,  2, "A"),
    ("quebecois_folk",     "stomp_folk",         1,  2,  0,  2, "L"),
    ("bluegrass",          "stomp_folk",         2,  0, -1,  2, "B"),
    ("scottish_folk",      "stomp_folk",        -1, -1,  0,  2, "B"),

    ("funk",               "funk_engine",        2,  1,  2, -1, "S"),
    ("new_orleans_funk",   "funk_engine",        1,  2,  2,  1, "C"),
    ("afrobeat",           "funk_engine",        2,  0,  1,  2, "B"),
    ("acid_jazz",          "funk_engine",        1,  1, -1, -2, "B"),
    ("reggae",             "caribbean_offbeat", -1,  1,  1,  1, "S"),
    ("rocksteady",         "caribbean_offbeat", -1, -1,  0,  1, "C"),
    ("ska",                "caribbean_offbeat",  2,  2,  1,  0, "A"),
    ("calypso",            "caribbean_offbeat",  1,  2,  1,  2, "C"),
    ("soul",               "soul",               0, -1,  0, -1, "S"),
    ("motown",             "soul",               1,  2,  1, -2, "A"),
    ("rnb_neo_soul",       "soul",               0,  0, -1, -2, "A"),
    ("neo_soul",           "soul",              -1,  0, -1,  0, "B"),
    ("kizomba",            "slow_sway",         -2,  1, -2,  1, "D"),
    ("son_cubano",         "slow_sway",         -2,  1,  2,  2, "B"),
    ("highlife",           "slow_sway",         -1,  2,  0,  2, "D"),
    ("smooth_jazz",        "slow_sway",         -2,  1, -1, -2, "B"),

    ("fado",               "saudade",           -1, -2, -1,  0, "B"),
    ("morna",              "saudade",           -2, -1,  0,  1, "D"),
    ("bossa_nova",         "saudade",           -2,  1, -2, -1, "S"),
    ("choro",              "saudade",            1,  1,  0,  0, "D"),
    ("tango",              "passion",            1, -2,  0, -2, "A"),
    ("flamenco",           "passion",            2, -2,  0,  1, "A"),
    ("chicago_blues",      "passion",            0, -1, -1, -2, "B"),
    ("russian_folk",       "passion",            1, -1,  2,  2, "C"),
    ("gospel",             "voices",             2,  2,  2,  0, "S"),
    ("isicathamiya",       "voices",            -1,  1,  2,  2, "D"),
    ("polynesian",         "voices",             0,  2,  1,  2, "D"),
    ("doo_wop",            "voices",             0,  2,  1, -2, "B"),
    ("city_pop",           "nostalgia",          0,  1, -2, -2, "S"),
    ("chanson",            "nostalgia",         -1,  0,  0, -1, "A"),
    ("andean_folk",        "nostalgia",          0, -2,  0,  2, "B"),
    ("mpb",                "nostalgia",          0,  2, -1, -1, "C"),

    ("gagaku",             "ancient_classics",  -2,  0,  1,  2, "C"),
    ("chinese_traditional","ancient_classics",  -1,  1, -1,  2, "B"),
    ("gamelan",            "ancient_classics",   0,  1,  2,  2, "B"),
    ("carnatic",           "ancient_classics",   1,  1,  0,  2, "D"),
    ("hindustani",         "modal_trance",      -1, -1, -2,  1, "C"),
    ("persian",            "modal_trance",      -2, -2, -1,  0, "L"),
    ("arabic_tarab",       "modal_trance",       0, -1,  1,  0, "D"),
    ("rajasthani",         "modal_trance",       1,  2,  1,  1, "D"),
    ("hard_bop",           "jazz_labyrinth",     1,  0,  0, -2, "B"),
    ("jazz_fusion",        "jazz_labyrinth",     2,  1, -1, -2, "A"),
    ("gypsy_jazz",         "jazz_labyrinth",     2,  1,  1, -1, "B"),
    ("afro_cuban_jazz",    "jazz_labyrinth",     2,  2,  2, -1, "C"),
    ("desert_blues",       "otherworld",         0, -1, -2,  2, "C"),
    ("ethio_jazz",         "otherworld",         1, -2,  0, -1, "D"),
    ("bulgarian_voices",   "otherworld",        -1, -2,  1,  1, "L"),
    ("georgian_polyphony", "otherworld",        -1, -1,  2,  2, "L"),
]

SECRET = {"genreId": "yodel"}

# Semantic (-2..+2) -> raw units: tribe centroid + semantic * per-axis std * spread.
TARGET_SPREAD = 0.9
# Common types sit nearer the centroid, deep cuts farther out, so geometry (not
# just bias) carries the rarity and each type keeps the people it describes.
TIER_SPREAD = {"S": 0.7, "A": 0.8, "B": 0.9, "C": 1.0, "D": 1.15, "L": 1.35}

# Overall-rate thresholds (fraction) for the star display, rarest first.
STARS = [
    (0.0035, 5, "LEGEND"),
    (0.008, 4, "SUPER RARE"),
    (0.015, 3, "RARE"),
    (0.03, 2, "UNCOMMON"),
    (1.0, 1, "COMMON"),
]
