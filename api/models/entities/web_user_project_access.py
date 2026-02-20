from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base


class WebUserProjectAccess(Base):
    __tablename__ = "web_user_project_access"

    id = Column(Integer, primary_key=True, index=True)
    web_user_id = Column(Integer, ForeignKey("web_users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("web_user_id", "project_id", name="uq_web_user_project"),
    )

    web_user = relationship("WebUser", back_populates="project_access", lazy="select")
    project = relationship("Project", lazy="select")

    def __repr__(self):
        return f"<WebUserProjectAccess(web_user_id={self.web_user_id}, project_id={self.project_id})>"
