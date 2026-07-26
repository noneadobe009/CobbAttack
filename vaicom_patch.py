"""Re-apply the VAICOM second-mission fix that VoiceAttack erases on every start.

VAICOM CE (3.1.5.2) rewrites its DCS-side device script to stock each time
VoiceAttack launches. Stock has a bug: after a mission switch the old lua state
can keep UDP port 52341, post_initialize() dies before `dev_timer = 0`, and
every later mission logs "dev_timer (a nil value)" while VAICOM reports
"DCS is not connected". Three small edits make it survive:

  1. init dev_timer at declaration (no nil arithmetic),
  2. reuseaddr on the receiver socket (rebind past a leaked port),
  3. pcall(start) so a failed bind can't abort the rest of init.

Called at CobbAttack startup: by then VoiceAttack has usually done its rewrite,
and DCS only reads the file at mission load, so our timing wins. Harmless when
the file is already patched, VAICOM isn't installed, or DCS isn't found.
"""

import logging
import os
import re

log = logging.getLogger("cobb.vaicom")

DEVICE_REL = os.path.join(
    "Scripts", "Aircrafts", "_Common", "Cockpit", "VAICOMPRO", "device",
    "VAICOMPRO_Device.lua",
)
# VAICOM's modified radio-menu panel. Its init.start() opens three UDP sockets
# with socket.try in a row — all-or-nothing, no retry ever: one failed bind on a
# mission restart leaves sender/relay nil, the plugin never hears a heartbeat
# ("DCS is not connected"), and dcs.log fills with "'relay' (a nil value)".
# Worse, vaicom_loop removes itself ("KILL VAICOM LOOP") when sockets are nil.
# Three edits teach it to self-heal instead (observed live 2026-07-25).
PANEL_REL = os.path.join(
    "Scripts", "UI", "RadioCommandDialogPanel", "RadioCommandDialogsPanel.lua",
)
DCS_CANDIDATES = [
    r"C:\Games\DCS World",
    r"C:\Program Files\Eagle Dynamics\DCS World",
    r"C:\Program Files\Eagle Dynamics\DCS World OpenBeta",
    r"D:\Games\DCS World",
]


def _find_lua(settings, rel):
    roots = [settings.get("dcs_install", "")] + DCS_CANDIDATES
    for root in roots:
        if root:
            path = os.path.join(root, rel)
            if os.path.exists(path):
                return path
    return None


def _transform(text):
    """Patched text and how many edits were applied (0 = already patched)."""
    applied = 0
    if not re.search(r"local\s+dev_timer\s*=\s*0", text):
        text, n = re.subn(r"(local\s+dev_timer)([ \t]*\r?\n)", r"\1 = 0\2", text, count=1)
        applied += n
    if "reuseaddr" not in text:
        text, n = re.subn(
            r"(receiver = socket\.try\(socket\.udp\(\)\)[ \t]*\r?\n)([ \t]*)"
            r"(socket\.try\(receiver:setsockname)",
            "\\1\\2pcall(function() receiver:setoption(\"reuseaddr\", true) end)\n\\2\\3",
            text, count=1)
        applied += n
    if "pcall(start)" not in text:
        text, n = re.subn(r"(stop\(\)[ \t]*\r?\n[ \t]*)start\(\)", r"\1pcall(start)", text, count=1)
        applied += n
    return text, applied


