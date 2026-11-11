[Setup]
AppId={{7F2E5A0D-51C4-4E5D-A6D4-6C6B2B3B44A1}
AppName=Kimi Token Usage
AppVersion=1.3.0
AppPublisher=Cyberkillr013
AppPublisherURL=https://github.com/Cyberkillr013/kimi-token-usage
AppSupportURL=https://github.com/Cyberkillr013/kimi-token-usage/issues
AppUpdatesURL=https://github.com/Cyberkillr013/kimi-token-usage/releases
DefaultDirName={localappdata}\Programs\Kimi Token Usage
DefaultGroupName=Kimi Token Usage
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=KimiTokenUsage-Setup
SetupIconFile=..\assets\token_widget.ico
UninstallDisplayIcon={app}\KimiTokenUsage.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Files]
Source: "..\dist\KimiTokenUsage.exe"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
Type: files; Name: "{autodesktop}\Kimi Token Usage.lnk"
Type: files; Name: "{autostartup}\Kimi Token Usage.lnk"

[Icons]
Name: "{autoprograms}\Kimi Token Usage"; Filename: "{app}\KimiTokenUsage.exe"; IconFilename: "{app}\KimiTokenUsage.exe"
Name: "{autodesktop}\Kimi Token Usage"; Filename: "{app}\KimiTokenUsage.exe"; IconFilename: "{app}\KimiTokenUsage.exe"; Check: CreateDesktopShortcut

[Run]
Filename: "{app}\KimiTokenUsage.exe"; Description: "Launch Kimi Token Usage"; Flags: nowait postinstall skipifsilent

[Code]
var
  OptionsPage: TWizardPage;
  InstallCheck: TNewCheckBox;
  StartupCheck: TNewCheckBox;
  DesktopCheck: TNewCheckBox;

procedure InitializeWizard;
begin
  OptionsPage := CreateCustomPage(
    wpSelectDir,
    'Installation options',
    'Choose how Kimi Token Usage is installed.'
  );

  InstallCheck := TNewCheckBox.Create(WizardForm);
  InstallCheck.Parent := OptionsPage.Surface;
  InstallCheck.Left := 0;
  InstallCheck.Top := 8;
  InstallCheck.Width := OptionsPage.SurfaceWidth;
  InstallCheck.Height := 24;
  InstallCheck.Caption := 'Install app (required)';
  InstallCheck.Checked := True;
  InstallCheck.Enabled := False;

  StartupCheck := TNewCheckBox.Create(WizardForm);
  StartupCheck.Parent := OptionsPage.Surface;
  StartupCheck.Left := 0;
  StartupCheck.Top := 44;
  StartupCheck.Width := OptionsPage.SurfaceWidth;
  StartupCheck.Height := 24;
  StartupCheck.Caption := 'Open Kimi Token Usage when Windows starts';
  StartupCheck.Checked := True;

  DesktopCheck := TNewCheckBox.Create(WizardForm);
  DesktopCheck.Parent := OptionsPage.Surface;
  DesktopCheck.Left := 0;
  DesktopCheck.Top := 80;
  DesktopCheck.Width := OptionsPage.SurfaceWidth;
  DesktopCheck.Height := 24;
  DesktopCheck.Caption := 'Put a shortcut on my Desktop';
  DesktopCheck.Checked := True;
end;

function StartWithWindows: Boolean;
begin
  Result := not Assigned(StartupCheck) or StartupCheck.Checked;
end;

function CreateDesktopShortcut: Boolean;
begin
  Result := not Assigned(DesktopCheck) or DesktopCheck.Checked;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if StartWithWindows then
      RegWriteStringValue(
        HKCU,
        'Software\Microsoft\Windows\CurrentVersion\Run',
        'Kimi Token Usage',
        ExpandConstant('"{app}\KimiTokenUsage.exe"')
      )
    else
      RegDeleteValue(
        HKCU,
        'Software\Microsoft\Windows\CurrentVersion\Run',
        'Kimi Token Usage'
      );
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RegDeleteValue(
      HKCU,
      'Software\Microsoft\Windows\CurrentVersion\Run',
      'Kimi Token Usage'
    );
end;
