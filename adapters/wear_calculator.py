"""
Модуль расчета физического износа здания по ВСН 53-86(р)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from pathlib import Path

@dataclass
class ConstructionElement:
    """Конструктивный элемент здания"""
    name: str
    weight_percent: float  # Удельный вес в общей стоимости здания (%)
    wear_percent: float = 0.0  # Физический износ элемента (%)
    
    @property
    def weighted_wear(self) -> float:
        """Средневзвешенная степень физического износа"""
        return (self.weight_percent * self.wear_percent) / 100

class WearCalculator:
    """Калькулятор физического износа здания"""
    
    # Стандартные элементы здания по ВСН 53-86(р)
    DEFAULT_ELEMENTS = [
        ConstructionElement("Фундаменты", 2.0),
        ConstructionElement("Стены и перегородки", 29.0),
        ConstructionElement("Перекрытия", 16.0),
        ConstructionElement("Кровля", 3.0),
        ConstructionElement("Полы", 10.0),
        ConstructionElement("Проёмы", 9.0),
        ConstructionElement("Отделочные работы", 6.0),
        ConstructionElement("Внутренние санитарно-технические устройства", 12.0),
        ConstructionElement("Внутренние электротехнические устройства", 9.0),
        ConstructionElement("Прочие работы", 4.0),
    ]
    
    def __init__(self, elements: Optional[List[ConstructionElement]] = None):
        self.elements = elements or self.DEFAULT_ELEMENTS.copy()
        
    def calculate_total_wear(self) -> float:
        """Расчет общего физического износа здания"""
        total_weighted_wear = sum(element.weighted_wear for element in self.elements)
        return round(total_weighted_wear, 1)
    
    def get_technical_condition(self, total_wear: float) -> Dict[str, str]:
        """Определение технического состояния здания по износу"""
        if total_wear <= 20:
            return {
                "category": "Исправное",
                "description": "Здание находится в исправном состоянии",
                "recommendation": "Проведение текущего ремонта"
            }
        elif total_wear <= 40:
            return {
                "category": "Работоспособное", 
                "description": "Здание находится в работоспособном состоянии",
                "recommendation": "Проведение среднего ремонта"
            }
        elif total_wear <= 60:
            return {
                "category": "Ограниченно работоспособное",
                "description": "Здание находится в ограниченно работоспособном состоянии", 
                "recommendation": "Проведение капитального ремонта"
            }
        else:
            return {
                "category": "Аварийное",
                "description": "Здание находится в аварийном состоянии",
                "recommendation": "Реконструкция или снос здания"
            }
    
    def get_element_by_name(self, name: str) -> Optional[ConstructionElement]:
        """Получение элемента по названию"""
        for element in self.elements:
            if element.name == name:
                return element
        return None
    
    def update_element_wear(self, element_name: str, wear_percent: float) -> bool:
        """Обновление износа элемента"""
        element = self.get_element_by_name(element_name)
        if element and 0 <= wear_percent <= 100:
            element.wear_percent = wear_percent
            return True
        return False
    
    def reset_all_wear(self):
        """Сброс всех значений износа"""
        for element in self.elements:
            element.wear_percent = 0.0
    
    def to_dict(self) -> Dict:
        """Экспорт в словарь"""
        return {
            "elements": [
                {
                    "name": elem.name,
                    "weight_percent": elem.weight_percent,
                    "wear_percent": elem.wear_percent,
                    "weighted_wear": elem.weighted_wear
                }
                for elem in self.elements
            ],
            "total_wear": self.calculate_total_wear(),
            "technical_condition": self.get_technical_condition(self.calculate_total_wear())
        }
    
    def from_dict(self, data: Dict):
        """Импорт из словаря"""
        self.elements = [
            ConstructionElement(
                elem["name"],
                elem["weight_percent"], 
                elem.get("wear_percent", 0.0)
            )
            for elem in data.get("elements", [])
        ]
    
    def save_to_file(self, filepath: str):
        """Сохранение в JSON файл"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str) -> bool:
        """Загрузка из JSON файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.from_dict(data)
                return True
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return False
    
    def generate_report_data(self) -> Dict:
        """Генерация данных для отчета"""
        total_wear = self.calculate_total_wear()
        condition = self.get_technical_condition(total_wear)
        
        return {
            "elements_table": [
                {
                    "name": elem.name,
                    "weight": elem.weight_percent,
                    "wear": elem.wear_percent,
                    "weighted_wear": elem.weighted_wear
                }
                for elem in self.elements
            ],
            "total_wear": total_wear,
            "total_weight": sum(elem.weight_percent for elem in self.elements),
            "condition": condition,
            "vsn_reference": "ВСН 53-86(р)"
        }

# Примеры использования для разных типов зданий
class BuildingTypeTemplates:
    """Шаблоны расчета для разных типов зданий"""
    
    @staticmethod
    def get_residential_building() -> List[ConstructionElement]:
        """Жилое здание (из примера)"""
        return [
            ConstructionElement("Фундаменты", 2.0),
            ConstructionElement("Стены и перегородки", 29.0),
            ConstructionElement("Перекрытия", 16.0),
            ConstructionElement("Кровля", 3.0),
            ConstructionElement("Полы", 10.0),
            ConstructionElement("Проёмы", 9.0),
            ConstructionElement("Отделочные работы", 6.0),
            ConstructionElement("Внутренние санитарно-технические устройства", 12.0),
            ConstructionElement("Внутренние электротехнические устройства", 9.0),
            ConstructionElement("Прочие работы", 4.0),
        ]
    
    @staticmethod 
    def get_office_building() -> List[ConstructionElement]:
        """Офисное здание"""
        return [
            ConstructionElement("Фундаменты", 3.0),
            ConstructionElement("Стены и перегородки", 25.0),
            ConstructionElement("Перекрытия", 18.0),
            ConstructionElement("Кровля", 4.0),
            ConstructionElement("Полы", 12.0),
            ConstructionElement("Проёмы", 8.0),
            ConstructionElement("Отделочные работы", 8.0),
            ConstructionElement("Внутренние санитарно-технические устройства", 10.0),
            ConstructionElement("Внутренние электротехнические устройства", 8.0),
            ConstructionElement("Системы кондиционирования", 4.0),
        ]
    
    @staticmethod
    def get_industrial_building() -> List[ConstructionElement]:
        """Промышленное здание"""
        return [
            ConstructionElement("Фундаменты", 4.0),
            ConstructionElement("Стены", 20.0),
            ConstructionElement("Каркас", 25.0),
            ConstructionElement("Покрытие", 15.0),
            ConstructionElement("Кровля", 5.0),
            ConstructionElement("Полы", 15.0),
            ConstructionElement("Проёмы", 6.0),
            ConstructionElement("Внутренние устройства", 8.0),
            ConstructionElement("Прочие работы", 2.0),
        ]