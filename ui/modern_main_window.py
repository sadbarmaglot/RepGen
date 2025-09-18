import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
from PIL import Image, ImageTk
import os
import sys
import json
import io
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Импортируем поддержку буфера обмена
from ui.clipboard_support import ClipboardEntry, ClipboardScrolledText

# Добавляем путь к корневой папке проекта
sys.path.append(str(Path(__file__).parent.parent))

from adapters.ai_adapter import analyze_local_photo, batch_analyze_photos
from adapters.file_manager import WindowsFileManager
from ui.project_dialogs import ProjectDialog, ProjectManagerDialog

# Импорт диалогов (с обработкой ошибок)
try:
    from ui.model_3d_dialog import Model3DDialog
    HAS_3D_ANALYSIS = True
except ImportError:
    HAS_3D_ANALYSIS = False

class PlanDialog:
    """Диалог для добавления нового плана"""
    
    def __init__(self, parent, title="Добавить план"):
        self.result = None
        
        # Создаем модальное окно
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрируем окно
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        self.create_widgets()
        
        # Фокус на поле названия
        self.name_entry.focus()
        
        # Обработка закрытия окна
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
    def create_widgets(self):
        """Создание виджетов диалога"""
        # Основной фрейм
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Название плана
        name_label = ttk.Label(main_frame, text="Название плана:")
        name_label.pack(anchor='w', pady=(0, 5))
        
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=50)
        self.name_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Описание плана
        desc_label = ttk.Label(main_frame, text="Описание:")
        desc_label.pack(anchor='w', pady=(0, 5))
        
        self.desc_text = tk.Text(main_frame, height=8, width=50, wrap=tk.WORD)
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Кнопки
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            buttons_frame,
            text="Отмена",
            command=self.cancel
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            buttons_frame,
            text="OK",
            command=self.ok
        ).pack(side=tk.RIGHT)
        
        # Привязываем Enter к кнопке OK
        self.dialog.bind('<Return>', lambda e: self.ok())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def ok(self):
        """Обработка нажатия OK"""
        name = self.name_var.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        
        if not name:
            messagebox.showerror("Ошибка", "Название плана не может быть пустым")
            return
        
        self.result = (name, description)
        self.dialog.destroy()
    
    def cancel(self):
        """Обработка отмены"""
        self.result = None
        self.dialog.destroy()

