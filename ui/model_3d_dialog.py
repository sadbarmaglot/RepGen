"""
Диалог для загрузки и анализа 3D моделей
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import json
from typing import Optional, Dict

try:
    from ..adapters.model_3d_analyzer import Model3DAnalyzer, install_3d_dependencies
    HAS_3D_MODULE = True
except ImportError:
    HAS_3D_MODULE = False


class Model3DDialog:
    """Диалог для работы с 3D моделями"""
    
    def __init__(self, parent, file_manager):
        self.parent = parent
        self.file_manager = file_manager
        self.analyzer = None
        self.current_analysis = None
        
        # Проверяем доступность 3D модуля
        if not HAS_3D_MODULE:
            self.show_install_dependencies_dialog()
            return
        
        try:
            self.analyzer = Model3DAnalyzer()
        except ImportError as e:
            self.show_install_dependencies_dialog()
            return
        
        self.create_dialog()
    
    def show_install_dependencies_dialog(self):
        """Показывает диалог установки зависимостей"""
        result = messagebox.askyesno(
            "Установка зависимостей",
            "Для работы с 3D моделями нужно установить дополнительные библиотеки:\n\n"
            "• trimesh[easy] - для работы с 3D мешами\n"
            "• pygltflib - для GLB/GLTF файлов\n"
            "• numpy - для математических операций\n\n"
            "Установить сейчас? (потребуется время)"
        )
        
        if result:
            self.install_dependencies()
    
    def install_dependencies(self):
        """Устанавливает зависимости в фоновом режиме"""
        progress_window = tk.Toplevel(self.parent)
        progress_window.title("Установка зависимостей")
        progress_window.geometry("400x150")
        progress_window.transient(self.parent)
        progress_window.grab_set()
        
        # Центрируем окно
        progress_window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Интерфейс прогресса
        ttk.Label(progress_window, text="Устанавливаю библиотеки для 3D анализа...").pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        status_label = ttk.Label(progress_window, text="Пожалуйста, ждите...")
        status_label.pack(pady=10)
        
        def install_worker():
            try:
                success = install_3d_dependencies()
                
                progress_window.after(100, lambda: self.installation_complete(
                    progress_window, success, ""
                ))
            except Exception as exc:
                error_msg = str(exc)
                progress_window.after(100, lambda: self.installation_complete(
                    progress_window, False, error_msg
                ))
        
        # Запускаем установку в отдельном потоке
        threading.Thread(target=install_worker, daemon=True).start()
    
    def installation_complete(self, progress_window, success: bool, error: str = ""):
        """Завершение установки зависимостей"""
        progress_window.destroy()
        
        if success:
            messagebox.showinfo(
                "Установка завершена",
                "Зависимости установлены успешно!\n\n"
                "Перезапустите приложение для использования 3D анализа."
            )
        else:
            messagebox.showerror(
                "Ошибка установки",
                f"Не удалось установить зависимости.\n\n"
                f"Ошибка: {error}\n\n"
                "Попробуйте установить вручную:\n"
                "pip install trimesh[easy] pygltflib numpy"
            )
    
    def create_dialog(self):
        """Создает основной диалог"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("3D Анализ строительных дефектов")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Центрируем окно
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создает элементы интерфейса"""
        # Заголовок
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(
            header_frame, 
            text="🏗️ Анализ 3D модели строительного объекта",
            font=("Arial", 14, "bold")
        ).pack()
        
        ttk.Label(
            header_frame, 
            text="Поддерживаемые форматы: GLB, GLTF, OBJ, PLY, STL",
            font=("Arial", 10)
        ).pack(pady=5)
        
        # Фрейм загрузки файла
        file_frame = ttk.LabelFrame(self.dialog, text="Загрузка 3D модели")
        file_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Выбор файла
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(
            file_select_frame, 
            textvariable=self.file_path_var, 
            state="readonly",
            width=60
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            file_select_frame,
            text="Выбрать файл",
            command=self.select_3d_file
        ).pack(side=tk.RIGHT)
        
        # Контекст анализа
        context_frame = ttk.LabelFrame(self.dialog, text="Дополнительная информация")
        context_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.context_text = tk.Text(context_frame, height=3, wrap=tk.WORD)
        self.context_text.pack(fill=tk.X, padx=10, pady=10)
        self.context_text.insert(tk.END, "Опишите объект: тип здания, возраст, назначение...")
        
        # Кнопки действий
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.analyze_button = ttk.Button(
            buttons_frame,
            text="🔍 Анализировать модель",
            command=self.start_analysis,
            state=tk.DISABLED
        )
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            buttons_frame,
            text="❌ Закрыть",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)
        
        # Прогресс анализа
        self.progress_frame = ttk.LabelFrame(self.dialog, text="Ход анализа")
        self.progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Готов к анализу")
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            mode='indeterminate'
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)
        
        # Результаты анализа
        results_frame = ttk.LabelFrame(self.dialog, text="Результаты анализа")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Текстовое поле с прокруткой
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.results_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки действий с результатами
        results_buttons_frame = ttk.Frame(results_frame)
        results_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.save_button = ttk.Button(
            results_buttons_frame,
            text="💾 Сохранить результат",
            command=self.save_analysis_result,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_button = ttk.Button(
            results_buttons_frame,
            text="📄 Экспорт в Word",
            command=self.export_to_word,
            state=tk.DISABLED
        )
        self.export_button.pack(side=tk.LEFT)
    
    def select_3d_file(self):
        """Выбор 3D файла"""
        file_types = [
            ("3D модели", "*.glb *.gltf *.obj *.ply *.stl"),
            ("GLB файлы", "*.glb"),
            ("GLTF файлы", "*.gltf"),
            ("OBJ файлы", "*.obj"),
            ("PLY файлы", "*.ply"),
            ("STL файлы", "*.stl"),
            ("Все файлы", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Выберите 3D модель",
            filetypes=file_types
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.analyze_button.config(state=tk.NORMAL)
            
            # Проверяем формат
            if not self.analyzer.is_supported_format(file_path):
                messagebox.showwarning(
                    "Предупреждение",
                    f"Формат файла может не поддерживаться.\n"
                    f"Рекомендуемые форматы: GLB, OBJ, PLY"
                )
    
    def start_analysis(self):
        """Запускает анализ 3D модели"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Ошибка", "Выберите файл 3D модели")
            return
        
        context = self.context_text.get("1.0", tk.END).strip()
        if context == "Опишите объект: тип здания, возраст, назначение...":
            context = ""
        
        # Отключаем кнопку и запускаем прогресс
        self.analyze_button.config(state=tk.DISABLED)
        self.progress_bar.start()
        self.progress_label.config(text="Загрузка и обработка 3D модели...")
        
        # Очищаем результаты
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        self.results_text.config(state=tk.DISABLED)
        
        # Запускаем анализ в отдельном потоке
        def analysis_worker():
            try:
                result = self.analyzer.analyze_3d_model(file_path, context)
                
                # Обновляем UI в главном потоке
                self.dialog.after(100, lambda: self.analysis_complete(result))
                
            except Exception as e:
                error_result = {
                    'success': False,
                    'error': f'Ошибка анализа: {str(e)}'
                }
                self.dialog.after(100, lambda: self.analysis_complete(error_result))
        
        threading.Thread(target=analysis_worker, daemon=True).start()
    
    def analysis_complete(self, result: Dict):
        """Завершение анализа"""
        self.progress_bar.stop()
        self.analyze_button.config(state=tk.NORMAL)
        
        if result.get('success', False):
            self.current_analysis = result
            self.display_analysis_results(result['analysis'])
            self.progress_label.config(
                text=f"✅ Анализ завершен! Проанализировано {result.get('num_views_analyzed', 0)} видов"
            )
            
            # Активируем кнопки
            self.save_button.config(state=tk.NORMAL)
            self.export_button.config(state=tk.NORMAL)
            
        else:
            error_msg = result.get('error', 'Неизвестная ошибка')
            self.progress_label.config(text=f"❌ Ошибка: {error_msg}")
            
            self.results_text.config(state=tk.NORMAL)
            self.results_text.insert(tk.END, f"Ошибка анализа:\n{error_msg}")
            self.results_text.config(state=tk.DISABLED)
    
    def display_analysis_results(self, analysis: Dict):
        """Отображает результаты анализа"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)
        
        # Заголовок
        self.results_text.insert(tk.END, "🏗️ РЕЗУЛЬТАТЫ 3D АНАЛИЗА СТРОИТЕЛЬНЫХ ДЕФЕКТОВ\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Общее состояние
        overall = analysis.get('overall_condition', 'Не определено')
        self.results_text.insert(tk.END, f"📊 ОБЩЕЕ СОСТОЯНИЕ: {overall}\n\n")
        
        # Краткое резюме
        summary = analysis.get('analysis_summary', '')
        if summary:
            self.results_text.insert(tk.END, f"📋 РЕЗЮМЕ АНАЛИЗА:\n{summary}\n\n")
        
        # Дефекты
        defects = analysis.get('defects', [])
        if defects:
            self.results_text.insert(tk.END, f"🔍 ОБНАРУЖЕННЫЕ ДЕФЕКТЫ ({len(defects)}):\n")
            self.results_text.insert(tk.END, "-" * 40 + "\n\n")
            
            for i, defect in enumerate(defects, 1):
                self.results_text.insert(tk.END, f"{i}. {defect.get('type', 'Неизвестный дефект')}\n")
                self.results_text.insert(tk.END, f"   📍 Местоположение: {defect.get('location', 'Не указано')}\n")
                self.results_text.insert(tk.END, f"   ⚠️ Серьезность: {defect.get('severity', 'Не определена')}\n")
                self.results_text.insert(tk.END, f"   📝 Описание: {defect.get('description', 'Нет описания')}\n")
                
                causes = defect.get('causes', '')
                if causes:
                    self.results_text.insert(tk.END, f"   🔍 Возможные причины: {causes}\n")
                
                recommendations = defect.get('recommendations', '')
                if recommendations:
                    self.results_text.insert(tk.END, f"   🔧 Рекомендации: {recommendations}\n")
                
                view_angles = defect.get('view_angles', [])
                if view_angles:
                    self.results_text.insert(tk.END, f"   👁️ Видимо на видах: {', '.join(view_angles)}\n")
                
                self.results_text.insert(tk.END, "\n")
        else:
            self.results_text.insert(tk.END, "✅ Серьезных дефектов не обнаружено\n\n")
        
        # Приоритетные ремонты
        priority_repairs = analysis.get('priority_repairs', [])
        if priority_repairs:
            self.results_text.insert(tk.END, "🚨 ПРИОРИТЕТНЫЕ РЕМОНТНЫЕ РАБОТЫ:\n")
            for i, repair in enumerate(priority_repairs, 1):
                self.results_text.insert(tk.END, f"{i}. {repair}\n")
            self.results_text.insert(tk.END, "\n")
        
        # Вопросы безопасности
        safety_concerns = analysis.get('safety_concerns', [])
        if safety_concerns:
            self.results_text.insert(tk.END, "⚠️ ВОПРОСЫ БЕЗОПАСНОСТИ:\n")
            for i, concern in enumerate(safety_concerns, 1):
                self.results_text.insert(tk.END, f"{i}. {concern}\n")
            self.results_text.insert(tk.END, "\n")
        
        self.results_text.config(state=tk.DISABLED)
    
    def save_analysis_result(self):
        """Сохраняет результат анализа"""
        if not self.current_analysis:
            messagebox.showerror("Ошибка", "Нет результатов для сохранения")
            return
        
        try:
            # Подготавливаем данные для сохранения
            analysis_data = {
                'type': '3d_model_analysis',
                'file_path': self.file_path_var.get(),
                'context': self.context_text.get("1.0", tk.END).strip(),
                'analysis': self.current_analysis['analysis'],
                'model_info': self.current_analysis.get('model_info', {}),
                'defects_count': len(self.current_analysis['analysis'].get('defects', [])),
                'overall_condition': self.current_analysis['analysis'].get('overall_condition', ''),
                'views_analyzed': self.current_analysis.get('num_views_analyzed', 0)
            }
            
            # Сохраняем через file_manager
            result_id = self.file_manager.save_analysis_result(analysis_data)
            
            messagebox.showinfo(
                "Успех",
                f"Результат 3D анализа сохранен!\n\nID: {result_id}"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить результат:\n{str(e)}")
    
    def export_to_word(self):
        """Экспорт результатов в Word"""
        if not self.current_analysis:
            messagebox.showerror("Ошибка", "Нет результатов для экспорта")
            return
        
        # Пока простая заглушка - в будущем можно реализовать специальный экспорт для 3D
        messagebox.showinfo(
            "Экспорт в Word",
            "Функция экспорта 3D анализа в Word будет добавлена в следующей версии.\n\n"
            "Пока используйте 'Сохранить результат' для сохранения данных."
        )