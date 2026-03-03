import logging
import os
import platform

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320


def _is_pi_framebuffer():
    """Detect if we should use direct framebuffer mode."""
    return platform.system() == "Linux" and not os.environ.get("DISPLAY")


class FramebufferDisplay:
    """Writes directly to /dev/fb1 in RGB565 format (SPI TFT screens)."""

    def __init__(self, device="/dev/fb1"):
        self.device = device

    def init(self):
        logger.info("Using direct framebuffer: %s", self.device)
        # Clear screen on start
        self.show_black()

    def show_image(self, pil_image):
        """Write a PIL Image to the framebuffer as RGB565."""
        img = pil_image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
        self._write_rgb565(img)

    def show_black(self):
        black = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0))
        self._write_rgb565(black)

    def _write_rgb565(self, img):
        """Convert PIL RGB image to RGB565 and write to framebuffer."""
        arr = np.array(img, dtype=np.uint16)
        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        with open(self.device, "wb") as fb:
            fb.write(rgb565.astype(np.uint16).tobytes())

    def cleanup(self):
        self.show_black()


class PygameDisplay:
    """Windowed pygame display for development on Mac/Linux desktop."""

    def __init__(self):
        self.screen = None

    def init(self):
        import pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Spotify Display")
        logger.info("Using windowed mode (dev)")

    def show_image(self, pil_image):
        import pygame
        img = pil_image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
        raw = img.tobytes()
        surface = pygame.image.fromstring(raw, (SCREEN_WIDTH, SCREEN_HEIGHT), "RGB")
        self.screen.blit(surface, (0, 0))
        pygame.display.flip()

    def show_black(self):
        import pygame
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def cleanup(self):
        import pygame
        pygame.quit()


class Display:
    """Auto-selects framebuffer or pygame backend."""

    def __init__(self):
        if _is_pi_framebuffer():
            fb_dev = os.environ.get("SDL_FBDEV", "/dev/fb1")
            self._backend = FramebufferDisplay(device=fb_dev)
        else:
            self._backend = PygameDisplay()

    def init(self):
        self._backend.init()

    def show_image(self, pil_image):
        self._backend.show_image(pil_image)

    def show_black(self):
        self._backend.show_black()

    def cleanup(self):
        self._backend.cleanup()
