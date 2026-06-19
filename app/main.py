import logging
logging.basicConfig(level=logging.DEBUG)
from fastapi import FastAPI
from app.api.v1.auth import router as auth_router
from app.api.v1.routes import router as routes_router
from app.api.v1.trips import router as trips_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.drivers import router as drivers_router

app = FastAPI(title="Межгород Такси API")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(routes_router, prefix="/api/v1")
app.include_router(trips_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")
app.include_router(drivers_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "API работает"}