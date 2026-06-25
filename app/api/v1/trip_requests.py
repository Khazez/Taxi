import json as _json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.trip_request import TripRequest, TripRequestStatus, TripOffer
from app.models.trip import Trip, TripStatus
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.models.route import Route
from app.models.driver_profile import DriverProfile

from app.schemas.trip_request import TripRequestCreate, TripRequestOut

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
        contact_name=data.contact_name,
        contact_phone=data.contact_phone,
        pickup_address=data.pickup_address,
        entrance=data.entrance,
        extra_pickups=_json.dumps([ep.model_dump(exclude_none=True) for ep in data.extra_pickups]) if data.extra_pickups else None,
        destination_address=data.destination_address,
        destination_entrance=data.destination_entrance,
        extra_destinations=_json.dumps([ed.model_dump(exclude_none=True) for ed in data.extra_destinations]) if data.extra_destinations else None,
        payment_type=data.payment_type,
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
    passenger_id = current_user.get("user_id")
    result = await db.execute(
        select(TripRequest, Route)
        .join(Route, TripRequest.route_id == Route.id)
        .where(TripRequest.passenger_id == passenger_id)
        .order_by(TripRequest.id.desc())
    )
    rows = result.all()

    output = []
    for req, r in rows:
        item = {
            "id": req.id,
            "status": req.status.value,
            "seats_needed": req.seats_needed,
            "departure_date": req.departure_date.isoformat() if req.departure_date else None,
            "route_name": f"{r.city_from} → {r.city_to}",
            "comment": req.comment,
            "contact_name": req.contact_name,
            "contact_phone": req.contact_phone,
            "pickup_address": req.pickup_address,
            "entrance": req.entrance,
            "extra_pickups": _json.loads(req.extra_pickups) if req.extra_pickups else [],
            "destination_address": req.destination_address,
            "destination_entrance": req.destination_entrance,
            "extra_destinations": _json.loads(req.extra_destinations) if req.extra_destinations else [],
            "payment_type": req.payment_type,
        }
        if req.status == TripRequestStatus.accepted:
            offer_result = await db.execute(
                select(TripOffer, User, DriverProfile)
                .join(User, TripOffer.driver_id == User.id)
                .outerjoin(DriverProfile, DriverProfile.user_id == TripOffer.driver_id)
                .where(TripOffer.request_id == req.id)
                .limit(1)
            )
            offer_row = offer_result.first()
            if offer_row:
                offer_obj, driver, profile = offer_row
                item["driver_name"] = driver.name
                item["driver_phone"] = driver.phone
                item["driver_user_id"] = driver.id
                if offer_obj.price_per_seat:
                    item["agreed_price"] = float(offer_obj.price_per_seat) * (req.seats_needed or 1)
                if profile:
                    item["car_brand"] = profile.car_brand
                    item["car_model"] = profile.car_model
                    item["car_color"] = profile.car_color
                    item["car_number"] = profile.car_number
                    item["car_year"] = profile.car_year
                # Найти trip_id и trip_status
                trip_id = offer_obj.trip_id
                if trip_id:
                    trip = await db.get(Trip, trip_id)
                    item["trip_id"] = trip_id
                    item["trip_status"] = trip.status.value if trip else None
                else:
                    # Fallback для старых записей
                    b_result = await db.execute(
                        select(Booking, Trip)
                        .join(Trip, Booking.trip_id == Trip.id)
                        .where(Booking.passenger_id == passenger_id)
                        .where(Trip.driver_id == driver.id)
                        .where(Trip.route_id == req.route_id)
                        .order_by(Booking.id.desc()).limit(1)
                    )
                    b_row = b_result.first()
                    if b_row:
                        b, t = b_row
                        item["trip_id"] = t.id
                        item["trip_status"] = t.status.value
        output.append(item)

    return output


class _ExtraAddrItem(BaseModel):
    address: str
    entrance: str | None = None

class TripRequestUpdate(BaseModel):
    seats_needed: int | None = None
    departure_date: str | None = None
    pickup_address: str | None = None
    entrance: str | None = None
    extra_pickups: list[_ExtraAddrItem] | None = None
    destination_address: str | None = None
    destination_entrance: str | None = None
    extra_destinations: list[_ExtraAddrItem] | None = None
    payment_type: str | None = None
    comment: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None

