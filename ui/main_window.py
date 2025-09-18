#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно ИИ-Инженера
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from pathlib import Path
import sys

# Импортируем поддержку буфера обмена
from ui.clipboard_support import ClipboardEntry, ClipboardScrolledText

# Добавляем путь к корневой папке проекта
sys.path.append(str(Path(__file__).parent.parent))

from adapters.ai_adapter import analyze_local_photo, batch_analyze_photos
from adapters.file_manager import WindowsFileManager
from ui.project_dialogs import ProjectDialog, ProjectManagerDialog
from ui.model_3d_dialog import Model3DDialog
from adapters.unified_report_generator import save_unified_report

class DefectAnalyzerWindow:
    """Главное окно ИИ-Инженера"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏗️ ИИ-Инженер")
        
        # Получаем размер экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Устанавливаем размер окна в 80% экрана
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Центрируем окно
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Файловый менеджер
        self.file_manager = WindowsFileManager()
        
        # Создание интерфейса
        self.setup_ui()
        
    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        # Основной контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="🏗️ ИИ-Инженер",
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=20)
        
        # Кнопка анализа фото
        analyze_btn = ttk.Button(
            buttons_frame,
            text="📸 Анализ фотографий",
            command=self.analyze_photos,
            style='Modern.TButton'
        )
        analyze_btn.pack(pady=5)
        
        # Кнопка управления проектами
        projects_btn = ttk.Button(
            buttons_frame,
            text="📁 Управление проектами",
            command=self.manage_projects,
            style='Modern.TButton'
        )
        projects_btn.pack(pady=5)
        
        # Кнопка калькулятора износа
        wear_btn = ttk.Button(
            buttons_frame,
            text="🧮 Калькулятор износа",
            command=self.open_wear_calculator,
            style='Modern.TButton'
        )
        wear_btn.pack(pady=5)
        
        # Кнопка конструктивных решений
        construction_btn = ttk.Button(
            buttons_frame,
            text="🏗️ Конструктивные решения",
            command=self.open_construction_dialog,
            style='Modern.TButton'
        )
        construction_btn.pack(pady=5)
        
        # Кнопка 3D анализа
        model_3d_btn = ttk.Button(
            buttons_frame,
            text="🎯 3D анализ модели",
            command=self.open_model_3d_dialog,
            style='Modern.TButton'
        )
        model_3d_btn.pack(pady=5)
        
    def analyze_photos(self):
        """Анализ фотографий"""
        # Реализация анализа фотографий
        pass
        
    def manage_projects(self):
        """Управление проектами"""
        # Реализация управления проектами
        pass
        
    def open_wear_calculator(self):
        """Открытие калькулятора износа"""
        try:
            from ui.modern_main_window import ModernDefectAnalyzerWindow
            # Закрываем текущее окно
            self.root.destroy()
            # Открываем современное окно
            modern_window = ModernDefectAnalyzerWindow()
            # Переключаемся на вкладку расчета износа
            modern_window.show_wear_data()
            modern_window.run()
        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить современный интерфейс: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка открытия калькулятора износа: {e}")
        
    def open_construction_dialog(self):
        """Открытие диалога конструктивных решений"""
        try:
            from ui.modern_main_window import ModernDefectAnalyzerWindow
            # Закрываем текущее окно
            self.root.destroy()
            # Открываем современное окно
            modern_window = ModernDefectAnalyzerWindow()
            # Переключаемся на вкладку конструктивных решений
            modern_window.show_construction_data()
            modern_window.run()
        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить современный интерфейс: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка открытия конструктивных решений: {e}")
        
    def open_model_3d_dialog(self):
        """Открытие диалога 3D анализа"""
        # Реализация открытия диалога 3D анализа
        pass
        
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    app = DefectAnalyzerWindow()
    app.run()
