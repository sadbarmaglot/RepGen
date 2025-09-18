import tkinter as tk
from tkinter import ttk, messagebox
import threading
from pathlib import Path
import sys

# Импортируем поддержку буфера обмена
from ui.clipboard_support import ClipboardEntry

# Добавляем путь к корневой папке проекта
sys.path.append(str(Path(__file__).parent.parent))

from adapters.file_manager import WindowsFileManager
from ui.project_dialogs import ProjectDialog, ProjectManagerDialog

class WelcomeWindow:
    """Приветственное окно приложения"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏗️ ИИ-Инженер - Добро пожаловать")
        
        # Получаем размер экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Устанавливаем размер окна в половину экрана
        window_width = screen_width // 2
        window_height = screen_height // 2
        
        # Центрируем окно
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(False, False)
        
        # Файловый менеджер
        self.file_manager = WindowsFileManager()
        
        # Результат выбора
        self.selected_project = None
        self.create_new_project = False
        
        # Настройка стилей
        self.setup_styles()
        
        # Создание интерфейса
        self.setup_ui()
        
    def setup_styles(self):
        """Настройка современных стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка цветов и шрифтов
        style.configure('Welcome.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       foreground='#2c3e50',
                       background='#ecf0f1')
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 12),
                       foreground='#7f8c8d',
                       background='#ecf0f1')
        
        style.configure('Modern.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 10),
                       relief='flat',
                       borderwidth=0)
        
        style.map('Modern.TButton',
                 background=[('active', '#3498db'), ('!active', '#2980b9')],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        style.configure('Project.TFrame',
                       background='#ecf0f1',
                       relief='flat',
                       borderwidth=0)
        
        style.configure('Project.TLabel',
                       font=('Segoe UI', 10),
                       background='#ecf0f1',
                       foreground='#2c3e50')
        
    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        # Основной контейнер
        main_frame = ttk.Frame(self.root, style='Project.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="🏗️ ИИ-Инженер",
            style='Welcome.TLabel'
        )
        title_label.pack(pady=(0, 10))
        
        # Подзаголовок
        subtitle_label = ttk.Label(
            main_frame,
            text="Программа для автоматического анализа строительных дефектов\nс использованием искусственного интеллекта",
            style='Subtitle.TLabel',
            justify=tk.CENTER
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Информация о возможностях
        features_frame = ttk.Frame(main_frame, style='Project.TFrame')
        features_frame.pack(fill=tk.X, pady=(0, 30))
        
        features_text = """• 📸 Анализ фотографий дефектов с помощью ИИ
• 📊 Расчет физического износа здания
• 🏗️ Конструктивные решения
• 📄 Экспорт отчетов в Word
• ☁️ Облачная синхронизация
• 📁 Управление проектами"""
        
        features_label = ttk.Label(
            features_frame,
            text=features_text,
            style='Project.TLabel',
            justify=tk.LEFT
        )
        features_label.pack()
        
        # Кнопка "Начать работу"
        start_button = ttk.Button(
            main_frame,
            text="🚀 Начать работу",
            style='Modern.TButton',
            command=self.start_application
        )
        start_button.pack(pady=(0, 20))
        
        # Версия программы
        version_label = ttk.Label(
            main_frame,
            text="Версия 1.1",
            style='Subtitle.TLabel'
        )
        version_label.pack(side=tk.BOTTOM)
        
    def start_application(self):
        """Запуск основного приложения"""
        # Сначала проверяем, есть ли уже активная сессия
        try:
            from adapters.auth_client import auth_client
            if auth_client.is_authenticated():
                # Автоматически переходим к выбору проектов
                user_info = auth_client.user_info
                self.root.destroy()
                project_window = ProjectSelectionWindow(user_info)
                project_window.run()
                return
        except Exception as e:
            print(f"Ошибка проверки аутентификации: {e}")
        
        # Если активной сессии нет, показываем диалог аутентификации
        from ui.auth_dialog import show_auth_dialog
        
        auth_result, user_info = show_auth_dialog(self.root)
        
        if auth_result:
            # Закрываем приветственное окно
            self.root.destroy()
            
            # Открываем окно выбора проекта
            project_window = ProjectSelectionWindow(user_info)
            project_window.run()
        else:
            # Пользователь отменил аутентификацию
            messagebox.showinfo("Информация", "Для работы с программой необходима аутентификация")
        
    def run(self):
        """Запуск приветственного окна"""
        self.root.mainloop()


class ProjectSelectionWindow:
    """Окно выбора проекта"""
    
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
        self.root.title("🏗️ Выбор проекта")
        
        # Получаем размер экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Устанавливаем размер окна больше половины экрана
        window_width = min(900, screen_width * 2 // 3)
        window_height = min(750, screen_height * 2 // 3)
        
        # Центрируем окно
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)  # Разрешаем изменение размера
        
        # Устанавливаем минимальную высоту окна, чтобы кнопки всегда были видны
        self.root.minsize(window_width, 800)
        
        # Файловый менеджер
        self.file_manager = WindowsFileManager()
        
        # API клиент для работы с проектами и объектами
        self.project_api_client = None
        try:
            from adapters.project_api_client import get_project_api_client
            from adapters.auth_client import auth_client
            self.project_api_client = get_project_api_client(auth_client)
        except Exception as e:
            print(f"Не удалось инициализировать API клиент: {e}")
        
        # Результат выбора
        self.selected_project = None
        self.create_new_project = False
        
        # Настройка стилей
        self.setup_styles()
        
        # Создание интерфейса
        self.setup_ui()
        
    def setup_styles(self):
        """Настройка современных стилей в стиле iOS"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # iOS-стиль токены (на основе текущей палитры)
        self.tokens = {
            '--bg': '#f5f5f5',           # Общий фон экрана (светлый)
            '--card': '#ffffff',         # Фон карточек (белый)
            '--text': '#212121',         # Основной текст
            '--muted': '#757575',        # Вторичный текст/подписи
            '--primary': '#1e88e5',      # Синий (текущий)
            '--border': '#e0e0e0',       # Серый бордер/разделители
            '--focus': '#1e88e5'         # Primary с прозрачностью для фокуса
        }
        
        # iOS-стиль иконки (SF Symbols стиль, 16-20px)
        self.icons = {
            'add': '➕',           # Добавить
            'settings': '⚙️',     # Настройки
            'sync': '☁️',         # Синхронизация
            'folder': '📁',       # Папка/проект
            'rocket': '🚀',       # Продолжить
            'logout': '🚪',       # Выйти
            'search': '🔍',       # Поиск
            'manage': '⚙️',       # Управление
            'hint': '💡',         # Подсказка
            'empty': '📂'         # Пустое состояние
        }
        
        # Дополнительные цвета для состояний
        primary_color = self.tokens['--primary']
        primary_hover = '#1976d2'       # Темно-синий при наведении
        secondary_color = '#64b5f6'    # Светло-синий
        secondary_hover = '#42a5f5'    # Светло-синий при наведении
        background_color = self.tokens['--bg']
        surface_color = self.tokens['--card']
        text_primary = self.tokens['--text']
        text_secondary = self.tokens['--muted']
        border_color = self.tokens['--border']
        
        # iOS-стиль шрифты и размеры
        style.configure('LargeTitle.TLabel', 
                       font=('Segoe UI', 28, 'bold'),  # LargeTitle: 28px semibold
                       foreground=text_primary,
                       background=background_color)
        
        style.configure('H2.TLabel',
                       font=('Segoe UI', 17, 'bold'),  # H2 секций: 17px semibold
                       foreground=text_primary,
                       background=background_color)
        
        style.configure('Body.TLabel',
                       font=('Segoe UI', 15),         # Текст/плейсхолдеры: 15px
                       foreground=text_primary,
                       background=background_color)
        
        style.configure('Muted.TLabel',
                       font=('Segoe UI', 15),         # Вторичный текст: 15px
                       foreground=text_secondary,
                       background=background_color)
        
        # Старые стили для совместимости
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 18, 'bold'),
                       foreground=text_primary,
                       background=background_color)
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 13),
                       foreground=text_secondary,
                       background=background_color)
        
        # iOS-стиль кнопки (компактные)
        style.configure('Primary.TButton',
                       font=('Segoe UI', 13, 'bold'),  # Уменьшенный шрифт
                       padding=(12, 8),               # Уменьшенные отступы
                       relief='flat',
                       borderwidth=0,
                       background=primary_color,
                       foreground='white')
        
        style.map('Primary.TButton',
                 background=[('active', primary_hover), ('!active', primary_color)],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        # Secondary кнопки (компактные)
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 13),
                       padding=(12, 8),
                       relief='flat',
                       borderwidth=1,
                       background=surface_color,
                       foreground=text_primary,
                       bordercolor=border_color)
        
        style.map('Secondary.TButton',
                 background=[('active', '#f0f0f0'), ('!active', surface_color)],
                 foreground=[('active', text_primary), ('!active', text_primary)])
        
        # Ghost кнопки (компактные)
        style.configure('Ghost.TButton',
                       font=('Segoe UI', 13),
                       padding=(12, 8),
                       relief='flat',
                       borderwidth=0,
                       background=background_color,
                       foreground=text_secondary)
        
        style.map('Ghost.TButton',
                 background=[('active', '#f0f0f0'), ('!active', background_color)],
                 foreground=[('active', text_primary), ('!active', text_secondary)])
        
        # Старые стили для совместимости
        style.configure('Modern.TButton',
                       font=('Segoe UI', 12, 'bold'),
                       padding=(24, 12),
                       relief='flat',
                       borderwidth=0,
                       background=primary_color,
                       foreground='white')
        
        style.map('Modern.TButton',
                 background=[('active', primary_hover), ('!active', primary_color)],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        # iOS-стиль фреймы и карточки
        style.configure('Card.TFrame',
                       background=surface_color,      # --card (белый)
                       relief='flat',
                       borderwidth=1,
                       bordercolor=border_color)      # --border
        
        style.configure('Project.TFrame',
                       background=background_color,    # --bg (светлый фон)
                       relief='flat',
                       borderwidth=0)
        
        style.configure('Project.TLabel',
                       font=('Segoe UI', 11),
                       background=background_color,
                       foreground=text_primary)
        
        # iOS-стиль LabelFrame (карточки)
        style.configure('Card.TLabelframe',
                       background=surface_color,       # --card
                       relief='flat',
                       borderwidth=1,
                       bordercolor=border_color)       # --border
        
        style.configure('Card.TLabelframe.Label',
                       font=('Segoe UI', 17, 'bold'), # H2: 17px semibold
                       foreground=text_primary,
                       background=surface_color)
        
        # Старые стили для совместимости
        style.configure('TLabelframe',
                       background=background_color,
                       relief='flat',
                       borderwidth=1,
                       bordercolor=border_color)
        
        style.configure('TLabelframe.Label',
                       font=('Segoe UI', 12, 'bold'),
                       foreground=text_primary,
                       background=background_color)
        
        # iOS-стиль поля ввода (высота 44px, радиус 12px)
        style.configure('iOS.TEntry',
                       font=('Segoe UI', 15),          # 15px для полей ввода
                       fieldbackground=surface_color, # --card
                       borderwidth=1,
                       relief='flat',
                       bordercolor=border_color)       # --border
        
        style.map('iOS.TEntry',
                 bordercolor=[('focus', primary_color), ('!focus', border_color)],
                 fieldbackground=[('focus', surface_color), ('!focus', surface_color)])
        
        # iOS-стиль Combobox
        style.configure('iOS.TCombobox',
                       font=('Segoe UI', 15),
                       background=surface_color,
                       fieldbackground=surface_color,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=border_color)
        
        style.map('iOS.TCombobox',
                 fieldbackground=[('readonly', surface_color)],
                 selectbackground=[('readonly', primary_color)],
                 selectforeground=[('readonly', 'white')],
                 bordercolor=[('focus', primary_color), ('!focus', border_color)])
        
        # iOS-стиль Treeview (как iOS-список)
        style.configure('iOS.Treeview',
                       font=('Segoe UI', 15),          # 15px для списков
                       background=surface_color,       # --card
                       foreground=text_primary,       # --text
                       fieldbackground=surface_color,
                       borderwidth=0,                  # Без бордера
                       relief='flat')
        
        style.configure('iOS.Treeview.Heading',
                       font=('Segoe UI', 15, 'bold'), # 15px полужирный
                       background=surface_color,        # --card
                       foreground=text_secondary,      # --muted
                       relief='flat',
                       borderwidth=0)
        
        style.map('iOS.Treeview',
                 background=[('selected', '#f0f0f0'), ('!selected', surface_color)],  # Деликатная подсветка
                 foreground=[('selected', text_primary), ('!selected', text_primary)])
        
        # iOS-стиль скроллбары (overlay/автоскрытие)
        style.configure('iOS.Vertical.TScrollbar',
                       background='#c0c0c0',           # Серый для overlay
                       bordercolor='#c0c0c0',
                       arrowcolor=text_secondary,
                       troughcolor='transparent',       # Прозрачный фон
                       width=8,                         # Уже скроллбар
                       relief='flat')
        
        style.map('iOS.Vertical.TScrollbar',
                 background=[('active', '#a0a0a0'), ('!active', '#c0c0c0')],
                 arrowcolor=[('active', text_primary), ('!active', text_secondary)])
        
        # Старые стили для совместимости
        # Combobox стили
        style.configure('TCombobox',
                       font=('Segoe UI', 11),
                       background=surface_color,
                       fieldbackground=surface_color,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=border_color)
        
        style.map('TCombobox',
                 fieldbackground=[('readonly', surface_color)],
                 selectbackground=[('readonly', primary_color)],
                 selectforeground=[('readonly', 'white')])
        
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
        
    def setup_ui(self):
        """Создание пользовательского интерфейса в стиле iOS"""
        # Основной контейнер
        main_frame = ttk.Frame(self.root, style='Project.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)  # Отступы 24px
        
        # Заголовок (iOS LargeTitle)
        title_label = ttk.Label(
            main_frame,
            text="Выберите проект",
            style='LargeTitle.TLabel'
        )
        title_label.pack(pady=(0, 8))
        
        # Информация о пользователе
        if self.user_info:
            user_name = self.user_info.get('name') or self.user_info.get('email', 'Пользователь')
            user_label = ttk.Label(
                main_frame,
                text=f"Добро пожаловать, {user_name}!",
                style='Muted.TLabel'
            )
            user_label.pack(pady=(0, 4))
        
        # Подзаголовок (вторичным цветом)
        subtitle_label = ttk.Label(
            main_frame,
            text="Выберите существующий проект или создайте новый",
            style='Muted.TLabel'
        )
        subtitle_label.pack(pady=(0, 24))
        
        # Горизонтальная структура (сверху проекты, снизу объекты)
        layout_frame = ttk.Frame(main_frame, style='Project.TFrame')
        layout_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Верхняя секция - Проекты (меньше пространства)
        projects_card = ttk.LabelFrame(layout_frame, text="Проекты", style='Card.TLabelframe', padding=16)
        projects_card.pack(fill=tk.X, pady=(0, 16))  # Отступ снизу 16px
        
        # Горизонтальная компоновка проектов
        projects_content_frame = ttk.Frame(projects_card, style='Card.TFrame')
        projects_content_frame.pack(fill=tk.X)
        
        # Левая часть - таблица проектов
        left_projects_frame = ttk.Frame(projects_content_frame, style='Card.TFrame')
        left_projects_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 16))
        
        # Создаем таблицу проектов (iOS-стиль)
        projects_table_frame = ttk.Frame(left_projects_frame, style='Card.TFrame')
        projects_table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем Treeview для проектов
        columns = ('name', 'count')
        self.projects_tree = ttk.Treeview(
            projects_table_frame,
            columns=columns,
            show='headings',
            style='iOS.Treeview'
        )
        
        # Настройка колонок
        self.projects_tree.heading('name', text='Название проекта')
        self.projects_tree.heading('count', text='Количество объектов')
        
        # Настройка ширины колонок (выравнивание с таблицей объектов)
        self.projects_tree.column('name', width=200, anchor='w')
        self.projects_tree.column('count', width=120, anchor='e')  # Выравнивание вправо для чисел
        
        # Скроллбар для таблицы проектов
        projects_scrollbar = ttk.Scrollbar(projects_table_frame, orient=tk.VERTICAL, command=self.projects_tree.yview, style='iOS.Vertical.TScrollbar')
        self.projects_tree.configure(yscrollcommand=projects_scrollbar.set)
        
        # Размещение таблицы проектов
        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        projects_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Переменная для хранения выбранного проекта
        self.project_var = tk.StringVar(value="Основной проект")
        
        # Правая часть - кнопки управления проектами (вертикально)
        buttons_frame = ttk.Frame(projects_content_frame, style='Card.TFrame')
        buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Primary кнопка "Добавить проект" (компактная)
        add_project_button = ttk.Button(
            buttons_frame,
            text=f"{self.icons['add']} Добавить",
            style='Primary.TButton',
            command=self.add_new_project_global
        )
        add_project_button.pack(fill=tk.X, pady=(0, 8))
        
        # Кнопка "Удалить проект" (компактная)
        delete_project_button = ttk.Button(
            buttons_frame,
            text=f"❌ Удалить",
            style='Secondary.TButton',
            command=self.delete_selected_project
        )
        delete_project_button.pack(fill=tk.X, pady=(0, 8))
        
        # Secondary кнопка "Синхронизировать" (компактная)
        sync_projects_button = ttk.Button(
            buttons_frame,
            text=f"{self.icons['sync']} Синхронизировать",
            style='Secondary.TButton',
            command=self.sync_projects_from_server
        )
        sync_projects_button.pack(fill=tk.X)
        
        # Переменная для хранения выбранного проекта
        self.project_var = tk.StringVar(value="Основной проект")
        
        # Обработчик выбора проекта из таблицы
        self.projects_tree.bind('<<TreeviewSelect>>', self.on_project_tree_select)
        self.projects_tree.bind('<Double-1>', self.on_project_tree_double_click)
        
        # Нижняя секция - Объекты (больше пространства)
        objects_card = ttk.LabelFrame(layout_frame, text="Объекты", style='Card.TLabelframe', padding=20)
        objects_card.pack(fill=tk.X, pady=(0, 0))
        
        # Горизонтальная компоновка объектов
        objects_content_frame = ttk.Frame(objects_card, style='Card.TFrame')
        objects_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая часть - таблица объектов
        objects_table_frame = ttk.Frame(objects_content_frame, style='Card.TFrame')
        objects_table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 16))
        
        # Правая часть - кнопки управления объектами (вертикально)
        objects_buttons_frame = ttk.Frame(objects_content_frame, style='Card.TFrame')
        objects_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Primary кнопка "Добавить объект" (компактная)
        self.add_object_button = ttk.Button(
            objects_buttons_frame,
            text=f"{self.icons['add']} Добавить",
            style='Primary.TButton',
            command=self.add_new_object
        )
        self.add_object_button.pack(fill=tk.X, pady=(0, 8))
        
        # Secondary кнопка "Удалить объект" (компактная)
        self.delete_object_button = ttk.Button(
            objects_buttons_frame,
            text=f"❌ Удалить",
            style='Secondary.TButton',
            command=self.delete_selected_object
        )
        self.delete_object_button.pack(fill=tk.X)
        
        
        # Создаем таблицу объектов
        columns = ('name', 'wear', 'last_date')
        self.objects_tree = ttk.Treeview(
            objects_table_frame,
            columns=columns,
            show='headings',
            style='iOS.Treeview'
        )
        
        # Настройка колонок (iOS-стиль заголовки)
        self.objects_tree.heading('name', text='Название')
        self.objects_tree.heading('wear', text='Износ')
        self.objects_tree.heading('last_date', text='Изменён')
        
        # Настройка ширины колонок (выравнивание с таблицей проектов)
        self.objects_tree.column('name', width=200, anchor='w')
        self.objects_tree.column('wear', width=120, anchor='e')  # Выравнивание вправо для чисел
        self.objects_tree.column('last_date', width=120, anchor='e')  # Выравнивание вправо для дат
        
        # Скроллбар (iOS-стиль)
        scrollbar = ttk.Scrollbar(objects_table_frame, orient=tk.VERTICAL, command=self.objects_tree.yview, style='iOS.Vertical.TScrollbar')
        self.objects_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение с ограниченной высотой
        self.objects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Ограничиваем высоту таблицы объектов
        self.objects_tree.configure(height=8)
        
        # Обработчик выбора
        self.objects_tree.bind('<<TreeviewSelect>>', self.on_project_select)
        
        # Обработчик двойного клика для быстрого перехода
        self.objects_tree.bind('<Double-1>', self.on_double_click)
        
        # Обработчик клавиши Enter для перехода
        self.objects_tree.bind('<Return>', self.on_enter_press)
        
        # Обработчик клавиши Enter для всего окна
        self.root.bind('<Return>', self.on_enter_press)
        
        # Клавиатурная навигация для доступности
        self.root.bind('<Tab>', self.on_tab_navigation)
        self.root.bind('<Shift-Tab>', self.on_shift_tab_navigation)
        self.root.bind('<Up>', self.on_arrow_navigation)
        self.root.bind('<Down>', self.on_arrow_navigation)
        self.root.bind('<Left>', self.on_arrow_navigation)
        self.root.bind('<Right>', self.on_arrow_navigation)
        
        # Устанавливаем фокус на таблицу проектов
        self.projects_tree.focus_set()
        
        # Нижняя панель с кнопками действий (зафиксирована внизу)
        bottom_frame = ttk.Frame(main_frame, style='Project.TFrame')
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        # Кнопка "Продолжить" (Primary)
        self.continue_btn = ttk.Button(
            bottom_frame,
            text=f"{self.icons['rocket']} Продолжить",
            style='Primary.TButton',
            command=self.continue_to_main,
            state="disabled"  # Изначально неактивна
        )
        self.continue_btn.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Подсказка для пользователя
        hint_label = ttk.Label(
            bottom_frame,
            text=f"{self.icons['hint']} Выберите объект и нажмите 'Продолжить', или дважды кликните по объекту",
            style='Muted.TLabel',
            justify=tk.LEFT
        )
        hint_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Кнопка выхода из системы (Ghost)
        if self.user_info:
            logout_button = ttk.Button(
                bottom_frame,
                text=f"{self.icons['logout']} Выйти из системы",
                style='Ghost.TButton',
                command=self.logout
            )
            logout_button.pack(side=tk.RIGHT, padx=(0, 16))
        
        # Инициализируем список проектов
        self.update_projects_list()
        
        # Инициализируем список объектов для текущего проекта (после создания кнопки)
        self.update_objects_list(self.project_var.get())
        
        # Автоматическая синхронизация при загрузке (в фоновом режиме)
        self.auto_sync_projects()
        
        # Отладочная информация
        print(f"Кнопка 'Продолжить' создана: {self.continue_btn}")
        print(f"Размер окна: {self.root.winfo_width()}x{self.root.winfo_height()}")
        print(f"Кнопка видима: {self.continue_btn.winfo_viewable()}")
        print(f"Кнопка размещена: {self.continue_btn.winfo_geometry()}")
        
        # Принудительно обновляем отображение
        self.root.update_idletasks()
    
    def delete_selected_project(self):
        """Удаление выбранного проекта с подтверждением"""
        try:
            # Получаем выбранный проект
            selection = self.projects_tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите проект для удаления")
                return
            
            item = self.projects_tree.item(selection[0])
            project_name = item['values'][0]
            
            # Показываем диалог подтверждения
            result = messagebox.askyesno(
                "Подтверждение удаления",
                f"Вы точно хотите удалить проект '{project_name}'?",
                icon='warning'
            )
            
            if result:
                # Удаляем проект локально
                local_success = self.file_manager.remove_global_project(project_name)
                
                # Удаляем проект на сервере
                server_success = False
                try:
                    from adapters.project_api_client import get_project_api_client
                    from adapters.auth_client import auth_client
                    
                    if auth_client.is_authenticated():
                        project_client = get_project_api_client(auth_client)
                        
                        # Находим ID проекта на сервере
                        projects_result = project_client.get_projects()
                        if projects_result.get('success'):
                            projects = projects_result.get('projects', [])
                            project_id = None
                            for project in projects:
                                if project.get('name') == project_name:
                                    project_id = project.get('id')
                                    break
                            
                            if project_id:
                                delete_result = project_client.delete_project(project_id)
                                if delete_result.get('success'):
                                    server_success = True
                except Exception as e:
                    print(f"Ошибка удаления проекта с сервера: {e}")
                
                if local_success:
                    # Обновляем список проектов
                    self.update_projects_list()
                    
                    # Если удаленный проект был выбран, выбираем первый доступный
                    remaining_projects = self.file_manager.get_global_projects()
                    if remaining_projects:
                        self.project_var.set(remaining_projects[0])
                        self.update_objects_list(remaining_projects[0])
                    else:
                        self.project_var.set("Основной проект")
                        self.update_objects_list("Основной проект")
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить проект")
                    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка удаления проекта: {str(e)}")
    
    def delete_selected_object(self):
        """Удаление выбранного объекта с подтверждением"""
        try:
            # Получаем выбранный объект
            selection = self.objects_tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите объект для удаления")
                return
            
            item = self.objects_tree.item(selection[0])
            object_name = item['values'][0]
            
            # Показываем диалог подтверждения
            result = messagebox.askyesno(
                "Подтверждение удаления",
                f"Вы точно хотите удалить объект '{object_name}'?",
                icon='warning'
            )
            
            if result:
                current_project = self.project_var.get()
                
                # Удаляем объект через API
                api_success = False
                if self.project_api_client and self.user_info:
                    try:
                        # Находим ID проекта по имени
                        projects_result = self.project_api_client.get_projects()
                        if projects_result.get('success'):
                            projects = projects_result.get('projects', [])
                            project_id = None
                            for project in projects:
                                if project.get('name') == current_project:
                                    project_id = project.get('id')
                                    break
                            
                            if project_id:
                                # Получаем объекты проекта чтобы найти ID объекта
                                objects_result = self.project_api_client.get_objects_by_project(project_id)
                                if objects_result.get('success'):
                                    api_objects = objects_result.get('objects', [])
                                    object_id = None
                                    for obj in api_objects:
                                        if obj.get('name') == object_name:
                                            object_id = obj.get('id')
                                            break
                                    
                                    if object_id:
                                        # Удаляем объект через API
                                        delete_result = self.project_api_client.delete_object(object_id)
                                        if delete_result.get('success'):
                                            api_success = True
                    except Exception as e:
                        print(f"Ошибка удаления объекта через API: {e}")
                
                # Удаляем локальный объект
                local_success = self.file_manager.remove_object_from_project(current_project, object_name)
                
                if api_success or local_success:
                    # Обновляем список объектов
                    self.update_objects_list(current_project)
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить объект")
                    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка удаления объекта: {str(e)}")
    
    def on_tab_navigation(self, event):
        """Обработчик Tab для навигации"""
        # Получаем текущий фокус
        current_focus = self.root.focus_get()
        
        # Определяем следующий элемент для фокуса
        if current_focus == self.projects_tree:
            self.objects_tree.focus_set()
        elif current_focus == self.objects_tree:
            self.continue_btn.focus_set()
        else:
            # Возвращаемся к началу
            self.projects_tree.focus_set()
        
        return "break"  # Предотвращаем стандартное поведение Tab
    
    def on_shift_tab_navigation(self, event):
        """Обработчик Shift+Tab для обратной навигации"""
        current_focus = self.root.focus_get()
        
        # Обратная навигация
        if current_focus == self.projects_tree:
            self.continue_btn.focus_set()
        elif current_focus == self.objects_tree:
            self.projects_tree.focus_set()
        else:
            self.objects_tree.focus_set()
        
        return "break"
    
    def on_arrow_navigation(self, event):
        """Обработчик стрелок для навигации по спискам"""
        current_focus = self.root.focus_get()
        
        if current_focus == self.projects_tree:
            # Навигация по таблице проектов
            if event.keysym == 'Up':
                current_selection = self.projects_tree.selection()
                if current_selection:
                    prev_item = self.projects_tree.prev(current_selection[0])
                    if prev_item:
                        self.projects_tree.selection_clear()
                        self.projects_tree.selection_set(prev_item)
                        self.projects_tree.see(prev_item)
            elif event.keysym == 'Down':
                current_selection = self.projects_tree.selection()
                if current_selection:
                    next_item = self.projects_tree.next(current_selection[0])
                    if next_item:
                        self.projects_tree.selection_clear()
                        self.projects_tree.selection_set(next_item)
                        self.projects_tree.see(next_item)
            
            # Обновляем выбранный проект
            self.on_project_tree_select(None)
            return "break"
        
        elif current_focus == self.objects_tree:
            # Навигация по таблице объектов
            if event.keysym == 'Up':
                current_selection = self.objects_tree.selection()
                if current_selection:
                    prev_item = self.objects_tree.prev(current_selection[0])
                    if prev_item:
                        self.objects_tree.selection_clear()
                        self.objects_tree.selection_set(prev_item)
                        self.objects_tree.see(prev_item)
            elif event.keysym == 'Down':
                current_selection = self.objects_tree.selection()
                if current_selection:
                    next_item = self.objects_tree.next(current_selection[0])
                    if next_item:
                        self.objects_tree.selection_clear()
                        self.objects_tree.selection_set(next_item)
                        self.objects_tree.see(next_item)
            
            # Обновляем выбранный объект
            self.on_project_select(None)
            return "break"
        
    def on_project_select(self, event):
        """Обработчик выбора объекта"""
        # Получаем выбранный объект из таблицы
        selection = self.objects_tree.selection()
        if selection:
            # Получаем данные выбранного объекта
            item = self.objects_tree.item(selection[0])
            object_name = item['values'][0]  # Название объекта
            
            # Устанавливаем выбранный объект
            self.selected_project = object_name
            # Активируем кнопку "Продолжить"
            self.continue_btn.config(state="normal")
            print(f"Выбран объект: {object_name}, кнопка активирована")
        else:
            self.selected_project = None
            self.continue_btn.config(state="disabled")
            print("Объект не выбран, кнопка деактивирована")
    
    def on_double_click(self, event):
        """Обработчик двойного клика по объекту"""
        selection = self.objects_tree.selection()
        if selection:
            # Получаем данные выбранного объекта
            item = self.objects_tree.item(selection[0])
            object_name = item['values'][0]  # Название объекта
            
            # Устанавливаем выбранный объект и переходим к главному окну
            self.selected_project = object_name
            self.continue_to_main()
    
    def on_enter_press(self, event):
        """Обработчик нажатия клавиши Enter"""
        if self.selected_project and self.continue_btn.cget('state') == 'normal':
            self.continue_to_main()
            
    def add_new_project_global(self):
        """Добавление нового глобального проекта"""
        try:
            # Создаем диалоговое окно для ввода информации о проекте
            dialog = tk.Toplevel(self.root)
            dialog.title("Добавить новый проект")
            dialog.geometry("500x300")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Центрируем окно
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (300 // 2)
            dialog.geometry(f"500x300+{x}+{y}")
            
            # Содержимое диалога
            main_frame = ttk.Frame(dialog, padding=24)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Заголовок секции
            section_label = ttk.Label(main_frame, text="ИНФОРМАЦИЯ О ПРОЕКТЕ", style='Muted.TLabel')
            section_label.pack(anchor=tk.W, pady=(0, 16))
            
            # Карточка с полями ввода
            input_card = ttk.Frame(main_frame, style='Card.TFrame')
            input_card.pack(fill=tk.X, pady=(0, 20))
            
            # Поле названия проекта
            name_frame = ttk.Frame(input_card, style='Card.TFrame')
            name_frame.pack(fill=tk.X, padx=16, pady=16)
            
            project_var = tk.StringVar()
            project_entry = ClipboardEntry(
                name_frame, 
                textvariable=project_var, 
                font=('Segoe UI', 15)
            )
            project_entry.pack(fill=tk.X, ipady=8)
            project_entry.insert(0, "Название проекта")
            project_entry.configure(foreground=self.tokens['--muted'])
            project_entry.focus()
            
            # Разделитель
            separator = ttk.Frame(input_card, height=1, style='Card.TFrame')
            separator.pack(fill=tk.X, padx=16)
            separator.configure(background=self.tokens['--border'])
            
            # Поле описания
            desc_frame = ttk.Frame(input_card, style='Card.TFrame')
            desc_frame.pack(fill=tk.X, padx=16, pady=16)
            
            desc_var = tk.StringVar()
            desc_entry = ClipboardEntry(
                desc_frame, 
                textvariable=desc_var, 
                font=('Segoe UI', 15)
            )
            desc_entry.pack(fill=tk.X, ipady=8)
            desc_entry.insert(0, "Описание (необязательно)")
            desc_entry.configure(foreground=self.tokens['--muted'])
            
            # Обработчики фокуса для плейсхолдеров
            def on_name_focus_in(event):
                if project_entry.get() == "Название проекта":
                    project_entry.delete(0, tk.END)
                    project_entry.configure(foreground=self.tokens['--text'])
            
            def on_name_focus_out(event):
                if not project_entry.get():
                    project_entry.insert(0, "Название проекта")
                    project_entry.configure(foreground=self.tokens['--muted'])
            
            def on_desc_focus_in(event):
                if desc_entry.get() == "Описание (необязательно)":
                    desc_entry.delete(0, tk.END)
                    desc_entry.configure(foreground=self.tokens['--text'])
            
            def on_desc_focus_out(event):
                if not desc_entry.get():
                    desc_entry.insert(0, "Описание (необязательно)")
                    desc_entry.configure(foreground=self.tokens['--muted'])
            
            project_entry.bind('<FocusIn>', on_name_focus_in)
            project_entry.bind('<FocusOut>', on_name_focus_out)
            desc_entry.bind('<FocusIn>', on_desc_focus_in)
            desc_entry.bind('<FocusOut>', on_desc_focus_out)
            
            # Кнопки
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack()
            
            def save_project():
                project_name = project_var.get().strip()
                project_desc = desc_var.get().strip()
                
                if project_name and project_name != "Название проекта":
                    # Создаем проект локально
                    local_success = self.file_manager.add_global_project(project_name)
                    
                    # Создаем проект на сервере
                    server_success = False
                    try:
                        from adapters.project_api_client import get_project_api_client
                        from adapters.auth_client import auth_client
                        
                        if auth_client.is_authenticated():
                            project_client = get_project_api_client(auth_client)
                            result = project_client.create_project(project_name, project_desc)
                            if result.get('success'):
                                server_success = True
                    except Exception as e:
                        print(f"Ошибка создания проекта на сервере: {e}")
                    
                    if local_success:
                        # Обновляем список проектов
                        self.update_projects_list()
                        self.project_var.set(project_name)
                        self.update_objects_list(project_name)
                    else:
                        messagebox.showwarning("Предупреждение", "Такой проект уже существует")
                    
                    dialog.destroy()
                else:
                    messagebox.showwarning("Предупреждение", "Введите название проекта")
            
            def cancel():
                dialog.destroy()
            
            # Кнопки
            ttk.Button(buttons_frame, text="Сохранить", style='Primary.TButton', command=save_project).pack(side=tk.RIGHT, padx=(8, 0))
            ttk.Button(buttons_frame, text="Отмена", style='Secondary.TButton', command=cancel).pack(side=tk.RIGHT)
            
            # Обработка Enter и Escape
            project_entry.bind('<Return>', lambda e: save_project())
            desc_entry.bind('<Return>', lambda e: save_project())
            dialog.bind('<Escape>', lambda e: cancel())
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка добавления проекта: {str(e)}")
            
    def manage_global_projects(self):
        """Управление глобальными проектами"""
        try:
            # Создаем диалог управления проектами
            dialog = tk.Toplevel(self.root)
            dialog.title("Управление проектами")
            dialog.geometry("500x400")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Центрируем окно
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"500x400+{x}+{y}")
            
            # Содержимое диалога
            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Заголовок
            title_label = ttk.Label(main_frame, text="Управление глобальными проектами", style='Title.TLabel')
            title_label.pack(pady=(0, 20))
            
            # Список проектов
            projects_frame = ttk.LabelFrame(main_frame, text="Список проектов", padding=15)
            projects_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            # Получаем текущие проекты
            current_projects = self.file_manager.get_global_projects()
            
            # Создаем список проектов
            projects_listbox = tk.Listbox(
                projects_frame,
                font=('Segoe UI', 11),
                selectmode=tk.SINGLE,
                relief='flat',
                borderwidth=1
            )
            
            # Добавляем проекты в список
            for project in current_projects:
                projects_listbox.insert(tk.END, project)
            
            # Скроллбар
            scrollbar = ttk.Scrollbar(projects_frame, orient=tk.VERTICAL, command=projects_listbox.yview)
            projects_listbox.configure(yscrollcommand=scrollbar.set)
            
            # Размещение
            projects_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Кнопки управления
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill=tk.X)
            
            def delete_project():
                selection = projects_listbox.curselection()
                if selection:
                    index = selection[0]
                    project_name = projects_listbox.get(index)
                    
                    # Автоматически удаляем проект
                    if True:
                        # Удаляем проект локально
                        local_success = self.file_manager.remove_global_project(project_name)
                        
                        # Удаляем проект на сервере
                        server_success = False
                        server_message = ""
                        
                        try:
                            from adapters.project_api_client import get_project_api_client
                            from adapters.auth_client import auth_client
                            
                            if auth_client.is_authenticated():
                                project_client = get_project_api_client(auth_client)
                                
                                # Находим ID проекта на сервере
                                result = project_client.get_projects()
                                if result.get('success'):
                                    projects = result.get('projects', [])
                                    project_id = None
                                    for project in projects:
                                        if project.get('name') == project_name:
                                            project_id = project.get('id')
                                            break
                                    
                                    if project_id:
                                        delete_result = project_client.delete_project(project_id)
                                        if delete_result.get('success'):
                                            server_success = True
                                            server_message = " и удален с сервера"
                                        else:
                                            server_message = f" (ошибка удаления с сервера: {delete_result.get('error', 'неизвестная ошибка')})"
                                    else:
                                        server_message = " (проект не найден на сервере)"
                                else:
                                    server_message = f" (ошибка получения списка проектов: {result.get('error', 'неизвестная ошибка')})"
                            else:
                                server_message = " (синхронизация недоступна - не авторизован)"
                                
                        except Exception as e:
                            server_message = f" (ошибка синхронизации: {str(e)})"
                        
                        if local_success:
                            # Удаляем из списка
                            projects_listbox.delete(index)
                            # Обновляем список проектов
                            self.update_projects_list()
                            
                            # Если удаленный проект был выбран, выбираем первый
                            if self.project_var.get() == project_name:
                                remaining_projects = self.file_manager.get_global_projects()
                                if remaining_projects:
                                    self.project_var.set(remaining_projects[0])
                                else:
                                    self.project_var.set("Основной проект")
                            
                            # Успешное удаление не требует диалога
                            pass
                        else:
                            messagebox.showerror("Ошибка", "Не удалось удалить проект")
                else:
                    messagebox.showwarning("Предупреждение", "Выберите проект для удаления")
            
            def close_dialog():
                dialog.destroy()
            
            # Кнопки
            ttk.Button(buttons_frame, text="🗑️ Удалить проект", style='Secondary.TButton', command=delete_project).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(buttons_frame, text="Закрыть", style='Modern.TButton', command=close_dialog).pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка управления проектами: {str(e)}")
            
    
    def continue_to_main(self):
        """Переход к главному окну"""
        if self.selected_project:
            # Устанавливаем выбранный проект
            self.file_manager.set_current_project(self.selected_project)
            
            # Закрываем окно выбора проекта
            self.root.destroy()
            
            # Открываем главное окно
            try:
                from ui.modern_main_window import ModernDefectAnalyzerWindow
                main_app = ModernDefectAnalyzerWindow(self.user_info)
                main_app.run()
            except Exception as e:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Ошибка", f"Не удалось запустить приложение: {str(e)}")
        else:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите проект или создайте новый")
    
    def update_projects_list(self):
        """Обновление таблицы проектов"""
        # Очищаем текущую таблицу
        if hasattr(self, 'projects_tree'):
            for item in self.projects_tree.get_children():
                self.projects_tree.delete(item)
        
        # Получаем список проектов
        projects = self.file_manager.get_global_projects()
        
        # Добавляем проекты в таблицу с подсчетом объектов
        for project in projects:
            # Подсчитываем количество объектов в проекте
            objects_count = len(self.file_manager.get_objects_for_project(project))
            self.projects_tree.insert('', tk.END, values=(project, objects_count))
        
        # Выбираем первый проект по умолчанию
        if projects:
            first_item = self.projects_tree.get_children()[0]
            self.projects_tree.selection_set(first_item)
            self.project_var.set(projects[0])
            # Активируем кнопку "Продолжить"
            self.continue_btn.config(state="normal")
    
    def on_project_tree_select(self, event):
        """Обработчик выбора проекта из таблицы"""
        selection = self.projects_tree.selection()
        if selection:
            item = self.projects_tree.item(selection[0])
            project_name = item['values'][0]
            self.project_var.set(project_name)
            # Обновляем список объектов для выбранного проекта
            self.update_objects_list(project_name)
            print(f"Выбран проект: {project_name}")
    
    def on_project_tree_double_click(self, event):
        """Обработчик двойного клика по проекту"""
        selection = self.projects_tree.selection()
        if selection:
            item = self.projects_tree.item(selection[0])
            project_name = item['values'][0]
            self.project_var.set(project_name)
            # Обновляем список объектов и переходим к главному окну
            self.update_objects_list(project_name)
            # Если есть объекты, выбираем первый и переходим к главному окну
            if hasattr(self, 'objects_tree'):
                objects = self.file_manager.get_objects_for_project(project_name)
                if objects:
                    self.selected_project = objects[0]
                    self.continue_to_main()
        
    def update_objects_list(self, project_name):
        """Обновление списка объектов для выбранного проекта"""
        # Очищаем текущую таблицу объектов
        if hasattr(self, 'objects_tree'):
            for item in self.objects_tree.get_children():
                self.objects_tree.delete(item)
        
        # Получаем список объектов для выбранного проекта
        objects = []
        
        # Сначала пытаемся получить объекты через API
        if self.project_api_client and self.user_info:
            try:
                # Находим ID проекта по имени
                projects_result = self.project_api_client.get_projects()
                if projects_result.get('success'):
                    projects = projects_result.get('projects', [])
                    project_id = None
                    for project in projects:
                        if project.get('name') == project_name:
                            project_id = project.get('id')
                            break
                    
                    if project_id:
                        # Получаем объекты проекта через API
                        objects_result = self.project_api_client.get_objects_by_project(project_id)
                        if objects_result.get('success'):
                            api_objects = objects_result.get('objects', [])
                            objects = [obj.get('name') for obj in api_objects]
                            
                            # Синхронизируем локальные объекты с серверными
                            local_objects = self.file_manager.get_objects_for_project(project_name)
                            for obj_name in objects:
                                if obj_name not in local_objects:
                                    self.file_manager.add_object_to_project(project_name, obj_name)
                        else:
                            print(f"Ошибка получения объектов через API: {objects_result.get('error')}")
                            # Fallback к локальным объектам
                            objects = self.file_manager.get_objects_for_project(project_name)
                    else:
                        print(f"Проект '{project_name}' не найден на сервере")
                        # Fallback к локальным объектам
                        objects = self.file_manager.get_objects_for_project(project_name)
                else:
                    print(f"Ошибка получения проектов через API: {projects_result.get('error')}")
                    # Fallback к локальным объектам
                    objects = self.file_manager.get_objects_for_project(project_name)
            except Exception as e:
                print(f"Ошибка при работе с API: {e}")
                # Fallback к локальным объектам
                objects = self.file_manager.get_objects_for_project(project_name)
        else:
            # Если API недоступен, используем локальные объекты
            objects = self.file_manager.get_objects_for_project(project_name)
        
        if objects:
            # Добавляем объекты в таблицу
            for object_name in objects:
                # Получаем статистику объекта
                try:
                    self.file_manager.set_current_project(object_name)
                    stats = self.file_manager.get_project_stats()
                    wear_info = "Не рассчитан"
                    last_date = "Нет данных"
                    
                    # Пытаемся получить данные о износе
                    try:
                        wear_data = self.file_manager.load_wear_data()
                        if wear_data and 'total_wear' in wear_data:
                            wear_info = f"{wear_data['total_wear']:.1f}%"
                    except:
                        pass
                    
                    # Получаем дату последнего редактирования
                    if stats.get('last_activity'):
                        last_date = stats['last_activity'].strftime("%d.%m.%Y")
                    
                    self.objects_tree.insert('', tk.END, values=(object_name, wear_info, last_date))
                except:
                    self.objects_tree.insert('', tk.END, values=(object_name, "Не рассчитан", "Нет данных"))
            
            # Выбираем первый объект по умолчанию
            if objects:
                first_item = self.objects_tree.get_children()[0]
                self.objects_tree.selection_set(first_item)
                self.selected_project = objects[0]
                # Активируем кнопку "Продолжить"
                self.continue_btn.config(state="normal")
        else:
            # Пустое состояние в iOS-стиле
            self.show_empty_state()
            # Деактивируем кнопку "Продолжить"
            self.continue_btn.config(state="disabled")
    
    def show_empty_state(self):
        """Показать пустое состояние в iOS-стиле"""
        # Очищаем таблицу
        for item in self.objects_tree.get_children():
            self.objects_tree.delete(item)
        
        # Добавляем пустое состояние
        self.objects_tree.insert('', tk.END, values=(f"{self.icons['empty']}", "", ""))  # Иконка пустого состояния
        self.objects_tree.insert('', tk.END, values=("В этом проекте пока нет объектов", "", ""))
        self.objects_tree.insert('', tk.END, values=("", "", ""))  # Пустая строка
        self.objects_tree.insert('', tk.END, values=("Создайте первый объект для начала работы", "", ""))
        
        # Настраиваем стиль для пустого состояния
        for item in self.objects_tree.get_children():
            self.objects_tree.set(item, 'name', '')
            self.objects_tree.set(item, 'wear', '')
            self.objects_tree.set(item, 'last_date', '')
            
    def add_new_object(self):
        """Добавление нового объекта"""
        try:
            dialog = ProjectDialog(self.root, "Создание нового объекта")
            if dialog.result:
                object_name = dialog.result.strip()
                
                if object_name:
                    current_project = self.project_var.get()
                    
                    # Сначала пытаемся создать объект через API
                    api_success = False
                    if self.project_api_client and self.user_info:
                        try:
                            # Находим ID проекта по имени
                            projects_result = self.project_api_client.get_projects()
                            if projects_result.get('success'):
                                projects = projects_result.get('projects', [])
                                project_id = None
                                for project in projects:
                                    if project.get('name') == current_project:
                                        project_id = project.get('id')
                                        break
                                
                                if project_id:
                                    # Создаем объект через API
                                    create_result = self.project_api_client.create_object(
                                        project_id=project_id,
                                        name=object_name
                                    )
                                    if create_result.get('success'):
                                        api_success = True
                                        print(f"Объект '{object_name}' создан через API")
                                    else:
                                        print(f"Ошибка создания объекта через API: {create_result.get('error')}")
                                else:
                                    print(f"Проект '{current_project}' не найден на сервере")
                        except Exception as e:
                            print(f"Ошибка при создании объекта через API: {e}")
                    
                    # Создаем локальный объект
                    local_success = self.file_manager.add_object_to_project(current_project, object_name)
                    
                    if api_success or local_success:
                        self.selected_project = object_name
                        # Обновляем список объектов
                        self.update_objects_list(current_project)
                        # Успешное создание не требует диалога
                    else:
                        messagebox.showerror("Ошибка", "Не удалось создать объект")
                else:
                    messagebox.showwarning("Предупреждение", "Название объекта не может быть пустым")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка создания объекта: {str(e)}")
            
    def manage_objects(self):
        """Управление объектами"""
        try:
            # Создаем диалог управления объектами
            dialog = tk.Toplevel(self.root)
            dialog.title("Управление объектами")
            dialog.geometry("500x400")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Центрируем окно
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"500x400+{x}+{y}")
            
            # Содержимое диалога
            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Заголовок
            title_label = ttk.Label(main_frame, text="Управление объектами", style='Title.TLabel')
            title_label.pack(pady=(0, 20))
            
            # Список объектов
            objects_frame = ttk.LabelFrame(main_frame, text="Список объектов", padding=15)
            objects_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            # Получаем текущие объекты для выбранного проекта
            current_project = self.project_var.get()
            current_objects = self.file_manager.get_objects_for_project(current_project)
            
            # Создаем список объектов
            objects_listbox = tk.Listbox(
                objects_frame,
                font=('Segoe UI', 11),
                selectmode=tk.SINGLE,
                relief='flat',
                borderwidth=1
            )
            
            # Добавляем объекты в список
            for object_name in current_objects:
                objects_listbox.insert(tk.END, object_name)
            
            # Скроллбар
            scrollbar = ttk.Scrollbar(objects_frame, orient=tk.VERTICAL, command=objects_listbox.yview)
            objects_listbox.configure(yscrollcommand=scrollbar.set)
            
            # Размещение
            objects_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Кнопки управления
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill=tk.X)
            
            def delete_object():
                selection = objects_listbox.curselection()
                if selection:
                    index = selection[0]
                    object_name = objects_listbox.get(index)
                    
                    # Сначала пытаемся удалить объект через API
                    api_success = False
                    if self.project_api_client and self.user_info:
                        try:
                            # Находим ID проекта по имени
                            projects_result = self.project_api_client.get_projects()
                            if projects_result.get('success'):
                                projects = projects_result.get('projects', [])
                                project_id = None
                                for project in projects:
                                    if project.get('name') == current_project:
                                        project_id = project.get('id')
                                        break
                                
                                if project_id:
                                    # Получаем объекты проекта чтобы найти ID объекта
                                    objects_result = self.project_api_client.get_objects_by_project(project_id)
                                    if objects_result.get('success'):
                                        api_objects = objects_result.get('objects', [])
                                        object_id = None
                                        for obj in api_objects:
                                            if obj.get('name') == object_name:
                                                object_id = obj.get('id')
                                                break
                                        
                                        if object_id:
                                            # Удаляем объект через API
                                            delete_result = self.project_api_client.delete_object(object_id)
                                            if delete_result.get('success'):
                                                api_success = True
                                                print(f"Объект '{object_name}' удален через API")
                                            else:
                                                print(f"Ошибка удаления объекта через API: {delete_result.get('error')}")
                        except Exception as e:
                            print(f"Ошибка при удалении объекта через API: {e}")
                    
                    # Удаляем локальный объект
                    local_success = self.file_manager.remove_object_from_project(current_project, object_name)
                    
                    if api_success or local_success:
                        # Удаляем из списка
                        objects_listbox.delete(index)
                        # Обновляем список объектов
                        self.update_objects_list(current_project)
                        # Успешное удаление не требует диалога
                    else:
                        messagebox.showerror("Ошибка", "Не удалось удалить объект")
                else:
                    messagebox.showwarning("Предупреждение", "Выберите объект для удаления")
            
            def close_dialog():
                dialog.destroy()
            
            # Кнопки
            ttk.Button(buttons_frame, text="🗑️ Удалить объект", style='Secondary.TButton', command=delete_object).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(buttons_frame, text="Закрыть", style='Modern.TButton', command=close_dialog).pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка управления объектами: {str(e)}")
            
    def create_new_project(self):
        """Создание нового проекта"""
        try:
            dialog = ProjectDialog(self.root, "Создание нового проекта")
            if dialog.result:
                project_name = dialog.result.strip()
                
                if project_name:
                    if self.file_manager.create_new_project(project_name):
                        self.selected_project = project_name
                        messagebox.showinfo("Успех", f"Проект '{project_name}' создан")
                        self.continue_to_main()
                    else:
                        messagebox.showerror("Ошибка", "Не удалось создать проект")
                else:
                    messagebox.showwarning("Предупреждение", "Название проекта не может быть пустым")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка создания проекта: {str(e)}")
                
    def manage_projects(self):
        """Управление проектами"""
        dialog = ProjectManagerDialog(self.root, self.file_manager)
        if dialog.projects_changed:
            # Обновляем список проектов
            self.root.destroy()
            project_window = ProjectSelectionWindow(self.user_info)
            project_window.run()
            
            
    def logout(self):
        """Выход из системы"""
        try:
            from adapters.auth_client import auth_client
            auth_client.logout()
            
            # Закрываем текущее окно
            self.root.destroy()
            
            # Возвращаемся к приветственному окну
            welcome = WelcomeWindow()
            welcome.run()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка выхода из системы: {str(e)}")
    
    def sync_projects_from_server(self):
        """Синхронизация проектов с сервера"""
        print("☁️ Кнопка синхронизации проектов в окне выбора нажата!")
        
        try:
            # Импортируем клиент проектов
            from adapters.project_api_client import get_project_api_client
            from adapters.auth_client import auth_client
            
            print(f"🔐 Статус авторизации: {auth_client.is_authenticated()}")
            
            # Проверяем авторизацию
            if not auth_client.is_authenticated():
                messagebox.showwarning("Предупреждение", "Необходима авторизация для синхронизации проектов")
                return
            
            # Получаем клиент проектов
            project_client = get_project_api_client(auth_client)
            print(f"📡 Клиент проектов создан: {project_client}")
            
            # Получаем проекты с сервера
            result = project_client.get_projects()
            print(f"📥 Результат: {result}")
            
            if result.get('success'):
                projects = result.get('projects', [])
                print(f"✅ Получено проектов: {len(projects)}")
                
                # Получаем текущие локальные проекты
                local_projects = self.file_manager.get_global_projects()
                server_project_names = [project.get('name', '') for project in projects if project.get('name')]
                
                # Создаем локальные проекты на основе серверных данных
                created_count = 0
                for project_name in server_project_names:
                    if self.file_manager.add_global_project(project_name):
                        created_count += 1
                
                # Удаляем локальные проекты, которых нет на сервере
                removed_count = 0
                removed_projects = []
                for local_project in local_projects:
                    if local_project not in server_project_names and local_project != "Основной проект":
                        # Не удаляем "Основной проект" - это системный проект
                        if self.file_manager.remove_global_project(local_project):
                            removed_count += 1
                            removed_projects.append(local_project)
                
                # Обновляем список проектов в интерфейсе
                self.update_projects_list()
                
                # Обновляем список объектов для текущего проекта
                current_project = self.project_var.get()
                if current_project:
                    self.update_objects_list(current_project)
                
                # Синхронизация завершена успешно - не показываем диалог
                # Обновляем интерфейс автоматически
                pass
            else:
                error_msg = result.get('error', 'Неизвестная ошибка')
                print(f"❌ Ошибка: {error_msg}")
                messagebox.showerror("Ошибка", f"Ошибка получения проектов: {error_msg}")
                
        except Exception as e:
            print(f"💥 Исключение: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"Ошибка синхронизации проектов: {str(e)}")
    
    def auto_sync_projects(self):
        """Автоматическая синхронизация проектов при загрузке"""
        def sync_in_background():
            try:
                # Импортируем клиент проектов
                from adapters.project_api_client import get_project_api_client
                from adapters.auth_client import auth_client
                
                # Проверяем авторизацию
                if not auth_client.is_authenticated():
                    print("🔐 Автоматическая синхронизация пропущена - не авторизован")
                    return
                
                print("🔄 Запуск автоматической синхронизации проектов...")
                
                # Получаем клиент проектов
                project_client = get_project_api_client(auth_client)
                
                # Получаем проекты с сервера
                result = project_client.get_projects()
                
                if result.get('success'):
                    projects = result.get('projects', [])
                    server_project_names = [project.get('name', '') for project in projects if project.get('name')]
                    
                    # Получаем текущие локальные проекты
                    local_projects = self.file_manager.get_global_projects()
                    
                    # Создаем локальные проекты на основе серверных данных
                    created_count = 0
                    for project_name in server_project_names:
                        if self.file_manager.add_global_project(project_name):
                            created_count += 1
                    
                    # Удаляем локальные проекты, которых нет на сервере
                    removed_count = 0
                    for local_project in local_projects:
                        if local_project not in server_project_names and local_project != "Основной проект":
                            if self.file_manager.remove_global_project(local_project):
                                removed_count += 1
                    
                    # Обновляем интерфейс в основном потоке
                    self.root.after(0, self._update_ui_after_auto_sync, created_count, removed_count, len(projects))
                    
                    print(f"✅ Автоматическая синхронизация завершена: создано {created_count}, удалено {removed_count}")
                else:
                    print(f"❌ Ошибка автоматической синхронизации: {result.get('error', 'Неизвестная ошибка')}")
                    
            except Exception as e:
                print(f"💥 Ошибка автоматической синхронизации: {e}")
        
        # Запускаем синхронизацию в отдельном потоке
        threading.Thread(target=sync_in_background, daemon=True).start()
    
    def _update_ui_after_auto_sync(self, created_count, removed_count, total_projects):
        """Обновление интерфейса после автоматической синхронизации"""
        try:
            # Обновляем список проектов в интерфейсе
            self.update_projects_list()
            
            # Обновляем список объектов для текущего проекта
            current_project = self.project_var.get()
            if current_project:
                self.update_objects_list(current_project)
            
            # Показываем уведомление только если были изменения
            if created_count > 0 or removed_count > 0:
                sync_message = f"Автоматическая синхронизация завершена:\n"
                sync_message += f"• Проектов с сервера: {total_projects}\n"
                sync_message += f"• Создано новых: {created_count}\n"
                sync_message += f"• Удалено устаревших: {removed_count}"
                
                # Показываем уведомление в статусной строке (если есть) или в консоли
                print(f"📢 {sync_message}")
        except Exception as e:
            print(f"Ошибка обновления UI после синхронизации: {e}")
    
    
    def run(self):
        """Запуск окна выбора проекта"""
        self.root.mainloop()


if __name__ == "__main__":
    # Запускаем приветственное окно
    welcome = WelcomeWindow()
    welcome.run()
