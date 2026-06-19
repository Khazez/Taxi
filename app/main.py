import logging
logging.basicConfig(level=logging.DEBUG)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.routes import router as routes_router
from app.api.v1.trips import router as trips_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.drivers import router as drivers_router
from app.api.v1.agreements import router as agreements_router
from app.api.v1.ratings import router as ratings_router
from app.api.v1.fleet import router as fleet_router
from app.api.v1.payments import router as payments_router
from app.api.v1.trip_requests import router as trip_requests_router
from app.api.v1.settings import router as settings_router   
from app.api.v1.files import router as files_router

app = FastAPI(title="Межгород Такси API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(routes_router, prefix="/api/v1")
app.include_router(trips_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")
app.include_router(drivers_router, prefix="/api/v1")
app.include_router(agreements_router, prefix="/api/v1")
app.include_router(ratings_router, prefix="/api/v1")
app.include_router(fleet_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(trip_requests_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "API работает"}