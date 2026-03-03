# Spotify Now Playing Display — Raspberry Pi

Affiche la pochette de la chanson en cours sur un écran TFT 3.5" SPI connecté au Raspberry Pi, avec fond blur ambiant et contrôle tactile.

## Matériel requis

- Raspberry Pi 4 (Raspberry Pi OS Lite 64-bit)
- Écran TFT 3.5" SPI 480x320 (accessible via `/dev/fb1`)
- Écran tactile (accessible via evdev)
- Connexion réseau (Wi-Fi ou Ethernet)
- Compte Spotify Premium

## Fonctionnalités

- Affichage de la pochette avec fond blur ambiant (style Apple Music)
- Écran idle (noir + logo) quand rien ne joue
- Mise à jour automatique au changement de piste (~2.5s polling)
- Contrôle tactile :
  - Zone gauche (< 160px) → piste précédente
  - Zone milieu (160-320px) → pause/play
  - Zone droite (> 320px) → piste suivante
- Service systemd avec redémarrage automatique

## Installation

### 1. Créer une app Spotify Developer

1. Aller sur https://developer.spotify.com/dashboard
2. Créer une application
3. Ajouter `https://localhost:8888/callback` comme Redirect URI
4. Noter le Client ID et Client Secret

### 2. Installer sur le Pi

```bash
ssh pi@192.168.2.3
git clone <repo-url> ~/spotify_display_rasbery_pi
cd ~/spotify_display_rasbery_pi
./install.sh
```

### 3. Configurer

```bash
nano .env
```

Remplir :
```
SPOTIPY_CLIENT_ID=votre_client_id
SPOTIPY_CLIENT_SECRET=votre_client_secret
SPOTIPY_REDIRECT_URI=https://localhost:8888/callback
```

### 4. Première autorisation

La première fois, il faut autoriser l'app manuellement (spotipy affiche une URL à ouvrir dans un navigateur) :

```bash
source venv/bin/activate
python -m app.main
```

Copier l'URL affichée, l'ouvrir dans un navigateur, autoriser, puis coller l'URL de callback. Le token sera mis en cache dans `.spotify_cache`.

### 5. Lancer le service

```bash
sudo systemctl start spotify-display
```

## Commandes utiles

```bash
# Voir les logs en temps réel
journalctl -u spotify-display -f

# Redémarrer le service
sudo systemctl restart spotify-display

# Arrêter le service
sudo systemctl stop spotify-display

# Désactiver le démarrage automatique
sudo systemctl disable spotify-display
```

## Développement local (Mac/Linux avec X11)

L'app détecte automatiquement l'environnement. Sur un desktop, elle s'ouvre en mode fenêtré 480x320 (le contrôle tactile est désactivé, mais le clavier fonctionne — Escape pour quitter).

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # remplir les credentials
python -m app.main
```

## Architecture

```
app/
├── main.py              # Boucle principale (polling + state machine)
├── spotify_client.py    # Wrapper spotipy (auth, API calls)
├── display.py           # Rendu pygame (framebuffer ou fenêtré)
├── image_processor.py   # Pillow (blur, resize, composition)
└── touch_controller.py  # evdev (événements tactiles)
```
