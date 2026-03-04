import logging
import platform
import threading
import time

logger = logging.getLogger(__name__)

# Touch zones on 480px-wide screen
ZONE_PREV = 160       # x < 160 → previous (double tap)
ZONE_PLAY = 320       # 160 <= x < 320 → play/pause (single tap)
                      # x >= 320 → next (double tap)

TAP_TIMEOUT = 0.4     # Max seconds between touch down and up for a tap
DOUBLE_TAP_TIMEOUT = 0.5  # Max seconds between two taps for double tap


class TouchController:
    """Reads touch events from evdev (Linux) and emits actions."""

    def __init__(self, callback):
        """
        callback: function(action) where action is "previous", "play_pause", or "next"
        """
        self.callback = callback
        self._running = False
        self._thread = None
        self._last_tap_time = None
        self._last_tap_x = None
        self._pending_timer = None

    def start(self):
        if platform.system() != "Linux":
            logger.info("Touch controller disabled (not Linux)")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _find_touch_device(self):
        """Find the first touchscreen input device."""
        try:
            import evdev
        except ImportError:
            logger.error("python-evdev not installed")
            return None

        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for dev in devices:
            caps = dev.capabilities(verbose=True)
            for (type_name, _), events in caps.items():
                if type_name == "EV_ABS":
                    logger.info("Found touch device: %s (%s)", dev.name, dev.path)
                    return dev
        logger.warning("No touchscreen device found")
        return None

    def _run(self):
        import evdev
        from evdev import ecodes

        device = self._find_touch_device()
        if not device:
            return

        # Get the actual range of X coordinates from the device
        abs_info = device.capabilities().get(ecodes.EV_ABS, [])
        x_max = 480  # default
        for code, info in abs_info:
            if code == ecodes.ABS_X:
                if hasattr(info, 'max'):
                    x_max = info.max
                elif isinstance(info, tuple) and len(info) > 1:
                    x_max = info[1]
                logger.info("Touch X range: 0-%d (will scale to 0-480)", x_max)
                break

        touch_x = None
        touch_down_time = None

        try:
            for event in device.read_loop():
                if not self._running:
                    break

                # Track X coordinate
                if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_X:
                    raw_x = event.value
                    # Scale to screen coordinates (0-480)
                    touch_x = int((raw_x / x_max) * 480)
                    logger.debug("Touch X: raw=%d, scaled=%d", raw_x, touch_x)

                # Touch down
                if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                    if event.value == 1:  # down
                        touch_down_time = time.monotonic()
                    elif event.value == 0 and touch_down_time is not None:  # up
                        duration = time.monotonic() - touch_down_time
                        if duration < TAP_TIMEOUT and touch_x is not None:
                            self._handle_tap(touch_x)
                        touch_down_time = None
        except Exception as e:
            logger.error("Touch controller error: %s", e)

    def _handle_tap(self, x):
        """Map x coordinate to action based on single/double tap and zone."""
        now = time.monotonic()

        # Determine zone
        if x < ZONE_PREV:
            zone = "left"
        elif x < ZONE_PLAY:
            zone = "middle"
        else:
            zone = "right"

        # Middle zone: single tap → play/pause (immediate)
        if zone == "middle":
            logger.debug("Single tap at x=%d (middle) → play_pause", x)
            self.callback("play_pause")
            return

        # Left/Right zones: require double tap
        if self._last_tap_time and (now - self._last_tap_time) < DOUBLE_TAP_TIMEOUT:
            # Check if it's the same zone
            if self._last_tap_x is not None:
                last_zone = "left" if self._last_tap_x < ZONE_PREV else "right"
                if last_zone == zone:
                    # Double tap detected!
                    action = "previous" if zone == "left" else "next"
                    logger.debug("Double tap at x=%d (%s) → %s", x, zone, action)
                    self.callback(action)
                    self._last_tap_time = None
                    self._last_tap_x = None
                    return

        # First tap in left/right zone - remember it
        logger.debug("First tap at x=%d (%s), waiting for double tap...", x, zone)
        self._last_tap_time = now
        self._last_tap_x = x
