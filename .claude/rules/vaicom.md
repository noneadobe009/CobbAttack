# VAICOM / VoiceAttack integration rules

- VAICOM must run in **VSPX** (single-pass) mode, and VoiceAttack's own speech recognition
  must be **disabled** — otherwise every command fires twice (once from WSR, once from us).
- `vaProxy.Command.Execute` matches by **exact command name**. Our normalizer's job is to output
  exactly a phrase that exists in the VAICOM-generated VSPX profile. The WASC plugin's
  `Command.Exists` check is a second safety net — don't rely on it as the only one.
- **Never forward unmatched/garbage text.** Whisper hallucinates on silence ("Thank you. Thank
  you."). The rapidfuzz firewall (threshold 85) in `normalize.py` is a safety feature, not a
  nicety: below threshold → discard and log, never send.
- VAICOM itself rewrites a leading `"to "` → `"two "` (`requirescorrection`). Don't double-apply
  that fix in `normalize.py`.
- Numeric aliases: since VAICOM 3.0, wingmen etc. already have numerical values — spoken-numbers
  → digits conversion ("two" → "2") is expected by the profile.
- VAICOM → DCS transport (UDP 33491/33492 etc.) is VAICOM's business. We never talk to DCS
  directly except the kneeboard parity feature.
