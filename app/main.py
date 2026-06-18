import logging
logging.basicConfig(level=logging.DEBUG)
from fastapi import FastAPI
from app.api.v1.auth import router as auth_router

app = FastAPI(title="Межгород Такси API")

app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "API работает"}