# 🪟 Руководство по сборке Windows приложения

## 📋 Обзор

Это руководство поможет вам создать исполняемый файл (.exe) для Windows из Python приложения DefectAnalyzer.

## 🛠️ Требования

### Обязательные компоненты:
- **Python 3.8+** - [Скачать с python.org](https://python.org)
- **Git** - [Скачать с git-scm.com](https://git-scm.com)

### Для создания установщика:
- **Inno Setup 6** - [Скачать с jrsoftware.org](https://jrsoftware.org/isinfo.php)

## 🚀 Способы сборки

### 1️⃣ Автоматическая сборка через GitHub Actions (Рекомендуется)

**Самый простой способ** - использовать автоматическую сборку:

1. **Загрузите код в репозиторий:**
   ```bash
   git add .
   git commit -m "Подготовка к сборке Windows приложения"
   git push windows main
   ```

2. **Запустите сборку:**
   - Перейдите в ваш репозиторий на GitHub
   - Откройте вкладку "Actions"
   - Найдите workflow "Build Windows Installer"
   - Нажмите "Run workflow"
   - Выберите ветку `main` и нажмите "Run workflow"

3. **Скачайте результат:**
   - После завершения сборки (5-10 минут)
   - В разделе "Artifacts" скачайте `windows-installer`
   - Распакуйте архив - внутри будет файл `Setup-DefectAnalyzer-1.0.0.exe`

### 2️⃣ Локальная сборка на Windows

#### Вариант A: Через PowerShell (Рекомендуется)

1. **Откройте PowerShell как администратор**

2. **Перейдите в папку проекта:**
   ```powershell
   cd C:\path\to\RepGen
   ```

3. **Запустите скрипт сборки:**
   ```powershell
   .\build_windows_local.ps1
   ```

4. **Результат:**
   - EXE файл: `build\win\DefectAnalyzer.exe`

#### Вариант B: Через командную строку

1. **Откройте командную строку**

2. **Перейдите в папку проекта:**
   ```cmd
   cd C:\path\to\RepGen
   ```

3. **Запустите скрипт сборки:**
   ```cmd
   build_windows_local.bat
   ```

#### Вариант C: Ручная сборка

1. **Создайте виртуальное окружение:**
   ```cmd
   python -m venv venv_build
   venv_build\Scripts\activate
   ```

2. **Установите зависимости:**
   ```cmd
   pip install -r requirements.txt
   pip install pyinstaller
   ```

3. **Соберите приложение:**
   ```cmd
   python build_exe.py
   ```

4. **Результат:**
   - EXE файл: `dist\DefectAnalyzer.exe`

### 3️⃣ Сборка на macOS/Linux для Windows

Если у вас нет Windows машины, можно собрать на macOS/Linux:

```bash
# Установите wine для создания Windows exe
brew install wine  # macOS
# или
sudo apt install wine  # Ubuntu/Debian

# Запустите скрипт сборки
./build_windows_app.sh
```

## 📦 Создание установщика

### Через Inno Setup (Рекомендуется)

1. **Установите Inno Setup 6**

2. **Откройте файл установщика:**
   - Файл: `installer\windows\DefectAnalyzer.iss`

3. **Настройте параметры:**
   - Версию приложения
   - Название компании
   - URL проекта
   - Иконку (если есть)

4. **Скомпилируйте установщик:**
   - Нажмите `F9` или `Build -> Compile`
   - Установщик будет создан в папке `dist\`

### Автоматически через GitHub Actions

GitHub Actions автоматически создает установщик при сборке.

## 🔧 Настройка и отладка

### Проблемы с зависимостями

Если приложение не запускается:

1. **Проверьте отсутствующие модули:**
   ```cmd
   python -c "import tkinter, PIL, openai; print('Все модули найдены')"
   ```

2. **Установите недостающие пакеты:**
   ```cmd
   pip install missing-package-name
   ```

### Проблемы с PyInstaller

1. **Очистите кэш:**
   ```cmd
   pyinstaller --clean main.py
   ```

2. **Добавьте скрытые импорты в build_exe.py:**
   ```python
   "--hidden-import=module_name",
   ```

### Проблемы с размерами файла

Если EXE файл слишком большой:

1. **Исключите ненужные модули:**
   ```python
   "--exclude-module=module_name",
   ```

2. **Используйте UPX для сжатия:**
   ```python
   "--upx-dir=path\to\upx",
   ```

## 📁 Структура файлов после сборки

```
build/
└── win/
    ├── DefectAnalyzer.exe          # Главный исполняемый файл
    └── [другие файлы и библиотеки]

dist/
└── Setup-DefectAnalyzer-1.0.0.exe # Установщик (если создан)
```

## 🚨 Частые проблемы и решения

### ❌ "Python не найден"
**Решение:** Установите Python и добавьте в PATH

### ❌ "PyInstaller не найден"
**Решение:** 
```cmd
pip install pyinstaller
```

### ❌ "tkinter не найден"
**Решение:** Установите tkinter:
```cmd
# Windows
pip install tk

# Ubuntu/Debian
sudo apt install python3-tk
```

### ❌ "Приложение не запускается"
**Решение:** 
1. Запустите из командной строки для просмотра ошибок
2. Проверьте все зависимости
3. Убедитесь что все файлы на месте

### ❌ "Ошибка при создании установщика"
**Решение:**
1. Установите Inno Setup 6
2. Проверьте пути в DefectAnalyzer.iss
3. Убедитесь что EXE файл существует

## 📞 Поддержка

Если возникли проблемы:

1. **Проверьте логи сборки**
2. **Убедитесь что все зависимости установлены**
3. **Попробуйте очистить кэш и пересобрать**
4. **Создайте issue в репозитории**

## 🎯 Результат

После успешной сборки у вас будет:

- ✅ **DefectAnalyzer.exe** - готовое к запуску приложение
- ✅ **Setup-DefectAnalyzer-1.0.0.exe** - установщик для распространения
- ✅ Все зависимости включены в один файл
- ✅ Приложение работает без установки Python

---

**Удачной сборки! 🚀**
