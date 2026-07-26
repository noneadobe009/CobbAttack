"""In-memory PTT capture: 16 kHz mono float32 (the protocol's audio contract).

Pattern borrowed from Parlez's Recorder — stream stays closed between utterances;
open on start, close on stop, hand back one contiguous array.
"""

import io
import logging
import threading
import wave

import numpy as np
import sounddevice as sd

log = logging.getLogger("cobb.recorder")

SAMPLE_RATE = 16000


class Recorder:
    def __init__(self, settings):
        self.settings = settings
        self._stream = None
        self._chunks = []
        self._lock = threading.Lock()

    def _device_index(self):
        wanted = self.settings.get("input_device")
        if not wanted:
            return None
        wanted = wanted.lower()
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0 and wanted in dev["name"].lower():
                return i
        log.warning("input device %r not found; using system default", wanted)
        return None

    def start(self):
        with self._lock:
            if self._stream is not None:
                return  # already recording; duplicate "start" is harmless
            self._chunks = []
            max_frames = int(self.settings["max_record_seconds"] * SAMPLE_RATE)

            def callback(indata, frames, time_info, status):
                if status:
                    log.warning("capture status: %s", status)
                if sum(len(c) for c in self._chunks) < max_frames:
                    self._chunks.append(indata[:, 0].copy())

            device = self._device_index()
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="float32",
                device=device,
                callback=callback,
            )
            self._stream.start()
            # name the actual device — the frozen exe once resolved "default"
            # to the wrong mic and recorded silence; this line is the tell
            try:
                idx = device if device is not None else sd.default.device[0]
                log.info("recording from: %s", sd.query_devices(idx)["name"])
            except Exception:
                log.info("recording from: system default (name unavailable)")

    def stop(self) -> np.ndarray:
        with self._lock:
            if self._stream is None:
                return np.zeros(0, dtype=np.float32)
            self._stream.stop()
            self._stream.close()
            self._stream = None
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            return np.concatenate(self._chunks)

    @staticmethod
    def to_wav(audio: np.ndarray) -> bytes:
        pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(pcm.tobytes())
        return buf.getvalue()