@router.patch("/{request_id}")
async def update_request(
    request_id: int,
    data: TripRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Пассажир редактирует заявку пока водитель не принял."""
    request = await db.get(TripRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if request.passenger_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if request.status != TripRequestStatus.open:
        raise HTTPException(status_code=400, detail="Нельзя редактировать принятую заявку")

    from datetime import datetime as _dt
    if data.seats_needed is not None:
        request.seats_needed = data.seats_needed
    if data.departure_date is not None:
        request.departure_date = _dt.fromisoformat(data.departure_date)
    if data.pickup_address is not None:
        request.pickup_address = data.pickup_address
    if data.entrance is not None:
        request.entrance = data.entrance
    if data.extra_pickups is not None:
        request.extra_pickups = _json.dumps([ep.model_dump(exclude_none=True) for ep in data.extra_pickups]) if data.extra_pickups else None
    if data.destination_address is not None:
        request.destination_address = data.destination_address
    if data.destination_entrance is not None:
        request.destination_entrance = data.destination_entrance
    if data.extra_destinations is not None:
        request.extra_destinations = _json.dumps([ed.model_dump(exclude_none=True) for ed in data.extra_destinations]) if data.extra_destinations else None
    if data.payment_type is not None:
        request.payment_type = data.payment_type
    if data.comment is not None:
        request.comment = data.comment
    if data.contact_name is not None:
        request.contact_name = data.contact_name
    if data.contact_phone is not None:
        request.contact_phone = data.contact_phone

    await db.commit()
    return {"message": "Заявка обновлена"}


@router.delete("/{request_id}")
async def cancel_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Пассажир отменяет заявку."""
    request = await db.get(TripRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if request.passenger_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if request.status != TripRequestStatus.open:
        raise HTTPException(status_code=400, detail="Нельзя отменить принятую заявку")

    request.status = TripRequestStatus.cancelled

    offers_result = await db.execute(
        select(TripOffer).where(TripOffer.request_id == request_id)
    )
    offers = offers_result.scalars().all()
    await db.commit()

    from app.services.firebase_service import send_push
    for offer in offers:
        driver = await db.get(User, offer.driver_id)
        if driver and driver.fcm_token:
            try:
                send_push(driver.fcm_token, "Заявка отменена", "Пассажир отменил заявку")
            except Exception:
                pass

    return {"message": "Заявка отменена"}


class DriverOfferCreate(BaseModel):
    request_id: int
    price_per_seat: float


@router.post("/offers")
async def create_offer(
    data: DriverOfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Водитель откликается на заявку — указывает только цену."""
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
        trip_id=None,
        driver_id=current_user.get("user_id"),
        price_per_seat=data.price_per_seat,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)

    # Уведомить пассажира о новом отклике
    passenger = await db.get(User, request.passenger_id)
    if passenger and passenger.fcm_token:
        driver_user = await db.get(User, current_user.get("user_id"))
        driver_name = driver_user.name if driver_user else "Водитель"
        from app.services.firebase_service import send_push
        try:
            send_push(
                passenger.fcm_token,
                "Новый отклик!",
                f"{driver_name} предлагает {int(data.price_per_seat)} ₸",
            )
        except Exception:
            pass

    return {"id": offer.id, "request_id": offer.request_id, "price_per_seat": float(data.price_per_seat)}


@router.delete("/{request_id}/offers/{offer_id}")
async def decline_offer(
    request_id: int,
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Пассажир отклоняет конкретный оффер водителя."""
    request = await db.get(TripRequest, request_id)
    if not request or request.passenger_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if request.status != TripRequestStatus.open:
        raise HTTPException(status_code=400, detail="Заявка уже закрыта")

    offer = await db.get(TripOffer, offer_id)
    if not offer or offer.request_id != request_id:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    driver = await db.get(User, offer.driver_id)
    if driver and driver.fcm_token:
        from app.services.firebase_service import send_push
        try:
            send_push(driver.fcm_token, "Отклик отклонён", "Пассажир не принял ваш отклик")
        except Exception:
            pass

    await db.delete(offer)
    await db.commit()
    return {"message": "Отклик отклонён"}


@router.delete("/offers/{offer_id}")
async def cancel_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Водитель отзывает свой отклик (в т.ч. после принятия — поездка отменяется, заявка снова открывается)."""
    offer = await db.get(TripOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Отклик не найден")
    if offer.driver_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Нет доступа")

    request = await db.get(TripRequest, offer.request_id)
    was_accepted = request is not None and request.status == TripRequestStatus.accepted

    if was_accepted:
        # Отменяем поездку и бронь, возвращаем заявку в open
        if offer.trip_id:
            trip = await db.get(Trip, offer.trip_id)
            if trip:
                trip.status = TripStatus.cancelled
                # Отменяем все брони этой поездки
                bookings_result = await db.execute(
                    select(Booking).where(Booking.trip_id == trip.id)
                )
                for booking in bookings_result.scalars().all():
                    booking.status = BookingStatus.cancelled
        else:
            # Trip создавался автоматически при accept — ищем по driver+route+time
            from sqlalchemy import and_
            trips_result = await db.execute(
                select(Trip).where(
                    and_(
                        Trip.driver_id == offer.driver_id,
                        Trip.route_id == request.route_id,
                    )
                ).order_by(Trip.id.desc()).limit(1)
            )
            trip = trips_result.scalar_one_or_none()
            if trip and trip.status == TripStatus.active:
                trip.status = TripStatus.cancelled
                bookings_result = await db.execute(
                    select(Booking).where(Booking.trip_id == trip.id)
                )
                for booking in bookings_result.scalars().all():
                    booking.status = BookingStatus.cancelled

        request.status = TripRequestStatus.open

    # Уведомить пассажира
    if request:
        passenger = await db.get(User, request.passenger_id)
        if passenger and passenger.fcm_token:
            driver_user = await db.get(User, current_user.get("user_id"))
            driver_name = driver_user.name if driver_user else "Водитель"
            from app.services.firebase_service import send_push
            if was_accepted:
                title = "Водитель отменил поездку"
                body = f"{driver_name} отменил принятую поездку. Заявка снова открыта."
            else:
                title = "Водитель отозвал отклик"
                body = f"{driver_name} отозвал свой отклик"
            try:
                send_push(passenger.fcm_token, title, body)
            except Exception:
                pass

    await db.delete(offer)
    await db.commit()
    return {"message": "Отклик отозван"}


@router.get("/{request_id}/offers")
async def get_offers(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Пассажир видит отклики на свою заявку с данными водителя и поездки."""
    request = await db.get(TripRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    if request.passenger_id != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Это не ваша заявка")

    result = await db.execute(
        select(TripOffer, User, DriverProfile)
        .join(User, TripOffer.driver_id == User.id)
        .outerjoin(DriverProfile, DriverProfile.user_id == TripOffer.driver_id)
        .where(TripOffer.request_id == request_id)
        .order_by(TripOffer.id.asc())
    )
    rows = result.all()

    output = []
    for offer, driver, profile in rows:
        seats_needed = request.seats_needed or 1
        price = float(offer.price_per_seat) if offer.price_per_seat else 0.0
        output.append({
            "id": offer.id,
            "driver_name": driver.name,
            "driver_phone": driver.phone,
            "price_per_seat": price,
            "total_price": price * seats_needed,
            "created_at": offer.created_at.isoformat() if offer.created_at else None,
            "car_brand": profile.car_brand if profile else None,
            "car_model": profile.car_model if profile else None,
            "car_color": profile.car_color if profile else None,
            "car_number": profile.car_number if profile else None,
            "car_year": profile.car_year if profile else None,
        })
    return output


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

    # Если у оффера нет trip_id — создаём поездку автоматически
    if offer.trip_id:
        trip = await db.get(Trip, offer.trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Поездка не найдена")
    else:
        price = offer.price_per_seat or 0
        trip = Trip(
            driver_id=offer.driver_id,
            route_id=request.route_id,
            departure_time=request.departure_date,
            seats_total=request.seats_needed,
            seats_available=0,
            price_per_seat=price,
        )
        db.add(trip)
        await db.flush()
        offer.trip_id = trip.id

    booking = Booking(
        trip_id=trip.id,
        passenger_id=current_user.get("user_id"),
        seats_count=request.seats_needed,
        total_price=trip.price_per_seat * request.seats_needed,
        pickup_address=request.pickup_address,
        entrance=request.entrance,
        extra_pickups=request.extra_pickups,
        destination_address=request.destination_address,
        destination_entrance=request.destination_entrance,
        extra_destinations=request.extra_destinations,
        contact_name=request.contact_name,
        contact_phone=request.contact_phone,
        comment=request.comment,
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
