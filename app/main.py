import logging
import os
import platform
import signal
import time

import requests
from dotenv import load_dotenv

from app.display import Display
from app.image_processor import create_display_image, create_idle_screen
from app.spotify_client import SpotifyClient
from app.touch_controller import TouchController

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

POLL_INTERVAL = 2.5  # seconds


def _is_desktop():
    return platform.system() != "Linux" or os.environ.get("DISPLAY")


class App:
    def __init__(self):
        self.display = Display()
        self.spotify = SpotifyClient()
        self.touch = TouchController(callback=self._on_touch)
        self.current_track_id = None
        self.running = True
        self._force_poll = False

    def _on_touch(self, action):
        """Handle touch events from the touch controller."""
        logger.info("Touch action: %s", action)
        if action == "previous":
            self.spotify.previous_track()
        elif action == "play_pause":
            self.spotify.play_pause()
        elif action == "next":
            self.spotify.next_track()
        self._force_poll = True

    def run(self):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        # Auth FIRST (may need user input), before display/touch
        self.spotify.ensure_auth()

        self.display.init()
        self.touch.start()

        logger.info("Spotify Display started")
        idle_image = create_idle_screen()

        try:
            while self.running:
                if _is_desktop():
                    self._process_pygame_events()

                track = self.spotify.get_current_track()

                if track is None:
                    if self.current_track_id is not None:
                        self.display.show_image(idle_image)
                        self.current_track_id = None
                        logger.info("No playback — idle screen")
                elif track["track_id"] != self.current_track_id:
                    logger.info("Now playing: %s — %s", track["title"], track["artist"])
                    image = self._download_and_render(track["cover_url"])
                    if image:
                        self.display.show_image(image)
                    self.current_track_id = track["track_id"]

                self._force_poll = False
                self._sleep(POLL_INTERVAL)

        except Exception as e:
            logger.error("Fatal error: %s", e, exc_info=True)
        finally:
            self._cleanup()

    def _download_and_render(self, cover_url):
        """Download cover art and create display image."""
        if not cover_url:
            return None
        try:
            resp = requests.get(cover_url, timeout=10)
            resp.raise_for_status()
            return create_display_image(resp.content)
        except Exception as e:
            logger.error("Failed to download/render cover: %s", e)
            return None

    def _process_pygame_events(self):
        """Drain pygame events to prevent freezing (desktop only)."""
        import pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def _sleep(self, duration):
        """Interruptible sleep that checks for force_poll."""
        end = time.monotonic() + duration
        while time.monotonic() < end and self.running and not self._force_poll:
            time.sleep(0.1)

    def _handle_signal(self, signum, frame):
        logger.info("Received signal %d, shutting down", signum)
        self.running = False

    def _cleanup(self):
        logger.info("Cleaning up")
        self.touch.stop()
        self.display.show_black()
        self.display.cleanup()


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
