"""
spotify_control.py — Core Nexus Spotify Control
Full playback control via the Spotify Web API.

Setup:
  pip install spotipy

  1. Go to https://developer.spotify.com/dashboard
  2. Create a free app (any name)
  3. Add redirect URI: http://localhost:8888/callback
  4. Copy Client ID and Client Secret
  5. Add to config.json:
     "spotify": {
         "client_id":     "YOUR_CLIENT_ID",
         "client_secret": "YOUR_CLIENT_SECRET",
         "redirect_uri":  "http://localhost:8888/callback"
     }

First run will open a browser to authenticate. After that it's automatic.
"""

import os
import json
import webbrowser

CACHE_PATH = os.path.join(os.path.dirname(__file__), ".spotify_cache")

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False

SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "streaming",
    "playlist-read-private",
    "user-library-read",
])


class SpotifyController:
    def __init__(self, config: dict):
        self._sp     = None
        self._ready  = False

        if not SPOTIPY_AVAILABLE:
            print("  [SPOTIFY] spotipy not installed. Run: pip install spotipy")
            return

        spotify_cfg = config.get("spotify", {})
        client_id     = spotify_cfg.get("client_id", "")
        client_secret = spotify_cfg.get("client_secret", "")
        redirect_uri  = spotify_cfg.get("redirect_uri", "http://localhost:8888/callback")

        if not client_id or client_id == "YOUR_CLIENT_ID":
            print("  [SPOTIFY] No credentials in config.json.")
            print("  [SPOTIFY] Add spotify.client_id and spotify.client_secret.")
            print("  [SPOTIFY] Get them free at: https://developer.spotify.com/dashboard")
            return

        try:
            auth = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=SCOPES,
                cache_path=CACHE_PATH,
                open_browser=True
            )
            self._sp    = spotipy.Spotify(auth_manager=auth)
            # Test connection
            self._sp.current_user()
            self._ready = True
            print("  [SPOTIFY] Connected successfully.")
        except Exception as e:
            print(f"  [SPOTIFY] Auth failed: {e}")

    @property
    def ready(self) -> bool:
        return self._ready

    def _get_device_id(self) -> str | None:
        """Get the active device ID."""
        try:
            devices = self._sp.devices()
            for d in devices.get("devices", []):
                if d["is_active"]:
                    return d["id"]
            # No active device — use first available
            devs = devices.get("devices", [])
            if devs:
                return devs[0]["id"]
        except Exception:
            pass
        return None

    def play(self, query: str = "") -> str:
        """Play music. If query given, search and play. Otherwise resume."""
        if not self._ready:
            return "Spotify is not connected, Sir."
        try:
            device_id = self._get_device_id()
            if query:
                results = self._sp.search(q=query, type="track,playlist,artist", limit=1)
                # Try track first
                tracks = results.get("tracks", {}).get("items", [])
                if tracks:
                    uri = tracks[0]["uri"]
                    name = tracks[0]["name"]
                    artist = tracks[0]["artists"][0]["name"]
                    self._sp.start_playback(device_id=device_id, uris=[uri])
                    return f"Playing '{name}' by {artist}, Sir."
                # Try playlist
                playlists = results.get("playlists", {}).get("items", [])
                if playlists:
                    uri  = playlists[0]["uri"]
                    name = playlists[0]["name"]
                    self._sp.start_playback(device_id=device_id, context_uri=uri)
                    return f"Playing playlist '{name}', Sir."
                return f"Could not find '{query}' on Spotify, Sir."
            else:
                self._sp.start_playback(device_id=device_id)
                return "Resuming playback, Sir."
        except spotipy.exceptions.SpotifyException as e:
            if "No active device" in str(e):
                return "No active Spotify device found, Sir. Open Spotify on this machine first."
            return f"Spotify error: {e}"

    def pause(self) -> str:
        if not self._ready:
            return "Spotify is not connected, Sir."
        try:
            self._sp.pause_playback()
            return "Playback paused, Sir."
        except Exception as e:
            return f"Could not pause: {e}"

    def skip(self) -> str:
        if not self._ready:
            return "Spotify is not connected, Sir."
        try:
            self._sp.next_track()
            time_sleep = __import__("time").sleep
            time_sleep(0.5)
            current = self.now_playing()
            return f"Skipped. {current}"
        except Exception as e:
            return f"Could not skip: {e}"

    def previous(self) -> str:
        if not self._ready:
            return "Spotify is not connected, Sir."
        try:
            self._sp.previous_track()
            return "Going back a track, Sir."
        except Exception as e:
            return f"Could not go back: {e}"

    def volume(self, level: int) -> str:
        if not self._ready:
            return "Spotify is not connected, Sir."
        try:
            level = max(0, min(100, level))
            device_id = self._get_device_id()
            self._sp.volume(level, device_id=device_id)
            return f"Spotify volume set to {level}%, Sir."
        except Exception as e:
            return f"Could not set volume: {e}"

    def now_playing(self) -> str:
        if not self._ready:
            return "Spotify is not connected, Sir."
        try:
            current = self._sp.current_playback()
            if not current or not current.get("is_playing"):
                return "Nothing is playing on Spotify, Sir."
            item    = current["item"]
            name    = item["name"]
            artist  = item["artists"][0]["name"]
            return f"Now playing: '{name}' by {artist}."
        except Exception as e:
            return f"Could not get current track: {e}"

    def shuffle(self, state: bool = True) -> str:
        if not self._ready:
            return "Spotify is not connected, Sir."
        try:
            self._sp.shuffle(state)
            return f"Shuffle {'on' if state else 'off'}, Sir."
        except Exception as e:
            return f"Could not set shuffle: {e}"
