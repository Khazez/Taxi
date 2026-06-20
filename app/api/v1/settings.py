from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.settings import PlatformSettings
from app.models.user import User, UserRole
from app.schemas.settings import SettingOut, SettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=list[SettingOut])
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Только админ видит все настройки."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только администратор")

    result = await db.execute(select(PlatformSettings))
    return result.scalars().all()


@router.patch("/{key}", response_model=SettingOut)
async def update_setting(
    key: str,
    data: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Админ меняет значение настройки."""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Только администратор")

    result = await db.execute(
        select(PlatformSettings).where(PlatformSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    if not setting:
        raise HTTPException(status_code=404, detail="Настройка не найдена")

    setting.value = data.value
    await db.commit()
    await db.refresh(setting)
    return setting