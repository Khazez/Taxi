from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.db.database import Base
import enum

class UserRole(enum.Enum):
    passenger = "passenger"
    driver = "driver"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.passenger)
    created_at = Column(DateTime, server_default=func.now())