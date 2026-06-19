from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.fleet_profile import FleetProfile, FleetDriver
from app.models.user import User, UserRole
from app.schemas.fleet import FleetProfileCreate, FleetProfileOut, FleetDriverAdd, FleetDriverOut

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.post("/profile", response_model=FleetProfileOut)
async def create_fleet_profile(
    data: FleetProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # только пользователь с ролью fleet может создать профиль
    if current_user.role != UserRole.fleet:
        raise HTTPException(status_code=403, detail="Только таксопарк может создать профиль")

    # проверяем что профиль ещё не создан
    existing = await db.execute(
        select(FleetProfile).where(FleetProfile.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Профиль уже существует")

    profile = FleetProfile(
        user_id=current_user.id,
        company_name=data.company_name,
        phone=data.phone,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/profile", response_model=FleetProfileOut)
async def get_my_fleet_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FleetProfile).where(FleetProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль не найден")
    return profile


@router.post("/drivers", response_model=FleetDriverOut)
async def add_driver(
    data: FleetDriverAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # находим профиль таксопарка
    result = await db.execute(
        select(FleetProfile).where(FleetProfile.user_id == current_user.id)
    )
    fleet = result.scalar_one_or_none()
    if not fleet:
        raise HTTPException(status_code=404, detail="Сначала создайте профиль таксопарка")

    # проверяем что водитель существует и имеет роль driver
    driver = await db.get(User, data.driver_id)
    if not driver or driver.role != UserRole.driver:
        raise HTTPException(status_code=404, detail="Водитель не найден")

    # проверяем что водитель ещё не в таксопарке
    existing = await db.execute(
        select(FleetDriver).where(FleetDriver.driver_id == data.driver_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Водитель уже в таксопарке")

    fleet_driver = FleetDriver(fleet_id=fleet.id, driver_id=data.driver_id)
    db.add(fleet_driver)
    await db.commit()
    await db.refresh(fleet_driver)
    return fleet_driver


@router.get("/drivers", response_model=list[FleetDriverOut])
async def get_my_drivers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FleetProfile).where(FleetProfile.user_id == current_user.id)
    )
    fleet = result.scalar_one_or_none()
    if not fleet:
        raise HTTPException(status_code=404, detail="Профиль не найден")

    drivers = await db.execute(
        select(FleetDriver).where(FleetDriver.fleet_id == fleet.id)
    )
    return drivers.scalars().all()