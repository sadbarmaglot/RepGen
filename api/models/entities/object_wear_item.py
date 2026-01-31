from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base


class ObjectWearItem(Base):
    """Данные износа по элементу для конкретного объекта"""
    __tablename__ = "object_wear_items"

    id = Column(Integer, primary_key=True)
    object_id = Column(
        Integer,
        ForeignKey("objects.id", ondelete="CASCADE"),
        nullable=False
    )
    element_id = Column(
        Integer,
        ForeignKey("wear_elements.id", ondelete="CASCADE"),
        nullable=False
    )
    assessment_percent = Column(Numeric(5, 2), nullable=True)  # ввод пользователя (0-100)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Уникальность: один элемент - один объект
    __table_args__ = (
        UniqueConstraint('object_id', 'element_id', name='uq_object_wear_item'),
    )

    # Связи
    object = relationship("Object", back_populates="wear_items")
    element = relationship("WearElement", back_populates="object_wear_items")

    def __repr__(self):
        return f"<ObjectWearItem(id={self.id}, object_id={self.object_id}, element_id={self.element_id})>"
