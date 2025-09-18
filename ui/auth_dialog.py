#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диалог аутентификации (логин/регистрация)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from pathlib import Path
import sys

# Импортируем поддержку буфера обмена
from ui.clipboard_support import ClipboardEntry

# Добавляем путь к корневой папке проекта
sys.path.append(str(Path(__file__).parent.parent))

from adapters.auth_client import auth_client

class AuthDialog:
    """Диалог аутентификации"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.user_info = None
        
        # Создаем диалоговое окно
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔐 Аутентификация")
        self.dialog.geometry("450x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрируем окно
        self.center_window()
        
        # Настройка стилей
        self.setup_styles()
        
        # Создание интерфейса
        self.setup_ui()
        
        # Обработчики событий
        self.setup_events()
        
        # Проверяем, есть ли сохраненные токены
        self.check_existing_auth()
    
    def center_window(self):
        """Центрирование окна"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"450x600+{x}+{y}")
    
    def setup_styles(self):
        """Настройка стилей"""
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
        
        # Настройка цветов и шрифтов
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 18, 'bold'),
                       foreground=text_primary,
                       background=background_color)
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 12),
                       foreground=text_secondary,
                       background=background_color)
        
        style.configure('Field.TLabel',
                       font=('Segoe UI', 11, 'bold'),
                       foreground=text_primary,
                       background=background_color)
        
        # Основные кнопки
        style.configure('Primary.TButton',
                       font=('Segoe UI', 12, 'bold'),
                       padding=(20, 10),
                       relief='flat',
                       borderwidth=0,
                       background=primary_color,
                       foreground='white')
        
        style.map('Primary.TButton',
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
        
        # Ссылки
        style.configure('Link.TButton',
                       font=('Segoe UI', 10),
                       padding=(8, 4),
                       relief='flat',
                       borderwidth=0,
                       background=background_color,
                       foreground=primary_color)
        
        style.map('Link.TButton',
                 foreground=[('active', primary_hover), ('!active', primary_color)])
        
        # Фреймы
        style.configure('Auth.TFrame',
                       background=background_color,
                       relief='flat',
                       borderwidth=0)
        
        # Entry стили
        style.configure('Auth.TEntry',
                       font=('Segoe UI', 11),
                       background=surface_color,
                       fieldbackground=surface_color,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=border_color)
        
        style.map('Auth.TEntry',
                 bordercolor=[('focus', primary_color)],
                 fieldbackground=[('focus', surface_color)])
    
    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        # Основной контейнер
        main_frame = ttk.Frame(self.dialog, style='Auth.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="🔐 Аутентификация",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 10))
        
        # Подзаголовок
        subtitle_label = ttk.Label(
            main_frame,
            text="Войдите в систему или зарегистрируйтесь",
            style='Subtitle.TLabel'
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Контейнер для форм
        self.forms_frame = ttk.Frame(main_frame, style='Auth.TFrame')
        self.forms_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем формы логина и регистрации
        self.create_login_form()
        self.create_register_form()
        
        # Показываем форму логина по умолчанию
        self.show_login_form()
        
        # Статус бар
        self.status_frame = ttk.Frame(main_frame, style='Auth.TFrame')
        self.status_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Готов к работе",
            style='Subtitle.TLabel'
        )
        self.status_label.pack()
        
        # Прогресс бар
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(pady=(5, 0))
    
    def create_login_form(self):
        """Создание формы логина"""
        self.login_frame = ttk.Frame(self.forms_frame, style='Auth.TFrame')
        
        # Заголовок формы
        login_title = ttk.Label(
            self.login_frame,
            text="Вход в систему",
            style='Field.TLabel'
        )
        login_title.pack(pady=(0, 20))
        
        # Поле email
        email_frame = ttk.Frame(self.login_frame, style='Auth.TFrame')
        email_frame.pack(fill=tk.X, pady=(0, 15))
        
        email_label = ttk.Label(email_frame, text="Email:", style='Field.TLabel')
        email_label.pack(anchor=tk.W)
        
        self.login_email_var = tk.StringVar()
        self.login_email_entry = ClipboardEntry(
            email_frame,
            textvariable=self.login_email_var,
            font=('Segoe UI', 11),
            style='Auth.TEntry'
        )
        self.login_email_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Поле пароля
        password_frame = ttk.Frame(self.login_frame, style='Auth.TFrame')
        password_frame.pack(fill=tk.X, pady=(0, 20))
        
        password_label = ttk.Label(password_frame, text="Пароль:", style='Field.TLabel')
        password_label.pack(anchor=tk.W)
        
        self.login_password_var = tk.StringVar()
        self.login_password_entry = ClipboardEntry(
            password_frame,
            textvariable=self.login_password_var,
            show="*",
            font=('Segoe UI', 11),
            style='Auth.TEntry'
        )
        self.login_password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Кнопка входа
        login_button = ttk.Button(
            self.login_frame,
            text="🚀 Войти",
            style='Primary.TButton',
            command=self.login
        )
        login_button.pack(fill=tk.X, pady=(0, 15))
        
        # Ссылка на регистрацию
        register_link = ttk.Button(
            self.login_frame,
            text="Нет аккаунта? Зарегистрироваться",
            style='Link.TButton',
            command=self.show_register_form
        )
        register_link.pack()
    
    def create_register_form(self):
        """Создание формы регистрации"""
        self.register_frame = ttk.Frame(self.forms_frame, style='Auth.TFrame')
        
        # Заголовок формы
        register_title = ttk.Label(
            self.register_frame,
            text="Регистрация",
            style='Field.TLabel'
        )
        register_title.pack(pady=(0, 20))
        
        # Поле имени
        name_frame = ttk.Frame(self.register_frame, style='Auth.TFrame')
        name_frame.pack(fill=tk.X, pady=(0, 15))
        
        name_label = ttk.Label(name_frame, text="Имя (необязательно):", style='Field.TLabel')
        name_label.pack(anchor=tk.W)
        
        self.register_name_var = tk.StringVar()
        self.register_name_entry = ClipboardEntry(
            name_frame,
            textvariable=self.register_name_var,
            font=('Segoe UI', 11),
            style='Auth.TEntry'
        )
        self.register_name_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Поле email
        email_frame = ttk.Frame(self.register_frame, style='Auth.TFrame')
        email_frame.pack(fill=tk.X, pady=(0, 15))
        
        email_label = ttk.Label(email_frame, text="Email:", style='Field.TLabel')
        email_label.pack(anchor=tk.W)
        
        self.register_email_var = tk.StringVar()
        self.register_email_entry = ClipboardEntry(
            email_frame,
            textvariable=self.register_email_var,
            font=('Segoe UI', 11),
            style='Auth.TEntry'
        )
        self.register_email_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Поле пароля
        password_frame = ttk.Frame(self.register_frame, style='Auth.TFrame')
        password_frame.pack(fill=tk.X, pady=(0, 15))
        
        password_label = ttk.Label(password_frame, text="Пароль:", style='Field.TLabel')
        password_label.pack(anchor=tk.W)
        
        self.register_password_var = tk.StringVar()
        self.register_password_entry = ClipboardEntry(
            password_frame,
            textvariable=self.register_password_var,
            show="*",
            font=('Segoe UI', 11),
            style='Auth.TEntry'
        )
        self.register_password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Поле подтверждения пароля
        confirm_password_frame = ttk.Frame(self.register_frame, style='Auth.TFrame')
        confirm_password_frame.pack(fill=tk.X, pady=(0, 20))
        
        confirm_password_label = ttk.Label(confirm_password_frame, text="Подтвердите пароль:", style='Field.TLabel')
        confirm_password_label.pack(anchor=tk.W)
        
        self.register_confirm_password_var = tk.StringVar()
        self.register_confirm_password_entry = ClipboardEntry(
            confirm_password_frame,
            textvariable=self.register_confirm_password_var,
            show="*",
            font=('Segoe UI', 11),
            style='Auth.TEntry'
        )
        self.register_confirm_password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Кнопка регистрации
        register_button = ttk.Button(
            self.register_frame,
            text="📝 Зарегистрироваться",
            style='Primary.TButton',
            command=self.register
        )
        register_button.pack(fill=tk.X, pady=(0, 15))
        
        # Ссылка на логин
        login_link = ttk.Button(
            self.register_frame,
            text="Уже есть аккаунт? Войти",
            style='Link.TButton',
            command=self.show_login_form
        )
        login_link.pack()
    
    def setup_events(self):
        """Настройка обработчиков событий"""
        # Обработка Enter в полях логина
        self.login_email_entry.bind('<Return>', lambda e: self.login())
        self.login_password_entry.bind('<Return>', lambda e: self.login())
        
        # Обработка Enter в полях регистрации
        self.register_name_entry.bind('<Return>', lambda e: self.register())
        self.register_email_entry.bind('<Return>', lambda e: self.register())
        self.register_password_entry.bind('<Return>', lambda e: self.register())
        self.register_confirm_password_entry.bind('<Return>', lambda e: self.register())
        
        # Обработка Escape для закрытия
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def show_login_form(self):
        """Показать форму логина"""
        # Скрываем все формы
        for widget in self.forms_frame.winfo_children():
            widget.pack_forget()
        
        # Показываем форму логина
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фокус на поле email
        self.login_email_entry.focus()
    
    def show_register_form(self):
        """Показать форму регистрации"""
        # Скрываем все формы
        for widget in self.forms_frame.winfo_children():
            widget.pack_forget()
        
        # Показываем форму регистрации
        self.register_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фокус на поле имени
        self.register_name_entry.focus()
    
    def check_existing_auth(self):
        """Проверка существующей аутентификации"""
        if auth_client.is_authenticated():
            user_name = auth_client.get_user_name()
            self.update_status(f"Добро пожаловать, {user_name}!")
            
            # Автоматически продолжаем с существующей сессией
            self.result = True
            self.user_info = auth_client.user_info
            
            # Небольшая задержка для показа приветствия
            self.dialog.after(1500, self.dialog.destroy)
            return
    
    def update_status(self, message):
        """Обновление статуса"""
        self.status_label.configure(text=message)
        self.dialog.update_idletasks()
    
    def login(self):
        """Вход в систему"""
        email = self.login_email_var.get().strip()
        password = self.login_password_var.get().strip()
        
        if not email or not password:
            messagebox.showwarning("Предупреждение", "Заполните все поля")
            return
        
        # Запускаем вход в отдельном потоке
        self.progress.start()
        self.update_status("Выполняется вход...")
        
        threading.Thread(
            target=self._login_thread,
            args=(email, password),
            daemon=True
        ).start()
    
    def _login_thread(self, email, password):
        """Поток для входа в систему"""
        try:
            result = auth_client.login(email, password)
            
            # Обновляем UI в основном потоке
            self.dialog.after(0, self._handle_login_result, result)
            
        except Exception as e:
            self.dialog.after(0, self._handle_login_result, {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            })
    
    def _handle_login_result(self, result):
        """Обработка результата входа"""
        self.progress.stop()
        
        if result['success']:
            self.result = True
            self.user_info = result['user']
            self.update_status("Вход выполнен успешно!")
            
            # Небольшая задержка перед закрытием
            self.dialog.after(1000, self.dialog.destroy)
        else:
            self.update_status("Ошибка входа")
            messagebox.showerror("Ошибка входа", result['error'])
    
    def register(self):
        """Регистрация"""
        name = self.register_name_var.get().strip()
        email = self.register_email_var.get().strip()
        password = self.register_password_var.get().strip()
        confirm_password = self.register_confirm_password_var.get().strip()
        
        if not email or not password:
            messagebox.showwarning("Предупреждение", "Заполните обязательные поля")
            return
        
        if password != confirm_password:
            messagebox.showwarning("Предупреждение", "Пароли не совпадают")
            return
        
        if len(password) < 6:
            messagebox.showwarning("Предупреждение", "Пароль должен содержать минимум 6 символов")
            return
        
        # Запускаем регистрацию в отдельном потоке
        self.progress.start()
        self.update_status("Выполняется регистрация...")
        
        threading.Thread(
            target=self._register_thread,
            args=(email, password, name if name else None),
            daemon=True
        ).start()
    
    def _register_thread(self, email, password, name):
        """Поток для регистрации"""
        try:
            result = auth_client.register(email, password, name)
            
            # Обновляем UI в основном потоке
            self.dialog.after(0, self._handle_register_result, result)
            
        except Exception as e:
            self.dialog.after(0, self._handle_register_result, {
                'success': False,
                'error': f'Неожиданная ошибка: {str(e)}'
            })
    
    def _handle_register_result(self, result):
        """Обработка результата регистрации"""
        self.progress.stop()
        
        if result['success']:
            self.update_status("Регистрация прошла успешно!")
            messagebox.showinfo("Успех", "Регистрация прошла успешно!\nТеперь вы можете войти в систему.")
            
            # Переключаемся на форму логина
            self.show_login_form()
            
            # Заполняем поле email
            self.login_email_var.set(result['user']['email'])
            self.login_password_entry.focus()
        else:
            self.update_status("Ошибка регистрации")
            messagebox.showerror("Ошибка регистрации", result['error'])
    
    def cancel(self):
        """Отмена"""
        self.result = False
        self.dialog.destroy()


def show_auth_dialog(parent) -> tuple[bool, dict]:
    """Показать диалог аутентификации"""
    dialog = AuthDialog(parent)
    dialog.dialog.wait_window()
    
    return dialog.result, dialog.user_info


if __name__ == "__main__":
    # Тестирование диалога
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    
    result, user_info = show_auth_dialog(root)
    
    if result:
        print("Аутентификация успешна!")
        print(f"Пользователь: {user_info}")
    else:
        print("Аутентификация отменена")
    
    root.destroy()
