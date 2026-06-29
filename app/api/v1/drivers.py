from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.driver_profile import DriverProfile, OFFER_PRICE
from app.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/drivers", tags=["drivers"])


def _profile_dict(p: DriverProfile) -> dict:
    return {
        "id": p.id,
        "user_id": p.user_id,
        "car_brand": p.car_brand,
        "car_model": p.car_model,
        "car_year": p.car_year,
        "car_color": p.car_color,
        "car_number": p.car_number,
        "is_verified": p.is_verified,
        "rejection_reason": p.rejection_reason,
        "rating": p.rating,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.post("/profile")
async def create_driver_profile(
    car_brand: str,
    car_model: str,
    car_year: int,
    car_color: str,
    car_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    existing = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == current_user["user_id"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Профиль уже создан")

    profile = DriverProfile(
        user_id=current_user["user_id"],
        car_brand=car_brand,
        car_model=car_model,
        car_year=car_year,
        car_color=car_color,
        car_number=car_number,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return {"message": "Профиль создан", "data": _profile_dict(profile)}


@router.get("/profile")
async def get_driver_profile(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == current_user["user_id"])
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return {"data": _profile_dict(profile)}


@router.patch("/profile/vehicle")
async def update_vehicle(
    car_brand: str,
    car_model: str,
    car_year: int,
    car_color: str,
    car_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Водитель меняет машину — верификация сбрасывается."""
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == current_user["user_id"])
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    profile.car_brand = car_brand
    profile.car_model = car_model
    profile.car_year = car_year
    profile.car_color = car_color
    profile.car_number = car_number
    profile.is_verified = False
    profile.rejection_reason = None
    await db.commit()
    return {"message": "Данные машины обновлены, ожидайте верификации"}


@router.get("/all")
async def get_all_drivers(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Админ видит всех водителей."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только администратор")

    result = await db.execute(select(DriverProfile))
    profiles = result.scalars().all()

    out = []
    for p in profiles:
        user = await db.get(User, p.user_id)
        out.append({
            **_profile_dict(p),
            "name": user.name if user else "",
            "phone": user.phone if user else "",
        })
    return {"data": out}


@router.get("/unverified")
async def get_unverified_drivers(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Админ видит список неверифицированных водителей с данными пользователя."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только администратор")

    result = await db.execute(
        select(DriverProfile).where(DriverProfile.is_verified == False)
    )
    profiles = result.scalars().all()

    out = []
    for p in profiles:
        user = await db.get(User, p.user_id)
        out.append({
            **_profile_dict(p),
            "name": user.name if user else "",
            "phone": user.phone if user else "",
        })
    return {"data": out}


@router.get("/balance")
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == current_user["user_id"])
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return {"balance": float(profile.balance or 0), "offer_price": OFFER_PRICE}


@router.post("/balance/topup")
async def topup_balance(
    amount: float,
    driver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Только администратор пополняет баланс водителя."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только администратор")
    profile = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == driver_id)
    )
    profile = profile.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    profile.balance = float(profile.balance or 0) + amount
    await db.commit()
    return {"balance": float(profile.balance), "message": f"Пополнено на {amount} ₸"}


@router.patch("/{driver_id}/verify")
async def verify_driver(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
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
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только администратор")

    profile = await db.get(DriverProfile, driver_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    profile.is_verified = False
    profile.rejection_reason = reason
    await db.commit()
    return {"message": "Водитель отклонён", "reason": reason}
