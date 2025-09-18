
import io
import os
import base64
import gradio as gr

from typing import List, Dict, Any
from PIL import Image

from api.client import DefectAnalysisClient
from api.models.config import AnalysisConfig


class ModelComparisonInterface:
    def __init__(self, api_url):
        self.api_client = DefectAnalysisClient(api_url)
        self.available_models = {
            "openai": ["gpt-4o-mini", "gpt-4o"],
            "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"]
        }
        self.current_results = []  # Храним текущие результаты
        self.current_image_index = 0  # Индекс текущего изображения

        
    def get_model_options(self) -> List[str]:
        """Получаем список всех доступных моделей"""
        all_models = []
        for _, models in self.available_models.items():
            for model in models:
                all_models.append(f"{model}")
        return all_models
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Конвертируем PIL Image в base64 строку для встраивания в HTML"""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            print(f"Ошибка конвертации изображения в base64: {e}")
            return ""
    
    def create_single_image_result_display(self, image: Image.Image, filename: str, results: List[Dict[str, Any]]) -> str:
        """Создает отображение результатов для одного изображения"""
        if not results:
            return f"**❌ Нет результатов анализа для {filename}**"
        
        img_base64 = self.image_to_base64(image)
        
        html_result = f"## 📸 <span style='color: #666666;'>{filename}</span>\n\n"
        
        if img_base64:
            html_result += f'<img src="{img_base64}" style="max-width: 600px; height: auto; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin: 15px 0; border: 3px solid #fff;" alt="{filename}">\n\n'
        
        html_result += "---\n\n"
        html_result += "### 🔍 <span style='color: #666666;'>Результаты анализа по моделям:</span>\n\n"
        
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get('status') == 'success':
                model_name = result.get('model', f'Модель {i+1}')
                description = result.get('description', 'Нет описания')
                recommendation = result.get('recommendation', 'Нет рекомендаций')
                
                html_result += f"<div class='model-result-card'>\n"
                html_result += f"**🤖 {model_name}**\n\n"
                html_result += f"**📝 Описание:**\n{description}\n\n"
                html_result += f"**💡 Рекомендации:**\n{recommendation}\n\n"
                html_result += "</div>\n\n"
                
            elif isinstance(result, dict) and 'description' in result:
                # Обрабатываем случай, когда статус не указан, но есть описание
                model_name = result.get('model', f'Модель {i+1}')
                description = result.get('description', 'Нет описания')
                recommendation = result.get('recommendation', 'Нет рекомендаций')
                
                html_result += f"<div class='model-result-card'>\n"
                html_result += f"**🤖 {model_name}**\n\n"
                html_result += f"**📝 Описание:**\n{description}\n\n"
                html_result += f"**💡 Рекомендации:**\n{recommendation}\n\n"
                html_result += "</div>\n\n"
                
            elif isinstance(result, Exception):
                html_result += f"<div class='model-result-card error-card'>\n"
                html_result += f"**❌ Ошибка анализа модели:**\n{str(result)}\n\n"
                html_result += "</div>\n\n"
            
            else:
                html_result += f"<div class='model-result-card warning-card'>\n"
                html_result += f"**⚠️ Модель {result.get('model', 'Неизвестная')}:**\nСтатус: {result.get('status', 'Неизвестно')}\n\n"
                html_result += "</div>\n\n"
        
        return html_result

    async def compare_models_multiple_images(self, image_files, selected_models: List[str], temperature: float, max_tokens: int) -> tuple:
        """Сравниваем результаты анализа нескольких изображений через batch workflow
        
        Оптимизированная логика:
        1. Загружаем все изображения одним запросом
        2. Для каждой модели анализируем уже загруженные изображения по их URL
        3. Это исключает повторную загрузку изображений для каждой модели
        """
        if not image_files or not selected_models:
            return "Пожалуйста, загрузите изображения и выберите модели для анализа.", "0 / 0"
        
        if not isinstance(image_files, list):
            image_files = [image_files]
        
        valid_files = [f for f in image_files if f is not None]
        
        if not valid_files:
            return "❌ Не найдено валидных изображений для анализа.", "0 / 0"
        
        try:
            # Преобразуем файлы в PIL Images
            images = []
            filenames = []
            
            for image_file in valid_files:
                try:
                    original_filename = os.path.basename(image_file.name) if hasattr(image_file, 'name') else f"image_{len(images) + 1}"
                    filenames.append(original_filename)
                    
                    if hasattr(image_file, 'name'):
                        image = Image.open(image_file.name)
                    else:
                        image = image_file
                    
                    images.append(image)
                except Exception as e:
                    print(f"Ошибка обработки изображения {image_file}: {e}")
                    continue
            
            if not images:
                return "❌ Не удалось обработать ни одного изображения.", "0 / 0"
            
            all_results = []
            
            print(f"📤 Загружаем {len(images)} изображений...")
            upload_results = await self.api_client.upload_images(images)
            
            image_infos = [
                {
                    "url": result["signed_url"], 
                    "mime_type": result["mime_type"]
                } for result in upload_results
            ]

            if not image_infos:
                return "❌ Не удалось загрузить изображения для анализа.", "0 / 0"
            
            print(f"✅ Изображения загружены. Анализируем {len(image_infos)} изображений {len(selected_models)} моделями...")
            
            for model in selected_models:
                try:
                    print(f"🔍 Анализируем {len(image_infos)} изображений моделью {model}...")
                    
                    config = AnalysisConfig(
                        model_name=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    analysis_results = await self.api_client.analyze_images(image_infos, config)
                    
                    if analysis_results and len(analysis_results) > 0:
                        if len(analysis_results) == len(image_infos):
                            for i, (image, filename) in enumerate(zip(images, filenames)):
                                analysis_result = analysis_results[i]
                                
                                if analysis_result.get('status') == 'success' or 'description' in analysis_result:
                                    analysis_result['model'] = model
                                    
                                    image_result = next((r for r in all_results if r['filename'] == filename), None)
                                    if image_result is None:
                                        image_result = {
                                            'image': image,
                                            'filename': filename,
                                            'results': []
                                        }
                                        all_results.append(image_result)
                                    
                                    image_result['results'].append(analysis_result)
                                else:
                                    # Обрабатываем ошибку
                                    error_msg = analysis_result.get('error', 'Неизвестная ошибка')
                                    error_result = Exception(f"Ошибка модели {model}: {error_msg}")
                                    
                                    # Ищем или создаем запись для этого изображения
                                    image_result = next((r for r in all_results if r['filename'] == filename), None)
                                    if image_result is None:
                                        image_result = {
                                            'image': image,
                                            'filename': filename,
                                            'results': []
                                        }
                                        all_results.append(image_result)
                                    
                                    image_result['results'].append(error_result)
                        else:
                            for i, (image, filename) in enumerate(zip(images, filenames)):
                                error_result = Exception(f"Ошибка модели {model}: Неожиданное количество результатов")
                                
                                image_result = next((r for r in all_results if r['filename'] == filename), None)
                                if image_result is None:
                                    image_result = {
                                        'image': image,
                                        'filename': filename,
                                        'results': []
                                    }
                                    all_results.append(image_result)
                                
                                image_result['results'].append(error_result)
                    else:
                        for i, (image, filename) in enumerate(zip(images, filenames)):
                            error_result = Exception(f"Ошибка модели {model}: Нет результатов анализа")
                            
                            image_result = next((r for r in all_results if r['filename'] == filename), None)
                            if image_result is None:
                                image_result = {
                                    'image': image,
                                    'filename': filename,
                                    'results': []
                                }
                                all_results.append(image_result)
                            
                            image_result['results'].append(error_result)
                            
                except Exception as e:
                    for i, (image, filename) in enumerate(zip(images, filenames)):
                        error_result = Exception(f"Ошибка модели {model}: {str(e)}")
                        
                        image_result = next((r for r in all_results if r['filename'] == filename), None)
                        if image_result is None:
                            image_result = {
                                'image': image,
                                'filename': filename,
                                'results': []
                            }
                            all_results.append(image_result)
                        
                        image_result['results'].append(error_result)
            
            print(f"✅ Анализ завершен! Обработано {len(all_results)} изображений для {len(selected_models)} моделей (загрузка: 1 раз)")
            
            self.current_results = all_results
            self.current_image_index = 0
            
            if not all_results:
                return "❌ Не удалось проанализировать ни одного изображения.", "0 / 0"
            
            first_result = all_results[0]
            display_result = self.create_single_image_result_display(
                first_result['image'], 
                first_result['filename'], 
                first_result['results']
            )
            
            counter_display = f"1 / {len(all_results)}"
            return display_result, counter_display
            
        except Exception as e:
            return f"**❌ Критическая ошибка анализа:**\n{str(e)}", "0 / 0"
    
    def navigate_to_image(self, direction: str, current_index: int, total_images: int) -> tuple:
        """Навигация между изображениями"""
        if not self.current_results:
            return "**📋 Нет результатов для навигации**", "0 / 0"
        
        if direction == "prev":
            new_index = max(0, current_index - 1)
        else:
            new_index = min(len(self.current_results) - 1, current_index + 1)
        
        self.current_image_index = new_index
        
        current_result = self.current_results[new_index]
        display_result = self.create_single_image_result_display(
            current_result['image'],
            current_result['filename'],
            current_result['results']
        )
        
        counter_display = f"{new_index + 1} / {len(self.current_results)}"
        
        return display_result, counter_display

    def get_current_image_display(self) -> tuple:
        """Получает отображение текущего изображения"""
        if not self.current_results:
            return "**📋 Нет результатов для отображения**", "0 / 0"
        
        current_result = self.current_results[self.current_image_index]
        display_result = self.create_single_image_result_display(
            current_result['image'],
            current_result['filename'],
            current_result['results']
        )
        
        counter_display = f"{self.current_image_index + 1} / {len(self.current_results)}"
        
        return display_result, counter_display
    
    def create_interface(self):
        """Создаем Gradio интерфейс"""
        
        css = """
        .markdown-analysis-results img {
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            max-width: 600px;
            height: auto;
            margin: 15px 0;
            border: 3px solid #fff;
        }
        .markdown-analysis-results {
            line-height: 1.7;
            font-size: 14px;
            color: #000000;
        }
        .markdown-analysis-results h1,
        .markdown-analysis-results h2,
        .markdown-analysis-results h3,
        .markdown-analysis-results h4,
        .markdown-analysis-results h5,
        .markdown-analysis-results h6 {
            color: #000000;
        }
        .markdown-analysis-results p,
        .markdown-analysis-results div,
        .markdown-analysis-results span {
            color: #000000;
        }
        .markdown-analysis-results strong,
        .markdown-analysis-results b {
            color: #000000;
        }
        .markdown-analysis-results .description,
        .markdown-analysis-results .recommendation {
            color: #000000;
        }
        .navigation-controls {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin: 25px 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        .image-counter {
            font-weight: bold;
            color: #fff;
            padding: 8px 15px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(10px);
            font-size: 14px;
        }
        .model-result-card {
            border: 2px solid #e1e5e9;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            position: relative;
            overflow: hidden;
            color: #000000;
        }
        .model-result-card * {
            color: #000000;
        }
        .model-result-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }
        .model-result-card:hover {
            border-color: #667eea;
            box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }
        .model-result-card:hover::before {
            transform: scaleX(1);
        }
        .model-result-card.selected {
            border-color: #4CAF50;
            background: linear-gradient(145deg, #f0f8f0 0%, #e8f5e8 100%);
            box-shadow: 0 8px 30px rgba(76, 175, 80, 0.25);
            transform: translateY(-2px);
        }
        .model-result-card.selected::before {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            transform: scaleX(1);
        }
        .model-result-card.selected .radio-button-group input[type="radio"] {
            filter: drop-shadow(0 2px 6px rgba(76, 175, 80, 0.4));
        }
        .model-result-card.selected .radio-button-group input[type="radio"]:checked {
            filter: drop-shadow(0 2px 8px rgba(76, 175, 80, 0.6));
        }
        .radio-button-group {
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .radio-button-group input[type="radio"] {
            margin: 0;
            transform: scale(1.5);
            accent-color: #667eea;
            cursor: pointer;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
        }
        .radio-button-group input[type="radio"]:checked {
            filter: drop-shadow(0 2px 6px rgba(102, 126, 234, 0.4));
        }
        .radio-button-group input[type="radio"]:focus {
            outline: 2px solid #667eea;
            outline-offset: 2px;
        }
        .radio-button-group input[type="radio"]:hover {
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
        }
        .radio-button-group label {
            font-weight: 600;
            color: #2c3e50;
            cursor: pointer;
            font-size: 16px;
            padding: 10px 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.2);
        }
        .radio-button-group label:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            border-color: rgba(255, 255, 255, 0.4);
        }
        .error-card {
            border-color: #f44336;
            background: linear-gradient(145deg, #ffebee 0%, #ffcdd2 100%);
        }
        .error-card::before {
            background: linear-gradient(90deg, #f44336, #d32f2f);
        }
        .error-card .radio-button-group input[type="radio"] {
            filter: drop-shadow(0 2px 4px rgba(244, 67, 54, 0.3));
        }
        .warning-card {
            border-color: #ff9800;
            background: linear-gradient(145deg, #fff3e0 0%, #ffe0b2 100%);
        }
        .warning-card::before {
            background: linear-gradient(90deg, #ff9800, #f57c00);
        }
        .warning-card .radio-button-group input[type="radio"] {
            filter: drop-shadow(0 2px 4px rgba(255, 152, 0, 0.3));
        }
        """
        
        with gr.Blocks(title="Сравнение Vision Моделей", theme=gr.themes.Soft(), css=css) as interface:
            gr.Markdown("# 🔍 Сравнение результатов анализа изображений разными Vision моделями")
            gr.Markdown("### 🚀 Загрузите одно или несколько изображений и выберите модели для сравнения результатов анализа. Результаты будут показаны по одному изображению с возможностью выбора лучшей модели.")
            
            with gr.Row():
                        with gr.Column(scale=1):

                            images_input = gr.File(
                                label="📁 Загрузите изображения для анализа",
                                file_count="multiple",
                                file_types=["image"],
                                height=300
                            )
                            
                            model_checkboxes = gr.CheckboxGroup(
                                choices=self.get_model_options(),
                                label="🤖 Выберите модели для анализа",
                                value=self.get_model_options()[:2] if len(self.get_model_options()) >= 2 else self.get_model_options()
                            )

                            with gr.Accordion("⚙️ Настройки анализа", open=False):
                                temperature = gr.Slider(
                                    minimum=0.0,
                                    maximum=2.0,
                                    value=0.2,
                                    step=0.1,
                                    label="🌡️ Температура (креативность)"
                                )
                                max_tokens = gr.Slider(
                                    minimum=100,
                                    maximum=4096,
                                    value=4096,
                                    step=100,
                                    label="🔢 Максимум токенов"
                                )
                            
                            analyze_btn = gr.Button(
                                "🚀 Запустить анализ изображений",
                                variant="primary",
                                size="lg"
                            )
                        
                        with gr.Column(scale=2):
                            results_output = gr.Markdown(
                                label="🔍 Результаты анализа изображений",
                                value="📋 Результаты анализа появятся здесь...",
                                elem_classes=["markdown-analysis-results"]
                            )
                            
                            with gr.Row():
                                prev_btn = gr.Button("⬅️ Предыдущее", variant="secondary", size="sm")
                                image_counter = gr.Markdown(
                                    value="0 / 0",
                                    elem_classes=["image-counter"]
                                )
                                next_btn = gr.Button("Следующее ➡️", variant="secondary", size="sm")
                                
            analyze_btn.click(
                fn=self.compare_models_multiple_images,
                inputs=[images_input, model_checkboxes, temperature, max_tokens],
                outputs=[results_output, image_counter]
            )
            
            prev_btn.click(
                fn=lambda: self.navigate_to_image("prev", self.current_image_index, len(self.current_results)),
                outputs=[results_output, image_counter]
            )
            
            next_btn.click(
                fn=lambda: self.navigate_to_image("next", self.current_image_index, len(self.current_results)),
                outputs=[results_output, image_counter]
            )
                

        
        return interface

def get_api_url() -> str:
    """Получаем URL API из переменных окружения или используем значение по умолчанию"""
    return os.getenv("API_BASE_URL", "http://defect-analysis-api:8000")

def main():
    """Запуск Gradio интерфейса"""
    try:
        api_url = get_api_url()
        interface = ModelComparisonInterface(api_url)
        gradio_interface = interface.create_interface()
        
        print("🚀 Запуск Gradio интерфейса...")
        print("📱 Доступные модели:")
        for provider, models in interface.available_models.items():
            print(f"  {provider}: {', '.join(models)}")
        
        gradio_interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            root_path="/gradio"
        )
        
    except Exception as e:
        print(f"❌ Ошибка запуска интерфейса: {e}")
        print("Убедитесь, что все зависимости установлены и API ключи настроены")

if __name__ == "__main__":
    main()