class ModernDefectAnalyzerWindow:
    """Современное главное окно ИИ-Инженера"""
    
    def __init__(self, user_info=None):
        self.user_info = user_info
        
        # Если user_info не передан, пытаемся получить из auth_client
        if not self.user_info:
            try:
                from adapters.auth_client import auth_client
                if auth_client.is_authenticated():
                    user_info_result = auth_client.get_user_info()
                    if user_info_result.get('success'):
                        self.user_info = user_info_result['user']
            except Exception as e:
                print(f"Не удалось получить информацию о пользователе: {e}")
        
        self.root = tk.Tk()
        self.root.title("🏗️ ИИ-Инженер v1.2")
        
        # Получаем размер экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Устанавливаем размер окна в 90% экрана
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        
        # Центрируем окно
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1000, 700)
        
        # Настройка зумирования окна
        self.setup_window_scaling()
        
        # Файловый менеджер
        self.file_manager = WindowsFileManager()
        
        # Список результатов анализа
        self.analysis_results = []
        
        # Калькулятор износа (будет инициализирован при открытии)
        self.wear_calculator = None
        
        # Текущая активная вкладка
        self.current_tab = "general"
        
        # Настройка стилей
        self.setup_styles()
        
        # Создание интерфейса
        self.setup_ui()
        
        # Загрузка последних результатов
        self.load_recent_analyses()
        
    def setup_window_scaling(self):
        """Настройка масштабирования окна для предотвращения исчезновения элементов"""
        # Привязываем обработчики изменения размера окна
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Устанавливаем минимальные размеры для элементов
        self.min_element_width = 200
        self.min_element_height = 100
        
        # Коэффициент масштабирования
        self.scale_factor = 1.0
        
    def on_window_resize(self, event):
        """Обработчик изменения размера окна"""
        if event.widget == self.root:
            # Получаем текущий размер окна
            current_width = self.root.winfo_width()
            current_height = self.root.winfo_height()
            
            # Рассчитываем коэффициент масштабирования
            base_width = 1200  # Базовый размер окна
            base_height = 800
            
            scale_x = max(0.8, current_width / base_width)
            scale_y = max(0.8, current_height / base_height)
            
            # Используем минимальный коэффициент для сохранения пропорций
            self.scale_factor = min(scale_x, scale_y)
            
            # Применяем масштабирование к элементам интерфейса
            self.apply_scaling()
    
    def apply_scaling(self):
        """Применение масштабирования к элементам интерфейса"""
        try:
            # Масштабируем шрифты
            base_font_size = 11
            scaled_font_size = max(9, int(base_font_size * self.scale_factor))
            
            # Обновляем стили с новыми размерами шрифтов
            style = ttk.Style()
            
            # Обновляем основные стили
            style.configure('Header.TLabel', 
                           font=('Segoe UI', int(16 * self.scale_factor), 'bold'))
            style.configure('Subtitle.TLabel',
                           font=('Segoe UI', int(13 * self.scale_factor)))
            style.configure('Modern.TButton',
                           font=('Segoe UI', int(12 * self.scale_factor), 'bold'),
                           padding=(int(20 * self.scale_factor), int(10 * self.scale_factor)))
            style.configure('Secondary.TButton',
                           font=('Segoe UI', int(11 * self.scale_factor)),
                           padding=(int(16 * self.scale_factor), int(8 * self.scale_factor)))
            
            # Обновляем размеры колонок в таблицах
            if hasattr(self, 'results_tree'):
                self.results_tree.column('#0', width=int(50 * self.scale_factor))
                self.results_tree.column('file', width=int(200 * self.scale_factor))
                self.results_tree.column('status', width=int(100 * self.scale_factor))
                self.results_tree.column('defect', width=int(300 * self.scale_factor))
            
            if hasattr(self, 'construction_tree'):
                self.construction_tree.column("element", width=int(260 * self.scale_factor))
                self.construction_tree.column("description", width=int(480 * self.scale_factor))
            
            if hasattr(self, 'wear_tree'):
                self.wear_tree.column('element', width=int(300 * self.scale_factor))
                self.wear_tree.column('weight', width=int(120 * self.scale_factor))
                self.wear_tree.column('wear', width=int(120 * self.scale_factor))
                self.wear_tree.column('weighted_wear', width=int(140 * self.scale_factor))
            
            if hasattr(self, 'objects_tree'):
                self.objects_tree.column('name', width=int(200 * self.scale_factor))
                self.objects_tree.column('wear', width=int(120 * self.scale_factor))
                self.objects_tree.column('last_date', width=int(180 * self.scale_factor))
                
        except Exception as e:
            print(f"Ошибка применения масштабирования: {e}")
        
    def setup_styles(self):
        """Настройка современных стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Современная цветовая палитра
        primary_color = '#1e88e5'      # Синий
        primary_hover = '#1976d2'      # Темно-синий при наведении
        secondary_color = '#64b5f6'    # Светло-синий
        secondary_hover = '#42a5f5'    # Светло-синий при наведении
        background_color = '#f5f5f5'   # Светло-серый фон
        surface_color = '#ffffff'      # Белый
        text_primary = '#212121'       # Темно-серый текст
        text_secondary = '#757575'     # Серый текст
        border_color = '#e0e0e0'       # Светло-серый для границ
        
        # Настройка цветов
        style.configure('Header.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       foreground=text_primary,
                       background=background_color)
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 13),
                       foreground=text_secondary,
                       background=background_color)
        
        # Основные кнопки
        style.configure('Modern.TButton',
                       font=('Segoe UI', 12, 'bold'),
                       padding=(20, 10),
                       relief='flat',
                       borderwidth=0,
                       background=primary_color,
                       foreground='white')
        
        style.map('Modern.TButton',
                 background=[('active', primary_hover), ('!active', primary_color)],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        # Вторичные кнопки
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 11),
                       padding=(16, 8),
                       relief='flat',
                       borderwidth=0,
                       background=secondary_color,
                       foreground='white')
        
        style.map('Secondary.TButton',
                 background=[('active', secondary_hover), ('!active', secondary_color)],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        # Вкладки
        style.configure('Tab.TButton',
                       font=('Segoe UI', 12, 'bold'),
                       padding=(24, 12),
                       relief='flat',
                       borderwidth=0,
                       background=primary_color,
                       foreground='white')
        
        style.map('Tab.TButton',
                 background=[('active', primary_hover), ('!active', primary_color)],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        style.configure('InactiveTab.TButton',
                       font=('Segoe UI', 12),
                       padding=(24, 12),
                       relief='flat',
                       borderwidth=0,
                       background=text_secondary,
                       foreground='white')
        
        style.map('InactiveTab.TButton',
                 background=[('active', '#616161'), ('!active', text_secondary)],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        # Фреймы
        style.configure('Main.TFrame',
                       background=background_color,
                       relief='flat',
                       borderwidth=0)
        
        style.configure('Content.TFrame',
                       background=surface_color,
                       relief='flat',
                       borderwidth=0)
        
        # LabelFrame стили
        style.configure('TLabelframe',
                       background=background_color,
                       relief='flat',
                       borderwidth=1,
                       bordercolor=border_color)
        
        style.configure('TLabelframe.Label',
                       font=('Segoe UI', 13, 'bold'),
                       foreground=text_primary,
                       background=background_color)
        
        # Entry стили
        style.configure('TEntry',
                       font=('Segoe UI', 11),
                       background=surface_color,
                       fieldbackground=surface_color,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=border_color)
        
        style.map('TEntry',
                 bordercolor=[('focus', primary_color)],
                 fieldbackground=[('focus', surface_color)])
        
        # Treeview стили
        style.configure('Treeview',
                       font=('Segoe UI', 10),
                       background=surface_color,
                       foreground=text_primary,
                       fieldbackground=surface_color,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=border_color)
        
        style.configure('Treeview.Heading',
                       font=('Segoe UI', 11, 'bold'),
                       background=primary_color,
                       foreground='white',
                       relief='flat',
                       borderwidth=0)
        
        style.map('Treeview',
                 background=[('selected', primary_color)],
                 foreground=[('selected', 'white')])
        
        # Scrollbar стили
        style.configure('Vertical.TScrollbar',
                       background=border_color,
                       bordercolor=border_color,
                       arrowcolor=text_secondary,
                       troughcolor=background_color,
                       width=12,
                       relief='flat')
        
        style.map('Vertical.TScrollbar',
                 background=[('active', primary_color)],
                 arrowcolor=[('active', 'white')])
        
        # Статусные цвета
        style.configure('Success.TLabel', foreground='#4caf50')
        style.configure('Error.TLabel', foreground='#f44336')
        style.configure('Warning.TLabel', foreground='#ff9800')
        
    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        # Главный контейнер
        main_container = ttk.Frame(self.root, style='Main.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель с проектом и навигацией
        self.create_top_panel(main_container)
        
        # Панель вкладок
        self.create_tab_panel(main_container)
        
        # Основной контент
        self.create_content_area(main_container)
        
        # Статус бар
        self.create_status_bar(main_container)
        
        # Загружаем данные с сервера после создания всех элементов интерфейса
        self.root.after(1000, self.load_object_info_from_server)  # Задержка 1 секунда
        
    def create_top_panel(self, parent):
        """Создание верхней панели"""
        top_frame = ttk.Frame(parent, style='Main.TFrame')
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Левая часть - информация о проекте
        project_frame = ttk.Frame(top_frame, style='Main.TFrame')
        project_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Заголовок с названием проекта
        self.project_title_label = ttk.Label(
            project_frame,
            text=f"Проект: {self.file_manager.current_project}",
            style='Header.TLabel'
        )
        self.project_title_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Кнопка смены проекта
        change_project_button = ttk.Button(
            project_frame,
            text="🔄 Сменить проект",
            style='Secondary.TButton',
            command=self.change_project
        )
        change_project_button.pack(side=tk.LEFT)
        
        
        # Правая часть - информация о пользователе
        actions_frame = ttk.Frame(top_frame, style='Main.TFrame')
        actions_frame.pack(side=tk.RIGHT)
        
        # Информация о пользователе
        if self.user_info:
            user_name = self.user_info.get('name') or self.user_info.get('email', 'Пользователь')
            user_label = ttk.Label(
                actions_frame,
                text=f"👤 {user_name}",
                style='Subtitle.TLabel'
            )
            user_label.pack(side=tk.RIGHT, padx=(0, 10))
            
            # Кнопка выхода
            logout_button = ttk.Button(
                actions_frame,
                text="🚪 Выйти",
                style='Secondary.TButton',
                command=self.logout
            )
            logout_button.pack(side=tk.RIGHT)
        
    def create_tab_panel(self, parent):
        """Создание панели вкладок"""
        tab_frame = ttk.Frame(parent, style='Main.TFrame')
        tab_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Вкладки
        self.tabs = {}
        
        tab_configs = [
            ("general", "📋 Общие данные", self.show_general_data),
            ("construction", "🏗️ Конструктивное решение", self.show_construction_data),
            ("defects", "⚠️ Ведомость дефектов", self.show_defects_data),
            ("wear", "📊 Расчет износа", self.show_wear_data),
            ("export", "📄 Экспорт в Word", self.show_export_data)
        ]
        
        for tab_id, tab_text, tab_command in tab_configs:
            tab_button = ttk.Button(
                tab_frame,
                text=tab_text,
                style='Tab.TButton' if tab_id == self.current_tab else 'InactiveTab.TButton',
                command=lambda tid=tab_id, cmd=tab_command: self.switch_tab(tid, cmd)
            )
            tab_button.pack(side=tk.LEFT, padx=(0, 5))
            self.tabs[tab_id] = tab_button
            
    def create_content_area(self, parent):
        """Создание области контента"""
        self.content_frame = ttk.Frame(parent, style='Content.TFrame')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Инициализируем первую вкладку
        self.show_general_data()
        
    def create_status_bar(self, parent):
        """Создание статус бара"""
        status_frame = ttk.Frame(parent, style='Main.TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Готов к работе", style='Subtitle.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=5)
        
    def switch_tab(self, tab_id, tab_command):
        """Переключение вкладки"""
        # Обновляем стили кнопок
        for tid, button in self.tabs.items():
            if tid == tab_id:
                button.configure(style='Tab.TButton')
            else:
                button.configure(style='InactiveTab.TButton')
        
        self.current_tab = tab_id
        
        # Очищаем контент
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Показываем новый контент
        tab_command()
        
    def show_general_data(self):
        """Показать вкладку общих данных"""
        
        # Основная информация о проекте
        main_info_frame = ttk.LabelFrame(self.content_frame, text="Основная информация", padding=20)
        main_info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Поле для названия объекта
        name_frame = ttk.Frame(main_info_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        name_label = ttk.Label(name_frame, text="Название объекта:", style='Subtitle.TLabel')
        name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.object_name_var = tk.StringVar(value=self.file_manager.current_project)
        name_entry = ClipboardEntry(name_frame, textvariable=self.object_name_var, width=40, font=('Segoe UI', 11))
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Поле для адреса
        address_frame = ttk.Frame(main_info_frame)
        address_frame.pack(fill=tk.X, pady=(0, 10))
        
        address_label = ttk.Label(address_frame, text="Адрес расположения:", style='Subtitle.TLabel')
        address_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.object_address_var = tk.StringVar(value="Адрес уточняется")
        address_entry = ClipboardEntry(address_frame, textvariable=self.object_address_var, width=40, font=('Segoe UI', 11))
        address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Поле для описания объекта
        description_frame = ttk.Frame(main_info_frame)
        description_frame.pack(fill=tk.X, pady=(0, 10))
        
        description_label = ttk.Label(description_frame, text="Описание объекта:", style='Subtitle.TLabel')
        description_label.pack(side=tk.LEFT, padx=(0, 10), anchor='nw')
        
        # Создаем фрейм для текстового поля с описанием
        desc_text_frame = ttk.Frame(description_frame)
        desc_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.object_description_var = tk.StringVar(value="")
        description_text = tk.Text(desc_text_frame, height=4, width=40, font=('Segoe UI', 11), wrap=tk.WORD)
        description_text.pack(fill=tk.BOTH, expand=True)
        
        # Синхронизируем текстовое поле с переменной
        def on_description_change(event=None):
            self.object_description_var.set(description_text.get("1.0", tk.END).strip())
        
        description_text.bind('<KeyRelease>', on_description_change)
        description_text.bind('<FocusOut>', on_description_change)
        
        # Загружаем сохраненную информацию
        self.load_project_info()
        
        # Кнопка сохранения
        save_button = ttk.Button(
            main_info_frame,
            text="💾 Сохранить информацию",
            style='Modern.TButton',
            command=self.save_project_info
        )
        save_button.pack(pady=(10, 0))
        
        # Блок планов
        self.create_plans_section(self.content_frame)
        
        
    def show_construction_data(self):
        """Показать вкладку конструктивных решений"""
        # Очищаем контент
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Инициализируем данные конструктивных решений, если еще не инициализированы
        if not hasattr(self, 'construction_data'):
            try:
                # Импорт дерева конструкций
                try:
                    from adapters.construction_data import (
                        CONSTRUCTION_TREE, 
                        PREDEFINED_SOLUTIONS,
                        load_construction_data_from_json,
                        merge_construction_data
                    )
                    self.CONSTRUCTION_TREE = CONSTRUCTION_TREE
                    self.PREDEFINED_SOLUTIONS = PREDEFINED_SOLUTIONS
                except Exception:
                    # Запасной вариант на случай отсутствия файла данных
                    self.CONSTRUCTION_TREE = {
                        "Фундаменты": {
                            "Ленточные": {
                                "Бутовые": "Фундаменты выполнены ленточными из бутовой кладки",
                                "Железобетонные": {
                                    "Монолитные": "Фундаменты выполнены ленточными монолитными",
                                    "Сборные": "Фундаменты выполнены ленточными из фундаментных блоков",
                                },
                            },
                            "Свайные": {
                                "Деревянные": "Фундаменты выполнены свайными деревянными из бруса",
                                "Железобетонные": {
                                    "__custom__": {
                                        "labels": ["Укажите сечение, мм"],
                                        "callback": lambda section: (
                                            f"Фундаменты выполнены свайными железобетонными, сечением {section} мм"
                                        ),
                                    }
                                },
                            },
                        },
                        "Стены": {
                            "Кирпичные": {
                                "__custom__": {
                                    "labels": ["Укажите толщину, мм"],
                                    "callback": lambda section: (
                                        f"Стены выполнены из кирпичной кладки на цементно-песчаном растворе, толщиной {section} мм"
                                    ),
                                }
                            },
                            "Железобетонные": {
                                "__custom__": {
                                    "labels": ["Укажите серию", "Укажите марку"],
                                    "callback": lambda series, mark: (
                                        f"Стены выполнены из навесных сборных железобетонных панелей марки {mark} по серии {series}"
                                    ),
                                }
                            },
                        },
                        "Перекрытия": {
                            "Железобетонные": {
                                "Плиты ПК": "Перекрытия выполнены из сборных железобетонных плит ПК",
                                "Монолитные": "Перекрытия выполнены монолитными железобетонными",
                            }
                        },
                    }
                    self.PREDEFINED_SOLUTIONS = {}
                
                self.construction_data = []
                self._all_elements = list(self.CONSTRUCTION_TREE.keys())
                self._desc_label_to_text = {}
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить модуль конструктивных решений: {e}")
                return
        
        # Заголовок
        header_label = ttk.Label(
            self.content_frame,
            text="Конструктивные решения",
            style='Header.TLabel'
        )
        header_label.pack(pady=(20, 10))
        

        
        # Основной контейнер
        main_frame = ttk.Frame(self.content_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Таблица
        table_frame = ttk.LabelFrame(main_frame, text="Состав решений")
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.construction_tree = ttk.Treeview(
            table_frame,
            columns=("element", "description"),
            show="headings",
            height=10,
        )
        self.construction_tree.heading("element", text="Конструкция")
        self.construction_tree.heading("description", text="Описание")
        self.construction_tree.column("element", width=260)
        self.construction_tree.column("description", width=480)

        yscroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.construction_tree.yview)
        self.construction_tree.configure(yscrollcommand=yscroll.set)
        self.construction_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.construction_tree.bind("<<TreeviewSelect>>", self._on_construction_row_select)

        # Панель кнопок для таблицы
        tb = ttk.Frame(main_frame)
        tb.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(tb, text="➕ Добавить", style='Secondary.TButton', command=self._add_construction_row).pack(side=tk.LEFT)
        ttk.Button(tb, text="🗑 Удалить", style='Secondary.TButton', command=self._delete_construction_row).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(tb, text="Очистить", style='Secondary.TButton', command=self._clear_construction_all).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(tb, text="📋 Быстрые решения", style='Secondary.TButton', command=self._show_quick_solutions).pack(side=tk.RIGHT)

        # Редактор
        editor = ttk.LabelFrame(main_frame, text="Редактор строки")
        editor.pack(fill=tk.X, pady=(10, 0))

        # Левая колонка: конструкция
        left = ttk.Frame(editor)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 8), pady=8)
        ttk.Label(left, text="Конструкция").pack(anchor=tk.W)
        self.element_combo = ttk.Combobox(left, state="normal")
        self.element_combo.pack(fill=tk.X, pady=(4, 0))

        # Правая колонка: описание
        right = ttk.Frame(editor)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 8), pady=8)
        ttk.Label(right, text="Описание").pack(anchor=tk.W)
        self.desc_combo = ttk.Combobox(right, state="normal")
        self.desc_combo.pack(fill=tk.X, pady=(4, 0))

        # Кнопки действия
        actions = ttk.Frame(self.content_frame)
        actions.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(actions, text="Отмена", style='Secondary.TButton', command=self._cancel_construction_edits).pack(side=tk.RIGHT)
        ttk.Button(actions, text="Сохранить", style='Modern.TButton', command=self._save_construction_data).pack(side=tk.RIGHT, padx=(0, 10))

        # Данные выпадающих списков
        self.element_combo.configure(values=self._all_elements)
        self.element_combo.bind('<<ComboboxSelected>>', self._on_construction_element_change)
        self.element_combo.bind('<KeyRelease>', self._on_construction_element_change)

        # Удобный ввод: двойной клик/фокус выделяет текст
        self._enable_select_all(self.element_combo)
        self._enable_select_all(self.desc_combo)

        # Сетка редактора
        editor.grid_columnconfigure(0, weight=1)
        editor.grid_columnconfigure(1, weight=1)
        
        # Загружаем сохраненные данные
        self._load_saved_construction_data_silent()
        
    def show_defects_data(self):
        """Показать вкладку ведомости дефектов"""
        # Заголовок
        header_label = ttk.Label(
            self.content_frame,
            text="Ведомость дефектов",
            style='Header.TLabel'
        )
        header_label.pack(pady=(20, 10))
        
        # Основной контент с разделителем
        main_paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Левая панель - список результатов
        self.create_results_panel(main_paned)
        
        # Правая панель - детали анализа
        self.create_details_panel(main_paned)
        
    def show_wear_data(self):
        """Показать вкладку расчета износа"""
        # Очищаем контент
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Инициализируем калькулятор износа, если еще не инициализирован
        if not hasattr(self, 'wear_calculator') or self.wear_calculator is None:
            try:
                from adapters.wear_calculator import WearCalculator, BuildingTypeTemplates
                self.wear_calculator = WearCalculator()
                self._saved_wear_by_template = {}
                self._current_template_key = "default"
            except ImportError as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить модуль расчета износа: {e}")
                return
        
        # Заголовок
        header_label = ttk.Label(
            self.content_frame,
            text="Расчет физического износа здания",
            style='Header.TLabel'
        )
        header_label.pack(pady=(20, 10))
        
        # Подзаголовок
        subtitle_label = ttk.Label(
            self.content_frame,
            text="в соответствии с ВСН 53-86(р)",
            style='Subtitle.TLabel'
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Панель инструментов
        toolbar = ttk.Frame(self.content_frame)
        toolbar.pack(fill=tk.X, padx=20, pady=10)
        
        # Шаблоны зданий
        templates_frame = ttk.LabelFrame(toolbar, text="Тип здания", padding=5)
        templates_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            templates_frame,
            text="🏠 Жилое",
            style='Secondary.TButton',
            command=lambda: self.load_wear_template("residential")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            templates_frame,
            text="🏢 Офисное", 
            style='Secondary.TButton',
            command=lambda: self.load_wear_template("office")
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            templates_frame,
            text="🏭 Промышленное",
            style='Secondary.TButton',
            command=lambda: self.load_wear_template("industrial") 
        ).pack(side=tk.LEFT, padx=2)
        
        # Управление данными
        data_frame = ttk.LabelFrame(toolbar, text="Данные", padding=5)
        data_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            data_frame,
            text="📄 Экспорт в Word",
            style='Secondary.TButton',
            command=self.export_wear_to_word
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            data_frame,
            text="🔄 Сбросить",
            style='Secondary.TButton',
            command=self.reset_wear_data
        ).pack(side=tk.LEFT, padx=2)
        
        # Основная таблица
        table_frame = ttk.LabelFrame(self.content_frame, text="Конструктивные элементы здания", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Создаем таблицу
        columns = ('element', 'weight', 'wear', 'weighted_wear')
        self.wear_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=12,
            selectmode='browse'
        )
        
        # Настраиваем заголовки
        self.wear_tree.heading('element', text='Элементы здания', anchor='center')
        self.wear_tree.heading('weight', text='Удельный вес\nв стоимости, %', anchor='center')
        self.wear_tree.heading('wear', text='Физический\nизнос, %', anchor='center')
        self.wear_tree.heading('weighted_wear', text='Средневзвешенная\nстепень износа', anchor='center')
        
        # Настраиваем ширину колонок
        self.wear_tree.column('element', width=300)
        self.wear_tree.column('weight', width=120)
        self.wear_tree.column('wear', width=120)
        self.wear_tree.column('weighted_wear', width=140)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.wear_tree.yview)
        self.wear_tree.configure(yscrollcommand=scrollbar.set)
        
        self.wear_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Обработчики для редактирования
        self.wear_tree.bind('<Double-1>', self.edit_wear_value)
        self.wear_tree.bind('<Button-1>', self.on_wear_tree_click)
        
        # Панель результатов
        results_frame = ttk.LabelFrame(self.content_frame, text="Результаты расчета", padding=10)
        results_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Общий износ
        total_frame = ttk.Frame(results_frame)
        total_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(total_frame, text="Общий физический износ здания:", 
                 font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
        self.total_wear_label = ttk.Label(total_frame, text="0.0%", 
                                        font=("Segoe UI", 12, "bold"), foreground="green")
        self.total_wear_label.pack(side=tk.RIGHT)
        
        # Техническое состояние
        condition_frame = ttk.Frame(results_frame)
        condition_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(condition_frame, text="Техническое состояние:", 
                 font=("Segoe UI", 11)).pack(side=tk.LEFT)
        self.condition_label = ttk.Label(condition_frame, text="Исправное", 
                                       font=("Segoe UI", 11), foreground="green")
        self.condition_label.pack(side=tk.RIGHT)
        
        # Рекомендации
        self.recommendation_text = tk.Text(results_frame, height=3, wrap=tk.WORD, 
                                         font=("Segoe UI", 10))
        self.recommendation_text.pack(fill=tk.X, pady=(5, 0))
        
        # Загружаем данные и обновляем интерфейс
        if hasattr(self, 'wear_calculator') and self.wear_calculator is not None:
            self.load_wear_data()
            self.update_wear_totals()
        
    def show_export_data(self):
        """Показать вкладку экспорта"""
        # Заголовок
        header_label = ttk.Label(
            self.content_frame,
            text="Экспорт в Word",
            style='Header.TLabel'
        )
        header_label.pack(pady=(20, 10))
        
        # Основной контент
        content_frame = ttk.Frame(self.content_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Информация об экспорте
        info_label = ttk.Label(
            content_frame,
            text="Создание объединенного отчета в формате Word",
            style='Subtitle.TLabel'
        )
        info_label.pack(pady=(0, 20))
        
        # Кнопка экспорта
        export_button = ttk.Button(
            content_frame,
            text="📄 Создать отчет",
            style='Modern.TButton',
            command=self.export_to_docx
        )
        export_button.pack()
        
    def create_results_panel(self, parent):
        """Создание панели со списком результатов"""
        results_frame = ttk.LabelFrame(parent, text="Результаты анализа", padding=10)
        parent.add(results_frame, weight=1)
        
        # Панель с кнопками для работы с фото
        buttons_frame = ttk.Frame(results_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопка добавления фото
        add_photo_button = ttk.Button(
            buttons_frame,
            text="📸 Добавить фото",
            style='Secondary.TButton',
            command=self.add_photo
        )
        add_photo_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка пакетного анализа
        batch_analyze_button = ttk.Button(
            buttons_frame,
            text="🔍 Пакетный анализ",
            style='Secondary.TButton',
            command=self.batch_analyze_photos
        )
        batch_analyze_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка очистки результатов
        clear_results_button = ttk.Button(
            buttons_frame,
            text="🗑️ Очистить результаты",
            style='Secondary.TButton',
            command=self.clear_results
        )
        clear_results_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка обновления списка
        refresh_button = ttk.Button(
            buttons_frame,
            text="🔄 Обновить",
            style='Secondary.TButton',
            command=self.refresh_results
        )
        refresh_button.pack(side=tk.LEFT)
        
        # Таблица результатов
        self.results_tree = ttk.Treeview(
            results_frame, 
            columns=('file', 'status', 'defect'), 
            show='tree headings',
            height=15
        )
        
        # Настройка колонок
        self.results_tree.heading('#0', text='№')
        self.results_tree.heading('file', text='Файл')
        self.results_tree.heading('status', text='Статус')
        self.results_tree.heading('defect', text='Дефект')
        
        self.results_tree.column('#0', width=50)
        self.results_tree.column('file', width=200)
        self.results_tree.column('status', width=100)
        self.results_tree.column('defect', width=300)
        
        # Скроллбар для таблицы
        results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scroll.set)
        
        # Размещение
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Обработчик выбора элемента
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_select)
        self.results_tree.bind('<ButtonRelease-1>', self.on_result_select)  # Добавляем обработчик клика
        
        # Обработчик двойного клика для быстрого анализа
        self.results_tree.bind('<Double-1>', self.on_double_click_analyze)
        
        # Загружаем данные в таблицу
        self.populate_results_table()
        
    def populate_results_table(self):
        """Заполнение таблицы результатами анализа"""
        # Очищаем таблицу
        if hasattr(self, 'results_tree'):
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
        
        # Добавляем все результаты в таблицу
        for i, result in enumerate(self.analysis_results):
            self.add_result_to_tree(result, i)
        
    def create_details_panel(self, parent):
        """Создание панели с деталями анализа"""
        details_frame = ttk.LabelFrame(parent, text="Детали анализа", padding=10)
        parent.add(details_frame, weight=2)
        
        # Вертикальный разделитель для фото и текста
        details_paned = ttk.PanedWindow(details_frame, orient=tk.VERTICAL)
        details_paned.pack(fill=tk.BOTH, expand=True)
        
        # Панель для фото
        photo_frame = ttk.Frame(details_paned)
        details_paned.add(photo_frame, weight=1)
        
        self.photo_label = ttk.Label(photo_frame, text="Выберите результат для просмотра", anchor=tk.CENTER)
        self.photo_label.pack(fill=tk.BOTH, expand=True)
        
        # Панель для текстовых деталей
        text_frame = ttk.Frame(details_paned)
        details_paned.add(text_frame, weight=1)
        
        # Текстовое поле с результатами
        self.details_text = ClipboardScrolledText(
            text_frame, 
            wrap=tk.WORD, 
            height=10,
            font=('Segoe UI', 11)
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
    def change_project(self):
        """Смена проекта"""
        from ui.welcome_window import ProjectSelectionWindow
        
        # Закрываем текущее окно
        self.root.destroy()
        
        # Открываем окно выбора проекта с передачей информации о пользователе
        project_window = ProjectSelectionWindow(self.user_info)
        project_window.run()
        
    def update_projects_list(self):
        """Обновление списка объектов"""
        projects = self.file_manager.get_all_projects()
        
        # Устанавливаем текущий объект
        if self.file_manager.current_project in projects:
            self.project_title_label.configure(text=f"Проект: {self.file_manager.current_project}")
        else:
            self.project_title_label.configure(text=f"Проект: {projects[0] if projects else 'Общий объект'}")
    
            
    def on_project_change(self, event=None):
        """Обработчик смены объекта"""
        new_project = self.file_manager.current_project
        
        # Сохраняем текущие результаты
        self.save_current_results()
        
        # Очищаем текущие результаты и загружаем новые
        self.analysis_results.clear()
        if hasattr(self, 'results_tree'):
            self.results_tree.delete(*self.results_tree.get_children())
        self.load_recent_analyses()
        
        # Очищаем панель деталей
        if hasattr(self, 'details_text'):
            self.details_text.delete(1.0, tk.END)
        if hasattr(self, 'photo_label'):
            self.photo_label.configure(image="", text="Выберите результат для просмотра")
            
        self.update_status(f"Переключено на объект: {new_project}")
        self.update_projects_list()
        
    def save_current_results(self):
        """Сохранение текущих результатов перед сменой объекта"""
        # Результаты уже сохраняются автоматически при анализе
        pass
        
    def select_photos(self):
        """Выбор фотографий для анализа"""
        file_paths = filedialog.askopenfilenames(
            title="Выберите фотографии дефектов",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("JPEG файлы", "*.jpg *.jpeg"),
                ("PNG файлы", "*.png"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_paths:
            self.add_photos_to_analysis(file_paths)
            
    def add_photos_to_analysis(self, file_paths):
        """Добавление фотографий в список для анализа"""
        for file_path in file_paths:
            # Копируем файл в рабочую папку
            copied_path = self.file_manager.copy_photo_to_workspace(file_path)
            
            # Добавляем в список результатов как "ожидает анализа"
            result_item = {
                'file_path': copied_path,
                'filename': Path(file_path).name,
                'status': 'pending',
                'defect': 'Ожидает анализа...',
                'eliminating_method': '',
                'analyzed': False
            }
            
            self.analysis_results.append(result_item)
            
        # Обновляем всю таблицу
        if hasattr(self, 'results_tree'):
            self.populate_results_table()
            
        # Подсчитываем количество ожидающих анализа
        pending_count = len([r for r in self.analysis_results if not r.get('analyzed', False)])
        total_count = len(self.analysis_results)
        
        self.update_status(f"Добавлено {len(file_paths)} фото. Всего: {total_count}, ожидает анализа: {pending_count}")
        
        # Автоматически запускаем анализ первого файла
        self.analyze_next_pending()
        
    def add_result_to_tree(self, result, index):
        """Добавление результата в таблицу"""
        if not hasattr(self, 'results_tree'):
            return
            
        status_text = "✅ Готово" if result.get('analyzed') else "⏳ Ожидает"
        if result.get('error'):
            status_text = "❌ Ошибка"
            
        self.results_tree.insert(
            '', 
            tk.END, 
            iid=str(index + 1),
            text=str(index + 1),
            values=(result.get('filename', 'N/A'), status_text, result.get('defect', 'N/A')[:50] + '...' if len(result.get('defect', '')) > 50 else result.get('defect', 'N/A'))
        )
        
    def analyze_next_pending(self):
        """Анализ следующего ожидающего файла"""
        for i, result in enumerate(self.analysis_results):
            if not result.get('analyzed', False) and result.get('status') == 'pending':
                self.analyze_single_photo(i)
                break
                
    def analyze_single_photo(self, index):
        """Анализ одной фотографии"""
        if index >= len(self.analysis_results):
            return
            
        result = self.analysis_results[index]
        
        # Запускаем анализ в отдельном потоке
        thread = threading.Thread(target=self._analyze_photo_thread, args=(index, result))
        thread.daemon = True
        thread.start()
        
    def _analyze_photo_thread(self, index, result):
        """Анализ фото в отдельном потоке"""
        try:
            # Обновляем статус с подробной информацией
            self.root.after(0, self.update_status, f"🔍 Анализирую {result['filename']}...")
            self.root.after(0, self.progress.start)
            
            # Имитируем этапы анализа для лучшего UX
            stages = [
                "Загружаю изображение...",
                "Отправляю в ИИ для анализа...",
                "Обрабатываю результат...",
                "Сохраняю данные..."
            ]
            
            for i, stage in enumerate(stages):
                self.root.after(0, self.update_status, f"🔍 {stage}")
                import time
                time.sleep(0.5)  # Небольшая задержка для показа этапов
            
            # Анализируем фото с помощью AI
            ai_result = analyze_local_photo(result['file_path'])
            
            # Обновляем результат
            result.update(ai_result)
            result['analyzed'] = True
            result['status'] = 'completed'
            
            # Сохраняем результат
            self.file_manager.save_analysis_result(result)
            
            # Обновляем UI в основном потоке
            self.root.after(0, self._update_ui_after_analysis, index, result)
            
        except Exception as e:
            result['error'] = True
            result['defect'] = f"Ошибка анализа: {str(e)}"
            result['status'] = 'error'
            
            self.root.after(0, self._update_ui_after_analysis, index, result)
            
    def _update_ui_after_analysis(self, index, result):
        """Обновление UI после завершения анализа"""
        self.progress.stop()
        
        # Обновляем всю таблицу для отображения изменений
        if hasattr(self, 'results_tree'):
            self.populate_results_table()
            
        # Подсчитываем прогресс
        completed_count = len([r for r in self.analysis_results if r.get('analyzed', False)])
        total_count = len(self.analysis_results)
        
        self.update_status(f"✅ Анализ завершен: {result['filename']} ({completed_count}/{total_count})")
        
        # Продолжаем анализ следующего файла
        self.analyze_next_pending()
        
    def on_result_select(self, event):
        """Обработчик выбора результата в таблице"""
        if not hasattr(self, 'results_tree'):
            return
            
        selection = self.results_tree.selection()
        
        if not selection:
            return
            
        item_id = selection[0]
        
        try:
            index = int(item_id) - 1
            
            if 0 <= index < len(self.analysis_results):
                result = self.analysis_results[index]
                self.show_result_details(result)
            else:
                # Попробуем найти по item_id напрямую
                for i, result in enumerate(self.analysis_results):
                    if str(i + 1) == item_id:
                        self.show_result_details(result)
                        return
        except (ValueError, IndexError):
            pass
            
    def show_result_details(self, result):
        """Отображение деталей результата"""
        # Показываем фото (используем file_path или image_path)
        photo_path = result.get('file_path') or result.get('image_path', '')
        self.show_photo(photo_path)
        
        # Показываем текстовые детали
        details = f"""Файл: {result['filename']}
