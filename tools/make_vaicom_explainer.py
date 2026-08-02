"""Build vaicom-explainer.html — the interactive "what does this checkbox do?" page.

Screenshots of all ten VAICOM config-window tabs (screenshots/vaicom/) become
hover maps: move the mouse over any control and a panel underneath explains it
in plain English. Explanations are condensed from the official VAICOM PRO
Community User Manual (3.1.5.x, "The Configuration Window" chapters); the
"Our setup:" tags mirror what SETUP.md step 4 tells Cobb to tick.

    python tools/make_vaicom_explainer.py   -> vaicom-explainer.html

The Setup Instruction links here from section 4 — this page deliberately stays
out of the setup flow itself: setup says WHICH boxes, this page explains WHY.
"""

import base64
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "screenshots", "vaicom")
DST = os.path.join(ROOT, "vaicom-explainer.html")


def data_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


ON = '<span class="rec on">Our setup: ON</span>'
OFF = '<span class="rec off">Our setup: OFF</span>'
INFO = '<span class="rec info">Informational — nothing to set</span>'

# Each spot: (x%, y%, w%, h%, label, explanation-html)
TABS = [
 ("ptt", "PTT", "01-ptt.png",
  "The radio panel: shows which TX button talks on which radio for the aircraft "
  "you're flying. You mostly just LOOK at this page — the actual TX buttons are "
  "bound in VoiceAttack.",
  [
   (17, 24, 11, 22, "Up / Down buttons",
    "For aircraft with only ONE real mic button: choose which TX slot that single "
    "button should use. Ignored for jets with multiple radios." + INFO),
   (28, 23, 52, 26, "Main display",
    "The green screen shows the detected aircraft, whether DCS Easy Communication "
    "is ON or OFF, and the current PTT mode. \"None Detected\" just means DCS isn't "
    "in a mission yet." + INFO),
   (82, 33, 12, 18, "CHATTER volume",
    "Volume knob for the background radio-chatter extension (if you enabled Chatter "
    "on the EX tab)."),
   (19, 54, 16, 30, "PTT mode dial",
    "How radios map to your TX buttons. <b>NORM</b> (default): aircraft with several "
    "radios use several TX buttons, single-radio aircraft use one. <b>MULTI</b>: force "
    "separate buttons even in single-radio aircraft. <b>SNGL</b>: force everything onto "
    "one button. <b>INV</b>: both swaps at once. Leave on NORM unless you know why."),
   (36, 52, 19, 32, "TX1–TX6 list",
    "What each TX button currently talks on. The standard logic: TX1 = VHF AM (ATC, "
    "AWACS, tanker), TX2 = UHF, TX3 = VHF FM (JTAC), TX4 = AUTO (picks the right radio "
    "— only works with Easy Comms ON), TX5 = intercom (ground crew), TX6 = AUX for "
    "your own non-VAICOM commands. \"— —\" means that slot is unused. With SRS "
    "mapping on it shows SRS 1/2/3 instead — that's normal." + INFO),
   (66, 51, 10, 12, "RLY light",
    "Lights up in multiplayer when your voice is being forwarded to human players "
    "over SRS or Voice Chat." + INFO),
   (65, 64, 12, 21, "REL / HOT switch",
    "\"Release Hot\" keeps VoiceAttack listening even after you let go of the TX "
    "button — only useful if you run extra non-VAICOM profiles (cockpit commands "
    "without PTT). Leave on REL." + OFF),
   (78, 59, 11, 17, "DIAL (OPER / MAN)",
    "For helicopters with a radio-selector dial and Easy Comms OFF: OPER lets VAICOM "
    "turn that dial for you automatically, MAN means you turn it yourself in the "
    "cockpit."),
   (15, 80, 9, 12, "SRS button",
    "Switches the TX slots to Simple Radio Standalone's radio order (TX1 = SRS radio 1, "
    "and so on), so VAICOM and SRS can share the same buttons in multiplayer." + ON),
  ]),

 ("prefs", "Preferences", "02-preferences.png",
  "The famous checkbox wall. Hover each one — the ticks in this screenshot are "
  "exactly what the CobbAttack setup wants.",
  [
   (17, 29, 32, 7, "VSPX Processing",
    "Single-pass speech processing: your whole sentence is recognized in one go "
    "instead of word-by-word. <b>CobbAttack requires this ON</b> — the whole app "
    "sends complete phrases." + ON),
   (17, 36, 32, 7, "Use Voice Access",
    "Would use Windows Voice Access for keyword training instead of Windows Speech "
    "Recognition. Disabled by the developers for now — you can't tick it."),
   (17, 42, 32, 7, "Extended Command Set",
    "<b>The big one.</b> Unlocks VAICOM's full command list — far more than the DCS "
    "menus show — and lets commands cross aircraft (JTAC everywhere, for example). "
    "Without it VAICOM understands you and then silently drops the command." + ON),
   (17, 49, 32, 7, "Select Tunes Radio",
    "Makes the \"Select\" voice command also tune the radio to the recipient you "
    "selected, even when Easy Comms is OFF."),
   (17, 56, 32, 7, "Instant Select",
    "With Easy Comms ON: just saying a recipient's name (\"Texaco...\") switches to "
    "them immediately — no separate \"Select\" command needed."),
   (17, 62, 32, 7, "Import F10 Menu",
    "Turns the mission's F10 (Other) menu items into voice commands. Tick it, fly the "
    "mission once, then run the Keywords Editor FINISH steps — items appear as "
    "\"Action …\" commands."),
   (20, 69, 29, 7, "Force Speech",
    "Forces English comms in every aircraft, even Russian ones (or vice versa)." + OFF),
   (20, 75, 29, 7, "Force Callsigns",
    "Always use NATO-style callsigns (\"Springfield\") or numeric Russian-style "
    "(\"100\") — pick with the little NATO/RUS switch underneath." + OFF),
   (20, 82, 29, 7, "Force ATC Names",
    "Some Russian modules use their own ATC names for the Caucasus map. This forces "
    "standard NATO tower names everywhere. VAICOM defaults it ON; our checklist "
    "leaves the Force row alone." + OFF),
   (50, 29, 32, 7, "UI Sounds",
    "VAICOM's little confirmation beeps. Turning them off means no feedback at all — "
    "advanced users only." + ON),
   (50, 36, 32, 7, "Use Audio Cues",
    "Extra feedback sounds — for example when you call someone who isn't available, "
    "or use the wrong radio with Easy Comms ON." + ON),
   (50, 42, 32, 7, "Disable Player Voice",
    "Silences the in-game pilot voice so you don't hear a robot repeat what you just "
    "said. Recommended for realism — your call, though."),
   (50, 49, 32, 7, "Disable PTT Static Hint",
    "Removes the little radio-static noise that tells you VAICOM is transmitting."),
   (50, 56, 32, 7, "Use Appendices",
    "Lets Engage commands carry extras: \"Two, engage artillery <i>with guns from the "
    "east</i>\". Unticked, the extras are ignored."),
   (50, 62, 32, 7, "Require Engage Cue",
    "You must actually say \"Engage / Attack / Strike\" to send your flight at a "
    "target. Unticked, merely mentioning \"air defences\" can launch an attack — "
    "keep this ON as a safety." + ON),
   (50, 69, 32, 7, "Disable Menus",
    "Hides every on-screen comms menu for maximum immersion. Advanced users."),
   (50, 75, 32, 7, "Allow Options",
    "Lets you say \"Options\" to pop up the menu for a recipient and see what you can "
    "say right now. Great while learning." + ON),
   (50, 82, 32, 7, "Hide On-Screen Text",
    "No text briefings or messages on screen at all (needs a DCS restart)."),
  ]),

 ("mp", "MP", "03-mp.png",
  "Multiplayer: how VAICOM behaves online and how it cooperates with SRS and "
  "DCS Voice Chat.",
  [
   (17, 39, 31, 7, "Use with Multiplayer",
    "Master switch: VAICOM works in multiplayer at all." + ON),
   (17, 45, 31, 7, "Display Info",
    "Shows on-screen info about the human players on your selected frequency."),
   (17, 52, 31, 7, "AOCS",
    "Keeps the Crystal Palace AOCS unit (briefing / status / interrogate) available "
    "in multiplayer too."),
   (17, 58, 31, 7, "SRS Integration",
    "Lets VAICOM automatically control SRS's mic listening state, so the two don't "
    "talk over each other." + ON),
   (17, 64, 31, 7, "SRS PTT Mapping",
    "Maps TX buttons in SRS's radio order — recommended whenever you use SRS. This is "
    "why the PTT page shows \"SRS 1/2/3\"." + ON),
   (17, 71, 31, 7, "VoiceChat Integration",
    "Same as SRS Integration but for DCS's built-in Voice Chat."),
   (17, 77, 31, 7, "VoiceChat Open Mic",
    "Keeps the Voice Chat mic permanently open, regardless of PTT."),
   (49, 37, 34, 17, "VoIP Control slider",
    "How your voice reaches humans vs the AI: Broadcast Parallel sends to both at "
    "once; TX Link enables the Switch/Auto-Switch options below; Dynamic Switching "
    "changes over automatically."),
   (49, 56, 34, 7, "Use Switch Command",
    "Keep holding PTT after an AI call and say \"Switch\" — your mic hands over to "
    "SRS/Voice Chat until you release the button."),
   (49, 62, 34, 6, "Auto Switch",
    "Same, but automatic: once the AI command is recognized, keep holding PTT and "
    "you're talking to humans."),
   (52, 68, 31, 6, "Ignore Select",
    "Don't auto-switch to VoIP right after a \"Select\" command."),
   (49, 74, 34, 7, "Hold AI Transmission",
    "Delays the AI message until you release PTT — makes AI replies time better when "
    "you're also talking to humans."),
   (49, 81, 34, 7, "Sound Notification",
    "Plays a sound whenever your mic is actually audible to human players."),
  ]),

 ("ex", "EX", "04-ex.png",
  "Expansions: AI crew, carrier comms, the AOCS briefing unit, background chatter, "
  "and the built-in kneeboard.",
  [
   (9, 39, 27, 7, "Crew Messages",
    "Shows on-screen confirmations and hints for AI crew-member voice commands "
    "(Jester, George, WSO…)." + ON),
   (13, 45, 23, 7, "Hints Only",
    "Limits those messages to incomplete commands only — just usage hints." + OFF),
   (9, 52, 27, 7, "Use ICS Hot Mic",
    "Intercom hot-mic to your AI crew — set it from inside the cockpit. Note: open "
    "mic can make recognition less reliable."),
   (9, 58, 27, 7, "Hide F-4E Dialog",
    "Removes Jester 2.0's contextual dialog window in the F-4E."),
   (9, 65, 27, 7, "F-14 Mini Wheel",
    "A cleaner, smaller Jester wheel for the F-14. ⚠️ Breaks the integrity check on "
    "multiplayer servers that require pure client scripts — since 3.1.5.3, unticking "
    "it properly restores pure-client mode." + ON),
   (12, 76, 24, 7, "Suppress Auto",
    "Carrier comms: stops the sim's automatic pilot radio messages." + OFF),
   (12, 82, 24, 7, "Carrier Comms",
    "Enables the realistic aircraft-carrier communications set (CASE recoveries, "
    "Marshal, Paddles…)." + ON),
   (40, 39, 24, 7, "Auto Brief",
    "AOCS reads the mission briefing out loud automatically at mission start."),
   (40, 45, 24, 7, "Concise",
    "AOCS reads only the briefing summary instead of the whole thing."),
   (40, 52, 24, 7, "Deep Interrogate",
    "Single-player: \"Interrogate\" returns detailed unit data with range, bearing and "
    "altitude." + ON),
   (40, 64, 24, 7, "Chatter: Enable",
    "Background radio chatter for atmosphere. Volume is the CHATTER knob on the PTT "
    "page." + ON),
   (40, 70, 26, 7, "Req Radio On & Freq",
    "Chatter only plays when a UHF radio is on and tuned to 281.0 — detune and it "
    "goes quiet."),
   (40, 76, 24, 7, "Auto-start",
    "Chatter starts by itself when the aircraft connects (or when the frequency rule "
    "above is met)."),
   (44, 81, 28, 8, "Theme",
    "Which chatter sound pack plays. AUTO picks one matching your aircraft." + ON),
   (66, 39, 18, 7, "Kneeboard: Enable",
    "VAICOM's own kneeboard extension (needs VoiceAttack AND DCS restarted). "
    "⚠️ Same pure-client-scripts warning as the Mini Wheel." + ON),
   (71, 45, 8, 40, "BRT / DIM slider",
    "Kneeboard transparency in display mode (does nothing in VR)."),
   (80, 47, 15, 7, "Auto Browse",
    "Kneeboard flips to the right category tab by itself when you call a recipient."),
  ]),

 ("okb", "OKB Out", "05-okb-out.png",
  "OpenKneeboard integration — only relevant if you use the separate OpenKneeboard "
  "app (mostly VR pilots). Our setup leaves this whole page off.",
  [
   (11, 40, 14, 8, "Enable",
    "Starts the OpenKneeboard OUT connection and its web dashboard, and creates the "
    "Vaicom plugin inside OpenKneeboard." + OFF),
   (14, 49, 14, 10, "OKB Broadcast Port",
    "The network port the kneeboard data broadcasts on (default 7779). Only change it "
    "if something else is using that port."),
   (11, 59, 18, 8, "Auto Browse",
    "Voice commands automatically select the matching tab in OpenKneeboard."),
  ]),

 ("config", "Config", "06-config.png",
  "Local PC setup: where DCS lives and how VAICOM keeps its database in sync. "
  "Normally everything here stays unticked.",
  [
   (18, 39, 33, 7, "Run in debug mode",
    "Extra detail in the VoiceAttack log plus a logfile in the Logs folder. Turn on "
    "only while hunting a reproducible problem, then off again." + OFF),
   (18, 45, 30, 8, "Use custom DCS path",
    "VAICOM normally finds DCS through the Windows registry. If it can't (or installs "
    "its lua into the wrong copy of DCS), tick this, press SET, and point it at your "
    "DCS World root folder — the folder, not the .exe." + OFF),
   (52, 44, 24, 9, "Path field + SET",
    "The custom DCS folder you picked. SET opens the browse dialog."),
   (81, 44, 13, 9, "fix Reg",
    "For standalone DCS with a broken registry path: writes the corrected path back "
    "into the registry."),
   (18, 52, 33, 7, "Auto-import new theater",
    "New maps: VAICOM scans for their ATCs and adds them to the keyword database so "
    "you can call the new airfields."),
   (18, 58, 33, 7, "Auto-import new modules",
    "Unknown aircraft modules get added to VAICOM's database automatically."),
   (18, 65, 35, 7, "Manage DCS-side files manually",
    "You install VAICOM's lua files into DCS yourself instead of letting the plugin "
    "do it. Leave off." + OFF),
   (63, 53, 31, 8, "Standalone / Steam slider",
    "Which kind of DCS install you have. Our setup: <b>Standalone</b>."),
   (63, 63, 31, 8, "Combined/Stable / OpenBeta slider",
    "Which DCS version branch. Our setup: <b>Combined/Stable</b>."),
   (41, 71, 12, 9, "EXPORT",
    "Writes the keywords export (keywords.txt) that CobbAttack's step 7 reads to "
    "learn every valid phrase."),
  ]),

 ("audio", "Audio", "07-audio.png",
  "Sound redirection: send VAICOM's own sounds (squelch, AOCS voice, chatter) to a "
  "specific speaker/headset. Our setup leaves it OFF — DCS's own audio settings "
  "handle device routing now.",
  [
   (26, 34, 47, 8, "Output device list",
    "Which audio device VAICOM's sounds go to when redirection is on. Not "
    "plug-and-play: restart VoiceAttack after plugging in new devices."),
   (79, 33, 10, 13, "REDIR light",
    "Green = the chosen device initialized fine. Blinking = it didn't; pick another "
    "device." + INFO),
   (28, 46, 36, 28, "PAN sliders (TX1–TX6)",
    "Left/right stereo placement per radio, so each radio sits in a different ear."),
   (28, 71, 36, 12, "AOCS / CHTR sliders",
    "Same panning for the AOCS voice and the chatter track (VAR = random)."),
   (66, 51, 10, 14, "ADJ knob",
    "Permanently greyed out since DCS 2.5.6 — audio routing for comms moved into "
    "DCS's own Audio options." + INFO),
   (67, 66, 10, 14, "INIT",
    "Re-initializes the selected audio device if redirection glitches."),
   (79, 51, 12, 29, "OPER / OFF switch",
    "Master switch for the whole redirect feature. OFF = bypassed, everything "
    "normal." + OFF),
  ]),

 ("editor", "Editor", "08-editor.png",
  "The keywords database — advanced territory. CobbAttack only needs one thing "
  "from this page: after any keyword change, press FINISH and re-paste into the "
  "VoiceAttack profile (setup step 7).",
  [
   (14, 36, 11, 10, "Keyword counter",
    "Total keywords (phrases/aliases) in the database — around 2200+ by default." + INFO),
   (26, 34, 32, 14, "category / segment",
    "Which command segment and category the selected phrase belongs to." + INFO),
   (80, 36, 11, 14, "TEST",
    "Speak-test the selected keyword without DCS."),
   (38, 52, 38, 8, "Command phrase list",
    "Every voice phrase VAICOM knows, alphabetically. Pick one to inspect or edit it."),
   (77, 51, 13, 9, "ALIAS cycle",
    "The number shows how many alternative phrases trigger the same command "
    "(Engage / Attack / Strike…). Click to cycle through them."),
   (13, 66, 9, 16, "VSPX light",
    "Green when VSPX single-pass mode is active — it should be, for CobbAttack." + INFO),
   (24, 62, 10, 22, "Microphone icon",
    "Keywords Training Mode: opens Windows Speech Recognition loaded with only "
    "VAICOM's phrases so you can train them one by one. Not needed with CobbAttack — "
    "Whisper doesn't use Windows voice training."),
   (38, 62, 45, 10, "ADD NEW · DELETE · REVERT · APPLY",
    "Database editing: add your own phrase, delete one, undo, or apply the change."),
   (38, 73, 34, 10, "RELOAD · EXPORT",
    "RELOAD refreshes the list and counter. EXPORT writes the keywords to a .csv and "
    "an HTML reference document."),
   (62, 73, 21, 10, "FINISH / CANCEL",
    "<b>The step everyone forgets:</b> FINISH copies the updated keyword list to the "
    "clipboard. Then: edit the VoiceAttack profile (pencil icon) → Keyword Collections "
    "command → clear \"When I say\" (Ctrl+A, Delete) → paste (Ctrl+V) → OK. Skip this "
    "and your keyword edits never reach VoiceAttack."),
  ]),

 ("help", "Help", "09-help.png",
  "Support shortcuts — nothing here changes any setting.",
  [
   (25, 36, 50, 12, "Community Discord",
    "The VAICOM Community Discord — where the plugin's developers and users hang "
    "out." + INFO),
   (11, 57, 28, 9, "Press for diagnostics",
    "Runs a diagnostics check for support purposes."),
   (11, 68, 30, 9, "Press for Vaicom Log File",
    "Opens VAICOM's own log file (CobbAttack's log is separate — 🚑 button)."),
   (60, 57, 31, 9, "Press for PDF Manual",
    "Opens the full 70-page VAICOM manual — this page is the short version."),
   (60, 68, 33, 9, "Press for YouTube Tutorials",
    "Video tutorials for VAICOM."),
   (60, 79, 31, 9, "Press for Keywords",
    "Opens the formatted keywords reference — every phrase VAICOM can hear."),
  ]),

 ("reset", "Reset", "10-reset.png",
  "⚠️ The factory-reset page. You should never need this — and NEVER press MASTER "
  "ZERO casually: it erases what you tick on the left.",
  [
   (16, 34, 20, 7, "Keywords",
    "Reset the keywords database to factory defaults."),
   (16, 40, 20, 7, "Imported",
    "Remove keywords you imported (F10 menus, custom additions)."),
   (16, 46, 20, 7, "Settings",
    "Reset every preference and configuration setting."),
   (16, 52, 20, 7, "Profile",
    "Reset the VoiceAttack profile (.vap)."),
   (16, 58, 20, 7, "Theme",
    "Reset the DCS theme."),
   (16, 64, 20, 7, "Lua code",
    "Reinstall VAICOM's lua files in DCS. Note: CobbAttack re-applies its own lua "
    "fixes automatically afterwards, so this is safe with CobbAttack running."),
   (40, 33, 19, 38, "Warning triangle",
    "It means it. A reset can't be undone." + INFO),
   (69, 40, 11, 19, "MASTER ZERO",
    "Executes the reset for everything ticked on the left, then requires a "
    "VoiceAttack restart. To fully uninstall VAICOM: tick everything, reset, close "
    "VoiceAttack, delete the VAICOMPRO folder from Apps."),
   (16, 70, 52, 18, "Instructions text",
    "The FINISH / re-paste procedure for keyword edits — same steps as on the Editor "
    "tab." + INFO),
  ]),
]

