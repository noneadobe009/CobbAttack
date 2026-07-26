"""whisper.cpp engine: one long-lived whisper-server.exe child, HTTP /inference per utterance.

Binary selection is the point of this project: try the Vulkan build first (AMD/NVIDIA/Intel),
fall back to the CPU build, and say loudly which one won. The model stays loaded across
utterances — spawning per command would cost seconds of reload.
"""

import ctypes
import logging
import os
import socket
import subprocess
import threading
import time

import requests

import config

log = logging.getLogger("cobb.engine")


def _make_kill_on_close_job():
    """A Windows Job Object that kills its processes when the last handle closes.

    Assigning the whisper-server child to this job means it dies with us even if
    CobbAttack is force-killed (Task Manager, Stop-Process) — otherwise the server
    lingers, holds the model in RAM, and squats on the engine port so the NEXT run
    silently talks to the stale server (observed: 20 orphans after a day of dev).
    """
    kernel32 = ctypes.windll.kernel32
    job = kernel32.CreateJobObjectW(None, None)

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", ctypes.c_char * 64),  # opaque; only flags matter
            ("IoInfo", ctypes.c_char * 48),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    # LimitFlags (DWORD) sits at offset 16 within BasicLimitInformation.
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    flags = ctypes.c_uint32(0x2000)  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    ctypes.memmove(ctypes.addressof(info) + 16, ctypes.addressof(flags), 4)
    ok = kernel32.SetInformationJobObject(job, 9, ctypes.byref(info),  # 9 = ExtendedLimitInformation
                                          ctypes.sizeof(info))
    if not ok:
        kernel32.CloseHandle(job)
        return None
    return job

# Primes Whisper toward DCS vocabulary (same idea as WhisperAttack's initial prompt).
DCS_PROMPT = (
    "DCS radio message. Callsigns: Enfield, Springfield, Uzi, Colt, Dodge, Chevy, "
    "Pontiac, Texaco, Arco, Shell, Overlord, Magic, Wizard, Darkstar, Focus. "
    "Anapa, Batumi, Kobuleti, Senaki, Kutaisi. Request startup, taxi, takeoff, "
    "inbound, refuel, rearm, bogey dope, picture, declare."
)

_STARTUP_TIMEOUT = 30  # model load can take a while on slow disks
_VULKAN_DIR = os.path.join(config.BIN_DIR, "vulkan")
_CPU_DIR = os.path.join(config.BIN_DIR, "cpu", "Release")


class EngineError(Exception):
    pass


class Engine:
    def __init__(self, settings):
        self.settings = settings
        self.process = None
        self.device_line = "unknown"
        self._stderr_lines = []
        self._job = None

    def _kill_stale_servers(self):
        # A crashed/killed previous run leaves its whisper-server behind, still
        # bound to our port — the new run would then talk to the OLD model.
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "whisper-server.exe"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode == 0:
            log.warning("killed stale whisper-server process(es) from a previous run")

    def start(self):
        self._kill_stale_servers()
        candidates = []
        if self.settings["prefer_gpu"]:
            candidates.append(("Vulkan", _VULKAN_DIR))
        candidates.append(("CPU", _CPU_DIR))

        for label, bin_dir in candidates:
            exe = os.path.join(bin_dir, "whisper-server.exe")
            if not os.path.exists(exe):
                log.warning("%s build missing at %s", label, exe)
                continue
            if self._launch(label, exe):
                self._warm_up()
                return
        raise EngineError("no whisper-server build could be started")

    def _launch(self, label, exe) -> bool:
        model = os.path.join(config.MODELS_DIR, self.settings["model"])
        if not os.path.exists(model):
            raise EngineError(f"model not found: {model}")
        args = [
            exe,
            "-m", model,
            "--host", "127.0.0.1",
            "--port", str(self.settings["engine_port"]),
            "-t", str(self.settings["threads"]),
        ]
        if self.settings["audio_ctx"]:
            args += ["--audio-ctx", str(self.settings["audio_ctx"])]

        log.info("starting %s engine: %s", label, os.path.basename(exe))
        self._stderr_lines = []
        self.process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if self._job is None:
            self._job = _make_kill_on_close_job()
            if self._job is None:
                log.warning("could not create kill-on-close job — orphan protection off")
        if self._job is not None:
            ctypes.windll.kernel32.AssignProcessToJobObject(
                self._job, int(self.process._handle))
        threading.Thread(target=self._drain_stderr, daemon=True).start()

        deadline = time.monotonic() + _STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                log.warning("%s engine exited during startup (code %s)", label, self.process.returncode)
                return False
            if self._port_open():
                self._resolve_device(label)
                return True
            time.sleep(0.25)
        log.warning("%s engine did not open its port in time", label)
        self.stop()
        return False

    def _drain_stderr(self):
        proc = self.process
        for line in proc.stderr:
            self._stderr_lines.append(line.rstrip())

    def _port_open(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.settings["engine_port"]), timeout=0.2):
                return True
        except OSError:
            return False

    def _resolve_device(self, label):
        # The rule (.claude/rules/latency.md): say loudly what we're running on.
        # The device lines land on stderr asynchronously — on a warm start the
        # port can open before they're drained, so give them a moment.
        gpu = None
        deadline = time.monotonic() + 3
        while gpu is None and time.monotonic() < deadline:
            gpu = next(
                (l for l in self._stderr_lines if "ggml_vulkan: 0 =" in l or "using Vulkan" in l),
                None,
            )
            if gpu is None:
                time.sleep(0.1)
        if label == "Vulkan" and gpu:
            name = gpu.split("=", 1)[-1].split("|", 1)[0].strip() if "=" in gpu else "Vulkan GPU"
            self.device_line = f"Vulkan GPU — {name}"
        elif label == "Vulkan":
            self.device_line = "Vulkan build (device unconfirmed — check cobbattack.log)"
        else:
            self.device_line = "CPU — no GPU acceleration"
        log.info("device: %s", self.device_line)

    def _warm_up(self):
        # First inference pays JIT/context cost (~seconds); absorb it now so the
        # first real radio call doesn't.
        import wave, io

        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(b"\x00\x00" * 16000)
        t0 = time.monotonic()
        self.transcribe(buf.getvalue())
        log.info("engine warm-up done in %.1f s", time.monotonic() - t0)

    def transcribe(self, wav_bytes: bytes) -> str:
        url = f"http://127.0.0.1:{self.settings['engine_port']}/inference"
        resp = requests.post(
            url,
            files={"file": ("utterance.wav", wav_bytes, "audio/wav")},
            data={
                "temperature": "0",
                "response_format": "json",
                "prompt": DCS_PROMPT,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("text", "").strip()

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
