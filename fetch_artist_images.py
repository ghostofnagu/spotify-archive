#!/usr/bin/env python3
"""Fetch artist press photos from the Deezer API (no key required).
search/artist -> picture_xl (1000x1000). Cache: data/artist_images.json.
Light pacing; Deezer allows ~50 req / 5s. Resumable."""
import json, time, urllib.parse, urllib.request
from pathlib import Path

DATA = Path("/Users/emotebot/Projects/spotify-archive/data")
lib = json.load(open(DATA / "library.json"))
CACHE = DATA / "artist_images.json"
cache = json.load(open(CACHE)) if CACHE.exists() else {}

artists = sorted(lib["artists"], key=lambda a: -a["liked_tracks"])
todo = [a for a in artists if a["name"] not in cache]
print(f"artists={len(artists)} cached={len(cache)} todo={len(todo)}", flush=True)

done = fails = 0
for i, a in enumerate(todo):
    try:
        q = urllib.parse.quote(a["name"])
        url = f"https://api.deezer.com/search/artist?q={q}&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
        hits = d.get("data") or []
        # exact-ish name match guard
        pic = ""
        if hits and hits[0].get("name", "").strip().lower() == a["name"].strip().lower():
            pic = hits[0].get("picture_xl") or hits[0].get("picture_big") or ""
        cache[a["name"]] = {"img": pic}
        done += 1
    except Exception as e:
        fails += 1
        print(f"[{i+1}/{len(todo)}] ERROR {a['name']}: {e}", flush=True)
        if fails > 25:
            time.sleep(60); fails = 0
        continue
    if done % 40 == 0:
        json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
        print(f"[{i+1}/{len(todo)}] images={done}", flush=True)
    time.sleep(0.4)

json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
have = sum(1 for v in cache.values() if v.get("img"))
print(f"DONE images={done} total={len(cache)} with_photo={have}", flush=True)
