#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск современного интерфейса ИИ-Инженера
"""

import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

def check_dependencies():
    """Проверка наличия необходимых зависимостей"""
    required_packages = [
        ('tkinter', 'tkinter'),
        ('PIL', 'Pillow'),
        ('openai', 'openai'),
    ]
    
    missing_packages = []
    
    for package_import, package_name in required_packages:
        try:
            __import__(package_import)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Отсутствуют необходимые пакеты:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nУстановите их командой:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_openai_key():
    """Проверка наличия API ключа OpenAI"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ Не найден API ключ OpenAI!")
        print("Установите переменную окружения OPENAI_API_KEY")
        print("Или создайте файл .env с содержимым:")
        print("OPENAI_API_KEY=your_api_key_here")
        return False
    return True

def setup_environment():
    """Настройка окружения приложения"""
    # Загружаем .env файл если есть
    env_file = root_dir / '.env'
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("✅ Загружен .env файл")
        except ImportError:
            print("⚠️ python-dotenv не установлен, используем системные переменные")
    
    # Проверяем API ключ
    return check_openai_key()

def main():
    """Главная функция приложения"""
    print("🏗️ Запуск современного ИИ-Инженера...")
    
    # Проверяем зависимости
    if not check_dependencies():
        input("Нажмите Enter для выхода...")
        return 1
    
    # Настраиваем окружение
    if not setup_environment():
        input("Нажмите Enter для выхода...")
        return 1
    
    try:
        # Импортируем и запускаем приветственное окно
        from ui.welcome_window import WelcomeWindow
        
        print("✅ Запуск современного интерфейса...")
        app = WelcomeWindow()
        app.run()
        
        print("👋 Приложение закрыто")
        return 0
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь что все файлы приложения на месте")
        input("Нажмите Enter для выхода...")
        return 1
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        return 1

if __name__ == "__main__":
    sys.exit(main())

