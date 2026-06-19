from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.booking import Booking, BookingStatus
from app.models.trip import Trip
from app.models.payment import Payment, PaymentStatus
from app.models.settings import PlatformSettings


async def get_setting(db: AsyncSession, key: str) -> str:
    result = await db.execute(
        select(PlatformSettings).where(PlatformSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=500, detail=f"Настройка '{key}' не найдена")
    return setting.value


async def cancel_booking(booking_id: int, user_id: int, db: AsyncSession) -> Booking:
    # получаем бронь
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    if booking.passenger_id != user_id:
        raise HTTPException(status_code=403, detail="Это не ваша бронь")
    if booking.status == BookingStatus.cancelled:
        raise HTTPException(status_code=400, detail="Бронь уже отменена")

    # получаем поездку чтобы знать время отправления
    trip = await db.get(Trip, booking.trip_id)

    # считаем сколько минут до поездки
    now = datetime.now(timezone.utc)
    departure = trip.departure_time.replace(tzinfo=timezone.utc)
    minutes_left = (departure - now).total_seconds() / 60

    # читаем настройки из БД
    window = int(await get_setting(db, "cancellation_window_minutes"))
    fee_percent = int(await get_setting(db, "cancellation_fee_percent"))

    # применяем штраф если нужно
    if minutes_left < window:
        fee = booking.total_price * fee_percent / 100
        # обновляем платёж — возврат минус штраф
        result = await db.execute(
            select(Payment).where(Payment.booking_id == booking_id)
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = PaymentStatus.refunded
            # здесь в будущем логика частичного возврата через платёжный шлюз

    booking.status = BookingStatus.cancelled
    await db.commit()
    await db.refresh(booking)
    return booking