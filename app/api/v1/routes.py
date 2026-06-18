from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.route import Route, RoutePrice

router = APIRouter(prefix="/routes", tags=["routes"])

@router.get("/")
async def get_routes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Route).where(Route.is_active == 1))
    routes = result.scalars().all()
    return {"data": routes}

@router.post("/")
async def create_route(city_from: str, city_to: str, price: float, db: AsyncSession = Depends(get_db)):
    route = Route(city_from=city_from, city_to=city_to)
    db.add(route)
    await db.flush()
    
    route_price = RoutePrice(route_id=route.id, price=price)
    db.add(route_price)
    await db.commit()
    return {"message": "Маршрут создан", "id": route.id}