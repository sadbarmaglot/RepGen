# ==========================================
# 🏗️ ЛОКАЛЬНАЯ СБОРКА УСТАНОВЩИКА (PowerShell)
# ==========================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🏗️ ЛОКАЛЬНАЯ СБОРКА УСТАНОВЩИКА" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Функция для поиска Inno Setup
function Find-InnoSetup {
    $paths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 5\ISCC.exe"
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            Write-Host "✅ Найден Inno Setup: $path" -ForegroundColor Green
            return $path
        }
    }
    
    Write-Host "❌ Inno Setup не найден!" -ForegroundColor Red
    Write-Host "Скачайте с https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "или установите через: choco install innosetup" -ForegroundColor Yellow
    return $null
}

# Проверяем наличие Inno Setup
$isccPath = Find-InnoSetup
if (-not $isccPath) {
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем структуру проекта
Write-Host ""
Write-Host "📁 Проверяем структуру проекта..." -ForegroundColor Yellow

if (-not (Test-Path "build\win")) {
    Write-Host "❌ Папка build\win не найдена!" -ForegroundColor Red
    Write-Host "Убедитесь, что приложение собрано и находится в build\win\" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем наличие exe файлов
$exeFiles = Get-ChildItem -Path "build\win" -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue
if ($exeFiles.Count -eq 0) {
    Write-Host "⚠️ ВНИМАНИЕ: Не найдено exe файлов в build\win\" -ForegroundColor Yellow
    Write-Host "Убедитесь, что приложение собрано" -ForegroundColor Yellow
} else {
    Write-Host "✅ Найдены exe файлы:" -ForegroundColor Green
    $exeFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor White }
}

# Показываем содержимое build/win
Write-Host ""
Write-Host "📋 Содержимое build\win\:" -ForegroundColor Yellow
Get-ChildItem -Path "build\win" -Recurse | ForEach-Object { 
    Write-Host "  $($_.FullName)" -ForegroundColor Gray 
}

# Проверяем наличие скрипта установщика
if (-not (Test-Path "installer\windows\DefectAnalyzer.iss")) {
    Write-Host "❌ Файл installer\windows\DefectAnalyzer.iss не найден!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""
Write-Host "🔧 Компилируем установщик..." -ForegroundColor Yellow
Write-Host "Используем: $isccPath" -ForegroundColor White
Write-Host "Компилируем: installer\windows\DefectAnalyzer.iss" -ForegroundColor White
Write-Host ""

# Запускаем компиляцию
try {
    & $isccPath "installer\windows\DefectAnalyzer.iss"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Установщик успешно скомпилирован!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Ошибка компиляции установщика!" -ForegroundColor Red
        Write-Host "Проверьте файл installer\windows\DefectAnalyzer.iss" -ForegroundColor Yellow
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Ошибка при запуске компиляции: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем результат
Write-Host ""
Write-Host "📋 Проверяем результат..." -ForegroundColor Yellow

if (Test-Path "dist") {
    $setupFiles = Get-ChildItem -Path "dist" -Filter "*.exe" -ErrorAction SilentlyContinue
    if ($setupFiles.Count -gt 0) {
        Write-Host "📁 Созданные установщики:" -ForegroundColor Green
        $setupFiles | ForEach-Object { 
            $sizeKB = [math]::Round($_.Length / 1KB, 2)
            Write-Host "  - $($_.Name) ($sizeKB KB)" -ForegroundColor White 
        }
        
        Write-Host ""
        Write-Host "🎉 ГОТОВО! Установщик находится в папке dist\" -ForegroundColor Green
        Write-Host "📦 Скопируйте .exe файл на флешку для установки" -ForegroundColor Cyan
        
        # Предлагаем открыть папку
        Write-Host ""
        $openFolder = Read-Host "Открыть папку dist? (y/n)"
        if ($openFolder -eq "y" -or $openFolder -eq "Y") {
            Invoke-Item "dist"
        }
    } else {
        Write-Host "⚠️ В папке dist не найдено exe файлов" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️ Папка dist не найдена" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Read-Host "Нажмите Enter для выхода"
