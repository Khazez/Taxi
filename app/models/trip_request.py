from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, Text, String, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class TripRequestStatus(enum.Enum):
    open = "open"          # ждёт откликов
    accepted = "accepted"  # пассажир выбрал водителя
    cancelled = "cancelled" # пассажир отменил


class PaymentType(enum.Enum):
    cash = "cash"
    card = "card"
    kaspi = "kaspi"


class TripRequest(Base):
    __tablename__ = "trip_requests"

    id = Column(Integer, primary_key=True)
    passenger_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    departure_date = Column(DateTime, nullable=False)
    seats_needed = Column(Integer, nullable=False, default=1)
    comment = Column(Text, nullable=True)
    status = Column(Enum(TripRequestStatus), default=TripRequestStatus.open)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Контактное лицо (если заказ для другого человека)
    contact_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)

    # Адреса подачи и назначения
    pickup_address       = Column(String, nullable=True)
    entrance             = Column(String, nullable=True)
    extra_pickups        = Column(Text, nullable=True)   # JSON: [{address,entrance?}]
    destination_address  = Column(String, nullable=True)
    destination_entrance = Column(String, nullable=True)
    extra_destinations   = Column(Text, nullable=True)   # JSON: [{address,entrance?}]

    # Оплата — хранится как строка ('cash', 'card', 'kaspi'), без PostgreSQL enum
    payment_type = Column(String, nullable=True, default='cash')

    passenger = relationship("User", foreign_keys=[passenger_id])
    route = relationship("Route")
    offers = relationship("TripOffer", back_populates="request")


class TripOffer(Base):
    __tablename__ = "trip_offers"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("trip_requests.id", ondelete="CASCADE"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)
    driver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    price_per_seat = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    request = relationship("TripRequest", back_populates="offers")
    trip = relationship("Trip")
    driver = relationship("User", foreign_keys=[driver_id])