from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database.base import Base
from ..database.enums import DefectCategory


class PhotoDefectAnalysis(Base):
    """Модель анализа дефектов по фотографии"""
    __tablename__ = "photo_defect_analysis"

    id = Column(Integer, primary_key=True)
    photo_id = Column(
        Integer,
        ForeignKey("photos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    defect_description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    category = Column(
        Enum(DefectCategory, name="defect_category"),
        nullable=False
    )
    confidence = Column(
        Numeric(3, 2),
        nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь с фотографией
    photo = relationship("Photo", back_populates="defect_analysis")

    def __repr__(self):
        return f"<PhotoDefectAnalysis(id={self.id}, photo_id={self.photo_id}, category='{self.category}')>"
