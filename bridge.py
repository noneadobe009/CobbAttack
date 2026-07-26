"""The two TCP sockets of the WhisperAttack protocol (.claude/rules/protocol.md).

Control in on :65432 — `start` / `stop` / `shutdown`, case-insensitive, no reply.
Text out to :65433 — raw UTF-8, one send, close. The WASC plugin inside VoiceAttack
receives it and runs the matching command.
"""

import logging
import socket
import threading

log = logging.getLogger("cobb.bridge")


class ControlServer:
    """Listens for the WASC plugin's start/stop/shutdown messages."""

    def __init__(self, port: int, on_message):
        self.port = port
        self.on_message = on_message
        self._server = None

    def start(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", self.port))
        self._server.listen(4)
        threading.Thread(target=self._accept_loop, daemon=True).start()
        log.info("control listener on 127.0.0.1:%d", self.port)

    def _accept_loop(self):
        while True:
            try:
                conn, _ = self._server.accept()
            except OSError:
                return  # closed during shutdown
            with conn:
                try:
                    data = conn.recv(1024)
                except OSError:
                    continue
            message = data.decode("utf-8", errors="replace").strip().lower()
            if message:
                self.on_message(message)

    def close(self):
        if self._server:
            self._server.close()


def send_to_voiceattack(text: str, host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=3) as s:
            s.sendall(text.encode("utf-8"))
        return True
    except OSError as e:
        log.error("could not reach VoiceAttack plugin on %s:%d — %s", host, port, e)
        return False


def send_to_kneeboard(text: str):
    """Parity with WhisperAttack's `note ` prefix: clipboard + Ctrl+Alt+P into DCS."""
    try:
        import pyperclip
        import keyboard
    except ImportError:
        log.warning("kneeboard note skipped — pyperclip/keyboard not installed")
        return
    pyperclip.copy(text)
    keyboard.press_and_release("ctrl+alt+p")
