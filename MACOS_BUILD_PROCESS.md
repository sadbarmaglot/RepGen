# 🔄 Процесс сборки macOS приложения

## 📊 Схема процесса

```
GitHub Push/Tag
       ↓
GitHub Actions (macOS Runner)
       ↓
┌─────────────────────────────────────┐
│ 1. Checkout Code                    │
│ 2. Setup Python 3.10               │
│ 3. Install Dependencies            │
│ 4. Cache Dependencies              │
└─────────────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│ 5. Build macOS App Bundle           │
│    - PyInstaller сборка             │
│    - Создание .app структуры         │
│    - Info.plist настройка           │
└─────────────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│ 6. Create DMG Installer            │
│    - Создание DMG образа            │
│    - Настройка внешнего вида        │
│    - Добавление README              │
└─────────────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│ 7. Sign & Notarize (if secrets)    │
│    - Подпись кода                   │
│    - Отправка на нотаризацию        │
│    - Скрепление билета              │
└─────────────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│ 8. Upload Artifacts                 │
│    - DMG файл                       │
│    - App Bundle                     │
└─────────────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│ 9. Create Release (on tag)         │
│    - Автоматический релиз           │
│    - DMG в релизе                  │
└─────────────────────────────────────┘
```

## 🛠️ Детали каждого этапа

### 1-4. Подготовка окружения
- **Checkout**: Клонирование кода
- **Python Setup**: Установка Python 3.10
- **Dependencies**: Установка requirements.txt
- **Cache**: Кэширование pip пакетов

### 5. Сборка App Bundle
```bash
pyinstaller --onefile --windowed \
  --name=DefectAnalyzer \
  --add-data="ui:ui" \
  --osx-bundle-identifier=com.defectanalyzer.app \
  main.py
```

**Результат**: `dist/DefectAnalyzer.app`

### 6. Создание DMG
```bash
hdiutil create -srcfolder temp_dmg \
  -volname "DefectAnalyzer" \
  -format UDZO \
  dist/DefectAnalyzer.dmg
```

**Результат**: `dist/DefectAnalyzer.dmg`

### 7. Подпись и нотаризация
```bash
# Подпись
codesign --force --deep --sign "Developer ID Application: $TEAM_ID" DefectAnalyzer.app

# Нотаризация
xcrun notarytool submit DefectAnalyzer.zip \
  --apple-id $APPLE_ID \
  --password $APPLE_ID_PASSWORD \
  --team-id $TEAM_ID

# Скрепление билета
xcrun stapler staple DefectAnalyzer.app
```

### 8-9. Публикация
- **Artifacts**: Загрузка в GitHub Actions
- **Release**: Автоматическое создание релиза при тегах

## ⏱️ Временные затраты

| Этап | Время | Описание |
|------|-------|----------|
| Подготовка | 2-3 мин | Установка зависимостей |
| Сборка | 3-5 мин | PyInstaller + App Bundle |
| DMG | 1-2 мин | Создание установщика |
| Подпись | 5-10 мин | Нотаризация Apple |
| Публикация | 1 мин | Загрузка артефактов |
| **Итого** | **12-21 мин** | Полный цикл |

## 🔧 Требования

### Системные
- **macOS Runner**: GitHub Actions предоставляет
- **Python**: 3.10 (автоматически)
- **Инструменты**: hdiutil, codesign, xcrun

### Дополнительные (для подписи)
- **Apple Developer Account**: $99/год
- **Developer ID Certificate**: Создается в Portal
- **App-specific Password**: Для нотаризации

## 🚨 Возможные ошибки

### Сборка
- **ImportError**: Добавить `--hidden-import`
- **Missing modules**: Проверить requirements.txt
- **PyInstaller errors**: Обновить версию

### Подпись
- **Certificate not found**: Проверить Keychain
- **Invalid Team ID**: Проверить в Developer Portal
- **Notarization failed**: Проверить App-specific password

### DMG
- **Mount errors**: Очистить временные файлы
- **Size too large**: Увеличить размер образа
- **Permission denied**: Проверить права доступа

## 📈 Оптимизация

### Ускорение сборки
- **Кэширование**: pip dependencies
- **Параллелизация**: Несколько job'ов
- **Уменьшение размера**: Исключение ненужных модулей

### Улучшение DMG
- **Сжатие**: UDZO формат
- **Красивый дизайн**: Кастомный фон
- **Автоматическая установка**: Drag & Drop

---

**Процесс полностью автоматизирован! 🚀**
