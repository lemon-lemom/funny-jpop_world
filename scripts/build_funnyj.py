#!/usr/bin/env python3
"""Funny J-POP チャンネルの動画を解析し、各動画の「アレンジ・スタイル」を
world-music-map の genre_id に対応付けて data/funnyj.json を生成する。

出力: data/funnyj.json = { genre_id: [ {videoId, song, artist, style, url, publishedAt} ... ] }
フロントの world-music-map.html がジャンル詳細の「Funny J-POP」タブで読む。
"""
import json, re, csv, sys, io
from pathlib import Path
from collections import defaultdict, Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:/claude/web_test")
SRC = Path(r"C:/claude/funnyJ-pop/output/youtube_channel_videos_2026-06-17/funny_jpop_videos.json")

# ---------- title parsing (see extract_funnyj_styles.py for derivation) ----------
DASHES = "–—−-"
MANUAL_STYLE = {"EZ DO DANCE/ TRF": "Funky Soul", "Sexy / hitomi": "Southern Confession Soul"}

def is_quiz(t):    return "イントロどん" in t or "難易度" in t
def is_medley(t):  return "メドレー" in t

def clean_style(s):
    s = re.split(r"[｜|]", s)[0]
    s = re.sub(r"\s*\(?\s*ver\.*\s*\)?\s*$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\bReboot\b|\bReimagined\b|\bRe-?make\b|\bRevue\b|\bRevival\b", "", s, flags=re.IGNORECASE)
    return s.strip(" -–—.｜|×").strip()

def parse(title):
    t = title.strip()
    mp = re.search(r"[（(]\s*([^（）()]+?)\s*(?:ver|cover)\.?\s*[)）]", t, flags=re.IGNORECASE)
    if mp:
        left, style = t[:mp.start()], mp.group(1).strip()
    else:
        head = re.split(r"[｜|]", t)[0]
        slash = head.find("/")
        rs = slash + 1 if slash >= 0 else 0
        m = re.search(r"\s*[–—]\s*|\s+-\s*|\s+-\s+", head[rs:])
        if not m:
            for k, v in MANUAL_STYLE.items():
                if k in t:
                    a = k.split("/")[1].strip() if "/" in k else ""
                    return {"song": k.split("/")[0].strip(), "artist": a, "style": v}
            return None
        cut = rs + m.start()
        left, style = head[:cut], head[cut + (m.end() - m.start()):]
    style = clean_style(style)
    if not style:
        return None
    left = re.sub(r"^【[^】]*】\s*", "", left).strip()
    if "/" in left:
        song, artist = left.rsplit("/", 1)
    else:
        song, artist = left, ""
    return {"song": song.strip(" -–—"), "artist": artist.strip(), "style": style}

