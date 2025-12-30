from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base

class Photo(Base):
    """Модель фотографии"""
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    mark_id = Column(Integer, ForeignKey("marks.id", ondelete="CASCADE"), nullable=False, index=True)
    image_name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=True)
    type_confidence = Column(Numeric(3, 2), nullable=True, comment="Уверенность модели в определении типа конструкции (0.0-1.0)")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с отметкой
    mark = relationship("Mark", back_populates="photos", lazy="select")
    
    def __repr__(self):
        return f"<Photo(id={self.id}, mark_id={self.mark_id}, image_name='{self.image_name}', type='{self.type}', order={self.order})>"
