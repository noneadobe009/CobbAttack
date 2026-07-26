@echo off
cd /d "%~dp0"
rem Prefer the standalone exe (no Python needed); fall back to source for devs.
if exist "%~dp0CobbAttack.exe" (
    start "" "%~dp0CobbAttack.exe"
) else (
    start "" pythonw main.py
)
