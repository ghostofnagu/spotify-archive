#!/usr/bin/env python3
"""Fetch artist genres from iTunes (entity=musicArtist, limit=1).
Paced 1.5s, resumable cache at data/artist_info.json."""
import json, time, urllib.parse, urllib.request
from pathlib import Path

DATA = Path("/Users/emotebot/Projects/spotify-archive/data")
lib = json.load(open(DATA / "library.json"))
CACHE = DATA / "artist_info.json"
cache = json.load(open(CACHE)) if CACHE.exists() else {}

artists = sorted(lib["artists"], key=lambda a: -a["liked_tracks"])
todo = [a for a in artists if a["name"] not in cache]
print(f"artists={len(artists)} cached={len(cache)} todo={len(todo)}", flush=True)

done = fails = 0
for i, a in enumerate(todo):
    try:
        term = urllib.parse.quote(a["name"])
        url = f"https://itunes.apple.com/search?term={term}&entity=musicArtist&limit=1&country=US"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.load(r)
        hit = d.get("results") or []
        cache[a["name"]] = {"genre": hit[0].get("primaryGenreName", "")} if hit else {"genre": ""}
        done += 1
    except Exception as e:
        fails += 1
        print(f"[{i+1}/{len(todo)}] ERROR {a['name']}: {e}", flush=True)
        if fails > 25:
            time.sleep(120); fails = 0
        continue
    if done % 20 == 0:
        json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
        print(f"[{i+1}/{len(todo)}] genres={done}", flush=True)
    time.sleep(1.5)

json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
print(f"DONE genres={done} total={len(cache)}", flush=True)
