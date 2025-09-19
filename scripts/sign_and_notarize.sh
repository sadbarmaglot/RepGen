#!/bin/bash
# -*- coding: utf-8 -*-
"""
Скрипт для подписи кода и нотаризации macOS приложения
Требует Apple Developer Account
"""

set -e  # Остановка при ошибке

echo "🔐 Настраиваем подпись кода и нотаризацию..."

APP_NAME="DefectAnalyzer"
APP_DIR="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME}.dmg"
DMG_PATH="dist/${DMG_NAME}"

# Проверяем наличие необходимых переменных окружения
if [ -z "$APPLE_ID" ]; then
    echo "⚠️ Переменная APPLE_ID не установлена"
    echo "Установите: export APPLE_ID=your_apple_id@example.com"
fi

if [ -z "$APPLE_ID_PASSWORD" ]; then
    echo "⚠️ Переменная APPLE_ID_PASSWORD не установлена"
    echo "Установите: export APPLE_ID_PASSWORD=your_app_specific_password"
fi

if [ -z "$TEAM_ID" ]; then
    echo "⚠️ Переменная TEAM_ID не установлена"
    echo "Установите: export TEAM_ID=your_team_id"
fi

# Проверяем что приложение существует
if [ ! -d "${APP_DIR}" ]; then
    echo "❌ Ошибка: Приложение ${APP_DIR} не найдено!"
    exit 1
fi

echo "✍️ Подписываем приложение..."

# Подписываем приложение
codesign --force --deep --sign "Developer ID Application: ${TEAM_ID}" "${APP_DIR}"

echo "🔍 Проверяем подпись..."
codesign --verify --verbose "${APP_DIR}"

echo "📋 Получаем информацию о подписи..."
codesign --display --verbose "${APP_DIR}"

echo "📦 Создаем ZIP архив для нотаризации..."
ZIP_PATH="dist/${APP_NAME}.zip"
rm -f "${ZIP_PATH}"
ditto -c -k --keepParent "${APP_DIR}" "${ZIP_PATH}"

echo "🚀 Отправляем на нотаризацию..."
if [ -n "$APPLE_ID" ] && [ -n "$APPLE_ID_PASSWORD" ]; then
    # Отправляем на нотаризацию
    xcrun notarytool submit "${ZIP_PATH}" \
        --apple-id "${APPLE_ID}" \
        --password "${APPLE_ID_PASSWORD}" \
        --team-id "${TEAM_ID}" \
        --wait
    
    echo "✅ Нотаризация завершена!"
    
    # Скрепляем билет нотаризации
    echo "🎫 Скрепляем билет нотаризации..."
    xcrun stapler staple "${APP_DIR}"
    
    # Проверяем что билет прикреплен
    xcrun stapler validate "${APP_DIR}"
    
else
    echo "⚠️ Пропускаем нотаризацию - не установлены учетные данные"
fi

echo "💿 Подписываем DMG (если существует)..."
if [ -f "${DMG_PATH}" ]; then
    codesign --force --sign "Developer ID Application: ${TEAM_ID}" "${DMG_PATH}"
    codesign --verify --verbose "${DMG_PATH}"
    
    if [ -n "$APPLE_ID" ] && [ -n "$APPLE_ID_PASSWORD" ]; then
        echo "🚀 Отправляем DMG на нотаризацию..."
        xcrun notarytool submit "${DMG_PATH}" \
            --apple-id "${APPLE_ID}" \
            --password "${APPLE_ID_PASSWORD}" \
            --team-id "${TEAM_ID}" \
            --wait
        
        echo "🎫 Скрепляем билет нотаризации к DMG..."
        xcrun stapler staple "${DMG_PATH}"
        xcrun stapler validate "${DMG_PATH}"
    fi
fi

echo "✅ Подпись и нотаризация завершены!"
echo "📁 Подписанное приложение: ${APP_DIR}"
if [ -f "${DMG_PATH}" ]; then
    echo "💿 Подписанный DMG: ${DMG_PATH}"
fi
