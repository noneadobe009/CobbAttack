# VAICOM "works for the first mission only" — root cause found + fix

*Diagnosed 2026-07-26 on VAICOM CE 3.1.5.2 (Community Edition), DCS 2.9.x, Windows 11.
Draft write-up for posting to the VAICOM Community Discord / GitHub / ED forums.*

## The symptom (you probably know it)

- First mission after starting DCS: voice commands work, ATC/AWACS/wingmen answer.
- Restart the mission (Shift+R) or start a second mission: VoiceAttack still
  recognizes and keys your commands (`TX1 | [Air Traffic Controller], [Request Taxi
  to Runway]` shows in the log), but **nothing in the game ever answers**. Sometimes
  it degrades further to "DCS is not connected. Command processing is disabled."
- Only known cure until now: **fully restart DCS** between missions.

This matches long-standing community reports, e.g. ED forums "VAICOM working for
first mission only" and VAICOM-Community GitHub issue #136 (comm menu gone after a
2nd mission), which was closed undiagnosed.

## Root cause (proven live, not guessed)

VAICOM's DCS-side radio panel script (`Scripts/UI/RadioCommandDialogPanel/
RadioCommandDialogsPanel.lua`, the appended VAICOM section) receives commands on a
UDP socket bound to `127.0.0.1:33334`. Message path:

```
VoiceAttack plugin → UDP 33491 (VAICOM export script) → forwards → UDP 33334 (radio panel) → DCS world
```

On every mission restart, the panel's `init.stop()` **closes** the 33334 receiver
socket and `init.start()` **re-creates and re-binds** it.

Here's the killer detail: **on Windows, when several sockets are bound to the same
UDP port (SO_REUSEADDR), incoming unicast packets are delivered to the FIRST socket
that bound — not the newest.** Another socket in the DCS process ends up holding a
bind on 33334 (created at the same moment as the panel's first receiver; it survives
mission restarts). The moment the panel closes its original receiver, that other
socket inherits "first in line." The panel's *new* receiver binds successfully,
listens dutifully — and never receives a single byte. Every keyed command is
silently eaten. No lua errors, nothing in dcs.log. The radios are dead until DCS
restarts and the panel wins the front-of-line spot again.

### How it was proven

1. Debug beacons in the panel showed: after Shift+R, clean `release()` →
   `initialize()` → sockets rebuilt → loop running — yet **zero packets arriving**,
   while the plugin logged the commands as sent.
2. `netstat -ano -p UDP` showed **two sockets bound to 127.0.0.1:33334** inside
   DCS.exe after a mission restart (one created at first-mission init, one at
   restart init).
3. Decisive experiment: bound a **third** test socket to 33334 (newest binder)
   inside the live DCS lua state, pinged the port — the test socket received
   nothing, the panel's socket received nothing. Only the oldest binder gets
   traffic. First-binder-wins confirmed.

## The fix (small, surgical)

**Never give up the front-of-line spot: bind the receiver once per DCS session and
never close it.** Two edits in the VAICOM append of
`RadioCommandDialogsPanel.lua`:

In `base.vaicom.init.start`, create/bind the receiver **only if it doesn't already
exist**:

```lua
-- before:
base.vaicom.receiver = socket.try(socket.udp())
socket.try(base.vaicom.receiver:setsockname(base.vaicom.config.receiveaddress,base.vaicom.config.receiveport))
socket.try(base.vaicom.receiver:settimeout(base.vaicom.config.receivetimeout))

-- after:
if base.vaicom.receiver == nil then
    base.vaicom.receiver = socket.try(socket.udp())
    pcall(function() base.vaicom.receiver:setoption("reuseaddr", true) end)  -- use base.pcall in the GUI sandbox
    pcall(function() base.vaicom.receiver:setsockname(base.vaicom.config.receiveaddress,base.vaicom.config.receiveport) end)
    socket.try(base.vaicom.receiver:settimeout(base.vaicom.config.receivetimeout))
end
```

In `base.vaicom.init.stop`, **delete** (or comment out) the receiver close:

```lua
-- DELETE this block — closing the receiver forfeits packet delivery to a zombie
-- socket for the rest of the DCS session (Windows first-binder-wins):
if base.vaicom.receiver then
    socket.try(base.vaicom.receiver:close())
    base.vaicom.receiver = nil
end
```

The sender/relay sockets are outbound (connected via `setpeername`) — they can keep
being rebuilt each mission, no contention there.

**Result, user-confirmed:** call ATC → answer; Shift+R → same call → **answer**. No
DCS restart needed anymore.

## Caveats for anyone applying this by hand

- VAICOM **rewrites this lua file to stock every time VoiceAttack starts** (the
  template lives inside the plugin as `Resources/Files/Append.Core.RadioCommandDialogsPanel.lua`).
  A hand edit lasts until the next VoiceAttack launch. Options: re-apply after
  starting VoiceAttack, script the re-patch (we run an idempotent Python patcher at
  our app's startup), or — the right long-term fix — **patch the template in the
  VAICOM-Community source** so everyone gets it. (Our patcher: `vaicom_patch.py`
  in the CobbAttack project, panel edit #7 "keepalive receiver".)
- The GUI lua sandbox has no bare `pcall` — use `base.pcall` inside the panel file.
- DCS only reads the file at launch, so restart DCS once after patching.
- Related but separate bugs we hit on the way (also patched in `vaicom_patch.py`):
  the plugin's 60-second reconnect timer dies on a null after any mission end
  (`UI/Timer.cs`, ~line 134, `State.currentstate.id` null → "DCS is not connected"
  never recovers on its own), and `initialize()` can trip its own
  `assert(data.initialized == false)` when a mission ends without `release()`
  running. Worth fixing upstream at the same time.

## Identification of the zombie socket

Still open: the second 33334 bind is created within the same instant as the panel's
first receiver, is not any lua file's code we could find (only the panel binds
33334 anywhere in DCS or Saved Games), survives `collectgarbage("collect")` in the
panel's state, so it's live-referenced somewhere — possibly a duplicated handle at
the C/luasocket layer. Not needed for the fix, but a fun mystery for whoever
maintains VAICOM.

---
*Found by instrumenting the panel with UDP debug beacons, a live in-game lua probe
(GameGUI hook + `net.dostring_in`), `netstat` socket forensics, and a
binding-order experiment — full method available on request.*