# ---------- style -> genre_id (ordered; first substring match wins) ----------
# 順序が優先度。具体的なものを上に、汎用を下に置く。
RULES = [
    # --- Cuba / Latin Caribbean ---
    ("cha-cha", "chacha"), ("cha cha", "chacha"),
    ("mambo", "mambo"), ("boogaloo", "boogaloo"),
    ("guaguanc", "guaguanco"),
    ("cali salsa", "salsa_calena"), ("salsa cali", "salsa_calena"),
    ("cuban salsa", "salsa_cubana"), ("salsa carnival", "salsa_cubana"),
    ("salsa dura", "salsa_ny"), ("salsa", "salsa_ny"), ("latin velocity", "salsa_ny"),
    ("son afro", "son_cubano"), ("street son", "son_cubano"),
    # --- Flamenco / Iberia (before generic rumba) ---
    ("flamenco", "flamenco"), ("toque y cante", "flamenco"), ("palmas", "flamenco"),
    ("fado", "fado"), ("morna", "morna"),
    ("yé-yé", "chanson"), ("ye-ye", "chanson"), ("chanson", "chanson"),
    # --- remaining rumba / cuban ---
    ("rumba", "rumba_cubana"), ("cuban", "son_cubano"),
    # --- Brazil ---
    ("bossa", "bossa_nova"), ("choro", "choro"), ("mpb", "mpb"),
    ("pagode", "samba"), ("samba", "samba"),
    # --- Caribbean ---
    ("calypso", "calypso"), ("soca", "soca"), ("zouk", "kizomba"),
    ("rocksteady", "rocksteady"), ("two-tone ska", "ska"), ("ska", "ska"),
    ("reggae", "reggae"), ("dub", "dub"),
    # --- Tango / Andes ---
    ("tango", "tango"), ("milonga", "milonga"),
    ("andean", "andean_folk"), ("huayno", "andean_folk"),
    # --- Gospel (before soul) ---
    ("gospel", "gospel"), ("soul prayer", "gospel"), ("testimony", "gospel"),
    ("soul choir", "gospel"), ("soul-gospel", "gospel"),
    # --- Neo-soul (own genre) / R&B (before soul) ---
    ("neo-soul", "neo_soul"), ("neo soul", "neo_soul"), ("r&b", "rnb_neo_soul"),
    # --- Jazz (specific first) ---
    ("acid jazz", "acid_jazz"), ("hard bop", "hard_bop"), ("bebop", "bebop"),
    ("gypsy jazz", "gypsy_jazz"), ("manouche", "gypsy_jazz"),
    ("smooth jazz", "smooth_jazz"),
    ("latin jazz", "afro_cuban_jazz"), ("afro-cuban jazz", "afro_cuban_jazz"),
    ("big band jazz", "swing_big_band"), ("swing", "swing_big_band"),
    ("ethio", "ethio_jazz"),
    ("afro-jazz", "jazz_fusion"), ("world-jazz", "jazz_fusion"),
    ("jazz trio", "jazz_fusion"), ("contemporary jazz", "jazz_fusion"), ("jazz", "jazz_fusion"),
    # --- Blues / Doo-wop ---
    ("bluegrass", "bluegrass"),
    ("blues", "chicago_blues"), ("bluesology", "chicago_blues"),
    ("doo-wop", "doo_wop"), ("doo wop", "doo_wop"),
    # --- Disco / Funk / Motown / Soul ---
    ("disco", "disco"),
    ("swamp-funk", "new_orleans_funk"), ("swamp funk", "new_orleans_funk"),
    ("funk", "funk"),
    ("motown", "motown"),
    ("philly", "soul"), ("philadelphia", "soul"),
    ("behind-the-beat", "soul"),
    ("soul", "soul"),
    # --- Africa ---
    ("afrobeat", "afrobeat"), ("mbalax", "mbalax"), ("mbala", "mbalax"),
    ("makossa", "makossa"), ("highlife", "highlife"), ("soukous", "soukous"),
    ("juju", "juju"), ("yoruba", "juju"),
    ("zulu", "isicathamiya"), ("ndebele", "isicathamiya"), ("isicathamiya", "isicathamiya"),
    ("wassoulou", "desert_blues"), ("sahel", "desert_blues"), ("desert", "desert_blues"),
    ("balafon", "highlife"), ("guinea", "highlife"),
    ("kwaito", "kwaito"), ("amapiano", "amapiano"), ("gqom", "gqom"),
    ("ethiopian", "ethio_jazz"),
    # European choral (must precede the generic African "a cappella" below)
    ("georgian", "georgian_polyphony"), ("bulgarian", "bulgarian_voices"),
    ("a cappella", "isicathamiya"), ("acappella", "isicathamiya"),
    ("afro choir", "isicathamiya"), ("african choir", "isicathamiya"),
    ("african vocal", "isicathamiya"), ("vocal ensemble", "isicathamiya"),
    ("african", "afrobeat"), ("afro-vocal", "isicathamiya"), ("afro ", "afrobeat"),
    # --- Celtic / Euro folk ---
    ("québéc", "quebecois_folk"), ("quebec", "quebecois_folk"),
    ("irish", "irish_folk"), ("reel", "irish_folk"), ("jig", "irish_folk"),
    ("celtic", "scottish_folk"),
    ("yodel", "yodel"), ("alpine", "yodel"),
    ("cossack", "russian_folk"),
    ("bulgarian", "bulgarian_voices"), ("georgian", "georgian_polyphony"),
    ("balkan", "balkan_brass"),
    # --- India ---
    ("carnatic", "carnatic"),
    ("bollywood", "filmi"), ("filmi", "filmi"),
    ("bhangra", "bhangra"), ("qawwali", "qawwali"),
    ("garba", "rajasthani"), ("dandiya", "rajasthani"), ("rajasthani", "rajasthani"),
    ("bihu", "rajasthani"), ("indian folk", "rajasthani"),
    ("hindustani", "hindustani"), ("indian classical", "hindustani"),
    ("インド古典", "hindustani"), ("hindustani indo", "hindustani"), ("indo", "hindustani"),
    # --- SE Asia ---
    ("jaipongan", "gamelan"), ("gamelan", "gamelan"), ("gong kebyar", "gamelan"),
    ("dangdut", "dangdut"),
    # --- China / HK ---
    ("cantopop", "cantopop"), ("香港", "chinese_traditional"), ("kung", "chinese_traditional"),
    ("mandopop", "mandopop"),
    ("han chinese", "chinese_traditional"), ("heterophony", "chinese_traditional"),
    ("chinese", "chinese_traditional"),
    # --- Japan ---
    ("雅楽", "gagaku"), ("gagaku", "gagaku"),
    ("city pop", "city_pop"), ("aor", "city_pop"),
    # --- Middle East ---
    ("egyptian", "arabic_tarab"), ("takht", "arabic_tarab"), ("tarab", "arabic_tarab"),
    ("arabic", "arabic_tarab"), ("cabaret", "arabic_tarab"),
    ("persian", "persian"), ("avaz", "persian"),
    # --- Oceania ---
    ("polynesi", "polynesian"), ("oceanic", "polynesian"),
]

