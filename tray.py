"""System-tray icon: minimize gets CobbAttack out of the way without closing it.

Minimize → the window disappears from the taskbar and lives as a corn icon by the
clock. Left-click it (or right-click → Show) to bring it back; right-click → Quit
exits properly. The X button still quits, same as before — the tray is only for
minimize, so there is no way to "lose" the app.

pystray owns its own Windows message loop on a background thread, so every callback
comes from that thread: they all bounce through root.after() before touching Tk.
Missing library or a tray that refuses to start is not fatal — minimize then just
behaves the old way.
"""

import logging
import os

import config

log = logging.getLogger("cobb.tray")


class Tray:
    """Wraps pystray. `.available` is False when the tray couldn't be created."""

    def __init__(self, root, on_show, on_quit, title="CobbAttack"):
        self.root = root
        self._on_show = on_show
        self._on_quit = on_quit
        self.icon = None
        self.available = False
        self._told_them = False
        try:
            import pystray
            from PIL import Image
        except ImportError as e:
            log.info("system tray unavailable (%s) — minimize stays on the taskbar", e)
            return
        image = self._load_image(Image)
        if image is None:
            return
        menu = pystray.Menu(
            pystray.MenuItem("Show CobbAttack", self._show, default=True),
            pystray.MenuItem("Quit", self._quit),
        )
        try:
            self.icon = pystray.Icon("cobbattack", image, title, menu)
            self.icon.visible = False
            self.icon.run_detached()
            self.available = True
            log.info("system tray ready — minimize hides to the tray")
        except Exception:
            log.warning("system tray could not start — minimize stays on the taskbar",
                        exc_info=True)
            self.icon = None

    @staticmethod
    def _load_image(Image):
        for name in ("cobbattack.ico", "cob-hero-48.png", "cob-hero-icon.png"):
            path = os.path.join(config.ROOT, name)
            if os.path.exists(path):
                try:
                    return Image.open(path)
                except OSError:
                    continue
        log.warning("no icon file for the tray")
        return None

    # ---- called from the pystray thread ----
    def _show(self, *_):
        self.root.after(0, self._on_show)

    def _quit(self, *_):
        self.root.after(0, self._on_quit)

    # ---- called from the Tk thread ----
    def show_icon(self):
        if not self.available:
            return False
        self.icon.visible = True
        if not self._told_them:
            self._told_them = True
            try:
                self.icon.notify(
                    "Still listening — click this icon to bring the window back.",
                    "CobbAttack minimized to the tray")
            except Exception:
                pass  # notifications are optional on some Windows builds
        return True

    def hide_icon(self):
        if self.available:
            self.icon.visible = False

    def stop(self):
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
            self.available = False
