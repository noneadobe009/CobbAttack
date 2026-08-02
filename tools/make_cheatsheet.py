"""Build commands-cheatsheet.html — the in-app flight guide — from vaicom_keywords.txt.

Self-contained dark page (CobbAttack's 📖 Commands button opens it; ships to Cobb).
Front page: how-to-speak rules + the six-call "first flight" script. Then sections in
flight order; mid-flight sections group by who you call (wingman/AWACS/tanker/JTAC),
because that's how a pilot thinks in the moment. Everyday calls sit on top of each
section; the long tail hides behind "show all". Search always wins over structure.

Classification is keyword heuristics over the profile's own phrase list, so the guide
can never claim a command the profile doesn't have. Regenerate after any VAICOM
keywords rebuild: export AI Communications "When I say" → vaicom_keywords.txt → run.
"""

import base64
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "vaicom_keywords.txt")
DST = os.path.join(ROOT, "commands-cheatsheet.html")

# (key, icon, title, tagline, regex) — first match wins, order matters.
SECTIONS = [
    ("ground", "🔧", "Before start — ground crew",
     "Talk to the chief on your normal talk button (TX1) — he's always listening.",
     r"rearm|ground power|ground electric|chocks|wheel|ladder|boarding|canopy|"
     r"connect|disconnect|air supply|ground air|refuel and|and rearm|stores|"
     r"chaff|flare|gun ?load|tire|repair|clean the|windshield|remove|install|"
     r"launch bar|hook up|salute|request launch|down lock|pin"),
    ("startup", "🛫", "Startup & taxi",
     "First radio calls of the day — clearance to start and roll.",
     r"startup|start up|taxi to runway|taxi for|taxi clearance|taxi to active|"
     r"radio check|check in with|abort start"),
    ("takeoff", "✈️", "Takeoff & departure",
     "Cleared for takeoff, climbing out, leaving the pattern.",
     r"takeoff|take off|departure|airborne|rolling|unrestricted climb|"
     r"request departure|switch to departure"),
    ("wingman", "⚔️", "Combat — wingman & flight",
     "Orders to Two / your element / the whole flight.",
     r"engage|attack|strike|weapons (free|hold|tight)|cleared to|cover|rejoin|"
     r"formation|spread|trail|wedge|echelon|line abreast|route|fluid|break |"
     r"anchor|sanitize|clear my six|go (active|spread|trail)|bandit|threat|"
     r"mission complete|resume|hold fire|fence|music|sort|target my|"
     r"my target|flight,|pincer|posit|status|drop tanks|glint|smash|burner"),
    ("awacs", "📡", "AWACS — the big picture",
     "Ask the controller what's out there and where to go.",
     r"picture|bogey|declare|alpha check|snaplock|cutoff|vector|home plate|"
     r"request relief|commit|judy|clean|naked|spiked|mud spike|strangle|"
     r"tactical|braa|check ?out|request bra|(left|right) go|go (port|starboard)|"
     r"kick out|flow (north|south|east|west)|skunk|copy kill|playtime|bda|"
     r"heading .* go|steady"),
    ("tanker", "⛽", "Air refueling — tanker",
     "Getting gas: from intent to plugged-in.",
     r"pre.?contact|intent to refuel|refuel(l)?ing complete|abort refuel|"
     r"how much fuel|tanker|drogue|basket|top (me )?off|ready to receive|"
     r"request refuel"),
    ("jtac", "🎯", "JTAC — close air support",
     "Checking in with the ground controller and running attacks.",
     r"9.?line|nine.?line|ready to copy|in from|in hot|laser on|laser off|"
     r"sparkle|type (one|two|three)|contact the|abort abort|check.?in|"
     r"immediate|troops"),
    ("jester", "🐱", "F-14 — Jester (your RIO)",
     "Backseat commands for the Tomcat: radar, nav, TACAN, the works. "
     "“Jester” and “RIO” both work.",
     r"jester|\brio\b|tacan tune|link tune|scan sector|track marker|"
     r"scan elevation|switch stt|\bvsl\b|pulse doppler|pd search|pulse search|"
     r"switch tws|switch rws|stab (on|off)|jamming|nav grid|navgrid"),
    ("george", "🚁", "AH-64 — George (your gunner)",
     "Apache front seat: weapons, targets, and flying the guns.",
     r"george|gunner"),
    ("wso", "🎓", "F-4 — Boots, your WSO",
     "In-game he's Jester, but the Phantom radio ONLY answers to Boots, Wizzo or "
     "WSO (“Jester” is reserved for the F-14) — e.g. “Boots, hold current turn point”.",
     r"wizzo|\bwso\b|\bboots\b|turn point|hold waypoint|deactivate waypoint|"
     r"cycle waypoint|select waypoint"),
    ("crewai", "🤖", "Crew AI — everything else in the cockpit",
     "Generic crew commands: radar modes, systems, countermeasures.",
     r"tads|radar|scan|tws|ripple|grid|zoom|slave|"
     r"burst|laser code|countermeasure|angels|turn (left|right)|come (left|right)|"
     r"call me|below \d|feet|track|acquisition|rocket|missile|weapon|store|"
     r"hover|controls|flame out|search|boresight|pilot night|fcr|ihadss|"
     r"waypoint|iff|alignment|auto focus"),
    ("landing", "🛬", "Arrival & landing",
     "Coming home: inbound call to touchdown (field and boat).",
     r"inbound|landing|pattern|overhead|straight in|final|touch and go|"
     r"low approach|fuel state|ball|marshal|case (one|two|three)|see you at|"
     r"platform|commencing|established|missed approach|wave.?off|bingo|divert|"
     r"gear (down|check)|long in the groove|azimuth|glidepath|needles|bullseye|"
     r"clara|paddles|groove|bolter|mother|passing|abeam|deck|hook|"
     r"instrument approach|full stop|on base|base to land|squawk|g ?c ?a|"
     r"airboss|grades"),
    ("after", "🅿️", "After landing",
     "Off the runway, back to the ramp, engines off.",
     r"taxi to parking|to parking|shutdown|shut down|parking|abort takeoff"),
    ("radios", "🎚️", "Radios & systems",
     "Tuning, channels, TACAN, options — housekeeping calls.",
     r"tune|channel|frequency|tacan|select|radio (one|two)|com(m)? (one|two)|"
     r"preset|button [0-9]|options|take command|disregard"),
]

