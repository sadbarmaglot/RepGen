import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

class ProjectDialog:
    """Диалог для создания нового объекта"""
    
    def __init__(self, parent, title="Новый объект"):
        self.result = None
        
        # Создаем диалоговое окно
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрируем относительно родительского окна
        self.center_window(parent)
        
        self.create_widgets()
        
        # Фокус на поле ввода
        self.name_entry.focus()
        
        # Ждем закрытия диалога
        self.dialog.wait_window()
        
    def center_window(self, parent):
        """Центрирование окна относительно родителя"""
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 100
        self.dialog.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        """Создание виджетов диалога"""
        # Заголовок
        header = ttk.Label(
            self.dialog, 
            text="Создание нового объекта", 
            font=("Arial", 12, "bold")
        )
        header.pack(pady=(20, 10))
        
        # Форма
        form_frame = ttk.Frame(self.dialog)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(form_frame, text="Название объекта:").pack(anchor=tk.W)
        
        self.name_entry = ttk.Entry(form_frame, width=40)
        self.name_entry.pack(fill=tk.X, pady=(5, 10))
        self.name_entry.bind('<Return>', lambda e: self.ok_clicked())
        
        # Примечание
        note = ttk.Label(
            form_frame, 
            text="Например: 'ЖК Солнечный', 'Офисное здание на Невском'",
            foreground="gray"
        )
        note.pack(anchor=tk.W)
        
        # Кнопки
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        ttk.Button(
            buttons_frame, 
            text="Отмена", 
            command=self.cancel_clicked
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            buttons_frame, 
            text="Создать", 
            command=self.ok_clicked
        ).pack(side=tk.RIGHT)
        
    def ok_clicked(self):
        """Обработчик кнопки ОК"""
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Предупреждение", "Введите название объекта")
            return
            
        if len(name) > 100:
            messagebox.showwarning("Предупреждение", "Название слишком длинное (максимум 100 символов)")
            return
            
        # Проверяем недопустимые символы
        invalid_chars = '<>:"/\\|?*'
        if any(char in name for char in invalid_chars):
            messagebox.showwarning(
                "Предупреждение", 
                f"Название не должно содержать символы: {invalid_chars}"
            )
            return
            
        self.result = name
        self.dialog.destroy()
        
    def cancel_clicked(self):
        """Обработчик кнопки Отмена"""
        self.dialog.destroy()

