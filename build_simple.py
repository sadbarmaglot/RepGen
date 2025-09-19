#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой скрипт сборки без Unicode символов
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Основная функция"""
    print("[INFO] Запуск сборки...")
    
    # Проверяем наличие main.py
    if not Path("main.py").exists():
        print("[ERROR] main.py не найден!")
        return 1
    
    # Аргументы PyInstaller
    args = [
        "pyinstaller",
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
        "main.py"
    ]
    
    # Добавляем иконку если есть
    if Path("assets/icon.ico").exists():
        args.insert(4, "--icon=assets/icon.ico")
    
    print("[INFO] Запуск PyInstaller...")
    
    try:
        # Запускаем PyInstaller
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        print("[OK] Сборка завершена успешно!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Ошибка PyInstaller: {e}")
        print(f"[ERROR] Код выхода: {e.returncode}")
        return 1
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
