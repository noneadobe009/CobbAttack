"""Build SETUP.html — the pretty, shippable version of SETUP.md.

Same dark cockpit look as the flight guide (commands-cheatsheet.html): hero corn,
accent-colored step sections, checkbox panels, and real screenshots (embedded from
screenshots/, click any to zoom). Content is hand-synced with SETUP.md — if you edit
one, update the other, then rerun:
    python tools/make_setup.py
"""

import base64
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "SETUP.html")
SHOTS = os.path.join(ROOT, "screenshots")


def data_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def shot(folder, name, caption):
    path = os.path.join(SHOTS, folder, name)
    if not os.path.exists(path):
        return ""
    return (f'<figure class="shot"><img src="{data_uri(path)}" alt="{caption}" '
            f'loading="lazy"><figcaption>{caption}</figcaption></figure>')


hero_path = os.path.join(ROOT, "cob-hero-200.png")
if os.path.exists(hero_path):
    HERO = (f'<img src="{data_uri(hero_path)}" alt="CobbAttack" '
            f'style="width:170px;height:170px">')
else:
    HERO = '<div style="font-size:3rem">🌽</div>'

VA_SHOTS = "".join([
    shot("voiceattack-settings", "01-general.png",
         "General — Plugin Support on, VAICOM profile loads on startup, Joystick 1 enabled."),
    shot("voiceattack-settings", "02-recognition.png",
         "Recognition — delay 700, Disable Speech Recognition TICKED. The red note is correct."),
    shot("voiceattack-settings", "04-hotkeys.png",
         "Hotkeys — everything Disabled; buttons live in the profile."),
    shot("voiceattack-settings", "03-audio.png",
         "Audio — defaults, nothing to change."),
    shot("voiceattack-settings", "05-system-advanced.png",
         "System/Advanced — on THIS PC “Run as Administrator” shows unticked because "
         "admin is set by a registry flag instead. On your install: tick it, restart, "
         "check it stuck."),
])

VAICOM_SHOTS = "".join([
    shot("vaicom", "02-preferences.png",
         "PREFERENCES — the important one. VSPX + Extended Command Set ticked."),
    shot("vaicom", "03-mp.png", "MP — SRS Integration + SRS PTT Mapping on."),
    shot("vaicom", "04-ex.png",
         "EX — Crew Messages, F-14 Mini Wheel, Carrier Comms, Deep Interrogate, "
         "Chatter, DCS Kneeboard."),
    shot("vaicom", "01-ptt.png",
         "PTT — “SRS 1/2/3” labels are normal (SRS PTT Mapping). "
         "Easy Communication: ON."),
    shot("vaicom", "05-okb-out.png", "OKB OUT — all off (OpenKneeboard not used)."),
    shot("vaicom", "06-config.png",
         "CONFIG — all unticked; sliders on Standalone and Combined/Stable."),
    shot("vaicom", "07-audio.png", "AUDIO — defaults; leave the switch alone."),
    shot("vaicom", "08-editor.png",
         "EDITOR — only used when rebuilding keywords (the FINISH button)."),
    shot("vaicom", "09-help.png",
         "HELP — diagnostics, the log file and the PDF manual live here."),
    shot("vaicom", "10-reset.png",
         "RESET — look, don’t touch. MASTER ZERO wipes your whole setup."),
])

BUTTON_SHOTS = "".join([
    shot("voiceattack-profile", "03-profile-ptt-section.png",
         "The profile’s Push-To-Talk commands — TX1 on Joystick 1 Button 18, "
         "TX2 on Button 20."),
    shot("voiceattack-profile", "06-other-advanced-execute-plugin.png",
         "Where the plugin action hides: in the command editor click "
         "Other → Advanced → “Execute an External Plugin Function”. "
         "Do this once for the WASC action and once for the VAICOM action."),
    shot("voiceattack-profile", "04-tx1-press-command.png",
         "TX1 press — BOTH actions, this order: Start Whisper Recording, then "
         "ptt.hotkey.TX1.press."),
    shot("voiceattack-profile", "05-tx1-release-command.png",
         "TX1 release — Stop Whisper Recording, then ptt.hotkey.TX1.release."),
])

