#!/usr/bin/env python3
"""Build a local, browsable archive from a Spotify account data export.

Reads:  YourLibrary.json, StreamingHistory_music_*.json, Playlist1.json
Writes: data/*.csv, data/*.json, index.html (single-file visual archive)
"""
import json, csv, re, unicodedata
from pathlib import Path
from collections import defaultdict
from html import escape

SRC = Path("/Users/emotebot/.hermes/cache/documents/spotify_export/Spotify Account Data")
OUT = Path("/Users/emotebot/Projects/spotify-archive")
DATA = OUT / "data"
DATA.mkdir(parents=True, exist_ok=True)

# ---------- load ----------
lib = json.load(open(SRC / "YourLibrary.json"))
tracks = lib["tracks"]          # liked songs: artist, album, track, uri
albums = lib["albums"]          # saved albums: artist, album, uri
artists = lib["artists"]        # saved artists: name, uri
playlists = json.load(open(SRC / "Playlist1.json"))["playlists"]

history = []
for f in sorted(SRC.glob("StreamingHistory_music_*.json")):
    history.extend(json.load(open(f)))

# ---------- helpers ----------
def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return re.sub(r"\s+", " ", s).strip().lower()

# streaming stats (last ~12 months of history)
artist_plays = defaultdict(int)
artist_ms = defaultdict(int)
album_plays = defaultdict(int)   # key: (artist, track->album unknown in history) -> use track only
track_plays = defaultdict(int)
for h in history:
    a = h.get("artistName") or ""
    artist_plays[norm(a)] += 1
    artist_ms[norm(a)] += h.get("msPlayed", 0)
    track_plays[(norm(a), norm(h.get("trackName") or ""))] += 1

# liked-track counts per artist / per (artist, album)
liked_per_artist = defaultdict(int)
liked_per_album = defaultdict(int)
album_first_seen_uri = {}
for t in tracks:
    liked_per_artist[norm(t["artist"])] += 1
    liked_per_album[(norm(t["artist"]), norm(t["album"]))] += 1

# ---------- assemble: artists ----------
# union of saved artists + artists appearing in liked tracks/albums
artist_rows = {}
for a in artists:
    k = norm(a["name"])
    artist_rows[k] = {"name": a["name"], "uri": a["uri"], "saved": True,
                      "liked_tracks": 0, "albums_in_library": set(),
                      "plays": 0, "hours": 0.0}
for t in tracks:
    k = norm(t["artist"])
    r = artist_rows.setdefault(k, {"name": t["artist"], "uri": "", "saved": False,
                                   "liked_tracks": 0, "albums_in_library": set(),
                                   "plays": 0, "hours": 0.0})
    r["liked_tracks"] += 1
    r["albums_in_library"].add(t["album"])
for al in albums:
    k = norm(al["artist"])
    r = artist_rows.setdefault(k, {"name": al["artist"], "uri": "", "saved": False,
                                   "liked_tracks": 0, "albums_in_library": set(),
                                   "plays": 0, "hours": 0.0})
    r["albums_in_library"].add(al["album"])
for k, r in artist_rows.items():
    r["plays"] = artist_plays.get(k, 0)
    r["hours"] = round(artist_ms.get(k, 0) / 3_600_000, 1)
    r["albums_in_library"] = sorted(r["albums_in_library"])

# ---------- assemble: albums ----------
album_rows = {}
for al in albums:
    k = (norm(al["artist"]), norm(al["album"]))
    album_rows[k] = {"artist": al["artist"], "album": al["album"], "uri": al["uri"],
                     "saved": True, "liked_tracks": 0}
for t in tracks:
    k = (norm(t["artist"]), norm(t["album"]))
    r = album_rows.setdefault(k, {"artist": t["artist"], "album": t["album"], "uri": "",
                                  "saved": False, "liked_tracks": 0})
    r["liked_tracks"] += 1

