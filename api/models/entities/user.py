from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base
from ..database.enums import GlobalRoleType, RoleType

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    name = Column(String(255), nullable=True)
    global_role = Column(Enum(GlobalRoleType, name="global_role_type"), nullable=False, default=GlobalRoleType.user)
    role_type = Column(Enum(RoleType, name="role_type_enum"), nullable=False, default=RoleType.all)
    refresh_token = Column(Text, nullable=True)
    refresh_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Связь с проектами
    projects = relationship("Project", back_populates="owner", lazy="select")
    
    # Связь с участием в объектах
    object_memberships = relationship("ObjectMember", back_populates="user", lazy="select", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}', global_role='{self.global_role}')>"
