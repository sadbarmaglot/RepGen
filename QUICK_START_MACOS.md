# 🚀 Быстрый старт: macOS установщик

## 📦 Что создано

✅ **GitHub Actions workflow** - автоматическая сборка при push/тегах  
✅ **Скрипты сборки** - создание .app bundle и DMG  
✅ **Подпись кода** - нотаризация для App Store  
✅ **Документация** - полное руководство по развертыванию  

## 🎯 Быстрый запуск

### 1. Загрузите код на GitHub
```bash
git add .
git commit -m "Add macOS build system"
git push origin main
```

### 2. Настройте секреты (опционально)
В GitHub → Settings → Secrets and variables → Actions:
- `APPLE_ID` - ваш Apple ID
- `APPLE_ID_PASSWORD` - app-specific password  
- `TEAM_ID` - ваш Team ID

### 3. Создайте релиз
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 4. Скачайте DMG
- Перейдите в GitHub → Releases
- Скачайте `DefectAnalyzer.dmg`

## 🖥️ Локальная сборка

```bash
# На macOS машине
chmod +x build_macos_local.sh
./build_macos_local.sh
```

## 📁 Созданные файлы

```
.github/workflows/build-macos.yml     # GitHub Actions
scripts/build_macos.sh               # Сборка .app
scripts/create_dmg.sh               # Создание DMG
scripts/sign_and_notarize.sh        # Подпись кода
build_macos_local.sh                 # Локальная сборка
BUILD_MACOS_GUIDE.md                # Полная документация
```

## 🔗 Полезные ссылки

- [Полное руководство](BUILD_MACOS_GUIDE.md)
- [Настройка секретов](.github/workflows/macos-secrets-template.md)
- [Apple Developer Portal](https://developer.apple.com)

---

**Готово! 🎉** Ваше приложение теперь автоматически собирается для macOS!
