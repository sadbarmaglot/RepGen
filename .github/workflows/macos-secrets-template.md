# 🔐 Настройка секретов для macOS сборки

Для полной функциональности сборки macOS приложения (включая подпись кода и нотаризацию) необходимо настроить следующие секреты в GitHub:

## 📋 Необходимые секреты

Перейдите в **Settings → Secrets and variables → Actions** и добавьте:

### 1. APPLE_ID
```
APPLE_ID=your_apple_id@example.com
```
- Ваш Apple ID (email)
- Должен иметь доступ к Apple Developer Program

### 2. APPLE_ID_PASSWORD
```
APPLE_ID_PASSWORD=abcd-efgh-ijkl-mnop
```
- App-specific password (НЕ обычный пароль!)
- Создается в appleid.apple.com → Security → App-Specific Passwords
- Название: "macOS App Notarization"

### 3. TEAM_ID
```
TEAM_ID=ABCD123456
```
- 10-символьный идентификатор команды
- Найти в Apple Developer Portal → Membership

## 🛠️ Как получить TEAM_ID

1. Войдите в [developer.apple.com](https://developer.apple.com)
2. Перейдите в **Account → Membership**
3. Скопируйте **Team ID** (10 символов)

## 🔑 Как создать App-specific password

1. Перейдите в [appleid.apple.com](https://appleid.apple.com)
2. Войдите в свой аккаунт
3. Перейдите в **Security → App-Specific Passwords**
4. Нажмите **"Generate Password"**
5. Введите название: "macOS App Notarization"
6. Скопируйте сгенерированный пароль (формат: abcd-efgh-ijkl-mnop)

## ⚠️ Важные замечания

- **НЕ используйте** обычный пароль Apple ID
- **App-specific password** создается только один раз
- **Сохраните пароль** в безопасном месте
- **TEAM_ID** остается неизменным для вашей команды

## 🚫 Без секретов

Если секреты не настроены:
- ✅ Приложение будет собрано
- ✅ DMG будет создан
- ❌ Подпись кода будет пропущена
- ❌ Нотаризация будет пропущена
- ⚠️ Пользователи увидят предупреждение при запуске

## ✅ Проверка настройки

После добавления секретов:
1. Создайте тег: `git tag v1.0.0 && git push origin v1.0.0`
2. Проверьте GitHub Actions → Build macOS App
3. Убедитесь что шаг "Sign and notarize" выполнился успешно

---

**Безопасность**: Никогда не коммитьте эти значения в код!
