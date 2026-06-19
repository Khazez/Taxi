from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.driver_profile import DriverProfile
from app.models.user import User, UserRole
from app.services.minio_service import upload_file

router = APIRouter(prefix="/files", tags=["files"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/driver/license")
async def upload_license(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Водитель загружает фото прав."""
    if current_user.role != UserRole.driver:
        raise HTTPException(status_code=403, detail="Только водитель")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Только JPG, PNG или PDF")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Файл больше 10MB")

    url = upload_file(data, file.filename, file.content_type)

    # сохраняем ссылку в профиле водителя
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Сначала создайте профиль водителя")

    profile.license_doc_url = url
    await db.commit()
    return {"url": url}


@router.post("/driver/car-doc")
async def upload_car_doc(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Водитель загружает тех.паспорт."""
    if current_user.role != UserRole.driver:
        raise HTTPException(status_code=403, detail="Только водитель")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Только JPG, PNG или PDF")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Файл больше 10MB")

    url = upload_file(data, file.filename, file.content_type)

    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Сначала создайте профиль водителя")

    profile.car_doc_url = url
    await db.commit()
    return {"url": url}