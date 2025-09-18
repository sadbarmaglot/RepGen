; =============================================================================
; DefectAnalyzer Installer Script for Inno Setup
; =============================================================================
; 
; Константы приложения - ЗАМЕНИТЕ НА РЕАЛЬНЫЕ ЗНАЧЕНИЯ
; =============================================================================

#define AppName "DefectAnalyzer"
#define AppVersion "1.0.0"
#define AppPublisher "AI Engineering Solutions"
#define AppURL "https://github.com/your-username/RepGen"
#define AppExeName "DefectAnalyzer.exe"
#define AppDescription "AI-powered construction defect analysis tool"

; =============================================================================
; Основные настройки установщика
; =============================================================================

[Setup]
; НАСТРОЙКИ ПРИЛОЖЕНИЯ
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
AppCopyright=Copyright (C) 2024 {#AppPublisher}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppDescription}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}

; ПУТИ И ФАЙЛЫ
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=..\..\dist
OutputBaseFilename=Setup-{#AppName}-{#AppVersion}
SetupIconFile=..\app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; ПРАВА ДОСТУПА
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; ИНТЕРФЕЙС
WizardImageFile=
WizardSmallImageFile=
DisableProgramGroupPage=yes
DisableReadyPage=no
DisableFinishedPage=no

; ДОПОЛНИТЕЛЬНЫЕ ОПЦИИ
CreateUninstallRegKey=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

; =============================================================================
; Языки
; =============================================================================

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

; =============================================================================
; Задачи установки
; =============================================================================

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

; =============================================================================
; Файлы для установки
; =============================================================================

[Files]
; Основной исполняемый файл и все ресурсы из build/win/
; TODO: Убедитесь, что структура build/win/ содержит:
;       - DefectAnalyzer.exe (главный exe файл)
;       - Все необходимые DLL, библиотеки и ресурсы
Source: "..\..\build\win\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

; Иконка приложения (если есть)
; Source: "..\app.ico"; DestDir: "{app}"; Flags: ignoreversion

; =============================================================================
; Ярлыки
; =============================================================================

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon; WorkingDir: "{app}"

; =============================================================================
; Реестр
; =============================================================================

[Registry]
; Регистрация приложения для удаления через "Программы и компоненты"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}"; ValueType: string; ValueName: "DisplayName"; ValueData: "{#AppName} {#AppVersion}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#AppVersion}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}"; ValueType: string; ValueName: "Publisher"; ValueData: "{#AppPublisher}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "{#AppURL}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}"; ValueType: dword; ValueName: "NoModify"; ValueData: 1
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#AppName}"; ValueType: dword; ValueName: "NoRepair"; ValueData: 1

; =============================================================================
; Код установки
; =============================================================================

[Code]
// Проверка, запущено ли приложение перед установкой
function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  Result := True;
  
  // Проверяем, не запущен ли уже DefectAnalyzer
  if CheckForMutexes('DefectAnalyzer') then
  begin
    if MsgBox('Обнаружено запущенное приложение DefectAnalyzer. ' +
              'Для корректной установки необходимо закрыть приложение. ' +
              'Закрыть приложение сейчас?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Пытаемся закрыть приложение
      if not Exec('taskkill', '/F /IM ' + '{#AppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode) then
      begin
        MsgBox('Не удалось автоматически закрыть приложение. ' +
               'Пожалуйста, закройте DefectAnalyzer вручную и повторите установку.', 
               mbError, MB_OK);
        Result := False;
      end;
    end
    else
    begin
      Result := False;
    end;
  end;
end;

// Проверка перед удалением
function InitializeUninstall(): Boolean;
var
  ErrorCode: Integer;
begin
  Result := True;
  
  // Проверяем, не запущено ли приложение перед удалением
  if CheckForMutexes('DefectAnalyzer') then
  begin
    if MsgBox('Обнаружено запущенное приложение DefectAnalyzer. ' +
              'Для корректного удаления необходимо закрыть приложение. ' +
              'Закрыть приложение сейчас?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Пытаемся закрыть приложение
      if not Exec('taskkill', '/F /IM ' + '{#AppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode) then
      begin
        MsgBox('Не удалось автоматически закрыть приложение. ' +
               'Пожалуйста, закройте DefectAnalyzer вручную и повторите удаление.', 
               mbError, MB_OK);
        Result := False;
      end;
    end
    else
    begin
      Result := False;
    end;
  end;
end;

// =============================================================================
; ДОПОЛНИТЕЛЬНЫЕ ОПЦИИ (ЗАКОММЕНТИРОВАНЫ ПО УМОЛЧАНИЮ)
; =============================================================================

; УСТАНОВКА VC++ REDISTRIBUTABLE
; Раскомментируйте этот блок, если нужно установить Visual C++ Redistributable
; [Run]
; Filename: "{app}\runtime\vcredist_x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "Установка Visual C++ Redistributable..."; Check: not IsVCRedistInstalled

; [Code]
; function IsVCRedistInstalled: Boolean;
; var
;   Version: Cardinal;
; begin
;   Result := RegQueryDWordValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Version', Version);
; end;

; АССОЦИАЦИЯ ФАЙЛОВ
; Раскомментируйте этот блок, если нужно зарегистрировать расширения файлов
; [Registry]
; Root: HKCR; Subkey: ".defect"; ValueType: string; ValueName: ""; ValueData: "DefectAnalyzerFile"
; Root: HKCR; Subkey: "DefectAnalyzerFile"; ValueType: string; ValueName: ""; ValueData: "DefectAnalyzer File"
; Root: HKCR; Subkey: "DefectAnalyzerFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"
; Root: HKCR; Subkey: "DefectAnalyzerFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""

; СОЗДАНИЕ ФАЙЛА КОНФИГУРАЦИИ
; Раскомментируйте этот блок, если нужно создать файл конфигурации по умолчанию
; [Files]
; Source: "..\default_config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist

; =============================================================================
; ПРИМЕЧАНИЯ ПО НАСТРОЙКЕ
; =============================================================================
; 
; 1. ЗАМЕНИТЕ ЗНАЧЕНИЯ В СЕКЦИИ КОНСТАНТ:
;    - AppName: имя вашего приложения
;    - AppVersion: версия приложения
;    - AppPublisher: название компании/разработчика
;    - AppURL: ссылка на сайт/репозиторий
;    - AppExeName: имя главного exe файла
;
; 2. УБЕДИТЕСЬ, ЧТО СТРУКТУРА build/win/ СОДЕРЖИТ:
;    - Все необходимые файлы приложения
;    - DLL библиотеки
;    - Ресурсы и конфигурационные файлы
;
; 3. ДЛЯ ИКОНКИ:
;    - Поместите app.ico в папку installer/
;    - Раскомментируйте соответствующие строки в [Files]
;
; 4. ДЛЯ VC++ REDISTRIBUTABLE:
;    - Скачайте vcredist_x64.exe с официального сайта Microsoft
;    - Поместите в installer/runtime/
;    - Раскомментируйте блок [Run] и функцию IsVCRedistInstalled
;
; 5. ДЛЯ АССОЦИАЦИИ ФАЙЛОВ:
;    - Раскомментируйте соответствующий блок в [Registry]
;    - Измените расширения на нужные вам
;
; 6. КОМПИЛЯЦИЯ:
;    - Установите Inno Setup
;    - Откройте этот файл в Inno Setup Compiler
;    - Нажмите F9 или Build -> Compile
;    - Или используйте командную строку: iscc DefectAnalyzer.iss
;
; =============================================================================
