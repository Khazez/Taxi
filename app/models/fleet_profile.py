from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class FleetProfile(Base):
    __tablename__ = "fleet_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    company_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="fleet_profile")
    drivers = relationship("FleetDriver", back_populates="fleet")


class FleetDriver(Base):
    __tablename__ = "fleet_drivers"

    id = Column(Integer, primary_key=True)
    fleet_id = Column(Integer, ForeignKey("fleet_profiles.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    fleet = relationship("FleetProfile", back_populates="drivers")
    driver = relationship("User", foreign_keys=[driver_id])