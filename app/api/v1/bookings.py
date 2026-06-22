from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.trip import Trip
from app.models.route import Route
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/")
async def create_booking(
    trip_id: int,
    seats_count: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()

    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    if trip.seats_available < seats_count:
        raise HTTPException(status_code=400, detail="Недостаточно мест")

    booking = Booking(
        trip_id=trip_id,
        passenger_id=current_user.get("user_id"),
        seats_count=seats_count,
        total_price=trip.price_per_seat * seats_count,
    )
    db.add(booking)

    trip.seats_available -= seats_count
    await db.commit()

    return {"message": "Бронь создана", "id": booking.id, "total": float(booking.total_price)}


@router.get("/my")
async def get_my_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Booking, Trip, Route)
        .join(Trip, Booking.trip_id == Trip.id)
        .join(Route, Trip.route_id == Route.id)
        .where(Booking.passenger_id == current_user.get("user_id"))
        .order_by(Booking.id.desc())
    )
    rows = result.all()
    return [
        {
            "id": b.id,
            "trip_id": b.trip_id,
            "seats_count": b.seats_count,
            "total_price": float(b.total_price),
            "status": b.status.value,
            "route_name": f"{r.city_from} → {r.city_to}",
            "departure_time": t.departure_time.isoformat() if t.departure_time else None,
        }
        for b, t, r in rows
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
