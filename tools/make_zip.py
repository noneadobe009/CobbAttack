"""Build the shippable CobbAttack zip for Cobb.

    python tools/make_zip.py            -> dist/CobbAttack.zip

What goes in (and the judgment calls, per .claude/rules/quality.md):
- the app, engine binaries (Vulkan + CPU), BOTH models (base.en default,
  small.en opt-in via settings.json),
- the bundled WASC plugin + its MIT license (third_party/),
- both guides + the flight guide, the working commands/keywords lists so voice
  works out of the box (Cobb refreshes them when he rebuilds keywords),
- word_mappings.txt is REPLACED by tools/word_mappings.seed.txt — the owner's
  personal voice fixes stay home.
What stays out: logs, settings.json (machine-specific mic/model pins),
custom_commands.txt + *.vap (owner's profile), screenshots/ (already embedded
in SETUP.html), backups, caches.
"""

import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
DST = os.path.join(DIST, "CobbAttack.zip")

TOP_FILES = [
    "main.py", "ui.py", "config.py", "engine.py", "bridge.py", "recorder.py",
    "normalize.py", "jokes.py", "vaicom_patch.py", "custom_vap.py",
    "requirements.txt", "run-cobbattack.bat", "Add to Start Menu.bat",
    "cobbattack.ico",
    "cob-hero.png", "cob-hero-48.png", "cob-hero-58.png", "cob-hero-200.png",
    "cob-hero-icon.png",
    "README.md", "Install Instruction.md", "Install Instruction.html",
    "SETUP.md", "SETUP.html", "commands-cheatsheet.html",
    "VAICOM-mission-restart-bug.md",
    "fuzzy_terms.txt", "commands.txt", "recipients.txt", "vaicom_keywords.txt",
]
TOOL_FILES = [
    "make_commands.py", "make_cheatsheet.py", "make_setup.py", "make_zip.py",
    "selftest.py", "fake_va.py", "send_ctl.py", "word_mappings.seed.txt",
]
TREES = ["bin", "models", "third_party"]
# PyInstaller output (pyinstaller CobbAttack.spec --noconfirm -> dist/CobbAttack).
# Only the exe + its _internal runtime come from there; data files come from ROOT.
EXE_DIR = os.path.join(ROOT, "dist", "CobbAttack")


def main():
    os.makedirs(DIST, exist_ok=True)
    added, missing = 0, []

    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        def put(src, arc):
            nonlocal added
            z.write(src, os.path.join("CobbAttack", arc))
            added += 1

        exe = os.path.join(EXE_DIR, "CobbAttack.exe")
        if os.path.exists(exe):
            put(exe, "CobbAttack.exe")
            internal = os.path.join(EXE_DIR, "_internal")
            for dirpath, _dirnames, filenames in os.walk(internal):
                for fn in filenames:
                    src = os.path.join(dirpath, fn)
                    put(src, os.path.relpath(src, EXE_DIR))
        else:
            missing.append("CobbAttack.exe (run PyInstaller first — see docstring)")

        for name in TOP_FILES:
            src = os.path.join(ROOT, name)
            if os.path.exists(src):
                put(src, name)
            else:
                missing.append(name)
        for name in TOOL_FILES:
            src = os.path.join(ROOT, "tools", name)
            if os.path.exists(src):
                put(src, os.path.join("tools", name))
            else:
                missing.append(f"tools/{name}")
        # Cobb starts with the clean seed, not the owner's personal voice fixes.
        put(os.path.join(ROOT, "tools", "word_mappings.seed.txt"), "word_mappings.txt")
        for tree in TREES:
            base = os.path.join(ROOT, tree)
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for fn in filenames:
                    src = os.path.join(dirpath, fn)
                    put(src, os.path.relpath(src, ROOT))

    size_mb = os.path.getsize(DST) / (1024 * 1024)
    print(f"{added} files -> {DST} ({size_mb:.0f} MB)")
    if missing:
        print("SKIPPED (not found):", ", ".join(missing))


if __name__ == "__main__":
    main()
