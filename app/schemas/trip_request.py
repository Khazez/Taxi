import json as _json
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.models.trip_request import TripRequestStatus


class ExtraAddress(BaseModel):
    address: str
    entrance: str | None = None


def _parse_addr_list(v) -> list:
    if v is None:
        return []
    if isinstance(v, str):
        try:
            result = _json.loads(v)
            return result if isinstance(result, list) else []
        except Exception:
            return []
    return v if isinstance(v, list) else []


class TripRequestCreate(BaseModel):
    route_id: int
    departure_date: datetime
    seats_needed: int = 1
    comment: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    pickup_address: str | None = None
    entrance: str | None = None
    extra_pickups: list[ExtraAddress] = []
    destination_address: str | None = None
    destination_entrance: str | None = None
    extra_destinations: list[ExtraAddress] = []
    payment_type: str | None = "cash"


class TripRequestOut(BaseModel):
    id: int
    passenger_id: int
    route_id: int
    departure_date: datetime
    seats_needed: int
    comment: str | None = None
    status: TripRequestStatus
    created_at: datetime

    pickup_address: str | None = None
    entrance: str | None = None
    extra_pickups: list[ExtraAddress] = []
    destination_address: str | None = None
    destination_entrance: str | None = None
    extra_destinations: list[ExtraAddress] = []
    contact_name: str | None = None
    contact_phone: str | None = None
    payment_type: str | None = None

    @field_validator('extra_pickups', 'extra_destinations', mode='before')
    @classmethod
    def parse_addr_list(cls, v):
        raw = _parse_addr_list(v)
        result = []
        for item in raw:
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                result.append({'address': item})
        return result

    model_config = {"from_attributes": True}


class TripOfferCreate(BaseModel):
    request_id: int
    trip_id: int


class TripOfferOut(BaseModel):
    id: int
    request_id: int
    trip_id: int
    driver_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
