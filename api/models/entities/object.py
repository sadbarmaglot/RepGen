from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base

class Object(Base):
    """Модель объекта"""
    __tablename__ = "objects"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    address = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь с проектом
    project = relationship("Project", back_populates="objects", lazy="select")
    
    # Связь с планами
    plans = relationship("Plan", back_populates="object", lazy="select", cascade="all, delete-orphan")
    
    # Связь с участниками объекта
    members = relationship("ObjectMember", back_populates="object", lazy="select", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Object(id={self.id}, name='{self.name}', project_id={self.project_id})>"
