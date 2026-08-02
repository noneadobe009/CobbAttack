"""CobbAttack — AMD-friendly Whisper voice recognition for VAICOM/VoiceAttack.

Default is the window (ui.py): status light, live feed, teach-a-word box.
--nogui keeps the plain console for debugging; --wav <file> pushes one audio
file through the whole pipeline and exits.
"""

import argparse
import json
import logging
import os
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import config
import custom_vap
import valink
import engine as engine_mod
import normalize as normalize_mod
import recorder as recorder_mod
import bridge
import troubleshoot as troubleshoot_mod
import vaicom_patch

log = logging.getLogger("cobb")

IMPORT_PORT = 65434  # the flight guide's profile drop-box posts .vap files here


class _VapImportHandler(BaseHTTPRequestHandler):
    """Receives a .vap dropped onto the flight guide page (localhost only)."""

    app = None  # set to the running App before the server starts

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Filename")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        count = -1
        if self.path == "/import-vap":
            try:
                size = int(self.headers.get("Content-Length", 0))
                data = self.rfile.read(size)
                name = os.path.basename(
                    self.headers.get("X-Filename", "") or "profile.vap")
                if not name.lower().endswith(".vap"):
                    name += ".vap"
                with open(os.path.join(config.ROOT, name), "wb") as f:
                    f.write(data)
                count = self.app.reimport_profiles()
            except Exception:
                log.exception("profile drop import failed")
        body = json.dumps({"count": count}).encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep HTTP chatter out of the app log
        pass

BANNER = r"""
  CobbAttack — local Whisper for VAICOM / VoiceAttack (AMD-friendly)
"""

# Voice-trainer drill list: the everyday calls plus the phrases Whisper finds
# phonetically slippery (jargon, clipped consonants). Filtered against the real
# profile at startup, so the trainer never asks for a phrase that doesn't exist.
PRACTICE_CANDIDATES = [
    # ground & departure
    "request startup", "request taxi to runway", "request takeoff",
    "request rearming", "request refuel",
    # wingman
    "break right", "break left", "anchor here", "rejoin",
    # awacs
    "request picture", "bogey dope", "declare", "request vector to bandit",
    # tanker
    "ready precontact",
    # arrival
    "inbound", "request landing", "taxi to parking",
    # harder — long or jargon-heavy, the ones worth drilling
    "wilco", "commencing", "request straight in",
    "inbound for carrier", "inbound mother request marshal",
    "requesting unrestricted climb one eight zero",
    "jester scan azimuth",
]


def setup_logging():
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if sys.stdout is not None:  # absent under pythonw — the log file still gets everything
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        root.addHandler(console)
    file_handler = logging.FileHandler(config.LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)


