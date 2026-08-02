"""Builds troubleshoot.html — "why did that just happen?" in one page.

Opened by the red 🚑 TROUBLESHOOT button. Three parts, in the order you need them:

  1. LIVE CHECK    — everything that has to be true right now, each one green or red.
  2. THIS SESSION  — every call since startup: what you said, what was sent, and for
                     anything refused, the exact reason plus the fix.
  3. REFERENCE     — every message CobbAttack can show, and the VAICOM-side symptoms
                     (wrong command fired, ATC silent) that aren't our messages at all.

Nothing here talks to the network except two localhost port probes; the page is a
plain file written next to the exe, so it can be sent to us as-is.
"""

import base64
import html
import os
import socket
import subprocess
import time

import config
import vaicom_patch

VA_APPS = [
    r"C:\Program Files (x86)\VoiceAttack\Apps",
    r"C:\Program Files\VoiceAttack\Apps",
]
DST = os.path.join(config.ROOT, "troubleshoot.html")

# Every refusal reason the pipeline can produce → what it means, what to do.
# Keyed by normalize.Verdict.reason plus the app-level ones main.py records.
REASONS = {
    "blank": (
        "Blank audio — no speech in the clip",
        "Whisper returned only a non-speech annotation like <code>[BLANK_AUDIO]</code>, "
        "<code>(wind)</code> or <code>[typing]</code>. It heard the clip, but there were "
        "no words in it.",
        "Almost always the microphone, not you: wrong input device, mic muted, or the "
        "talk button released before you started speaking. Check Windows Sound → Input "
        "is your headset, say the command a beat after pressing the button, and confirm "
        "the mic level moves while you talk.",
    ),
    "hallucination": (
        "Whisper's silence filler — discarded",
        "On silence Whisper invents stock phrases (\"Thank you.\", \"Bye.\", \"You\"). "
        "These are on a block-list and never reach VoiceAttack.",
        "Same causes as blank audio: an empty clip. If it happens on every press, your "
        "mic isn't being captured.",
    ),
    "no_match": (
        "Real words, but no command is close enough",
        "The words were understood, but nothing in your VAICOM profile scores at or "
        "above the fuzzy threshold, so it was refused rather than guessed at. This is "
        "the firewall doing its job — sending the closest wrong command mid-flight is "
        "worse than sending nothing.",
        "Three possibilities: (a) it genuinely wasn't a command — nothing to fix; "
        "(b) it was a command but a word came out wrong — click the wrong word in the "
        "blue heard: line and teach the fix; (c) it's YOUR own VoiceAttack command and "
        "CobbAttack has never seen your profile — export the profile and drop it on the "
        "voice commands page's drop-box.",
    ),
    "too_short": (
        "Button released too fast",
        "The talk button was held for less than the minimum, so the clip was thrown "
        "away before transcription.",
        "Hold the button, speak, then release. If your button is on a stiff HOTAS trigger, "
        "raise <code>min_record_seconds</code> in <code>settings.json</code>.",
    ),
    "engine_error": (
        "The whisper engine failed on this clip",
        "whisper-server.exe was reached but errored or timed out.",
        "Look at the engine line at the top of the window. If CobbAttack has been running "
        "a long time, restart it. Send us <code>cobbattack.log</code> if it repeats.",
    ),
    "va_unreachable": (
        "VoiceAttack didn't take the command",
        "The command passed every check but nothing was listening on the text port — so "
        "VoiceAttack is closed, or the WASC plugin isn't loaded.",
        "Start VoiceAttack, and check Options → <b>Enable Plugin Support</b> is ticked "
        "and the <code>WhisperAttackServerCommand</code> folder is in VoiceAttack's "
        "<code>Apps</code> folder. VoiceAttack must be running as Administrator.",
    ),
    "kneeboard": (
        "Sent to the DCS kneeboard, not VoiceAttack",
        "Anything you start with the word \"note\" is written to the kneeboard instead "
        "of being run as a command.",
        "Working as intended. Don't start a radio call with the word \"note\".",
    ),
}

