@echo off
rem Creates a Start Menu shortcut for CobbAttack.exe (with the corn icon).
rem Safe to run again — it just overwrites the old shortcut.
cd /d "%~dp0"
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$lnk = $ws.CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\CobbAttack.lnk\");" ^
  "$lnk.TargetPath = '%~dp0CobbAttack.exe';" ^
  "$lnk.WorkingDirectory = '%~dp0';" ^
  "$lnk.IconLocation = '%~dp0cobbattack.ico';" ^
  "$lnk.Description = 'CobbAttack - voice control for VAICOM/DCS';" ^
  "$lnk.Save()"
echo Done! CobbAttack is now in your Start Menu.
pause
