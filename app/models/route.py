from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True)
    city_from = Column(String, nullable=False)
    city_to = Column(String, nullable=False)
    is_active = Column(Integer, default=1)

class RoutePrice(Base):
    __tablename__ = "route_prices"

    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())