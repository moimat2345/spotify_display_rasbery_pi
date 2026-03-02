import logging
import os
import platform

import pygame

logger = logging.getLogger(__name__)

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320


class Display:
    """Manages the pygame display on framebuffer or windowed fallback."""

    def __init__(self):
        self.screen = None

    def init(self):
        """Initialize pygame display."""
        if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
            # Framebuffer mode for Raspberry Pi (no X11)
            os.environ.setdefault("SDL_VIDEODRIVER", "fbcon")
            os.environ.setdefault("SDL_FBDEV", "/dev/fb1")
            logger.info("Using framebuffer: %s", os.environ.get("SDL_FBDEV"))

        pygame.init()

        if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
            self.screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN
            )
            pygame.mouse.set_visible(False)
        else:
            # Windowed mode for development
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Spotify Display")
            logger.info("Using windowed mode (dev)")

    def show_image(self, surface):
        """Display a pygame Surface on screen."""
        self.screen.blit(surface, (0, 0))
        pygame.display.flip()

    def show_black(self):
        """Fill screen with black."""
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def cleanup(self):
        """Shut down pygame."""
        pygame.quit()
