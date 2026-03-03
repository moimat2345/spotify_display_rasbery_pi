#!/bin/bash
set -e

echo "=== Spotify Display — Installation ==="

# System dependencies
echo "[1/4] Installing system packages..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-pygame \
    python3-evdev \
    libsdl2-dev \
    libsdl2-image-dev \
    libjpeg-dev \
    zlib1g-dev

# Python venv
echo "[2/4] Setting up Python virtual environment..."
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# .env
echo "[3/4] Setting up configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ">>> Created .env — edit it with your Spotify credentials:"
    echo "    nano .env"
else
    echo ">>> .env already exists, skipping"
fi

# systemd
echo "[4/4] Installing systemd service..."
sudo cp spotify-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable spotify-display

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your Spotify app credentials"
echo "  2. Run once manually to authorize: source venv/bin/activate && python -m app.main"
echo "     (This will print a URL — open it in a browser to authorize)"
echo "  3. Start the service: sudo systemctl start spotify-display"
echo "  4. Check logs: journalctl -u spotify-display -f"
