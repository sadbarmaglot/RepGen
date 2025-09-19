# 🍎 Руководство по сборке macOS приложения

Полное руководство по созданию установщика DefectAnalyzer для macOS с помощью GitHub Actions.

## 📋 Содержание

1. [Автоматическая сборка через GitHub Actions](#автоматическая-сборка)
2. [Локальная сборка на macOS](#локальная-сборка)
3. [Настройка подписи кода](#настройка-подписи-кода)
4. [Создание релизов](#создание-релизов)
5. [Устранение проблем](#устранение-проблем)

## 🚀 Автоматическая сборка

### Настройка GitHub Actions

1. **Создайте репозиторий на GitHub** и загрузите код
2. **Настройте секреты** в Settings → Secrets and variables → Actions:
   ```
   APPLE_ID=your_apple_id@example.com
   APPLE_ID_PASSWORD=your_app_specific_password
   TEAM_ID=your_team_id
   ```

3. **Workflow автоматически запустится** при:
   - Push в ветки `main` или `develop`
   - Создании тега `v*` (например, `v1.0.0`)
   - Ручном запуске через Actions tab

### Результаты сборки

- **DMG установщик**: `dist/DefectAnalyzer.dmg`
- **App Bundle**: `dist/DefectAnalyzer.app`
- **Артефакты**: доступны в разделе Actions
- **Релизы**: автоматически создаются при тегах

## 🖥️ Локальная сборка

### Быстрый старт

```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd RepGen

# Запустите локальную сборку
chmod +x build_macos_local.sh
./build_macos_local.sh
```

### Ручная сборка

```bash
# 1. Установите зависимости
pip3 install -r requirements.txt
pip3 install pyinstaller

# 2. Соберите приложение
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh

# 3. Создайте DMG
chmod +x scripts/create_dmg.sh
./scripts/create_dmg.sh

# 4. Подпишите код (опционально)
export APPLE_ID=your_apple_id@example.com
export APPLE_ID_PASSWORD=your_app_specific_password
export TEAM_ID=your_team_id
chmod +x scripts/sign_and_notarize.sh
./scripts/sign_and_notarize.sh
```

## 🔐 Настройка подписи кода

### Требования

- **Apple Developer Account** ($99/год)
- **Developer ID Application Certificate**
- **App-specific password** для Apple ID

### Получение сертификата

1. Войдите в [Apple Developer Portal](https://developer.apple.com)
2. Перейдите в Certificates, Identifiers & Profiles
3. Создайте **Developer ID Application** сертификат
4. Скачайте и установите сертификат в Keychain

### Настройка переменных окружения

```bash
# В GitHub Secrets или локально
export APPLE_ID=your_apple_id@example.com
export APPLE_ID_PASSWORD=your_app_specific_password  # App-specific password
export TEAM_ID=your_team_id  # Найти в Developer Portal
```

### Создание App-specific password

1. Перейдите в [appleid.apple.com](https://appleid.apple.com)
2. Войдите в свой аккаунт
3. В разделе Security → App-Specific Passwords
4. Создайте новый пароль для "macOS App Notarization"

## 📦 Создание релизов

### Автоматические релизы

```bash
# Создайте и отправьте тег
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions автоматически:
- Соберет приложение
- Подпишет код (если настроено)
- Создаст релиз с DMG файлом

### Ручное создание релиза

1. Перейдите в GitHub → Releases
2. Нажмите "Create a new release"
3. Выберите тег или создайте новый
4. Загрузите DMG файл из артефактов сборки

## 🛠️ Структура файлов

```
.github/workflows/
├── build-macos.yml          # GitHub Actions workflow

scripts/
├── build_macos.sh          # Сборка .app bundle
├── create_dmg.sh           # Создание DMG установщика
└── sign_and_notarize.sh    # Подпись и нотаризация

dist/
├── DefectAnalyzer.app      # macOS приложение
└── DefectAnalyzer.dmg      # DMG установщик
```

## 🔧 Настройка приложения

### Info.plist параметры

Основные настройки в `scripts/build_macos.sh`:

```xml
<key>CFBundleIdentifier</key>
<string>com.defectanalyzer.app</string>
<key>LSMinimumSystemVersion</key>
<string>10.15</string>  <!-- macOS Catalina+ -->
```

### Системные требования

- **macOS**: 10.15 (Catalina) или новее
- **Архитектура**: Intel x64, Apple Silicon (M1/M2)
- **Python**: 3.8+ (встроен в приложение)

## 🐛 Устранение проблем

### Ошибки сборки

**PyInstaller не найден:**
```bash
pip3 install pyinstaller
```

**Модули не найдены:**
```bash
pip3 install -r requirements.txt
```

**Ошибки импорта:**
- Проверьте все `--hidden-import` в `build_macos.sh`
- Добавьте недостающие модули

### Ошибки подписи

**Сертификат не найден:**
```bash
# Проверьте установленные сертификаты
security find-identity -v -p codesigning
```

**Неправильный Team ID:**
- Найдите в Apple Developer Portal → Membership
- Используйте 10-символьный идентификатор

**Ошибки нотаризации:**
- Проверьте App-specific password
- Убедитесь что Apple ID имеет доступ к Developer Program

### Ошибки DMG

**hdiutil ошибки:**
```bash
# Очистите временные файлы
rm -rf temp_dmg
rm -f dist/*.temp
```

**Проблемы с монтированием:**
```bash
# Размонтируйте все DMG
hdiutil detach /Volumes/DefectAnalyzer -force
```

## 📱 Тестирование

### Локальное тестирование

```bash
# Запустите приложение
open dist/DefectAnalyzer.app

# Проверьте логи
log stream --predicate 'process == "DefectAnalyzer"'
```

### Проверка подписи

```bash
# Проверьте подпись приложения
codesign --verify --verbose dist/DefectAnalyzer.app

# Проверьте нотаризацию
spctl --assess --verbose dist/DefectAnalyzer.app
```

## 🚀 Развертывание

### Для пользователей

1. **Скачайте DMG** с GitHub Releases
2. **Откройте DMG** файл
3. **Перетащите приложение** в Applications
4. **Запустите** из Applications или Launchpad

### Первый запуск

При первом запуске macOS может показать предупреждение:
1. Перейдите в **System Preferences → Security & Privacy**
2. Нажмите **"Open Anyway"** рядом с DefectAnalyzer
3. Или запустите из терминала: `open DefectAnalyzer.app`

## 📊 Мониторинг

### GitHub Actions

- Проверяйте статус сборки в Actions tab
- Скачивайте артефакты для тестирования
- Просматривайте логи при ошибках

### Метрики

- **Время сборки**: ~5-10 минут
- **Размер DMG**: ~50-100 MB
- **Размер App**: ~40-80 MB

## 🔄 Обновления

### Автоматические обновления

Для реализации автообновлений рассмотрите:
- [Sparkle](https://sparkle-project.org/) - популярный фреймворк
- [Squirrel](https://github.com/Squirrel/Squirrel.Mac) - альтернатива
- Собственное решение через GitHub API

### Версионирование

Используйте семантическое версионирование:
- `v1.0.0` - мажорный релиз
- `v1.1.0` - минорное обновление
- `v1.1.1` - патч

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи** GitHub Actions
2. **Протестируйте локально** на macOS
3. **Проверьте сертификаты** и учетные данные
4. **Создайте Issue** в GitHub с подробным описанием

---

**Удачной сборки! 🚀**
