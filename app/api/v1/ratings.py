from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.rating import Rating
from app.models.trip import Trip, TripStatus
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingOut

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("/", response_model=RatingOut)
async def create_rating(
    data: RatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # проверяем что поездка существует и завершена
    trip = await db.get(Trip, data.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Поездка не найдена")
    if trip.status != TripStatus.completed:
        raise HTTPException(status_code=400, detail="Можно оценивать только завершённые поездки")

    # нельзя оценить самого себя
    if data.to_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя оценить самого себя")

    # нельзя оценить дважды
    existing = await db.execute(
        select(Rating).where(
            Rating.trip_id == data.trip_id,
            Rating.from_user_id == current_user.id,
            Rating.to_user_id == data.to_user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Вы уже оценили этого пользователя")

    rating = Rating(
        trip_id=data.trip_id,
        from_user_id=current_user.id,
        to_user_id=data.to_user_id,
        score=data.score,
    )
    db.add(rating)
    await db.commit()
    await db.refresh(rating)
    return rating


@router.get("/user/{user_id}", response_model=dict)
async def get_user_rating(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(func.avg(Rating.score), func.count(Rating.id))
        .where(Rating.to_user_id == user_id)
    )
    avg_score, total = result.one()
    return {
        "user_id": user_id,
        "average_score": round(float(avg_score), 2) if avg_score else None,
        "total_ratings": total,
    }