# 🍎 DefectAnalyzer для macOS

Автоматическая система сборки macOS приложения с помощью GitHub Actions.

## 🚀 Быстрый старт

### 1. Загрузите на GitHub
```bash
git add .
git commit -m "Add macOS build system"
git push origin main
```

### 2. Создайте релиз
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 3. Скачайте DMG
- GitHub → Releases → DefectAnalyzer.dmg

## 📁 Структура файлов

```
.github/workflows/build-macos.yml     # GitHub Actions workflow
scripts/
├── build_macos.sh                   # Сборка .app bundle
├── create_dmg.sh                    # Создание DMG
└── sign_and_notarize.sh            # Подпись кода
build_macos_local.sh                 # Локальная сборка
BUILD_MACOS_GUIDE.md                 # Полная документация
QUICK_START_MACOS.md                 # Быстрый старт
MACOS_BUILD_PROCESS.md               # Схема процесса
```

## 🛠️ Локальная сборка

```bash
# На macOS машине
chmod +x build_macos_local.sh
./build_macos_local.sh
```

## 🔐 Подпись кода (опционально)

Настройте секреты в GitHub:
- `APPLE_ID` - ваш Apple ID
- `APPLE_ID_PASSWORD` - app-specific password
- `TEAM_ID` - ваш Team ID

## 📊 Результаты

- **DMG установщик**: `dist/DefectAnalyzer.dmg`
- **App Bundle**: `dist/DefectAnalyzer.app`
- **Артефакты**: GitHub Actions
- **Релизы**: GitHub Releases

## 📖 Документация

- [Полное руководство](BUILD_MACOS_GUIDE.md)
- [Быстрый старт](QUICK_START_MACOS.md)
- [Процесс сборки](MACOS_BUILD_PROCESS.md)
- [Настройка секретов](.github/workflows/macos-secrets-template.md)

## ✅ Что работает

- ✅ Автоматическая сборка при push/тегах
- ✅ Создание .app bundle
- ✅ DMG установщик с красивым интерфейсом
- ✅ Подпись кода и нотаризация
- ✅ Автоматические релизы
- ✅ Локальная сборка для тестирования

## 🎯 Системные требования

- **macOS**: 10.15 (Catalina) или новее
- **Архитектура**: Intel x64, Apple Silicon (M1/M2)
- **Интернет**: для работы с OpenAI API

---

**Готово к использованию! 🚀**
