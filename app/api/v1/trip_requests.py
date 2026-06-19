from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.trip_request import TripRequest, TripRequestStatus, TripOffer
from app.models.trip import Trip
from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole
from app.schemas.trip_request import TripRequestCreate, TripRequestOut, TripOfferCreate, TripOfferOut

router = APIRouter(prefix="/trip-requests", tags=["trip-requests"])


@router.post("/", response_model=TripRequestOut)
async def create_request(
    data: TripRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Пассажир создаёт заявку на поездку."""
    if current_user.role != UserRole.passenger:
        raise HTTPException(status_code=403, detail="Только пассажир может создать заявку")

    request = TripRequest(
        passenger_id=current_user.id,
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
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Водитель видит открытые заявки по маршруту."""
    result = await db.execute(
        select(TripRequest).where(
            TripRequest.route_id == route_id,
            TripRequest.status == TripRequestStatus.open,
        )
    )
    return result.scalars().all()


@router.post("/offers", response_model=TripOfferOut)
async def create_offer(
    data: TripOfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Водитель откликается на заявку пассажира."""
    if current_user.role != UserRole.driver:
        raise HTTPException(status_code=403, detail="Только водитель может откликнуться")

    # проверяем что заявка открыта
    request = await db.get(TripRequest, data.request_id)
    if not request or request.status != TripRequestStatus.open:
        raise HTTPException(status_code=404, detail="Заявка не найдена или уже закрыта")

    # проверяем что водитель не откликался уже
    existing = await db.execute(
        select(TripOffer).where(
            TripOffer.request_id == data.request_id,
            TripOffer.driver_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже откликнулись на эту заявку")

    offer = TripOffer(
        request_id=data.request_id,
        trip_id=data.trip_id,
        driver_id=current_user.id,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


@router.get("/{request_id}/offers", response_model=list[TripOfferOut])
async def get_offers(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Пассажир видит отклики на свою заявку."""
    request = await db.get(TripRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if request.passenger_id != current_user.id:
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
    current_user: User = Depends(get_current_user),
):
    """Пассажир выбирает водителя — заявка закрывается, бронь создаётся."""
    request = await db.get(TripRequest, request_id)
    if not request or request.passenger_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")
    if request.status != TripRequestStatus.open:
        raise HTTPException(status_code=400, detail="Заявка уже закрыта")

    offer = await db.get(TripOffer, offer_id)
    if not offer or offer.request_id != request_id:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    # получаем поездку чтобы узнать цену
    trip = await db.get(Trip, offer.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    # создаём бронь автоматически
    booking = Booking(
        trip_id=trip.id,
        passenger_id=current_user.id,
        seats_count=request.seats_needed,
        total_price=trip.price_per_seat * request.seats_needed,
        status=BookingStatus.confirmed,
    )
    db.add(booking)

    # закрываем заявку
    # закрываем заявку
    request.status = TripRequestStatus.accepted
    await db.commit()
    await db.refresh(request)

    # уведомляем водителя
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
            pass  # не ломаем если push не дошёл

    return request