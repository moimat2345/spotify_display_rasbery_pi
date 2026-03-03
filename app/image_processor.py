import io
import logging
import os

from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger(__name__)

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
BLUR_RADIUS = 30
DARKEN_FACTOR = 0.4  # 0 = full black, 1 = no darkening


def create_display_image(cover_bytes, screen_size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """Build a PIL Image with blurred background + centered cover art."""
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

    return bg


def create_idle_screen(screen_size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    """Black screen with Spotify logo centered (or green circle fallback)."""
    img = Image.new("RGB", screen_size, (0, 0, 0))

    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "spotify_logo.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            ratio = min(80 / logo.height, 80 / logo.width)
            new_size = (int(logo.width * ratio), int(logo.height * ratio))
            logo = logo.resize(new_size, Image.LANCZOS)
            x = (screen_size[0] - logo.width) // 2
            y = (screen_size[1] - logo.height) // 2
            img.paste(logo, (x, y), logo)
        except Exception as e:
            logger.warning("Could not load logo: %s", e)
            _draw_fallback_logo(img, screen_size)
    else:
        _draw_fallback_logo(img, screen_size)

    return img


def _draw_fallback_logo(img, screen_size):
    """Draw a simple green circle as Spotify logo placeholder."""
    draw = ImageDraw.Draw(img)
    cx, cy = screen_size[0] // 2, screen_size[1] // 2
    r = 30
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 215, 96))
