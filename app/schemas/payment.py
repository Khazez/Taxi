from pydantic import BaseModel
from datetime import datetime
from app.models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: int
    method: PaymentMethod  # kaspi / card / cash


class PaymentOut(BaseModel):
    id: int
    booking_id: int
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}