def _transform_panel(text):
    """Self-healing edits for RadioCommandDialogsPanel.lua (0 = already patched)."""
    applied = 0
    # 1. receiver socket: reuseaddr + non-fatal bind, so one leaked port can't
    #    abort init.start halfway and leave relay nil.
    if "reuseaddr" not in text:
        text, n = re.subn(
            r"(base\.vaicom\.receiver = socket\.try\(socket\.udp\(\)\)[ \t]*\r?\n)"
            r"([ \t]*)socket\.try\(base\.vaicom\.receiver:setsockname\("
            r"([^)]*)\)\)",
            "\\1\\2base.pcall(function() base.vaicom.receiver:setoption(\"reuseaddr\", true) end)\n"
            "\\2base.pcall(function() base.vaicom.receiver:setsockname(\\3) end)",
            text, count=1)
        applied += n
    # 2. onMsgStart/onMsgFinish (they PROVABLY survive mission restarts): watchdog.
    #    If relay is gone or vaicom_loop hasn't ticked in 5 s (Shift+R kills it and
    #    nothing revives it — the plugin then never reconnects), rebuild sockets AND
    #    re-register the loop via init.start. Never let a send error kill the panel.
    if "_lastloop" not in text:
        text, n = re.subn(
            re.escape("socket.try(base.vaicom.relay:send(JSON:encode(sendtbl)))"),
            "if base.vaicom.relay == nil or (socket.gettime() - (base.vaicom._lastloop or 0)) > 5 then\n"
            "\t\tbase.pcall(base.vaicom.init.stop)\n"
            "\t\tbase.pcall(base.vaicom.init.start)\n"
            "\tend\n"
            "\tbase.pcall(function() base.vaicom.relay:send(JSON:encode(sendtbl)) end)",
            text)
        applied += n
    # 2b. Loop heartbeat + unsolicited state push every 20 s: reconnects the plugin
    #     (its own 60 s "beacon pulse" dies on a null after mission end — plugin bug)
    #     the moment the loop is alive, without waiting to be asked.
    if "_lastpush" not in text:
        text, n = re.subn(
            r"(local function vaicom_loop\(\)[ \t]*\r?\n)",
            "\\1\tbase.vaicom._lastloop = socket.gettime()\n"
            "\tif (socket.gettime() - (base.vaicom._lastpush or 0)) > 20"
            " and data.initialized and data.pUnit then\n"
            "\t\tbase.vaicom._lastpush = socket.gettime()\n"
            "\t\tbase.pcall(function() base.vaicom.state.sendupdateall() end)\n"
            "\tend\n",
            text, count=1)
        applied += n
    # 4. THE mission-restart killer (diagnosed live 2026-07-26): ending a mission
    #    doesn't always call release(), so the next mission's initialize() trips
    #    base.assert(data.initialized == false) and aborts BEFORE init.start() —
    #    loop never restarts, plugin says "DCS is not connected" until a full DCS
    #    restart. Heal: if stale state is present when initialize() runs, force
    #    release() (it guards itself and clears everything) and carry on.
    #    COBBDBG beacons (UDP → 127.0.0.1:33999, fire-and-forget) let us watch
    #    initialize/release/KILL live; harmless when nothing listens.
    if "COBBDBG" not in text:
        text, n = re.subn(
            r"(local[ \t]+Gui[ \t]+=[ \t]*base\.require\('dxgui'\)[ \t]*\r?\n)",
            "\\1local function COBBDBG(msg)\n"
            "\tbase.pcall(function()\n"
            "\t\tlocal u = socket.udp()\n"
            "\t\tu:setpeername(\"127.0.0.1\", 33999)\n"
            "\t\tu:send(\"[panel] \" .. msg)\n"
            "\t\tu:close()\n"
            "\tend)\n"
            "end\n",
            text, count=1)
        applied += n
        text, n = re.subn(
            r"(function initialize\(pUnitIn, easyComm, intercomId, communicators\)"
            r"[ \t]*\r?\n[ \t]*count=count\+1)",
            "\\1\n"
            "\tCOBBDBG(\"initialize called (stale=\" .. base.tostring(data.initialized) .. \")\")\n"
            "\tif data.initialized or data.communicators then\n"
            "\t\tbase.pcall(release)\n"
            "\t\tdata.communicators = nil\n"
            "\t\tCOBBDBG(\"stale state healed — continuing init\")\n"
            "\tend",
            text, count=1)
        applied += n
        text, n = re.subn(
            r"(base\.vaicom\.init\.stop\(\)[ \t]*\r?\n[ \t]*base\.vaicom\.init\.start\(\)[ \t]*\r?\n)(end)",
            "\\1\tCOBBDBG(\"initialize complete — loop started\")\n\\2",
            text, count=1)
        applied += n
        text, n = re.subn(
            re.escape('base.print("KILL VAICOM LOOP")'),
            "base.print(\"KILL VAICOM LOOP\")\n"
            "\t\tCOBBDBG(\"loop KILLED (initialized=\" .. base.tostring(data.initialized)"
            " .. \" pUnit=\" .. base.tostring(data.pUnit ~= nil) .. \")\")",
            text, count=1)
        applied += n
        text, n = re.subn(
            re.escape("--base.print('RadioCommandDialogPanel:release()')"),
            "--base.print('RadioCommandDialogsPanel:release()')\n"
            "\tbase.pcall(function() local sk = base.require('socket') local u = sk.udp()"
            " u:setpeername(\"127.0.0.1\", 33999) u:send(\"[panel] release() ran\") u:close() end)",
            text, count=1)
        applied += n
    # 5. Beacons in the command path (2026-07-26): after Shift+R the plugin
    #    reconnects and keys commands, but no AI reply and no sound activity in
    #    dcs.log. These show whether the aicomms message reaches the panel and
    #    what it does with it.
    if 'COBBDBG("recv' not in text:
        text, n = re.subn(
            re.escape("local clientmessage = base.vaicom.state.activemessage"),
            "local clientmessage = base.vaicom.state.activemessage\n"
            "\tCOBBDBG(\"recv type=\" .. base.tostring(clientmessage.type)"
            " .. \" cmd=\" .. base.tostring(clientmessage.command))",
            text, count=1)
        applied += n
        text, n = re.subn(
            r"selectAndTuneCommunicator\(unitcomm\)[ \t]*\r?\n",
            "selectAndTuneCommunicator(unitcomm)\n"
            "\t\tCOBBDBG(\"aicomms cmd=\" .. base.tostring(clientmessage.command)"
            " .. \" unitcomm=\" .. base.tostring(unitcomm)"
            " .. \" tgt=\" .. base.tostring(tgtunit)"
            " .. \" pComm=\" .. base.tostring(data.pComm ~= nil)"
            " .. \" pUnit=\" .. base.tostring(data.pUnit ~= nil))\n",
            text, count=1)
        applied += n
        text, n = re.subn(
            re.escape("purgeMessage:perform()"),
            "purgeMessage:perform()\n\t\tCOBBDBG(\"aicomms perform done\")",
            text, count=1)
        applied += n
    # 6. Socket-generation fix + beacons (2026-07-26): after Shift+R, netstat
    #    showed TWO sockets bound to 33334 in DCS — an orphaned old receiver was
    #    eating every inbound command (reuseaddr made the double-bind silent).
    #    start() now force-closes any existing handles before creating new ones,
    #    stop()'s closes are made non-aborting, and both log their generations.
    if 'base.vaicom._gen' not in text:
        text, n = re.subn(
            r"(start = function\(self\)[ \t]*\r?\n)",
            "\\1\t\tbase.vaicom._gen = (base.vaicom._gen or 0) + 1\n"
            "\t\tCOBBDBG(\"init.start gen=\" .. base.tostring(base.vaicom._gen)"
            " .. \" oldrecv=\" .. base.tostring(base.vaicom.receiver))\n"
            "\t\tif base.vaicom.receiver then base.pcall(function() base.vaicom.receiver:close() end) end\n"
            "\t\tif base.vaicom.sender then base.pcall(function() base.vaicom.sender:close() end) end\n"
            "\t\tif base.vaicom.relay then base.pcall(function() base.vaicom.relay:close() end) end\n",
            text, count=1)
        applied += n
        text, n = re.subn(
            r"(socket\.try\(base\.vaicom\.relay:settimeout\(base\.vaicom\.config\.relaytimeout\)\)[ \t]*\r?\n)",
            "\\1\tCOBBDBG(\"init.start done recv=\" .. base.tostring(base.vaicom.receiver))\n",
            text, count=1)
        applied += n
        text, n = re.subn(
            r"(stop = function\(self\)[ \t]*\r?\n)",
            "\\1\t\tCOBBDBG(\"init.stop recv=\" .. base.tostring(base.vaicom.receiver))\n",
            text, count=1)
        applied += n
        for sock in ("sender", "receiver", "relay"):
            text, n = re.subn(
                re.escape("socket.try(base.vaicom.%s:close())" % sock),
                "base.pcall(function() base.vaicom.%s:close() end)" % sock,
                text, count=1)
            applied += n
    # 7. Keepalive receiver (2026-07-26, proven live): Windows delivers UDP on a
    #    shared port to the FIRST bound socket. A zombie socket (created in the
    #    same instant as the panel's first receiver) becomes first-in-line the
    #    moment the panel closes its receiver on mission restart, and silently
    #    eats every inbound command (verified: a fresh last-bound test socket
    #    received nothing). Fix: bind the receiver ONCE per DCS run and never
    #    close it — the panel keeps its winning first-binder slot forever.
    if "base.vaicom.receiver == nil" not in text:
        text, n = re.subn(
            r"[ \t]*if base\.vaicom\.receiver then base\.pcall\(function\(\) "
            r"base\.vaicom\.receiver:close\(\) end\) end[ \t]*\r?\n",
            "", text, count=1)
        applied += n
        text, n = re.subn(
            r"([ \t]*)base\.vaicom\.receiver = socket\.try\(socket\.udp\(\)\)[ \t]*\r?\n"
            r"[ \t]*base\.pcall\(function\(\) base\.vaicom\.receiver:setoption\(\"reuseaddr\", true\) end\)[ \t]*\r?\n"
            r"[ \t]*base\.pcall\(function\(\) base\.vaicom\.receiver:setsockname\(base\.vaicom\.config\.receiveaddress,base\.vaicom\.config\.receiveport\) end\)[ \t]*\r?\n"
            r"[ \t]*socket\.try\(base\.vaicom\.receiver:settimeout\(base\.vaicom\.config\.receivetimeout\)\)[ \t]*\r?\n",
            "\\1if base.vaicom.receiver == nil then\n"
            "\\1\tbase.vaicom.receiver = socket.try(socket.udp())\n"
            "\\1\tbase.pcall(function() base.vaicom.receiver:setoption(\"reuseaddr\", true) end)\n"
            "\\1\tbase.pcall(function() base.vaicom.receiver:setsockname(base.vaicom.config.receiveaddress,base.vaicom.config.receiveport) end)\n"
            "\\1\tsocket.try(base.vaicom.receiver:settimeout(base.vaicom.config.receivetimeout))\n"
            "\\1\tCOBBDBG(\"receiver bound once (keepalive)\")\n"
            "\\1end\n",
            text, count=1)
        applied += n
        text, n = re.subn(
            r"[ \t]*if base\.vaicom\.receiver then[ \t]*\r?\n"
            r"[ \t]*base\.pcall\(function\(\) base\.vaicom\.receiver:close\(\) end\)[ \t]*\r?\n"
            r"[ \t]*base\.vaicom\.receiver = nil[ \t]*\r?\n"
            r"[ \t]*end[ \t]*\r?\n",
            "", text, count=1)
        applied += n
    # 3. vaicom_loop: while in a live mission with missing sockets, rebuild them
    #    instead of hitting the KILL branch and going deaf until DCS restarts.
    if "not base.vaicom.sender or not base.vaicom.relay" not in text:
        text, n = re.subn(
            r"([ \t]*)(if base\.vaicom and base\.vaicom\.devicecontrol and "
            r"base\.vaicom\.devicecontrol\.busy then)",
            "\\1if base.vaicom and data.initialized and data.pUnit and\n"
            "\\1\t\t(not base.vaicom.receiver or not base.vaicom.sender or not base.vaicom.relay) then\n"
            "\\1\tbase.pcall(base.vaicom.init.stop)\n"
            "\\1\tbase.pcall(base.vaicom.init.start)\n"
            "\\1end\n"
            "\\1\\2",
            text, count=1)
        applied += n
    return text, applied


def _patch_file(path, transform, label):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        patched, applied = transform(text)
        if applied:
            with open(path, "w", encoding="utf-8") as f:
                f.write(patched)
            log.info("%s applied (%d edits): %s", label, applied, path)
        else:
            log.info("%s already in place", label)
    except OSError as e:
        log.warning("could not apply %s: %s", label, e)


def apply(settings):
    device = _find_lua(settings, DEVICE_REL)
    if device is None:
        log.info("VAICOM device script not found — skipping patch (fine if no VAICOM/DCS)")
        return
    _patch_file(device, _transform, "VAICOM second-mission fix")
    panel = _find_lua(settings, PANEL_REL)
    if panel is not None:
        _patch_file(panel, _transform_panel, "VAICOM radio-panel self-heal")