TEACH_SHOTS = "".join([
    shot("voiceattack-profile", "01-profile-command-list.png",
         "In Edit Profile, find AI Communications under Keyword Collections."),
    shot("voiceattack-profile", "02-ai-communications-command.png",
         "Double-click it — the “When I say” box holds every phrase. "
         "Click in it, Ctrl+A, Ctrl+C, then Cancel."),
])

RUN_SHOTS = "".join([
    shot("others", "01-cobbattack-ready.png",
         "What good looks like: green READY light, and the engine line names your "
         "GPU. This picture is from the dev machine (NVIDIA) — on yours it should "
         "say Vulkan GPU — AMD Radeon."),
])

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CobbAttack — Setup Guide</title>
<style>
 :root { --bg:#14181d; --panel:#1c2229; --field:#242c35; --text:#d7dde3;
         --dim:#7a8794; --green:#5dd08c; --amber:#e8b33e; --blue:#5aa7e0;
         --red:#e06c5b; }
 * { box-sizing:border-box; }
 body { font-family:'Segoe UI',sans-serif; background:var(--bg); color:var(--text);
        max-width:1100px; margin:0 auto; padding:0 1.4rem 3rem; }
 .top { display:flex; gap:1.6rem; align-items:center; padding:1.4rem 0 .6rem; }
 .brand { flex:0 0 230px; text-align:center; }
 .brand img { filter:drop-shadow(0 6px 16px #0008); }
 .brand h1 { font-size:1.35rem; letter-spacing:.14em; margin:.4rem 0 .1rem; }
 .brand .sub { color:var(--dim); margin:0; font-size:.85rem; }
 .cards { flex:1; display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
        gap:.9rem; }
 .card { background:linear-gradient(160deg,#1e2630,#1a2028); border:1px solid #2a333e;
        border-radius:14px; padding:1rem 1.1rem; }
 .card h3 { margin:.1rem 0 .5rem; font-size:.98rem; color:var(--green); }
 .card p, .card li { color:var(--text); font-size:.9rem; margin:.2rem 0; }
 .chips { display:flex; flex-wrap:wrap; gap:.5rem; margin:.8rem 0 1.2rem; }
 .chip { background:var(--field); color:var(--text); text-decoration:none;
        padding:.35rem .8rem; border-radius:999px; font-size:.85rem;
        border:1px solid #2e3946; }
 .chip:hover { border-color:var(--blue); }
 .sec { background:var(--panel); border:1px solid #2a333e; border-radius:14px;
        padding:1.1rem 1.4rem; margin:0 0 1rem; scroll-margin-top:1rem;
        border-left:4px solid var(--acc,#7a8794); }
 .sec h2 { margin:.1rem 0 .2rem; font-size:1.12rem; color:var(--acc,var(--text)); }
 .sec h2 .stepno { display:inline-block; background:var(--acc); color:#14181d;
        border-radius:8px; padding:.05rem .55rem; margin-right:.55rem;
        font-size:1rem; }
 .sec .tag { color:var(--dim); margin:.1rem 0 .7rem; font-size:.9rem; }
 .sec p, .sec li { font-size:.95rem; line-height:1.5; }
 .sec ol, .sec ul { margin:.4rem 0 .4rem 1.3rem; padding:0; }
 .sec a { color:var(--blue); }
 b.k { color:var(--amber); font-weight:600; }
 code { background:var(--field); border:1px solid #2e3946; border-radius:6px;
        padding:.08rem .4rem; font-size:.88em; color:#bfe3ff; }
 .warn { background:#2b2018; border:1px solid #6b4a23; border-left:4px solid var(--amber);
        border-radius:10px; padding:.7rem .9rem; margin:.7rem 0; font-size:.92rem; }
 .danger { background:#2b1a18; border:1px solid #6b2f23; border-left:4px solid var(--red);
        border-radius:10px; padding:.7rem .9rem; margin:.7rem 0; font-size:.92rem; }
 .ok { background:#182b1f; border:1px solid #23532f; border-left:4px solid var(--green);
        border-radius:10px; padding:.7rem .9rem; margin:.7rem 0; font-size:.92rem; }
 .panelgrid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
        gap:.9rem; margin:.6rem 0; }
 .vpanel { background:#11151a; border:1px solid #2e3946; border-radius:12px;
        padding:.8rem 1rem; }
 .vpanel h4 { margin:.1rem 0 .5rem; font-size:.92rem; letter-spacing:.08em;
        color:var(--acc,var(--amber)); }
 .vpanel ul { list-style:none; margin:.2rem 0; padding:0; }
 .vpanel li { padding:.14rem 0; font-size:.9rem; }
 .vpanel li.on::before { content:"✅ "; }
 .vpanel li.off { color:var(--dim); }
 .vpanel li.off::before { content:"⬜ "; }
 .vpanel li.note { color:var(--dim); font-size:.82rem; padding-top:.35rem; }
 .shots { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
        gap:1rem; margin:.8rem 0 .3rem; }
 .shot { margin:0; background:#11151a; border:1px solid #2e3946; border-radius:12px;
        padding:.6rem; }
 .shot img { width:100%; border-radius:8px; cursor:zoom-in; display:block;
        border:1px solid #2a333e; }
 .shot figcaption { color:var(--dim); font-size:.82rem; padding:.45rem .15rem .05rem;
        line-height:1.4; }
 #lightbox { position:fixed; inset:0; display:none; background:#000d; z-index:99;
        padding:2vh 2vw; cursor:zoom-out; }
 #lightbox img { max-width:100%; max-height:100%; margin:auto; display:block;
        border-radius:8px; }
 table.fix { border-collapse:collapse; width:100%; margin:.5rem 0; }
 table.fix th, table.fix td { text-align:left; padding:.5rem .7rem; font-size:.92rem;
        border-bottom:1px solid #2a333e; vertical-align:top; }
 table.fix th { color:var(--dim); font-weight:600; }
 table.fix td:first-child { color:var(--red); white-space:nowrap; }
 .device { font-family:Consolas,monospace; background:#0e1216; border:1px solid #34455a;
        border-radius:9px; padding:.6rem .9rem; margin:.5rem 0; font-size:.9rem; }
 .device .good { color:var(--green); }
 .device .bad { color:var(--red); }
 footer { color:var(--dim); text-align:center; font-size:.85rem; margin-top:1.6rem; }
 @media (max-width:800px) { .top { flex-direction:column; } .brand { flex:none; } }
 @media print { body { background:#fff; color:#000; } }
</style></head><body>

<div class="top">
<div class="brand">
  __HERO__
  <h1>SETUP GUIDE</h1>
  <p class="sub">CobbAttack · voice control that uses your AMD card</p>
</div>
<div class="cards">
  <div class="card"><h3>🌽 What is this?</h3>
    <p>Voice recognition for VAICOM that runs on your <b class="k">AMD graphics
    card</b>. It replaces WhisperAttack's server program only — everything else in
    your VoiceAttack/VAICOM setup stays the same.</p></div>
  <div class="card"><h3>🗺️ The short version</h3>
    <p>① Install the four pieces → ② set VoiceAttack &amp; VAICOM exactly as
    pictured → ③ bind two talk buttons → ④ run it and check the
    <b class="k">Vulkan GPU</b> line → ⑤ fly.</p></div>
  <div class="card"><h3>🕹️ Your two buttons</h3>
    <p><b class="k">TX1</b> — radio 1 · ATC, AWACS, tanker, ground crew</p>
    <p><b class="k">TX2</b> — radio 2 · your wingmen</p>
    <p style="color:var(--dim)">That covers everything single-player.</p></div>
</div>
</div>

<nav class="chips">
  <a class="chip" href="#install">🧰 Install</a>
  <a class="chip" href="#va">🎛️ VoiceAttack</a>
  <a class="chip" href="#vaicom">📻 VAICOM</a>
  <a class="chip" href="#buttons">🕹️ Buttons</a>
  <a class="chip" href="#run">▶️ First run</a>
  <a class="chip" href="#teach">📖 Teach it</a>
  <a class="chip" href="#custom">⚙️ Your commands</a>
  <a class="chip" href="#trouble">🚑 Troubleshooting</a>
</nav>

<p style="color:var(--dim);font-size:.88rem">Every screenshot below is from the
verified working setup — <b>click any picture to zoom</b>. If your screen matches
the pictures, you're done with that step.</p>

<section class="sec" id="install" style="--acc:#5dd08c">
<h2><span class="stepno">1</span>🧰 Install the four pieces</h2>
<p class="tag">Three downloads and a pip install. You likely have the first two.</p>
<ol>
  <li><b class="k">VoiceAttack</b> (paid, voiceattack.com) — you already have it.</li>
  <li><b class="k">VAICOM PRO Community Edition</b> (free): the <code>.msi</code> from
      <a href="https://github.com/Penecruz/VAICOM-Community/releases">github.com/Penecruz/VAICOM-Community/releases</a>.
      Version 3.x — it has numeric keywords built in.</li>
  <li><b class="k">The WASC VoiceAttack plugin</b> — already in the box: copy the
      <code>WhisperAttackServerCommand</code> folder from CobbAttack's
      <code>third_party\\</code> into <code>C:\\Program Files (x86)\\VoiceAttack\\Apps\\</code>
      (Windows will ask for admin — say yes). Then VoiceAttack → Options →
      <b>Enable Plugin Support</b> and restart VoiceAttack.
      <span style="color:var(--dim)">(The plugin comes from the
      <a href="https://github.com/nikoelt/WhisperAttack">WhisperAttack</a> project,
      MIT-licensed — license file included.)</span></li>
  <li>That's it — <b>no Python needed</b>: CobbAttack ships as
      <code>CobbAttack.exe</code>. (If your antivirus ever quarantines the exe —
      rare false alarm — allow it, or use the fallback: install Python 3.13 with
      "Add to PATH" ticked, run <code>pip install -r requirements.txt</code>, and
      start with <code>run-cobbattack.bat</code> instead.)</li>
</ol>
<div class="ok">✔ Already in the box: the whisper.cpp engine (Vulkan + CPU builds)
and the <code>base.en</code> model ship inside CobbAttack's <code>bin\\</code> and
<code>models\\</code> folders — there is nothing else to download.</div>
</section>

<section class="sec" id="va" style="--acc:#5aa7e0">
<h2><span class="stepno">2</span>🎛️ VoiceAttack settings (v2.1.8, verified)</h2>
<p class="tag">Options (wrench icon). Only these matter — everything not listed stays
at its default. Match the pictures.</p>
<div class="panelgrid">
  <div class="vpanel"><h4>OPTIONS → GENERAL</h4><ul>
    <li class="on">Enable Plugin Support <span style="color:var(--dim)">(restart VA after first enabling)</span></li>
    <li class="on">Load Profile on Startup = <b class="k">your VAICOM profile</b></li>
    <li class="on">Joystick assigned as Joystick 1 and <b>enabled</b></li>
  </ul></div>
  <div class="vpanel"><h4>OPTIONS → RECOGNITION</h4><ul>
    <li class="on">Unrecognized Speech Delay = <b class="k">700</b></li>
    <li class="on"><b>Disable Speech Recognition</b> — CobbAttack does the listening</li>
    <li class="note">The red "Listening is currently disabled" note is CORRECT, not an error.</li>
  </ul></div>
  <div class="vpanel"><h4>OPTIONS → HOTKEYS / AUDIO</h4><ul>
    <li class="off">Hotkeys: everything Disabled (buttons live in the profile)</li>
    <li class="off">Audio: defaults, nothing special</li>
  </ul></div>
  <div class="vpanel"><h4>OPTIONS → SYSTEM / ADVANCED</h4><ul>
    <li class="on">Run VoiceAttack as an Administrator — tick, restart, check it stuck</li>
    <li class="note">Admin matters: without it VAICOM can't create its files and
        nothing works. If it won't elevate, ask us about the registry fallback.</li>
  </ul></div>
</div>
<div class="shots">__VA_SHOTS__</div>
<div class="warn">⚠️ The game-controller icon in VoiceAttack's sidebar <b>toggles all
joysticks off</b>. If your buttons suddenly do nothing anywhere, you probably clicked
it — click it again.</div>
</section>

<section class="sec" id="vaicom" style="--acc:#e8b33e">
<h2><span class="stepno">3</span>📻 VAICOM settings (Community 3.1.5.2, verified)</h2>
<p class="tag">Open the VAICOM window (LCtrl+LAlt+C). Tick EXACTLY these; leave
everything else unticked/default. Match the pictures.</p>
<div class="ok">🆕 <b>Fresh VAICOM install?</b> Start VoiceAttack once (as admin) so
VAICOM creates its files. If the profile "VAICOM PRO for DCS World" isn't in
VoiceAttack's profile list, import it: profile dropdown → the little import icon →
<code>C:\\Program Files (x86)\\VoiceAttack\\Apps\\VAICOMPRO\\Profiles\\VAICOM PRO for
DCS World.vap</code>. Then fill the keywords once: EDITOR tab → <b>FINISH</b> → paste
into AI Communications (step 6's warning box explains the paste).</div>
<div class="panelgrid">
  <div class="vpanel"><h4>PREFERENCES</h4><ul>
    <li class="on">VSPX Processing</li>
    <li class="on"><b>Extended Command Set</b> ← the big one</li>
    <li class="on">UI Sounds</li>
    <li class="on">Use Audio Cues</li>
    <li class="on">Require Engage Cue</li>
    <li class="on">Allow Options</li>
    <li class="off">Force Speech / Force Callsigns / Force ATC Names — all OFF</li>
  </ul></div>
  <div class="vpanel"><h4>MP</h4><ul>
    <li class="on">Use with Multiplayer</li>
    <li class="on">SRS Integration</li>
    <li class="on">SRS PTT Mapping</li>
    <li class="note">This makes the PTT page label keys "SRS 1/2/3" — normal. In the
        Hornet TX1 is still radio 1 (COMM1), TX2 radio 2 (COMM2).</li>
  </ul></div>
  <div class="vpanel"><h4>EX</h4><ul>
    <li class="on">Crew Messages <span style="color:var(--dim)">("Hints Only" off)</span></li>
    <li class="on">F-14 Mini Wheel</li>
    <li class="on">Carrier Comms</li>
    <li class="on">Deep Interrogate</li>
    <li class="on">Chatter: Enable · Theme (AUTO)</li>
    <li class="on">DCS Kneeboard: Enable</li>
  </ul></div>
  <div class="vpanel"><h4>OKB OUT · CONFIG · AUDIO</h4><ul>
    <li class="off">OKB Out: all unticked</li>
    <li class="off">Config: all unticked · sliders on <b>Standalone</b> and
        <b>Combined/Stable</b></li>
    <li class="off">Audio: defaults</li>
  </ul></div>
</div>
<div class="shots">__VAICOM_SHOTS__</div>
<div class="warn">⚠️ <b>Extended Command Set</b> is the box that cost us hours:
without it VAICOM understands "request taxi to runway" and then silently throws it
away — ATC never answers, and the only clue is a quiet orange log line.</div>
<div class="danger">🚫 <b>RESET page:</b> touch nothing there. The yellow
<b>MASTER ZERO</b> button wipes your whole VAICOM setup.</div>
</section>

<section class="sec" id="buttons" style="--acc:#e8a04b">
<h2><span class="stepno">4</span>🕹️ Push-to-talk buttons</h2>
<p class="tag">Two buttons is plenty for the Hornet in single player.</p>
<ul>
  <li><b class="k">TX1</b> = radio 1 — ATC, AWACS, tanker, <b>and ground crew</b>
      (ground crew answers on any radio key).</li>
  <li><b class="k">TX2</b> = radio 2 — your wingmen.</li>
  <li style="color:var(--dim)">TX5 is a dedicated ground-crew key if you ever want a
      third button. TX3 (FM/JTAC) doesn't exist in the Hornet, TX6 isn't a radio,
      TX4 (AUTO) we skip.</li>
</ul>
<p>In Edit Profile, each TX has a <b>press</b> and a <b>release</b> command. Assign
your joystick button to both ("When I press button"). To add a plugin action, click
<b class="k">Other → Advanced → Execute an External Plugin Function</b>, pick the
plugin from the dropdown, and type the context. Each command needs <b>both</b>
plugin actions, in this order:</p>
<ul>
  <li>On <b>press</b>: WASC context <code>Start Whisper Recording</code>
      <b>+</b> VAICOM context <code>ptt.hotkey.TX1.press</code></li>
  <li>On <b>release</b>: WASC context <code>Stop Whisper Recording</code>
      <b>+</b> VAICOM context <code>ptt.hotkey.TX1.release</code></li>
</ul>
<div class="shots">__BUTTON_SHOTS__</div>
<div class="warn">⚠️ <b>Repeat this for EVERY TX button you use.</b> Each one is four
plugin actions total: the press command and the release command each need the WASC
action <i>and</i> the VAICOM action (added via Other → Advanced → Execute an External
Plugin Function). So two buttons (TX1 + TX2) = four commands to edit. If a TX has the
VAICOM action but no Whisper action, that radio will key up but nothing you say will
be heard.</div>
<div class="warn">⚠️ Type the WASC context <b>exactly</b> — a typo (e.g. "Wisper")
fails silently: the button will move the radio but never record.</div>
</section>

<section class="sec" id="run" style="--acc:#4ecdc4">
<h2><span class="stepno">5</span>▶️ First run</h2>
<ol>
  <li><b class="k">Microphone first:</b> CobbAttack listens to your Windows
      <b>default</b> microphone — set your headset as the default input device in
      Windows Sound settings (or put part of its name in <code>"input_device"</code>
      in <code>settings.json</code>).</li>
  <li>In DCS: OPTIONS → GAMEPLAY → <b class="k">Easy Communication</b>. ON is the
      simple choice: calls just work. OFF works too — but then you must tune each
      radio to the recipient's real frequency yourself, or nobody answers.</li>
  <li>Start <b class="k">VoiceAttack</b> (with your VAICOM profile).</li>
  <li>Double-click <b class="k">CobbAttack.exe</b>.</li>
  <li><b>Look at the first lines of the window:</b>
    <div class="device"><span class="good">✔ device: Vulkan GPU — AMD Radeon …</span> ← what you want<br>
    <span class="bad">✘ device: CPU — no GPU acceleration</span> ← tell us; update AMD
    (Adrenalin) drivers</div></li>
  <li>Hold your talk button, say <b class="k">"request taxi to runway"</b>, release.
      The window shows what it heard, what it cleaned it up to, and how long it took.</li>
</ol>
<div class="shots">__RUN_SHOTS__</div>
<div class="ok">✔ Order matters: start CobbAttack <b>after</b> VoiceAttack — on startup
it also auto-repairs a VAICOM script bug (commands dying after the first mission).</div>
</section>

<section class="sec" id="teach" style="--acc:#e8c94b">
<h2><span class="stepno">6</span>📖 Teach it the real VAICOM commands</h2>
<p class="tag">With this done, CobbAttack only ever sends phrases that actually exist
in your profile — near-misses get corrected, garbage gets dropped.</p>
<ol>
  <li>In VoiceAttack, open your VAICOM profile with the <b class="k">✏️ pencil
      icon</b> next to the profile name, then double-click the
      <b class="k">AI Communications</b> command (Keyword Collections).</li>
  <li>Click in the big "When I say" box: <b>Ctrl+A</b>, <b>Ctrl+C</b>, then Cancel out.</li>
  <li>Paste into a file called <code>vaicom_keywords.txt</code> in the CobbAttack folder
      (Notepad → Ctrl+V → save with that exact name).</li>
  <li>Restart CobbAttack — it notices the new file and rebuilds its command list
      automatically. The log says <code>commands.txt rebuilt</code> and
      <code>… command phrases</code> with a big number.</li>
</ol>
<div class="shots">__TEACH_SHOTS__</div>
<div class="warn">⚠️ <b>Copying OUT vs pasting IN — don't mix them up.</b> The steps
above only <i>copy the list out</i>, so you Cancel — nothing in the profile changes.
The one time you <i>paste IN</i> is after rebuilding keywords in VAICOM's EDITOR tab
(the <b>FINISH</b> button): FINISH puts the new list on the clipboard — then open
AI Communications, click in "When I say", <b>Ctrl+A</b>, <b>Ctrl+V</b> (replace old
with new), and click <b>OK</b> (not Cancel!). If the paste comes out empty, FINISH's
clipboard copy failed (it often does) — the same list is saved at
<code>C:\\Program Files (x86)\\VoiceAttack\\Apps\\VAICOMPRO\\Export\\keywords.txt</code>;
copy its contents from there. Afterwards, redo steps 1–4 so CobbAttack learns the
new list too.</div>
<p style="color:var(--dim)">The 📖 flight guide rebuilds itself from the same list
on the next restart — nothing extra to run.</p>
<p><b>If a word keeps coming out wrong:</b> click the wrong word in a blue
<code>heard:</code> line and pick a fix. If one word came out as two, <b>drag
across both wrong words</b> — they go into the teach box as one phrase. The feed
confirms every Add. Right-click the feed for <b>Undo fix</b> and
<b>Clear window</b>. Hand-edit route: open <code>word_mappings.txt</code>, add a
line like <code>miss heard thing -&gt; right thing</code>, save, restart.</p>
<p><b>Better accuracy (optional):</b> put <code>ggml-small.en.bin</code> from
<a href="https://huggingface.co/ggerganov/whisper.cpp/tree/main">huggingface.co/ggerganov/whisper.cpp</a>
into <code>models</code> and set <code>"model": "ggml-small.en.bin"</code> in
<code>settings.json</code>. Your GPU will still be fast.</p>
</section>

<section class="sec" id="custom" style="--acc:#f0d060">
<h2><span class="stepno">7</span>⚙️ Your own voice commands (optional)</h2>
<p class="tag">Made your own VoiceAttack command — like "turn on the lights" flipping
a cockpit switch? Two clicks and CobbAttack learns it.</p>
<ol>
  <li>Build the command in your VAICOM profile as usual (Edit Profile → New Command:
      the "When I say" phrase + whatever keys it presses).</li>
  <li>Export the profile: VoiceAttack main window → <b>profile menu</b> →
      <b class="k">Export Profile</b> → save the <code>.vap</code> file anywhere.</li>
  <li>Drag the file onto the box below (or click the box to pick it) —
      CobbAttack must be running.</li>
</ol>
<div id="vapdrop" style="border:2px dashed #4a5563;border-radius:12px;
padding:14px 16px;margin:6px 0 14px;color:#9aa7b4;cursor:pointer;text-align:center">
⬇ Drop your VoiceAttack profile export (<b>.vap</b>) here — or click to pick a file
<br><span style="font-size:.8rem">CobbAttack must be running — your commands are
learned instantly</span></div>
<input type="file" id="vapfile" accept=".vap" style="display:none">
<script>
(function(){
 var z=document.getElementById('vapdrop'), inp=document.getElementById('vapfile');
 if(!z) return;
 function done(msg){ z.innerHTML=msg; }
 function send(file){
  done('importing…');
  fetch('http://127.0.0.1:65434/import-vap',{method:'POST',
        headers:{'X-Filename':file.name},body:file})
   .then(function(r){return r.json();})
   .then(function(j){ if(j.count>=0) done('✓ imported — '+j.count+' of your commands are known');
        else done('✗ couldn\\'t read that file — is it a .vap export?'); })
   .catch(function(){ done('✗ CobbAttack isn\\'t running — start it, then try again'); });
 }
 z.addEventListener('click',function(){inp.click();});
 inp.addEventListener('change',function(){ if(inp.files[0]) send(inp.files[0]); });
 z.addEventListener('dragover',function(e){e.preventDefault();z.style.borderColor='#5aa7e0';});
 z.addEventListener('dragleave',function(){z.style.borderColor='#4a5563';});
 z.addEventListener('drop',function(e){e.preventDefault();z.style.borderColor='#4a5563';
   if(e.dataTransfer.files[0]) send(e.dataTransfer.files[0]);});
})();
</script>
<p>What that does: your phrases are added to the firewall's allow-list (otherwise
CobbAttack would discard them as mishears), and the flight guide's
"⚙️ Your custom commands" section updates automatically.</p>
<div class="warn">⚠️ Re-export after every new command — CobbAttack can only read
the <code>.vap</code> file, not VoiceAttack's memory. Forgot? Symptom: your new
command works when typed but the spoken version gets "no matching command."</div>
</section>

<section class="sec" id="trouble" style="--acc:#e06c5b">
<h2><span class="stepno">8</span>🚑 Troubleshooting</h2>
<table class="fix">
<tr><th>Symptom</th><th>Fix</th></tr>
<tr><td>Nothing happens on PTT</td><td>VoiceAttack running? WASC plugin installed and
plugin support enabled? TX buttons have the Start/Stop Whisper actions (spelled
exactly)?</td></tr>
<tr><td>Commands fire twice</td><td>VoiceAttack's own speech recognition is still on —
disable it (step 2).</td></tr>
<tr><td>ATC never answers</td><td>VAICOM PREFS → <b>Extended Command Set</b> must be
ticked (step 3). Also: VAICOM only listens while DCS is unpaused, in a mission.</td></tr>
<tr><td>"could not reach VoiceAttack plugin"</td><td>VoiceAttack isn't running, or the
WASC plugin didn't load.</td></tr>
<tr><td>"DCS is not connected"</td><td>Normal outside a mission. In a mission: unpause.
If it persists — especially after restarting VoiceAttack — restart in this order:
VoiceAttack → CobbAttack → then DCS <b>completely</b>.</td></tr>
<tr><td>Radios dead after restarting a mission (Shift+R)</td><td>Old VAICOM bug —
CobbAttack fixes it automatically at startup (you'll see "VAICOM radio-panel
self-heal" in the log). Restart missions freely. If radios ever do go quiet after a
mission restart, tell us — that's news.</td></tr>
<tr><td>Buttons dead everywhere</td><td>You clicked VoiceAttack's game-controller
sidebar icon — it disables all joysticks. Click it again.</td></tr>
<tr><td>It hears you badly / wrong mic</td><td>CobbAttack uses the Windows default
microphone — set your headset as default input in Windows Sound settings, or set
<code>"input_device"</code> in <code>settings.json</code>.</td></tr>
<tr><td>Windows Firewall pops up</td><td>Allow it — CobbAttack and its engine only
talk to each other on this PC (127.0.0.1); nothing goes online.</td></tr>
<tr><td>Still stuck</td><td>Everything is logged in <code>cobbattack.log</code> — send
us that file.</td></tr>
</table>
</section>

<footer>CobbAttack 🌽 · built for Cobb's AMD rig · guide version 2026-07-25</footer>

<div id="lightbox"><img alt=""></div>
<script>
const lb = document.getElementById('lightbox');
const lbImg = lb.querySelector('img');
document.querySelectorAll('.shot img').forEach(im => {
  im.addEventListener('click', () => { lbImg.src = im.src; lb.style.display = 'flex'; });
});
lb.addEventListener('click', () => { lb.style.display = 'none'; lbImg.src = ''; });
document.addEventListener('keydown', e => { if (e.key === 'Escape') lb.click(); });
</script>
</body></html>
"""

page = (PAGE.replace("__HERO__", HERO)
            .replace("__VA_SHOTS__", VA_SHOTS)
            .replace("__VAICOM_SHOTS__", VAICOM_SHOTS)
            .replace("__BUTTON_SHOTS__", BUTTON_SHOTS)
            .replace("__TEACH_SHOTS__", TEACH_SHOTS)
            .replace("__RUN_SHOTS__", RUN_SHOTS))
with open(DST, "w", encoding="utf-8") as f:
    f.write(page)
print(f"wrote {DST} ({os.path.getsize(DST) // 1024} KB)")
