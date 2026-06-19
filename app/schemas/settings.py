from pydantic import BaseModel
from datetime import datetime


class SettingOut(BaseModel):
    id: int
    key: str
    value: str
    description: str | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: str