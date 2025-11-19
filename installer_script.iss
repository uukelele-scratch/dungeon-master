#define AppName      "Dungeon Master"
#define AppVersion   "DEV-BUILD"
#define AppPublisher "Uukelele"
#define AppExeName   "DungeonMaster.exe"
#define AppIcon      "assets\icon.ico"

#define AppId        "{{83F1C63B-9402-4279-B6D4-557362507931}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}

DefaultDirName={autopf}\{#AppName}

DisableProgramGroupPage=yes
PrivilegesRequired=lowest

OutputBaseFilename=DungeonMaster_Installer_v{#AppVersion}
SetupIconFile={#AppIcon}

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\DungeonMaster\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Shortcut
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppIcon}"
; Desktop Shortcut
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppIcon}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent