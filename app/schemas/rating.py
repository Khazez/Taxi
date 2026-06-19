from pydantic import BaseModel, Field
from datetime import datetime


class RatingCreate(BaseModel):
    trip_id: int
    to_user_id: int
    score: int = Field(..., ge=1, le=5)  # только от 1 до 5


class RatingOut(BaseModel):
    id: int
    trip_id: int
    from_user_id: int
    to_user_id: int
    score: int
    created_at: datetime

    model_config = {"from_attributes": True}