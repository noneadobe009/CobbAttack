# Drop-in protocol (do not break)

CobbAttack must stay a **drop-in replacement** for WhisperAttack's `whisper_server.py`.
Cobb's whole setup path is WhisperAttack's documented VAICOM guide; breaking wire compatibility
breaks that.

- Control **in**, TCP `127.0.0.1:65432`: messages `start` / `stop` / `shutdown` —
  case-insensitive, UTF-8, single recv (≤1024 bytes), **no reply is sent**.
- Text **out**, TCP `127.0.0.1:65433`: raw UTF-8 transcription, no framing, one send,
  close the socket. The receiving WASC plugin runs `vaProxy.Command.Execute(text)`.
- Ports are configurable in `settings.json` but the defaults above must match WhisperAttack's.
- Parity feature: text starting with `note ` goes to the DCS kneeboard (clipboard +
  `Ctrl+Alt+P`) instead of VoiceAttack. Low priority, but don't repurpose the prefix.
- Audio contract: 16 kHz, mono, float32.
