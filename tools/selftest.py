"""Self-test for the text pipeline: the parts that can be wrong silently.
Run: python tools/selftest.py — exits nonzero on any failure."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import normalize

settings = config.load()
n = normalize.Normalizer(settings)
failures = []


def check(name, actual, expected):
    ok = actual == expected
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {actual!r}" + ("" if ok else f"  (expected {expected!r})"))
    if not ok:
        failures.append(name)


# Hallucination firewall
check("silence junk dropped", n.normalize("Thank you."), None)
check("annotation dropped", n.normalize("[typing]"), None)
check("annotation+noise dropped", n.normalize("(wind blowing)"), None)
check("empty dropped", n.normalize("   "), None)

# Cleanup pipeline — tested without the command firewall so we can assert the
# exact intermediate text (the firewall's job is checked separately below).
raw = normalize.Normalizer(settings)
raw.commands = []
check("digits split", raw.normalize("Enfield 1-1, request taxi."), "enfield 1 1 request taxi")
check("number words", raw.normalize("Enfield one one, inbound."), "enfield 1 1 inbound")
check("learned mapping", raw.normalize("Chief, request lunch."), "chief request launch")
check("refuel mapping", raw.normalize("Texaco, request refere."), "texaco request refuel")

# Teaching (in-memory only — use a throwaway pair, then verify it applies)
raw.mappings.insert(0, ("zzz test wrongzzz", "corrected"))
check("taught mapping applies", raw.normalize("zzz test wrongzzz"), "corrected")
raw.mappings.remove(("zzz test wrongzzz", "corrected"))

# Command firewall (full normalizer, real profile phrases)
check("basic command", n.normalize("Chief, request launch."), "chief request launch")
check("real phrase passes", n.normalize("Texaco, approaching for refuel."),
      "texaco approaching for refuel")
check("fuzzy snap", n.normalize("Overlord, bogey doped."), "overlord bogey dope")
check("half phrase dropped", n.normalize("Fly towards the purple elephant."), None)

# Suggestions
sugg = n.suggest("refuell")
check("suggest finds refuel", "refuel" in sugg, True)

print()
if failures:
    print(f"{len(failures)} FAILURE(S): {failures}")
    sys.exit(1)
print("ALL CHECKS PASSED")
