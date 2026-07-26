# CobbAttack — Install for plain VoiceAttack (no VAICOM)

*This is the short path for using your own VoiceAttack commands. Every step below
is also in **SETUP.html** with screenshots of each click. VAICOM users: follow
SETUP.md instead.*

## 1. Unzip
Unzip `CobbAttack.zip` somewhere simple like `C:\CobbAttack`. **Not** inside
Program Files.

## 2. Install the plugin (one folder copy)
Copy the folder `third_party\WhisperAttackServerCommand` into:

    C:\Program Files (x86)\VoiceAttack\Apps\

No downloads — the plugin is bundled (MIT-licensed, from WhisperAttack).
(Installed VoiceAttack somewhere else? Use its `Apps` folder there instead —
right-click the VoiceAttack shortcut → Open file location to find it.)

## 3. Turn ON plugin support
VoiceAttack → wrench icon (Options) → tick **Enable Plugin Support** → restart
VoiceAttack when it asks.

## 4. Turn OFF VoiceAttack's own speech recognition
Same Options screen. Important — otherwise Windows speech recognition and
CobbAttack both hear you and commands fire twice. Your commands still work;
CobbAttack becomes the ears.

## 5. Wire your talk button
In your profile, add two commands:

| When | Action |
|---|---|
| talk button **press** | *Execute an external plugin function* → **WhisperAttack Server Command** → context: `Start Whisper Recording` |
| talk button **release** | same plugin → context: `Stop Whisper Recording` |

Type the context text **exactly** — a typo fails silently with no error anywhere.

## 6. Add your profile (so your commands are recognized)
In VoiceAttack: profile pencil icon → **Export Profile** → save the `.vap` file
anywhere. Then open the **📖 FLIGHT VOICE GUIDE** (button in the CobbAttack
window) and drag the file onto the drop-box under "Your custom commands" — or
just click the drop-box to pick the file. It's copied into the CobbAttack folder
and your phrases are learned immediately.
**Re-do this after adding new commands** — the symptom of forgetting is
"no matching command" in the CobbAttack window for a command that works when
clicked.

## 7. Start up — order matters
1. VoiceAttack first
2. then CobbAttack (`run-cobbattack.bat`; run `Add to Start Menu.bat` once if
   you want a Start Menu entry)

## 8. Check ONE line
The first line in the CobbAttack window must say:

    Vulkan GPU — AMD Radeon ...

That's the whole point on your machine. If it says **CPU** — stop and tell us,
don't fly like that.

## 9. Test without flying
Hold the talk button, say one of your commands, release. The window shows
`heard:` → `sent`, and VoiceAttack's log shows the command firing.

## 10. Firewall popup
Windows Firewall may ask once → **Allow**. Everything stays on your PC
(127.0.0.1); nothing goes online.

---

## Daily use

- Say a command wrong-word? Click the wrong word in a blue `heard:` line — or
  hold the **left** mouse button and sweep across several words, then
  **right-click** the highlighted text → **Teach fix** — type what it should
  be, press Add. Sticks forever, works immediately.
- Taught something dumb? Right-click the feed → **Undo fix**.
- Right-click the feed → **Clear window**.
- 🎯 **VOICE TRAINER** button: practice phrases scored as heard/missed, with
  one-click fixes. Nothing is sent to VoiceAttack while training.
- Problems? Everything is logged in `cobbattack.log` — send us that file.
