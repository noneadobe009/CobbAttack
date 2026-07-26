"""Read the user's own voice commands from a VoiceAttack profile export (.vap).

Workflow (documented in SETUP.md "Your own voice commands"): the user exports
their profile as a .vap file into this folder; on every startup we parse the
newest one and regenerate custom_commands.txt. Those phrases join the firewall
allow-list (normalize.py) — without this, a custom command like "turn on the
lights" would be discarded as garbage — and the flight guide shows them in a
"Your custom commands" section (tools/make_cheatsheet.py).

A .vap is plain XML. We keep only commands the user made themselves: anything
whose actions mention the VAICOM or WhisperAttack plugins is plumbing, and the
giant keyword-collection entries are VAICOM's, not the user's.
"""

import glob
import logging
import os
import sys
import xml.etree.ElementTree as ET

import config

log = logging.getLogger("cobb.custom")

sys.path.insert(0, os.path.join(config.ROOT, "tools"))
from make_commands import split_top, expand  # noqa: E402  (single source for [a;b] expansion)

_PLUMBING_MARKS = ("vaicom", "whisper")


def _newest_vap():
    vaps = glob.glob(os.path.join(config.ROOT, "*.vap"))
    return max(vaps, key=os.path.getmtime) if vaps else None


def _iter_custom_commands(vap_path):
    """Yield (spoken_string) for user-made commands only."""
    tree = ET.parse(vap_path)
    for cmd in tree.getroot().iter("Command"):
        spoken = (cmd.findtext("CommandString") or "").strip()
        if not spoken:
            continue
        blob = ET.tostring(cmd, encoding="unicode").lower()
        if any(mark in blob for mark in _PLUMBING_MARKS):
            continue  # VAICOM/WhisperAttack plumbing, not a user command
        if len(spoken) > 400:
            continue  # keyword-collection monsters
        yield spoken


def refresh():
    """Regenerate custom_commands.txt if a newer .vap export exists. Returns count."""
    vap = _newest_vap()
    if vap is None:
        if not os.path.exists(config.CUSTOM_COMMANDS_PATH):
            log.info("custom commands: no profile export (*.vap) in folder — none loaded")
        return None
    dst = config.CUSTOM_COMMANDS_PATH
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(vap):
        return None  # up to date; normalizer will load the existing file
    try:
        phrases = set()
        spoken_count = 0
        for spoken in _iter_custom_commands(vap):
            spoken_count += 1
            for alt in split_top(spoken):
                for p in expand(alt):
                    phrases.add(p.lower())
        with open(dst, "w", encoding="utf-8") as f:
            f.write(f"# generated from {os.path.basename(vap)} — do not edit; re-export instead\n")
            for p in sorted(phrases):
                f.write(p + "\n")
        log.info("custom commands: %d command(s) → %d phrase(s) from %s",
                 spoken_count, len(phrases), os.path.basename(vap))
        try:  # refresh the flight guide so the new commands appear in it too
            import make_cheatsheet
            make_cheatsheet.main()
            log.info("flight guide rebuilt with your custom commands")
        except (SystemExit, Exception) as e:  # no keywords file yet, etc. — not fatal
            log.warning("flight guide not rebuilt: %s", e)
        return len(phrases)
    except ET.ParseError as e:
        log.error("could not read %s: %s", os.path.basename(vap), e)
        return None
