import logging
import platform
import threading
import time

logger = logging.getLogger(__name__)

# Touch zones on 480px-wide screen
ZONE_PREV = 160       # x < 160 → previous
ZONE_PLAY = 320       # 160 <= x < 320 → play/pause
                      # x >= 320 → next

TAP_TIMEOUT = 0.4     # Max seconds between touch down and up for a tap


class TouchController:
    """Reads touch events from evdev (Linux) and emits actions."""

    def __init__(self, callback):
        """
        callback: function(action) where action is "previous", "play_pause", or "next"
        """
        self.callback = callback
        self._running = False
        self._thread = None

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

        touch_x = None
        touch_down_time = None

        try:
            for event in device.read_loop():
                if not self._running:
                    break

                # Track X coordinate
                if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_X:
                    touch_x = event.value

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
        """Map x coordinate to action."""
        if x < ZONE_PREV:
            action = "previous"
        elif x < ZONE_PLAY:
            action = "play_pause"
        else:
            action = "next"
        logger.debug("Tap at x=%d → %s", x, action)
        self.callback(action)
