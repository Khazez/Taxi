from pydantic import BaseModel
from datetime import datetime


class FleetProfileCreate(BaseModel):
    company_name: str
    phone: str | None = None


class FleetProfileOut(BaseModel):
    id: int
    user_id: int
    company_name: str
    phone: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FleetDriverAdd(BaseModel):
    driver_id: int  # id водителя которого добавляем в таксопарк


class FleetDriverOut(BaseModel):
    id: int
    fleet_id: int
    driver_id: int
    created_at: datetime

    model_config = {"from_attributes": True}