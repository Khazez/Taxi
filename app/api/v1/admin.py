from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.booking import Booking
from app.models.driver_profile import DriverProfile

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_trips = await db.scalar(select(func.count()).select_from(Trip))
    total_bookings = await db.scalar(select(func.count()).select_from(Booking))
    pending_drivers = await db.scalar(
        select(func.count())
        .select_from(DriverProfile)
        .where(DriverProfile.is_verified == False)
    )

    return {
        "data": {
            "total_users": total_users or 0,
            "total_trips": total_trips or 0,
            "total_bookings": total_bookings or 0,
            "pending_drivers": pending_drivers or 0,
        }
    }

@router.get("/trips")
async def get_all_trips(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Trip).order_by(Trip.id.desc()))
    trips = result.scalars().all()
    return {"data": trips}