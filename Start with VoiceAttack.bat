@echo off
rem One click: VoiceAttack (elevated, the way VAICOM needs it) then CobbAttack.
rem Anything already running is left alone, so no pointless admin prompt.
cd /d "%~dp0"

rem Full paths on purpose: if Git for Windows (or similar) is on PATH, a bare
rem "find" or "timeout" resolves to the Unix tool and this script misbehaves.
set "TL=%SystemRoot%\System32\tasklist.exe"
set "FIND=%SystemRoot%\System32\find.exe"
set "WAIT=%SystemRoot%\System32\timeout.exe"

set "VA="
if exist "C:\Program Files (x86)\VoiceAttack\VoiceAttack.exe" set "VA=C:\Program Files (x86)\VoiceAttack\VoiceAttack.exe"
if exist "C:\Program Files\VoiceAttack\VoiceAttack.exe" set "VA=C:\Program Files\VoiceAttack\VoiceAttack.exe"

"%TL%" /FI "IMAGENAME eq VoiceAttack.exe" 2>nul | "%FIND%" /I "VoiceAttack.exe" >nul
if not errorlevel 1 (
    echo VoiceAttack is already running - leaving it alone.
    goto :cobb
)
if not defined VA (
    echo.
    echo Could not find VoiceAttack.exe in Program Files.
    echo Start VoiceAttack yourself, then run CobbAttack.
    echo.
    pause
    goto :cobb
)
echo Starting VoiceAttack ^(say yes to the admin prompt^)...
powershell -NoProfile -Command "Start-Process -FilePath '%VA%' -Verb RunAs"
rem VoiceAttack needs a moment to load its profile and the WASC plugin
"%WAIT%" /t 6 /nobreak >nul

:cobb
"%TL%" /FI "IMAGENAME eq CobbAttack.exe" 2>nul | "%FIND%" /I "CobbAttack.exe" >nul
if not errorlevel 1 (
    echo CobbAttack is already running.
    exit /b
)
if exist "%~dp0CobbAttack.exe" (
    start "" "%~dp0CobbAttack.exe"
) else (
    start "" pythonw main.py
)
