from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..database.base import Base


class WearElement(Base):
    """Справочник элементов для расчёта износа"""
    __tablename__ = "wear_elements"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True)  # "1", "2.1", "4.2"
    name = Column(String(255), nullable=False)  # "Фундамент", "Стены"
    parent_id = Column(
        Integer,
        ForeignKey("wear_elements.id", ondelete="SET NULL"),
        nullable=True
    )
    default_weight = Column(Numeric(5, 2), nullable=True)  # 9.8, 32.8 (NULL для групп)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    # Связь с родительским элементом
    parent = relationship("WearElement", remote_side=[id], backref="children")

    # Связь с данными износа объектов
    object_wear_items = relationship("ObjectWearItem", back_populates="element")

    def __repr__(self):
        return f"<WearElement(id={self.id}, code='{self.code}', name='{self.name}')>"