CSS = """
 :root { --bg:#14181d; --panel:#1c2229; --field:#242c35; --text:#d7dde3;
         --dim:#7a8794; --green:#5dd08c; --amber:#e8b33e; --blue:#5aa7e0;
         --red:#e06c5b; --joke:#ff8c42; }
 * { box-sizing:border-box; }
 body { font-family:'Segoe UI',sans-serif; background:var(--bg); color:var(--text);
        max-width:1040px; margin:0 auto; padding:0 1.4rem 3rem; }
 h1 { font-size:1.5rem; letter-spacing:.06em; margin:1.4rem 0 .2rem; }
 h1 .em { color:var(--amber); }
 .sub { color:var(--dim); margin:.1rem 0 1rem; font-size:.95rem; line-height:1.5; }
 code { background:var(--field); border:1px solid #2e3946; border-radius:6px;
        padding:.05rem .35rem; font-size:.88em; color:#bfe3ff; }
 .tabs { display:flex; flex-wrap:wrap; gap:.4rem; margin:0 0 1rem; }
 .tabs button { background:var(--field); color:var(--text); border:1px solid #2e3946;
        border-radius:999px; padding:.45rem .95rem; font-size:.9rem; cursor:pointer;
        font-family:inherit; }
 .tabs button:hover { border-color:var(--blue); }
 .tabs button.active { background:#2a3a4d; border-color:var(--blue); color:#bfe3ff; }
 .panel { display:none; }
 .panel.active { display:block; }
 .intro { background:var(--panel); border:1px solid #2a333e; border-left:4px solid
        var(--amber); border-radius:12px; padding:.8rem 1rem; margin:0 0 .9rem;
        color:var(--dim); font-size:.92rem; line-height:1.5; }
 .stage { position:relative; max-width:840px; margin:0 auto; }
 .stage img { width:100%; display:block; border-radius:10px; border:1px solid #2a333e; }
 .spot { position:absolute; border:2px solid transparent; border-radius:6px;
        cursor:help; }
 .spot:hover, .spot.active { border-color:#ffd84d;
        background:rgba(255,216,77,.16); }
 .explain { background:var(--panel); border:1px solid #2a333e; border-radius:12px;
        max-width:840px; margin:.8rem auto 0; padding:.9rem 1.1rem; min-height:7.5rem; }
 .explain h3 { margin:0 0 .35rem; font-size:1rem; color:#ffd84d; }
 .explain p { margin:0; color:var(--text); font-size:.93rem; line-height:1.55; }
 .explain .hint { color:var(--dim); }
 .rec { display:block; margin-top:.5rem; font-weight:600; font-size:.85rem; }
 .rec.on { color:var(--green); }  .rec.on::before { content:"✅ "; }
 .rec.off { color:var(--dim); }   .rec.off::before { content:"⬜ "; }
 .rec.info { color:var(--blue); font-weight:400; } .rec.info::before { content:"ℹ️ "; }
 footer { color:var(--dim); text-align:center; font-size:.85rem; margin-top:1.8rem; }
"""


