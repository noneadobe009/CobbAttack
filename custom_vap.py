"""Read the user's own voice commands from a VoiceAttack profile export (.vap).

Workflow (documented in SETUP.md "Your own voice commands"): the user exports
their profile as a .vap file into this folder; on every startup we parse the
newest one and regenerate custom_commands.txt. Those phrases join the firewall
allow-list (normalize.py) — without this, a custom command like "turn on the
lights" would be discarded as garbage — and the flight guide shows them in a
"Your custom commands" section (tools/make_cheatsheet.py).

Two .vap formats exist:
- Old VoiceAttack: plain XML.
- Current VoiceAttack (verified against a 2026 v2.1.8 export): a raw-deflate
  stream. Inside, each command record is laid out as
  [table of increasing uint32 offsets][16-byte GUID][uint32 length][spoken
  phrase, UTF-8] followed by action data. The first record is the profile
  itself (its "spoken" string is the profile name). We only need each
  command's spoken phrase plus its record bytes for the plumbing check below.

We keep only commands the user made themselves: anything mentioning VAICOM,
AIRIO, or WhisperAttack — by name or by plugin GUID, which is how the binary
format references plugins — is plumbing, and the giant keyword-collection
entries are VAICOM's, not the user's.
"""

import glob
import logging
import os
import struct
import sys
import zlib
import xml.etree.ElementTree as ET

import config

log = logging.getLogger("cobb.custom")

sys.path.insert(0, os.path.join(config.ROOT, "tools"))
from make_commands import split_top, expand  # noqa: E402  (single source for [a;b] expansion)

# Text marks plus the two plugin ids (VAICOM PRO, WhisperAttack WASC) — the
# binary format stores an "execute plugin" action as a bare GUID with no
# plugin name nearby, so the names alone are not enough there.
_PLUMBING_MARKS = (
    "vaicom", "whisper", "airio",
    "5b433065-dec8-4852-8912-2ff6edf9807f",   # VAICOM PRO plugin
    "1ad02372-145e-4143-bbbe-ac7575595c24",   # WhisperAttack WASC plugin
)


def _newest_vap():
    vaps = glob.glob(os.path.join(config.ROOT, "*.vap"))
    return max(vaps, key=os.path.getmtime) if vaps else None


def _inc_run_before(d, p):
    """How many uint32s form an increasing run ending exactly at byte p."""
    count, prev = 0, None
    while p >= 8 and count <= 200:
        v, = struct.unpack_from("<I", d, p - 4)
        if prev is not None and v >= prev:
            break
        prev = v
        count += 1
        p -= 4
    return count


def _binary_records(d):
    """(start_offset, spoken) for each record in a decompressed binary .vap."""
    records, i, n = [], 0, len(d)
    while i < n - 24:
        # cheap structural check first: an offset table ending right before a
        # GUID; only then try the (possibly large) string decode
        if _inc_run_before(d, i) >= 4:
            length, = struct.unpack_from("<I", d, i + 16)
            if 1 <= length <= 150000 and i + 20 + length <= n:
                try:
                    spoken = d[i + 20:i + 20 + length].decode("utf-8")
                except UnicodeDecodeError:
                    spoken = None
                if spoken and all(ch >= " " or ch in "\t\n\r" for ch in spoken):
                    records.append((i, spoken))
                    i += 20 + length
                    continue
        i += 1
    return records


def _iter_binary_commands(data):
    """Yield (spoken, record_blob_lowercased) from a binary .vap file."""
    d = zlib.decompress(data, -15)
    records = _binary_records(d)
    # records[0] is the profile header (its string is the profile name)
    for k in range(1, len(records)):
        start, spoken = records[k]
        end = records[k + 1][0] if k + 1 < len(records) else len(d)
        yield spoken, d[start:end].decode("latin-1").lower()


def _iter_commands(vap_path):
    """Yield (spoken, blob) for every command, whichever format the file is."""
    with open(vap_path, "rb") as f:
        data = f.read()
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        log.info("%s is a binary export (current VoiceAttack format)",
                 os.path.basename(vap_path))
        yield from _iter_binary_commands(data)
        return
    for cmd in root.iter("Command"):
        spoken = (cmd.findtext("CommandString") or "").strip()
        if spoken:
            yield spoken, ET.tostring(cmd, encoding="unicode").lower()


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
        for spoken, blob in _iter_commands(vap):
            if any(mark in blob for mark in _PLUMBING_MARKS):
                continue  # VAICOM/WhisperAttack plumbing, not a user command
            if len(spoken) > 400:
                continue  # keyword-collection monsters
            spoken_count += 1
            for alt in split_top(spoken):
                for p in expand(alt):
                    phrases.add(p.lower())
        with open(dst, "w", encoding="utf-8") as f:
            f.write(f"# generated from {os.path.basename(vap)} — do not edit; re-export instead\n")
            for p in sorted(phrases):
                f.write(p + "\n")
        # "->" not "→": the frozen exe's console stream is cp1252 and a real
        # arrow crashes the logging handler with a UnicodeEncodeError traceback
        log.info("custom commands: %d command(s) -> %d phrase(s) from %s",
                 spoken_count, len(phrases), os.path.basename(vap))
        try:  # refresh the flight guide so the new commands appear in it too
            import make_cheatsheet
            make_cheatsheet.main()
            log.info("flight guide rebuilt with your custom commands")
        except (SystemExit, Exception) as e:  # no keywords file yet, etc. — not fatal
            log.warning("flight guide not rebuilt: %s", e)
        return len(phrases)
    except (zlib.error, ValueError, OSError) as e:
        log.error("could not read %s: %s", os.path.basename(vap), e)
        return None
