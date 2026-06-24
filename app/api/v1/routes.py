from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from app.db.database import get_db
from app.models.route import Route, RoutePrice

router = APIRouter(prefix="/routes", tags=["routes"])


async def _route_with_price(route: Route, db: AsyncSession) -> dict:
    price_res = await db.execute(
        select(RoutePrice)
        .where(RoutePrice.route_id == route.id)
        .order_by(desc(RoutePrice.created_at))
        .limit(1)
    )
    latest = price_res.scalar_one_or_none()
    return {
        "id": route.id,
        "city_from": route.city_from,
        "city_to": route.city_to,
        "is_active": bool(route.is_active),
        "current_price": float(latest.price) if latest else None,
    }


@router.get("/")
async def get_routes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Route).where(Route.is_active == 1))
    routes = result.scalars().all()
    data = [await _route_with_price(r, db) for r in routes]
    return {"data": data}


@router.get("/all")
async def get_all_routes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Route))
    routes = result.scalars().all()
    data = [await _route_with_price(r, db) for r in routes]
    return {"data": data}


@router.post("/")
async def create_route(city_from: str, city_to: str, price: float, db: AsyncSession = Depends(get_db)):
    # Создаём A→B
    route_ab = Route(city_from=city_from, city_to=city_to)
    db.add(route_ab)
    await db.flush()
    db.add(RoutePrice(route_id=route_ab.id, price=price))

    # Создаём B→A
    route_ba = Route(city_from=city_to, city_to=city_from)
    db.add(route_ba)
    await db.flush()
    db.add(RoutePrice(route_id=route_ba.id, price=price))

    await db.commit()
    return {"message": "Маршрут создан в обе стороны", "id": route_ab.id}


@router.patch("/{route_id}")
async def update_route(
    route_id: int,
    city_from: Optional[str] = None,
    city_to: Optional[str] = None,
    price: Optional[float] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Маршрут не найден")

    if city_from is not None:
        route.city_from = city_from
    if city_to is not None:
        route.city_to = city_to
    if is_active is not None:
        route.is_active = 1 if is_active else 0
    if price is not None:
        db.add(RoutePrice(route_id=route_id, price=price))

    await db.commit()
    return {"message": "Маршрут обновлён"}


@router.delete("/{route_id}")
async def delete_route(route_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Маршрут не найден")

    route.is_active = 0
    await db.commit()
    return {"message": "Маршрут деактивирован"}
