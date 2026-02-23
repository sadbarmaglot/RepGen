from sqlalchemy import Column, Integer, String, Text, Date, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base


class ObjectGeneralInfo(Base):
    """Общая информация об объекте для заключения"""
    __tablename__ = "object_general_info"

    id = Column(Integer, primary_key=True)
    object_id = Column(
        Integer,
        ForeignKey("objects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # Даты
    inspection_date = Column(Date, nullable=True)  # Дата обследования
    inspection_duration = Column(Integer, nullable=True)  # Время обследования (дней)

    # Адресация
    fias_code = Column(String(100), nullable=True)  # Код ФИАС
    latitude = Column(Numeric(10, 8), nullable=True)  # Широта
    longitude = Column(Numeric(11, 8), nullable=True)  # Долгота

    # Характеристики дома
    apartments_count = Column(Integer, nullable=True)  # Количество квартир
    non_residential_count = Column(Integer, nullable=True)  # Количество нежилых помещений
    total_area = Column(Numeric(12, 2), nullable=True)  # Общая площадь м²
    living_area = Column(Numeric(12, 2), nullable=True)  # Жилая площадь м²
    floors_count = Column(Integer, nullable=True)  # Число этажей
    entrances_count = Column(Integer, nullable=True)  # Число подъездов
    construction_year = Column(Integer, nullable=True)  # Год возведения
    project_type = Column(String(255), nullable=True)  # Тип проекта

    # Статус и история
    object_status = Column(Text, nullable=True)  # Статус (памятник и т.д.)
    last_repair = Column(Text, nullable=True)  # Последний капремонт
    replanning = Column(Text, nullable=True)  # Перепланировки

    # Организация
    organization = Column(String(255), nullable=True)  # Организация

    # Конструктивные решения (JSON-массив)
    construction_solutions = Column(JSONB, nullable=True, default=[])

    # Упрощенное заключение (для нежилых зданий)
    simplified_conclusion = Column(JSONB, nullable=True, default={})

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связь с объектом
    object = relationship("Object", back_populates="general_info")

    def __repr__(self):
        return f"<ObjectGeneralInfo(id={self.id}, object_id={self.object_id})>"
