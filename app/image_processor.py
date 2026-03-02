import io
import logging
import os

import pygame
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
BLUR_RADIUS = 30
DARKEN_FACTOR = 0.4  # 0 = full black, 1 = no darkening


def create_display_image(cover_bytes, screen_size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """Build a pygame Surface with blurred background + centered cover art."""
    cover = Image.open(io.BytesIO(cover_bytes)).convert("RGB")

    # --- Background: stretch to screen, blur, darken ---
    bg = cover.resize(screen_size, Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    dark_overlay = Image.new("RGB", screen_size, (0, 0, 0))
    bg = Image.blend(bg, dark_overlay, 1.0 - DARKEN_FACTOR)

    # --- Cover: fit in screen keeping aspect ratio ---
    cover.thumbnail(screen_size, Image.LANCZOS)
    cx = (screen_size[0] - cover.width) // 2
    cy = (screen_size[1] - cover.height) // 2
    bg.paste(cover, (cx, cy))

    # --- Convert to pygame Surface ---
    raw = bg.tobytes()
    surface = pygame.image.fromstring(raw, screen_size, "RGB")
    return surface


def create_idle_screen(screen_size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """Black screen with Spotify logo centered (or just a green circle fallback)."""
    surface = pygame.Surface(screen_size)
    surface.fill((0, 0, 0))

    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "spotify_logo.png")
    if os.path.exists(logo_path):
        try:
            logo = pygame.image.load(logo_path).convert_alpha()
            # Scale logo to fit nicely (max 80px height)
            ratio = min(80 / logo.get_height(), 80 / logo.get_width())
            new_size = (int(logo.get_width() * ratio), int(logo.get_height() * ratio))
            logo = pygame.transform.smoothscale(logo, new_size)
            x = (screen_size[0] - logo.get_width()) // 2
            y = (screen_size[1] - logo.get_height()) // 2
            surface.blit(logo, (x, y))
        except Exception as e:
            logger.warning("Could not load logo: %s", e)
            _draw_fallback_logo(surface, screen_size)
    else:
        _draw_fallback_logo(surface, screen_size)

    return surface


def _draw_fallback_logo(surface, screen_size):
    """Draw a simple green circle as Spotify logo placeholder."""
    cx, cy = screen_size[0] // 2, screen_size[1] // 2
    pygame.draw.circle(surface, (30, 215, 96), (cx, cy), 30)
