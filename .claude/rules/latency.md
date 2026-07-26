# Engine & latency rules

- **AMD is the whole point.** Never add a CUDA or torch dependency. The engine is whisper.cpp
  (`whisper-server.exe` child process, Vulkan build) — Vulkan covers AMD/NVIDIA/Intel; CPU is
  the fallback, chosen automatically, never silently.
- **Log the resolved device loudly at startup** (e.g. `device: Vulkan (AMD Radeon ...)` or
  `device: CPU — no Vulkan GPU found`). "Silently slow" is the exact failure this project
  exists to fix.
- The model stays loaded: one long-lived `whisper-server.exe`, HTTP `/inference` per utterance.
  Never spawn a fresh process per command (model reload costs seconds).
- Whisper's encoder pads every clip to 30 s — short-command latency is a fixed cost per
  utterance, not proportional to clip length. `--audio-ctx` is the big lever for 1–4 s commands;
  benchmark before changing it, and record numbers in the commit/summary.
- Model default is **`base.en`** (fast enough under DCS CPU load); `small.en` is opt-in via
  settings. Quantized ggml (`q5_0`) preferred.
- Decode settings for command-and-control: temperature 0, no context carry-over between
  utterances, English pinned, DCS initial prompt (callsigns/airfields) from the glossary packs.