# Per-section accent color — cells and headers take the section's hue.
ACCENTS = {
    "ground": "#e8a04b", "startup": "#5dd08c", "takeoff": "#5aa7e0",
    "wingman": "#e06c5b", "awacs": "#a98ae8", "tanker": "#4ecdc4",
    "jtac": "#b8cc5a", "crewai": "#e08ac2", "landing": "#e8c94b",
    "jester": "#e8a0c8", "wso": "#c8a0e8", "george": "#a0e8c0",
    "after": "#8fa3b8", "radios": "#6bd0e8", "other": "#7a8794",
    "callsigns": "#7a8794",
}

# Hover explanations for jargon-heavy phrases. First regex match wins; phrases
# with no match get no tooltip (plain English needs no help).
DESCRIPTIONS = [
    (r"\bpicture\b", "Ask AWACS for the big overview: what's flying out there and where."),
    (r"bogey dope", "Ask AWACS for bearing, range and altitude of the nearest unknown/threat."),
    (r"\bdeclare\b", "Ask AWACS whether a contact is friendly or hostile."),
    (r"alpha check", "Ask for bearing and distance to a reference point (checks your nav)."),
    (r"home plate", "Your home airfield or carrier."),
    (r"\bbraa\b", "Bearing, Range, Altitude, Aspect — a contact's position relative to YOU."),
    (r"\bbullseye\b", "Position given relative to the mission's agreed reference point."),
    (r"\bcommit\b", "Start the intercept — you're taking the fight."),
    (r"\bjudy\b", "You have radar contact and will finish the intercept without AWACS help."),
    (r"\bclean\b", "Your radar scope shows nothing."),
    (r"\bnaked\b", "No radar warning indications on you."),
    (r"\bspiked\b", "Your radar warning receiver shows a threat locked on you."),
    (r"mud spike", "Ground radar (SAM) painting you on the warning receiver."),
    (r"\bskunk\b", "Unknown surface (ship) contact."),
    (r"weapons free", "Shoot anything not positively identified as friendly."),
    (r"weapons hold", "Hold fire — shoot only in self-defense or on direct order."),
    (r"weapons tight", "Shoot only targets positively identified hostile."),
    (r"\bsort\b", "Assign who shoots which contact in a group."),
    (r"\bpincer\b", "Split and attack the group from two sides."),
    (r"\bsanitize\b", "Search and clear a sector."),
    (r"\banchor\b", "Orbit and hold at a location."),
    (r"fence in", "Combat checks entering hostile airspace: weapons, sensors, lights."),
    (r"fence out", "Reverse combat checks when leaving hostile airspace."),
    (r"\bmusic\b", "Radar jamming."),
    (r"\bstrangle\b", "Turn OFF the named system (transponder, jammer...)."),
    (r"\bgate\b", "Fly as fast as the jet will go."),
    (r"\bplaytime\b", "How long you can stay before fuel forces you home."),
    (r"\bposit\b", "Report your position."),
    (r"\bstatus\b", "Report what you're doing / your situation."),
    (r"\bwords\b", "Any instructions or information for me?"),
    (r"\bbingo\b", "Fuel state: just enough left to make it home."),
    (r"\bjoker\b", "Fuel state: time to start wrapping up the fight."),
    (r"ready pre.?contact", "Tell the tanker you're stable behind the boom/basket, ready to plug in."),
    (r"intent to refuel", "Announce you're coming to the tanker for gas."),
    (r"9.?line|nine.?line", "The standard 9-item attack briefing a JTAC reads you."),
    (r"\bin hot\b", "Rolling in on the attack, weapons coming off."),
    (r"\bin dry\b", "Practice pass — no weapons released."),
    (r"cleared hot", "JTAC approves weapons release on this pass."),
    (r"\bsparkle\b", "Mark the target with an IR pointer."),
    (r"type (one|two|three)", "JTAC control level: 1 sees target+aircraft, 2 sees one, 3 = multiple attacks cleared."),
    (r"\bcase one\b", "Carrier recovery: daytime, good weather, visual overhead pattern."),
    (r"\bcase two\b", "Carrier recovery: marginal weather — instruments until you see the boat."),
    (r"\bcase three\b", "Carrier recovery: night/bad weather, full instrument approach."),
    (r"\bclara\b", "Ball call: I do NOT see the glideslope lights."),
    (r"\bball\b", "I see the carrier's landing light ('meatball') — starting the graded pass."),
    (r"\bpaddles\b", "The Landing Signal Officer who grades and guides carrier landings."),
    (r"\bmother\b", "The carrier."),
    (r"\bplatform\b", "Descending through 5,000 ft on a night carrier approach."),
    (r"\bcommencing\b", "Leaving the holding stack to start the carrier approach."),
    (r"\bmarshal\b", "The carrier's holding pattern controller."),
    (r"\bbolter\b", "Missed all the wires — full power, go around."),
    (r"see you at ten", "Checking in with the carrier at 10 miles."),
    (r"\bchocks\b", "The wheel blocks ground crew put around the tires."),
    (r"hold current turn", "Keep circling the point you're on now."),
    (r"\btally\b", "I SEE the enemy."),
    (r"\bvisual\b", "I SEE the friendly (or named object)."),
    (r"\bblind\b", "I've lost sight of my flight member."),
    (r"\bno joy\b", "I do NOT see the target/bandit."),
    (r"\bdefensive\b", "I'm under attack and maneuvering to survive."),
    (r"\bengaged\b", "Actively fighting a bandit right now."),
    (r"\bpress\b", "Continue the attack — I'm supporting you."),
    (r"\bskip it\b", "Break off the attack."),
    (r"\bscram\b", "Get out of there NOW (toward the given direction)."),
    (r"\bnotch\b", "Turn the radar threat to your 3/9 line to defeat its lock."),
    (r"\bdrag\b", "Turn cold and run, pulling the bandit with you."),
    (r"\bshackle\b", "Weave — swap sides with your wingman once."),
    (r"\bkick out\b", "Widen the formation."),
    (r"\bclose up\b", "Tighten the formation."),
    (r"\bin place\b", "Everyone turns where they are (formation keeps its shape)."),
    (r"\bcross turn\b", "Flight turns through each other to reverse direction."),
    (r"\bwedge\b|\bechelon\b|line abreast|\btrail\b", "A formation shape."),
    (r"\bripple\b", "Fire several in a timed series instead of one at a time."),
    (r"\btads\b", "The Apache's targeting sensor (Target Acquisition and Designation Sight)."),
    (r"\bfcr\b", "Fire Control Radar."),
    (r"\bihadss\b", "The Apache's helmet sight."),
    (r"laser code", "The code weapon and laser must share for guided hits."),
    (r"\btws\b", "Track-While-Scan radar mode — track several targets at once."),
    (r"\bsquawk\b", "Set the transponder to this code."),
    (r"\bg ?c ?a\b", "Ground Controlled Approach — a controller talks you down."),
    (r"\bpigeons\b", "Bearing and range to a destination."),
    (r"\bwilco\b", "Will comply."),
    # ATC & pattern
    (r"request startup", "Ask ATC for permission to start engines."),
    (r"taxi to runway", "Ask clearance to taxi to the active runway."),
    (r"request takeoff", "Ask for takeoff clearance."),
    (r"radio check", "Ask if your transmission is being heard."),
    (r"unrestricted climb", "Ask to climb as steep/fast as you like after takeoff."),
    (r"touch and go", "Land and immediately take off again (practice)."),
    (r"low approach", "Fly the approach but don't touch down."),
    (r"straight in", "Skip the pattern — approach the runway directly."),
    (r"\boverhead\b", "The military arrival: fly over the field, break, land from the circuit."),
    (r"\bdownwind\b", "Pattern leg flying parallel to the runway, opposite landing direction."),
    (r"missed approach", "Abort the landing and fly the published go-around."),
    (r"\bgo.around\b", "Abort this landing attempt, climb, and come around again."),
    (r"full stop", "A landing to a complete stop (not a touch-and-go)."),
    (r"fuel state", "Report how much fuel you have left."),
    (r"gear check", "Ask them to confirm your landing gear looks down."),
    (r"directions to base", "Ask for a heading home."),
    (r"instrument approach", "A guided approach flown on instruments through weather."),
    (r"\bdivert\b", "Head to the alternate airfield instead."),
    # Ground crew
    (r"ground power|ground electric", "Connect/disconnect external electrical power."),
    (r"ground air|air supply", "Connect the external air cart used to start engines."),
    (r"rearm and refuel", "Full turnaround: weapons and fuel."),
    (r"boarding ladder", "The ladder you climb to the cockpit."),
    (r"request launch", "Carrier deck: ready for catapult launch."),
    (r"\bsalute\b", "Signal the catapult officer you're ready to be shot off the deck."),
    (r"launch bar", "The nose-gear bar that hooks into the catapult."),
    (r"wheel chocks", "Blocks around the tires so the jet can't roll."),
    (r"\bstores\b", "The weapons and pods loaded on the jet."),
    (r"\bchaff\b", "Radar decoys you dispense."),
    (r"\bflares?\b", "Heat decoys against IR missiles."),
    (r"damage report", "Ask the crew how banged up the jet is."),
    # AWACS & controller
    (r"request relief", "Ask permission to leave your station and go home."),
    (r"request tasking", "Ask the controller for a job to do."),
    (r"vector to tanker", "Ask for a heading to the tanker."),
    (r"\bsnaplock\b", "Emergency call: immediate bearing/range on a threat very close."),
    (r"\bcutoff\b", "Intercept geometry that cuts the target off ahead of its track."),
    (r"(left|right) go\b", "Controller-style turn order: that many degrees, that way, now."),
    (r"\bflow\b", "Whole formation: head that direction."),
    (r"copy kill", "Controller confirms your kill."),
    (r"\bsteady\b", "Stop turning — hold this heading."),
    (r"\boutbound\b", "Heading away from the point/gate named."),
    (r"\bbda\b", "Bomb Damage Assessment — what did the strike destroy?"),
    # Combat & formation
    (r"engage my target", "Attack the thing I have locked up."),
    (r"engage bandits", "Attack the hostile aircraft."),
    (r"\bcover\b", "Protect me / watch my back while I act."),
    (r"break (left|right|high|low)", "EMERGENCY: hard defensive turn that way, NOW."),
    (r"buddy spike", "That radar lock on you is ME — friendly, don't shoot."),
    (r"go active", "Missiles/radar to active mode."),
    (r"drop tanks", "Jettison the external fuel tanks."),
    (r"\bresume\b", "Go back to what you were doing before."),
    (r"hold fire", "Do not shoot."),
    (r"clear my six", "Check (and clear) behind me."),
    (r"mission complete", "Job's done."),
    (r"\bburner\b", "Afterburner."),
    (r"close group|close up", "Tighten the formation."),
    (r"open up", "Widen the formation."),
    (r"go (port|starboard)", "Naval: turn left (port) / right (starboard)."),
    (r"\bninety\b", "A 90-degree turn."),
    (r"\bthreat\b", "Warning: hostile in a position to hurt you."),
    (r"reference point", "The agreed map point everyone measures from."),
    # Tanker
    (r"returning pre.?contact", "Going back to the waiting position behind the tanker."),
    (r"refuel(l)?ing complete", "Done taking gas."),
    (r"abort refuel", "Breaking off the refueling."),
    (r"how much fuel", "Ask the tanker what it can give you."),
    # Crew AI
    (r"\bgeorge\b", "The Apache's AI co-pilot/gunner — these are orders to him."),
    (r"\bjester\b", "The F-4's AI backseater."),
    (r"\bgunner\b", "Order to the Apache's AI gunner."),
    (r"\bslave\b", "Point the sensor where I'm looking."),
    (r"\bboresight\b", "Align the sensor/weapon straight ahead."),
    (r"acquisition", "The source the sensor uses to find targets."),
    (r"burst limit", "How many rounds per trigger pull."),
    (r"weapon select|select (gun|rockets|missiles)", "Choose which weapon is active."),
    (r"call me", "Ask the AI to remind you at that altitude/moment."),
    (r"\bangels\b", "Altitude in thousands of feet — 'angels 20' = 20,000 ft."),
    (r"turn (left|right) \d", "Heading change by that many degrees."),
    (r"simulated flame out", "Practice a landing as if the engine died."),
    (r"latch laser", "Keep the laser firing continuously."),
    (r"pave spike", "The F-4's laser designator pod."),
    (r"countermeasures", "The chaff/flare dispensing system."),
    (r"\biff\b", "The transponder that answers 'friend' when radar interrogates."),
    (r"\balignment\b", "The INS gyro alignment — the jet learning where it is."),
    (r"steerpoint|waypoint|turn point", "A navigation point in your route."),
    (r"scan (high|low|left|right|sector|\d)", "Where the radar/sensor should search."),
    (r"track (next|previous|left|right)", "Step the sensor between detected targets."),
    (r"\bripple distance\b", "Spacing between weapons in a ripple release."),
    # Radios & systems
    (r"\btacan\b", "Military nav beacon giving bearing and distance."),
    (r"\bpreset\b|channel \d", "A saved radio frequency slot."),
    (r"radio mode", "AM/FM/TR — TR means transmit and receive."),
    (r"\bdatalink\b|\blink\b", "Digital data sharing between aircraft."),
    (r"\btune\b", "Set the radio/nav to that station."),
    (r"\bdisregard\b", "Ignore my last call."),
    (r"say again", "Repeat your last transmission."),
    (r"some silence", "Quiet the radio chatter."),
    (r"talk to me", "Resume the radio chatter."),
    (r"take command", "Transfer flight lead."),
    (r"show my grades", "Carrier: show my landing scores."),
]

