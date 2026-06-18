from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, String, Enum
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class TripStatus(enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    seats_total = Column(Integer, nullable=False)
    seats_available = Column(Integer, nullable=False)
    price_per_seat = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(TripStatus), default=TripStatus.active)
    created_at = Column(DateTime, server_default=func.now())