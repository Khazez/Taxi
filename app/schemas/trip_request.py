from pydantic import BaseModel
from datetime import datetime
from app.models.trip_request import TripRequestStatus


class TripRequestCreate(BaseModel):
    route_id: int
    departure_date: datetime
    seats_needed: int = 1
    comment: str | None = None


class TripRequestOut(BaseModel):
    id: int
    passenger_id: int
    route_id: int
    departure_date: datetime
    seats_needed: int
    comment: str | None
    status: TripRequestStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TripOfferCreate(BaseModel):
    request_id: int
    trip_id: int  # водитель указывает какую поездку предлагает


class TripOfferOut(BaseModel):
    id: int
    request_id: int
    trip_id: int
    driver_id: int
    created_at: datetime

    model_config = {"from_attributes": True}