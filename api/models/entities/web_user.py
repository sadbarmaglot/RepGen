from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base


class WebUser(Base):
    __tablename__ = "web_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default="client")
    is_active = Column(Boolean, nullable=False, default=True)
    refresh_token = Column(Text, nullable=True)
    refresh_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    project_access = relationship("WebUserProjectAccess", back_populates="web_user", lazy="select", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WebUser(id={self.id}, email='{self.email}', role='{self.role}')>"
