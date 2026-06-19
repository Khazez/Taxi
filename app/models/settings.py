from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)   # название настройки
    value = Column(String, nullable=False)               # значение (всегда строка)
    description = Column(String, nullable=True)          # описание для админа
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())