def main():
    tab_buttons, panels = [], []
    for key, title, shot, intro, spots in TABS:
        img = data_uri(os.path.join(SHOTS, shot))
        spot_html = "".join(
            f'<div class="spot" style="left:{x}%;top:{y}%;width:{w}%;height:{h}%" '
            f'data-tab="{key}" data-i="{i}"></div>'
            for i, (x, y, w, h, _label, _text) in enumerate(spots))
        panels.append(
            f'<div class="panel" id="p-{key}">'
            f'<div class="intro">{intro}</div>'
            f'<div class="stage"><img src="{img}" alt="VAICOM {title} tab">{spot_html}</div>'
            f'<div class="explain" id="e-{key}"><h3>👆 Hover a control</h3>'
            f'<p class="hint">Move the mouse over any checkbox, knob or button in the '
            f'picture (tap on a touchscreen) and the explanation appears here.</p></div>'
            f'</div>')
        tab_buttons.append(f'<button data-tab="{key}">{title}</button>')

    import json
    data = {key: [(label, text) for _x, _y, _w, _h, label, text in spots]
            for key, _t, _s, _i, spots in TABS}

    icon48 = os.path.join(ROOT, "cob-hero-48.png")
    foot_icon = (f'<img src="{data_uri(icon48)}" alt="🌽" '
                 f'style="height:1.4em;vertical-align:-0.35em">'
                 if os.path.exists(icon48) else "🌽")

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VAICOM — what every switch does</title><style>{CSS}</style></head><body>

