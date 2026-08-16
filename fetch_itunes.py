#!/usr/bin/env python3
"""Fetch album artwork + 30s preview URLs from the iTunes Search API.

One call per album (entity=song, limit=1, term="artist album") — the top hit
carries artworkUrl100 + previewUrl + trackViewUrl. Paced 1.5s, resumable cache.
Only successful API responses are cached; errors stay absent so retries pick up.
"""
import json, time, urllib.parse, urllib.request, sys
from pathlib import Path

OUT = Path("/Users/emotebot/Projects/spotify-archive")
DATA = OUT / "data"
CACHE = DATA / "itunes_cache.json"

lib = json.load(open(DATA / "library.json"))
cache = json.load(open(CACHE)) if CACHE.exists() else {}

# priority: saved albums first, then most liked tracks
albums = sorted(lib["albums"], key=lambda r: (not r["saved"], -r["liked_tracks"]))

def fetch(artist, album):
    term = urllib.parse.quote(f"{artist} {album}")
    url = f"https://itunes.apple.com/search?term={term}&entity=song&limit=1&country=US"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)
    if d.get("results"):
        t = d["results"][0]
        return {
            "art": t.get("artworkUrl100", "").replace("100x100bb", "600x600bb"),
            "prev": t.get("previewUrl", ""),
            "track": t.get("trackName", ""),
            "url": t.get("collectionViewUrl", t.get("trackViewUrl", "")),
            "match_artist": t.get("artistName", ""),
            "match_album": t.get("collectionName", ""),
        }
    return None

todo = [a for a in albums if f'{a["artist"]}|||{a["album"]}' not in cache]
print(f"total={len(albums)} cached={len(cache)} todo={len(todo)}", flush=True)

done = fails = 0
for i, a in enumerate(todo):
    key = f'{a["artist"]}|||{a["album"]}'
    try:
        res = fetch(a["artist"], a["album"])
        cache[key] = res  # None = API responded with no match (won't retry)
        done += 1
    except Exception as e:
        fails += 1
        print(f"[{i+1}/{len(todo)}] ERROR {a['artist']} - {a['album']}: {e}", flush=True)
        if fails > 25:
            print("too many errors, backing off 120s", flush=True)
            time.sleep(120); fails = 0
        continue
    if done % 20 == 0:
        json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
        print(f"[{i+1}/{len(todo)}] fetched={done}", flush=True)
    time.sleep(1.5)

json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
print(f"DONE fetched={done} cache_total={len(cache)}", flush=True)
