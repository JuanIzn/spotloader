import subprocess
import yaml
import logging
import json
import requests
from pathlib import Path
from typing import Optional
from spotify_metadata import get_playlist_tracks
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("sync.log"),
        logging.StreamHandler(),
    ],
)


def load_config() -> Optional[dict]:
    """Loads and returns the YAML configuration file."""
    config_path = Path("config.yaml")
    if not config_path.exists():
        logging.error("config.yaml not found!")
        return None
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_itunes_metadata(artist: str, title: str) -> Optional[dict[str, str]]:
    """Fetches real album metadata from the iTunes Search API."""
    try:
        params = {"term": f"{artist} {title}", "entity": "song", "limit": 1}
        r = requests.get(
            "https://itunes.apple.com/search", params=params, timeout=5
        )
        data = r.json()
        if data.get("resultCount", 0) > 0:
            result = data["results"][0]
            return {
                "album": result.get("collectionName"),
                "title": result.get("trackName", title),
                "artist": result.get("artistName", artist),
            }
    except Exception as e:
        logging.warning(f"iTunes lookup failed for {artist} - {title}: {e}")
    return None


def sanitize_filename(name: str) -> str:
    """Removes characters that are unsafe for file and directory names."""
    return "".join(c for c in name if c.isalnum() or c in " -_").strip()


def download_track(
    track_info: dict, output_path: Path, cookie_file: Optional[str]
) -> bool:
    """Downloads audio from YouTube Music via yt-dlp."""
    search_query = (
        f"ytsearch1:{track_info['artist']} - {track_info['title']} official audio"
    )

    cmd = [
        "yt-dlp",
        search_query,
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--output", str(output_path),
        "--no-playlist",
        "--quiet",
    ]

    if cookie_file and Path(cookie_file).exists():
        cmd.extend(["--cookies", cookie_file])

    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"yt-dlp failed for {track_info['title']}: {e}")
        return False


def tag_file(file_path: Path, track_info: dict) -> bool:
    """Adds ID3 tags (title, artist, album) and cover art to an MP3 file."""
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except error:
            pass

        audio.tags.add(TIT2(encoding=3, text=track_info["title"]))
        audio.tags.add(TPE1(encoding=3, text=track_info["artist"]))
        audio.tags.add(TALB(encoding=3, text=track_info["album"]))

        if track_info.get("cover_url"):
            response = requests.get(track_info["cover_url"])
            if response.status_code == 200:
                audio.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=response.content,
                    )
                )

        audio.save()
        return True
    except Exception as e:
        logging.error(f"Tagging failed for {file_path}: {e}")
        return False


def run_sync() -> None:
    """Main synchronization entry point. Runs once per invocation."""
    config = load_config()
    if not config:
        return

    output_dir = Path(config.get("output_dir", "music"))
    state_file = Path(".state/sync_state.json")
    state_file.parent.mkdir(exist_ok=True)

    if state_file.exists():
        with open(state_file, "r") as f:
            state: dict = json.load(f)
    else:
        state = {"downloaded_tracks": []}

    playlists: list[str] = config.get("playlists", [])
    cookie_file: Optional[str] = config.get("cookie_file")

    for playlist_url in playlists:
        logging.info(f"Syncing playlist: {playlist_url}")
        tracks = get_playlist_tracks(playlist_url)

        if not tracks:
            logging.warning(f"No tracks found for {playlist_url}")
            continue

        for track in tracks:
            itunes_meta = get_itunes_metadata(track["artist"], track["title"])
            if itunes_meta and itunes_meta.get("album"):
                track["album"] = itunes_meta["album"]

            track_id = f"{track['artist']} - {track['title']}"
            if track_id in state["downloaded_tracks"]:
                continue

            logging.info(f"Downloading: {track_id} (Album: {track['album']})")

            safe_artist = sanitize_filename(track["artist"])
            safe_album = sanitize_filename(track["album"])
            safe_title = sanitize_filename(track["title"])

            track_folder = output_dir / safe_artist / safe_album
            track_folder.mkdir(parents=True, exist_ok=True)

            final_path = track_folder / f"{safe_title}.mp3"

            if download_track(track, final_path.with_suffix(""), cookie_file):
                actual_path = (
                    final_path
                    if final_path.exists()
                    else Path(str(final_path) + ".mp3")
                )

                if tag_file(actual_path, track):
                    state["downloaded_tracks"].append(track_id)
                    with open(state_file, "w") as f:
                        json.dump(state, f, indent=2)
                    logging.info(f"Successfully synced: {track_id}")
                else:
                    logging.error(f"Failed to tag: {track_id}")
            else:
                logging.error(f"Failed to download: {track_id}")

    logging.info("Sync complete.")


if __name__ == "__main__":
    run_sync()
