from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == data.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Телефон уже зарегистрирован")
    
    user = User(
        name=data.name,
        phone=data.phone,
        password_hash=hash_password(data.password)
    )
    db.add(user)
    await db.commit()
    return {"message": "Пользователь создан"}

@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный телефон или пароль")
    
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"access_token": token}
@router.post("/fcm-token")
async def update_fcm_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Пользователь обновляет FCM токен своего устройства."""
    current_user.fcm_token = token
    await db.commit()
    return {"message": "FCM токен обновлён"}
@router.post("/admin/login")
async def admin_login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import noload
    result = await db.execute(select(User).where(User.email == email).options(noload("*")))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Нет доступа")

    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"access_token": token}