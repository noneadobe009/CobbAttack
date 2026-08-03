; Inno Setup script for CobbAttack.
;
; Build the exe first, then compile this:
;   pyinstaller CobbAttack.spec --noconfirm
;   & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
;
; Inno Setup is installed per-user on this machine (%LOCALAPPDATA%\Programs),
; not in Program Files.
;
; Produces dist\CobbAttackSetup-<version>.exe
;
; What this installer does that the zip cannot:
;   1. Puts the WhisperAttack WASC plugin into VoiceAttack's Apps folder for
;      them. That copy is the single step people get wrong, and getting it
;      wrong means PTT does nothing with no useful error.
;   2. Keeps their taught words on upgrade. Extracting the zip over an existing
;      folder silently overwrote word_mappings.txt and vaicom_keywords.txt —
;      see the "preserve" flags in [Files].
;   3. Refuses to install into Program Files (see CheckInstallDir below).

#define AppName "CobbAttack"
#define AppExeName "CobbAttack.exe"
#define AppPublisher "Jerome Sexton"
; Single source of truth — version.py. Kept in step with the app itself rather
; than typed here again, which is how an installer ends up claiming a different
; version than the exe inside it.
#define AppVersion ReadIni(SourcePath + "\dist\installer_version.ini", "v", "version", "0.0.0")
#define BuildDir "dist\CobbAttack"

