"""Defaults merged under user values from settings.json (same pattern as Parlez).

Port defaults are WhisperAttack's — see .claude/rules/protocol.md before touching them.
"""

import json
import os
import sys

# Frozen (PyInstaller exe): everything lives next to CobbAttack.exe.
# Source run: everything lives next to this file. Same folder layout either way.
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(ROOT, "settings.json")
BIN_DIR = os.path.join(ROOT, "bin")
MODELS_DIR = os.path.join(ROOT, "models")
LOG_PATH = os.path.join(ROOT, "cobbattack.log")
WORD_MAPPINGS_PATH = os.path.join(ROOT, "word_mappings.txt")
FUZZY_TERMS_PATH = os.path.join(ROOT, "fuzzy_terms.txt")
COMMANDS_PATH = os.path.join(ROOT, "commands.txt")
CUSTOM_COMMANDS_PATH = os.path.join(ROOT, "custom_commands.txt")
RECIPIENTS_PATH = os.path.join(ROOT, "recipients.txt")

_DEFAULTS = {
    # WhisperAttack wire protocol (drop-in) — keep defaults identical to theirs.
    "control_port": 65432,
    "voiceattack_host": "127.0.0.1",
    "voiceattack_port": 65433,
    # whisper.cpp server (local only).
    "engine_port": 18090,
    "model": "ggml-base.en.bin",
    "threads": 4,
    # 0 = full 30 s context. 768 measured 2026-07-24 on base.en/Vulkan: ~41 ms vs
    # ~53 ms full, identical transcription on test clips. If commands ever come
    # out oddly truncated, set back to 0 (.claude/rules/latency.md).
    "audio_ctx": 768,
    "prefer_gpu": True,
    # Recognition post-processing.
    "fuzzy_threshold": 85,
    # Capture.
    "input_device": None,  # None = system default; or device name substring
    "max_record_seconds": 15,
    "min_record_seconds": 0.3,
    # 🔗 checkbox: start VoiceAttack with us and close it when we quit (valink.py).
    # Off = fully independent, for people who launch everything from their own script.
    "link_voiceattack": False,
}


def load() -> dict:
    settings = dict(_DEFAULTS)
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass  # bad settings file falls back to defaults; logged by main
    return settings


def save_setting(key, value):
    """Persist one key into settings.json without dumping every default."""
    raw = {}
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    raw[key] = value
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)
