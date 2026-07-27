@echo off
rem Creates two Start Menu shortcuts (both with the corn icon):
rem   CobbAttack                  - just the app
rem   CobbAttack + VoiceAttack    - starts VoiceAttack too, one click
rem Safe to run again - it just overwrites the old shortcuts.
cd /d "%~dp0"
powershell -NoProfile -Command ^
  "$sm = \"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\";" ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$a = $ws.CreateShortcut($sm + 'CobbAttack.lnk');" ^
  "$a.TargetPath = '%~dp0CobbAttack.exe';" ^
  "$a.WorkingDirectory = '%~dp0';" ^
  "$a.IconLocation = '%~dp0cobbattack.ico';" ^
  "$a.Description = 'CobbAttack - voice control for VAICOM/DCS';" ^
  "$a.Save();" ^
  "$b = $ws.CreateShortcut($sm + 'CobbAttack + VoiceAttack.lnk');" ^
  "$b.TargetPath = '%~dp0Start with VoiceAttack.bat';" ^
  "$b.WorkingDirectory = '%~dp0';" ^
  "$b.IconLocation = '%~dp0cobbattack.ico';" ^
  "$b.WindowStyle = 7;" ^
  "$b.Description = 'Start VoiceAttack and CobbAttack together';" ^
  "$b.Save()"
echo Done! Both shortcuts are now in your Start Menu.
pause