# Everyday calls pinned (bold, always visible) at the top of their section.
STARRED = {
    "request startup", "request taxi to runway", "request takeoff",
    "inbound", "request landing", "taxi to parking", "request refueling",
    "rearm and refuel", "request rearming", "request launch",
    "engage bandits", "engage my target", "attack my target", "rejoin",
    "weapons free", "break right", "break left",
    "picture", "bogey dope", "declare", "vector to home plate",
    "ready pre-contact", "intent to refuel", "request relief",
    "check in", "ready to copy 9 line", "in from the north", "in hot",
    "fuel state", "request azimuth", "gear check", "see you at ten",
    "radio check", "shutdown",
}


def split_top(text):
    parts, depth, cur = [], 0, []
    for ch in text:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def parse(text):
    """(command phrases, recipient/callsign names) from the whole export.

    In a multipart alternative the last bracket group carries the commands;
    earlier groups are optional recipient prefixes (Tower, airfield names,
    wingman callsigns) — reference material, not commands."""
    commands, recipients = set(), set()
    for alt in split_top(text):
        groups = re.findall(r"\[([^\]]*)\]", alt)
        if not groups:
            commands.add(alt.strip())
            continue
        for g in groups[:-1]:
            recipients.update(o.strip() for o in g.split(";") if o.strip())
        commands.update(o.strip() for o in groups[-1].split(";") if o.strip())
    return commands - recipients, recipients


