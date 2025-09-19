#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сборки Windows приложения в EXE файл
БЕЗОПАСНАЯ ВЕРСИЯ - только ASCII символы
"""

import os
import sys
from pathlib import Path

def safe_print(message, prefix="INFO"):
    """Безопасный вывод сообщений"""
    try:
        print(f"[{prefix}] {message}")
    except UnicodeEncodeError:
        # Заменяем проблемные символы
        safe_msg = message.encode('ascii', 'replace').decode('ascii')
        print(f"[{prefix}] {safe_msg}")

def build_exe():
    """Сборка EXE файла"""
    try:
        import PyInstaller.__main__
        
        # Путь к главному файлу приложения
        main_file = Path(__file__).parent / "main.py"
        
        # Параметры сборки
        args = [
            str(main_file),
            "--onefile",
            "--windowed",
            "--name=DefectAnalyzer",
            "--add-data", "ui;ui",
            "--add-data", "common;common",
            "--add-data", "docx_generator;docx_generator",
            "--add-data", "adapters;adapters",
            "--add-data", "assets;assets",
            "--add-data", "examples;examples",
            "--add-data", "settings.py;.",
            "--hidden-import=tkinter",
            "--hidden-import=tkinter.ttk",
            "--hidden-import=tkinter.messagebox",
            "--hidden-import=tkinter.filedialog",
            "--hidden-import=PIL",
            "--hidden-import=PIL.Image",
            "--hidden-import=PIL.ImageTk",
            "--hidden-import=openai",
            "--hidden-import=pathlib",
            "--hidden-import=threading",
            "--hidden-import=json",
            "--hidden-import=logging",
            "--hidden-import=requests",
            "--hidden-import=docx",
            "--hidden-import=dotenv",
            "--hidden-import=trimesh",
            "--hidden-import=numpy",
        ]
        
        # Добавляем иконку если есть
        icon_file = Path(__file__).parent / "assets" / "icon.ico"
        if icon_file.exists():
            args.append("--icon=assets/icon.ico")
        
        # Запускаем сборку
        PyInstaller.__main__.run(args)
        
        safe_print("EXE файл успешно создан!", "OK")
        safe_print("Файл находится в папке dist/", "INFO")
        
    except ImportError:
        safe_print("PyInstaller не установлен!", "ERROR")
        safe_print("Установите его командой: pip install pyinstaller", "INFO")
        return False
        
    except Exception as e:
        safe_print(f"Ошибка сборки: {e}", "ERROR")
        return False
        
    return True

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
