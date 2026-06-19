from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.agreement import Agreement
from app.models.user import User
from app.schemas.agreement import AgreementCreate, AgreementOut

router = APIRouter(prefix="/agreements", tags=["agreements"])


@router.post("/accept", response_model=AgreementOut)
async def accept_agreement(
    data: AgreementCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    agreement = Agreement(
        user_id=current_user.id,
        version=data.version,
        ip_address=request.client.host if request.client else None,
    )
    db.add(agreement)
    await db.commit()
    await db.refresh(agreement)
    return agreement


@router.get("/my", response_model=list[AgreementOut])
async def my_agreements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Agreement)
        .where(Agreement.user_id == current_user.id)
        .order_by(Agreement.accepted_at.desc())
    )
    return result.scalars().all()