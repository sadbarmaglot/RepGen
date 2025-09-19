#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Безопасный скрипт для сборки Windows приложения в EXE файл
Без Unicode символов - только ASCII для Windows CI
"""

import os
import sys
from pathlib import Path

# Настройка кодировки для Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def print_safe(message, prefix="INFO"):
    """Безопасный вывод сообщений без Unicode символов"""
    print(f"[{prefix}] {message}")

def check_dependencies():
    """Проверка зависимостей"""
    required_modules = [
        'tkinter', 'PIL', 'openai', 'requests', 
        'docx', 'trimesh', 'numpy'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print_safe(f"{module} OK", "OK")
        except ImportError:
            missing.append(module)
            print_safe(f"{module} не найден", "ERROR")
    
    if missing:
        print_safe(f"Отсутствуют модули: {', '.join(missing)}", "ERROR")
        return False
    
    return True

def check_project_structure():
    """Проверка структуры проекта"""
    required_files = ["main.py", "settings.py", "requirements.txt"]
    required_dirs = ["ui", "adapters", "common", "docx_generator", "assets"]
    
    # Проверяем файлы
    for file in required_files:
        if Path(file).exists():
            print_safe(f"{file} найден", "OK")
        else:
            print_safe(f"{file} не найден", "ERROR")
            return False
    
    # Проверяем папки
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print_safe(f"папка {dir_name} найдена", "OK")
        else:
            print_safe(f"папка {dir_name} не найдена", "ERROR")
            return False
    
    return True

def build_exe():
    """Сборка EXE файла"""
    print_safe("Начинаем сборку Windows приложения...")
    
    # Проверяем структуру проекта
    if not check_project_structure():
        print_safe("Структура проекта некорректна", "ERROR")
        return False
    
    # Проверяем зависимости
    if not check_dependencies():
        print_safe("Зависимости не установлены", "ERROR")
        return False
    
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
            print_safe("Иконка найдена: assets/icon.ico", "OK")
        else:
            print_safe("assets/icon.ico не найден, используем без иконки", "WARNING")
        
        print_safe("Запускаем PyInstaller...")
        
        # Запускаем сборку
        PyInstaller.__main__.run(args)
        
        print_safe("EXE файл успешно создан!", "OK")
        print_safe("Файл находится в папке dist/", "INFO")
        
        return True
        
    except ImportError:
        print_safe("PyInstaller не установлен!", "ERROR")
        print_safe("Установите его командой: pip install pyinstaller", "INFO")
        return False
        
    except Exception as e:
        print_safe(f"Ошибка сборки: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)