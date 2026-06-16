#!/usr/bin/env python3
"""data_master/*.csv を読み込み、フロント表示用の静的JSONを data/ に書き出す。

出力:
  data/places.json      … 都市マスタ（flag は country_code から生成）
  data/genres.json      … ジャンルマスタ（説明・代表アーティスト・メタデータ・関連都市・キーワード）
  data/map_points.json  … 地図マーカー用の軽量データ（都市 + そこに紐づく genreIds）

YouTube API は不要。ランキング（data/rankings/{id}.json）は別バッチで生成する。
"""
import csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "data_master")
OUT = os.path.join(ROOT, "data")

REL_ORDER = {"origin": 0, "important": 1, "current": 2}


def read(name):
    with open(os.path.join(MASTER, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def flag(cc):
    """ISO 3166-1 alpha-2 → 国旗絵文字（地域指示記号）"""
    cc = (cc or "").strip().upper()
    if len(cc) != 2 or not cc.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in cc)


def split_list(s):
    return [x.strip() for x in (s or "").split("/") if x.strip()]


def main():
    places = read("places.csv")
    genres = read("genres.csv")
    gpm = read("genre_place_map.csv")
    kws = read("genre_keywords.csv")

    active_places = [p for p in places if p.get("is_active", "1") == "1"]
    active_genres = [g for g in genres if g.get("is_active", "1") == "1"]
    place_ids = {p["place_id"] for p in active_places}
    genre_ids = {g["genre_id"] for g in active_genres}

    # genre -> [{placeId, relationType, weight}]  (origin→important→current 順)
    g_places = {}
    for r in gpm:
        if r["genre_id"] in genre_ids and r["place_id"] in place_ids:
            g_places.setdefault(r["genre_id"], []).append(
                {"placeId": r["place_id"], "relationType": r["relation_type"],
                 "weight": float(r["weight"]) if r.get("weight") else None})
    for v in g_places.values():
        v.sort(key=lambda x: REL_ORDER.get(x["relationType"], 9))

    # genre -> [keyword,...]  (is_active かつ priority 昇順)
    g_kw = {}
    for r in kws:
        if r["genre_id"] in genre_ids and r.get("is_active", "1") == "1":
            g_kw.setdefault(r["genre_id"], []).append(
                (int(r.get("priority") or 99), r["keyword"]))
    for k in g_kw:
        g_kw[k] = [kw for _, kw in sorted(g_kw[k])]

    # place -> [genreId,...]  (origin を優先して並べる)
    p_genres = {}
    for gid, plist in g_places.items():
        for pl in plist:
            p_genres.setdefault(pl["placeId"], []).append(
                (REL_ORDER.get(pl["relationType"], 9), gid))
    for k in p_genres:
        p_genres[k] = [gid for _, gid in sorted(p_genres[k])]

    # ---- places.json ----
    places_out = [{
        "placeId": p["place_id"],
        "countryCode": p["country_code"],
        "countryNameEn": p["country_name_en"],
        "countryNameJa": p["country_name_ja"],
        "cityNameEn": p["city_name_en"],
        "cityNameJa": p["city_name_ja"],
        "flag": flag(p["country_code"]),
        "lat": float(p["lat"]),
        "lon": float(p["lon"]),
        "descriptionJa": p.get("description_ja", ""),
    } for p in active_places]

    # ---- genres.json ----
    def order(g):
        try:
            return int(g.get("display_order") or 0)
        except ValueError:
            return 0

    genres_out = [{
        "genreId": g["genre_id"],
        "nameEn": g["name_en"],
        "nameJa": g["name_ja"],
        "parentGenreId": g.get("parent_genre_id") or None,
        "descriptionJa": g.get("description_ja", ""),
        "descriptionEn": g.get("description_en", ""),
        "energy": int(g["energy"]) if (g.get("energy") or "").isdigit() else None,
        "mood": g.get("mood", ""),
        "keyInstruments": split_list(g.get("key_instruments")),
        "referenceArtists": split_list(g.get("reference_artists")),
        "keywords": g_kw.get(g["genre_id"], []),
        "places": g_places.get(g["genre_id"], []),
    } for g in sorted(active_genres, key=order)]

    # ---- map_points.json ----
    map_points = [{
        "placeId": p["place_id"],
        "label": p["city_name_en"],
        "labelJa": p["city_name_ja"],
        "flag": flag(p["country_code"]),
        "lat": float(p["lat"]),
        "lon": float(p["lon"]),
        "genreIds": p_genres.get(p["place_id"], []),
    } for p in active_places if p_genres.get(p["place_id"])]

    os.makedirs(OUT, exist_ok=True)
    for name, data in [("places.json", places_out),
                       ("genres.json", genres_out),
                       ("map_points.json", map_points)]:
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print(f"wrote data/{name}: {len(data)} records")


if __name__ == "__main__":
    main()