class App:
    def __init__(self, settings):
        self.settings = settings
        self.engine = engine_mod.Engine(settings)
        self.recorder = recorder_mod.Recorder(settings)
        self.normalizer = normalize_mod.Normalizer(settings)
        self.control = bridge.ControlServer(settings["control_port"], self.on_control)
        self.window = None  # set by run_gui; every .post is a no-op without it
        self._recording_since = None
        self._shutdown = threading.Event()
        self.practice_mode = threading.Event()  # trainer on: results go to the panel, not VoiceAttack
        self.started_at = time.time()
        # Everything the troubleshoot page explains after the fact. Capped so a
        # long session can't grow without bound.
        self.history = deque(maxlen=300)

    # ---- UI helper (safe with or without a window) ----
    def post(self, kind, **data):
        if self.window is not None:
            self.window.post(kind, **data)

    def record(self, kind, **data):
        """Keep one pipeline outcome for the troubleshoot page."""
        self.history.append(dict(kind=kind, t=time.time(), **data))

    def reject(self, reason, raw="", cleaned="", best=None, score=0):
        """One refused call: red line in the feed, full story on the page."""
        self.record(reason, raw=raw, cleaned=cleaned, best=best, score=score)
        self.post("rejected", reason=reason, raw=raw, cleaned=cleaned, best=best,
                  score=score, threshold=self.settings["fuzzy_threshold"])

    def build_troubleshoot(self):
        """Write troubleshoot.html from live state — the 🚑 button calls this."""
        return troubleshoot_mod.build(self)

    def start_services(self):
        try:
            self.engine.start()
        except Exception as e:
            log.error("engine failed to start: %s", e)
            self.post("error", message=f"engine failed to start: {e}")
            return
        self.post("device", line=self.engine.device_line)
        self.control.start()
        try:
            _VapImportHandler.app = self
            self.import_server = ThreadingHTTPServer(
                ("127.0.0.1", IMPORT_PORT), _VapImportHandler)
            threading.Thread(target=self.import_server.serve_forever,
                             daemon=True).start()
        except OSError as e:
            log.warning("profile drop-box server not started: %s", e)
        self.post("state", state="ready")
        log.info("ready — waiting for PTT (start/stop on port %d)", self.settings["control_port"])
        if self.settings.get("link_voiceattack"):
            valink.start(self)

    def on_control(self, message):
        if message == "start":
            self._recording_since = time.monotonic()
            self.recorder.start()
            self.post("state", state="recording")
            log.info("PTT down — recording")
        elif message == "stop":
            audio = self.recorder.stop()
            held = time.monotonic() - (self._recording_since or time.monotonic())
            log.info("PTT up — %.2f s of audio", held)
            if held < self.settings["min_record_seconds"] or audio.size == 0:
                log.info("too short — ignored")
                if not self.practice_mode.is_set():
                    self.reject("too_short")
                self.post("state", state="ready")
                return
            self.post("state", state="thinking")
            threading.Thread(target=self.process, args=(audio,), daemon=True).start()
        elif message == "shutdown":
            # The WASC plugin sends this when VoiceAttack exits. Only follow it
            # down when the 🔗 link is on — otherwise the two stay independent.
            if not self.settings.get("link_voiceattack"):
                log.info("VoiceAttack closed — staying open (🔗 link is off)")
                self.post("dropped",
                          reason="VoiceAttack closed — CobbAttack stays open (🔗 link is off)")
                return
            log.info("shutdown requested by plugin")
            self._shutdown.set()
            if self.window is not None:
                self.window.post("state", state="starting")
                self.window.root.after(0, self.window.root.destroy)
        else:
            log.warning("unknown control message: %r", message)

    def process(self, audio):
        t0 = time.monotonic()
        wav = recorder_mod.Recorder.to_wav(audio)
        try:
            raw = self.engine.transcribe(wav)
        except Exception as e:  # engine hiccup must not kill the app mid-flight
            log.error("transcription failed: %s", e)
            self.record("engine_error", raw=str(e))
            self.post("error", message=f"transcription failed: {e}")
            self.post("state", state="ready")
            return
        t_stt = time.monotonic() - t0
        log.info("heard: %r (%.0f ms)", raw, t_stt * 1000)
        self.post("heard", raw=raw, ms=t_stt * 1000)

        verdict = self.normalizer.judge(raw)
        text = verdict.text
        if self.practice_mode.is_set():
            self.post("practice", raw=raw, text=text)
            self.post("state", state="ready")
            return
        if text is None:
            self.reject(verdict.reason, raw=raw, cleaned=verdict.cleaned,
                        best=verdict.best, score=verdict.score)
            self.post("state", state="ready")
            return
        if text.startswith("note "):
            bridge.send_to_kneeboard(text[5:])
            log.info("kneeboard note sent")
            self.record("kneeboard", raw=raw, text=text)
            self.post("dropped", reason="kneeboard note sent")
            self.post("state", state="ready")
            return
        if bridge.send_to_voiceattack(
            text, self.settings["voiceattack_host"], self.settings["voiceattack_port"]
        ):
            total = (time.monotonic() - t0) * 1000
            log.info("sent to VoiceAttack: %r (total %.0f ms)", text, total)
            self.record("sent", raw=raw, text=text, cleaned=verdict.cleaned,
                        best=verdict.best, score=verdict.score)
            self.post("sent", text=text, total_ms=total)
        else:
            self.record("va_unreachable", raw=raw, text=text)
            self.post("error", message="VoiceAttack not reachable — is it running with the WASC plugin?")
        self.post("state", state="ready")

    def teach(self, wrong, right):
        w = " ".join(wrong.strip().lower().split())
        r = " ".join(right.strip().lower().split())
        if self.normalizer.add_mapping(wrong, right):
            self.post("learned", wrong=w, right=r)
            return True
        if (w, r) in self.normalizer.mappings:
            # already taught — still a success from the user's point of view
            self.post("learned_dup", wrong=w, right=r)
            return True
        self.post("error",
                  message="couldn't teach that — both boxes need words, and they must differ")
        return False

    def set_va_link(self, on: bool):
        """🔗 checkbox: start/close VoiceAttack together with CobbAttack."""
        self.settings["link_voiceattack"] = bool(on)
        config.save_setting("link_voiceattack", bool(on))
        if on:
            log.info("🔗 link ON — VoiceAttack opens and closes with CobbAttack")
            valink.start(self)  # no-op if the janitor is already armed
        else:
            # the janitor re-reads settings.json before closing, so saving the
            # setting is all it takes to disarm the close half too
            log.info("🔗 link OFF — VoiceAttack and CobbAttack are independent")
            self.post("dropped", reason="link off — VoiceAttack is on its own now")

    def reimport_profiles(self):
        """Re-parse .vap exports, reload command lists, rebuild the flight guide."""
        custom_vap.refresh()
        self.normalizer.reload_commands()
        try:
            import make_cheatsheet  # tools/ is on sys.path via custom_vap
            make_cheatsheet.main()
        except Exception:
            log.warning("flight guide rebuild failed", exc_info=True)
        count = len(self.normalizer.custom)
        self.post("profile", count=count)
        return count

    # ---- run modes ----
    def practice_phrases(self):
        cmds = set(self.normalizer.commands)
        if not cmds:  # no commands.txt yet — drill the full candidate list
            return list(PRACTICE_CANDIDATES)
        return [p for p in PRACTICE_CANDIDATES if p in cmds]

    def set_practice(self, on: bool):
        if on:
            self.practice_mode.set()
            log.info("voice trainer ON — results stay in the app")
        else:
            self.practice_mode.clear()
            log.info("voice trainer OFF — back to normal operation")

    def run_gui(self):
        from ui import CobbWindow

        # First launch on a new machine: open the setup guide once. It covers
        # installing as step 1, so there is only ever one manual to follow.
        marker = os.path.join(config.ROOT, ".install-guide-shown")
        if not os.path.exists(marker):
            guide = os.path.join(config.ROOT, "Setup-Instruction.html")
            if os.path.exists(guide):
                import webbrowser
                webbrowser.open(guide)
            try:
                open(marker, "w").close()
            except OSError:
                pass

        self.window = CobbWindow(on_teach=self.teach, on_close=self.stop,
                                 on_unteach=self.normalizer.remove_mapping,
                                 on_suggest=self.normalizer.suggest,
                                 on_practice=self.set_practice,
                                 on_troubleshoot=self.build_troubleshoot,
                                 practice_phrases=self.practice_phrases(),
                                 on_valink=self.set_va_link,
                                 valink_on=self.settings.get("link_voiceattack", False))
        threading.Thread(target=self.start_services, daemon=True).start()
        self.window.run()  # blocks until the window closes

    def run_console(self):
        print(BANNER)
        self.start_services()
        print(f"\n  >>> DEVICE: {self.engine.device_line} <<<\n")
        try:
            self._shutdown.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def run_wav(self, path):
        """One-shot pipeline test without a microphone."""
        self.engine.start()
        print(f"\n  >>> DEVICE: {self.engine.device_line} <<<\n")
        with open(path, "rb") as f:
            wav = f.read()
        t0 = time.monotonic()
        raw = self.engine.transcribe(wav)
        log.info("heard: %r (%.0f ms)", raw, (time.monotonic() - t0) * 1000)
        text = self.normalizer.normalize(raw)
        log.info("normalized: %r", text)
        if text is not None:
            bridge.send_to_voiceattack(
                text, self.settings["voiceattack_host"], self.settings["voiceattack_port"]
            )
        self.stop()

    def stop(self):
        self.control.close()
        self.engine.stop()
        log.info("stopped")


