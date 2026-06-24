import json as _json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.trip import Trip, TripStatus
from app.models.trip_request import TripOffer, TripRequest, TripRequestStatus
from app.models.route import Route
from app.models.user import User
from datetime import datetime
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/trips", tags=["trips"])

@router.get("/my-offers")
async def get_my_offers(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Водитель видит все свои отклики и их статус."""
    driver_id = current_user.get("user_id")
    result = await db.execute(
        select(TripOffer, TripRequest, Route, User)
        .join(TripRequest, TripOffer.request_id == TripRequest.id)
        .join(Route, TripRequest.route_id == Route.id)
        .join(User, TripRequest.passenger_id == User.id)
        .where(TripOffer.driver_id == driver_id)
        .order_by(TripOffer.id.desc())
    )
    rows = result.all()
    return [
        {
            "offer_id": offer.id,
            "request_id": req.id,
            "request_status": req.status.value,
            "route_name": f"{route.city_from} → {route.city_to}",
            "departure_date": req.departure_date.isoformat() if req.departure_date else None,
            "seats_needed": req.seats_needed,
            "price_per_seat": float(offer.price_per_seat) if offer.price_per_seat else None,
            "pickup_address": req.pickup_address,
            "entrance": req.entrance,
            "extra_pickups": _json.loads(req.extra_pickups) if req.extra_pickups else [],
            "destination_address": req.destination_address,
            "destination_entrance": req.destination_entrance,
            "extra_destinations": _json.loads(req.extra_destinations) if req.extra_destinations else [],
            "contact_name": req.contact_name,
            "contact_phone": req.contact_phone,
            "payment_type": req.payment_type,
            "comment": req.comment,
            "passenger_phone": passenger.phone,
            "passenger_name": passenger.name,
        }
        for offer, req, route, passenger in rows
    ]


@router.get("/")
async def get_trips(
    route_id: int | None = None,
    my: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = select(Trip).where(Trip.status == TripStatus.active)
    if not my:
        query = query.where(Trip.seats_available > 0)
    if route_id is not None:
        query = query.where(Trip.route_id == route_id)
    if my:
        query = query.where(Trip.driver_id == current_user.get("user_id"))
    result = await db.execute(query.order_by(Trip.departure_time.asc()))
    trips = result.scalars().all()
    return {"data": [
        {
            "id": t.id,
            "route_id": t.route_id,
            "departure_time": t.departure_time.isoformat() if t.departure_time else None,
            "seats_total": t.seats_total,
            "seats_available": t.seats_available,
            "price_per_seat": float(t.price_per_seat),
            "status": t.status.value,
        }
        for t in trips
    ]}

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


@router.patch("/{trip_id}/complete")
async def complete_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Водитель отмечает поездку завершённой."""
    trip = await db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    if trip.driver_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if trip.status != TripStatus.active:
        raise HTTPException(status_code=400, detail="Поездка уже завершена или отменена")
    trip.status = TripStatus.completed
    await db.commit()
    return {"message": "Поездка завершена"}


@router.patch("/{trip_id}/cancel")
async def cancel_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Водитель отменяет поездку."""
    trip = await db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    if trip.driver_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if trip.status != TripStatus.active:
        raise HTTPException(status_code=400, detail="Поездка уже завершена или отменена")
    trip.status = TripStatus.cancelled
    await db.commit()
    return {"message": "Поездка отменена"}
