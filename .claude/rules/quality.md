# Quality gates

- **Launch after every change.** Watch two things: the startup device line, and one full PTT
  round-trip (start → record → transcribe → normalize → send).
- Test without DCS/VoiceAttack first: `tools/fake_va.py` listens on :65433 and prints what
  would fire; drive the control port with `tools/send_ctl.py start|stop`.
- Any change to protocol, ports, or setup steps must update `SETUP.md` in the same change.
- Before shipping to Cobb: verify end-to-end on this machine (Vulkan runs on NVIDIA too),
  then zip `bin/` + app + `SETUP.md`. Have him confirm his startup log says Vulkan/AMD.
- Report performance honestly: per-utterance latency numbers, not "feels fast".
