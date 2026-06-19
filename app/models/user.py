from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class UserRole(enum.Enum):
    passenger = "passenger"
    driver = "driver"
    fleet = "fleet"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.passenger)
    created_at = Column(DateTime, server_default=func.now())

    agreements = relationship("Agreement", back_populates="user")
    fleet_profile = relationship("FleetProfile", back_populates="user", uselist=False)