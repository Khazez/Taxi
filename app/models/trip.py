from sqlalchemy import Boolean, Column, Integer, Numeric, ForeignKey, DateTime, String, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    is_departed = Column(Boolean, default=False, server_default="false")
    is_arrived  = Column(Boolean, default=False, server_default="false")
    created_at = Column(DateTime, server_default=func.now())

    ratings = relationship("Rating", back_populates="trip")