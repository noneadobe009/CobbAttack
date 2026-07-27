# CobbAttack — AMD-friendly Whisper voice control for DCS (VAICOM/VoiceAttack)

Replaces Windows Speech Recognition for VAICOM PRO users. A small Python tray app records on
push-to-talk, transcribes locally with whisper.cpp (Vulkan → works on AMD GPUs, CPU fallback),
cleans the text, and feeds it to VoiceAttack through WhisperAttack's existing WASC plugin.
Built for Cobb (AMD GPU), where WhisperAttack's CUDA-only engine silently runs on CPU and lags.

Binding rules live in `.claude/rules/` and load automatically:
`protocol.md` (drop-in wire compatibility), `vaicom.md` (VSPX, exact-match, hallucination
firewall), `latency.md` (engine/device/model rules), `quality.md` (testing gates).

## Talking to me

**Explain things simply, in a few words.** Short plain-English answers, not walls of detail.
Skip the jargon unless I ask. Detail on request, or when the decision is mine (money, deleting
things, hard-to-undo). Don't soften real problems to keep it brief.

## Architecture (one breath)

VoiceAttack TX button → WASC plugin → `start`/`stop` on :65432 → we record 16 kHz mono float32 →
whisper.cpp `whisper-server.exe` child process (HTTP `/inference`, model stays loaded) →
normalize (numbers→digits, glossary, rapidfuzz ≥85 vs command list) → text to :65433 →
`vaProxy.Command.Execute` → VAICOM (VSPX mode) parses → UDP 33491 → DCS.

## File map

- `main.py` — wiring; GUI by default, `--nogui` console, `--wav` one-shot test
- `ui.py` — tkinter window (stdlib on purpose — no extra install for Cobb): status light,
  clickable activity feed, teach-a-word box that calls `Normalizer.add_mapping` live,
  red 🚑 button, and minimize-to-tray
- `tray.py` — system-tray icon (pystray, optional: no library → minimize just uses the
  taskbar). Minimize hides to tray; the X button still quits
- `troubleshoot.py` — builds `troubleshoot.html` on demand: live green/red checks
  (engine, ports, plugin folder, VAICOM lua patches, command list) + every call this
  session with the exact refusal reason. Port checks BIND, never connect — connecting
  to :65433 would hand VoiceAttack an empty command
- `config.py` — settings over `settings.json`
- `engine.py` — whisper-server child process lifecycle + HTTP inference + device detection
- `bridge.py` — the two TCP sockets (WhisperAttack protocol)
- `recorder.py` — sounddevice in-memory capture (pattern from Parlez)
- `normalize.py` — cleanup pipeline + fuzzy firewall; `glossary.py`/`packs.py` — from Parlez
- `tools/fake_va.py`, `tools/send_ctl.py` — test harness (no VoiceAttack needed)
- `bin/` — bundled whisper.cpp binaries (Vulkan build); `models/` — ggml models (not committed)
- `SETUP.md` / `Setup-Instruction.html` (from `tools/make_setup.py`) — **the one manual**;
  installing is step 1 of it. Keep in sync with any protocol/config change. There was a
  separate Install-Instruction; it was merged in on 2026-07-27, don't reintroduce it
- `Start with VoiceAttack.bat` — one-click launcher for VoiceAttack (elevated) + CobbAttack;
  `Add to Start Menu.bat` makes both shortcuts

## Sibling project

Parlez (`../Parlez/`, formerly the `Whisper/` folder) is the dictation app this borrows from
(recorder pattern, glossary packs,
logging/paths conventions). **Don't graft this onto Parlez** — different engine (whisper.cpp vs
faster-whisper), different output path (VoiceAttack socket vs clipboard paste). Copy patterns,
not dependencies.

## References

- VAICOM Community (MIT): https://github.com/Penecruz/VAICOM-Community
- WhisperAttack (protocol + WASC plugin + VAICOM guide): https://github.com/nikoelt/WhisperAttack
- whisper.cpp: https://github.com/ggml-org/whisper.cpp
