@echo off
echo ==========================================
echo 🏗️ ЛОКАЛЬНАЯ СБОРКА УСТАНОВЩИКА
echo ==========================================

:: Проверяем наличие Inno Setup
set ISCC_PATH=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    echo ✅ Найден Inno Setup в Program Files (x86)
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
    echo ✅ Найден Inno Setup в Program Files
) else (
    echo ❌ Inno Setup не найден!
    echo Скачайте с https://jrsoftware.org/isdl.php
    echo или установите через: choco install innosetup
    pause
    exit /b 1
)

:: Проверяем наличие готового приложения
if not exist "build\win" (
    echo ❌ Папка build\win не найдена!
    echo Убедитесь, что приложение собрано и находится в build\win\
    pause
    exit /b 1
)

echo.
echo 📁 Проверяем содержимое build\win\...
dir /b build\win\*.exe 2>nul
if errorlevel 1 (
    echo ⚠️ ВНИМАНИЕ: Не найдено exe файлов в build\win\
    echo Убедитесь, что приложение собрано
) else (
    echo ✅ Найдены exe файлы в build\win\
)

:: Проверяем наличие скрипта установщика
if not exist "installer\windows\DefectAnalyzer.iss" (
    echo ❌ Файл installer\windows\DefectAnalyzer.iss не найден!
    pause
    exit /b 1
)

echo.
echo 🔧 Компилируем установщик...
echo Используем: %ISCC_PATH%
echo Компилируем: installer\windows\DefectAnalyzer.iss
echo.

:: Запускаем компиляцию
%ISCC_PATH% installer\windows\DefectAnalyzer.iss

if errorlevel 1 (
    echo.
    echo ❌ Ошибка компиляции установщика!
    echo Проверьте файл installer\windows\DefectAnalyzer.iss
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Установщик успешно скомпилирован!
)

echo.
echo 📋 Проверяем результат...
if exist "dist" (
    echo 📁 Файлы в папке dist:
    dir /b dist\*.exe
    echo.
    echo 🎉 ГОТОВО! Установщик находится в папке dist\
    echo 📦 Скопируйте .exe файл на флешку для установки
) else (
    echo ⚠️ Папка dist не найдена
)

echo.
echo ==========================================
pause
