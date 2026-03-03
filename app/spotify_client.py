import logging
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)

SCOPES = "user-read-playback-state user-modify-playback-state"


class SpotifyClient:
    def __init__(self):
        self.auth_manager = SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
            scope=SCOPES,
            cache_path=".spotify_cache",
            open_browser=False,
        )
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

    def ensure_auth(self):
        """Run interactive auth if no cached token. Call before main loop."""
        token_info = self.auth_manager.cache_handler.get_cached_token()
        if token_info:
            logger.info("Using cached Spotify token")
            return

        logger.info("No cached token — starting Spotify authorization")
        auth_url = self.auth_manager.get_authorize_url()
        print(f"\n  Open this URL in your browser:\n\n  {auth_url}\n")
        print("  After authorizing, paste the full redirect URL here:")
        response_url = input("  > ").strip()
        code = self.auth_manager.parse_response_code(response_url)
        self.auth_manager.get_access_token(code)
        logger.info("Spotify authorization complete")

    def get_current_track(self):
        """Return current track info dict or None if nothing playing."""
        try:
            playback = self.sp.current_playback()
        except spotipy.SpotifyException as e:
            logger.error("Spotify API error: %s", e)
            return None
        except Exception as e:
            logger.error("Network error: %s", e)
            return None

        if not playback or not playback.get("item"):
            return None

        item = playback["item"]
        images = item.get("album", {}).get("images", [])
        cover_url = images[0]["url"] if images else None

        return {
            "track_id": item["id"],
            "title": item["name"],
            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
            "cover_url": cover_url,
            "is_playing": playback.get("is_playing", False),
        }

    def play_pause(self):
        """Toggle play/pause on the active device."""
        try:
            playback = self.sp.current_playback()
            if not playback:
                return
            if playback.get("is_playing"):
                self.sp.pause_playback()
            else:
                self.sp.start_playback()
        except spotipy.SpotifyException as e:
            logger.error("Play/pause error: %s", e)

    def next_track(self):
        try:
            self.sp.next_track()
        except spotipy.SpotifyException as e:
            logger.error("Next track error: %s", e)

    def previous_track(self):
        try:
            self.sp.previous_track()
        except spotipy.SpotifyException as e:
            logger.error("Previous track error: %s", e)
