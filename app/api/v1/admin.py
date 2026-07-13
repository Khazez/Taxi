from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.booking import Booking
from app.models.driver_profile import DriverProfile
from app.models.route import Route
from app.models.trip_request import TripRequest, TripOffer

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
    result = await db.execute(
        select(Trip, Route)
        .join(Route, Trip.route_id == Route.id)
        .order_by(Trip.id.desc())
    )
    rows = result.all()
    return {
        "data": [
            {
                "id": trip.id,
                "route_name": f"{route.city_from} → {route.city_to}",
                "driver_id": trip.driver_id,
                "departure_time": trip.departure_time.isoformat() if trip.departure_time else None,
                "seats_total": trip.seats_total,
                "seats_available": trip.seats_available,
                "price_per_seat": trip.price_per_seat,
                "status": trip.status.value if hasattr(trip.status, 'value') else trip.status,
            }
            for trip, route in rows
        ]
    }


@router.get("/trip-requests")
async def get_all_trip_requests(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(TripRequest, Route, User)
        .join(Route, TripRequest.route_id == Route.id)
        .join(User, TripRequest.passenger_id == User.id)
        .order_by(TripRequest.id.desc())
    )
    rows = result.all()

    offers_count_result = await db.execute(
        select(TripOffer.request_id, func.count(TripOffer.id)).group_by(TripOffer.request_id)
    )
    offers_count = dict(offers_count_result.all())

    return {
        "data": [
            {
                "id": req.id,
                "passenger_name": passenger.name,
                "passenger_phone": passenger.phone,
                "route_name": f"{route.city_from} → {route.city_to}",
                "departure_date": req.departure_date.isoformat() if req.departure_date else None,
                "seats_needed": req.seats_needed,
                "comment": req.comment,
                "status": req.status.value if hasattr(req.status, "value") else req.status,
                "payment_type": req.payment_type,
                "pickup_address": req.pickup_address,
                "destination_address": req.destination_address,
                "offers_count": offers_count.get(req.id, 0),
                "created_at": req.created_at.isoformat() if req.created_at else None,
            }
            for req, route, passenger in rows
        ]
    }