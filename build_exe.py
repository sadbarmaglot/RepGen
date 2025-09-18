#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сборки Windows приложения в EXE файл
"""

import os
import sys
from pathlib import Path

def build_exe():
    """Сборка EXE файла"""
    try:
        import PyInstaller.__main__
        
        # Путь к главному файлу приложения
        main_file = Path(__file__).parent / "run_modern.py"
        
        # Параметры сборки
        args = [
            str(main_file),
            "--onefile",
            "--windowed",
            "--name=DefectAnalyzer",
            "--icon=assets/icon.ico",  # Если есть иконка
            "--add-data", "windows_app;windows_app",  # Добавляем папку приложения
            "--add-data", "common;common",  # Добавляем общие модули
            "--add-data", "docx_generator;docx_generator",  # Добавляем генератор документов
            "--add-data", "settings.py;.",  # Добавляем настройки
            "--hidden-import=tkinter",
            "--hidden-import=PIL",
            "--hidden-import=openai",
            "--hidden-import=pathlib",
            "--hidden-import=threading",
            "--hidden-import=json",
            "--hidden-import=logging",
        ]
        
        # Запускаем сборку
        PyInstaller.__main__.run(args)
        
        print("✅ EXE файл успешно создан!")
        print("📁 Файл находится в папке dist/")
        
    except ImportError:
        print("❌ PyInstaller не установлен!")
        print("Установите его командой: pip install pyinstaller")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка сборки: {e}")
        return False
        
    return True

if __name__ == "__main__":
    build_exe()
