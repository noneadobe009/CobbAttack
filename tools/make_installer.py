"""Build the CobbAttack installer.

    python tools/make_installer.py          -> dist/CobbAttackSetup-<version>.exe

Runs PyInstaller first unless dist/CobbAttack/CobbAttack.exe is already newer
than every source file, then compiles installer.iss.

The version is read from version.py and handed to Inno through
dist/installer_version.ini — Inno's #define is evaluated at compile time and
cannot import Python, so a generated ini is the bridge. That keeps version.py
the only place the number is written down (Parlez learned this the hard way:
its installer used to claim a different version than the exe inside it).
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
EXE = os.path.join(DIST, "CobbAttack", "CobbAttack.exe")
VERSION_INI = os.path.join(DIST, "installer_version.ini")

# Inno Setup is installed per-user on this machine, not in Program Files.
ISCC_CANDIDATES = (
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
)


def read_version():
    with open(os.path.join(ROOT, "version.py"), encoding="utf-8") as fh:
        match = re.search(r'__version__\s*=\s*"([^"]+)"', fh.read())
    if not match:
        sys.exit("version.py has no __version__ — cannot version the installer")
    return match.group(1)


def find_iscc():
    for path in ISCC_CANDIDATES:
        if path and os.path.exists(path):
            return path
    sys.exit("Inno Setup 6 not found. Install it, or add ISCC.exe to ISCC_CANDIDATES.")


def build_exe():
    print("--- PyInstaller ---")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "CobbAttack.spec", "--noconfirm"],
        cwd=ROOT, check=True)


def main():
    version = read_version()
    print(f"CobbAttack {version}")

    if "--skip-exe" not in sys.argv:
        build_exe()
    if not os.path.exists(EXE):
        sys.exit(f"missing {EXE} — run without --skip-exe")

    os.makedirs(DIST, exist_ok=True)
    with open(VERSION_INI, "w", encoding="utf-8") as fh:
        fh.write(f"[v]\nversion={version}\n")

    print("--- Inno Setup ---")
    iscc = find_iscc()
    result = subprocess.run([iscc, "installer.iss"], cwd=ROOT,
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-3000:])
        sys.exit(f"ISCC failed ({result.returncode})")

    out = os.path.join(DIST, f"CobbAttackSetup-{version}.exe")
    size_mb = os.path.getsize(out) / (1024 * 1024)
    print(f"{out} ({size_mb:.0f} MB)")


if __name__ == "__main__":
    main()
