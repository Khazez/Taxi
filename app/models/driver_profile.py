from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    car_brand = Column(String, nullable=False)       # Марка: Toyota
    car_model = Column(String, nullable=False)       # Модель: Camry
    car_year = Column(Integer, nullable=False)       # Год: 2020
    car_color = Column(String, nullable=False)       # Цвет: Белый
    car_number = Column(String, nullable=False)      # Номер: 123 ABC 02
    license_doc_url = Column(String)                 # Ссылка на права в MinIO
    car_doc_url = Column(String)                     # Ссылка на тех.паспорт в MinIO
    is_verified = Column(Boolean, default=False)     # Верифицирован ли админом
    rejection_reason = Column(String, nullable=True) # Причина отказа
    rating = Column(Float, default=5.0)              # Рейтинг водителя
    created_at = Column(DateTime, server_default=func.now())