def match_genre(style):
    s = style.lower()
    for kw, gid in RULES:
        if kw in s:
            return gid
    return None

MIN_DURATION = 120   # ショート動画(クイズ等)を尺で除外する閾値(秒)。本編は概ね2分以上。

# スナップショット(取得日時点)に未収録の動画を手動で追加する(公開前/公開直後など)。
MANUAL_VIDEOS = {
    "soul": [
        {"videoId": "4TgmM9R9zUU", "song": "未来予想図II", "artist": "DREAMS COME TRUE",
         "style": "Deep Soul", "url": "https://youtu.be/4TgmM9R9zUU",
         "publishedAt": "2026-06-19T10:00:00Z"},   # 6/19 19:00 JST
    ],
}

def load_durations():
    f = ROOT/"data_runtime"/"funnyj_durations.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

def build():
    valid_ids = {r["genre_id"] for r in csv.DictReader(open(ROOT/"data_master"/"genres.csv", encoding="utf-8"))}
    data = json.load(open(SRC, encoding="utf-8"))
    durations = load_durations()

    by_genre = defaultdict(list)
    unmapped, dropped_short = [], []
    for v in data["videos"]:
        t = v["title"]
        if is_quiz(t) or is_medley(t):
            continue
        dur = durations.get(v["video_id"])
        if dur is not None and dur <= MIN_DURATION:
            dropped_short.append((dur, t)); continue
        p = parse(t)
        if not p:
            continue
        gid = match_genre(p["style"])
        if not gid:
            unmapped.append(p["style"]); continue
        assert gid in valid_ids, f"bad genre_id {gid} for style {p['style']}"
        by_genre[gid].append({
            "videoId": v["video_id"], "song": p["song"], "artist": p["artist"],
            "style": p["style"], "url": v["url"], "publishedAt": v["published_at"],
        })

    for gid, vids in MANUAL_VIDEOS.items():        # スナップショット外の手動追加
        assert gid in valid_ids, f"bad genre_id {gid} in MANUAL_VIDEOS"
        have = {v["videoId"] for v in by_genre[gid]}
        for v in vids:
            if v["videoId"] not in have:
                by_genre[gid].append(v)

    for gid in by_genre:                          # newest first within each genre
        by_genre[gid].sort(key=lambda x: x["publishedAt"], reverse=True)
    return by_genre, unmapped, dropped_short

def main():
    by_genre, unmapped, dropped_short = build()
    out = ROOT/"data"/"funnyj.json"
    out.write_text(json.dumps(by_genre, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(v) for v in by_genre.values())
    print(f"mapped {total} videos into {len(by_genre)} genres  -> {out}")
    print(f"dropped as shorts (<= {MIN_DURATION}s, non-quiz): {len(dropped_short)}")
    for d, t in sorted(dropped_short):
        print(f"   {d:4d}s  {t}")
    print(f"unmapped: {len(unmapped)}")
    for s in sorted(set(unmapped)):
        print("   ??", s)
    print("\n=== videos per genre ===")
    for gid, vids in sorted(by_genre.items(), key=lambda x: -len(x[1])):
        print(f"{len(vids):2d}  {gid}")

if __name__ == "__main__":
    main()
