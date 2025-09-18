# Windows Installer для DefectAnalyzer

Этот каталог содержит файлы для создания Windows установщика приложения DefectAnalyzer с помощью Inno Setup.

## 📁 Структура файлов

```
installer/
├── README.md                    # Этот файл
├── windows/
│   └── DefectAnalyzer.iss      # Скрипт Inno Setup
├── app.ico                     # Иконка приложения (опционально)
└── runtime/                    # Дополнительные зависимости (опционально)
    └── vcredist_x64.exe        # Visual C++ Redistributable
```

## 🚀 Автоматическая сборка через GitHub Actions

### Запуск сборки

1. **Автоматический запуск**: Сборка запускается автоматически при пуше в ветку `main`
2. **Ручной запуск**: 
   - Перейдите в раздел "Actions" вашего репозитория
   - Выберите "Build Windows Installer"
   - Нажмите "Run workflow"
   - При необходимости укажите версию приложения

### Определение версии

Версия приложения определяется в следующем порядке:
1. **Ручной ввод** в GitHub Actions (если указан)
2. **Git тег** вида `v1.2.3` (автоматически убирается префикс 'v')
3. **Переменная APP_VERSION** в файле `.env`
4. **По умолчанию**: `0.1.0-dev`

### Получение готового установщика

1. После завершения сборки перейдите в раздел "Actions"
2. Откройте последний запуск workflow
3. В разделе "Artifacts" скачайте `windows-installer`
4. Распакуйте архив - внутри будет файл `Setup-DefectAnalyzer-{version}.exe`

## 🛠️ Локальная сборка установщика

### Предварительные требования

1. **Inno Setup 6.x** - [скачать с официального сайта](https://jrsoftware.org/isdl.php)
2. **Готовое Windows приложение** в папке `build/win/`

### Подготовка приложения

Убедитесь, что структура папки `build/win/` выглядит так:
```
build/win/
├── DefectAnalyzer.exe          # Главный исполняемый файл
├── [другие .exe файлы]        # Дополнительные исполняемые файлы
├── [.dll файлы]               # Библиотеки
├── [папки с ресурсами]        # Конфигурации, данные и т.д.
└── [другие файлы]             # Все необходимые файлы
```

### 🚀 Быстрая сборка (рекомендуется)

#### Вариант 1: Через готовый скрипт (Batch)
```batch
# Просто запустите готовый скрипт
build_installer_local.bat
```

#### Вариант 2: Через PowerShell скрипт
```powershell
# Запустите PowerShell скрипт (более подробный)
.\build_installer_local.ps1
```

### Сборка через графический интерфейс

1. Установите Inno Setup
2. Откройте файл `installer/windows/DefectAnalyzer.iss` в Inno Setup Compiler
3. Нажмите `F9` или выберите `Build -> Compile`
4. Готовый установщик появится в папке `dist/`

### Сборка через командную строку

```batch
# Перейдите в корень проекта
cd C:\path\to\RepGen

# Запустите компиляцию
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\DefectAnalyzer.iss
```

## ⚙️ Настройка скрипта установщика

### Основные параметры

Откройте файл `installer/windows/DefectAnalyzer.iss` и измените константы в начале файла:

```pascal
#define AppName "DefectAnalyzer"              // Имя приложения
#define AppVersion "1.0.0"                    // Версия
#define AppPublisher "AI Engineering Solutions" // Издатель
#define AppURL "https://github.com/your-username/RepGen" // Сайт
#define AppExeName "DefectAnalyzer.exe"       // Имя exe файла
```

### Иконка приложения

1. Поместите файл `app.ico` в папку `installer/`
2. В файле `DefectAnalyzer.iss` раскомментируйте строки:
   ```pascal
   Source: "..\app.ico"; DestDir: "{app}"; Flags: ignoreversion
   ```

### Visual C++ Redistributable

Если ваше приложение требует VC++ Redistributable:

1. Скачайте `vcredist_x64.exe` с [официального сайта Microsoft](https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
2. Поместите в папку `installer/runtime/`
3. В файле `DefectAnalyzer.iss` раскомментируйте блок `[Run]` и функцию `IsVCRedistInstalled`

### Ассоциация файлов

Чтобы приложение открывало определенные типы файлов:

1. В файле `DefectAnalyzer.iss` раскомментируйте блок `[Registry]` в разделе "АССОЦИАЦИЯ ФАЙЛОВ"
2. Измените расширения файлов на нужные (например, `.defect`, `.analysis`)

## 🔧 Дополнительные возможности

### Тихая установка

Установщик поддерживает тихую установку:
```batch
Setup-DefectAnalyzer-1.0.0.exe /SILENT
Setup-DefectAnalyzer-1.0.0.exe /VERYSILENT
```

### Проверка запущенных процессов

Установщик автоматически проверяет, не запущено ли приложение, и предлагает закрыть его перед установкой/удалением.

### Права администратора

По умолчанию установщик требует права администратора. Для изменения отредактируйте:
```pascal
PrivilegesRequired=lowest  // Вместо admin
```

## 🐛 Устранение проблем

### "Не найден exe файл"

- Убедитесь, что приложение собрано и находится в `build/win/`
- Проверьте имя файла в константе `AppExeName`

### "ISCC.exe не найден"

- Убедитесь, что Inno Setup установлен
- Проверьте путь в переменной окружения или укажите полный путь

### "Ошибка компиляции"

- Проверьте синтаксис в файле `.iss`
- Убедитесь, что все указанные файлы существуют
- Проверьте права доступа к папкам

### GitHub Actions не запускается

- Убедитесь, что файл `.github/workflows/build-installer.yml` находится в репозитории
- Проверьте, что папка `build/win/` содержит готовое приложение
- Убедитесь, что файл `installer/windows/DefectAnalyzer.iss` существует

## 📝 Примеры использования

### Создание релиза с установщиком

```bash
# Создайте тег версии
git tag v1.2.3
git push origin v1.2.3

# GitHub Actions автоматически соберет установщик
# Версия будет определена из тега: 1.2.3
```

### Указание версии в .env

```env
APP_VERSION=2.0.0-beta
```

### Сборка с кастомной версией

В GitHub Actions выберите "Run workflow" и укажите версию: `3.0.0-rc1`

## 📚 Дополнительные ресурсы

- [Документация Inno Setup](https://jrsoftware.org/ishelp/)
- [Примеры скриптов Inno Setup](https://github.com/jrsoftware/issrc)
- [Visual C++ Redistributable](https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи GitHub Actions
2. Убедитесь в правильности структуры файлов
3. Проверьте настройки в файле `DefectAnalyzer.iss`
4. Создайте issue в репозитории с описанием проблемы