class ProjectManagerDialog:
    """Диалог для управления объектами"""
    
    def __init__(self, parent, file_manager):
        self.file_manager = file_manager
        self.projects_changed = False
        
        # Создаем диалоговое окно
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Управление объектами")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрируем относительно родительского окна
        self.center_window(parent)
        
        self.create_widgets()
        self.load_projects()
        
        # Ждем закрытия диалога
        self.dialog.wait_window()
        
    def center_window(self, parent):
        """Центрирование окна относительно родителя"""
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 300
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 200
        self.dialog.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        """Создание виджетов диалога"""
        # Заголовок
        header = ttk.Label(
            self.dialog, 
            text="Управление объектами", 
            font=("Arial", 14, "bold")
        )
        header.pack(pady=(10, 20))
        
        # Основная область
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Список объектов
        list_frame = ttk.LabelFrame(main_frame, text="Объекты (двойной клик по износу или дате для редактирования)", padding=10)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Создаем Treeview для объектов
        columns = ('name', 'wear', 'last_activity')
        self.projects_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # Настраиваем заголовки
        self.projects_tree.heading('name', text='Название')
        self.projects_tree.heading('wear', text='Износ здания')
        self.projects_tree.heading('last_activity', text='Дата обследования')
        
        # Настраиваем ширину колонок
        self.projects_tree.column('name', width=250)
        self.projects_tree.column('wear', width=100)
        self.projects_tree.column('last_activity', width=120)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=scrollbar.set)
        
        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязываем двойной клик для редактирования износа
        self.projects_tree.bind('<Double-1>', self.on_double_click)
        
        # Кнопки управления
        buttons_frame = ttk.LabelFrame(main_frame, text="Действия", padding=10)
        buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(
            buttons_frame,
            text="➕ Создать объект",
            command=self.create_project
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            buttons_frame,
            text="📝 Переименовать",
            command=self.rename_project
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            buttons_frame,
            text="📂 Открыть папку",
            command=self.open_project_folder
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            buttons_frame,
            text="🏗️ Износ здания",
            command=self.edit_selected_wear
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            buttons_frame,
            text="📅 Дата обследования",
            command=self.edit_selected_survey_date
        ).pack(fill=tk.X, pady=2)
        
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame,
            text="🗑️ Удалить объект",
            command=self.delete_project
        ).pack(fill=tk.X, pady=2)
        
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        
        ttk.Button(
            buttons_frame,
            text="☁️ Синхронизировать",
            command=self.sync_projects_from_server
        ).pack(fill=tk.X, pady=2)
        
        # Кнопка закрытия
        close_frame = ttk.Frame(self.dialog)
        close_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
        
        ttk.Button(
            close_frame,
            text="Закрыть",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)
        
    def load_projects(self):
        """Загрузка списка объектов"""
        # Очищаем список
        self.projects_tree.delete(*self.projects_tree.get_children())
        
        # Загружаем объекты
        projects = self.file_manager.get_all_projects()
        
        for project in projects:
            stats = self.file_manager.get_project_stats(project)
            
            # Получаем дату обследования
            survey_date = self.file_manager.get_survey_date(project)
            if not survey_date:
                # Если нет даты обследования, используем последнюю активность как fallback
                if stats['last_activity']:
                    survey_date = stats['last_activity'].strftime("%d.%m.%Y")
                else:
                    survey_date = "Нет данных"
                
            # Получаем износ здания
            wear_percentage = self.file_manager.get_building_wear(project)
                
            # Добавляем в дерево
            self.projects_tree.insert('', tk.END, values=(
                project,
                wear_percentage,
                survey_date
            ))
            
    def create_project(self):
        """Создание нового объекта"""
        dialog = ProjectDialog(self.dialog, "Создание нового объекта")
        if dialog.result:
            project_name = dialog.result.strip()
            
            # Создаем локальный проект
            local_success = self.file_manager.create_new_project(project_name)
            
            # Пытаемся создать проект на сервере
            server_success = False
            server_message = ""
            
            try:
                from adapters.project_api_client import get_project_api_client
                from adapters.auth_client import auth_client
                
                if auth_client.is_authenticated():
                    project_client = get_project_api_client(auth_client)
                    result = project_client.create_project(project_name)
                    
                    if result.get('success'):
                        server_success = True
                        server_message = " и синхронизирован с сервером"
                    else:
                        server_message = f" (ошибка синхронизации: {result.get('error', 'неизвестная ошибка')})"
                else:
                    server_message = " (синхронизация недоступна - не авторизован)"
                    
            except Exception as e:
                server_message = f" (ошибка синхронизации: {str(e)})"
            
            if local_success:
                self.load_projects()
                self.projects_changed = True
                
                # Успешное создание объекта не требует диалога
                pass
            else:
                messagebox.showerror("Ошибка", "Не удалось создать объект")
                
    def rename_project(self):
        """Переименование объекта"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите объект для переименования")
            return
            
        item = self.projects_tree.item(selection[0])
        old_name = item['values'][0]
        
        if old_name == "Общий объект":
            messagebox.showwarning("Предупреждение", "Нельзя переименовать основной объект")
            return
            
        new_name = simpledialog.askstring(
            "Переименование объекта",
            f"Новое название для '{old_name}':",
            initialvalue=old_name
        )
        
        if new_name and new_name.strip() and new_name.strip() != old_name:
            # Переименование локально
            local_success = False
            try:
                # Создаем новый проект с новым именем
                if self.file_manager.create_new_project(new_name.strip()):
                    # Копируем данные из старого проекта
                    old_dirs = self.file_manager.get_project_directories(old_name)
                    new_dirs = self.file_manager.get_project_directories(new_name.strip())
                    
                    # Копируем файлы
                    import shutil
                    for old_dir, new_dir in zip(old_dirs.values(), new_dirs.values()):
                        if old_dir.exists() and not new_dir.exists():
                            shutil.copytree(old_dir, new_dir)
                    
                    # Удаляем старый проект
                    self.file_manager.delete_project(old_name)
                    local_success = True
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка переименования: {str(e)}")
                return
            
            # Обновляем проект на сервере
            server_success = False
            server_message = ""
            
            try:
                from adapters.project_api_client import get_project_api_client
                from adapters.auth_client import auth_client
                
                if auth_client.is_authenticated():
                    project_client = get_project_api_client(auth_client)
                    
                    # Находим ID старого проекта на сервере
                    result = project_client.get_projects()
                    if result.get('success'):
                        projects = result.get('projects', [])
                        project_id = None
                        for project in projects:
                            if project.get('name') == old_name:
                                project_id = project.get('id')
                                break
                        
                        if project_id:
                            # Обновляем название проекта на сервере
                            update_result = project_client.update_project(project_id, name=new_name.strip())
                            if update_result.get('success'):
                                server_success = True
                                server_message = " и обновлен на сервере"
                            else:
                                server_message = f" (ошибка обновления на сервере: {update_result.get('error', 'неизвестная ошибка')})"
                        else:
                            server_message = " (проект не найден на сервере)"
                    else:
                        server_message = f" (ошибка получения списка проектов: {result.get('error', 'неизвестная ошибка')})"
                else:
                    server_message = " (обновление на сервере недоступно - не авторизован)"
                    
            except Exception as e:
                server_message = f" (ошибка обновления на сервере: {str(e)})"
            
            if local_success:
                # Обновляем список
                self.load_projects()
                self.projects_changed = True
                
                # Успешное переименование не требует диалога
                pass
            else:
                messagebox.showerror("Ошибка", "Не удалось переименовать проект")
            
    def delete_project(self):
        """Удаление объекта"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите объект для удаления")
            return
            
        item = self.projects_tree.item(selection[0])
        project_name = item['values'][0]
        
        if project_name == "Общий объект":
            messagebox.showwarning("Предупреждение", "Нельзя удалить основной объект")
            return
            
        # Подтверждение удаления
        if messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить объект '{project_name}'?\n\n"
            "Все фотографии, анализы и отчеты будут удалены безвозвратно!"
        ):
            # Удаляем локальный проект
            local_success = self.file_manager.delete_project(project_name)
            
            # Пытаемся удалить проект с сервера
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
                self.load_projects()
                self.projects_changed = True
                
                # Успешное удаление не требует диалога
                pass
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить объект")
                
    def open_project_folder(self):
        """Открытие папки объекта"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите объект")
            return
            
        item = self.projects_tree.item(selection[0])
        project_name = item['values'][0]
        
        dirs = self.file_manager.get_project_directories(project_name)
        folder_path = str(dirs['project_dir'])
        
        try:
            import os
            import subprocess
            
            # Открываем в проводнике (попытка для разных ОС)
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', folder_path])
            else:
                subprocess.run(['xdg-open', folder_path])
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")
    
    def on_double_click(self, event):
        """Обработчик двойного клика для редактирования износа"""
        # Получаем выбранный элемент
        selection = self.projects_tree.selection()
        if not selection:
            return
            
        # Получаем информацию о клике
        region = self.projects_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        # Получаем колонку, по которой кликнули
        column = self.projects_tree.identify_column(event.x)
        
        # Получаем данные выбранной строки
        item = self.projects_tree.item(selection[0])
        project_name = item['values'][0]
        
        if column == '#2':  # Колонка "Износ здания"
            current_wear = item['values'][1]
            # Открываем диалог редактирования износа
            self.edit_wear_dialog(project_name, current_wear)
        elif column == '#3':  # Колонка "Дата обследования"
            current_date = item['values'][2]
            # Открываем диалог редактирования даты
            self.edit_survey_date_dialog(project_name, current_date)
    
    def edit_wear_dialog(self, project_name: str, current_wear: str):
        """Диалог редактирования износа здания"""
        # Создаем диалоговое окно
        dialog = tk.Toplevel(self.dialog)
        dialog.title(f"Редактирование износа - {project_name}")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        # Центрируем относительно родительского окна
        dialog.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() // 2) - 200
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
        
        # Заголовок
        header = ttk.Label(
            dialog, 
            text=f"Износ здания: {project_name}", 
            font=("Arial", 12, "bold")
        )
        header.pack(pady=(20, 10))
        
        # Форма
        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(form_frame, text="Процент износа (%):").pack(anchor=tk.W)
        
        # Извлекаем текущее значение (убираем "%" если есть)
        current_value = "0"
        if current_wear and current_wear != "Нет данных" and current_wear != "Ошибка":
            current_value = current_wear.replace("%", "").strip()
        
        wear_entry = ttk.Entry(form_frame, width=10)
        wear_entry.pack(fill=tk.X, pady=(5, 10))
        wear_entry.insert(0, current_value)
        wear_entry.focus()
        wear_entry.select_range(0, tk.END)
        
        # Примечание
        note = ttk.Label(
            form_frame, 
            text="Введите значение от 0 до 100. Оставьте пустым для сброса.",
            foreground="gray"
        )
        note.pack(anchor=tk.W)
        
        # Кнопки
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        def save_wear():
            """Сохранение износа"""
            value = wear_entry.get().strip()
            
            if not value:
                # Удаляем данные об износе
                self.file_manager.delete_building_wear(project_name)
                # Успешное удаление не требует диалога
            else:
                try:
                    wear_percentage = float(value)
                    if wear_percentage < 0 or wear_percentage > 100:
                        messagebox.showwarning("Предупреждение", "Значение должно быть от 0 до 100")
                        return
                    
                    # Сохраняем данные об износе
                    self.file_manager.save_building_wear(project_name, wear_percentage)
                    # Успешное сохранение не требует диалога
                except ValueError:
                    messagebox.showwarning("Предупреждение", "Введите корректное числовое значение")
                    return
            
            # Обновляем список
            self.load_projects()
            self.projects_changed = True
            dialog.destroy()
        
        def cancel_edit():
            """Отмена редактирования"""
            dialog.destroy()
        
        ttk.Button(
            buttons_frame, 
            text="Отмена", 
            command=cancel_edit
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            buttons_frame, 
            text="Сохранить", 
            command=save_wear
        ).pack(side=tk.RIGHT)
        
        # Привязываем Enter к сохранению
        wear_entry.bind('<Return>', lambda e: save_wear())
        
        # Ждем закрытия диалога
        dialog.wait_window()
    
    def edit_survey_date_dialog(self, project_name: str, current_date: str):
        """Диалог редактирования даты обследования"""
        # Создаем диалоговое окно
        dialog = tk.Toplevel(self.dialog)
        dialog.title(f"Редактирование даты обследования - {project_name}")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        # Центрируем относительно родительского окна
        dialog.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() // 2) - 200
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
        
        # Заголовок
        header = ttk.Label(
            dialog, 
            text=f"Дата обследования: {project_name}", 
            font=("Arial", 12, "bold")
        )
        header.pack(pady=(20, 10))
        
        # Форма
        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(form_frame, text="Дата обследования (ДД.ММ.ГГГГ):").pack(anchor=tk.W)
        
        # Извлекаем текущее значение
        current_value = ""
        if current_date and current_date != "Нет данных":
            current_value = current_date
        
        date_entry = ttk.Entry(form_frame, width=15)
        date_entry.pack(fill=tk.X, pady=(5, 10))
        date_entry.insert(0, current_value)
        date_entry.focus()
        date_entry.select_range(0, tk.END)
        
        # Примечание
        note = ttk.Label(
            form_frame, 
            text="Введите дату в формате ДД.ММ.ГГГГ. Оставьте пустым для сброса.",
            foreground="gray"
        )
        note.pack(anchor=tk.W)
        
        # Кнопки
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        def save_date():
            """Сохранение даты обследования"""
            value = date_entry.get().strip()
            
            if not value:
                # Удаляем данные о дате обследования
                self.file_manager.delete_survey_date(project_name)
                # Успешное удаление не требует диалога
            else:
                # Проверяем формат даты
                try:
                    from datetime import datetime
                    # Парсим дату для проверки корректности
                    parsed_date = datetime.strptime(value, "%d.%m.%Y")
                    # Проверяем, что дата не в будущем
                    if parsed_date > datetime.now():
                        messagebox.showwarning("Предупреждение", "Дата не может быть в будущем")
                        return
                    
                    # Сохраняем дату обследования
                    self.file_manager.save_survey_date(project_name, value)
                    # Успешное сохранение не требует диалога
                except ValueError:
                    messagebox.showwarning("Предупреждение", "Введите дату в формате ДД.ММ.ГГГГ")
                    return
            
            # Обновляем список
            self.load_projects()
            self.projects_changed = True
            dialog.destroy()
        
        def cancel_edit():
            """Отмена редактирования"""
            dialog.destroy()
        
        ttk.Button(
            buttons_frame, 
            text="Отмена", 
            command=cancel_edit
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            buttons_frame, 
            text="Сохранить", 
            command=save_date
        ).pack(side=tk.RIGHT)
        
        # Привязываем Enter к сохранению
        date_entry.bind('<Return>', lambda e: save_date())
        
        # Ждем закрытия диалога
        dialog.wait_window()
    
    def sync_projects_from_server(self):
        """Синхронизация проектов с сервера"""
        try:
            # Импортируем клиент проектов
            from adapters.project_api_client import get_project_api_client
            from adapters.auth_client import auth_client
            
            # Проверяем авторизацию
            if not auth_client.is_authenticated():
                messagebox.showwarning("Предупреждение", "Необходима авторизация для синхронизации проектов")
                return
            
            # Получаем клиент проектов
            project_client = get_project_api_client(auth_client)
            
            # Получаем проекты с сервера
            result = project_client.get_projects()
            
            if result.get('success'):
                projects = result.get('projects', [])
                server_project_names = [project.get('name', '') for project in projects if project.get('name')]
                
                # Получаем текущие локальные проекты
                local_projects = self.file_manager.get_all_projects()
                
                # Создаем локальные проекты на основе серверных данных
                created_count = 0
                for project_name in server_project_names:
                    if project_name not in local_projects:
                        if self.file_manager.create_new_project(project_name):
                            created_count += 1
                
                # Удаляем локальные проекты, которых нет на сервере
                removed_count = 0
                removed_projects = []
                for local_project in local_projects:
                    if local_project not in server_project_names and local_project != "Общий объект":
                        # Не удаляем "Общий объект" - это системный проект
                        if self.file_manager.delete_project(local_project):
                            removed_count += 1
                            removed_projects.append(local_project)
                
                # Обновляем список
                self.load_projects()
                self.projects_changed = True
                
                # Синхронизация завершена успешно - не показываем диалог
                pass
            else:
                error_msg = result.get('error', 'Неизвестная ошибка')
                messagebox.showerror("Ошибка", f"Ошибка получения проектов: {error_msg}")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка синхронизации проектов: {str(e)}")
    
    def edit_selected_wear(self):
        """Редактирование износа выбранного объекта"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите объект для редактирования износа")
            return
            
        item = self.projects_tree.item(selection[0])
        project_name = item['values'][0]
        current_wear = item['values'][1]
        
        # Открываем диалог редактирования износа
        self.edit_wear_dialog(project_name, current_wear)
    
    def edit_selected_survey_date(self):
        """Редактирование даты обследования выбранного объекта"""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите объект для редактирования даты обследования")
            return
            
        item = self.projects_tree.item(selection[0])
        project_name = item['values'][0]
        current_date = item['values'][2]
        
        # Открываем диалог редактирования даты
        self.edit_survey_date_dialog(project_name, current_date)