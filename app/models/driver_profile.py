from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime, Numeric
from sqlalchemy.sql import func
from app.db.database import Base


OFFER_PRICE = 50  # ₸ списывается при каждом отклике


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    car_brand = Column(String, nullable=False)
    car_model = Column(String, nullable=False)
    car_year = Column(Integer, nullable=False)
    car_color = Column(String, nullable=False)
    car_number = Column(String, nullable=False)
    license_doc_url = Column(String)
    car_doc_url = Column(String)
    is_verified = Column(Boolean, default=False)
    rejection_reason = Column(String, nullable=True)
    rating = Column(Float, default=5.0)
    balance = Column(Numeric(10, 2), default=0, server_default='0')
    created_at = Column(DateTime, server_default=func.now())