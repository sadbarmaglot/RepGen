# ==========================================
# 🪟 СБОРКА WINDOWS ПРИЛОЖЕНИЯ НА WINDOWS (PowerShell)
# ==========================================

param(
    [switch]$Clean,
    [switch]$NoVirtualEnv,
    [string]$PythonPath = "python"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🪟 СБОРКА WINDOWS ПРИЛОЖЕНИЯ НА WINDOWS" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Функция для вывода сообщений
function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    $timestamp = Get-Date -Format "HH:mm:ss"
    switch ($Type) {
        "Success" { Write-Host "✅ $Message" -ForegroundColor Green }
        "Error" { Write-Host "❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "⚠️ $Message" -ForegroundColor Yellow }
        default { Write-Host "ℹ️ $Message" -ForegroundColor Blue }
    }
}

# Проверяем наличие Python
Write-Status "Проверяем Python..."
try {
    $pythonVersion = & $PythonPath --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Python найден: $pythonVersion" "Success"
    } else {
        throw "Python не найден"
    }
} catch {
    Write-Status "Python не найден! Установите Python с https://python.org" "Error"
    exit 1
}

# Очистка предыдущих сборок
if ($Clean) {
    Write-Status "Очищаем предыдущие сборки..."
    if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
    if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
    if (Test-Path "*.spec") { Remove-Item "*.spec" -Force }
    Write-Status "Очистка завершена" "Success"
}

# Создаем виртуальное окружение
if (-not $NoVirtualEnv) {
    Write-Status "Создаем виртуальное окружение..."
    if (Test-Path "venv_build") {
        Remove-Item "venv_build" -Recurse -Force
    }
    & $PythonPath -m venv venv_build
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Виртуальное окружение создано" "Success"
    } else {
        Write-Status "Ошибка создания виртуального окружения" "Error"
        exit 1
    }
    
    # Активируем виртуальное окружение
    Write-Status "Активируем виртуальное окружение..."
    $activateScript = "venv_build\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Status "Виртуальное окружение активировано" "Success"
    } else {
        Write-Status "Скрипт активации не найден" "Error"
        exit 1
    }
}

# Устанавливаем зависимости
Write-Status "Устанавливаем зависимости..."
& $PythonPath -m pip install --upgrade pip
& $PythonPath -m pip install pyinstaller

if (Test-Path "requirements.txt") {
    Write-Status "Устанавливаем зависимости из requirements.txt..."
    & $PythonPath -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Зависимости установлены" "Success"
    } else {
        Write-Status "Ошибка установки зависимостей" "Error"
        exit 1
    }
} else {
    Write-Status "requirements.txt не найден" "Warning"
}

# Создаем папку для сборки
Write-Status "Создаем папку для сборки..."
if (-not (Test-Path "build\win")) {
    New-Item -ItemType Directory -Path "build\win" -Force | Out-Null
}

# Проверяем наличие главного файла
if (-not (Test-Path "main.py")) {
    Write-Status "main.py не найден!" "Error"
    exit 1
}

# Собираем приложение
Write-Status "Собираем Windows приложение..."
if (Test-Path "build_exe.py") {
    Write-Status "Запускаем сборку через build_exe.py..."
    & $PythonPath build_exe.py
} else {
    Write-Status "Запускаем PyInstaller напрямую..."
    $pyinstallerArgs = @(
        "--onefile",
        "--windowed", 
        "--name=DefectAnalyzer",
        "--icon=assets\icon.ico",
        "main.py"
    )
    & $PythonPath -m PyInstaller $pyinstallerArgs
}

if ($LASTEXITCODE -eq 0) {
    Write-Status "Сборка завершена" "Success"
} else {
    Write-Status "Ошибка сборки" "Error"
    exit 1
}

# Копируем собранный файл
if (Test-Path "dist\DefectAnalyzer.exe") {
    Copy-Item "dist\DefectAnalyzer.exe" "build\win\" -Force
    Write-Status "DefectAnalyzer.exe скопирован в build\win\" "Success"
    
    # Показываем информацию о файле
    $fileInfo = Get-Item "build\win\DefectAnalyzer.exe"
    Write-Status "Размер файла: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" "Info"
    Write-Status "Дата создания: $($fileInfo.CreationTime)" "Info"
} else {
    Write-Status "DefectAnalyzer.exe не найден в папке dist\" "Error"
    exit 1
}

# Проверяем результат
if (Test-Path "build\win\DefectAnalyzer.exe") {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "🎯 СБОРКА ЗАВЕРШЕНА УСПЕШНО!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "📁 EXE файл: build\win\DefectAnalyzer.exe" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🔧 Для создания установщика:" -ForegroundColor Cyan
    Write-Host "1. Установите Inno Setup" -ForegroundColor White
    Write-Host "2. Откройте installer\windows\DefectAnalyzer.iss" -ForegroundColor White
    Write-Host "3. Нажмите F9 или Build -> Compile" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor Green
} else {
    Write-Status "Приложение не собрано или не найдено" "Error"
    exit 1
}

# Деактивируем виртуальное окружение
if (-not $NoVirtualEnv) {
    deactivate
}

Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