def main():
    parser = argparse.ArgumentParser(description="CobbAttack voice server")
    parser.add_argument("--wav", help="transcribe one WAV file through the pipeline and exit")
    parser.add_argument("--nogui", action="store_true", help="plain console instead of the window")
    args = parser.parse_args()

    setup_logging()
    settings = config.load()
    vaicom_patch.apply(settings)
    vaicom_patch.start_watch(settings)  # VA start wipes the fix — reapply on file change
    custom_vap.refresh()  # pick up any new profile export before the normalizer loads
    # vaicom_keywords.txt newer than commands.txt (or commands.txt missing)?
    # Rebuild automatically — no Python knowledge needed for the exe.
    try:
        kw = os.path.join(config.ROOT, "vaicom_keywords.txt")
        cmds = config.COMMANDS_PATH
        if os.path.exists(kw) and (not os.path.exists(cmds)
                                   or os.path.getmtime(kw) > os.path.getmtime(cmds)):
            import make_commands  # tools/ is on sys.path via custom_vap
            make_commands.main()
            log.info("commands.txt rebuilt from vaicom_keywords.txt")
            import make_cheatsheet
            make_cheatsheet.main()
            log.info("flight guide rebuilt")
    except Exception:
        log.warning("commands.txt rebuild failed", exc_info=True)
    app = App(settings)
    if args.wav:
        app.run_wav(args.wav)
    elif args.nogui:
        app.run_console()
    else:
        app.run_gui()


if __name__ == "__main__":
    main()
