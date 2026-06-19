from pydantic import BaseModel
from datetime import datetime


class AgreementCreate(BaseModel):
    version: str  # версия оферты, например "1.0"


class AgreementOut(BaseModel):
    id: int
    user_id: int
    version: str
    accepted_at: datetime
    ip_address: str | None

    model_config = {"from_attributes": True}