# ---------- write CSVs ----------
with open(DATA / "artists.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["artist", "saved_artist", "albums_in_library", "liked_tracks",
                "plays_last_year", "hours_last_year", "spotify_uri"])
    for r in sorted(artist_rows.values(), key=lambda x: (-x["liked_tracks"], x["name"].lower())):
        w.writerow([r["name"], "yes" if r["saved"] else "", len(r["albums_in_library"]),
                    r["liked_tracks"], r["plays"], r["hours"], r["uri"]])

with open(DATA / "albums.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["artist", "album", "saved_album", "liked_tracks", "spotify_uri"])
    for r in sorted(album_rows.values(), key=lambda x: (x["artist"].lower(), x["album"].lower())):
        w.writerow([r["artist"], r["album"], "yes" if r["saved"] else "",
                    r["liked_tracks"], r["uri"]])

with open(DATA / "liked_tracks.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["artist", "album", "track", "spotify_uri"])
    for t in sorted(tracks, key=lambda x: (x["artist"].lower(), x["album"].lower(), x["track"].lower())):
        w.writerow([t["artist"], t["album"], t["track"], t["uri"]])

json.dump({"artists": [{**r, "albums_in_library": r["albums_in_library"]} for r in artist_rows.values()],
           "albums": list(album_rows.values())},
          open(DATA / "library.json", "w"), ensure_ascii=False, indent=1)

# ---------- stats ----------
n_artists = len(artist_rows)
n_albums = len(album_rows)
n_saved_albums = sum(1 for r in album_rows.values() if r["saved"])
n_saved_artists = sum(1 for r in artist_rows.values() if r["saved"])
total_hours = round(sum(h.get("msPlayed", 0) for h in history) / 3_600_000, 1)
top_played = sorted(artist_rows.values(), key=lambda x: -x["plays"])[:10]
top_liked = sorted(artist_rows.values(), key=lambda x: -x["liked_tracks"])[:10]
pl_summary = [(p["name"], len(p.get("items", [])), p.get("lastModifiedDate", "")) for p in playlists]

# ---------- HTML ----------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Spotify Archive — Hriday Nagu</title>
<style>
:root { color-scheme: dark; --bg:#0e0e10; --ink:#ececec; --dim:#8a8a90; --line:#232327; --acc:#1db954; }
* { box-sizing: border-box; margin: 0; }
body { background: var(--bg); color: var(--ink); font: 15px/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif; }
header { padding: 56px 40px 28px; border-bottom: 1px solid var(--line); }
h1 { font-size: 42px; letter-spacing: -0.03em; font-weight: 700; }
.sub { color: var(--dim); margin-top: 6px; }
.stats { display: flex; flex-wrap: wrap; gap: 32px; padding: 24px 40px; border-bottom: 1px solid var(--line); }
.stat b { display: block; font-size: 28px; letter-spacing: -0.02em; }
.stat span { color: var(--dim); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }
nav { position: sticky; top: 0; z-index: 5; background: rgba(14,14,16,.92); backdrop-filter: blur(8px);
      display: flex; gap: 8px; align-items: center; padding: 12px 40px; border-bottom: 1px solid var(--line); flex-wrap: wrap; }
nav button { background: none; border: 1px solid var(--line); color: var(--dim); border-radius: 999px;
             padding: 7px 16px; font-size: 13px; cursor: pointer; }
nav button.on { background: var(--ink); color: #111; border-color: var(--ink); }
nav input { flex: 1; min-width: 180px; background: #17171a; border: 1px solid var(--line); border-radius: 999px;
            padding: 8px 18px; color: var(--ink); font-size: 14px; outline: none; }
nav select { background: #17171a; border: 1px solid var(--line); border-radius: 999px; color: var(--dim); padding: 8px 12px; }
main { padding: 8px 40px 80px; }
.row { display: grid; grid-template-columns: 44px 1fr auto; gap: 8px; align-items: baseline;
       padding: 10px 0; border-bottom: 1px solid var(--line); }
.row .i { color: var(--dim); font-size: 12px; font-variant-numeric: tabular-nums; }
.row .meta { color: var(--dim); font-size: 12.5px; white-space: nowrap; }
.row a { color: inherit; text-decoration: none; }
.row a:hover { color: var(--acc); }
.badge { display: inline-block; font-size: 10px; letter-spacing: .06em; text-transform: uppercase;
         border: 1px solid var(--acc); color: var(--acc); border-radius: 999px; padding: 1px 8px; margin-left: 8px; vertical-align: 2px; }
.badge.grey { border-color: var(--dim); color: var(--dim); }
.panels h2 { font-size: 22px; margin: 36px 0 4px; letter-spacing: -0.02em; }
.panels .note { color: var(--dim); font-size: 13px; margin-bottom: 12px; }
table { border-collapse: collapse; width: 100%; margin-top: 8px; }
td, th { text-align: left; padding: 7px 12px 7px 0; border-bottom: 1px solid var(--line); font-size: 13.5px; }
th { color: var(--dim); font-weight: 400; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
footer { padding: 24px 40px 48px; color: var(--dim); font-size: 12px; border-top: 1px solid var(--line); }
.hidden { display: none; }
</style>
</head>
<body>
<header>
  <h1>Spotify Archive</h1>
  <div class="sub">Hriday Nagu · local library archive · generated <span id="gen"></span></div>
</header>
<section class="stats" id="stats"></section>
<nav>
  <button data-v="artists" class="on">Artists</button>
  <button data-v="albums">Albums</button>
  <button data-v="insights">Insights</button>
  <input id="q" placeholder="Search…" autocomplete="off">
  <select id="sort"></select>
  <label style="color:var(--dim);font-size:12.5px"><input type="checkbox" id="savedOnly"> saved only</label>
</nav>
<main>
  <div id="list"></div>
  <div id="insights" class="panels hidden"></div>
</main>
<footer>Source: Spotify account data export · data/*.csv + data/library.json · everything local, no API calls.</footer>
<script>
const P = __PAYLOAD__, S = __STATS__;
document.getElementById('gen').textContent = new Date().toLocaleDateString('en-GB', {day:'numeric', month:'long', year:'numeric'});
const statsEl = document.getElementById('stats');
statsEl.innerHTML = [
  [S.artists, 'artists'], [S.albums, 'albums'], [S.liked, 'liked tracks'],
  [S.saved_artists, 'saved artists'], [S.saved_albums, 'saved albums'],
  [S.hours.toLocaleString() + ' h', 'listened last year']
].map(([b, s]) => `<div class="stat"><b>${b}</b><span>${s}</span></div>`).join('');

const sorts = {
  artists: [['alpha','A–Z'], ['liked','Most liked tracks'], ['albums','Most albums'], ['plays','Most played'], ['hours','Most hours']],
  albums:  [['alpha','Artist A–Z'], ['album','Album A–Z'], ['liked','Most liked tracks']]
};
let view = 'artists';
const q = document.getElementById('q'), sortSel = document.getElementById('sort'),
      savedOnly = document.getElementById('savedOnly'), listEl = document.getElementById('list'),
      insEl = document.getElementById('insights');

function fillSorts() {
  sortSel.innerHTML = sorts[view === 'albums' ? 'albums' : 'artists'].map(([v, l]) => `<option value="${v}">${l}</option>`).join('');
}
function spotUrl(uri) { return uri ? 'https://open.spotify.com/' + uri.replace('spotify:', '').replace(':', '/') : '#'; }
function esc(s) { return s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

function render() {
  const term = q.value.trim().toLowerCase(), so = savedOnly.checked, sv = sortSel.value;
  if (view === 'insights') { listEl.classList.add('hidden'); insEl.classList.remove('hidden'); renderInsights(); return; }
  insEl.classList.add('hidden'); listEl.classList.remove('hidden');
  let rows;
  if (view === 'artists') {
    rows = P.artists.filter(r => (!so || r.s) && (!term || r.n.toLowerCase().includes(term)));
    const k = {alpha:(a,b)=>a.n.localeCompare(b.n), liked:(a,b)=>b.lt-a.lt, albums:(a,b)=>b.al-a.al, plays:(a,b)=>b.pl-a.pl, hours:(a,b)=>b.h-a.h}[sv||'alpha'];
    rows.sort(k);
    listEl.innerHTML = rows.map((r, i) => `
      <div class="row"><span class="i">${i+1}</span>
      <span><a href="${spotUrl(r.uri)}">${esc(r.n)}</a>${r.s ? '<span class="badge">saved</span>' : ''}</span>
      <span class="meta">${r.al} album${r.al===1?'':'s'} · ${r.lt} liked · ${r.pl} plays · ${r.h} h</span></div>`).join('');
  } else {
    rows = P.albums.filter(r => (!so || r.s) && (!term || r.t.toLowerCase().includes(term) || r.a.toLowerCase().includes(term)));
    const k = {alpha:(a,b)=>a.a.localeCompare(b.a)||a.t.localeCompare(b.t), album:(a,b)=>a.t.localeCompare(b.t), liked:(a,b)=>b.lt-a.lt}[sv||'alpha'];
    rows.sort(k);
    listEl.innerHTML = rows.map((r, i) => `
      <div class="row"><span class="i">${i+1}</span>
      <span><a href="${spotUrl(r.uri)}">${esc(r.t)}</a> <span style="color:var(--dim)">— ${esc(r.a)}</span>${r.s ? '<span class="badge">saved</span>' : ''}</span>
      <span class="meta">${r.lt} liked track${r.lt===1?'':'s'}</span></div>`).join('');
  }
}
function renderInsights() {
  insEl.innerHTML = `
    <h2>Most played — last 12 months</h2><div class="note">${esc(S.history_start)} → ${esc(S.history_end)}</div>
    <table><tr><th>#</th><th>Artist</th><th>Plays</th><th>Hours</th></tr>
    ${S.top_played.map((t,i)=>`<tr><td>${i+1}</td><td>${esc(t[0])}</td><td>${t[1]}</td><td>${t[2]}</td></tr>`).join('')}</table>
    <h2>Most liked</h2><div class="note">artists with the most tracks in your liked songs</div>
    <table><tr><th>#</th><th>Artist</th><th>Liked tracks</th></tr>
    ${S.top_liked.map((t,i)=>`<tr><td>${i+1}</td><td>${esc(t[0])}</td><td>${t[1]}</td></tr>`).join('')}</table>
    <h2>Playlists</h2><div class="note">from the export</div>
    <table><tr><th>Playlist</th><th>Tracks</th><th>Last modified</th></tr>
    ${S.playlists.map(p=>`<tr><td>${esc(p[0])}</td><td>${p[1]}</td><td>${esc(p[2])}</td></tr>`).join('')}</table>`;
}
document.querySelectorAll('nav button').forEach(b => b.onclick = () => {
  document.querySelectorAll('nav button').forEach(x => x.classList.remove('on'));
  b.classList.add('on'); view = b.dataset.v; fillSorts(); render();
});
q.oninput = render; sortSel.onchange = render; savedOnly.onchange = render;
fillSorts(); render();
</script>
</body>
</html>
"""

payload = {
    "artists": [{"n": r["name"], "s": r["saved"], "al": len(r["albums_in_library"]),
                 "lt": r["liked_tracks"], "pl": r["plays"], "h": r["hours"],
                 "uri": r["uri"]} for r in artist_rows.values()],
    "albums": [{"a": r["artist"], "t": r["album"], "s": r["saved"],
                "lt": r["liked_tracks"], "uri": r["uri"]} for r in album_rows.values()],
}
stats = {
    "artists": n_artists, "saved_artists": n_saved_artists,
    "albums": n_albums, "saved_albums": n_saved_albums,
    "liked": len(tracks), "hours": total_hours,
    "history_start": history[0]["endTime"] if history else "",
    "history_end": history[-1]["endTime"] if history else "",
    "playlists": pl_summary,
    "top_played": [(r["name"], r["plays"], r["hours"]) for r in top_played],
    "top_liked": [(r["name"], r["liked_tracks"]) for r in top_liked],
}

html = HTML_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False)) \
                    .replace("__STATS__", json.dumps(stats, ensure_ascii=False))
(OUT / "index.html").write_text(html, encoding="utf-8")
print(f"artists={n_artists} albums={n_albums} liked={len(tracks)} playlists={len(playlists)} hours={total_hours}")
print("wrote", OUT)
