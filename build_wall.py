#!/usr/bin/env python3
"""Build the visual 'jewel wall' archive — album-art grid + hover previews.
Dark/light themes, dynamic motion, purchase links. Re-runnable any time."""
import json
from pathlib import Path

OUT = Path("/Users/emotebot/Projects/spotify-archive")
DATA = OUT / "data"

lib = json.load(open(DATA / "library.json"))
cache = json.load(open(DATA / "itunes_cache.json")) if (DATA / "itunes_cache.json").exists() else {}
ainfo = json.load(open(DATA / "artist_info.json")) if (DATA / "artist_info.json").exists() else {}
aimgs = json.load(open(DATA / "artist_images.json")) if (DATA / "artist_images.json").exists() else {}

albums = []
for a in lib["albums"]:
    hit = cache.get(f'{a["artist"]}|||{a["album"]}') or {}
    albums.append({
        "a": a["artist"], "t": a["album"], "s": a["saved"], "lt": a["liked_tracks"],
        "art": hit.get("art", ""), "prev": hit.get("prev", ""),
        "pt": hit.get("track", ""), "url": hit.get("url", ""), "suri": a.get("uri", ""),
    })

artists = lib["artists"]

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Shelf — Hriday's Music Archive</title>
<style>
:root, [data-theme="light"] { color-scheme: light;
  --bg:#e9e7e2; --panel:#f4f2ee; --ink:#141412; --dim:#7c7a72; --line:#d4d1c9;
  --acc:#1db954; --chip:#fff; --gloss:rgba(255,255,255,.32); --shadow:rgba(20,20,18,.16); --shadow2:rgba(20,20,18,.30); }
[data-theme="dark"] { color-scheme: dark;
  --bg:#0d0d0f; --panel:#16161a; --ink:#ececec; --dim:#85858c; --line:#232327;
  --acc:#1db954; --chip:#1c1c21; --gloss:rgba(255,255,255,.14); --shadow:rgba(0,0,0,.5); --shadow2:rgba(0,0,0,.7); }
* { box-sizing: border-box; margin: 0; }
html { scroll-behavior: smooth; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body { background: var(--bg); color: var(--ink); transition: background .4s, color .4s;
  font: 14px/1.45 "Helvetica Neue", Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; }
.smallcaps { font-size: 10.5px; letter-spacing: .14em; text-transform: uppercase; color: var(--dim); }

#themeBtn { position:fixed; top:28px; right:32px; z-index:30; background:color-mix(in srgb, var(--panel) 88%, transparent); border:1px solid var(--line);
  color:var(--ink); border-radius:999px; width:46px; height:46px; font-size:18px; cursor:pointer; backdrop-filter:blur(12px);
  transition:transform .3s, background .3s, border-color .3s; }
#themeBtn:hover { transform:rotate(40deg) scale(1.08); border-color:var(--acc); }
#themeBtn:focus-visible { outline:2px solid var(--acc); outline-offset:4px; }
@media (max-width:700px) { #themeBtn { top:18px; right:18px; width:44px; height:44px; } }

/* hero: restored exactly to the original corridor composition */
.hero { position: relative; isolation: isolate; min-height: min(640px, 58vw); margin: 22px 0 8px; overflow: hidden;
  background: var(--panel); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.hero::before { content:""; position:absolute; inset:0; z-index:0; pointer-events:none;
  background: radial-gradient(ellipse 52% 54% at 50% 51%, transparent 0 45%, color-mix(in srgb, var(--bg) 54%, transparent) 100%); }
.hero-copy { position: relative; z-index: 3; width: min(520px, calc(100% - 48px)); margin: 0 auto; padding-top: clamp(54px, 8vw, 102px); text-align: center; pointer-events: none; }
.hero-copy h2 { max-width: 500px; margin: 8px auto 0; color: var(--ink); font-size: clamp(40px, 5.8vw, 78px); line-height: .91; letter-spacing: -.065em; }
.hero-copy p:last-child { max-width: 300px; margin: 18px auto 0; color: var(--dim); font-size: 13px; line-height: 1.38; }
.hero-stage { position:absolute; z-index:1; inset:0; container-type: inline-size; perspective:30cqw; perspective-origin:50% 55%; pointer-events:none; }
.hero-stage > div { position:absolute; inset:0; transform-style:preserve-3d; }
.stream-card { position:absolute; left:50%; top:55%; width:18cqw; height:25cqw; margin-left:-9cqw; margin-top:-12.5cqw; overflow:hidden;
  border-radius:.4cqw; background:var(--line); box-shadow:0 20px 38px var(--shadow2), 0 4px 11px var(--shadow); backface-visibility:hidden; will-change:transform; }
.stream-card::before { content:""; position:absolute; z-index:2; inset:0; pointer-events:none;
  background:linear-gradient(108deg,var(--gloss) 0%,rgba(255,255,255,.05) 22%,transparent 43%),linear-gradient(to right,rgba(0,0,0,.33),transparent 5px); }
.stream-card img { width:100%; height:100%; display:block; object-fit:cover; }
.hero:hover .stream-card { animation-play-state:paused; }
@media (max-width:700px) {
  .hero { min-height: 610px; }
  .hero-copy { padding-top: 48px; width: min(340px, calc(100% - 32px)); }
  .hero-copy h2 { font-size: clamp(42px, 13vw, 62px); }
  .hero-copy p:last-child { margin-top: 15px; }
}
@media (prefers-reduced-motion:reduce) { .stream-card { animation-play-state:paused !important; } }

.collection-meta { padding:20px 40px 8px; border-bottom:1px solid var(--line); background:var(--bg); }
.collection-meta .meta { display:flex; gap:16px 34px; flex-wrap:wrap; }
@media (max-width:700px) { .collection-meta { padding:18px 22px 8px; } .collection-meta .meta { gap:10px 22px; } }

nav { position: sticky; top: 0; z-index: 10; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
  padding: 12px 40px; background: color-mix(in srgb, var(--bg) 90%, transparent); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--line); }
nav button { background: none; border: 1px solid var(--line); color: var(--dim); border-radius: 999px;
  padding: 7px 16px; font-size: 12.5px; cursor: pointer; transition: all .2s; }
nav button.on { background: var(--ink); color: var(--bg); border-color: var(--ink); }
nav input[type=search] { flex: 1; min-width: 160px; background: var(--panel); border: 1px solid var(--line);
  border-radius: 999px; padding: 8px 18px; font-size: 13.5px; color: var(--ink); outline: none; transition: border-color .2s; }
nav input[type=search]:focus { border-color: var(--acc); }
nav select { background: var(--panel); border: 1px solid var(--line); border-radius: 999px; color: var(--dim); padding: 8px 10px; }
nav label { color: var(--dim); font-size: 12px; }

/* walls */
.wall, .shelf { display: grid; grid-template-columns: repeat(auto-fill, minmax(172px, 1fr)); gap: 30px 18px; padding: 30px 40px 90px; }
.card, .acard { position: relative; cursor: pointer; opacity: 0; transform: translateY(16px);
  transition: opacity .5s ease, transform .5s cubic-bezier(.2,.8,.2,1); }
.card.rev, .acard.rev { opacity: 1; transform: translateY(0); }
.case { position: relative; border-radius: 3px; overflow: hidden; background: var(--line);
  box-shadow: 0 8px 20px var(--shadow), 0 2px 5px var(--shadow);
  transition: transform .18s ease-out, box-shadow .3s; aspect-ratio: 1;
  transform-style: preserve-3d; will-change: transform; }
.card:hover .case, .acard:hover .case, .card.playing .case, .acard.playing .case {
  box-shadow: 0 22px 44px var(--shadow2), 0 4px 10px var(--shadow); }
.case::before { content:""; position:absolute; inset:0; z-index:2;
  background: linear-gradient(105deg, var(--gloss) 0%, rgba(255,255,255,.04) 24%, rgba(255,255,255,0) 42%),
              linear-gradient(to right, rgba(0,0,0,.30) 0, rgba(0,0,0,0) 5px); pointer-events:none; }
.case img { display:block; width:100%; height:100%; aspect-ratio:1; object-fit:cover; opacity:0; transition: opacity .5s, transform .6s; }
.card:hover .case img, .acard:hover .case img { transform: scale(1.04); }
.case img.on { opacity: 1; }
.noart { position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
  text-align:center; padding:14px; font-size:12px; color:var(--dim); line-height:1.3; }
.mosaic { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; width: 100%; height: 100%; }
.mosaic.single { grid-template-columns: 1fr; grid-template-rows: 1fr; }
.mosaic .noart { position: static; grid-column: 1 / -1; grid-row: 1 / -1; }

.lbl { margin-top: 10px; }
.lbl b { display:block; font-size: 13px; letter-spacing:-.01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lbl .sub { font-size: 11.5px; color: var(--dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display:block; }
.lbl .g { font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--acc); display: block; margin-top: 1px; }
.badge { position:absolute; top:8px; left:8px; z-index:3; font-size:9px; letter-spacing:.1em; text-transform:uppercase;
  background: rgba(10,10,12,.82); color:#fff; border-radius:999px; padding:3px 9px; backdrop-filter: blur(4px); }

/* playing state */
@keyframes glow { 0%,100% { box-shadow: 0 22px 44px var(--shadow2), 0 0 0 0 rgba(29,185,84,.45); }
  50% { box-shadow: 0 22px 44px var(--shadow2), 0 0 26px 4px rgba(29,185,84,.30); } }
.card.playing .case, .acard.playing .case { animation: glow 2.2s ease-in-out infinite; }
.eq { position:absolute; right:10px; bottom:10px; z-index:3; display:none; gap:3px; align-items:flex-end; height:16px; }
.playing .eq { display:flex; }
.eq i { width:3px; background:#fff; border-radius:1px; animation: eq .8s ease-in-out infinite; box-shadow:0 0 6px rgba(0,0,0,.4); }
.eq i:nth-child(2){ animation-delay:.15s } .eq i:nth-child(3){ animation-delay:.3s } .eq i:nth-child(4){ animation-delay:.45s }
@keyframes eq { 0%,100%{ height:5px } 50%{ height:16px } }
.ring { position:absolute; left:10px; bottom:10px; z-index:3; width:22px; height:22px; display:none; }
.playing .ring { display:block; }
.ring circle { fill:none; stroke-width:2.5; }
.ring .bgr { stroke: rgba(255,255,255,.35); }
.ring .fg { stroke: #fff; stroke-linecap: round; stroke-dasharray: 57; stroke-dashoffset: 57;
  transform: rotate(-90deg); transform-origin: center; filter: drop-shadow(0 0 4px rgba(0,0,0,.4)); }

/* purchase links — revealed on select */
.links { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .35s cubic-bezier(.2,.8,.2,1); }
.sel .links { grid-template-rows: 1fr; }
.links > div { overflow: hidden; }
.links a { display: flex; align-items: center; gap: 8px; margin-top: 6px; padding: 6px 12px;
  background: var(--chip); border: 1px solid var(--line); border-radius: 999px;
  font-size: 11.5px; color: var(--ink); text-decoration: none; transition: border-color .2s, transform .2s; }
.links a:hover { border-color: var(--acc); transform: translateX(3px); }
.links a .tag { margin-left: auto; font-size: 9px; letter-spacing: .08em; text-transform: uppercase; color: var(--dim); }

/* insights */
.panels { padding: 20px 40px 90px; }
.panels h2 { font-size: 24px; letter-spacing:-.02em; margin: 30px 0 6px; }
.panels .note { margin-bottom: 12px; }
table { border-collapse: collapse; width: 100%; }
td, th { text-align:left; padding: 7px 12px 7px 0; border-bottom: 1px solid var(--line); font-size: 13px; }
th { font-size: 10px; letter-spacing:.12em; text-transform:uppercase; color:var(--dim); font-weight:400; }

footer.archive-footer { padding:clamp(48px,8vw,112px) 40px 42px; border-top:1px solid var(--line); background:var(--panel); min-height:52vh; display:flex; flex-direction:column; justify-content:space-between; }
.archive-footer h1 { max-width:900px; margin-top:18px; font-size:clamp(54px,9vw,132px); letter-spacing:-.07em; font-weight:700; line-height:.84; }
.archive-footer h1 em { display:block; margin-top:.12em; font-style:normal; color:var(--dim); font-size:.68em; letter-spacing:-.055em; }
.archive-footer .meta { max-width:850px; margin-top:34px; display:flex; gap:20px 48px; flex-wrap:wrap; font-size:11px; }
.footer-bottom { display:flex; justify-content:space-between; align-items:flex-end; gap:20px; margin-top:70px; border-top:1px solid var(--line); padding-top:17px; }
.footer-bottom p { max-width:560px; }
.footer-bottom a { color:var(--ink); text-decoration:none; border-bottom:1px solid var(--line); padding-bottom:3px; transition:border-color .2s,color .2s; }
.footer-bottom a:hover { color:var(--acc); border-color:var(--acc); }
@media (max-width:700px) { footer.archive-footer { padding:54px 22px 28px; min-height:60vh; } .archive-footer h1 { font-size:clamp(54px,17vw,78px); } .archive-footer .meta { gap:15px 25px; margin-top:30px; } .footer-bottom { margin-top:55px; align-items:flex-start; flex-direction:column; } }
.hidden { display: none !important; }
</style>
</head>
<body id="top">
<button id="themeBtn" title="Toggle theme" aria-label="Toggle dark mode">☾</button>
<section class="hero" aria-label="A moving stream of album artwork">
  <div class="hero-copy">
    <div class="smallcaps">Every album, within reach</div>
    <h2>A life in records.</h2>
    <p>The music that stayed with you, streaming through one personal shelf.</p>
  </div>
  <div class="hero-stage" id="hero" aria-hidden="true"></div>
</section>
<div class="collection-meta" aria-label="Archive statistics"><div class="meta smallcaps" id="meta"></div></div>
<nav id="archive-nav">
  <button data-v="albums" class="on">Albums</button>
  <button data-v="artists">Artists</button>
  <button data-v="insights">Insights</button>
  <input type="search" id="q" placeholder="Search the shelf…" autocomplete="off">
  <select id="sort"></select>
  <label><input type="checkbox" id="savedOnly"> saved only</label>
  <label><input type="checkbox" id="artOnly" checked> with artwork</label>
</nav>
<main>
  <div class="wall" id="wall"></div>
  <div class="shelf hidden" id="shelf"></div>
  <div class="panels hidden" id="insights"></div>
</main>
<footer class="archive-footer">
  <div>
    <div class="smallcaps">Hriday Nagu’s listening archive</div>
    <h1>The Shelf <em>— a music archive</em></h1>
  </div>
  <div class="footer-bottom smallcaps">
    <p>Spotify library export · artwork &amp; 30s previews via iTunes · artist photos via Deezer · hover to listen · click for buy links</p>
    <a href="#top">Return to the stream ↑</a>
  </div>
</footer>
<script>
const ALBUMS = __ALBUMS__, ARTISTS = __ARTISTS__, STATS = __STATS__;
const $ = s => document.querySelector(s);

// theme
const rootEl = document.documentElement, themeBtn = $('#themeBtn');
function setTheme(t) { rootEl.dataset.theme = t; const to = t === 'dark' ? 'light' : 'dark';
  themeBtn.textContent = t === 'dark' ? '☀' : '☾'; themeBtn.title = `Switch to ${to} mode`; themeBtn.setAttribute('aria-label', `Switch to ${to} mode`);
  try { localStorage.setItem('shelf-theme', t); } catch(e){} }
let savedTheme = 'dark';
try { savedTheme = localStorage.getItem('shelf-theme') || 'dark'; } catch(e){}
setTheme(savedTheme);
themeBtn.onclick = () => setTheme(rootEl.dataset.theme === 'dark' ? 'light' : 'dark');

document.getElementById('meta').innerHTML =
  `<span>${STATS.albums} albums</span><span>${STATS.artists} artists</span><span>${STATS.liked} liked tracks</span><span>${STATS.hours} h / last 12 mo</span>`;

// hero: the two rails use independent actual artist portraits from the existing archive data
const heroArtists = ARTISTS.filter(a => a.img).sort((a,b) => b.plays - a.plays || b.liked_tracks - a.liked_tracks || a.name.localeCompare(b.name));
const hero = document.getElementById('hero');
const PATH = { perspective:30, cardWidth:18, cardHeight:25, cardRadius:.4, birthHeight:2.6, exitHeight:46, railBirth:-11, railExit:44, fan:3.3, turnBirth:6, turnExit:28, stops:24 };
const streamCards = 9;
const streamSpeed = 18;
function corridorKeyframes(dir, name, p) {
  const steps = [];
  for (let s = 0; s <= p.stops; s++) {
    const u = s / p.stops;
    const scale = (p.birthHeight / p.cardHeight) * Math.pow(p.exitHeight / p.birthHeight, u);
    const z = p.perspective * (1 - 1 / scale);
    const rail = p.railExit - (p.railExit - p.railBirth) * Math.pow(1 - u, p.fan);
    const turn = p.turnBirth + (p.turnExit - p.turnBirth) * u;
    steps.push(`${(u * 100).toFixed(2)}%{transform:translate3d(${(dir * rail).toFixed(2)}cqw,0,${z.toFixed(2)}cqw) rotateY(${(-dir * turn).toFixed(2)}deg)}`);
  }
  return `@keyframes ${name}{${steps.join('')}}`;
}
const streamId = `shelf-${Math.random().toString(36).slice(2)}`;
const streamRight = `shelf-right-${streamId}`;
const streamLeft = `shelf-left-${streamId}`;
const streamStyle = document.createElement('style');
streamStyle.textContent = corridorKeyframes(1, streamRight, PATH) + corridorKeyframes(-1, streamLeft, PATH);
document.head.appendChild(streamStyle);
const streamPlane = document.createElement('div');
for (const [railIndex, name] of [streamRight, streamLeft].entries()) {
  for (let i = 0; i < streamCards; i++) {
    const artist = heroArtists[(i * (railIndex ? 7 : 11) + railIndex * 17) % heroArtists.length];
    const el = document.createElement('div');
    el.className = 'stream-card';
    el.dataset.artist = artist.name;
    el.style.animation = `${name} ${streamSpeed}s linear infinite`;
    el.style.animationDelay = `${-(i * streamSpeed) / streamCards}s`;
    el.innerHTML = `<img loading="eager" src="${artist.img}" alt="">`;
    streamPlane.appendChild(el);
  }
}
hero.appendChild(streamPlane);

// ---- audio ----
const audio = new Audio(); audio.preload = 'none';
let current = null, intent = null, progressTimer = null;
function stopAll() {
  clearTimeout(intent); intent = null;
  audio.pause(); audio.src = '';
  if (current) { current.classList.remove('playing'); current = null; }
  clearInterval(progressTimer);
}
function playCard(card, src) {
  stopAll();
  intent = setTimeout(() => {
    audio.src = src; audio.currentTime = 0;
    audio.play().then(() => {
      current = card; card.classList.add('playing');
      const fg = card.querySelector('.fg');
      progressTimer = setInterval(() => {
        if (audio.duration) fg.style.strokeDashoffset = 57 * (1 - audio.currentTime / audio.duration);
      }, 200);
    }).catch(() => {});
  }, 350);
}
audio.addEventListener('ended', stopAll);

// ---- reveal on scroll ----
const io = new IntersectionObserver(entries => {
  entries.forEach(en => {
    if (en.isIntersecting) {
      en.target.style.transitionDelay = (en.target._b % 12) * 30 + 'ms';
      en.target.classList.add('rev');
      io.unobserve(en.target);
    }
  });
}, { rootMargin: '0px 0px 60px 0px' });
function observeCards(container) {
  let b = 0;
  container.querySelectorAll('.card:not(.rev), .acard:not(.rev)').forEach(c => { c._b = b++; io.observe(c); });
}

// ---- tilt ----
function bindTilt(el) {
  el.addEventListener('pointermove', e => {
    const c = e.target.closest('.card, .acard'); if (!c) return;
    const cs = c.querySelector('.case'), r = cs.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - .5, py = (e.clientY - r.top) / r.height - .5;
    cs.style.transform = `translateY(-7px) rotateX(${(-py*7).toFixed(2)}deg) rotateY(${(px*7).toFixed(2)}deg)`;
  });
  el.addEventListener('pointerout', e => {
    const c = e.target.closest('.card, .acard');
    if (c && !c.contains(e.relatedTarget)) c.querySelector('.case').style.transform = '';
  });
}

// ---- render ----
const sortsA = [['alpha','Artist A–Z'],['album','Album A–Z'],['liked','Most liked']];
const sortsR = [['alpha','A–Z'],['liked','Most liked'],['plays','Most played'],['hours','Most hours']];
let view = 'albums';
const wall = $('#wall'), shelf = $('#shelf'), ins = $('#insights'),
      q = $('#q'), sortSel = $('#sort'), savedOnly = $('#savedOnly'), artOnly = $('#artOnly');
function fillSorts() {
  sortSel.innerHTML = (view === 'artists' ? sortsR : sortsA).map(([v,l]) => `<option value="${v}">${l}</option>`).join('');
}
function esc(s){ return (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function buyLinks(a, t, directUrl) {
  const qq = encodeURIComponent(a + ' ' + t);
  const itunes = directUrl || ('https://music.apple.com/us/search?term=' + qq);
  return `<div class="links"><div>
    <a href="${itunes}" target="_blank" rel="noopener">💿 iTunes AAC <span class="tag">iPod native</span></a>
    <a href="https://bandcamp.com/search?q=${qq}" target="_blank" rel="noopener">🅱 Bandcamp <span class="tag">MP3 320</span></a>
    <a href="https://www.qobuz.com/us-en/search?q=${qq}" target="_blank" rel="noopener">Qobuz <span class="tag">hi-res</span></a>
    <a href="https://www.beatport.com/search?q=${qq}" target="_blank" rel="noopener">Beatport <span class="tag">DJ</span></a>
  </div></div>`;
}

const BY_ARTIST = {};
ALBUMS.forEach(a => { (BY_ARTIST[a.a] = BY_ARTIST[a.a] || []).push(a); });
Object.values(BY_ARTIST).forEach(l => l.sort((x, y) => y.lt - x.lt));

function render() {
  stopAll();
  const term = q.value.trim().toLowerCase();
  wall.classList.toggle('hidden', view !== 'albums');
  shelf.classList.toggle('hidden', view !== 'artists');
  ins.classList.toggle('hidden', view !== 'insights');
  if (view === 'insights') return renderInsights();
  if (view === 'albums') {
    let rows = ALBUMS.filter(r =>
      (!savedOnly.checked || r.s) && (!artOnly.checked || r.art) &&
      (!term || r.t.toLowerCase().includes(term) || r.a.toLowerCase().includes(term)));
    const k = {alpha:(a,b)=>a.a.localeCompare(b.a)||a.t.localeCompare(b.t),
               album:(a,b)=>a.t.localeCompare(b.t), liked:(a,b)=>b.lt-a.lt}[sortSel.value||'alpha'];
    rows.sort(k);
    wall.innerHTML = rows.map(r => `
      <div class="card" data-prev="${r.prev}" data-url="${r.url}">
        ${r.s ? '<span class="badge">saved</span>' : ''}
        <div class="case">
          ${r.art ? `<img loading="lazy" src="${r.art}" alt="" onload="this.classList.add('on')">`
                  : `<div class="noart">${esc(r.t)}</div>`}
          <span class="eq"><i></i><i></i><i></i><i></i></span>
          <svg class="ring" viewBox="0 0 22 22"><circle class="bgr" cx="11" cy="11" r="9"/><circle class="fg" cx="11" cy="11" r="9"/></svg>
        </div>
        <div class="lbl"><b>${esc(r.t)}</b><span class="sub">${esc(r.a)}${r.prev && r.pt ? ' · ▶ ' + esc(r.pt) : ''}</span></div>
        ${buyLinks(r.a, r.t, r.url)}
      </div>`).join('');
    observeCards(wall);
  } else {
    let rows = ARTISTS.filter(r => (!savedOnly.checked || r.s) && (!term || r.name.toLowerCase().includes(term)));
    const k = {alpha:(a,b)=>a.name.localeCompare(b.name), liked:(a,b)=>b.liked_tracks-a.liked_tracks,
               plays:(a,b)=>b.plays-a.plays, hours:(a,b)=>b.hours-a.hours}[sortSel.value||'alpha'];
    rows.sort(k);
    shelf.innerHTML = rows.map(r => {
      const albs = (BY_ARTIST[r.name] || []).filter(x => x.art);
      const arts = albs.slice(0, 4);
      const prev = (BY_ARTIST[r.name] || []).find(x => x.prev);
      const mosaic = r.img
        ? `<div class="mosaic single"><img loading="lazy" src="${r.img}" alt="" onload="this.classList.add('on')"></div>`
        : arts.length
        ? `<div class="mosaic${arts.length === 1 ? ' single' : ''}">` +
          arts.map(x => `<img loading="lazy" src="${x.art}" alt="" onload="this.classList.add('on')">`).join('') + `</div>`
        : `<div class="mosaic single"><div class="noart">${esc(r.name)}</div></div>`;
      return `
      <div class="acard" data-prev="${prev ? prev.prev : ''}" data-url="${prev ? prev.url : ''}">
        ${r.saved ? '<span class="badge">saved</span>' : ''}
        <div class="case">${mosaic}
          <span class="eq"><i></i><i></i><i></i><i></i></span>
          <svg class="ring" viewBox="0 0 22 22"><circle class="bgr" cx="11" cy="11" r="9"/><circle class="fg" cx="11" cy="11" r="9"/></svg>
        </div>
        <div class="lbl"><b>${esc(r.name)}</b>
          ${r.g ? `<span class="g">${esc(r.g)}</span>` : ''}
          <span class="sub">${r.albums_in_library.length} album${r.albums_in_library.length===1?'':'s'} · ${r.liked_tracks} liked · ${r.plays} plays · ${r.hours} h</span>
        </div>
      </div>`;
    }).join('');
    observeCards(shelf);
  }
}
function renderInsights() {
  ins.innerHTML = `
    <h2>All-time most played artists</h2><div class="note smallcaps">${esc(STATS.range)}</div>
    <table><tr><th>#</th><th>Artist</th><th>Plays</th><th>Hours</th></tr>
    ${STATS.top_played.map((t,i)=>`<tr><td>${i+1}</td><td>${esc(t[0])}</td><td>${t[1]}</td><td>${t[2]}</td></tr>`).join('')}</table>
    <h2>All-time most played songs</h2><div class="note smallcaps">${esc(STATS.range)}</div>
    <table><tr><th>#</th><th>Track</th><th>Artist</th><th>Plays</th><th>Hours</th></tr>
    ${STATS.top_songs.map((t,i)=>`<tr><td>${i+1}</td><td>${esc(t[0])}</td><td>${esc(t[1])}</td><td>${t[2]}</td><td>${t[3]}</td></tr>`).join('')}</table>
    <h2>Most liked</h2>
    <table><tr><th>#</th><th>Artist</th><th>Liked tracks</th></tr>
    ${STATS.top_liked.map((t,i)=>`<tr><td>${i+1}</td><td>${esc(t[0])}</td><td>${t[1]}</td></tr>`).join('')}</table>`;
}

// ---- events ----
function bindPreview(el) {
  el.addEventListener('mouseover', e => {
    const c = e.target.closest('.card, .acard'); if (!c || c === current) return;
    if (c.dataset.prev) playCard(c, c.dataset.prev);
  });
  el.addEventListener('mouseout', e => {
    const c = e.target.closest('.card, .acard');
    if (c && !c.contains(e.relatedTarget)) stopAll();
  });
  el.addEventListener('click', e => {
    if (e.target.closest('a')) return;
    const c = e.target.closest('.card, .acard'); if (!c) return;
    if (matchMedia('(hover: none)').matches && c.dataset.prev && c !== current && !c.classList.contains('sel')) {
      playCard(c, c.dataset.prev); return;
    }
    const was = c.classList.contains('sel');
    el.querySelectorAll('.sel').forEach(x => x.classList.remove('sel'));
    if (!was) c.classList.add('sel');
  });
}
bindPreview(wall); bindPreview(shelf);
bindTilt(wall); bindTilt(shelf);
document.querySelectorAll('nav button').forEach(b => b.onclick = () => {
  document.querySelectorAll('nav button').forEach(x => x.classList.remove('on'));
  b.classList.add('on'); view = b.dataset.v; fillSorts(); render();
});
q.oninput = render; sortSel.onchange = render; savedOnly.onchange = render; artOnly.onchange = render;
fillSorts(); render();
</script>
</body>
</html>
"""

# all-time track stats straight from the streaming history export
SRC = Path("/Users/emotebot/.hermes/cache/documents/spotify_export/Spotify Account Data")
track_plays, track_ms, track_meta = {}, {}, {}
hist_ts = []
if SRC.exists():
    from collections import defaultdict
    track_plays, track_ms = defaultdict(int), defaultdict(int)
    for f in sorted(SRC.glob("StreamingHistory_music_*.json")):
        for h in json.load(open(f)):
            an, tn = h.get("artistName") or "", h.get("trackName") or ""
            k = (an, tn)
            track_plays[k] += 1
            track_ms[k] += h.get("msPlayed", 0)
            hist_ts.append(h.get("endTime", ""))
hist_ts.sort()
range_note = (f"{hist_ts[0][:10]} → {hist_ts[-1][:10]} · standard export (12 mo) — request Spotify's "
              f"extended streaming history for true lifetime stats") if hist_ts else "from streaming history"

stats = {
    "albums": len(albums), "artists": len(artists),
    "liked": sum(1 for _ in open(DATA / "liked_tracks.csv")) - 1,
    "hours": round(sum(a["hours"] for a in artists), 1),
    "range": range_note,
    "top_played": [[a["name"], a["plays"], a["hours"]] for a in
                   sorted(artists, key=lambda x: -x["plays"])[:20]],
    "top_songs": [[tn, an, track_plays[(an, tn)], round(track_ms[(an, tn)] / 3.6e6, 1)]
                  for (an, tn) in sorted(track_plays, key=lambda k: -track_plays[k])[:25]],
    "top_liked": [[a["name"], a["liked_tracks"]] for a in
                  sorted(artists, key=lambda x: -x["liked_tracks"])[:10]],
}

html = TEMPLATE.replace("__ALBUMS__", json.dumps(albums, ensure_ascii=False)) \
               .replace("__ARTISTS__", json.dumps(
                   [{**{k: v for k, v in a.items() if k != "uri"},
                     "g": (ainfo.get(a["name"]) or {}).get("genre", ""),
                     "img": (aimgs.get(a["name"]) or {}).get("img", "")} for a in artists], ensure_ascii=False)) \
               .replace("__STATS__", json.dumps(stats, ensure_ascii=False))
(OUT / "wall.html").write_text(html, encoding="utf-8")

n_art = sum(1 for a in albums if a["art"])
n_prev = sum(1 for a in albums if a["prev"])
print(f"wall.html written — {n_art}/{len(albums)} artwork, {n_prev}/{len(albums)} previews")
