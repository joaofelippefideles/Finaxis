; ===========================================================================
;  Instalador do Finaxis (Sistema de Controle Financeiro Pessoal)  (Inno Setup 6)
; ---------------------------------------------------------------------------
;  Compilar:
;     ISCC.exe installer\SistemaFinanceiro.iss
;  Normalmente NAO precisa chamar direto: use installer\build.ps1, que monta
;  o payload (executavel + frontend) e passa /DSourceDir e /DAppVersion.
;
;  Caracteristicas:
;    * instalacao por usuario (sem exigir administrador);
;    * dados do usuario (data\ e backups\) ficam FORA do executavel e NUNCA
;      sao sobrescritos nem apagados em atualizacoes/desinstalacao;
;    * atualizacao no mesmo diretorio preserva todos os arquivos JSON.
; ===========================================================================

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

#ifndef SourceDir
  #define SourceDir "..\payload\SistemaFinanceiro"
#endif

#define AppName        "Finaxis"
#define AppShortName   "SistemaFinanceiro"
#define AppPublisher   "Projeto de Paradigmas de Programacao em Python"
#define AppExeName     "SistemaFinanceiro.exe"

[Setup]
AppId={{9C4B7E2A-6F1D-4B3E-A8C2-1D5E9F0A7B64}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\SistemaFinanceiro
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=FinaxisSetup
SetupIconFile=app.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableDirPage=no
CloseApplications=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent