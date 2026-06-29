from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.rating import Rating
from app.models.trip import Trip, TripStatus
from app.models.booking import Booking, BookingStatus
from app.models.route import Route
from app.models.driver_profile import DriverProfile
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingOut

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("/", response_model=RatingOut)
async def create_rating(
    data: RatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from_id = current_user.get("user_id")

    trip = await db.get(Trip, data.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    if trip.status != TripStatus.completed:
        raise HTTPException(status_code=400, detail="Можно оценивать только завершённые поездки")

    if data.to_user_id == from_id:
        raise HTTPException(status_code=400, detail="Нельзя оценить самого себя")

    existing = await db.execute(
        select(Rating).where(
            Rating.trip_id == data.trip_id,
            Rating.from_user_id == from_id,
            Rating.to_user_id == data.to_user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже оценили этого пользователя")

    rating = Rating(
        trip_id=data.trip_id,
        from_user_id=from_id,
        to_user_id=data.to_user_id,
        score=data.score,
        comment=data.comment,
    )
    db.add(rating)
    await db.commit()
    await db.refresh(rating)

    # Пересчитать средний рейтинг водителя
    avg_result = await db.execute(
        select(func.avg(Rating.score)).where(Rating.to_user_id == data.to_user_id)
    )
    new_avg = avg_result.scalar()
    if new_avg is not None:
        profile = await db.execute(
            select(DriverProfile).where(DriverProfile.user_id == data.to_user_id)
        )
        profile_obj = profile.scalar_one_or_none()
        if profile_obj:
            profile_obj.rating = round(float(new_avg), 2)
            await db.commit()

    return rating


@router.get("/pending")
async def get_pending_ratings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Завершённые поездки пассажира, которые ещё не оценены."""
    passenger_id = current_user.get("user_id")

    result = await db.execute(
        select(Booking, Trip, Route)
        .join(Trip, Booking.trip_id == Trip.id)
        .join(Route, Trip.route_id == Route.id)
        .where(Booking.passenger_id == passenger_id)
        .where(Booking.status == BookingStatus.confirmed)
        .where(Trip.status == TripStatus.completed)
    )
    rows = result.all()

    pending = []
    for booking, trip, route in rows:
        existing = await db.execute(
            select(Rating).where(
                Rating.trip_id == trip.id,
                Rating.from_user_id == passenger_id,
                Rating.to_user_id == trip.driver_id,
            )
        )
        if existing.scalar_one_or_none():
            continue
        driver = await db.get(User, trip.driver_id)
        pending.append({
            "trip_id": trip.id,
            "driver_user_id": trip.driver_id,
            "driver_name": driver.name if driver else "Водитель",
            "route_name": f"{route.city_from} → {route.city_to}",
            "departure_time": trip.departure_time.isoformat() if trip.departure_time else None,
        })

    return pending


@router.get("/received")
async def get_received_ratings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Оценки, полученные текущим пользователем (от пассажиров или водителей)."""
    user_id = current_user.get("user_id")
    result = await db.execute(
        select(Rating, User)
        .join(User, Rating.from_user_id == User.id)
        .where(Rating.to_user_id == user_id)
        .order_by(Rating.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id": r.id,
            "score": r.score,
            "comment": r.comment,
            "from_name": u.name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r, u in rows
    ]


@router.get("/pending-driver")
async def get_pending_ratings_driver(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Завершённые поездки водителя, где он ещё не оценил пассажира."""
    driver_id = current_user.get("user_id")

    result = await db.execute(
        select(Booking, Trip, Route, User)
        .join(Trip, Booking.trip_id == Trip.id)
        .join(Route, Trip.route_id == Route.id)
        .join(User, Booking.passenger_id == User.id)
        .where(Trip.driver_id == driver_id)
        .where(Trip.status == TripStatus.completed)
        .where(Booking.status == BookingStatus.confirmed)
    )
    rows = result.all()

    pending = []
    for booking, trip, route, passenger in rows:
        existing = await db.execute(
            select(Rating).where(
                Rating.trip_id == trip.id,
                Rating.from_user_id == driver_id,
                Rating.to_user_id == passenger.id,
            )
        )
        if existing.scalar_one_or_none():
            continue
        pending.append({
            "trip_id": trip.id,
            "passenger_user_id": passenger.id,
            "passenger_name": passenger.name,
            "route_name": f"{route.city_from} → {route.city_to}",
        })

    return pending


@router.get("/user/{user_id}")
async def get_user_rating(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Средний рейтинг и список отзывов пользователя."""
    avg_result = await db.execute(
        select(func.avg(Rating.score), func.count(Rating.id))
        .where(Rating.to_user_id == user_id)
    )
    avg_score, total = avg_result.one()

    reviews_result = await db.execute(
        select(Rating, User)
        .join(User, Rating.from_user_id == User.id)
        .where(Rating.to_user_id == user_id)
        .order_by(Rating.created_at.desc())
    )
    reviews = [
        {
            "score": r.score,
            "comment": r.comment,
            "from_name": u.name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r, u in reviews_result.all()
    ]

    return {
        "user_id": user_id,
        "average_score": round(float(avg_score), 2) if avg_score else None,
        "total_ratings": total,
        "reviews": reviews,
    }