Путь: {photo_path}
Статус: {result.get('status', 'Неизвестно')}

ОПИСАНИЕ ДЕФЕКТА:
{result.get('defect', 'Не определено')}

СПОСОБ УСТРАНЕНИЯ:
{result.get('eliminating_method', 'Не указан')}
"""
        
        if hasattr(self, 'details_text'):
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, details)
            
    def show_analysis_details(self, result):
        """Отображение деталей анализа (для повторного анализа)"""
        # Показываем фото (используем file_path или image_path)
        photo_path = result.get('file_path') or result.get('image_path', '')
        self.show_photo(photo_path)
        
        # Показываем текстовые детали
        details = f"""Файл: {result['filename']}
Путь: {photo_path}
Статус: {result.get('status', 'Неизвестно')}

ОПИСАНИЕ ДЕФЕКТА:
{result.get('defect', 'Не определено')}

СПОСОБ УСТРАНЕНИЯ:
{result.get('eliminating_method', 'Не указан')}
"""
        
        if hasattr(self, 'details_text'):
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(1.0, details)
        
    def show_photo(self, photo_path):
        """Отображение фотографии"""
        if not hasattr(self, 'photo_label'):
            return
            
        try:
            # Проверяем существование файла
            if not Path(photo_path).exists():
                self.photo_label.configure(text=f"Файл не найден: {Path(photo_path).name}")
                return
                
            # Проверяем, является ли файл HEIC/HEIF
            file_extension = Path(photo_path).suffix.lower()
            
            try:
                if file_extension in ['.heic', '.heif']:
                    # Регистрируем поддержку HEIC для PIL
                    try:
                        from pillow_heif import register_heif_opener
                        register_heif_opener()
                        print(f"✅ Поддержка HEIC активирована для файла: {Path(photo_path).name}")
                    except ImportError:
                        # Если pillow-heif не установлен, показываем сообщение
                        self.photo_label.configure(text=f"HEIC файл: {Path(photo_path).name}\nДля просмотра установите: pip install pillow-heif")
                        return
                
                # Загружаем изображение
                image = Image.open(photo_path)
                
                # Конвертируем в RGB если необходимо (для совместимости с Tkinter)
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Создаем белый фон для прозрачных изображений
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Получаем размер виджета
                self.photo_label.update()
                max_width = self.photo_label.winfo_width() - 10
                max_height = self.photo_label.winfo_height() - 10
                
                if max_width > 100 and max_height > 100:  # Проверяем что виджет инициализирован
                    # Масштабируем с сохранением пропорций
                    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    # Конвертируем для Tkinter
                    photo = ImageTk.PhotoImage(image)
                    
                    # Отображаем
                    self.photo_label.configure(image=photo, text="")
                    self.photo_label.image = photo  # Сохраняем ссылку
                    print(f"✅ Изображение успешно отображено: {Path(photo_path).name}")
                else:
                    self.photo_label.configure(text=f"Изображение: {Path(photo_path).name}")
                    
            except Exception as e:
                error_msg = f"Ошибка загрузки изображения: {str(e)}"
                print(f"❌ {error_msg}")
                self.photo_label.configure(text=error_msg)
                
        except Exception as e:
            error_msg = f"Общая ошибка: {str(e)}"
            print(f"❌ {error_msg}")
            self.photo_label.configure(text=error_msg)
            
    def export_to_docx(self):
        """Экспорт объединенного отчета в Word документ"""
        try:
            # Импортируем объединенный генератор отчетов
            from adapters.unified_report_generator import save_unified_report
            
            # Собираем данные для отчета
            defects_data = [r for r in self.analysis_results if r.get('analyzed')]
            
            # Получаем данные физического износа
            wear_data = None
            try:
                if hasattr(self, 'wear_calculator') and self.wear_calculator:
                    wear_data = self.wear_calculator.generate_report_data()
            except:
                pass
            
            # Получаем данные конструктивных решений
            constructive_data = None
            try:
                if self.file_manager:
                    saved_solutions = self.file_manager.load_constructive_solutions_bundle()
                    if saved_solutions:
                        constructive_data = saved_solutions
            except:
                pass
            
            # Проверяем, есть ли данные для экспорта
            if not defects_data and not wear_data and not constructive_data:
                messagebox.showwarning("Предупреждение", "Нет данных для экспорта. Добавьте результаты анализа дефектов, расчета износа или конструктивных решений.")
                return
            
            # Выбираем файл для сохранения
            file_path = filedialog.asksaveasfilename(
                title="Сохранить объединенный отчет",
                defaultextension=".docx",
                filetypes=[("Word документы", "*.docx"), ("Все файлы", "*.*")]
            )
            
            if file_path:
                # Показываем прогресс
                self.update_status("Создание объединенного отчета...")
                self.progress.start()
                
                # Получаем информацию об объекте
                project_name = self.file_manager.current_project if self.file_manager else "Общий объект"
                object_name = f"Объект '{project_name}'"
                address = "Адрес уточняется"
                
                # Создаем объединенный отчет
                success = save_unified_report(
                    defects_data=defects_data,
                    wear_data=wear_data,
                    constructive_data=constructive_data,
                    output_path=file_path,
                    object_name=object_name,
                    address=address,
                    project_name=project_name
                )
                
                self.progress.stop()
                
                if success:
                    # Формируем сообщение о содержимом отчета
                    report_parts = []
                    if constructive_data:
                        report_parts.append(f"конструктивных решений ({len(constructive_data)} шт.)")
                    if wear_data:
                        report_parts.append("физического износа")
                    if defects_data:
                        report_parts.append(f"дефектов ({len(defects_data)} шт.)")
                    
                    content_info = ", ".join(report_parts)
                    
                    # Экспорт завершен успешно - не показываем диалог
                    pass
                    self.update_status(f"Объединенный отчет сохранен: {Path(file_path).name}")
                    
                    # Предлагаем открыть файл
                    # Автоматически открываем созданный отчет
                    if True:
                        try:
                            import subprocess
                            subprocess.run(['open', file_path], check=True)  # macOS
                        except:
                            try:
                                os.startfile(file_path)  # Windows
                            except:
                                # Файл сохранен успешно - не показываем диалог
                                pass
                else:
                    messagebox.showerror("Ошибка", "Не удалось создать объединенный отчет")
                    self.update_status("Ошибка создания объединенного отчета")
                    
        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")
            self.update_status(f"Ошибка экспорта: {str(e)}")
            print(f"Подробная ошибка: {e}")
            import traceback
            traceback.print_exc()


                

            
    def load_recent_analyses(self):
        """Загрузка последних анализов для текущего объекта"""
        try:
            recent = self.file_manager.get_recent_analyses(20)
            
            for data in recent:
                analysis = data.get('analysis', {})
                if analysis:
                    self.analysis_results.append(analysis)
            
        except Exception as e:
            print(f"Ошибка загрузки истории: {e}")
            
    def save_project_info(self):
        """Сохранение информации о проекте"""
        try:
            object_name = self.object_name_var.get().strip()
            object_address = self.object_address_var.get().strip()
            object_description = self.object_description_var.get().strip() if hasattr(self, 'object_description_var') else ""
            
            if not object_name:
                messagebox.showwarning("Предупреждение", "Название объекта не может быть пустым")
                return
            
            # Сохраняем информацию в файл проекта
            project_info = {
                'object_name': object_name,
                'object_address': object_address,
                'object_description': object_description,
                'last_updated': datetime.now().isoformat()
            }
            
            # Сохраняем в файл проекта
            project_file = self.file_manager.get_project_file('project_info.json')
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_info, f, ensure_ascii=False, indent=2)
            
            # Синхронизируем с сервером
            self.sync_object_info_to_server(object_name, object_address, object_description)
            
            self.update_status("Информация о проекте обновлена")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить информацию: {str(e)}")
            self.update_status(f"Ошибка сохранения: {str(e)}")
            
    def load_project_info(self):
        """Загрузка информации о проекте"""
        try:
            project_file = self.file_manager.get_project_file('project_info.json')
            if os.path.exists(project_file):
                with open(project_file, 'r', encoding='utf-8') as f:
                    project_info = json.load(f)
                
                if hasattr(self, 'object_name_var'):
                    self.object_name_var.set(project_info.get('object_name', self.file_manager.current_project))
                if hasattr(self, 'object_address_var'):
                    self.object_address_var.set(project_info.get('object_address', 'Адрес уточняется'))
                if hasattr(self, 'object_description_var'):
                    self.object_description_var.set(project_info.get('object_description', ''))
                    
                    # Обновляем текстовое поле описания, если оно существует
                    for widget in self.content_frame.winfo_children():
                        if isinstance(widget, ttk.LabelFrame) and widget.cget('text') == 'Основная информация':
                            for child in widget.winfo_children():
                                if isinstance(child, ttk.Frame):
                                    for grandchild in child.winfo_children():
                                        if isinstance(grandchild, ttk.Frame):
                                            for text_widget in grandchild.winfo_children():
                                                if isinstance(text_widget, tk.Text):
                                                    text_widget.delete("1.0", tk.END)
                                                    text_widget.insert("1.0", project_info.get('object_description', ''))
                                                    break
        except Exception as e:
            print(f"Ошибка загрузки информации о проекте: {e}")
    
    def sync_object_info_to_server(self, name, address, description):
        """Синхронизация информации об объекте с сервером"""
        try:
            from adapters.project_api_client import get_project_api_client
            from adapters.auth_client import auth_client
            
            if not auth_client.is_authenticated():
                self.update_status("Синхронизация недоступна - не авторизован")
                return
            
            project_client = get_project_api_client(auth_client)
            
            # Получаем текущий проект
            current_project = self.file_manager.current_project
            
            # Находим ID объекта на сервере по имени
            # Сначала получаем все проекты
            projects_result = project_client.get_projects()
            if not projects_result.get('success'):
                self.update_status("Ошибка получения проектов для синхронизации")
                return
            
            projects = projects_result.get('projects', [])
            project_id = None
            
            # Находим ID проекта
            for project in projects:
                if project.get('name') == current_project:
                    project_id = project.get('id')
                    break
            
            if not project_id:
                self.update_status("Проект не найден на сервере")
                return
            
            # Получаем объекты проекта
            objects_result = project_client.get_objects_by_project(project_id)
            if not objects_result.get('success'):
                self.update_status("Ошибка получения объектов для синхронизации")
                return
            
            objects = objects_result.get('objects', [])
            object_id = None
            
            # Находим ID объекта по имени (или создаем новый, если не найден)
            for obj in objects:
                if obj.get('name') == name:
                    object_id = obj.get('id')
                    break
            
            if object_id:
                # Обновляем существующий объект
                update_result = project_client.update_object(
                    object_id=object_id,
                    name=name,
                    address=address,
                    description=description
                )
                
                if update_result.get('success'):
                    self.update_status("Информация об объекте синхронизирована с сервером")
                else:
                    error_msg = update_result.get('error', 'Неизвестная ошибка')
                    self.update_status(f"Ошибка синхронизации: {error_msg}")
            else:
                # Создаем новый объект
                create_result = project_client.create_object(
                    project_id=project_id,
                    name=name,
                    address=address,
                    description=description
                )
                
                if create_result.get('success'):
                    self.update_status("Объект создан и синхронизирован с сервером")
                else:
                    error_msg = create_result.get('error', 'Неизвестная ошибка')
                    self.update_status(f"Ошибка создания объекта: {error_msg}")
                    
        except Exception as e:
            self.update_status(f"Ошибка синхронизации: {str(e)}")
    
    def save_project_info_locally(self):
        """Сохранение информации о проекте только локально (без синхронизации с сервером)"""
        try:
            object_name = self.object_name_var.get().strip()
            object_address = self.object_address_var.get().strip()
            object_description = self.object_description_var.get().strip() if hasattr(self, 'object_description_var') else ""
            
            if not object_name:
                return  # Не сохраняем, если название пустое
            
            # Сохраняем информацию в файл проекта
            project_info = {
                'object_name': object_name,
                'object_address': object_address,
                'object_description': object_description,
                'last_updated': datetime.now().isoformat()
            }
            
            # Сохраняем в файл проекта
            project_file = self.file_manager.get_project_file('project_info.json')
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_info, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Ошибка локального сохранения информации о проекте: {e}")
    
    def load_object_info_from_server(self):
        """Загрузка информации об объекте с сервера"""
        try:
            from adapters.project_api_client import get_project_api_client
            from adapters.auth_client import auth_client
            
            if not auth_client.is_authenticated():
                return  # Не показываем ошибку, просто пропускаем загрузку с сервера
            
            project_client = get_project_api_client(auth_client)
            
            # Получаем текущий проект
            current_project = self.file_manager.current_project
            
            # Находим ID проекта на сервере
            projects_result = project_client.get_projects()
            if not projects_result.get('success'):
                return
            
            projects = projects_result.get('projects', [])
            project_id = None
            
            for project in projects:
                if project.get('name') == current_project:
                    project_id = project.get('id')
                    break
            
            if not project_id:
                return
            
            # Получаем объекты проекта
            objects_result = project_client.get_objects_by_project(project_id)
            if not objects_result.get('success'):
                return
            
            objects = objects_result.get('objects', [])
            
            # Если есть объекты, берем первый (или можно выбрать по названию)
            if objects:
                obj = objects[0]  # Берем первый объект
                
                # Обновляем локальные поля, если они отличаются от серверных
                server_name = obj.get('name', '')
                server_address = obj.get('address', '')
                server_description = obj.get('description', '')
                
                current_name = self.object_name_var.get() if hasattr(self, 'object_name_var') else ''
                current_address = self.object_address_var.get() if hasattr(self, 'object_address_var') else ''
                current_description = self.object_description_var.get() if hasattr(self, 'object_description_var') else ''
                
                # Обновляем только если данные с сервера отличаются и не пустые
                if server_name and server_name != current_name:
                    self.object_name_var.set(server_name)
                    
                if server_address and server_address != current_address:
                    self.object_address_var.set(server_address)
                    
                if server_description and server_description != current_description:
                    self.object_description_var.set(server_description)
                    
                    # Обновляем текстовое поле описания
                    for widget in self.content_frame.winfo_children():
                        if isinstance(widget, ttk.LabelFrame) and widget.cget('text') == 'Основная информация':
                            for child in widget.winfo_children():
                                if isinstance(child, ttk.Frame):
                                    for grandchild in child.winfo_children():
                                        if isinstance(grandchild, ttk.Frame):
                                            for text_widget in grandchild.winfo_children():
                                                if isinstance(text_widget, tk.Text):
                                                    text_widget.delete("1.0", tk.END)
                                                    text_widget.insert("1.0", server_description)
                                                    break
                
                # Сохраняем обновленные данные локально (без синхронизации с сервером)
                if any([server_name != current_name, server_address != current_address, server_description != current_description]):
                    self.save_project_info_locally()
                    
        except Exception as e:
            # Не показываем ошибку пользователю, просто логируем
            print(f"Ошибка загрузки данных с сервера: {e}")
            
    def update_status(self, message):
        """Обновление статусной строки"""
        # Проверяем, существует ли статусная строка
        if not hasattr(self, 'status_label') or self.status_label is None:
            return  # Если статусная строка еще не создана, просто выходим
        
        # Добавляем временную метку для более информативного отображения
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.status_label.configure(text=formatted_message)
        self.root.update_idletasks()
        
    def add_photo(self):
        """Добавление фотографии для анализа"""
        try:
            # Открываем диалог выбора файлов
            file_paths = filedialog.askopenfilenames(
                title="Выберите фотографии для анализа",
                filetypes=[
                    ("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff *.heic *.heif"),
                    ("HEIC/HEIF", "*.heic *.heif"),
                    ("Все файлы", "*.*")
                ]
            )
            
            if file_paths:
                self.update_status(f"Добавление {len(file_paths)} фотографий...")
                self.progress.start()
                
                # Запускаем анализ в отдельном потоке
                threading.Thread(
                    target=self._analyze_photos_thread,
                    args=(file_paths,),
                    daemon=True
                ).start()
            else:
                self.update_status("Выбор файлов отменен")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка добавления фотографий: {str(e)}")
            self.update_status(f"Ошибка: {str(e)}")
            
    def _analyze_photos_thread(self, file_paths):
        """Поток для анализа фотографий"""
        try:
            for i, file_path in enumerate(file_paths):
                # Обновляем статус
                self.root.after(0, lambda: self.update_status(f"Анализ фото {i+1}/{len(file_paths)}: {Path(file_path).name}"))
                
                # Анализируем фотографию
                result = analyze_local_photo(file_path)
                
                if result:
                    # Добавляем результат в интерфейс
                    self.root.after(0, lambda r=result: self.add_result_to_tree(r, len(self.analysis_results) + 1))
                    self.analysis_results.append(result)
                    
            # Завершаем
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.update_status(f"Анализ завершен. Обработано {len(file_paths)} фотографий"))
            # Анализ завершен успешно - не показываем диалог
            pass
            
        except Exception as e:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка анализа: {str(e)}"))
            self.root.after(0, lambda: self.update_status(f"Ошибка анализа: {str(e)}"))
            
    def batch_analyze_photos(self):
        """Пакетный анализ фотографий"""
        try:
            # Открываем диалог выбора папки
            folder_path = filedialog.askdirectory(
                title="Выберите папку с фотографиями для пакетного анализа"
            )
            
            if folder_path:
                # Получаем все изображения в папке
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.heic', '.heif'}
                image_files = []
                
                for file_path in Path(folder_path).rglob('*'):
                    if file_path.suffix.lower() in image_extensions:
                        image_files.append(str(file_path))
                
                if image_files:
                    # Показываем диалог подтверждения
                    count = len(image_files)
                    # Автоматически продолжаем пакетный анализ
                    if True:
                        self.update_status(f"Начинаем пакетный анализ {count} фотографий...")
                        self.progress.start()
                        
                        # Запускаем анализ в отдельном потоке
                        threading.Thread(
                            target=self._batch_analyze_thread,
                            args=(image_files,),
                            daemon=True
                        ).start()
                else:
                    messagebox.showwarning("Предупреждение", "В выбранной папке не найдено изображений")
            else:
                self.update_status("Выбор папки отменен")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка пакетного анализа: {str(e)}")
            self.update_status(f"Ошибка: {str(e)}")
            
    def _batch_analyze_thread(self, file_paths):
        """Поток для пакетного анализа"""
        try:
            # Используем функцию пакетного анализа
            results = batch_analyze_photos(file_paths)
            
            if results:
                # Добавляем результаты в интерфейс
                for i, result in enumerate(results):
                    self.root.after(0, lambda r=result, idx=i: self.add_result_to_tree(r, len(self.analysis_results) + idx + 1))
                    self.analysis_results.append(result)
                
                # Завершаем
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.update_status(f"Пакетный анализ завершен. Обработано {len(results)} фотографий"))
                # Пакетный анализ завершен успешно - не показываем диалог
                pass
            else:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.update_status("Пакетный анализ не дал результатов"))
                
        except Exception as e:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка пакетного анализа: {str(e)}"))
            self.root.after(0, lambda: self.update_status(f"Ошибка пакетного анализа: {str(e)}"))
            
    def clear_results(self):
        """Очистка результатов анализа"""
        # Автоматически очищаем результаты анализа
        if True:
            # Очищаем список результатов
            self.analysis_results.clear()
            
            # Обновляем таблицу
            if hasattr(self, 'results_tree'):
                self.populate_results_table()
            
            # Очищаем детали
            if hasattr(self, 'photo_label'):
                self.photo_label.configure(text="Выберите результат для просмотра")
            if hasattr(self, 'details_text'):
                self.details_text.delete(1.0, tk.END)
            
            self.update_status("Результаты анализа очищены")
            
    def refresh_results(self):
        """Обновление списка результатов"""
        try:
            # Загружаем последние результаты
            self.load_recent_analyses()
            
            # Заполняем таблицу данными
            self.populate_results_table()
            
            self.update_status("Список результатов обновлен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка обновления результатов: {str(e)}")
            self.update_status(f"Ошибка обновления: {str(e)}")
            
    def on_double_click_analyze(self, event):
        """Обработчик двойного клика для быстрого анализа"""
        selection = self.results_tree.selection()
        if selection:
            # Получаем данные выбранного элемента
            item = self.results_tree.item(selection[0])
            file_path = item['values'][1]  # Путь к файлу
            
            # Если файл существует, запускаем повторный анализ
            if os.path.exists(file_path):
                self.update_status(f"Повторный анализ: {Path(file_path).name}")
                self.progress.start()
                
                # Запускаем анализ в отдельном потоке
                threading.Thread(
                    target=self._reanalyze_photo_thread,
                    args=(file_path,),
                    daemon=True
                ).start()
            else:
                messagebox.showwarning("Предупреждение", "Файл не найден")
                
    # ===== Методы для работы с калькулятором износа =====
    
    def load_wear_template(self, building_type: str):
        """Загрузка шаблона здания"""
        if not hasattr(self, 'wear_calculator') or self.wear_calculator is None:
            messagebox.showerror("Ошибка", "Калькулятор износа не инициализирован")
            return
            
        try:
            from adapters.wear_calculator import BuildingTypeTemplates
            
            # Сохраняем текущие введённые значения для активного шаблона
            prev_values = {elem.name: elem.wear_percent for elem in self.wear_calculator.elements}
            self._saved_wear_by_template[self._current_template_key] = prev_values

            if building_type == "residential":
                elements = BuildingTypeTemplates.get_residential_building()
                type_name = "жилого здания"
            elif building_type == "office":
                elements = BuildingTypeTemplates.get_office_building()
                type_name = "офисного здания"
            elif building_type == "industrial":
                elements = BuildingTypeTemplates.get_industrial_building()
                type_name = "промышленного здания"
            else:
                return
                
            # Применяем новый набор элементов
            self.wear_calculator.elements = elements
            self._current_template_key = building_type

            # Восстанавливаем сохранённые значения износа, если есть для выбранного шаблона
            saved = self._saved_wear_by_template.get(building_type)
            if saved is None:
                # Если раньше не сохраняли конкретно для этого шаблона, переносим значения
                # из только что активного (prev_values) по совпадающим именам
                saved = prev_values
            for elem in self.wear_calculator.elements:
                if elem.name in saved:
                    try:
                        elem.wear_percent = float(saved.get(elem.name, 0.0))
                    except (TypeError, ValueError):
                        elem.wear_percent = 0.0
                        
            self.update_wear_table()
            self.update_wear_totals()
            
            messagebox.showinfo("Шаблон загружен", f"Загружен шаблон {type_name}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки шаблона: {str(e)}")
            
    def load_wear_data(self):
        """Загрузка данных при открытии"""
        self.update_wear_table()
        
    def update_wear_table(self):
        """Обновление таблицы элементов"""
        if not hasattr(self, 'wear_tree') or not hasattr(self, 'wear_calculator') or self.wear_calculator is None:
            return
            
        # Очищаем таблицу
        self.wear_tree.delete(*self.wear_tree.get_children())
        
        # Заполняем данными
        for element in self.wear_calculator.elements:
            self.wear_tree.insert('', tk.END, values=(
                element.name,
                f"{element.weight_percent:.1f}",
                f"{element.wear_percent:.1f}",
                f"{element.weighted_wear:.2f}"
            ))
            
        # Добавляем итоговую строку
        total_weight = sum(elem.weight_percent for elem in self.wear_calculator.elements)
        total_wear = self.wear_calculator.calculate_total_wear()
        
        self.wear_tree.insert('', tk.END, values=(
            "ИТОГО",
            f"{total_weight:.1f}",
            "-",
            f"{total_wear:.1f}"
        ), tags=('total',))
        
        # Настраиваем стиль итоговой строки
        self.wear_tree.tag_configure('total', background='lightgray', font=('Segoe UI', 10, 'bold'))
        self.wear_tree.update_idletasks()
        
    def update_wear_totals(self):
        """Обновление итоговых результатов"""
        if not hasattr(self, 'total_wear_label') or not hasattr(self, 'wear_calculator') or self.wear_calculator is None:
            return
            
        total_wear = self.wear_calculator.calculate_total_wear()
        condition = self.wear_calculator.get_technical_condition(total_wear)
        
        # Обновляем лейблы
        self.total_wear_label.config(text=f"{total_wear}%")
        self.condition_label.config(text=condition["category"])
        
        # Цвет в зависимости от состояния
        if total_wear <= 20:
            color = "green"
        elif total_wear <= 40:
            color = "orange"
        elif total_wear <= 60:
            color = "red"
        else:
            color = "darkred"
            
        self.total_wear_label.config(foreground=color)
        self.condition_label.config(foreground=color)
        
        # Обновляем рекомендации
        self.recommendation_text.delete(1.0, tk.END)
        self.recommendation_text.insert(1.0, 
            f"{condition['description']}.\n"
            f"Рекомендации: {condition['recommendation']}."
        )
        
    def edit_wear_value(self, event):
        """Редактирование значения износа по двойному клику"""
        if not hasattr(self, 'wear_tree') or not hasattr(self, 'wear_calculator') or self.wear_calculator is None:
            return
            
        # Находим идентификатор строки под курсором
        item_id = self.wear_tree.identify_row(event.y)
        if not item_id:
            return

        # Устанавливаем фокус и выделение на найденную строку
        self.wear_tree.focus(item_id)
        self.wear_tree.selection_set(item_id)

        values = self.wear_tree.item(item_id, 'values')
        if not values:
            return

        # Не редактируем итоговую строку
        if values[0] == "ИТОГО":
            return

        element_name = values[0]
        try:
            current_wear = float(values[2])
        except (ValueError, TypeError):
            current_wear = 0.0

        # Получаем координаты ячейки третьей колонки ('wear')
        bbox = self.wear_tree.bbox(item_id, '#3')
        if not bbox:
            return
        x, y, w, h = bbox

        # Создаем Entry поверх ячейки
        editor_entry = ttk.Entry(self.wear_tree, justify='center')
        editor_entry.place(x=x, y=y, width=w, height=h)
        editor_entry.insert(0, f"{current_wear}")
        editor_entry.focus_set()
        
        # Выделяем всё содержимое
        try:
            editor_entry.select_range(0, tk.END)
            editor_entry.icursor(tk.END)
        except Exception:
            pass

        def commit(event=None):
            try:
                text = editor_entry.get().replace(',', '.')
                new_value = float(text)
            except ValueError:
                new_value = current_wear

            new_value = max(0.0, min(100.0, new_value))

            element_name_local = self.wear_tree.item(item_id, 'values')[0]
            updated = self.wear_calculator.update_element_wear(element_name_local, new_value)
            if updated:
                # Обновляем текущую строку
                elem = self.wear_calculator.get_element_by_name(element_name_local)
                if elem:
                    self.wear_tree.item(item_id, values=(
                        elem.name,
                        f"{elem.weight_percent:.1f}",
                        f"{elem.wear_percent:.1f}",
                        f"{elem.weighted_wear:.2f}"
                    ))

                # Обновляем итоговую строку и метки
                self.update_wear_table()
                self.update_wear_totals()
                
                # Сохраняем значения для текущего шаблона
                self._saved_wear_by_template[self._current_template_key] = {
                    e.name: e.wear_percent for e in self.wear_calculator.elements
                }

            editor_entry.destroy()

        def cancel(event=None):
            editor_entry.destroy()

        editor_entry.bind('<Return>', commit)
        editor_entry.bind('<KP_Enter>', commit)
        editor_entry.bind('<Escape>', cancel)
        editor_entry.bind('<FocusOut>', commit)
        
    def on_wear_tree_click(self, event):
        """Обработчик клика по таблице износа"""
        item_id = self.wear_tree.identify_row(event.y)
        if item_id:
            self.wear_tree.selection_set(item_id)
            self.wear_tree.focus(item_id)
            
    def reset_wear_data(self):
        """Сброс всех данных износа"""
        if not hasattr(self, 'wear_calculator') or self.wear_calculator is None:
            messagebox.showerror("Ошибка", "Калькулятор износа не инициализирован")
            return
            
        # Автоматически сбрасываем значения износа
        if True:
            self.wear_calculator.reset_all_wear()
            self.update_wear_table()
            self.update_wear_totals()
            # Обновляем сохранённые значения для текущего шаблона
            self._saved_wear_by_template[self._current_template_key] = {
                elem.name: elem.wear_percent for elem in self.wear_calculator.elements
            }
            
    def export_wear_to_word(self):
        """Экспорт расчета износа в Word"""
        if not hasattr(self, 'wear_calculator') or self.wear_calculator is None:
            messagebox.showerror("Ошибка", "Калькулятор износа не инициализирован")
            return
            
        try:
            from adapters.unified_report_generator import generate_wear_report
            
            file_path = filedialog.asksaveasfilename(
                title="Сохранить отчет по износу",
                defaultextension=".docx",
                filetypes=[("Word документы", "*.docx"), ("Все файлы", "*.*")]
            )
            
            if file_path:
                report_data = self.wear_calculator.generate_report_data()
                success = generate_wear_report(report_data, file_path)
                
                if success:
                    messagebox.showinfo("Экспорт", f"✅ Отчет сохранен в:\n{file_path}")
                    
                    # Предлагаем открыть файл
                    # Автоматически открываем созданный отчет
                    if True:
                        try:
                            import subprocess
                            subprocess.run(['open', file_path], check=True)  # macOS
                        except:
                            try:
                                import os
                                os.startfile(file_path)  # Windows
                            except:
                                pass
                else:
                    messagebox.showerror("Ошибка", "Не удалось создать отчет")
                    
        except ImportError:
            messagebox.showwarning("Функция недоступна", "Модуль экспорта в Word пока не реализован")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")
                
    # ===== Методы для работы с конструктивными решениями =====
    
    def _enable_select_all(self, widget: ttk.Combobox):
        """Включить выделение всего текста при фокусе"""
        def select_all(event=None):
            try:
                widget.select_range(0, tk.END)
                widget.icursor(tk.END)
            except Exception:
                pass
        widget.bind('<FocusIn>', select_all)
        widget.bind('<Double-Button-1>', select_all)

    def _is_leaf(self, value: Any) -> bool:
        """Проверка, является ли значение листом дерева"""
        return isinstance(value, str)

    def _collect_label_text_pairs(self, subtree: Any, path: Optional[List[str]] = None) -> List[Tuple[str, str]]:
        """Возвращает пары (краткая_метка, полный_текст) для всех листов поддерева"""
        if path is None:
            path = []
        pairs: List[Tuple[str, str]] = []
        if isinstance(subtree, str):
            label = " / ".join([p for p in path if p]) or subtree[:40]
            pairs.append((label, subtree))
        elif isinstance(subtree, dict):
            for k, v in subtree.items():
                if k == "__custom__":
                    continue
                pairs.extend(self._collect_label_text_pairs(v, path + [k]))
        return pairs

    def _on_construction_element_change(self, event=None):
        """Обработчик изменения выбранной конструкции"""
        sel = self.element_combo.get().strip()
        self._desc_label_to_text.clear()
        values: List[str] = []
        if sel and sel in self.CONSTRUCTION_TREE:
            pairs = self._collect_label_text_pairs(self.CONSTRUCTION_TREE[sel], [])
            for label, text in pairs:
                # Накапливаем уникальные метки
                if label not in self._desc_label_to_text:
                    self._desc_label_to_text[label] = text
            values = list(self._desc_label_to_text.keys())
        values.sort()
        self.desc_combo.configure(values=values)

    def _get_construction_editor_values(self) -> Tuple[str, str]:
        """Получение значений из редактора"""
        element = self.element_combo.get().strip()
        desc_label_or_text = self.desc_combo.get().strip()
        return element, desc_label_or_text

    def _add_construction_row(self):
        """Добавление строки в таблицу конструктивных решений"""
        element, desc = self._get_construction_editor_values()
        if not element:
            messagebox.showwarning("Предупреждение", "Укажите конструкцию")
            return
        if not desc:
            messagebox.showwarning("Предупреждение", "Укажите описание")
            return
        # Всегда добавляем новую строку (дубликаты допускаются)
        self.construction_tree.insert('', tk.END, values=(element, desc))

    def _delete_construction_row(self):
        """Удаление выбранных строк из таблицы"""
        for iid in self.construction_tree.selection():
            self.construction_tree.delete(iid)

    def _clear_construction_all(self):
        """Очистка всей таблицы конструктивных решений"""
        self.construction_tree.delete(*self.construction_tree.get_children())

    def _on_construction_row_select(self, event=None):
        """Обработчик выбора строки в таблице"""
        sel = self.construction_tree.selection()
        if not sel:
            return
        vals = self.construction_tree.item(sel[0], 'values')
        if not vals:
            return
        element, desc = vals[0], vals[1]
        # Подставляем значения в редактор. Оба поля редактируемые
        self.element_combo.set(element)
        self._on_construction_element_change()
        self.desc_combo.set(desc)

    def _label_to_full_text(self, category: str, label_or_text: str) -> str:
        """Возвращает полный текст по метке для выбранной категории"""
        try:
            subtree = self.CONSTRUCTION_TREE.get(category)
            if not isinstance(subtree, dict):
                return label_or_text
            pairs = self._collect_label_text_pairs(subtree, [])
            for lbl, text in pairs:
                if lbl == label_or_text:
                    return text
            return label_or_text
        except Exception:
            return label_or_text

    def _save_construction_data(self):
        """Сохранение конструктивных решений"""
        items = []
        for iid in self.construction_tree.get_children():
            vals = self.construction_tree.item(iid, 'values')
            if not vals:
                continue
            category = str(vals[0]).strip()
            desc_value = str(vals[1]).strip()
            full_text = self._label_to_full_text(category, desc_value)
            items.append({'category': category, 'text': full_text})

        if not items:
            messagebox.showwarning("Предупреждение", "Добавьте хотя бы одну строку")
            return

        saved_ok = True
        # Пакетное сохранение, если доступно
        try:
            if self.file_manager and hasattr(self.file_manager, 'save_constructive_solutions_bundle'):
                self.file_manager.save_constructive_solutions_bundle(items)
            elif self.file_manager and hasattr(self.file_manager, 'save_constructive_solution'):
                for it in items:
                    self.file_manager.save_constructive_solution(it)
        except Exception as e:
            saved_ok = False
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

        self.construction_data = items
        if saved_ok:
            messagebox.showinfo("Готово", "Конструктивные решения сохранены")
            self.update_status("Конструктивные решения сохранены")

    def _cancel_construction_edits(self):
        """Отмена редактирования конструктивных решений"""
        # Просто очищаем редактор
        self.element_combo.set("")
        self.desc_combo.set("")

    def _show_quick_solutions(self):
        """Показать диалог быстрого выбора предзаполненных решений"""
        try:
            if not self.PREDEFINED_SOLUTIONS:
                messagebox.showinfo("Информация", "Нет доступных быстрых решений")
                return
                
            # Создаем диалог выбора
            quick_dialog = tk.Toplevel(self.root)
            quick_dialog.title("Быстрые решения")
            quick_dialog.geometry("600x400")
            quick_dialog.transient(self.root)
            quick_dialog.grab_set()
            
            # Заголовок
            ttk.Label(
                quick_dialog,
                text="Выберите предзаполненные решения для добавления:",
                font=("Segoe UI", 12, "bold"),
            ).pack(padx=20, pady=(15, 10), anchor=tk.W)
            
            # Список решений
            listbox_frame = ttk.Frame(quick_dialog)
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Создаем список с прокруткой
            listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE)
            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Заполняем список
            for solution_name in self.PREDEFINED_SOLUTIONS.keys():
                listbox.insert(tk.END, solution_name)
            
            # Кнопки
            button_frame = ttk.Frame(quick_dialog)
            button_frame.pack(fill=tk.X, padx=20, pady=10)
            
            def add_selected():
                selected_indices = listbox.curselection()
                if not selected_indices:
                    messagebox.showwarning("Предупреждение", "Выберите хотя бы одно решение")
                    return
                    
                added_count = 0
                for index in selected_indices:
                    solution_name = listbox.get(index)
                    solution_data = self.PREDEFINED_SOLUTIONS[solution_name]
                    description = solution_data.get('описание', solution_name)
                    
                    # Добавляем в таблицу
                    self.construction_tree.insert('', tk.END, values=(solution_name, description))
                    added_count += 1
                
                quick_dialog.destroy()
                messagebox.showinfo("Готово", f"Добавлено {added_count} решений")
            
            def show_details():
                selected_indices = listbox.curselection()
                if not selected_indices:
                    messagebox.showwarning("Предупреждение", "Выберите решение для просмотра")
                    return
                    
                index = selected_indices[0]
                solution_name = listbox.get(index)
                solution_data = self.PREDEFINED_SOLUTIONS[solution_name]
                
                details_text = f"Название: {solution_name}\n\n"
                details_text += f"Тип: {solution_data.get('тип', 'Не указан')}\n"
                details_text += f"Материал: {solution_data.get('материал', 'Не указан')}\n"
                details_text += f"Исполнение: {solution_data.get('исполнение', 'Не указано')}\n"
                
                if solution_data.get('основание_и_подготовка'):
                    details_text += f"Основание и подготовка: {solution_data['основание_и_подготовка']}\n"
                if solution_data.get('армирование'):
                    details_text += f"Армирование: {solution_data['армирование']}\n"
                if solution_data.get('гидроизоляция_и_защита'):
                    details_text += f"Гидроизоляция и защита: {solution_data['гидроизоляция_и_защита']}\n"
                if solution_data.get('узлы_и_закладные'):
                    details_text += f"Узлы и закладные: {solution_data['узлы_и_закладные']}\n"
                if solution_data.get('прочее'):
                    details_text += f"Прочее: {solution_data['прочее']}\n"
                
                details_text += f"\nПолное описание:\n{solution_data.get('описание', 'Не указано')}"
                
                # Показываем в отдельном окне
                details_window = tk.Toplevel(quick_dialog)
                details_window.title(f"Детали: {solution_name}")
                details_window.geometry("500x400")
                details_window.transient(quick_dialog)
                
                text_widget = tk.Text(details_window, wrap=tk.WORD, padx=10, pady=10)
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_widget.insert(tk.END, details_text)
                text_widget.config(state=tk.DISABLED)
                
                ttk.Button(details_window, text="Закрыть", command=details_window.destroy).pack(pady=10)
            
            ttk.Button(button_frame, text="Показать детали", command=show_details).pack(side=tk.LEFT)
            ttk.Button(button_frame, text="Отмена", command=quick_dialog.destroy).pack(side=tk.RIGHT)
            ttk.Button(button_frame, text="Добавить выбранные", command=add_selected).pack(side=tk.RIGHT, padx=(0, 10))
            
            # Центрирование
            try:
                self.root.update_idletasks()
                x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 300
                y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 200
                quick_dialog.geometry(f"+{x}+{y}")
            except Exception:
                pass
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть быстрые решения: {e}")

    def _load_construction_json_data(self):
        """Загрузить данные конструктивных решений из JSON"""
        try:
            # Открываем диалог выбора файла
            file_path = filedialog.askopenfilename(
                title="Выберите JSON файл с данными конструктивных решений",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Проверяем формат данных
            if isinstance(json_data, dict) and 'solutions' in json_data:
                # Формат экспортированных данных
                solutions = json_data.get('solutions', [])
                if solutions:
                    # Очищаем текущие данные
                    self.construction_tree.delete(*self.construction_tree.get_children())
                    
                    # Добавляем новые данные
                    for item in solutions:
                        if isinstance(item, dict):
                            category = item.get('category', '')
                            text = item.get('text', '')
                            if category and text:
                                self.construction_tree.insert('', tk.END, values=(category, text))
                    
                    messagebox.showinfo("Готово", f"Загружено {len(solutions)} решений из файла")
                else:
                    messagebox.showwarning("Предупреждение", "Файл не содержит данных решений")
            else:
                # Старый формат - пытаемся загрузить через адаптер
                try:
                    from adapters.construction_data import load_construction_data_from_json, merge_construction_data
                    new_solutions = load_construction_data_from_json(json_data)
                    
                    if not new_solutions:
                        messagebox.showwarning("Предупреждение", "Не удалось загрузить данные из файла")
                        return
                    
                    # Объединяем с существующими данными
                    self.PREDEFINED_SOLUTIONS = merge_construction_data(self.PREDEFINED_SOLUTIONS, new_solutions)
                    
                    messagebox.showinfo("Готово", f"Загружено {len(new_solutions)} новых решений")
                except Exception:
                    messagebox.showerror("Ошибка", "Неизвестный формат файла")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Ошибка", f"Ошибка чтения JSON файла: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")

    def _load_saved_construction_data_silent(self):
        """Тихая загрузка сохраненных данных конструктивных решений"""
        if not self.file_manager:
            return
            
        try:
            saved_data = self.file_manager.load_constructive_solutions_bundle()
            if saved_data:
                for item in saved_data:
                    # Проверяем структуру данных
                    if isinstance(item, dict):
                        category = item.get('category', '')
                        text = item.get('text', '')
                        if category and text:
                            self.construction_tree.insert('', tk.END, values=(category, text))
                
                if saved_data:
                    print(f"Загружено {len(saved_data)} сохраненных решений")
        except Exception as e:
            print(f"Не удалось загрузить сохраненные данные: {e}")

    def _load_saved_construction_data(self):
        """Ручная загрузка сохраненных данных с уведомлением пользователя"""
        if not self.file_manager:
            messagebox.showwarning("Предупреждение", "Файл-менеджер не доступен")
            return
            
        try:
            # Очищаем текущие данные
            self.construction_tree.delete(*self.construction_tree.get_children())
            
            saved_data = self.file_manager.load_constructive_solutions_bundle()
            if saved_data:
                for item in saved_data:
                    # Проверяем структуру данных
                    if isinstance(item, dict):
                        category = item.get('category', '')
                        text = item.get('text', '')
                        if category and text:
                            self.construction_tree.insert('', tk.END, values=(category, text))
                
                messagebox.showinfo("Готово", f"Загружено {len(saved_data)} сохраненных решений")
            else:
                messagebox.showinfo("Информация", "Сохраненных данных не найдено")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить сохраненные данные: {e}")

    def _export_construction_to_json(self):
        """Экспорт текущих данных в JSON файл"""
        try:
            from datetime import datetime
            
            # Собираем текущие данные
            items = []
            for iid in self.construction_tree.get_children():
                vals = self.construction_tree.item(iid, 'values')
                if not vals:
                    continue
                category = str(vals[0]).strip()
                desc_value = str(vals[1]).strip()
                if category and desc_value:
                    items.append({'category': category, 'text': desc_value})
            
            if not items:
                messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
                return
            
            # Открываем диалог сохранения файла
            file_path = filedialog.asksaveasfilename(
                title="Сохранить конструктивные решения",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Формируем данные для экспорта
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "project": self.file_manager.current_project if self.file_manager else "Неизвестный объект",
                "solutions": items
            }
            
            # Сохраняем файл
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Готово", f"Экспортировано {len(items)} решений в файл:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {e}")
                
    def _reanalyze_photo_thread(self, file_path):
        """Поток для повторного анализа фотографии"""
        try:
            # Анализируем фотографию
            result = analyze_local_photo(file_path)
            
            if result:
                # Обновляем результат в интерфейсе
                self.root.after(0, lambda: self.update_status(f"Повторный анализ завершен: {Path(file_path).name}"))
                self.root.after(0, lambda: self.progress.stop())
                
                # Обновляем отображение деталей
                self.root.after(0, lambda: self.show_analysis_details(result))
            else:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.update_status("Повторный анализ не дал результатов"))
                
        except Exception as e:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка повторного анализа: {str(e)}"))
            self.root.after(0, lambda: self.update_status(f"Ошибка повторного анализа: {str(e)}"))
        
    def create_plans_section(self, parent):
        """Создание блока планов"""
        
        # Основной контейнер для планов
        plans_frame = ttk.Frame(parent)
        plans_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Главный горизонтальный разделитель (левая и правая панели)
        main_paned = ttk.PanedWindow(plans_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - список планов и детали
        left_panel = ttk.Frame(main_paned)
        main_paned.add(left_panel, weight=1)
        
        # Вертикальный разделитель для левой панели (список планов и детали)
        left_paned = ttk.PanedWindow(left_panel, orient=tk.VERTICAL)
        left_paned.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя часть левой панели - список планов
        list_section = ttk.LabelFrame(left_paned, text="Список планов", padding=10)
        left_paned.add(list_section, weight=1)
        
        # Кнопки управления
        buttons_frame = ttk.Frame(list_section)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        add_plan_button = ttk.Button(
            buttons_frame,
            text="➕ Добавить план",
            style='Modern.TButton',
            command=self.add_new_plan
        )
        add_plan_button.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_plan_button = ttk.Button(
            buttons_frame,
            text="🗑️ Удалить",
            style='Secondary.TButton',
            command=self.delete_selected_plan
        )
        delete_plan_button.pack(side=tk.LEFT, padx=(0, 5))
        
        refresh_plans_button = ttk.Button(
            buttons_frame,
            text="🔄 Обновить",
            style='Secondary.TButton',
            command=self.load_plans
        )
        refresh_plans_button.pack(side=tk.LEFT)
        
        # Список планов
        list_frame = ttk.Frame(list_section)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем Treeview для списка планов
        self.plans_tree = ttk.Treeview(list_frame, columns=('name',), show='headings', height=6)
        self.plans_tree.heading('name', text='Название плана')
        self.plans_tree.column('name', width=250)
        
        # Скроллбар для списка
        plans_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.plans_tree.yview)
        self.plans_tree.configure(yscrollcommand=plans_scrollbar.set)
        
        self.plans_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plans_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязываем событие выбора
        self.plans_tree.bind('<<TreeviewSelect>>', self.on_plan_select)
        
        # Нижняя часть левой панели - детали плана
        details_section = ttk.LabelFrame(left_paned, text="Детали плана", padding=10)
        left_paned.add(details_section, weight=2)
        
        # Контейнер для деталей плана
        self.plan_details_frame = ttk.Frame(details_section)
        self.plan_details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Правая панель - изображение плана
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=1)
        
        # Заголовок изображения
        image_header = ttk.Label(right_panel, text="Изображение плана", style='Subtitle.TLabel')
        image_header.pack(pady=(0, 10))
        
        # Контейнер для изображения плана
        image_frame = ttk.LabelFrame(right_panel, text="Превью", padding=10)
        image_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для отображения изображения
        self.plan_image_frame = ttk.Frame(image_frame)
        self.plan_image_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем лейбл для изображения
        self.plan_image_label = ttk.Label(
            self.plan_image_frame, 
            text="Выберите план для просмотра изображения",
            anchor='center',
            font=('Segoe UI', 10),
            foreground='gray'
        )
        self.plan_image_label.pack(fill=tk.BOTH, expand=True)
        
        # Настраиваем стили для разделителей
        self.setup_paned_styles(main_paned, left_paned)
        
        # Настраиваем начальные пропорции разделителей
        # Устанавливаем пропорции после создания всех элементов
        self.root.after(100, lambda: self.setup_paned_proportions(main_paned, left_paned))
        
        
        # Инициализируем переменные для планов
        self.current_plan = None
        self.plans_data = []
        self.current_plan_image = None
        
        # Загружаем планы
        self.load_plans()
    
    def setup_paned_styles(self, main_paned, left_paned):
        """Настройка стилей для разделителей"""
        try:
            # Настраиваем стили разделителей
            style = ttk.Style()
            
            # Стиль для горизонтального разделителя (основной)
            style.configure('Horizontal.TPanedwindow', 
                           background='#f0f0f0',
                           sashwidth=6,
                           sashpad=2)
            
            # Стиль для вертикального разделителя
            style.configure('Vertical.TPanedwindow', 
                           background='#f0f0f0',
                           sashwidth=6,
                           sashpad=2)
            
            # Применяем стили
            main_paned.configure(style='Horizontal.TPanedwindow')
            left_paned.configure(style='Vertical.TPanedwindow')
            
        except Exception as e:
            print(f"Ошибка настройки стилей разделителей: {e}")
    
    def setup_paned_proportions(self, main_paned, left_paned):
        """Настройка начальных пропорций разделителей"""
        try:
            # Получаем общую ширину окна
            main_paned.update_idletasks()
            total_width = main_paned.winfo_width()
            
            if total_width > 0:
                # Настраиваем горизонтальный разделитель (левая панель : правая панель = 60% : 40%)
                left_width = int(total_width * 0.6)
                main_paned.sash_place(0, left_width, 0)
            
            # Получаем высоту левой панели
            left_paned.update_idletasks()
            left_height = left_paned.winfo_height()
            
            if left_height > 0:
                # Настраиваем вертикальный разделитель (список планов : детали = 40% : 60%)
                list_height = int(left_height * 0.4)
                left_paned.sash_place(0, 0, list_height)
                
        except Exception as e:
            print(f"Ошибка настройки пропорций разделителей: {e}")
    
    
    def display_plan_image(self, image):
        """Отображение изображения плана"""
        try:
            # Получаем размеры фрейма
            self.plan_image_frame.update_idletasks()
            frame_width = self.plan_image_frame.winfo_width()
            frame_height = self.plan_image_frame.winfo_height()
            
            if frame_width <= 1 or frame_height <= 1:
                # Если фрейм еще не отрисован, используем стандартные размеры
                frame_width, frame_height = 400, 300
            
            # Вычисляем размеры для отображения с сохранением пропорций
            img_width, img_height = image.size
            aspect_ratio = img_width / img_height
            
            if aspect_ratio > frame_width / frame_height:
                # Изображение шире
                display_width = min(frame_width - 20, img_width)
                display_height = int(display_width / aspect_ratio)
            else:
                # Изображение выше
                display_height = min(frame_height - 20, img_height)
                display_width = int(display_height * aspect_ratio)
            
            # Изменяем размер изображения
            resized_image = image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            # Конвертируем в PhotoImage для tkinter
            photo = ImageTk.PhotoImage(resized_image)
            
            # Обновляем лейбл
            self.plan_image_label.configure(image=photo, text="")
            self.plan_image_label.image = photo  # Сохраняем ссылку
            
        except Exception as e:
            print(f"Ошибка отображения изображения: {e}")
            self.plan_image_label.configure(
                image="", 
                text=f"Ошибка загрузки изображения:\n{str(e)}",
                foreground='red'
            )
    
    
    def load_plan_image(self, plan_id):
        """Загрузка изображения плана из файла"""
        try:
            # Ищем файл изображения
            plans_images_dir = self.file_manager.get_project_file('plans_images')
            
            if not plans_images_dir.exists():
                return None
            
            # Ищем файлы изображений для данного плана
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
            for ext in image_extensions:
                image_path = plans_images_dir / f"plan_{plan_id}{ext}"
                if image_path.exists():
                    return str(image_path)
            
            return None
            
        except Exception as e:
            print(f"Ошибка поиска изображения плана: {e}")
            return None
    
    def load_plans(self):
        """Загрузка списка планов с сервера"""
        try:
            print("DEBUG: Начинаем загрузку планов...")
            from adapters.plans_api_client import get_plans_api_client
            from adapters.auth_client import auth_client
            
            if not auth_client.is_authenticated():
                print("DEBUG: Пользователь не авторизован")
                self.update_status("Авторизация необходима для работы с планами")
                return
            
            print("DEBUG: Пользователь авторизован")
            
            # Получаем ID объекта
            object_id = self.get_current_object_id()
            print(f"DEBUG: Получен object_id: {object_id}")
            if not object_id:
                print("DEBUG: Не удалось получить object_id")
                self.update_status("Не удалось определить ID объекта")
                return
            
            plans_client = get_plans_api_client(auth_client)
            print(f"DEBUG: Делаем запрос планов для объекта {object_id}")
            result = plans_client.get_plans_by_object(object_id)
            print(f"DEBUG: Результат запроса: {result}")
            
            if result.get('success'):
                self.plans_data = result.get('plans', [])
                print(f"DEBUG: Загружено планов: {len(self.plans_data)}")
                print(f"DEBUG: Данные планов: {self.plans_data}")
                self.update_plans_list()
                self.update_status(f"Загружено {len(self.plans_data)} планов")
            else:
                print(f"DEBUG: Ошибка загрузки планов: {result.get('error')}")
                self.update_status(f"Ошибка загрузки планов: {result.get('error')}")
                
        except Exception as e:
            print(f"DEBUG: Исключение при загрузке планов: {str(e)}")
            import traceback
            traceback.print_exc()
            self.update_status(f"Ошибка загрузки планов: {str(e)}")
    
    def get_current_object_id(self):
        """Получение ID текущего объекта"""
        try:
            print("DEBUG: Начинаем получение object_id...")
            from adapters.project_api_client import get_project_api_client
            from adapters.auth_client import auth_client
            
            if not auth_client.is_authenticated():
                print("DEBUG: Пользователь не авторизован в get_current_object_id")
                return None
            
            project_client = get_project_api_client(auth_client)
            current_object_name = self.file_manager.current_project  # Это название объекта
            print(f"DEBUG: Текущий объект: {current_object_name}")
            
            # Получаем все проекты
            projects_result = project_client.get_projects()
            print(f"DEBUG: Результат получения проектов: {projects_result}")
            if not projects_result.get('success'):
                print("DEBUG: Не удалось получить проекты")
                return None
            
            projects = projects_result.get('projects', [])
            print(f"DEBUG: Найдено проектов: {len(projects)}")
            
            # Ищем объект по названию во всех проектах
            for project in projects:
                project_id = project.get('id')
                project_name = project.get('name')
                print(f"DEBUG: Проверяем проект {project_name} (ID: {project_id})")
                
                # Получаем объекты проекта
                objects_result = project_client.get_objects_by_project(project_id)
                if objects_result.get('success'):
                    objects = objects_result.get('objects', [])
                    print(f"DEBUG: В проекте {project_name} найдено объектов: {len(objects)}")
                    
                    # Ищем объект по названию
                    for obj in objects:
                        obj_name = obj.get('name')
                        obj_id = obj.get('id')
                        print(f"DEBUG: Проверяем объект '{obj_name}' (ID: {obj_id})")
                        if obj_name == current_object_name:
                            print(f"DEBUG: Найден объект '{current_object_name}' с ID: {obj_id}")
                            return obj_id
                else:
                    print(f"DEBUG: Не удалось получить объекты проекта {project_name}")
            
            print(f"DEBUG: Объект '{current_object_name}' не найден ни в одном проекте")
            
            # Если объект не найден, создаем его в первом доступном проекте
            if projects:
                first_project = projects[0]
                project_id = first_project.get('id')
                project_name = first_project.get('name')
                print(f"DEBUG: Создаем объект '{current_object_name}' в проекте '{project_name}' (ID: {project_id})")
                
                current_name = self.object_name_var.get() if hasattr(self, 'object_name_var') else current_object_name
                current_address = self.object_address_var.get() if hasattr(self, 'object_address_var') else ''
                current_description = self.object_description_var.get() if hasattr(self, 'object_description_var') else ''
                
                print(f"DEBUG: Создаем объект с данными: name={current_name}, address={current_address}")
                create_result = project_client.create_object(
                    project_id=project_id,
                    name=current_name,
                    address=current_address,
                    description=current_description
                )
                print(f"DEBUG: Результат создания объекта: {create_result}")
                
                if create_result.get('success'):
                    new_object_id = create_result.get('object', {}).get('id')
                    print(f"DEBUG: Создан новый объект с ID: {new_object_id}")
                    return new_object_id
            
            print("DEBUG: Не удалось создать объект")
            return None
            
        except Exception as e:
            print(f"DEBUG: Исключение в get_current_object_id: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_plans_list(self):
        """Обновление списка планов в Treeview"""
        print(f"DEBUG: Обновляем список планов, количество: {len(self.plans_data)}")
        
        # Очищаем список
        for item in self.plans_tree.get_children():
            self.plans_tree.delete(item)
        
        # Добавляем планы
        for plan in self.plans_data:
            print(f"DEBUG: Добавляем план в список: {plan}")
            self.plans_tree.insert('', 'end', 
                                 iid=plan.get('id'),
                                 values=(plan.get('name', ''),))
        
        print(f"DEBUG: Список планов обновлен, элементов в TreeView: {len(self.plans_tree.get_children())}")
    
    def on_plan_select(self, event):
        """Обработчик выбора плана в списке"""
        selection = self.plans_tree.selection()
        if not selection:
            return
        
        plan_id = int(selection[0])
        self.current_plan = next((p for p in self.plans_data if p.get('id') == plan_id), None)
        
        if self.current_plan:
            self.show_plan_details()
            self.load_and_display_plan_image()
    
    def load_and_display_plan_image(self):
        """Загрузка и отображение изображения плана"""
        if not self.current_plan:
            return
            
        try:
            plan_id = self.current_plan.get('id')
            
            # Сначала пробуем загрузить локальное изображение
            local_image_path = self.load_plan_image(plan_id)
            if local_image_path:
                image = Image.open(local_image_path)
                self.display_plan_image(image)
                return
            
            # Если локального изображения нет, пробуем загрузить с сервера
            image_url = self.current_plan.get('image_url')
            if image_url:
                import urllib.request
                import ssl
                
                # Создаем SSL контекст, который не проверяет сертификаты
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # Создаем opener с SSL контекстом
                opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
                urllib.request.install_opener(opener)
                
                with urllib.request.urlopen(image_url) as url:
                    img_data = url.read()
                
                image = Image.open(io.BytesIO(img_data))
                self.display_plan_image(image)
                return
            
            # Если изображения нет, показываем заглушку
            self.plan_image_label.configure(
                image="", 
                text="Изображение плана не найдено",
                foreground='gray'
            )
            self.plan_image_label.image = None
            
        except Exception as e:
            print(f"Ошибка загрузки изображения плана: {e}")
            self.plan_image_label.configure(
                image="", 
                text=f"Ошибка загрузки изображения:\n{str(e)}",
                foreground='red'
            )
            self.plan_image_label.image = None
    
    def show_plan_details(self):
        """Отображение деталей выбранного плана"""
        # Очищаем панель деталей
        for widget in self.plan_details_frame.winfo_children():
            widget.destroy()
        
        if not self.current_plan:
            return
        
        # Информация о плане
        info_frame = ttk.LabelFrame(self.plan_details_frame, text="Информация о плане", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Название плана
        name_frame = ttk.Frame(info_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        name_label = ttk.Label(name_frame, text="Название:", style='Subtitle.TLabel')
        name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.plan_name_var = tk.StringVar(value=self.current_plan.get('name', ''))
        name_entry = ttk.Entry(name_frame, textvariable=self.plan_name_var, width=40, font=('Segoe UI', 11))
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Описание плана
        desc_frame = ttk.Frame(info_frame)
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        desc_label = ttk.Label(desc_frame, text="Описание:", style='Subtitle.TLabel')
        desc_label.pack(anchor='nw', pady=(0, 5))
        
        self.plan_description_var = tk.StringVar(value=self.current_plan.get('description', ''))
        desc_text = tk.Text(desc_frame, height=6, width=40, font=('Segoe UI', 11), wrap=tk.WORD)
        desc_text.pack(fill=tk.BOTH, expand=True)
        desc_text.insert("1.0", self.plan_description_var.get())
        
        # Синхронизация текстового поля с переменной
        def on_desc_change(event=None):
            self.plan_description_var.set(desc_text.get("1.0", tk.END).strip())
        
        desc_text.bind('<KeyRelease>', on_desc_change)
        desc_text.bind('<FocusOut>', on_desc_change)
        
        # Кнопка сохранения изменений
        save_button = ttk.Button(
            info_frame,
            text="💾 Сохранить изменения",
            style='Modern.TButton',
            command=self.save_plan_changes
        )
        save_button.pack(pady=(10, 0))
    
    def add_new_plan(self):
        """Добавление нового плана"""
        try:
            from tkinter import filedialog
            
            # Выбираем файл изображения
            file_path = filedialog.askopenfilename(
                title="Выберите изображение плана",
                filetypes=[
                    ("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif"),
                    ("Все файлы", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Запрашиваем название и описание плана
            dialog = PlanDialog(self.root, "Добавить новый план")
            if dialog.result is None:
                return
            
            name, description = dialog.result
            
            if not name.strip():
                messagebox.showerror("Ошибка", "Название плана не может быть пустым")
                return
            
            # Загружаем изображение
            from adapters.plans_api_client import get_plans_api_client
            from adapters.auth_client import auth_client
            
            if not auth_client.is_authenticated():
                messagebox.showerror("Ошибка", "Необходима авторизация")
                return
            
            plans_client = get_plans_api_client(auth_client)
            
            # Загружаем изображение в GCP
            upload_result = plans_client.upload_image(file_path)
            if not upload_result.get('success'):
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {upload_result.get('error')}")
                return
            
            image_name = upload_result.get('image_name')
            
            # Получаем ID объекта
            object_id = self.get_current_object_id()
            if not object_id:
                messagebox.showerror("Ошибка", "Не удалось определить ID объекта")
                return
            
            # Создаем план
            create_result = plans_client.create_plan(
                object_id=object_id,
                name=name,
                description=description,
                image_name=image_name
            )
            
            if create_result.get('success'):
                messagebox.showinfo("Успех", "План успешно создан")
                self.load_plans()  # Перезагружаем список планов
                self.update_status("План создан успешно")
            else:
                messagebox.showerror("Ошибка", f"Не удалось создать план: {create_result.get('error')}")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка создания плана: {str(e)}")
    
    def delete_selected_plan(self):
        """Удаление выбранного плана"""
        if not self.current_plan:
            messagebox.showwarning("Предупреждение", "Выберите план для удаления")
            return
        
        if not messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить план '{self.current_plan.get('name')}'?"):
            return
        
        try:
            from adapters.plans_api_client import get_plans_api_client
            from adapters.auth_client import auth_client
            
            if not auth_client.is_authenticated():
                messagebox.showerror("Ошибка", "Необходима авторизация")
                return
            
            plans_client = get_plans_api_client(auth_client)
            
            delete_result = plans_client.delete_plan(self.current_plan.get('id'))
            
            if delete_result.get('success'):
                messagebox.showinfo("Успех", "План успешно удален")
                self.current_plan = None
                self.load_plans()  # Перезагружаем список планов
                self.update_status("План удален успешно")
            else:
                messagebox.showerror("Ошибка", f"Не удалось удалить план: {delete_result.get('error')}")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка удаления плана: {str(e)}")
    
    def save_plan_changes(self):
        """Сохранение изменений плана"""
        if not self.current_plan:
            messagebox.showwarning("Предупреждение", "Выберите план для редактирования")
            return
        
        try:
            from adapters.plans_api_client import get_plans_api_client
            from adapters.auth_client import auth_client
            
            if not auth_client.is_authenticated():
                messagebox.showerror("Ошибка", "Необходима авторизация")
                return
            
            plans_client = get_plans_api_client(auth_client)
            
            name = self.plan_name_var.get().strip()
            description = self.plan_description_var.get().strip()
            
            if not name:
                messagebox.showerror("Ошибка", "Название плана не может быть пустым")
                return
            
            update_result = plans_client.update_plan(
                plan_id=self.current_plan.get('id'),
                name=name,
                description=description
            )
            
            if update_result.get('success'):
                messagebox.showinfo("Успех", "План успешно обновлен")
                self.load_plans()  # Перезагружаем список планов
                self.update_status("План обновлен успешно")
            else:
                messagebox.showerror("Ошибка", f"Не удалось обновить план: {update_result.get('error')}")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка обновления плана: {str(e)}")

    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти из системы?"):
            try:
                from adapters.auth_client import auth_client
                auth_client.logout()
                
                # Закрываем текущее окно
                self.root.destroy()
                
                # Возвращаемся к приветственному окну
                from ui.welcome_window import WelcomeWindow
                welcome = WelcomeWindow()
                welcome.run()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка выхода из системы: {str(e)}")
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ModernDefectAnalyzerWindow()
    app.run()
