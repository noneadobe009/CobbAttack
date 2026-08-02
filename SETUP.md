# CobbAttack — Setup Guide

> **Prefer pictures?** Open `Setup-Instruction.html` — the same guide with screenshots of every
> settings page (the raw images live in `screenshots\`). Rebuild it with
> `python tools\make_setup.py` after editing this file.

Voice recognition for VAICOM that actually uses your AMD graphics card.
It replaces the WhisperAttack server program only — everything else in your
VoiceAttack/VAICOM setup stays the same.

**This is the only manual** — installing is the first section, configuration is the
rest. (There used to be a separate Install Instruction; it was folded in here so
there's one place to look.)

## Where every file goes

Two locations, that's the whole map:

| What | Where it goes |
|---|---|
| The unzipped **CobbAttack folder** (app, engine, models, guides) | Anywhere simple, e.g. `C:\CobbAttack` — **NOT inside Program Files**, which blocks the app from saving your word fixes |
| One folder from inside it: `third_party\WhisperAttackServerCommand` | Into **VoiceAttack's** `Apps` folder, usually `C:\Program Files (x86)\VoiceAttack\Apps\` |

1. Unzip `CobbAttack.zip` to `C:\CobbAttack` (or any simple folder outside Program Files).
2. Copy the plugin folder as above. Installed VoiceAttack somewhere else? Right-click
   your VoiceAttack shortcut → Open file location → use the `Apps` folder there.
3. Optional: run `Add to Start Menu.bat` once. It makes two Start Menu shortcuts —
   **CobbAttack**, and **CobbAttack + VoiceAttack** which starts both in one click.

Nothing is downloaded, nothing goes online.

## What you need installed

1. **VoiceAttack** (paid, voiceattack.com) — you already have it.
2. **VAICOM PRO Community Edition** (free): download the latest release from
   https://github.com/Penecruz/VAICOM-Community/releases (the `.msi`).
   Version 3.x is recommended — it has numeric keywords built in.
3. **The WASC VoiceAttack plugin** — already in the box: copy the
   `WhisperAttackServerCommand` folder from CobbAttack's `third_party\` into
   `C:\Program Files (x86)\VoiceAttack\Apps\` (needs admin). Then VoiceAttack →
   Options → Enable Plugin Support, and restart VoiceAttack.
   (From the WhisperAttack project, MIT license — included. No need to install
   anything else of theirs; CobbAttack replaces their server program.)
4. That's it — **no Python needed**: CobbAttack ships as `CobbAttack.exe`.
   (Antivirus false alarm on the exe? Allow it, or fallback: install Python 3.13
   with "Add to PATH", run `pip install -r requirements.txt`, start with
   `run-cobbattack.bat`.)

Already in the box: the whisper.cpp engine (Vulkan + CPU builds) and the `base.en`
model ship inside `bin\` and `models\` — nothing else to download.

## One-time VoiceAttack / VAICOM settings

These come from WhisperAttack's own VAICOM guide
(https://github.com/nikoelt/WhisperAttack/blob/main/VAICOM%20PRO/VAICOM_INTEGRATION.md):

0. Fresh VAICOM install? Start VoiceAttack once (as admin) so VAICOM creates its
   files. If the "VAICOM PRO for DCS World" profile isn't in VoiceAttack's list,
   import it from `C:\Program Files (x86)\VoiceAttack\Apps\VAICOMPRO\Profiles\`.
   Then fill the keywords once: VAICOM EDITOR tab → FINISH → paste into
   AI Communications (the "Teach it" section explains the paste).

1. VAICOM config → Preferences → speech processing mode = **VSPX**.
   Also tick **"Extended Command Set"** — without it VAICOM silently ignores many
   common commands ("request taxi to runway" included) and only logs a quiet
   orange line about it. This one cost us hours.
2. VoiceAttack → Options → **disable speech recognition** (otherwise every
   command fires twice). Easiest: run VoiceAttack with the `-nospeech` shortcut
   option, or untick the recognition options in Settings.
3. In the VAICOM profile, each TX button (press) must have as its FIRST action:
   Other → Advanced → Execute an External Plugin Function → WASC → context `Start Whisper Recording`,
   and on release: `Stop Whisper Recording`. (WhisperAttack's guide shows this
   with screenshots — if you had WhisperAttack working before, this is already done.)
   **Repeat for EVERY TX button you use** (TX1, TX2, and any more): press AND release
   each need both the WASC action and the VAICOM ptt action — a TX with only the
   VAICOM action will key the radio but never hear you.

## Known-good VAICOM settings (Community 3.1.5.2, verified working 2026-07-25)

Open the VAICOM window (say nothing — just click the VoiceAttack log line "VAICOM PRO
Config" or press LCtrl+LAlt+C). Tabs across the top. Tick EXACTLY these; leave
everything else unticked/default.

**Preferences (PREFS)**
- ✅ VSPX Processing
- ✅ **Extended Command Set** ← the big one; without it ATC ignores you (see above)
- ✅ UI Sounds
- ✅ Use Audio Cues
- ✅ Require Engage Cue
- ✅ Allow Options
- Everything else on this page: unticked. (Force Speech / Force Callsigns /
  Force ATC Names all OFF.)

**MP**
- ✅ Use with Multiplayer
- ✅ SRS Integration
- ✅ SRS PTT Mapping — heads-up: this makes the PTT page label the keys
  "TX1 - SRS 1, TX2 - SRS 2, TX3 - SRS 3". That's normal. In the Hornet
  TX1 is still radio 1 (COMM1) and TX2 is radio 2 (COMM2).
- Everything else: unticked.

**EX**
- ✅ Crew Messages ("Hints Only" unticked)
- ✅ F-14 Mini Wheel
- ✅ Carrier Comms (under REALISTIC ATC; "Suppress Auto" unticked)
- ✅ Deep Interrogate (under AOCS)
- ✅ Chatter: Enable, Theme (AUTO), "Auto-start" unticked
- ✅ DCS Kneeboard: Enable ("Auto Browse" unticked)
- Everything else: unticked.

**OKB Out** — all unticked (OpenKneeboard not used).

**Config** — all unticked; sliders on **Standalone** and **Combined/Stable**.
(If DCS is somewhere unusual, that's where "Use custom DCS path" lives.)

**Audio** — leave everything at defaults.

**Editor** — only used when rebuilding keywords (the FINISH button). Not a settings page.

**Reset** — do not touch anything here. The yellow **MASTER ZERO** button wipes
your whole VAICOM setup.

Which push-to-talk buttons to bind (Hornet, single player — 2 is plenty):
- **TX1** = radio 1: ATC, AWACS, tanker — and ground crew works here too.
- **TX2** = radio 2: your wingmen.
- TX5 is a dedicated ground-crew/intercom key if you ever want a third button.
  TX3 (FM/JTAC) doesn't exist in the Hornet, TX6 isn't a radio, and TX4 (AUTO)
  we skip.

## Known-good VoiceAttack settings (v2.1.8, verified working 2026-07-25)

Only these matter — everything not listed stays at its default.

**Options → General**
- ✅ Enable Plugin Support (restart VoiceAttack after first enabling)
- Load Profile on Startup = **your VAICOM profile** (so restarts never load the wrong one)
- Joystick Options → your stick/throttle assigned as Joystick 1 and **enabled**
  (the game-controller icon in the main window toggles joysticks — if buttons
  suddenly do nothing anywhere, you probably clicked it; click it again)

**Options → Recognition**
- Unrecognized Speech Delay = **700** (VAICOM's VSPX recommendation)
- ✅ **Disable Speech Recognition** — CobbAttack does the listening, not Windows.
  The red "Listening is currently disabled" note is CORRECT, not an error.

**Options → Hotkeys** — everything Disabled (buttons come from the profile, not here).

**Options → Audio** — defaults; pick nothing special.

**Options → System / Advanced**
- "Run VoiceAttack as an Administrator": tick it, restart, and check it stuck.
  If VoiceAttack still doesn't elevate (no UAC prompt on launch), use the registry
  fallback: set `HKCU\...\AppCompatFlags\Layers` → VoiceAttack.exe → `~ RUNASADMIN`.
  Admin matters: without it VAICOM can't create its files and nothing works.

## Running it

0. Microphone first: CobbAttack listens to your Windows **default** microphone —
   set your headset as the default input device in Windows Sound settings (or put
   part of its name in `"input_device"` in `settings.json`). And in DCS:
   OPTIONS → GAMEPLAY → **Easy Communication**: ON = calls just work; OFF works
   too, but you must tune each radio to the right frequency yourself.
1. Start VoiceAttack (with your VAICOM profile).
2. Double-click `CobbAttack.exe` (fallback: `run-cobbattack.bat` with Python).
   Or use the **CobbAttack + VoiceAttack** shortcut (`Start with VoiceAttack.bat`):
   it starts VoiceAttack elevated, waits for it to load, then starts CobbAttack —
   and skips anything that's already running, so no needless admin prompt.

   **🔗 Linked or separate?** The checkbox at the bottom of the CobbAttack window —
   **"Start & close VoiceAttack together with CobbAttack"** — decides how the two
   apps live:
   - **Ticked**: starting CobbAttack also starts VoiceAttack (one admin prompt),
     and closing either one closes the other.
   - **Unticked (default)**: they are fully independent. Start and close each one
     yourself, in any order — the right choice if you launch your apps from your
     own script or in a fixed order.
3. **Look at the first lines of the window.** You want:
   `>>> DEVICE: Vulkan GPU — AMD Radeon ... <<<`
   If it says `CPU — no GPU acceleration`, tell us — that's the exact problem
   this exists to fix, and it should not happen on your card. Update your AMD
   drivers (Adrenalin) if it does.
4. Press your PTT in DCS, speak normally ("Chief, request launch", "Texaco,
   Enfield 1-1, request refuel"), release. The window shows what it heard,
   what it cleaned it up to, and the time it took.

## Daily use — the buttons and the tray

- **Minimize goes to the system tray.** The window leaves the taskbar and becomes a
  corn icon by the clock, still listening. Left-click it to bring it back;
  right-click for Show / Quit. The **X** button still quits.
- **🚑 TROUBLESHOOT** (red button) — builds `troubleshoot.html` from live state and
  opens it: a green/red check of everything that must be true right now, plus every
  call this session with the exact reason anything was refused. Start here when
  something's wrong.
- **📖 FLIGHT VOICE GUIDE** — every phrase your profile knows, plus the `.vap` drop-box.
- **🎯 VOICE TRAINER** — scored practice; nothing reaches VoiceAttack while it runs.

**"✗ NOT A COMMAND — nothing sent"** (red line + a beep) means it heard you and
refused to guess. The line below says why: no speech in the clip, or nothing in your
profile is close enough — with the closest match and its score against the threshold.
Click **why?** on that line to open the troubleshoot page.

## Teach it the real VAICOM commands (recommended)

With this done, CobbAttack only ever sends phrases that actually exist in your
VAICOM profile — near-misses get corrected, garbage gets dropped.

1. In VoiceAttack, open your VAICOM profile with the ✏️ pencil (edit) icon next to
   the profile name and double-click the **AI Communications** command
   (Keyword Collections).
2. Click in the big "When I say" box, press **Ctrl+A** then **Ctrl+C**,
   then Cancel out (change nothing).
3. Paste the clipboard into a file called `vaicom_keywords.txt` in the
   CobbAttack folder (Notepad → Ctrl+V → save with that exact name).
4. Restart CobbAttack — it notices the new file and rebuilds its command list
   automatically (log: `commands.txt rebuilt` and `... command phrases` with a
   big number). No Python needed.

Copying OUT vs pasting IN — don't mix them up: the steps above only COPY the list
out (that's why you Cancel — nothing changes). The one time you PASTE is after
rebuilding keywords in VAICOM's EDITOR tab (FINISH): then open AI Communications,
Ctrl+A, Ctrl+V the new list in, and click OK (not Cancel). If the paste is empty,
FINISH's clipboard copy failed (it often does) — the list is also saved at
`C:\Program Files (x86)\VoiceAttack\Apps\VAICOMPRO\Export\keywords.txt`.
After any rebuild, redo the copy-out steps so CobbAttack learns the new list too.
Note: plain "request taxi" is not a real VAICOM phrase — the full ones are
things like "request taxi to runway". The window shows what was matched.

## Your own voice commands (optional)

Made your own VoiceAttack command — like "turn on the lights" flipping a cockpit
switch? Two clicks and CobbAttack learns it:

1. Build the command in your VAICOM profile as usual (Edit Profile → New Command).
2. VoiceAttack main window → profile menu → **Export Profile** → save the `.vap`
   **into the CobbAttack folder** (overwrite the old one each time).
3. Restart CobbAttack — the log says `custom commands: N command(s) ...`.

Your phrases now pass the firewall (otherwise they'd be discarded as mishears),
and the flight guide automatically lists them under
"Your custom commands". Re-export after every new command — if a spoken command
gets "no matching command" but works when clicked, you forgot to re-export.

## If a word keeps coming out wrong

Easiest: in the CobbAttack window, click the wrong word in a blue `heard:` line
and pick a fix. If it turned one word into *two* (like "boat key" for "bogey"),
**drag across both wrong words** — they land in the teach box as one phrase;
type what it should be and press Add. Takes effect immediately, and the feed
confirms every Add (including "already taught").

Right-click in the feed also gives you **Undo fix** (takes back the last thing
you taught) and **Clear window**.

Hand-editing works too: open `word_mappings.txt`, add a line like
`miss heard thing -> right thing`, save, restart CobbAttack.

## Better accuracy (optional)

The default model is `base.en` (fast). For a bit more accuracy, download
`ggml-small.en.bin` from https://huggingface.co/ggerganov/whisper.cpp/tree/main
into the `models` folder and set `"model": "ggml-small.en.bin"` in
`settings.json`. On your GPU it will still be fast.

## Troubleshooting

**Press 🚑 TROUBLESHOOT in the app first** — it checks all of this live against your
own machine and explains every call you've made this session. The list below is the
short reference.

- **"NOT A COMMAND" on a real command** → the phrase isn't in the list CobbAttack
  learned. VAICOM command → redo the keyword export. Your own command → re-export
  your profile. The 🚑 page shows the closest match and how far off the score was.
- **"NOT A COMMAND" on everything, blank audio** → the microphone isn't being
  captured: wrong default input device, muted mic, or the button released too early.
- **Window vanished** → you minimized it; it's the corn icon by the clock.
- **Nothing happens on PTT** → VoiceAttack running? WASC plugin installed and
  enabled (VoiceAttack → Options → Enable plugin support)? TX buttons have the
  Start/Stop actions?
- **Commands fire twice** → VoiceAttack's own speech recognition is still on.
- **`could not reach VoiceAttack plugin`** in the window → VoiceAttack isn't
  running, or the WASC plugin didn't load.
- **It hears you badly / wrong mic** → CobbAttack uses the Windows default
  microphone; set your headset as default input, or set `"input_device"` in
  `settings.json`.
- **Windows Firewall pops up** → allow it; everything stays on this PC (127.0.0.1).
- Everything it does is logged in `cobbattack.log` — send us that file if stuck.
- The startup lines about "VAICOM ... fix" are CobbAttack auto-repairing several
  VAICOM bugs — including the famous one where **radios die after a mission
  restart (Shift+R) until you restart DCS**. That one is fixed for real (a
  Windows socket quirk VAICOM trips over; full story in
  `VAICOM-mission-restart-bug.md`). Automatic — CobbAttack re-applies the repair
  within seconds whenever VoiceAttack starts (VoiceAttack erases it each time).
  Only rule: **start DCS last**, after CobbAttack is up. You can restart missions
  freely.
- **"DCS is not connected" that won't go away**: with everything else still
  running, restart DCS **completely** (not Shift+R). Universal reset if truly
  stuck: close everything, start VoiceAttack and CobbAttack (either order), DCS
  last. (With CobbAttack's patches this should basically never happen anymore —
  if it does, tell us.)
