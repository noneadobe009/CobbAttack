# CobbAttack — Install Instruction

*Your own VoiceAttack commands, spoken — fast, local, GPU-powered. Ten steps,
about ten minutes. Using VAICOM for DCS? Use the full
[Illustrated Setup Manual](https://sextonjerome-cmyk.github.io/Cobb/Setup%20Instruction.html)
instead — this page is the quick path for plain VoiceAttack.*

## 🗺️ Before you start — where everything goes

Grab the zip from the
[latest release](https://github.com/sextonjerome-cmyk/Cobb/releases/latest).
There are only two locations to care about:

| What | Where it goes |
|---|---|
| The unzipped **CobbAttack folder** (app, engine, models, guides) | Anywhere simple, e.g. `C:\CobbAttack` — **NOT inside Program Files** |
| One small folder from inside it: `third_party\WhisperAttackServerCommand` | Into **VoiceAttack's** `Apps` folder, usually `C:\Program Files (x86)\VoiceAttack\Apps\` |

That's the whole map: everything lives in your CobbAttack folder, and exactly
**one** plugin folder is copied over to VoiceAttack. Nothing is downloaded,
nothing goes online.

## 1. Unzip
Unzip `CobbAttack.zip` to `C:\CobbAttack` (or any simple folder — just **not**
Program Files, which blocks the app from saving your word fixes).

## 2. Copy the plugin (one folder)
Copy the folder `third_party\WhisperAttackServerCommand` into:

    C:\Program Files (x86)\VoiceAttack\Apps\

(Installed VoiceAttack somewhere else? Right-click your VoiceAttack shortcut →
Open file location → use the `Apps` folder there.)
📸 Screenshots: [Illustrated Manual → Install](https://sextonjerome-cmyk.github.io/Cobb/Setup%20Instruction.html#install)

---

## 🎉 Files installed — now the setup

Everything from here on is **setup**, not installation, and the
[Setup Instruction](https://sextonjerome-cmyk.github.io/Cobb/Setup%20Instruction.html)
covers it in full detail with a screenshot for every click. **Open it now and
follow along there** — the steps below are only the short version for people who
already know VoiceAttack well.

---

## 3. Turn ON plugin support
VoiceAttack → wrench icon (Options) → tick **Enable Plugin Support** → restart
VoiceAttack when it asks.
📸 Screenshots: [Illustrated Manual → VoiceAttack settings](https://sextonjerome-cmyk.github.io/Cobb/Setup%20Instruction.html#va)

## 4. Turn OFF VoiceAttack's own speech recognition
Same Options screen. Important — otherwise Windows speech recognition and
CobbAttack both hear you and commands fire twice. Your commands still work;
CobbAttack becomes the ears.
📸 Screenshots: [Illustrated Manual → VoiceAttack settings](https://sextonjerome-cmyk.github.io/Cobb/Setup%20Instruction.html#va)

## 5. Wire your talk button
In your profile, add two commands:

| When | Action |
|---|---|
| talk button **press** | *Execute an external plugin function* → **WhisperAttack Server Command** → context: `Start Whisper Recording` |
| talk button **release** | same plugin → context: `Stop Whisper Recording` |

Type the context text **exactly** — a typo fails silently with no error anywhere.
📸 Click-by-click: [Illustrated Manual → Buttons](https://sextonjerome-cmyk.github.io/Cobb/Setup%20Instruction.html#buttons)

## 6. Add your profile (so your commands are recognized)
In VoiceAttack: profile pencil icon → **Export Profile** → save the `.vap` file
anywhere. Then open the **📖 FLIGHT VOICE GUIDE** (button in the CobbAttack
window) and drag the file onto the drop-box under "Your custom commands" — or
just click the drop-box to pick the file. Your phrases are learned immediately.
**Re-do this after adding new commands** — the symptom of forgetting is
"no matching command" for a command that works when clicked.

## 7. Start up — order matters
1. VoiceAttack first
2. then CobbAttack (`run-cobbattack.bat`; run `Add to Start Menu.bat` once if
   you want a Start Menu entry)

## 8. Check ONE line
The first line in the CobbAttack window must say:

    Vulkan GPU — AMD Radeon ...

If it says **CPU** — stop and tell us, don't fly like that.

## 9. Test without flying
Hold the talk button, say one of your commands, release. The window shows
`heard:` → `sent`, and VoiceAttack's log shows the command firing.

## 10. Firewall popup
Windows Firewall may ask once → **Allow**. Everything stays on your PC
(127.0.0.1); nothing goes online.

---

## Daily use

- Fix a mishear: click the wrong word in a blue `heard:` line — or drag across
  several words: they land in the teach box together. Type what it should be,
  press Add. Works immediately, remembered forever.
- Taught something dumb? Right-click the feed → **Undo fix**.
- Right-click the feed → **Clear window**.
- 🎯 **VOICE TRAINER**: scored practice, nothing sent to VoiceAttack.
- Stuck? [Illustrated Manual → Troubleshooting](https://sextonjerome-cmyk.github.io/Cobb/Setup%20Instruction.html#trouble),
  and everything is logged in `cobbattack.log` — send us that file.
