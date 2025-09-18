import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

class ClipboardSupport:
    """Класс для добавления поддержки копирования/вставки в текстовые поля"""
    
    @staticmethod
    def add_clipboard_support(widget):
        """Добавляет поддержку Ctrl+C/Ctrl+V к виджету"""
        
        def copy_selection(event):
            """Копирование выделенного текста"""
            try:
                if hasattr(widget, 'selection_get'):
                    # Для Entry и Text виджетов
                    selected_text = widget.selection_get()
                    widget.clipboard_clear()
                    widget.clipboard_append(selected_text)
                return "break"  # Предотвращаем стандартную обработку
            except tk.TclError:
                # Нет выделенного текста
                pass
            return None
        
        def paste_text(event):
            """Вставка текста из буфера обмена"""
            try:
                clipboard_text = widget.clipboard_get()
                if hasattr(widget, 'delete'):
                    # Для Entry виджетов
                    if hasattr(widget, 'selection_range'):
                        # Удаляем выделенный текст
                        try:
                            widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                        except tk.TclError:
                            pass
                    widget.insert(tk.INSERT, clipboard_text)
                elif hasattr(widget, 'insert'):
                    # Для Text виджетов
                    widget.insert(tk.INSERT, clipboard_text)
                return "break"  # Предотвращаем стандартную обработку
            except tk.TclError:
                # Буфер обмена пуст или недоступен
                pass
            return None
        
        def cut_selection(event):
            """Вырезание выделенного текста"""
            try:
                if hasattr(widget, 'selection_get'):
                    selected_text = widget.selection_get()
                    widget.clipboard_clear()
                    widget.clipboard_append(selected_text)
                    if hasattr(widget, 'delete'):
                        widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                return "break"  # Предотвращаем стандартную обработку
            except tk.TclError:
                # Нет выделенного текста
                pass
            return None
        
        # Привязываем горячие клавиши
        widget.bind('<Control-c>', copy_selection)
        widget.bind('<Control-v>', paste_text)
        widget.bind('<Control-x>', cut_selection)
        
        # Для macOS также поддерживаем Cmd+C/Cmd+V
        widget.bind('<Command-c>', copy_selection)
        widget.bind('<Command-v>', paste_text)
        widget.bind('<Command-x>', cut_selection)

class ClipboardEntry(ttk.Entry):
    """Entry виджет с поддержкой копирования/вставки"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ClipboardSupport.add_clipboard_support(self)

class ClipboardText(tk.Text):
    """Text виджет с поддержкой копирования/вставки"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ClipboardSupport.add_clipboard_support(self)

class ClipboardScrolledText(scrolledtext.ScrolledText):
    """ScrolledText виджет с поддержкой копирования/вставки"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ClipboardSupport.add_clipboard_support(self)

