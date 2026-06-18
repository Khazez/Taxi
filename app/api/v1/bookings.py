from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.booking import Booking, BookingStatus
from app.models.trip import Trip

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/")
async def create_booking(
    trip_id: int,
    passenger_id: int,
    seats_count: int,
    comment: str = None,
    db: AsyncSession = Depends(get_db)
):
    # Находим поездку
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    
    if trip.seats_available < seats_count:
        raise HTTPException(status_code=400, detail="Недостаточно мест")
    
    # Создаём бронь
    booking = Booking(
        trip_id=trip_id,
        passenger_id=passenger_id,
        seats_count=seats_count,
        comment=comment,
        total_price=trip.price_per_seat * seats_count
    )
    db.add(booking)
    
    # Уменьшаем количество мест
    trip.seats_available -= seats_count
    
    await db.commit()
    return {"message": "Бронь создана", "id": booking.id, "total": float(booking.total_price)}