[Setup]
AppId={{7C4E1A93-2B85-4D6F-9E31-A8F05C2D71B4}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppCopyright=Copyright (C) 2026 {#AppPublisher}
SetupIconFile=cobbattack.ico
UninstallDisplayIcon={app}\{#AppExeName}

; NOT {autopf}. CobbAttack keeps settings.json, word_mappings.txt, commands.txt,
; cobbattack.log and troubleshoot.html next to its own exe (config.ROOT is the
; exe's folder when frozen). Program Files is read-only for normal users, so an
; install there produces an app that cannot save anything the user teaches it.
; SETUP.md has warned about this since v1.0 — the installer now enforces it.
DefaultDirName={sd}\{#AppName}
DefaultGroupName={#AppName}
; They can still move it, but not into Program Files (CheckInstallDir).
AllowNoIcons=yes

OutputDir=dist
OutputBaseFilename=CobbAttackSetup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; Admin is required for one reason only: writing the plugin into
; C:\Program Files (x86)\VoiceAttack\Apps. The app's own folder is deliberately
; outside Program Files and is opened up to normal users in [Run] below.
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Upgrading over a running copy otherwise leaves a half-written exe. Restart
; Manager asks to close it instead.
CloseApplications=yes
RestartApplications=no

; The payload is ~480 MB before compression, nearly all of it the two speech
; models and the whisper.cpp binaries. Both ship in the box on purpose:
; "nothing is downloaded, nothing goes online" is a promise the setup guide
; makes, and Cobb's whole reason for using this is that it works offline.
DiskSpanning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "valink"; Description: "Also create a ""CobbAttack + VoiceAttack"" shortcut (starts both in one click)"; GroupDescription: "Additional shortcuts:"

[Files]
; --- the frozen app -------------------------------------------------------
Source: "{#BuildDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BuildDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- engine, models, bundled plugin source --------------------------------
Source: "bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "models\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "third_party\*"; DestDir: "{app}\third_party"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- source (the no-Python fallback path in SETUP.md still works) ---------
Source: "main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "ui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "engine.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "bridge.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "recorder.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "normalize.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "jokes.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "vaicom_patch.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "custom_vap.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "valink.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "tray.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "troubleshoot.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "version.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "run-cobbattack.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "Start with VoiceAttack.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "Add to Start Menu.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "tools\*"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- icons, art, documentation --------------------------------------------
Source: "cobbattack.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "cob-hero.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "cob-hero-48.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "cob-hero-72.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "cob-hero-200.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "cob-hero-icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "SETUP.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "Setup-Instruction.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "commands-cheatsheet.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "vaicom-explainer.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "VAICOM-mission-restart-bug.md"; DestDir: "{app}"; Flags: ignoreversion

; --- app data that should always refresh ----------------------------------
Source: "fuzzy_terms.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "recipients.txt"; DestDir: "{app}"; Flags: ignoreversion

; --- the user's own files: WRITE ONCE, NEVER OVERWRITE --------------------
; This is the bug the zip had. word_mappings.txt holds every word they have
; taught the app by hand; vaicom_keywords.txt is their VAICOM profile export.
; Upgrading must not touch either, and uninstalling should not throw them away.
Source: "tools\word_mappings.seed.txt"; DestDir: "{app}"; DestName: "word_mappings.txt"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "vaicom_keywords.txt"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall
; commands.txt is generated from vaicom_keywords.txt at startup, so a stale one
; is harmless — but overwriting a user's rebuilt list would silently undo their
; keyword export until the next restart.
Source: "commands.txt"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

; --- the WASC plugin, straight into VoiceAttack ---------------------------
; The whole point of having an installer. Skipped entirely if VoiceAttack was
; not found and the user chose not to point us at it.
Source: "third_party\WhisperAttackServerCommand\*"; DestDir: "{code:GetPluginDest}"; Flags: ignoreversion recursesubdirs createallsubdirs uninsneveruninstall; Check: InstallingPlugin

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\cobbattack.ico"; Comment: "CobbAttack - voice control for VAICOM/DCS"
Name: "{group}\{#AppName} + VoiceAttack"; Filename: "{app}\Start with VoiceAttack.bat"; WorkingDir: "{app}"; IconFilename: "{app}\cobbattack.ico"; Comment: "Start VoiceAttack and CobbAttack together"; Tasks: valink
Name: "{group}\Setup guide (with screenshots)"; Filename: "{app}\Setup-Instruction.html"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\cobbattack.ico"; Tasks: desktopicon

[Run]
; The install folder is outside Program Files precisely so the app can write to
; it — but a folder created under C:\ by an elevated installer does not give
; normal users write access by default, which would leave the app unable to save
; settings or taught words. S-1-5-32-545 is the built-in Users group, used as a
; SID so this still works on a non-English Windows.
Filename: "{sys}\icacls.exe"; Parameters: """{app}"" /grant *S-1-5-32-545:(OI)(CI)M /T /C /Q"; Flags: runhidden waituntilterminated; StatusMsg: "Allowing CobbAttack to save your settings..."

Filename: "{app}\Setup-Instruction.html"; Description: "Open the setup guide (VAICOM and VoiceAttack settings still need doing)"; Flags: postinstall shellexec nowait
Filename: "{app}\{#AppExeName}"; Description: "Start CobbAttack now"; Flags: postinstall nowait skipifsilent

[Code]
var
  PluginPage: TInputDirWizardPage;
  DetectedVADir: String;

{ The two places VoiceAttack's own installer puts it — same list valink.py uses
  to find VoiceAttack.exe at runtime. Kept in step with that file by hand; if a
  third location ever shows up, both need it. }
function FindVoiceAttackDir(): String;
begin
  Result := '';
  if FileExists(ExpandConstant('{commonpf32}') + '\VoiceAttack\VoiceAttack.exe') then
    Result := ExpandConstant('{commonpf32}') + '\VoiceAttack'
  else if FileExists(ExpandConstant('{commonpf64}') + '\VoiceAttack\VoiceAttack.exe') then
    Result := ExpandConstant('{commonpf64}') + '\VoiceAttack';
end;

procedure InitializeWizard();
begin
  DetectedVADir := FindVoiceAttackDir();

  { Only ask when we could not find it. Someone with a stock VoiceAttack install
    should never see this page. }
  PluginPage := CreateInputDirPage(wpSelectTasks,
    'VoiceAttack folder',
    'Where is VoiceAttack installed?',
    'CobbAttack could not find VoiceAttack automatically.' + #13#10#13#10 +
    'Point this at your VoiceAttack folder (the one containing VoiceAttack.exe) and the ' +
    'required plugin will be installed for you.' + #13#10#13#10 +
    'Leave it empty to skip. You can copy third_party\WhisperAttackServerCommand into ' +
    'VoiceAttack''s Apps folder yourself later — SETUP.md explains how.',
    False, '');
  PluginPage.Add('');
  PluginPage.Values[0] := '';
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  { Found it already — no need to bother them. }
  if (PageID = PluginPage.ID) and (DetectedVADir <> '') then
    Result := True;
end;

{ Where the plugin goes, or an empty string when we are not installing it. }
function GetVADir(): String;
begin
  if DetectedVADir <> '' then
    Result := DetectedVADir
  else
    Result := Trim(PluginPage.Values[0]);
end;

function InstallingPlugin(): Boolean;
var
  Dir: String;
begin
  Dir := GetVADir();
  Result := (Dir <> '') and FileExists(Dir + '\VoiceAttack.exe');
end;

function GetPluginDest(Param: String): String;
begin
  { Only ever evaluated for entries whose Check passed, but return something
    harmless rather than an empty path if that ever stops being true. }
  if InstallingPlugin() then
    Result := GetVADir() + '\Apps\WhisperAttackServerCommand'
  else
    Result := ExpandConstant('{tmp}') + '\no-plugin';
end;

{ Program Files would break the app: it writes its settings, log and taught
  words next to its own exe. Catching it here is far kinder than the app
  failing to save an hour later. }
function CheckInstallDir(Dir: String): Boolean;
var
  Lower: String;
begin
  Lower := Lowercase(Dir);
  Result := (Pos('\program files', Lower) = 0);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Dir: String;
begin
  Result := True;

  if CurPageID = wpSelectDir then
  begin
    if not CheckInstallDir(WizardDirValue) then
    begin
      MsgBox('CobbAttack cannot be installed inside Program Files.' + #13#10#13#10 +
             'It saves your settings and the words you teach it next to the program itself, ' +
             'and Windows makes Program Files read-only for that.' + #13#10#13#10 +
             'Please choose somewhere else — C:\CobbAttack is the usual answer.',
             mbError, MB_OK);
      Result := False;
    end;
  end;

  if CurPageID = PluginPage.ID then
  begin
    Dir := Trim(PluginPage.Values[0]);
    { Empty means "skip", which is allowed. A wrong path is not. }
    if (Dir <> '') and (not FileExists(Dir + '\VoiceAttack.exe')) then
    begin
      MsgBox('VoiceAttack.exe is not in that folder.' + #13#10#13#10 +
             'Right-click your VoiceAttack shortcut, choose Open file location, and use ' +
             'the folder it shows you.' + #13#10#13#10 +
             'Or clear the box to skip installing the plugin for now.',
             mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if not InstallingPlugin() then
      MsgBox('CobbAttack is installed, but the VoiceAttack plugin was not.' + #13#10#13#10 +
             'Without it, pressing your push-to-talk button will do nothing.' + #13#10#13#10 +
             'To finish by hand: copy the folder' + #13#10 +
             ExpandConstant('  {app}\third_party\WhisperAttackServerCommand') + #13#10 +
             'into VoiceAttack''s Apps folder, then turn on Enable Plugin Support in ' +
             'VoiceAttack''s options and restart it.',
             mbInformation, MB_OK);
  end;
end;
