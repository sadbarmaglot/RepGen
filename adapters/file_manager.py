import os
import shutil
from pathlib import Path
from datetime import datetime
import json

class WindowsFileManager:
    """Управление файлами для Windows версии приложения"""
    
    def __init__(self, app_dir="DefectAnalyzer"):
        # Создаем папку приложения в Documents
        self.documents_dir = Path.home() / "Documents"
        self.app_dir = self.documents_dir / app_dir
        self.projects_dir = self.app_dir / "projects"
        self.config_file = self.app_dir / "config.json"
        
        # Текущий объект
        self.current_project = "Общий объект"
        
        # Создаем все необходимые папки
        self.create_directories()
        
        # Загружаем конфигурацию
        self.load_config()
        
    def create_directories(self):
        """Создание структуры папок"""
        for directory in [self.app_dir, self.projects_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Создаем папку для общего объекта по умолчанию
        self.create_project_directories("Общий объект")
    
    def create_project_directories(self, project_name: str):
        """Создание папок для конкретного объекта"""
        project_dir = self.projects_dir / project_name
        photos_dir = project_dir / "photos"
        reports_dir = project_dir / "reports"
        data_dir = project_dir / "data"
        solutions_dir = project_dir / "solutions"
        
        for directory in [project_dir, photos_dir, reports_dir, data_dir, solutions_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    def get_project_directories(self, project_name: str = None):
        """Получение путей к папкам объекта"""
        if project_name is None:
            project_name = self.current_project
            
        project_dir = self.projects_dir / project_name
        return {
            'project_dir': project_dir,
            'photos_dir': project_dir / "photos",
            'reports_dir': project_dir / "reports", 
            'data_dir': project_dir / "data",
            'solutions_dir': project_dir / "solutions",
        }

    # ===== Конструктивные решения =====
    def save_constructive_solution(self, solution: dict) -> str:
        """Сохраняет конструктивное решение в JSON файл и возвращает путь."""
        dirs = self.get_project_directories()
        # Убеждаемся, что папка solutions существует
        dirs['solutions_dir'].mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"solution_{timestamp}.json"
        filepath = dirs['solutions_dir'] / filename

        data = {
            "timestamp": datetime.now().isoformat(),
            "project": self.current_project,
            "solution": solution,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def load_constructive_solutions(self, limit: int = 50, project_name: str = None) -> list:
        """Возвращает список последних сохранённых конструктивных решений."""
        dirs = self.get_project_directories(project_name)
        # Убеждаемся, что папка solutions существует
        if not dirs['solutions_dir'].exists():
            dirs['solutions_dir'].mkdir(parents=True, exist_ok=True)
            return []
            
        json_files = list(dirs['solutions_dir'].glob("solution_*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        results = []
        for file_path in json_files[:limit]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"Ошибка чтения файла {file_path}: {e}")
        return results

    def save_constructive_solutions_bundle(self, solutions: list) -> str:
        """Сохраняет список решений одним файлом для удобства пакетной работы."""
        if not isinstance(solutions, list) or not solutions:
            raise ValueError("Пустой список решений")

        dirs = self.get_project_directories()
        # Убеждаемся, что папка solutions существует
        dirs['solutions_dir'].mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"solutions_bundle_{timestamp}.json"
        filepath = dirs['solutions_dir'] / filename

        payload = {
            "timestamp": datetime.now().isoformat(),
            "project": self.current_project,
            "solutions": solutions,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return str(filepath)
    
    def load_constructive_solutions_bundle(self, project_name: str = None) -> list:
        """Загружает последний сохраненный пакет конструктивных решений."""
        dirs = self.get_project_directories(project_name)
        # Убеждаемся, что папка solutions существует
        if not dirs['solutions_dir'].exists():
            dirs['solutions_dir'].mkdir(parents=True, exist_ok=True)
            return []
            
        # Ищем файлы пакетов решений
        bundle_files = list(dirs['solutions_dir'].glob("solutions_bundle_*.json"))
        if not bundle_files:
            return []
            
        # Берем самый последний файл
        latest_file = max(bundle_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('solutions', [])
        except Exception as e:
            print(f"Ошибка чтения файла {latest_file}: {e}")
            return []
    
    def set_current_project(self, project_name: str):
        """Установка текущего объекта"""
        self.current_project = project_name
        self.create_project_directories(project_name)
        self.save_config()
        
    def get_all_projects(self) -> list:
        """Получение списка всех объектов"""
        if not self.projects_dir.exists():
            return ["Общий объект"]
            
        projects = []
        for item in self.projects_dir.iterdir():
            if item.is_dir():
                projects.append(item.name)
                
        if not projects:
            projects = ["Общий объект"]
            
        return sorted(projects)
    
    def create_new_project(self, project_name: str) -> bool:
        """Создание нового объекта"""
        try:
            # Проверяем что имя объекта валидное
            if not project_name or project_name.strip() == "":
                return False
                
            # Очищаем имя от недопустимых символов
            import re
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', project_name.strip())
            
            self.create_project_directories(clean_name)
            return True
        except Exception as e:
            print(f"Ошибка создания объекта: {e}")
            return False
    
    def delete_project(self, project_name: str) -> bool:
        """Удаление объекта"""
        try:
            if project_name == "Общий объект":
                return False  # Нельзя удалить основной объект
                
            project_dir = self.projects_dir / project_name
            if project_dir.exists():
                import shutil
                shutil.rmtree(project_dir)
                
                # Если удаляем текущий объект, переключаемся на общий
                if self.current_project == project_name:
                    self.set_current_project("Общий объект")
                    
            return True
        except Exception as e:
            print(f"Ошибка удаления объекта: {e}")
            return False
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            if self.config_file.exists():
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_project = config.get('current_project', 'Общий объект')
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            self.current_project = "Общий объект"
    
    def save_config(self):
        """Сохранение конфигурации"""
        try:
            import json
            config = {
                'current_project': self.current_project,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def save_analysis_result(self, result: dict) -> str:
        """
        Сохранение результата анализа в JSON файл
        
        Args:
            result: Результат анализа фото
            
        Returns:
            str: Путь к сохраненному файлу
        """
        dirs = self.get_project_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{timestamp}.json"
        filepath = dirs['data_dir'] / filename
        
        # Добавляем метаданные
        result_with_meta = {
            "timestamp": datetime.now().isoformat(),
            "project": self.current_project,
            "analysis": result
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_with_meta, f, ensure_ascii=False, indent=2)
            
        return str(filepath)
    
    def copy_photo_to_workspace(self, source_path: str) -> str:
        """
        Копирование фото в рабочую папку текущего объекта
        
        Args:
            source_path: Исходный путь к фото
            
        Returns:
            str: Новый путь к скопированному фото
        """
        dirs = self.get_project_directories()
        source = Path(source_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"defect_{timestamp}_{source.name}"
        destination = dirs['photos_dir'] / new_filename
        
        shutil.copy2(source, destination)
        return str(destination)
    
    def get_recent_analyses(self, limit=10, project_name: str = None) -> list:
        """
        Получение последних анализов для объекта
        
        Args:
            limit: Максимальное количество результатов
            project_name: Имя объекта (если None, то текущий)
            
        Returns:
            list: Список последних анализов
        """
        dirs = self.get_project_directories(project_name)
        json_files = list(dirs['data_dir'].glob("analysis_*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        results = []
        for file_path in json_files[:limit]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"Ошибка чтения файла {file_path}: {e}")
                
        return results
    
    def export_to_docx(self, analyses: list, output_filename: str = None) -> str:
        """
        Экспорт анализов в DOCX файл для текущего объекта
        
        Args:
            analyses: Список анализов для экспорта
            output_filename: Имя выходного файла
            
        Returns:
            str: Путь к созданному файлу
        """
        dirs = self.get_project_directories()
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_safe = self.current_project.replace(" ", "_")
            output_filename = f"defect_report_{project_safe}_{timestamp}.docx"
            
        output_path = dirs['reports_dir'] / output_filename
        
        # Здесь будем использовать существующий генератор документов
        # Пока просто создаем заглушку
        
        return str(output_path)
    
    def get_app_directory(self) -> str:
        """Получение основной папки приложения"""
        return str(self.app_dir)
    
    def cleanup_old_files(self, days_old=30, project_name: str = None):
        """
        Очистка старых файлов в объекте
        
        Args:
            days_old: Возраст файлов в днях для удаления
            project_name: Имя объекта (если None, то текущий)
        """
        import time
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        dirs = self.get_project_directories(project_name)
        for directory in [dirs['photos_dir'], dirs['data_dir']]:
            if directory.exists():
                for file_path in directory.iterdir():
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            print(f"Удален старый файл: {file_path}")
                        except Exception as e:
                            print(f"Ошибка удаления файла {file_path}: {e}")
                            
    def get_project_stats(self, project_name: str = None) -> dict:
        """
        Получение статистики по объекту
        
        Args:
            project_name: Имя объекта (если None, то текущий)
            
        Returns:
            dict: Статистика объекта
        """
        dirs = self.get_project_directories(project_name)
        
        stats = {
            'project_name': project_name or self.current_project,
            'photos_count': 0,
            'analyses_count': 0,
            'reports_count': 0,
            'last_activity': None
        }
        
        try:
            # Считаем фото
            if dirs['photos_dir'].exists():
                stats['photos_count'] = len(list(dirs['photos_dir'].glob("*")))
            
            # Считаем анализы
            if dirs['data_dir'].exists():
                stats['analyses_count'] = len(list(dirs['data_dir'].glob("analysis_*.json")))
            
            # Считаем отчеты
            if dirs['reports_dir'].exists():
                stats['reports_count'] = len(list(dirs['reports_dir'].glob("*.docx")))
            
            # Находим последнюю активность
            all_files = []
            for dir_path in dirs.values():
                if dir_path.exists():
                    all_files.extend(dir_path.rglob("*"))
            
            if all_files:
                latest_file = max(all_files, key=lambda x: x.stat().st_mtime if x.is_file() else 0)
                if latest_file.is_file():
                    stats['last_activity'] = datetime.fromtimestamp(latest_file.stat().st_mtime)
                    
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            
        return stats
    
    def get_building_wear(self, project_name: str = None) -> str:
        """
        Получение процента износа здания для объекта
        
        Args:
            project_name: Имя объекта (если None, то текущий)
            
        Returns:
            str: Процент износа в формате "XX%"
        """
        try:
            # Ищем файлы с данными об износе
            dirs = self.get_project_directories(project_name)
            wear_files = list(dirs['data_dir'].glob("wear_*.json"))
            
            if wear_files:
                # Берем самый свежий файл
                latest_wear_file = max(wear_files, key=lambda x: x.stat().st_mtime)
                with open(latest_wear_file, 'r', encoding='utf-8') as f:
                    wear_data = json.load(f)
                    total_wear = wear_data.get('total_wear_percentage', 0)
                    return f"{total_wear}%"
            else:
                # Если нет данных об износе, возвращаем заглушку
                return "Нет данных"
                
        except Exception as e:
            print(f"Ошибка получения износа здания: {e}")
            return "Ошибка"
    
    def save_building_wear(self, project_name: str, wear_percentage: float) -> bool:
        """
        Сохранение процента износа здания для объекта
        
        Args:
            project_name: Имя объекта
            wear_percentage: Процент износа (0-100)
            
        Returns:
            bool: True если успешно
        """
        try:
            dirs = self.get_project_directories(project_name)
            
            # Создаем данные об износе
            wear_data = {
                "timestamp": datetime.now().isoformat(),
                "project_name": project_name,
                "total_wear_percentage": wear_percentage,
                "calculation_method": "manual_input",
                "notes": "Введено вручную через интерфейс управления объектами"
            }
            
            # Сохраняем в файл
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wear_{timestamp}.json"
            filepath = dirs['data_dir'] / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(wear_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Износ здания сохранен: {project_name} - {wear_percentage}%")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения износа здания: {e}")
            return False
    
    def delete_building_wear(self, project_name: str) -> bool:
        """
        Удаление данных об износе здания для объекта
        
        Args:
            project_name: Имя объекта
            
        Returns:
            bool: True если успешно
        """
        try:
            dirs = self.get_project_directories(project_name)
            wear_files = list(dirs['data_dir'].glob("wear_*.json"))
            
            # Удаляем все файлы с данными об износе
            for wear_file in wear_files:
                wear_file.unlink()
                print(f"🗑️ Удален файл износа: {wear_file.name}")
            
            print(f"✅ Данные об износе удалены: {project_name}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления износа здания: {e}")
            return False
    
    def get_survey_date(self, project_name: str = None) -> str:
        """
        Получение даты обследования для объекта
        
        Args:
            project_name: Имя объекта (если None, то текущий)
            
        Returns:
            str: Дата в формате ДД.ММ.ГГГГ или пустая строка
        """
        try:
            # Ищем файлы с данными о дате обследования
            dirs = self.get_project_directories(project_name)
            survey_files = list(dirs['data_dir'].glob("survey_date_*.json"))
            
            if survey_files:
                # Берем самый свежий файл
                latest_survey_file = max(survey_files, key=lambda x: x.stat().st_mtime)
                with open(latest_survey_file, 'r', encoding='utf-8') as f:
                    survey_data = json.load(f)
                    return survey_data.get('survey_date', '')
            else:
                return ''
                
        except Exception as e:
            print(f"Ошибка получения даты обследования: {e}")
            return ''
    
    def save_survey_date(self, project_name: str, survey_date: str) -> bool:
        """
        Сохранение даты обследования для объекта
        
        Args:
            project_name: Имя объекта
            survey_date: Дата в формате ДД.ММ.ГГГГ
            
        Returns:
            bool: True если успешно
        """
        try:
            dirs = self.get_project_directories(project_name)
            
            # Создаем данные о дате обследования
            survey_data = {
                "timestamp": datetime.now().isoformat(),
                "project_name": project_name,
                "survey_date": survey_date,
                "input_method": "manual_input",
                "notes": "Введено вручную через интерфейс управления объектами"
            }
            
            # Сохраняем в файл
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"survey_date_{timestamp}.json"
            filepath = dirs['data_dir'] / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(survey_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Дата обследования сохранена: {project_name} - {survey_date}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения даты обследования: {e}")
            return False
    
    def delete_survey_date(self, project_name: str) -> bool:
        """
        Удаление данных о дате обследования для объекта
        
        Args:
            project_name: Имя объекта
            
        Returns:
            bool: True если успешно
        """
        try:
            dirs = self.get_project_directories(project_name)
            survey_files = list(dirs['data_dir'].glob("survey_date_*.json"))
            
            # Удаляем все файлы с данными о дате обследования
            for survey_file in survey_files:
                survey_file.unlink()
                print(f"🗑️ Удален файл даты обследования: {survey_file.name}")
            
            print(f"✅ Данные о дате обследования удалены: {project_name}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления даты обследования: {e}")
            return False
    
    def get_project_file(self, filename: str, project_name: str = None) -> Path:
        """
        Получение пути к файлу в папке проекта
        
        Args:
            filename: Имя файла
            project_name: Имя проекта (если None, то текущий)
            
        Returns:
            Path: Полный путь к файлу
        """
        if project_name is None:
            project_name = self.current_project
            
        dirs = self.get_project_directories(project_name)
        return dirs['data_dir'] / filename
    
    def get_global_projects(self) -> list:
        """Получение списка глобальных проектов"""
        try:
            projects_file = self.app_dir / "global_projects.json"
            if projects_file.exists():
                with open(projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('projects', ["Основной проект"])
            else:
                # Создаем файл с основным проектом
                default_projects = ["Основной проект"]
                self.save_global_projects(default_projects)
                return default_projects
        except Exception as e:
            print(f"Ошибка получения глобальных проектов: {e}")
            return ["Основной проект"]
    
    def save_global_projects(self, projects: list):
        """Сохранение списка глобальных проектов"""
        try:
            projects_file = self.app_dir / "global_projects.json"
            data = {
                "projects": projects,
                "last_updated": datetime.now().isoformat()
            }
            with open(projects_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения глобальных проектов: {e}")
    
    def add_global_project(self, project_name: str) -> bool:
        """Добавление нового глобального проекта"""
        try:
            projects = self.get_global_projects()
            if project_name not in projects:
                projects.append(project_name)
                self.save_global_projects(projects)
                return True
            return False
        except Exception as e:
            print(f"Ошибка добавления глобального проекта: {e}")
            return False
    
    def remove_global_project(self, project_name: str) -> bool:
        """Удаление глобального проекта"""
        try:
            projects = self.get_global_projects()
            if project_name in projects:
                projects.remove(project_name)
                self.save_global_projects(projects)
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления глобального проекта: {e}")
            return False
    
    def get_objects_for_project(self, project_name: str) -> list:
        """Получение списка объектов для конкретного проекта"""
        try:
            objects_file = self.app_dir / f"project_{project_name}_objects.json"
            if objects_file.exists():
                with open(objects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('objects', [])
            else:
                # Если это основной проект, возвращаем существующие объекты
                if project_name == "Основной проект":
                    existing_objects = self.get_all_projects()
                    self.save_objects_for_project(project_name, existing_objects)
                    return existing_objects
                else:
                    # Для новых проектов возвращаем пустой список
                    self.save_objects_for_project(project_name, [])
                    return []
        except Exception as e:
            print(f"Ошибка получения объектов для проекта {project_name}: {e}")
            return []
    
    def save_objects_for_project(self, project_name: str, objects: list):
        """Сохранение списка объектов для проекта"""
        try:
            objects_file = self.app_dir / f"project_{project_name}_objects.json"
            data = {
                "project": project_name,
                "objects": objects,
                "last_updated": datetime.now().isoformat()
            }
            with open(objects_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения объектов для проекта {project_name}: {e}")
    
    def add_object_to_project(self, project_name: str, object_name: str) -> bool:
        """Добавление объекта к проекту"""
        try:
            objects = self.get_objects_for_project(project_name)
            if object_name not in objects:
                objects.append(object_name)
                self.save_objects_for_project(project_name, objects)
                # Создаем папки для нового объекта
                self.create_project_directories(object_name)
                return True
            return False
        except Exception as e:
            print(f"Ошибка добавления объекта к проекту: {e}")
            return False
    
    def remove_object_from_project(self, project_name: str, object_name: str) -> bool:
        """Удаление объекта из проекта"""
        try:
            objects = self.get_objects_for_project(project_name)
            if object_name in objects:
                objects.remove(object_name)
                self.save_objects_for_project(project_name, objects)
                return True
            return False
        except Exception as e:
            print(f"Ошибка удаления объекта из проекта: {e}")
            return False