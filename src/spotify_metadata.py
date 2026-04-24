import requests
import json
import re
import logging
import sys


def get_playlist_tracks(playlist_url: str) -> list[dict[str, str]]:
    """
    Fetches playlist tracks from a public Spotify playlist
    without using the official Spotify API.

    Parses the embedded player's server-rendered JSON to extract
    track title, artist, playlist name and cover art URL.
    """
    try:
        if "embed" not in playlist_url:
            playlist_url = playlist_url.replace(
                "open.spotify.com/playlist/",
                "open.spotify.com/embed/playlist/",
            )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(playlist_url, headers=headers)
        response.raise_for_status()

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text,
        )
        if not match:
            match = re.search(r'{"props":.*}', response.text)
            if not match:
                logging.error("Could not find metadata JSON in page.")
                return []

        json_str = match.group(1) if match.lastindex else match.group(0)
        data = json.loads(json_str)

        tracks: list[dict[str, str]] = []
        try:
            entity = data["props"]["pageProps"]["state"]["data"]["entity"]
            album_name: str = entity.get("title", "Unknown Album")
            cover_url: str = (
                entity.get("coverArt", {}).get("sources", [{}])[0].get("url")
            )

            for item in entity.get("trackList", []):
                tracks.append(
                    {
                        "title": item.get("title", ""),
                        "artist": item.get("subtitle", ""),
                        "album": album_name,
                        "cover_url": cover_url,
                    }
                )
        except KeyError:
            logging.error("Failed to parse tracks from JSON structure.")

        return tracks

    except Exception as e:
        logging.error(f"Error scraping Spotify: {e}")
        return []


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python spotify_metadata.py <playlist_url>")
        sys.exit(1)

    found = get_playlist_tracks(sys.argv[1])
    print(f"Found {len(found)} tracks.")
    for t in found[:5]:
        print(f"  - {t['artist']} — {t['title']}")
