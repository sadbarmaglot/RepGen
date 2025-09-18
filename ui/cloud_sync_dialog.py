import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import sys

# Добавляем путь к корневой папке проекта
sys.path.append(str(Path(__file__).parent.parent))

from adapters.cloud_sync import CloudSyncManager

class CloudSyncDialog:
    """Диалог настройки облачной синхронизации"""
    
    def __init__(self, parent, file_manager=None):
        self.file_manager = file_manager
        self.sync_manager = CloudSyncManager()
        self.config = self.sync_manager.config_manager.config
        
        # Создаем диалоговое окно
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🌐 Настройка облачной синхронизации")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрируем относительно родительского окна
        self.center_window(parent)
        
        self.create_widgets()
        self.load_current_settings()
        
        # Ждем закрытия диалога
        self.dialog.wait_window()
        
    def center_window(self, parent):
        """Центрирование окна относительно родителя"""
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 350
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 300
        self.dialog.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        """Создание виджетов диалога"""
        # Заголовок
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(
            header_frame, 
            text="Настройка облачной синхронизации", 
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W)
        
        ttk.Label(
            header_frame,
            text="Автоматическая выгрузка отчетов в облако",
            font=("Arial", 10),
            foreground="gray"
        ).pack(anchor=tk.W)
        
        # Основные настройки
        main_frame = ttk.LabelFrame(self.dialog, text="Основные настройки", padding=10)
        main_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Включение синхронизации
        self.enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            main_frame,
            text="Включить облачную синхронизацию",
            variable=self.enabled_var,
            command=self.on_enabled_change
        ).pack(anchor=tk.W, pady=5)
        
        # Выбор метода синхронизации
        method_frame = ttk.Frame(main_frame)
        method_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(method_frame, text="Метод синхронизации:").pack(side=tk.LEFT)
        
        self.method_var = tk.StringVar(value="ftp")
        method_combo = ttk.Combobox(
            method_frame,
            textvariable=self.method_var,
            values=["ftp", "email", "webhook", "google_drive"],
            state="readonly",
            width=15
        )
        method_combo.pack(side=tk.LEFT, padx=(10, 0))
        method_combo.bind('<<ComboboxSelected>>', self.on_method_change)
        
        # Автоматическая синхронизация
        self.auto_sync_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main_frame,
            text="Автоматическая синхронизация после создания отчета",
            variable=self.auto_sync_var
        ).pack(anchor=tk.W, pady=5)
        
        # Notebook для разных методов
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Вкладки для разных методов
        self.create_ftp_tab()
        self.create_email_tab()
        self.create_webhook_tab()
        self.create_google_drive_tab()
        
        # Кнопки управления
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(
            buttons_frame,
            text="🧪 Тест соединения",
            command=self.test_connection
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            buttons_frame,
            text="📤 Синхронизировать сейчас",
            command=self.sync_now
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=self.save_settings
        ).pack(side=tk.RIGHT)
        
        ttk.Button(
            buttons_frame,
            text="Отмена",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=(0, 10))
        
    def create_ftp_tab(self):
        """Вкладка настроек FTP"""
        ftp_frame = ttk.Frame(self.notebook)
        self.notebook.add(ftp_frame, text="📁 FTP Сервер")
        
        # Настройки FTP
        ttk.Label(ftp_frame, text="Хост:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ftp_host_var = tk.StringVar()
        ttk.Entry(ftp_frame, textvariable=self.ftp_host_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(ftp_frame, text="Порт:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ftp_port_var = tk.StringVar(value="21")
        ttk.Entry(ftp_frame, textvariable=self.ftp_port_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(ftp_frame, text="Логин:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.ftp_user_var = tk.StringVar()
        ttk.Entry(ftp_frame, textvariable=self.ftp_user_var, width=30).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(ftp_frame, text="Пароль:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.ftp_pass_var = tk.StringVar()
        ttk.Entry(ftp_frame, textvariable=self.ftp_pass_var, width=30, show="*").grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(ftp_frame, text="Папка на сервере:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.ftp_path_var = tk.StringVar(value="/reports/")
        ttk.Entry(ftp_frame, textvariable=self.ftp_path_var, width=30).grid(row=4, column=1, padx=5, pady=5)
        
        # Описание
        info_text = """FTP сервер для загрузки отчетов.
Файлы будут загружаться в указанную папку на сервере.
        Поддерживается создание папок по объектам."""
        
        ttk.Label(ftp_frame, text=info_text, foreground="gray", wraplength=400).grid(
            row=5, column=0, columnspan=2, padx=5, pady=10, sticky=tk.W
        )
        
    def create_email_tab(self):
        """Вкладка настроек Email"""
        email_frame = ttk.Frame(self.notebook)
        self.notebook.add(email_frame, text="📧 Email")
        
        ttk.Label(email_frame, text="SMTP сервер:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_smtp_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_smtp_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(email_frame, text="Порт:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_port_var = tk.StringVar(value="587")
        ttk.Entry(email_frame, textvariable=self.email_port_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(email_frame, text="Email:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_user_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_user_var, width=30).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(email_frame, text="Пароль:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_pass_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_pass_var, width=30, show="*").grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(email_frame, text="Получатели:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_recipients_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_recipients_var, width=40).grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(email_frame, text="(через запятую)", foreground="gray").grid(row=5, column=1, sticky=tk.W, padx=5)
        
        info_text = """Отправка отчетов по email.
Поддерживаются Gmail, Yandex, Mail.ru и корпоративные SMTP.
Отчеты отправляются как вложения."""
        
        ttk.Label(email_frame, text=info_text, foreground="gray", wraplength=400).grid(
            row=6, column=0, columnspan=2, padx=5, pady=10, sticky=tk.W
        )
        
    def create_webhook_tab(self):
        """Вкладка настроек Webhook"""
        webhook_frame = ttk.Frame(self.notebook)
        self.notebook.add(webhook_frame, text="🔗 Webhook")
        
        ttk.Label(webhook_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.webhook_url_var = tk.StringVar()
        ttk.Entry(webhook_frame, textvariable=self.webhook_url_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(webhook_frame, text="Токен авторизации:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.webhook_token_var = tk.StringVar()
        ttk.Entry(webhook_frame, textvariable=self.webhook_token_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        info_text = """Отправка отчетов через HTTP POST запрос.
Подходит для интеграции с корпоративными системами.
Файл отправляется в поле 'file', метаданные в 'data'."""
        
        ttk.Label(webhook_frame, text=info_text, foreground="gray", wraplength=400).grid(
            row=2, column=0, columnspan=2, padx=5, pady=10, sticky=tk.W
        )
        
    def create_google_drive_tab(self):
        """Вкладка настроек Google Drive"""
        drive_frame = ttk.Frame(self.notebook)
        self.notebook.add(drive_frame, text="☁️ Google Drive")
        
        ttk.Label(drive_frame, text="Файл credentials.json:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        creds_frame = ttk.Frame(drive_frame)
        creds_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.drive_creds_var = tk.StringVar()
        ttk.Entry(creds_frame, textvariable=self.drive_creds_var, width=30).pack(side=tk.LEFT)
        ttk.Button(creds_frame, text="Обзор...", command=self.select_credentials_file).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(drive_frame, text="ID папки:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.drive_folder_var = tk.StringVar()
        ttk.Entry(drive_frame, textvariable=self.drive_folder_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(drive_frame, text="(необязательно)", foreground="gray").grid(row=2, column=1, sticky=tk.W, padx=5)
        
        info_text = """Загрузка в Google Drive.
Требуется настройка Google Cloud Console и файл credentials.json.
Инструкция: console.cloud.google.com → APIs & Services → Credentials"""
        
        ttk.Label(drive_frame, text=info_text, foreground="gray", wraplength=400).grid(
            row=3, column=0, columnspan=2, padx=5, pady=10, sticky=tk.W
        )
        
    def select_credentials_file(self):
        """Выбор файла credentials.json"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл credentials.json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.drive_creds_var.set(file_path)
            
    def load_current_settings(self):
        """Загрузка текущих настроек"""
        # Основные настройки
        self.enabled_var.set(self.config.get('enabled', False))
        self.method_var.set(self.config.get('sync_method', 'ftp'))
        self.auto_sync_var.set(self.config.get('auto_sync', True))
        
        # FTP
        ftp_config = self.config.get('ftp', {})
        self.ftp_host_var.set(ftp_config.get('host', ''))
        self.ftp_port_var.set(str(ftp_config.get('port', 21)))
        self.ftp_user_var.set(ftp_config.get('username', ''))
        self.ftp_pass_var.set(ftp_config.get('password', ''))
        self.ftp_path_var.set(ftp_config.get('remote_path', '/reports/'))
        
        # Email
        email_config = self.config.get('email', {})
        self.email_smtp_var.set(email_config.get('smtp_server', ''))
        self.email_port_var.set(str(email_config.get('smtp_port', 587)))
        self.email_user_var.set(email_config.get('username', ''))
        self.email_pass_var.set(email_config.get('password', ''))
        self.email_recipients_var.set(', '.join(email_config.get('recipients', [])))
        
        # Webhook
        webhook_config = self.config.get('webhook', {})
        self.webhook_url_var.set(webhook_config.get('url', ''))
        self.webhook_token_var.set(webhook_config.get('auth_token', ''))
        
        # Google Drive
        drive_config = self.config.get('google_drive', {})
        self.drive_creds_var.set(drive_config.get('credentials_file', ''))
        self.drive_folder_var.set(drive_config.get('folder_id', ''))
        
        self.on_enabled_change()
        
    def on_enabled_change(self):
        """Обработчик изменения состояния включения"""
        enabled = self.enabled_var.get()
        state = "normal" if enabled else "disabled"
        
        # Включаем/выключаем все элементы управления
        for child in self.notebook.winfo_children():
            self._set_widget_state(child, state)
            
    def _set_widget_state(self, widget, state):
        """Рекурсивное изменение состояния виджетов"""
        try:
            widget.configure(state=state)
        except:
            pass
        
        for child in widget.winfo_children():
            self._set_widget_state(child, state)
            
    def on_method_change(self, event=None):
        """Обработчик изменения метода синхронизации"""
        method = self.method_var.get()
        
        # Переключаем на соответствующую вкладку
        method_tabs = {
            'ftp': 0,
            'email': 1,
            'webhook': 2,
            'google_drive': 3
        }
        
        if method in method_tabs:
            self.notebook.select(method_tabs[method])
            
    def save_settings(self):
        """Сохранение настроек"""
        try:
            # Обновляем конфигурацию
            self.config['enabled'] = self.enabled_var.get()
            self.config['sync_method'] = self.method_var.get()
            self.config['auto_sync'] = self.auto_sync_var.get()
            
            # FTP
            self.config['ftp'] = {
                'host': self.ftp_host_var.get(),
                'port': int(self.ftp_port_var.get() or 21),
                'username': self.ftp_user_var.get(),
                'password': self.ftp_pass_var.get(),
                'remote_path': self.ftp_path_var.get()
            }
            
            # Email
            recipients = [r.strip() for r in self.email_recipients_var.get().split(',') if r.strip()]
            self.config['email'] = {
                'smtp_server': self.email_smtp_var.get(),
                'smtp_port': int(self.email_port_var.get() or 587),
                'username': self.email_user_var.get(),
                'password': self.email_pass_var.get(),
                'recipients': recipients
            }
            
            # Webhook
            self.config['webhook'] = {
                'url': self.webhook_url_var.get(),
                'auth_token': self.webhook_token_var.get()
            }
            
            # Google Drive
            self.config['google_drive'] = {
                'credentials_file': self.drive_creds_var.get(),
                'folder_id': self.drive_folder_var.get()
            }
            
            # Сохраняем
            self.sync_manager.config_manager.save_config()
            
            messagebox.showinfo("Сохранение", "Настройки сохранены успешно")
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения настроек: {e}")
            
    def test_connection(self):
        """Тестирование соединения"""
        method = self.method_var.get()
        
        def test_thread():
            try:
                # Временно сохраняем настройки для теста
                self.save_settings()
                
                # Тестируем соединение
                success = self.sync_manager.test_connection(method)
                
                if success:
                    self.dialog.after(0, lambda: messagebox.showinfo(
                        "Тест соединения", 
                        f"✅ Соединение с {method} успешно!"
                    ))
                else:
                    self.dialog.after(0, lambda: messagebox.showerror(
                        "Тест соединения", 
                        f"❌ Не удалось подключиться к {method}"
                    ))
                    
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Ошибка", 
                    f"Ошибка тестирования: {e}"
                ))
        
        threading.Thread(target=test_thread, daemon=True).start()
        
    def sync_now(self):
        """Немедленная синхронизация"""
        if not self.file_manager:
            messagebox.showwarning("Предупреждение", "Файловый менеджер недоступен")
            return
            
        def sync_thread():
            try:
                # Сохраняем настройки
                self.save_settings()
                
                # Получаем директории текущего объекта
                dirs = self.file_manager.get_project_directories()
                project_name = self.file_manager.current_project
                
                # Синхронизируем отчеты
                result = self.sync_manager.sync_project_reports(dirs['project_dir'], project_name)
                
                synced_count = len(result['synced'])
                failed_count = len(result['failed'])
                
                message = f"Синхронизация завершена:\n✅ Успешно: {synced_count}\n❌ Ошибок: {failed_count}"
                
                self.dialog.after(0, lambda: messagebox.showinfo("Синхронизация", message))
                
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Ошибка", 
                    f"Ошибка синхронизации: {e}"
                ))
        
        threading.Thread(target=sync_thread, daemon=True).start()