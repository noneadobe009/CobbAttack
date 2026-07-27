# CobbAttack

**Fast local voice recognition for VoiceAttack / VAICOM / DCS — built for AMD GPUs.**

CobbAttack replaces Windows Speech Recognition (and WhisperAttack's CUDA-only
engine) with [whisper.cpp](https://github.com/ggml-org/whisper.cpp) running on
**Vulkan** — so it's GPU-fast on AMD, NVIDIA, and Intel alike, with automatic
CPU fallback. Hold your push-to-talk, speak, and the recognized command is in
VoiceAttack typically in **50–85 ms** after you release the button.

Named for Cobb, whose AMD card deserved better than silent CPU lag.

> ### 🚀 New here? Two links:
> **[⬇️ Download the latest release](https://github.com/sextonjerome-cmyk/Cobb/releases/latest)** — everything bundled, no Python needed
> **[🛠️ Setup Instruction](https://sextonjerome-cmyk.github.io/Cobb/Setup-Instruction.html)** — the one manual: install is step 1, then a screenshot for every click

## How it works (one breath)

```
VoiceAttack TX button ──► WASC plugin ──► "start"/"stop" on TCP :65432
        ▼
CobbAttack records (16 kHz mono) ──► whisper-server.exe (Vulkan, model stays loaded)
        ▼
normalize: numbers→digits, word fixes, fuzzy firewall vs your command list
        ▼
text ──► TCP :65433 ──► WASC plugin ──► vaProxy.Command.Execute ──► your command fires
```

Drop-in wire-compatible with WhisperAttack's `whisper_server.py` — same ports,
same protocol, same plugin.

## Features

### Recognition
- **whisper.cpp engine, Vulkan build** — one long-lived `whisper-server.exe`,
  model loaded once, HTTP inference per utterance. Never a per-command reload.
- **Resolved device logged loudly at startup** (`Vulkan GPU — AMD Radeon …` or
  `CPU — no Vulkan GPU found`). "Silently slow" is the failure this project
  exists to kill.
- Models: `base.en` default (fast under DCS load), `small.en` opt-in via
  `settings.json`. Quantized ggml preferred.
- Command-and-control decode settings: temperature 0, English pinned, no
  context carry-over, DCS-aware initial prompt (callsigns, airfields).
- Mic pinning: `"input_device": "hyperx"` (any name substring) in
  `settings.json`.

### Cleanup & safety (normalize.py)
- Spoken numbers → digits ("two" → "2" — what VAICOM's profile expects).
- **Word-fix mappings** (`word_mappings.txt`): "boogie doggy" → "bogey dope",
  learned live from the UI, applied instantly.
- **Hallucination firewall**: Whisper invents text on silence ("Thank you.").
  Output must fuzzy-match (rapidfuzz ≥ 85) a phrase in your command list or it
  is dropped and logged — never sent.
- **It tells you *why* it refused.** Every refusal carries a reason (blank audio /
  silence filler / no command close enough / button released too fast), so the
  window can say `✗ NOT A COMMAND — nothing sent` with the closest match and its
  score instead of a shrug.
- **Recipient preservation**: "Two, rejoin" matches recipient + command
  separately and re-joins ("2 rejoin"), so you address one wingman, not the
  whole flight.
- Command lists: VAICOM keyword export (`tools/make_commands.py` →
  `commands.txt` + `recipients.txt`) and/or **your own VoiceAttack profile**
  (drop your `.vap` export in the folder — parsed on every startup).

### The window (ui.py — pure tkinter, nothing to install)
- Status light, live activity feed: `heard` → `sent` with per-utterance
  latency in ms. Honest numbers, not "feels fast".
- **Click a wrong word** in a blue `heard:` line → suggestion popup →
  one-click fix. **Select several words + right-click → Teach fix** for
  two-words-heard-as-one repairs. Right-click → **Clear window**.
- Teach-a-word box: type `it heard` / `should be`, Add — live, no restart.
- 🎯 **Voice Trainer**: profile-verified practice phrases, ✓ auto-advance,
  ✗ one-click TEACH FIX, session score. Nothing is sent to VoiceAttack while
  training. (Rumor has it there's a bonus round.)
- **Refused commands are loud, not silent**: a red `✗ NOT A COMMAND — nothing sent`
  line plus an error beep, the reason underneath, and a clickable **why?** that
  opens the troubleshoot page at the matching explanation.
- **Minimize goes to the system tray** (`tray.py`) — out of the taskbar, still
  listening; left-click the icon to return, right-click for Show/Quit. The X
  button still quits, so the app can't be "lost". No tray library → minimize
  simply behaves the old way.
- 🛠️ **SETUP INSTRUCTION** → the manual; 📖 **FLIGHT VOICE GUIDE** → command
  cheatsheet; 🚑 **TROUBLESHOOT** (red) → live diagnostics page. A rotating
  fighter-pilot joke on every launch.
- **One-click start**: `Start with VoiceAttack.bat` launches VoiceAttack
  (elevated) and CobbAttack together, skipping whatever is already running.
  `Add to Start Menu.bat` makes both shortcuts.

### VAICOM auto-repair (vaicom_patch.py)
CobbAttack re-applies these at every startup (VoiceAttack erases them on each
launch; harmless if VAICOM isn't installed):
- **The mission-restart bug — fixed.** The community-famous "VAICOM works for
  the first mission only, restart DCS to fix" is a Windows UDP socket quirk
  VAICOM trips over. Full story + hand-fix for non-CobbAttack users in
  [VAICOM-mission-restart-bug.md](VAICOM-mission-restart-bug.md). With
  CobbAttack running you can Shift+R freely.
- Device-script repair (`dev_timer` nil / leaked-port bind failures).
- Radio-panel self-heal: socket rebuilds, loop watchdog, stale-state cleanup
  in `initialize()`, unsolicited state pushes so the plugin reconnects after
  mission end (its own 60 s reconnect timer has a null-crash bug).

### Guides & tools
- **SETUP.md / Setup-Instruction.html** — the single manual: install (step 1) through
  VAICOM settings, screenshot per click. Opens automatically on first launch.
  (The separate Install Instruction was folded into it — one manual, one link.)
- **troubleshoot.py** — the 🚑 button: writes `troubleshoot.html` from live state
  (green/red check of engine device, ports, WASC plugin, VAICOM lua patches,
  command list, mic) plus every call this session with the exact refusal reason
  and fix, a "VoiceAttack/VAICOM did the wrong thing" section for problems
  downstream of us, and the log tail. Port checks **bind** rather than connect —
  connecting to :65433 would hand VoiceAttack an empty command.
- `tools/make_cheatsheet.py` — flight-phase command cheatsheet
  (`commands-cheatsheet.html`) with hover tooltips and your custom commands.
- `tools/fake_va.py` + `tools/send_ctl.py` — full test harness, no VoiceAttack
  or DCS needed: fake the plugin, drive start/stop, watch what would fire.
- `tools/selftest.py` — normalizer regression tests.
- `tools/make_zip.py` — builds the distributable zip; `build_exe` PyInstaller
  onedir build with `Add to Start Menu.bat`.
- Kneeboard parity: text starting with `note ` goes to the DCS kneeboard
  (clipboard + Ctrl+Alt+P) instead of VoiceAttack.

## Quick start

- **Users:** [SETUP.md](SETUP.md), or the illustrated
  [Setup-Instruction.html](Setup-Instruction.html) — same guide with a screenshot
  for every click. Installing is step 1; it also opens on first launch.
- **Developers:** `pip install -r requirements.txt`, `python main.py`
  (`--nogui` for console, `--wav file.wav` for a one-shot test). Test without
  VoiceAttack: `python tools/fake_va.py` in one terminal,
  `python tools/send_ctl.py start` / `stop` in another.

## Configuration

`settings.json` next to the app (all optional):

| Key | Default | What |
|---|---|---|
| `model` | `ggml-base.en-q5_0.bin` | any ggml model in `models/` |
| `input_device` | Windows default | mic name substring, e.g. `"hyperx"` |
| `control_port` / `text_port` | 65432 / 65433 | WhisperAttack-compatible ports |
| `dcs_install` | auto-detected | DCS path for the VAICOM patches |

## Credits

- [WhisperAttack](https://github.com/nikoelt/WhisperAttack) — the protocol and
  the WASC VoiceAttack plugin (bundled, MIT).
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) — the engine.
- [VAICOM Community](https://github.com/Penecruz/VAICOM-Community) — VAICOM CE.
- Parlez — sibling dictation project this borrows recorder/glossary patterns from.
