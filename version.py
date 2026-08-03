"""The one place the version number lives.

Read by main.py (the startup log line), installer.iss (AppVersion and the setup
filename) and tools/make_zip.py. Bump it here and everything else follows —
there is deliberately no second copy to forget.

Why it exists: until 1.3.0 the app printed no version at all, so the only way to
tell which build someone was running was to look for a feature that had been
added recently. That guessing game is what this ends.
"""

__version__ = "1.3.0"
