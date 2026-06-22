from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.trip_request import TripRequest, TripRequestStatus, TripOffer
from app.models.trip import Trip
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.models.route import Route
from app.schemas.trip_request import TripRequestCreate, TripRequestOut, TripOfferCreate, TripOfferOut

router = APIRouter(prefix="/trip-requests", tags=["trip-requests"])


@router.post("/", response_model=TripRequestOut)
async def create_request(
    data: TripRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Пассажир создаёт заявку на поездку."""
    if current_user.get("role") != "passenger":
        raise HTTPException(status_code=403, detail="Только пассажир может создать заявку")

    request = TripRequest(
        passenger_id=current_user.get("user_id"),
        route_id=data.route_id,
        departure_date=data.departure_date,
        seats_needed=data.seats_needed,
        comment=data.comment,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


@router.get("/", response_model=list[TripRequestOut])
async def get_open_requests(
    route_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Открытые заявки пассажиров. Если route_id передан — фильтруем по маршруту."""
    query = select(TripRequest).where(TripRequest.status == TripRequestStatus.open)
    if route_id is not None:
        query = query.where(TripRequest.route_id == route_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/my")
async def get_my_requests(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(TripRequest, Route)
        .join(Route, TripRequest.route_id == Route.id)
        .where(TripRequest.passenger_id == current_user.get("user_id"))
        .order_by(TripRequest.id.desc())
    )
    rows = result.all()
    return [
        {
            "id": req.id,
            "status": req.status.value,
            "seats_needed": req.seats_needed,
            "departure_date": req.departure_date.isoformat() if req.departure_date else None,
            "route_name": f"{r.city_from} → {r.city_to}",
            "comment": req.comment,
        }
        for req, r in rows
    ]


@router.post("/offers", response_model=TripOfferOut)
async def create_offer(
    data: TripOfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Водитель откликается на заявку пассажира."""
    if current_user.get("role") != "driver":
        raise HTTPException(status_code=403, detail="Только водитель может откликнуться")

    request = await db.get(TripRequest, data.request_id)
    if not request or request.status != TripRequestStatus.open:
        raise HTTPException(status_code=404, detail="Заявка не найдена или уже закрыта")

    existing = await db.execute(
        select(TripOffer).where(
            TripOffer.request_id == data.request_id,
            TripOffer.driver_id == current_user.get("user_id"),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже откликнулись на эту заявку")

    offer = TripOffer(
        request_id=data.request_id,
        trip_id=data.trip_id,
        driver_id=current_user.get("user_id"),
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


@router.get("/{request_id}/offers", response_model=list[TripOfferOut])
async def get_offers(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Пассажир видит отклики на свою заявку."""
    request = await db.get(TripRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if request.passenger_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Это не ваша заявка")

    result = await db.execute(
        select(TripOffer).where(TripOffer.request_id == request_id)
    )
    return result.scalars().all()


@router.post("/{request_id}/accept/{offer_id}", response_model=TripRequestOut)
async def accept_offer(
    request_id: int,
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Пассажир выбирает водителя — заявка закрывается, бронь создаётся."""
    request = await db.get(TripRequest, request_id)
    if not request or request.passenger_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if request.status != TripRequestStatus.open:
        raise HTTPException(status_code=400, detail="Заявка уже закрыта")

    offer = await db.get(TripOffer, offer_id)
    if not offer or offer.request_id != request_id:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    trip = await db.get(Trip, offer.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    booking = Booking(
        trip_id=trip.id,
        passenger_id=current_user.get("user_id"),
        seats_count=request.seats_needed,
        total_price=trip.price_per_seat * request.seats_needed,
        status=BookingStatus.confirmed,
    )
    db.add(booking)

    request.status = TripRequestStatus.accepted
    await db.commit()
    await db.refresh(request)

    driver = await db.get(User, offer.driver_id)
    if driver and driver.fcm_token:
        from app.services.firebase_service import send_push
        try:
            send_push(
                driver.fcm_token,
                "Пассажир выбрал вас!",
                "Ваш отклик принят. Проверьте детали поездки."
            )
        except Exception:
            pass

    return request