# Symptoms that are NOT our messages — the command left CobbAttack correctly and
# something downstream (VoiceAttack, VAICOM, DCS) did the wrong thing with it.
DOWNSTREAM = [
    ("The feed says <b>sent</b> but nothing happens in the cockpit",
     "VoiceAttack got the text but has no command with that exact name, or DCS isn't "
     "listening. VoiceAttack's own log (the big list in its main window) is the place "
     "to look — it shows every command it received and whether it matched.",
     "If VoiceAttack's log shows nothing at all, the plugin isn't loaded. If it shows "
     "the phrase but says it didn't match, your profile has changed since CobbAttack "
     "learned it — redo the keyword export (Setup step 7)."),
    ("VAICOM runs the <b>wrong</b> command",
     "CobbAttack sends one exact phrase; VAICOM then decides who it was addressed to "
     "and what it meant. If the phrase in the <b>sent</b> line is the phrase you wanted, "
     "the mistake happened inside VAICOM — usually the recipient (\"two\", \"tower\", "
     "\"texaco\") was dropped or misheard, so the right command went to the wrong "
     "listener.",
     "Compare the <b>sent</b> line here with what VAICOM's window shows it received. "
     "Recipient wrong → say the callsign more distinctly, or teach the fix. Command "
     "wrong → the phrase itself was mis-snapped: teach the correction."),
    ("ATC never answers, no error anywhere",
     "The classic one: VAICOM PREFERENCES → <b>Extended Command Set</b> is unticked. "
     "VAICOM accepts the phrase and silently discards it.",
     "Tick Extended Command Set (Setup step 3). Also check DCS is unpaused and in a "
     "mission — VAICOM ignores everything otherwise."),
    ("Every command fires <b>twice</b>",
     "VoiceAttack's own speech recognition is still enabled, so Windows Speech and "
     "CobbAttack both hear you.",
     "VoiceAttack → Options → Recognition → tick <b>Disable Speech Recognition</b>."),
    ("\"DCS is not connected\"",
     "Normal outside a mission. Persisting inside one means VAICOM's UDP sockets died — "
     "the bug CobbAttack patches at startup.",
     "Restart in this order: VoiceAttack → CobbAttack → DCS last. The LIVE CHECK above "
     "shows whether the lua repairs are currently in place."),
    ("Radios dead after restarting a mission (Shift+R)",
     "Old VAICOM bug. CobbAttack's radio-panel self-heal fixes it, but DCS only reads "
     "those files when DCS starts.",
     "Make sure the two lua checks above are green, then start DCS <b>after</b> CobbAttack."),
]