<h1>📻 VAICOM — <span class="em">what every switch does</span></h1>
<p class="sub">Open the real window with <code>LCtrl + LAlt + C</code> while VoiceAttack
is running. This page is the same window, but you can <b>hover anything</b> to learn what
it does — green ✅ tags show what the CobbAttack setup expects. Which boxes to tick is in
the Setup Instruction, step 4; this page is the <i>why</i>.</p>

<div class="tabs">{''.join(tab_buttons)}</div>
{''.join(panels)}

<footer>CobbAttack {foot_icon} · VAICOM explainer · condensed from the official VAICOM
PRO Community User Manual</footer>

<script>
const DATA = {json.dumps(data)};
const tabs = document.querySelectorAll('.tabs button');
function show(key) {{
  tabs.forEach(b => b.classList.toggle('active', b.dataset.tab === key));
  document.querySelectorAll('.panel').forEach(p =>
    p.classList.toggle('active', p.id === 'p-' + key));
}}
tabs.forEach(b => b.addEventListener('click', () => show(b.dataset.tab)));
show('{TABS[0][0]}');

document.querySelectorAll('.spot').forEach(s => {{
  const reveal = () => {{
    const tab = s.dataset.tab, i = +s.dataset.i;
    document.querySelectorAll('#p-' + tab + ' .spot').forEach(o =>
      o.classList.toggle('active', o === s));
    const [label, text] = DATA[tab][i];
    document.getElementById('e-' + tab).innerHTML =
      '<h3>' + label + '</h3><p>' + text + '</p>';
  }};
  s.addEventListener('mouseenter', reveal);
  s.addEventListener('click', reveal);
}});
</script>
</body></html>"""

    with open(DST, "w", encoding="utf-8") as f:
        f.write(page)
    spots = sum(len(t[4]) for t in TABS)
    print(f"wrote {DST} ({os.path.getsize(DST) // 1024} KB, "
          f"{len(TABS)} tabs, {spots} explained controls)")


if __name__ == "__main__":
    main()
