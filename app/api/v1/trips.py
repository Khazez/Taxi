from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.trip import Trip, TripStatus
from datetime import datetime
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/trips", tags=["trips"])

@router.get("/")
async def get_trips(
    route_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = select(Trip).where(
        Trip.status == TripStatus.active,
        Trip.seats_available > 0,
    )
    if route_id is not None:
        query = query.where(Trip.route_id == route_id)
    result = await db.execute(query)
    trips = result.scalars().all()
    return {"data": trips}

@router.post("/")
async def create_trip(
    route_id: int,
    departure_time: datetime,
    seats_total: int,
    price_per_seat: float,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "driver":
        raise HTTPException(status_code=403, detail="Только водитель может создать поездку")

    trip = Trip(
        route_id=route_id,
        driver_id=current_user.get("user_id"),
        departure_time=departure_time,
        seats_total=seats_total,
        seats_available=seats_total,
        price_per_seat=price_per_seat,
    )
    db.add(trip)
    await db.commit()
    return {"message": "Поездка создана", "id": trip.id}