def classify(phrase):
    low = phrase.lower()
    for key, _, _, _, pattern in SECTIONS:
        if re.search(pattern, low):
            return key
    return "other"


def main():
    if not os.path.exists(SRC):
        sys.exit(f"missing {SRC} — paste the VAICOM keyword export there first")
    with open(SRC, "r", encoding="utf-8-sig") as f:
        text = f.read().strip()

    commands, recipients = parse(text)
    buckets = {key: set() for key, *_ in SECTIONS}
    buckets["other"] = set()
    for p in commands:
        buckets[classify(p)].add(p)

    desc_res = [(re.compile(rx, re.I), txt) for rx, txt in DESCRIPTIONS]

    def item(p):
        star = p.lower() in STARRED
        cls = "cmd star" if star else "cmd"
        tip = next((t for rx, t in desc_res if rx.search(p)), None)
        if tip:
            return (f'<li class="{cls} tip" data-tip="{html.escape(tip, quote=True)}">'
                    f'{html.escape(p)}</li>')
        return f'<li class="{cls}">{html.escape(p)}</li>'

    def section_html(key, icon, title, tagline):
        phrases = sorted(buckets[key], key=str.lower)
        if not phrases:
            return ""
        starred = [p for p in phrases if p.lower() in STARRED]
        rest = [p for p in phrases if p.lower() not in STARRED]
        top = "".join(item(p) for p in starred)
        tail = "".join(item(p) for p in rest)
        block = f'<ul class="cmds">{top}</ul>' if top else ""
        if tail:
            block += (f'<details class="more"><summary>show all {len(rest)} commands'
                      f' ▾</summary><ul class="cmds">{tail}</ul></details>')
        return (f'<section class="sec" id="{key}" style="--acc:{ACCENTS.get(key, "#7a8794")}">'
                f'<h2>{icon} {html.escape(title)}</h2>'
                f'<p class="tag">{html.escape(tagline)}</p>{block}</section>')

    sections_html = "".join(section_html(k, i, t, g) for k, i, t, g, _ in SECTIONS)
    other = sorted(buckets["other"], key=str.lower)
    if other:
        sections_html += (
            f'<section class="sec" id="other" style="--acc:{ACCENTS["other"]}">'
            f'<h2>📦 More commands</h2>'
            f'<p class="tag">Everything else in the profile — search finds these too.</p>'
            f'<details class="more"><summary>show all {len(other)} commands ▾</summary>'
            f'<ul class="cmds">{"".join(item(p) for p in other)}</ul></details></section>')
    if recipients:
        names = sorted(recipients, key=str.lower)
        sections_html += (
            f'<section class="sec" id="callsigns" style="--acc:{ACCENTS["callsigns"]}">'
            f'<h2>🗺️ Airfields &amp; callsigns</h2>'
            f'<p class="tag">Names you can put in front of a call ("Batumi, request '
            f'taxi…") — always optional.</p>'
            f'<details class="more"><summary>show all {len(names)} names ▾</summary>'
            f'<ul class="cmds">{"".join(item(p) for p in names)}</ul></details></section>')

    nav = "".join(
        f'<a class="chip" href="#{k}">{i} {html.escape(t.split(" — ")[0])}</a>'
        for k, i, t, g, _ in SECTIONS if buckets[k])

    # The user's own commands (custom_commands.txt, generated from their .vap
    # profile export by custom_vap.py). The section always exists — with the
    # commands when there are any, and the how-to either way.
    custom_path = os.path.join(ROOT, "custom_commands.txt")
    custom = []
    if os.path.exists(custom_path):
        with open(custom_path, "r", encoding="utf-8") as f:
            custom = sorted({ln.strip() for ln in f
                             if ln.strip() and not ln.startswith("#")}, key=str.lower)
    howto = (
        f'<p><b>How to add one:</b></p><ol>'
        f'<li>Make the command in VoiceAttack: pencil icon → <b>New Command</b> → '
        f'type the "When I say" phrase and add what it should do (key press etc.).</li>'
        f'<li>Export the profile: VoiceAttack main window → profile menu → '
        f'<b>Export Profile</b> → save the <code>.vap</code> file into the '
        f'<b>CobbAttack folder</b> (overwrite the old one every time).</li>'
        f'<li>Restart CobbAttack. Done — the phrase now works when spoken, and this '
        f'page rebuilds itself with your command listed here.</li></ol>'
        f'<p style="color:var(--dim)">Re-export after every new command. If a spoken '
        f'command does nothing but clicking it works, you forgot to re-export.</p>')
    if custom:
        # commands exist: just the list, how-to collapsed out of the way
        body = ('<ul class="cmds">'
                + "".join(f'<li class="cmd star">{html.escape(p)}</li>' for p in custom)
                + "</ul>"
                + f'<details class="more"><summary>how to add more ▾</summary>'
                  f'{howto}</details>')
    else:
        body = ('<p style="color:var(--dim)">None yet — your commands will appear '
                'here automatically once you follow the steps below.</p>' + howto)
    dropzone = (
        '<div id="vapdrop" style="border:2px dashed #4a5563;border-radius:12px;'
        'padding:14px 16px;margin:6px 0 14px;color:#9aa7b4;cursor:pointer;'
        'text-align:center">'
        '⬇ Drop your VoiceAttack profile export (<b>.vap</b>) here — or click to pick a file'
        '<br><span style="font-size:.8rem">CobbAttack must be running — your commands are '
        'learned instantly and this page refreshes itself</span></div>'
        '<input type="file" id="vapfile" accept=".vap" style="display:none">')
    drop_js = """
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
   .then(function(j){ if(j.count>=0){done('✓ imported — '+j.count+' commands · reloading…');
        setTimeout(function(){location.reload();},1400);}
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
</script>"""
    sections_html += (
        f'<section class="sec" id="custom" style="--acc:#f0d060">'
        f'<h2>⚙️ Your custom commands</h2>'
        f'<p class="tag">Your own VoiceAttack commands — anything you build yourself, '
        f'like "turn on the lights" flipping a cockpit switch.</p>'
        f'{dropzone}{body}{drop_js}</section>')
    nav += '<a class="chip" href="#custom">⚙️ Your commands</a>'

    hero_path = os.path.join(ROOT, "cob-hero-200.png")
    if os.path.exists(hero_path):  # embed so the page stays a single file
        with open(hero_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        hero_img = (f'<img src="data:image/png;base64,{b64}" alt="CobbAttack" '
                    f'style="width:170px;height:170px">')
    else:
        hero_img = '<div style="font-size:2rem">🎙️✈️</div>'

    # footer mascot: the corn-with-sunglasses icon instead of a plain emoji
    icon48 = os.path.join(ROOT, "cob-hero-48.png")
    if os.path.exists(icon48):
        with open(icon48, "rb") as f:
            i64 = base64.b64encode(f.read()).decode()
        foot_icon = (f'<img src="data:image/png;base64,{i64}" alt="🌽" '
                     f'style="height:1.4em;vertical-align:-0.35em">')
    else:
        foot_icon = "🌽"

    total = sum(len(b) for b in buckets.values())
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CobbAttack — Flight Voice Guide</title>
<style>
 :root {{ --bg:#14181d; --panel:#1c2229; --field:#242c35; --text:#d7dde3;
          --dim:#7a8794; --green:#5dd08c; --amber:#e8b33e; --blue:#5aa7e0; }}
 * {{ box-sizing:border-box; }}
 body {{ font-family:'Segoe UI',sans-serif; background:var(--bg); color:var(--text);
        max-width:1620px; margin:0 auto; padding:0 1.4rem 3rem; }}
 .top {{ display:flex; gap:1.6rem; align-items:center; padding:1.4rem 0 .4rem; }}
 .brand {{ flex:0 0 230px; text-align:center; }}
 .brand img {{ width:150px; height:150px; filter:drop-shadow(0 6px 16px #0008); }}
 .brand h1 {{ font-size:1.35rem; letter-spacing:.14em; margin:.4rem 0 .1rem; }}
 .brand .sub {{ color:var(--dim); margin:0; font-size:.85rem; }}
 .cards {{ flex:1; display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
        gap:.9rem; }}
 .card {{ background:linear-gradient(160deg,#1e2630,#1a2028); border:1px solid #2a333e;
        border-radius:14px; padding:1rem 1.1rem; }}
 .card h3 {{ margin:.1rem 0 .5rem; font-size:.98rem; color:var(--green); }}
 .card p, .card li {{ color:var(--text); font-size:.9rem; margin:.2rem 0; }}
 .card ol {{ margin:.3rem 0 .2rem 1.2rem; padding:0; }}
 .card ol li b {{ color:var(--amber); font-weight:600; }}
 .search {{ position:sticky; top:0; background:var(--bg); padding:.7rem 0; z-index:5; }}
 .search input {{ width:100%; padding:.7rem 1.1rem; font-size:1.05rem; color:var(--text);
        background:var(--field); border:1px solid #34455a; border-radius:12px; }}
 .search input:focus {{ outline:none; border-color:var(--blue); }}
 .chips {{ display:flex; flex-wrap:wrap; gap:.5rem; margin:.6rem 0 1.1rem; }}
 .chip {{ background:var(--field); color:var(--text); text-decoration:none;
        padding:.35rem .8rem; border-radius:999px; font-size:.85rem;
        border:1px solid #2e3946; }}
 .chip:hover {{ border-color:var(--blue); }}
 .sec {{ background:var(--panel); border:1px solid #2a333e; border-radius:14px;
        padding:1rem 1.3rem; margin:0 0 1rem; scroll-margin-top:4.5rem; }}
 .sec h2 {{ margin:.1rem 0 .2rem; font-size:1.08rem; }}
 .sec .tag {{ color:var(--dim); margin:.1rem 0 .6rem; font-size:.88rem; }}
 ul.cmds {{ list-style:none; margin:.4rem 0; padding:0; columns:17rem;
        column-gap:2.2rem; }}
 li.cmd {{ break-inside:avoid; padding:.16rem .3rem; border-radius:6px;
        font-size:.98rem;
        color:color-mix(in srgb, var(--acc, #9fb0c0) 60%, #eef2f6); }}
 li.cmd.star {{ color:var(--acc, var(--green)); font-weight:600;
        filter:brightness(1.15); }}
 li.cmd.hit {{ background:#26332b; }}
 li.cmd.tip {{ text-decoration:underline dotted #56657a; text-underline-offset:3px;
        cursor:help; }}
 #tipbox {{ position:fixed; display:none; z-index:50; pointer-events:none;
        background:#0e1216; color:#e8edf2; border:1px solid #34455a;
        border-radius:9px; padding:.5rem .7rem; max-width:300px;
        font-size:.85rem; box-shadow:0 6px 18px #000a; }}
 .sec h2 {{ color:var(--acc, var(--text)); }}
 details.more summary {{ color:var(--blue); cursor:pointer; font-size:.9rem;
        padding:.4rem 0 .15rem; user-select:none; }}
 details.more summary:hover {{ text-decoration:underline; }}
 details.more ul.cmds {{ margin-top:.5rem; }}
 .hide {{ display:none !important; }}
 footer {{ color:var(--dim); text-align:center; font-size:.85rem; margin-top:1.6rem; }}
 @media (max-width:900px) {{ .top {{ flex-direction:column; }}
        .brand {{ flex:none; }} }}
 @media (max-width:640px) {{ .masonry {{ columns:1; }} }}
 @media print {{ body {{ background:#fff; color:#000; }} .search {{ display:none; }} }}
</style></head><body>

<div class="top">
<div class="brand">
  {hero_img}
  <h1>FLIGHT VOICE GUIDE</h1>
  <p class="sub">{total} commands · your VAICOM profile · word-for-word</p>
</div>
<div class="cards">
  <div class="card"><h3>🎙️ How to speak</h3>
    <p>Hold your talk button, speak <b>word-for-word</b>, release. The squawk sound
    means it transmitted. <span style="color:var(--dim)">Green bold commands below are
    the everyday ones.</span></p>
    <p style="color:var(--dim)">Starting a call with the recipient's name
    ("Tower, …", "Two, …") is allowed but optional.</p></div>
  <div class="card"><h3>🕹️ Your buttons</h3>
    <p><b style="color:var(--amber)">TX1</b> — radio 1 · ATC, AWACS, tanker, ground crew</p>
    <p><b style="color:var(--amber)">TX2</b> — radio 2 · your wingmen</p></div>
  <div class="card"><h3>🛫 Your first flight</h3>
    <ol>
      <li><b>request startup</b></li>
      <li><b>request taxi to runway</b></li>
      <li><b>request takeoff</b></li>
      <li>…fly…</li>
      <li><b>inbound</b></li>
      <li><b>taxi to parking</b></li>
    </ol></div>
</div>
</div>

<div class="search"><input id="q" placeholder="Search any command… (taxi, picture, refuel, 9 line)" autofocus></div>

<nav class="chips">{nav}</nav>

{sections_html}

<footer>Generated from your VAICOM profile · CobbAttack {foot_icon}</footer>

<script>
// Clicking a section chip also expands that section's "show all" list.
document.querySelectorAll('.chips a').forEach(a => {{
  a.addEventListener('click', () => {{
    const sec = document.querySelector(a.getAttribute('href'));
    if (sec) sec.querySelectorAll('details.more').forEach(d => d.open = true);
  }});
}});

const q = document.getElementById('q');
q.addEventListener('input', () => {{
  const t = q.value.trim().toLowerCase();
  document.querySelectorAll('.sec').forEach(sec => {{
    let any = false;
    sec.querySelectorAll('li.cmd').forEach(li => {{
      const hit = !t || li.textContent.toLowerCase().includes(t);
      li.classList.toggle('hide', !hit);
      li.classList.toggle('hit', !!t && hit);
      if (hit) any = true;
    }});
    sec.querySelectorAll('details.more').forEach(d => d.open = !!t && any);
    sec.classList.toggle('hide', !!t && !any);
  }});
}});

const tip = document.createElement('div');
tip.id = 'tipbox';
document.body.appendChild(tip);
document.querySelectorAll('li.cmd.tip').forEach(li => {{
  li.addEventListener('mouseenter', () => {{
    tip.textContent = li.dataset.tip;
    const acc = getComputedStyle(li.closest('.sec')).getPropertyValue('--acc').trim();
    tip.style.borderColor = acc || '#34455a';
    tip.style.display = 'block';
    const r = li.getBoundingClientRect(), tw = tip.offsetWidth, th = tip.offsetHeight;
    let x = Math.min(Math.max(8, r.left), window.innerWidth - tw - 8);
    let y = r.top - th - 8;                       // prefer above
    if (y < 8) y = r.bottom + 8;                  // else below
    y = Math.min(Math.max(8, y), window.innerHeight - th - 8);  // never off-screen
    tip.style.left = x + 'px';
    tip.style.top = y + 'px';
  }});
  li.addEventListener('mouseleave', () => {{ tip.style.display = 'none'; }});
}});
</script>
</body></html>"""
    with open(DST, "w", encoding="utf-8") as f:
        f.write(page)
    counts = {k: len(v) for k, v in buckets.items() if v}
    print(f"{total} phrases -> {DST}")
    print("per section:", counts)


if __name__ == "__main__":
    main()
