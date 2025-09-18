from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from ..database.base import Base

class ObjectMember(Base):
    """Модель участника объекта"""
    __tablename__ = "object_members"
    
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Уникальная связь объект-пользователь
    __table_args__ = (UniqueConstraint('object_id', 'user_id'),)
    
    # Связи
    object = relationship("Object", lazy="select")
    user = relationship("User", lazy="select")
    
    def __repr__(self):
        return f"<ObjectMember(id={self.id}, object_id={self.object_id}, user_id={self.user_id})>"
