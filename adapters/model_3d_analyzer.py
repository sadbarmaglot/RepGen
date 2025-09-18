"""
Анализатор 3D моделей для обнаружения строительных дефектов
Поддерживает форматы: GLB, OBJ, PLY, STL, USDZ
"""

import os
import json
import tempfile
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import base64

# Настройка логирования для 3D анализа
model_3d_logger = logging.getLogger('model_3d')
model_3d_logger.setLevel(logging.INFO)

if not model_3d_logger.handlers:
    model_3d_handler = logging.FileHandler('model_3d_analysis.log', encoding='utf-8')
    model_3d_handler.setLevel(logging.INFO)
    model_3d_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    model_3d_handler.setFormatter(model_3d_formatter)
    model_3d_logger.addHandler(model_3d_handler)
    
    # Консольный вывод
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(model_3d_formatter)
    model_3d_logger.addHandler(console_handler)

try:
    import trimesh
    import pygltflib
    HAS_3D_SUPPORT = True
except ImportError:
    HAS_3D_SUPPORT = False

from .ai_adapter import get_openai_client
from common.defects_db import SYSTEM_MESSAGE


class Model3DAnalyzer:
    """Анализатор 3D моделей строительных объектов"""
    
    # Специальный промпт для 3D анализа
    PROMPT_3D = """
    Вы анализируете строительный объект по множественным видам 3D модели, созданной сканированием.
    
    Изучите каждое изображение и найдите:
    1. Видимые дефекты (трещины, сколы, разрушения, коррозия)
    2. Повреждения конструкций (стены, перекрытия, колонны, балки)  
    3. Проблемы покрытий (отслоения, высолы, пятна)
    4. Деформации и смещения элементов
    5. Признаки протечек или увлажнения
    
    Для каждого найденного дефекта укажите:
    - Тип повреждения
    - Примерное местоположение
    - Степень серьезности
    - Краткое описание
    
    Ответ предоставьте в формате JSON:
    {
        "defects": [
            {
                "type": "тип дефекта",
                "location": "где находится", 
                "severity": "критический/серьезный/незначительный",
                "description": "подробное описание"
            }
        ],
        "overall_condition": "общая оценка состояния объекта",
        "analysis_summary": "краткий итоговый анализ"
    }
    """
    
    def __init__(self):
        """Инициализация анализатора"""
        if not HAS_3D_SUPPORT:
            raise ImportError("Для работы с 3D моделями требуются библиотеки: trimesh, pygltflib")
    
    def is_supported_format(self, file_path: str) -> bool:
        """Проверяет, поддерживается ли формат файла"""
        supported_extensions = ['.glb', '.gltf', '.obj', '.ply', '.stl', '.usdz']
        return Path(file_path).suffix.lower() in supported_extensions
    
    def load_3d_model(self, file_path: str) -> Optional[trimesh.Scene]:
        """Загружает 3D модель из файла"""
        if not self.is_supported_format(file_path):
            raise ValueError(f"Неподдерживаемый формат файла: {file_path}")
        
        try:
            # Используем trimesh для загрузки различных форматов
            if file_path.lower().endswith('.glb'):
                # Специальная обработка для GLB файлов
                scene = trimesh.load(file_path, file_type='glb')
            else:
                scene = trimesh.load(file_path)
            
            # Если загружен одиночный меш, конвертируем в сцену
            if hasattr(scene, 'vertices'):
                new_scene = trimesh.Scene()
                new_scene.add_geometry(scene)
                scene = new_scene
            
            print(f"✅ Загружена 3D сцена с {len(scene.geometry)} объектами")
            return scene
            
        except Exception as e:
            print(f"❌ Ошибка загрузки 3D модели: {e}")
            return None
    
    def generate_camera_positions(self, scene: trimesh.Scene, num_views: int = 8) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Генерирует позиции камеры для съемки модели с разных углов"""
        bounds = scene.bounds
        center = bounds.mean(axis=0)
        size = np.max(bounds[1] - bounds[0])
        
        # Радиус камеры (увеличиваем для лучшего обзора)
        camera_distance = size * 2.5
        
        positions = []
        
        # Горизонтальные виды с разных углов
        for i in range(num_views):
            angle = 2 * np.pi * i / num_views
            
            # Позиция камеры
            cam_x = center[0] + camera_distance * np.cos(angle)
            cam_y = center[1] + camera_distance * np.sin(angle)
            cam_z = center[2] + size * 0.3  # Немного поднимаем камеру
            
            camera_pos = np.array([cam_x, cam_y, cam_z])
            look_at = center
            
            positions.append((camera_pos, look_at))
        
        return positions
    
    def render_views(self, scene: trimesh.Scene, camera_positions: List[Tuple[np.ndarray, np.ndarray]], 
                    resolution: Tuple[int, int] = (1024, 768)) -> List[str]:
        """Рендерит виды сцены и возвращает пути к сохраненным изображениям"""
        rendered_images = []
        
        try:
            # Создаем временную папку для рендеров
            temp_dir = tempfile.mkdtemp(prefix="3d_analysis_")
            
            # Пробуем использовать matplotlib для рендеринга (headless)
            import matplotlib
            matplotlib.use('Agg')  # Без GUI
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            
            for i, (camera_pos, look_at) in enumerate(camera_positions):
                try:
                    # Создаем 3D plot с matplotlib
                    fig = plt.figure(figsize=(10, 8))
                    ax = fig.add_subplot(111, projection='3d')
                    
                    # Получаем меши из сцены
                    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                    
                    for geometry_name, geometry in scene.geometry.items():
                        if hasattr(geometry, 'vertices') and hasattr(geometry, 'faces'):
                            vertices = geometry.vertices
                            faces = geometry.faces
                            
                            # Создаем коллекцию треугольников для быстрого рендеринга
                            face_subset = faces[:min(2000, len(faces))]  # Ограничиваем для производительности
                            triangles = vertices[face_subset]
                            
                            # Добавляем все треугольники одной коллекцией
                            collection = Poly3DCollection(triangles, alpha=0.8, facecolor='lightblue', edgecolor='navy', linewidth=0.1)
                            ax.add_collection3d(collection)
                    
                    # Настраиваем камеру
                    ax.view_init(elev=20, azim=i * 45)  # Разные углы обзора
                    
                    # Настраиваем оси
                    bounds = scene.bounds
                    ax.set_xlim(bounds[0, 0], bounds[1, 0])
                    ax.set_ylim(bounds[0, 1], bounds[1, 1])
                    ax.set_zlim(bounds[0, 2], bounds[1, 2])
                    
                    # Скрываем оси для чистого изображения
                    ax.set_xticks([])
                    ax.set_yticks([])
                    ax.set_zticks([])
                    
                    # Сохраняем изображение
                    image_path = os.path.join(temp_dir, f"view_{i:02d}.png")
                    plt.savefig(image_path, dpi=150, bbox_inches='tight', facecolor='white')
                    plt.close(fig)
                    
                    rendered_images.append(image_path)
                    print(f"✅ Рендер {i+1}: {image_path}")
                    
                except Exception as e:
                    print(f"❌ Ошибка рендеринга вида {i+1}: {e}")
                    continue
            
            return rendered_images
            
        except Exception as e:
            print(f"❌ Ошибка рендеринга: {e}")
            return []
    
    def extract_orthographic_projections(self, scene: trimesh.Scene) -> List[str]:
        """Создает ортогональные проекции (виды спереди, сбоку, сверху)"""
        projections = []
        
        try:
            temp_dir = tempfile.mkdtemp(prefix="3d_ortho_")
            
            # Используем matplotlib для ортогональных проекций
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            
            # Получаем границы модели
            bounds = scene.bounds
            
            # Определяем ракурсы для ортогональных проекций
            views = [
                ("front", (0, 0)),    # Вид спереди
                ("side", (0, 90)),    # Вид сбоку
                ("top", (90, 0))      # Вид сверху
            ]
            
            for name, (elev, azim) in views:
                try:
                    # Создаем 3D plot
                    fig = plt.figure(figsize=(12, 12))
                    ax = fig.add_subplot(111, projection='3d')
                    
                    # Получаем меши из сцены
                    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                    
                    for geometry_name, geometry in scene.geometry.items():
                        if hasattr(geometry, 'vertices') and hasattr(geometry, 'faces'):
                            vertices = geometry.vertices
                            faces = geometry.faces
                            
                            # Создаем коллекцию треугольников для быстрого рендеринга
                            face_subset = faces[:min(2000, len(faces))]
                            triangles = vertices[face_subset]
                            
                            # Добавляем треугольники
                            collection = Poly3DCollection(triangles, alpha=0.8, facecolor='lightgreen', edgecolor='darkgreen', linewidth=0.1)
                            ax.add_collection3d(collection)
                    
                    # Настраиваем ортогональную проекцию
                    ax.view_init(elev=elev, azim=azim)
                    
                    # Настраиваем оси
                    ax.set_xlim(bounds[0, 0], bounds[1, 0])
                    ax.set_ylim(bounds[0, 1], bounds[1, 1])
                    ax.set_zlim(bounds[0, 2], bounds[1, 2])
                    
                    # Скрываем оси для технического чертежа
                    ax.set_xticks([])
                    ax.set_yticks([])
                    ax.set_zticks([])
                    
                    # Сохраняем проекцию
                    image_path = os.path.join(temp_dir, f"ortho_{name}.png")
                    plt.savefig(image_path, dpi=150, bbox_inches='tight', facecolor='white')
                    plt.close(fig)
                    
                    projections.append(image_path)
                    print(f"✅ Ортогональная проекция {name}: {image_path}")
                    
                except Exception as e:
                    print(f"❌ Ошибка создания проекции {name}: {e}")
                    continue
            
            return projections
            
        except Exception as e:
            print(f"❌ Ошибка создания ортогональных проекций: {e}")
            return []
    
    def analyze_3d_model(self, file_path: str, context: str = "") -> Dict:
        """Основная функция анализа 3D модели"""
        try:
            print(f"🎯 Начинаю анализ 3D модели: {file_path}")
            
            # 1. Загружаем модель
            scene = self.load_3d_model(file_path)
            if scene is None:
                return {
                    'success': False,
                    'error': 'Не удалось загрузить 3D модель'
                }
            
            # 2. Генерируем позиции камеры
            camera_positions = self.generate_camera_positions(scene, 8)
            
            # 3. Рендерим виды
            print("📸 Генерирую виды модели...")
            rendered_views = self.render_views(scene, camera_positions)
            
            # 4. Создаем ортогональные проекции
            print("📐 Создаю ортогональные проекции...")
            projections = self.extract_orthographic_projections(scene)
            
            # Собираем все изображения
            all_images = rendered_views + projections
            
            if not all_images:
                return {
                    'success': False,
                    'error': 'Не удалось создать изображения для анализа'
                }
            
            # 5. Анализируем через GPT-4o группами
            print(f"🤖 Анализирую {len(all_images)} изображений группами по 3...")
            analysis_result = self.analyze_images_with_ai(all_images, context)
            
            # 6. Очищаем временные файлы
            self.cleanup_temp_files(all_images)
            
            return {
                'success': True,
                'analysis': analysis_result,
                'num_views_analyzed': len(all_images),
                'model_info': {
                    'file_path': file_path,
                    'geometry_count': len(scene.geometry) if hasattr(scene, 'geometry') else 1,
                    'bounds': scene.bounds.tolist() if hasattr(scene, 'bounds') else None
                }
            }
            
        except Exception as e:
            print(f"❌ Ошибка анализа 3D модели: {e}")
            return {
                'success': False,
                'error': f'Ошибка анализа: {str(e)}'
            }
    
    def analyze_images_with_ai(self, image_paths: List[str], context: str) -> Dict:
        """Анализирует изображения ГРУППАМИ - как в оригинальном боте"""
        model_3d_logger.info(f"🚀 Начинаю анализ {len(image_paths)} изображений группами по 3")
        
        try:
            client = get_openai_client()
            all_results = []
            
            # Анализируем группами по 3 изображения (как в оригинальном боте)
            batch_size = 3
            
            for batch_start in range(0, len(image_paths), batch_size):
                batch_end = min(batch_start + batch_size, len(image_paths))
                batch_images = image_paths[batch_start:batch_end]
                
                model_3d_logger.info(f"📦 Группа {batch_start//batch_size + 1}: анализирую {len(batch_images)} изображений")
                
                # Подготавливаем содержимое для группы
                content = [{"type": "text", "text": f"""Проанализируй эти изображения 3D модели здания (группа {batch_start//batch_size + 1}):

{context if context else "Строительный объект"}

Найди и опиши видимые дефекты, повреждения и проблемы. 
Ответ в формате JSON:
{{
    "defects_found": ["дефект 1", "дефект 2"],
    "condition": "общее состояние",
    "details": "детальное описание"
}}"""}]
                
                # Добавляем изображения группы
                for i, image_path in enumerate(batch_images):
                    try:
                        with open(image_path, "rb") as image_file:
                            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                        
                        view_type = "ортогональная проекция" if "ortho_" in os.path.basename(image_path) else f"вид #{batch_start + i + 1}"
                        
                        content.append({
                            "type": "text",
                            "text": f"--- {view_type.upper()} ---"
                        })
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        })
                        
                    except Exception as e:
                        model_3d_logger.error(f"⚠️ Ошибка обработки изображения {image_path}: {e}")
                        continue
                
                # Отправляем группу к GPT-4o
                model_3d_logger.info(f"🤖 Отправляю группу {batch_start//batch_size + 1} к OpenAI...")
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        SYSTEM_MESSAGE,
                        {"role": "user", "content": content}
                    ],
                    max_tokens=1500,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                # Логируем успешный ответ
                tokens_used = response.usage.total_tokens if response.usage else 0
                model_3d_logger.info(f"✅ Группа {batch_start//batch_size + 1} проанализирована. Токенов: {tokens_used}")
                
                # Парсим ответ группы
                try:
                    ai_response = response.choices[0].message.content.strip()
                    group_result = json.loads(ai_response)
                    all_results.append(group_result)
                    
                    defects_count = len(group_result.get('defects_found', []))
                    model_3d_logger.info(f"📋 Группа {batch_start//batch_size + 1}: найдено {defects_count} дефектов")
                    
                except json.JSONDecodeError as e:
                    model_3d_logger.error(f"❌ Ошибка парсинга JSON группы {batch_start//batch_size + 1}: {e}")
                    all_results.append({
                        'defects_found': [],
                        'condition': 'Ошибка парсинга',
                        'details': ai_response[:200] + '...' if len(ai_response) > 200 else ai_response
                    })
            
            # Агрегируем результаты всех групп
            model_3d_logger.info(f"🔄 Агрегирую результаты {len(all_results)} групп...")
            final_result = self._aggregate_batch_results(all_results, context)
            
            model_3d_logger.info(f"✅ Анализ завершен! Найдено дефектов: {len(final_result.get('defects', []))}")
            return final_result
            
        except Exception as e:
            model_3d_logger.error(f"❌ Ошибка ИИ анализа: {str(e)}")
            print(f"❌ Ошибка ИИ анализа: {e}")
            return {
                'defects': [],
                'overall_condition': 'Ошибка анализа',
                'analysis_summary': f'Произошла ошибка: {str(e)}',
                'error': str(e)
            }
    
    def _aggregate_batch_results(self, results: List[Dict], context: str) -> Dict:
        """Агрегирует результаты анализа всех групп изображений"""
        all_defects = []
        all_conditions = []
        all_details = []
        
        # Собираем все дефекты и наблюдения из всех групп
        for i, result in enumerate(results):
            if "error" in result or not result:
                continue
                
            # Извлекаем дефекты
            defects = result.get('defects_found', [])
            all_defects.extend(defects)
            
            # Собираем состояния
            condition = result.get('condition', '')
            if condition:
                all_conditions.append(f"Группа {i+1}: {condition}")
            
            # Собираем детали
            details = result.get('details', '')
            if details:
                all_details.append(details)
        
        # Удаляем дубликаты дефектов
        unique_defects = list(set(all_defects))
        
        # Формируем итоговый результат
        return {
            "defects": [
                {
                    "type": defect,
                    "location": "По результатам 3D анализа",
                    "severity": "Требует детального обследования",
                    "description": f"Обнаружено при анализе 3D модели: {defect}"
                }
                for defect in unique_defects[:15]  # Ограничиваем до 15 дефектов
            ],
            "overall_condition": f"Проанализировано {len(results)} групп изображений 3D модели. Выявлено {len(unique_defects)} типов дефектов.",
            "analysis_summary": f"3D анализ объекта: {context}. " + " ".join(all_details[:3])
        }
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """Очищает временные файлы"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                # Также удаляем временные папки если они пустые
                temp_dir = os.path.dirname(file_path)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
                    
            except Exception as e:
                print(f"⚠️ Не удалось удалить временный файл {file_path}: {e}")


def check_dependencies() -> Tuple[bool, List[str]]:
    """Проверяет наличие необходимых зависимостей для 3D анализа"""
    missing = []
    
    try:
        import trimesh
    except ImportError:
        missing.append('trimesh[easy]')
    
    try:
        import pygltflib
    except ImportError:
        missing.append('pygltflib')
        
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
        
    try:
        import matplotlib
    except ImportError:
        missing.append('matplotlib')
    
    return len(missing) == 0, missing


def install_3d_dependencies():
    """Устанавливает зависимости для 3D анализа"""
    import subprocess
    import sys
    import os
    
    dependencies = [
        "'trimesh[easy]'",  # Кавычки для zsh
        "pygltflib", 
        "Pillow", 
        "numpy", 
        "matplotlib>=3.0.0"
    ]
    
    print("📦 Устанавливаю зависимости для 3D анализа...")
    
    try:
        # Формируем команду установки
        cmd = [sys.executable, "-m", "pip", "install"] + dependencies
        print(f"Выполняю: {' '.join(cmd)}")
        
        # Выполняем установку
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 минут максимум
        )
        
        if result.returncode == 0:
            print("🎉 Все зависимости установлены!")
            print(result.stdout)
            return True
        else:
            print(f"❌ Ошибка установки: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Тайм-аут установки (более 5 минут)")
        return False
    except Exception as e:
        print(f"❌ Критическая ошибка установки: {e}")
        return False