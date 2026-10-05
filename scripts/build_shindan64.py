# -*- coding: utf-8 -*-
"""Tune rarity for Soul Rhythm Check 64 and write data/shindan64.json.

Enumerates all 4^12 answer paths exactly (as a distribution over summed axis
vectors), tunes tribe / type biases so appearance rates match the familiarity
tiers in shindan64_spec.py, then exports questions + scoring params + rates.

Run:  .\\.venv\\Scripts\\python.exe scripts\\build_shindan64.py            (full re-tune, ~3 min)
      .\\.venv\\Scripts\\python.exe scripts\\build_shindan64.py --content  (copy/text edits only)
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shindan64_content as content  # noqa: E402
import shindan64_spec as spec  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "shindan64.json")
FUNNYJ = os.path.join(ROOT, "data", "funnyj.json")

NDIM = 9            # F W C M H B S E + yodel-trigger count
BITS, OFF = 6, 32   # per-dim key packing (values must stay within -32..31)


# ---------------------------------------------------------------- validation
def validate():
    funnyj = json.load(open(FUNNYJ, encoding="utf-8"))
    ids = [t[0] for t in spec.TYPES]
    assert len(ids) == 64 and len(set(ids)) == 64, "need 64 unique types"
    missing = [g for g in ids + [spec.SECRET["genreId"]] if g not in funnyj]
    assert not missing, f"no arrangement videos for: {missing}"
    lin_tribe = {l["id"]: l["tribe"] for l in spec.LINEAGES}
    for tr in spec.TRIBES:
        lins = [l for l in spec.LINEAGES if l["tribe"] == tr["id"]]
        assert len(lins) == 4, tr["id"]
        for l in lins:
            n = sum(1 for t in spec.TYPES if t[1] == l["id"])
            assert n == 4, f"lineage {l['id']} has {n} types"
    assert all(t[1] in lin_tribe for t in spec.TYPES)
    for q in spec.QUESTIONS:
        assert len(q["opts"]) == 4
    assert abs(sum(t["target"] for t in spec.TRIBES) - 1) < 1e-9
    need = set(ids) | {spec.SECRET["genreId"]}
    assert need == set(content.CONTENT), f"content mismatch: {need ^ set(content.CONTENT)}"


# ------------------------------------------------------------ distribution
def encode(a):
    key = np.zeros(len(a), dtype=np.int64)
    for i in range(NDIM):
        key = (key << BITS) | (a[:, i] + OFF)
    return key


def decode(key):
    out = np.zeros((len(key), NDIM), dtype=np.int64)
    for i in reversed(range(NDIM)):
        out[:, i] = (key & ((1 << BITS) - 1)) - OFF
        key = key >> BITS
    return out


def distribution():
    states = np.zeros((1, NDIM), dtype=np.int64)
    counts = np.ones(1, dtype=np.int64)
    for q in spec.QUESTIONS:
        deltas = np.array([o["d"] + [1 if o["y"] else 0] for o in q["opts"]], dtype=np.int64)
        new = (states[:, None, :] + deltas[None, :, :]).reshape(-1, NDIM)
        assert new.min() >= -OFF and new.max() < OFF
        uk, inv = np.unique(encode(new), return_inverse=True)
        counts = np.bincount(inv.ravel(), weights=np.repeat(counts, 4)).astype(np.int64)
        states = decode(uk)
    return states, counts


# ------------------------------------------------------------------ tuning
def tribe_of(body, tbias):
    return np.argmax(body + tbias[None, :], axis=1)


def tune_tribes(body, w):
    target = np.array([t["target"] for t in spec.TRIBES])
    bias = np.zeros(4)
    best = (1e9, bias.copy())
    for it in range(600):
        mass = np.bincount(tribe_of(body, bias), weights=w, minlength=4) / w.sum()
        err = np.max(np.abs(mass / target - 1))
        if err < best[0]:
            best = (err, bias.copy())
        lr = 0.6 * (1 - it / 600) + 0.01
        bias += lr * np.log(target / np.maximum(mass, 1e-9))
        bias -= bias.mean()
    return best[1]


def tune_types(mods, w, targets, tw):
    """Power-diagram bias tuning inside one tribe."""
    d2 = ((mods[:, None, :] - targets[None, :, :]) ** 2).sum(-1)
    goal = tw / tw.sum()
    bias = np.zeros(len(targets))
    best = (1e9, bias.copy())
    for it in range(4000):
        mass = np.bincount(np.argmin(d2 + bias[None, :], axis=1), weights=w, minlength=len(targets)) / w.sum()
        err = np.max(np.abs(mass / goal - 1))
        if err < best[0]:
            best = (err, bias.copy())
        if err < 0.01:
            break
        lr = 4.0 * (1 - it / 4000) + 0.02
        bias += lr * np.log(np.maximum(mass, 1e-6) / goal)
        bias -= bias.mean()
    return best[1]


# ------------------------------------------------------------------ scoring
def classify(states, tbias, targets, ybias_by_tribe, type_tribe):
    """Exact replica of the JS scorer. Returns type index per state (-1 = secret)."""
    n_trig = sum(1 for q in spec.QUESTIONS for o in q["opts"] if o["y"])
    tribe = tribe_of(states[:, :4].astype(float), tbias)
    mods = states[:, 4:8].astype(float)
    out = np.full(len(states), -1)
    for ti in range(4):
        idx = np.where(type_tribe == ti)[0]
        sel = tribe == ti
        d2 = ((mods[sel][:, None, :] - targets[idx][None, :, :]) ** 2).sum(-1)
        out[sel] = idx[np.argmin(d2 + ybias_by_tribe[idx][None, :], axis=1)]
    out[states[:, 8] == n_trig] = -1
    return out


def stars_for(rate):
    for th, s, label in spec.STARS:
        if rate < th:
            return s, label
    return 1, "COMMON"


def path_state(answers):
    v = np.zeros(NDIM, dtype=np.int64)
    for q, a in zip(spec.QUESTIONS, answers):
        o = q["opts"][a]
        v += np.array(o["d"] + [1 if o["y"] else 0])
    return v[None, :]


# ------------------------------------------------------------------- main
def main():
    validate()
    states, counts = distribution()
    total = int(counts.sum())
    n_trig = sum(1 for q in spec.QUESTIONS for o in q["opts"] if o["y"])
    assert total == 4 ** len(spec.QUESTIONS)
    print(f"answer paths: {total:,}  distinct score vectors: {len(states):,}")

    normal = states[:, 8] < n_trig
    tbias = np.round(tune_tribes(states[normal, :4].astype(float), counts[normal].astype(float)), 2)

    tribe_ids = [t["id"] for t in spec.TRIBES]
    lin_tribe = {l["id"]: l["tribe"] for l in spec.LINEAGES}
    type_tribe = np.array([tribe_ids.index(lin_tribe[t[1]]) for t in spec.TYPES])
    semantic = np.array([t[2:6] for t in spec.TYPES], dtype=float)
    targets = np.zeros((64, 4))
    tw = np.array([spec.TIER_WEIGHT[t[6]] for t in spec.TYPES])

    tribe = tribe_of(states[:, :4].astype(float), tbias)
    ybias = np.zeros(64)
    for ti in range(4):
        sel = normal & (tribe == ti)
        uk, inv = np.unique(encode(states[sel]) & ((1 << (BITS * 5)) - 1), return_inverse=True)  # H B S E Y
        w = np.bincount(inv.ravel(), weights=counts[sel].astype(float))
        mods = decode(uk)[:, 4:8].astype(float)
        idx = np.where(type_tribe == ti)[0]
        # Targets live around this tribe's own answer centroid, so a type's cell
        # stays near the people it describes instead of being stretched by bias.
        mean = (mods * w[:, None]).sum(0) / w.sum()
        std = np.sqrt((((mods - mean) ** 2) * w[:, None]).sum(0) / w.sum())
        spread = np.array([spec.TIER_SPREAD[spec.TYPES[i][6]] for i in idx])[:, None]
        targets[idx] = np.round(mean + semantic[idx] * std * spec.TARGET_SPREAD * spread, 2)
        ybias[idx] = np.round(tune_types(mods, w, targets[idx], tw[idx]), 2)

    result = classify(states, tbias, targets, ybias, type_tribe)
    tcount = np.bincount(result[result >= 0], weights=counts[result >= 0], minlength=64).astype(np.int64)
    secret_count = int(counts[result < 0].sum())
    assert tcount.sum() + secret_count == total
    assert (tcount > 0).all(), "unreachable type!"

    # --------------------------------------------------------------- report
    funnyj = json.load(open(FUNNYJ, encoding="utf-8"))
    genres = {g["genreId"]: g for g in json.load(open(os.path.join(ROOT, "data", "genres.json"), encoding="utf-8"))}
    print(f"tribe bias: {dict(zip(tribe_ids, tbias.tolist()))}  mean |type bias|: {np.abs(ybias).mean():.2f}  max: {np.abs(ybias).max():.2f}")
    for ti, tr in enumerate(spec.TRIBES):
        tr_rate = tcount[type_tribe == ti].sum() / total
        print(f"\n{tr['emoji']} {tr['nameJa']}  {tr_rate:6.2%} (target {tr['target']:.0%} of non-secret)")
        for lin in [l for l in spec.LINEAGES if l["tribe"] == tr["id"]]:
            idx = [i for i, t in enumerate(spec.TYPES) if t[1] == lin["id"]]
            print(f"   {lin['emoji']} {lin['nameJa']}  {tcount[idx].sum() / total:6.2%}")
            for i in idx:
                r = tcount[i] / total
                s, label = stars_for(r)
                print(f"      {genres[spec.TYPES[i][0]]['nameJa']:<16} {r:6.2%}  {'★' * s:<5} {label:<10} tier {spec.TYPES[i][6]}  bias {ybias[i]:+.2f}")
    print(f"\n🔒 secret yodel: {secret_count / total:.4%} ({secret_count:,} paths)")
    rates = tcount / total
    print(f"min {rates.min():.3%}  max {rates.max():.3%}  ratio {rates.max() / rates.min():.0f}x")
    star_hist = {}
    for r in rates:
        s = stars_for(r)[1]
        star_hist[s] = star_hist.get(s, 0) + 1
    print("star histogram:", star_hist)

    # sanity personas
    personas = {
        "all 1st options": [0] * 12,
        "all 2nd options": [1] * 12,
        "all 3rd options": [2] * 12,
        "all 4th options": [3] * 12,
        "city-night loner": [3, 1, 2, 3, 0, 1, 1, 1, 3, 1, 3, 1],
        "sad poet": [3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 2, 2],
        "mystic traveller": [1, 3, 3, 3, 3, 3, 3, 3, 2, 3, 2, 3],
        "jazz nerd": [0, 1, 0, 3, 0, 3, 1, 3, 1, 3, 1, 3],
        "yodel path": [1, 3, 1, 0, 3, 0, 0, 0, 2, 0, 0, 0],
    }
    print("\npersonas:")
    for name, ans in personas.items():
        r = classify(path_state(ans), tbias, targets, ybias, type_tribe)[0]
        print(f"   {name:<18} -> {'yodel (secret)' if r < 0 else genres[spec.TYPES[r][0]]['nameJa']}")

    # ---------------------------------------------------------------- export
    lineage_rate = {l["id"]: 0 for l in spec.LINEAGES}
    for i, t in enumerate(spec.TYPES):
        lineage_rate[t[1]] += int(tcount[i])
    out = {
        "version": 1,
        "totalPatterns": total,
        "axes": spec.AXES,
        "questions": spec.QUESTIONS,
        "tribes": [dict(tr, bias=float(tbias[i]), count=int(tcount[type_tribe == i].sum()))
                   for i, tr in enumerate(spec.TRIBES)],
        "lineages": [dict(l, count=lineage_rate[l["id"]]) for l in spec.LINEAGES],
        "types": [{
            "id": t[0], "lineage": t[1], "tier": t[6],
            "target": [float(x) for x in targets[i]], "bias": float(ybias[i]),
            "count": int(tcount[i]), "stars": stars_for(tcount[i] / total)[0],
            "rank": stars_for(tcount[i] / total)[1],
        } for i, t in enumerate(spec.TYPES)],
        "secret": {"id": spec.SECRET["genreId"], "count": secret_count, "stars": 6, "rank": "SECRET"},
    }
    write(out)


# ------------------------------------------------------------------ copy
GENRES = {g["genreId"]: g for g in json.load(open(os.path.join(ROOT, "data", "genres.json"), encoding="utf-8"))}


def enrich(entry):
    """Attach display copy (shindan64_content) and genre metadata (genres.json)."""
    g = GENRES[entry["id"]]
    entry.pop("trackNote", None)
    entry.update(
        nameJa=g["nameJa"], nameEn=g["nameEn"].upper(),
        mood=[m for m in str(g.get("mood") or "").split("/") if m][:3],
        artists=" / ".join(g.get("referenceArtists") or []),
        **content.CONTENT[entry["id"]],
    )
    return entry


def write(out):
    out["questions"] = spec.QUESTIONS
    out["tribes"] = [dict(tr, bias=o["bias"], count=o["count"]) for tr, o in zip(spec.TRIBES, out["tribes"])]
    out["lineages"] = [dict(l, count=o["count"]) for l, o in zip(spec.LINEAGES, out["lineages"])]
    out["types"] = [enrich(t) for t in out["types"]]
    out["secret"] = enrich(out["secret"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}")


def content_only():
    """Re-merge copy into the existing tuned JSON. Refuses if scoring inputs changed."""
    out = json.load(open(OUT, encoding="utf-8"))

    def scoring(qs):
        return [[(o["d"], o["y"]) for o in q["opts"]] for q in qs]

    if (scoring(out["questions"]) != scoring(json.loads(json.dumps(spec.QUESTIONS)))
            or [t["id"] for t in out["types"]] != [t[0] for t in spec.TYPES]):
        sys.exit("scoring inputs changed since the last tune - run without --content")
    write(out)


if __name__ == "__main__":
    if "--content" in sys.argv:
        content_only()
    else:
        main()
