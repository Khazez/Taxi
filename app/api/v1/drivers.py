from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.driver_profile import DriverProfile
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.post("/profile")
async def create_driver_profile(
    car_brand: str,
    car_model: str,
    car_year: int,
    car_color: str,
    car_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    profile = DriverProfile(
        user_id=current_user["user_id"],
        car_brand=car_brand,
        car_model=car_model,
        car_year=car_year,
        car_color=car_color,
        car_number=car_number
    )
    db.add(profile)
    await db.commit()
    return {"message": "Профиль создан"}

@router.get("/profile")
async def get_driver_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == current_user["user_id"])
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return {"data": profile}
    from app.models.user import User, UserRole


@router.get("/unverified")
async def get_unverified_drivers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Админ видит список неверифицированных водителей."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Только администратор")

    result = await db.execute(
        select(DriverProfile).where(DriverProfile.is_verified == False)
    )
    return {"data": result.scalars().all()}


@router.patch("/{driver_id}/verify")
async def verify_driver(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Админ одобряет водителя."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Только администратор")

    profile = await db.get(DriverProfile, driver_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    profile.is_verified = True
    profile.rejection_reason = None
    await db.commit()
    return {"message": "Водитель верифицирован"}


@router.patch("/{driver_id}/reject")
async def reject_driver(
    driver_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Админ отклоняет водителя с указанием причины."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Только администратор")

    profile = await db.get(DriverProfile, driver_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    profile.is_verified = False
    profile.rejection_reason = reason
    await db.commit()
    return {"message": "Водитель отклонён", "reason": reason}