def _port_in_use(port, host="127.0.0.1"):
    """Is something listening there? Tested by trying to BIND, never by connecting.

    Connecting to VoiceAttack's text port would hand the WASC plugin an empty
    message — a stray command in the cockpit is not an acceptable price for a
    diagnostic. Binding touches nobody: it fails with EADDRINUSE if the port is
    taken and is released immediately if it isn't. (No SO_REUSEADDR — that would
    let the bind succeed alongside the real listener and report a false "free".)
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        return False
    except OSError:
        return True
    finally:
        s.close()


def _process_running(name):
    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}"],
                             capture_output=True, text=True,
                             creationflags=subprocess.CREATE_NO_WINDOW).stdout
        return name.lower() in out.lower()
    except OSError:
        return False


def _plugin_folder():
    for apps in VA_APPS:
        path = os.path.join(apps, "WhisperAttackServerCommand")
        if os.path.isdir(path):
            return path
    return None


def _lua_state(settings, rel, transform):
    """(status, detail) for one VAICOM lua file: found? patched?"""
    path = vaicom_patch._find_lua(settings, rel)
    if path is None:
        return "warn", "not found — fine if DCS/VAICOM aren't installed on this PC"
    try:
        with open(path, "r", encoding="utf-8") as f:
            _, pending = transform(f.read())
    except OSError as e:
        return "bad", f"could not read: {e}"
    if pending:
        return "bad", f"{pending} repair(s) missing — restart CobbAttack ({path})"
    return "ok", f"repaired and in place<br><span class='path'>{html.escape(path)}</span>"


def checks(app):
    """The LIVE CHECK board: list of (status, title, detail)."""
    s = app.settings
    out = []

    device = getattr(app.engine, "device_line", "unknown")
    on_gpu = "GPU" in device and "no GPU" not in device
    out.append(("ok" if on_gpu else "bad", "Speech engine device",
                html.escape(device) + ("" if on_gpu else
                " — this is the slow path. Update your AMD Adrenalin drivers, then "
                "restart CobbAttack.")))

    alive = _port_in_use(s["engine_port"])
    out.append(("ok" if alive else "bad", "whisper-server running",
                f"listening on 127.0.0.1:{s['engine_port']}" if alive else
                "not answering — the engine died; restart CobbAttack"))

    out.append(("ok", "Talk-button listener",
                f"127.0.0.1:{s['control_port']} — this is what your TX buttons hit"))

    va = _process_running("VoiceAttack.exe")
    text_port = _port_in_use(s["voiceattack_port"], s["voiceattack_host"])
    if va and text_port:
        status, detail = "ok", ("running, and the WASC plugin is listening on "
                                f"{s['voiceattack_host']}:{s['voiceattack_port']}")
    elif va:
        status, detail = "bad", (
            f"VoiceAttack is running but nothing is listening on port "
            f"{s['voiceattack_port']} — the WASC plugin didn't load. Tick "
            "<b>Enable Plugin Support</b> in VoiceAttack's Options and restart it.")
    else:
        status, detail = "bad", ("not running — start VoiceAttack, or nothing you say "
                                 "can reach the cockpit")
    out.append((status, "VoiceAttack", detail))

    plugin = _plugin_folder()
    out.append(("ok" if plugin else "bad", "WASC plugin folder",
                f"<span class='path'>{html.escape(plugin)}</span>" if plugin else
                "not found in VoiceAttack's Apps folder — copy "
                "<code>third_party\\WhisperAttackServerCommand</code> there"))

    out.append(_prefix("VAICOM second-mission fix",
                       _lua_state(s, vaicom_patch.DEVICE_REL, vaicom_patch._transform)))
    out.append(_prefix("VAICOM radio-panel self-heal",
                       _lua_state(s, vaicom_patch.PANEL_REL, vaicom_patch._transform_panel)))

    n = len(app.normalizer.commands)
    out.append(("ok" if n else "bad", "Command list",
                f"{n:,} phrases loaded from your profile" if n else
                "empty — CobbAttack has no idea what your commands are. Do Setup step 7 "
                "(paste AI Communications into vaicom_keywords.txt)."))

    custom = len(app.normalizer.custom)
    out.append(("ok" if custom else "warn", "Your own commands",
                f"{custom} learned from your .vap export" if custom else
                "none imported — only needed if you built your own VoiceAttack commands"))

    mic = s.get("input_device") or "Windows default input device"
    out.append(("ok", "Microphone", html.escape(str(mic)) +
                " — blank audio every time means this is the wrong device"))

    out.append(("ok", "Settings",
                f"model <code>{html.escape(s['model'])}</code> · "
                f"fuzzy threshold <b>{s['fuzzy_threshold']}</b> · "
                f"audio_ctx {s['audio_ctx']} · threads {s['threads']}"))
    return out


def _prefix(title, state):
    status, detail = state
    return status, title, detail


def _session_rows(app):
    rows = []
    for e in reversed(list(app.history)):
        when = time.strftime("%H:%M:%S", time.localtime(e["t"]))
        raw = html.escape(e.get("raw", "") or "")
        if e["kind"] == "sent":
            rows.append(
                f"<tr class='good'><td>{when}</td><td class='said'>{raw}</td>"
                f"<td><b>sent</b> → <code>{html.escape(e['text'])}</code></td>"
                f"<td class='why'>Matched your profile{_score(e)}. Anything wrong from "
                f"here happened inside VoiceAttack or VAICOM — see the reference below."
                f"</td></tr>")
        else:
            title, meaning, fix = REASONS.get(
                e["kind"], ("Refused", "", "Send us cobbattack.log."))
            extra = ""
            if e.get("cleaned") and e["cleaned"] != (e.get("raw") or "").lower():
                extra += f" It cleaned up to <code>{html.escape(e['cleaned'])}</code>."
            if e.get("best"):
                extra += (f" Closest command was <code>{html.escape(e['best'])}</code> "
                          f"at <b>{e.get('score', 0)}</b> — the threshold is "
                          f"<b>{app.settings['fuzzy_threshold']}</b>.")
            rows.append(
                f"<tr class='bad'><td>{when}</td><td class='said'>{raw or '—'}</td>"
                f"<td><b>{html.escape(title)}</b></td>"
                f"<td class='why'>{meaning}{extra}<br><span class='fix'>→ {fix}</span>"
                f"</td></tr>")
    if not rows:
        rows.append("<tr><td colspan='4' class='why'>Nothing yet this session — hold "
                    "your talk button and say something, then reopen this page.</td></tr>")
    return "".join(rows)


def _score(e):
    if e.get("score") and e.get("best") and e["best"] != e["text"]:
        return (f" (corrected from <code>{html.escape(e.get('cleaned', ''))}</code> "
                f"at {e['score']})")
    return ""


def _foot_icon():
    """The corn-with-sunglasses mascot as an inline image; 🌽 if the art is gone."""
    path = os.path.join(config.ROOT, "cob-hero-48.png")
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return (f'<img src="data:image/png;base64,{b64}" alt="🌽" '
                f'style="height:1.4em;vertical-align:-0.35em">')
    except OSError:
        return "🌽"


def _log_tail(lines=250):
    try:
        with open(config.LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
            tail = f.readlines()[-lines:]
    except OSError:
        return "(no log file yet)"
    return html.escape("".join(tail))


CSS = """
 :root { --bg:#14181d; --panel:#1c2229; --field:#242c35; --text:#d7dde3;
         --dim:#7a8794; --green:#5dd08c; --amber:#e8b33e; --blue:#5aa7e0;
         --red:#e06c5b; }
 * { box-sizing:border-box; }
 body { font-family:'Segoe UI',sans-serif; background:var(--bg); color:var(--text);
        max-width:1100px; margin:0 auto; padding:0 1.4rem 3rem; }
 h1 { font-size:1.5rem; letter-spacing:.06em; margin:1.4rem 0 .2rem; }
 h1 .em { color:var(--red); }
 .sub { color:var(--dim); margin:.1rem 0 1rem; font-size:.92rem; }
 .chips { display:flex; flex-wrap:wrap; gap:.5rem; margin:.2rem 0 1.4rem; }
 .chip { background:var(--field); color:var(--text); text-decoration:none;
        padding:.35rem .8rem; border-radius:999px; font-size:.85rem;
        border:1px solid #2e3946; }
 .chip:hover { border-color:var(--blue); }
 section { background:var(--panel); border:1px solid #2a333e; border-radius:14px;
        padding:1.1rem 1.4rem; margin:0 0 1.1rem; border-left:4px solid var(--acc,#7a8794);
        scroll-margin-top:1rem; }
 section h2 { margin:.1rem 0 .1rem; font-size:1.1rem; color:var(--acc,var(--text)); }
 section .tag { color:var(--dim); margin:.15rem 0 .8rem; font-size:.9rem; }
 .checks { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
        gap:.7rem; }
 .check { background:#11151a; border:1px solid #2e3946; border-radius:12px;
        padding:.7rem .9rem; border-left:4px solid var(--dim); }
 .check.ok { border-left-color:var(--green); }
 .check.bad { border-left-color:var(--red); background:#20161a; }
 .check.warn { border-left-color:var(--amber); }
 .check h4 { margin:0 0 .25rem; font-size:.94rem; }
 .check.ok h4::before { content:"\\2705  "; }
 .check.bad h4::before { content:"\\274C  "; }
 .check.warn h4::before { content:"\\26A0\\FE0F  "; }
 .check p { margin:0; font-size:.87rem; color:var(--dim); line-height:1.45; }
 .check .path { font-family:Consolas,monospace; font-size:.78rem; color:#5f6b78;
        word-break:break-all; }
 table { border-collapse:collapse; width:100%; }
 th, td { text-align:left; padding:.55rem .7rem; font-size:.9rem;
        border-bottom:1px solid #2a333e; vertical-align:top; }
 th { color:var(--dim); font-weight:600; font-size:.82rem; letter-spacing:.06em;
      text-transform:uppercase; }
 td:first-child { color:var(--dim); white-space:nowrap; font-family:Consolas,monospace;
        font-size:.84rem; }
 tr.good td:nth-child(3) b { color:var(--green); }
 tr.bad td:nth-child(3) b { color:var(--red); }
 .said { font-family:Consolas,monospace; color:var(--blue); max-width:230px; }
 .why { color:var(--dim); line-height:1.5; }
 .fix { color:var(--amber); }
 code { background:var(--field); border:1px solid #2e3946; border-radius:6px;
        padding:.05rem .35rem; font-size:.88em; color:#bfe3ff; }
 pre { background:#0e1216; border:1px solid #2a333e; border-radius:10px;
        padding:.9rem 1rem; overflow:auto; max-height:460px; font-size:.8rem;
        color:#9fb0c0; line-height:1.45; }
 .copybtn { background:var(--field); color:var(--text); border:1px solid #3d5a7a;
        border-radius:999px; padding:.55rem 1.1rem; font-size:.95rem; cursor:pointer;
        font-family:inherit; margin:0 0 .8rem; }
 .copybtn:hover { border-color:var(--blue); background:#2a3540; }
 footer { color:var(--dim); text-align:center; font-size:.85rem; margin-top:1.6rem; }
"""


def build(app) -> str:
    """Write troubleshoot.html from the running app and return its path."""
    check_html = "".join(
        f"<div class='check {st}'><h4>{html.escape(title)}</h4><p>{detail}</p></div>"
        for st, title, detail in checks(app))

    reason_rows = "".join(
        f"<tr><td style='color:var(--red);white-space:normal'>{html.escape(title)}</td>"
        f"<td class='why'>{meaning}</td><td class='why fix'>{fix}</td></tr>"
        for title, meaning, fix in REASONS.values())

    downstream_rows = "".join(
        f"<tr><td style='white-space:normal;color:var(--text)'>{sym}</td>"
        f"<td class='why'>{cause}</td><td class='why fix'>{fix}</td></tr>"
        for sym, cause, fix in DOWNSTREAM)

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CobbAttack — Troubleshoot</title><style>{CSS}</style></head><body>

<h1>🚑 <span class="em">TROUBLESHOOT</span></h1>
<p class="sub">Snapshot taken {time.strftime('%A %d %B %Y, %H:%M:%S')} · CobbAttack up for
{_uptime(app)} · reopen the page from the app to refresh it.</p>

<nav class="chips">
  <a class="chip" href="#live">🔎 Live check</a>
  <a class="chip" href="#session">🗒️ This session</a>
  <a class="chip" href="#reasons">❓ Why it was refused</a>
  <a class="chip" href="#downstream">📻 VoiceAttack &amp; VAICOM</a>
  <a class="chip" href="#log">📄 Log</a>
</nav>

<section id="live" style="--acc:#5dd08c">
<h2>🔎 Live check</h2>
<p class="tag">Everything that has to be true right now. Fix the red ones top to bottom.</p>
<div class="checks">{check_html}</div>
</section>

<section id="session" style="--acc:#5aa7e0">
<h2>🗒️ This session — every call, and what happened to it</h2>
<p class="tag">Newest first. Blue is what Whisper heard; the last column is why it did
what it did.</p>
<table><tr><th>Time</th><th>It heard</th><th>Result</th><th>Why / what to do</th></tr>
{_session_rows(app)}</table>
</section>

<section id="reasons" style="--acc:#e8b33e">
<h2>❓ Every reason a command can be refused</h2>
<p class="tag">CobbAttack never guesses. When it refuses, it is always one of these five.</p>
<table><tr><th>Message</th><th>What it means</th><th>What to do</th></tr>
{reason_rows}</table>
</section>

<section id="downstream" style="--acc:#e06c5b">
<h2>📻 It said "sent" — but VoiceAttack or VAICOM did the wrong thing</h2>
<p class="tag">Once the feed says <b>sent</b>, CobbAttack's job is finished: the exact
phrase in that line went to VoiceAttack. Anything wrong after that is one of these.</p>
<table><tr><th>Symptom</th><th>What's actually happening</th><th>What to do</th></tr>
{downstream_rows}</table>
</section>

<section id="log" style="--acc:#7a8794">
<h2>📄 Log — last 250 lines</h2>
<p class="tag">The whole file is <code>cobbattack.log</code> next to the app. If nothing
above explains it, hit the button — it copies the <b>file itself</b> to the clipboard,
so pasting into Discord attaches the complete log no matter how big it is.</p>
<button id="copylog" class="copybtn">📋 Copy log file for Discord</button>
<pre id="logpre">{_log_tail()}</pre>
<script>
document.getElementById('copylog').addEventListener('click', function () {{
  var btn = this;
  // Ask the running app to put cobbattack.log on the clipboard as a real file
  // (like Ctrl+C in Explorer). If CobbAttack is closed, copy the text instead.
  fetch('http://127.0.0.1:{config.IMPORT_PORT}/copy-log', {{method: 'POST'}})
    .then(function (r) {{ return r.json(); }})
    .then(function (j) {{ if (j.ok) {{ done(true, true); }} else {{ textCopy(); }} }})
    .catch(textCopy);
  function done(ok, isFile) {{
    if (!ok) {{  // blocked? pre-select the log so one Ctrl+C finishes the job
      var r = document.createRange();
      r.selectNodeContents(document.getElementById('logpre'));
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(r);
    }}
    btn.textContent = ok ? (isFile ? '✅ Log file copied — paste it in Discord'
                                   : '✅ Copied (last 250 lines) — paste it in Discord')
                         : '⚠️ Blocked — the log is selected for you, just press Ctrl+C';
    setTimeout(function () {{ btn.textContent = '📋 Copy log file for Discord'; }}, 6000);
  }}
  function textCopy() {{
    var text = '```\\n' + document.getElementById('logpre').textContent + '\\n```';
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(text).then(function () {{ done(true, false); }},
                                              function () {{ fallback(); }});
    }} else {{ fallback(); }}
    function fallback() {{
      var ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try {{ ok = document.execCommand('copy'); }} catch (e) {{}}
      document.body.removeChild(ta);
      done(ok, false);
    }}
  }}
}});
</script>
</section>

<footer>CobbAttack {_foot_icon()} · troubleshoot page</footer>
</body></html>"""

    with open(DST, "w", encoding="utf-8") as f:
        f.write(page)
    return DST


def _uptime(app):
    secs = int(time.time() - getattr(app, "started_at", time.time()))
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m {secs % 60}s"
    return f"{secs // 3600}h {(secs % 3600) // 60}m"
