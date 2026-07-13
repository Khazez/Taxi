import re
import random
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

# phone -> (code, expires_at)
_otp_store: dict[str, tuple[str, float]] = {}


def _normalize(phone: str) -> str:
    """Приводит номер к виду +7XXXXXXXXXX."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    return f'+{digits}' if digits.startswith('7') else phone


# для демонстрации без реального SMS-шлюза
TEST_PHONES = {
    "+77009998877",  # пассажир (новый, без профиля)
    "+77001112233",  # водитель Алибек — уже верифицирован, Toyota Camry
    "+77001112244",  # водитель Ержан — уже верифицирован, Hyundai Sonata
}
TEST_CODE = "0000"


def _gen_otp(phone: str) -> str:
    key = _normalize(phone)
    code = TEST_CODE if key in TEST_PHONES else str(random.randint(1000, 9999))
    _otp_store[key] = (code, time.time() + 300)
    return code

@router.post("/register")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == data.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Телефон уже зарегистрирован")
    
    role = UserRole.driver if data.role == "driver" else UserRole.passenger
    user = User(
        name=data.name,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"message": "Пользователь создан", "access_token": token}

@router.post("/send-otp")
async def send_otp(phone: str, db: AsyncSession = Depends(get_db)):
    """Отправить код на телефон. Пока код печатается в консоль."""
    key = _normalize(phone)
    code = _gen_otp(key)
    print(f"[SMS] {key} → код: {code}")
    return {"message": "Код отправлен"}


@router.post("/verify-otp")
async def verify_otp(
    phone: str,
    code: str,
    name: str | None = None,
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Проверить код. Если новый пользователь — нужно передать name."""
    key = _normalize(phone)
    entry = _otp_store.get(key)
    if not entry:
        raise HTTPException(status_code=400, detail="Неверный или истёкший код")
    stored, expires = entry
    if time.time() > expires:
        del _otp_store[key]
        raise HTTPException(status_code=400, detail="Неверный или истёкший код")
    if stored != code:
        raise HTTPException(status_code=400, detail="Неверный или истёкший код")

    # Ищем пользователя по нормализованному (+7...) и старому (8...) форматам
    alt = '8' + key[2:] if key.startswith('+7') else key
    result = await db.execute(
        select(User).where(or_(User.phone == key, User.phone == alt))
    )
    user = result.scalar_one_or_none()

    new_role = UserRole.driver if role == "driver" else UserRole.passenger

    if user is None:
        if not name:
            raise HTTPException(status_code=400, detail="Новый пользователь — укажите имя")
        del _otp_store[key]
        user = User(name=name, phone=key, password_hash="otp", role=new_role)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        del _otp_store[key]
        if role in ("passenger", "driver"):
            user.role = new_role
            await db.commit()

    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"access_token": token}


@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный телефон или пароль")
    
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"access_token": token}
@router.get("/me")
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = await db.get(User, current_user.get("user_id"))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "role": user.role.value,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.patch("/me")
async def update_me(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = await db.get(User, current_user.get("user_id"))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if "name" in data and data["name"]:
        user.name = data["name"].strip()
    await db.commit()
    return {"message": "Профиль обновлён", "name": user.name}


@router.post("/fcm-token")
async def update_fcm_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Пользователь обновляет FCM токен своего устройства."""
    user = await db.get(User, current_user.get("user_id"))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.fcm_token = token
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