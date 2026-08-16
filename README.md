# The Shelf — a music archive

A visual archive of Hriday's Spotify library, built from a Spotify data export.

## 🌐 Live

- **[The Shelf](https://ghostofnagu.github.io/spotify-archive/wall.html)** — jewel-case wall of every album: dark/light themes, 3D tilt, 30s audio previews on hover, and per-album buy links (iTunes AAC · Bandcamp · Qobuz · Beatport)
- **[Data deck](https://ghostofnagu.github.io/spotify-archive/)** — the plain `index.html` archive view

## 🔨 Rebuild

```bash
python3 build_archive.py   # data deck (index.html)
python3 build_wall.py      # The Shelf (wall.html)
```

Data sources: Spotify library export (`data/`), artwork & 30s previews via iTunes Search API, artist photos via Deezer. All processing is local; no API keys required.
