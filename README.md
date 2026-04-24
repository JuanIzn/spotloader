# Spotloader - Spotify Playlist Synchronizer (No-API)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A streamlined automation tool designed to keep your local music library in sync with your Spotify playlists. Perfect for **Navidrome**, **Plex**, or **Jellyfin** enthusiasts who want a reliable, self-hosted music experience without the headaches of official API restrictions.

---

### Why this project?
Most Spotify downloaders rely on the official Web API, which has become increasingly restrictive for Free accounts (rate limits, developer app requirements, etc.). 

This tool uses a **Custom Scraping Engine** combined with **iTunes Metadata Enrichment** to fetch perfect ID3 tags (Artist, Album, High-Res Covers) without needing a single Spotify API key. It's built to run quickly and reliably, making it perfect for scheduling via **cron** or external task runners.

---

## Deployment

The recommended way to run the synchronizer is using **Docker Compose**.

1. **Setup your configuration:**
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your playlist URLs
   ```

2. **Run the sync:**
   ```bash
   docker compose up --build
   ```

3. **Schedule periodic syncs** (optional, via cron):

Open cron with `crontab -e`, then add:

   ```bash
   # Run every day at 3 AM
   0 3 * * * cd /path/to/spotloader && docker compose up --build
   ```

> [!TIP]
> Check the `volumes` section in `docker-compose.yml` to point the output to your media server's music library.

---

## How it Works

1. **Smart Scraper:** Reads public Spotify embed data to extract tracks without a Developer Account.
2. **iTunes Enrichment:** Automatically fetches official Album names and high-resolution cover art.
3. **High-Quality Audio:** Leverages `yt-dlp` to find and download the best audio streams.
4. **Perfect Tagging:** Injects standard ID3 tags so your media server categorizes everything flawlessly.
5. **Incremental Sync:** Tracks download state so re-runs only process new songs.

---

## Configuration

Your `config.yaml` is the heart of the project. See `config.example.yaml` for a template:

```yaml
playlists:
  - "https://open.spotify.com/playlist/YOUR_PLAYLIST_ID"

output_dir: "music"

# Optional: browser cookies to avoid YouTube 403 errors
cookie_file: "cookies.txt"
```

---

## Library Organization

The tool follows the standard music library hierarchy, fully compatible with any media server:

```text
music/
└── Artist Name/
    └── Album Name/
        └── Track Title.mp3
```

---

## Manual Execution

For development or bare-metal installations:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 src/sync.py
```

---

## Legal & License

**Disclaimer:** This tool is for **educational and personal use only**. Please support your favorite artists by purchasing their music or using official streaming platforms. The authors are not responsible for any misuse.

Distributed under the **MIT License**. See `LICENSE` for more information.
