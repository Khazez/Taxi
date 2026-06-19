from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentOut

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentOut)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # проверяем что бронь существует и принадлежит текущему пользователю
    booking = await db.get(Booking, data.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    if booking.passenger_id != current_user.id:
        raise HTTPException(status_code=403, detail="Это не ваша бронь")

    # проверяем что платёж ещё не создан
    existing = await db.execute(
        select(Payment).where(Payment.booking_id == data.booking_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Платёж уже существует")

    payment = Payment(
        booking_id=data.booking_id,
        amount=booking.total_price,
        method=data.method,
        status=PaymentStatus.completed if data.method == PaymentMethod.cash else PaymentStatus.pending,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")

    # проверяем что это платёж текущего пользователя
    booking = await db.get(Booking, payment.booking_id)
    if booking.passenger_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа")

    return payment