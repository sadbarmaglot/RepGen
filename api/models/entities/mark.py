from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base
from ..database.enums import MarkType

class Mark(Base):
    """Модель отметки"""
    __tablename__ = "marks"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    type = Column(Enum(MarkType, name="mark_type"), nullable=False, default=MarkType.other)
    x = Column(Numeric(5, 4), nullable=True, comment="Координата X (не зависит от размеров изображения)")
    y = Column(Numeric(5, 4), nullable=True, comment="Координата Y (не зависит от размеров изображения)")
    is_horizontal = Column(Boolean, nullable=False, default=True, comment="Горизонтальная линия измерения")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с планом
    plan = relationship("Plan", back_populates="marks", lazy="select")
    
    # Связь с фотографиями
    photos = relationship("Photo", back_populates="mark", lazy="select", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Mark(id={self.id}, name='{self.name}', plan_id={self.plan_id}, type='{self.type}')>"
