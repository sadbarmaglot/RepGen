from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base

class Plan(Base):
    """Модель плана"""
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    image_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с объектом
    object = relationship("Object", back_populates="plans", lazy="select")
    
    # Связь с отметками
    marks = relationship("Mark", back_populates="plan", lazy="select", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Plan(id={self.id}, name='{self.name}', object_id={self.object_id})>"
