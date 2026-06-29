import json as _json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.trip import Trip
from app.models.route import Route
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])


class _ExtraAddr(BaseModel):
    address: str
    entrance: str | None = None

class BookingCreate(BaseModel):
    trip_id: int
    seats_count: int = 1
    pickup_address: str | None = None
    entrance: str | None = None
    extra_pickups: list[_ExtraAddr] = []
    destination_address: str | None = None
    destination_entrance: str | None = None
    extra_destinations: list[_ExtraAddr] = []
    contact_name: str | None = None
    contact_phone: str | None = None
    comment: str | None = None


@router.post("/")
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Trip).where(Trip.id == data.trip_id))
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    if trip.seats_available < data.seats_count:
        raise HTTPException(status_code=400, detail="Недостаточно мест")

    booking = Booking(
        trip_id=data.trip_id,
        passenger_id=current_user.get("user_id"),
        seats_count=data.seats_count,
        total_price=trip.price_per_seat * data.seats_count,
        pickup_address=data.pickup_address,
        entrance=data.entrance,
        extra_pickups=_json.dumps([ep.model_dump(exclude_none=True) for ep in data.extra_pickups]) if data.extra_pickups else None,
        destination_address=data.destination_address,
        destination_entrance=data.destination_entrance,
        extra_destinations=_json.dumps([ed.model_dump(exclude_none=True) for ed in data.extra_destinations]) if data.extra_destinations else None,
        contact_name=data.contact_name,
        contact_phone=data.contact_phone,
        comment=data.comment,
        status=BookingStatus.confirmed,
    )
    db.add(booking)
    trip.seats_available -= data.seats_count
    await db.commit()

    return {"message": "Бронь создана", "id": booking.id, "total": float(booking.total_price)}


@router.get("/my")
async def get_my_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Booking, Trip, Route, User)
        .join(Trip, Booking.trip_id == Trip.id)
        .join(Route, Trip.route_id == Route.id)
        .join(User, Trip.driver_id == User.id)
        .where(Booking.passenger_id == current_user.get("user_id"))
        .order_by(Booking.id.desc())
    )
    rows = result.all()
    return [
        {
            "id": b.id,
            "trip_id": b.trip_id,
            "driver_id": t.driver_id,
            "driver_name": u.name,
            "driver_phone": u.phone,
            "seats_count": b.seats_count,
            "total_price": float(b.total_price),
            "status": b.status.value,
            "trip_status": t.status.value,
            "route_name": f"{r.city_from} → {r.city_to}",
            "departure_time": t.departure_time.isoformat() if t.departure_time else None,
            "pickup_address": b.pickup_address,
            "entrance": b.entrance,
            "extra_pickups": _json.loads(b.extra_pickups) if b.extra_pickups else [],
            "destination_address": b.destination_address,
            "destination_entrance": b.destination_entrance,
            "extra_destinations": _json.loads(b.extra_destinations) if b.extra_destinations else [],
            "contact_name": b.contact_name,
            "contact_phone": b.contact_phone,
            "comment": b.comment,
        }
        for b, t, r, u in rows
    ]


@router.get("/for-driver")
async def get_driver_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Водитель видит всех пассажиров по своим поездкам."""
    driver_id = current_user.get("user_id")
    result = await db.execute(
        select(Booking, Trip, Route, User)
        .join(Trip, Booking.trip_id == Trip.id)
        .join(Route, Trip.route_id == Route.id)
        .join(User, Booking.passenger_id == User.id)
        .where(Trip.driver_id == driver_id, Booking.status != BookingStatus.cancelled)
        .order_by(Trip.departure_time.asc(), Booking.id.asc())
    )
    rows = result.all()
    return [
        {
            "booking_id": b.id,
            "trip_id": t.id,
            "route_name": f"{r.city_from} → {r.city_to}",
            "departure_time": t.departure_time.isoformat() if t.departure_time else None,
            "trip_status": t.status.value,
            "passenger_id": u.id,
            "passenger_name": u.name,
            "passenger_phone": u.phone,
            "seats_count": b.seats_count,
            "total_price": float(b.total_price),
            "pickup_address": b.pickup_address,
            "entrance": b.entrance,
            "extra_pickups": _json.loads(b.extra_pickups) if b.extra_pickups else [],
            "destination_address": b.destination_address,
            "destination_entrance": b.destination_entrance,
            "extra_destinations": _json.loads(b.extra_destinations) if b.extra_destinations else [],
            "contact_name": b.contact_name,
            "contact_phone": b.contact_phone,
            "comment": b.comment,
            "booking_status": b.status.value,
        }
        for b, t, r, u in rows
    ]


@router.delete("/{booking_id}")
async def cancel_booking_endpoint(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    if booking.passenger_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Нет доступа")

    booking.status = BookingStatus.cancelled
    await db.commit()
    return {"message": "Бронь отменена", "id": booking.id}
